"""
F004 wave 5 integration test: backtest_apex.py's DEFAULT (non --param-optimization)
path must actually run through backtest_engine.run_backtest (cost/equity-aware),
not silently still call the old cost-free strategy.backtest_trailing.

This is the discriminating check named in the ticket: it is not enough for the
new engine's total_pnl to be merely "different" from the old free calculation --
it must be lower by a verifiable, non-zero cost amount, reconciled exactly
against the same trades' own recorded total_costs.
"""

import runpy
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "ohlcv_sample.csv"

sys.path.insert(0, str(REPO_ROOT))
import backtest_engine as be  # noqa: E402
import strategy  # noqa: E402

STRATEGY_NAME = "RSI14_7030"

# Same defaults backtest_apex.py reads from configuration/default.yaml.
LEVERAGE = 10
ATR_MULT = 2.5
MAX_SL_PCT = 0.03
ACTIVATE_PCT = 0.03
TRAIL_PCT = 0.015
COOLDOWN_CANDLES = 0
POSITION_SIZE_USDT = 100.0
ENTRY_ON_OPEN = False  # configuration/default.yaml's ENTRY_ON_OPEN: false
INTERVAL = "240"


def _block_network(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("Nieoczekiwane polaczenie sieciowe w trybie offline")
    monkeypatch.setattr(requests, "get", _raise)
    monkeypatch.setattr(requests, "post", _raise)


def _run_backtest_apex(tmp_path, monkeypatch, csv_path):
    """Same pattern as tests/test_offline_backtest.py: run backtest_apex.py as a
    standalone script (runpy, run_name="__main__") against a local CSV, offline."""
    (tmp_path / "configuration").mkdir()
    shutil.copy(REPO_ROOT / "configuration" / "default.yaml", tmp_path / "configuration" / "default.yaml")

    argv = [
        "backtest_apex.py",
        "configuration/default.yaml",
        "--local-csv", str(csv_path),
        "--strategies", STRATEGY_NAME,
    ]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.chdir(tmp_path)
    runpy.run_path(str(REPO_ROOT / "backtest_apex.py"), run_name="__main__")


def _load_fixture_df_ind():
    df_raw = pd.read_csv(FIXTURE, parse_dates=["timestamp"], index_col="timestamp")
    df_raw = df_raw[["open", "high", "low", "close", "volume"]].astype(float)
    df_raw = df_raw[~df_raw.index.duplicated(keep="last")].sort_index()
    return df_raw, strategy.add_indicators(df_raw.copy())


def test_apex_default_path_uses_cost_aware_engine_not_free_legacy_one(tmp_path, monkeypatch):
    _block_network(monkeypatch)
    _run_backtest_apex(tmp_path, monkeypatch, FIXTURE)

    report_paths = list((tmp_path / "output" / "backtests").glob("*/report.json"))
    assert len(report_paths) == 1
    import json
    report = json.loads(report_paths[0].read_text())
    summary = report["summary"]
    assert summary["best_strategy"] == STRATEGY_NAME
    apex_pnl = summary["best_pnl"]
    apex_n_trades = summary["best_n_trades"]

    # --- Reference 1: call backtest_engine.run_backtest directly with the exact
    # same parameters backtest_apex.py's non-optimization branch now passes. If
    # apex is really wired to this engine, the numbers must match closely (same
    # code path, same inputs) -- not just be "in the same ballpark".
    df_raw, df_ind = _load_fixture_df_ind()
    direct_real_costs = be.run_backtest(
        df_ind, STRATEGY_NAME, interval=INTERVAL,
        initial_equity=500.0, stake=POSITION_SIZE_USDT, leverage=LEVERAGE,
        atr_multiplier=ATR_MULT, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN_CANDLES,
    )
    assert direct_real_costs.metrics["n_trades"] == apex_n_trades
    assert direct_real_costs.metrics["total_net_pnl"] == pytest.approx(apex_pnl, abs=0.01)

    # --- Reference 2: the SAME run with all cost params forced to zero. Entry/exit
    # timing in backtest_engine.run_backtest does not depend on cost params at all
    # (costs are only applied at Portfolio.close_position, after the fill price and
    # timing are already decided) -- so this must produce the IDENTICAL trade
    # sequence, differing only in net_pnl by exactly the omitted costs.
    direct_zero_costs = be.run_backtest(
        df_ind, STRATEGY_NAME, interval=INTERVAL,
        initial_equity=500.0, stake=POSITION_SIZE_USDT, leverage=LEVERAGE,
        atr_multiplier=ATR_MULT, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        cooldown_candles=COOLDOWN_CANDLES,
        commission_rate_bps=0.0, half_spread_bps=0.0, slippage_bps=0.0, slippage_fixed=0.0,
    )
    assert direct_zero_costs.metrics["n_trades"] == direct_real_costs.metrics["n_trades"]
    assert (direct_zero_costs.trades["entry_time"].to_numpy() == direct_real_costs.trades["entry_time"].to_numpy()).all()
    assert (direct_zero_costs.trades["exit_time"].to_numpy() == direct_real_costs.trades["exit_time"].to_numpy()).all()

    total_costs_sum = float(direct_real_costs.trades["total_costs"].sum())
    assert total_costs_sum > 0.0  # non-zero: real trades really did incur commission/spread/slippage
    pnl_gap = direct_zero_costs.metrics["total_net_pnl"] - direct_real_costs.metrics["total_net_pnl"]
    # No funding events were passed (funding_pnl == 0 for every trade), so the
    # entire zero-cost-vs-real-cost pnl gap must reconcile exactly to the sum of
    # the recorded per-trade total_costs -- not just be "some smaller number".
    assert (direct_real_costs.trades["funding_pnl"] == 0.0).all()
    assert pnl_gap == pytest.approx(total_costs_sum, rel=1e-6)

    # --- Reference 3 (the literal ticket comparison): the OLD free engine,
    # strategy.backtest_trailing, called the same way backtest_apex.py used to
    # call it before this wave (same config-driven params, same degenerate
    # offline sub_lookup). apex's cost-aware PnL must be strictly lower than
    # what the old free calculation would have produced for the same data.
    sub_lookup = strategy._build_sub_lookup(df_raw, int(INTERVAL))
    df_with_signal = df_ind.copy()
    df_with_signal["signal"] = strategy.STRATEGY_CATALOG[STRATEGY_NAME](df_with_signal)
    _legacy_trades, legacy_metrics = strategy.backtest_trailing(
        df_with_signal,
        atr_multiplier=ATR_MULT, max_sl_pct=MAX_SL_PCT, activate_pct=ACTIVATE_PCT,
        trail_pct=TRAIL_PCT, leverage=LEVERAGE, stake=POSITION_SIZE_USDT,
        atr_col="atr14", entry_on_open=ENTRY_ON_OPEN, cooldown_candles=COOLDOWN_CANDLES,
        sub_lookup=sub_lookup, main_interval_min=int(INTERVAL),
    )
    legacy_free_pnl = legacy_metrics["total_pnl"]
    assert apex_pnl < legacy_free_pnl
    assert (legacy_free_pnl - apex_pnl) > 1.0  # not a rounding-noise-sized gap
