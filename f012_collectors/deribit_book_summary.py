"""F012 · Slim Deribit option book-summary collector (non-trading, public, no key).

Fetches BTC/ETH option book summaries, keeps a slim PIT record per instrument, and
appends one gzipped JSONL line per run. Hard-capped disk use. Does not trade and does
not touch the F011 liquidation collector.

Schema (one JSON object per instrument row inside the run record):
  run_ts_ms, run_ts, currency, instrument_name, open_interest, mark_price,
  bid_price, ask_price, underlying_price, mark_iv, volume, creation_timestamp
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from f012_collectors.disk_guard import allow_write

DERIBIT_URL = (
    "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
    "?currency={currency}&kind=option"
)
KEEP_FIELDS = (
    "instrument_name",
    "open_interest",
    "mark_price",
    "bid_price",
    "ask_price",
    "underlying_price",
    "mark_iv",
    "volume",
    "creation_timestamp",
)
DEFAULT_CURRENCIES = ("BTC", "ETH")
# Owner: limen has ~31 GB free; hard-cap this collector tree at 2 GB and refuse
# writes if free space would fall below 5 GB.
DEFAULT_MAX_DIR_BYTES = 2 * 1024**3
DEFAULT_MIN_FREE_BYTES = 5 * 1024**3


def iso_utc(ts_ms: int) -> str:
    return (
        datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z"
    )


def utc_day(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")


def slim_row(raw: Dict[str, Any], currency: str, run_ts_ms: int) -> Dict[str, Any]:
    row = {
        "run_ts_ms": run_ts_ms,
        "run_ts": iso_utc(run_ts_ms),
        "currency": currency,
    }
    for key in KEEP_FIELDS:
        row[key] = raw.get(key)
    return row


def parse_book_summary_payload(
    payload: Dict[str, Any], currency: str, run_ts_ms: int
) -> List[Dict[str, Any]]:
    """Parse a Deribit JSON-RPC book-summary response into slim rows."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict")
    if payload.get("error"):
        raise ValueError(f"deribit error: {payload['error']}")
    result = payload.get("result")
    if result is None:
        raise ValueError("missing result")
    if not isinstance(result, list):
        raise ValueError("result must be a list")
    rows: List[Dict[str, Any]] = []
    for item in result:
        if not isinstance(item, dict):
            continue
        rows.append(slim_row(item, currency, run_ts_ms))
    return rows


def fetch_currency(currency: str, timeout: float = 30.0) -> Dict[str, Any]:
    url = DERIBIT_URL.format(currency=currency)
    req = urllib.request.Request(url, headers={"User-Agent": "limen-f012-collector/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def append_jsonl_gz(path: Path, records: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "ab") as fh:
        for rec in records:
            line = (json.dumps(rec, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
                "utf-8"
            )
            fh.write(line)
            n += 1
    return n


def run_once(
    out_dir: Path,
    currencies: Iterable[str] = DEFAULT_CURRENCIES,
    max_dir_bytes: int = DEFAULT_MAX_DIR_BYTES,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    fetch=fetch_currency,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    run_ts_ms = int(time.time() * 1000)
    ok, reason = allow_write(
        out_dir, max_dir_bytes=max_dir_bytes, min_free_bytes=min_free_bytes, upcoming_bytes=0
    )
    if not ok:
        return {"ok": False, "reason": reason, "run_ts_ms": run_ts_ms, "rows": 0}

    all_rows: List[Dict[str, Any]] = []
    errors: Dict[str, str] = {}
    for currency in currencies:
        try:
            payload = fetch(currency)
            all_rows.extend(parse_book_summary_payload(payload, currency, run_ts_ms))
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            errors[currency] = str(exc)

    # Estimate ~200 bytes/row compressed conservatively for the cap check.
    upcoming = max(4096, len(all_rows) * 200)
    ok, reason = allow_write(
        out_dir,
        max_dir_bytes=max_dir_bytes,
        min_free_bytes=min_free_bytes,
        upcoming_bytes=upcoming,
    )
    if not ok:
        return {
            "ok": False,
            "reason": reason,
            "run_ts_ms": run_ts_ms,
            "rows": 0,
            "errors": errors,
        }

    day = utc_day(run_ts_ms)
    path = out_dir / f"deribit_option_book_{day}.jsonl.gz"
    written = append_jsonl_gz(path, all_rows) if all_rows else 0
    meta = {
        "ok": True,
        "reason": "ok",
        "run_ts_ms": run_ts_ms,
        "run_ts": iso_utc(run_ts_ms),
        "path": str(path),
        "rows": written,
        "errors": errors,
    }
    heartbeat = out_dir / "heartbeat.json"
    heartbeat.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return meta


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path.home()
        / "bot_traiding_daily"
        / "bot_traiding_daily"
        / "data_cache"
        / "f012"
        / "deribit_book",
    )
    p.add_argument("--currencies", nargs="+", default=list(DEFAULT_CURRENCIES))
    p.add_argument("--max-dir-gb", type=float, default=2.0)
    p.add_argument("--min-free-gb", type=float, default=5.0)
    args = p.parse_args(argv)
    meta = run_once(
        args.out_dir,
        currencies=args.currencies,
        max_dir_bytes=int(args.max_dir_gb * 1024**3),
        min_free_bytes=int(args.min_free_gb * 1024**3),
    )
    print(json.dumps(meta, sort_keys=True))
    return 0 if meta.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
