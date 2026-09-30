"""
vol_regime_wrap.py -- causal realized-vol-percentile regime switch wrapping a frozen
Donchian(20) breakout trigger (F006, H-VOL-REGIME-WRAP-01).

Additive module, same pattern as donchian.py/lorentzian.py: it adds new entries to
strategy.STRATEGY_CATALOG (registered at the bottom of strategy.py) and changes
nothing in any existing entry. It depends on donchian.py only -- an already-merged
sibling F006 family, not an unmerged research module -- for the ONE frozen base
trigger this wraps (spec/research/F006-hypothesis-vol-regime-wrap.md's "Freeze").

MECHANISM (frozen in the research note before this module existed):

  1. atr_pct[i] = ATR14[i] / close[i], ATR14 a Wilder-style ewm(span=14,
     adjust=False).mean() of true range over bars 0..i only (self-contained, no
     add_indicators dependency -- same smoothing convention strategy.py uses for its
     own atr14 column, recomputed here so this module has zero dependency on
     add_indicators having already run).
  2. pct[i] = percentile rank of atr_pct[i] within the trailing window
     atr_pct[max(0, i-99) .. i] (W=100, inclusive of bar i). NaN for i < 99.
  3. A single left-to-right hysteresis state machine buckets pct[i] into
     LOW/MID/HIGH (edges 25/75, hysteresis margin 10 -- see module docstring's
     research note for the exact transition table).
  4. donchian.sig_donchian_breakout(df, 20) supplies the ONE frozen directional
     trigger. Three wrapped names switch its use by bucket: HIGH-only (breakout
     mode), LOW-only inverted (mean-revert/fade mode), and the HIGH+LOW combo with
     MID always flat.

CAUSALITY. ewm and a fixed trailing rolling window are both functions of bars 0..i
only; the hysteresis state machine is one forward pass with no bar re-visited.
Appending bars after i cannot change atr_pct[i], pct[i], the bucket at i, or the
wrapped output at i -- tests/test_vol_regime_wrap.py asserts this by prefix
truncation and future-bar perturbation, the same discipline as tests/test_donchian.py
and the shared contract in tests/test_signal_family_contract.py.

Zero network connections.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

import donchian

ATR_PERIOD = 14
PCT_WINDOW = 100
LOW_EDGE = 25.0
HIGH_EDGE = 75.0
HYSTERESIS = 10.0
DONCHIAN_N = 20

LOW, MID, HIGH = -1, 0, 1


def atr_pct_series(df: pd.DataFrame) -> pd.Series:
    """ATR14 (Wilder ewm of true range, bars 0..i only) as a fraction of close."""
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = tr.ewm(span=ATR_PERIOD, adjust=False).mean()
    return atr / close


def vol_percentile(df: pd.DataFrame) -> pd.Series:
    """Trailing-window (W=100, inclusive of bar i) percentile rank of atr_pct[i]."""
    atr_pct = atr_pct_series(df)
    return atr_pct.rolling(PCT_WINDOW).apply(
        lambda w: 100.0 * (w <= w[-1]).sum() / len(w), raw=True
    )


def vol_regime(df: pd.DataFrame) -> pd.Series:
    """LOW(-1)/MID(0)/HIGH(1) bucket via the frozen hysteresis state machine."""
    pct = vol_percentile(df).to_numpy()
    out = np.zeros(len(df), dtype=int)
    regime = MID
    for i in range(len(df)):
        p = pct[i]
        if np.isnan(p):
            regime = MID
        elif regime == MID:
            if p >= HIGH_EDGE:
                regime = HIGH
            elif p <= LOW_EDGE:
                regime = LOW
        elif regime == HIGH:
            if p <= LOW_EDGE:
                regime = LOW
            elif p < HIGH_EDGE - HYSTERESIS:
                regime = MID
        elif regime == LOW:
            if p >= HIGH_EDGE:
                regime = HIGH
            elif p > LOW_EDGE + HYSTERESIS:
                regime = MID
        out[i] = regime
    return pd.Series(out, index=df.index)


def _wrapped(df: pd.DataFrame, use_high: bool, use_low: bool, invert_low: bool) -> pd.Series:
    regime = vol_regime(df).to_numpy()
    direction = donchian.sig_donchian_breakout(df, DONCHIAN_N).to_numpy()
    out = np.zeros(len(df), dtype=int)
    if use_high:
        mask = regime == HIGH
        out[mask] = direction[mask]
    if use_low:
        mask = regime == LOW
        out[mask] = -direction[mask] if invert_low else direction[mask]
    return pd.Series(out, index=df.index)


def sig_vol_high_breakout(df: pd.DataFrame) -> pd.Series:
    """HIGH bucket only: Donchian(20) direction as-is (breakout mode). Else 0."""
    return _wrapped(df, use_high=True, use_low=False, invert_low=False)


def sig_vol_low_mean_revert(df: pd.DataFrame) -> pd.Series:
    """LOW bucket only: INVERTED Donchian(20) direction (fade/mean-revert). Else 0."""
    return _wrapped(df, use_high=False, use_low=True, invert_low=True)


def sig_vol_high_low_combo(df: pd.DataFrame) -> pd.Series:
    """HIGH: breakout direction. LOW: inverted (fade). MID: flat."""
    return _wrapped(df, use_high=True, use_low=True, invert_low=True)


def catalog_entries() -> dict:
    """New, additive STRATEGY_CATALOG entries. Registered from strategy.py."""
    return {
        "VOLW_HIGH_BRK_20": sig_vol_high_breakout,
        "VOLW_LOW_MR_20": sig_vol_low_mean_revert,
        "VOLW_HL_20": sig_vol_high_low_combo,
    }
