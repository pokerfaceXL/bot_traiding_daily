import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_bb_20_25_entry_breakout_depth as experiment


def test_breakout_depth_gate_is_directional_inclusive_and_rejects_invalid_width():
    idx = pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {
            "close": [12.5, 12.49, 7.0, 7.01, 10.0, 10.0],
            "bb_20_2.5_upper": [12.0, 12.0, 12.0, 12.0, 10.0, 9.0],
            "bb_20_2.5_lower": [10.0, 10.0, 8.0, 8.0, 10.0, 10.0],
        },
        index=idx,
    )
    signal = pd.Series([1, 1, -1, -1, 1, -1], index=idx)

    gate = experiment.breakout_depth_gate(bars, signal, threshold=0.25)

    assert gate.tolist() == [True, False, True, False, False, False]
    assert gate.dtype == bool


def test_breakout_depth_entry_mask_intersects_gate_with_one_shot_entries():
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {
            "close": [12.5, 13.0, 11.0, 7.0, 7.0],
            "bb_20_2.5_upper": [12.0] * 5,
            "bb_20_2.5_lower": [8.0] * 5,
        },
        index=idx,
    )
    signal = pd.Series([1, 1, 0, -1, -1], index=idx)

    actual = experiment.breakout_depth_entry_mask(bars, signal, threshold=0.125)

    assert actual.tolist() == [True, False, False, True, False]


def test_control_gate_does_not_filter_one_shot_entries():
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    bars = pd.DataFrame(index=idx)
    signal = pd.Series([1, 1, 0, -1, -1], index=idx)

    actual = experiment.breakout_depth_entry_mask(bars, signal, threshold=None)

    pd.testing.assert_series_equal(actual, entry_masks.one_shot_entry_mask(signal))
