import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_bb_20_2_entry_htf_direction as experiment


def _bars(opens, closes, start="2024-01-01", freq="h"):
    idx = pd.date_range(start, periods=len(opens), freq=freq, tz="UTC")
    return pd.DataFrame({"open": opens, "close": closes}, index=idx)


def test_card_targets_bb_20_2_baseline_not_bb_20_25():
    assert experiment.CONTROL_NAME == "BB_20_2_EMA200"
    assert experiment.EXPECTED_MEAN == 95.3217987
    assert experiment.EXPECTED_MEAN != 82.900262
    assert experiment.EXPECTED_COHORT_N == 756
    assert experiment.EXPECTED_LOSING_MONTHS == 7
    assert experiment.EXPECTED_BIG_WINNER_N == 12
    assert experiment.BIG_WINNER_THRESHOLD == 29.9
    assert experiment.HTF_BARS == 4
    assert experiment.OUT.name == "f006_bb_20_2_entry_htf_direction"
    assert experiment.CONTROL_REFERENCE.parent.name == "f006_bb_20_2_entry_breakout_depth"


def test_gate_ignores_k25_bands_atr_candle_strength_and_depth():
    opens = [10, 11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2]
    closes = [11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2, 9]
    bars = _bars(opens, closes)
    signal = pd.Series([1, -1] * 6, index=bars.index)
    decorated = bars.assign(**{
        # Decoys that would change the result if the gate read them.
        "high": 1e9, "low": -1e9,
        "bb_20_2.5_upper": 1e9, "bb_20_2.5_lower": -1e9,
        "bb_20_2.0_upper": 1e9, "bb_20_2.0_lower": -1e9, "bb_20_2.0_width": 0.0,
        "atr_14": 0.0, "atr_pct": 0.0, "ema_200": 1e9,
    })

    gate = experiment.htf_direction_gate(decorated, signal, 60)

    pd.testing.assert_series_equal(gate, experiment.htf_direction_gate(bars, signal, 60))
    assert gate.tolist() == [False] * 4 + [True, False] * 2 + [False, True] * 2


def test_agreement_keeps_long_on_up_and_short_on_down():
    opens = [10, 11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2]
    closes = [11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2, 9]
    bars = _bars(opens, closes)

    direction = experiment.htf_direction(bars, 60)

    assert direction.tolist() == [0] * 4 + [1] * 4 + [-1] * 4
    long = pd.Series(1, index=bars.index)
    assert experiment.htf_direction_gate(bars, long, 60).tolist() == [False] * 4 + [True] * 4 + [False] * 4
    assert experiment.htf_direction_gate(bars, -long, 60).tolist() == [False] * 8 + [True] * 4


def test_flat_prior_bucket_rejects_both_directions():
    bars = _bars([10, 11, 12, 13, 5, 5, 5, 5], [11, 12, 13, 10, 5, 5, 5, 5])
    long = pd.Series([0, 0, 0, 0, 1, 0, 0, 0], index=bars.index)

    assert experiment.htf_direction(bars, 60).iloc[4] == 0
    assert not experiment.htf_direction_gate(bars, long, 60).iloc[4]
    assert not experiment.htf_direction_gate(bars, -long, 60).iloc[4]


def test_incomplete_prior_bucket_rejects():
    bars = _bars([10, 11, 12, 13, 14, 15, 16, 17], [11, 12, 13, 14, 15, 16, 17, 18])
    gapped = bars.drop(bars.index[2])  # bucket 00:00 has only 3 native bars
    signal = pd.Series(1, index=gapped.index)

    assert experiment.htf_direction(gapped, 60).iloc[3:].tolist() == [0, 0, 0, 0]
    assert not experiment.htf_direction_gate(gapped, signal, 60).iloc[3:].any()
    assert experiment.htf_direction(bars, 60).iloc[4:].tolist() == [1, 1, 1, 1]


def test_signal_bar_never_inside_its_htf_bucket_even_when_last_bar():
    # Bucket 00:00 falls; bucket 04:00 rallies and its last bar (07:00) is the
    # signal bar. Only bucket 00:00 (closed at 04:00 <= 07:00) may be used.
    bars = _bars([10, 9, 8, 7, 6, 20, 30, 40], [9, 8, 7, 6, 20, 30, 40, 50])
    signal = pd.Series([0, 0, 0, 0, 0, 0, 0, 1], index=bars.index)

    assert not experiment.htf_direction_gate(bars, signal, 60).iloc[7]
    assert experiment.htf_direction_gate(bars, -signal, 60).iloc[7]
    # First bar of the next bucket (08:00) now sees the closed rally bucket.
    nxt = _bars([10, 9, 8, 7, 6, 20, 30, 40, 1], [9, 8, 7, 6, 20, 30, 40, 50, 0])
    assert experiment.htf_direction(nxt, 60).iloc[8] == 1


def test_240m_uses_epoch_aligned_960m_buckets():
    sixteen = pd.Timedelta(hours=16).value
    assert pd.Timestamp("2024-01-01 08:00", tz="UTC").value % sixteen == 0
    aligned = _bars([10, 11, 12, 13, 1, 1, 1, 1], [11, 12, 13, 14, 2, 2, 2, 0],
                    start="2024-01-01 08:00", freq="4h")
    assert experiment.htf_direction(aligned, 240).tolist() == [0, 0, 0, 0, 1, 1, 1, 1]


def test_htf_mask_intersects_one_shot_and_control_is_ungated():
    bars = _bars([10, 11, 12, 13, 14, 15, 16, 17], [11, 12, 13, 14, 15, 16, 17, 18])
    signal = pd.Series([0, 0, 0, 0, 1, 1, -1, -1], index=bars.index)

    gated = experiment.htf_direction_entry_mask(bars, signal, 60, gated=True)
    control = experiment.htf_direction_entry_mask(bars, signal, 60, gated=False)

    assert gated.tolist() == [False, False, False, False, True, False, False, False]
    pd.testing.assert_series_equal(control, entry_masks.one_shot_entry_mask(signal))
