"""Ticker mapping, survivorship-safe daily prices and short availability (prereg §7)."""
from __future__ import annotations

import gzip
import json

import numpy as np
import pandas as pd

from unlock_lab.fetch import ROOT, bybit_daily, free_gb, vision_daily

MIN_FREE_GB = 15.0


def gecko_symbols() -> dict[str, str]:
    lst = json.loads(gzip.decompress((ROOT / "coingecko_coins_list.json.gz").read_bytes()))
    return {c["id"]: c["symbol"].upper() for c in lst}


def _series(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or not len(df):
        return None
    t = pd.to_numeric(df.open_time).astype("int64")
    t = t.where(t < 10**14, t // 1000)   # vision spot switched to µs from 2025-01 (per row)
    out = pd.DataFrame({"close": pd.to_numeric(df.close).values, "qv": pd.to_numeric(df.quote_volume).values},
                       index=pd.to_datetime(t.values, unit="ms", utc=True).floor("D"))
    out = out[~out.index.duplicated(keep="last")].sort_index()
    return out[out.close > 0]


def token_prices(sym: str) -> tuple[pd.DataFrame | None, str | None, dict]:
    """Price venue cascade: Binance spot → Binance UM perp → Bybit linear. Perp first-bar for short availability."""
    if free_gb() < MIN_FREE_GB:
        raise RuntimeError("disk floor")
    pair = f"{sym}USDT"
    um = _series(vision_daily("futures/um", pair))
    byb = _series(bybit_daily(pair))
    spot = _series(vision_daily("spot", pair))
    info = {"um_first": um.index.min() if um is not None else pd.NaT,
            "bybit_first": byb.index.min() if byb is not None else pd.NaT}
    for name, s in (("binance_spot", spot), ("binance_um", um), ("bybit_linear", byb)):
        if s is not None and len(s) > 60:
            return s, name, info
    return None, None, info


def btc() -> pd.DataFrame:
    return _series(vision_daily("spot", "BTCUSDT"))


def build_universe(workers: int = 12) -> pd.DataFrame:
    from concurrent.futures import ThreadPoolExecutor
    prot = pd.read_csv(ROOT / "protocols.csv")
    gs = gecko_symbols()
    prot["symbol"] = prot.gecko_id.map(gs)
    todo = prot.dropna(subset=["symbol"]).drop_duplicates("symbol")

    def one(r):
        try:
            s, venue, info = token_prices(r.symbol)
        except Exception as e:  # noqa: BLE001
            return dict(slug=r.slug, symbol=r.symbol, venue=None, err=str(e)[:80])
        return dict(slug=r.slug, symbol=r.symbol, venue=venue, n_bars=0 if s is None else len(s), **info)
    with ThreadPoolExecutor(workers) as ex:
        out = list(ex.map(one, todo.itertuples()))
    u = prot.merge(pd.DataFrame(out).drop(columns="symbol"), on="slug", how="left")
    u.to_csv(ROOT / "universe.csv", index=False)
    return u


if __name__ == "__main__":
    u = build_universe()
    print(len(u), u.symbol.notna().sum(), u.venue.value_counts(dropna=False).to_dict(), f"{free_gb():.1f} GB")
