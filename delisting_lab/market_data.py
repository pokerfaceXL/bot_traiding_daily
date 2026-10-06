"""Survivorship-safe market data per delisting event (disk-safe: download → aggregate → delete).

Per perp event we build and cache (data_cache/f012_c02/events/<event_id>/):
- perp_1m.pkl.gz  : 1m OHLCV + taker buy/sell quote volume + trade count, [ann-1d, end]
                    Bybit: public.bybit.com/trading tick archive (taker side) aggregated.
                    Binance: data.binance.vision futures/um daily 1m klines.
- ticks_ann.pkl.gz: tick trades in [ann-10m, obs+2h] (sub-minute latency entries).
- perp_1h.pkl.gz  : 1h closes for pre-window [ann-21d, ann-1d] (beta, pre-trend, placebo).
- oi.pkl.gz       : open interest (Bybit REST 5min / Binance metrics 5m), [ann-3d, end].
- funding.pkl.gz  : funding history.
- spot_1m.pkl.gz  : same-token spot 1m (Binance spot vision klines preferred; Bybit spot
                    archive fallback), with `spot_venue` recorded.
where end = max(effective_ts, ann+72h) + 1h.
"""
from __future__ import annotations

import gzip
import io
import json
import shutil
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path("data_cache/f012_c02")
EV = ROOT / "events"
TMP = ROOT / "tmp"
H = {"User-Agent": "Mozilla/5.0"}
MIN_FREE_GB = 15.0
KL_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume",
           "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]


def free_gb() -> float:
    return shutil.disk_usage(".").free / 1e9


def _get(url, params=None, tries=5, ok404=True):
    for k in range(tries):
        try:
            r = requests.get(url, params=params, headers=H, timeout=60)
            if r.status_code == 200:
                return r
            if r.status_code == 404 and ok404:
                return None
        except requests.RequestException:
            pass
        time.sleep(3 * (k + 1))
    return None


def _days(lo: pd.Timestamp, hi: pd.Timestamp) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in pd.date_range(lo.floor("D"), hi.floor("D"), freq="D")]


# ---------------------------------------------------------------- Bybit perp trades
def bybit_trades_day(sym: str, day: str) -> pd.DataFrame | None:
    if free_gb() < MIN_FREE_GB:
        raise RuntimeError(f"disk floor reached ({free_gb():.1f} GB free)")
    r = _get(f"https://public.bybit.com/trading/{sym}/{sym}{day}.csv.gz")
    if r is None:
        return None
    TMP.mkdir(parents=True, exist_ok=True)
    f = TMP / f"{sym}{day}.csv.gz"
    f.write_bytes(r.content)
    try:
        df = pd.read_csv(f, usecols=["timestamp", "side", "size", "price", "foreignNotional"])
    finally:
        f.unlink(missing_ok=True)
    df["ts"] = pd.to_datetime((df.timestamp * 1000).round().astype("int64"), unit="ms", utc=True)
    df["is_buy"] = df.side.eq("Buy")
    return df.rename(columns={"foreignNotional": "quote"})[["ts", "price", "size", "quote", "is_buy"]]


def ticks_to_1m(t: pd.DataFrame) -> pd.DataFrame:
    t = t.sort_values("ts")
    g = t.set_index("ts").groupby(pd.Grouper(freq="1min"))
    out = pd.DataFrame({
        "open": g.price.first(), "high": g.price.max(), "low": g.price.min(), "close": g.price.last(),
        "quote_volume": g.quote.sum(), "count": g.price.count(),
        "taker_buy_quote": t.assign(q=np.where(t.is_buy, t.quote, 0.0)).set_index("ts").q.resample("1min").sum(),
    })
    out["taker_sell_quote"] = out.quote_volume - out.taker_buy_quote
    return out


# ---------------------------------------------------------------- Binance vision
def vision_zip_csv(path: str, cols=None) -> pd.DataFrame | None:
    r = _get("https://data.binance.vision/data/" + path)
    if r is None:
        return None
    z = zipfile.ZipFile(io.BytesIO(r.content))
    raw = z.read(z.namelist()[0])
    first = raw[:200].decode(errors="ignore")
    header = 0 if first[:1].isalpha() else None
    df = pd.read_csv(io.BytesIO(raw), header=header)
    if header is None and cols is not None:
        df.columns = cols[: df.shape[1]]
    return df


def binance_klines_1m(sym: str, days: list[str], market="futures/um") -> pd.DataFrame | None:
    parts = []
    for d in days:
        df = vision_zip_csv(f"{market}/daily/klines/{sym}/1m/{sym}-1m-{d}.zip", KL_COLS)
        if df is not None:
            parts.append(df)
    if not parts:
        return None
    k = pd.concat(parts)
    ot = pd.to_numeric(k.open_time)
    unit = "us" if ot.max() > 1e14 else "ms"  # spot vision switched to µs in 2025
    k.index = pd.to_datetime(ot, unit=unit, utc=True)
    out = pd.DataFrame({c: pd.to_numeric(k[c]) for c in ("open", "high", "low", "close", "quote_volume", "count")})
    out["taker_buy_quote"] = pd.to_numeric(k.taker_buy_quote_volume)
    out["taker_sell_quote"] = out.quote_volume - out.taker_buy_quote
    return out.sort_index()[~out.index.duplicated()]


def binance_aggtrades(sym: str, days: list[str]) -> pd.DataFrame | None:
    parts = []
    for d in days:
        df = vision_zip_csv(f"futures/um/daily/aggTrades/{sym}/{sym}-aggTrades-{d}.zip",
                            ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
                             "transact_time", "is_buyer_maker"])
        if df is not None:
            parts.append(df)
    if not parts:
        return None
    a = pd.concat(parts)
    t = pd.DataFrame({"ts": pd.to_datetime(pd.to_numeric(a.transact_time), unit="ms", utc=True),
                      "price": pd.to_numeric(a.price), "size": pd.to_numeric(a.quantity)})
    t["quote"] = t.price * t["size"]
    t["is_buy"] = ~a.is_buyer_maker.astype(str).str.lower().eq("true").values
    return t


# ---------------------------------------------------------------- REST helpers
def bybit_kline(sym: str, lo: pd.Timestamp, hi: pd.Timestamp, interval="60", category="linear"):
    rows, start = [], int(lo.timestamp() * 1000)
    end = int(hi.timestamp() * 1000)
    step = {"1": 60_000, "5": 300_000, "60": 3_600_000}[interval] * 1000
    while start < end:
        r = _get("https://api.bybit.com/v5/market/kline",
                 {"category": category, "symbol": sym, "interval": interval, "start": start,
                  "end": min(end, start + step - 1), "limit": 1000})
        lst = (r.json().get("result") or {}).get("list", []) if r else []
        rows += lst
        start += step
        time.sleep(0.1)
    if not rows:
        return None
    k = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume", "turnover"]).astype(float)
    k.index = pd.to_datetime(k.t.astype("int64"), unit="ms", utc=True)
    k = k.sort_index()[~k.index.duplicated()]
    return k.rename(columns={"turnover": "quote_volume"})[["open", "high", "low", "close", "quote_volume"]]


def binance_klines_1h(sym: str, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame | None:
    rows, start = [], int(lo.timestamp() * 1000)
    end = int(hi.timestamp() * 1000)
    while start < end:
        r = _get("https://fapi.binance.com/fapi/v1/klines",
                 {"symbol": sym, "interval": "1h", "startTime": start, "endTime": end, "limit": 1500})
        lst = r.json() if r else []
        if not lst:
            break
        rows += lst
        start = lst[-1][0] + 3_600_000
        time.sleep(0.2)
    if not rows:
        # vision fallback (daily 1h klines)
        parts = [vision_zip_csv(f"futures/um/daily/klines/{sym}/1h/{sym}-1h-{d}.zip", KL_COLS)
                 for d in _days(lo, hi)]
        parts = [p for p in parts if p is not None]
        if not parts:
            return None
        k = pd.concat(parts)
        k.index = pd.to_datetime(pd.to_numeric(k.open_time), unit="ms", utc=True)
    else:
        k = pd.DataFrame(rows, columns=KL_COLS)
        k.index = pd.to_datetime(k.open_time, unit="ms", utc=True)
    out = pd.DataFrame({c: pd.to_numeric(k[c]) for c in ("open", "high", "low", "close", "quote_volume")})
    return out.sort_index()[~out.index.duplicated()]


def bybit_oi(sym: str, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame | None:
    rows, end = [], int(hi.timestamp() * 1000)
    start = int(lo.timestamp() * 1000)
    while end > start:
        r = _get("https://api.bybit.com/v5/market/open-interest",
                 {"category": "linear", "symbol": sym, "intervalTime": "5min", "startTime": start,
                  "endTime": end, "limit": 200})
        lst = (r.json().get("result") or {}).get("list", []) if r else []
        if not lst:
            break
        rows += lst
        new_end = min(int(x["timestamp"]) for x in lst) - 1
        if new_end >= end:
            break
        end = new_end
        time.sleep(0.1)
    if not rows:
        return None
    o = pd.DataFrame(rows)
    o.index = pd.to_datetime(o.timestamp.astype("int64"), unit="ms", utc=True)
    return pd.DataFrame({"oi": o.openInterest.astype(float)}).sort_index().loc[lambda d: ~d.index.duplicated()]


def binance_oi(sym: str, days: list[str]) -> pd.DataFrame | None:
    parts = [vision_zip_csv(f"futures/um/daily/metrics/{sym}/{sym}-metrics-{d}.zip") for d in days]
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    m = pd.concat(parts)
    m.index = pd.to_datetime(m.create_time, utc=True)
    return pd.DataFrame({"oi": pd.to_numeric(m.sum_open_interest),
                         "oi_value": pd.to_numeric(m.sum_open_interest_value)}).sort_index()


def funding(exchange: str, sym: str, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame | None:
    if exchange == "bybit":
        rows, end = [], int(hi.timestamp() * 1000)
        start = int(lo.timestamp() * 1000)
        while end > start:
            r = _get("https://api.bybit.com/v5/market/funding/history",
                     {"category": "linear", "symbol": sym, "startTime": start, "endTime": end, "limit": 200})
            lst = (r.json().get("result") or {}).get("list", []) if r else []
            if not lst:
                break
            rows += lst
            new_end = min(int(x["fundingRateTimestamp"]) for x in lst) - 1
            if new_end >= end:
                break
            end = new_end
        if not rows:
            return None
        f = pd.DataFrame(rows)
        f.index = pd.to_datetime(f.fundingRateTimestamp.astype("int64"), unit="ms", utc=True)
        return pd.DataFrame({"rate": f.fundingRate.astype(float)}).sort_index()
    r = _get("https://fapi.binance.com/fapi/v1/fundingRate",
             {"symbol": sym, "startTime": int(lo.timestamp() * 1000), "endTime": int(hi.timestamp() * 1000),
              "limit": 1000})
    lst = r.json() if r else []
    if not lst:
        return None
    f = pd.DataFrame(lst)
    f.index = pd.to_datetime(f.fundingTime.astype("int64"), unit="ms", utc=True)
    return pd.DataFrame({"rate": f.fundingRate.astype(float)}).sort_index()


def bybit_spot_1m(sym: str, days: list[str]) -> pd.DataFrame | None:
    parts = []
    for d in days:
        r = _get(f"https://public.bybit.com/spot/{sym}/{sym}_{d}.csv.gz")
        if r is None:
            continue
        t = pd.read_csv(io.BytesIO(gzip.decompress(r.content)))
        # columns: id,timestamp(ms),price,volume,side
        t = pd.DataFrame({"ts": pd.to_datetime(t.timestamp.astype("int64"), unit="ms", utc=True),
                          "price": t.price.astype(float), "size": t.volume.astype(float),
                          "is_buy": t.side.str.lower().eq("buy")})
        t["quote"] = t.price * t["size"]
        parts.append(t)
    if not parts:
        return None
    return ticks_to_1m(pd.concat(parts))


# ---------------------------------------------------------------- per-event build
def _save(df, p: Path):
    if df is not None and len(df):
        df.to_pickle(p, compression="gzip")


def build_event(ev: pd.Series, force=False) -> dict:
    d = EV / ev.event_id
    flag = d / "done.json"
    if flag.exists() and not force:
        return json.loads(flag.read_text())
    d.mkdir(parents=True, exist_ok=True)
    ann, obs, eff = ev.announcement_ts, ev.first_publicly_observable_ts, ev.effective_ts
    end = max(eff, ann + pd.Timedelta(hours=72)) + pd.Timedelta(hours=1)
    days = _days(ann - pd.Timedelta(days=1), end)
    sym, ex, base = ev.symbol, ev.exchange, ev.base
    info = {"event_id": ev.event_id, "perp_1m_src": None, "ticks_src": None}

    if ex == "bybit":
        ticks_keep, bars = [], []
        for day in days:
            t = bybit_trades_day(sym, day)
            if t is None:
                continue
            bars.append(ticks_to_1m(t))
            w = t[(t.ts >= ann - pd.Timedelta(minutes=10)) & (t.ts <= obs + pd.Timedelta(hours=2))]
            if len(w):
                ticks_keep.append(w)
        if bars:
            b = pd.concat(bars)
            _save(b[~b.index.duplicated()], d / "perp_1m.pkl.gz")
            info["perp_1m_src"] = "bybit_trade_archive"
        else:
            k = bybit_kline(sym, ann - pd.Timedelta(days=1), end, interval="1")
            _save(k, d / "perp_1m.pkl.gz")
            info["perp_1m_src"] = "bybit_rest_kline" if k is not None else None
        if ticks_keep:
            _save(pd.concat(ticks_keep), d / "ticks_ann.pkl.gz")
            info["ticks_src"] = "bybit_trade_archive"
        h = bybit_kline(sym, ann - pd.Timedelta(days=21), ann + pd.Timedelta(hours=1), interval="60")
        _save(h, d / "perp_1h.pkl.gz")
        info["perp_1h_src"] = "bybit_rest_kline" if h is not None else None
        _save(bybit_oi(sym, ann - pd.Timedelta(days=3), end), d / "oi.pkl.gz")
    else:
        k = binance_klines_1m(sym, days)
        _save(k, d / "perp_1m.pkl.gz")
        info["perp_1m_src"] = "binance_vision_1m" if k is not None else None
        tk = binance_aggtrades(sym, _days(ann - pd.Timedelta(minutes=10), obs + pd.Timedelta(hours=2)))
        if tk is not None:
            tk = tk[(tk.ts >= ann - pd.Timedelta(minutes=10)) & (tk.ts <= obs + pd.Timedelta(hours=2))]
            _save(tk, d / "ticks_ann.pkl.gz")
            info["ticks_src"] = "binance_vision_aggtrades"
        h = binance_klines_1h(sym, ann - pd.Timedelta(days=21), ann + pd.Timedelta(hours=1))
        _save(h, d / "perp_1h.pkl.gz")
        info["perp_1h_src"] = "binance_1h" if h is not None else None
        _save(binance_oi(sym, _days(ann - pd.Timedelta(days=3), end)), d / "oi.pkl.gz")

    _save(funding(ex, sym, ann - pd.Timedelta(days=10), end), d / "funding.pkl.gz")
    # spot: Binance spot vision first, then Bybit spot archive
    spot_sym = base + "USDT"
    sp = binance_klines_1m(spot_sym, days, market="spot")
    info["spot_venue"] = "binance_spot" if sp is not None else None
    if sp is None:
        sp = bybit_spot_1m(spot_sym, days)
        info["spot_venue"] = "bybit_spot" if sp is not None else None
    _save(sp, d / "spot_1m.pkl.gz")
    for n in ("oi", "funding", "spot_1m", "perp_1m", "ticks_ann", "perp_1h"):
        info[f"has_{n}"] = (d / f"{n}.pkl.gz").exists()
    flag.write_text(json.dumps(info))
    return info


def btc_1m(lo="2024-02-01", hi="2025-03-31") -> pd.DataFrame:
    p = ROOT / "BTCUSDT_1m.pkl.gz"
    if p.exists():
        return pd.read_pickle(p)
    parts = []
    for m in pd.date_range(lo, hi, freq="MS"):
        df = vision_zip_csv(f"futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-{m:%Y-%m}.zip", KL_COLS)
        df.index = pd.to_datetime(pd.to_numeric(df.open_time), unit="ms", utc=True)
        parts.append(pd.DataFrame({"close": pd.to_numeric(df.close)}))
    b = pd.concat(parts).sort_index()
    b = b[~b.index.duplicated()]
    b.to_pickle(p, compression="gzip")
    return b


if __name__ == "__main__":
    import sys

    from delisting_lab.catalog import build_catalog

    cat, _ = build_catalog()
    from delisting_lab.run_study import spot_only_comparators

    perps = pd.concat([cat[cat.in_train1 & (cat.contract_type == "linear_perp")], spot_only_comparators(cat)])
    btc_1m()
    only = set(sys.argv[1:])
    for _, ev in perps.iterrows():
        if only and ev.symbol not in only:
            continue
        t0 = time.time()
        try:
            info = build_event(ev)
        except Exception as e:  # keep going; report as missing
            info = {"event_id": ev.event_id, "error": repr(e)}
        print(f"{ev.event_id} {time.time() - t0:.0f}s free={free_gb():.1f}GB {info}", flush=True)
