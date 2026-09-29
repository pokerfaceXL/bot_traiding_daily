"""
tests/test_signal_family_contract.py -- shared F006 signal-family contract
(spec/research/F006-shared-harness.md). Every F006 signal module must satisfy this
contract; family-specific formula tests (exact hand-derived values, mirror
directions, edge-case guards, ...) stay in tests/test_<family>.py and are not
duplicated here.

Parametrized over every family module currently wired into production
(donchian.py, lorentzian.py -- both `strategy.STRATEGY_CATALOG.update(...)` at
strategy.py import time) plus a synthetic DUMMY family defined only in this file,
so the contract itself is proven family-agnostic rather than accidentally hardcoded
to one family's fixture shape. No sibling F006 branch module (obv.py, aroon.py,
cci.py, bb_kelt_squeeze.py, ...) is imported here -- per the ticket, this must not
depend on any unmerged research module at runtime.

Six checks, each generic over "a dict[name -> callable(df) -> pd.Series]":
  1. signal domain    -- every non-NaN value is in {-1, 0, 1}.
  2. causality         -- prefix-truncation and future-perturbation invariance.
  3. no input mutation -- the caller's frame is never written to.
  4. catalog additivity -- registering a family's entries changes no other entry's
                            signal and a name collision is rejected, not silently
                            overwritten.
  5. one-shot alignment + next-bar fill -- through the real engine, a one-shot
     entry only ever fills on the bar immediately after its decision bar, never on
     the decision bar's own close.
"""
import inspect
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import backtest_engine  # noqa: E402
import donchian  # noqa: E402
import entry_masks  # noqa: E402
import f006_family_runner  # noqa: E402
import lorentzian  # noqa: E402
import strategy  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")


def _ohlcv() -> pd.DataFrame:
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


def _dummy_sma_cross(df: pd.DataFrame, fast: int, slow: int) -> pd.Series:
    """A minimal, genuinely causal persistent-state signal (fast/slow SMA cross),
    defined only to prove the contract below is not accidentally specific to
    donchian.py's or lorentzian.py's fixture shape."""
    close = pd.Series(df["close"])
    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    sig = pd.Series(0, index=df.index, dtype="float64")
    sig = sig.mask(fast_ma > slow_ma, 1.0).mask(fast_ma < slow_ma, -1.0)
    sig[fast_ma.isna() | slow_ma.isna()] = np.nan
    return sig


DUMMY_ENTRIES = {
    "CONTRACT_DUMMY_5_20": lambda df: _dummy_sma_cross(df, 5, 20),
    "CONTRACT_DUMMY_10_30": lambda df: _dummy_sma_cross(df, 10, 30),
}

# (family_name, catalog_entries(), already_registered_in_strategy_py)
FAMILIES = [
    ("donchian", donchian.catalog_entries(), True),
    ("lorentzian", lorentzian.catalog_entries(), True),
    ("dummy", DUMMY_ENTRIES, False),
]

FLAT_ENTRIES = [
    (family_name, name, fn)
    for family_name, entries, _ in FAMILIES
    for name, fn in entries.items()
]


# ── 1. signal domain ────────────────────────────────────────────────────────

@pytest.mark.parametrize("family_name,name,fn", FLAT_ENTRIES, ids=[f"{f}:{n}" for f, n, _ in FLAT_ENTRIES])
def test_signal_domain_is_minus1_zero_plus1_or_nan(family_name, name, fn):
    df = _ohlcv()
    sig = pd.Series(fn(df))
    assert len(sig) == len(df), f"{family_name}:{name} changed the frame length"
    assert sig.index.equals(df.index), f"{family_name}:{name} changed the frame index"
    non_nan = sig.dropna()
    assert non_nan.isin([-1, 0, 1]).all(), (
        f"{family_name}:{name} emitted a value outside {{-1, 0, 1}}: "
        f"{sorted(non_nan[~non_nan.isin([-1, 0, 1])].unique())}"
    )


# ── 2. causality / no lookahead ─────────────────────────────────────────────

@pytest.mark.parametrize("family_name,name,fn", FLAT_ENTRIES, ids=[f"{f}:{n}" for f, n, _ in FLAT_ENTRIES])
@pytest.mark.parametrize("prefix", [150, 300, 450])
def test_every_prefix_matches_and_future_perturbation_does_not_move_the_past(family_name, name, fn, prefix):
    df = _ohlcv()
    full = pd.Series(fn(df)).fillna(0)
    assert full.ne(0).any(), f"{family_name}:{name}: vacuous fixture, test would pass trivially"

    truncated = pd.Series(fn(df.iloc[:prefix])).fillna(0)
    assert truncated.tolist() == full.iloc[:prefix].tolist(), (
        f"{family_name}:{name}: a bar before {prefix} changed when the frame was truncated"
    )

    perturbed = df.copy()
    cols = perturbed.columns.get_indexer(["open", "high", "low", "close"])
    perturbed.iloc[prefix:, cols] *= 50.0
    if "volume" in perturbed.columns:
        perturbed.iloc[prefix:, perturbed.columns.get_loc("volume")] *= 500.0
    moved = pd.Series(fn(perturbed)).fillna(0)
    assert moved.iloc[:prefix].tolist() == full.iloc[:prefix].tolist(), (
        f"{family_name}:{name}: a bar before {prefix} changed when future bars were perturbed"
    )


# ── 3. no input mutation ────────────────────────────────────────────────────

@pytest.mark.parametrize("family_name,entries,_registered", FAMILIES, ids=[f[0] for f in FAMILIES])
def test_input_frame_is_never_mutated(family_name, entries, _registered):
    df = _ohlcv()
    before = df.copy(deep=True)
    for fn in entries.values():
        fn(df)
    pd.testing.assert_frame_equal(df, before)


# ── 4. catalog additivity ───────────────────────────────────────────────────

@pytest.mark.parametrize("family_name,entries,already_registered", FAMILIES, ids=[f[0] for f in FAMILIES])
def test_registering_a_family_leaves_every_other_catalog_entry_byte_identical(
    family_name, entries, already_registered, monkeypatch
):
    work = strategy.add_indicators(_ohlcv())
    baseline_names = [n for n in strategy.STRATEGY_CATALOG if n not in entries]
    baseline_signals = {n: pd.Series(strategy.STRATEGY_CATALOG[n](work)).copy() for n in baseline_names}

    if already_registered:
        for name in entries:
            assert name in strategy.STRATEGY_CATALOG, f"{family_name}:{name} claims to be registered but is not"
    else:
        for name in entries:
            assert name not in strategy.STRATEGY_CATALOG, f"{family_name}:{name} collides with an existing entry"
        for name, fn in entries.items():
            monkeypatch.setitem(strategy.STRATEGY_CATALOG, name, fn)

    for name, sig in baseline_signals.items():
        pd.testing.assert_series_equal(pd.Series(strategy.STRATEGY_CATALOG[name](work)), sig, check_names=False)


def test_register_catalog_entries_rejects_a_name_collision(monkeypatch):
    existing_name = next(iter(strategy.STRATEGY_CATALOG))
    with pytest.raises(ValueError):
        f006_family_runner.register_catalog_entries({existing_name: lambda df: df["close"] * 0})


def test_register_catalog_entries_adds_new_names_only(monkeypatch):
    # swap in a throwaway copy so register_catalog_entries's real mutation is
    # reverted by monkeypatch teardown, not left behind on the production catalog
    before = dict(strategy.STRATEGY_CATALOG)
    monkeypatch.setattr(strategy, "STRATEGY_CATALOG", dict(before))
    f006_family_runner.register_catalog_entries(DUMMY_ENTRIES)
    assert set(strategy.STRATEGY_CATALOG) == set(before) | set(DUMMY_ENTRIES)
    for name, fn in DUMMY_ENTRIES.items():
        assert strategy.STRATEGY_CATALOG[name] is fn


# ── 5. one-shot alignment + next-bar fill, through the real engine ─────────

@pytest.mark.parametrize("family_name,entries,already_registered", FAMILIES, ids=[f[0] for f in FAMILIES])
def test_one_shot_calls_fill_only_on_the_bar_after_the_decision_bar(
    family_name, entries, already_registered, monkeypatch
):
    df = _ohlcv()
    name = next(iter(entries))
    fn = entries[name]
    if not already_registered:
        monkeypatch.setitem(strategy.STRATEGY_CATALOG, name, fn)

    sig = entry_masks.strategy_signal_series(df, name, interval="240")
    mask = entry_masks.one_shot_entry_mask(sig)
    n_calls = int(mask.sum())
    if n_calls == 0:
        pytest.skip(f"{family_name}:{name}: no one-shot calls on this fixture")

    result = backtest_engine.run_backtest(
        df, name, interval="240", leverage=1.0, max_sl_pct=0.03, activate_pct=10.0,
        entry_regime_mask=mask,
    )
    assert len(result.trades) <= n_calls, (
        f"{family_name}:{name}: {len(result.trades)} trades from {n_calls} one-shot calls"
    )

    # a fill bar may itself be a DIFFERENT call's decision bar (back-to-back calls), so
    # only "immediately after its own decision bar" is asserted, not "never a mask bar"
    idx = df.index
    mask_arr = mask.to_numpy()
    eligible_next_bars = {idx[j + 1] for j in range(len(mask_arr) - 1) if mask_arr[j]}
    for _, trade in result.trades.iterrows():
        entry_time = pd.Timestamp(trade["entry_time"])
        assert entry_time in eligible_next_bars, (
            f"{family_name}:{name}: entry_time {entry_time} is not immediately after any one-shot call"
        )


# -- 6. frozen basket + harness control cannot be bypassed ------------------
# scripts/f006_family_runner.py: run_family() must always own the 5x2 SYMBOLS x
# INTERVALS basket and the DONCHIAN_55 control -- no kwarg may let a caller narrow
# the basket or skip the control while still claiming the frozen H1/H2 schema.

FORBIDDEN_RUN_FAMILY_KWARGS = {"symbols", "intervals", "control_name", "control_reference_csv"}


def test_run_family_exposes_no_basket_or_control_override():
    sig = inspect.signature(f006_family_runner.run_family)
    leaked = FORBIDDEN_RUN_FAMILY_KWARGS & set(sig.parameters)
    assert not leaked, f"run_family exposes a basket/control override kwarg: {leaked}"


@pytest.mark.parametrize("kwarg", sorted(FORBIDDEN_RUN_FAMILY_KWARGS))
def test_run_family_rejects_a_basket_or_control_override_kwarg(kwarg):
    with pytest.raises(TypeError):
        f006_family_runner.run_family(
            family="should_not_run", candidate_names=["DONCHIAN_20"],
            hypothesis_note="contract test", script_path="tests/test_signal_family_contract.py",
            **{kwarg: object()},
        )


def test_run_family_rejects_the_control_name_as_a_candidate():
    with pytest.raises(ValueError):
        f006_family_runner.run_family(
            family="should_not_run",
            candidate_names=[f006_family_runner.CONTROL_NAME],
            hypothesis_note="contract test", script_path="tests/test_signal_family_contract.py",
        )


def test_run_family_always_covers_the_frozen_basket_and_control(tmp_path):
    # This is the one live engine/cache integration test in this contract file.
    # CSVs are deliberately gitignored; a clean worktree has only their committed
    # manifests. Do not turn that expected absence into a failure of the API/unit
    # contract above. Prepare them offline from the main checkout's frozen cache
    # before requesting this live proof (see F006-shared-harness.md).
    cache_files = [
        "data_cache/{}_{}_20240126T000000Z_20250301T000000Z.csv".format(symbol, interval)
        for symbol in f006_family_runner.SYMBOLS
        for interval in f006_family_runner.INTERVALS
    ]
    missing = [path for path in cache_files if not os.path.exists(path)]
    if missing:
        pytest.skip(
            "live frozen-basket proof requires local bounded Train-1 CSVs; "
            "prepare them offline from the main checkout data_cache as documented "
            "in spec/research/F006-shared-harness.md (missing: {})".format(missing[0])
        )

    manifest = f006_family_runner.run_family(
        family="contract_basket_check",
        candidate_names=["DONCHIAN_20"],
        hypothesis_note=(
            "Contract test (tests/test_signal_family_contract.py): proves run_family "
            "always covers the frozen 5x2 SYMBOLS x INTERVALS basket and the DONCHIAN_55 "
            "harness control -- not a signal-family hypothesis."
        ),
        script_path="tests/test_signal_family_contract.py",
        output_dir=str(tmp_path / "f006_contract_basket_check"),
    )
    expected_keys = {f"{s}_{i}" for s in f006_family_runner.SYMBOLS for i in f006_family_runner.INTERVALS}
    assert set(manifest["checksums_used"]) == expected_keys, "basket was narrowed"
    assert manifest["n_series"] == len(expected_keys) * 2  # 1 candidate + 1 control, per series
    assert manifest["control_name"] == "DONCHIAN_55"
    assert manifest["harness_control"] is not None, "control check was skipped"
    assert manifest["harness_control"]["rows_compared"] == 10
    assert manifest["harness_control"]["n_mismatches"] == 0

    results_csv = os.path.join(str(tmp_path / "f006_contract_basket_check"), "summary", "results.csv")
    with open(results_csv) as f:
        header = f.readline().strip().split(",")
    assert set(header) == set(f006_family_runner.SUMMARY_COLUMNS), (
        "results.csv columns drifted from f006_family_runner.SUMMARY_COLUMNS"
    )
    for col in (
        "exit_initial_sl", "exit_trailing_sl", "exit_take_profit",
        "exit_signal_reverse", "exit_end_of_data", "sum_wins", "sum_losses",
        "mean_bars_held", "total_costs", "profit_factor", "calmar",
        "max_drawdown_usd",
    ):
        assert col in header, f"results.csv is missing frozen column {col!r}"


# -- 7. H1 must use Train-1 PnL, not diagnostic full-run PnL -----------------

def test_h1_uses_train1_pnl_not_full_run_pnl():
    # WARMUP_BOUNDARY_GAIN looks profitable in full-run net_pnl but lost during
    # Train-1; TRAIN1_GAIN is the reverse. H1's frozen gate must follow only the
    # pre-registered Train-1 window.
    rows = pd.DataFrame([
        {"strategy": "WARMUP_BOUNDARY_GAIN", "net_pnl": 100.0, "train1_net_pnl": -5.0, "n_trades": 2},
        {"strategy": "WARMUP_BOUNDARY_GAIN", "net_pnl": 20.0, "train1_net_pnl": 0.0, "n_trades": 3},
        {"strategy": "TRAIN1_GAIN", "net_pnl": -100.0, "train1_net_pnl": 5.0, "n_trades": 4},
        {"strategy": "TRAIN1_GAIN", "net_pnl": -20.0, "train1_net_pnl": 1.0, "n_trades": 5},
    ])

    h1 = {
        row["strategy"]: row
        for row in f006_family_runner._build_h1_table(
            rows, ["WARMUP_BOUNDARY_GAIN", "TRAIN1_GAIN"]
        )
    }

    assert h1["WARMUP_BOUNDARY_GAIN"] == {
        "strategy": "WARMUP_BOUNDARY_GAIN", "sum_net_pnl": -5.0,
        "mean_net_pnl": -2.5, "n_series": 2, "n_profitable_series": 0,
        "n_trades_total": 5, "h1_pass": False,
    }
    assert h1["TRAIN1_GAIN"]["sum_net_pnl"] == 6.0
    assert h1["TRAIN1_GAIN"]["mean_net_pnl"] == 3.0
    assert h1["TRAIN1_GAIN"]["n_profitable_series"] == 2
    assert h1["TRAIN1_GAIN"]["h1_pass"] is True


# -- 8. Train-1 loader must not peek beyond its frozen boundary ---------------

def test_load_train1_requests_only_warmup_through_train1_end(monkeypatch):
    requested = {}
    symbol, interval = "BTCUSDT", "60"
    index = pd.DatetimeIndex([
        pd.Timestamp("2024-01-26T00:00:00Z"),
        pd.Timestamp("2025-02-28T23:00:00Z"),
    ])
    df = pd.DataFrame(
        {"open": [1.0, 1.0], "high": [1.0, 1.0], "low": [1.0, 1.0],
         "close": [1.0, 1.0], "volume": [1.0, 1.0]},
        index=index,
    )

    class Manifest:
        checksum_sha256 = f006_family_runner.EXPECTED_CHECKSUMS[(symbol, interval)]

    def fake_load_dataset(cache_dir, got_symbol, got_interval, start, end):
        requested.update(cache_dir=cache_dir, symbol=got_symbol, interval=got_interval,
                         start=start, end=end)
        return df, Manifest()

    monkeypatch.setattr(f006_family_runner.data_contract, "load_dataset", fake_load_dataset)
    train1_df, _manifest = f006_family_runner.load_train1(symbol, interval)

    assert requested == {
        "cache_dir": "data_cache", "symbol": symbol, "interval": interval,
        "start": f006_family_runner.WARMUP_START, "end": f006_family_runner.TRAIN1_END,
    }
    assert train1_df.index.max() < f006_family_runner.TRAIN1_END
