import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_bb_20_25_entry_htf_direction as experiment


def _bars(opens, closes, start="2024-01-01", freq="h"):
    idx = pd.date_range(start, periods=len(opens), freq=freq, tz="UTC")
    return pd.DataFrame({"open": opens, "close": closes}, index=idx)


def test_htf_direction_uses_prior_closed_bucket_and_never_signal_bucket():
    # 60m bars -> 240m buckets at 00:00, 04:00, 08:00 (epoch-aligned).
    # Bucket 00:00 up (10 -> 14), bucket 04:00 down (14 -> 9), bucket 08:00 flat.
    opens = [10, 11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2]
    closes = [11, 12, 13, 14, 13, 12, 11, 9, 50, 1, 2, 9]
    bars = _bars(opens, closes)

    direction = experiment.htf_direction(bars, 60)

    # Bucket 00:00 has no complete prior bucket in the data.
    assert direction.iloc[:4].tolist() == [0, 0, 0, 0]
    # All of bucket 04:00 (including its last bar 07:00) sees bucket 00:00 only.
    assert direction.iloc[4:8].tolist() == [1, 1, 1, 1]
    # Bucket 08:00 sees bucket 04:00 (down), not its own strongly-moving bars.
    assert direction.iloc[8:12].tolist() == [-1, -1, -1, -1]


def test_signal_bar_last_in_its_bucket_ignores_own_bucket():
    # Bucket 00:00 down overall; bucket 04:00 rallies hard and its last bar
    # (07:00) is the signal bar. The gate must use bucket 00:00 only.
    opens = [10, 9, 8, 7, 6, 20, 30, 40]
    closes = [9, 8, 7, 6, 20, 30, 40, 50]
    bars = _bars(opens, closes)
    signal = pd.Series([0, 0, 0, 0, 0, 0, 0, 1], index=bars.index)

    gate = experiment.htf_direction_gate(bars, signal, 60)

    assert not gate.iloc[7]
    short = experiment.htf_direction_gate(bars, -signal, 60)
    assert short.iloc[7]


def test_flat_prior_bucket_rejects_both_directions():
    opens = [10, 11, 12, 13, 5, 5, 5, 5]
    closes = [11, 12, 13, 10, 5, 5, 5, 5]
    bars = _bars(opens, closes)
    long = pd.Series([0, 0, 0, 0, 1, 0, 0, 0], index=bars.index)

    assert experiment.htf_direction(bars, 60).iloc[4] == 0
    assert not experiment.htf_direction_gate(bars, long, 60).iloc[4]
    assert not experiment.htf_direction_gate(bars, -long, 60).iloc[4]


def test_incomplete_prior_bucket_rejects():
    bars = _bars([10, 11, 12, 13, 14, 15, 16, 17], [11, 12, 13, 14, 15, 16, 17, 18])
    gapped = bars.drop(bars.index[2])  # bucket 00:00 has only 3 bars
    signal = pd.Series(1, index=gapped.index)

    assert experiment.htf_direction(gapped, 60).iloc[3:].tolist() == [0, 0, 0, 0]
    assert not experiment.htf_direction_gate(gapped, signal, 60).iloc[3:].any()
    # Same data without the gap agrees for longs.
    assert experiment.htf_direction(bars, 60).iloc[4:].tolist() == [1, 1, 1, 1]


def test_240m_uses_epoch_aligned_960m_buckets():
    # 960m = 16h buckets floored from the Unix epoch: 2024-01-01 08:00 UTC is a
    # bucket open (00:00 is not), so buckets open at 08:00 and 2024-01-02 00:00.
    sixteen = pd.Timedelta(hours=16).value
    assert pd.Timestamp("2024-01-01 08:00", tz="UTC").value % sixteen == 0
    assert pd.Timestamp("2024-01-01 00:00", tz="UTC").value % sixteen != 0
    aligned = _bars([10, 11, 12, 13, 1, 1, 1, 1], [11, 12, 13, 14, 2, 2, 2, 0],
                    start="2024-01-01 08:00", freq="4h")
    assert experiment.htf_direction(aligned, 240).tolist() == [0, 0, 0, 0, 1, 1, 1, 1]

    # Starting at 00:00 the first two bars belong to the incomplete 16:00-prior
    # bucket; the 08:00 bucket (bars 2..5) is the first complete one.
    shifted = _bars([10, 11, 12, 13, 1, 1, 1, 1], [11, 12, 13, 14, 2, 2, 2, 0],
                    start="2024-01-01 00:00", freq="4h")
    assert experiment.htf_direction(shifted, 240).tolist() == [0, 0, 0, 0, 0, 0, -1, -1]


def test_htf_mask_intersects_one_shot_and_control_is_ungated():
    opens = [10, 11, 12, 13, 14, 15, 16, 17]
    closes = [11, 12, 13, 14, 15, 16, 17, 18]
    bars = _bars(opens, closes)
    signal = pd.Series([0, 0, 0, 0, 1, 1, -1, -1], index=bars.index)

    gated = experiment.htf_direction_entry_mask(bars, signal, 60, gated=True)
    control = experiment.htf_direction_entry_mask(bars, signal, 60, gated=False)

    assert gated.tolist() == [False, False, False, False, True, False, False, False]
    pd.testing.assert_series_equal(control, entry_masks.one_shot_entry_mask(signal))
