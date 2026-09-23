"""
entry_masks.py -- entry-eligibility masks for backtest_engine's `entry_regime_mask` (F006).

Additive research module. It computes boolean Series that are handed to
`backtest_engine.run_backtest(..., entry_regime_mask=...)`; it imports the engine's
own dependencies (data_contract, strategy) to build them and changes nothing in
strategy.py / backtest_engine.py / any frozen F004/F005 module.

WHY THIS EXISTS (spec/research/F006-hypothesis-one-shot-entry.md): a catalog signal
column is a *persistent state*, not an edge. `EMA_8_21` is +1 for every bar the fast
EMA stays above the slow one, so after a stop-out the engine's step 4 re-queues an
entry into the very same, unchanged directional call on the next bar
(spec/research/F006-lorentzian-causality.md measured 4-5 executed trades per
directional call at 4h). `cooldown_candles` defers that re-entry by N bars and only
after an "initial_sl" exit (spec/research/F006-hypothesis-cooldown.md). The one-shot
mask removes it entirely and independently of exit reason:

    a "call" = one maximal contiguous run of the same nonzero signal value;
    only the FIRST bar of each call is entry-eligible.

Two boundary cases that make this more than a `diff() != 0`:
  * a return to the SAME direction after a flat gap (+1, 0, +1) is a NEW call --
    the underlying condition switched off and back on;
  * a direct flip (+1, -1) with no flat bar between is a new call too.
Both are asserted in tests/test_entry_masks.py.

Alignment contract: `run_backtest` reindexes the mask onto its own post-
`filter_closed_candles` + `add_indicators` frame and fills missing bars with False,
so a mask computed on the caller's raw frame index would silently disable entries on
any bar the engine drops. `strategy_signal_series` therefore reproduces the engine's
exact pipeline (same `interval`/`now`), and its integer conversion mirrors the
engine's own `pd.Series(raw).fillna(0).astype(int)` bar for bar.

Zero network connections.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

import data_contract
import strategy


def normalized_signal(signal: pd.Series) -> pd.Series:
    """The signal as the engine sees it: NaN -> 0, integer-valued, index preserved.

    Mirrors backtest_engine.run_backtest's `sig_a` construction exactly, so a mask
    built from this is aligned with the values the entry loop actually tests.
    """
    s = pd.Series(signal)
    if s.empty:
        return pd.Series([], dtype=int, index=s.index)
    return s.fillna(0).astype(int)


def one_shot_entry_mask(signal: pd.Series) -> pd.Series:
    """True only on the first bar of each maximal contiguous run of a nonzero signal.

    False on every flat (0) bar and on every continuation bar of a run. A run is
    delimited by a *change of value*, so both `+1 -> 0 -> +1` and `+1 -> -1` start a
    new run (see module docstring).
    """
    sig = normalized_signal(signal)
    if sig.empty:
        return pd.Series([], dtype=bool, index=sig.index)
    prev = sig.shift(1, fill_value=0)  # before the series starts = flat, so bar 0 can open a call
    return ((sig != 0) & (sig != prev)).astype(bool)


def call_id(signal: pd.Series) -> pd.Series:
    """Run index (0, 1, 2, ...) of each bar's call; -1 on flat bars.

    Diagnostic companion to one_shot_entry_mask -- lets a test or an experiment ask
    "which call did this trade's entry belong to?" instead of re-deriving boundaries.
    """
    sig = normalized_signal(signal)
    if sig.empty:
        return pd.Series([], dtype=int, index=sig.index)
    starts = one_shot_entry_mask(sig)
    ids = starts.cumsum() - 1
    return ids.where(sig != 0, -1).astype(int)


def strategy_signal_series(
    df: pd.DataFrame,
    strategy_name: str,
    interval: str,
    now: Optional[pd.Timestamp] = None,
) -> pd.Series:
    """The raw per-bar signal on the exact frame `run_backtest(df, ...)` will use.

    Same three steps, same order, as the engine: filter_closed_candles(interval, now)
    -> strategy.add_indicators -> STRATEGY_CATALOG[strategy_name]. Returned on the
    engine's own index, so `reindex` inside run_backtest is a no-op rather than a
    silent False-fill.
    """
    closed_df, _dropped = data_contract.filter_closed_candles(df, interval, now=now)
    work = strategy.add_indicators(closed_df)
    if strategy_name not in strategy.STRATEGY_CATALOG:
        raise ValueError(
            f"Nieznana strategia: '{strategy_name}'. Dostepne: {sorted(strategy.STRATEGY_CATALOG.keys())}"
        )
    return normalized_signal(strategy.STRATEGY_CATALOG[strategy_name](work))
