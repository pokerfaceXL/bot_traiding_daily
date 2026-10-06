"""Free-data fetchers for F012-R2A (prereg §5). Raw caches under data_cache/f012_r2a/ (git-ignored).

Idempotent: an existing cache file is reused. Every fetcher records the source URL.
"""
from __future__ import annotations

import io
import json
import re
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

CACHE = Path("data_cache/f012_r2a")
UA = {"User-Agent": "Mozilla/5.0 (research; f012-r2a)"}
FETCH_START = "2024-02-20"  # signal windows reach back to the prior session close
FETCH_END = "2025-03-02"
PROSHARES_URL = "https://accounts.profunds.com/etfdata/ByFund/{t}-historical_nav.csv"
BITX_PAGE = "https://www.volatilityshares.com/bitx"
CDX = "http://web.archive.org/cdx/search/cdx"


def _get(url: str, params: dict | None = None, timeout: int = 60, tries: int = 6) -> requests.Response:
    last = None
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            if r.status_code == 200:
                return r
            last = r
        except requests.RequestException as e:  # transient network
            last = e
        time.sleep(2.0 * (attempt + 1))
    raise RuntimeError(f"GET failed {url} {params}: {last}")


# ---------------------------------------------------------------- AUM sources
def proshares_nav(ticker: str) -> pd.DataFrame:
    """ProShares issuer daily history: Date, NAV, Shares Outstanding (000), AUM. Downloaded today."""
    path = CACHE / f"proshares_{ticker}_historical_nav.csv"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(_get(PROSHARES_URL.format(t=ticker)).content)
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    df = df.rename(columns={"NAV": "nav", "Assets Under Management": "aum"})
    df["shares"] = df["Shares Outstanding (000)"] * 1000.0
    return df[["date", "nav", "shares", "aum"]].sort_values("date").reset_index(drop=True)


def wayback_index(url: str, start: str = "20240201", end: str = "20250305") -> pd.DataFrame:
    """All Wayback captures (status 200) of `url` in [start, end]."""
    path = CACHE / ("cdx_" + re.sub(r"\W+", "_", url) + ".json")
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        r = _get(CDX, params={"url": url, "from": start, "to": end, "output": "json",
                              "fl": "timestamp,original,statuscode,digest"}, timeout=120)
        path.write_text(r.text)
    rows = json.loads(path.read_text() or "[]")
    df = pd.DataFrame(rows[1:], columns=rows[0] if rows else ["timestamp", "original", "statuscode", "digest"])
    return df[df.statuscode == "200"].reset_index(drop=True)


def wayback_raw(timestamp: str, url: str) -> tuple[str, str]:
    """Raw archived body and the timestamp Wayback actually served (id_ may redirect to a nearby capture)."""
    path = CACHE / "wayback" / (timestamp + "_" + re.sub(r"\W+", "_", url) + ".html")
    served = path.with_suffix(".served")
    if not path.exists() or not served.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        r = _get(f"http://web.archive.org/web/{timestamp}id_/{url}", timeout=90)
        path.write_bytes(r.content)
        m = re.search(r"/web/(\d{14})id_/", r.url)
        served.write_text(m.group(1) if m else timestamp)
        time.sleep(1.0)
    return path.read_text(errors="ignore"), served.read_text().strip()


BITX_RE = re.compile(r"Net Assets as of (\d{2}/\d{2}/\d{4}) \$([\d,\.]+) NAV \$([\d,\.]+) Shares Outstanding ([\d,]+)")


def parse_bitx_capture(html: str) -> dict | None:
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    m = BITX_RE.search(t)
    if not m:
        return None
    f = lambda s: float(s.replace(",", ""))  # noqa: E731
    return {"as_of": pd.to_datetime(m.group(1), format="%m/%d/%Y"), "net_assets": f(m.group(2)),
            "nav": f(m.group(3)), "shares": f(m.group(4))}


def bitx_wayback() -> pd.DataFrame:
    """Every parseable Train-1 Wayback capture of the BITX issuer page (PIT by capture time)."""
    idx = wayback_index(BITX_PAGE)
    out = []
    for ts in idx.timestamp:
        html, served = wayback_raw(ts, BITX_PAGE)
        rec = parse_bitx_capture(html)
        out.append({"cdx_ts": ts, "served_ts": served,
                    "capture_utc": pd.to_datetime(served, format="%Y%m%d%H%M%S", utc=True),
                    "parsed": rec is not None, **(rec or {})})
    return (pd.DataFrame(out).drop_duplicates("served_ts").sort_values("capture_utc").reset_index(drop=True))


# ---------------------------------------------------------------- prices
def coinbase_5m(product: str = "BTC-USD") -> pd.DataFrame:
    """Coinbase Exchange 5m candles (bar-open UTC). 300 per call."""
    path = CACHE / f"coinbase_{product}_5m.csv.gz"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        rows, cur = [], pd.Timestamp(FETCH_START, tz="UTC")
        t1, step = pd.Timestamp(FETCH_END, tz="UTC"), pd.Timedelta(minutes=5 * 300)
        while cur < t1:
            nxt = min(cur + step, t1)
            r = _get(f"https://api.exchange.coinbase.com/products/{product}/candles",
                     params={"granularity": 300, "start": cur.isoformat(), "end": nxt.isoformat()}, timeout=30)
            rows.extend(r.json())
            cur = nxt
            time.sleep(0.15)
        df = pd.DataFrame(rows, columns=["ts", "low", "high", "open", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df.ts, unit="s", utc=True)
        df = (df.drop(columns="ts").drop_duplicates("timestamp").sort_values("timestamp")
              .query("timestamp < @t1")[["timestamp", "open", "high", "low", "close", "volume"]])
        df.to_csv(path, index=False, compression="gzip")
    return pd.read_csv(path, parse_dates=["timestamp"])


def bybit_5m(symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Bybit v5 public kline, linear, 5m (bar-open UTC). volume = base, turnover = USDT."""
    path = CACHE / f"bybit_{symbol}_5m.csv.gz"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        rows, cur = [], pd.Timestamp(FETCH_START, tz="UTC")
        t1, step = pd.Timestamp(FETCH_END, tz="UTC"), pd.Timedelta(minutes=5 * 1000)
        while cur < t1:
            nxt = min(cur + step, t1)
            r = _get("https://api.bybit.com/v5/market/kline",
                     params={"category": "linear", "symbol": symbol, "interval": "5",
                             "start": int(cur.timestamp() * 1000), "end": int(nxt.timestamp() * 1000) - 1,
                             "limit": 1000}, timeout=30)
            rows.extend(r.json()["result"]["list"])
            cur = nxt
            time.sleep(0.12)
        df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume", "turnover"])
        df["timestamp"] = pd.to_datetime(df.ts.astype("int64"), unit="ms", utc=True)
        df = df.drop(columns="ts").astype({c: float for c in ["open", "high", "low", "close", "volume", "turnover"]})
        df = df.drop_duplicates("timestamp").sort_values("timestamp")
        df[["timestamp", "open", "high", "low", "close", "volume", "turnover"]].to_csv(path, index=False, compression="gzip")
    return pd.read_csv(path, parse_dates=["timestamp"])


def binance_um_5m(symbol: str = "BTCUSDT") -> pd.DataFrame:
    """Binance USD-M futures monthly 5m klines from data.binance.vision (quote_volume in USDT)."""
    path = CACHE / f"binance_um_{symbol}_5m.csv.gz"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        frames = []
        for m in pd.period_range(FETCH_START[:7], "2025-02", freq="M"):
            url = (f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/"
                   f"{symbol}-5m-{m.strftime('%Y-%m')}.zip")
            z = zipfile.ZipFile(io.BytesIO(_get(url, timeout=120).content))
            raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
            if not str(raw.iloc[0, 0]).isdigit():
                raw = raw.iloc[1:]
            frames.append(raw.iloc[:, [0, 1, 4, 7]])
        df = pd.concat(frames)
        df.columns = ["ts", "open", "close", "quote_volume"]
        df["timestamp"] = pd.to_datetime(df.ts.astype("int64"), unit="ms", utc=True)
        df = df.drop(columns="ts").astype(float, errors="ignore").drop_duplicates("timestamp").sort_values("timestamp")
        df[["timestamp", "open", "close", "quote_volume"]].to_csv(path, index=False, compression="gzip")
    return pd.read_csv(path, parse_dates=["timestamp"])


def yahoo_daily(ticker: str) -> pd.DataFrame:
    """Yahoo daily bars, used only to cross-check the NYSE session calendar."""
    path = CACHE / f"yahoo_{ticker}_1d.csv"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        p1 = int(pd.Timestamp("2024-03-01", tz="UTC").timestamp())
        p2 = int(pd.Timestamp("2025-03-01", tz="UTC").timestamp())
        r = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                 params={"period1": p1, "period2": p2, "interval": "1d"}, timeout=30)
        res = r.json()["chart"]["result"][0]
        ts = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York")
        pd.DataFrame({"date": ts.tz_localize(None).normalize(),
                      "close": res["indicators"]["quote"][0]["close"]}).to_csv(path, index=False)
    return pd.read_csv(path, parse_dates=["date"])
