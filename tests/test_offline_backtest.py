"""Testy offline dla backtest_apex.py — dane z lokalnego fixture, bez sieci."""

import runpy
import shutil
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "ohlcv_sample.csv"


def _block_network(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("Nieoczekiwane polaczenie sieciowe w trybie offline")
    monkeypatch.setattr(requests, "get", _raise)
    monkeypatch.setattr(requests, "post", _raise)


def _run_backtest_apex(tmp_path, monkeypatch, csv_path):
    """Uruchamia backtest_apex.py jak skrypt CLI, z CWD w tmp_path (relatywne sciezki wyjsciowe)."""
    (tmp_path / "configuration").mkdir()
    shutil.copy(REPO_ROOT / "configuration" / "default.yaml", tmp_path / "configuration" / "default.yaml")

    argv = [
        "backtest_apex.py",
        "configuration/default.yaml",
        "--local-csv", str(csv_path),
        "--strategies", "EMA_8_21",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.chdir(tmp_path)
    return runpy.run_path(str(REPO_ROOT / "backtest_apex.py"), run_name="__main__")


def test_offline_backtest_runs_without_network(tmp_path, monkeypatch):
    """Fixture z 600 swiecami wystarcza do przebiegu bez zadnego zapytania sieciowego."""
    _block_network(monkeypatch)

    _run_backtest_apex(tmp_path, monkeypatch, FIXTURE)

    report_dirs = list((tmp_path / "output" / "backtests").glob("*/report.json"))
    assert len(report_dirs) == 1


def test_offline_backtest_exits_nonzero_when_too_few_candles(tmp_path, monkeypatch):
    """Fixture z za mala liczba swiec (<500) musi konczyc proces kodem != 0."""
    _block_network(monkeypatch)

    tiny_csv = tmp_path / "tiny.csv"
    lines = FIXTURE.read_text().splitlines()
    tiny_csv.write_text("\n".join(lines[:11]) + "\n")  # naglowek + 10 swiec

    with pytest.raises(SystemExit) as exc_info:
        _run_backtest_apex(tmp_path, monkeypatch, tiny_csv)

    assert exc_info.value.code != 0
