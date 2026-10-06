"""Unit tests for Farside ETF flow HTML parser (offline)."""

from __future__ import annotations

from pathlib import Path

from f012_collectors.farside_etf_flows import (
    parse_flow_number,
    parse_farside_table,
    run_once,
)

SAMPLE_HTML = """
<html><body>
<table>
  <thead><tr><th>Date</th><th>IBIT</th><th>FBTC</th><th>GBTC</th><th>Total</th></tr></thead>
  <tbody>
    <tr><td>11 Jan 2024</td><td>111.7</td><td>227.0</td><td>(95.1)</td><td>655.3</td></tr>
    <tr><td>12 Jan 2024</td><td>386.0</td><td>195.3</td><td>(484.1)</td><td>203.0</td></tr>
    <tr><td>06 Oct 2026</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
    <tr><td>Total</td><td>1</td><td>2</td><td>3</td><td>4</td></tr>
  </tbody>
</table>
</body></html>
"""


def test_parse_flow_number():
    assert parse_flow_number("655.3") == 655.3
    assert parse_flow_number("(95.1)") == -95.1
    assert parse_flow_number("-") is None
    assert parse_flow_number("1,373.8") == 1373.8


def test_parse_farside_table():
    headers, rows = parse_farside_table(SAMPLE_HTML)
    assert "Total" in headers
    assert rows[0]["date"] == "2024-01-11"
    assert rows[0]["Total"] == 655.3
    assert rows[0]["GBTC"] == -95.1
    assert rows[1]["date"] == "2024-01-12"
    # placeholder day kept with None totals
    assert rows[2]["date"] == "2026-10-06"
    assert rows[2]["Total"] is None
    # 'Total' footer row is not a date — excluded
    assert all(r["date"] != "Total" for r in rows)


def test_run_once_writes_csv(tmp_path: Path):
    def fake_fetch(url: str) -> str:
        return SAMPLE_HTML

    meta = run_once(
        tmp_path,
        assets=["BTC"],
        max_dir_bytes=10_000_000,
        min_free_bytes=1,
        fetch=fake_fetch,
    )
    assert meta["ok"] is True
    path = Path(meta["assets"]["BTC"]["path"])
    text = path.read_text(encoding="utf-8")
    assert "2024-01-11" in text
    assert "655.3" in text
