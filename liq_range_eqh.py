"""Causal EQH/EQL range-sweep reclaim signals for F006 H-LIQ-RANGE-EQH-01.

This additive research module intentionally has no live registration: the Train-1
family script registers its frozen catalog only for that process. Every decision at
bar i uses OHLCV through i; pivots become available only after their L-bar
confirmation lag and the engine fills a resulting decision at i+1's open.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

W_MIN, W_MAX, N_MIN, N_MAX = 1.5, 8.0, 8, 64
DEAD_VOL_RATIO = 0.002


@dataclass(frozen=True)
class RangeEqhParams:
    lag: int
    eps: float
    sweep_eps: float
    reclaim_max: int
    cooldown: int
    wick_only: bool = False


CATALOG = {
    "RANGE_EQH_RECLAIM_L2": RangeEqhParams(2, 0.20, 0.05, 3, 6),
    "RANGE_EQH_RECLAIM_L3": RangeEqhParams(3, 0.20, 0.05, 3, 6),
    "RANGE_EQH_RECLAIM_WIDE": RangeEqhParams(2, 0.30, 0.05, 5, 6),
    "RANGE_EQH_RECLAIM_TIGHT": RangeEqhParams(2, 0.15, 0.10, 2, 8),
    "RANGE_EQH_RECLAIM_WICK": RangeEqhParams(2, 0.20, 0.05, 3, 6, True),
}


def atr14(df: pd.DataFrame) -> pd.Series:
    """Wilder ATR(14), computed only from current and prior bars."""
    high, low, close = (df[c].astype(float) for c in ("high", "low", "close"))
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()


def confirmed_pivots(df: pd.DataFrame, lag: int) -> tuple[pd.Series, pd.Series]:
    """Pivot-index flags revealed only at pivot+lag (not a centered-window signal)."""
    high, low = df["high"].to_numpy(dtype=float), df["low"].to_numpy(dtype=float)
    high_out, low_out = np.zeros(len(df), dtype=bool), np.zeros(len(df), dtype=bool)
    for i in range(len(df)):
        p = i - lag
        if p >= lag:
            high_out[i] = high[p] >= np.max(high[p - lag:p]) and high[p] > np.max(high[p + 1:i + 1])
            low_out[i] = low[p] <= np.min(low[p - lag:p]) and low[p] < np.min(low[p + 1:i + 1])
    return pd.Series(high_out, index=df.index), pd.Series(low_out, index=df.index)


def _pool_level(pivots: list[tuple[int, float]], edge: float, atr: float, eps: float, high_side: bool):
    prices = [price for _, price in pivots if abs(price - edge) <= eps * atr]
    if len(prices) < 2:
        return None
    # A pool needs any pairwise-valid subset, not one pivot compatible with every
    # edge candidate. Keep every price that participates in at least one valid pair:
    # the EQH/EQL extreme then belongs to a witnessing pair even in a chained set.
    paired = [p for pos, p in enumerate(prices)
              if any(pos != other and abs(p - q) <= eps * atr for other, q in enumerate(prices))]
    if len(paired) < 2:
        return None
    return max(paired) if high_side else min(paired)


def compute_signal(df: pd.DataFrame, params: RangeEqhParams) -> pd.Series:
    """Return +1/0/-1 range EQL/EQH reclaim decisions, causally left-to-right."""
    n = len(df)
    out = np.zeros(n, dtype=int)
    if n == 0:
        return pd.Series(out, index=df.index)
    high = df["high"].astype(float).to_numpy()
    low = df["low"].astype(float).to_numpy()
    close = df["close"].astype(float).to_numpy()
    atr = atr14(df).to_numpy()
    high_confirmed, low_confirmed = confirmed_pivots(df, L := params.lag)
    highs: list[tuple[int, int, float]] = []  # pivot index, confirm time, price
    lows: list[tuple[int, int, float]] = []
    consumed_high: set[int] = set()
    consumed_low: set[int] = set()
    cooldown_until = -1
    for i in range(n):
        p = i - L
        if high_confirmed.iloc[i]:
            highs.append((p, i, high[p]))
        if low_confirmed.iloc[i]:
            lows.append((p, i, low[p]))
        if not highs or not lows or not np.isfinite(atr[i]) or close[i] == 0:
            continue
        sh, sl = highs[-1], lows[-1]
        top, bottom = sh[2], sl[2]
        age = i - min(sh[1], sl[1])
        width = (top - bottom) / atr[i]
        valid = top > bottom and W_MIN <= width <= W_MAX and N_MIN <= age <= N_MAX
        proximity = bottom - .25 * atr[i] <= close[i] <= top + .25 * atr[i]
        if not valid or not proximity or atr[i] / close[i] < DEAD_VOL_RATIO or i < cooldown_until:
            continue
        confirmed_highs = [(pivot, price) for pivot, confirmed, price in highs if confirmed <= i]
        confirmed_lows = [(pivot, price) for pivot, confirmed, price in lows if confirmed <= i]
        eqh = _pool_level(confirmed_highs, top, atr[i], params.eps, True)
        eql = _pool_level(confirmed_lows, bottom, atr[i], params.eps, False)

        short_sweep = None
        long_sweep = None
        if eqh is not None:
            for s in range(i - 1, max(-1, i - params.reclaim_max - 1), -1):
                if s not in consumed_high and high[s] >= eqh + params.sweep_eps * atr[s]:
                    if not params.wick_only or close[s] <= eqh:
                        short_sweep = s
                        break
        if eql is not None:
            for s in range(i - 1, max(-1, i - params.reclaim_max - 1), -1):
                if s not in consumed_low and low[s] <= eql - params.sweep_eps * atr[s]:
                    if not params.wick_only or close[s] >= eql:
                        long_sweep = s
                        break
        short_fire = short_sweep is not None and close[i] < eqh and close[i] <= top
        long_fire = long_sweep is not None and close[i] > eql and close[i] >= bottom
        if short_fire == long_fire:  # both false or pathological dual reclaim: flat
            continue
        out[i] = -1 if short_fire else 1
        if short_fire:
            consumed_high.add(short_sweep)
        else:
            consumed_low.add(long_sweep)
        cooldown_until = i + params.cooldown + 1
    return pd.Series(out, index=df.index, dtype=int)


def catalog_entries() -> dict:
    return {name: (lambda df, params=params: compute_signal(df, params)) for name, params in CATALOG.items()}
