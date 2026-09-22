import os
import sys
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import regularity


def test_full_month_all_positive_zero_deviation():
    # Buffer before/after April 2024 so April is a full, non-partial month
    # (first/last day of the whole curve fall outside April). One bar/day at
    # 12:00 UTC (mid-day -> unambiguous local calendar date; April 2024 is
    # fully CEST, the only 2024 spring transition is March 31, safely before
    # this range's April portion).
    idx = pd.date_range("2024-03-30 12:00:00", "2024-05-02 12:00:00", freq="D", tz="UTC")
    n = len(idx)
    assert n == 34  # Mar30, Mar31, Apr1..Apr30, May1, May2
    equity = [1000.0 + 10.0 * i for i in range(n)]
    curve = pd.DataFrame({"equity": equity}, index=idx)

    _, months = regularity.compute_regularity(curve)
    april = next(m for m in months if (m.year, m.month) == (2024, 4))

    # April has 30 calendar days, every one +10 vs its previous end-of-day
    # (equity increases by a constant 10/day across the whole curve):
    # N=30, N_plus=30, N_minus=N_zero=0.
    # positive_day_pct = 100*30/30 = 100.0 ; deviation_pct = 100*0/30 = 0.0
    assert april.n == 30
    assert april.is_partial is False
    assert april.n_missing == 0
    assert april.is_valid is True
    assert april.positive_day_pct == pytest.approx(100.0)
    assert april.deviation_pct == pytest.approx(0.0)
    assert april.target_met is True


def test_full_month_exactly_20pct_nonpositive_boundary_pass():
    # June 2024 has 30 calendar days -- 20% of 30 = 6 exactly, an integer
    # boundary (deviation_pct hits exactly 20.0, not an approximation from
    # either side).
    idx = pd.date_range("2024-05-31 12:00:00", "2024-07-01 12:00:00", freq="D", tz="UTC")
    assert len(idx) == 32  # May31, Jun1..Jun30, Jul1
    # Non-positive June days (delta <= 0 vs previous EOD): June 5, 10, 15,
    # 20, 25, 30 -- exactly 6 of the 30 June days. Every other day of the
    # whole curve (incl. the two buffer days) steps +10; those six get -5.
    nonpositive_june_days = {5, 10, 15, 20, 25, 30}
    equity = [1000.0]
    for ts in idx[1:]:
        if ts.month == 6 and ts.day in nonpositive_june_days:
            equity.append(equity[-1] - 5.0)
        else:
            equity.append(equity[-1] + 10.0)
    curve = pd.DataFrame({"equity": equity}, index=idx)

    _, months = regularity.compute_regularity(curve)
    june = next(m for m in months if (m.year, m.month) == (2024, 6))

    # N=30, N_minus=6, N_plus=24.
    # positive_day_pct = 100*24/30 = 80.0 ; deviation_pct = 100*6/30 = 20.0
    assert june.n == 30
    assert june.n_positive == 24
    assert june.n_nonpositive == 6
    assert june.is_valid is True
    assert june.positive_day_pct == pytest.approx(80.0)
    assert june.deviation_pct == pytest.approx(20.0)
    assert june.target_met is True  # boundary: deviation_pct <= 20, not < 20


def test_full_month_just_over_20pct_nonpositive_fails():
    idx = pd.date_range("2024-08-31 12:00:00", "2024-10-01 12:00:00", freq="D", tz="UTC")
    assert len(idx) == 32  # Aug31, Sep1..Sep30, Oct1
    nonpositive_sep_days = {3, 7, 11, 15, 19, 23, 27}  # 7 of the 30 September days
    equity = [1000.0]
    for ts in idx[1:]:
        if ts.month == 9 and ts.day in nonpositive_sep_days:
            equity.append(equity[-1] - 5.0)
        else:
            equity.append(equity[-1] + 10.0)
    curve = pd.DataFrame({"equity": equity}, index=idx)

    _, months = regularity.compute_regularity(curve)
    september = next(m for m in months if (m.year, m.month) == (2024, 9))

    # N=30, N_minus=7, N_plus=23.
    # positive_day_pct = 100*23/30 = 76.666... ; deviation_pct = 100*7/30 = 23.333...
    assert september.n == 30
    assert september.n_nonpositive == 7
    assert september.positive_day_pct == pytest.approx(100.0 * 23 / 30)
    assert september.deviation_pct == pytest.approx(100.0 * 7 / 30)
    assert september.deviation_pct > 20.0
    assert september.target_met is False


def test_exact_zero_pnl_day_is_nonpositive_not_positive_not_missing():
    idx = pd.date_range("2024-06-10 12:00:00", periods=3, freq="D", tz="UTC")
    # day0 (Jun10): first day of the whole curve -> missing by definition
    #   (no predecessor end-of-day to diff against).
    # day1 (Jun11): equity unchanged from day0 -> pnl == 0.0 exactly -> non_positive.
    # day2 (Jun12): equity up from day1 -> positive.
    equity = [1000.0, 1000.0, 1050.0]
    curve = pd.DataFrame({"equity": equity}, index=idx)

    days, _ = regularity.compute_regularity(curve)
    assert days[0].status == "missing"
    assert days[1].pnl == pytest.approx(0.0)
    assert days[1].status == "non_positive"
    assert days[2].status == "positive"


def test_month_with_missing_interior_day_is_invalid_not_scored():
    idx_dates = [pd.Timestamp("2024-07-31 12:00:00", tz="UTC")]
    idx_dates += [pd.Timestamp(f"2024-08-{d:02d} 12:00:00", tz="UTC") for d in range(1, 32) if d != 15]
    idx_dates += [pd.Timestamp("2024-09-01 12:00:00", tz="UTC")]
    idx = pd.DatetimeIndex(idx_dates)
    # 30 August bars (1..31 minus the 15th, which has no snapshot at all) +
    # 2 buffer bars (Jul31, Sep1) = 32 bars total.
    assert len(idx) == 32
    equity = [1000.0 + 10.0 * i for i in range(len(idx))]
    curve = pd.DataFrame({"equity": equity}, index=idx)

    days, months = regularity.compute_regularity(curve)
    august = next(m for m in months if (m.year, m.month) == (2024, 8))

    # August has 31 calendar days; Aug 15 has no equity snapshot at all ->
    # missing. That single missing day invalidates the whole month's
    # evaluation -- N is still 31 (all calendar days of the month), but
    # positive_day_pct/deviation_pct/target_met must be None, not computed
    # with Aug 15 silently treated as a zero-PnL day.
    assert august.n == 31
    assert august.n_missing == 1
    assert august.is_partial is False
    assert august.is_valid is False
    assert august.positive_day_pct is None
    assert august.deviation_pct is None
    assert august.target_met is None

    aug15 = next(d for d in days if d.day == date(2024, 8, 15))
    assert aug15.status == "missing"
    assert aug15.equity is None


def test_partial_month_flagged_with_actual_day_count_not_full_month_length():
    idx = pd.date_range("2025-02-10 12:00:00", "2025-02-20 12:00:00", freq="D", tz="UTC")
    assert len(idx) == 11  # Feb10..Feb20
    # The whole curve starts/ends inside February -- February 2025 has 28
    # calendar days, but this curve only covers 11 of them.
    equity = [1000.0 + 10.0 * i for i in range(len(idx))]
    curve = pd.DataFrame({"equity": equity}, index=idx)

    _, months = regularity.compute_regularity(curve)
    assert len(months) == 1
    feb = months[0]
    assert (feb.year, feb.month) == (2025, 2)
    # N = 11 actual days present, not 28 (the full calendar month length).
    assert feb.n == 11
    assert feb.n != 28
    assert feb.is_partial is True
    # Feb 10 is the very first day of the whole curve -> missing (no
    # predecessor equity to diff against) -- an inherent edge of "PnL =
    # change since previous end-of-day", not an interior data gap (compare
    # test_month_with_missing_interior_day_is_invalid_not_scored above).
    assert feb.n_missing == 1
    assert feb.n_positive == 10  # the remaining 10 days each step +10


def test_dst_spring_transition_boundary_timestamps_map_to_correct_local_day():
    # Poland's 2026 spring-forward transition: clocks jump from 02:00 CET
    # (UTC+1) to 03:00 CEST (UTC+2) at 2026-03-29 01:00:00 UTC.
    # Hand-computed local (Europe/Warsaw) dates for timestamps straddling
    # the transition instant:
    #   2026-03-28 23:30 UTC -> +1h (CET, before transition) -> 2026-03-29 00:30 local -> 2026-03-29
    #   2026-03-29 00:30 UTC -> +1h (still CET)               -> 2026-03-29 01:30 local -> 2026-03-29
    #   2026-03-29 01:30 UTC -> +2h (CEST, after transition)  -> 2026-03-29 03:30 local -> 2026-03-29
    #   2026-03-29 22:30 UTC -> +2h (CEST)                    -> 2026-03-30 00:30 local -> 2026-03-30
    # A fixed-offset (non-DST-aware) implementation would misplace the last
    # timestamp onto 2026-03-29 instead of 2026-03-30.
    idx = pd.DatetimeIndex(
        [
            "2026-03-28 23:30:00",
            "2026-03-29 00:30:00",
            "2026-03-29 01:30:00",
            "2026-03-29 22:30:00",
        ],
        tz="UTC",
    )
    equity = [100.0, 110.0, 120.0, 130.0]
    curve = pd.DataFrame({"equity": equity}, index=idx)

    daily = regularity.daily_equity_snapshots(curve)
    assert list(daily.index) == [date(2026, 3, 29), date(2026, 3, 30)]
    # 2026-03-29's end-of-day value is its LAST snapshot (01:30 UTC), not
    # the first (23:30 UTC on the 28th) or the middle one.
    assert daily.loc[date(2026, 3, 29)] == 120.0
    assert daily.loc[date(2026, 3, 30)] == 130.0


def test_dst_spring_transition_no_day_lost_or_duplicated_across_range():
    # Hourly UTC bars spanning the 2026-03-29 transition, 2026-03-27 00:00
    # UTC through 2026-03-31 00:00 UTC inclusive (97 bars). Independently
    # (not via regularity.py) compute the expected set of Europe/Warsaw
    # calendar dates using the standard library directly.
    idx = pd.date_range("2026-03-27 00:00:00", periods=97, freq="h", tz="UTC")
    warsaw = ZoneInfo("Europe/Warsaw")
    expected_dates = sorted({ts.astimezone(warsaw).date() for ts in idx})
    # Ground truth: exactly 5 distinct, contiguous calendar dates
    # (Mar27..Mar31), even though Mar29 has only 23 local hours (the
    # spring-forward transition loses one hour that day).
    assert expected_dates == [date(2026, 3, 27) + timedelta(days=i) for i in range(5)]

    equity = list(range(len(idx)))
    curve = pd.DataFrame({"equity": equity}, index=idx)
    days, _ = regularity.compute_regularity(curve)

    actual_dates = [d.day for d in days]
    assert actual_dates == expected_dates  # no day lost, none duplicated, none reordered
    assert len(actual_dates) == len(set(actual_dates)) == 5
