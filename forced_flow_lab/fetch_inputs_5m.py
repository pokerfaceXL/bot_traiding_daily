"""Fetch the small, free Plan-C inputs; never read or write liquidation data.

Trade archives are handled only by reduce_trades_5m. Binance archives here are
small daily metrics/kline ZIPs, held in memory, not aggTrades or raw tick files.
"""
from __future__ import annotations

import argparse
import io
import json
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

from data_contract import build_manifest, load_dataset, save_dataset
from forced_flow_lab.build_frame_5m import START, END, TAG, grid
from forced_flow_lab.reduce_trades_5m import DiskGuard, SYMBOLS, atomic_write, sha256

BYBIT = "https://api.bybit.com/v5/market"
BINANCE = "https://data.binance.vision/data/futures/um/daily"
KLINE_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume", "close_time",
                 "quote_volume", "trade_count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def get(session, url, params=None):
    for attempt in range(5):
        try:
            response = session.get(url, params=params, timeout=(15, 60))
            response.raise_for_status()
            return response
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)


def publish(path, frame, source):
    guard = DiskGuard(path.parent)
    atomic_write(path, frame.to_csv(index=True).encode(), guard)
    metadata = {"source": source, "sha256": sha256(path), "rows": len(frame),
                "retrieved_at": pd.Timestamp.now(tz="UTC").isoformat()}
    atomic_write(path.with_suffix(".source.json"), (json.dumps(metadata, indent=2) + "\n").encode(), guard)


def cached(path):
    try:
        return json.loads(path.with_suffix(".source.json").read_text())["sha256"] == sha256(path)
    except (OSError, ValueError, KeyError):
        return False


def bybit_klines(session, symbol, interval):
    step = pd.Timedelta(minutes=int(interval))
    records = []
    start = START
    while start < END:
        stop = min(start + 1000 * step, END)
        params = {"category": "linear", "symbol": symbol, "interval": interval,
                  "start": start.value // 10**6, "end": stop.value // 10**6 - 1, "limit": 1000}
        payload = get(session, f"{BYBIT}/kline", params).json()
        if payload.get("retCode") != 0:
            raise ValueError(f"Bybit kline error: {payload}")
        records.extend(payload["result"]["list"])
        start = stop
        time.sleep(0.04)
    frame = pd.DataFrame(records, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    frame.index = pd.DatetimeIndex(pd.to_datetime(frame.pop("timestamp").astype("int64"), unit="ms", utc=True), name="timestamp")
    frame = frame.astype(float).sort_index()
    expected = pd.date_range(START, END, freq=step, inclusive="left", name="timestamp")
    if not frame.index.equals(expected):
        raise ValueError(f"Incomplete/duplicate Bybit {interval}m OHLCV: {symbol}")
    return frame


def binance_day(session, symbol, kind, day):
    stamp = str(day.date())
    # Authoritative keys (scripts/f011_data_coverage.py BINANCE_DATASETS):
    # klines/{s}/5m/{s}-5m-{date}.zip, metrics/{s}/{s}-metrics-{date}.zip
    if kind == "klines":
        url = f"{BINANCE}/klines/{symbol}/5m/{symbol}-5m-{stamp}.zip"
    else:
        url = f"{BINANCE}/metrics/{symbol}/{symbol}-metrics-{stamp}.zip"
    response = get(session, url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        members = archive.namelist()
        if len(members) != 1:
            raise ValueError(f"Unexpected ZIP members: {url}")
        with archive.open(members[0]) as fh:
            frame = pd.read_csv(fh)
    if kind == "klines":
        if list(frame.columns)[0] != "open_time":
            # Binance historical files may have no header.
            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                with archive.open(members[0]) as fh:
                    frame = pd.read_csv(fh, header=None)
        frame.columns = KLINE_COLUMNS
        frame.index = pd.DatetimeIndex(pd.to_datetime(frame.pop("timestamp"), unit="ms", utc=True), name="timestamp")
        frame = frame.drop(columns=["close_time", "ignore"])
    else:
        if not frame.symbol.eq(symbol).all():
            raise ValueError(f"Wrong Binance symbol: {url}")
        frame.index = pd.DatetimeIndex(pd.to_datetime(frame.pop("create_time"), utc=True), name="timestamp")
        frame = frame.drop(columns="symbol")
    frame = frame.astype(float).sort_index()
    if frame.index.has_duplicates:
        raise ValueError(f"Duplicate Binance {kind}: {symbol} {day}")
    return frame, url


def fetch(cache: Path, reuse_cache: Path | None):
    root = cache / "frame_5m_inputs"
    root.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        for symbol in SYMBOLS:
            # Existing Plan-C full pulls and cached funding/hourly OI are inputs,
            # copied explicitly: no recursive copying of data_cache/liquidations.
            relatives = [
                Path("open_interest_5m") / f"{symbol}_oi_5min_{TAG}.csv",
                Path("account_ratio_5m") / f"{symbol}_account_ratio_5min_{TAG}.csv",
                Path("funding") / f"{symbol}_funding_{TAG}.csv",
                Path("open_interest") / f"{symbol}_oi_1h_{TAG}.csv",
            ]
            for relative in relatives:
                path = cache / relative
                if not path.exists():
                    if reuse_cache is None:
                        raise FileNotFoundError(f"Missing verified coverage input {path}; pass --reuse-cache")
                    path.parent.mkdir(parents=True, exist_ok=True)
                    atomic_write(path, (reuse_cache / relative).read_bytes(), DiskGuard(path.parent))
            ohlcv = root / f"{symbol}_ohlcv.csv"
            if not cached(ohlcv):
                publish(ohlcv, bybit_klines(session, symbol, "5"), f"{BYBIT}/kline?symbol={symbol}&interval=5&category=linear")
            # Existing hourly causality tests require the standard data-contract
            # cache. Reuse the verified cache if present, else fetch through the
            # established contract format (a skip would break those tests).
            hourly = cache / f"{symbol}_60_{TAG}.csv"
            manifest_path = hourly.with_name(f"{symbol}_60_{TAG}.manifest.json")
            if not hourly.exists() and reuse_cache is not None and (reuse_cache / hourly.name).exists():
                for name in (hourly.name, manifest_path.name):
                    atomic_write(cache / name, (reuse_cache / name).read_bytes(), DiskGuard(cache))
            if not hourly.exists():
                frame = bybit_klines(session, symbol, "60")
                manifest = build_manifest(symbol, "60", frame, START, END)
                DiskGuard(cache).check(len(frame.to_csv().encode()) + 16384)
                save_dataset(str(cache), symbol, "60", START, END, frame, manifest)
            load_dataset(str(cache), symbol, "60", START, END)
            for kind in ("metrics", "klines"):
                combined = root / f"{symbol}_{kind}.csv"
                if cached(combined):
                    continue
                daily = root / f"{symbol}_{kind}"
                daily.mkdir(exist_ok=True)
                pieces = []
                for day in pd.date_range(START, END, freq="D", inclusive="left"):
                    path = daily / f"{day.date()}.csv"
                    if not cached(path):
                        frame, url = binance_day(session, symbol, kind, day)
                        publish(path, frame, url)
                    pieces.append(pd.read_csv(path, index_col=0, parse_dates=True))
                frame = pd.concat(pieces).sort_index()
                if frame.index.has_duplicates:
                    raise ValueError(f"Duplicate combined {symbol} {kind}")
                publish(combined, frame, {"daily_manifests": str(daily), "base_url": BINANCE})
            print(json.dumps({"symbol": symbol, "status": "inputs-cached"}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))
    parser.add_argument("--reuse-cache", type=Path)
    args = parser.parse_args()
    fetch(args.cache_dir, args.reuse_cache)


if __name__ == "__main__":
    main()
