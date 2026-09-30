"""Unit contract for the pre-registered causal range-EQH/EQL family."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine
import liq_range_eqh
import strategy


def _frame(highs, lows=None):
    lows = lows or [h - 2 for h in highs]
    idx = pd.date_range("2024-01-01", periods=len(highs), freq="h", tz="UTC")
    return pd.DataFrame({"open": np.asarray(highs) - .5, "high": highs, "low": lows,
                         "close": np.asarray(highs) - 1, "volume": 1.0}, index=idx)


def test_pivot_is_not_known_until_the_confirmation_lag_not_a_centered_window():
    # The high at pivot 3 is visibly the local maximum after bar 4, but L=2 must
    # not reveal it until bar 5. A centered implementation would reveal it early.
    df = _frame([8, 9, 10, 15, 11, 10, 9, 8])
    highs, lows = liq_range_eqh.confirmed_pivots(df, lag=2)
    assert not highs.iloc[:5].any()
    assert highs.iloc[5]
    assert not lows.iloc[:5].any()


def test_confirmed_pivots_are_prefix_invariant():
    df = _frame([8, 9, 10, 15, 11, 10, 9, 8, 7, 9, 10])
    full_high, full_low = liq_range_eqh.confirmed_pivots(df, lag=2)
    short_high, short_low = liq_range_eqh.confirmed_pivots(df.iloc[:8], lag=2)
    assert short_high.tolist() == full_high.iloc[:8].tolist()
    assert short_low.tolist() == full_low.iloc[:8].tolist()


def test_pool_accepts_a_pairwise_valid_subset_not_only_an_all_candidate_clique():
    # [-.8, 0, .8] is a chain: both adjacent pairs satisfy EPS=1, while no
    # member satisfies the old (incorrect) all-candidate-clique condition.
    pivots = [(1, -.8), (2, 0.0), (3, .8)]
    assert liq_range_eqh._pool_level(pivots, edge=0, atr=1, eps=1, high_side=True) == .8
    assert liq_range_eqh._pool_level(pivots, edge=0, atr=1, eps=1, high_side=False) == -.8


def test_catalog_is_exactly_the_five_frozen_names_and_signal_domain():
    expected = {"RANGE_EQH_RECLAIM_L2", "RANGE_EQH_RECLAIM_L3", "RANGE_EQH_RECLAIM_WIDE",
                "RANGE_EQH_RECLAIM_TIGHT", "RANGE_EQH_RECLAIM_WICK"}
    assert set(liq_range_eqh.catalog_entries()) == expected
    df = _frame(list(range(100, 140)) + list(range(140, 100, -1)))
    for fn in liq_range_eqh.catalog_entries().values():
        signal = fn(df)
        assert signal.index.equals(df.index)
        assert signal.isin([-1, 0, 1]).all()


def test_engine_fills_a_family_decision_at_next_bar_open(monkeypatch):
    # Isolate the execution timing contract with the real engine: a decision at i
    # from this family can only become an entry at i+1's open, never i's close.
    df = _frame([100 + i for i in range(40)])
    name = "RANGE_EQH_TIMING_TEST"
    decision_i = 20
    def signal(work):
        out = pd.Series(0, index=work.index)
        out.iloc[decision_i] = 1
        return out
    monkeypatch.setitem(strategy.STRATEGY_CATALOG, name, signal)
    result = backtest_engine.run_backtest(
        df, name, interval="60", now=df.index[-1] + pd.Timedelta(hours=1),
        leverage=1.0, max_sl_pct=.03, activate_pct=10.0,
        entry_regime_mask=pd.Series([False] * decision_i + [True] + [False] * (len(df)-decision_i-1), index=df.index),
    )
    assert len(result.trades) == 1
    assert pd.Timestamp(result.trades.iloc[0].entry_time) == df.index[decision_i + 1]
    assert result.trades.iloc[0].entry_price == df.iloc[decision_i + 1].open
