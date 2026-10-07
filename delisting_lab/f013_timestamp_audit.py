"""F013 Gate A — timestamp integrity audit of the delisting event catalog.

Primary timestamp P = first_publicly_observable_ts (never trade before it).
Secondary S = announcement_ts (audited only). Rules are frozen in
spec/features/active/F013-delisting-informational-alpha/prereg.md §Gate A; this module
implements them verbatim. No prices are read and no alpha is scored here.

Run: python3 -m delisting_lab.f013_timestamp_audit [--refetch]
Writes output/f013_delisting_info/gate_a_timestamp_audit.{csv,md}.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from delisting_lab.catalog import binance_article_events, bybit_article_events, parse_datetimes

CATALOG = Path("output/f012_c02_delisting/event_catalog.csv")
RAW = Path("data_cache/f013/raw")
OUT = Path("output/f013_delisting_info")

H = 3600 * 1000
ANCHOR_TOL_MS = 60 * 1000          # raw-field vs catalog anchor tolerance
PUSH_GAP_MAX_MS = 6 * H            # C02 rule: |publishTime - dateTimestamp| <= 6h → real push
EFF_TOL_MS = 60 * 1000             # body re-parse vs catalog effective_ts
INSTR_TOL_MIN = 1.0                # instrument delivery vs effective_ts (minutes)
OBS_LAG_WARN_S = 15 * 60           # P - S above this → A/B choice materially matters
BODY_PAST_TOL_MS = 1 * H           # explicit body datetime earlier than S - 1h
LATENCIES_S = (10, 30, 60, 300, 900)

FAIL_CODES = ("F1_primary_missing_or_before_secondary", "F2_raw_anchor_mismatch",
              "F3_ambiguous_late_push", "F4_no_positive_notice")


def bybit_push_class(date_ms: float | None, publish_ms: float | None, eff_ms: float | None) -> str:
    """Classify Bybit publishTime relative to dateTimestamp (both raw API fields).

    - "none": no publishTime
    - "within_gap": |gap| <= 6h (C02 took max(both) as P — conservative)
    - "early_push": publishTime earlier than date by > 6h (P = date is conservative)
    - "post_event_edit": publishTime later by > 6h but at/after effective_ts → an edit,
      cannot be the first push of a forward-looking notice
    - "ambiguous_late_push": publishTime later by > 6h and before effective_ts → the true
      first push may be publishTime, so P = dateTimestamp may precede observability
    """
    if publish_ms is None or pd.isna(publish_ms):
        return "none"
    gap = publish_ms - date_ms
    if abs(gap) <= PUSH_GAP_MAX_MS:
        return "within_gap"
    if gap < 0:
        return "early_push"
    if eff_ms is not None and not pd.isna(eff_ms) and publish_ms >= eff_ms:
        return "post_event_edit"
    return "ambiguous_late_push"


def conservative_observable_ms(date_ms: float, publish_ms: float | None, eff_ms: float | None) -> float:
    """Latest raw time at which the article can be claimed public (Bybit)."""
    c = bybit_push_class(date_ms, publish_ms, eff_ms)
    if c in ("within_gap", "ambiguous_late_push"):
        return max(date_ms, publish_ms)
    return date_ms


def classify(r: dict) -> tuple[str, list[str]]:
    """Gate A per-event status from audit fields (ms ints / NaN). Pure; frozen rules."""
    fails, warns = [], []
    P, S, eff = r.get("P_ms"), r.get("S_ms"), r.get("eff_ms")
    if _na(P) or _na(S) or P < S:
        fails.append(FAIL_CODES[0])
    anc = r.get("raw_anchor_diff_ms")
    if not _na(anc) and abs(anc) > ANCHOR_TOL_MS:
        fails.append(FAIL_CODES[1])
    if r.get("push_class") == "ambiguous_late_push" and not _na(P) and not _na(r.get("cons_obs_ms")) \
            and P < r["cons_obs_ms"]:
        fails.append(FAIL_CODES[2])
    if _na(eff) or _na(P) or eff <= P:
        fails.append(FAIL_CODES[3])
    if _na(anc):
        warns.append("W6_raw_source_unavailable")
    if r.get("push_class") in ("post_event_edit", "early_push"):
        warns.append("W4_publishTime_" + r["push_class"])
    reparse = r.get("eff_reparse_diff_ms")
    if _na(reparse):
        warns.append("W1_body_effective_unparsed")
    elif abs(reparse) > EFF_TOL_MS:
        warns.append("W1_body_effective_mismatch")
    iv = r.get("eff_vs_instrument_min")
    if not _na(iv) and abs(iv) > INSTR_TOL_MIN:
        warns.append("W2_instrument_delivery_mismatch")
    if r.get("effective_revised"):
        warns.append("W3_effective_revised")
    if not _na(P) and not _na(S) and (P - S) / 1000 > OBS_LAG_WARN_S:
        warns.append("W5_observability_lag_gt_15m")
    if r.get("body_past_dt"):
        warns.append("W8_body_datetime_before_announcement")
    status = "FAIL" if fails else ("WARN" if warns else "PASS")
    return status, fails + warns


def _na(x) -> bool:
    return x is None or (isinstance(x, float) and np.isnan(x)) or (x is pd.NaT)


def _ms(ts) -> float:
    if ts is None or (isinstance(ts, float) and np.isnan(ts)) or (isinstance(ts, str) and not ts):
        return np.nan
    t = pd.Timestamp(ts)
    if pd.isna(t):
        return np.nan
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return float(t.value // 10**6)


def _reparse_eff(exchange: str, row: pd.Series, raw: dict) -> tuple[float, list[int]]:
    """(effective_ms re-parsed from the re-fetched body for this row, all body datetimes)."""
    if not raw or "text" not in raw:
        return np.nan, []
    if exchange == "binance":
        p = binance_article_events(raw["title"], raw["text"])
        dts = [t for _, t in parse_datetimes(raw["text"])]
    else:
        p = bybit_article_events(raw["title"], raw.get("description", ""), raw["text"])
        dts = [t for _, t in parse_datetimes(raw.get("description", "") + "\n" + raw["text"])]
    if row.contract_type == "linear_perp":
        hit = [e for s, e in p["perps"] if s == row.symbol]
        eff = hit[0] if hit and hit[0] is not None else np.nan
    else:
        eff = p["spot_eff"] if row.base in p["spot_tokens"] and p["spot_eff"] else np.nan
    return float(eff) if not _na(eff) else np.nan, dts


def build_audit(cat: pd.DataFrame, raw_dir: Path = RAW) -> pd.DataFrame:
    bn = _jload(raw_dir / "binance_detail.json")
    bp = _jload(raw_dir / "bybit_pages.json")
    api = {a["url"].rstrip("/").split("-")[-1]: a
           for a in (_jload(raw_dir / "bybit_api_delistings.json") or [])}
    rows = []
    for _, e in cat.iterrows():
        S, P = _ms(e.announcement_ts), _ms(e.first_publicly_observable_ts)
        eff, eff_ann = _ms(e.effective_ts), _ms(e.effective_ts_announced)
        r = dict(event_id=e.event_id, exchange=e.exchange, symbol=e.symbol, contract_type=e.contract_type,
                 category=e.category, announcement_cluster_id=e.announcement_cluster_id,
                 day_batch_cluster_id=e.day_batch_cluster_id, source_id=e.source_id,
                 announcement_ts=e.announcement_ts, first_publicly_observable_ts=e.first_publicly_observable_ts,
                 effective_ts=e.effective_ts, catalog_ts_flag=e.ts_flag if isinstance(e.ts_flag, str) else "",
                 S_ms=S, P_ms=P, eff_ms=eff, effective_revised=bool(e.effective_revised),
                 eff_vs_instrument_min=float(e.eff_vs_instrument_min) if not pd.isna(e.eff_vs_instrument_min)
                 else np.nan)
        if e.exchange == "binance":
            raw = bn.get(e.source_id)
            pub = float(raw["publishDate"]) if raw and raw.get("publishDate") else np.nan
            r.update(raw_binance_publishDate=pub, raw_anchor_diff_ms=pub - S if not _na(pub) else np.nan,
                     push_class="n/a", cons_obs_ms=pub)
        else:
            raw = bp.get(e.source_url)
            raw = raw if raw and "error" not in raw else None
            date_ms = float(e.bybit_dateTimestamp)
            pub_ms = float(e.bybit_publishTime) if not pd.isna(e.bybit_publishTime) else np.nan
            page = _ms(raw["date"]) if raw else np.nan
            a = api.get(e.source_id.replace("BYBIT-", ""))
            r.update(raw_bybit_dateTimestamp=date_ms, raw_bybit_publishTime=pub_ms, raw_bybit_page_date=page,
                     raw_bybit_api_dateTimestamp=float(a["dateTimestamp"]) if a else np.nan,
                     raw_bybit_api_publishTime=float(a["publishTime"]) if a and a.get("publishTime") else np.nan,
                     raw_anchor_diff_ms=page - date_ms if not _na(page) else np.nan,
                     push_class=bybit_push_class(date_ms, None if _na(pub_ms) else pub_ms, eff),
                     cons_obs_ms=conservative_observable_ms(date_ms, None if _na(pub_ms) else pub_ms, eff))
        rep, dts = _reparse_eff(e.exchange, e, raw)
        r["eff_reparsed_ms"] = rep
        r["eff_reparse_diff_ms"] = rep - eff_ann if not _na(rep) else np.nan
        r["body_min_dt_ms"] = float(min(dts)) if dts else np.nan
        r["body_past_dt"] = bool(dts) and min(dts) < S - BODY_PAST_TOL_MS
        r["obs_lag_s"] = (P - S) / 1000 if not (_na(P) or _na(S)) else np.nan
        r["notice_h_from_P"] = (eff - P) / H if not (_na(P) or _na(eff)) else np.nan
        for L in LATENCIES_S:   # would "S + L" precede P? (only legal if False)
            r[f"S_plus_{L}s_before_P"] = bool(not _na(P) and S + L * 1000 < P)
        st, why = classify(r)
        r["gate_a_status"], r["gate_a_reasons"] = st, ";".join(why)
        rows.append(r)
    out = pd.DataFrame(rows)
    for c in [c for c in out.columns if c.endswith("_ms") and c not in ("raw_anchor_diff_ms",
                                                                        "eff_reparse_diff_ms")]:
        out[c.replace("_ms", "_utc")] = pd.to_datetime(out[c], unit="ms", utc=True)
    return out


def _md(df: pd.DataFrame, index: bool = True) -> str:
    """Minimal markdown table (no tabulate dependency)."""
    d = df.reset_index() if index else df
    h = [str(c) for c in d.columns]
    rows = ["| " + " | ".join(h) + " |", "|" + "---|" * len(h)]
    rows += ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(rows)


def _jload(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def _q(s: pd.Series) -> str:
    s = s.dropna()
    if not len(s):
        return "n/a"
    q = s.quantile([0, .25, .5, .75, .9, 1]).round(1).tolist()
    return f"n={len(s)} min {q[0]} p25 {q[1]} p50 {q[2]} p75 {q[3]} p90 {q[4]} max {q[5]}"


def gate_a_verdict(a: pd.DataFrame) -> tuple[str, str]:
    """Aggregate Gate A decision — frozen in prereg §Gate A."""
    n = len(a)
    usable = (a.gate_a_status != "FAIL").mean()
    worst_venue_fail = a.groupby("exchange").gate_a_status.apply(lambda s: (s == "FAIL").mean()).max()
    f3_after_drop = 0  # F3 events are dropped, so no residual look-ahead in the usable set
    if usable >= 0.85 and worst_venue_fail <= 0.25 and f3_after_drop == 0:
        return "PASS", f"usable {usable:.1%} ≥ 85%, worst-venue FAIL {worst_venue_fail:.1%} ≤ 25% (n={n})"
    return "FAIL", f"usable {usable:.1%} (bar 85%), worst-venue FAIL {worst_venue_fail:.1%} (bar 25%) (n={n})"


def write_report(a: pd.DataFrame, out: Path = OUT) -> str:
    out.mkdir(parents=True, exist_ok=True)
    cols_first = ["event_id", "exchange", "symbol", "contract_type", "category", "gate_a_status", "gate_a_reasons"]
    a[cols_first + [c for c in a.columns if c not in cols_first]].to_csv(out / "gate_a_timestamp_audit.csv",
                                                                       index=False)
    verdict, why = gate_a_verdict(a)
    st = pd.crosstab(a.exchange, a.gate_a_status, margins=True)
    reasons = a.gate_a_reasons.str.split(";").explode()
    reasons = reasons[reasons != ""].value_counts()
    art = a.drop_duplicates("source_id")
    flag = (a.catalog_ts_flag != "")
    L = []
    L.append("# F013 Gate A — timestamp integrity audit\n")
    L.append("Sample: C02 Train-1 discovery catalog (`output/f012_c02_delisting/event_catalog.csv`, "
             "CONTAMINATED discovery set). No prices read; no alpha scored. Rules frozen in "
             "`spec/features/active/F013-delisting-informational-alpha/prereg.md` §Gate A.\n")
    L.append(f"## Verdict: **Gate A {verdict}** — {why}\n")
    L.append("Primary timestamp **P = first_publicly_observable_ts** (choice B). Secondary "
             "S = announcement_ts (choice A) is audit-only. FAIL events are excluded from every later gate; "
             "WARN events stay in the primary sample and are re-run as a PASS-only robustness split.\n")
    L.append("## Status by venue (events)\n")
    L.append(_md(st) + "\n")
    L.append(f"Articles: {len(art)} ({(art.exchange == 'binance').sum()} Binance, "
             f"{(art.exchange == 'bybit').sum()} Bybit).\n")
    L.append("## Reason counts (events; one event may carry several)\n")
    L.append(_md(reasons.rename("events").rename_axis("reason").to_frame()) + "\n")
    L.append("## Raw-source re-verification\n")
    for ex, g in a.groupby("exchange"):
        have = g.raw_anchor_diff_ms.notna()
        L.append(f"- **{ex}**: raw anchor re-fetched for {have.sum()}/{len(g)} events; "
                 f"|anchor − catalog| ≤ 60 s for {(g.raw_anchor_diff_ms.abs() <= ANCHOR_TOL_MS).sum()}; "
                 f"max |diff| {g.raw_anchor_diff_ms.abs().max() / 1000 if have.any() else float('nan'):.1f} s.")
    by = a[a.exchange == "bybit"]
    if len(by):
        api_have = by.raw_bybit_api_dateTimestamp.notna()
        L.append(f"- Bybit API list (re-fetched today) serves {api_have.sum()}/{len(by)} catalog events; "
                 f"dateTimestamp equal to catalog for "
                 f"{(by.raw_bybit_api_dateTimestamp == by.raw_bybit_dateTimestamp)[api_have].sum()}; "
                 f"publishTime equal to the C02-cached value for "
                 f"{(by.raw_bybit_api_publishTime == by.raw_bybit_publishTime)[api_have].sum()}. "
                 "publishTime is still not a proven first-push clock: gaps of days/months exist (W4/F3).")
    bn = a[(a.exchange == "binance") & a.raw_anchor_diff_ms.notna()]
    if len(bn):
        L.append(f"- Binance `publishDate − releaseDate`: min {bn.raw_anchor_diff_ms.min() / 1000:.1f} s, "
                 f"max {bn.raw_anchor_diff_ms.max() / 1000:.1f} s (negative = publishDate earlier, so P = "
                 "releaseDate is the later, conservative clock).")
    L.append("- Binance: the catalog anchor is CMS `releaseDate`; detail `publishDate` is the re-fetch. "
             "Both are Binance CMS clocks — no third-party observability clock exists in the free data. "
             "Residual risk: an article staged before `releaseDate` cannot be detected here.\n")
    L.append("## Body-parsed effective times\n")
    rep = a.eff_reparse_diff_ms
    L.append("- Consistency check, not an independent parser: re-fetched bodies run through the same C02 "
             "parser. It proves the body text did not change and the catalog matches today's source.")
    L.append(f"- Re-parsed from re-fetched bodies: {rep.notna().sum()}/{len(a)}; match catalog "
             f"announced effective_ts (±60 s): {(rep.abs() <= EFF_TOL_MS).sum()}; mismatch: "
             f"{(rep.abs() > EFF_TOL_MS).sum()}; unparsed: {rep.isna().sum()}.")
    L.append(f"- Instrument delivery cross-check |Δ| > 1 min: {(a.eff_vs_instrument_min.abs() > INSTR_TOL_MIN).sum()} "
             f"of {a.eff_vs_instrument_min.notna().sum()} with a reported delivery time.")
    L.append(f"- Postponed (effective_revised): {a.effective_revised.sum()}.")
    L.append(f"- Notice length from P (h): {_q(a.notice_h_from_P)}.\n")
    L.append("## Observability lag P − S (seconds)\n")
    for ex, g in a.groupby("exchange"):
        L.append(f"- {ex}: {_q(g.obs_lag_s)}; P ≠ S for {(g.obs_lag_s > 0).sum()}/{len(g)}.")
    L.append(f"- all: {_q(a.obs_lag_s)}; P ≠ S for {(a.obs_lag_s > 0).sum()}/{len(a)}.\n")
    L.append("Look-ahead exposure if entries were timed from S instead of P "
             "(share of events where S + latency is still before P):\n")
    L.append("| latency | events where S+latency < P | share |\n|---|---|---|")
    for Ls in LATENCIES_S:
        k = a[f"S_plus_{Ls}s_before_P"].sum()
        L.append(f"| {Ls}s | {k} | {k / len(a):.1%} |")
    L.append("")
    L.append("## ts_flag rates (C02 catalog)\n")
    L.append(f"- events with a ts_flag: {flag.sum()}/{len(a)} ({flag.mean():.1%}); "
             f"Bybit {flag[a.exchange == 'bybit'].sum()}/{(a.exchange == 'bybit').sum()}; "
             f"Binance {flag[a.exchange == 'binance'].sum()}/{(a.exchange == 'binance').sum()}.")
    pc = by.push_class.value_counts()
    L.append("- Bybit publishTime classes (events): " + ", ".join(f"{k} {v}" for k, v in pc.items()) + ".\n")
    L.append("## A vs B primary timestamp choice\n")
    L.append("- **B (first_publicly_observable_ts) is primary — frozen.** It is ≥ A for every event by "
             "construction and audited above; entries are only legal at P + latency.")
    L.append("- A (announcement_ts) is retained for audit only. Using A as the clock would place entries before "
             "public observability for the share shown in the look-ahead table; it is forbidden as a trading clock.")
    L.append("- F3 (ambiguous late push) events are dropped instead of re-timing them to publishTime: re-timing "
             "would be a post-hoc choice, and the drop is the conservative frozen rule.\n")
    fails = a[a.gate_a_status == "FAIL"]
    L.append("## FAIL events (excluded downstream)\n")
    if len(fails):
        L.append(_md(fails[["event_id", "gate_a_reasons", "catalog_ts_flag"]], index=False) + "\n")
    else:
        L.append("None.\n")
    L.append("## Reproduce\n\n`python3 -m delisting_lab.f013_timestamp_audit --refetch` (network, public endpoints, "
             "cache `data_cache/f013/raw/`), then without `--refetch` offline.\n")
    md = "\n".join(L)
    (out / "gate_a_timestamp_audit.md").write_text(md)
    return verdict


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--refetch", action="store_true")
    args = ap.parse_args(argv)
    cat = pd.read_csv(CATALOG)
    if args.refetch:
        from delisting_lab.f013_raw import refetch_all
        refetch_all(cat)
    a = build_audit(cat)
    v = write_report(a)
    print("Gate A", v, a.gate_a_status.value_counts().to_dict())


if __name__ == "__main__":
    main()
