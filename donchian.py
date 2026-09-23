"""
donchian.py -- Donchian channel breakout & pullback-after-breakout signals (F006).

Additive module, same pattern as lorentzian.py: it adds new entries to
strategy.STRATEGY_CATALOG (registered at the bottom of strategy.py) and changes
nothing in the existing engine or in any existing catalog entry. The contract is
the catalog's own -- callable(df) -> pd.Series of +1/-1/0 on df's index -- so
backtest_engine.run_backtest calls these exactly like every other name.

WHY THIS FAMILY (spec/research/F006-hypothesis-donchian.md): every existing trend
entry in STRATEGY_CATALOG fires on a relationship between two *smoothed* series
(EMA vs EMA, MACD line vs its signal, price vs a Bollinger band built from a
rolling mean and std), and six F006 slices have found the same negative per-trade
expectancy for all of them. A Donchian channel has no smoothing: the upper band is
literally the highest high of the last N bars, so the signal changes state only on
a genuinely new N-bar extreme. N in {20, 55} is the Dennis/Eckhardt Turtle pair
(System 1 / System 2 entry channels), cited as the historically specified pair
rather than chosen by a grid search.

CAUSALITY. The channel at bar i is built from bars [i-N, i-1] -- the current bar is
EXCLUDED (`.rolling(N).max().shift(1)`), so bar i's own high/low never enters the
level it is compared against, and no later bar enters anything. Every value at bar
i is a function of bars 0..i only; tests/test_donchian.py asserts this the way
tests/test_lorentzian.py does, by truncating the frame and comparing.

Zero network connections.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The Turtle pair. See module docstring / the research note's "Sources".
TURTLE_LOOKBACKS = (20, 55)


def donchian_channel(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Upper/lower/mid Donchian bands over the PREVIOUS n bars (current bar excluded).

    upper[i] = max(high[i-n .. i-1]), lower[i] = min(low[i-n .. i-1]),
    mid[i] = (upper[i] + lower[i]) / 2. The first n bars are NaN (warm-up).
    """
    if n < 1:
        raise ValueError(f"donchian lookback must be >= 1, got {n}")
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    upper = high.rolling(n).max().shift(1)
    lower = low.rolling(n).min().shift(1)
    return pd.DataFrame({"upper": upper, "lower": lower, "mid": (upper + lower) / 2.0}, index=df.index)


def sig_donchian_breakout(df: pd.DataFrame, n: int) -> pd.Series:
    """+1 on a new n-bar high close, -1 on a new n-bar low close, carried forward.

    Persistent state, the same convention as sig_ema_cross and every other trend
    entry in the catalog: the value only changes when the OPPOSITE extreme is
    breached, so one contiguous run = one directional call (which is what makes
    entry_masks.one_shot_entry_mask meaningful on it). 0 until the first breakout.

    Strict inequalities. A bar that both exceeds the n-bar high and undercuts the
    n-bar low (wider than the whole channel) resolves SHORT -- an arbitrary
    tie-break, documented in the research note and pinned in the tests.
    """
    ch = donchian_channel(df, n)
    close = df["close"].astype(float)
    state = pd.Series(np.nan, index=df.index, dtype=float)
    state[close > ch["upper"]] = 1.0
    state[close < ch["lower"]] = -1.0  # applied second: short wins the (rare) tie
    return state.ffill().fillna(0.0).astype(int)


def sig_donchian_pullback(df: pd.DataFrame, n: int) -> pd.Series:
    """Enter in the breakout's direction only on a re-cross of the channel midline.

    State machine, one left-to-right pass (spec/research/F006-hypothesis-donchian.md,
    "Signal definitions"):

      1. ARM    -- on the first bar of a new directional run of sig_donchian_breakout,
                   arm that direction and emit 0. The breakout bar is never an entry,
                   and any held position from the previous call ends here.
      2. TOUCH  -- the first later bar whose close reaches the midline from the
                   breakout's side (close <= mid for a long, >= mid for a short)
                   arms the trigger. Still 0.
      3. TRIGGER-- the first bar after that which closes back through the midline in
                   the breakout's direction emits +1 (resp. -1).
      4. HOLD   -- carried forward until the next ARM, i.e. until the OPPOSITE n-bar
                   extreme is breached. Crossing back under the midline does not exit.

    Two decided failure modes: an armed call that never completes its pullback waits
    without a bar limit and is discarded unentered when the opposite breakout arms
    (so a runaway breakout is simply never traded), and an overshoot through the far
    channel edge needs no special case -- it IS the opposite breakout, so it cancels
    rather than fills.
    """
    ch = donchian_channel(df, n)
    direction = sig_donchian_breakout(df, n).to_numpy()
    mid = ch["mid"].to_numpy(dtype=float)
    close = df["close"].astype(float).to_numpy()

    out = np.zeros(len(df), dtype=int)
    armed = 0        # direction of a breakout call that has not yet been entered
    touched = False  # has the armed call reached the midline?
    held = 0         # the currently emitted state
    prev_dir = 0

    for i in range(len(df)):
        d = int(direction[i])
        if d != 0 and d != prev_dir:      # 1. ARM (start of a new directional run)
            prev_dir = d
            armed, touched, held = d, False, 0
            out[i] = 0
            continue
        prev_dir = d
        if armed != 0 and not np.isnan(mid[i]):
            if not touched:               # 2. TOUCH
                if (armed == 1 and close[i] <= mid[i]) or (armed == -1 and close[i] >= mid[i]):
                    touched = True
            elif (armed == 1 and close[i] > mid[i]) or (armed == -1 and close[i] < mid[i]):
                held, armed = armed, 0    # 3. TRIGGER
        out[i] = held                     # 4. HOLD
    return pd.Series(out, index=df.index)


def catalog_entries() -> dict:
    """New, additive STRATEGY_CATALOG entries. Registered from strategy.py."""
    entries = {}
    for n in TURTLE_LOOKBACKS:
        # default-arg binding, not closure capture, so each lambda keeps its own n
        entries[f"DONCHIAN_{n}"] = lambda df, n=n: sig_donchian_breakout(df, n)
        entries[f"DONCHIAN_PULLBACK_{n}"] = lambda df, n=n: sig_donchian_pullback(df, n)
    return entries
