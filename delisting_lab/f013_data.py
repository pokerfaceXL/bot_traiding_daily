"""F013 market data per discovery event (fresh download; C02 caches are gone).

Cache: data_cache/f013/events/<event_id>/ (git-ignored). Disk-safe: archives are parsed in
memory or a temp file that is deleted right after aggregation; only compact frames are kept.

Per event (P = first_publicly_observable_ts, eff = effective_ts):
- perp_1m : [P - 73 h, eff + 1 m] 1m OHLC + quote volume (+ trade count on Binance).
            Binance fapi REST klines; Bybit v5 REST kline (both serve delisted symbols).
- ticks   : trades in [P, P + 10 m] (Gate B sub-minute entries; Gate C first trade).
            Binance vision aggTrades; Bybit public trade archive.
- perp_1h : [P - 21 d, P] 1h closes (Gate G beta over [P - 20 d, P - 24 h]).
- funding : [P - 1 d, eff + 1 d] settled funding rates.
- spot_1m : same-token spot 1m over [P - 25 h, min(P + 80 h, eff) ] — same venue first,
            else the other venue (Binance spot REST → spot vision daily; Bybit spot REST).
Global: BTCUSDT perp 1m closes/opens (Binance vision monthly) for Gate G.
"""
from __future__ import annotations

import io
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from delisting_lab.market_data import KL_COLS, _days

ROOT = Path("data_cache/f013")
EV = ROOT / "events"
TMP = ROOT / "tmp"
H = {"User-Agent": "Mozilla/5.0"}
MIN_FREE_GB = 8.0
M1 = pd.Timedelta(minutes=1)


def free_gb() -> float:
    return shutil.disk_usage(".").free / 1e9


def _get(url, params=None, tries=5):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code in (400, 404):
                return None
            if r.status_code in (418, 429):
                time.sleep(30)
        except requests.RequestException:
            pass
        time.sleep(2 * (k + 1))
    return None


def _ms(t: pd.Timestamp) -> int:
    return int(t.timestamp() * 1000)


# ------------------------------------------------------------------ REST klines
def binance_rest_klines(sym, lo, hi, interval="1m", base="https://fapi.binance.com/fapi/v1/klines"):
    step = {"1m": 60_000, "1h": 3_600_000}[interval]
    rows, start, end = [], _ms(lo), _ms(hi)
    while start < end:
        r = _get(base, {"symbol": sym, "interval": interval, "startTime": start, "endTime": end, "limit": 1000})
        lst = r.json() if r is not None else []
        if not lst:
            break
        rows += lst
        start = lst[-1][0] + step
        time.sleep(0.12)
    if not rows:
        return None
    k = pd.DataFrame(rows, columns=KL_COLS)
    k.index = pd.to_datetime(k.open_time.astype("int64"), unit="ms", utc=True)
    out = pd.DataFrame({c: pd.to_numeric(k[c]) for c in ("open", "high", "low", "close", "quote_volume", "count")})
    return out.sort_index()[~out.index.duplicated()]


def bybit_rest_klines(sym, lo, hi, interval="1", category="linear"):
    step = {"1": 60_000, "60": 3_600_000}[interval]
    rows, start, end = [], _ms(lo), _ms(hi)
    while start < end:
        stop = min(end, start + 1000 * step - 1)
        r = _get("https://api.bybit.com/v5/market/kline", {"category": category, "symbol": sym, "interval": interval,
                                                           "start": start, "end": stop, "limit": 1000})
        res = (r.json().get("result") or {}) if r is not None else {}
        rows += res.get("list", []) or []
        start = stop + 1
        time.sleep(0.05)
    if not rows:
        return None
    k = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume", "turnover"]).astype(float)
    k.index = pd.to_datetime(k.t.astype("int64"), unit="ms", utc=True)
    k = k.sort_index()[~k.index.duplicated()]
    out = k.rename(columns={"turnover": "quote_volume"})[["open", "high", "low", "close", "quote_volume"]].copy()
    out["count"] = np.where(k.volume > 0, np.nan, 0.0)  # Bybit REST has no trade count: 0 iff no volume
    return out


def vision_zip(path: str, cols=None) -> pd.DataFrame | None:
    r = _get("https://data.binance.vision/data/" + path)
    if r is None:
        return None
    z = zipfile.ZipFile(io.BytesIO(r.content))
    raw = z.read(z.namelist()[0])
    header = 0 if raw[:1].decode(errors="ignore").isalpha() else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    if header is None and cols is not None:
        df.columns = cols[: df.shape[1]]
    return df


def binance_vision_klines(sym, lo, hi, market="spot", interval="1m"):
    parts = [vision_zip(f"{market}/daily/klines/{sym}/{interval}/{sym}-{interval}-{d}.zip", KL_COLS)
             for d in _days(lo, hi)]
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    k = pd.concat(parts)
    ot = pd.to_numeric(k.open_time)
    k.index = pd.to_datetime(ot, unit="us" if ot.max() > 1e14 else "ms", utc=True)
    out = pd.DataFrame({c: pd.to_numeric(k[c]) for c in ("open", "high", "low", "close", "quote_volume", "count")})
    out = out.sort_index()[~out.index.duplicated()]
    return out[(out.index >= lo) & (out.index <= hi)]


def binance_perp(sym, lo, hi, interval="1m"):
    """fapi REST first; vision daily klines when REST no longer serves the symbol / window."""
    k = binance_rest_klines(sym, lo, hi, interval=interval)
    if k is None or k.index.min() > lo + pd.Timedelta(hours=2) or k.index.max() < hi - pd.Timedelta(hours=2):
        v = binance_vision_klines(sym, lo, hi, market="futures/um", interval=interval)
        if v is not None and (k is None or len(v) > len(k)):
            return v
    return k


# ------------------------------------------------------------------ ticks
def binance_ticks(sym, lo, hi):
    parts = []
    for d in _days(lo, hi):
        a = vision_zip(f"futures/um/daily/aggTrades/{sym}/{sym}-aggTrades-{d}.zip",
                       ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time",
                        "is_buyer_maker"])
        if a is None:
            continue
        t = pd.DataFrame({"ts": pd.to_datetime(pd.to_numeric(a.transact_time), unit="ms", utc=True),
                          "price": pd.to_numeric(a.price), "size": pd.to_numeric(a.quantity)})
        parts.append(t[(t.ts >= lo) & (t.ts <= hi)])
    return pd.concat(parts).sort_values("ts").reset_index(drop=True) if parts else None


def bybit_ticks(sym, lo, hi):
    parts = []
    TMP.mkdir(parents=True, exist_ok=True)
    for d in _days(lo, hi):
        if free_gb() < MIN_FREE_GB:
            raise RuntimeError(f"disk floor ({free_gb():.1f} GB)")
        r = _get(f"https://public.bybit.com/trading/{sym}/{sym}{d}.csv.gz")
        if r is None:
            continue
        f = TMP / f"{sym}{d}.csv.gz"
        f.write_bytes(r.content)
        try:
            a = pd.read_csv(f, usecols=["timestamp", "price", "size"])
        finally:
            f.unlink(missing_ok=True)
        t = pd.DataFrame({"ts": pd.to_datetime((a.timestamp * 1000).round().astype("int64"), unit="ms", utc=True),
                          "price": a.price.astype(float), "size": a["size"].astype(float)})
        parts.append(t[(t.ts >= lo) & (t.ts <= hi)])
    return pd.concat(parts).sort_values("ts").reset_index(drop=True) if parts else None


# ------------------------------------------------------------------ funding
def funding(ex, sym, lo, hi):
    rows = []
    if ex == "bybit":
        end, start = _ms(hi), _ms(lo)
        while end > start:
            r = _get("https://api.bybit.com/v5/market/funding/history",
                     {"category": "linear", "symbol": sym, "startTime": start, "endTime": end, "limit": 200})
            lst = (r.json().get("result") or {}).get("list", []) if r is not None else []
            if not lst:
                break
            rows += [(int(x["fundingRateTimestamp"]), float(x["fundingRate"])) for x in lst]
            new_end = min(int(x["fundingRateTimestamp"]) for x in lst) - 1
            if new_end >= end:
                break
            end = new_end
    else:
        start = _ms(lo)
        while start < _ms(hi):
            r = _get("https://fapi.binance.com/fapi/v1/fundingRate",
                     {"symbol": sym, "startTime": start, "endTime": _ms(hi), "limit": 1000})
            lst = r.json() if r is not None else []
            if not lst:
                break
            rows += [(int(x["fundingTime"]), float(x["fundingRate"])) for x in lst]
            if len(lst) < 1000:
                break
            start = int(lst[-1]["fundingTime"]) + 1
    if not rows:
        return None
    f = pd.DataFrame(rows, columns=["t", "rate"]).drop_duplicates("t")
    f.index = pd.to_datetime(f.t, unit="ms", utc=True)
    return f[["rate"]].sort_index()


# ------------------------------------------------------------------ per event
def _save(df, p: Path):
    if df is not None and len(df):
        df.to_pickle(p, compression="gzip")


def load(eid: str, name: str):
    p = EV / eid / f"{name}.pkl.gz"
    return pd.read_pickle(p) if p.exists() else None


def spot_1m(ex, base, lo, hi):
    sym = base + "USDT"
    order = ["binance", "bybit"] if ex == "binance" else ["bybit", "binance"]
    for v in order:
        if v == "binance":
            s = binance_rest_klines(sym, lo, hi, base="https://api.binance.com/api/v3/klines")
            if s is None or s.index.min() > lo + pd.Timedelta(hours=2):
                s = binance_vision_klines(sym, lo, hi)
        else:
            s = bybit_rest_klines(sym, lo, hi, category="spot")
        if s is not None and len(s):
            return s, f"{v}_spot"
    return None, None


def build_event(ev, force=False) -> dict:
    d = EV / ev.event_id
    flag = d / "done.json"
    if flag.exists() and not force:
        info = json.loads(flag.read_text())
        if info.get("has_perp_1m"):
            return info
    if free_gb() < MIN_FREE_GB:
        raise RuntimeError(f"disk floor ({free_gb():.1f} GB)")
    d.mkdir(parents=True, exist_ok=True)
    P, eff, sym, ex = ev.P, ev.effective_ts, ev.symbol, ev.exchange
    lo1m, hi1m = P - pd.Timedelta(hours=73), eff + M1
    if ex == "binance":
        bars = binance_perp(sym, lo1m, hi1m)
        h1 = binance_perp(sym, P - pd.Timedelta(days=21), P, interval="1h")
        ticks = binance_ticks(sym, P, P + pd.Timedelta(minutes=10))
    else:
        bars = bybit_rest_klines(sym, lo1m, hi1m)
        h1 = bybit_rest_klines(sym, P - pd.Timedelta(days=21), P, interval="60")
        ticks = bybit_ticks(sym, P, P + pd.Timedelta(minutes=10))
    _save(bars, d / "perp_1m.pkl.gz")
    _save(h1, d / "perp_1h.pkl.gz")
    _save(ticks, d / "ticks.pkl.gz")
    _save(funding(ex, sym, P - pd.Timedelta(days=1), eff + pd.Timedelta(days=1)), d / "funding.pkl.gz")
    sp, venue = spot_1m(ex, ev.base, P - pd.Timedelta(hours=25), min(P + pd.Timedelta(hours=80), eff + M1))
    _save(sp, d / "spot_1m.pkl.gz")
    info = {"event_id": ev.event_id, "spot_venue": venue}
    for n in ("perp_1m", "perp_1h", "ticks", "funding", "spot_1m"):
        info[f"has_{n}"] = (d / f"{n}.pkl.gz").exists()
    flag.write_text(json.dumps(info))
    return info


def btc_1m(lo="2024-02-01", hi="2025-04-30") -> pd.DataFrame:
    p = ROOT / "BTCUSDT_1m.pkl.gz"
    if p.exists():
        return pd.read_pickle(p)
    parts = []
    for m in pd.date_range(lo, hi, freq="MS"):
        df = vision_zip(f"futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{m:%Y-%m}.zip", KL_COLS)
        df.index = pd.to_datetime(pd.to_numeric(df.open_time), unit="ms", utc=True)
        parts.append(pd.DataFrame({"open": pd.to_numeric(df.open), "close": pd.to_numeric(df.close)}))
    b = pd.concat(parts).sort_index()
    b = b[~b.index.duplicated()]
    ROOT.mkdir(parents=True, exist_ok=True)
    b.to_pickle(p, compression="gzip")
    return b


if __name__ == "__main__":
    from delisting_lab.f013_sample import load_events

    evs = load_events(include_excluded=True)
    btc_1m()
    only = set(sys.argv[1:])
    for _, ev in evs.iterrows():
        if only and ev.symbol not in only:
            continue
        t0 = time.time()
        try:
            info = build_event(ev)
        except Exception as e:  # keep going; reported as missing
            info = {"event_id": ev.event_id, "error": repr(e)[:200]}
        print(f"{ev.event_id} {time.time() - t0:.0f}s free={free_gb():.1f}GB {info}", flush=True)
