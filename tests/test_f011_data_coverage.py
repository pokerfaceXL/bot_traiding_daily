"""Small offline regressions for retained coverage evidence and optional pulls."""

import copy
import json
from pathlib import Path

from scripts import f011_data_coverage as m


OUT = Path(__file__).resolve().parents[1] / "output/f011_forced_flow/coverage"


def coverage():
    return json.loads((OUT / "coverage.json").read_text())


def test_spot_check_retains_exact_response(tmp_path, monkeypatch):
    responses = []

    def window(series, symbol, start, end, limit):
        response = {"retCode": 0, "time": 123, "result": {"symbol": symbol, "list": [
            {"timestamp": str(start), "openInterest": "42.00"}]}}
        responses.append(copy.deepcopy(response))
        return response

    monkeypatch.setattr(m, "bybit_window", window)
    raw = m.Raw(tmp_path / "raw")
    for symbol in m.SYMBOLS:
        spots = m.bybit_spot_check("oi_15min", symbol, raw)
        for spot, response in zip(spots.values(), responses[-2:]):
            assert json.loads((tmp_path / spot["raw_file"]).read_text()) == response
            assert spot["rows"] == 1
            assert spot["expected"] == 96
    assert len(raw.files) == len(set(raw.files)) == 4


def test_recommendation_and_report_without_full_pulls(tmp_path):
    cov = coverage()
    for ent in cov["bybit_rest"].values():
        ent.pop("train1_full_pull", None)
    rec, notes = m.auto_recommendation(cov)
    assert "already pulled" not in rec
    assert rec.count("full-window coverage unverified; full pull skipped") == 2
    assert "unverified (full pull skipped)" in " ".join(notes)
    m.finish(cov, tmp_path, rec, notes)
    assert (tmp_path / "report.md").read_text() == m.build_report(cov)


def test_refresh_only_fetches_four_spots(tmp_path, monkeypatch):
    cov = coverage()
    (tmp_path / "coverage.json").write_text(json.dumps(cov))
    calls = []

    def window(series, symbol, start, end, limit):
        calls.append((series, symbol, start, end))
        m.REQ_STATS["count"] += 1
        return {"retCode": 0, "result": {"list": [{"timestamp": str(start)}]}}

    monkeypatch.setattr(m, "bybit_window", window)
    refreshed, out = m.main(["--out", str(tmp_path), "--refresh-oi-spots"])
    assert out == tmp_path
    assert len(calls) == 4
    assert all(call[0]["val"] == "15min" for call in calls)
    assert refreshed["oi_spot_refresh"]["http_requests"] == 4
    assert refreshed["crosscheck"] == cov["crosscheck"]
    for row in refreshed["table"]:
        if row["source"] == "Bybit REST oi_15min":
            assert row["covered"] == "check"
            assert row["gaps"] == "spot: 2024-01-26 1/96, 2025-02-28 1/96"
    m.finish(refreshed, out, *m.auto_recommendation(refreshed))
    assert "4 additional HTTP requests" in (out / "report.md").read_text()


def test_committed_spot_counts_trace_to_retained_raw_and_report():
    cov = coverage()
    total_bytes = 0
    for symbol in m.SYMBOLS:
        spots = cov["bybit_rest"][f"oi_15min/{symbol}"]["train1_spot_check"]
        row = next(r for r in cov["table"] if r["source"] == "Bybit REST oi_15min" and r["symbol"] == symbol)
        for day, spot in spots.items():
            path = OUT / spot["raw_file"]
            total_bytes += path.stat().st_size
            raw = json.loads(path.read_text())
            assert raw["retCode"] == 0
            assert raw["result"]["symbol"] == symbol
            rows = m.bybit_rows(raw)
            assert spot["rows"] == len(rows)
            timestamps = {int(r["timestamp"]) for r in rows}
            assert len(timestamps) == len(rows)
            assert all(m.iso(t).startswith(day) for t in timestamps)
            assert spot["expected"] == m.DAY_MS // m.BYBIT_SERIES["oi_15min"]["step"]
            assert f"{day} {len(rows)}/{spot['expected']}" in row["gaps"]
            assert spot["raw_file"] in cov["raw_files"]
    assert total_bytes < 100_000
    assert (OUT / "report.md").read_text() == m.build_report(cov)
