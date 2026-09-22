"""
F006 positive-control sanity check.

Asserts the qualitative result actually verified by scripts/f006_positive_control.py
on tests/fixtures/positive_control_uptrend.csv (a deterministic, clean, low-noise
synthetic uptrend, no RNG -- see that script's build_synthetic_uptrend): both engines
should clearly profit from an EMA_8_21 long held through a monotonic price rise, the
cost/equity-aware engine should survive with a positive final_equity, and February 2024
(the one full, non-partial, valid calendar month fully covered by the fixture) should
meet the <=20% regularity deviation target. This is the honest, verified result -- not
an assumption made before running the pipeline.
"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import costs
import regularity
import strategy

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "positive_control_uptrend.csv")

STRATEGY_NAME = "EMA_8_21"
ATR_MULTIPLIER = 1.5
MAX_SL_PCT = 0.05
ACTIVATE_PCT = 0.03
TRAIL_PCT = 0.02
COOLDOWN_CANDLES = 0
INITIAL_EQUITY = 500.0
STAKE = 100.0
LEVERAGE = 1.0
COMMISSION_RATE_BPS = 10.0
HALF_SPREAD_BPS = 5.0
SLIPPAGE_BPS = 2.0


def _load_fixture():
    return pd.read_csv(FIXTURE, index_col=0, parse_dates=True)


def _run_new_engine():
    df = _load_fixture()
    now = df.index[-1] + pd.Timedelta(hours=4)
    return be.run_backtest(
        df, STRATEGY_NAME, interval="240", now=now,
        initial_equity=INITIAL_EQUITY, stake=STAKE, leverage=LEVERAGE,
        atr_multiplier=ATR_MULTIPLIER, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT, cooldown_candles=COOLDOWN_CANDLES,
        commission_rate_bps=COMMISSION_RATE_BPS, half_spread_bps=HALF_SPREAD_BPS,
        slippage_bps=SLIPPAGE_BPS,
    )


def test_synthetic_fixture_is_a_clean_monotonic_uptrend():
    df = _load_fixture()
    assert len(df) == 280
    n_down_bars = int((df["close"].diff().dropna() < 0).sum())
    assert n_down_bars == 0  # by construction: drift always dominates the wiggle
    assert df["close"].iloc[-1] > df["close"].iloc[0]


def test_new_engine_survives_with_positive_pnl_on_easy_uptrend():
    result = _run_new_engine()

    # Verified result: exactly one long trade, held from just after the start
    # (first EMA_8/21 crossover) to end_of_data (trend never reverses).
    assert len(result.trades) == 1
    assert result.skipped_signals == []
    t = result.trades.iloc[0]
    assert t["direction"] == 1
    assert t["exit_reason"] == "end_of_data"

    assert result.metrics["n_trades"] == 1
    assert result.metrics["total_net_pnl"] > 0
    assert result.metrics["final_equity"] > INITIAL_EQUITY
    # Account survives comfortably: far from the $100 (=stake) InsufficientMarginError
    # floor that F005-baseline.md documents as the failure mechanism for the real
    # strategy catalog under leverage=10.
    assert result.metrics["final_equity"] > 500.0
    # Clean uptrend -> tiny drawdown, nowhere near the 50% hard-reject threshold.
    assert result.metrics["max_drawdown_pct"] < 5.0


def test_new_engine_single_trade_matches_hand_calculation():
    result = _run_new_engine()
    t = result.trades.iloc[0]
    entry_price, exit_price = float(t["entry_price"]), float(t["exit_price"])
    notional = STAKE * LEVERAGE
    quantity = notional / entry_price
    gross_pnl = quantity * (exit_price - entry_price)
    exit_notional = exit_price * quantity
    total_costs = (
        costs.commission(notional, COMMISSION_RATE_BPS)
        + costs.commission(exit_notional, COMMISSION_RATE_BPS)
        + costs.spread_cost(notional, HALF_SPREAD_BPS)
        + costs.spread_cost(exit_notional, HALF_SPREAD_BPS)
        + costs.slippage_cost(notional, bps=SLIPPAGE_BPS)
    )
    hand_net_pnl = gross_pnl - total_costs

    assert float(t["gross_pnl"]) == pytest.approx(gross_pnl)
    assert float(t["total_costs"]) == pytest.approx(total_costs)
    assert float(t["net_pnl"]) == pytest.approx(hand_net_pnl)


def test_regularity_meets_target_in_the_one_full_valid_month():
    result = _run_new_engine()
    _, months = regularity.compute_regularity(result.equity_curve)

    jan = next(m for m in months if (m.year, m.month) == (2024, 1))
    feb = next(m for m in months if (m.year, m.month) == (2024, 2))
    mar = next(m for m in months if (m.year, m.month) == (2024, 3))

    # Jan 2024: curve starts mid-month (Jan 15) -> partial, AND its first day
    # is the whole curve's first day -> missing -> invalidated (regularity.py's
    # documented "first day of any curve is always missing" rule).
    assert jan.is_partial is True
    assert jan.is_valid is False
    assert jan.target_met is None

    # Feb 2024: the one full calendar month entirely inside the fixture's
    # range, no missing days -> valid, non-partial, and the clean uptrend
    # makes every single day of it positive.
    assert feb.is_partial is False
    assert feb.is_valid is True
    assert feb.n == 29  # 2024 is a leap year
    assert feb.positive_day_pct == pytest.approx(100.0)
    assert feb.deviation_pct == pytest.approx(0.0)
    assert feb.target_met is True

    # Mar 2024: only 1 day covered by the fixture -> partial, not compared
    # against the full-month 20% tolerance.
    assert mar.is_partial is True


def test_old_engine_trade_matches_new_engine_gross_pnl():
    """strategy.backtest_trailing (F004-era, free/no-cost) on the same signal/SL params."""
    df = _load_fixture()
    df2 = strategy.add_indicators(df.copy())
    df2["signal"] = strategy.STRATEGY_CATALOG[STRATEGY_NAME](df2)
    old_trades, _old_metrics = strategy.backtest_trailing(
        df2,
        atr_multiplier=ATR_MULTIPLIER, max_sl_pct=MAX_SL_PCT,
        activate_pct=ACTIVATE_PCT, trail_pct=TRAIL_PCT,
        leverage=LEVERAGE, stake=STAKE,
        entry_on_open=True, cooldown_candles=COOLDOWN_CANDLES,
    )

    assert len(old_trades) == 1
    old_trade = old_trades.iloc[0]
    assert old_trade["pnl_usd"] > 0  # clearly positive, no costs in this engine

    new_result = _run_new_engine()
    new_trade = new_result.trades.iloc[0]
    # Same signal, same entry/exit timing/prices (entry_on_open=True both sides) ->
    # old engine's cost-free pnl_usd should equal the new engine's gross_pnl (pre-cost).
    assert float(old_trade["pnl_usd"]) == pytest.approx(float(new_trade["gross_pnl"]), abs=1e-6)
