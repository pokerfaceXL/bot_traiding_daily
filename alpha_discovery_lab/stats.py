"""F014 pure statistics: HAC state-vs-complement test, BH-FDR, Spearman IC, distribution summaries."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def p_two_sided(z: float) -> float:
    return math.erfc(abs(z) / math.sqrt(2.0)) if np.isfinite(z) else 1.0


def hac_state_test(y: np.ndarray, s: np.ndarray, lags: int) -> dict:
    """OLS y = a + b*s with Newey-West (Bartlett) SE on b. Observations in time order."""
    y = np.asarray(y, float)
    s = np.asarray(s, float)
    n = len(y)
    n1 = int(s.sum())
    if n1 == 0 or n1 == n:
        return {"b": float("nan"), "se": float("nan"), "z": float("nan"), "p": 1.0}
    X = np.column_stack([np.ones(n), s])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = X * (y - X @ beta)[:, None]
    S = u.T @ u
    for lag in range(1, min(lags, n - 1) + 1):
        w = 1.0 - lag / (lags + 1.0)
        g = u[lag:].T @ u[:-lag]
        S += w * (g + g.T)
    V = xtx_inv @ S @ xtx_inv
    se = math.sqrt(max(V[1, 1], 0.0))
    z = beta[1] / se if se > 0 else float("nan")
    return {"b": float(beta[1]), "se": se, "z": float(z), "p": p_two_sided(z)}


def bh_qvalues(p: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted p-values (q-values), same order as input."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    ranked = p[order] * m / np.arange(1, m + 1)
    q = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(q, 1.0)
    return out.tolist()


def spearman_ic(score: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if len(y) < 10 or np.nanstd(score) == 0:
        return float("nan"), 1.0
    r, p = spearmanr(score, y)
    return float(r), float(p) if np.isfinite(p) else 1.0


def describe(y: pd.Series) -> dict:
    y = y.dropna()
    if y.empty:
        return {"n": 0}
    q = y.quantile([0.1, 0.25, 0.75, 0.9])
    return {"n": int(len(y)), "mean": float(y.mean()), "median": float(y.median()),
            "q10": float(q[0.1]), "q25": float(q[0.25]), "q75": float(q[0.75]), "q90": float(q[0.9]),
            "p_pos": float((y > 0).mean()), "mean_abs": float(y.abs().mean())}


def mfe_mae(px: pd.DataFrame, pos: pd.Series, h: int) -> tuple[pd.Series, pd.Series]:
    """Max favourable / adverse excursion (bp) over bars t+1..t+h vs close_t, in position direction pos (+-1)."""
    c = px["close"]
    hi = pd.concat([px["high"].shift(-k) for k in range(1, h + 1)], axis=1).max(axis=1, skipna=False)
    lo = pd.concat([px["low"].shift(-k) for k in range(1, h + 1)], axis=1).min(axis=1, skipna=False)
    up = 1e4 * np.log(hi / c)
    dn = 1e4 * np.log(lo / c)
    mfe = pd.Series(np.where(pos > 0, up, -dn), index=c.index)
    mae = pd.Series(np.where(pos > 0, dn, -up), index=c.index)
    return mfe, mae
