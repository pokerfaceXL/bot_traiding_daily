"""
The NO_TRAIL control spec/research/F006-hypothesis-trailing-boundary.md uses: setting
activate_pct so high the trail can never arm, so exits come only from initial_sl,
signal_reverse or end_of_data. No engine change -- this pins that the existing
activate_pct parameter, used outside its normal range, actually produces that behaviour
on both a synthetic fixture and a real Train-1 slice.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import data_contract

OHLCV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")
NO_TRAIL_ACTIVATE = 10.0


def _fixture_frame():
    df = pd.read_csv(OHLCV, parse_dates=["timestamp"], index_col="timestamp")
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


def test_no_trail_produces_zero_trailing_exits_on_fixture():
    df = _fixture_frame()
    result = be.run_backtest(
        df, "EMA_8_21", interval="240", now=df.index[-1] + pd.Timedelta(hours=4),
        initial_equity=500.0, stake=100.0, leverage=1.0, max_sl_pct=0.03,
        activate_pct=NO_TRAIL_ACTIVATE, trail_pct=0.04,
        commission_rate_bps=10.0, half_spread_bps=5.0, slippage_bps=2.0,
    )
    trades = result.trades
    assert len(trades) > 0, "fixture must produce at least one trade for this test to mean anything"
    assert (trades["exit_reason"] != "trailing_sl").all()


def test_no_trail_produces_zero_trailing_exits_on_real_data():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data_cache")
    if not os.path.isdir(path):
        pytest.skip("data_cache not present in this worktree")
    try:
        full_df, _ = data_contract.load_dataset(
            "data_cache", "BTCUSDT", "60", "2024-01-26T00:00:00Z", "2026-09-01T00:00:00Z")
    except data_contract.DataContractError:
        pytest.skip("BTCUSDT/60 not cached in this worktree")
    idx = pd.DatetimeIndex(full_df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    train1_end = pd.Timestamp("2025-03-01T00:00:00Z")
    df = full_df.loc[idx < train1_end]
    result = be.run_backtest(
        df, "EMA_8_21", interval="60", now=train1_end,
        initial_equity=500.0, stake=100.0, leverage=1.0, max_sl_pct=0.03,
        activate_pct=NO_TRAIL_ACTIVATE, trail_pct=0.04,
        commission_rate_bps=10.0, half_spread_bps=5.0, slippage_bps=2.0,
    )
    trades = result.trades
    assert len(trades) > 0
    assert (trades["exit_reason"] != "trailing_sl").all()
