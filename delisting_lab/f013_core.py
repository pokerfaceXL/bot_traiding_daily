"""F013 pure helpers (no I/O, no network): prices, returns, costs, bootstrap, tail stats.

Conventions (prereg §3):
- Entry/exit price = open of the first 1-minute bar starting at or after the target time.
- Sub-minute entries = first trade at or after the target time (ticks).
- Short gross bp = -(exit/entry - 1) * 1e4. Funding: short receives positive rates with
  funding time in (entry, exit]. net = gross + funding - cost_rt.
- Uncertainty = cluster bootstrap of the event mean (resample clusters), seed 13, 10 000 draws.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

COST_LADDER = (34, 50, 75, 100, 150, 200)
OWNER_CONTEXT_BP = 9.9
DECISION_BP = 34
STRESS_BP = 75
N_BOOT = 10_000
SEED = 13
N_MIN = 8
MAX_BAR_WAIT = pd.Timedelta(minutes=30)
MAX_TICK_WAIT = pd.Timedelta(minutes=5)


def bar_open_at(bars: pd.DataFrame | None, t: pd.Timestamp, max_wait=MAX_BAR_WAIT) -> tuple[pd.Timestamp | None, float]:
    """(bar start, open) of the first 1m bar starting at or after t; NaN if none within max_wait."""
    if bars is None or not len(bars):
        return None, np.nan
    i = bars.index.searchsorted(t, side="left")
    if i >= len(bars) or bars.index[i] - t > max_wait:
        return None, np.nan
    return bars.index[i], float(bars.open.iloc[i])


def close_before(bars: pd.DataFrame | None, t: pd.Timestamp, max_stale=pd.Timedelta(hours=6)) -> float:
    """Close of the last 1m bar that ENDED at or before t (causal pre-P price)."""
    if bars is None or not len(bars):
        return np.nan
    i = bars.index.searchsorted(t - pd.Timedelta(minutes=1), side="right") - 1
    if i < 0 or t - bars.index[i] > max_stale:
        return np.nan
    return float(bars.close.iloc[i])


def first_tick_at(ticks: pd.DataFrame | None, t: pd.Timestamp, max_wait=MAX_TICK_WAIT) -> tuple[pd.Timestamp | None, float]:
    if ticks is None or not len(ticks):
        return None, np.nan
    i = ticks.ts.searchsorted(t, side="left")
    if i >= len(ticks) or ticks.ts.iloc[i] - t > max_wait:
        return None, np.nan
    return ticks.ts.iloc[i], float(ticks.price.iloc[i])


def short_bp(p_entry: float, p_exit: float) -> float:
    if not (np.isfinite(p_entry) and np.isfinite(p_exit)) or p_entry <= 0:
        return np.nan
    return -(p_exit / p_entry - 1.0) * 1e4


def funding_bp(fund: pd.DataFrame | None, t0, t1) -> float:
    """Funding received by a short over (t0, t1] in bp of notional (0 if no print in window)."""
    if fund is None or not len(fund):
        return np.nan
    f = fund.rate
    return float(f[(f.index > t0) & (f.index <= t1)].sum() * 1e4)


def exit_target(entry: pd.Timestamp, eff: pd.Timestamp, hold=pd.Timedelta(hours=72)) -> pd.Timestamp:
    return min(entry + hold, eff - pd.Timedelta(hours=1))


def ols_beta(y: np.ndarray, x: np.ndarray, min_obs: int = 200) -> tuple[float, int]:
    m = np.isfinite(y) & np.isfinite(x)
    n = int(m.sum())
    if n < min_obs:
        return 1.0, n
    x, y = x[m], y[m]
    return float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)), n


# ------------------------------------------------------------------ inference
def cluster_boot(values, clusters, n_boot=N_BOOT, seed=SEED) -> np.ndarray:
    """Bootstrap distribution of the pooled event mean, resampling whole clusters."""
    v = np.asarray(values, float)
    c = np.asarray(clusters)
    m = np.isfinite(v)
    v, c = v[m], c[m]
    if len(v) == 0:
        return np.array([np.nan])
    codes, inv = np.unique(c, return_inverse=True)
    sums = np.bincount(inv, weights=v)
    cnts = np.bincount(inv).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(codes), size=(n_boot, len(codes)))
    return sums[idx].sum(1) / cnts[idx].sum(1)


def ci(values, clusters, n_boot=N_BOOT, seed=SEED) -> tuple[float, float]:
    b = cluster_boot(values, clusters, n_boot, seed)
    return float(np.nanpercentile(b, 2.5)), float(np.nanpercentile(b, 97.5))


def describe(values, clusters, n_boot=N_BOOT, seed=SEED) -> dict:
    v = np.asarray(values, float)
    m = np.isfinite(v)
    lo, hi = ci(v, clusters, n_boot, seed) if m.any() else (np.nan, np.nan)
    return {"n": int(m.sum()), "n_clusters": int(len(set(np.asarray(clusters)[m]))),
            "mean": float(np.nanmean(v)) if m.any() else np.nan,
            "median": float(np.nanmedian(v)) if m.any() else np.nan, "ci_lo": lo, "ci_hi": hi}


def winsor_mean(v, lo=5, hi=95) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    a, b = np.percentile(v, [lo, hi])
    return float(np.clip(v, a, b).mean())


def trimmed_mean(v, frac=0.10) -> float:
    v = np.sort(np.asarray(v, float)[np.isfinite(v)])
    k = int(np.floor(len(v) * frac))
    return float(v[k: len(v) - k].mean())


def tail_stats(v) -> dict:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    s = np.sort(v)[::-1]
    out = {"n": len(v), "mean": v.mean(), "median": np.median(v), "trimmed10_mean": trimmed_mean(v),
           "winsor5_95_mean": winsor_mean(v)}
    for k in (1, 3, 5):
        out[f"top{k}_share_of_sum"] = float(s[:k].sum() / v.sum()) if v.sum() != 0 else np.nan
        out[f"mean_ex_top{k}"] = float(s[k:].mean()) if len(s) > k else np.nan
    return {k: float(x) for k, x in out.items()}


RESTRICT_PAT = re.compile(r"[^.\n]*(?:not (?:be )?(?:allowed|able) to open new position|reduce[- ]only|close[- ]only|"
                          r"no (?:more )?new positions?)[^.\n]*", re.I)


def restriction_times(text: str, parse_datetimes) -> list[int]:
    """Explicit UTC times (ms) attached to an opening-restriction sentence in an article body."""
    out = []
    for m in RESTRICT_PAT.finditer(text or ""):
        out += [ts for _, ts in parse_datetimes(m.group(0))]
    return out


def notice_bin(h: float) -> str:
    if h <= 24:
        return "(0,24h]"
    if h <= 72:
        return "(24h,72h]"
    if h <= 168:
        return "(72h,168h]"
    return ">168h"
