"""Causal Sube inversion signals for F006 H-SUBE-INV-FVG-01.

Five fixed names only.  This is not a gap-midfill, MTFP prior-N break, or EQH reclaim:
FVG signals fire at a gap's birth and MSS signals fire at a confirmed-swing close.
"""
from __future__ import annotations

from typing import Callable, Mapping

import numpy as np
import pandas as pd

HTF_MIN = 7200
H4_MIN = 240
PIVOT_P = 2
NAMES = ("SINV_FIRST_FVG", "SINV_MSS_CLOSE", "SINV_MSS_IN_FVG", "SINV_FIRST_H4", "SINV_FIRST_SMT")


def _index_utc(df: pd.DataFrame) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(df.index)
    return idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")


def completed_blocks(df: pd.DataFrame, tf_min: int, block_min: int) -> pd.DataFrame:
    """Return only complete epoch-aligned blocks; a missing constituent bar kills it."""
    if block_min % tf_min:
        raise ValueError("block length must be a whole number of bars")
    idx = _index_utc(df)
    bars = block_min // tf_min
    opens = (idx.view("int64") // 60_000_000_000).astype(np.int64)
    ids = opens // block_min
    records = []
    for block_id in np.unique(ids):
        positions = np.flatnonzero(ids == block_id)
        expected = block_id * block_min + np.arange(bars) * tf_min
        if len(positions) != bars or not np.array_equal(opens[positions], expected):
            continue
        part = df.iloc[positions]
        records.append({"id": int(block_id), "open": float(part["open"].iloc[0]),
                        "high": float(part["high"].max()), "low": float(part["low"].min()),
                        "close": float(part["close"].iloc[-1]),
                        "complete_at": part.index[-1]})
    return pd.DataFrame(records).set_index("id", drop=False) if records else pd.DataFrame(
        columns=["id", "open", "high", "low", "close", "complete_at"]).set_index("id", drop=False)


def _state(df: pd.DataFrame, tf_min: int, block_min: int) -> dict:
    b = completed_blocks(df, tf_min, block_min)
    ids = list(b.index)
    piv_hi, piv_lo = {}, {}
    for pos in range(PIVOT_P, len(ids) - PIVOT_P):
        j = ids[pos]
        if ids[pos - PIVOT_P:pos + PIVOT_P + 1] != list(range(j - PIVOT_P, j + PIVOT_P + 1)):
            continue
        window = b.loc[ids[pos - PIVOT_P:pos + PIVOT_P + 1]]
        if b.at[j, "high"] > window.drop(index=j)["high"].max(): piv_hi[j] = b.at[j, "high"]
        if b.at[j, "low"] < window.drop(index=j)["low"].min(): piv_lo[j] = b.at[j, "low"]
    trend, mss, fvgs, first = {}, {}, [], {}
    used_hi, used_lo = set(), set()
    for pos, k in enumerate(ids):
        confirmed_hi = [(j, x) for j, x in piv_hi.items() if j + 2 <= k]
        confirmed_lo = [(j, x) for j, x in piv_lo.items() if j + 2 <= k]
        t = 0
        if len(confirmed_hi) >= 2 and len(confirmed_lo) >= 2:
            t = 1 if confirmed_hi[-1][1] > confirmed_hi[-2][1] and confirmed_lo[-1][1] > confirmed_lo[-2][1] else (
                -1 if confirmed_hi[-1][1] < confirmed_hi[-2][1] and confirmed_lo[-1][1] < confirmed_lo[-2][1] else 0)
        trend[k] = t
        prev = trend.get(ids[pos - 1], 0) if pos else 0
        prior_hi = [(j, x) for j, x in piv_hi.items() if j + 2 <= k - 1]
        prior_lo = [(j, x) for j, x in piv_lo.items() if j + 2 <= k - 1]
        direction = 0
        if prior_hi and b.at[k, "close"] > prior_hi[-1][1] and prev != 1 and prior_hi[-1][0] not in used_hi:
            direction, used_hi = 1, used_hi | {prior_hi[-1][0]}
        elif prior_lo and b.at[k, "close"] < prior_lo[-1][1] and prev != -1 and prior_lo[-1][0] not in used_lo:
            direction, used_lo = -1, used_lo | {prior_lo[-1][0]}
        mss[k] = direction
        fvg_dir = 0
        if pos >= 2 and ids[pos - 2:pos + 1] == [k - 2, k - 1, k]:
            if b.at[k, "low"] > b.at[k - 2, "high"]:
                fvg_dir, bot, top = 1, b.at[k - 2, "high"], b.at[k, "low"]
            elif b.at[k, "high"] < b.at[k - 2, "low"]:
                fvg_dir, bot, top = -1, b.at[k, "high"], b.at[k - 2, "low"]
            else: fvg_dir = 0
            if fvg_dir: fvgs.append({"k": k, "direction": fvg_dir, "bot": bot, "top": top})
        if fvg_dir and prev == -fvg_dir:
            flip = next((q for q in reversed(ids[:pos]) if trend[q] == prev and (q == ids[0] or trend.get(q - 1, 0) != prev)), None)
            if not any(x["direction"] == fvg_dir and flip < x["k"] < k for x in fvgs): first[k] = fvg_dir
    return {"blocks": b, "trend": trend, "mss": mss, "fvgs": fvgs, "first": first, "piv_hi": piv_hi, "piv_lo": piv_lo}


def _open_fvg_overlap(state: dict, k: int) -> bool:
    b = state["blocks"]
    for gap in state["fvgs"]:
        if gap["k"] >= k: continue
        between = b.loc[(b.index > gap["k"]) & (b.index < k)]
        filled = (between["low"] <= gap["bot"]).any() if gap["direction"] == 1 else (between["high"] >= gap["top"]).any()
        if not filled and b.at[k, "low"] <= gap["top"] and b.at[k, "high"] >= gap["bot"]: return True
    return False


def _at_completion(df: pd.DataFrame, state: dict, values: dict) -> pd.Series:
    out = pd.Series(0, index=df.index, dtype=int)
    for k, value in values.items(): out.loc[state["blocks"].at[k, "complete_at"]] = value
    return out


def compute_signals(df: pd.DataFrame, tf_min: int, reference: pd.DataFrame | None = None) -> dict[str, pd.Series]:
    """Compute all five causal signals. Reference is required only for SMT."""
    s = _state(df, tf_min, HTF_MIN)
    first = _at_completion(df, s, s["first"])
    mss = _at_completion(df, s, s["mss"])
    in_fvg = _at_completion(df, s, {k: v for k, v in s["mss"].items() if v and _open_fvg_overlap(s, k)})
    h4 = _state(df, tf_min, H4_MIN)
    h4_values = {}
    for k, direction in s["first"].items():
        event_at = s["blocks"].at[k, "complete_at"]
        containing = int((_index_utc(df)[df.index.get_loc(event_at)].value // 60_000_000_000) // H4_MIN)
        for hk, hd in h4["first"].items():
            if containing < hk <= containing + 6 and hd == direction and h4["blocks"].at[hk, "complete_at"] > event_at:
                h4_values[h4["blocks"].at[hk, "complete_at"]] = direction; break
    first_h4 = pd.Series(0, index=df.index, dtype=int)
    for t, v in h4_values.items(): first_h4.loc[t] = v
    smt = pd.Series(0, index=df.index, dtype=int)
    if reference is not None:
        r = _state(reference, tf_min, HTF_MIN)
        for k, direction in s["first"].items():
            if k not in r["blocks"].index: continue
            own = ([(j,x) for j,x in (s["piv_lo"] if direction == 1 else s["piv_hi"]).items() if j+2 <= k-1])
            ref = ([(j,x) for j,x in (r["piv_lo"] if direction == 1 else r["piv_hi"]).items() if j+2 <= k-1])
            if not own or not ref: continue
            own_run = s["blocks"].at[k, "low" if direction == 1 else "high"] < own[-1][1] if direction == 1 else s["blocks"].at[k, "high"] > own[-1][1]
            ref_run = r["blocks"].at[k, "low" if direction == 1 else "high"] < ref[-1][1] if direction == 1 else r["blocks"].at[k, "high"] > ref[-1][1]
            if own_run != ref_run: smt.loc[s["blocks"].at[k, "complete_at"]] = direction
    return {"SINV_FIRST_FVG": first, "SINV_MSS_CLOSE": mss, "SINV_MSS_IN_FVG": in_fvg, "SINV_FIRST_H4": first_h4, "SINV_FIRST_SMT": smt}


def catalog_entries(references: Mapping[object, pd.DataFrame] | None = None) -> dict[str, Callable]:
    """Runtime catalog closures; references maps a target close-series fingerprint to its peer."""
    references = references or {}
    def signal(name):
        def fn(df):
            key = tuple(np.asarray(df["close"], dtype=float))
            idx = _index_utc(df)
            tf_min = int((idx[1] - idx[0]).total_seconds() // 60)
            return compute_signals(df, tf_min, references.get(key))[name]
        return fn
    return {name: signal(name) for name in NAMES}
