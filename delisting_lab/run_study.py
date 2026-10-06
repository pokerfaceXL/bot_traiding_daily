"""Run the full F012-C02 study from cached data and write output/f012_c02_delisting/*."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from scipy import stats

from delisting_lab import analysis as A
from delisting_lab.catalog import build_catalog
from delisting_lab.controls import CTRL, pool
from delisting_lab.market_data import EV, btc_1m

OUT = A.OUT
PRIMARY_LAT = "bar5m"
PRIMARY_TARGETS = ["+24h", "+72h", "mid", "eff-1h"]  # pre-registered family (F012 research)


def spot_only_comparators(cat: pd.DataFrame) -> pd.DataFrame:
    """Spot-delisted tokens whose same-venue perp kept trading (information-only comparator)."""
    s = cat[cat.in_train1 & (cat.contract_type == "spot") & (cat.same_venue_perp_live_at_announcement == True)]  # noqa: E712
    rows = []
    for _, r in s.iterrows():
        x = r.copy()
        x["symbol"] = r.base + "USDT"
        x["contract_type"] = "perp_continues_spot_delisted"
        x["event_id"] = r.event_id.replace("/", "") + "-SPOTONLY"
        rows.append(x)
    return pd.DataFrame(rows)


def write_catalog(cat: pd.DataFrame, art: pd.DataFrame, perps: pd.DataFrame, info: pd.DataFrame):
    t1 = cat[cat.in_train1].copy()
    keep = ["event_id", "announcement_cluster_id", "day_batch_cluster_id", "exchange", "symbol", "base",
            "contract_type", "category", "announcement_ts", "first_publicly_observable_ts", "observability_lag_s",
            "effective_ts", "effective_ts_announced", "effective_revised", "effective_ts_instrument",
            "eff_vs_instrument_min", "notice_duration_h", "source_url", "source_id", "title", "ts_flag",
            "bybit_dateTimestamp", "bybit_publishTime", "spot_also_delisted_same_article",
            "same_venue_perp_live_at_announcement", "perp_explicitly_not_affected",
            "prior_other_venue_ann_ts", "follower_event", "migration_flag", "migration_note", "index_contract"]
    t1 = t1[[c for c in keep if c in t1]]
    t1 = t1.merge(info, on="event_id", how="left")
    t1.to_csv(OUT / "event_catalog.csv", index=False)
    a = art[(art.announcement_ts >= A.pd.Timestamp("2024-03-01", tz="UTC").value // 10**6)
            & (art.announcement_ts < A.pd.Timestamp("2025-03-01", tz="UTC").value // 10**6)].copy()
    a["announcement_ts"] = pd.to_datetime(a.announcement_ts, unit="ms", utc=True)
    a.sort_values("announcement_ts").to_csv(OUT / "article_catalog.csv", index=False)
    return t1, a


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cat, art = build_catalog()
    perps = cat[cat.in_train1 & (cat.contract_type == "linear_perp")].copy()
    comps = spot_only_comparators(cat)
    btc = btc_1m().close
    infos = []
    for eid in list(perps.event_id) + list(comps.event_id):
        p = EV / eid / "done.json"
        infos.append(json.loads(p.read_text()) if p.exists() else {"event_id": eid, "error": "not_fetched"})
    info = pd.DataFrame(infos)
    t1, arts = write_catalog(cat, art, perps, info)

    ctrl = {s: pd.read_pickle(CTRL / f"{s}.pkl.gz") for s in pool()}
    rows, plac, ctl = [], [], []
    for _, ev in pd.concat([perps, comps]).iterrows():
        if not (EV / ev.event_id / "done.json").exists():
            rows.append({"event_id": ev.event_id})
            continue
        d = A.EventData(ev, btc)
        m = A.event_metrics(d)
        rows.append(m)
        if ev.contract_type == "linear_perp" and d.close is not None:
            pl = A.placebo_returns(d)
            if len(pl):
                plac.append(pl)
            c = A.matched_control_returns(d, ctrl)
            c["event_id"] = ev.event_id
            ctl.append(c)
    met = pd.DataFrame(rows)
    meta_cols = ["event_id", "exchange", "symbol", "base", "contract_type", "announcement_cluster_id",
                 "day_batch_cluster_id", "announcement_ts", "first_publicly_observable_ts", "effective_ts",
                 "notice_duration_h", "follower_event", "migration_flag", "index_contract", "spot_also_delisted_same_article",
                 "observability_lag_s"]
    allev = pd.concat([perps, comps])
    met = allev[meta_cols].merge(met, on="event_id", how="left")
    ctl = pd.DataFrame(ctl)
    met = met.merge(ctl, on="event_id", how="left") if len(ctl) else met
    met.to_csv(OUT / "event_metrics.csv", index=False)
    plac = pd.concat(plac) if plac else pd.DataFrame()
    plac.to_csv(OUT / "placebo_time_scrambled.csv", index=False)

    ev_all = met[met.contract_type == "linear_perp"].copy()
    ev_all["usable"] = ev_all.p0.notna() & ev_all[f"short_{PRIMARY_LAT}_eff-1h"].notna()
    usable = ev_all[ev_all.usable]
    write_missingness(t1, ev_all, info)
    res = {}
    res["counts"] = {
        "perp_events_train1": int(len(ev_all)),
        "perp_article_clusters": int(ev_all.announcement_cluster_id.nunique()),
        "perp_day_batch_clusters": int(ev_all.day_batch_cluster_id.nunique()),
        "usable_events": int(len(usable)),
        "usable_article_clusters": int(usable.announcement_cluster_id.nunique()),
        "usable_day_batch_clusters": int(usable.day_batch_cluster_id.nunique()),
        "missing_event_rate": float(1 - len(usable) / len(ev_all)),
        "spot_only_comparators": int((met.contract_type == "perp_continues_spot_delisted").sum()),
    }
    subs = {"all": usable, "ex_migration": usable[~usable.migration_flag],
            "ex_follower": usable[~usable.follower_event],
            "ex_migration_ex_follower": usable[~usable.migration_flag & ~usable.follower_event],
            "tokens_ex_migration_ex_index": usable[~usable.migration_flag & ~usable.index_contract],
            "bybit": usable[usable.exchange == "bybit"], "binance": usable[usable.exchange == "binance"]}
    cl = "day_batch_cluster_id"

    # 1) announcement response (CAR from announcement, pre-entry not tradeable)
    t = []
    for name, s in subs.items():
        for k in ["firsttrade"] + list(A.ANN_HORIZONS) + ["eff-1h", "eff-1m"]:
            c = f"car_{k}"
            if c in s:
                t.append({"subset": name, "horizon_from_ann": k, **A.summarise(s[c], s[cl])})
        for k in ("pre7d", "pre1d", "pre1h"):
            t.append({"subset": name, "horizon_from_ann": k, **A.summarise(s[f"car_{k}"], s[cl])})
    pd.DataFrame(t).to_csv(OUT / "h1_announcement_car.csv", index=False)

    # 2) latency: share of effect before entry, short PnL after entry (raw, abnormal, vs ctrl)
    t = []
    for name, s in subs.items():
        for lat in A.LATENCIES:
            base = {"subset": name, "latency": lat, "median_entry_lag_s": s[f"entry_lag_s_{lat}"].median()}
            t.append({**base, "target": "CAR_pre_entry(long)", **A.summarise(s[f"car_pre_entry_{lat}"], s[cl])})
            for tg in ["+1h", "+4h"] + PRIMARY_TARGETS + ["eff-24h"]:
                t.append({**base, "target": f"short_raw->{tg}", **A.summarise(s[f"short_{lat}_{tg}"], s[cl])})
                t.append({**base, "target": f"short_abn->{tg}", **A.summarise(s[f"shortab_{lat}_{tg}"], s[cl])})
                cc = f"ctrl_short_{lat}_{tg}"
                if cc in s:
                    t.append({**base, "target": f"short_raw_minus_ctrl->{tg}",
                              **A.summarise(s[f"short_{lat}_{tg}"] - s[cc], s[cl])})
    lat_df = pd.DataFrame(t)
    lat_df.to_csv(OUT / "h1_latency_short.csv", index=False)

    # 3) H2: post-repricing drift (long sign; negative = continued selling)
    t = []
    for name, s in subs.items():
        for w in ["ann+4h->eff-1h", "ann+24h->eff-1h", "eff-24h->eff-1h", "eff-1h->eff-1m"]:
            t.append({"subset": name, "window": w, "metric": "abn_drift", **A.summarise(s[f"drift_{w}"], s[cl])})
            cc = f"ctrl_drift_{w}"
            if cc in s:
                t.append({"subset": name, "window": w, "metric": "raw_drift_minus_ctrl",
                          **A.summarise(s[f"drift_{w}"] - s[cc], s[cl])})
    pd.DataFrame(t).to_csv(OUT / "h2_post_repricing_drift.csv", index=False)

    # 4) placebo
    if len(plac):
        pl = plac.merge(ev_all[["event_id", cl]], on="event_id")
        prow = []
        for k in ("+24h", "+72h"):
            evm = pl.groupby("event_id")[k].mean()
            prow.append({"window": k, "placebo_short_abn_mean_bp": pl[k].mean() * 1e4,
                         "placebo_short_abn_median_bp": pl[k].median() * 1e4,
                         "placebo_event_level_sd_bp": evm.std() * 1e4, "n_draws": int(pl[k].notna().sum()),
                         "event_short_abn_bar5m_mean_bp": usable[f"shortab_bar5m_{k}"].mean() * 1e4})
            ev_v = usable.set_index("event_id")[f"shortab_bar5m_{k}"]
            j = pd.concat([ev_v, evm], axis=1, join="inner").dropna()
            if len(j) > 5:
                prow[-1]["paired_event_minus_placebo_mean_bp"] = float((j.iloc[:, 0] - j.iloc[:, 1]).mean() * 1e4)
                prow[-1]["paired_wilcoxon_p"] = float(stats.wilcoxon(j.iloc[:, 0] - j.iloc[:, 1]).pvalue)
        pd.DataFrame(prow).to_csv(OUT / "controls_placebo_summary.csv", index=False)

    # 5) OI study
    o = usable[usable.oi_norm_24h.notna()].copy()
    oi_rows = [{"metric": f"oi_norm_{k}", "n": int(o[f'oi_norm_{k}'].notna().sum()),
                "median": o[f"oi_norm_{k}"].median(), "p25": o[f"oi_norm_{k}"].quantile(.25),
                "p75": o[f"oi_norm_{k}"].quantile(.75)} for k in ("1h", "4h", "24h", "eff-24h", "eff-1h")]
    if len(o) > 8:
        rho, p = stats.spearmanr(o.oi_norm_24h, o["drift_ann+24h->eff-1h"], nan_policy="omit")
        oi_rows.append({"metric": "spearman(oi_norm_24h, drift ann+24h->eff-1h)", "n": len(o), "median": rho, "p25": p})
    pd.DataFrame(oi_rows).to_csv(OUT / "oi_study.csv", index=False)

    # 6) identification: perp vs spot
    idn = usable[usable.spot_car_24h.notna()].copy()
    id_rows = []
    for grp, g in [("all_with_spot", idn), ("spot_also_delisted", idn[idn.spot_also_delisted_same_article == True]),  # noqa: E712
                   ("perp_only_delist", idn[idn.spot_also_delisted_same_article != True])]:  # noqa: E712
        for c in ["perp_car_1h", "spot_car_1h", "perp_car_24h", "spot_car_24h", "perp_car_eff-1h",
                  "spot_car_eff-1h", "perp_minus_spot_24h_to_eff-1h"]:
            id_rows.append({"group": grp, "metric": c, **A.summarise(g[c], g[cl])})
        for c in ["basis_bp_pre", "basis_bp_24h", "basis_bp_eff-24h", "basis_bp_eff-1h",
                  "flow_imb_pre24h", "flow_imb_ann_1h", "flow_imb_post4h_to_eff", "flow_imb_last24h"]:
            v = g[c].dropna()
            id_rows.append({"group": grp, "metric": c, "n": len(v), "mean_bp": v.mean(), "median_bp": v.median()})
    cmp_ = met[met.contract_type == "perp_continues_spot_delisted"]
    for c in ["car_1h", "car_24h", "car_72h", "car_eff-1h", "drift_ann+24h->eff-1h"]:
        if c in cmp_:
            v = cmp_[c].dropna()
            id_rows.append({"group": "spot_only_delist_perp_continues", "metric": c, "n": len(v),
                            "mean_bp": v.mean() * 1e4, "median_bp": v.median() * 1e4})
    pd.DataFrame(id_rows).to_csv(OUT / "identification_perp_vs_spot.csv", index=False)
    res["identification_coverage"] = {"usable_with_spot": int(len(idn)), "usable": int(len(usable)),
                                      "spot_venues": idn.event_id.map(info.set_index("event_id").spot_venue).value_counts().to_dict()}

    # 7) directional conditioning (exploratory)
    feats = ["fund_pre3d_mean", "car_pre7d", "oi_vs_3d", "notice_duration_h", "qv_pre7d_daily"]
    y = "drift_ann+24h->eff-1h"
    cr = []
    for f in feats:
        g = usable[[f, y, f"short_{PRIMARY_LAT}_eff-1h"]].dropna()
        if len(g) > 8:
            r1 = stats.spearmanr(g[f], g[y])
            r2 = stats.spearmanr(g[f], g[f"short_{PRIMARY_LAT}_eff-1h"])
            cr.append({"feature": f, "n": len(g), "rho_vs_post24h_drift": r1.statistic, "p1": r1.pvalue,
                       "rho_vs_short_bar5m_eff-1h": r2.statistic, "p2": r2.pvalue})
    for f, cond in [("funding_sign", usable.fund_pre3d_mean > 0), ("exchange_bybit", usable.exchange == "bybit"),
                    ("spot_also_delisted", usable.spot_also_delisted_same_article == True),  # noqa: E712
                    ("follower", usable.follower_event), ("migration", usable.migration_flag)]:
        for lab, s in (("true", usable[cond]), ("false", usable[~cond])):
            cr.append({"feature": f"{f}={lab}", "n": len(s),
                       "mean_post24h_drift_bp": s[y].mean() * 1e4,
                       "mean_short_bar5m_eff-1h_bp": s[f"short_{PRIMARY_LAT}_eff-1h"].mean() * 1e4})
    pd.DataFrame(cr).to_csv(OUT / "conditioning_exploratory.csv", index=False)

    # 8) costs + 9) tails on the primary registered trade family
    ct, tails = [], []
    for name, s in subs.items():
        for tg in PRIMARY_TARGETS:
            x = s[f"short_{PRIMARY_LAT}_{tg}"]
            for c in COSTS:
                row = {"subset": name, "target": tg, "cost_bp_rt": c,
                       **A.summarise(x - c / 1e4, s[cl])}
                cc = f"ctrl_short_{PRIMARY_LAT}_{tg}"
                if cc in s:
                    row["mean_minus_ctrl_net_bp"] = float(((x - s[cc]) - c / 1e4).mean() * 1e4)
                ct.append(row)
    for name, s in subs.items():
        for tg in PRIMARY_TARGETS:
            x = (s[f"short_{PRIMARY_LAT}_{tg}"] - 0.0050).dropna().sort_values(ascending=False)
            if len(x) < 6:
                continue
            tot = x.sum()
            row = {"subset": name, "target": tg, "cost_bp": 50, "n": len(x), "mean_bp": x.mean() * 1e4,
                   "median_bp": x.median() * 1e4, "trim10_bp": stats.trim_mean(x, .1) * 1e4,
                   "win_rate": (x > 0).mean(), **{f"q{int(q*100)}_bp": x.quantile(q) * 1e4 for q in (.05, .25, .5, .75, .95)},
                   "sum_bp": tot * 1e4}
            for k in (1, 3, 5):
                row[f"top{k}_share_of_sum"] = float(x.iloc[:k].sum() / tot) if tot != 0 else np.nan
                row[f"mean_ex_top{k}_bp"] = float(x.iloc[k:].mean() * 1e4)
            row["top_events"] = ";".join(s.loc[x.index[:5], "symbol"].astype(str) + "@" + s.loc[x.index[:5], "exchange"])
            tails.append(row)
    pd.DataFrame(ct).to_csv(OUT / "costs_primary.csv", index=False)
    pd.DataFrame(tails).to_csv(OUT / "tails_primary.csv", index=False)
    exe = []
    for c in ["hl1m_pre24h_bp", "hl1m_post1h_bp", "hl1m_last24h_bp", "bs_gap_pre10m_bp", "bs_gap_post2h_bp",
              "ret1m_max_abs_post_bp", "qv_pre24h", "qv_post24h", "qv_last24h", "short_mfe", "short_mae"]:
        v = usable[c].dropna()
        exe.append({"metric": c, "n": len(v), "median": v.median(), "p25": v.quantile(.25), "p75": v.quantile(.75)})
    pd.DataFrame(exe).to_csv(OUT / "execution_proxies.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps(res, indent=2, default=str))


COSTS = A.COSTS_BP


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4g}" if isinstance(v, float) else str(v) for v in r.values) + " |")
    return "\n".join(out)


def write_missingness(t1: pd.DataFrame, ev_all: pd.DataFrame, info: pd.DataFrame):
    lines = ["# F012-C02 missingness report (Train-1 2024-03-01 → 2025-03-01)", ""]
    lines.append("## Catalog rows by exchange × contract_type × category\n")
    lines.append(t1.groupby(["exchange", "contract_type", "category"]).size().rename("rows").reset_index()
                 .pipe(md))
    lines.append("\n## Perp delisting events: data availability\n")
    flags = ev_all.merge(info, on="event_id", how="left")
    cols = ["has_perp_1m", "has_ticks_ann", "has_perp_1h", "has_oi", "has_funding", "has_spot_1m"]
    tab = flags.groupby("exchange")[cols].agg(lambda s: f"{int(s.fillna(False).sum())}/{len(s)}")
    lines.append(tab.reset_index().pipe(md))
    miss = ev_all[~ev_all.usable]
    lines.append(f"\n**Usable (p0 + primary entry + eff-1h exit)**: {int(ev_all.usable.sum())}/{len(ev_all)} "
                 f"→ missing-event rate {1 - ev_all.usable.mean():.1%}.\n")
    if len(miss):
        lines.append("Excluded events (not silently dropped):\n")
        lines.append(miss[["event_id", "exchange", "symbol", "notice_duration_h"]].pipe(md))
        inc = ev_all[ev_all.usable]
        lines.append("\nIncluded vs excluded: median notice "
                     f"{inc.notice_duration_h.median():.1f}h vs {miss.notice_duration_h.median():.1f}h; "
                     f"bybit share {(inc.exchange == 'bybit').mean():.0%} vs {(miss.exchange == 'bybit').mean():.0%}.")
    lines.append("\n## Spot coverage for identification\n")
    lines.append(flags.groupby(["exchange", "spot_venue"], dropna=False).size().rename("events").reset_index()
                 .pipe(md))
    (OUT / "missingness.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
