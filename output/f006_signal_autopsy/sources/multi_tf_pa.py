"""
multi_tf_pa.py -- higher-timeframe structure gate for lower-TF continuation/rejection (F006).

Tests spec/research/F006-hypothesis-multi-tf-pa.md (H-MULTI-TF-PA-01). Additive module: it
defines catalog_entries() for scripts/f006_family_runner.py's run_family() to register into
strategy.STRATEGY_CATALOG at runtime only -- this module is NOT imported or wired by strategy.py
and changes nothing in it, per the ticket ("no merge to main, no production strategy.py change").

Mechanism: classify a HIGHER timeframe's completed-block swing structure into a bias
(+1 uptrend / -1 downtrend / 0 undefined-or-mixed), recomputed only when a HTF block completes,
then gate a LOWER-timeframe one-shot continuation (break of a LTF rolling extreme or of the
just-completed HTF block's own extreme) or rejection (pin at a LTF rolling extreme) signal to
fire only when it agrees with that bias.

HTF definition (frozen in the hypothesis note): the LTF bar spacing is inferred from the frame's
own DatetimeIndex (median consecutive delta) -- no `interval` string is threaded through
catalog_entries()'s fn(df) signature, matching every other F006 family's calling convention
(tests/test_signal_family_contract.py calls fn(df) alone). ~1h spacing -> HTF = non-overlapping
4h blocks; ~4h spacing -> HTF = non-overlapping daily blocks. Both alignments are calendar
(`floor`), not count-based, so a gap in the LTF series does not desynchronize a block boundary.

Causality: HTF block high/low for block B is only exposed to LTF bars belonging to a LATER
block (via shift(1)/shift(2) on the block-level series, never a per-bar transform read before B
has completed) -- no LTF bar ever sees the still-forming HTF block it itself belongs to. Every
LTF rolling extreme used inside a candidate name is the existing Donchian-style
`.rolling(N).max()/.min()`.shift(1)`, excluding the current bar, unchanged in kind from
donchian.py. All crosses are strict (equality excluded); the PIN name's own bar-range/rolling
comparisons are non-strict, per the frozen note.

Zero network connections. Zero third-party dependency: pure pandas over OHLC.
"""
from __future__ import annotations

from typing import Callable, Dict, Tuple

import pandas as pd

# LTF spacing below this is classified as ~1h -> 4h HTF blocks; at or above, ~4h -> daily blocks.
_LTF_SPACING_THRESHOLD = pd.Timedelta(hours=2)


def _htf_freq(index: pd.DatetimeIndex) -> str:
    """Infers the HTF block frequency from the LTF frame's own bar spacing (median delta)."""
    diffs = pd.Series(index).diff().dropna()
    median = diffs.median()
    if pd.isna(median) or median < _LTF_SPACING_THRESHOLD:
        return "4h"  # ~1h LTF (or too short a frame to tell) -> 4h HTF blocks
    return "1D"  # ~4h LTF -> daily HTF blocks


def _htf_bias_and_block_levels(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Returns (bias, prior_completed_block_high, prior_completed_block_low), all reindexed onto
    df's own LTF index. bias/levels for the LTF bars of forming HTF block B depend only on
    completed blocks B-1 and B-2 -- never on block B's own (possibly future, within-block) bars.
    """
    idx = pd.DatetimeIndex(df.index)
    freq = _htf_freq(idx)
    block_id = pd.Series(idx.floor(freq), index=df.index)

    block_stats = pd.DataFrame({"block_id": block_id, "high": df["high"], "low": df["low"]})
    agg = block_stats.groupby("block_id", sort=True).agg(high=("high", "max"), low=("low", "min"))

    prior1_high = agg["high"].shift(1)
    prior1_low = agg["low"].shift(1)
    prior2_high = agg["high"].shift(2)
    prior2_low = agg["low"].shift(2)

    higher_high_higher_low = (prior1_high > prior2_high) & (prior1_low > prior2_low)
    lower_high_lower_low = (prior1_high < prior2_high) & (prior1_low < prior2_low)

    bias_per_block = pd.Series(0.0, index=agg.index)
    bias_per_block = bias_per_block.mask(higher_high_higher_low, 1.0)
    bias_per_block = bias_per_block.mask(lower_high_lower_low, -1.0)
    # fewer than two completed blocks yet (either prior1 or prior2 undefined) -> bias 0, not
    # carried forward from any earlier comparison.
    bias_per_block = bias_per_block.mask(prior2_high.isna() | prior2_low.isna(), 0.0)

    bias = block_id.map(bias_per_block).fillna(0.0)
    block_high = block_id.map(prior1_high)
    block_low = block_id.map(prior1_low)
    return bias, block_high, block_low


def _strict_cross_up(series: pd.Series, level: pd.Series) -> pd.Series:
    return (series > level) & (series.shift(1) <= level.shift(1))


def _strict_cross_down(series: pd.Series, level: pd.Series) -> pd.Series:
    return (series < level) & (series.shift(1) >= level.shift(1))


def _make_htf_brk(n: int) -> Callable[[pd.DataFrame], pd.Series]:
    def sig(df: pd.DataFrame) -> pd.Series:
        bias, _prior_high, _prior_low = _htf_bias_and_block_levels(df)
        high = df["high"]
        low = df["low"]
        close = df["close"]
        level_up = high.rolling(n).max().shift(1)
        level_dn = low.rolling(n).min().shift(1)
        cross_up = _strict_cross_up(close, level_up)
        cross_dn = _strict_cross_down(close, level_dn)
        out = pd.Series(0.0, index=df.index)
        out = out.mask((bias == 1.0) & cross_up, 1.0)
        out = out.mask((bias == -1.0) & cross_dn, -1.0)
        return out

    return sig


def sig_htf_block(df: pd.DataFrame) -> pd.Series:
    """MTFP_HTF_BLOCK: strict cross of close through the prior *completed* HTF block's own
    high (bias +1) or low (bias -1) -- the HTF-block-level analogue of the BRKn names."""
    bias, prior_high, prior_low = _htf_bias_and_block_levels(df)
    close = df["close"]
    cross_up = _strict_cross_up(close, prior_high)
    cross_dn = _strict_cross_down(close, prior_low)
    out = pd.Series(0.0, index=df.index)
    out = out.mask((bias == 1.0) & cross_up, 1.0)
    out = out.mask((bias == -1.0) & cross_dn, -1.0)
    return out


def sig_htf_pin(df: pd.DataFrame) -> pd.Series:
    """MTFP_HTF_PIN: pin/rejection at the prior-20-LTF-bar extreme in the bias direction.
    Long pin: bar low <= prior-20 low (shift(1) rolling) and close in the upper third of that
    bar's own high-low range, gated to bias=+1. Short mirror, gated to bias=-1. 0 if bias
    undefined (0) or the pin condition does not hold.
    """
    bias, _prior_high, _prior_low = _htf_bias_and_block_levels(df)
    high = df["high"]
    low = df["low"]
    close = df["close"]
    level_low20 = low.rolling(20).min().shift(1)
    level_high20 = high.rolling(20).max().shift(1)
    bar_range = high - low
    upper_third_boundary = low + (2.0 / 3.0) * bar_range
    lower_third_boundary = low + (1.0 / 3.0) * bar_range

    long_pin = (low <= level_low20) & (close >= upper_third_boundary)
    short_pin = (high >= level_high20) & (close <= lower_third_boundary)

    out = pd.Series(0.0, index=df.index)
    out = out.mask((bias == 1.0) & long_pin, 1.0)
    out = out.mask((bias == -1.0) & short_pin, -1.0)
    return out


def catalog_entries() -> Dict[str, Callable[[pd.DataFrame], pd.Series]]:
    """The five pre-registered MTFP_* names, frozen in the hypothesis note. Runtime-registered
    only (f006_family_runner.register_catalog_entries) -- never wired into strategy.py."""
    return {
        "MTFP_HTF_BRK20": _make_htf_brk(20),
        "MTFP_HTF_BRK10": _make_htf_brk(10),
        "MTFP_HTF_BRK5": _make_htf_brk(5),
        "MTFP_HTF_BLOCK": sig_htf_block,
        "MTFP_HTF_PIN": sig_htf_pin,
    }
