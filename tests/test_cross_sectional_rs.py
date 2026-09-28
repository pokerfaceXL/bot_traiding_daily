"""
Regression tests for the F006 cross-sectional relative-strength family
(cross_sectional_rs.py).

What's actually at stake:

  1. Rank correctness. A hand-built 5-symbol close fixture where the ranking is
     obvious by construction (monotone symbols) must produce the exact +1/-1/0
     pattern the rule describes, not "runs without error".
  2. Causality / warm-up. Bars before `lookback` bars of history exist must rank
     nobody (0 for all 5), not silently rank on a partial/NaN return.
  3. Missing-peer-bar handling. A timestamp present on only 4 of 5 symbols must be
     dropped for ALL FIVE, not forward-filled or ranked on 4.
  4. TOP_K=2 covers two longs and two shorts (and leaves exactly one flat, the
     middle rank).
  5. The additive-only guarantee: the 83 pre-existing catalog entries (79 F005 +
     4 Donchian; LORENTZIAN_* excluded, same as tests/test_donchian.py, since
     advanced-ta is not importable on this test interpreter) must produce
     bit-identical signals to the commit before cross_sectional_rs.py was wired in.
  6. The peer-aware plumbing itself: a XS_RS_* catalog entry called with no active
     context (or a context nothing was registered for) must raise, not return zeros.
"""
import hashlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import cross_sectional_rs as xsrs
import entry_masks
import strategy

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")
PRE_XSRS_FINGERPRINTS = os.path.join(FIXTURES, "catalog_fingerprints_pre_cross_sectional_rs.json")


def _ohlcv():
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


@pytest.fixture(autouse=True)
def _clear_context():
    xsrs.set_active_context(None, None)
    yield
    xsrs.set_active_context(None, None)


def _closes(idx, **series_by_symbol):
    return {sym: pd.Series(vals, index=idx, dtype=float) for sym, vals in series_by_symbol.items()}


# ── rank math ──────────────────────────────────────────────────────────────

def test_known_top_and_bottom_ranks_go_long_and_short():
    idx = pd.date_range("2024-01-01", periods=4, freq="4h", tz="UTC")
    closes = _closes(
        idx,
        SOLUSDT=[100, 101, 102, 103],   # strongest -> rank 1
        ETHUSDT=[100, 100, 100, 100],   # flat -> middle
        BTCUSDT=[100, 99, 98, 97],      # weakest -> rank 5
        XRPUSDT=[100, 100.5, 101, 101.5],
        DOGEUSDT=[100, 99.5, 99, 98.5],
    )
    out = xsrs.compute_basket_signals(closes, lookback=1, top_k=1)
    # bar 0: no lookback=1 history yet -> flat for everyone
    for s in xsrs.BASKET:
        assert out[s].iloc[0] == 0
    # bar 3 (fully warmed up): SOL strongest -> +1, BTC weakest -> -1, rest 0
    assert out["SOLUSDT"].iloc[3] == 1
    assert out["BTCUSDT"].iloc[3] == -1
    assert out["ETHUSDT"].iloc[3] == 0
    assert out["XRPUSDT"].iloc[3] == 0
    assert out["DOGEUSDT"].iloc[3] == 0


def test_missing_peer_bar_drops_the_timestamp_for_all_five():
    idx_full = pd.date_range("2024-01-01", periods=5, freq="4h", tz="UTC")
    idx_missing_one = idx_full.delete(2)  # SOLUSDT is missing bar index 2
    closes = {
        "SOLUSDT": pd.Series([100, 101, 104, 105.0], index=idx_missing_one),
        "ETHUSDT": pd.Series([100, 100, 100, 100, 100.0], index=idx_full),
        "BTCUSDT": pd.Series([100, 99, 98, 97, 96.0], index=idx_full),
        "XRPUSDT": pd.Series([100, 100.5, 101, 101.5, 102.0], index=idx_full),
        "DOGEUSDT": pd.Series([100, 99.5, 99, 98.5, 98.0], index=idx_full),
    }
    out = xsrs.compute_basket_signals(closes, lookback=1, top_k=1)
    # ETHUSDT's own index still has 5 bars (its input index is preserved on output)
    assert len(out["ETHUSDT"]) == 5
    # the timestamp SOLUSDT lacked must be flat for the 4 peers that DO still have
    # it in their own index (it's absent from SOLUSDT's own output entirely, since
    # each symbol's output is reindexed onto that symbol's own input index)
    missing_ts = idx_full[2]
    assert missing_ts not in out["SOLUSDT"].index
    for s in ("ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"):
        assert out[s].loc[missing_ts] == 0
    # a bar present on all five (e.g. the last one) still ranks normally
    last_ts = idx_full[4]
    assert out["SOLUSDT"].loc[last_ts] == 1  # SOL still strongest there
    assert out["BTCUSDT"].loc[last_ts] == -1


def test_lookback_warmup_is_flat_for_everyone():
    idx = pd.date_range("2024-01-01", periods=10, freq="4h", tz="UTC")
    closes = _closes(
        idx,
        SOLUSDT=[100 + i for i in range(10)],
        ETHUSDT=[100.0] * 10,
        BTCUSDT=[100 - i for i in range(10)],
        XRPUSDT=[100 + 0.5 * i for i in range(10)],
        DOGEUSDT=[100 - 0.5 * i for i in range(10)],
    )
    lookback = 5
    out = xsrs.compute_basket_signals(closes, lookback=lookback, top_k=1)
    for s in xsrs.BASKET:
        assert (out[s].iloc[:lookback] == 0).all()
    # first bar with a defined lookback return ranks normally
    assert out["SOLUSDT"].iloc[lookback] == 1
    assert out["BTCUSDT"].iloc[lookback] == -1


def test_top_k_2_covers_two_longs_two_shorts_one_flat():
    idx = pd.date_range("2024-01-01", periods=2, freq="4h", tz="UTC")
    closes = _closes(
        idx,
        SOLUSDT=[100, 105],   # rank 1
        ETHUSDT=[100, 103],   # rank 2
        BTCUSDT=[100, 100],   # rank 3 (middle) -> flat
        XRPUSDT=[100, 98],    # rank 4
        DOGEUSDT=[100, 95],   # rank 5
    )
    out = xsrs.compute_basket_signals(closes, lookback=1, top_k=2)
    assert out["SOLUSDT"].iloc[1] == 1
    assert out["ETHUSDT"].iloc[1] == 1
    assert out["BTCUSDT"].iloc[1] == 0
    assert out["XRPUSDT"].iloc[1] == -1
    assert out["DOGEUSDT"].iloc[1] == -1
    n_long = sum(out[s].iloc[1] == 1 for s in xsrs.BASKET)
    n_short = sum(out[s].iloc[1] == -1 for s in xsrs.BASKET)
    n_flat = sum(out[s].iloc[1] == 0 for s in xsrs.BASKET)
    assert (n_long, n_short, n_flat) == (2, 2, 1)


def test_rejects_a_basket_that_is_not_exactly_the_five_symbols():
    idx = pd.date_range("2024-01-01", periods=2, freq="4h", tz="UTC")
    closes = _closes(idx, SOLUSDT=[100, 101], ETHUSDT=[100, 100])
    with pytest.raises(ValueError):
        xsrs.compute_basket_signals(closes, lookback=1, top_k=1)


# ── engine wiring / additive guarantee ──────────────────────────────────────

def test_catalog_gained_five_xs_rs_entries_and_left_the_other_83_bit_identical():
    for name in xsrs.NAME_GRID:
        assert callable(strategy.STRATEGY_CATALOG[name])
    # 79 F005 baseline + 2 Lorentzian (F006) + 4 Donchian (F006) + 3 vol-regime-wrap
    # (F006, merged earlier) + 5 XS_RS (this slice)
    assert len(strategy.STRATEGY_CATALOG) == 93

    with open(PRE_XSRS_FINGERPRINTS) as f:
        expected = json.load(f)
    assert len(expected) == 83
    work = strategy.add_indicators(_ohlcv())
    for name, digest in sorted(expected.items()):
        sig = pd.Series(strategy.STRATEGY_CATALOG[name](work)).fillna(0).astype(int)
        got = hashlib.sha256(sig.to_numpy().tobytes()).hexdigest()[:16]
        assert got == digest, f"{name} changed: {got} != {digest}"


def test_catalog_entry_raises_without_active_context_instead_of_returning_zeros():
    work = strategy.add_indicators(_ohlcv())
    with pytest.raises(RuntimeError):
        strategy.STRATEGY_CATALOG["XS_RS_20_TOP1"](work)


def test_catalog_entry_raises_for_an_unregistered_symbol_interval():
    work = strategy.add_indicators(_ohlcv())
    xsrs.set_active_context("SOLUSDT", "240")
    with pytest.raises(RuntimeError):
        strategy.STRATEGY_CATALOG["XS_RS_20_TOP1"](work)


def test_catalog_entry_returns_the_registered_series_for_the_active_context():
    idx = pd.date_range("2024-01-01", periods=3, freq="4h", tz="UTC")
    fake_signal = pd.Series([0, 1, -1], index=idx)
    xsrs.register_signals(
        "XS_RS_20_TOP1", "240",
        {sym: fake_signal if sym == "SOLUSDT" else pd.Series([0, 0, 0], index=idx) for sym in xsrs.BASKET},
    )
    xsrs.set_active_context("SOLUSDT", "240")
    fake_df = pd.DataFrame({"close": [1, 2, 3]}, index=idx)
    got = strategy.STRATEGY_CATALOG["XS_RS_20_TOP1"](fake_df)
    assert got.tolist() == [0, 1, -1]


def test_xs_rs_runs_through_the_engine_with_the_one_shot_mask():
    """End-to-end on the path the experiment uses: signal -> entry_masks -> engine."""
    df = _ohlcv()
    idx = df.index
    if pd.DatetimeIndex(idx).tz is None:
        idx = pd.DatetimeIndex(idx).tz_localize("UTC")
        df = df.set_axis(idx)
    closes = {
        "SOLUSDT": df["close"],
        "ETHUSDT": df["close"] * 1.01,
        "BTCUSDT": df["close"] * 0.99,
        "XRPUSDT": df["close"].shift(1).fillna(df["close"].iloc[0]),
        "DOGEUSDT": df["close"].shift(-1).ffill(),
    }
    signals = xsrs.compute_basket_signals(closes, lookback=20, top_k=1)
    xsrs.register_signals("XS_RS_20_TOP1", "240", signals)
    xsrs.set_active_context("SOLUSDT", "240")

    sig = entry_masks.strategy_signal_series(df, "XS_RS_20_TOP1", interval="240")
    mask = entry_masks.one_shot_entry_mask(sig)
    masked = be.run_backtest(df, "XS_RS_20_TOP1", interval="240", entry_regime_mask=mask)
    assert masked.metrics["n_trades"] <= int(mask.sum())
    assert sig.index.equals(masked.equity_curve.index)
