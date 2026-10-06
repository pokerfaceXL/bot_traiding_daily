"""Train-1 cliff token-day catalog from the frozen DefiLlama emissions snapshot (prereg §4–§6)."""
from __future__ import annotations

import gzip
import json
import re

import numpy as np
import pandas as pd

from unlock_lab.fetch import EM, ROOT

T1_LO, T1_HI = pd.Timestamp("2024-03-01", tz="UTC"), pd.Timestamp("2025-03-01", tz="UTC")
HIGH_SELL = {"TEAM", "VC"}
RX = [  # prereg §5, label regex first (VC before TEAM so "insider investors" → VC)
    ("VC", r"investor|seed|private|strategic|backer|venture|\bvc\b|series|angel|\bkol"),
    ("TEAM", r"team|contributor|advisor|\bcore\b|founder|employee|insider"),
    ("ECOSYSTEM", r"ecosystem|treasury|foundation|\bdao\b|community|grant|reserve|incentive|reward|"
                  r"staking|liquidity mining|development|growth|partner"),
    ("OTHER", r"airdrop|public|\bido\b|\bico\b|launchpad|sale|liquidity|market mak"),
]
CAT = {"insiders": "TEAM", "privateSale": "VC", "noncirculating": "ECOSYSTEM", "farming": "ECOSYSTEM",
       "publicSale": "OTHER", "airdrop": "OTHER", "liquidity": "OTHER"}


def recipient(label: str, category: str | None) -> str:
    s = (label or "").lower()
    for k, rx in RX:
        if re.search(rx, s):
            return k
    return CAT.get(category or "", "UNKNOWN")


def load(slug: str) -> dict:
    return json.loads(gzip.decompress((EM / f"{slug}.json.gz").read_bytes()))


def schedule_circ(d: dict) -> pd.Series:
    """Daily schedule-implied cumulative unlocked (sum over documented sections)."""
    tot = None
    for sec in (d.get("documentedData") or {}).get("data") or []:
        s = pd.Series({pd.Timestamp(int(x["timestamp"]), unit="s", tz="UTC").floor("D"): float(x.get("unlocked") or 0)
                       for x in sec.get("data") or []})
        s = s[~s.index.duplicated(keep="last")]
        tot = s if tot is None else tot.add(s, fill_value=np.nan)
    if tot is None or tot.empty:
        return pd.Series(dtype=float)
    return tot.sort_index().ffill()


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    slugs = json.loads((ROOT / "emissionsProtocolsList.json").read_text())
    rows, prot = [], []
    for slug in slugs:
        try:
            d = load(slug)
        except FileNotFoundError:
            continue
        m = d.get("metadata") or {}
        tok = str(m.get("token") or "")
        gid = d.get("gecko_id") or (tok.split(":", 1)[1] if tok.startswith("coingecko:") else None)
        notes = " ".join(m.get("notes") or [])
        prot.append(dict(slug=slug, name=d.get("name"), gecko_id=gid, token=tok,
                         n_cliff_all=sum(1 for e in (m.get("events") or []) if e.get("unlockType") == "cliff"),
                         calibrated_note=bool(re.search(r"calibrat|actual|on-chain|onchain|adjusted", notes, re.I))))
        circ = schedule_circ(d)
        for ue in m.get("unlockEvents") or []:
            t = pd.Timestamp(int(float(ue["timestamp"])), unit="s", tz="UTC")
            if not (T1_LO <= t < T1_HI):
                continue
            for a in ue.get("cliffAllocations") or []:
                amt = float(a.get("amount") or 0)
                if amt > 0:
                    rows.append(dict(slug=slug, gecko_id=gid, ts=t, day=t.floor("D"), label=a.get("recipient"),
                                     category=a.get("category"), amount=amt,
                                     rtype=recipient(a.get("recipient"), a.get("category"))))
        if len(circ):
            for r in rows:
                if r["slug"] == slug and "circ_m1" not in r:
                    c = circ[circ.index <= r["day"] - pd.Timedelta(days=1)]
                    r["circ_m1"] = float(c.iloc[-1]) if len(c) else np.nan
    alloc = pd.DataFrame(rows)
    prot = pd.DataFrame(prot)

    def agg(g):
        by = g.groupby("rtype").amount.sum()
        return pd.Series(dict(gecko_id=g.gecko_id.iloc[0], ts=g.ts.min(), tokens=g.amount.sum(),
                              circ_m1=g.circ_m1.iloc[0] if "circ_m1" in g else np.nan,
                              rtype=by.idxmax(), mixed=len(by) > 1, n_alloc=len(g),
                              labels="|".join(sorted(set(map(str, g.label))))))
    ev = alloc.groupby(["slug", "day"]).apply(agg).reset_index()
    ev["pct_circ"] = ev.tokens / ev.circ_m1
    ev["high_sell"] = ev.rtype.isin(HIGH_SELL)
    ev = ev.sort_values(["slug", "day"])
    prev = ev.groupby("slug").day.shift()
    # first vs recurring: no cliff of this token in the prior 180d (pre-Train-1 cliffs counted too)
    allc = {}
    for slug in ev.slug.unique():
        d = load(slug)
        allc[slug] = sorted({pd.Timestamp(int(float(u["timestamp"])), unit="s", tz="UTC").floor("D")
                             for u in (d.get("metadata") or {}).get("unlockEvents") or []
                             if any(float(a.get("amount") or 0) > 0 for a in u.get("cliffAllocations") or [])})
    ev["first"] = [not any(r.day - pd.Timedelta(days=180) <= x < r.day for x in allc[r.slug]) for r in ev.itertuples()]
    ev["event_id"] = ev.slug + "_" + ev.day.dt.strftime("%Y%m%d")
    return ev.reset_index(drop=True), prot


if __name__ == "__main__":
    ev, prot = build()
    ev.to_csv(ROOT / "events_all.csv.gz", index=False)
    prot.to_csv(ROOT / "protocols.csv", index=False)
    print(len(ev), ev.slug.nunique(), ev.rtype.value_counts().to_dict())
    print(ev.pct_circ.describe())
