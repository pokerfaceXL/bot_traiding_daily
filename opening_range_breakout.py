"""
opening_range_breakout.py -- UTC opening-range breakout (ORB) signal family (F006).

Additive module, same pattern as donchian.py / lorentzian.py: it adds new entries to
strategy.STRATEGY_CATALOG (registered at the bottom of strategy.py) and changes
nothing in the existing engine or in any existing catalog entry. The contract is the
catalog's own -- callable(df) -> pd.Series of +1/-1/0 on df's index -- so
backtest_engine.run_backtest calls these exactly like every other name.

WHY THIS FAMILY (spec/research/F006-hypothesis-opening-range-breakout.md): every
catalog name is path-dependent on rolling windows of the same series (EMA/BB/
Donchian/RSI/MACD/Stoch/ADX) or Lorentzian neighbors -- none is keyed to a fixed
clock anchor. An opening-range breakout defines its entry from "first N bars after a
UTC calendar-day boundary, then trade the break of that range for the rest of the
day" -- a session/calendar mechanism, orthogonal to relative volume and to
cross-sectional rank (neither of which this module depends on).

CAUSALITY. `or_high`/`or_low` for UTC day D are built only from bars whose 0-based
position within D is < or_bars; a bar's breakout decision compares only its own
close against that already-completed range. No bar ever sees a later bar's high,
low or close, and no day's range ever includes a bar from a different day.

Zero network connections.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Pre-registered grid, spec/research/F006-hypothesis-opening-range-breakout.md.
OR_BARS_GRID = (1, 2, 3, 4, 6)


def compute_orb_signal(df: pd.DataFrame, or_bars: int) -> pd.Series:
    """+1/0/-1 UTC opening-range breakout, one row per bar of df's index.

    For each UTC calendar day D (bar timestamps treated as UTC, Bybit cache
    convention): let i = 0, 1, 2, ... be the 0-based order of bars whose open falls
    on D. While i < or_bars the range is still forming and the signal is 0.
    or_high = max(high[0..or_bars)), or_low = min(low[0..or_bars)) once or_bars bars
    exist for D; a day with fewer than or_bars bars never arms (every bar of it stays
    0, since no bar of it then has i >= or_bars). For i >= or_bars: +1 if
    close > or_high, -1 if close < or_low, else 0. No carry across days -- each
    day's range and breakout state is independent of every other day's.
    """
    if or_bars < 1:
        raise ValueError(f"or_bars must be >= 1, got {or_bars}")

    idx = df.index
    day = idx.tz_convert("UTC") if idx.tz is not None else idx
    day = day.normalize()

    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()

    work = pd.DataFrame({"day": day, "high": high, "low": low, "close": close})
    work["i"] = work.groupby("day").cumcount()

    forming = work[work["i"] < or_bars]
    or_high = forming.groupby("day")["high"].max()
    or_low = forming.groupby("day")["low"].min()
    work_or_high = work["day"].map(or_high).to_numpy()
    work_or_low = work["day"].map(or_low).to_numpy()

    active = (work["i"] >= or_bars).to_numpy()
    out = np.zeros(len(df), dtype=int)
    long_mask = active & (close > work_or_high)
    short_mask = active & (close < work_or_low)  # unreachable together: or_high>=or_low
    out[long_mask] = 1
    out[short_mask] = -1
    return pd.Series(out, index=df.index)


def catalog_entries() -> dict:
    """New, additive STRATEGY_CATALOG entries. Registered from strategy.py."""
    entries = {}
    for n in OR_BARS_GRID:
        # default-arg binding, not closure capture, so each lambda keeps its own n
        entries[f"ORB_UTC_{n}"] = lambda df, n=n: compute_orb_signal(df, n)
    return entries
