"""PIT data layer for F012-C01: Farside flows, ET session windows, daily feature frame."""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from etf_lab import fetch

ET = "America/New_York"
OUT = Path("output/f012_c01_etf")
FARSIDE_SRC = Path(os.environ.get(
    "F012_FARSIDE_BTC",
    "/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache/f012/etf_flows/farside_BTC_flows.csv"))
FARSIDE_SNAPSHOT = OUT / "inputs" / "farside_BTC_flows_snapshot.csv"
TRAIN1 = (pd.Timestamp("2024-03-01"), pd.Timestamp("2025-03-01"))
# Conservative earliest live availability of Farside row T-1 on day T (UTC). Evidence: the
# 2026-10-06 14:52 UTC collector snapshot already held a complete 2026-10-05 row; same-day row
# was blank/0.0. One observation → stamp kept at 15:00 UTC, ≥ 4 h before 15:00 ET (19/20 UTC).
FARSIDE_LIVE_HOUR_UTC = 15
FRAME_5M = Path("output/f011_forced_flow/frame_5m/BTCUSDT.csv.gz")


def parse_farside(path: Path) -> pd.DataFrame:
    """Trading-day rows only: a row whose issuer cells are all blank is a US market holiday
    (Farside prints Total 0.0 for it) and is dropped. Remaining blank issuer cells → 0."""
    d = pd.read_csv(path, parse_dates=["date"])
    issuers = [c for c in d.columns if c not in ("date", "Total")]
    holiday = d[issuers].isna().all(axis=1)
    d = d[~holiday].copy()
    d[issuers] = d[issuers].fillna(0.0)
    return d.sort_values("date").reset_index(drop=True)


def load_farside() -> pd.DataFrame:
    if FARSIDE_SRC.exists():
        FARSIDE_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        snap = pd.read_csv(FARSIDE_SRC, parse_dates=["date"])
        snap = snap[snap.date < pd.Timestamp("2025-03-08")]  # Train-1 + one week; nothing later kept
        snap.to_csv(FARSIDE_SNAPSHOT, index=False, date_format="%Y-%m-%d")
    return parse_farside(FARSIDE_SNAPSHOT)


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def et_to_utc(day: pd.Timestamp, hhmm: str) -> pd.Timestamp:
    """Wall-clock ET time on a calendar date → UTC (DST-aware)."""
    return pd.Timestamp(f"{pd.Timestamp(day).date()} {hhmm}", tz=ET).tz_convert("UTC")


def window_bars(bars: pd.DataFrame, day, start_et: str, end_et: str) -> pd.DataFrame:
    """5m bars whose bar-open lies in [start, end) ET on `day` (bars indexed by UTC open)."""
    a, b = et_to_utc(day, start_et), et_to_utc(day, end_et)
    return bars.loc[(bars.index >= a) & (bars.index < b)]


def window_stats(bars: pd.DataFrame, day, start_et: str, end_et: str, vol_col: str) -> dict:
    w = window_bars(bars, day, start_et, end_et)
    if len(w) == 0:
        return {"ret": np.nan, "vol": np.nan, "rv": np.nan, "hi": np.nan, "lo": np.nan, "n": 0}
    o, c = w.open.iloc[0], w.close.iloc[-1]
    lr = np.log(w.close / w.close.shift(1).fillna(w.open))
    return {"ret": np.log(c / o), "vol": float(w[vol_col].sum()), "rv": float(np.sqrt((lr**2).sum())),
            "hi": np.log(w.high.max() / o), "lo": np.log(w.low.min() / o), "n": len(w)}


def price_at(bars: pd.DataFrame, ts_utc: pd.Timestamp) -> float:
    """Last 5m close fully completed at or before ts_utc (bar open + 5m ≤ ts)."""
    s = bars.close.loc[: ts_utc - pd.Timedelta(minutes=5)]
    return float(s.iloc[-1]) if len(s) else np.nan


def coinbase_bars() -> pd.DataFrame:
    cb = fetch.coinbase_5m().set_index("timestamp")
    cb.index = pd.to_datetime(cb.index, utc=True)
    cb["usd_vol"] = cb.volume * cb.close
    return cb


def bybit_bars() -> pd.DataFrame:
    cols = ["timestamp", "open", "high", "low", "close", "turnover",
            "bn_open", "bn_high", "bn_low", "bn_close", "bn_quote_volume"]
    f = pd.read_csv(FRAME_5M, usecols=cols, parse_dates=["timestamp"]).set_index("timestamp")
    f.index = pd.to_datetime(f.index, utc=True)
    return f


def binance_bars(frame: pd.DataFrame) -> pd.DataFrame:
    b = frame[["bn_open", "bn_high", "bn_low", "bn_close", "bn_quote_volume"]].copy()
    b.columns = ["open", "high", "low", "close", "quote_volume"]
    return b.dropna()


def etf_daily() -> pd.DataFrame:
    """Per-date ETF regular-session dollar volume (sum of 5 largest) and IBIT close."""
    parts = []
    for t in fetch.ETFS:
        y = fetch.yahoo_daily(t).set_index("date")
        parts.append((y.close * y.volume).rename(f"dv_{t}"))
        if t == "IBIT":
            parts.append(y.close.rename("ibit_close"))
    d = pd.concat(parts, axis=1)
    d["etf_dollar_vol"] = d[[f"dv_{t}" for t in fetch.ETFS]].sum(axis=1)
    return d


def build_daily(far: pd.DataFrame, cb: pd.DataFrame) -> pd.DataFrame:
    """One row per US trading day T with target y and PIT-lagged observables.

    Every `*_lag` column is information fixed by T-1 16:00 ET (prior session close) or the
    prior Farside row, both live before T 15:00 UTC. `ovn_ret` (16:00 ET T-1 → 09:30 ET T)
    is a flagged pre-open input."""
    d = far[["date", "Total", "IBIT", "GBTC", "FBTC"]].rename(columns={"Total": "y"}).copy()
    d["btc_1600"] = [price_at(cb, et_to_utc(t, "16:00")) for t in d.date]
    d["btc_0930"] = [price_at(cb, et_to_utc(t, "09:30")) for t in d.date]
    etf = etf_daily()
    d = d.merge(etf[["etf_dollar_vol", "ibit_close"]], left_on="date", right_index=True, how="left")
    d["day_ret"] = np.log(d.btc_1600 / d.btc_1600.shift(1))  # 16:00 ET T-1 → T
    d["prem_raw"] = np.log(d.ibit_close / d.btc_1600)
    d["prem"] = d.prem_raw - d.prem_raw.rolling(20, min_periods=10).mean().shift(1)
    ldv = np.log(d.etf_dollar_vol)
    d["dv_z"] = (ldv - ldv.rolling(20, min_periods=10).mean().shift(1)) / ldv.rolling(20, min_periods=10).std().shift(1)
    d["y_lag1"] = d.y.shift(1)
    d["y_mean5"] = d.y.shift(1).rolling(5).mean()
    d["ibit_lag1"] = d.IBIT.shift(1)
    d["gbtc_lag1"] = d.GBTC.shift(1)
    d["ret_lag1"] = d.day_ret.shift(1)
    d["dvz_lag1"] = d.dv_z.shift(1)
    d["prem_lag1"] = d.prem.shift(1)
    d["ovn_ret"] = np.log(d.btc_0930 / d.btc_1600.shift(1))
    d["obs_live_utc"] = [pd.Timestamp(t, tz="UTC") + pd.Timedelta(hours=FARSIDE_LIVE_HOUR_UTC) for t in d.date]
    d["window_start_utc"] = [et_to_utc(t, "15:00") for t in d.date]
    d["in_train1"] = (d.date >= TRAIN1[0]) & (d.date < TRAIN1[1])
    return d
