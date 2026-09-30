"""Causal compression-to-expansion continuation signals for F006.

This OHLCV-only proxy identifies a quiet rolling-range state, then consumes that
state on one unusually wide, high-volume directional bar. It deliberately emits
only on the expansion event: no channel breakout, prior-bias, fade, or persistent
post-event position state is embedded here. The experiment's one-shot mask and
engine therefore decide at the event close and fill at the following open.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RANGE_WINDOW = 20
PERCENTILE_LOOKBACK = 120
COMPRESSION_PERCENTILE = 0.20
ARM_BARS = 6
BASELINE_WINDOW = 20

PARAM_GRID = {
    "LIQ_CASCADE_20_120_6_R18_V20_C75": (1.8, 2.0, 0.75),
    "LIQ_CASCADE_20_120_6_R15_V25_C75": (1.5, 2.5, 0.75),
    "LIQ_CASCADE_20_120_6_R20_V15_C75": (2.0, 1.5, 0.75),
    "LIQ_CASCADE_20_120_6_R18_V20_C80": (1.8, 2.0, 0.80),
    "LIQ_CASCADE_20_120_6_R18_V30_C75": (1.8, 3.0, 0.75),
}


def cascade_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return causal compression and event features without changing ``df``.

    The compression threshold at i excludes C_i; expansion baselines likewise
    exclude their event bar. This makes prefix evaluation identical to full-frame
    evaluation through every prefix bar.
    """
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


def sig_liq_cascade_proxy(
    df: pd.DataFrame, range_multiple: float, volume_multiple: float, close_fraction: float
) -> pd.Series:
    """Emit +1/-1 exactly once when an armed compression becomes a trauma proxy."""
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


def catalog_entries() -> dict:
    """Return the five pre-registered names for runtime-only harness registration."""
    return {
        name: (
            lambda df, range_multiple=range_multiple, volume_multiple=volume_multiple,
            close_fraction=close_fraction: sig_liq_cascade_proxy(
                df, range_multiple, volume_multiple, close_fraction
            )
        )
        for name, (range_multiple, volume_multiple, close_fraction) in PARAM_GRID.items()
    }
