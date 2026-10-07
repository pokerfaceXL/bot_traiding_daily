"""F014 data loading: Train-1 files only (warmup + discovery). Validation/holdout never loaded.

OHLCV 1h and the 5m account ratio are gitignored, so the data root is configurable
(`--data-root` / env F014_DATA_ROOT); funding and OI 1h are committed under data_cache/.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pandas as pd

from alpha_discovery_lab.registry import SPLITS

REPO = Path(__file__).resolve().parent.parent
TRAIN1 = "20240126T000000Z_20250301T000000Z"
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
T_START = pd.Timestamp(SPLITS["warmup"][0])
T_END = pd.Timestamp(SPLITS["discovery"][1])  # exclusive; == validation start


def data_root(arg: str | None = None) -> Path:
    return Path(arg or os.environ.get("F014_DATA_ROOT") or REPO / "data_cache")


def paths(root: Path, sym: str) -> dict[str, Path]:
    return {
        "ohlcv": root / f"{sym}_60_{TRAIN1}.csv",
        "funding": root / "funding" / f"{sym}_funding_{TRAIN1}.csv",
        "oi_1h": root / "open_interest" / f"{sym}_oi_1h_{TRAIN1}.csv",
        "account_ratio_5m": root / "account_ratio_5m" / f"{sym}_account_ratio_5min_{TRAIN1}.csv",
    }


def _clip(df: pd.DataFrame) -> pd.DataFrame:
    """Hard guard: never keep a row at/after the validation start."""
    df = df[(df.index >= T_START) & (df.index < T_END)]
    assert df.index.max() < T_END
    return df


def load_ohlcv(root: Path, sym: str) -> pd.DataFrame:
    df = pd.read_csv(paths(root, sym)["ohlcv"])
    df.index = pd.to_datetime(df.pop("timestamp"), utc=True)
    return _clip(df.sort_index()[["open", "high", "low", "close", "volume"]].astype(float))


def load_funding(root: Path, sym: str) -> pd.Series:
    df = pd.read_csv(paths(root, sym)["funding"])
    s = pd.Series(df["funding_rate"].astype(float).values, index=pd.to_datetime(df["timestamp"], utc=True))
    return _clip(s.sort_index().to_frame("f"))["f"]


def load_oi(root: Path, sym: str) -> pd.Series:
    df = pd.read_csv(paths(root, sym)["oi_1h"])
    s = pd.Series(df["open_interest"].astype(float).values, index=pd.to_datetime(df["timestamp"], utc=True))
    return _clip(s.sort_index().to_frame("oi"))["oi"]


def load_buyratio(root: Path, sym: str) -> pd.Series | None:
    p = paths(root, sym)["account_ratio_5m"]
    if not p.exists():
        return None
    df = pd.read_csv(p)
    s = pd.Series(df["buyRatio"].astype(float).values, index=pd.to_datetime(df["time_utc"], utc=True))
    return _clip(s.sort_index().to_frame("br"))["br"]


def align_aux(bar_index: pd.DatetimeIndex, s: pd.Series | None) -> pd.Series:
    """Attach the last aux row with timestamp <= bar-open timestamp (registry aux_alignment rule)."""
    if s is None or s.empty:
        return pd.Series(float("nan"), index=bar_index)
    s = s[~s.index.duplicated(keep="last")]
    return s.reindex(s.index.union(bar_index)).ffill().reindex(bar_index)


def load_asset(root: Path, sym: str) -> pd.DataFrame:
    """1h frame with aligned aux columns: funding, oi, buyratio (NaN when missing)."""
    df = load_ohlcv(root, sym)
    p = paths(root, sym)
    df["funding"] = align_aux(df.index, load_funding(root, sym) if p["funding"].exists() else None)
    df["oi"] = align_aux(df.index, load_oi(root, sym) if p["oi_1h"].exists() else None)
    df["buyratio"] = align_aux(df.index, load_buyratio(root, sym))
    return df


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path) -> dict:
    """File-level inventory (row counts, ranges, hashes). Reads no returns; scores nothing."""
    out: dict = {"data_root": str(root), "window": [str(T_START), str(T_END)], "files": {}, "gaps": []}
    for sym in SYMBOLS:
        for kind, p in paths(root, sym).items():
            key = f"{sym}/{kind}"
            if not p.exists():
                out["files"][key] = {"present": False}
                out["gaps"].append(f"{key}: missing ({p.name})")
                continue
            df = pd.read_csv(p)
            tcol = "time_utc" if "time_utc" in df.columns else "timestamp"
            ts = pd.to_datetime(df[tcol], utc=True)
            out["files"][key] = {"present": True, "path": str(p), "rows": int(len(df)),
                                 "first": str(ts.min()), "last": str(ts.max()), "sha256": _sha(p)}
    out["gaps"] += [
        "liquidations/bybit: live only from ~2026-10-05 -> not usable for Train-1 discovery (collector untouched)",
        "5m OHLCV: only 2-day samples -> primary bar is 1h",
        "account_ratio_5m and open_interest_5m: BTC/ETH only (no SOL) -> Family C has no bonus asset",
        "f012 deribit/etf: preserved read-only, not used",
        "funding / OI: Train-1 only -> Family B and H-TIME-FUNDING-HOUR cannot be re-scored on validation "
        "without a new discovery-window-safe fetch (not done here)",
    ]
    return out
