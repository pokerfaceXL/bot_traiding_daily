"""Unit tests for Deribit book-summary parser (offline)."""

from __future__ import annotations

import json
from pathlib import Path

from f012_collectors.deribit_book_summary import (
    parse_book_summary_payload,
    run_once,
    slim_row,
)


SAMPLE = {
    "jsonrpc": "2.0",
    "result": [
        {
            "instrument_name": "BTC-27MAR26-100000-C",
            "open_interest": 12.5,
            "mark_price": 0.01,
            "bid_price": 0.009,
            "ask_price": 0.011,
            "underlying_price": 86000.0,
            "mark_iv": 50.0,
            "volume": 1.0,
            "creation_timestamp": 1700000000000,
            "extra_ignored": True,
        },
        {
            "instrument_name": "BTC-27MAR26-90000-P",
            "open_interest": 3.0,
            "mark_price": 0.02,
            "bid_price": None,
            "ask_price": 0.025,
            "underlying_price": 86000.0,
            "mark_iv": 55.0,
            "volume": 0.0,
            "creation_timestamp": 1700000000001,
        },
    ],
}


def test_slim_row_keeps_only_schema_fields():
    row = slim_row(SAMPLE["result"][0], "BTC", 1_700_000_000_000)
    assert row["currency"] == "BTC"
    assert row["instrument_name"] == "BTC-27MAR26-100000-C"
    assert row["open_interest"] == 12.5
    assert "extra_ignored" not in row
    assert row["run_ts"].endswith("Z")


def test_parse_book_summary_payload():
    rows = parse_book_summary_payload(SAMPLE, "BTC", 1_700_000_000_000)
    assert len(rows) == 2
    assert rows[1]["instrument_name"].endswith("-P")


def test_parse_rejects_error_payload():
    try:
        parse_book_summary_payload({"error": {"message": "nope"}}, "BTC", 1)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "deribit error" in str(exc)


def test_run_once_writes_gz(tmp_path: Path):
    def fake_fetch(currency: str):
        return SAMPLE if currency == "BTC" else {"result": []}

    meta = run_once(
        tmp_path,
        currencies=["BTC", "ETH"],
        max_dir_bytes=10_000_000,
        min_free_bytes=1,  # floor effectively disabled in tmpfs tests
        fetch=fake_fetch,
    )
    assert meta["ok"] is True
    assert meta["rows"] == 2
    path = Path(meta["path"])
    assert path.exists()
    # gunzip via stdlib
    import gzip

    lines = gzip.open(path, "rt", encoding="utf-8").read().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["currency"] == "BTC"
