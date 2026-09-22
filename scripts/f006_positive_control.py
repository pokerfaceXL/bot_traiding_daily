"""
F006 positive-control sanity check (diagnostic script, not strategy research).

Constructs a deterministic, low-noise synthetic uptrend (tests/fixtures/
positive_control_uptrend.csv) that a simple trend-following strategy should
clearly profit from, then runs it through both engines:

  1. backtest_engine.run_backtest (F004/F005 cost/equity-aware engine),
     strategy_name="EMA_8_21", leverage=1 (F006 research placeholder per
     spec/build.md), same cost/equity params as F005-baseline.md.
  2. strategy.backtest_trailing (old F004-era free/no-cost engine), same
     signal + SL/trailing params, so the two engines are otherwise
     apples-to-apples -- only cost/equity modeling differs.

Prints a summary used to write spec/research/F006-pipeline-positive-control.md.
Does not modify strategy.py/backtest_engine.py/costs.py/equity.py/
execution.py/data_contract.py/regularity.py/backtest_apex.py -- read-only
imports only.
"""

from __future__ import annotations

import json
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import costs
import regularity
import strategy

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "tests", "fixtures", "positive_control_uptrend.csv",
)

# --- Synthetic scenario parameters (deterministic, no RNG) ---
N_BARS = 280
START_TS = pd.Timestamp("2024-01-15 00:00:00")
INTERVAL_HOURS = 4
BASE_PRICE = 100.0
DRIFT_PER_BAR = 0.12
WIGGLE_AMP = 0.35
WIGGLE_PERIOD_BARS = 24

STRATEGY_NAME = "EMA_8_21"

# Params shared by BOTH engines (equivalent comparison, requirement 3).
ATR_MULTIPLIER = 1.5
MAX_SL_PCT = 0.05
ACTIVATE_PCT = 0.03
TRAIL_PCT = 0.02
COOLDOWN_CANDLES = 0

# Cost/equity params, same as F005-baseline.md.
INITIAL_EQUITY = 500.0
STAKE = 100.0
LEVERAGE = 1.0
COMMISSION_RATE_BPS = 10.0
HALF_SPREAD_BPS = 5.0
SLIPPAGE_BPS = 2.0


def _trend_close(i: int) -> float:
    """Deterministic closing price: linear drift + small sine wiggle.

    Derivative of the continuous approximation is drift +/- amp*2*pi/period.
    With DRIFT_PER_BAR=0.12 and amp*2*pi/period = 0.35*2*pi/24 ~= 0.0916,
    the derivative stays in [0.0284, 0.2116] -- always positive, so close
    is bar-over-bar non-decreasing by construction (no down bars, no
    whipsaw), while still wiggling instead of being a straight line.
    """
    return BASE_PRICE + DRIFT_PER_BAR * i + WIGGLE_AMP * math.sin(2 * math.pi * i / WIGGLE_PERIOD_BARS)


def build_synthetic_uptrend(n_bars: int = N_BARS) -> pd.DataFrame:
    closes = [_trend_close(i) for i in range(n_bars)]
    opens = [closes[0]] + closes[:-1]  # open[i] = close[i-1], continuous, no gaps
    rows = []
    for i in range(n_bars):
        o, c = opens[i], closes[i]
        rng = 0.10 + 0.02 * math.sin(i * 0.7)  # small deterministic intrabar range, ~0.08-0.12
        high = max(o, c) + rng
        low = min(o, c) - rng
        volume = 1000.0 + 50.0 * math.sin(i * 0.3)
        ts = START_TS + pd.Timedelta(hours=INTERVAL_HOURS * i)
        rows.append({"timestamp": ts, "open": o, "high": high, "low": low, "close": c, "volume": volume})
    df = pd.DataFrame(rows).set_index("timestamp")
    return df


def _fmt_month(m: regularity.MonthResult) -> str:
    return (
        f"{m.year}-{m.month:02d}: n={m.n} is_partial={m.is_partial} is_valid={m.is_valid} "
        f"positive_day_pct={m.positive_day_pct} deviation_pct={m.deviation_pct} target_met={m.target_met}"
    )


def main() -> None:
    df = build_synthetic_uptrend()
    os.makedirs(os.path.dirname(FIXTURE_PATH), exist_ok=True)
    df.to_csv(FIXTURE_PATH, float_format="%.6f")
    print(f"Wrote fixture: {FIXTURE_PATH} ({len(df)} bars, {df.index[0]} .. {df.index[-1]})")

    close_first, close_last = float(df["close"].iloc[0]), float(df["close"].iloc[-1])
    print(f"Synthetic close: first={close_first:.4f} last={close_last:.4f} "
          f"total_rise={(close_last - close_first):.4f} ({100 * (close_last / close_first - 1):.2f}%)")
    n_down_bars = int((df["close"].diff().dropna() < 0).sum())
    print(f"Down bars (close[i] < close[i-1]): {n_down_bars} / {len(df) - 1} (expected 0, by construction)")

    now = df.index[-1] + pd.Timedelta(hours=INTERVAL_HOURS)

    # --- New engine: backtest_engine.run_backtest ---
    result = be.run_backtest(
        df, STRATEGY_NAME, interval="240", now=now,
        initial_equity=INITIAL_EQUITY, stake=STAKE, leverage=LEVERAGE,
        atr_multiplier=ATR_MULTIPLIER, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN_CANDLES,
        commission_rate_bps=COMMISSION_RATE_BPS, half_spread_bps=HALF_SPREAD_BPS,
        slippage_bps=SLIPPAGE_BPS,
    )
    print("\n=== NEW ENGINE (backtest_engine.run_backtest) ===")
    print(json.dumps(result.metrics, indent=2))
    print(f"n_trades={len(result.trades)}, skipped_signals={len(result.skipped_signals)}")
    if not result.trades.empty:
        print(result.trades[["direction", "entry_time", "entry_price", "exit_time", "exit_price",
                              "exit_reason", "gross_pnl", "total_costs", "net_pnl"]].to_string())

    # --- Independent hand-calculation for the (expected) single long trade ---
    if len(result.trades) == 1:
        t = result.trades.iloc[0]
        entry_price, exit_price = float(t["entry_price"]), float(t["exit_price"])
        notional = STAKE * LEVERAGE
        quantity = notional / entry_price
        gross_pnl = quantity * (exit_price - entry_price)  # direction == +1 (long)
        exit_notional = exit_price * quantity
        entry_commission = costs.commission(notional, COMMISSION_RATE_BPS)
        exit_commission = costs.commission(exit_notional, COMMISSION_RATE_BPS)
        entry_spread = costs.spread_cost(notional, HALF_SPREAD_BPS)
        exit_spread = costs.spread_cost(exit_notional, HALF_SPREAD_BPS)
        slippage = costs.slippage_cost(notional, bps=SLIPPAGE_BPS)
        total_costs = entry_commission + exit_commission + entry_spread + exit_spread + slippage
        hand_net_pnl = gross_pnl - total_costs
        print("\n=== HAND CALCULATION (independent, from raw entry/exit prices + costs.py) ===")
        print(f"entry_price={entry_price:.6f} exit_price={exit_price:.6f} quantity={quantity:.6f}")
        print(f"hand gross_pnl={gross_pnl:.6f} hand total_costs={total_costs:.6f} hand net_pnl={hand_net_pnl:.6f}")
        print(f"engine gross_pnl={float(t['gross_pnl']):.6f} engine total_costs={float(t['total_costs']):.6f} "
              f"engine net_pnl={float(t['net_pnl']):.6f}")
        assert abs(hand_net_pnl - float(t["net_pnl"])) < 1e-6, "hand calc does not match engine net_pnl"
        print("Hand calculation MATCHES engine output exactly.")
    else:
        print(f"\n(Skipping hand-calc single-trade check: engine produced {len(result.trades)} trades, not 1.)")

    # --- Regularity check ---
    days, months = regularity.compute_regularity(result.equity_curve)
    print("\n=== REGULARITY (regularity.compute_regularity on the new engine's equity curve) ===")
    for m in months:
        print(_fmt_month(m))
    valid_full_months = [m for m in months if m.is_valid and not m.is_partial]
    target_met_months = [m for m in valid_full_months if m.target_met]
    print(f"\nvalid full months: {len(valid_full_months)}, target_met among them: {len(target_met_months)}")
    if valid_full_months:
        best = min(valid_full_months, key=lambda m: m.deviation_pct)
        print(f"best (lowest) deviation_pct among valid full months: {best.deviation_pct} ({best.year}-{best.month:02d})")

    # --- Old engine: strategy.backtest_trailing, same signal + SL/trailing params ---
    df2 = strategy.add_indicators(df.copy())
    df2["signal"] = strategy.STRATEGY_CATALOG[STRATEGY_NAME](df2)
    old_trades, old_metrics = strategy.backtest_trailing(
        df2,
        atr_multiplier=ATR_MULTIPLIER, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        leverage=LEVERAGE, stake=STAKE,
        entry_on_open=True, cooldown_candles=COOLDOWN_CANDLES,
    )
    print("\n=== OLD ENGINE (strategy.backtest_trailing, F004-era, free/no-cost) ===")
    print(json.dumps(old_metrics, indent=2))
    print(f"n_trades={len(old_trades)}")
    if not old_trades.empty:
        print(old_trades[["type", "entry_date", "entry_price", "exit_date", "exit_price",
                           "close_by", "pnl_usd"]].to_string())

    print("\n=== SUMMARY ===")
    print(f"new engine: final_equity={result.metrics['final_equity']}, "
          f"total_net_pnl={result.metrics['total_net_pnl']}, "
          f"max_drawdown_pct={result.metrics['max_drawdown_pct']}, "
          f"n_trades={result.metrics['n_trades']}")
    print(f"old engine: total_pnl={old_metrics['total_pnl']}, n_trades={old_metrics['n_trades']}, "
          f"max_drawdown={old_metrics.get('max_drawdown')}")
    print(f"regularity: {len(target_met_months)}/{len(valid_full_months)} valid full months meet <=20% deviation target")


if __name__ == "__main__":
    main()
