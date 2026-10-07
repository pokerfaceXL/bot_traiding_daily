"""F013 discovery gates B–N, Q (prereg §6). Gate P lives in f013_placebo.py.

Every gate returns a GateResult: status, the per-gate table, and a short markdown body.
Statuses: PASS | FAIL (KILL or thesis mismatch) | ROUTE_CONDITIONAL | NO_PASS_ROUTE
(ROUTE gate did not pass but has no FAIL consequence by itself) | REPORTED.

Sample funnel (frozen order): Gate-A usable → primary universe (no index / migration) →
sufficient notice (eff - 1 h - entry >= 1 h) → Gate C eligible → Gate K liquidity exclusion
= scored sample. Gates B, D–J, L–N, Q are evaluated on the scored sample.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from delisting_lab import f013_core as C

K_MIN_TURNOVER = 500_000.0
K_MAX_ZERO_SHARE = 0.20
C_MIN_ELIGIBLE = 0.70
I_MIN_DAY_CLUSTERS = 25


@dataclass
class GateResult:
    gate: str
    kind: str  # KILL | ROUTE
    title: str
    status: str
    table: pd.DataFrame
    notes: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


def net(df: pd.DataFrame, cost: float, gross="gross", fund="fund", with_funding=True) -> pd.Series:
    f = df[fund].fillna(0.0) if with_funding else 0.0
    return df[gross] + f - cost


def row(label: str, v: pd.Series, clusters: pd.Series, **extra) -> dict:
    d = C.describe(v.values, clusters.values)
    return {"split": label, **extra, **d}


def fmt(df: pd.DataFrame) -> str:
    """Markdown table without the optional `tabulate` dependency."""
    def cell(x):
        if isinstance(x, (float, np.floating)):
            return "" if not np.isfinite(x) else (f"{x:.3f}" if abs(x) < 1 else f"{x:.1f}")
        return str(x).replace("|", "/")
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(cell(x) for x in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


# ------------------------------------------------------------------ funnel
def funnel(t: pd.DataFrame) -> dict[str, pd.DataFrame]:
    u = t[t.in_primary_universe]
    has = u[u.has_perp_1m.fillna(False) & u.entry_px.notna()]
    suff = u[~u.insufficient_notice.fillna(True)]
    elig = suff[suff.eligible.astype("boolean").fillna(False).astype(bool)]
    liq_ok = (elig.turnover_24h >= K_MIN_TURNOVER) & (elig.zero_vol_share_24h <= K_MAX_ZERO_SHARE)
    scored = elig[liq_ok & elig.exit_ts.notna() & elig.gross.notna()]
    return {"usable_primary": u, "with_data": has, "sufficient_notice": suff, "eligible": elig,
            "k_included": elig[liq_ok], "scored": scored}


# ------------------------------------------------------------------ gates
def gate_b(s: pd.DataFrame) -> GateResult:
    rows = []
    for k in ("10s", "30s", "60s", "1m", "5m", "15m"):
        sub = s[s[f"gross_{k}"].notna()]
        v = net(sub, C.DECISION_BP, f"gross_{k}", f"fund_{k}")
        rows.append(row(f"P+{k}", v, sub.day_batch_cluster_id, source="ticks" if k.endswith("s") else "1m bar open",
                        median_entry_lag_s=float(sub[f"entry_lag_s_{k}"].median()) if len(sub) else np.nan,
                        n_missing=int(len(s) - len(sub)), gross_mean=float(sub[f"gross_{k}"].mean())))
    tb = pd.DataFrame(rows)
    pos = dict(zip(tb.split, tb["mean"] > 0))
    if pos["P+5m"] and pos["P+15m"]:
        st = "PASS"
    elif any(pos[k] for k in ("P+10s", "P+30s", "P+60s")) and not any(pos[k] for k in ("P+1m", "P+5m", "P+15m")):
        st = "FAIL"
    else:
        st = "NO_PASS_ROUTE"
    missing = s.loc[s.gross_10s.isna(), "event_id"].tolist()
    return GateResult("B", "ROUTE", "Latency decay", st, tb,
                      [f"Events without tick support at P+10s: {len(missing)} (listed, not imputed): "
                       + ", ".join(missing[:40])])


def gate_c(f: dict) -> GateResult:
    suff = f["sufficient_notice"]
    u = f["usable_primary"]
    share = len(f["eligible"]) / len(suff) if len(suff) else 0.0
    inel = suff[~suff.eligible.astype("boolean").fillna(False).astype(bool)]
    tb = inel[["event_id", "symbol", "has_perp_1m", "trade_in_entry_minute", "restricted_before_entry",
               "restriction_times"]].copy()
    st = "PASS" if share >= C_MIN_ELIGIBLE else "FAIL"
    notes = [f"Gate-A-usable primary universe: {len(u)}; insufficient notice (eff−1h−entry<1h or no entry bar): "
             f"{len(u) - len(suff)}; eligible {len(f['eligible'])}/{len(suff)} = {share:.1%} (bar ≥ 70 %).",
             "Restriction sentences found only in Binance articles (no new positions from ≈ eff − 30 min) — all after entry."]
    return GateResult("C", "KILL", "Short eligibility", st, tb, notes, {"eligible_share": share})


def gate_d(s: pd.DataFrame, pre_k: pd.DataFrame | None = None) -> GateResult:
    rows = []
    for c in (C.OWNER_CONTEXT_BP, *C.COST_LADDER):
        rows.append(row(f"{c:g} bp RT" + (" (context only)" if c == C.OWNER_CONTEXT_BP else ""),
                        net(s, c), s.day_batch_cluster_id, cost_bp=c))
    tb = pd.DataFrame(rows)
    be = float((s.gross + s.fund.fillna(0)).mean())
    lo34 = float(tb.loc[tb.cost_bp == 34, "ci_lo"].iloc[0])
    m75 = float(tb.loc[tb.cost_bp == 75, "mean"].iloc[0])
    st = "PASS" if lo34 > 0 and m75 > 0 else "FAIL"
    return GateResult("D", "KILL", "Cost ladder", st, tb,
                      [f"Breakeven RT cost (mean gross + funding) = {be:.1f} bp.",
                       f"Decision: net@34 CI lower = {lo34:.1f} bp (needs > 0); mean net@75 = {m75:.1f} bp (needs > 0)."]
                      + _pre_k_note(pre_k),
                      {"breakeven_bp": be, "net34_ci_lo": lo34, "net75_mean": m75})


def _pre_k_note(pre_k: pd.DataFrame | None) -> list[str]:
    """Context only: the same rung on the eligible sample before the Gate K liquidity exclusion."""
    if pre_k is None or not len(pre_k):
        return []
    p = pre_k[pre_k.gross.notna()]
    d = C.describe(net(p, 34).values, p.day_batch_cluster_id.values)
    return [f"Context (not decision): eligible sample before Gate K exclusion, n = {d['n']} "
            f"({d['n_clusters']} day-batch clusters): net@34 mean {d['mean']:.1f} bp, CI [{d['ci_lo']:.1f}, "
            f"{d['ci_hi']:.1f}]."]


def gate_e(s: pd.DataFrame) -> GateResult:
    cl = s.day_batch_cluster_id
    rows = [row("gross", s.gross, cl), row("funding (short receives)", s.fund.fillna(0), cl),
            row("net@34 incl funding", net(s, 34), cl), row("net@34 excl funding", net(s, 34, with_funding=False), cl)]
    tb = pd.DataFrame(rows)
    n34 = float(net(s, 34).mean())
    ex = float(net(s, 34, with_funding=False).mean())
    contrib = float(s.fund.fillna(0).mean()) / n34 if n34 != 0 else np.inf
    st = "PASS" if ex > 0 and contrib < 0.5 else "FAIL"
    return GateResult("E", "KILL", "Funding carry", st, tb,
                      [f"Events without funding history: {int((~s.has_funding.fillna(False)).sum())} (funding = 0).",
                       f"Funding share of net@34 = {contrib:.1%} (must be < 50 %); net@34 ex funding = {ex:.1f} bp."],
                      {"funding_share": contrib, "net34_ex_funding": ex})


def gate_f(s: pd.DataFrame) -> GateResult:
    rows = []
    for h in (1, 4, 12, 24, 72):
        sub = s[s[f"gross_h{h}"].notna()]
        rows.append(row(f"entry+{h}h", net(sub, 34, f"gross_h{h}", f"fund_h{h}"), sub.day_batch_cluster_id,
                        fixed=True))
    sub = s[s.gross_heff.notna()]
    rows.append(row("eff−1h", net(sub, 34, "gross_heff", "fund_heff"), sub.day_batch_cluster_id, fixed=False))
    tb = pd.DataFrame(rows)
    k = int((tb[tb.fixed]["mean"] > 0).sum())
    st = "PASS" if k >= 3 else "FAIL"
    return GateResult("F", "ROUTE", "Fixed-horizon drift", st, tb,
                      [f"net@34 > 0 at {k}/5 fixed horizons (needs ≥ 3; FAIL ⇒ track FAIL per §10)."])


def gate_g(s: pd.DataFrame) -> GateResult:
    sub = s[s.abn_gross.notna()]
    cl = sub.day_batch_cluster_id
    tb = pd.DataFrame([row("raw net@34", net(sub, 34), cl),
                       row("abnormal net@34", net(sub, 34, "abn_gross"), cl),
                       row("BTC return over window (bp)", sub.btc_ret_bp, cl)])
    lo = float(tb.loc[1, "ci_lo"])
    st = "PASS" if lo > 0 else "FAIL"
    return GateResult("G", "KILL", "Market-adjusted", st, tb,
                      [f"β from ≥200 hourly obs for {int((sub.beta_n >= 200).sum())}/{len(sub)} events (else β = 1); "
                       f"median β {sub.beta.median():.2f}.", f"Abnormal net@34 CI lower = {lo:.1f} bp (needs > 0)."])


def gate_h(s: pd.DataFrame) -> GateResult:
    sub = s[s.spot_gross.notna()]
    cl = sub.day_batch_cluster_id
    tb = pd.DataFrame([row("perp short gross", sub.gross, cl), row("spot short gross", sub.spot_gross, cl),
                       row("perp − spot", sub.gross - sub.spot_gross, cl)])
    diff_lo, spot_m = float(tb.loc[2, "ci_lo"]), float(tb.loc[1, "mean"])
    st = "FAIL" if (diff_lo > 0 and spot_m <= 0) else ("PASS" if len(sub) >= C.N_MIN else "NO_PASS_ROUTE")
    return GateResult("H", "ROUTE", "Spot/perp co-move", st, tb,
                      [f"Spot coverage {len(sub)}/{len(s)} (venues: {sub.spot_venue.value_counts().to_dict()}).",
                       "Thesis mismatch FAIL iff perp−spot CI lower > 0 and spot mean ≤ 0."])


def gate_i(s: pd.DataFrame) -> GateResult:
    v = net(s, 34)
    tb = pd.DataFrame([
        row("day-batch cluster bootstrap", v, s.day_batch_cluster_id),
        row("token cluster bootstrap", v, s.token_cluster_id),
        row("announcement cluster bootstrap", v, s.announcement_cluster_id),
        row("event-level iid (comparison only)", v, s.event_id),
    ])
    nd = s.day_batch_cluster_id.nunique()
    ok = nd >= I_MIN_DAY_CLUSTERS and tb.loc[0, "ci_lo"] > 0 and tb.loc[1, "ci_lo"] > 0
    return GateResult("I", "KILL", "Clustering", "PASS" if ok else "FAIL", tb,
                      [f"n events {len(s)}, announcement clusters {s.announcement_cluster_id.nunique()}, "
                       f"day-batch clusters {nd} (needs ≥ 25), token clusters {s.token_cluster_id.nunique()}."])


def gate_j(s: pd.DataFrame) -> GateResult:
    ts = C.tail_stats(net(s, 34).values)
    tb = pd.DataFrame([ts])
    ok = ts["median"] > 0 and ts["winsor5_95_mean"] > 0 and ts["mean_ex_top3"] > 0
    notes = ["Pass iff median > 0, 5/95 winsorized mean > 0, mean ex-top-3 > 0 (net@34)."]
    if ts["mean_ex_top5"] <= 0:
        notes.append("WARNING: mean ex-top-5 ≤ 0.")
    return GateResult("J", "KILL", "Tails", "PASS" if ok else "FAIL", tb, notes)


def gate_k(f: dict) -> GateResult:
    e, inc, s = f["eligible"], f["k_included"], f["scored"]
    med = inc.turnover_24h.median()
    hi, lo = s[s.turnover_24h >= med], s[s.turnover_24h < med]
    tb = pd.DataFrame([row("more liquid half", net(hi, 34), hi.day_batch_cluster_id),
                       row("less liquid half", net(lo, 34), lo.day_batch_cluster_id)])
    st = "PASS" if tb.loc[0, "mean"] > 0 else "FAIL"
    exc = e[~e.event_id.isin(inc.event_id)]
    return GateResult("K", "KILL", "Liquidity", st, tb,
                      [f"Eligible {len(e)}; excluded by pre-P 24h turnover < 500k USDT or > 20 % zero-volume bars: "
                       f"{len(exc)} ({', '.join(exc.symbol)}); included {len(inc)}; median pre-P 24h turnover "
                       f"{med:,.0f} USDT."])


def _split_gate(s, col, order, gate, kind, title, pass_rule) -> GateResult:
    rows = []
    for k in order:
        sub = s[s[col] == k]
        d = row(str(k), net(sub, 34), sub.day_batch_cluster_id) if len(sub) else {"split": str(k), "n": 0}
        d["populated"] = d.get("n", 0) >= C.N_MIN
        rows.append(d)
    tb = pd.DataFrame(rows)
    st, notes = pass_rule(tb)
    return GateResult(gate, kind, title, st, tb, notes)


def gate_l(s: pd.DataFrame) -> GateResult:
    def rule(tb):
        pop = tb[tb.populated]
        k = int((pop["mean"] > 0).sum())
        if k >= 2:
            return "PASS", [f"net@34 > 0 in {k} populated bins."]
        if k == 1:
            return "ROUTE_CONDITIONAL", [f"Effect confined to bin {pop[pop['mean'] > 0].split.iloc[0]} ⇒ CONDITIONAL route."]
        return "NO_PASS_ROUTE", ["No populated bin with net@34 > 0."]
    return _split_gate(s, "notice_bin", ["(0,24h]", "(24h,72h]", "(72h,168h]", ">168h"], "L", "ROUTE",
                       "Notice length", rule)


def gate_m(s: pd.DataFrame, excluded: pd.DataFrame) -> GateResult:
    allx = pd.concat([s, excluded])

    def rule(tb):
        p = tb.set_index("split")
        prim = [k for k in ("perp_only", "spot_and_perp") if p.loc[k, "populated"]]
        posp = [k for k in prim if p.loc[k, "mean"] > 0]
        notes = [f"{k} below n_min (limitation)" for k in ("perp_only", "spot_and_perp") if k not in prim]
        exc_pos = any(p.loc[k].get("n", 0) > 0 and p.loc[k, "mean"] > 0 for k in ("migration", "index"))
        if not posp and exc_pos:
            return "FAIL", notes + ["Effect only via migration/index ⇒ FAIL."]
        if len(posp) == len(prim) and prim:
            return "PASS", notes
        if posp:
            return "ROUTE_CONDITIONAL", notes + [f"Effect only in {posp} ⇒ CONDITIONAL route."]
        return "NO_PASS_ROUTE", notes
    return _split_gate(allx, "delist_type_m", ["perp_only", "spot_and_perp", "migration", "index"], "M", "ROUTE",
                       "Delisting type", rule)


def gate_n(s: pd.DataFrame) -> GateResult:
    s = s.assign(novelty=np.where(s.follower_event, "follower", "first_venue"))

    def rule(tb):
        p = tb.set_index("split")
        f_m = p.loc["first_venue", "mean"] if p.loc["first_venue"].get("n", 0) else np.nan
        fo_m = p.loc["follower", "mean"] if p.loc["follower"].get("n", 0) else np.nan
        if np.isfinite(f_m) and f_m <= 0 and np.isfinite(fo_m) and fo_m > 0:
            return "ROUTE_CONDITIONAL", ["First-venue net@34 ≤ 0 while followers carry the effect ⇒ CONDITIONAL."]
        return "PASS", [f"first-venue mean {f_m:.1f} bp vs follower {fo_m:.1f} bp (H1 predicts first ≥ follower)."]
    return _split_gate(s, "novelty", ["first_venue", "follower"], "N", "ROUTE", "Announcement novelty", rule)


def gate_q(s: pd.DataFrame) -> GateResult:
    cl = s.day_batch_cluster_id
    tb = [row("short [P−72h, P−5m]", -s.pre_72h_5m, cl), row("short [P−24h, P−5m]", -s.pre_24h_5m, cl),
          row("short [P−1h, P)", -s.pre_1h_0, cl)]
    sub = s[s.pre_24h_5m.notna()]
    up = sub[sub.pre_24h_5m >= sub.pre_24h_5m.median()]
    dn = sub[sub.pre_24h_5m < sub.pre_24h_5m.median()]
    tb += [row("post-P net@34 | upper half pre-24h return (least decline)", net(up, 34), up.day_batch_cluster_id),
           row("post-P net@34 | lower half pre-24h return", net(dn, 34), dn.day_batch_cluster_id)]
    tb = pd.DataFrame(tb)
    m1h = float(s.pre_1h_0.mean())
    notes = [f"Mean raw [P−1h, P) return = {m1h:.1f} bp."]
    if m1h < -200:
        notes.append("LEAK FLAG: mean [P−1h, P) drop worse than −200 bp — re-check vs Gate A FAILs.")
    return GateResult("Q", "KILL", "Pre-trend", "PASS" if tb.loc[3, "mean"] > 0 else "FAIL", tb, notes)


def robustness_pass_only(s: pd.DataFrame) -> pd.DataFrame:
    """Every KILL gate re-run on Gate-A PASS-only must keep the sign of net@34 (§6 Gate A)."""
    p = s[s.gate_a_status == "PASS"]
    return pd.DataFrame([row("all scored (PASS+WARN)", net(s, 34), s.day_batch_cluster_id),
                         row("Gate A PASS only", net(p, 34), p.day_batch_cluster_id)])
