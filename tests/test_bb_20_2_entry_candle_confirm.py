import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import f006_bb_20_2_entry_candle_confirm as experiment


def test_card_targets_bb_20_2_baseline_not_bb_20_25():
    assert experiment.CONTROL_NAME == "BB_20_2_EMA200"
    assert experiment.EXPECTED_MEAN == 95.3217987
    assert experiment.EXPECTED_COHORT_N == 756
    assert experiment.THRESHOLDS == (0.50, 0.60, 0.70, 0.80, 0.90)
    assert experiment.BIG_WINNER_THRESHOLD == 29.9
    assert experiment.OUT.name == "f006_bb_20_2_entry_candle_confirm"
