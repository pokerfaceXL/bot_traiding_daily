"""Gate A/B/C scoring for F012-C01. Criteria fixed in spec/features/active/F012-c01-etf-identification/prereg.md."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

RNG = np.random.default_rng(20261006)
PIT_X = ["y_lag1", "y_mean5", "ibit_lag1", "gbtc_lag1", "ret_lag1", "dvz_lag1", "prem_lag1"]
MODELS = {"M1": None, "M2": None, "M3": PIT_X, "M3o": PIT_X + ["ovn_ret"]}
BURN_IN = 60


def folds(n: int) -> np.ndarray:
    """Chronological thirds within Train-1: 1 = fit, 2 = selection, 3 = untouched test."""
    return np.repeat([1, 2, 3], [n // 3, n // 3, n - 2 * (n // 3)])


def _ols(X: np.ndarray, y: np.ndarray, Xp: np.ndarray) -> np.ndarray:
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return np.column_stack([np.ones(len(Xp)), Xp]) @ beta


def predict(t1: pd.DataFrame, model: str, fit_mask: np.ndarray | None = None, walk: bool = False) -> np.ndarray:
    """Prediction of y_T from PIT inputs only. M0 = expanding mean of past y (Train-1 + history
    is not used for M0 to keep the benchmark comparable to the fitted models)."""
    y = t1.y.to_numpy()
    n = len(t1)
    if model == "M0":
        past = np.concatenate([[np.nan], np.cumsum(y)[:-1] / np.arange(1, n)])
        return past
    if model == "M1":
        return t1.y_lag1.to_numpy()
    if model == "M2":
        return t1.y_mean5.to_numpy()
    X = t1[MODELS[model]].to_numpy(dtype=float)
    X = np.nan_to_num(X)  # early rolling NaNs → 0 (neutral; z-scored/demeaned inputs)
    if walk:
        out = np.full(n, np.nan)
        for i in range(BURN_IN, n):
            out[i] = _ols(X[:i], y[:i], X[i:i + 1])[0]
        return out
    return _ols(X[fit_mask], y[fit_mask], X)


def pit_quantile_flag(x: np.ndarray, q: float, min_hist: int = 20) -> np.ndarray:
    """flag_i = |x_i| ≥ q-quantile of |x_0..x_{i-1}| (strictly past values; NaN-safe)."""
    a = np.abs(x)
    out = np.zeros(len(a), dtype=bool)
    for i in range(len(a)):
        h = a[:i][~np.isnan(a[:i])]
        if len(h) >= min_hist and not np.isnan(a[i]):
            out[i] = a[i] >= np.quantile(h, q)
    return out


def score_a(y: np.ndarray, pred: np.ndarray, bench: np.ndarray, large: np.ndarray, pred_large: np.ndarray) -> dict:
    m = ~np.isnan(pred) & ~np.isnan(bench)
    y, pred, bench, large, pred_large = y[m], pred[m], bench[m], large[m], pred_large[m]
    sse, sse0 = np.sum((y - pred) ** 2), np.sum((y - bench) ** 2)
    rho, p_rho = stats.spearmanr(pred, y)
    pear = np.corrcoef(pred, y)[0, 1]
    nz = y != 0
    acc = np.mean(np.sign(pred[nz]) == np.sign(y[nz]))
    acc0 = np.mean(np.sign(bench[nz]) == np.sign(y[nz]))
    L = large & nz
    k = int(np.sum(np.sign(pred[L]) == np.sign(y[L])))
    nL = int(L.sum())
    accL = k / nL if nL else np.nan
    accL0 = np.mean(np.sign(bench[L]) == np.sign(y[L])) if nL else np.nan
    p_accL = stats.binomtest(k, nL, 0.5, alternative="greater").pvalue if nL else np.nan
    base = large.mean()
    hit = large[pred_large].mean() if pred_large.any() else np.nan
    return {"n": int(m.sum()), "oos_r2_vs_M0": 1 - sse / sse0, "spearman": rho, "p_spearman_1s": p_rho / 2 if rho > 0 else 1 - p_rho / 2,
            "pearson": pear, "mae": float(np.mean(np.abs(y - pred))), "mae_M0": float(np.mean(np.abs(y - bench))),
            "dir_acc": acc, "dir_acc_M0": acc0, "n_large": nL, "dir_acc_large": accL, "dir_acc_large_M0": accL0,
            "p_dir_acc_large_1s": p_accL, "p_large_base": base, "n_pred_large": int(pred_large.sum()),
            "p_large_given_pred_large": hit, "lift_large": hit / base if base else np.nan}


def holm(p: list[float]) -> list[float]:
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(order):
        run = max(run, (m - r) * p[i])
        adj[i] = min(1.0, run)
    return list(adj)


def gate_a_verdict(s: dict) -> tuple[bool, dict]:
    p_adj = holm([s["p_spearman_1s"], s["p_dir_acc_large_1s"]])
    checks = {
        "a_r2_pos": s["oos_r2_vs_M0"] > 0,
        "a_spearman_sig": s["spearman"] > 0 and p_adj[0] < 0.05,
        "b_large_acc_ge_0.60": s["dir_acc_large"] >= 0.60,
        "b_large_acc_sig": p_adj[1] < 0.05,
        "b_large_acc_ge_M0": s["dir_acc_large"] >= s["dir_acc_large_M0"],
        "c_lift_ge_1.5": s["lift_large"] >= 1.5,
        "holm_p_spearman": p_adj[0], "holm_p_large_acc": p_adj[1],
    }
    ok = all(v for k, v in checks.items() if not k.startswith("holm"))
    return ok, checks


def boot_ci(x: np.ndarray, n: int = 5000, block: int = 1) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 3:
        return (np.nan, np.nan)
    if block <= 1:
        bs = RNG.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    else:
        nb = int(np.ceil(len(x) / block))
        starts = RNG.integers(0, len(x) - block + 1, size=(n, nb))
        idx = (starts[:, :, None] + np.arange(block)).reshape(n, -1)[:, : len(x)]
        bs = x[idx].mean(axis=1)
    return tuple(np.quantile(bs, [0.025, 0.975]))
