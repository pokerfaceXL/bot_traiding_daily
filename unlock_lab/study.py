"""Gates 0–3, 6–8 tables (prereg §6–§9). Gate 0b failed → everything below is UB (hindsight upper bound)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from unlock_lab.fetch import ROOT
from unlock_lab.prices import _series, btc
from unlock_lab.fetch import KL

OUT = Path("output/f012_c03_unlock")
LARGE = 0.01
LOW_ABS = 1.0
K = range(-31, 31)
WIN = {"PRE": (-31, -1), "EARLY_PRE": (-31, -15), "LATE_PRE": (-15, -1), "AT": (-1, 1), "POST": (1, 30)}
FAM = {"A_calendar_-31_-1": (-31, -1), "B_into_cliff_-2_+1": (-2, 1), "C_post_+1_+14": (1, 14)}
COSTS = {"owner_9.9": 9.9, "stress_34": 34, "stress_50": 50, "stress_75": 75, "stress_100": 100}
RNG = np.random.default_rng(20261006)


def panel(u: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    tag = {"binance_spot": "spot", "binance_um": "um", "bybit_linear": "bybitlinear"}
    px, qv = {}, {}
    for r in u.dropna(subset=["venue"]).itertuples():
        s = _series(pd.read_csv(KL / f"{tag[r.venue]}_{r.symbol}USDT.csv.gz"))
        px[r.slug], qv[r.slug] = np.log(s.close), s.qv
    b = btc()
    px["__BTC__"] = np.log(b.close)
    return pd.DataFrame(px), pd.DataFrame(qv)


def cluster_ci(x: pd.Series, cl: pd.Series, n=5000) -> tuple[float, float, float, int, int]:
    x, cl = x.dropna(), cl[x.dropna().index]
    if len(x) < 3:
        return (x.mean() if len(x) else np.nan, np.nan, np.nan, len(x), cl.nunique())
    g = x.groupby(cl).agg(["sum", "count"])
    s, c = g["sum"].values, g["count"].values
    idx = RNG.integers(0, len(g), (n, len(g)))
    bs = s[idx].sum(1) / c[idx].sum(1)
    return x.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(x), len(g)


def cluster_slope(y: pd.Series, x: pd.Series, cl: pd.Series, n=2000) -> tuple[float, float, float]:
    d = pd.DataFrame({"y": y, "x": x, "c": cl}).dropna()
    b = np.polyfit(d.x, d.y, 1)[0]
    groups = [g for _, g in d.groupby("c")]
    bs = []
    for _ in range(n):
        s = pd.concat([groups[i] for i in RNG.integers(0, len(groups), len(groups))])
        if s.x.nunique() > 1:
            bs.append(np.polyfit(s.x, s.y, 1)[0])
    return b, np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def build_frame() -> tuple[pd.DataFrame, dict]:
    ev = pd.read_csv(ROOT / "events_all.csv.gz", parse_dates=["day", "ts"])
    u = pd.read_csv(ROOT / "universe.csv", parse_dates=["um_first", "bybit_first"])
    px, qv = panel(u)
    days = px.index
    att = {"cliff_token_days": len(ev), "tokens": ev.slug.nunique()}
    ev = ev.merge(u[["slug", "symbol", "venue", "um_first", "bybit_first", "calibrated_note"]], on="slug", how="left")
    att["mapped_symbol"] = int(ev.symbol.notna().sum())
    att["priced_any"] = int(ev.venue.notna().sum())
    ev = ev[(ev.circ_m1 > 0) & (ev.pct_circ > 0)].copy()
    att["valid_pct_circ_and_any"] = len(ev)
    # cliffs for control exclusion: any token-day with pct_circ >= 0.1%
    big = ev[ev.pct_circ >= 0.001].groupby("slug").day.apply(list).to_dict()
    pos = {d: i for i, d in enumerate(days)}
    rows = []
    for r in ev.itertuples():
        e = dict(event_id=r.event_id, slug=r.slug, day=r.day, pct_circ=r.pct_circ, rtype=r.rtype,
                 high_sell=r.high_sell, first=r.first, mixed=r.mixed, venue=r.venue, calibrated_note=r.calibrated_note)
        e["perp_bybit"] = bool(pd.notna(r.bybit_first) and r.bybit_first < r.day - pd.Timedelta(days=1))
        e["perp_um"] = bool(pd.notna(r.um_first) and r.um_first < r.day - pd.Timedelta(days=1))
        e["short_avail"] = e["perp_bybit"] or e["perp_um"]
        if r.venue is None or not isinstance(r.venue, str) or r.day not in pos:
            rows.append(e); continue
        i0 = pos[r.day]
        p, b = px[r.slug], px["__BTC__"]
        def at(k, s=p):
            j = i0 + k
            return s.iloc[j] if 0 <= j < len(days) else np.nan
        base, bb = at(-31), at(-31, b)
        for k in K:
            e[f"raw_{k}"] = at(k) - base
            e[f"ar_{k}"] = (at(k) - base) - (at(k, b) - bb)
        # beta on daily log returns −120..−31
        lo, hi = max(0, i0 - 120), i0 - 31
        if hi - lo > 40:
            rt, rb = p.iloc[lo:hi].diff(), b.iloc[lo:hi].diff()
            ok = rt.notna() & rb.notna()
            e["beta"] = np.polyfit(rb[ok], rt[ok], 1)[0] if ok.sum() > 30 else np.nan
        q = qv[r.slug].iloc[max(0, i0 - 37):max(0, i0 - 7)]
        e["adv_usd"] = q.mean() if q.notna().sum() >= 15 else np.nan
        e["usd_value"] = r.tokens * np.exp(at(-8))
        e["usd_adv"] = e["usd_value"] / e["adv_usd"] if e["adv_usd"] and e["adv_usd"] > 0 else np.nan
        # matched controls: nearest log 30d ADV at −31, no >=0.1% cliff within ±45d
        if i0 - 61 >= 0:
            adv31 = qv.iloc[i0 - 61:i0 - 31].mean()
            cand = [s for s in px.columns if s not in ("__BTC__", r.slug) and pd.notna(adv31.get(s)) and adv31.get(s) > 0
                    and not any(abs((d - r.day).days) <= 45 for d in big.get(s, []))
                    and pd.notna(at(-31, px[s])) and pd.notna(at(30, px[s]))]
            if cand and pd.notna(e["adv_usd"]):
                ref = np.log(qv[r.slug].iloc[i0 - 61:i0 - 31].mean())
                cs = sorted(cand, key=lambda s: abs(np.log(adv31[s]) - ref))[:5]
                e["n_ctrl"] = len(cs)
                for k in K:
                    c = np.nanmean([(at(k, px[s]) - at(-31, px[s])) - (at(k, b) - bb) for s in cs])
                    e[f"ctl_{k}"] = c
                    e[f"arc_{k}"] = e[f"ar_{k}"] - c
        rows.append(e)
    f = pd.DataFrame(rows)
    f["LARGE"] = f.pct_circ >= LARGE
    f["low_abs"] = f.usd_adv >= LOW_ABS
    f["cell"] = f.LARGE & f.low_abs & f.high_sell
    for w, (a, b_) in WIN.items():
        for pre in ("ar", "arc", "raw"):
            if f"{pre}_{a}" in f and f"{pre}_{b_}" in f:
                f[f"{pre}_{w}"] = (f[f"{pre}_{b_}"] - f[f"{pre}_{a}"]) * 1e4  # bp
    if "beta" in f:
        for w, (a, b_) in WIN.items():
            f[f"arb_{w}"] = ((f[f"raw_{b_}"] - f[f"raw_{a}"]) - f.beta.fillna(1) *
                             ((f[f"raw_{b_}"] - f[f"raw_{a}"]) - (f[f"ar_{b_}"] - f[f"ar_{a}"]))) * 1e4
    att["priced_full_window"] = int(f["ar_30"].notna().sum()) if "ar_30" in f else 0
    att["with_controls"] = int(f["arc_30"].notna().sum()) if "arc_30" in f else 0
    return f, att


def summarise(f: pd.DataFrame) -> dict[str, pd.DataFrame]:
    s = f[f["ar_30"].notna() & f["ar_-31"].notna()].copy()
    t = {}
    groups = {"ALL": s, "LARGE": s[s.LARGE], "SMALL": s[~s.LARGE], "HIGH_SELL": s[s.high_sell],
              "LARGE_HIGH_SELL": s[s.LARGE & s.high_sell], "CELL_LARGE_LOWABS_HIGHSELL": s[s.cell],
              "LARGE_not_cell": s[s.LARGE & ~s.cell], "LARGE_first": s[s.LARGE & s["first"]],
              **{f"rtype_{k}": g for k, g in s.groupby("rtype")}}
    rows = []
    for g, d in groups.items():
        for w in WIN:
            for m in ("ar", "arc", "arb", "raw"):
                c = f"{m}_{w}"
                if c in d and d[c].notna().sum():
                    mu, lo, hi, n, nt = cluster_ci(d[c], d.slug)
                    rows.append(dict(group=g, window=w, measure={"ar": "vs_BTC", "arc": "vs_controls",
                                     "arb": "vs_BTC_beta", "raw": "raw"}[m], mean_bp=mu, ci_lo=lo, ci_hi=hi,
                                     n_events=n, n_tokens=nt))
    t["gate3_windows"] = pd.DataFrame(rows)
    # CAR path
    path = []
    for g in ("ALL", "LARGE", "SMALL", "CELL_LARGE_LOWABS_HIGHSELL"):
        d = groups[g]
        for k in K:
            for m in ("ar", "ctl", "arc"):
                c = f"{m}_{k}"
                if c in d:
                    w = d.groupby("slug")[c].mean()  # token-equal weight
                    path.append(dict(group=g, k=k, measure=m, mean_bp_evw=d[c].mean() * 1e4, mean_bp_tokw=w.mean() * 1e4))
    t["gate3_car_path"] = pd.DataFrame(path)
    # Gate 6 continuous + LARGE-SMALL difference
    rows = []
    for w in WIN:
        c = f"arc_{w}"
        d = s[[c, "pct_circ", "slug", "LARGE"]].dropna()
        b, lo, hi = cluster_slope(d[c], np.log10(d.pct_circ), d.slug)
        rows.append(dict(window=w, test="slope_bp_per_log10_pct_circ", est=b, ci_lo=lo, ci_hi=hi, n=len(d), tokens=d.slug.nunique()))
        b, lo, hi = cluster_slope(d[c], d.LARGE.astype(float), d.slug)
        rows.append(dict(window=w, test="LARGE_minus_SMALL_bp", est=b, ci_lo=lo, ci_hi=hi, n=len(d), tokens=d.slug.nunique()))
        dd = d[d.LARGE]
        sub = s.loc[dd.index]
        cell = sub.cell.astype(float)
        if cell.nunique() > 1:
            b, lo, hi = cluster_slope(dd[c], cell, dd.slug)
            rows.append(dict(window=w, test="CELL_minus_otherLARGE_bp", est=b, ci_lo=lo, ci_hi=hi, n=len(dd), tokens=dd.slug.nunique()))
        cs = d[s.loc[d.index, "cell"] | ~d.LARGE]  # BUY rule (prereg §3): CELL vs SMALL
        b, lo, hi = cluster_slope(cs[c], s.loc[cs.index, "cell"].astype(float), cs.slug)
        rows.append(dict(window=w, test="CELL_minus_SMALL_bp", est=b, ci_lo=lo, ci_hi=hi, n=len(cs), tokens=cs.slug.nunique()))
    t["gate6_7_tests"] = pd.DataFrame(rows)
    # Gate 8 families: short-only raw and BTC-hedged, net of costs (gross bp = −return)
    rows = []
    for fam, (a, b_) in FAM.items():
        for g in ("ALL", "LARGE", "CELL_LARGE_LOWABS_HIGHSELL", "LARGE_HIGH_SELL"):
            d = groups[g]
            d = d[d.short_avail]
            for m, legs in (("raw", 1), ("ar", 2), ("arc", 2)):
                x = -(d[f"{m}_{b_}"] - d[f"{m}_{a}"]) * 1e4
                for cn, cbp in COSTS.items():
                    mu, lo, hi, n, nt = cluster_ci(x - cbp * legs, d.slug)
                    rows.append(dict(family=fam, group=g, leg={"raw": "short_only", "ar": "short_vs_BTC_hedge", "arc": "excess_vs_matched_controls"}[m],
                                     cost=cn, net_mean_bp=mu, ci_lo=lo, ci_hi=hi, n_events=n, n_tokens=nt))
    t["gate8_families"] = pd.DataFrame(rows)
    return t


def distributions(f: pd.DataFrame) -> pd.DataFrame:
    q = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    rows = []
    for col in ("pct_circ", "usd_value", "usd_adv"):
        for g, d in (("ALL", f), *[(k, x) for k, x in f.groupby("rtype")]):
            v = d[col].dropna()
            if len(v):
                rows.append(dict(metric=col, group=g, n=len(v), tokens=d.loc[v.index, "slug"].nunique(),
                                 **{f"q{int(p*100)}": v.quantile(p) for p in q}, share_ge_1pct=(v >= 0.01).mean() if col == "pct_circ" else np.nan,
                                 share_ge_1=(v >= 1).mean() if col == "usd_adv" else np.nan))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    f, att = build_frame()
    keep = [c for c in f.columns if not c.split("_")[-1].lstrip("-").isdigit()]
    f[keep].to_csv(OUT / "event_frame.csv", index=False)
    distributions(f).to_csv(OUT / "gate1_distributions.csv", index=False)
    for k, v in summarise(f).items():
        v.to_csv(OUT / f"{k}.csv", index=False)
    (OUT / "attrition.json").write_text(json.dumps(att, indent=1, default=str))
    print(json.dumps(att, indent=1))
