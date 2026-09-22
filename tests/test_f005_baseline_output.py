"""
Smoke test for F005 wave 3: confirms the baseline measurement's report and
summary output files were actually produced with the expected shape, not
that the measured numbers are any particular value (that's spec/research/
F005-baseline.md's job, this is just "did the run leave the artifacts it
claims to have left").
"""
import csv
import json
import os

import pytest

SUMMARY_DIR = "output/f005_baseline/summary"
RAW_DIR = "output/f005_baseline/raw"

pytestmark = pytest.mark.skipif(
    not os.path.isdir(SUMMARY_DIR), reason="F005 wave 3 baseline output not present in this checkout"
)


def test_validation_and_holdout_summaries_have_one_row_per_symbol_interval_strategy():
    for name in ("validation_summary.csv", "holdout_summary.csv"):
        with open(os.path.join(SUMMARY_DIR, name)) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 790
        assert {r["symbol"] for r in rows} == {"SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"}
        assert {r["interval"] for r in rows} == {"240", "60"}


def test_manifest_records_790_runs_and_verified_checksums():
    with open(os.path.join(SUMMARY_DIR, "manifest.json")) as f:
        manifest = json.load(f)
    assert manifest["n_runs"] == 790
    assert manifest["n_strategies"] == 79
    assert len(manifest["data_checksums_verified"]) == 10


def test_global_extremes_has_attribution_for_worst_month_day_and_streak():
    with open(os.path.join(SUMMARY_DIR, "global_extremes.json")) as f:
        extremes = json.load(f)
    for key in ("worst_month", "worst_day", "longest_losing_streak"):
        record = extremes[key]
        assert record["symbol"]
        assert record["interval"]
        assert record["strategy"]


def test_raw_per_run_files_exist_for_every_combination():
    if not os.path.isdir(RAW_DIR):
        pytest.skip("raw output is local-disk-only, not committed (see .gitignore)")
    files = os.listdir(RAW_DIR)
    assert len(files) == 790
