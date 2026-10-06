"""F012-C02 event-study analysis (Train-1 only). Reads cached per-event data, writes
compact tables to output/f012_c02_delisting/.

Conventions
- Price at time t = close of the last 1m bar that ENDED at or before t (bar end = open+1m),
  so no bar that is still open at t is used (causal).
- Sub-minute entries use tick trades: first trade at or after t.
- All latency entries are anchored on first_publicly_observable_ts (obs), never earlier.
- Returns are log returns. Short PnL = -(log P_exit - log P_entry). Abnormal return
  AR = R - beta * R_BTC with beta from 1h returns over [ann-21d, ann-1d] only.
- Every horizon is truncated at effective_ts - 1m (cannot hold past the delist); a horizon
  beyond that is reported as missing, not filled.
- Inference clusters on `day_batch_cluster_id` (announcements by one exchange within 2h),
  the most conservative independence unit.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from delisting_lab.market_data import EV, ROOT

OUT = Path("output/f012_c02_delisting")
MIN = pd.Timedelta(minutes=1)
HOURS = pd.Timedelta(hours=1)
ANN_HORIZONS = {"1m": MIN, "5m": 5 * MIN, "15m": 15 * MIN, "30m": 30 * MIN, "1h": HOURS,
                "4h": 4 * HOURS, "12h": 12 * HOURS, "24h": 24 * HOURS, "72h": 72 * HOURS}
LATENCIES = ["10s", "30s", "60s", "bar1m", "bar5m"]
COSTS_BP = [34, 50, 75, 100]
RNG = np.random.default_rng(20261006)


# ------------------------------------------------------------------ loading
def _ld(eid: str, name: str):
    p = EV / eid / f"{name}.pkl.gz"
    return pd.read_pickle(p) if p.exists() else None


class EventData:
    def __init__(self, ev: pd.Series, btc: pd.Series):
        self.ev = ev
        eid = ev.event_id
        self.bars = _ld(eid, "perp_1m")
        self.ticks = _ld(eid, "ticks_ann")
        self.h1 = _ld(eid, "perp_1h")
        self.oi = _ld(eid, "oi")
        self.fund = _ld(eid, "funding")
        self.spot = _ld(eid, "spot_1m")
        self.info = json.loads((EV / eid / "done.json").read_text()) if (EV / eid / "done.json").exists() else {}
        self.btc = btc
        self.close = None
        if self.bars is not None and len(self.bars):
            b = self.bars[self.bars.index < ev.effective_ts]  # nothing after settlement
            b = b[b["count"] > 0] if "count" in b else b
            self.close = pd.Series(b.close.values, index=b.index + MIN).dropna()
        self.spot_close = None
        if self.spot is not None and len(self.spot):
            s = self.spot[self.spot["count"] > 0] if "count" in self.spot else self.spot
            self.spot_close = pd.Series(s.close.values, index=s.index + MIN).dropna()

    def px(self, t: pd.Timestamp, series=None, max_stale=pd.Timedelta(hours=6)) -> float:
        s = self.close if series is None else series
        if s is None or t < s.index[0]:
            return np.nan
        i = s.index.searchsorted(t, side="right") - 1
        if i < 0 or t - s.index[i] > max_stale:
            return np.nan
        return float(s.iloc[i])

    def tick_px(self, t: pd.Timestamp) -> float:
        if self.ticks is None or not len(self.ticks):
            return np.nan
        tk = self.ticks.sort_values("ts")
        i = tk.ts.searchsorted(t, side="left")
        if i >= len(tk) or tk.ts.iloc[i] - t > pd.Timedelta(minutes=5):
            return np.nan
        return float(tk.price.iloc[i])

    def btc_px(self, t):
        i = self.btc.index.searchsorted(t, side="right") - 1
        return float(self.btc.iloc[i]) if i >= 0 else np.nan

    # beta from pre-window hourly returns only
    def beta(self) -> tuple[float, int]:
        ev = self.ev
        if self.h1 is None or len(self.h1) < 50:
            return 1.0, 0
        c = self.h1.close
        c = c[(c.index >= ev.announcement_ts - pd.Timedelta(days=21)) & (c.index < ev.announcement_ts - pd.Timedelta(days=1))]
        b = self.btc.resample("1h").last()
        j = pd.concat([np.log(c).diff(), np.log(b).diff()], axis=1, join="inner").dropna()
        j = j[(j.iloc[:, 0].abs() < 0.5)]
        if len(j) < 100:
            return 1.0, len(j)
        x, y = j.iloc[:, 1].values, j.iloc[:, 0].values
        return float(np.cov(x, y)[0, 1] / np.var(x, ddof=1)), len(j)

    def entry(self, lat: str) -> tuple[pd.Timestamp, float]:
        obs = self.ev.first_publicly_observable_ts
        if lat.endswith("s"):
            t = obs + pd.Timedelta(seconds=int(lat[:-1]))
            p = self.tick_px(t)
            if np.isnan(p):  # degrade: next 1m close
                t = obs.ceil("1min") + MIN
                p = self.px(t)
            return t, p
        step = "1min" if lat == "bar1m" else "5min"
        start = obs.ceil(step)
        t = start + pd.Timedelta(step)
        return t, self.px(t)


# ------------------------------------------------------------------ per-event metrics
def horizon_targets(ev) -> dict[str, pd.Timestamp]:
    ann, eff = ev.announcement_ts, ev.effective_ts
    return {"+1h": None, "+4h": None, "+24h": ann + 24 * HOURS, "+72h": ann + 72 * HOURS,
            "mid": ann + (eff - ann) / 2, "eff-24h": eff - 24 * HOURS, "eff-1h": eff - HOURS}


def event_metrics(d: EventData) -> dict:
    ev = d.ev
    ann, obs, eff = ev.announcement_ts, ev.first_publicly_observable_ts, ev.effective_ts
    last_ok = eff - MIN
    r = {"event_id": ev.event_id}
    if d.close is None:
        return r
    beta, nb = d.beta()
    r.update(beta=beta, beta_n=nb)
    # reference: last trade strictly before announcement
    p0 = np.nan
    if d.ticks is not None and len(d.ticks):
        pre = d.ticks[d.ticks.ts < ann]
        if len(pre):
            p0 = float(pre.sort_values("ts").price.iloc[-1])
    if np.isnan(p0):
        p0 = d.px(ann)
    b0 = d.btc_px(ann)
    r.update(p0=p0)

    def ar(t0, p_a, t1, p_b):
        if np.isnan(p_a) or np.isnan(p_b):
            return np.nan, np.nan
        raw = np.log(p_b / p_a)
        return raw, raw - beta * np.log(d.btc_px(t1) / d.btc_px(t0))

    # cumulative from announcement
    for k, h in ANN_HORIZONS.items():
        t = ann + h
        if t > last_ok:
            r[f"car_{k}"] = r[f"cr_{k}"] = np.nan
            continue
        r[f"cr_{k}"], r[f"car_{k}"] = ar(ann, p0, t, d.px(t))
    r["car_eff-1h"] = ar(ann, p0, eff - HOURS, d.px(eff - HOURS))[1]
    r["car_eff-1m"] = ar(ann, p0, last_ok, d.px(last_ok))[1]
    # first trade after announcement / observation
    if d.ticks is not None and len(d.ticks):
        post = d.ticks[d.ticks.ts >= ann].sort_values("ts")
        if len(post):
            r["first_trade_lag_s"] = (post.ts.iloc[0] - ann).total_seconds()
            r["car_firsttrade"] = ar(ann, p0, post.ts.iloc[0], float(post.price.iloc[0]))[1]
    # pre-announcement drift (leak / selection diagnostic)
    for k, h in {"pre7d": pd.Timedelta(days=7), "pre1d": pd.Timedelta(days=1), "pre1h": HOURS}.items():
        t0 = ann - h
        if d.h1 is not None and k == "pre7d":
            pa = d.px(t0, series=pd.Series(d.h1.close.values, index=d.h1.index + HOURS))
        else:
            pa = d.px(t0)
        r[f"car_{k}"] = ar(t0, pa, ann, p0)[1]
    # MFE / MAE of a short from bar5m entry to eff-1h
    te, pe = d.entry("bar5m")
    seg = d.close[(d.close.index > te) & (d.close.index <= eff - HOURS)]
    if len(seg) and not np.isnan(pe):
        r["short_mfe"] = float(np.log(pe / seg.min()))
        r["short_mae"] = float(np.log(pe / seg.max()))
    # latency ladder: entries and short PnL to targets
    tg = horizon_targets(ev)
    for lat in LATENCIES:
        te, pe = d.entry(lat)
        r[f"entry_lag_s_{lat}"] = (te - obs).total_seconds()
        r[f"car_pre_entry_{lat}"] = ar(ann, p0, te, pe)[1]
        for name, t1 in tg.items():
            if t1 is None:
                t1 = te + (HOURS if name == "+1h" else 4 * HOURS)
            if t1 > last_ok or t1 <= te:
                r[f"short_{lat}_{name}"] = r[f"shortab_{lat}_{name}"] = np.nan
                continue
            raw, abn = ar(te, pe, t1, d.px(t1))
            r[f"short_{lat}_{name}"] = -raw
            r[f"shortab_{lat}_{name}"] = -abn
    # H2 post-repricing drift windows (abnormal, long-sign)
    for name, (a, b) in {"ann+4h->eff-1h": (ann + 4 * HOURS, eff - HOURS),
                         "ann+24h->eff-1h": (ann + 24 * HOURS, eff - HOURS),
                         "eff-24h->eff-1h": (eff - 24 * HOURS, eff - HOURS),
                         "eff-1h->eff-1m": (eff - HOURS, last_ok)}.items():
        if b <= a or a <= obs:
            r[f"drift_{name}"] = np.nan
            continue
        r[f"drift_{name}"] = ar(a, d.px(a), b, d.px(b))[1]
    # funding / liquidity / OI / flow features
    if d.fund is not None and len(d.fund):
        f = d.fund.rate
        pre = f[(f.index < ann) & (f.index >= ann - pd.Timedelta(days=3))]
        post = f[(f.index > ann) & (f.index < eff)]
        r["fund_pre3d_mean"] = float(pre.mean()) if len(pre) else np.nan
        r["fund_post_mean"] = float(post.mean()) if len(post) else np.nan
    bars = d.bars[d.bars.index < eff]
    qv = bars.quote_volume
    r["qv_pre24h"] = float(qv[(qv.index >= ann - 24 * HOURS) & (qv.index < ann)].sum())
    r["qv_post24h"] = float(qv[(qv.index >= ann) & (qv.index < ann + 24 * HOURS)].sum())
    r["qv_last24h"] = float(qv[(qv.index >= eff - 24 * HOURS)].sum())
    if d.h1 is not None:
        hq = d.h1.quote_volume[(d.h1.index >= ann - pd.Timedelta(days=7)) & (d.h1.index < ann - HOURS)]
        r["qv_pre7d_daily"] = float(hq.sum() / 7) if len(hq) else np.nan
    if "taker_buy_quote" in bars:
        def imb(a, b):
            w = bars[(bars.index >= a) & (bars.index < b)]
            tot = w.quote_volume.sum()
            return float((w.taker_buy_quote.sum() - w.taker_sell_quote.sum()) / tot) if tot > 0 else np.nan
        r["flow_imb_pre24h"] = imb(ann - 24 * HOURS, ann)
        r["flow_imb_ann_1h"] = imb(ann, ann + HOURS)
        r["flow_imb_post4h_to_eff"] = imb(ann + 4 * HOURS, eff)
        r["flow_imb_last24h"] = imb(eff - 24 * HOURS, eff)
    # execution: 1m high-low range and buy-sell price gap (effective-spread proxy)
    def hl(a, b):
        w = bars[(bars.index >= a) & (bars.index < b) & (bars["count"] > 0)]
        return float(np.median(np.log(w.high / w.low))) if len(w) else np.nan
    r["hl1m_pre24h_bp"] = hl(ann - 24 * HOURS, ann) * 1e4
    r["hl1m_post1h_bp"] = hl(ann, ann + HOURS) * 1e4
    r["hl1m_last24h_bp"] = hl(eff - 24 * HOURS, eff) * 1e4
    r["ret1m_max_abs_post_bp"] = float(np.log(d.close).diff()[(d.close.index > ann)].abs().max() * 1e4)
    if d.ticks is not None and len(d.ticks):
        tk = d.ticks.copy()
        tk["m"] = tk.ts.dt.floor("1min")
        def bsgap(a, b):
            w = tk[(tk.ts >= a) & (tk.ts < b)]
            g = w.groupby(["m", "is_buy"]).price.mean().unstack()
            if g.shape[1] < 2:
                return np.nan
            g = g.dropna()
            return float(np.median(np.log(g[True] / g[False])) * 1e4) if len(g) else np.nan
        r["bs_gap_pre10m_bp"] = bsgap(ann - 10 * MIN, ann)
        r["bs_gap_post2h_bp"] = bsgap(obs, obs + 2 * HOURS)
    # OI trajectory normalised to pre-announcement level
    if d.oi is not None and len(d.oi):
        o = d.oi.oi
        base = o[(o.index >= ann - 6 * HOURS) & (o.index < ann)].mean()
        hist = o[(o.index >= ann - pd.Timedelta(days=3)) & (o.index < ann - 6 * HOURS)].mean()
        r["oi_vs_3d"] = float(base / hist) if hist and hist > 0 else np.nan
        for k, t in {"1h": ann + HOURS, "4h": ann + 4 * HOURS, "24h": ann + 24 * HOURS,
                     "eff-24h": eff - 24 * HOURS, "eff-1h": eff - HOURS}.items():
            v = o[o.index <= t]
            r[f"oi_norm_{k}"] = float(v.iloc[-1] / base) if len(v) and base and t > ann else np.nan
    # perp vs spot identification
    if d.spot_close is not None and len(d.spot_close):
        s0 = d.px(ann, series=d.spot_close)
        for k, t in {"1h": ann + HOURS, "24h": ann + 24 * HOURS, "eff-1h": eff - HOURS}.items():
            r[f"spot_car_{k}"] = ar(ann, s0, t, d.px(t, series=d.spot_close))[1]
            r[f"perp_car_{k}"] = ar(ann, p0, t, d.px(t))[1]
        a, b = ann + 24 * HOURS, eff - HOURS
        if b > a:
            r["perp_minus_spot_24h_to_eff-1h"] = (np.log(d.px(b) / d.px(a))
                                                  - np.log(d.px(b, series=d.spot_close) / d.px(a, series=d.spot_close)))
        for k, t in {"pre": ann, "24h": ann + 24 * HOURS, "eff-24h": eff - 24 * HOURS, "eff-1h": eff - HOURS}.items():
            r[f"basis_bp_{k}"] = float(np.log(d.px(t) / d.px(t, series=d.spot_close)) * 1e4)
    return r


# ------------------------------------------------------------------ placebo (time-scrambled)
def placebo_returns(d: EventData, n=30) -> pd.DataFrame:
    """Short-from-random-hour returns on the SAME symbol, pseudo-announcements in
    [ann-21d, ann-4d] (pre-event, so no delisting information), 1h data."""
    ev = d.ev
    if d.h1 is None or len(d.h1) < 200:
        return pd.DataFrame()
    c = pd.Series(d.h1.close.values, index=d.h1.index + HOURS)
    beta, _ = d.beta()
    cand = c.index[(c.index >= ev.announcement_ts - pd.Timedelta(days=21))
                   & (c.index <= ev.announcement_ts - pd.Timedelta(days=4))]
    if len(cand) < 10:
        return pd.DataFrame()
    rows = []
    for t in RNG.choice(cand, size=min(n, len(cand)), replace=False):
        t = pd.Timestamp(t)
        row = {"event_id": ev.event_id}
        for k, h in {"+24h": 24, "+72h": 72}.items():
            t1 = t + pd.Timedelta(hours=h)
            if t1 >= ev.announcement_ts:
                row[k] = np.nan
                continue
            raw = np.log(d.px(t1, series=c) / d.px(t, series=c))
            row[k] = -(raw - beta * np.log(d.btc_px(t1) / d.btc_px(t)))
        rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ matched controls
def matched_control_returns(d: EventData, ctrl: dict[str, pd.DataFrame], k=5) -> dict:
    """Same-timestamp short returns on the k pool perps with closest pre-event 7d volume."""
    ev = d.ev
    ann = ev.announcement_ts
    lo, hi = ann - pd.Timedelta(days=7), ann - HOURS
    target = np.nan
    if d.h1 is not None:
        target = d.h1.quote_volume[(d.h1.index >= lo) & (d.h1.index < hi)].sum()
    vols = {}
    for s, df in ctrl.items():
        w = df.quote_volume[(df.index >= lo) & (df.index < hi)]
        if len(w) > 5000:
            vols[s] = float(w.sum())
    if not vols or not np.isfinite(target) or target <= 0:
        return {}
    pick = sorted(vols, key=lambda s: abs(np.log(vols[s] / target)))[:k]
    out = {"ctrl_symbols": ",".join(pick)}
    tg = horizon_targets(ev)
    for lat in ("60s", "bar5m"):
        te, _ = d.entry(lat)
        for name, t1 in tg.items():
            if t1 is None:
                t1 = te + (HOURS if name == "+1h" else 4 * HOURS)
            if t1 > ev.effective_ts - MIN or t1 <= te:
                continue
            vals = []
            for s in pick:
                c = ctrl[s].close
                c = pd.Series(c.values, index=c.index + MIN)
                i0, i1 = c.index.searchsorted(te, "right") - 1, c.index.searchsorted(t1, "right") - 1
                if i0 >= 0 and i1 >= 0:
                    vals.append(-np.log(c.iloc[i1] / c.iloc[i0]))
            if vals:
                out[f"ctrl_short_{lat}_{name}"] = float(np.mean(vals))
    for name, (a, b) in {"ann+24h->eff-1h": (ann + 24 * HOURS, ev.effective_ts - HOURS),
                         "eff-24h->eff-1h": (ev.effective_ts - 24 * HOURS, ev.effective_ts - HOURS)}.items():
        if b <= a:
            continue
        vals = []
        for s in pick:
            c = pd.Series(ctrl[s].close.values, index=ctrl[s].index + MIN)
            i0, i1 = c.index.searchsorted(a, "right") - 1, c.index.searchsorted(b, "right") - 1
            if i0 >= 0 and i1 >= 0:
                vals.append(np.log(c.iloc[i1] / c.iloc[i0]))
        if vals:
            out[f"ctrl_drift_{name}"] = float(np.mean(vals))
    return out


# ------------------------------------------------------------------ inference helpers
def cluster_boot(x: pd.Series, cl: pd.Series, n=5000) -> tuple[float, float, float]:
    """Mean, 95% CI, one-sided p(mean<=0) by cluster bootstrap (equal-weight events)."""
    m = x.notna()
    x, cl = x[m].values, cl[m].values
    if len(x) < 3:
        return np.nan, np.nan, np.nan
    u = np.unique(cl)
    idx = {c: np.where(cl == c)[0] for c in u}
    means = np.empty(n)
    for i in range(n):
        pick = RNG.choice(u, size=len(u), replace=True)
        ii = np.concatenate([idx[c] for c in pick])
        means[i] = x[ii].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    # p-value for H0 mean<=0 via recentred bootstrap
    p = float(np.mean(means - x.mean() >= x.mean()))
    return float(lo), float(hi), p


def summarise(x: pd.Series, cl: pd.Series) -> dict:
    v = x.dropna()
    if len(v) == 0:
        return {"n": 0}
    lo, hi, p = cluster_boot(x, cl)
    return {"n": len(v), "n_clusters": cl[x.notna()].nunique(), "mean_bp": v.mean() * 1e4,
            "median_bp": v.median() * 1e4, "trim10_bp": stats.trim_mean(v, 0.1) * 1e4,
            "win_rate": float((v > 0).mean()), "ci_lo_bp": lo * 1e4, "ci_hi_bp": hi * 1e4,
            "p_one_sided_mean_gt0": p}
