"""Bounded-memory, one-raw-day Bybit trade reducer (research only).

Run: python -m forced_flow_lab.reduce_trades_5m --help
Bars are [timestamp, timestamp + 5m), available only at available_at.
CVD resets daily here; the frame builder must cumsum delta_cvd across days.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import gzip
import hashlib
import io
import json
import math
import shutil
import sys
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests

SYMBOLS = ("BTCUSDT", "ETHUSDT")
VERSION = 1
MIN_FREE_BYTES = 10 * 1024**3  # conservative: 10 GiB, not decimal GB
WRITE_HEADROOM = 16 * 1024**2
CHUNK_BYTES = 1024**2
ARCHIVE = "https://public.bybit.com/trading"
FIELDS = ("timestamp", "available_at", "taker_buy_vol", "taker_sell_vol",
          "ofi", "delta_cvd", "cvd_day", "trade_count")


class LowDiskSpace(RuntimeError):
    pass


class DiskGuard:
    def __init__(self, root: Path):
        self.root = root
        self.minimum_observed = None

    def check(self, write_bytes: int = 0) -> int:
        free = shutil.disk_usage(self.root).free
        self.minimum_observed = free if self.minimum_observed is None else min(self.minimum_observed, free)
        if free < MIN_FREE_BYTES + WRITE_HEADROOM + write_bytes:
            raise LowDiskSpace(f"free={free} bytes; need >= {MIN_FREE_BYTES + WRITE_HEADROOM + write_bytes}")
        return free


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def day_paths(root: Path, symbol: str, day: date):
    stem = root / f"{symbol}_{day.isoformat()}"
    return stem.with_suffix(".csv"), stem.with_suffix(".manifest.json")


def verified(root: Path, symbol: str, day: date) -> bool:
    output, manifest = day_paths(root, symbol, day)
    try:
        meta = json.loads(manifest.read_text())
        return (meta["version"] == VERSION and meta["symbol"] == symbol
                and meta["day"] == day.isoformat() and meta["rows"] == 288
                and meta["sha256"] == sha256(output))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def reduce_raw(raw: Path, symbol: str, day: date) -> tuple[bytes, dict]:
    """Read compressed CSV incrementally; retain only 288 bucket accumulators."""
    start = datetime.combine(day, time(), tzinfo=timezone.utc)
    epoch = int(start.timestamp())
    buy, sell, count = [0.0] * 288, [0.0] * 288, [0] * 288
    with gzip.open(raw, "rt", newline="") as fh:
        reader = csv.DictReader(fh)
        if not {"timestamp", "symbol", "side", "size"}.issubset(reader.fieldnames or []):
            raise ValueError("Bybit trade archive missing required columns")
        for row in reader:
            try:
                ts = Decimal(row["timestamp"])
            except InvalidOperation as exc:
                raise ValueError(f"Invalid trade timestamp: {row['timestamp']}") from exc
            size = float(row["size"])
            if (not ts.is_finite() or not epoch <= ts < epoch + 86400
                    or not math.isfinite(size) or size <= 0
                    or row["symbol"] != symbol or row["side"] not in ("Buy", "Sell")):
                raise ValueError(f"Invalid trade in {symbol} {day}: {row}")
            bucket = int((ts - epoch) // 300)
            (buy if row["side"] == "Buy" else sell)[bucket] += size
            count[bucket] += 1
    if not sum(count):
        raise ValueError("Empty trade archive")
    text = io.StringIO(newline="")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(FIELDS)
    cvd = 0.0
    gaps = []
    for i in range(288):
        timestamp = start + timedelta(minutes=5 * i)
        delta = buy[i] - sell[i]
        cvd += delta
        total = buy[i] + sell[i]
        if not all(math.isfinite(v) for v in (total, delta, cvd)):
            raise ValueError("Non-finite aggregate")
        if not count[i]:
            gaps.append(timestamp.isoformat())
        writer.writerow((timestamp.isoformat(), (timestamp + timedelta(minutes=5)).isoformat(),
                         buy[i], sell[i], delta / total if total else 0.0, delta, cvd, count[i]))
    return text.getvalue().encode(), {"rows": 288, "trade_count": sum(count), "empty_buckets": gaps}


def atomic_write(path: Path, payload: bytes, guard: DiskGuard):
    partial = path.with_name(path.name + ".part")
    try:
        guard.check(len(payload))
        with partial.open("wb", buffering=0) as fh:
            fh.write(payload)
        partial.replace(path)
        guard.check()
    finally:
        partial.unlink(missing_ok=True)


def process_day(root: Path, symbol: str, day: date, session, guard: DiskGuard) -> dict:
    guard.minimum_observed = None
    before = guard.check()
    if verified(root, symbol, day):
        return {"symbol": symbol, "day": str(day), "status": "verified-skip", "free_bytes": before}
    url = f"{ARCHIVE}/{symbol}/{symbol}{day.isoformat()}.csv.gz"
    raw = root / ".raw-day.csv.gz"
    digest, downloaded = hashlib.sha256(), 0
    output, manifest = day_paths(root, symbol, day)
    # Invalidate the commit marker before replacing an unverified day.
    manifest.unlink(missing_ok=True)
    try:
        with session.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            with raw.open("wb", buffering=0) as fh:
                for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
                    if not chunk:
                        continue
                    guard.check(len(chunk))
                    fh.write(chunk)
                    digest.update(chunk)
                    downloaded += len(chunk)
                    guard.check()
        payload, stats = reduce_raw(raw, symbol, day)
        atomic_write(output, payload, guard)
        raw.unlink()  # raw must be gone before the manifest marks this day complete
        meta = {
            "version": VERSION, "symbol": symbol, "day": str(day), "source": url,
            "source_sha256": digest.hexdigest(), "source_bytes": downloaded,
            "sha256": hashlib.sha256(payload).hexdigest(), **stats,
            "bar_convention": "[timestamp, available_at); available only at bar close",
            "volume_unit": "base asset; side is taker side",
            "cvd_convention": "cvd_day resets at UTC midnight; cumsum delta_cvd for full-range CVD",
            "empty_bucket_convention": "zero volume/count/OFI; explicitly listed, not imputed trades",
            "disk_guard_bytes": MIN_FREE_BYTES, "write_headroom_bytes": WRITE_HEADROOM,
            "minimum_observed_free_bytes": guard.minimum_observed,
        }
        atomic_write(manifest, (json.dumps(meta, indent=2) + "\n").encode(), guard)
        return {"symbol": symbol, "day": str(day), "status": "written", **stats,
                "minimum_observed_free_bytes": guard.minimum_observed}
    finally:
        raw.unlink(missing_ok=True)


def run(root: Path, symbols, start: date, end: date, session, emit=print):
    """Exclusive cache lock covers both symbols, recovery, download and publication."""
    if start >= end or not symbols or any(s not in SYMBOLS for s in symbols):
        raise ValueError("Require BTCUSDT/ETHUSDT and start < end (exclusive)")
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".reducer.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError(f"Another reducer owns {root}") from exc
        # Recover only files owned by this reducer, including after SIGKILL.
        (root / ".raw-day.csv.gz").unlink(missing_ok=True)
        for symbol in SYMBOLS:
            for partial in root.glob(f"{symbol}_*.part"):
                partial.unlink()
        guard = DiskGuard(root)
        day = start
        while day < end:
            for symbol in symbols:
                emit(json.dumps(process_day(root, symbol, day, session, guard), sort_keys=True))
            day += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path("data_cache/bybit_trades_5m"))
    parser.add_argument("--symbols", nargs="+", choices=SYMBOLS, default=list(SYMBOLS))
    parser.add_argument("--start", type=date.fromisoformat, default=date(2024, 1, 26))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2025, 3, 1), help="exclusive UTC day")
    args = parser.parse_args()
    try:
        with requests.Session() as session:
            run(args.cache_dir, args.symbols, args.start, args.end, session,
                emit=lambda line: print(line, flush=True))
    except (OSError, EOFError, ValueError, RuntimeError, requests.RequestException) as exc:
        print(json.dumps({"status": "stopped", "reason": str(exc)}), file=sys.stderr, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
