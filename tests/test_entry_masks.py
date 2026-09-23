import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import entry_masks

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")

# The deterministic run-structure fixture named in the F006 one-shot ticket. It
# contains every boundary case the mask has to get right in one series:
#   idx 1  -- a call opening from flat
#   idx 5  -- the SAME direction returning after a flat gap: a NEW call, not a
#             continuation of the run at idx 1-3
#   idx 7  -- a direct +1 -> -1 flip with no flat bar between: a new call
#   idx 10 -- a call opening on the last bar
SIGNAL_FIXTURE = [0, 1, 1, 1, 0, 1, 1, -1, -1, 0, -1]
EXPECTED_MASK = [False, True, False, False, False, True, False, True, False, False, True]
EXPECTED_CALL_ID = [-1, 0, 0, 0, -1, 1, 1, 2, 2, -1, 3]


def _series(values, index=None):
    return pd.Series(values, index=index if index is not None else pd.RangeIndex(len(values)))


def test_mask_marks_exactly_the_first_bar_of_each_nonzero_run():
    mask = entry_masks.one_shot_entry_mask(_series(SIGNAL_FIXTURE))
    assert mask.tolist() == EXPECTED_MASK
    assert mask.dtype == bool
    # Stated as counts too, so a mask that shifted by one bar but kept the right
    # number of Trues cannot pass on the count alone.
    assert int(mask.sum()) == 4


def test_same_direction_after_flat_gap_is_a_new_call():
    # +1 at idx 5 follows +1 at idx 3 with one 0 bar between: the underlying
    # condition switched off and back on, so idx 5 is eligible.
    mask = entry_masks.one_shot_entry_mask(_series(SIGNAL_FIXTURE))
    assert bool(mask.iloc[5]) is True
    assert bool(mask.iloc[3]) is False


def test_direct_flip_without_a_flat_bar_is_a_new_call():
    mask = entry_masks.one_shot_entry_mask(_series([1, 1, -1, -1, 1]))
    assert mask.tolist() == [True, False, True, False, True]


def test_no_flat_bar_is_ever_eligible():
    sig = _series(SIGNAL_FIXTURE)
    mask = entry_masks.one_shot_entry_mask(sig)
    assert not mask[sig == 0].any()


def test_call_id_numbers_runs_and_marks_flat_bars():
    ids = entry_masks.call_id(_series(SIGNAL_FIXTURE))
    assert ids.tolist() == EXPECTED_CALL_ID


def test_nonzero_first_bar_opens_a_call():
    assert entry_masks.one_shot_entry_mask(_series([1, 1, 0])).tolist() == [True, False, False]
    assert entry_masks.one_shot_entry_mask(_series([-1])).tolist() == [True]


def test_nan_is_treated_as_flat_like_the_engine_does():
    # run_backtest builds its integer signal with .fillna(0).astype(int); a NaN bar
    # is flat there, so it must break a run here too -- 1, NaN, 1 is two calls.
    mask = entry_masks.one_shot_entry_mask(_series([1.0, np.nan, 1.0]))
    assert mask.tolist() == [True, False, True]


def test_all_flat_and_empty_series_produce_no_eligible_bar():
    assert entry_masks.one_shot_entry_mask(_series([0, 0, 0])).tolist() == [False, False, False]
    empty = entry_masks.one_shot_entry_mask(pd.Series([], dtype=float))
    assert empty.empty and empty.dtype == bool


def test_index_is_preserved_so_run_backtest_reindex_is_a_no_op():
    idx = pd.date_range("2024-01-01", periods=len(SIGNAL_FIXTURE), freq="4h", tz="UTC")
    mask = entry_masks.one_shot_entry_mask(_series(SIGNAL_FIXTURE, index=idx))
    assert mask.index.equals(idx)


def test_signal_series_matches_the_frame_run_backtest_actually_uses():
    df = pd.read_csv(FIXTURE, index_col=0, parse_dates=True)
    sig = entry_masks.strategy_signal_series(df, "RSI14_7030", interval="240")
    # Same pipeline as the engine: the index must line up bar for bar with the
    # engine's own equity curve (one row per post-filter bar), otherwise the mask
    # would be reindexed to False on the missing bars and silently block entries.
    res = be.run_backtest(df, "RSI14_7030", interval="240")
    assert sig.index.equals(res.equity_curve.index)


def test_one_shot_mask_gives_at_most_one_entry_per_call_in_the_engine():
    # End-to-end: the mask is only useful if the engine's step-4 gate turns it into
    # "one entry per directional call". EMA_8_21 is chosen deliberately -- it is a
    # persistent always-in-market state, the shape the hypothesis is about.
    df = pd.read_csv(FIXTURE, index_col=0, parse_dates=True)
    sig = entry_masks.strategy_signal_series(df, "EMA_8_21", interval="240")
    mask = entry_masks.one_shot_entry_mask(sig)
    ids = entry_masks.call_id(sig)

    baseline = be.run_backtest(df, "EMA_8_21", interval="240")
    masked = be.run_backtest(df, "EMA_8_21", interval="240", entry_regime_mask=mask)

    assert baseline.metrics["n_trades"] > masked.metrics["n_trades"] > 0  # the re-entry chains are real
    assert masked.metrics["n_trades"] <= int(mask.sum())

    # Every entry fills at the bar AFTER the bar that queued it, so the queue bar of
    # each trade must be an eligible bar, and no two trades may share a call.
    positions = {ts: i for i, ts in enumerate(sig.index)}
    call_ids_used = []
    for entry_time in masked.trades["entry_time"]:
        queue_i = positions[entry_time] - 1
        assert bool(mask.iloc[queue_i]), f"entry at {entry_time} was queued on an ineligible bar"
        call_ids_used.append(int(ids.iloc[queue_i]))
    assert len(call_ids_used) == len(set(call_ids_used)), "two entries into the same directional call"
