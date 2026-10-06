"""F012 · Daily Farside US spot BTC/ETH ETF flow snapshot (non-trading).

Re-fetches the public all-data HTML tables, parses issuer + Total columns with the
stdlib HTML parser (no lxml/pandas required at runtime), and writes/replaces a small
CSV per asset under out_dir. Point-in-time rule for research: treat a calendar day's
Total as known only after US cash close (see F012 doc).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from f012_collectors.disk_guard import allow_write

URLS = {
    "BTC": "https://farside.co.uk/bitcoin-etf-flow-all-data/",
    "ETH": "https://farside.co.uk/ethereum-etf-flow-all-data/",
}
DEFAULT_MAX_DIR_BYTES = 64 * 1024**2  # 64 MB — tables are tiny
DEFAULT_MIN_FREE_BYTES = 5 * 1024**3
UA = "limen-f012-collector/1.0 (research; contact via project owner)"


def iso_utc(ts_ms: int) -> str:
    return (
        datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z"
    )


def parse_flow_number(cell: str) -> Optional[float]:
    """Parse Farside cells like '655.3', '(95.1)', '-', '' into float $M or None."""
    if cell is None:
        return None
    s = str(cell).strip().replace(",", "")
    if s in ("", "-", "–", "—", "nan", "None"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if neg else val


class _TableParser(HTMLParser):
    """Collect raw cell text for every HTML table on the page."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: List[List[List[str]]] = []
        self._table: Optional[List[List[str]]] = None
        self._row: Optional[List[str]] = None
        self._cell: Optional[List[str]] = None
        self._in_cell = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            self._in_cell = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in ("td", "th") and self._in_cell and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell or [])).strip()
            self._row.append(text)
            self._cell = None
            self._in_cell = False
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            if self._table:
                self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._in_cell and self._cell is not None:
            self._cell.append(data)


def extract_largest_table(html: str) -> List[List[str]]:
    parser = _TableParser()
    parser.feed(html)
    if not parser.tables:
        raise ValueError("no <table> found in HTML")
    return max(parser.tables, key=lambda t: len(t) * max((len(r) for r in t), default=0))


def parse_farside_table(html: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Parse Farside all-data HTML into (headers, row dicts). Stdlib only."""
    table = extract_largest_table(html)
    if len(table) < 2:
        raise ValueError("table too small")
    headers = [h if h else f"col{i}" for i, h in enumerate(table[0])]
    if headers and (headers[0].startswith("Unnamed") or headers[0] in ("nan", "col0", "")):
        headers[0] = "Date"
    if "Date" not in headers:
        headers[0] = "Date"
    if "Total" not in headers:
        raise ValueError(f"Total column missing; columns={headers}")

    rows: List[Dict[str, Any]] = []
    for raw in table[1:]:
        # Pad short rows.
        cells = list(raw) + [""] * max(0, len(headers) - len(raw))
        date_raw = cells[0].strip()
        try:
            date = datetime.strptime(date_raw, "%d %b %Y").date().isoformat()
        except ValueError:
            continue
        rec: Dict[str, Any] = {"date": date}
        for col, cell in zip(headers[1:], cells[1:]):
            rec[col] = parse_flow_number(cell)
        rows.append(rec)
    return headers, rows


def rows_to_csv(headers: List[str], rows: List[Dict[str, Any]]) -> str:
    cols = ["date"] + [h for h in headers if h != "Date"]
    lines = [",".join(cols)]
    for r in rows:
        cells = [r["date"]]
        for h in cols[1:]:
            v = r.get(h)
            cells.append("" if v is None else f"{v}")
        lines.append(",".join(cells))
    return "\n".join(lines) + "\n"


def fetch_html(url: str, timeout: float = 60.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def run_once(
    out_dir: Path,
    assets: Optional[List[str]] = None,
    max_dir_bytes: int = DEFAULT_MAX_DIR_BYTES,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    fetch=fetch_html,
) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_ts_ms = int(time.time() * 1000)
    assets = assets or list(URLS)
    ok, reason = allow_write(
        out_dir, max_dir_bytes=max_dir_bytes, min_free_bytes=min_free_bytes
    )
    if not ok:
        return {"ok": False, "reason": reason, "run_ts_ms": run_ts_ms}

    results: Dict[str, Any] = {}
    for asset in assets:
        url = URLS[asset]
        html = fetch(url)
        headers, rows = parse_farside_table(html)
        csv_text = rows_to_csv(headers, rows)
        upcoming = len(csv_text.encode("utf-8"))
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
                "partial": results,
            }
        path = out_dir / f"farside_{asset}_flows.csv"
        path.write_text(csv_text, encoding="utf-8")
        results[asset] = {"path": str(path), "rows": len(rows)}

    meta = {
        "ok": True,
        "reason": "ok",
        "run_ts_ms": run_ts_ms,
        "run_ts": iso_utc(run_ts_ms),
        "assets": results,
    }
    (out_dir / "heartbeat.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    receipt = {
        "run_ts": meta["run_ts"],
        "urls": {a: URLS[a] for a in assets},
        "row_counts": {a: results[a]["rows"] for a in results},
    }
    (out_dir / "last_fetch.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
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
        / "etf_flows",
    )
    p.add_argument("--assets", nargs="+", default=["BTC", "ETH"], choices=list(URLS))
    p.add_argument("--max-dir-mb", type=float, default=64.0)
    p.add_argument("--min-free-gb", type=float, default=5.0)
    args = p.parse_args(argv)
    meta = run_once(
        args.out_dir,
        assets=args.assets,
        max_dir_bytes=int(args.max_dir_mb * 1024**2),
        min_free_bytes=int(args.min_free_gb * 1024**3),
    )
    print(json.dumps(meta, sort_keys=True))
    return 0 if meta.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
