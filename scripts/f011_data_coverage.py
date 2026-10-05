#!/usr/bin/env python3
"""
F011 · Free high-resolution data coverage recon (T0, non-trading).

Empirically probes which FREE >=5m-resolution data exists for BTCUSDT / ETHUSDT USDT perps over
Train-1 (2024-01-26T00:00Z .. 2025-02-28T23:00Z, i.e. 5m bars in [2024-01-26, 2025-03-01)):

  1. Bybit /v5/market/open-interest intervalTime=5min (+15min): earliest reachable bar (monthly
     scan + day bisection + intra-day paging), full Train-1 5m pull, gap list.
  2. Bybit /v5/market/account-ratio period=5min: same.
  3. Bybit trade archive public.bybit.com/trading/<SYM>/: listing + HEAD size per Train-1 day,
     2 sample days per symbol downloaded, 5m taker_buy/sell, OFI, CVD, trade_count rebuilt.
  4. Binance data.binance.vision futures/um daily metrics, klines 5m, aggTrades (+ monthly
     fundingRate): S3 listing (marker pagination), missing days, sizes, sample columns.
  5. Cached funding (data_cache/funding) Train-1 coverage; Binance funding monthly files.
  6. Cross-check on the sample days: Bybit vs Binance 5m OI change direction, Bybit rebuilt
     taker flow vs Binance kline taker volume (correlations; sanity only).

Every number in report.md / coverage.json comes from responses captured by this run; small raw
probe responses go to <out>/raw/. Large pulls/samples go to <data-dir> (git-ignored).

Usage:
  python3 scripts/f011_data_coverage.py \
      [--out output/f011_forced_flow/coverage] [--data-dir data_cache] \
      [--sample-days 2024-06-12,2024-10-01] [--no-full-pull]
  python3 scripts/f011_data_coverage.py --refresh-oi-spots  # existing report; four small requests only
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import socket
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TRAIN1_START = datetime(2024, 1, 26, tzinfo=timezone.utc)
TRAIN1_END_EXCL = datetime(2025, 3, 1, tzinfo=timezone.utc)  # last hourly bar 2025-02-28T23Z
SCAN_START = datetime(2018, 1, 1, tzinfo=timezone.utc)

BYBIT_API = "https://api.bybit.com"
BYBIT_ARCHIVE = "https://public.bybit.com/trading"
BINANCE_S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
BINANCE_DL = "https://data.binance.vision"
S3_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"

REPO = Path(__file__).resolve().parent.parent
DAY_MS = 86_400_000

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "f011-data-coverage/1.0 (research, public data)"
REQ_STATS = {"count": 0, "errors": 0}


# --------------------------------------------------------------------------- utils
def ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def iso(ts_ms) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(int(ts_ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def train1_days() -> list[date]:
    d, out = TRAIN1_START.date(), []
    while d < TRAIN1_END_EXCL.date():
        out.append(d)
        d += timedelta(days=1)
    return out


def http(method: str, url: str, params=None, stream=False, headers=None, timeout=30, tries=5):
    last = None
    for i in range(tries):
        try:
            REQ_STATS["count"] += 1
            r = SESSION.request(method, url, params=params, stream=stream, headers=headers, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(1.5 * (i + 1))
                continue
            return r
        except requests.RequestException as exc:
            last = repr(exc)
            REQ_STATS["errors"] += 1
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{method} {url} failed: {last}")


def bybit_get(path: str, params: dict) -> dict:
    r = http("GET", BYBIT_API + path, params=params)
    j = r.json()
    if j.get("retCode") != 0:
        raise RuntimeError(f"Bybit {path} {params} -> {j.get('retCode')} {j.get('retMsg')}")
    time.sleep(0.04)
    return j


class Raw:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.files = []

    def save(self, name: str, obj) -> str:
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(obj, (bytes, bytearray)):
            p.write_bytes(obj)
        elif isinstance(obj, str):
            p.write_text(obj)
        else:
            p.write_text(json.dumps(obj, indent=1, default=str))
        rel = str(p.relative_to(self.root.parent))
        self.files.append(rel)
        return rel


def runs_of_missing(expected: np.ndarray, present: np.ndarray, step_ms: int) -> list[dict]:
    """Group missing timestamps (expected - present) into contiguous runs."""
    missing = np.setdiff1d(expected, present)
    runs = []
    if missing.size == 0:
        return runs
    start = prev = int(missing[0])
    for t in missing[1:]:
        t = int(t)
        if t - prev != step_ms:
            runs.append({"from": iso(start), "to": iso(prev), "bars": (prev - start) // step_ms + 1})
            start = t
        prev = t
    runs.append({"from": iso(start), "to": iso(prev), "bars": (prev - start) // step_ms + 1})
    return runs


def missing_day_runs(missing: list[date]) -> list[str]:
    out, i = [], 0
    while i < len(missing):
        j = i
        while j + 1 < len(missing) and missing[j + 1] - missing[j] == timedelta(days=1):
            j += 1
        out.append(str(missing[i]) if i == j else f"{missing[i]}..{missing[j]}")
        i = j + 1
    return out


# --------------------------------------------------------------------------- 1+2 Bybit REST
BYBIT_SERIES = {
    "oi_5min": dict(path="/v5/market/open-interest", key="intervalTime", val="5min", step=300_000, limit=200),
    "oi_15min": dict(path="/v5/market/open-interest", key="intervalTime", val="15min", step=900_000, limit=200),
    "account_ratio_5min": dict(path="/v5/market/account-ratio", key="period", val="5min", step=300_000, limit=500),
}


def bybit_window(series: dict, symbol: str, t0: int, t1: int, limit: int, cursor: str | None = None) -> dict:
    p = {"category": "linear", "symbol": symbol, series["key"]: series["val"],
         "startTime": t0, "endTime": t1, "limit": limit}
    if cursor:
        p["cursor"] = urllib.parse.unquote(cursor)
    return bybit_get(series["path"], p)


def bybit_rows(j: dict) -> list[dict]:
    return j["result"]["list"]


def bybit_earliest(name: str, symbol: str, raw: Raw) -> dict:
    s = BYBIT_SERIES[name]
    now = datetime.now(timezone.utc)

    def has(t0: datetime, t1: datetime) -> bool:
        return len(bybit_rows(bybit_window(s, symbol, ms(t0), ms(t1) - 1, 1))) > 0

    # coarse scan: 1-day window at every month start (also exposes month-start holes)
    months, m = [], SCAN_START
    while m < now:
        months.append(m)
        m = (m.replace(day=28) + timedelta(days=4)).replace(day=1)
    scan = [(mm, has(mm, mm + timedelta(days=1))) for mm in months]
    first_idx = next((i for i, (_, ok) in enumerate(scan) if ok), None)
    if first_idx is None:
        return {"earliest": None, "note": "no data at any month start since 2018"}
    holes_after = [str(mm.date()) for mm, ok in scan[first_idx:] if not ok]
    # bisect days in (previous month start, first month with data]
    lo = scan[first_idx - 1][0] if first_idx > 0 else SCAN_START - timedelta(days=1)
    hi = scan[first_idx][0]
    lo_d, hi_d = 0, (hi - lo).days  # has(lo+hi_d) True; search smallest day index with data
    probes = 0
    while hi_d - lo_d > 1:
        mid = (lo_d + hi_d) // 2
        probes += 1
        if has(lo + timedelta(days=mid), lo + timedelta(days=mid + 1)):
            hi_d = mid
        else:
            lo_d = mid
    day0 = lo + timedelta(days=hi_d)
    # page through the earliest day fully
    rows, cursor, pages = [], None, 0
    first_page = None
    while True:
        j = bybit_window(s, symbol, ms(day0), ms(day0) + DAY_MS - 1, s["limit"], cursor)
        if first_page is None:
            first_page = j
        rows += bybit_rows(j)
        pages += 1
        cursor = j["result"].get("nextPageCursor")
        if not cursor or not bybit_rows(j) or pages > 20:
            break
    ts = sorted({int(r["timestamp"]) for r in rows})
    earliest = ts[0]
    # verify nothing exists before it and that data exists after it
    before = bybit_window(s, symbol, ms(SCAN_START), earliest - 1, 1)
    after = bybit_window(s, symbol, earliest, ms(now), 1)
    raw.save(f"bybit/{name}_{symbol}_earliest_day_page1.json", first_page)
    raw.save(f"bybit/{name}_{symbol}_before_earliest.json", before)
    return {
        "earliest": iso(earliest),
        "earliest_ms": earliest,
        "earliest_day_rows": len(ts),
        "verified_empty_before": len(bybit_rows(before)) == 0,
        "verified_data_after": len(bybit_rows(after)) > 0,
        "first_month_with_data": str(scan[first_idx][0].date()),
        "month_start_holes_after_earliest": holes_after,
        "month_probes": len(scan),
        "bisect_probes": probes,
    }


def bybit_full_pull(name: str, symbol: str, raw: Raw, data_dir: Path | None, save: bool) -> dict:
    s = BYBIT_SERIES[name]
    step, limit = s["step"], s["limit"]
    t, t_end = ms(TRAIN1_START), ms(TRAIN1_END_EXCL)
    rows, requests_n, full_pages = [], 0, 0
    while t < t_end:
        t1 = min(t + step * limit, t_end) - 1
        j = bybit_window(s, symbol, t, t1, limit)
        lst = bybit_rows(j)
        if requests_n == 0:
            raw.save(f"bybit/{name}_{symbol}_train1_first_page.json", j)
        requests_n += 1
        full_pages += len(lst) >= limit
        rows += lst
        t = t1 + 1
    df = pd.DataFrame(rows)
    df["timestamp"] = df["timestamp"].astype("int64")
    n_raw = len(df)
    df = df.drop_duplicates("timestamp").sort_values("timestamp")
    expected = np.arange(ms(TRAIN1_START), t_end, step, dtype="int64")
    present = df["timestamp"].to_numpy()
    off_grid = int(np.setdiff1d(present, expected).size)
    gaps = runs_of_missing(expected, present, step)
    out = {
        "requests": requests_n,
        "rows": int(len(df)),
        "duplicates_dropped": int(n_raw - len(df)),
        "expected_bars": int(expected.size),
        "missing_bars": int(sum(g["bars"] for g in gaps)),
        "off_grid_rows": off_grid,
        "gap_runs": len(gaps),
        "gaps_top10_by_length": sorted(gaps, key=lambda g: -g["bars"])[:10],
        "first": iso(present.min()),
        "last": iso(present.max()),
        "fields": [c for c in df.columns],
        "pages_hitting_limit": int(full_pages),
    }
    if "singleOpenInterest" in df.columns:
        ratio = df["openInterest"].astype(float) / df["singleOpenInterest"].astype(float)
        out["openInterest_over_singleOpenInterest"] = {"min": round(float(ratio.min()), 6),
                                                       "max": round(float(ratio.max()), 6)}
        cached = sorted((REPO / "data_cache" / "open_interest").glob(f"{symbol}_oi_1h_*.csv"))
        if cached:
            h = pd.read_csv(cached[0])
            h_ms = pd.to_datetime(h["timestamp"], utc=True).astype("int64") // 10**6
            hs = pd.Series(h["open_interest"].astype(float).to_numpy(), index=h_ms.to_numpy())
            j = pd.concat([hs.rename("h1"), df.set_index("timestamp")["openInterest"].astype(float).rename("m5")],
                          axis=1, join="inner")
            out["vs_cached_1h_oi"] = {"file": str(cached[0].relative_to(REPO)), "matched_hours": int(len(j)),
                                      "exact_equal_frac": round(float(np.isclose(j["h1"], j["m5"], rtol=0, atol=1e-6).mean()), 6),
                                      "max_abs_rel_diff": float((j["h1"] / j["m5"] - 1).abs().max())}
    if save and data_dir is not None:
        sub = "open_interest_5m" if name.startswith("oi") else "account_ratio_5m"
        d = data_dir / sub
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{symbol}_{name}_20240126T000000Z_20250301T000000Z.csv"
        o = df.copy()
        o.insert(0, "time_utc", pd.to_datetime(o["timestamp"], unit="ms", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
        o.to_csv(f, index=False)
        out["saved_to"] = str(f)
        out["saved_bytes"] = f.stat().st_size
    out["_df"] = df
    return out


def bybit_spot_check(name: str, symbol: str, raw: Raw) -> dict:
    """Train-1 first and last day bar counts (used for 15min, which we do not full-pull)."""
    s = BYBIT_SERIES[name]
    per_day = DAY_MS // s["step"]
    res = {}
    for d in (TRAIN1_START, TRAIN1_END_EXCL - timedelta(days=1)):
        j = bybit_window(s, symbol, ms(d), ms(d) + DAY_MS - 1, s["limit"])
        probe = raw.save(f"bybit/{name}_{symbol}_{d.date()}_spot.json", j)
        res[str(d.date())] = {"rows": len(bybit_rows(j)), "expected": per_day, "raw_file": probe}
    return res


# --------------------------------------------------------------------------- 3 Bybit archive
def bybit_archive(symbol: str, raw: Raw) -> dict:
    r = http("GET", f"{BYBIT_ARCHIVE}/{symbol}/")
    names = re.findall(rf'href="({symbol}(\d{{4}}-\d{{2}}-\d{{2}})\.csv\.gz)"', r.text)
    raw.save(f"bybit_archive/{symbol}_listing_head.html", r.text[:3000])
    listed = {date.fromisoformat(d): n for n, d in names}
    days = train1_days()
    missing = [d for d in days if d not in listed]

    def head(d):
        rr = http("HEAD", f"{BYBIT_ARCHIVE}/{symbol}/{listed[d]}")
        return str(d), rr.status_code, int(rr.headers.get("content-length", -1))

    with ThreadPoolExecutor(8) as ex:
        heads = list(ex.map(head, [d for d in days if d in listed]))
    sizes = {d: sz for d, st, sz in heads if st == 200}
    bad = [d for d, st, _ in heads if st != 200]
    raw.save(f"bybit_archive/{symbol}_train1_head_sizes.json", {"status_non200": bad, "sizes": sizes})
    vals = np.array(list(sizes.values()), dtype="int64")
    return {
        "listed_files": len(listed),
        "earliest_listed": str(min(listed)) if listed else None,
        "latest_listed": str(max(listed)) if listed else None,
        "train1_days": len(days),
        "train1_missing_days": missing_day_runs(missing),
        "train1_missing_count": len(missing),
        "head_non200": bad,
        "train1_total_bytes_gz": int(vals.sum()),
        "per_day_bytes_gz": {"min": int(vals.min()), "median": int(np.median(vals)), "max": int(vals.max())},
        "_sizes": sizes,
    }


def download(url: str, dest: Path, expect_size: int | None = None) -> Path:
    if dest.exists() and (expect_size is None or dest.stat().st_size == expect_size):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    r = http("GET", url, stream=True, timeout=120)
    r.raise_for_status()
    with open(tmp, "wb") as fh:
        for chunk in r.iter_content(1 << 20):
            fh.write(chunk)
    os.replace(tmp, dest)
    return dest


def bybit_trades_sample(symbol: str, day: str, data_dir: Path, raw: Raw) -> dict:
    fn = f"{symbol}{day}.csv.gz"
    p = download(f"{BYBIT_ARCHIVE}/{symbol}/{fn}", data_dir / "f011_samples" / "bybit_trading" / fn)
    with gzip.open(p, "rt") as fh:
        head_lines = [next(fh) for _ in range(4)]
    raw.save(f"bybit_archive/{symbol}_{day}_head.csv", "".join(head_lines))
    df = pd.read_csv(p, usecols=["timestamp", "side", "size", "price"])
    ts_unit = "s" if df["timestamp"].max() < 1e11 else "ms"
    t_ms = (df["timestamp"] * (1000 if ts_unit == "s" else 1)).round().astype("int64")
    sides = df["side"].value_counts().to_dict()
    df["bucket"] = (t_ms // 300_000) * 300_000
    buy = df["size"].where(df["side"] == "Buy", 0.0)
    sell = df["size"].where(df["side"] == "Sell", 0.0)
    g = pd.DataFrame({"bucket": df["bucket"], "B": buy, "S": sell, "notional": df["size"] * df["price"]})
    agg = g.groupby("bucket").agg(taker_buy_vol=("B", "sum"), taker_sell_vol=("S", "sum"),
                                  trade_count=("B", "size"), notional=("notional", "sum"))
    agg["ofi"] = (agg["taker_buy_vol"] - agg["taker_sell_vol"]) / (agg["taker_buy_vol"] + agg["taker_sell_vol"])
    agg["cvd"] = (agg["taker_buy_vol"] - agg["taker_sell_vol"]).cumsum()
    agg.index.name = "bucket_ms"
    out_df = agg.reset_index()
    out_df.insert(0, "time_utc", pd.to_datetime(out_df["bucket_ms"], unit="ms", utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
    rel = raw.save(f"bybit_archive/{symbol}_{day}_5m_reconstruction.csv", out_df.to_csv(index=False, float_format="%.6f"))
    return {
        "file": str(p), "bytes_gz": p.stat().st_size, "header": head_lines[0].strip(),
        "rows": int(len(df)), "timestamp_unit": ts_unit,
        "first_trade": iso(t_ms.min()), "last_trade": iso(t_ms.max()),
        "side_values": {k: int(v) for k, v in sides.items()},
        "buckets_5m": int(len(agg)), "reconstruction_csv": rel,
        "day_taker_buy_vol": float(agg["taker_buy_vol"].sum()),
        "day_taker_sell_vol": float(agg["taker_sell_vol"].sum()),
        "_agg": agg,
    }


# --------------------------------------------------------------------------- 4 Binance
def s3_list(prefix: str) -> tuple[list[dict], int, str]:
    keys, marker, pages, first_xml = [], "", 0, ""
    while True:
        r = http("GET", BINANCE_S3, params={"delimiter": "/", "prefix": prefix, "marker": marker})
        r.raise_for_status()
        if not first_xml:
            first_xml = r.text[:4000]
        root = ET.fromstring(r.content)
        pages += 1
        for c in root.findall(f"{S3_NS}Contents"):
            keys.append({"key": c.find(f"{S3_NS}Key").text, "size": int(c.find(f"{S3_NS}Size").text),
                         "last_modified": c.find(f"{S3_NS}LastModified").text})
        trunc = root.find(f"{S3_NS}IsTruncated").text == "true"
        if not trunc:
            break
        nm = root.find(f"{S3_NS}NextMarker")
        marker = nm.text if nm is not None else keys[-1]["key"]
    return keys, pages, first_xml


BINANCE_DATASETS = {
    "metrics": ("data/futures/um/daily/metrics/{s}/", r"{s}-metrics-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", "daily"),
    "klines_5m": ("data/futures/um/daily/klines/{s}/5m/", r"{s}-5m-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", "daily"),
    "aggTrades": ("data/futures/um/daily/aggTrades/{s}/", r"{s}-aggTrades-(\d{{4}}-\d{{2}}-\d{{2}})\.zip$", "daily"),
    "fundingRate_monthly": ("data/futures/um/monthly/fundingRate/{s}/", r"{s}-fundingRate-(\d{{4}}-\d{{2}})\.zip$", "monthly"),
}


def binance_listing(ds: str, symbol: str, raw: Raw) -> dict:
    prefix_t, rx_t, freq = BINANCE_DATASETS[ds]
    prefix = prefix_t.format(s=symbol)
    keys, pages, first_xml = s3_list(prefix)
    raw.save(f"binance/{ds}_{symbol}_listing_page1_head.xml", first_xml)
    rx = re.compile(rx_t.format(s=symbol))
    files = {}
    for k in keys:
        m = rx.search(k["key"])
        if m:
            files[m.group(1)] = k
    checks = sum(1 for k in keys if k["key"].endswith(".CHECKSUM"))
    if freq == "daily":
        want = [str(d) for d in train1_days()]
    else:
        want = sorted({d.strftime("%Y-%m") for d in train1_days()})
    present = [w for w in want if w in files]
    missing = [w for w in want if w not in files]
    sizes = np.array([files[w]["size"] for w in present], dtype="int64")
    raw.save(f"binance/{ds}_{symbol}_train1_listing.json",
             {w: {"size": files[w]["size"], "last_modified": files[w]["last_modified"]} for w in present})
    if freq == "daily":
        miss_fmt = missing_day_runs([date.fromisoformat(x) for x in missing])
    else:
        miss_fmt = missing
    return {
        "prefix": prefix, "listing_pages": pages, "data_files": len(files), "checksum_files": checks,
        "earliest_listed": min(files) if files else None, "latest_listed": max(files) if files else None,
        "train1_expected_files": len(want), "train1_missing": miss_fmt, "train1_missing_count": len(missing),
        "train1_total_bytes_zip": int(sizes.sum()) if sizes.size else 0,
        "per_file_bytes_zip": ({"min": int(sizes.min()), "median": int(np.median(sizes)), "max": int(sizes.max())}
                               if sizes.size else None),
        "_files": files,
    }


def read_zip_csv(p: Path) -> pd.DataFrame:
    with zipfile.ZipFile(p) as z:
        name = z.namelist()[0]
        with z.open(name) as fh:
            return pd.read_csv(fh)


def binance_sample(ds: str, symbol: str, day: str, data_dir: Path, raw: Raw) -> dict:
    if ds == "metrics":
        fn, url_dir = f"{symbol}-metrics-{day}.zip", f"data/futures/um/daily/metrics/{symbol}/"
    else:
        fn, url_dir = f"{symbol}-5m-{day}.zip", f"data/futures/um/daily/klines/{symbol}/5m/"
    p = download(f"{BINANCE_DL}/{url_dir}{fn}", data_dir / "f011_samples" / "binance" / fn)
    df = read_zip_csv(p)
    raw.save(f"binance/{ds}_{symbol}_{day}_head.csv", df.head(5).to_csv(index=False))
    out = {"file": str(p), "bytes_zip": p.stat().st_size, "columns": list(df.columns), "rows": int(len(df))}
    if ds == "metrics":
        t = pd.to_datetime(df["create_time"], utc=True)
        out["first"], out["last"] = str(t.min()), str(t.max())
        step = t.diff().dt.total_seconds().dropna()
        out["step_seconds_mode"] = float(step.mode().iloc[0]) if len(step) else None
        out["null_counts"] = {c: int(v) for c, v in df.isna().sum().items() if v}
    else:
        out["first_open_time"] = iso(df["open_time"].min())
        out["last_open_time"] = iso(df["open_time"].max())
    out["_df"] = df
    return out


def binance_aggtrades_peek(symbol: str, day: str, size: int, raw: Raw) -> dict:
    """Confirm aggTrades columns without downloading the whole (large) zip: Range-read the first
    256 KB, parse the zip local header and inflate the start of the CSV stream."""
    fn = f"{symbol}-aggTrades-{day}.zip"
    url = f"{BINANCE_DL}/data/futures/um/daily/aggTrades/{symbol}/{fn}"
    r = http("GET", url, headers={"Range": "bytes=0-262143"})
    b = r.content
    assert b[:4] == b"PK\x03\x04", "not a zip local header"
    method = int.from_bytes(b[8:10], "little")
    nlen = int.from_bytes(b[26:28], "little")
    xlen = int.from_bytes(b[28:30], "little")
    inner = b[30:30 + nlen].decode()
    data = b[30 + nlen + xlen:]
    text = zlib.decompressobj(-15).decompress(data) if method == 8 else data
    lines = text.decode("utf-8", errors="replace").splitlines()[:6]
    raw.save(f"binance/aggTrades_{symbol}_{day}_head.csv", "\n".join(lines) + "\n")
    return {"url": url, "http_status": r.status_code, "zip_bytes": size, "inner_file": inner,
            "header": lines[0], "first_rows": lines[1:3]}


def binance_funding(symbol: str, files: dict, data_dir: Path, raw: Raw) -> dict:
    frames = []
    for mth in sorted({d.strftime("%Y-%m") for d in train1_days()}):
        if mth not in files:
            continue
        fn = f"{symbol}-fundingRate-{mth}.zip"
        p = download(f"{BINANCE_DL}/data/futures/um/monthly/fundingRate/{symbol}/{fn}",
                     data_dir / "f011_samples" / "binance_funding" / fn)
        frames.append(read_zip_csv(p))
    df = pd.concat(frames, ignore_index=True)
    raw.save(f"binance/fundingRate_{symbol}_head.csv", df.head(5).to_csv(index=False))
    tcol = "calc_time" if "calc_time" in df.columns else df.columns[0]
    t = pd.to_datetime(df[tcol], unit="ms", utc=True).dt.floor("h")
    t = t[(t >= TRAIN1_START) & (t < TRAIN1_END_EXCL)]
    grid = pd.date_range(TRAIN1_START, TRAIN1_END_EXCL, freq="8h", inclusive="left")
    miss = grid.difference(pd.DatetimeIndex(t.unique()))
    return {"columns": list(df.columns), "train1_rows": int(len(t)), "expected_8h_slots": len(grid),
            "missing_8h_slots": len(miss), "missing_examples": [str(x) for x in miss[:10]],
            "first": str(t.min()), "last": str(t.max())}


# --------------------------------------------------------------------------- 5 cached funding
def cached_funding(symbol: str) -> dict:
    cands = sorted((REPO / "data_cache" / "funding").glob(f"{symbol}_funding_*.csv"))
    if not cands:
        return {"found": False}
    p = cands[0]
    df = pd.read_csv(p)
    t = pd.to_datetime(df["timestamp"], utc=True)
    grid = pd.date_range(TRAIN1_START, TRAIN1_END_EXCL, freq="8h", inclusive="left")
    miss = grid.difference(pd.DatetimeIndex(t))
    return {"found": True, "file": str(p.relative_to(REPO)), "rows": int(len(df)),
            "first": str(t.min()), "last": str(t.max()), "expected_8h_slots": len(grid),
            "missing_8h_slots": len(miss), "missing_examples": [str(x) for x in miss[:10]],
            "source": "Bybit /v5/market/funding/history (see data_cache/funding/manifest.json)"}


# --------------------------------------------------------------------------- 6 cross-check
def corr(a, b) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10 or np.std(a[m]) == 0 or np.std(b[m]) == 0:
        return None
    return round(float(np.corrcoef(a[m], b[m])[0, 1]), 4)


def crosscheck(symbol: str, day: str, bybit_oi: pd.DataFrame | None, metrics: pd.DataFrame,
               klines: pd.DataFrame, trades_agg: pd.DataFrame) -> dict:
    d0 = ms(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
    res = {"day": day}
    # OI direction agreement
    if bybit_oi is not None:
        by = bybit_oi[(bybit_oi["timestamp"] >= d0) & (bybit_oi["timestamp"] < d0 + DAY_MS)]
        by = by.set_index("timestamp")["openInterest"].astype(float).sort_index()
        bn_t = pd.to_datetime(metrics["create_time"], utc=True).astype("int64") // 10**6
        bn = pd.Series(metrics["sum_open_interest"].astype(float).to_numpy(), index=bn_t.to_numpy()).sort_index()
        lags = {}
        for lag in (-1, 0, 1):
            b2 = bn.copy()
            b2.index = b2.index + lag * 300_000
            j = pd.concat([by.rename("bybit"), b2.rename("binance")], axis=1, join="inner").sort_index()
            dj = j.diff().dropna()
            nz = dj[(dj["bybit"] != 0) & (dj["binance"] != 0)]
            agree = float((np.sign(nz["bybit"]) == np.sign(nz["binance"])).mean()) if len(nz) else None
            lags[str(lag)] = {"aligned_bars": int(len(j)), "nonzero_diff_pairs": int(len(nz)),
                              "direction_agreement": round(agree, 4) if agree is not None else None,
                              "diff_corr": corr(dj["bybit"], dj["binance"])}
        steps = {}
        jj = pd.concat([by.rename("bybit"), bn.rename("binance")], axis=1, join="inner").sort_index()
        for k in (1, 3, 12):
            dj = jj.iloc[::k].diff().dropna()
            nz = dj[(dj["bybit"] != 0) & (dj["binance"] != 0)]
            steps[f"{5 * k}m"] = {"pairs": int(len(nz)),
                                  "direction_agreement": round(float((np.sign(nz["bybit"]) == np.sign(nz["binance"])).mean()), 4) if len(nz) else None,
                                  "diff_corr": corr(dj["bybit"], dj["binance"])}
        res["oi_change"] = {"bybit_bars": int(len(by)), "binance_bars": int(len(bn)),
                            "by_binance_lag_bars": lags, "lag0_by_diff_step": steps,
                            "note": "lag k shifts Binance create_time by k*5m (timestamp convention check)"}
    # taker flow
    k = klines.copy()
    k = k.set_index("open_time")
    kb = k["taker_buy_volume"].astype(float)
    ks = k["volume"].astype(float) - kb
    t = trades_agg
    j = pd.concat([t["taker_buy_vol"].rename("by_B"), t["taker_sell_vol"].rename("by_S"),
                   t["trade_count"].rename("by_n"), kb.rename("bn_B"), ks.rename("bn_S"),
                   k["count"].astype(float).rename("bn_n")], axis=1, join="inner")
    by_ofi = (j["by_B"] - j["by_S"]) / (j["by_B"] + j["by_S"])
    bn_ofi = (j["bn_B"] - j["bn_S"]) / (j["bn_B"] + j["bn_S"])
    res["taker_flow"] = {
        "aligned_bars": int(len(j)),
        "corr_taker_buy_vol": corr(j["by_B"], j["bn_B"]),
        "corr_taker_sell_vol": corr(j["by_S"], j["bn_S"]),
        "corr_ofi": corr(by_ofi, bn_ofi),
        "ofi_sign_agreement": round(float((np.sign(by_ofi) == np.sign(bn_ofi)).mean()), 4),
        "corr_trade_count": corr(j["by_n"], j["bn_n"]),
        "corr_cvd": corr((j["by_B"] - j["by_S"]).cumsum(), (j["bn_B"] - j["bn_S"]).cumsum()),
        "day_volume_ratio_bybit_over_binance": round(float((j["by_B"] + j["by_S"]).sum() / (j["bn_B"] + j["bn_S"]).sum()), 4),
    }
    return res


# --------------------------------------------------------------------------- report
def strip_private(o):
    if isinstance(o, dict):
        return {k: strip_private(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, list):
        return [strip_private(v) for v in o]
    return o


def mb(n) -> str:
    if n < 1e6:
        return f"{n / 1e3:,.0f} KB"
    return f"{n / 1e6:,.1f} MB" if n < 1e9 else f"{n / 1e9:,.2f} GB"


def build_report(cov: dict) -> str:
    L = []
    L.append("# F011 · Free high-resolution data coverage (Train-1 recon)\n")
    L.append(f"Generated {cov['generated_at']} by `scripts/f011_data_coverage.py` on host "
             f"`{cov['host']}` (all probes run from this host). HTTP requests: {cov['http_requests']}.\n")
    L.append("Train-1 = 2024-01-26T00:00Z .. 2025-02-28T23:00Z → 5m grid [2024-01-26, 2025-03-01) = "
             f"{cov['train1_days']} days × 288 = {cov['train1_days'] * 288} bars per symbol. "
             "Every number below is taken from responses/listings captured in this run "
             "(`coverage.json`, `raw/`).\n")
    if "oi_spot_refresh" in cov:
        refresh = cov["oi_spot_refresh"]
        L.append(f"15min OI spot probes refreshed {refresh['generated_at']} "
                 f"({refresh['http_requests']} additional HTTP requests); other evidence unchanged. "
                 "Each spot count links to its response via `train1_spot_check.*.raw_file` in coverage.json.\n")
    L.append("## Coverage table\n")
    L.append("| source | symbol | earliest (empirical) | Train-1 covered | gaps in Train-1 | resolution | fields | approx. Train-1 size |")
    L.append("|---|---|---|---|---|---|---|---|")
    for row in cov["table"]:
        L.append("| " + " | ".join(str(row[k]) for k in
                 ["source", "symbol", "earliest", "covered", "gaps", "resolution", "fields", "size"]) + " |")
    L.append("")
    L.append("## Bybit 5m OI consistency\n")
    for key, ent in cov["bybit_rest"].items():
        fp = ent.get("train1_full_pull", {})
        if "openInterest_over_singleOpenInterest" in fp:
            r, v = fp["openInterest_over_singleOpenInterest"], fp.get("vs_cached_1h_oi", {})
            L.append(f"- {key}: openInterest / singleOpenInterest in [{r['min']}, {r['max']}] over all "
                     f"{fp['rows']:,} rows; 5m bars at HH:00 vs cached 1h OI (`{v.get('file')}`): "
                     f"{v.get('matched_hours')} hours matched, exact-equal fraction {v.get('exact_equal_frac')}, "
                     f"max |rel diff| {v.get('max_abs_rel_diff')}.")
    L.append("")
    L.append("## Sample-day checks\n")
    for sym, days in cov["bybit_trades_samples"].items():
        for day, s in days.items():
            L.append(f"- Bybit trades {sym} {day}: header `{s['header']}`; {s['rows']:,} trades, "
                     f"timestamp unit `{s['timestamp_unit']}`, sides {s['side_values']}, "
                     f"{s['buckets_5m']} 5m buckets rebuilt (taker_buy_vol, taker_sell_vol, OFI, CVD, "
                     f"trade_count) → `{s['reconstruction_csv']}`.")
    for sym, days in cov["binance_samples"].items():
        for day, s in days.items():
            m, k = s["metrics"], s["klines_5m"]
            L.append(f"- Binance {sym} {day}: metrics {m['rows']} rows (step {m['step_seconds_mode']}s), "
                     f"columns `{', '.join(m['columns'])}`; klines 5m {k['rows']} rows, columns "
                     f"`{', '.join(k['columns'])}`.")
    for sym, s in cov["binance_aggtrades_peek"].items():
        L.append(f"- Binance aggTrades {sym} (range-read, not downloaded): `{s['header']}`, e.g. `{s['first_rows'][0]}`.")
    L.append("")
    L.append("## Cross-check (sanity only)\n")
    L.append("| symbol | day | OI Δ direction agreement 5m lag0 / best lag | OI Δ agree 15m / 1h | OI Δ corr 5m / 15m / 1h | taker-buy corr | taker-sell corr | OFI corr | OFI sign agree | trade-count corr | Bybit/Binance volume |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for x in cov["crosscheck"]:
        oi = x.get("oi_change", {}).get("by_binance_lag_bars", {})
        best = max(oi.items(), key=lambda kv: kv[1]["direction_agreement"] or 0) if oi else None
        tf = x["taker_flow"]
        st = x.get("oi_change", {}).get("lag0_by_diff_step", {})
        L.append(f"| {x['symbol']} | {x['day']} | {oi.get('0', {}).get('direction_agreement')} / "
                 f"{best[1]['direction_agreement'] if best else None} (lag {best[0] if best else None}) | "
                 f"{st.get('15m', {}).get('direction_agreement')} / {st.get('60m', {}).get('direction_agreement')} | "
                 f"{st.get('5m', {}).get('diff_corr')} / {st.get('15m', {}).get('diff_corr')} / {st.get('60m', {}).get('diff_corr')} | {tf['corr_taker_buy_vol']} | {tf['corr_taker_sell_vol']} | "
                 f"{tf['corr_ofi']} | {tf['ofi_sign_agreement']} | {tf['corr_trade_count']} | "
                 f"{tf['day_volume_ratio_bybit_over_binance']} |")
    L.append("")
    L.append("## Funding\n")
    for sym, f in cov["funding_cached"].items():
        L.append(f"- Cached Bybit funding {sym}: `{f.get('file')}` {f.get('rows')} rows {f.get('first')} .. "
                 f"{f.get('last')}; missing 8h slots in Train-1: {f.get('missing_8h_slots')} / {f.get('expected_8h_slots')}.")
    for sym, f in cov["funding_binance"].items():
        L.append(f"- Binance funding {sym} (monthly fundingRate files, downloaded): {f['train1_rows']} rows in "
                 f"Train-1, missing 8h slots {f['missing_8h_slots']} / {f['expected_8h_slots']}; columns `{', '.join(f['columns'])}`.")
    L.append("")
    L.append("## Recommendation\n")
    L.append(cov["recommendation"] + "\n")
    L.append("## Notes / caveats\n")
    for n in cov["notes"]:
        L.append(f"- {n}")
    L.append("")
    return "\n".join(L)


def refresh_oi_spots(out: Path) -> dict:
    """Refresh only the four small 15min probes; reuse all other captured evidence."""
    cov = json.loads((out / "coverage.json").read_text())
    raw = Raw(out / "raw")
    requests_before = REQ_STATS["count"]
    for sym in SYMBOLS:
        ent = cov["bybit_rest"][f"oi_15min/{sym}"]
        spots = bybit_spot_check("oi_15min", sym, raw)
        ent["train1_spot_check"] = spots
        row = next(r for r in cov["table"] if r["source"] == "Bybit REST oi_15min" and r["symbol"] == sym)
        row["gaps"] = "spot: " + ", ".join(f"{d} {v['rows']}/{v['expected']}" for d, v in spots.items())
        row["covered"] = "y (spot)" if all(v["rows"] == v["expected"] for v in spots.values()) and ent["earliest_search"]["earliest_ms"] <= ms(TRAIN1_START) else "check"
    cov["raw_files"] = list(dict.fromkeys(cov["raw_files"] + raw.files))
    cov["oi_spot_refresh"] = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "http_requests": REQ_STATS["count"] - requests_before,
    }
    return cov


def main(argv=None) -> tuple[dict, Path]:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "output" / "f011_forced_flow" / "coverage"))
    ap.add_argument("--data-dir", default=str(REPO / "data_cache"),
                    help="where large pulls / samples go (git-ignored)")
    ap.add_argument("--sample-days", default="2024-06-12,2024-10-01")
    ap.add_argument("--no-full-pull", action="store_true", help="skip full Train-1 Bybit OI/account-ratio pull")
    ap.add_argument("--refresh-oi-spots", action="store_true",
                    help="refresh only the four 15min OI probes in an existing report (no bulk downloads)")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if args.refresh_oi_spots:
        return refresh_oi_spots(out), out
    data_dir = Path(args.data_dir)
    raw = Raw(out / "raw")
    sample_days = [d.strip() for d in args.sample_days.split(",") if d.strip()][:2]
    t_start = time.time()
    cov = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "host": socket.gethostname(), "train1": {"start": TRAIN1_START.isoformat(),
           "end_exclusive": TRAIN1_END_EXCL.isoformat()}, "train1_days": len(train1_days()),
           "sample_days": sample_days}

    def say(msg):
        print(f"[{time.time() - t_start:7.1f}s] {msg}", flush=True)

    # 1+2 Bybit REST
    cov["bybit_rest"] = {}
    pulled = {}
    for name in BYBIT_SERIES:
        for sym in SYMBOLS:
            say(f"bybit {name} {sym}: earliest search")
            e = bybit_earliest(name, sym, raw)
            ent = {"earliest_search": e}
            if name == "oi_15min" or args.no_full_pull:
                ent["train1_spot_check"] = bybit_spot_check(name, sym, raw)
            else:
                say(f"bybit {name} {sym}: full Train-1 pull")
                fp = bybit_full_pull(name, sym, raw, data_dir, save=True)
                pulled[(name, sym)] = fp.pop("_df")
                ent["train1_full_pull"] = fp
            cov["bybit_rest"][f"{name}/{sym}"] = ent

    # 3 Bybit archive
    cov["bybit_archive"], cov["bybit_trades_samples"], aggs = {}, {}, {}
    for sym in SYMBOLS:
        say(f"bybit archive {sym}: listing + HEAD")
        a = bybit_archive(sym, raw)
        a.pop("_sizes")
        cov["bybit_archive"][sym] = a
        cov["bybit_trades_samples"][sym] = {}
        for day in sample_days:
            say(f"bybit trades sample {sym} {day}")
            s = bybit_trades_sample(sym, day, data_dir, raw)
            aggs[(sym, day)] = s.pop("_agg")
            cov["bybit_trades_samples"][sym][day] = s

    # 4 Binance
    cov["binance"], listings = {}, {}
    for ds in BINANCE_DATASETS:
        for sym in SYMBOLS:
            say(f"binance listing {ds} {sym}")
            li = binance_listing(ds, sym, raw)
            listings[(ds, sym)] = li.pop("_files")
            cov["binance"][f"{ds}/{sym}"] = li
    cov["binance_samples"], cov["binance_aggtrades_peek"], bn = {}, {}, {}
    for sym in SYMBOLS:
        cov["binance_samples"][sym] = {}
        for day in sample_days:
            say(f"binance samples {sym} {day}")
            m = binance_sample("metrics", sym, day, data_dir, raw)
            k = binance_sample("klines_5m", sym, day, data_dir, raw)
            bn[(sym, day)] = (m.pop("_df"), k.pop("_df"))
            cov["binance_samples"][sym][day] = {"metrics": m, "klines_5m": k}
        d0 = sample_days[0]
        cov["binance_aggtrades_peek"][sym] = binance_aggtrades_peek(
            sym, d0, listings[("aggTrades", sym)].get(d0, {}).get("size", -1), raw)

    # 5 funding
    cov["funding_cached"] = {sym: cached_funding(sym) for sym in SYMBOLS}
    cov["funding_binance"] = {}
    for sym in SYMBOLS:
        say(f"binance funding {sym}")
        cov["funding_binance"][sym] = binance_funding(sym, listings[("fundingRate_monthly", sym)], data_dir, raw)

    # 6 cross-check
    cov["crosscheck"] = []
    for sym in SYMBOLS:
        oi_df = pulled.get(("oi_5min", sym))
        if oi_df is None:  # --no-full-pull: fetch the sample days directly
            frames = []
            for day in sample_days:
                d0 = ms(datetime.fromisoformat(day).replace(tzinfo=timezone.utc))
                for h in (0, 1):
                    j = bybit_window(BYBIT_SERIES["oi_5min"], sym, d0 + h * DAY_MS // 2, d0 + (h + 1) * DAY_MS // 2 - 1, 200)
                    frames.append(pd.DataFrame(bybit_rows(j)))
            oi_df = pd.concat(frames)
            oi_df["timestamp"] = oi_df["timestamp"].astype("int64")
        for day in sample_days:
            m, k = bn[(sym, day)]
            x = crosscheck(sym, day, oi_df, m, k, aggs[(sym, day)])
            x["symbol"] = sym
            cov["crosscheck"].append(x)

    # table
    table = []
    for key, ent in cov["bybit_rest"].items():
        name, sym = key.split("/")
        e = ent["earliest_search"]
        fp = ent.get("train1_full_pull")
        if fp:
            covered = "y" if fp["first"] == iso(ms(TRAIN1_START)) and fp["missing_bars"] < 0.01 * fp["expected_bars"] else "partial"
            gaps = f"{fp['missing_bars']} missing bars in {fp['gap_runs']} runs (of {fp['expected_bars']})"
            size = f"{mb(fp['saved_bytes'])} CSV ({fp['rows']:,} rows, {fp['requests']} requests)"
        else:
            sc = ent["train1_spot_check"]
            covered = "y (spot)" if all(v["rows"] == v["expected"] for v in sc.values()) and e["earliest_ms"] <= ms(TRAIN1_START) else "check"
            gaps = "spot: " + ", ".join(f"{d} {v['rows']}/{v['expected']}" for d, v in sc.items())
            size = f"~{cov['train1_days'] * (96 if '15' in name else 288):,} rows (est.)"
        fields = {"oi_5min": "openInterest (contracts=base), timestamp",
                  "oi_15min": "openInterest, timestamp",
                  "account_ratio_5min": "buyRatio, sellRatio (share of accounts long/short), timestamp"}[name]
        table.append({"source": f"Bybit REST {name}", "symbol": sym, "earliest": e["earliest"], "covered": covered,
                      "gaps": gaps, "resolution": name.split("_")[-1], "fields": fields, "size": size})
    for sym, a in cov["bybit_archive"].items():
        table.append({"source": "Bybit trade archive (public.bybit.com/trading)", "symbol": sym,
                      "earliest": a["earliest_listed"], "covered": "y" if a["train1_missing_count"] == 0 and not a["head_non200"] else "partial",
                      "gaps": f"{a['train1_missing_count']} missing days" + (f": {a['train1_missing_days']}" if a["train1_missing_days"] else ""),
                      "resolution": "tick (every trade; 5m rebuilt)",
                      "fields": "timestamp(s), side(taker), size, price, tickDirection, trdMatchID, grossValue, homeNotional, foreignNotional",
                      "size": f"{mb(a['train1_total_bytes_gz'])} gz (median {mb(a['per_day_bytes_gz']['median'])}/day)"})
    fields_bn = {"metrics": "sum_open_interest(+value), top-trader & global long/short ratios, taker long/short vol ratio",
                 "klines_5m": "OHLCV, quote_volume, count, taker_buy_volume, taker_buy_quote_volume",
                 "aggTrades": "agg_trade_id, price, quantity, first/last_trade_id, transact_time, is_buyer_maker",
                 "fundingRate_monthly": "calc_time, funding_interval_hours, last_funding_rate"}
    res_bn = {"metrics": "5m", "klines_5m": "5m", "aggTrades": "tick (aggregated trades)", "fundingRate_monthly": "8h"}
    for key, li in cov["binance"].items():
        ds, sym = key.split("/")
        table.append({"source": f"Binance vision {ds}", "symbol": sym, "earliest": li["earliest_listed"],
                      "covered": "y" if li["train1_missing_count"] == 0 else "partial",
                      "gaps": f"{li['train1_missing_count']} missing files" + (f": {li['train1_missing']}" if li["train1_missing"] else ""),
                      "resolution": res_bn[ds], "fields": fields_bn[ds],
                      "size": f"{mb(li['train1_total_bytes_zip'])} zip ({li['train1_expected_files'] - li['train1_missing_count']} files)"})
    for sym, f in cov["funding_cached"].items():
        table.append({"source": "cached Bybit funding (data_cache/funding)", "symbol": sym, "earliest": f.get("first"),
                      "covered": "y" if f.get("missing_8h_slots") == 0 else "partial",
                      "gaps": f"{f.get('missing_8h_slots')} missing 8h slots", "resolution": "8h",
                      "fields": "timestamp, funding_rate", "size": f"{f.get('rows')} rows"})
    cov["table"] = table
    cov["http_requests"] = REQ_STATS["count"]
    cov["recommendation"] = ""  # filled below from the numbers
    cov["notes"] = []
    cov["raw_files"] = raw.files
    cov["runtime_s"] = round(time.time() - t_start, 1)
    return cov, out


def finish(cov: dict, out: Path, recommendation: str, notes: list[str]) -> None:
    cov["recommendation"] = recommendation
    cov["notes"] = notes
    out.mkdir(parents=True, exist_ok=True)
    (out / "coverage.json").write_text(json.dumps(strip_private(cov), indent=1, default=str))
    (out / "report.md").write_text(build_report(cov))


def auto_recommendation(cov: dict) -> tuple[str, list[str]]:
    """Derive the recommendation text from the captured numbers (no hard-coded findings)."""
    def ok(cond):
        return "covered" if cond else "NOT fully covered"
    br = cov["bybit_rest"]
    oi_pulls = [br[f"oi_5min/{s}"].get("train1_full_pull") for s in SYMBOLS]
    ar_pulls = [br[f"account_ratio_5min/{s}"].get("train1_full_pull") for s in SYMBOLS]
    oi_pulled = all(oi_pulls)
    ar_pulled = all(ar_pulls)
    oi_ok = all(br[f"oi_5min/{s}"].get("train1_full_pull", {}).get("missing_bars", 1) == 0 or
                br[f"oi_5min/{s}"].get("train1_full_pull", {}).get("missing_bars", 10**9) < 0.01 * 115200
                for s in SYMBOLS)
    ar_ok = all(br[f"account_ratio_5min/{s}"].get("train1_full_pull", {}).get("missing_bars", 10**9) < 0.01 * 115200
                for s in SYMBOLS)
    tr_ok = all(cov["bybit_archive"][s]["train1_missing_count"] == 0 for s in SYMBOLS)
    bn = cov["binance"]
    m_ok = all(bn[f"metrics/{s}"]["train1_missing_count"] == 0 for s in SYMBOLS)
    k_ok = all(bn[f"klines_5m/{s}"]["train1_missing_count"] == 0 for s in SYMBOLS)
    a_ok = all(bn[f"aggTrades/{s}"]["train1_missing_count"] == 0 for s in SYMBOLS)
    tr_size = sum(cov["bybit_archive"][s]["train1_total_bytes_gz"] for s in SYMBOLS)
    ag_size = sum(bn[f"aggTrades/{s}"]["train1_total_bytes_zip"] for s in SYMBOLS)
    rec = (
        f"**Highest common free resolution over Train-1 is 5m** (tick for flow). Build the 5m frame on "
        f"**Bybit** (same venue as the bot): OI from `/v5/market/open-interest` 5min "
        f"({ok(oi_ok) + '; already pulled to `data_cache/open_interest_5m/`' if oi_pulled else 'full-window coverage unverified; full pull skipped'}), "
        f"long/short account ratio from `/v5/market/account-ratio` "
        f"5min ({ok(ar_ok) if ar_pulled else 'full-window coverage unverified; full pull skipped'}), and taker flow (taker_buy/sell, OFI, CVD, trade_count) rebuilt from the "
        f"`public.bybit.com/trading` tick archive ({ok(tr_ok)}; ~{mb(tr_size)} gz for both symbols). "
        f"Use **Binance data.binance.vision** as the cross-venue / robustness layer: `metrics` 5m "
        f"({ok(m_ok)}; OI, top-trader and global L/S, taker L/S vol ratio) and `klines` 5m with "
        f"taker_buy_volume + count ({ok(k_ok)}) — cheap (tens of MB); `aggTrades` ({ok(a_ok)}, ~{mb(ag_size)}) "
        f"only if Binance tick flow is needed. Funding stays 8h (cached Bybit). Liquidations: no free "
        f"history → live collector only."
    )
    cc = cov["crosscheck"]
    tb = [x["taker_flow"]["corr_taker_buy_vol"] for x in cc]
    ts_ = [x["taker_flow"]["corr_taker_sell_vol"] for x in cc]
    oa = [x["oi_change"]["lag0_by_diff_step"]["5m"]["direction_agreement"] for x in cc if "oi_change" in x]
    oh = [x["oi_change"]["lag0_by_diff_step"]["60m"]["direction_agreement"] for x in cc if "oi_change" in x]
    rec += (f" Caveat: cross-venue 5m OI-change direction agreement on the sample days is only "
            f"{min(oa):.2f}-{max(oa):.2f} (1h: {min(oh):.2f}-{max(oh):.2f}), so Bybit and Binance OI are "
            f"distinct series (treat them as separate features, do not splice/substitute one for the other).")
    notes = [
        f"Taker-side semantics confirmed empirically: Bybit rebuilt 5m taker-buy vs Binance kline taker_buy_volume "
        f"corr {min(tb):.3f}-{max(tb):.3f}, taker-sell corr {min(ts_):.3f}-{max(ts_):.3f} on the sample days.",
        "Bybit OI conventions (from the pulled rows): openInterest/singleOpenInterest ratio range "
        + "; ".join(f"{s}: {br[f'oi_5min/{s}'].get('train1_full_pull', {}).get('openInterest_over_singleOpenInterest', 'unverified (full pull skipped)')}" for s in SYMBOLS)
        + "; cached 1h OI vs 5m openInterest at HH:00 exact-equal fraction "
        + "; ".join(f"{s}: {br[f'oi_5min/{s}'].get('train1_full_pull', {}).get('vs_cached_1h_oi', {}).get('exact_equal_frac', 'unverified')}" for s in SYMBOLS)
        + ". Pick one convention (singleOpenInterest = one-sided) and use it consistently.",
        "Bybit OI/account-ratio retention verified by a 1-day-window probe at every month start since "
        "2018-01, day bisection, intra-day paging and an explicit empty-before check (see earliest_search).",
        "Bybit REST startTime/endTime are both inclusive; pulls use non-overlapping chunks [t, t+limit*step-1] "
        "(see train1_full_pull for duplicates/off-grid counts when a full pull was run).",
        "Bybit trade-archive `side` is the taker side (Buy = aggressive buy); Binance klines "
        "taker_buy_volume is the taker-buy base volume; Binance aggTrades is_buyer_maker=true means taker sell.",
        "Cross-check correlations are a sanity check of reconstruction/alignment only, not a test.",
        "Sample downloads and full pulls are in the main repo data dir (git-ignored), not committed.",
    ]
    return rec, notes


if __name__ == "__main__":
    cov, out = main()
    rec, notes = auto_recommendation(cov)
    finish(cov, out, rec, notes)
    if "oi_spot_refresh" in cov:
        print(f"wrote {out / 'report.md'} and coverage.json "
              f"({cov['oi_spot_refresh']['http_requests']} spot-refresh HTTP requests; other evidence unchanged)")
    else:
        print(f"wrote {out / 'report.md'} and coverage.json ({cov['http_requests']} HTTP requests, {cov['runtime_s']}s)")
