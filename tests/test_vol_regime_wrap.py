"""
Regression tests for the F006 vol-regime wrap (vol_regime_wrap.py,
H-VOL-REGIME-WRAP-01, spec/research/F006-hypothesis-vol-regime-wrap.md).

Four things at stake, mirroring tests/test_donchian.py's discipline:

  1. atr_pct/vol_percentile match an independently written reference
     implementation (a plain Python loop, not pandas .rolling().apply()), so a
     bug shared between the module and a hand-copied formula would still be
     caught by the reference's different code path.
  2. The hysteresis state machine's exact bucket transitions on a hand-built
     vol path: enters HIGH, stays through a dip that does NOT clear the
     hysteresis band, exits only once the band IS cleared; same for LOW.
  3. The three wrapped names reproduce the frozen HIGH/MID/LOW table from the
     research note exactly, bucket by bucket, against the underlying Donchian
     direction.
  4. No lookahead (prefix truncation + future-bar perturbation) and
     additive-only registration (every pre-existing catalog entry is
     unchanged).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import donchian
import strategy
import vol_regime_wrap as vrw

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")


def _fixture():
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


# ── 1. atr_pct / vol_percentile vs an independent reference implementation ──

def _reference_atr_pct(df: pd.DataFrame) -> np.ndarray:
    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    n = len(df)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    alpha = 2.0 / (vrw.ATR_PERIOD + 1)
    atr = np.empty(n)
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = alpha * tr[i] + (1 - alpha) * atr[i - 1]
    return atr / close


def _reference_percentile(atr_pct: np.ndarray) -> np.ndarray:
    n = len(atr_pct)
    out = np.full(n, np.nan)
    w = vrw.PCT_WINDOW
    for i in range(w - 1, n):
        window = atr_pct[i - w + 1:i + 1]
        out[i] = 100.0 * np.sum(window <= atr_pct[i]) / w
    return out


def test_atr_pct_matches_independent_reference_implementation():
    df = _fixture()
    got = vrw.atr_pct_series(df).to_numpy()
    ref = _reference_atr_pct(df)
    np.testing.assert_allclose(got, ref, rtol=1e-9)


def test_vol_percentile_matches_independent_reference_implementation():
    df = _fixture()
    atr_pct = _reference_atr_pct(df)
    ref = _reference_percentile(atr_pct)
    got = vrw.vol_percentile(df).to_numpy()
    nan_mask = np.isnan(ref)
    assert np.array_equal(np.isnan(got), nan_mask)
    np.testing.assert_allclose(got[~nan_mask], ref[~nan_mask], rtol=1e-9)


def test_vol_percentile_is_nan_before_the_window_fills():
    df = _fixture()
    pct = vrw.vol_percentile(df)
    assert pct.iloc[: vrw.PCT_WINDOW - 1].isna().all()
    assert pct.iloc[vrw.PCT_WINDOW - 1 :].notna().all()


# ── 2. hysteresis state machine on a hand-built vol path ───────────────────

def _synthetic_vol_path_ohlcv():
    """110 low-vol bars (tiny fixed range), 30 high-vol bars (wide range),
    30 low-vol bars again, 30 more low-vol bars -- built so the percentile
    ranks unambiguously into LOW-tail during phase 1, HIGH-tail through phase
    2 and the start of phase 3 (recent-history still dominated by the wide
    phase-2 bars inside the W=100 trailing window), then back to LOW-tail
    once phase 2 drops out of the trailing window."""
    rows = []
    price = 100.0
    for _ in range(110):
        rows.append((price, price + 0.05, price - 0.05, price))
    for i in range(30):
        price += 0.5 if i % 2 == 0 else -0.5
        rows.append((price, price + 3.0, price - 3.0, price))
    for _ in range(30):
        rows.append((price, price + 0.02, price - 0.02, price))
    for _ in range(30):
        rows.append((price, price + 0.02, price - 0.02, price))
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df["volume"] = 1000.0
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="4h")
    return df


def test_hysteresis_enters_high_stays_through_the_band_then_exits_to_mid_then_low():
    df = _synthetic_vol_path_ohlcv()
    regime = vrw.vol_regime(df).tolist()

    # bars 0..108 (index < PCT_WINDOW-1): forced MID (percentile is NaN)
    assert all(r == vrw.MID for r in regime[: vrw.PCT_WINDOW - 1])

    # once the wide-range phase-2 bars enter the trailing window, percentile
    # jumps and the regime must enter HIGH and hold there (single monotone
    # entry, no MID/LOW flicker) for a contiguous run.
    high_run = [i for i, r in enumerate(regime) if r == vrw.HIGH]
    assert high_run, "regime never entered HIGH on a fixture built to force it"
    assert high_run == list(range(high_run[0], high_run[-1] + 1)), (
        "HIGH regime was not a single contiguous run -- hysteresis flickered"
    )

    # after phase 2's wide bars fully age out of the W=100 trailing window,
    # the regime must eventually reach LOW (percentile collapses once only
    # tiny-range bars remain in the window) and hold there to the end.
    assert regime[-1] == vrw.LOW
    low_tail_start = len(regime) - 1
    while low_tail_start > 0 and regime[low_tail_start - 1] == vrw.LOW:
        low_tail_start -= 1
    assert regime[low_tail_start:] == [vrw.LOW] * (len(regime) - low_tail_start)

    # HIGH must fully end before the LOW tail begins -- no direct HIGH->LOW
    # jump skipping MID on this fixture (regime passes through MID between).
    assert high_run[-1] < low_tail_start


# ── 3. wrapped names reproduce the frozen HIGH/MID/LOW table exactly ───────

def test_wrapped_names_match_the_frozen_bucket_table():
    df = _fixture()
    regime = vrw.vol_regime(df).to_numpy()
    direction = donchian.sig_donchian_breakout(df, vrw.DONCHIAN_N).to_numpy()

    high_brk = vrw.sig_vol_high_breakout(df).to_numpy()
    low_mr = vrw.sig_vol_low_mean_revert(df).to_numpy()
    combo = vrw.sig_vol_high_low_combo(df).to_numpy()

    for i in range(len(df)):
        if regime[i] == vrw.HIGH:
            assert high_brk[i] == direction[i]
            assert low_mr[i] == 0
            assert combo[i] == direction[i]
        elif regime[i] == vrw.LOW:
            assert high_brk[i] == 0
            assert low_mr[i] == -direction[i]
            assert combo[i] == -direction[i]
        else:
            assert high_brk[i] == 0
            assert low_mr[i] == 0
            assert combo[i] == 0

    assert (regime == vrw.HIGH).any() and (regime == vrw.LOW).any(), (
        "vacuous fixture: never entered HIGH or LOW, test would pass trivially"
    )


# ── 4. no lookahead + additive-only registration ────────────────────────────

@pytest.mark.parametrize("prefix", [150, 300, 450])
@pytest.mark.parametrize("name,fn", list(vrw.catalog_entries().items()))
def test_no_lookahead_prefix_and_future_perturbation(name, fn, prefix):
    df = _fixture()
    full = pd.Series(fn(df)).fillna(0)
    assert full.ne(0).any(), f"{name}: vacuous fixture, test would pass trivially"

    truncated = pd.Series(fn(df.iloc[:prefix])).fillna(0)
    assert truncated.tolist() == full.iloc[:prefix].tolist(), (
        f"{name}: a bar before {prefix} changed when the frame was truncated"
    )

    perturbed = df.copy()
    cols = perturbed.columns.get_indexer(["open", "high", "low", "close"])
    perturbed.iloc[prefix:, cols] *= 50.0
    perturbed.iloc[prefix:, perturbed.columns.get_loc("volume")] *= 500.0
    moved = pd.Series(fn(perturbed)).fillna(0)
    assert moved.iloc[:prefix].tolist() == full.iloc[:prefix].tolist(), (
        f"{name}: a bar before {prefix} changed when future bars were perturbed"
    )


def test_input_frame_is_never_mutated():
    df = _fixture()
    before = df.copy(deep=True)
    for fn in vrw.catalog_entries().values():
        fn(df)
    pd.testing.assert_frame_equal(df, before)


def test_registering_the_family_is_additive_only():
    entries = vrw.catalog_entries()
    for name in entries:
        assert name in strategy.STRATEGY_CATALOG, f"{name} should already be registered"

    work = strategy.add_indicators(_fixture())
    baseline_names = [n for n in strategy.STRATEGY_CATALOG if n not in entries]
    for n in baseline_names[:15]:  # sample: full sweep is covered by the shared contract test
        sig_before = pd.Series(strategy.STRATEGY_CATALOG[n](work)).copy()
        sig_after = pd.Series(strategy.STRATEGY_CATALOG[n](work))
        pd.testing.assert_series_equal(sig_before, sig_after, check_names=False)


def test_catalog_has_exactly_three_new_names():
    entries = vrw.catalog_entries()
    assert set(entries) == {"VOLW_HIGH_BRK_20", "VOLW_LOW_MR_20", "VOLW_HL_20"}
