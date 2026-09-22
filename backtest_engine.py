"""
Backtest orchestration engine (F004, wave 4 -- backtest_engine.py).

Standalone module composing the three already-merged F004 pieces (costs.py
wave 1, equity.py wave 2, execution.py wave 3) plus data_contract.py (F003)
into a working end-to-end backtest loop. This is NOT the integration into
backtest_apex.py -- that is a later, separate wave (F004, wave 5).
strategy.py/backtest_apex.py/main.py/trader.py/configuration/ are read
(imported) but not modified by this module.

Signal generation reuses strategy.STRATEGY_CATALOG[...] and
strategy.add_indicators as-is -- pure indicator/signal math, not
reimplemented here.

Entry/SL/trailing decision logic replicates strategy.backtest_trailing's
entry_on_open=True contract (strategy.py:498) bar-for-bar:
- Same initial-SL formula as strategy.py's _calc_initial_sl (strategy.py:491):
  dist = price * max_sl_pct, sl = price -/+ dist. atr_multiplier is accepted
  as a parameter for contract parity (per the F004 ticket) but, exactly like
  strategy.py's current implementation, it is NOT applied to the SL distance
  -- the ATR component is commented out there (strategy.py:495) and this
  module reproduces that same behaviour rather than silently fixing it.
- Same trailing-SL math: activate_pct triggers trail_active once best_price
  has moved activate_pct in the position's favour, trail_pct sets the
  trailing distance from best_price, best_price/trailing_sl update using
  THIS bar's high/low BEFORE the stop-touch check for that bar (matching
  strategy.py's sub_lookup=None / "optymistyczny" branch order, since this
  module has no sub-candle Bar Magnifier data).
- Same cooldown_candles gate: after an initial-SL exit, no new entry is
  queued until cooldown_candles bars have passed.
- Same signal-reversal exit (close at current bar's close when a position is
  open and a new opposite-direction signal appears) and same end-of-data
  close (open position closed at the last bar's close).

What is NOT reused from strategy.py: the actual bar-touch resolution. Instead
of strategy.py's raw `low <= active_sl` / `high >= active_sl` checks, this
module calls execution.resolve_stop_take_within_bar (conservative,
gap-aware) for every bar with an open position, and entries fill via
execution.resolve_entry_fill(OrderType.MARKET, ...) at the next bar's open
(matching entry_on_open=True) instead of strategy.py's own open_a[i] lookup.

Equity/margin/costs run through a single shared equity.Portfolio
(initial_equity=500 default, stake=100 default per spec/build.md's
contract) -- costs.py's commission/spread/slippage/funding are applied on
every close via Portfolio.close_position. Only ONE position is open at a
time (same single-position state machine as strategy.py's backtest_trailing
-- this module does not add multi-position concurrency).

Decision on equity.InsufficientMarginError (documented, not left undefined):
when Portfolio.open_position would raise it, the signal is SKIPPED -- the
position is simply not opened, the loop continues, and the skip is recorded
in the returned skipped_signals list so callers can see it happened. The
error is not propagated and does not abort the backtest.

Zero network connections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

import data_contract
import equity as equity_module
import execution
import strategy
from execution import Bar, OrderType, TriggerKind


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict
    skipped_signals: List[dict]


def _calc_initial_sl(direction: int, price: float, max_sl_pct: float) -> float:
    """Same formula as strategy.py's _calc_initial_sl (strategy.py:491) -- atr is not used, see module docstring."""
    dist = price * max_sl_pct
    sl_level = (price - dist) if direction == 1 else (price + dist)
    return max(sl_level, 0.0) if direction == 1 else sl_level


def _update_trailing(direction: int, best_price: float, trailing_sl: float, trail_active: bool,
                      entry_price: float, bar_high: float, bar_low: float,
                      activate_pct: float, trail_pct: float) -> Tuple[float, float, bool]:
    if direction == 1:
        best_price = max(best_price, bar_high)
        if not trail_active and best_price >= entry_price * (1 + activate_pct):
            trail_active = True
            trailing_sl = best_price * (1 - trail_pct)
        if trail_active:
            trailing_sl = max(trailing_sl, best_price * (1 - trail_pct))
    else:
        best_price = min(best_price, bar_low)
        if not trail_active and best_price <= entry_price * (1 - activate_pct):
            trail_active = True
            trailing_sl = best_price * (1 + trail_pct)
        if trail_active:
            trailing_sl = min(trailing_sl, best_price * (1 + trail_pct))
    return best_price, trailing_sl, trail_active


def _active_sl(direction: int, initial_sl: float, trailing_sl: float, trail_active: bool) -> float:
    if not trail_active:
        return initial_sl
    return max(initial_sl, trailing_sl) if direction == 1 else min(initial_sl, trailing_sl)


def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    interval: str = "240",
    now: Optional[pd.Timestamp] = None,
    symbol: str = "BACKTEST",
    initial_equity: float = 500.0,
    stake: float = 100.0,
    leverage: float = 10.0,
    atr_multiplier: float = 1.5,
    max_sl_pct: float = 0.05,
    activate_pct: float = 0.03,
    trail_pct: float = 0.02,
    cooldown_candles: int = 0,
    commission_rate_bps: float = 10.0,
    half_spread_bps: float = 5.0,
    slippage_bps: float = 2.0,
    slippage_fixed: float = 0.0,
    funding_events: Iterable[Tuple[object, float]] = (),
    fee_buffer: float = 0.0,
) -> BacktestResult:
    """
    Runs one end-to-end backtest of `strategy_name` over `df`.

    Pipeline: data_contract.filter_closed_candles -> strategy.add_indicators
    -> strategy.STRATEGY_CATALOG[strategy_name] for the signal column ->
    per-bar entry (execution.resolve_entry_fill, market, next bar's open) /
    exit (execution.resolve_stop_take_within_bar, execution.resolve_level_fill)
    loop against a shared equity.Portfolio, with costs.py costs applied on
    every close. See module docstring for the full decision-logic contract.
    """
    closed_df, _dropped = data_contract.filter_closed_candles(df, interval, now=now)
    work = strategy.add_indicators(closed_df)
    if strategy_name not in strategy.STRATEGY_CATALOG:
        raise ValueError(f"Nieznana strategia: '{strategy_name}'. Dostepne: {sorted(strategy.STRATEGY_CATALOG.keys())}")
    work["signal"] = strategy.STRATEGY_CATALOG[strategy_name](work)

    n = len(work)
    if n == 0:
        empty_trades = pd.DataFrame()
        empty_curve = pd.DataFrame(columns=["equity", "drawdown_pct", "position_open"])
        return BacktestResult(trades=empty_trades, equity_curve=empty_curve, metrics=_empty_metrics(initial_equity), skipped_signals=[])

    idx_arr = work.index
    open_a = work["open"].to_numpy(dtype=float)
    high_a = work["high"].to_numpy(dtype=float)
    low_a = work["low"].to_numpy(dtype=float)
    close_a = work["close"].to_numpy(dtype=float)
    raw_sig = work["signal"].to_numpy(dtype=float)
    sig_a = pd.Series(raw_sig).fillna(0).astype(int).to_numpy()

    portfolio = equity_module.Portfolio(initial_equity=initial_equity)

    pos = 0
    entry_price = 0.0
    entry_time = None
    initial_sl = 0.0
    trailing_sl = 0.0
    best_price = 0.0
    trail_active = False
    active_position_id: Optional[str] = None

    pending_signal = 0
    cooldown_until = -1
    trade_counter = 0

    trades: List[dict] = []
    skipped_signals: List[dict] = []
    equity_rows: List[dict] = []

    def _record_close(closed_trade: equity_module.ClosedTrade, exit_reason: str, is_gap_fill: bool) -> None:
        p = closed_trade.position
        trades.append({
            "position_id": p.position_id,
            "symbol": p.symbol,
            "direction": p.direction,
            "entry_time": p.entry_time,
            "entry_price": p.entry_price,
            "exit_time": closed_trade.exit_time,
            "exit_price": closed_trade.exit_price,
            "exit_reason": exit_reason,
            "is_gap_fill": is_gap_fill,
            "initial_sl": initial_sl,
            "trailing_sl": trailing_sl if trail_active else None,
            "trailing_active": trail_active,
            "stake": p.stake,
            "leverage": p.leverage,
            "notional": p.notional,
            "margin": p.margin,
            "quantity": p.quantity,
            "gross_pnl": closed_trade.gross_pnl,
            "total_costs": closed_trade.total_costs,
            "funding_pnl": closed_trade.funding_pnl,
            "net_pnl": closed_trade.net_pnl,
        })

    for i in range(n):
        bar_count = i + 1
        bar = Bar(open=open_a[i], high=high_a[i], low=low_a[i], close=close_a[i])
        idx = idx_arr[i]
        signal = int(sig_a[i])

        # 1. Fill a pending entry (queued on a previous bar) at this bar's open.
        if pending_signal != 0 and pos == 0:
            fill = execution.resolve_entry_fill(OrderType.MARKET, direction=pending_signal, next_bar=bar)
            trade_counter += 1
            position_id = f"p{trade_counter}"
            try:
                portfolio.open_position(
                    position_id=position_id,
                    symbol=symbol,
                    direction=pending_signal,
                    entry_price=fill.fill_price,
                    entry_time=idx,
                    stake=stake,
                    leverage=leverage,
                    fee_buffer=fee_buffer,
                )
                pos = pending_signal
                entry_price = fill.fill_price
                entry_time = idx
                initial_sl = _calc_initial_sl(pos, entry_price, max_sl_pct)
                trailing_sl = 0.0
                best_price = entry_price
                trail_active = False
                active_position_id = position_id
            except equity_module.InsufficientMarginError as exc:
                skipped_signals.append({
                    "time": idx,
                    "direction": pending_signal,
                    "reason": str(exc),
                })
            pending_signal = 0

        # 2. Trailing update + stop-loss touch check for an open position, this bar.
        if pos != 0:
            best_price, trailing_sl, trail_active = _update_trailing(
                pos, best_price, trailing_sl, trail_active, entry_price, bar.high, bar.low, activate_pct, trail_pct
            )
            active_sl = _active_sl(pos, initial_sl, trailing_sl, trail_active)
            trigger = execution.resolve_stop_take_within_bar(pos, bar, stop_loss=active_sl, take_profit=None)
            if trigger.kind == TriggerKind.STOP_LOSS:
                exit_reason = "trailing_sl" if (trail_active and active_sl == trailing_sl and trailing_sl != initial_sl) else "initial_sl"
                closed_trade = portfolio.close_position(
                    active_position_id, trigger.fill_price, idx,
                    commission_rate_bps=commission_rate_bps,
                    half_spread_bps=half_spread_bps,
                    slippage_bps=slippage_bps,
                    slippage_fixed=slippage_fixed,
                    funding_events=funding_events,
                )
                _record_close(closed_trade, exit_reason, trigger.is_gap_fill)
                pos = 0
                trail_active = False
                active_position_id = None
                if exit_reason == "initial_sl" and cooldown_candles > 0:
                    cooldown_until = bar_count + cooldown_candles

        # 3. Signal reversal: close the open position at this bar's close.
        if pos != 0 and signal != 0 and signal != pos:
            closed_trade = portfolio.close_position(
                active_position_id, bar.close, idx,
                commission_rate_bps=commission_rate_bps,
                half_spread_bps=half_spread_bps,
                slippage_bps=slippage_bps,
                slippage_fixed=slippage_fixed,
                funding_events=funding_events,
            )
            _record_close(closed_trade, "signal_reverse", is_gap_fill=False)
            pos = 0
            trail_active = False
            active_position_id = None

        # 4. Queue an entry for the next bar's open.
        if pos == 0 and signal != 0 and bar_count > cooldown_until:
            pending_signal = signal

        # 5. Per-bar mark-to-market equity curve (includes the open position, if any).
        mark_prices = {active_position_id: bar.close} if active_position_id else None
        eq, dd = portfolio.mark_to_market(mark_prices)
        equity_rows.append({"timestamp": idx, "equity": eq, "drawdown_pct": dd, "position_open": pos != 0})

    # 6. Close any still-open position at the last bar's close (end of data).
    if pos != 0:
        last_idx = idx_arr[-1]
        last_close = close_a[-1]
        closed_trade = portfolio.close_position(
            active_position_id, last_close, last_idx,
            commission_rate_bps=commission_rate_bps,
            half_spread_bps=half_spread_bps,
            slippage_bps=slippage_bps,
            slippage_fixed=slippage_fixed,
            funding_events=funding_events,
        )
        _record_close(closed_trade, "end_of_data", is_gap_fill=False)
        eq, dd = portfolio.mark_to_market(None)
        equity_rows[-1] = {"timestamp": last_idx, "equity": eq, "drawdown_pct": dd, "position_open": False}

    trades_df = pd.DataFrame(trades)
    equity_curve = pd.DataFrame(equity_rows).set_index("timestamp") if equity_rows else pd.DataFrame(columns=["equity", "drawdown_pct", "position_open"])
    metrics = _compute_metrics(trades_df, equity_curve, initial_equity)
    return BacktestResult(trades=trades_df, equity_curve=equity_curve, metrics=metrics, skipped_signals=skipped_signals)


def _empty_metrics(initial_equity: float) -> dict:
    return {
        "total_net_pnl": 0.0,
        "win_rate": 0.0,
        "max_drawdown_pct": 0.0,
        "n_trades": 0,
        "final_equity": initial_equity,
        "profit_factor": 0.0,
        "max_drawdown_usd": 0.0,
        "max_drawdown_abs_pct": 0.0,
        "calmar": 0.0,
        # execution.py resolves intra-bar SL/TP ambiguity deterministically via a
        # documented conservative rule (SL always wins when both SL and TP fall
        # inside the same bar -- see execution.py's resolve_stop_take_within_bar)
        # instead of measuring ambiguity like strategy.py's ambiguous_count /
        # ambiguous_pct. This field is not applicable the same way anymore, but is
        # kept at 0.0 so downstream key access (backtest_apex.py) does not break.
        "ambiguous_pct": 0.0,
    }


def _max_drawdown_usd(equity_curve: pd.DataFrame) -> float:
    """Peak-to-trough drawdown in USD from the equity curve (peak - equity, running max of peak)."""
    if equity_curve.empty:
        return 0.0
    eq = equity_curve["equity"]
    peak = eq.cummax()
    return float((peak - eq).max())


def _compute_metrics(trades_df: pd.DataFrame, equity_curve: pd.DataFrame, initial_equity: float) -> dict:
    if trades_df.empty:
        metrics = _empty_metrics(initial_equity)
        if not equity_curve.empty:
            metrics["final_equity"] = float(equity_curve["equity"].iloc[-1])
            metrics["max_drawdown_pct"] = float(equity_curve["drawdown_pct"].max())
            metrics["max_drawdown_usd"] = _max_drawdown_usd(equity_curve)
            metrics["max_drawdown_abs_pct"] = metrics["max_drawdown_pct"]
        return metrics

    net_pnl = trades_df["net_pnl"]
    total_net_pnl = float(net_pnl.sum())
    win_rate = float((net_pnl > 0).mean() * 100)
    max_dd = float(equity_curve["drawdown_pct"].max()) if not equity_curve.empty else 0.0
    max_dd_usd = _max_drawdown_usd(equity_curve)
    final_equity = float(equity_curve["equity"].iloc[-1]) if not equity_curve.empty else initial_equity + total_net_pnl

    # profit_factor: sum of winning net_pnl / abs(sum of losing net_pnl); 0.0 if
    # there are no losing trades (per ticket -- not strategy.py's 9999.0 sentinel).
    winning_sum = float(net_pnl[net_pnl > 0].sum())
    losing_sum = float(net_pnl[net_pnl <= 0].sum())
    profit_factor = (winning_sum / abs(losing_sum)) if losing_sum != 0 else 0.0

    # calmar: same formula as strategy.py's _compute_metrics (strategy.py:816) --
    # total_pnl / (max_dd_usd + 1e-9), no annualization. Matched exactly, not fixed.
    calmar = total_net_pnl / (max_dd_usd + 1e-9)

    max_dd_pct_rounded = round(max_dd, 4)

    return {
        "total_net_pnl": round(total_net_pnl, 6),
        "win_rate": round(win_rate, 2),
        "max_drawdown_pct": max_dd_pct_rounded,
        "n_trades": int(len(trades_df)),
        "final_equity": round(final_equity, 6),
        "profit_factor": round(profit_factor, 6),
        "max_drawdown_usd": round(max_dd_usd, 6),
        "max_drawdown_abs_pct": max_dd_pct_rounded,
        "calmar": round(calmar, 6),
        "ambiguous_pct": 0.0,
    }
