"""Train-1 NYSE calendar and day classes for F012-R2A (prereg §4)."""
from __future__ import annotations

import pandas as pd

ET = "America/New_York"
TRAIN1 = ("2024-03-01", "2025-02-28")  # inclusive, ET dates
HOLIDAYS = pd.to_datetime([
    "2024-03-29", "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28",
    "2024-12-25", "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17",
])
EARLY_CLOSE = pd.to_datetime(["2024-07-03", "2024-11-29", "2024-12-24"])


def all_days() -> pd.DatetimeIndex:
    return pd.date_range(*TRAIN1, freq="D")


def sessions() -> pd.DatetimeIndex:
    """NYSE sessions (full + early close) in Train-1."""
    d = all_days()
    return d[(d.dayofweek < 5) & ~d.isin(HOLIDAYS)]


def day_class(d: pd.Timestamp) -> str:
    if d.dayofweek >= 5 or d in HOLIDAYS:
        return "placebo"
    if d in EARLY_CLOSE:
        return "early_close"
    return "us"


def close_time(d: pd.Timestamp) -> pd.Timestamp:
    """Official close (tz-aware ET) of session d."""
    hour = 13 if d in EARLY_CLOSE else 16
    return pd.Timestamp(d.date()).tz_localize(ET) + pd.Timedelta(hours=hour)


def prev_session(d: pd.Timestamp) -> pd.Timestamp:
    """Last NYSE session strictly before d."""
    cur = d - pd.Timedelta(days=1)
    while cur.dayofweek >= 5 or cur in HOLIDAYS:
        cur -= pd.Timedelta(days=1)
    return cur


def et(d: pd.Timestamp, hour: int, minute: int = 0) -> pd.Timestamp:
    return pd.Timestamp(d.date()).tz_localize(ET) + pd.Timedelta(hours=hour, minutes=minute)
