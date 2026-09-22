"""
F005 wave 1: build the exact pinned dataset the frozen protocol
(spec/research/F005-validation-protocol.md) is defined against, by re-slicing
the already-fetched full-history cache (data_cache/, written by
f005_fetch_audit_data.py) -- no network access here, no new Bybit calls.

Scoped range per symbol/interval: warmup_start (35 calendar days before
Train1 start, for indicator warm-up) through holdout_end (protocol holdout
window end). Writes a second, narrower cache entry via
data_contract.build_dataset so wave 2 can data_contract.load_dataset(...)
this exact (symbol, interval, warmup_start, holdout_end) tuple and get
byte-identical data to what this protocol was written against (checksum
verified on load).
"""
from __future__ import annotations

import glob
import json
import os
import re

import pandas as pd

import data_contract

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]

TRAIN1_START = pd.Timestamp("2024-03-01T00:00:00Z")
HOLDOUT_END = pd.Timestamp("2026-09-01T00:00:00Z")
WARMUP_START = pd.Timestamp("2024-01-26T00:00:00Z")  # 35 calendar days before TRAIN1_START
WARMUP_BARS = {"240": 210, "60": 840}  # 35 days worth of bars at each interval

_NAME_RE = re.compile(r"^(?P<symbol>[A-Z0-9]+)_(?P<interval>\d+)_(?P<start>\d{8}T\d{6}Z)_(?P<end>\d{8}T\d{6}Z)\.csv$")


def _full_range_from_cache(cache_dir: str, symbol: str, interval: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Recover the exact (start, end) pd.Timestamp pair f005_fetch_audit_data.py
    saved this symbol/interval's full-history cache under, by parsing the
    deterministic filename data_contract.save_dataset wrote -- avoids any
    risk of re-deriving a slightly different Timestamp that would miss the
    on-disk cache (data_contract.load_dataset matches on exact filename)."""
    matches = []
    for path in glob.glob(os.path.join(cache_dir, f"{symbol}_{interval}_*.csv")):
        m = _NAME_RE.match(os.path.basename(path))
        if m:
            matches.append(m)
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one full-history cache file for {symbol}/{interval}, found {len(matches)}")
    m = matches[0]
    fmt = "%Y%m%dT%H%M%SZ"
    start = pd.Timestamp(pd.to_datetime(m.group("start"), format=fmt), tz="UTC")
    end = pd.Timestamp(pd.to_datetime(m.group("end"), format=fmt), tz="UTC")
    return start, end


def main():
    results = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            full_start, full_end = _full_range_from_cache("data_cache", symbol, interval)
            full_df, _full_manifest = data_contract.load_dataset(
                "data_cache", symbol, interval, full_start, full_end,
            )
            usable, manifest = data_contract.build_dataset(
                symbol=symbol, interval=interval, raw_df=full_df,
                start=WARMUP_START, end=HOLDOUT_END,
                warmup_bars=WARMUP_BARS[interval], now=None,
                cache_dir="data_cache", allow_gaps=False, persist=True,
            )
            r = {
                "symbol": symbol, "interval": interval,
                "warmup_start": manifest.actual_start.isoformat(),
                "holdout_end_requested": HOLDOUT_END.isoformat(),
                "actual_end": manifest.actual_end.isoformat(),
                "row_count_incl_warmup": manifest.row_count,
                "warmup_bars": manifest.warmup_bars,
                "usable_row_count": len(usable),
                "coverage_pct": round(manifest.coverage_pct, 2),
                "gaps": len(manifest.gaps),
                "checksum_sha256": manifest.checksum_sha256,
            }
            print(r, flush=True)
            results.append(r)
    with open("data_cache/f005_protocol_scoped_manifest.json", "w") as f:
        json.dump({"results": results}, f, indent=2, sort_keys=True)
    print("done")


if __name__ == "__main__":
    main()
