"""F013 Gate A: re-fetch raw announcement timestamp fields for the C02 catalog articles.

The C02 raw JSON cache (data_cache/f012_c02/raw/) is not on disk any more, so Gate A
re-reads the venue sources independently of the C02 catalog:
- Binance CMS detail (`publishDate`, body node tree) per article code.
- Bybit article page `__NEXT_DATA__` (`date`, `end_time`, description, rich-text body).
- Bybit announcements API list (`dateTimestamp`, `publishTime`) — serves only items
  from 2024-12-02, so it covers part of Train-1 only.

Cache: data_cache/f013/raw/ (git-ignored). Read-only public endpoints; no keys.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pandas as pd

from delisting_lab.fetch_announcements import _get, binance_node_text, bybit_doc_text

RAW = Path("data_cache/f013/raw")
CATALOG = Path("output/f012_c02_delisting/event_catalog.csv")


def _load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def fetch_binance_details(codes: list[str]) -> dict:
    out_p = RAW / "binance_detail.json"
    cache = _load(out_p)
    for c in codes:
        if c in cache:
            continue
        d = _get("https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query",
                 {"articleCode": c}).json()["data"]
        cache[c] = {"id": d.get("id"), "title": d.get("title"), "publishDate": d.get("publishDate"),
                    "text": binance_node_text(d["body"]), "fetched_at": int(time.time() * 1000)}
        out_p.write_text(json.dumps(cache))
        time.sleep(1.2)
    return cache


def fetch_bybit_pages(urls: list[str]) -> dict:
    out_p = RAW / "bybit_pages.json"
    cache = _load(out_p)
    for u in urls:
        if u in cache:
            continue
        try:
            html = _get(u, tries=3).text
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
            d = json.loads(m.group(1))["props"]["pageProps"]["articleDetail"]
            cache[u] = {"title": d.get("title"), "description": d.get("description", ""),
                        "date": d.get("date"), "end_time": d.get("end_time"),
                        "text": bybit_doc_text(d["content"]["json"]), "fetched_at": int(time.time() * 1000)}
        except Exception as e:  # page gone / layout change → recorded, audited as WARN
            cache[u] = {"error": repr(e)[:200], "fetched_at": int(time.time() * 1000)}
        out_p.write_text(json.dumps(cache))
        time.sleep(1.0)
    return cache


def fetch_bybit_api_list() -> list[dict]:
    """Full Bybit delistings list as served today (paginated)."""
    rows, page = [], 1
    while True:
        r = _get("https://api.bybit.com/v5/announcements/index",
                 {"locale": "en-US", "type": "delistings", "limit": 50, "page": page}).json()["result"]
        rows += r["list"]
        if not r["list"] or len(rows) >= int(r.get("total", 0)):
            break
        page += 1
        time.sleep(0.5)
    (RAW / "bybit_api_delistings.json").write_text(json.dumps(rows))
    return rows


def refetch_all(catalog: pd.DataFrame | None = None) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    cat = catalog if catalog is not None else pd.read_csv(CATALOG)
    bn = cat[cat.exchange == "binance"].source_id.drop_duplicates().tolist()
    by = cat[cat.exchange == "bybit"].source_url.drop_duplicates().tolist()
    fetch_binance_details(bn)
    fetch_bybit_pages(by)
    fetch_bybit_api_list()


if __name__ == "__main__":
    refetch_all()
    print("ok", sorted(p.name for p in RAW.iterdir()))
