"""Gate 0b: verify a random 30-event sample against Wayback snapshots of defillama.com/unlocks/{slug}
taken BEFORE the event day (prereg §2). Snapshot pages embed the as-of schedule in __NEXT_DATA__.
Match rule (fixed before running): a cliff in the snapshot within ±1 UTC day of the event whose summed
tokens on that day are within ±10% of the hindsight token-day total."""
from __future__ import annotations

import json
import re
import time

import numpy as np
import pandas as pd
import requests

from unlock_lab.fetch import ROOT, H

WB = ROOT / "wayback"
OUT = "output/f012_c03_unlock"
SEED = 20261006


def _get(url, tries=6):
    for k in range(tries):
        try:
            r = requests.get(url, headers=H, timeout=90)
            if r.status_code == 200 and "Temporarily Offline" not in r.text[:3000]:
                return r
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(5 * (k + 1))
    return None


def snapshots(slug: str) -> list[str]:
    WB.mkdir(parents=True, exist_ok=True)
    p = WB / f"cdx_{slug}.json"
    if not p.exists():
        r = _get(f"http://web.archive.org/cdx/search/cdx?url=defillama.com/unlocks/{slug}&output=json"
                 f"&fl=timestamp,statuscode&filter=statuscode:200&from=2022")
        if r is None:
            return []
        p.write_text(r.text or "[]")
    rows = json.loads(p.read_text() or "[]")
    return sorted(x[0] for x in rows[1:])


def snapshot_events(slug: str, ts: str) -> list[dict] | None:
    p = WB / f"page_{slug}_{ts}.json"
    if not p.exists():
        r = _get(f"http://web.archive.org/web/{ts}id_/https://defillama.com/unlocks/{slug}")
        if r is None:
            return None
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            p.write_text("null"); return None
        em = json.loads(m.group(1))["props"]["pageProps"].get("emissions") or {}
        p.write_text(json.dumps({"events": em.get("events") or [], "categoriesBreakdown": em.get("categoriesBreakdown")}))
    d = json.loads(p.read_text())
    return None if d is None else d["events"]


def check(sample: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r in sample.itertuples():
        day = pd.Timestamp(r.day)
        snaps = [s for s in snapshots(r.slug) if pd.Timestamp(s[:8], tz="UTC") < day]
        res = dict(event_id=r.event_id, slug=r.slug, day=day.date(), tokens=r.tokens, pct_circ=r.pct_circ,
                   rtype=r.rtype, n_snap_before=len(snaps))
        if not snaps:
            rows.append({**res, "status": "NO_SNAPSHOT_BEFORE"}); continue
        ts = snaps[-1]
        evs = snapshot_events(r.slug, ts)
        res["snapshot"] = ts
        res["lead_days"] = (day - pd.Timestamp(ts[:8], tz="UTC")).days
        if evs is None:
            rows.append({**res, "status": "SNAPSHOT_UNPARSEABLE"}); continue
        tot = {}
        for e in evs:
            t =pd.Timestamp(int(float(e["timestamp"])), unit="s", tz="UTC").floor("D")
            if abs((t - day).days) <= 1 and "linear" not in e.get("description", "").lower():
                tot[t] = tot.get(t, 0) + float((e.get("noOfTokens") or [0])[-1] or 0)
        best = max(tot.values(), default=0.0)
        res["snapshot_tokens"] = best
        rel = best / r.tokens - 1 if r.tokens else np.nan
        res["rel_diff"] = rel
        res["status"] = ("VERIFIED" if best > 0 and abs(rel) <= 0.10 else
                         "AMOUNT_MISMATCH" if best > 0 else "EVENT_ABSENT_IN_SNAPSHOT")
        rows.append(res)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    ev = pd.read_csv(ROOT / "events_all.csv.gz", parse_dates=["day"])
    ev = ev[(ev.circ_m1 > 0) & (ev.pct_circ > 0)]
    prim = ev.sample(30, random_state=SEED)
    sec = ev[ev.pct_circ >= 0.01].sample(30, random_state=SEED)
    a, b = check(prim), check(sec)
    a.to_csv(f"{OUT}/gate0_pit_check_random30.csv", index=False)
    b.to_csv(f"{OUT}/gate0_pit_check_large30.csv", index=False)
    cov = {s: len([x for x in snapshots(s) if x < "20250301"]) for s in ev.slug.unique()}
    json.dump({"tokens_with_any_snapshot_before_2025-03-01": sum(v > 0 for v in cov.values()),
               "tokens_total": len(cov),
               "random30": a.status.value_counts().to_dict(), "large30": b.status.value_counts().to_dict()},
              open(f"{OUT}/gate0_pit_summary.json", "w"), indent=1)
    print(a.status.value_counts(), b.status.value_counts(), sep="\n")
