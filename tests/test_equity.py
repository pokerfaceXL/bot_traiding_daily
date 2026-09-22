import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import equity


def test_open_position_computes_notional_margin_quantity():
    # stake=100, leverage=5 -> notional=500, margin=notional/leverage=100, qty=500/entry_price
    portfolio = equity.Portfolio(initial_equity=500.0)
    pos = portfolio.open_position(
        "p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0
    )
    assert pos.notional == 500.0
    assert pos.margin == 100.0
    assert pos.quantity == 25.0
    assert portfolio.committed_margin == 100.0


def test_two_simultaneous_positions_share_one_500_usd_pool():
    # initial_equity=500. Two positions, each stake=100, leverage=5 -> margin=100 each.
    # After opening both: committed_margin = 100+100 = 200, equity unchanged at 500
    # (no PnL yet), available_margin = 500 - 200 - 0 = 300.
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)
    portfolio.open_position("p2", "ETHUSDT", direction=-1, entry_price=2000.0, entry_time=0, stake=100.0, leverage=5.0)

    assert portfolio.committed_margin == 200.0
    assert portfolio.equity() == 500.0
    assert portfolio.available_margin() == 300.0

    # A third position with margin=100 must still fit (300 available >= 100).
    portfolio.open_position("p3", "BTCUSDT", direction=1, entry_price=30000.0, entry_time=0, stake=100.0, leverage=5.0)
    assert portfolio.committed_margin == 300.0
    assert portfolio.available_margin() == 200.0


def test_new_position_rejected_when_margin_insufficient():
    # initial_equity=500. Open 4 positions of margin=100 each -> committed_margin=400,
    # available=100. A 5th position also needs margin=100, which exactly fits (100>=100)
    # so it must succeed; a 6th needs margin=100 with only 0 available -> must be rejected.
    portfolio = equity.Portfolio(initial_equity=500.0)
    for i in range(4):
        portfolio.open_position(
            f"p{i}", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=3.0
        )
    assert portfolio.committed_margin == 400.0
    assert portfolio.available_margin() == 100.0

    portfolio.open_position("p4", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=3.0)
    assert portfolio.committed_margin == 500.0
    assert portfolio.available_margin() == 0.0

    with pytest.raises(equity.InsufficientMarginError):
        portfolio.open_position("p5", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=3.0)
    # rejected position must not have been recorded
    assert "p5" not in portfolio.positions
    assert portfolio.committed_margin == 500.0


def test_new_position_rejected_by_fee_buffer_even_with_nominal_room():
    # available_margin without buffer = 500 - 450 = 50, exactly enough for a margin=50
    # position -- but a fee_buffer of 10 reserved for exit costs makes 50 < 50+10=60
    # required headroom, so it must be rejected.
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=450.0, leverage=1.0)
    assert portfolio.available_margin() == 50.0

    with pytest.raises(equity.InsufficientMarginError):
        portfolio.open_position(
            "p2", "ETHUSDT", direction=1, entry_price=2000.0, entry_time=0,
            stake=50.0, leverage=1.0, fee_buffer=10.0,
        )
    assert "p2" not in portfolio.positions


def test_mark_to_market_includes_unrealized_pnl_of_open_position():
    # long SOLUSDT: entry=20, stake=100, leverage=5 -> notional=500, qty=25.
    # mark price drops to 18 -> unrealized pnl = 1 * (18-20) * 25 = -50.
    # equity = 500 (initial) + 0 (realized) + (-50) = 450, while margin=100 stays committed.
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)

    current_equity, drawdown_pct = portfolio.mark_to_market({"p1": 18.0})
    assert current_equity == 450.0
    # peak_equity started at 500 (initial), current 450 -> dd = 100*(500-450)/500 = 10.0%
    assert drawdown_pct == 10.0
    assert portfolio.peak_equity == 500.0


def test_mark_to_market_drawdown_while_losing_position_still_open():
    # Same setup as above, position keeps losing further before it's ever closed:
    # mark price drops to 16 -> unrealized pnl = 1*(16-20)*25 = -100 -> equity = 400.
    # dd = 100*(500-400)/500 = 20.0%. Position is still open the whole time (never closed).
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)

    portfolio.mark_to_market({"p1": 18.0})
    current_equity, drawdown_pct = portfolio.mark_to_market({"p1": 16.0})

    assert current_equity == 400.0
    assert drawdown_pct == 20.0
    assert portfolio.realized_pnl == 0.0  # nothing realized -- position never closed
    assert "p1" in portfolio.positions  # still open


def test_peak_equity_updates_when_equity_recovers_above_prior_peak():
    # equity dips to 450 (dd=10%), then position recovers to mark price 22 ->
    # unrealized pnl = 1*(22-20)*25 = +50 -> equity = 550, new peak, dd back to 0.
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)

    portfolio.mark_to_market({"p1": 18.0})
    current_equity, drawdown_pct = portfolio.mark_to_market({"p1": 22.0})

    assert current_equity == 550.0
    assert drawdown_pct == 0.0
    assert portfolio.peak_equity == 550.0


def test_close_position_realizes_net_pnl_and_frees_margin():
    # long SOLUSDT: entry=20, stake=100, leverage=5 -> notional=500, qty=25.
    # exit=22 -> gross pnl = 1*(22-20)*25 = 50.00
    # exit_notional = 22*25 = 550.
    # commission 10 bps: entry 500*0.0010=0.50, exit 550*0.0010=0.55, total=1.05
    # spread 5 bps: entry 500*0.0005=0.25, exit 550*0.0005=0.275, total=0.525
    # slippage: 500*0.0002 (2bps) + fixed 0.10 = 0.10+0.10 = 0.20
    # total_costs = 1.05 + 0.525 + 0.20 = 1.775
    # no funding events -> funding_pnl = 0.0
    # net_pnl = 50.00 - 1.775 + 0.0 = 48.225
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)
    assert portfolio.committed_margin == 100.0

    trade = portfolio.close_position(
        "p1", exit_price=22.0, exit_time=1,
        commission_rate_bps=10.0, half_spread_bps=5.0,
        slippage_bps=2.0, slippage_fixed=0.10,
    )

    assert trade.gross_pnl == 50.0
    assert round(trade.total_costs, 10) == 1.775
    assert trade.funding_pnl == 0.0
    assert round(trade.net_pnl, 10) == 48.225

    assert round(portfolio.realized_pnl, 10) == 48.225
    assert portfolio.committed_margin == 0.0
    assert "p1" not in portfolio.positions
    assert round(portfolio.equity(), 10) == 548.225


def test_sequence_of_open_close_matches_manual_running_equity():
    # Trade 1: long SOLUSDT entry=20 exit=22, stake=100 leverage=5, no costs -> net=+50.
    #   equity after close: 500 + 50 = 550.
    # Trade 2: short ETHUSDT entry=2000 exit=1980, stake=100 leverage=2 -> notional=200,
    #   qty=200/2000=0.1. gross = -1*(1980-2000)*0.1 = -1*(-20)*0.1 = 2.0 -- wait short pnl:
    #   direction=-1, unrealized = -1*(exit-entry)*qty = -1*(1980-2000)*0.1 = -1*(-20)*0.1=2.0
    #   so short profits when price falls: gross=+2.0. No costs -> net=+2.0.
    #   equity after close: 550 + 2.0 = 552.0
    portfolio = equity.Portfolio(initial_equity=500.0)

    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)
    trade1 = portfolio.close_position("p1", exit_price=22.0, exit_time=1)
    assert trade1.net_pnl == 50.0
    assert portfolio.equity() == 550.0

    portfolio.open_position("p2", "ETHUSDT", direction=-1, entry_price=2000.0, entry_time=1, stake=100.0, leverage=2.0)
    trade2 = portfolio.close_position("p2", exit_price=1980.0, exit_time=2)
    assert round(trade2.net_pnl, 10) == 2.0
    assert round(portfolio.equity(), 10) == 552.0
    assert round(portfolio.realized_pnl, 10) == 52.0
    assert portfolio.committed_margin == 0.0
    assert portfolio.positions == {}


def test_close_position_applies_funding_pnl():
    # long SOLUSDT entry=20 exit=20 (flat price, no gross pnl), stake=100 leverage=5 ->
    # notional=500. One funding event inside holding window with rate=0.0001 (1bp):
    # funding_payment(long, notional=500, rate=0.0001) = -(+1)*500*0.0001 = -0.05
    # gross_pnl=0, no commission/spread/slippage configured -> total_costs=0
    # net_pnl = 0 - 0 + (-0.05) = -0.05
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)

    trade = portfolio.close_position(
        "p1", exit_price=20.0, exit_time=10,
        funding_events=[(5, 0.0001)],
    )

    assert trade.gross_pnl == 0.0
    assert round(trade.funding_pnl, 10) == -0.05
    assert round(trade.net_pnl, 10) == -0.05
    assert round(portfolio.realized_pnl, 10) == -0.05


def test_open_loss_reduces_available_margin_for_next_position_via_mark_to_market():
    # This is the discriminating check for the "available equity" design decision documented
    # in equity.py's module docstring: rejection MUST use current mark-to-market equity, not a
    # frozen initial_equity, otherwise a loss on one open position would let a second position
    # spend money that no longer exists.
    # p1: long SOLUSDT entry=20, stake=400, leverage=1 -> notional=400, margin=400, qty=20.
    # Price drops to 15 -> unrealized pnl = 1*(15-20)*20 = -100 -> equity = 500-100 = 400.
    # available_margin = equity(400) - committed_margin(400) - buffer(0) = 0.
    # A naive "initial_equity - committed_margin" formula would wrongly report 500-400=100
    # available and let a margin=100 position through; the correct MTM formula must reject it.
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=400.0, leverage=1.0)

    equity_after_loss, _ = portfolio.mark_to_market({"p1": 15.0})
    assert equity_after_loss == 400.0
    assert portfolio.available_margin({"p1": 15.0}) == 0.0

    with pytest.raises(equity.InsufficientMarginError):
        portfolio.open_position(
            "p2", "ETHUSDT", direction=1, entry_price=2000.0, entry_time=1,
            stake=100.0, leverage=1.0, mark_prices={"p1": 15.0},
        )
    assert "p2" not in portfolio.positions


def test_close_unknown_position_raises_key_error():
    portfolio = equity.Portfolio(initial_equity=500.0)
    with pytest.raises(KeyError):
        portfolio.close_position("missing", exit_price=1.0, exit_time=0)


def test_open_position_rejects_invalid_direction():
    portfolio = equity.Portfolio(initial_equity=500.0)
    with pytest.raises(ValueError):
        portfolio.open_position("p1", "SOLUSDT", direction=0, entry_price=20.0, entry_time=0)


def test_open_position_duplicate_id_rejected():
    portfolio = equity.Portfolio(initial_equity=500.0)
    portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=20.0, entry_time=0, stake=100.0, leverage=5.0)
    with pytest.raises(ValueError):
        portfolio.open_position("p1", "SOLUSDT", direction=1, entry_price=21.0, entry_time=1, stake=100.0, leverage=5.0)
