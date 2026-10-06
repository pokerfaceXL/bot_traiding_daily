"""Causal, non-trading Train-1 frame; bar-open labels, bar-close availability."""
from __future__ import annotations

import argparse
import gzip
import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from forced_flow_lab.reduce_trades_5m import DiskGuard, SYMBOLS, atomic_write, sha256, verified

START = pd.Timestamp("2024-01-26", tz="UTC")
END = pd.Timestamp("2025-03-01", tz="UTC")
STEP = pd.Timedelta(minutes=5)
WINDOWS = {"oi_zscore": 2016, "funding_zscore": 2016, "realized_vol": 288, "atr": 14}
WARMUP = max(WINDOWS.values())
LIQUIDATIONS = ("liquidation_buy_vol", "liquidation_sell_vol", "liquidation_total_vol")
# Bybit-venue series that must be gapless and non-null post warm-up. The Binance
# bn_ layer is cross-venue robustness only; its gaps are listed, never fatal.
CORE_INPUTS = ("ohlcv", "oi", "ratio", "trades")
TAG = "20240126T000000Z_20250301T000000Z"


def grid(start=START, end=END):
    return pd.date_range(start, end, freq=STEP, inclusive="left", name="timestamp")


def indexed(path: Path, time_column="timestamp", unit=None):
    data = pd.read_csv(path)
    timestamps = pd.to_datetime(data.pop(time_column), unit=unit, utc=True)
    data.index = pd.DatetimeIndex(timestamps, name="timestamp")
    if data.index.has_duplicates or not data.index.is_monotonic_increasing:
        raise ValueError(f"Duplicate or unordered timestamps: {path}")
    return data


def zscore(series, window):
    rolling = series.rolling(window, min_periods=window)
    std = rolling.std(ddof=1)
    # Constant observed windows have zero z-score, not fabricated warm-up values.
    return ((series - rolling.mean()) / std.where(std != 0)).mask(std == 0, 0.0)


def compute_frame(inputs: dict[str, pd.DataFrame], index: pd.DatetimeIndex):
    """No future samples, backfills, or cross-venue substitution.

    Instantaneous OI/ratios/metrics use the bar-open snapshot. OHLCV/flow use
    that bar's completed interval; the entire row is available at close only.
    Funding is the latest settlement at or before bar open, with 8h maximum age.
    """
    aligned = {key: value.reindex(index) for key, value in inputs.items() if key != "funding"}
    frame = aligned["ohlcv"][["open", "high", "low", "close", "volume", "turnover"]].copy()
    frame["available_at"] = index + STEP
    frame["open_interest"] = aligned["oi"]["openInterest"]
    frame["long_account_share"] = aligned["ratio"]["buyRatio"]
    frame["short_account_share"] = aligned["ratio"]["sellRatio"]
    frame["long_short_ratio"] = frame.long_account_share / frame.short_account_share
    frame["long_short_ratio_change"] = frame.long_short_ratio.diff()
    funding = inputs["funding"].sort_index()
    frame["funding_rate"] = funding.funding_rate.reindex(index, method="ffill", tolerance=pd.Timedelta(hours=8) - pd.Timedelta(nanoseconds=1))
    settlement = pd.Series(funding.index, index=funding.index)
    frame["funding_source_timestamp"] = settlement.reindex(index, method="ffill", tolerance=pd.Timedelta(hours=8) - pd.Timedelta(nanoseconds=1))
    frame["funding_filled"] = ~index.isin(funding.index)
    frame["funding_age_minutes"] = (index.to_series() - frame.funding_source_timestamp).dt.total_seconds() / 60
    for column in ("taker_buy_vol", "taker_sell_vol", "ofi", "delta_cvd", "trade_count"):
        frame[column] = aligned["trades"][column]
    # Never propagate a daily-reset CVD level into the continuous series.
    frame["cvd"] = frame.delta_cvd.cumsum(skipna=False)
    for name in ("metrics", "klines"):
        for column in aligned[name].columns:
            frame[f"bn_{column}"] = aligned[name][column]
    for periods in (1, 3, 12):
        frame[f"return_{periods * 5}m"] = frame.close.pct_change(periods, fill_method=None)
    previous = frame.close.shift(1)
    true_range = pd.concat([frame.high - frame.low, (frame.high - previous).abs(),
                            (frame.low - previous).abs()], axis=1).max(axis=1)
    frame["atr"] = true_range.rolling(WINDOWS["atr"]).mean()
    frame["atr_normalized_return"] = frame.close.diff() / frame.atr
    frame["realized_vol"] = frame.return_5m.rolling(WINDOWS["realized_vol"]).std(ddof=1)
    frame["delta_oi"] = frame.open_interest.diff()
    frame["delta_oi_pct"] = frame.open_interest.pct_change(fill_method=None)
    frame["oi_zscore"] = zscore(frame.open_interest, WINDOWS["oi_zscore"])
    frame["oi_acceleration"] = frame.delta_oi.diff()
    frame["funding_zscore"] = zscore(frame.funding_rate, WINDOWS["funding_zscore"])
    frame["fuel"] = frame.delta_oi.abs() / frame.atr
    for side in ("buy", "sell"):
        frame[f"{side}_impact"] = frame.close.diff().abs() / frame[f"taker_{side}_vol"].where(frame[f"taker_{side}_vol"] != 0)
    for column in LIQUIDATIONS:
        frame[column] = pd.Series(np.nan, index=index, dtype="float64")
    frame["is_warmup"] = np.arange(len(index)) < WARMUP
    return frame


def quality(frame):
    post = frame.loc[~frame.is_warmup]
    exempt = list(LIQUIDATIONS) + [c for c in frame.columns if c.startswith("bn_")]
    core = post.drop(columns=exempt)
    numeric = core.select_dtypes(include=np.number)
    return {
        "rows": len(frame), "warmup_bars": int(frame.is_warmup.sum()),
        "post_warmup_core_nulls": {key: int(n) for key, n in core.isna().sum().items() if n},
        "post_warmup_core_infinite": {key: int(n) for key, n in np.isinf(numeric).sum().items() if n},
        "post_warmup_bn_nulls": {key: int(n) for key, n in post[[c for c in frame.columns if c.startswith('bn_')]].isna().sum().items() if n},
        "null_liquidations": {key: int(frame[key].isna().sum()) for key in LIQUIDATIONS},
        "funding_filled_bars": int(frame.funding_filled.sum()),
    }


def reconcile_hourly_oi(oi_5m: pd.Series, hourly: pd.Series) -> dict:
    """5m openInterest sampled at full hours must equal the cached 1h OI exactly."""
    sampled = oi_5m.reindex(hourly.index)
    if sampled.isna().any():
        missing = [t.isoformat() for t in hourly.index[sampled.isna()]]
        raise ValueError(f"5m OI missing {len(missing)} hourly timestamps, e.g. {missing[:3]}")
    difference = (sampled.to_numpy() - hourly.to_numpy())
    max_abs = float(np.abs(difference).max()) if len(difference) else 0.0
    if max_abs != 0.0:
        raise ValueError(f"5m/1h OI mismatch: max |diff|={max_abs}")
    return {"matched": int(len(hourly)), "max_abs_difference": max_abs}


def load_inputs(cache: Path, symbol: str):
    root = cache / "frame_5m_inputs"
    paths = {
        "ohlcv": root / f"{symbol}_ohlcv.csv",
        "oi": cache / "open_interest_5m" / f"{symbol}_oi_5min_{TAG}.csv",
        "ratio": cache / "account_ratio_5m" / f"{symbol}_account_ratio_5min_{TAG}.csv",
        "funding": cache / "funding" / f"{symbol}_funding_{TAG}.csv",
        "metrics": root / f"{symbol}_metrics.csv",
        "klines": root / f"{symbol}_klines.csv",
    }
    inputs = {key: indexed(path, unit="ms" if key in ("oi", "ratio") else None)
              for key, path in paths.items()}
    trades, manifests = [], []
    trade_root = cache / "bybit_trades_5m"
    for day in pd.date_range(START, END, freq="D", inclusive="left"):
        if not verified(trade_root, symbol, day.date()):
            raise ValueError(f"Unverified trade day: {symbol} {day.date()}")
        path = trade_root / f"{symbol}_{day.date()}.csv"
        trades.append(indexed(path))
        manifests.append(json.loads(path.with_suffix(".manifest.json").read_text()))
    inputs["trades"] = pd.concat(trades)
    source_hashes = {key: {"path": str(path), "sha256": sha256(path)} for key, path in paths.items()}
    # Compact, verifiable trade provenance: a digest over sorted day:sha256 lines
    # rather than 800 embedded per-day manifests.
    digest_lines = "".join(sorted(f"{m['day']}:{m['sha256']}\n" for m in manifests))
    trade_summary = {
        "days": len(manifests),
        "total_trade_count": sum(m["trade_count"] for m in manifests),
        "minimum_observed_free_bytes": min(m["minimum_observed_free_bytes"] for m in manifests),
        "days_with_empty_buckets": [m["day"] for m in manifests if m["empty_buckets"]],
        "per_day_checksum_digest_sha256": hashlib.sha256(digest_lines.encode()).hexdigest(),
    }
    return inputs, source_hashes, trade_summary


def build(cache: Path, output: Path, symbol: str):
    inputs, sources, trade_summary = load_inputs(cache, symbol)
    index = grid()
    gaps = {key: [t.isoformat() for t in index.difference(data.index)]
            for key, data in inputs.items() if key != "funding"}
    core_gaps = {key: gaps[key] for key in CORE_INPUTS if gaps.get(key)}
    for key, data in inputs.items():
        if data.index.has_duplicates:
            raise ValueError(f"Duplicate {key} index")
    hourly_path = cache / "open_interest" / f"{symbol}_oi_1h_{TAG}.csv"
    hourly = indexed(hourly_path)
    # Column name in the existing hourly cache is normalized to open_interest.
    if len(hourly) != 9600:
        raise ValueError(f"Expected 9600 hourly OI rows, got {len(hourly)}: {symbol}")
    reconciliation = reconcile_hourly_oi(inputs["oi"].openInterest, hourly.open_interest)
    sources["hourly_oi_reference"] = {"path": str(hourly_path), "sha256": sha256(hourly_path)}
    frame = compute_frame(inputs, index)
    stats = quality(frame)
    if core_gaps or stats["post_warmup_core_nulls"] or stats["post_warmup_core_infinite"]:
        raise ValueError(f"Incomplete core frame {symbol}: core_gaps="
                         f"{ {k: len(v) for k, v in core_gaps.items()} }, quality={stats}")
    output.mkdir(parents=True, exist_ok=True)
    guard = DiskGuard(output)
    payload = gzip.compress(frame.to_csv(index=True).encode(), mtime=0)
    path = output / f"{symbol}.csv.gz"
    atomic_write(path, payload, guard)
    manifest = {
        "symbol": symbol, "start": START.isoformat(), "end_exclusive": END.isoformat(),
        "sources": sources, "trade_reduction": trade_summary, "frame_sha256": sha256(path),
        "oi_convention": "Bybit openInterest, two-sided; equals cached hourly OI; never Binance",
        "availability": "bar-open timestamp; row known only at available_at=t+5m; state snapshots at t, completed candles/flow [t,t+5m)",
        "funding": "latest settlement <= bar open; strictly <8h old; no backfill",
        "cvd": "cumsum(delta_cvd), zero baseline at Train-1 start, never reset at midnight",
        "rolling_windows_bars": WINDOWS, "std_ddof": 1, "warmup_bars": WARMUP,
        "liquidations": "float64 null; no free Train-1 history, intentional completeness exception",
        "dtypes": {key: str(dtype) for key, dtype in frame.dtypes.items()},
        "bn_layer": "Binance cross-venue; prefixed bn_; may carry listed gaps/nulls; never substitutes Bybit OI",
        "gaps": gaps,
        "minimum_observed_trade_free_bytes": trade_summary["minimum_observed_free_bytes"],
        "hourly_oi_reconciliation": reconciliation,
        "quality": stats,
    }
    atomic_write(output / f"{symbol}.manifest.json", (json.dumps(manifest, indent=2) + "\n").encode(), guard)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data_cache"))
    parser.add_argument("--output", type=Path, default=Path("output/f011_forced_flow/frame_5m"))
    args = parser.parse_args()
    for symbol in SYMBOLS:
        manifest = build(args.cache_dir, args.output, symbol)
        print(json.dumps({"symbol": symbol, **manifest["quality"]}), flush=True)


if __name__ == "__main__":
    main()
