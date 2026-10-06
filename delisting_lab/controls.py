"""Matched-control pool: Binance USD-M perps listed before Train-1 that kept trading through
it and are not in the delisting catalog. Pool = the 40 lowest-liquidity such names by
Feb-2024 median daily quote volume (closest to doomed-alt liquidity). 1m close + quote
volume cached per symbol (data_cache/f012_c02/controls/<SYM>.pkl.gz).

Survivorship caveat (reported): the pool survived Train-1 by construction.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from delisting_lab.market_data import KL_COLS, ROOT, free_gb, vision_zip_csv

CTRL = ROOT / "controls"
POOL_N = 40
# stablecoins / index products are not comparable price processes
NON_TOKEN = {"USDCUSDT", "BTCDOMUSDT", "DEFIUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT", "FOOTBALLUSDT",
             "BLUEBIRDUSDT", "EURUSDT", "XAUUSDT"}


def candidate_symbols(exclude_bases: set[str]) -> list[str]:
    info = json.loads((ROOT / "raw" / "binance_um_exchangeinfo.json").read_text())
    lo = pd.Timestamp("2024-02-01", tz="UTC").value // 10**6
    hi = pd.Timestamp("2025-03-05", tz="UTC").value // 10**6
    out = []
    for s in info:
        if s["contractType"] != "PERPETUAL" or s["quoteAsset"] != "USDT" or s["onboardDate"] >= lo:
            continue
        if s["status"] != "TRADING" and int(s.get("deliveryDate") or 0) < hi:
            continue
        b = s["baseAsset"].lstrip("1000") if s["baseAsset"].startswith("1000") else s["baseAsset"]
        if b in exclude_bases or s["baseAsset"] in ("BTC", "ETH"):
            continue
        out.append(s["symbol"])
    return sorted(out)


def rank_by_liquidity(syms: list[str]) -> pd.Series:
    p = CTRL / "pool_rank.csv"
    if p.exists():
        return pd.read_csv(p, index_col=0).iloc[:, 0]
    med = {}
    for s in syms:
        df = vision_zip_csv(f"futures/um/monthly/klines/{s}/1d/{s}-1d-2024-02.zip", KL_COLS)
        if df is not None:
            med[s] = pd.to_numeric(df.quote_volume).median()
    r = pd.Series(med, name="feb2024_median_daily_quote_volume").sort_values()
    CTRL.mkdir(parents=True, exist_ok=True)
    r.to_csv(p)
    return r


def fetch_symbol(s: str, lo="2024-02-01", hi="2025-03-31") -> None:
    p = CTRL / f"{s}.pkl.gz"
    if p.exists():
        return
    parts = []
    for m in pd.date_range(lo, hi, freq="MS"):
        if free_gb() < 15:
            raise RuntimeError("disk floor")
        df = vision_zip_csv(f"futures/um/monthly/klines/{s}/1m/{s}-1m-{m:%Y-%m}.zip", KL_COLS)
        if df is None:
            continue
        df.index = pd.to_datetime(pd.to_numeric(df.open_time), unit="ms", utc=True)
        parts.append(pd.DataFrame({"close": pd.to_numeric(df.close, downcast="float"),
                                   "quote_volume": pd.to_numeric(df.quote_volume, downcast="float")}))
    if parts:
        b = pd.concat(parts).sort_index()
        b[~b.index.duplicated()].to_pickle(p, compression="gzip")


def pool() -> list[str]:
    r = pd.read_csv(CTRL / "pool_rank.csv", index_col=0).iloc[:, 0]
    syms = [s for s in r.index if s not in NON_TOKEN][:POOL_N]
    return [s for s in syms if (CTRL / f"{s}.pkl.gz").exists()]


if __name__ == "__main__":
    from delisting_lab.catalog import build_catalog

    cat, _ = build_catalog()
    excl = set(cat.base)
    syms = candidate_symbols(excl)
    print("candidates", len(syms), flush=True)
    r = rank_by_liquidity(syms)
    for s in [x for x in r.index if x not in NON_TOKEN][:POOL_N]:
        fetch_symbol(s)
        print("ctrl", s, f"{r[s]:.0f}", f"free={free_gb():.1f}", flush=True)
    sys.exit(0)
