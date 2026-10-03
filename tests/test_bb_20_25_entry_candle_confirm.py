import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_bb_20_25_entry_candle_confirm as experiment


def test_candle_confirmation_gate_is_directional_inclusive_and_rejects_zero_range():
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {
            "high": [10.0, 10.0, 10.0, 10.0, 7.0],
            "low": [0.0, 0.0, 0.0, 0.0, 7.0],
            "close": [6.0, 4.0, 4.0, 6.0, 7.0],
        },
        index=idx,
    )
    signal = entry_masks.normalized_signal(pd.Series([1, 1, -1, -1, 1], index=idx))

    gate = experiment.candle_confirmation_gate(bars, signal, threshold=0.60)

    assert gate.tolist() == [True, False, True, False, False]
    assert gate.dtype == bool


def test_control_gate_does_not_filter_one_shot_entries():
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {"high": [1.0] * 5, "low": [1.0] * 5, "close": [1.0] * 5},
        index=idx,
    )
    signal = pd.Series([1, 1, 0, -1, -1], index=idx)

    actual = experiment.candle_confirmation_entry_mask(bars, signal, threshold=None)

    pd.testing.assert_series_equal(actual, entry_masks.one_shot_entry_mask(signal))
