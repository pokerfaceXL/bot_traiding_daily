import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import costs


def test_commission_basic_rate():
    # notional=1000, rate=10 bps = 0.10% -> 1000 * 0.0010 = 1.00
    assert costs.commission(1000.0, 10.0) == 1.0


def test_spread_cost_basic_rate():
    # notional=2000, half-spread=5 bps = 0.05% -> 2000 * 0.0005 = 1.00
    assert costs.spread_cost(2000.0, 5.0) == 1.0


def test_slippage_cost_bps_and_fixed():
    # notional=500, bps=20 (0.20%) -> 500*0.0020 = 1.00, plus fixed 0.25 -> 1.25
    assert costs.slippage_cost(500.0, bps=20.0, fixed=0.25) == 1.25


def test_profitable_long_minus_commission_and_slippage():
    # Long: entry=100, exit=110, qty=1 -> entry_notional=100, exit_notional=110
    # gross pnl = (exit - entry) * qty = (110 - 100) * 1 = 10.00
    entry_price, exit_price, qty = 100.0, 110.0, 1.0
    entry_notional = entry_price * qty
    exit_notional = exit_price * qty
    gross_pnl = (exit_price - entry_price) * qty
    assert gross_pnl == 10.0

    # commission taker 10 bps on each side:
    # entry: 100 * 0.0010 = 0.10 ; exit: 110 * 0.0010 = 0.11 ; total = 0.21
    entry_comm = costs.commission(entry_notional, 10.0)
    exit_comm = costs.commission(exit_notional, 10.0)
    assert entry_comm == 0.10
    assert exit_comm == 0.11

    # slippage 5 bps on entry notional only: 100 * 0.0005 = 0.05
    slip = costs.slippage_cost(entry_notional, bps=5.0)
    assert slip == 0.05

    # net = gross - (0.10 + 0.11) - 0.05 = 10 - 0.21 - 0.05 = 9.74
    net_pnl = gross_pnl - (entry_comm + exit_comm) - slip
    assert round(net_pnl, 10) == 9.74


def test_losing_short_minus_commission_and_fixed_slippage():
    # Short: entry=100, exit=105, qty=2 -> entry_notional=200, exit_notional=210
    # gross pnl (short) = (entry - exit) * qty = (100 - 105) * 2 = -10.00
    entry_price, exit_price, qty = 100.0, 105.0, 2.0
    entry_notional = entry_price * qty
    exit_notional = exit_price * qty
    gross_pnl = (entry_price - exit_price) * qty
    assert gross_pnl == -10.0

    # commission taker 10 bps on each side:
    # entry: 200 * 0.0010 = 0.20 ; exit: 210 * 0.0010 = 0.21 ; total = 0.41
    entry_comm = costs.commission(entry_notional, 10.0)
    exit_comm = costs.commission(exit_notional, 10.0)
    assert entry_comm == 0.20
    assert round(exit_comm, 10) == 0.21

    # fixed slippage of 0.50 applied once
    slip = costs.slippage_cost(entry_notional, fixed=0.50)
    assert slip == 0.50

    # net = -10 - (0.20 + 0.21) - 0.50 = -10.91
    net_pnl = gross_pnl - (entry_comm + exit_comm) - slip
    assert round(net_pnl, 10) == -10.91


def test_trade_with_spread_cost_on_entry_and_exit():
    # entry=50, exit=55, qty=10 -> entry_notional=500, exit_notional=550
    # gross pnl = (55 - 50) * 10 = 50.00
    entry_price, exit_price, qty = 50.0, 55.0, 10.0
    entry_notional = entry_price * qty
    exit_notional = exit_price * qty
    gross_pnl = (exit_price - entry_price) * qty
    assert gross_pnl == 50.0

    # half-spread 8 bps applied on both sides:
    # entry: 500 * 0.0008 = 0.40 ; exit: 550 * 0.0008 = 0.44 ; total = 0.84
    entry_spread = costs.spread_cost(entry_notional, 8.0)
    exit_spread = costs.spread_cost(exit_notional, 8.0)
    assert entry_spread == 0.40
    assert round(exit_spread, 10) == 0.44

    # net = 50 - (0.40 + 0.44) = 49.16
    net_pnl = gross_pnl - (entry_spread + exit_spread)
    assert round(net_pnl, 10) == 49.16


def test_funding_payment_sign_long_pays_positive_rate():
    # long, notional=1000, funding_rate=0.0001 (1bp) -> long pays: -(+1)*1000*0.0001 = -0.10
    assert costs.funding_payment(1, 1000.0, 0.0001) == -0.10


def test_funding_payment_sign_short_receives_positive_rate():
    # short, notional=1000, funding_rate=0.0001 (1bp) -> short receives: -(-1)*1000*0.0001 = +0.10
    assert costs.funding_payment(-1, 1000.0, 0.0001) == 0.10


def test_funding_pnl_long_held_across_one_funding_timestamp():
    entry = pd.Timestamp("2026-01-01 04:00:00", tz="UTC")
    exit_ = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")
    funding_ts = pd.Timestamp("2026-01-01 08:00:00", tz="UTC")  # inside [entry, exit)
    events = [(funding_ts, 0.0001)]

    # long, notional=1000: pays -1000*0.0001 = -0.10 exactly once
    net = costs.funding_pnl(1, 1000.0, entry, exit_, events)
    assert net == -0.10


def test_funding_pnl_short_held_across_one_funding_timestamp():
    entry = pd.Timestamp("2026-01-01 04:00:00", tz="UTC")
    exit_ = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")
    funding_ts = pd.Timestamp("2026-01-01 08:00:00", tz="UTC")  # inside [entry, exit)
    events = [(funding_ts, 0.0001)]

    # short, notional=1000: receives +1000*0.0001 = +0.10 exactly once
    net = costs.funding_pnl(-1, 1000.0, entry, exit_, events)
    assert net == 0.10


def test_funding_pnl_ignores_events_outside_holding_window():
    entry = pd.Timestamp("2026-01-01 04:00:00", tz="UTC")
    exit_ = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")
    before_entry = pd.Timestamp("2026-01-01 00:00:00", tz="UTC")  # before entry -> not counted
    at_exit = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")  # position already closed -> not counted
    events = [(before_entry, 0.0001), (at_exit, 0.0001)]

    # neither event falls in [entry, exit) -> total funding cash flow = 0.00
    net = costs.funding_pnl(1, 1000.0, entry, exit_, events)
    assert net == 0.0


def test_funding_pnl_counts_event_exactly_at_entry():
    entry = pd.Timestamp("2026-01-01 04:00:00", tz="UTC")
    exit_ = pd.Timestamp("2026-01-01 12:00:00", tz="UTC")
    events = [(entry, 0.0002)]  # funding fires exactly when position opens -> counted

    # long, notional=500: pays -500*0.0002 = -0.10
    net = costs.funding_pnl(1, 500.0, entry, exit_, events)
    assert net == -0.10
