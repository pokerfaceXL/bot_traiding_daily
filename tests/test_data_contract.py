import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_contract as dc

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "ohlcv_sample_gap.csv")
INTERVAL = "240"


def load_fixture():
    df = pd.read_csv(FIXTURE, index_col=0, parse_dates=True)
    return df


def test_fixture_has_a_deliberate_gap():
    df = load_fixture()
    gaps = dc.detect_gaps(df, INTERVAL)
    assert len(gaps) == 1
    assert gaps[0].missing_bars == 3


def test_filter_closed_candles_drops_currently_forming_bar():
    df = load_fixture()
    last_open = df.index[-1]
    now = last_open + pd.Timedelta(hours=1)  # bar still open (needs +4h to close)
    closed, dropped = dc.filter_closed_candles(df, INTERVAL, now=now)
    assert dropped == 1
    assert closed.index[-1] == df.index[-2]


def test_filter_closed_candles_keeps_bar_once_closed():
    df = load_fixture()
    last_open = df.index[-1]
    now = last_open + pd.Timedelta(hours=4)
    closed, dropped = dc.filter_closed_candles(df, INTERVAL, now=now)
    assert dropped == 0
    assert closed.index[-1] == df.index[-1]


def test_build_manifest_reports_coverage_and_checksum():
    df = load_fixture()
    manifest = dc.build_manifest(
        "BTCUSDT", INTERVAL, df,
        requested_start=df.index[0], requested_end=df.index[-1],
    )
    assert manifest.row_count == 20
    assert len(manifest.gaps) == 1
    assert manifest.coverage_pct < 100.0
    assert len(manifest.checksum_sha256) == 64


def test_enforce_no_silent_gaps_raises_by_default():
    df = load_fixture()
    manifest = dc.build_manifest("BTCUSDT", INTERVAL, df, df.index[0], df.index[-1])
    with pytest.raises(dc.DataGapError):
        dc.enforce_no_silent_gaps(manifest)


def test_enforce_no_silent_gaps_allows_explicit_opt_in():
    df = load_fixture()
    manifest = dc.build_manifest("BTCUSDT", INTERVAL, df, df.index[0], df.index[-1])
    dc.enforce_no_silent_gaps(manifest, allow_gaps=True)  # must not raise


def test_split_warmup_excludes_leading_bars_from_usable_set():
    df = load_fixture()
    warmup, usable = dc.split_warmup(df, warmup_bars=5)
    assert len(warmup) == 5
    assert len(usable) == 15
    assert usable.index[0] == df.index[5]


def test_build_dataset_end_to_end_no_gaps_slice(tmp_path):
    df = load_fixture()
    # slice without the injected gap (bars 0..9 are contiguous)
    clean = df.iloc[:10]
    usable, manifest = dc.build_dataset(
        "BTCUSDT", INTERVAL, clean,
        start=clean.index[0], end=clean.index[-1],
        warmup_bars=2, now=clean.index[-1] + pd.Timedelta(hours=4),
        cache_dir=str(tmp_path), allow_gaps=False,
    )
    assert manifest.gaps == []
    assert len(usable) == len(clean) - 2
    csv_path, manifest_path = dc._dataset_paths(str(tmp_path), "BTCUSDT", INTERVAL, clean.index[0], clean.index[-1])
    assert os.path.exists(csv_path)
    assert os.path.exists(manifest_path)


def test_build_dataset_raises_on_gap_without_opt_in(tmp_path):
    df = load_fixture()
    with pytest.raises(dc.DataGapError):
        dc.build_dataset(
            "BTCUSDT", INTERVAL, df,
            start=df.index[0], end=df.index[-1],
            now=df.index[-1] + pd.Timedelta(hours=4),
            cache_dir=str(tmp_path),
        )


def test_load_dataset_detects_tampered_cache(tmp_path):
    df = load_fixture().iloc[:10]
    usable, manifest = dc.build_dataset(
        "BTCUSDT", INTERVAL, df,
        start=df.index[0], end=df.index[-1],
        now=df.index[-1] + pd.Timedelta(hours=4),
        cache_dir=str(tmp_path),
    )
    csv_path, _ = dc._dataset_paths(str(tmp_path), "BTCUSDT", INTERVAL, df.index[0], df.index[-1])
    with open(csv_path, "a") as f:
        f.write("2099-01-01,1,1,1,1,1\n")
    with pytest.raises(dc.DataContractError):
        dc.load_dataset(str(tmp_path), "BTCUSDT", INTERVAL, df.index[0], df.index[-1])


def test_load_dataset_missing_cache_raises(tmp_path):
    with pytest.raises(dc.DataContractError):
        dc.load_dataset(str(tmp_path), "BTCUSDT", INTERVAL, "2026-01-01", "2026-01-02")
