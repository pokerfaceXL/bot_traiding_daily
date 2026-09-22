import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import costs
import equity as equity_module
import backtest_engine as be

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")

# Strategy choice: RSI14_7030 (sig_rsi_extreme, strategy.py) is picked over an
# always-in-market strategy like EMA_8_21 because it is a pure function of a
# single already-tested indicator column (rsi14) and, unlike EMA cross, is 0
# (flat) almost everywhere -- signals only fire on RSI extremes. That keeps
# the resulting trade count small enough (17 over 600 bars on the fixture)
# that a single trade can be picked out and hand-verified end-to-end, and
# keeps the no-overlap check in test (b) meaningful rather than trivially
# always-in-a-trade.
STRATEGY_NAME = "RSI14_7030"


def _load_fixture():
    return pd.read_csv(FIXTURE, index_col=0, parse_dates=True)


def _run_fixture_backtest():
    df = _load_fixture()
    return be.run_backtest(df, STRATEGY_NAME, interval="240")


def test_first_short_trade_matches_hand_calculated_entry_sl_and_costs():
    # RSI14 crosses above 70 (overbought -> short signal) on the bar at
    # 2024-01-04 00:00 (raw sig_rsi_extreme output, verified independently
    # against strategy.add_indicators + strategy.sig_rsi_extreme). Entry is
    # market, filled at the NEXT bar's open (2024-01-04 04:00, open=103.4276)
    # per execution.resolve_entry_fill semantics -- not at the signal bar's
    # close (that would be look-ahead).
    res = _run_fixture_backtest()
    trades = res.trades
    assert len(trades) > 0

    t = trades.iloc[0]
    assert t["direction"] == -1
    assert t["entry_time"] == pd.Timestamp("2024-01-04 04:00:00")
    assert t["entry_price"] == pytest.approx(103.4276)

    # Initial SL (short): strategy.py's _calc_initial_sl formula, replicated
    # by backtest_engine._calc_initial_sl -- dist = price * max_sl_pct (default
    # 0.05), sl = price + dist (short widens upward).
    expected_initial_sl = 103.4276 + 103.4276 * 0.05
    assert t["initial_sl"] == pytest.approx(expected_initial_sl)
    assert t["trailing_active"] == False  # noqa: E712 -- price never moved 3% in the position's favour before exit

    # The position survives (no SL touch: price only fell towards ~101, never
    # rose to the 108.6 initial SL) until the opposite (+1) signal appears at
    # 2024-01-08 20:00, closing it at that bar's close (signal-reverse exit,
    # not next-bar-open -- matches strategy.backtest_trailing's reversal rule).
    assert t["exit_reason"] == "signal_reverse"
    assert t["exit_time"] == pd.Timestamp("2024-01-08 20:00:00")
    assert t["exit_price"] == pytest.approx(101.0948)
    assert t["is_gap_fill"] == False  # noqa: E712

    # Hand-calculated costs, computed independently via costs.py (not by
    # trusting the engine's own numbers): stake=100, leverage=10 (engine
    # defaults) -> notional=1000, quantity=notional/entry_price.
    entry_price, exit_price = 103.4276, 101.0948
    notional = 100.0 * 10.0
    quantity = notional / entry_price
    exit_notional = exit_price * quantity
    assert t["quantity"] == pytest.approx(quantity)

    gross_pnl = -1 * (exit_price - entry_price) * quantity  # short: price fell -> profit
    assert t["gross_pnl"] == pytest.approx(gross_pnl)

    # Engine defaults: commission_rate_bps=10, half_spread_bps=5, slippage_bps=2.
    entry_commission = costs.commission(notional, 10.0)
    exit_commission = costs.commission(exit_notional, 10.0)
    entry_spread = costs.spread_cost(notional, 5.0)
    exit_spread = costs.spread_cost(exit_notional, 5.0)
    slippage = costs.slippage_cost(notional, bps=2.0, fixed=0.0)
    total_costs = entry_commission + exit_commission + entry_spread + exit_spread + slippage
    assert t["total_costs"] == pytest.approx(total_costs)

    net_pnl = gross_pnl - total_costs  # no funding events passed -> funding_pnl == 0
    assert t["funding_pnl"] == 0.0
    assert t["net_pnl"] == pytest.approx(net_pnl)

    # Equity after this one closed trade: initial_equity=500 (engine default) + net_pnl.
    equity_after = res.equity_curve.loc[t["exit_time"], "equity"]
    assert equity_after == pytest.approx(500.0 + net_pnl)


def test_full_run_never_implies_more_than_one_positions_margin_committed():
    # equity.Portfolio would raise InsufficientMarginError if a second
    # position's margin were committed while the first is still open and the
    # pool can't cover both. This engine only ever tracks one open position
    # (same single-position state machine as strategy.backtest_trailing), so
    # the invariant should hold structurally -- this test guards that
    # invariant directly against the produced trades/equity_curve rather than
    # assuming the implementation can't regress: for every bar timestamp, at
    # most one trade's [entry_time, exit_time) window may cover it, which is
    # exactly "never more than one position's worth of stake=100 margin
    # committed at once".
    res = _run_fixture_backtest()
    trades = res.trades
    assert len(trades) >= 10  # sanity: this run does open multiple trades over time

    for ts in res.equity_curve.index:
        concurrent = ((trades["entry_time"] <= ts) & (ts < trades["exit_time"])).sum()
        assert concurrent <= 1, f"more than one position's margin implied open at {ts}"

    # Cross-check against the trades themselves, sorted by entry: no trade
    # opens before the previous one has closed.
    ordered = trades.sort_values("entry_time")
    exit_times = ordered["exit_time"].to_numpy()[:-1]
    next_entry_times = ordered["entry_time"].to_numpy()[1:]
    assert (next_entry_times >= exit_times).all()


def test_insufficient_margin_skips_signal_leaves_position_unopened_and_equity_flat():
    # Decision (documented in backtest_engine.py's module docstring):
    # InsufficientMarginError from equity.Portfolio.open_position is handled
    # by SKIPPING the signal -- the position is simply not opened, the skip
    # is recorded, and the backtest keeps running (no exception propagates).
    # This test forces that path directly: initial_equity=50 < stake=100, so
    # margin=100 can never be covered, no matter how many long signals fire.
    idx = pd.date_range("2024-01-01", periods=6, freq="4h", tz="UTC")
    df = pd.DataFrame(
        {
            "open":   [100.0, 101.0, 103.0, 106.0, 110.0, 115.0],
            "high":   [101.0, 103.0, 106.0, 110.0, 115.0, 120.0],
            "low":    [99.5, 100.5, 102.5, 105.5, 109.5, 114.5],
            "close":  [101.0, 103.0, 106.0, 110.0, 115.0, 120.0],
            "volume": [1000.0] * 6,
        },
        index=idx,
    )

    res = be.run_backtest(df, "EMA_8_21", interval="240", initial_equity=50.0, stake=100.0, leverage=10.0)

    assert res.trades.empty
    assert len(res.skipped_signals) >= 1
    for skip in res.skipped_signals:
        assert skip["direction"] == 1
        assert "InsufficientMarginError" not in skip  # error was caught, not re-raised as a crash

    # No position was ever opened -> equity never moves away from initial_equity.
    assert (res.equity_curve["equity"] == 50.0).all()
    assert (res.equity_curve["position_open"] == False).all()  # noqa: E712
    assert res.metrics["n_trades"] == 0
    assert res.metrics["final_equity"] == 50.0

    # And explicitly confirm the underlying equity.py error type is the one
    # that would have been raised, by reproducing the same call directly.
    portfolio = equity_module.Portfolio(initial_equity=50.0)
    with pytest.raises(equity_module.InsufficientMarginError):
        portfolio.open_position("x", "BACKTEST", 1, entry_price=100.0, entry_time=idx[0], stake=100.0, leverage=10.0)


def test_metrics_summary_matches_trades_and_equity_curve():
    res = _run_fixture_backtest()
    trades = res.trades
    assert res.metrics["n_trades"] == len(trades)
    assert res.metrics["total_net_pnl"] == pytest.approx(trades["net_pnl"].sum())
    assert res.metrics["win_rate"] == pytest.approx((trades["net_pnl"] > 0).mean() * 100, abs=0.01)
    assert res.metrics["max_drawdown_pct"] == pytest.approx(res.equity_curve["drawdown_pct"].max())
    assert res.metrics["final_equity"] == pytest.approx(res.equity_curve["equity"].iloc[-1])
