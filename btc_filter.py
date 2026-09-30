"""Causal BTC ER permission filter for frozen F006 alt Donchian entries.

BTC is context only: ``catalog_entries`` returns runtime-only callables for the
four-alt research universe, and returns flat for BTC itself.  The BTC permission at
bar i uses only closes through i; an alt's channel excludes its current bar.
Nothing imports this module from strategy.py or live code.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

ALT_SYMBOLS = frozenset(("ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"))
BTC_SYMBOL = "BTCUSDT"
ER_WINDOW = 20
ER_THRESHOLD = 0.30
ALT_LOOKBACKS = (5, 10, 20)


def btc_er_permission(btc_df: pd.DataFrame, window: int = ER_WINDOW,
                      threshold: float = ER_THRESHOLD) -> pd.Series:
    """Return causal +1/-1/0 BTC permission from directional efficiency ratio."""
    if window < 1:
        raise ValueError("window must be >= 1")
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    close = btc_df["close"].astype(float)
    displacement = close - close.shift(window)
    path = close.diff().abs().rolling(window).sum()
    er = displacement.div(path.where(path != 0))
    return pd.Series(np.select([er >= threshold, er <= -threshold], [1, -1], default=0),
                     index=btc_df.index, dtype=int)


def alt_breakout(df: pd.DataFrame, n: int) -> pd.Series:
    """A flat, causal break of the prior n-bar high/low (current bar excluded)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    close = df["close"].astype(float)
    upper = df["high"].astype(float).rolling(n).max().shift(1)
    lower = df["low"].astype(float).rolling(n).min().shift(1)
    return pd.Series(np.select([close > upper, close < lower], [1, -1], default=0),
                     index=df.index, dtype=int)


def filtered_breakout(df: pd.DataFrame, btc_df: pd.DataFrame, n: int) -> pd.Series:
    """Pass an alt breakout only when the aligned causal BTC permission agrees.

    An absent BTC timestamp is neutral, deliberately never forward-filled.  Equality
    with BTC's close series identifies the runner's BTC row and keeps it flat: BTC
    is not a member of this family’s trade universe.
    """
    if df["close"].equals(btc_df["close"]):
        return pd.Series(0, index=df.index, dtype=int)
    permission = btc_er_permission(btc_df).reindex(df.index, fill_value=0)
    trigger = alt_breakout(df, n)
    return trigger.where(trigger.eq(permission), 0).astype(int)


def catalog_entries(btc_by_interval: Mapping[str, pd.DataFrame]) -> dict:
    """Build runtime-only entries closed over bounded Train-1 BTC frames."""
    missing = {"60", "240"} - set(btc_by_interval)
    if missing:
        raise ValueError(f"missing BTC frames for intervals: {sorted(missing)}")
    entries = {}
    for n in ALT_LOOKBACKS:
        name = f"BTC_FILTER_ER20_DONCHIAN_{n}"
        entries[name] = lambda df, n=n: filtered_breakout(
            df, btc_by_interval[_interval_for_index(df.index)], n
        )
    return entries


def _interval_for_index(index: pd.Index) -> str:
    """Infer the frozen hourly/four-hourly interval without caller metadata."""
    if len(index) < 2:
        raise ValueError("cannot infer interval from fewer than two bars")
    delta = pd.Timestamp(index[1]) - pd.Timestamp(index[0])
    minutes = int(delta.total_seconds() // 60)
    if minutes not in (60, 240):
        raise ValueError(f"unsupported F006 interval inferred from index: {minutes} minutes")
    return str(minutes)
