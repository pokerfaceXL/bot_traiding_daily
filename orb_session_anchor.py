"""
orb_session_anchor.py -- London/NY session-anchored opening-range breakout (F006).

Additive module, same contract as donchian.py / lorentzian.py: catalog_entries()
returns new STRATEGY_CATALOG names, callable(df) -> pd.Series of +1/-1/0 on df's
index. Registered at runtime by scripts/f006_family_runner.register_catalog_entries
(shared-harness convention), never by editing strategy.py.

WHY THIS FAMILY (spec/research/F006-hypothesis-orb-session-anchor.md): the separately
pre-registered follow-up named by the ORB_UTC_* Decision (branch
limen/2026-09-28-f006-opening-range-breakout-2a0ca90b, tip 239d3cf). The opening range
is anchored to a fixed UTC clock window (London / NY open), not to the first OR_BARS
bars of the UTC day. This module does not import or change opening_range_breakout.py.

CAUSALITY. or_high/or_low for UTC day D come only from bars of D whose open lies in
[start, end); a bar only trades if its own open is >= end on D, so every OR bar has
already closed; its decision compares only its own close to that completed range.

Zero network connections.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Frozen grid, spec/research/F006-hypothesis-orb-session-anchor.md: name -> UTC
# half-open OR window [start, end) on bar OPEN time.
SESSION_WINDOWS = {
    "ORB_LON_1H": ("07:00", "08:00"),
    "ORB_LON_2H": ("07:00", "09:00"),
    "ORB_LON_3H": ("07:00", "10:00"),
    "ORB_NY_1H": ("13:30", "14:30"),
    "ORB_NY_2H": ("13:30", "15:30"),
}


def _to_offset(hhmm: str) -> pd.Timedelta:
    h, m = hhmm.split(":")
    return pd.Timedelta(hours=int(h), minutes=int(m))


def compute_session_orb_signal(df: pd.DataFrame, start: str, end: str) -> pd.Series:
    """+1/0/-1 session-anchored opening-range breakout, one row per bar of df's index.

    For each UTC day D: bars whose open time-of-day is in [start, end) form the OR
    (or_high = max high, or_low = min low). A day with zero such bars never arms.
    Bars of D with open >= end: +1 if close > or_high, -1 if close < or_low, else 0
    (strict). Every other bar is 0. No carry across days.
    """
    t_start, t_end = _to_offset(start), _to_offset(end)
    if not (pd.Timedelta(0) <= t_start < t_end <= pd.Timedelta(days=1)):
        raise ValueError(f"invalid OR window [{start}, {end})")

    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_convert("UTC") if idx.tz is not None else idx
    day = idx.normalize()
    tod = idx - day

    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()

    in_or = np.asarray((tod >= t_start) & (tod < t_end))
    work = pd.DataFrame({"day": day, "high": high, "low": low})
    forming = work[in_or]
    or_high = work["day"].map(forming.groupby("day")["high"].max()).to_numpy(dtype=float)
    or_low = work["day"].map(forming.groupby("day")["low"].min()).to_numpy(dtype=float)

    # NaN or_high/or_low on a never-arm day: every comparison is False -> 0.
    active = np.asarray(tod >= t_end)
    out = np.zeros(len(df), dtype=int)
    out[active & (close > or_high)] = 1
    out[active & (close < or_low)] = -1  # exclusive with the long branch: or_high >= or_low
    return pd.Series(out, index=df.index)


def catalog_entries() -> dict:
    """The five frozen ORB_LON_* / ORB_NY_* names."""
    return {
        # default-arg binding so each lambda keeps its own window
        name: (lambda df, s=s, e=e: compute_session_orb_signal(df, s, e))
        for name, (s, e) in SESSION_WINDOWS.items()
    }
