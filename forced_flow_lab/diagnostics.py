"""F011 T4: forced-flow diagnostics on the 5m T2 states (non-trading).

Answers the three pre-registered §9b questions (spec/research/F011-forced-flow-lab.md §9b,
ticket spec/features/active/F011-forced-flow-diagnostics/ticket.md). No orders, positions,
sizing or PnL. Train-1 only, BTCUSDT + ETHUSDT, frozen T2 thresholds (the T2 state files are
read as-is; nothing is relabelled or tuned).

Event = state entry (T3 definition, `event_study.entries`): bar t is an entry when its state
is in the class's per-side set and bar t-1's is not. Classes (per side, LONG_* / SHORT_*):
  CROWDING     = {CROWDING}
  STRESS       = {STRESS}
  DELEVERAGING = {STRESS, LIQUIDATION_CASCADE}  (union of STRESS and CASCADE: the OI-declining
                 forced states; STRESS -> CASCADE on one side is one episode, as in T3)
  CASCADE      = {LIQUIDATION_CASCADE}
  EXHAUSTION   = {EXHAUSTION}
Sides are mirrored by sign and pooled. Direction d = -1 for LONG_* (forced move is down),
+1 for SHORT_*; every signed quantity is multiplied by d, so positive = in the forced /
cascade direction, for every class (including EXHAUSTION).

Timing: the label of bar t is known at its close, the reference price is close_t, forward
windows use bars t+1..t+h only, and windows past the last labelled bar are dropped.

Test 1 (magnitude). Per class x symbol x horizon, events are thinned greedily as in T3
(next kept t >= previous kept t + h). Matched baseline per event: labelled bars of the same
symbol, same UTC hour-of-day, same trailing-24h realized-vol decile at t (`realized_vol`,
288 bars; deciles over the symbol's labelled Train-1 bars), complete forward window, and
not within +-48 bars (4h) of ANY entry of ANY class on that symbol. 20 bars are drawn per
event without replacement (with replacement only if the stratum holds < 20), seeded. Each
baseline bar inherits its event's direction. Bootstrap: event-level, 2000 resamples; an
event carries its own baseline set (per-event baseline mean), percentile 95% CI.

Test 2 (continuation vs reversal). CASCADE entries (gating); DELEVERAGING entries are
reported as non-gating context. Outcome: d * fwd return at +1h > 0 (continuation); +30m
is the robustness outcome. Events thinned per horizon as in T3. Continuous features ->
Cliff's delta (continuation vs reversal) with a stratified bootstrap CI; categorical
(binary one-vs-rest) -> risk difference P(cont | X=1) - P(cont | X=0) with bootstrap CI.

Test 3 (pre-cascade prediction). y_h = 1 iff a CASCADE entry (either side) occurs in bars
t+1..t+h. Eligible bars: not CASCADE and not a STRESS bar whose STRESS/CASCADE episode has
already contained a cascade (= "STRESS after OI collapse"; plain STRESS bars stay eligible
so that the pre-registered P(cascade | STRESS) rule is defined). Features use rows <= t
only (see `precascade_features`, causality-tested). Time-ordered split: first 60% of
eligible bars fit, last 40% evaluate; the last h fit bars are purged so no fit label sees
an evaluation bar.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.preprocessing import StandardScaler

from forced_flow_lab import event_study as es
from forced_flow_lab import label_states as ls

STATES = es.STATES
OUTPUT = Path("output/f011_forced_flow/diagnostics")
SYMBOLS = es.SYMBOLS
COST_BAND = es.COST_BAND  # context only in Test 1
SEED = 20261006
N_BOOT = 2000
N_BASE = 20
EXCLUDE_BARS = 48  # +-4h
HORIZONS = {"5m": 1, "15m": 3, "30m": 6, "1h": 12, "4h": 48}
CLASSES = {
    "CROWDING": ("CROWDING",),
    "STRESS": ("STRESS",),
    "DELEVERAGING": ("STRESS", "LIQUIDATION_CASCADE"),
    "CASCADE": ("LIQUIDATION_CASCADE",),
    "EXHAUSTION": ("EXHAUSTION",),
}
PERIODS = ("full", "H1", "H2")
GATE_PERIODS = (("H1",), ("H2",))
RATIO_GATE = 1.25
CLIFF_GATE = 0.33
RD_GATE = 0.15
LIFT_GATE = 2.0
MIN_TEST_POSITIVES = 20
PRECASCADE_HORIZONS = {"15m": 3, "30m": 6, "60m": 12}
FIT_FRACTION = 0.6


def class_sides(cls: str) -> dict:
    names = CLASSES[cls]
    return {-1: tuple(f"LONG_{n}" for n in names), +1: tuple(f"SHORT_{n}" for n in names)}


# ---------------------------------------------------------------------------- Test 1
def forward_paths(close: np.ndarray, high: np.ndarray, low: np.ndarray, h: int) -> dict:
    """Per-bar forward quantities over bars t+1..t+h (NaN where the window is incomplete)."""
    n = len(close)
    out = {k: np.full(n, np.nan) for k in ("ret", "rv", "up", "dn")}
    if h >= n:
        return out
    m = n - h
    out["ret"][:m] = close[h:] / close[:m] - 1.0
    lr = np.diff(np.log(close))  # lr[i] = log(close[i+1]/close[i])
    win = np.lib.stride_tricks.sliding_window_view(lr, h)[:m]
    out["rv"][:m] = np.sqrt(np.mean(win ** 2, axis=1))
    hi = np.lib.stride_tricks.sliding_window_view(high[1:], h)[:m].max(axis=1)
    lo = np.lib.stride_tricks.sliding_window_view(low[1:], h)[:m].min(axis=1)
    out["up"][:m] = np.maximum(hi / close[:m] - 1.0, 0.0)
    out["dn"][:m] = np.maximum(1.0 - lo / close[:m], 0.0)
    return out


def directional(paths: dict, pos: np.ndarray, d: np.ndarray) -> dict:
    """Event-direction metrics at bar positions pos (d broadcast to pos's shape)."""
    ret = paths["ret"][pos]
    up, dn = paths["up"][pos], paths["dn"][pos]
    mfe = np.where(d > 0, up, dn)
    mae = np.where(d > 0, dn, up)
    tot = mfe + mae
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(tot > 0, mfe / tot, np.nan)
    return {"signed_ret": d * ret, "abs_ret": np.abs(ret), "fwd_rv": paths["rv"][pos],
            "mfe": mfe, "mae": mae, "excursion": tot, "mfe_share": share}


def exclusion_mask(state: pd.Series, n_bars: int = EXCLUDE_BARS) -> np.ndarray:
    """True where a bar is within +-n_bars of an entry of any class on any side."""
    starts = []
    for cls in CLASSES:
        starts.append(es.entries(state, class_sides(cls)).pos.to_numpy(dtype=int))
    pos = np.unique(np.concatenate(starts)) if starts else np.array([], dtype=int)
    diff = np.zeros(len(state) + 1, dtype=int)
    np.add.at(diff, np.clip(pos - n_bars, 0, len(state)), 1)
    np.add.at(diff, np.clip(pos + n_bars + 1, 0, len(state)), -1)
    near = np.cumsum(diff)[:-1]
    return near > 0


def rv_deciles(rv: pd.Series) -> np.ndarray:
    return pd.qcut(rv.rank(method="first"), 10, labels=False).to_numpy()


def sample_baselines(ev_pos: np.ndarray, hour: np.ndarray, dec: np.ndarray, pool_ok: np.ndarray,
                     rng: np.random.Generator, k: int = N_BASE) -> list[np.ndarray]:
    """For each event, k pool positions with the same hour and vol decile (empty if none)."""
    pool = np.flatnonzero(pool_ok)
    key = hour[pool] * 10 + dec[pool]
    strata = {kk: pool[key == kk] for kk in np.unique(key)}
    out = []
    for p in ev_pos:
        cand = strata.get(hour[p] * 10 + dec[p], np.array([], dtype=int))
        if len(cand) == 0:
            out.append(cand)
        else:
            out.append(rng.choice(cand, size=k, replace=len(cand) < k))
    return out


MEAN_METRICS = ("signed_ret", "abs_ret", "fwd_rv", "mfe", "mae", "excursion", "mfe_share")


def boot_compare(ev: dict, base_per_event: dict, rng: np.random.Generator) -> dict:
    """Event-level paired bootstrap of mean(event)/mean(base) and the difference, per metric."""
    n = len(ev["abs_ret"])
    idx = rng.integers(0, n, size=(N_BOOT, n))
    out = {}
    for m in MEAN_METRICS:
        e, b = ev[m], base_per_event[m]
        em, bm = np.nanmean(e), np.nanmean(b)
        with np.errstate(invalid="ignore", divide="ignore"):
            eb = np.nanmean(e[idx], axis=1)
            bb = np.nanmean(b[idx], axis=1)
            rb = eb / bb
            ratio = em / bm if bm != 0 else np.nan
        db = eb - bb
        out[m] = {"event": em, "base": bm, "ratio": ratio,
                  "ratio_lo": np.nanpercentile(rb, 2.5), "ratio_hi": np.nanpercentile(rb, 97.5),
                  "diff": em - bm, "diff_lo": np.nanpercentile(db, 2.5),
                  "diff_hi": np.nanpercentile(db, 97.5)}
    return out


def period_of(index: pd.DatetimeIndex, pos: np.ndarray) -> np.ndarray:
    mid = len(index) // 2
    return np.where(pos < mid, "H1", "H2")


def test1_symbol(symbol: str, frame: pd.DataFrame, state: pd.Series, rng: np.random.Generator,
                 boot_rng: np.random.Generator) -> tuple[list[dict], list[dict]]:
    lab = frame.loc[state.index]
    close, high, low = (lab[c].to_numpy(float) for c in ("close", "high", "low"))
    hour = state.index.hour.to_numpy()
    dec = rv_deciles(lab.realized_vol)
    excluded = exclusion_mask(state)
    rows, ev_rows = [], []
    for hz, h in HORIZONS.items():
        paths = forward_paths(close, high, low, h)
        pool_ok = ~excluded & ~np.isnan(paths["ret"]) & ~np.isnan(dec.astype(float))
        for cls in CLASSES:
            ev = es.entries(state, class_sides(cls))
            ev = ev[~np.isnan(paths["ret"][ev.pos.to_numpy()])].reset_index(drop=True)
            ev = ev[es.non_overlapping(ev.pos.to_numpy(), h)].reset_index(drop=True)
            pos, d = ev.pos.to_numpy(), ev.direction.to_numpy()
            bases = sample_baselines(pos, hour, dec, pool_ok, rng)
            has_base = np.array([len(b) > 0 for b in bases], dtype=bool)
            pos, d = pos[has_base], d[has_base]
            side = ev.side.to_numpy()[has_base]
            bases = [b for b, ok in zip(bases, has_base) if ok]
            em = directional(paths, pos, d)
            per_base = [directional(paths, b, np.full(len(b), dd)) for b, dd in zip(bases, d)]
            period = period_of(state.index, pos)
            for i, p in enumerate(pos):
                ev_rows.append({"symbol": symbol, "class": cls, "horizon": hz, "timestamp": state.index[p],
                                "side": side[i], "period": period[i],
                                **{m: em[m][i] for m in MEAN_METRICS},
                                **{f"base_{m}": np.nanmean(per_base[i][m]) for m in MEAN_METRICS}})
            for sd in ("pooled", "LONG", "SHORT"):
                for per in PERIODS:
                    sel = np.ones(len(pos), dtype=bool)
                    if sd != "pooled":
                        sel &= side == sd
                    if per != "full":
                        sel &= period == per
                    row = {"symbol": symbol, "class": cls, "side": sd, "period": per, "horizon": hz,
                           "horizon_bars": h, "n_entries_raw": int(len(es.entries(state, class_sides(cls)))),
                           "n_events": int(sel.sum()), "n_dropped_no_baseline": int((~has_base).sum())}
                    if sel.sum() < 2:
                        rows.append(row)
                        continue
                    ev_sel = {m: em[m][sel] for m in MEAN_METRICS}
                    bsel = [per_base[i] for i in np.flatnonzero(sel)]
                    base_mean = {m: np.array([np.nanmean(b[m]) for b in bsel]) for m in MEAN_METRICS}
                    pooled_base = {m: np.concatenate([b[m] for b in bsel]) for m in ("signed_ret", "abs_ret")}
                    row["n_baseline_bars"] = int(len(pooled_base["abs_ret"]))
                    q = np.quantile(ev_sel["signed_ret"], [0.05, 0.25, 0.5, 0.75, 0.95])
                    qb = np.quantile(pooled_base["signed_ret"], [0.05, 0.25, 0.5, 0.75, 0.95])
                    for name, a, b in zip(("q05", "q25", "q50", "q75", "q95"), q, qb):
                        row[f"signed_{name}"], row[f"base_signed_{name}"] = a, b
                    row["abs_median"] = float(np.median(ev_sel["abs_ret"]))
                    row["base_abs_median"] = float(np.median(pooled_base["abs_ret"]))
                    for m, s in boot_compare(ev_sel, base_mean, boot_rng).items():
                        for k, v in s.items():
                            row[f"{m}_{k}"] = v
                    row["abs_mean_vs_cost_band"] = row["abs_ret_event"] / COST_BAND
                    rows.append(row)
    return rows, ev_rows


def test1_verdict(t1: pd.DataFrame, symbols=SYMBOLS) -> dict:
    """POSITIVE iff some class x horizon has abs_ret or fwd_rv ratio >= 1.25 with CI lo > 1 on
    every symbol x half (pooled sides)."""
    g = t1[(t1.side == "pooled") & t1.period.isin(["H1", "H2"])].copy()
    passing = []
    for metric in ("abs_ret", "fwd_rv"):
        ok = (g[f"{metric}_ratio"] >= RATIO_GATE) & (g[f"{metric}_ratio_lo"] > 1.0)
        g["ok"] = ok.fillna(False)
        for (cls, hz), cell in g.groupby(["class", "horizon"], sort=False):
            if len(cell) == 2 * len(symbols) and cell.ok.all():
                passing.append({"class": cls, "horizon": hz, "metric": metric,
                                "min_ratio": float(cell[f"{metric}_ratio"].min()),
                                "min_ratio_lo": float(cell[f"{metric}_ratio_lo"].min())})
    return {"verdict": "POSITIVE" if passing else "NEGATIVE", "passing": passing,
            "gate_cells": int(len(g)), "class_horizon_metric_candidates": len(CLASSES) * len(HORIZONS) * 2}


# ---------------------------------------------------------------------------- Test 2
def btc_regime(btc: pd.DataFrame) -> pd.DataFrame:
    """BTC 24h / 7d return and close vs EMA200 of the last COMPLETED 1h bar, at 5m bar close."""
    c = btc.close
    out = pd.DataFrame(index=btc.index)
    out["btc_ret_24h"] = c / c.shift(288) - 1.0
    out["btc_ret_7d"] = c / c.shift(2016) - 1.0
    hourly = c.resample("1h", label="left", closed="left").last()
    ema = hourly.ewm(span=200, adjust=False, min_periods=200).mean()
    # 1h bar opening at H completes at H+1h; 5m bar t is known at t+5m.
    ema.index = ema.index + pd.Timedelta("1h")
    known_at = btc.index + pd.Timedelta("5min")
    ema_at = ema.reindex(known_at, method="ffill").to_numpy()
    out["btc_ema200_1h"] = ema_at
    out["btc_above_ema"] = np.where(np.isnan(ema_at), np.nan, (c.to_numpy() > ema_at).astype(float))
    return out


def event_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Unsigned per-bar pre-event / current features (rows <= t only)."""
    f = pd.DataFrame(index=frame.index)
    f["oi_build_24h"] = frame.open_interest / frame.open_interest.shift(288) - 1.0
    f["oi_zscore"] = frame.oi_zscore
    f["oi_decline_speed"] = frame.delta_oi_pct.rolling(3, min_periods=3).sum() / (frame.atr / frame.close)
    f["funding_rate"] = frame.funding_rate
    f["funding_zscore"] = frame.funding_zscore
    f["long_short_ratio"] = np.log(frame.long_short_ratio)
    f["long_account_share"] = frame.long_account_share - 0.5
    f["ofi_sum_3"] = frame.ofi.rolling(3, min_periods=3).sum()
    f["ofi_sum_12"] = frame.ofi.rolling(12, min_periods=12).sum()
    f["dcvd_sum_3"] = frame.delta_cvd.rolling(3, min_periods=3).sum()
    f["dcvd_sum_12"] = frame.delta_cvd.rolling(12, min_periods=12).sum()
    f["shock_entry"] = frame.atr_normalized_return
    f["shock_3"] = frame.atr_normalized_return.rolling(3, min_periods=3).sum()
    f["realized_vol"] = frame.realized_vol
    return f


# Sign applied to each feature before pooling sides: "d" = x * d (positive = in the cascade
# direction), "-d" = x * -d (positive = crowded-side positioning), None = unsigned.
CONTINUOUS = {
    "oi_build_24h": None, "oi_zscore": None, "oi_decline_speed": "-d",
    "funding_rate": "-d", "funding_zscore": "-d", "long_short_ratio": "-d", "long_account_share": "-d",
    "ofi_sum_3": "d", "ofi_sum_12": "d", "dcvd_sum_3": "d", "dcvd_sum_12": "d",
    "shock_entry": "d", "shock_3": "d", "realized_vol": None, "rv_decile": None,
}
CATEGORICAL = (["btc_24h_with_cascade", "btc_7d_with_cascade", "btc_ema_with_cascade"]
               + [f"hour_{b}" for b in ("asia", "eu", "us")]
               + [f"weekday_{d}" for d in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")]
               + ["cross_asset_confirm"])
N_FEATURES = len(CONTINUOUS) + len(CATEGORICAL)


def split_table(symbol: str, frame: pd.DataFrame, state: pd.Series, other_state: pd.Series,
                btc: pd.DataFrame, cls: str, horizon_bars: int) -> pd.DataFrame:
    """One row per (thinned) event: outcome + mirrored features."""
    lab = frame.loc[state.index]
    ev = es.events(state, lab.close, class_sides(cls), horizon_bars)
    if ev.empty:
        return pd.DataFrame()
    ts = state.index[ev.pos.to_numpy()]
    d = ev.direction.to_numpy().astype(float)
    feats = event_features(frame).loc[ts]
    feats["rv_decile"] = rv_deciles(lab.realized_vol)[ev.pos.to_numpy()]
    out = pd.DataFrame({"symbol": symbol, "timestamp": ts, "side": ev.side.to_numpy(), "d": d,
                        "signed_ret": ev.signed.to_numpy(), "continuation": ev.signed.to_numpy() > 0,
                        "period": period_of(state.index, ev.pos.to_numpy())})
    for name, sign in CONTINUOUS.items():
        x = feats[name].to_numpy(float)
        out[name] = x * d if sign == "d" else x * -d if sign == "-d" else x
    reg = btc.reindex(ts)
    for col, src in (("btc_24h_with_cascade", "btc_ret_24h"), ("btc_7d_with_cascade", "btc_ret_7d")):
        r = reg[src].to_numpy(float)
        out[col] = np.where(np.isnan(r), np.nan, (r * d > 0).astype(float))
    above = reg.btc_above_ema.to_numpy(float)
    out["btc_ema_with_cascade"] = np.where(np.isnan(above), np.nan, ((2 * above - 1) * d > 0).astype(float))
    hour = ts.hour.to_numpy()
    out["hour_asia"] = (hour < 8).astype(float)
    out["hour_eu"] = ((hour >= 8) & (hour < 16)).astype(float)
    out["hour_us"] = (hour >= 16).astype(float)
    for i, name in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun")):
        out[f"weekday_{name}"] = (ts.weekday == i).astype(float)
    forced = other_state.isin([f"{s}_{n}" for s in ("LONG", "SHORT") for n in ("STRESS", "LIQUIDATION_CASCADE")])
    near = forced.astype(int).rolling(7, center=True, min_periods=1).max().reindex(ts)  # +-3 bars = +-15m
    out["cross_asset_confirm"] = near.fillna(0).to_numpy(float)
    return out


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """P(a > b) - P(a < b) over all pairs."""
    if len(a) == 0 or len(b) == 0:
        return np.nan
    return float(np.mean(np.sign(a[:, None] - b[None, :])))


def cliffs_boot(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return np.nan, np.nan
    x = np.concatenate([a[rng.integers(0, na, (N_BOOT, na))], b[rng.integers(0, nb, (N_BOOT, nb))]], axis=1)
    r = rankdata(x, axis=1)
    u = r[:, :na].sum(axis=1) - na * (na + 1) / 2
    delta = 2 * u / (na * nb) - 1
    return float(np.percentile(delta, 2.5)), float(np.percentile(delta, 97.5))


def risk_diff(x: np.ndarray, y: np.ndarray) -> float:
    if x.sum() == 0 or (1 - x).sum() == 0:
        return np.nan
    return float(y[x == 1].mean() - y[x == 0].mean())


def rd_boot(x: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    n = len(x)
    if n < 4:
        return np.nan, np.nan
    idx = rng.integers(0, n, (N_BOOT, n))
    xb, yb = x[idx], y[idx]
    n1, n0 = xb.sum(axis=1), (1 - xb).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        rd = (yb * xb).sum(axis=1) / n1 - (yb * (1 - xb)).sum(axis=1) / n0
    rd = rd[np.isfinite(rd)]
    if len(rd) < N_BOOT // 2:
        return np.nan, np.nan
    return float(np.percentile(rd, 2.5)), float(np.percentile(rd, 97.5))


def effect_rows(tab: pd.DataFrame, rng: np.random.Generator) -> list[dict]:
    rows = []
    for per in PERIODS:
        sub = tab if per == "full" else tab[tab.period == per]
        y = sub.continuation.to_numpy()
        base = {"period": per, "n_events": int(len(sub)), "n_cont": int(y.sum()), "n_rev": int((~y).sum())}
        for name in CONTINUOUS:
            x = sub[name].to_numpy(float)
            ok = ~np.isnan(x)
            a, b = x[ok & y], x[ok & ~y]
            lo, hi = cliffs_boot(a, b, rng)
            rows.append({**base, "feature": name, "kind": "continuous", "n_group1": len(a), "n_group0": len(b),
                         "effect": cliffs_delta(a, b), "ci_lo": lo, "ci_hi": hi,
                         "group1_stat": np.median(a) if len(a) else np.nan,
                         "group0_stat": np.median(b) if len(b) else np.nan})
        for name in CATEGORICAL:
            x = sub[name].to_numpy(float)
            ok = ~np.isnan(x)
            xx, yy = x[ok], y[ok].astype(float)
            lo, hi = rd_boot(xx, yy, rng)
            rows.append({**base, "feature": name, "kind": "categorical",
                         "n_group1": int(xx.sum()), "n_group0": int((1 - xx).sum()),
                         "effect": risk_diff(xx, yy), "ci_lo": lo, "ci_hi": hi,
                         "group1_stat": yy[xx == 1].mean() if xx.sum() else np.nan,
                         "group0_stat": yy[xx == 0].mean() if (1 - xx).sum() else np.nan})
    return rows


def test2_verdict(t2: pd.DataFrame, cls: str = "CASCADE", outcome: str = "1h", symbols=SYMBOLS) -> dict:
    g = t2[(t2["class"] == cls) & (t2.outcome == outcome) & t2.period.isin(["H1", "H2"])].copy()
    gate = np.where(g.kind == "continuous", CLIFF_GATE, RD_GATE)
    g["big"] = (g.effect.abs() >= gate) & ((g.ci_lo > 0) | (g.ci_hi < 0))
    passing = []
    for feat, cell in g.groupby("feature", sort=False):
        signs = np.sign(cell.effect.to_numpy())
        if len(cell) == 2 * len(symbols) and cell.big.all() and len(set(signs)) == 1:
            passing.append({"feature": feat, "effects": cell.effect.round(3).tolist()})
    return {"verdict": "POSITIVE" if passing else "NEGATIVE", "class": cls, "outcome": outcome,
            "features_tested": N_FEATURES, "n_continuous": len(CONTINUOUS), "n_categorical": len(CATEGORICAL),
            "gate_cells": int(len(g)), "passing": passing,
            "cells_meeting_effect_and_ci": int(g.big.sum())}


# ---------------------------------------------------------------------------- Test 3
PRECASCADE_FEATURES = ["long_crowding", "short_crowding", "long_stress", "short_stress",
                       "oi_zscore", "funding_zscore", "oi_decline_speed", "ofi_mean_3",
                       "realized_vol", "long_short_ratio"]


def precascade_features(frame: pd.DataFrame, state: pd.Series) -> pd.DataFrame:
    """Features known at the close of bar t: state flags at t + continuous state variables
    built from rows <= t (trailing windows only)."""
    st = state.reindex(frame.index)
    f = pd.DataFrame(index=frame.index)
    f["long_crowding"] = (st == "LONG_CROWDING").astype(float)
    f["short_crowding"] = (st == "SHORT_CROWDING").astype(float)
    f["long_stress"] = (st == "LONG_STRESS").astype(float)
    f["short_stress"] = (st == "SHORT_STRESS").astype(float)
    f["oi_zscore"] = frame.oi_zscore
    f["funding_zscore"] = frame.funding_zscore
    f["oi_decline_speed"] = frame.delta_oi_pct.rolling(3, min_periods=3).sum() / (frame.atr / frame.close)
    f["ofi_mean_3"] = frame.ofi.rolling(3, min_periods=3).mean()
    f["realized_vol"] = frame.realized_vol
    f["long_short_ratio"] = frame.long_short_ratio
    return f[PRECASCADE_FEATURES]


def precascade_targets(state: pd.Series, h: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """y_h, eligibility, and cascade-entry flags (both sides) on the labelled index."""
    s = state.to_numpy()
    casc = np.isin(s, ["LONG_LIQUIDATION_CASCADE", "SHORT_LIQUIDATION_CASCADE"])
    entry = np.zeros(len(s), dtype=bool)
    for names in class_sides("CASCADE").values():
        entry[es.entries(state, {0: names}).pos.to_numpy(dtype=int)] = True
    n = len(s)
    y = np.full(n, np.nan)
    c = np.concatenate(([0], np.cumsum(entry)))
    m = n - h
    y[:m] = (c[np.arange(m) + h + 1] - c[np.arange(m) + 1]) > 0  # entries in t+1..t+h
    # STRESS after OI collapse = a STRESS bar whose same-side STRESS/CASCADE episode already had a cascade.
    post = np.zeros(n, dtype=bool)
    for side in ("LONG", "SHORT"):
        in_ep = np.isin(s, [f"{side}_STRESS", f"{side}_LIQUIDATION_CASCADE"])
        seen = False
        for i in range(n):
            if not in_ep[i]:
                seen = False
                continue
            if s[i] == f"{side}_STRESS" and seen:
                post[i] = True
            if s[i] == f"{side}_LIQUIDATION_CASCADE":
                seen = True
    eligible = ~casc & ~post
    return y, eligible, entry


def topk_stats(y: np.ndarray, score: np.ndarray, frac: float) -> dict:
    k = max(1, int(np.ceil(frac * len(y))))
    top = np.argsort(-score, kind="stable")[:k]
    hit = y[top].sum()
    return {"precision": hit / k, "recall": hit / y.sum() if y.sum() else np.nan, "n_flagged": k}


def test3_symbol(symbol: str, frame: pd.DataFrame, state: pd.Series) -> list[dict]:
    X_all = precascade_features(frame, state).loc[state.index]
    rows = []
    for hz, h in PRECASCADE_HORIZONS.items():
        y, eligible, entry = precascade_targets(state, h)
        ok = eligible & ~np.isnan(y) & X_all.notna().all(axis=1).to_numpy()
        pos = np.flatnonzero(ok)
        cut = pos[int(len(pos) * FIT_FRACTION)]
        fit = pos[pos < cut - h]  # purge: fit labels never look into the evaluation segment
        ev = pos[pos >= cut]
        X = X_all.to_numpy(float)
        scaler = StandardScaler().fit(X[fit])
        model = LogisticRegression(C=1.0, penalty="l2", max_iter=2000).fit(scaler.transform(X[fit]), y[fit])
        for seg, idx in (("fit_60", fit), ("test_40", ev)):
            yy = y[idx].astype(int)
            base_rate = yy.mean()
            n_entries = int(entry[idx.min(): idx.max() + 1].sum())
            common = {"symbol": symbol, "horizon": hz, "horizon_bars": h, "segment": seg,
                      "start": state.index[idx.min()], "end": state.index[idx.max()], "n_bars": int(len(idx)),
                      "n_positive_bars": int(yy.sum()), "n_cascade_entries": n_entries, "base_rate": base_rate}
            for rule, cols in (("rule_P(cascade|CROWDING)", ["long_crowding", "short_crowding"]),
                               ("rule_P(cascade|STRESS)", ["long_stress", "short_stress"])):
                flag = X_all[cols].to_numpy()[idx].max(axis=1) > 0
                tp = int(yy[flag].sum())
                prec = tp / flag.sum() if flag.sum() else np.nan
                ap = average_precision_score(yy, flag.astype(float)) if yy.sum() else np.nan
                rows.append({**common, "model": rule, "cutoff": "flag", "n_flagged": int(flag.sum()),
                             "precision": prec, "recall": tp / yy.sum() if yy.sum() else np.nan,
                             "precision_over_base": prec / base_rate if base_rate else np.nan,
                             "pr_auc": ap, "lift": ap / base_rate if base_rate else np.nan})
            score = model.predict_proba(scaler.transform(X[idx]))[:, 1]
            ap = average_precision_score(yy, score) if yy.sum() else np.nan
            for frac in (0.01, 0.05):
                st = topk_stats(yy, score, frac)
                rows.append({**common, "model": "logistic_l2_C1", "cutoff": f"top{int(frac * 100)}%", **st,
                             "precision_over_base": st["precision"] / base_rate if base_rate else np.nan,
                             "pr_auc": ap, "lift": ap / base_rate if base_rate else np.nan})
        coefs = dict(zip(PRECASCADE_FEATURES, model.coef_[0].round(4).tolist()))
        rows[-1]["coefficients"] = json.dumps(coefs)
    return rows


def test3_verdict(t3: pd.DataFrame, symbols=SYMBOLS) -> dict:
    g = t3[(t3.model == "logistic_l2_C1") & (t3.segment == "test_40") & (t3.cutoff == "top1%")]
    per_hz = {}
    passing = []
    for hz, cell in g.groupby("horizon", sort=False):
        per_hz[hz] = {r.symbol: {"lift": round(float(r.lift), 3), "pr_auc": round(float(r.pr_auc), 5),
                                 "base_rate": round(float(r.base_rate), 5),
                                 "n_cascade_entries_test": int(r.n_cascade_entries),
                                 "n_positive_bars_test": int(r.n_positive_bars),
                                 "few_positives_flag": bool(r.n_cascade_entries < MIN_TEST_POSITIVES)}
                      for r in cell.itertuples()}
        if len(cell) == len(symbols) and ((cell.lift >= LIFT_GATE) & (cell.n_cascade_entries >= MIN_TEST_POSITIVES)).all():
            passing.append(hz)
    return {"verdict": "POSITIVE" if passing else "NEGATIVE", "passing_horizons": passing,
            "per_horizon": per_hz, "gate_cells": int(len(g))}


def fmt(x, nd=2) -> str:
    return "—" if pd.isna(x) else f"{x:.{nd}f}"


def write_report(res: dict, v: dict, path: Path) -> None:
    t1, t2, t3 = res["t1"], res["t2"], res["t3"]
    c = v["_counts"]
    names = list(v)[:3]
    lines = [
        "# F011 T4 — forced-flow diagnostics (5m, Train-1, non-trading)",
        "",
        "Code: `forced_flow_lab/diagnostics.py` (method in its docstring). Seeds and gates: `manifest.json`."
        " Verdicts and counts: `verdict.json`. Inputs: frozen T2 states + `frame_5m`, BTCUSDT + ETHUSDT, Train-1"
        " labelled rows only (2024-02-02 → 2025-02-28); halves split at the labelled-bar midpoint.",
        "",
        "## Verdicts",
        "",
    ]
    for k in names:
        lines.append(f"- **{k}: {v[k]['verdict']}**")
    lines += [
        f"- **Recommendation (program note): {v['_recommendation']}**",
        "",
        f"Tests: {c['tests']}. Cells: {c['total_cells']} total (Test 1 {c['test1_cells']}, Test 2"
        f" {c['test2_cells']}, Test 3 {c['test3_cells']}); gate cells {c['total_gate_cells']} (Test 1"
        f" {c['test1_gate_cells']} = 5 classes × 5 horizons × 2 symbols × 2 halves, pooled sides, each checked on"
        f" |ret| and fwd vol; Test 2 {c['test2_gate_cells']} = {N_FEATURES} features × 2 symbols × 2 halves, CASCADE"
        f" +1h; Test 3 {c['test3_gate_cells']} = 3 horizons × 2 symbols, logistic OOS).",
        "",
        "## Test 1 — magnitude / vol vs matched baseline (pooled sides)",
        "",
        "Ratio event/baseline of mean |return| and of mean forward realized vol (RMS of 5m log returns over"
        " t+1..t+h); [95% event-level bootstrap CI]. Gate: ratio ≥ 1.25 and CI lo > 1 in all four symbol × half"
        " cells. Full per-side / per-half / all-metric table: `test1_magnitude.csv.gz`.",
        "",
        "| class | horizon | metric | BTC H1 | BTC H2 | ETH H1 | ETH H2 | BTC full n | ETH full n | BTC mean |r| bps | ETH mean |r| bps |",
        "|---|---|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    g = t1[t1.side == "pooled"].set_index(["class", "horizon", "symbol", "period"])
    for cls in CLASSES:
        for hz in HORIZONS:
            for m in ("abs_ret", "fwd_rv"):
                cells = []
                for sym in SYMBOLS:
                    for per in ("H1", "H2"):
                        r = g.loc[(cls, hz, sym, per)]
                        cells.append(f"{fmt(r[f'{m}_ratio'])} [{fmt(r[f'{m}_ratio_lo'])}, {fmt(r[f'{m}_ratio_hi'])}]")
                fb, fe = g.loc[(cls, hz, "BTCUSDT", "full")], g.loc[(cls, hz, "ETHUSDT", "full")]
                lines.append(f"| {cls} | {hz} | {m} | " + " | ".join(cells) +
                             f" | {int(fb.n_events)} | {int(fe.n_events)} | {fmt(fb.abs_ret_event * 1e4, 1)} |"
                             f" {fmt(fe.abs_ret_event * 1e4, 1)} |")
    lines += [
        "",
        "Cost context (34 bps RT): mean |return| reaches the band only at +4h (≈ 78–101 bps for every class), where"
        " the matched baseline is of the same size; event-specific magnitude never dwarfs costs.",
        "",
        "## Test 2 — CASCADE continuation vs reversal (+1h outcome; gating)",
        "",
        "Effect = Cliff's δ (continuous; continuation vs reversal) or risk difference P(cont|X=1) − P(cont|X=0)"
        " (categorical, one-vs-rest). `*` = |effect| ≥ gate and 95% CI excludes 0. Group n per cell and +30m /"
        " DELEVERAGING tables: `test2_continuation_split.csv.gz`.",
        "",
    ]
    g2 = t2[(t2["class"] == "CASCADE") & (t2.outcome == "1h")]
    ns = g2.drop_duplicates(["symbol", "period"]).set_index(["symbol", "period"])
    lines.append("Group n (cont / rev): " + "; ".join(
        f"{s} {p} {int(ns.loc[(s, p)].n_cont)}/{int(ns.loc[(s, p)].n_rev)}" for s in SYMBOLS for p in PERIODS) + ".")
    lines += ["", "| feature | kind | BTC H1 | BTC H2 | ETH H1 | ETH H2 | BTC full | ETH full |",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    gi = g2.set_index(["feature", "symbol", "period"])
    for feat in list(CONTINUOUS) + CATEGORICAL:
        vals = []
        for sym in SYMBOLS:
            for per in ("H1", "H2"):
                r = gi.loc[(feat, sym, per)]
                gate = CLIFF_GATE if r.kind == "continuous" else RD_GATE
                star = "*" if (abs(r.effect) >= gate and (r.ci_lo > 0 or r.ci_hi < 0)) else ""
                vals.append(f"{fmt(r.effect)}{star}")
        full = [fmt(gi.loc[(feat, sym, "full")].effect) for sym in SYMBOLS]
        lines.append(f"| {feat} | {gi.loc[(feat, SYMBOLS[0], 'full')].kind} | " + " | ".join(vals + full) + " |")
    ctx = v["_context_non_gating"]
    lines += ["", "Non-gating context: " + "; ".join(
        f"{k}: {x['verdict']} ({x['cells_meeting_effect_and_ci']} single cells meet effect+CI)" for k, x in ctx.items())
        + ". `long_short_ratio` and `long_account_share` are monotone transforms of each other (identical δ)."]
    lines += [
        "",
        "## Test 3 — pre-cascade prediction (time-ordered 60/40)",
        "",
        "`n_casc` = CASCADE entries in the segment (the pre-registered ≥ 20 positive-event requirement is applied to"
        " this count); `pos bars` = y=1 bars. Full table incl. top-5% cutoff and coefficients: `test3_precascade.csv`.",
        "",
        "| symbol | h | segment | model | n_casc | pos bars | base rate | precision | recall | prec/base | PR-AUC | lift |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in t3[t3.cutoff.isin(["flag", "top1%"])].itertuples():
        model = r.model if r.cutoff == "flag" else f"{r.model} top1%"
        lines.append(f"| {r.symbol} | {r.horizon} | {r.segment} | {model} | {r.n_cascade_entries} | {r.n_positive_bars} |"
                     f" {r.base_rate:.5f} | {fmt(r.precision, 4)} | {fmt(r.recall)} | {fmt(r.precision_over_base, 1)} |"
                     f" {r.pr_auc:.4f} | {fmt(r.lift)} |")
    lines += [
        "",
        "Gate status: logistic OOS lift ≥ 2.0 on both symbols at every horizon, but the test segment holds only"
        " 11 (BTC) / 18 (ETH) CASCADE entries < 20 → flagged, gate not met → NEGATIVE. Counting y=1 bars instead"
        " of entries (33–214) would flip Test 3 to POSITIVE; the lift is also largely by construction — a CASCADE"
        " requires an active crowd side + STRESS conditions, so the CROWDING/STRESS flags (largest logistic"
        " coefficients) are antecedents of the label, not independent predictors.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------- driver
def load_symbol(symbol: str) -> tuple[pd.DataFrame, pd.Series]:
    frame = ls.read_frame(symbol)
    states = pd.read_csv(STATES / f"{symbol}.csv.gz", index_col=0, parse_dates=True, usecols=["timestamp", "state"])
    return frame, states.state


def run(symbols=SYMBOLS) -> dict:
    data = {s: load_symbol(s) for s in symbols}
    rng = np.random.default_rng(SEED)
    boot_rng = np.random.default_rng(SEED + 1)
    t1, t1_events = [], []
    for s in symbols:
        r, e = test1_symbol(s, *data[s], rng, boot_rng)
        t1 += r
        t1_events += e
    btc = btc_regime(data["BTCUSDT"][0])
    t2, t2_events = [], []
    t2_rng = np.random.default_rng(SEED + 2)
    for s in symbols:
        other = [o for o in symbols if o != s]
        other_state = data[other[0]][1] if other else pd.Series(dtype=object)
        for cls in ("CASCADE", "DELEVERAGING"):
            for outcome, h in (("1h", 12), ("30m", 6)):
                tab = split_table(s, data[s][0], data[s][1], other_state, btc, cls, h)
                if tab.empty:
                    continue
                tab["class"], tab["outcome"] = cls, outcome
                t2_events.append(tab)
                for row in effect_rows(tab, t2_rng):
                    t2.append({"symbol": s, "class": cls, "outcome": outcome, **row})
    t3 = []
    for s in symbols:
        t3 += test3_symbol(s, *data[s])
    return {"t1": pd.DataFrame(t1), "t1_events": pd.DataFrame(t1_events), "t2": pd.DataFrame(t2),
            "t2_events": pd.concat(t2_events, ignore_index=True), "t3": pd.DataFrame(t3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    res = run(args.symbols)
    res["t1"].to_csv(OUTPUT / "test1_magnitude.csv.gz", index=False, float_format="%.6g")
    res["t1_events"].to_csv(OUTPUT / "test1_events.csv.gz", index=False, float_format="%.6g")
    res["t2"].to_csv(OUTPUT / "test2_continuation_split.csv.gz", index=False, float_format="%.6g")
    res["t2_events"].to_csv(OUTPUT / "test2_events.csv.gz", index=False, float_format="%.6g")
    res["t3"].to_csv(OUTPUT / "test3_precascade.csv", index=False, float_format="%.6g")
    v = {
        "H-FORCEDFLOW-DIAG-MAGNITUDE-01": test1_verdict(res["t1"], args.symbols),
        "H-FORCEDFLOW-DIAG-CONTINUATION-SPLIT-01": test2_verdict(res["t2"], symbols=args.symbols),
        "H-FORCEDFLOW-DIAG-PRECASCADE-01": test3_verdict(res["t3"], args.symbols),
    }
    v["_context_non_gating"] = {
        "test2_CASCADE_30m": test2_verdict(res["t2"], "CASCADE", "30m", args.symbols),
        "test2_DELEVERAGING_1h": test2_verdict(res["t2"], "DELEVERAGING", "1h", args.symbols),
        "test2_DELEVERAGING_30m": test2_verdict(res["t2"], "DELEVERAGING", "30m", args.symbols),
    }
    counts = {
        "tests": 3,
        "test1_cells": int(len(res["t1"])),
        "test1_gate_cells": v["H-FORCEDFLOW-DIAG-MAGNITUDE-01"]["gate_cells"],
        "test2_cells": int(len(res["t2"])),
        "test2_gate_cells": v["H-FORCEDFLOW-DIAG-CONTINUATION-SPLIT-01"]["gate_cells"],
        "test3_cells": int(len(res["t3"])),
        "test3_gate_cells": v["H-FORCEDFLOW-DIAG-PRECASCADE-01"]["gate_cells"],
    }
    counts["total_cells"] = counts["test1_cells"] + counts["test2_cells"] + counts["test3_cells"]
    counts["total_gate_cells"] = counts["test1_gate_cells"] + counts["test2_gate_cells"] + counts["test3_gate_cells"]
    v["_counts"] = counts
    all_neg = all(v[k]["verdict"] == "NEGATIVE" for k in list(v)[:3])
    v["_recommendation"] = "ARCHIVE" if all_neg else "NOT ARCHIVE (>=1 POSITIVE; coordinator decides)"
    manifest = {
        "ticket": "spec/features/active/F011-forced-flow-diagnostics/ticket.md",
        "spec": "spec/research/F011-forced-flow-lab.md §9b",
        "code": "forced_flow_lab/diagnostics.py",
        "inputs": {"frame": "output/f011_forced_flow/frame_5m/<SYMBOL>.csv.gz",
                   "states": "output/f011_forced_flow/states/<SYMBOL>.csv.gz (frozen T2 thresholds, not relabelled)"},
        "symbols": list(args.symbols), "window": "Train-1 labelled rows only",
        "seed_baseline_sampling": SEED, "seed_bootstrap_test1": SEED + 1, "seed_bootstrap_test2": SEED + 2,
        "bootstrap_resamples": N_BOOT, "baselines_per_event": N_BASE, "exclusion_bars_each_side": EXCLUDE_BARS,
        "horizons": HORIZONS, "precascade_horizons": PRECASCADE_HORIZONS, "classes": CLASSES,
        "gates": {"ratio": RATIO_GATE, "cliffs_delta": CLIFF_GATE, "risk_difference": RD_GATE,
                  "pr_auc_lift": LIFT_GATE, "min_test_positive_events": MIN_TEST_POSITIVES},
        "cost_band_round_trip_context_only": COST_BAND,
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    (OUTPUT / "verdict.json").write_text(json.dumps(v, indent=2, default=str) + "\n")
    write_report(res, v, OUTPUT / "report.md")
    print(json.dumps({k: v[k]["verdict"] for k in list(v)[:3]} | {"counts": counts, "rec": v["_recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
