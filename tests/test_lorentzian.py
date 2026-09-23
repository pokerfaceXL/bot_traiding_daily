"""
Regression tests for the F006 Lorentzian adapter (lorentzian.py).

The load-bearing test here is test_signal_at_bar_i_is_unchanged_by_future_bars:
advanced-ta 0.1.8, used the way its README documents it, fails exactly this check
(its MinMaxScaler feature normalisation is fit on the whole frame, and its ML
window start is len(df) - maxBarsBack), so "it runs" would prove nothing. See
spec/research/F006-lorentzian-causality.md.

Tests that need advanced-ta itself are skipped when it cannot be imported --
the package declares Requires-Python >=3.10 and uses match/case, so it does not
import at all on the project's current Python 3.9 test venv. The causality
property of the adapter's own normalisation, and the catalog wiring, are tested
unconditionally.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import lorentzian
import strategy

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")
TAIL = 50          # bars appended in the truncation test
PREFIX = 500       # bars of the 600-bar fixture used as "the series so far"

advanced_ta_missing = False
try:
    lorentzian._advanced_ta()
except lorentzian.LorentzianUnavailable:
    advanced_ta_missing = True

needs_advanced_ta = pytest.mark.skipif(
    advanced_ta_missing,
    reason="advanced-ta 0.1.8 not importable here (needs Python >= 3.10)",
)


def _fixture():
    return pd.read_csv(FIXTURE, index_col=0, parse_dates=True)


# ── catalog wiring (no advanced-ta needed) ────────────────────────────────

def test_catalog_gained_lorentzian_entries_without_touching_existing_ones():
    assert "LORENTZIAN_default" in strategy.STRATEGY_CATALOG
    assert "LORENTZIAN_raw" in strategy.STRATEGY_CATALOG
    # existing entries still present and still callables taking one frame
    for name in ("EMA_8_21", "RSI14_7030", "BB_20_25_breakout", "TS_13_34_200_14"):
        assert callable(strategy.STRATEGY_CATALOG[name])


def test_missing_advanced_ta_fails_loudly_and_only_when_computing():
    """Importing lorentzian.py must stay safe on Python 3.9; only computing may raise."""
    if not advanced_ta_missing:
        pytest.skip("advanced-ta is importable in this interpreter")
    with pytest.raises(lorentzian.LorentzianUnavailable) as exc:
        lorentzian.compute_lorentzian(_fixture())
    assert "3.10" in str(exc.value)


def test_expanding_normalize_is_causal_and_matches_minmax_on_the_prefix():
    rng = np.random.default_rng(20260923)
    x = rng.normal(size=300).cumsum()
    full = lorentzian._expanding_normalize(x)
    for n in (120, 200, 299):
        assert np.allclose(lorentzian._expanding_normalize(x[:n]), full[:n], rtol=0, atol=0)
        # at the last bar of a prefix it must equal the plain min-max of that prefix
        lo, hi = x[:n].min(), x[:n].max()
        assert full[n - 1] == pytest.approx((x[n - 1] - lo) / (hi - lo))


# ── causality of the signal itself ────────────────────────────────────────

@needs_advanced_ta
def test_signal_at_bar_i_is_unchanged_by_future_bars():
    df = _fixture()
    short = lorentzian.compute_lorentzian(df.iloc[:PREFIX])
    long = lorentzian.compute_lorentzian(df.iloc[: PREFIX + TAIL])

    assert len(short) == PREFIX and len(long) == PREFIX + TAIL
    for column in ("prediction", "signal", "raw_signal", "filter_all"):
        a = short[column].to_numpy()
        b = long[column].to_numpy()[:PREFIX]
        changed = int((a != b).sum())
        assert changed == 0, f"{column}: {changed}/{PREFIX} bars moved when {TAIL} future bars were appended"


@needs_advanced_ta
def test_documented_library_usage_fails_the_same_check():
    """Guard on the audit's premise: if a future advanced-ta release became causal
    on its own, the adapter's reframing would need revisiting rather than silently
    staying in place. Documents the leak, it does not bless it."""
    from advanced_ta import LorentzianClassification

    df = _fixture()[["open", "high", "low", "close", "volume"]].astype(float)
    short = LorentzianClassification(df.iloc[:PREFIX]).data
    long = LorentzianClassification(df.iloc[: PREFIX + TAIL]).data
    moved = int((short["prediction"].to_numpy() != long["prediction"].to_numpy()[:PREFIX]).sum())
    assert moved > 0, (
        "advanced-ta's documented batch usage no longer repaints past bars -- re-read "
        "spec/research/F006-lorentzian-causality.md before trusting this adapter's reframing"
    )


@needs_advanced_ta
def test_signal_is_a_plain_state_series_in_minus_one_zero_plus_one():
    frame = lorentzian.compute_lorentzian(_fixture().iloc[:PREFIX])
    assert set(np.unique(frame["signal"])) <= {-1, 0, 1}
    assert set(np.unique(frame["raw_signal"])) <= {-1, 0, 1}
    assert frame.index.equals(_fixture().iloc[:PREFIX].index)


# ── engine call contract ──────────────────────────────────────────────────

@needs_advanced_ta
def test_run_backtest_accepts_the_new_entry_exactly_like_an_existing_one():
    df = _fixture()
    result = be.run_backtest(df, "LORENTZIAN_default", interval="240",
                             now=pd.Timestamp("2024-04-01T00:00:00Z"), leverage=1.0)
    baseline = be.run_backtest(df, "RSI14_7030", interval="240",
                               now=pd.Timestamp("2024-04-01T00:00:00Z"), leverage=1.0)
    assert set(result.metrics.keys()) == set(baseline.metrics.keys())
    assert len(result.equity_curve) == len(baseline.equity_curve)
    assert result.metrics["n_trades"] >= 0
