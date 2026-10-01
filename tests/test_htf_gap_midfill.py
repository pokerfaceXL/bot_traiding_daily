"""Formula and causality checks for the frozen F006 HTF-FVG midfill family."""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import htf_gap_midfill


def _frame(rows, freq="1h"):
    index = pd.date_range("2024-01-01", periods=len(rows), freq=freq, tz="UTC")
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=index).assign(volume=1.0)


def _bull_midfill_rows():
    # With block_bars=1: bars 0/1/2 create bull FVG [10, 12]. Bar 3 makes the
    # 3-block close comparison bullish; bar 4 is then its first legal midfill.
    return [
        (9, 10, 8, 9), (9, 11, 9, 10), (12, 13, 12, 13),
        (13, 14, 12, 14), (12, 13, 11, 10.8), (11, 13, 11, 12),
    ]


def test_first_midfill_waits_for_a_later_continuation_close_within_rmax():
    signal = htf_gap_midfill.compute_htf_fvg_midfill_signal(
        _frame(_bull_midfill_rows()), 2, block_bars=1
    )
    # Bar 4 touches midpoint 11 but is neither reject nor bullish continuation;
    # bar 5 is the single allowed later bar and closes bullish.
    assert signal.tolist() == [0, 0, 0, 0, 0, 1]


def test_opposite_bias_at_first_midpoint_touch_retires_the_gap_before_a_later_bias_flip():
    # Bars 0/1/2 create bull FVG [10, 12]. At bar 7 the FIRST midpoint touch
    # occurs while the completed-block bias is bearish (bar 6 close 10.5 vs bar
    # 3 close 14). Bar 8 touches again after the bias turns bullish. The first
    # touch has consumed the FVG, so the old delayed +1 at index 8 is forbidden.
    rows = [
        (9, 10, 8, 9), (9, 11, 9, 10), (12, 13, 12, 13),
        (13, 14, 11, 14), (13, 14, 12, 13), (12, 13, 11.5, 12),
        (11, 11, 10.1, 10.5), (12, 13.5, 11, 13.2), (12, 14, 11, 13.5),
    ]
    signal = htf_gap_midfill.compute_htf_fvg_midfill_signal(_frame(rows), 3, block_bars=1)
    assert signal.tolist() == [0] * len(rows)


def test_rmax_one_expires_after_a_noncontinuation_midfill():
    signal = htf_gap_midfill.compute_htf_fvg_midfill_signal(
        _frame(_bull_midfill_rows()), 1, block_bars=1
    )
    assert signal.tolist() == [0, 0, 0, 0, 0, 0]


def test_far_side_reject_is_an_immediate_bull_signal_and_full_fill_cancels():
    reject = _bull_midfill_rows()[:4] + [(12, 13, 11, 12)]
    assert htf_gap_midfill.compute_htf_fvg_midfill_signal(_frame(reject), 1, block_bars=1).tolist()[-1] == 1

    filled = _bull_midfill_rows()[:4] + [(12, 13, 10, 12)]
    assert htf_gap_midfill.compute_htf_fvg_midfill_signal(_frame(filled), 1, block_bars=1).tolist()[-1] == 0


def test_bear_far_side_reject_is_mirrored():
    # Bars 0/1/2 create bear FVG [8, 10]; bar 3 establishes bear bias and bar 4
    # wicks through midpoint 9 before closing back below it.
    rows = [
        (9, 10, 8, 9), (9, 9, 7, 8), (7, 7, 6, 7),
        (7, 7, 6, 6), (8, 7.6, 6, 7),
    ]
    signal = htf_gap_midfill.compute_htf_fvg_midfill_signal(_frame(rows), 1, block_bars=1)
    assert signal.tolist() == [0, 0, 0, 0, -1]


def test_completed_htf_blocks_not_partial_bars_define_the_signal_and_future_is_irrelevant():
    # A 60m input needs four bars per 4h block. The 12th bar only CREATES an FVG;
    # it cannot trigger it. Appending arbitrary future data cannot move the prefix.
    rows = []
    for base in (8, 9, 12, 13, 12):
        rows.extend([(base, base + 1, base, base + 0.5)] * 4)
    df = _frame(rows)
    prefix = htf_gap_midfill.compute_htf_fvg_midfill_signal(df, 1)
    assert prefix.iloc[:12].eq(0).all()
    future = pd.concat([df, _frame([(100, 120, 80, 110)] * 8).set_axis(
        pd.date_range(df.index[-1] + pd.Timedelta(hours=1), periods=8, freq="1h", tz="UTC")
    )])
    expanded = htf_gap_midfill.compute_htf_fvg_midfill_signal(future, 1)
    assert expanded.iloc[:len(df)].tolist() == prefix.tolist()


def test_catalog_names_are_frozen_and_input_is_not_mutated():
    df = _frame(_bull_midfill_rows())
    before = df.copy(deep=True)
    entries = htf_gap_midfill.catalog_entries()
    assert set(entries) == {"HTF_FVG_MID_R1", "HTF_FVG_MID_R2", "HTF_FVG_MID_R3"}
    for fn in entries.values():
        fn(df)
    pd.testing.assert_frame_equal(df, before)
