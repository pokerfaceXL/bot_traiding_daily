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


def test_entry_regime_mask_all_true_matches_no_mask():
    df = _load_fixture()
    baseline = be.run_backtest(df, STRATEGY_NAME, interval="240")
    all_true = pd.Series(True, index=df.index)
    masked = be.run_backtest(df, STRATEGY_NAME, interval="240", entry_regime_mask=all_true)
    assert masked.metrics["n_trades"] == baseline.metrics["n_trades"]
    assert masked.metrics["total_net_pnl"] == pytest.approx(baseline.metrics["total_net_pnl"])


def test_entry_regime_mask_all_false_blocks_every_new_entry():
    df = _load_fixture()
    all_false = pd.Series(False, index=df.index)
    res = be.run_backtest(df, STRATEGY_NAME, interval="240", entry_regime_mask=all_false)
    assert res.trades.empty
    assert res.metrics["n_trades"] == 0
    assert res.metrics["final_equity"] == 500.0


def test_metrics_summary_matches_trades_and_equity_curve():
    res = _run_fixture_backtest()
    trades = res.trades
    assert res.metrics["n_trades"] == len(trades)
    assert res.metrics["total_net_pnl"] == pytest.approx(trades["net_pnl"].sum())
    assert res.metrics["win_rate"] == pytest.approx((trades["net_pnl"] > 0).mean() * 100, abs=0.01)
    assert res.metrics["max_drawdown_pct"] == pytest.approx(res.equity_curve["drawdown_pct"].max())
    assert res.metrics["final_equity"] == pytest.approx(res.equity_curve["equity"].iloc[-1])


def test_new_metrics_fields_on_full_fixture_run_recomputed_independently():
    # F004 wave 5: profit_factor/max_drawdown_usd/max_drawdown_abs_pct/calmar are
    # recomputed here directly from res.trades/res.equity_curve with the formulas
    # from the ticket, independently of backtest_engine._compute_metrics's own
    # code -- not by trusting the engine's own numbers against themselves.
    res = _run_fixture_backtest()
    trades = res.trades
    net_pnl = trades["net_pnl"]

    winning_sum = net_pnl[net_pnl > 0].sum()
    losing_sum = net_pnl[net_pnl <= 0].sum()
    assert losing_sum != 0  # this fixture run has losing trades -> exercises the real division, not the 0.0 no-losses fallback
    expected_profit_factor = winning_sum / abs(losing_sum)
    assert res.metrics["profit_factor"] == pytest.approx(expected_profit_factor, rel=1e-4)

    eq = res.equity_curve["equity"]
    expected_dd_usd = float((eq.cummax() - eq).max())
    assert res.metrics["max_drawdown_usd"] == pytest.approx(expected_dd_usd, rel=1e-4)

    # strategy.py's _compute_metrics (strategy.py:816-820) computes max_drawdown
    # and max_drawdown_abs_pct as the literal same value -- matched here.
    assert res.metrics["max_drawdown_abs_pct"] == pytest.approx(res.metrics["max_drawdown_pct"])

    expected_calmar = res.metrics["total_net_pnl"] / (expected_dd_usd + 1e-9)
    assert res.metrics["calmar"] == pytest.approx(expected_calmar, rel=1e-4)

    assert res.metrics["ambiguous_pct"] == 0.0


def test_compute_metrics_new_fields_hand_calculated():
    # Fully hand-built trades/equity_curve (not produced by run_backtest) so every
    # expected number below is worked out by hand, not cross-checked against the
    # implementation's own formula.
    #
    # 3 closed trades: net_pnl = +10, -4, +20.
    # winning_sum = 10 + 20 = 30, losing_sum = -4 -> profit_factor = 30 / 4 = 7.5.
    # total_net_pnl = 10 - 4 + 20 = 26.
    # win_rate = 2/3 winners * 100 = 66.666... -> rounded 66.67.
    #
    # Equity curve (6 mark-to-market rows, initial_equity=500):
    # equity = [500, 510, 508, 506, 515, 526]
    # running peak (cummax) = [500, 510, 510, 510, 515, 526]
    # dd_usd = peak - equity = [0, 0, 2, 4, 0, 0] -> max_drawdown_usd = 4.0
    # dd_pct = 100 * dd_usd / peak = [0, 0, 200/510*100=39.2157, 400/510*100=78.4314, 0, 0]
    #   -> max_drawdown_pct = round(78.4314, 4) = 78.4314, same value for max_drawdown_abs_pct.
    # calmar = total_net_pnl / (max_drawdown_usd + 1e-9) = 26 / 4.000000001 = 6.499999998...
    trades_df = pd.DataFrame({"net_pnl": [10.0, -4.0, 20.0]})
    equity_curve = pd.DataFrame({
        "equity": [500.0, 510.0, 508.0, 506.0, 515.0, 526.0],
        "drawdown_pct": [0.0, 0.0, 200 / 510 * 100, 400 / 510 * 100, 0.0, 0.0],
    })

    metrics = be._compute_metrics(trades_df, equity_curve, initial_equity=500.0)

    assert metrics["total_net_pnl"] == pytest.approx(26.0)
    assert metrics["win_rate"] == pytest.approx(66.67, abs=0.01)
    assert metrics["n_trades"] == 3
    assert metrics["final_equity"] == pytest.approx(526.0)
    assert metrics["profit_factor"] == pytest.approx(7.5)
    assert metrics["max_drawdown_usd"] == pytest.approx(4.0)
    assert metrics["max_drawdown_pct"] == pytest.approx(78.4314, abs=0.0001)
    assert metrics["max_drawdown_abs_pct"] == pytest.approx(metrics["max_drawdown_pct"])
    assert metrics["calmar"] == pytest.approx(26.0 / (4.0 + 1e-9), rel=1e-6)
    assert metrics["ambiguous_pct"] == 0.0


def test_compute_metrics_profit_factor_is_sentinel_when_no_losing_trades():
    # Coordinator correction (see backtest_engine.py comment): the original F004
    # wave 5 task instructed 0.0 here, but that reads as the worst possible score
    # for a flawless win record. Matched to strategy.py's own sentinel instead
    # (strategy.py:797, 9999.0), not left at the mistaken literal instruction.
    trades_df = pd.DataFrame({"net_pnl": [5.0, 10.0]})
    equity_curve = pd.DataFrame({
        "equity": [500.0, 505.0, 515.0],
        "drawdown_pct": [0.0, 0.0, 0.0],
    })

    metrics = be._compute_metrics(trades_df, equity_curve, initial_equity=500.0)

    assert metrics["profit_factor"] == 9999.0


def test_stake_series_none_matches_call_without_the_parameter():
    # spec/research/F006-hypothesis-position-sizing-vol-inverse.md discriminating check 5:
    # the new stake_series hook's default must be provably additive, not just by inspection.
    res_default = be.run_backtest(_load_fixture(), STRATEGY_NAME, interval="240")
    res_explicit_none = be.run_backtest(_load_fixture(), STRATEGY_NAME, interval="240", stake_series=None)

    pd.testing.assert_frame_equal(res_default.trades, res_explicit_none.trades)
    pd.testing.assert_frame_equal(res_default.equity_curve, res_explicit_none.equity_curve)
    assert res_default.metrics == res_explicit_none.metrics


def test_stake_series_scales_the_stake_used_at_each_entry():
    df = _load_fixture()
    baseline = be.run_backtest(df, STRATEGY_NAME, interval="240")
    entry_times = baseline.trades["entry_time"]

    # Double the stake on the first entry only, leave every other entry at the
    # scalar default (100.0) via .fillna, matching run_backtest's own reindex+fillna
    # handling of a stake_series that doesn't cover every bar.
    first_entry = entry_times.iloc[0]
    stake_series = pd.Series({first_entry: 200.0})

    sized = be.run_backtest(df, STRATEGY_NAME, interval="240", stake_series=stake_series)

    assert len(sized.trades) == len(baseline.trades)
    assert sized.trades["stake"].iloc[0] == pytest.approx(200.0)
    assert sized.trades["stake"].iloc[1:].tolist() == pytest.approx([100.0] * (len(sized.trades) - 1))
    # Doubling only the first trade's stake doubles only that trade's net_pnl
    # (linear-in-stake cost structure, see the hypothesis note's Observation section).
    assert sized.trades["net_pnl"].iloc[0] == pytest.approx(2 * baseline.trades["net_pnl"].iloc[0])
    assert sized.trades["net_pnl"].iloc[1:].tolist() == pytest.approx(baseline.trades["net_pnl"].iloc[1:].tolist())


# --- spec/research/F006-hypothesis-loss-recency-cooldown.md: loss_cooldown_candles ---

LOSS_COOLDOWN_STRATEGY = "_TEST_LOSS_COOLDOWN"


def _build_loss_cooldown_frame(ninth_bar_close: float):
    """11 synthetic bars, hand-designed so the first long trade (entered bar 1,
    filled at open=100.0) hits its initial_sl (sl=97.0) on bar 2 -- a loss -- and
    the persistent long signal would otherwise re-arm on the very next bar. Bar 9
    flips the signal to short, closing the second long trade via signal_reverse at
    `ninth_bar_close` (110.0 = win, 90.0 = loss depending on caller) and queuing a
    new short entry for bar 10. Every bar's low/high stays clear of any stop level
    except where a touch is explicitly intended, so every trade boundary is exactly
    where this docstring says it is, not an accidental touch elsewhere."""
    idx = pd.date_range("2024-01-01", periods=11, freq="4h", tz="UTC")
    rows = [
        (100.0, 100.5, 99.5, 100.0),   # 0: signal=1, arms entry
        (100.0, 100.6, 98.5, 100.0),   # 1: entry fill @100.0, sl=97.0 not touched
        (100.0, 100.2, 96.5, 96.6),    # 2: low touches sl=97.0 -> initial_sl loss
        (96.6, 96.7, 96.5, 96.6),      # 3: gated (or, at loss_cooldown=0, re-entry)
        (96.6, 96.7, 96.5, 96.6),      # 4: gated
        (96.6, 96.7, 96.5, 96.6),      # 5: gated
        (96.6, 96.7, 96.5, 96.6),      # 6: gate expires here, entry arms
        (96.6, 96.7, 96.5, 96.6),      # 7: 2nd trade entry fill @96.6, sl=93.702
        (96.6, 96.7, 96.5, 96.6),      # 8: sl not touched
        (96.6, max(110.2, ninth_bar_close + 0.2), 96.5, ninth_bar_close),  # 9: signal_reverse close
        (ninth_bar_close, ninth_bar_close + 0.5, ninth_bar_close - 0.5, ninth_bar_close),  # 10: 3rd (short) entry fill, if not gated
    ]
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx)
    df["volume"] = 1000.0
    signal = pd.Series([1] * 9 + [-1] * 2, index=idx, dtype=float)

    def _fixed_signal(work: pd.DataFrame) -> pd.Series:
        return signal.reindex(work.index).fillna(0.0)

    return df, _fixed_signal


def _run_loss_cooldown(monkeypatch, df, signal_fn, loss_cooldown_candles: int):
    import strategy
    monkeypatch.setitem(strategy.STRATEGY_CATALOG, LOSS_COOLDOWN_STRATEGY, signal_fn)
    now = df.index[-1] + pd.Timedelta(hours=4)
    return be.run_backtest(
        df, LOSS_COOLDOWN_STRATEGY, interval="240", now=now,
        max_sl_pct=0.03, activate_pct=10.0, trail_pct=0.5,
        loss_cooldown_candles=loss_cooldown_candles,
    )


def test_loss_cooldown_candles_zero_matches_call_without_the_parameter(monkeypatch):
    import strategy
    df, signal_fn = _build_loss_cooldown_frame(ninth_bar_close=110.0)
    monkeypatch.setitem(strategy.STRATEGY_CATALOG, LOSS_COOLDOWN_STRATEGY, signal_fn)
    now = df.index[-1] + pd.Timedelta(hours=4)

    res_default = be.run_backtest(df, LOSS_COOLDOWN_STRATEGY, interval="240", now=now, max_sl_pct=0.03, activate_pct=10.0, trail_pct=0.5)
    res_explicit_zero = be.run_backtest(df, LOSS_COOLDOWN_STRATEGY, interval="240", now=now, max_sl_pct=0.03, activate_pct=10.0, trail_pct=0.5, loss_cooldown_candles=0)

    pd.testing.assert_frame_equal(res_default.trades, res_explicit_zero.trades)
    pd.testing.assert_frame_equal(res_default.equity_curve, res_explicit_zero.equity_curve)
    assert res_default.metrics == res_explicit_zero.metrics


def test_loss_cooldown_delays_reentry_after_an_initial_sl_loss_without_dropping_the_trade(monkeypatch):
    # Win variant (bar 9 closes the 2nd long trade at a profit via signal_reverse):
    # gating the loss on bar 2 should delay the 2nd trade's entry from bar 3
    # (baseline, loss_cooldown_candles=0) to bar 7 (gated, loss_cooldown_candles=3),
    # but neither run drops a trade -- both end with exactly 3 trades, since the
    # persistent signal re-arms once the gate expires.
    df, signal_fn = _build_loss_cooldown_frame(ninth_bar_close=110.0)

    baseline = _run_loss_cooldown(monkeypatch, df, signal_fn, loss_cooldown_candles=0)
    assert len(baseline.trades) == 3
    assert baseline.trades["entry_time"].tolist() == [df.index[1], df.index[3], df.index[10]]
    assert baseline.trades["net_pnl"].iloc[0] < 0

    gated = _run_loss_cooldown(monkeypatch, df, signal_fn, loss_cooldown_candles=3)
    assert len(gated.trades) == 3
    assert gated.trades["entry_time"].tolist() == [df.index[1], df.index[7], df.index[10]]
    assert gated.trades["net_pnl"].iloc[0] < 0
    # the win at trade 2 must NOT itself start a new loss-cooldown window: the
    # short entry queued right after it still fires at the very next bar (10).
    assert gated.trades["net_pnl"].iloc[1] > 0


def test_loss_cooldown_also_gates_a_signal_reverse_loss_not_only_initial_sl(monkeypatch):
    # Loss variant (bar 9 closes the 2nd long trade at a LOSS via signal_reverse,
    # an exit_reason cooldown_candles never gates at all): the 3rd (short) entry
    # that would otherwise fire immediately at bar 10 must be suppressed, proving
    # the gate is conditioned on realized net_pnl sign, not on exit_reason label.
    df, signal_fn = _build_loss_cooldown_frame(ninth_bar_close=90.0)

    baseline = _run_loss_cooldown(monkeypatch, df, signal_fn, loss_cooldown_candles=0)
    assert len(baseline.trades) == 3
    assert baseline.trades["net_pnl"].iloc[1] < 0
    assert baseline.trades["entry_time"].iloc[2] == df.index[10]

    gated = _run_loss_cooldown(monkeypatch, df, signal_fn, loss_cooldown_candles=3)
    assert len(gated.trades) == 2
    assert gated.trades["net_pnl"].iloc[1] < 0
