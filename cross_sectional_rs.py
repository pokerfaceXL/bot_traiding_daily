"""
cross_sectional_rs.py -- cross-sectional relative-strength rank signal family (F006).

Additive module. Ranks each F006 basket symbol's own `lookback`-bar simple return
against its 4 peers at each bar, and turns that rank into a persistent +1/-1/0
directional state: long the top `top_k` ranks, short the bottom `top_k`, flat
everywhere else. See spec/research/F006-hypothesis-cross-sectional-rs.md.

PEER-AWARE PLUMBING. STRATEGY_CATALOG's own contract is callable(df) -> Series: a
single symbol's frame in, no symbol identity on it, no access to peers. That is
incompatible with a signal that needs all 5 symbols' closes at once. The split:

  1. compute_basket_signals() does the real cross-sectional work up front, given
     all 5 symbols' close series directly (not via the catalog).
  2. register_signals() stashes that precomputed {symbol: Series} output, keyed by
     (name, interval), for catalog_entries()'s closures to hand back later.
  3. Because a STRATEGY_CATALOG closure still only receives a single df with no
     symbol/interval on it, the caller (the experiment script) must tell this
     module which basket symbol + interval the NEXT catalog call is for, via
     set_active_context(). This is a documented, single-threaded, experiment-only
     side channel -- entry_masks.strategy_signal_series and backtest_engine.
     run_backtest are called completely unmodified.

A closure asked about a symbol/interval/name combination nothing was registered
for raises RuntimeError. Per the hypothesis note's explicit warning, a "single-df
stub that cannot see its peers" must not silently return zeros -- an unset or
mismatched context is a caller bug, not a flat signal.

Zero network connections.
"""
from __future__ import annotations

import pandas as pd

BASKET = ("SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT")

# Pre-registered name grid (spec/research/F006-hypothesis-cross-sectional-rs.md).
# name -> (lookback, top_k). Do not add names after seeing results.
NAME_GRID = {
    "XS_RS_20_TOP1": (20, 1),
    "XS_RS_48_TOP1": (48, 1),
    "XS_RS_96_TOP1": (96, 1),
    "XS_RS_20_TOP2": (20, 2),
    "XS_RS_48_TOP2": (48, 2),
}

_active_context: tuple | None = None  # (symbol, interval), set by the experiment script
_registry: dict = {}  # (name, interval) -> {symbol: pd.Series}


def set_active_context(symbol: str | None, interval: str | None) -> None:
    """Experiment-script-only side channel: which (symbol, interval) the next
    XS_RS_* catalog call is for. See module docstring, "PEER-AWARE PLUMBING"."""
    global _active_context
    _active_context = (symbol, interval) if symbol is not None else None


def get_active_context() -> tuple | None:
    return _active_context


def register_signals(name: str, interval: str, signals_by_symbol: dict) -> None:
    """Stash compute_basket_signals()'s output so the matching XS_RS_* closure can
    return the right symbol's series once set_active_context() names it."""
    if set(signals_by_symbol.keys()) != set(BASKET):
        raise ValueError(
            f"register_signals({name!r}, {interval!r}): expected exactly the basket "
            f"{BASKET}, got {sorted(signals_by_symbol.keys())}"
        )
    _registry[(name, interval)] = dict(signals_by_symbol)


def compute_basket_signals(closes_by_symbol: dict, lookback: int, top_k: int) -> dict:
    """Rank each basket symbol's own `lookback`-bar simple return against its peers.

    closes_by_symbol: {symbol: pd.Series of close, DatetimeIndex}, exactly the 5
    BASKET symbols.

    Inner-join index: only timestamps present in ALL 5 symbols' close series are
    ranked at all (no forward-fill of a missing peer bar) -- a bar missing from even
    one symbol drops that bar for every symbol.

    ret_i(t) = close_i(t) / close_i(t - lookback) - 1, a `lookback`-bar shift on the
    joined index (bar count, not calendar time -- same convention as this codebase's
    other `.shift(n)` lookbacks, e.g. donchian.py).

    Rank descending by ret (rank 1 = strongest). A bar where ANY of the 5 rets is
    NaN (lookback warm-up) gets no rank at all -- every symbol emits 0 that bar,
    never a partial ranking. Ties broken by symbol name ascending: pandas'
    `rank(method="first")` breaks ties by column order regardless of `ascending`,
    so basket columns are built in `sorted(BASKET)` order to get that tie-break.
    Ranks are then always a permutation of {1..5} once all 5 rets are finite.

    Long (+1) when rank <= top_k. Short (-1) when rank >= (5 - top_k + 1). Else 0.
    top_k in {1, 2} only -- top_k >= 3 would overlap long and short on a 5-symbol
    basket, which this signal's definition does not cover.

    Returns {symbol: pd.Series}, each reindexed back onto that symbol's own INPUT
    index (closes_by_symbol[symbol].index) with 0 fill for any bar outside the
    join -- callers that pass a symbol's post-add_indicators working frame index in
    get a series usable as that frame's "signal" column with no further alignment.
    """
    if set(closes_by_symbol.keys()) != set(BASKET):
        raise ValueError(
            f"compute_basket_signals requires exactly the F006 basket {BASKET}, "
            f"got {sorted(closes_by_symbol.keys())}"
        )
    if top_k not in (1, 2):
        raise ValueError(f"top_k must be 1 or 2 for a 5-symbol basket, got {top_k}")
    if lookback < 1:
        raise ValueError(f"lookback must be >= 1, got {lookback}")

    symbols = sorted(BASKET)  # fixed column order == the tie-break order
    joined_index = None
    for s in symbols:
        idx = closes_by_symbol[s].index
        joined_index = idx if joined_index is None else joined_index.intersection(idx)
    joined_index = joined_index.sort_values()

    closes = pd.DataFrame({s: closes_by_symbol[s].reindex(joined_index).astype(float) for s in symbols})
    rets = closes / closes.shift(lookback) - 1.0

    any_nan = rets.isna().any(axis=1)
    ranks = rets.rank(axis=1, method="first", ascending=False)
    ranks = ranks.where(~any_nan, other=pd.NA)

    long_cut = top_k
    short_cut = len(symbols) - top_k + 1

    out = {}
    for s in symbols:
        r = ranks[s]
        sig = pd.Series(0, index=joined_index, dtype=int)
        sig[r.notna() & (r <= long_cut)] = 1
        sig[r.notna() & (r >= short_cut)] = -1
        out[s] = sig.reindex(closes_by_symbol[s].index, fill_value=0)
    return out


def _lookup_active(name: str) -> pd.Series:
    ctx = _active_context
    if ctx is None:
        raise RuntimeError(
            f"{name}: no active (symbol, interval) context -- call "
            f"cross_sectional_rs.set_active_context() before invoking this catalog entry."
        )
    symbol, interval = ctx
    key = (name, interval)
    if key not in _registry:
        raise RuntimeError(
            f"{name}: no precomputed signals registered for interval={interval!r} -- "
            f"call cross_sectional_rs.register_signals({name!r}, {interval!r}, ...) first."
        )
    signals_by_symbol = _registry[key]
    if symbol not in signals_by_symbol:
        raise RuntimeError(f"{name}: no precomputed signal for symbol={symbol!r}.")
    return signals_by_symbol[symbol]


def catalog_entries() -> dict:
    """New, additive STRATEGY_CATALOG entries: XS_RS_{lookback}_TOP{top_k}.

    Each closure ignores its own df argument (the catalog contract gives it no
    symbol/interval) and instead returns the precomputed series for the currently
    active (symbol, interval) context -- see module docstring."""
    entries = {}
    for name in NAME_GRID:
        entries[name] = lambda df, name=name: _lookup_active(name)
    return entries
