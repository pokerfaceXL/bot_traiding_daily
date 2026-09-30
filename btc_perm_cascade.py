"""Frozen H-BTC-PERM-CASCADE-01 research signals; no live catalog changes.

CASCADE features/state transitions copied from 80c013c:liq_cascade_proxy.py;
ER20 permission and exact timestamp alignment from e518682:btc_filter.py.
Gate AFTER consuming the trauma arm, including when permission rejects the event.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

RANGE_WINDOW = 20
PERCENTILE_LOOKBACK = 120
COMPRESSION_PERCENTILE = 0.20
ARM_BARS = 6
BASELINE_WINDOW = 20
ER_WINDOW = 20
ALT_SYMBOLS = frozenset(("ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"))
PARAM_GRID = {
    "BPC_R15_V25_C75": (1.5, 2.5, 0.75, 0.30),
    "BPC_R18_V20_C75": (1.8, 2.0, 0.75, 0.30),
    "BPC_R18_V30_C75": (1.8, 3.0, 0.75, 0.30),
    "BPC_R15_V25_NOGATE": (1.5, 2.5, 0.75, None),
    "BPC_R15_V25_ER40": (1.5, 2.5, 0.75, 0.40),
}
NAMES = tuple(PARAM_GRID)


def btc_er_permission(btc_df: pd.DataFrame, threshold: float = 0.30) -> pd.Series:
    """Warm-up, missing prices and zero path are neutral; never forward-fill."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    close = btc_df["close"].astype(float)
    displacement = close - close.shift(ER_WINDOW)
    path = close.diff().abs().rolling(ER_WINDOW).sum()
    er = displacement.div(path.where(path != 0))
    return pd.Series(np.select([er >= threshold, er <= -threshold], [1, -1], default=0),
                     index=btc_df.index, dtype=int)


def cascade_features(df: pd.DataFrame) -> pd.DataFrame:
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    volume = df["volume"].astype(float)
    bar_range = high - low
    compression_range = bar_range.rolling(RANGE_WINDOW).sum()
    compression_threshold = compression_range.shift(1).rolling(PERCENTILE_LOOKBACK).quantile(
        COMPRESSION_PERCENTILE
    )
    prior_range_mean = bar_range.shift(1).rolling(BASELINE_WINDOW).mean()
    prior_volume_mean = volume.shift(1).rolling(BASELINE_WINDOW).mean()
    close_from_low = (close - low) / bar_range.replace(0, np.nan)
    return pd.DataFrame({
        "bar_range": bar_range,
        "compression_range": compression_range,
        "compression_threshold": compression_threshold,
        "prior_range_mean": prior_range_mean,
        "prior_volume_mean": prior_volume_mean,
        "close_from_low": close_from_low.fillna(0.0),
    }, index=df.index)


def cascade_direction(
    df: pd.DataFrame, range_multiple: float, volume_multiple: float, close_fraction: float
) -> pd.Series:
    """Exact frozen arm/refresh/consume machine, not a channel breakout."""
    f = cascade_features(df)
    compression = f["compression_range"] <= f["compression_threshold"]
    valid_range = f["prior_range_mean"] > 0
    valid_volume = f["prior_volume_mean"] > 0
    expansion = (
        valid_range & valid_volume
        & (f["bar_range"] > range_multiple * f["prior_range_mean"])
        & (df["volume"].astype(float) > volume_multiple * f["prior_volume_mean"])
    )
    out = np.zeros(len(df), dtype=int)
    armed_until = -1
    for i in range(len(df)):
        if bool(compression.iloc[i]):
            armed_until = i + ARM_BARS
            continue
        if i > armed_until or not bool(expansion.iloc[i]):
            continue
        location = f["close_from_low"].iloc[i]
        if location >= close_fraction:
            out[i] = 1
            armed_until = -1
        elif location <= 1.0 - close_fraction:
            out[i] = -1
            armed_until = -1
    return pd.Series(out, index=df.index)


def signal(df: pd.DataFrame, btc_df: pd.DataFrame, name: str) -> pd.Series:
    """Runner supplies only the frozen basket; BTC's diagnostic rows stay flat.

    As in the frozen BTC parent, price-series equality identifies BTC without
    requiring metadata changes to the shared runner/engine interface.
    """
    r, v, c, threshold = PARAM_GRID[name]
    if df["close"].equals(btc_df["close"]):
        return pd.Series(0, index=df.index, dtype=int)
    trigger = cascade_direction(df, r, v, c)
    if threshold is None:
        return trigger
    permission = btc_er_permission(btc_df, threshold).reindex(df.index, fill_value=0)
    return trigger.where(trigger.eq(permission), 0).astype(int)


def catalog_entries(btc_by_interval: Mapping[str, pd.DataFrame]) -> dict:
    """Runtime-only registration, with bounded same-interval BTC context."""
    if set(btc_by_interval) != {"60", "240"}:
        raise ValueError("require BTC frames for exactly intervals 60 and 240")

    def evaluate(df, name):
        if len(df) < 2:
            return pd.Series(0, index=df.index, dtype=int)
        minutes = (pd.Timestamp(df.index[1]) - pd.Timestamp(df.index[0])).total_seconds() / 60
        if minutes not in (60, 240):
            raise ValueError(f"unsupported interval: {minutes}")
        return signal(df, btc_by_interval[str(int(minutes))], name)

    return {name: lambda df, name=name: evaluate(df, name) for name in NAMES}
