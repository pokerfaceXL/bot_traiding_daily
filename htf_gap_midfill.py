"""Causal HTF fair-value-gap midfill continuation signals for F006.

This additive research module implements the frozen geometry in
spec/research/F006-hypothesis-htf-gap-midfill.md.  It does not register itself in
strategy.py: the Train-1 script registers catalog_entries() only in its process.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

R_MAX_VALUES = (1, 2, 3)
BIAS_LOOKBACK_BLOCKS = 3


def _block_bars_for_index(index: pd.Index) -> int:
    """Return frozen 4h-on-60m / 12h-on-240m aggregation size."""
    if len(index) < 2:
        return 4
    stamps = pd.DatetimeIndex(index)
    spacing = pd.Series(stamps[1:] - stamps[:-1]).median()
    if spacing == pd.Timedelta(hours=1):
        return 4
    if spacing == pd.Timedelta(hours=4):
        return 3
    raise ValueError("HTF FVG family supports only regular 60m or 240m input bars")


def compute_htf_fvg_midfill_signal(
    df: pd.DataFrame, r_max: int, *, block_bars: int | None = None
) -> pd.Series:
    """Emit a one-bar +/-1 signal for the frozen causal FVG midfill rule.

    The current input bar is processed before it can close an HTF block. Therefore
    an HTF candle, an FVG formed by it, and its bias are never available early.
    """
    if r_max not in R_MAX_VALUES:
        raise ValueError(f"r_max must be one of {R_MAX_VALUES}, got {r_max}")
    block_bars = block_bars or _block_bars_for_index(df.index)
    if block_bars < 1:
        raise ValueError("block_bars must be >= 1")

    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    opn = df["open"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()
    out = np.zeros(len(df), dtype=int)
    blocks: list[dict] = []
    gaps: list[dict] = []

    for i in range(len(df)):
        # The newest completed HTF close and three completed blocks before it define
        # the only live bias bit. Current partial-block data is intentionally absent.
        bias = 0
        if len(blocks) > BIAS_LOOKBACK_BLOCKS:
            delta = blocks[-1]["close"] - blocks[-1 - BIAS_LOOKBACK_BLOCKS]["close"]
            bias = 1 if delta > 0 else (-1 if delta < 0 else 0)

        candidates: list[dict] = []
        for gap in gaps:
            if not gap["active"]:
                continue
            direction, mid = gap["direction"], gap["mid"]
            fully_filled = (direction == 1 and low[i] <= gap["bot"]) or (
                direction == -1 and high[i] >= gap["top"]
            )
            if fully_filled:
                gap["active"] = False
                continue
            continuation = (direction == 1 and close[i] > opn[i]) or (
                direction == -1 and close[i] < opn[i]
            )
            if not gap["pending"]:
                if not low[i] <= mid <= high[i]:
                    continue
                # First midpoint contact consumes this FVG regardless of permission.
                # An opposite/flat bias must not leave it available for a later touch
                # after the HTF bias flips; only a permitted first touch can arm R_MAX.
                if bias != direction:
                    gap["active"] = False
                    continue
                gap["pending"] = True
                # Far-side reject is a stated same-bar alternative; a directional
                # continuation close is also allowed on the first midfill bar.
                reject = (direction == 1 and low[i] <= mid and close[i] > mid) or (
                    direction == -1 and high[i] >= mid and close[i] < mid
                )
                if reject or continuation:
                    candidates.append(gap)
                else:
                    gap["remaining"] = r_max - 1
                    if gap["remaining"] <= 0:
                        gap["active"] = False
            elif continuation:
                candidates.append(gap)
            else:
                gap["remaining"] -= 1
                if gap["remaining"] <= 0:
                    gap["active"] = False

        if candidates:
            # A simultaneous older-gap reaction never consumes a newer gap ID.
            winner = max(candidates, key=lambda g: g["created"])
            out[i] = winner["direction"]
            winner["active"] = False

        # Aggregate the bar only after it was evaluated against previously completed
        # blocks. This makes the final bar of a block unavailable until the next bar.
        pos = i % block_bars
        if pos == 0:
            building = {"open": opn[i], "high": high[i], "low": low[i], "close": close[i]}
        else:
            building["high"] = max(building["high"], high[i])
            building["low"] = min(building["low"], low[i])
            building["close"] = close[i]
        if pos == block_bars - 1:
            blocks.append(building)
            if len(blocks) >= 3:
                c1, c3 = blocks[-3], blocks[-1]
                if c3["low"] > c1["high"]:
                    gaps.append({"direction": 1, "bot": c1["high"], "top": c3["low"],
                                 "mid": (c1["high"] + c3["low"]) / 2.0,
                                 "created": i, "active": True, "pending": False,
                                 "remaining": None})
                elif c3["high"] < c1["low"]:
                    gaps.append({"direction": -1, "bot": c3["high"], "top": c1["low"],
                                 "mid": (c1["low"] + c3["high"]) / 2.0,
                                 "created": i, "active": True, "pending": False,
                                 "remaining": None})

    return pd.Series(out, index=df.index, dtype=int)


def catalog_entries() -> dict:
    """Runtime-only catalog names frozen by the F006 pre-registration."""
    return {
        f"HTF_FVG_MID_R{r_max}": (lambda df, r_max=r_max: compute_htf_fvg_midfill_signal(df, r_max))
        for r_max in R_MAX_VALUES
    }
