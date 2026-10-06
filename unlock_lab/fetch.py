"""F012-C03 free-data fetchers (prereg §1, §7). Raw caches under data_cache/f012_c03/ (git-ignored)."""
from __future__ import annotations

import gzip
import io
import json
import shutil
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path("data_cache/f012_c03")
EM = ROOT / "emissions"
KL = ROOT / "klines"
H = {"User-Agent": "Mozilla/5.0"}
DS = "https://defillama-datasets.llama.fi"
VISION = "https://data.binance.vision/data"
KL_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def free_gb() -> float:
    return shutil.disk_usage(".").free / 1e9


def _get(url, params=None, tries=4):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code in (404, 403):
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (k + 1))
    return None


def fetch_emissions() -> list[str]:
    EM.mkdir(parents=True, exist_ok=True)
    slugs = _get(f"{DS}/emissionsProtocolsList").json()
    (ROOT / "emissionsProtocolsList.json").write_text(json.dumps(slugs))
    for s in slugs:
        p = EM / f"{s}.json.gz"
        if p.exists():
            continue
        r = _get(f"{DS}/emissions/{s}")
        if r is not None:
            p.write_bytes(gzip.compress(r.content))
    return slugs


def fetch_gecko_list() -> None:
    p = ROOT / "coingecko_coins_list.json.gz"
    if not p.exists():
        r = _get("https://api.coingecko.com/api/v3/coins/list", {"include_platform": "true"})
        p.write_bytes(gzip.compress(r.content))


def vision_daily(kind: str, sym: str, lo="2023-10", hi="2025-04") -> pd.DataFrame | None:
    """kind: 'spot' or 'futures/um'. Monthly 1d klines; cached as one csv.gz per (kind,sym)."""
    KL.mkdir(parents=True, exist_ok=True)
    tag = "spot" if kind == "spot" else "um"
    p = KL / f"{tag}_{sym}.csv.gz"
    if p.exists():
        df = pd.read_csv(p)
        return df if len(df) else None
    rows = []
    for m in pd.period_range(lo, hi, freq="M"):
        r = _get(f"{VISION}/{kind}/monthly/klines/{sym}/1d/{sym}-1d-{m}.zip")
        if r is None:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            d = pd.read_csv(z.open(z.namelist()[0]), header=None, names=KL_COLS)
        d = d[pd.to_numeric(d.open_time, errors="coerce").notna()]
        rows.append(d)
    df = pd.concat(rows) if rows else pd.DataFrame(columns=KL_COLS)
    df.to_csv(p, index=False, compression="gzip")
    return df if len(df) else None


def bybit_daily(sym: str, category="linear") -> pd.DataFrame | None:
    KL.mkdir(parents=True, exist_ok=True)
    p = KL / f"bybit{category}_{sym}.csv.gz"
    if p.exists():
        df = pd.read_csv(p)
        return df if len(df) else None
    out, end = [], int(pd.Timestamp("2025-04-30", tz="UTC").timestamp() * 1000)
    start = int(pd.Timestamp("2023-10-01", tz="UTC").timestamp() * 1000)
    while end > start:
        r = _get("https://api.bybit.com/v5/market/kline",
                 {"category": category, "symbol": sym, "interval": "D", "end": end, "limit": 1000})
        lst = (r.json().get("result") or {}).get("list") if r is not None else None
        if not lst:
            break
        out += lst
        end = int(lst[-1][0]) - 1
        if len(lst) < 1000:
            break
    df = pd.DataFrame(out, columns=["open_time", "open", "high", "low", "close", "volume", "quote_volume"])
    df = df.astype(float).sort_values("open_time").drop_duplicates("open_time")
    df = df[df.open_time >= start]
    df.to_csv(p, index=False, compression="gzip")
    return df if len(df) else None


def bybit_instruments() -> pd.DataFrame:
    """Currently-listed Bybit linear perps (launchTime). Delisted ones resolved via kline history."""
    p = ROOT / "bybit_linear_instruments.json"
    if not p.exists():
        rows, cur = [], None
        while True:
            q = {"category": "linear", "limit": 1000}
            if cur:
                q["cursor"] = cur
            j = _get("https://api.bybit.com/v5/market/instruments-info", q).json()["result"]
            rows += j["list"]
            cur = j.get("nextPageCursor")
            if not cur:
                break
        p.write_text(json.dumps(rows))
    return pd.DataFrame(json.loads(p.read_text()))


if __name__ == "__main__":
    s = fetch_emissions()
    fetch_gecko_list()
    print(len(s), "slugs;", len(list(EM.glob("*.json.gz"))), "files;", f"{free_gb():.1f} GB free")
