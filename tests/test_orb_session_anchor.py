"""
Regression tests for the F006 session-anchored ORB family (orb_session_anchor.py),
spec/research/F006-hypothesis-orb-session-anchor.md.

Expected arrays below were derived by hand from the fixture tables, not from running
the code: window arming on bar OPEN in [start, end), never-arm day, new-day reset,
strict inequality at the range edges, and no lookahead.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import orb_session_anchor as osa
import strategy

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")


def _frame(stamps, highs, lows, closes):
    idx = pd.DatetimeIndex(pd.to_datetime(stamps, utc=True))
    return pd.DataFrame({"open": closes, "high": highs, "low": lows, "close": closes,
                         "volume": 1.0}, index=idx)


def _hourly_day(day, rows):
    """rows: {hour: (high, low, close)} -> hourly bars at those hours of `day`."""
    hours = sorted(rows)
    return ([f"{day} {h:02d}:00" for h in hours],
            [rows[h][0] for h in hours], [rows[h][1] for h in hours], [rows[h][2] for h in hours])


def test_frozen_names_exact():
    assert list(osa.catalog_entries()) == [
        "ORB_LON_1H", "ORB_LON_2H", "ORB_LON_3H", "ORB_NY_1H", "ORB_NY_2H"]
    assert osa.SESSION_WINDOWS["ORB_NY_2H"] == ("13:30", "15:30")
    assert not any(k.startswith("ORB_UTC") for k in osa.catalog_entries())


def test_london_2h_arming_and_breakout_hourly():
    # OR = 07:00,08:00 bars -> or_high=110, or_low=90. Bars before 07 and inside OR are 0.
    s, h, l, c = _hourly_day("2024-03-04", {
        5: (200, 1, 150),   # pre-window: huge range, must be ignored and stay 0
        7: (110, 95, 100),
        8: (105, 90, 100),  # inside OR, close irrelevant
        9: (112, 99, 111),  # 111 > 110 -> +1
        10: (111, 95, 110),  # == or_high -> 0 (strict)
        11: (100, 85, 90),  # == or_low -> 0 (strict)
        12: (100, 80, 89),  # < 90 -> -1
    })
    sig = osa.compute_session_orb_signal(_frame(s, h, l, c), "07:00", "09:00")
    assert sig.tolist() == [0, 0, 0, 1, 0, 0, -1]


def test_ny_half_hour_anchor_uses_bar_open_half_open_window():
    # [13:30,14:30) on hourly bars contains only the 14:00 bar; 13:00 bar is outside.
    s, h, l, c = _hourly_day("2024-03-04", {
        13: (500, 1, 100),   # opens 13:00 < 13:30 -> not in OR
        14: (101, 99, 100),  # the whole OR
        15: (103, 100, 102),  # open 15:00 >= 14:30 -> active, 102 > 101 -> +1
    })
    assert osa.compute_session_orb_signal(_frame(s, h, l, c), "13:30", "14:30").tolist() == [0, 0, 1]
    # 2H [13:30,15:30): OR = 14:00+15:00 bars (high 103) -> 16:00 needed to trade
    s2, h2, l2, c2 = _hourly_day("2024-03-04", {14: (101, 99, 100), 15: (103, 100, 102), 16: (104, 101, 103.5)})
    assert osa.compute_session_orb_signal(_frame(s2, h2, l2, c2), "13:30", "15:30").tolist() == [0, 0, 1]


def test_never_arm_day_when_no_bar_opens_in_window():
    # 4h grid: 00,04,08,12,16,20 -- no open in [07:00,08:00) nor [13:30,15:30)
    stamps = [f"2024-03-04 {h:02d}:00" for h in (0, 4, 8, 12, 16, 20)]
    df = _frame(stamps, [10, 10, 10, 10, 99, 99], [9, 9, 9, 9, 1, 1], [9.5, 9.5, 9.5, 9.5, 50, 0.5])
    assert osa.compute_session_orb_signal(df, "07:00", "08:00").tolist() == [0] * 6
    assert osa.compute_session_orb_signal(df, "13:30", "15:30").tolist() == [0] * 6
    # [07:00,09:00) contains the 08:00 bar -> OR (10, 9); 16:00 close 50 > 10 -> +1, 20:00 0.5 < 9 -> -1
    assert osa.compute_session_orb_signal(df, "07:00", "09:00").tolist() == [0, 0, 0, 0, 1, -1]


def test_new_day_resets_and_missing_window_day_never_arms():
    d1 = _hourly_day("2024-03-04", {7: (110, 90, 100), 9: (120, 100, 115)})   # +1 on day 1
    # day 2: no 07:00 bar (gap) -> never arms even though close is far outside day-1 range
    d2 = _hourly_day("2024-03-05", {6: (300, 200, 250), 9: (300, 200, 250)})
    # day 3: fresh range (50, 40); 45 inside -> 0, 39 -> -1
    d3 = _hourly_day("2024-03-06", {7: (50, 40, 45), 8: (46, 44, 45), 9: (41, 38, 39)})
    stamps, h, l, c = (sum((a[i] for a in (d1, d2, d3)), []) for i in range(4))
    sig = osa.compute_session_orb_signal(_frame(stamps, h, l, c), "07:00", "08:00")
    assert sig.tolist() == [0, 1, 0, 0, 0, 0, -1]


def test_causality_future_bars_do_not_change_past():
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    for name, (s, e) in osa.SESSION_WINDOWS.items():
        full = osa.compute_session_orb_signal(df, s, e)
        for cut in (len(df) // 3, len(df) // 2, len(df) - 20):
            part = osa.compute_session_orb_signal(df.iloc[:cut], s, e)
            assert part.equals(full.iloc[:cut]), (name, cut)


def test_fixture_4h_grid_structure():
    # ohlcv_sample.csv is a 4h grid: LON_1H / NY_* never arm; LON_2H fires (so the
    # causality test above is not vacuous) and equals LON_3H (same single 08:00 OR bar).
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    sigs = {n: fn(df) for n, fn in osa.catalog_entries().items()}
    for n in ("ORB_LON_1H", "ORB_NY_1H", "ORB_NY_2H"):
        assert (sigs[n] == 0).all(), n
    assert (sigs["ORB_LON_2H"] != 0).sum() > 0
    assert sigs["ORB_LON_2H"].equals(sigs["ORB_LON_3H"])
    assert sigs["ORB_LON_2H"].index.equals(df.index)


def test_catalog_not_mutated_by_import():
    assert not any(k.startswith(("ORB_LON", "ORB_NY")) for k in strategy.STRATEGY_CATALOG)


def test_invalid_window_rejected():
    df = _frame(["2024-03-04 07:00"], [1], [1], [1])
    with pytest.raises(ValueError):
        osa.compute_session_orb_signal(df, "09:00", "07:00")
