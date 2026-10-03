import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_bb_20_2_entry_breakout_depth as experiment


def test_card_targets_bb_20_2_baseline_not_bb_20_25():
    assert experiment.CONTROL_NAME == "BB_20_2_EMA200"
    assert experiment.EXPECTED_MEAN == 95.3217987
    assert experiment.EXPECTED_MEAN != 82.900262
    assert experiment.EXPECTED_COHORT_N == 756
    assert experiment.THRESHOLDS == (0.02, 0.05, 0.10, 0.25, 0.50)
    assert experiment.BIG_WINNER_THRESHOLD == 29.9
    assert experiment.OUT.name == "f006_bb_20_2_entry_breakout_depth"
    assert (experiment.UPPER, experiment.LOWER) == ("bb_20_2.0_upper", "bb_20_2.0_lower")


def test_gate_reads_k20_bands_not_k25_bands_or_width_ratio():
    idx = pd.date_range("2024-01-01", periods=6, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {
            "close": [12.5, 12.49, 7.0, 7.01, 10.0, 10.0],
            "bb_20_2.0_upper": [12.0, 12.0, 12.0, 12.0, 10.0, 9.0],
            "bb_20_2.0_lower": [10.0, 10.0, 8.0, 8.0, 10.0, 10.0],
            # Decoys that would flip every row if the gate read them.
            "bb_20_2.5_upper": [100.0] * 6,
            "bb_20_2.5_lower": [-100.0] * 6,
            "bb_20_2.0_width": [0.0] * 6,
        },
        index=idx,
    )
    signal = pd.Series([1, 1, -1, -1, 1, -1], index=idx)

    gate = experiment.breakout_depth_gate(bars, signal, threshold=0.25)

    assert gate.tolist() == [True, False, True, False, False, False]
    assert gate.dtype == bool
    k20_only = bars[["close", "bb_20_2.0_upper", "bb_20_2.0_lower"]]
    assert experiment.breakout_depth_gate(k20_only, signal, threshold=0.25).tolist() == gate.tolist()


def test_entry_mask_intersects_gate_with_one_shot_and_control_is_ungated():
    idx = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    bars = pd.DataFrame(
        {"close": [12.5, 13.0, 11.0, 7.0, 7.0], "bb_20_2.0_upper": [12.0] * 5, "bb_20_2.0_lower": [8.0] * 5},
        index=idx,
    )
    signal = pd.Series([1, 1, 0, -1, -1], index=idx)

    actual = experiment.breakout_depth_entry_mask(bars, signal, threshold=0.125)

    assert actual.tolist() == [True, False, False, True, False]
    pd.testing.assert_series_equal(
        experiment.breakout_depth_entry_mask(bars, signal, threshold=None),
        entry_masks.one_shot_entry_mask(signal),
    )
