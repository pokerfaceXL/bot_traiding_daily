"""
F005 wave 1: fetch full available Bybit history for the candidate basket at
4h and 1h, record earliest/latest candle per symbol/interval, and cache the
result through data_contract.build_dataset (checksum + manifest JSON under
data_cache/). Network access to strategy.get_bybit_ohlcv (public kline
endpoint) only -- no trader.py/main.py/configuration/ import, no order
placement, no signal generation, no backtest_engine.run_backtest call.

Rerunning this script is safe: data_contract.save_dataset overwrites the
deterministic cache path for a given (symbol, interval, start, end); wave 2
should instead call data_contract.load_dataset with the exact same
(symbol, interval, start, end) tuples recorded in
spec/research/F005-validation-protocol.md's manifest table so it reads the
pinned cache instead of hitting the network again.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

import data_contract
import strategy

SYMBOLS = ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
INTERVALS = ["240", "60"]  # 4h, 1h
FETCH_LIMIT = 200_000  # far above any realistic history depth; loop stops when Bybit runs out of data


def audit_one(symbol: str, interval: str, now: pd.Timestamp) -> dict:
    raw = strategy.get_bybit_ohlcv(symbol=symbol, interval=interval, limit=FETCH_LIMIT)
    if raw.empty:
        return {
            "symbol": symbol, "interval": interval, "rows_raw": 0,
            "earliest": None, "latest": None, "months": 0.0,
        }
    start = raw.index.min()
    end = raw.index.max()
    usable, manifest = data_contract.build_dataset(
        symbol=symbol, interval=interval, raw_df=raw,
        start=start, end=end, warmup_bars=0, now=now,
        cache_dir="data_cache", allow_gaps=True, persist=True,
    )
    months = (manifest.actual_end - manifest.actual_start).total_seconds() / (3600 * 24 * 30.4375)
    return {
        "symbol": symbol, "interval": interval,
        "rows_raw": len(raw),
        "rows_cached": manifest.row_count,
        "earliest": manifest.actual_start.isoformat(),
        "latest": manifest.actual_end.isoformat(),
        "months": round(months, 2),
        "gaps": len(manifest.gaps),
        "gap_missing_bars": sum(g.missing_bars for g in manifest.gaps),
        "coverage_pct": round(manifest.coverage_pct, 2),
        "checksum_sha256": manifest.checksum_sha256,
    }


def main():
    now = pd.Timestamp.now(tz="UTC")
    results = []
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            print(f"fetching {symbol} {interval} ...", flush=True)
            r = audit_one(symbol, interval, now)
            print(r, flush=True)
            results.append(r)
    with open("data_cache/f005_audit_summary.json", "w") as f:
        json.dump({"generated_at": now.isoformat(), "results": results}, f, indent=2, sort_keys=True)
    print("done, summary written to data_cache/f005_audit_summary.json")


if __name__ == "__main__":
    main()
