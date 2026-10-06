"""Free-data fetchers for F012-C01 (Coinbase BTC-USD 5m spot, Yahoo daily ETF bars).

Caches under data_cache/f012/c01/ (git-ignored). Idempotent: an existing cache is reused.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

CACHE = Path("data_cache/f012/c01")
UA = {"User-Agent": "Mozilla/5.0 (research; f012-c01)"}
TRAIN1 = ("2024-03-01", "2025-03-01")
# History needed before Train-1 for PIT rolling baselines (Farside starts 2024-01-11).
FETCH_START = "2024-01-11"
FETCH_END = "2025-03-04"
ETFS = ["IBIT", "FBTC", "GBTC", "ARKB", "BITB"]


def coinbase_5m(start: str = FETCH_START, end: str = FETCH_END) -> pd.DataFrame:
    """Coinbase Exchange BTC-USD 5m candles, bar-open UTC timestamps. 300 candles per call."""
    path = CACHE / "coinbase_BTCUSD_5m.csv.gz"
    if path.exists():
        return pd.read_csv(path, parse_dates=["timestamp"])
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    t0, t1 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    step = pd.Timedelta(minutes=5 * 300)
    cur = t0
    while cur < t1:
        nxt = min(cur + step, t1)
        for attempt in range(6):
            r = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/candles",
                             params={"granularity": 300, "start": cur.isoformat(), "end": nxt.isoformat()},
                             headers=UA, timeout=30)
            if r.status_code == 200:
                break
            time.sleep(1.5 * (attempt + 1))
        r.raise_for_status()
        rows.extend(r.json())
        cur = nxt
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["ts", "low", "high", "open", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df.ts, unit="s", utc=True)
    df = (df.drop(columns="ts").drop_duplicates("timestamp").sort_values("timestamp")
          .query("timestamp < @t1")[["timestamp", "open", "high", "low", "close", "volume"]])
    df.to_csv(path, index=False, compression="gzip")
    return pd.read_csv(path, parse_dates=["timestamp"])


def yahoo_daily(ticker: str, start: str = FETCH_START, end: str = FETCH_END) -> pd.DataFrame:
    """Yahoo daily regular-session bars (unadjusted close + volume). Date = US trading date."""
    path = CACHE / f"yahoo_{ticker}_1d.csv"
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    CACHE.mkdir(parents=True, exist_ok=True)
    p1 = int(pd.Timestamp(start, tz="UTC").timestamp())
    p2 = int(pd.Timestamp(end, tz="UTC").timestamp())
    r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                     params={"period1": p1, "period2": p2, "interval": "1d"}, headers=UA, timeout=30)
    r.raise_for_status()
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    ts = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York")
    df = pd.DataFrame({"date": ts.tz_localize(None).normalize(), "open": q["open"], "high": q["high"],
                       "low": q["low"], "close": q["close"], "volume": q["volume"]})
    df.to_csv(path, index=False)
    (CACHE / f"yahoo_{ticker}_1d.meta.json").write_text(json.dumps(
        {"ticker": ticker, "fetched_utc": pd.Timestamp.now(tz="UTC").isoformat(), "rows": len(df)}))
    return pd.read_csv(path, parse_dates=["date"])


if __name__ == "__main__":
    for t in ETFS:
        print(t, len(yahoo_daily(t)))
    print("coinbase", len(coinbase_5m()))
