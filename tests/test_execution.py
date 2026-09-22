import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import execution
from execution import Bar, EntryFill, ExitTrigger, OrderType, TriggerKind


def test_market_entry_fills_at_next_bars_open():
    # Signal computed on candle N (already closed). Earliest possible fill is
    # candle N+1's open -- never candle N's close (look-ahead).
    next_bar = Bar(open=101.0, high=103.0, low=100.5, close=102.0)
    fill = execution.resolve_entry_fill(OrderType.MARKET, direction=1, next_bar=next_bar)
    assert fill.filled is True
    assert fill.fill_price == 101.0
    assert fill.order_type == OrderType.MARKET


def test_limit_entry_does_not_fill_when_price_never_touches_it():
    # Long limit buy at 90; next bar's range [92, 98] never reaches down to 90 ->
    # order must NOT be silently filled at a worse price -- it stays unfilled.
    next_bar = Bar(open=95.0, high=98.0, low=92.0, close=96.0)
    fill = execution.resolve_entry_fill(OrderType.LIMIT, direction=1, next_bar=next_bar, limit_price=90.0)
    assert fill.filled is False
    assert fill.fill_price is None


def test_limit_entry_fills_at_limit_price_when_range_touches_it():
    # Long limit buy at 93; next bar's range [92, 98] touches 93, open=95>93
    # (not gapped through) -> fills exactly at the limit price, not at open.
    next_bar = Bar(open=95.0, high=98.0, low=92.0, close=96.0)
    fill = execution.resolve_entry_fill(OrderType.LIMIT, direction=1, next_bar=next_bar, limit_price=93.0)
    assert fill.filled is True
    assert fill.fill_price == 93.0


def test_limit_entry_fills_at_better_open_when_bar_gaps_through_limit():
    # Long limit buy at 90; bar opens at 88, already below the limit -> the
    # realistic fill is the better price (88), not the stale limit price.
    next_bar = Bar(open=88.0, high=91.0, low=87.0, close=89.0)
    fill = execution.resolve_entry_fill(OrderType.LIMIT, direction=1, next_bar=next_bar, limit_price=90.0)
    assert fill.filled is True
    assert fill.fill_price == 88.0


def test_short_limit_entry_fills_only_when_range_reaches_up_to_it():
    # Short limit sell at 105; next bar's range [98, 103] never reaches 105 -> unfilled.
    next_bar = Bar(open=100.0, high=103.0, low=98.0, close=101.0)
    fill = execution.resolve_entry_fill(OrderType.LIMIT, direction=-1, next_bar=next_bar, limit_price=105.0)
    assert fill.filled is False
    assert fill.fill_price is None

    # Same short limit at 102; range [98, 103] touches it, open=100<102 (not gapped)
    # -> fills exactly at 102.
    next_bar2 = Bar(open=100.0, high=103.0, low=98.0, close=101.0)
    fill2 = execution.resolve_entry_fill(OrderType.LIMIT, direction=-1, next_bar=next_bar2, limit_price=102.0)
    assert fill2.filled is True
    assert fill2.fill_price == 102.0


def test_normal_stop_loss_touch_mid_bar_long():
    # Long position, SL=97. Bar: open=100, high=102, low=95 -- SL is touched
    # mid-bar (low<=97), but open=100 is still above SL -> normal (non-gap)
    # fill exactly at the stop level.
    bar = Bar(open=100.0, high=102.0, low=95.0, close=99.0)
    trigger = execution.resolve_stop_take_within_bar(direction=1, bar=bar, stop_loss=97.0, take_profit=None)
    assert trigger.kind == TriggerKind.STOP_LOSS
    assert trigger.fill_price == 97.0
    assert trigger.is_gap_fill is False


def test_take_profit_touch_mid_bar_long():
    # Long position, TP=103. Bar: open=100, high=105, low=99 -- TP touched
    # mid-bar (high>=103), open=100 below TP -> normal (non-gap) fill at TP level.
    bar = Bar(open=100.0, high=105.0, low=99.0, close=104.0)
    trigger = execution.resolve_stop_take_within_bar(direction=1, bar=bar, stop_loss=None, take_profit=103.0)
    assert trigger.kind == TriggerKind.TAKE_PROFIT
    assert trigger.fill_price == 103.0
    assert trigger.is_gap_fill is False


def test_both_sl_and_tp_inside_same_bar_conservative_stop_wins():
    # Discriminating check for the F001 discrepancy #6 (Bar Magnifier ambiguous
    # ordering): SL=97 and TP=103 are BOTH inside this bar's [low=95, high=105]
    # range. Nothing in the OHLC tells us which was touched first. The module's
    # documented worst-case assumption is that price moved toward the stop
    # first, so the conservative (pessimistic) STOP_LOSS trigger must win over
    # the optimistic TAKE_PROFIT -- never the other way around.
    bar = Bar(open=100.0, high=105.0, low=95.0, close=101.0)
    trigger = execution.resolve_stop_take_within_bar(direction=1, bar=bar, stop_loss=97.0, take_profit=103.0)
    assert trigger.kind == TriggerKind.STOP_LOSS
    assert trigger.fill_price == 97.0
    assert trigger.is_gap_fill is False


def test_both_sl_and_tp_inside_same_bar_conservative_stop_wins_short():
    # Same discriminating check, short direction: SL=103 (above entry), TP=97
    # (below entry), both inside [low=95, high=105] -> SL still wins.
    bar = Bar(open=100.0, high=105.0, low=95.0, close=99.0)
    trigger = execution.resolve_stop_take_within_bar(direction=-1, bar=bar, stop_loss=103.0, take_profit=97.0)
    assert trigger.kind == TriggerKind.STOP_LOSS
    assert trigger.fill_price == 103.0
    assert trigger.is_gap_fill is False


def test_gap_through_stop_at_open_long():
    # Long position, SL=97. Bar OPENS at 96, already below the stop (a gap
    # through the stop level) -> fill must be at the bar's open (96), NOT at
    # the stop price (97) -- and flagged as a gap-fill so it's distinguishable
    # from a normal stop touch.
    bar = Bar(open=96.0, high=98.0, low=94.0, close=95.0)
    trigger = execution.resolve_stop_take_within_bar(direction=1, bar=bar, stop_loss=97.0, take_profit=None)
    assert trigger.kind == TriggerKind.STOP_LOSS
    assert trigger.fill_price == 96.0
    assert trigger.is_gap_fill is True


def test_gap_through_stop_at_open_short():
    # Short position, SL=103. Bar opens at 104, already above the stop ->
    # gap-fill at the open (104), not at 103.
    bar = Bar(open=104.0, high=106.0, low=102.0, close=105.0)
    trigger = execution.resolve_stop_take_within_bar(direction=-1, bar=bar, stop_loss=103.0, take_profit=None)
    assert trigger.kind == TriggerKind.STOP_LOSS
    assert trigger.fill_price == 104.0
    assert trigger.is_gap_fill is True


def test_no_trigger_when_neither_level_touched():
    bar = Bar(open=100.0, high=101.0, low=99.0, close=100.5)
    trigger = execution.resolve_stop_take_within_bar(direction=1, bar=bar, stop_loss=90.0, take_profit=110.0)
    assert trigger.kind == TriggerKind.NONE
    assert trigger.fill_price is None
    assert trigger.is_gap_fill is False


def test_resolve_level_fill_rejects_unknown_kind():
    bar = Bar(open=100.0, high=101.0, low=99.0, close=100.5)
    with pytest.raises(ValueError):
        execution.resolve_level_fill(1, bar, 100.0, TriggerKind.NONE)


def test_resolve_entry_fill_rejects_invalid_direction():
    bar = Bar(open=100.0, high=101.0, low=99.0, close=100.5)
    with pytest.raises(ValueError):
        execution.resolve_entry_fill(OrderType.MARKET, direction=0, next_bar=bar)


def test_resolve_stop_take_rejects_invalid_direction():
    bar = Bar(open=100.0, high=101.0, low=99.0, close=100.5)
    with pytest.raises(ValueError):
        execution.resolve_stop_take_within_bar(direction=2, bar=bar, stop_loss=90.0)


def test_limit_entry_requires_limit_price():
    bar = Bar(open=100.0, high=101.0, low=99.0, close=100.5)
    with pytest.raises(ValueError):
        execution.resolve_entry_fill(OrderType.LIMIT, direction=1, next_bar=bar)
