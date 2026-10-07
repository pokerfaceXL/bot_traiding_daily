"""F013 discovery event sample (prereg §1, §3): Gate-A-usable events on the C02 Train-1 catalog.

One row per (venue, traded perp symbol, article). Gate A FAIL rows are dropped (never re-timed).
- `perp_delist` / `token_delist` linear-perp rows trade their own perp.
- `token_delist` spot rows whose same-venue USDT perp is live at P (and which have no perp row in
  the same article) trade `<base>USDT` perp ("spot delisted, perp continues").
Primary sample excludes index perps and migrations (reported in Gate M only).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CATALOG = Path("output/f012_c02_delisting/event_catalog.csv")
GATE_A = Path("output/f013_delisting_info/gate_a_timestamp_audit.csv")
TS_COLS = ("announcement_ts", "first_publicly_observable_ts", "effective_ts")
TOKEN_CLUSTER_DAYS = 30


def token_clusters(df: pd.DataFrame) -> pd.Series:
    """Same base announced (either venue) within 30 d of the previous one → same token cluster."""
    out = pd.Series(index=df.index, dtype=object)
    for base, g in df.sort_values("first_publicly_observable_ts").groupby("base"):
        k, last = 0, None
        for i, t in g.first_publicly_observable_ts.items():
            if last is not None and t - last > pd.Timedelta(days=TOKEN_CLUSTER_DAYS):
                k += 1
            out[i] = f"{base}-{k}"
            last = t
    return out


def delist_type(r) -> str:
    if bool(r.get("index_contract")):
        return "index"
    if bool(r.get("migration_flag")):
        return "migration"
    if r["contract_type"] == "spot":
        return "spot_delisted_perp_live"
    return "spot_and_perp" if (r["category"] == "token_delist" or r.get("spot_also_delisted_same_article") is True
                               or r.get("spot_also_delisted_same_article") == "True") else "perp_only"


def load_events(include_excluded: bool = False) -> pd.DataFrame:
    cat = pd.read_csv(CATALOG)
    ga = pd.read_csv(GATE_A, usecols=["event_id", "gate_a_status", "gate_a_reasons"])
    cat = cat.merge(ga, on="event_id", how="left")
    for c in TS_COLS:
        cat[c] = pd.to_datetime(cat[c], utc=True, format="ISO8601")
    cat = cat[cat.gate_a_status.isin(["PASS", "WARN"])].copy()
    perp = cat[cat.contract_type == "linear_perp"].copy()
    live = cat[(cat.contract_type == "spot") & (cat.same_venue_perp_live_at_announcement == True)].copy()  # noqa: E712
    key = set(zip(perp.exchange, perp.base, perp.source_id))
    live = live[[k not in key for k in zip(live.exchange, live.base, live.source_id)]]
    live["symbol"] = live.base + "USDT"
    ev = pd.concat([perp, live]).drop_duplicates(["exchange", "symbol", "source_id"])
    ev["delist_type"] = ev.apply(delist_type, axis=1)
    ev["primary_type"] = ev.delist_type.map({"perp_only": "perp_only", "spot_and_perp": "spot_and_perp",
                                             "spot_delisted_perp_live": "spot_and_perp"}).fillna(ev.delist_type)
    ev["in_primary_universe"] = ~ev.delist_type.isin(["index", "migration"])
    ev["P"] = ev.first_publicly_observable_ts
    ev["token_cluster_id"] = token_clusters(ev)
    ev["follower_event"] = ev.follower_event.astype(str).str.lower().eq("true")
    ev = ev.sort_values(["P", "exchange", "symbol"]).reset_index(drop=True)
    return ev if include_excluded else ev[ev.in_primary_universe].reset_index(drop=True)


def primary_window(P: pd.Timestamp, eff: pd.Timestamp, latency=pd.Timedelta(minutes=5)):
    """(entry bar open, exit target) per prereg §3, or None if eff-1h - entry < 1h."""
    entry = (P + latency).ceil("1min")
    if eff - pd.Timedelta(hours=1) - entry < pd.Timedelta(hours=1):
        return None
    return entry, min(entry + pd.Timedelta(hours=72), eff - pd.Timedelta(hours=1))


if __name__ == "__main__":
    e = load_events(include_excluded=True)
    print(len(e), e.delist_type.value_counts().to_dict(), e.exchange.value_counts().to_dict())
    print(e[e.in_primary_universe].groupby("primary_type").size().to_dict(),
          "insufficient notice:", int(np.sum([primary_window(r.P, r.effective_ts) is None for r in e.itertuples()])))
