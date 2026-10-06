#!/usr/bin/env python3
"""F006 cost audit 2026-10-06: measure spread/impact; reprice closed results.

Disk guard: never let free space on /home/limen drop below 20 GB.
No strategy-logic changes. Report only.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import shutil
import statistics as st
import sys
import tempfile
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/limen/bot_traiding_daily/bot_traiding_daily")
OUT = REPO / "output" / "f006_cost_audit"
OUT.mkdir(parents=True, exist_ok=True)
MIN_FREE_BYTES = 20 * 1024**3
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT")
STAKE = 100.0  # USD notional at leverage 1

# Train-1 span days to sample (spread across + a few high-vol candidates)
SAMPLE_DAYS = [
    "2024-02-15",  # early Train-1
    "2024-03-15",  # BTC ATH run-up
    "2024-04-15",  # post-halving / vol
    "2024-05-20",
    "2024-06-15",
    "2024-08-05",  # Japan carry / vol
    "2024-09-15",
    "2024-11-11",  # post-election vol
    "2024-12-10",
    "2025-01-20",
]


def free_bytes(path: str = "/home/limen") -> int:
    u = shutil.disk_usage(path)
    return u.free


def guard_disk(tag: str = "") -> None:
    free = free_bytes()
    if free < MIN_FREE_BYTES:
        raise RuntimeError(f"disk guard: free={free} < {MIN_FREE_BYTES} ({tag})")


def http_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": "f006-cost-audit/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def live_orderbook(symbol: str, limit: int = 50, notional: float = STAKE) -> dict:
    url = f"https://api.bybit.com/v5/market/orderbook?category=linear&symbol={symbol}&limit={limit}"
    o = http_json(url)
    r = o["result"]
    bids = [(float(p), float(s)) for p, s in r["b"]]
    asks = [(float(p), float(s)) for p, s in r["a"]]
    bid, ask = bids[0][0], asks[0][0]
    mid = (bid + ask) / 2
    half_spread_bps = (ask - bid) / mid * 1e4 / 2

    def walk(levels, notional):
        rem = notional
        cost = 0.0
        qty = 0.0
        for px, sz in levels:
            level_n = px * sz
            take = min(rem, level_n)
            cost += take
            qty += take / px
            rem -= take
            if rem <= 1e-12:
                break
        if qty <= 0:
            return None, None
        avg = cost / qty
        # full mid→avg in bps; impact beyond touch = that minus half-spread
        full = abs(avg - mid) / mid * 1e4
        beyond = max(0.0, full - half_spread_bps)
        return full, beyond

    buy_full, buy_beyond = walk(asks, notional)
    sell_full, sell_beyond = walk(bids, notional)
    # depth to absorb notional
    def depth_usd(levels):
        return sum(p * s for p, s in levels)

    return {
        "symbol": symbol,
        "mid": mid,
        "half_spread_bps": half_spread_bps,
        "impact_beyond_touch_buy_bps": buy_beyond,
        "impact_beyond_touch_sell_bps": sell_beyond,
        "full_buy_bps": buy_full,
        "full_sell_bps": sell_full,
        "bid_depth_50_usd": depth_usd(bids),
        "ask_depth_50_usd": depth_usd(asks),
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def download_trades_day(symbol: str, day: str, dest: Path) -> Path:
    url = f"https://public.bybit.com/trading/{symbol}/{symbol}{day}.csv.gz"
    guard_disk(f"before download {symbol} {day}")
    req = urllib.request.Request(url, headers={"User-Agent": "f006-cost-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
    except Exception as e:
        if dest.exists():
            dest.unlink()
        raise RuntimeError(f"download failed {url}: {e}") from e
    guard_disk(f"after download {symbol} {day}")
    return dest


def effective_spread_from_trades(path: Path, symbol: str, day: str) -> dict:
    """Reduce one daily trade file: Roll-ish + trade-side effective half-spread proxy.

    Bybit public trading CSV columns (linear): timestamp, symbol, side, size, price, tickDirection, trdMatchID, ...
    We stream in chunks; delete caller handles file removal.
    """
    # detect columns from first lines
    with gzip.open(path, "rt") as f:
        header = f.readline().strip().split(",")
    # normalize
    colmap = {c.lower(): c for c in header}

    def pick(*names):
        for n in names:
            if n.lower() in colmap:
                return colmap[n.lower()]
        return None

    c_ts = pick("timestamp", "time", "t")
    c_side = pick("side", "S")
    c_price = pick("price", "p")
    c_size = pick("size", "qty", "v", "volume")
    if not all([c_ts, c_side, c_price]):
        return {"symbol": symbol, "day": day, "error": f"bad header {header[:10]}"}

    # stream aggregate: 1-minute mid proxy from last trade; signed returns for Roll
    # also accumulate buy/sell prices around mid for effective spread
    last_price = None
    last_minute = None
    minute_last = {}
    signed_r = []  # for Roll on 1s subsampled? use 1-min returns
    # trade-rule: Buy trades lift ask; Sell hit bid. Effective half-spread ≈ |trade - mid| but mid unknown.
    # Use rolling mid = EMA of prices; signed: +1 Buy, -1 Sell; es = 2 * mean(side * (p - mid_prev))
    ema = None
    alpha = 2 / (20 + 1)
    es_vals = []
    hour_hs = defaultdict(list)
    n = 0
    notionals = []

    usecols = [c_ts, c_side, c_price] + ([c_size] if c_size else [])
    for chunk in pd.read_csv(path, compression="gzip", chunksize=200_000, usecols=usecols):
        prices = chunk[c_price].astype(float).to_numpy()
        sides = chunk[c_side].astype(str).to_numpy()
        if c_ts:
            # timestamp may be ms int or datetime string
            ts_raw = chunk[c_ts]
            try:
                ts_num = ts_raw.astype(float).to_numpy()
                if np.nanmedian(ts_num) > 1e12:
                    ts_sec = ts_num / 1000.0
                elif np.nanmedian(ts_num) > 1e10:
                    ts_sec = ts_num / 1000.0
                else:
                    ts_sec = ts_num
            except Exception:
                ts_sec = pd.to_datetime(ts_raw, utc=True).astype("int64").to_numpy() / 1e9
        else:
            ts_sec = np.arange(len(prices))
        sizes = chunk[c_size].astype(float).to_numpy() if c_size else np.ones(len(prices))

        for p, side, t, sz in zip(prices, sides, ts_sec, sizes):
            n += 1
            if not math.isfinite(p) or p <= 0:
                continue
            s = 1.0 if str(side).lower().startswith("b") else -1.0
            if ema is None:
                ema = p
            else:
                # effective half-spread proxy vs pre-trade mid
                es = s * (p - ema) / ema * 1e4  # bps signed; positive = pay the spread
                if es > 0:  # only adverse
                    es_vals.append(es)
                    hour = int(datetime.fromtimestamp(t, tz=timezone.utc).hour) if t > 1e8 else 0
                    hour_hs[hour].append(es)
                ema = alpha * p + (1 - alpha) * ema
            minute = int(t) // 60
            minute_last[minute] = p
            notionals.append(p * abs(sz))

    # Roll on 1-min last prices
    mins = sorted(minute_last)
    px = np.array([minute_last[m] for m in mins], dtype=float)
    if len(px) > 5:
        r = np.diff(np.log(px))
        if len(r) > 2:
            cov = np.cov(r[1:], r[:-1])[0, 1]
            roll = 2.0 * math.sqrt(max(0.0, -cov)) * 1e4  # full spread bps
            roll_half = roll / 2.0
        else:
            roll_half = float("nan")
    else:
        roll_half = float("nan")

    def pct(xs, q):
        if not xs:
            return float("nan")
        s = sorted(xs)
        return s[min(len(s) - 1, max(0, int(q * len(s)) - (0 if q < 1 else 0)))]

    hour_med = {h: float(np.median(v)) for h, v in sorted(hour_hs.items()) if v}

    return {
        "symbol": symbol,
        "day": day,
        "n_trades": n,
        "eff_half_spread_median_bps": float(np.median(es_vals)) if es_vals else float("nan"),
        "eff_half_spread_p90_bps": float(np.percentile(es_vals, 90)) if es_vals else float("nan"),
        "roll_half_spread_bps": roll_half,
        "trade_notional_median_usd": float(np.median(notionals)) if notionals else float("nan"),
        "hour_eff_half_median_bps": hour_med,
    }


def corwin_schultz_from_frame(symbol: str) -> dict:
    """Corwin-Schultz high-low spread estimator on 5m frame (Train-1, skip warmup)."""
    path = REPO / "output" / "f011_forced_flow" / "frame_5m" / f"{symbol}.csv.gz"
    if not path.exists():
        # try hourly candles from cache
        return {"symbol": symbol, "error": "no frame_5m"}
    df = pd.read_csv(path, usecols=["timestamp", "high", "low", "close", "is_warmup", "realized_vol"])
    df = df.loc[~df["is_warmup"].astype(bool)].copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    h = df["high"].astype(float)
    l = df["low"].astype(float)
    # CS 2012 beta/gamma
    log_hl = np.log(h / l) ** 2
    # need pairs
    beta = log_hl + log_hl.shift(-1)  # H_t,L_t and H_{t+1},L_{t+1} — use t and t+1
    # standard formulation uses two-day; here two bars
    gamma = np.log(pd.concat([h, h.shift(-1)], axis=1).max(axis=1) / pd.concat([l, l.shift(-1)], axis=1).min(axis=1)) ** 2
    beta = log_hl + log_hl.shift(-1)
    alpha = ((np.sqrt(2 * beta) - np.sqrt(beta)) / (3 - 2 * np.sqrt(2))) - np.sqrt(gamma / (3 - 2 * np.sqrt(2)))
    # spread S = 2(e^alpha - 1)/(1 + e^alpha); clip negative to 0
    S = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
    S = S.replace([np.inf, -np.inf], np.nan).clip(lower=0)
    half_bps = (S / 2.0) * 1e4
    half_bps = half_bps.dropna()
    # volatile regimes: top realized_vol quartile
    rv = df["realized_vol"].astype(float)
    q75 = rv.quantile(0.75)
    vol_mask = rv >= q75
    half_vol = half_bps[vol_mask.reindex(half_bps.index).fillna(False)]
    hour = df.loc[half_bps.index, "timestamp"].dt.hour
    hour_med = half_bps.groupby(hour).median().to_dict()
    return {
        "symbol": symbol,
        "cs_half_spread_median_bps": float(half_bps.median()),
        "cs_half_spread_p90_bps": float(half_bps.quantile(0.90)),
        "cs_half_spread_vol_q75_median_bps": float(half_vol.median()) if len(half_vol) else float("nan"),
        "cs_hour_median_bps": {int(k): float(v) for k, v in hour_med.items()},
        "n_bars": int(len(half_bps)),
    }


def reprice_trades(df: pd.DataFrame, commission_bps: float, half_spread_bps: float, slippage_bps: float) -> pd.DataFrame:
    out = df.copy()
    exit_notional = (out["exit_price"].astype(float) * out["quantity"].astype(float).abs())
    notional = out["notional"].astype(float)
    new_costs = (
        (commission_bps / 1e4) * (notional + exit_notional)
        + (half_spread_bps / 1e4) * (notional + exit_notional)
        + (slippage_bps / 1e4) * notional
    )
    funding = out["funding_pnl"].astype(float) if "funding_pnl" in out.columns else 0.0
    out["total_costs_new"] = new_costs
    out["net_pnl_new"] = out["gross_pnl"].astype(float) - new_costs + funding
    return out


def month_stats(df: pd.DataFrame, net_col: str = "net_pnl_new") -> dict:
    if "month" not in df.columns:
        # derive from entry_time
        et = pd.to_datetime(df["entry_time"], utc=True)
        month = et.dt.strftime("%Y-%m")
    else:
        month = df["month"].astype(str)
    g = df.groupby(month, sort=True)[net_col].sum()
    shared = ["2024-03", "2024-04", "2024-05", "2024-08", "2024-09", "2024-12"]
    shared_sum = float(g.reindex(shared).fillna(0).sum()) if any(m in g.index for m in shared) else float("nan")
    return {
        "n_trades": int(len(df)),
        "mean_net": float(df[net_col].mean()) if len(df) else float("nan"),
        "total_net": float(df[net_col].sum()) if len(df) else float("nan"),
        "green_months": int((g > 0).sum()),
        "n_months": int(len(g)),
        "shared_losing_months_sum": shared_sum,
        "monthly": {k: float(v) for k, v in g.items()},
    }


# Known kill criteria (from profiles / notes) — approximate, documented:
# - FREEZE profiles were frozen for structural reasons at 17bps assumption; we report whether
#   mean net flips sign, or shared-months sum flips sign, or green-month floor story changes.
SHARED_MONTHS = ["2024-03", "2024-04", "2024-05", "2024-08", "2024-09", "2024-12"]


def main():
    print("free_gb", free_bytes() / 1024**3)
    guard_disk("start")

    # --- 1a live orderbook ---
    live = [live_orderbook(s) for s in SYMBOLS]
    (OUT / "live_orderbook.json").write_text(json.dumps(live, indent=2))
    print("live orderbook done")

    # --- 1b Corwin-Schultz from 5m frames ---
    cs = []
    for s in SYMBOLS:
        # frame_5m only has BTC/ETH; for others use hourly cache OHLC if present
        try:
            if s in ("BTCUSDT", "ETHUSDT"):
                cs.append(corwin_schultz_from_frame(s))
            else:
                # find a 60m cache CSV
                caches = list((REPO / "data_cache").glob(f"{s}_60_*.csv"))
                if not caches:
                    cs.append({"symbol": s, "error": "no 60m cache"})
                    continue
                df = pd.read_csv(caches[0], usecols=lambda c: c.lower() in ("timestamp", "open", "high", "low", "close", "time"))
                # normalize
                cols = {c.lower(): c for c in df.columns}
                h = df[cols["high"]].astype(float)
                l = df[cols["low"]].astype(float)
                log_hl = np.log(h / l) ** 2
                beta = log_hl + log_hl.shift(-1)
                gamma = np.log(pd.concat([h, h.shift(-1)], axis=1).max(axis=1) / pd.concat([l, l.shift(-1)], axis=1).min(axis=1)) ** 2
                alpha = ((np.sqrt(2 * beta) - np.sqrt(beta)) / (3 - 2 * np.sqrt(2))) - np.sqrt(gamma / (3 - 2 * np.sqrt(2)))
                S = 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))
                S = S.replace([np.inf, -np.inf], np.nan).clip(lower=0)
                half = (S / 2.0) * 1e4
                half = half.dropna()
                cs.append({
                    "symbol": s,
                    "cs_half_spread_median_bps": float(half.median()),
                    "cs_half_spread_p90_bps": float(half.quantile(0.90)),
                    "source": f"hourly_cache:{caches[0].name}",
                    "n_bars": int(len(half)),
                })
        except Exception as e:
            cs.append({"symbol": s, "error": str(e)})
    (OUT / "corwin_schultz.json").write_text(json.dumps(cs, indent=2))
    print("CS done", cs)

    # --- 1c sample trade days for effective spread (one file at a time) ---
    trade_proxy_rows = []
    tmpdir = Path(tempfile.mkdtemp(prefix="f006_cost_"))
    try:
        for day in SAMPLE_DAYS:
            for sym in SYMBOLS:
                dest = tmpdir / f"{sym}{day}.csv.gz"
                try:
                    download_trades_day(sym, day, dest)
                    row = effective_spread_from_trades(dest, sym, day)
                    trade_proxy_rows.append(row)
                    print("reduced", sym, day, row.get("eff_half_spread_median_bps"), row.get("roll_half_spread_bps"))
                except Exception as e:
                    trade_proxy_rows.append({"symbol": sym, "day": day, "error": str(e)})
                    print("FAIL", sym, day, e)
                finally:
                    if dest.exists():
                        dest.unlink()
                guard_disk(f"after {sym} {day}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    (OUT / "trade_effective_spread.json").write_text(json.dumps(trade_proxy_rows, indent=2, default=str))

    # summarize measured costs per symbol
    measured = {}
    for sym in SYMBOLS:
        live_row = next(x for x in live if x["symbol"] == sym)
        cs_row = next(x for x in cs if x["symbol"] == sym)
        day_rows = [r for r in trade_proxy_rows if r.get("symbol") == sym and "eff_half_spread_median_bps" in r]
        eff_meds = [r["eff_half_spread_median_bps"] for r in day_rows if math.isfinite(r.get("eff_half_spread_median_bps", float("nan")))]
        eff_p90s = [r["eff_half_spread_p90_bps"] for r in day_rows if math.isfinite(r.get("eff_half_spread_p90_bps", float("nan")))]
        roll_hs = [r["roll_half_spread_bps"] for r in day_rows if math.isfinite(r.get("roll_half_spread_bps", float("nan")))]
        # primary measured half-spread: prefer live for touch; trade-eff for historical typical; CS as OHLC backup
        half_med = float(np.median(eff_meds)) if eff_meds else float(cs_row.get("cs_half_spread_median_bps", float("nan")))
        half_p90 = float(np.median(eff_p90s)) if eff_p90s else float(cs_row.get("cs_half_spread_p90_bps", float("nan")))
        # impact beyond touch at $100: from live (≈0)
        impact_med = float(np.mean([
            live_row["impact_beyond_touch_buy_bps"],
            live_row["impact_beyond_touch_sell_bps"],
        ]))
        # p90 impact: use live only (single snapshot) — note limitation; bump with 0 for $100
        impact_p90 = impact_med
        measured[sym] = {
            "live_half_spread_bps": live_row["half_spread_bps"],
            "live_impact_beyond_touch_bps": impact_med,
            "trade_eff_half_median_bps": half_med,
            "trade_eff_half_p90_bps": half_p90,
            "roll_half_median_bps": float(np.median(roll_hs)) if roll_hs else float("nan"),
            "cs_half_median_bps": cs_row.get("cs_half_spread_median_bps"),
            "cs_half_p90_bps": cs_row.get("cs_half_spread_p90_bps"),
            "cs_vol_q75_half_median_bps": cs_row.get("cs_half_spread_vol_q75_median_bps"),
            "n_trade_days_ok": len(eff_meds),
            # adopted measurement for repricing: median half-spread from trade proxy (clamped to live floor), impact from live
            "adopted_half_spread_median_bps": half_med,
            "adopted_half_spread_p90_bps": half_p90,
            "adopted_impact_median_bps": impact_med,
            "adopted_impact_p90_bps": impact_p90,
        }
    (OUT / "measured_by_symbol.json").write_text(json.dumps(measured, indent=2))

    # basket-equal adopted half-spread for harness (strategies trade all 5)
    half_meds = [measured[s]["adopted_half_spread_median_bps"] for s in SYMBOLS if math.isfinite(measured[s]["adopted_half_spread_median_bps"])]
    half_p90s = [measured[s]["adopted_half_spread_p90_bps"] for s in SYMBOLS if math.isfinite(measured[s]["adopted_half_spread_p90_bps"])]
    impact_med = float(np.mean([measured[s]["adopted_impact_median_bps"] for s in SYMBOLS]))
    basket = {
        "half_spread_median_bps": float(np.median(half_meds)),
        "half_spread_p90_bps": float(np.median(half_p90s)),
        "impact_median_bps": impact_med,
        "impact_p90_bps": impact_med,
        "notional_usd": STAKE,
    }
    (OUT / "measured_basket.json").write_text(json.dumps(basket, indent=2))
    print("basket", basket)

    # --- 2 reprice ---
    # scenarios: (name, commission, half_spread, slippage)
    # measured median scenario uses measured half + impact as slippage replacement
    scen = [
        ("assumed_10_5_2", 10.0, 5.0, 2.0),
        ("taker_5_5_plus_assumed_spread_slip", 5.5, 5.0, 2.0),
        ("maker_2_plus_assumed_spread_slip", 2.0, 5.0, 2.0),
        ("taker_5_5_measured_median", 5.5, basket["half_spread_median_bps"], basket["impact_median_bps"]),
        ("taker_5_5_measured_p90", 5.5, basket["half_spread_p90_bps"], basket["impact_p90_bps"]),
        ("assumed_comm10_measured_median", 10.0, basket["half_spread_median_bps"], basket["impact_median_bps"]),
    ]

    trade_sources = {
        "DONCHIAN_55_NO_TRAIL": REPO / "output/f006_donchian_autopsy/donchian55_notrail_trades_train1.csv",
        "EMA3_21_50_200": REPO / "output/f006_catalog5_trio_autopsy/trades/EMA3_21_50_200_train1_trades.csv",
        "EMA3_13_50_200": REPO / "output/f006_catalog5_trio_autopsy/trades/EMA3_13_50_200_train1_trades.csv",
        "EMA_50_200": REPO / "output/f006_catalog5_dual_autopsy/trades/EMA_50_200_train1_trades.csv",
        "BB_20_25_EMA200": REPO / "output/f006_catalog5_dual_autopsy/trades/BB_20_25_EMA200_train1_trades.csv",
        "BB_20_2_EMA200": REPO / "output/f006_catalog5_trio_autopsy/trades/BB_20_2_EMA200_train1_trades.csv",
    }

    rows = []
    for name, path in trade_sources.items():
        df = pd.read_csv(path)
        # original stats
        base = month_stats(df.assign(net_pnl_new=df["net_pnl"]), "net_pnl_new")
        base.update({"strategy": name, "scenario": "stored_net_at_10_5_2", "path": str(path)})
        rows.append(base)
        for scen_name, c, h, s in scen:
            rdf = reprice_trades(df, c, h, s)
            stt = month_stats(rdf, "net_pnl_new")
            stt.update({
                "strategy": name,
                "scenario": scen_name,
                "commission_bps": c,
                "half_spread_bps": h,
                "slippage_bps": s,
                "per_side_bps": c + h + s,
                "rt_bps": 2 * c + 2 * h + s,  # matches engine: slip once
            })
            # flip flags vs stored
            stt["flip_mean_sign"] = (base["mean_net"] > 0) != (stt["mean_net"] > 0)
            stt["flip_shared_sum_sign"] = (
                math.isfinite(base["shared_losing_months_sum"])
                and math.isfinite(stt["shared_losing_months_sum"])
                and ((base["shared_losing_months_sum"] > 0) != (stt["shared_losing_months_sum"] > 0))
            )
            rows.append(stt)

    # sleeves: funding + oi fade — same blotter schema?
    for sleeve, folder in [
        ("H-FUNDING-CARRY-01", REPO / "output/f006_funding_carry/raw"),
        ("H-NONCANDLE-SLEEVE-01", REPO / "output/f006_noncandle_oi_fade/raw"),
    ]:
        files = sorted(folder.glob("*_trades.csv"))
        if not files:
            continue
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)
        if "gross_pnl" not in df.columns:
            rows.append({"strategy": sleeve, "scenario": "SKIP", "error": f"cols={list(df.columns)[:10]}"})
            continue
        base = month_stats(df.assign(net_pnl_new=df["net_pnl"]), "net_pnl_new")
        base.update({"strategy": sleeve, "scenario": "stored_net_at_10_5_2"})
        rows.append(base)
        for scen_name, c, h, s in scen:
            rdf = reprice_trades(df, c, h, s)
            stt = month_stats(rdf, "net_pnl_new")
            stt.update({
                "strategy": sleeve,
                "scenario": scen_name,
                "commission_bps": c,
                "half_spread_bps": h,
                "slippage_bps": s,
                "per_side_bps": c + h + s,
                "rt_bps": 2 * c + 2 * h + s,
            })
            stt["flip_mean_sign"] = (base["mean_net"] > 0) != (stt["mean_net"] > 0)
            stt["flip_shared_sum_sign"] = (
                math.isfinite(base["shared_losing_months_sum"])
                and math.isfinite(stt["shared_losing_months_sum"])
                and ((base["shared_losing_months_sum"] > 0) != (stt["shared_losing_months_sum"] > 0))
            )
            rows.append(stt)

    # F011: cells already in bps; reprice by comparing excess to new cost bands
    f011_cells = REPO / "output/f011_forced_flow/event_study/cells.csv"
    f011_rows = []
    if f011_cells.exists():
        cells = pd.read_csv(f011_cells)
        # expect columns with excess_bps or similar
        f011_rows.append({"note": "columns", "cols": list(cells.columns)})
        (OUT / "f011_cells_head.json").write_text(json.dumps({"cols": list(cells.columns), "head": cells.head(3).to_dict()}, indent=2, default=str))

    rep = pd.DataFrame(rows)
    rep.to_csv(OUT / "reprice_summary.csv", index=False)
    # compact json without monthly dicts for note
    compact = []
    for r in rows:
        compact.append({k: v for k, v in r.items() if k != "monthly"})
    (OUT / "reprice_summary.json").write_text(json.dumps(compact, indent=2, default=str))

    flips = [r for r in compact if r.get("flip_mean_sign") or r.get("flip_shared_sum_sign")]
    (OUT / "flips.json").write_text(json.dumps(flips, indent=2, default=str))
    print("flips", len(flips))
    print("done free_gb", free_bytes() / 1024**3)


if __name__ == "__main__":
    main()
