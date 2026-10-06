"""Gate 0 coverage + PIT summary aggregation (writes gate0_coverage.json, gate0_pit_summary.json).
Run after catalog, prices, study and pit_check. Uses the cached Wayback CDX prefix listing
(data_cache/f012_c03/wayback_cdx.txt: defillama.com/unlocks prefix, 2023–2025)."""
from __future__ import annotations

import json
import re

import pandas as pd

from unlock_lab.fetch import ROOT

OUT = "output/f012_c03_unlock"


def coverage() -> dict:
    ev = pd.read_csv(ROOT / "events_all.csv.gz", parse_dates=["day"])
    u = pd.read_csv(ROOT / "universe.csv", parse_dates=["um_first", "bybit_first"])
    e = ev.merge(u[["slug", "symbol", "venue", "um_first", "bybit_first", "calibrated_note"]], on="slug", how="left")
    e["byb"] = e.bybit_first.notna() & (e.bybit_first < e.day - pd.Timedelta(days=1))
    e["um"] = e.um_first.notna() & (e.um_first < e.day - pd.Timedelta(days=1))
    e["perp"] = e.byb | e.um
    v = e[(e.circ_m1 > 0) & (e.pct_circ > 0)]
    L = v[v.pct_circ >= 0.01]
    f = pd.read_csv(f"{OUT}/event_frame.csv")
    s = f[f.ar_PRE.notna()]
    return dict(
        catalog_events=len(e), catalog_tokens=e.slug.nunique(),
        recipient_nonunknown_pct=round(100 * (e.rtype != "UNKNOWN").mean(), 1),
        recipient_counts=e.rtype.value_counts().to_dict(),
        recipient_tokens=e.groupby("rtype").slug.nunique().to_dict(),
        high_sell_events=int(e.high_sell.sum()), events_mixed=int(e.mixed.sum()),
        first_events=int(e["first"].sum()), recurring_events=int((~e["first"]).sum()),
        valid_pct_events=len(v), valid_pct_tokens=v.slug.nunique(),
        large_events=len(L), large_tokens=L.slug.nunique(), large_first=int(L["first"].sum()),
        short_avail_all=f"{int(e.perp.sum())}/{len(e)}", short_avail_tokens=f"{e[e.perp].slug.nunique()}/{e.slug.nunique()}",
        short_avail_bybit_all=f"{int(e.byb.sum())}/{len(e)}",
        short_avail_large=f"{int(L.perp.sum())}/{len(L)}",
        short_avail_large_bybit=f"{int(L.byb.sum())}/{len(L)} ({L[L.byb].slug.nunique()} tokens)",
        short_avail_scored=f"{int(s.short_avail.sum())}/{len(s)}",
        scored_events=len(s), scored_tokens=s.slug.nunique(), scored_large=int(s.LARGE.sum()),
        scored_large_tokens=s[s.LARGE].slug.nunique(),
        calibrated_note_event_tokens=f"{int(e.drop_duplicates('slug').calibrated_note.sum())}/{e.slug.nunique()}",
        universe_protocols=len(u), universe_priced=int(u.venue.notna().sum()),
        events_on_chain_coverage_pct=0.0)


def pit_summary() -> dict:
    ev = pd.read_csv(ROOT / "events_all.csv.gz", parse_dates=["day"])
    snap: dict[str, list] = {}
    for line in open(ROOT / "wayback_cdx.txt"):
        r = line.split()
        if len(r) < 3 or r[2] != "200":
            continue
        m = re.match(r"https?://(?:www\.)?defillama\.com(?::80)?/unlocks/([^/?#%]+)$", r[1])
        if m:
            snap.setdefault(m.group(1), []).append(pd.Timestamp(r[0][:8], tz="UTC"))
    ev["b"] = [any(t < d for t in snap.get(s, [])) for s, d in zip(ev.slug, ev.day)]
    ev["b30"] = [any(t <= d - pd.Timedelta(days=30) for t in snap.get(s, [])) for s, d in zip(ev.slug, ev.day)]
    L = ev[ev.pct_circ >= 0.01]
    a = pd.read_csv(f"{OUT}/gate0_pit_check_random30.csv")
    b = pd.read_csv(f"{OUT}/gate0_pit_check_large30.csv")
    ok = (a.status == "VERIFIED").mean()
    return {"rule": "VERIFIED = snapshot before event day has a cliff within ±1 UTC day with tokens within ±10%; "
                    "0b needs >=80% of random30",
            "random30": a.status.value_counts().to_dict(), "random30_verified_pct": round(100 * ok, 1),
            "large30_secondary": b.status.value_counts().to_dict(),
            "large30_verified_pct": round(100 * (b.status == "VERIFIED").mean(), 1),
            "large30_verified_given_parseable_snapshot":
                f"{(b.status == 'VERIFIED').sum()}/{b.status.isin(['VERIFIED', 'EVENT_ABSENT_IN_SNAPSHOT', 'AMOUNT_MISMATCH']).sum()}",
            "event_tokens_with_any_snapshot_before_event": f"{ev[ev.b].slug.nunique()}/{ev.slug.nunique()}",
            "events_with_snapshot_before": f"{int(ev.b.sum())}/{len(ev)}",
            "events_with_snapshot_>=30d_before": f"{int(ev.b30.sum())}/{len(ev)}",
            "large_events_with_snapshot_before": f"{int(L.b.sum())}/{len(L)}",
            "gate0b": "PASS" if ok >= 0.8 else "FAIL"}


if __name__ == "__main__":
    json.dump(coverage(), open(f"{OUT}/gate0_coverage.json", "w"), indent=1, default=str)
    json.dump(pit_summary(), open(f"{OUT}/gate0_pit_summary.json", "w"), indent=1)
