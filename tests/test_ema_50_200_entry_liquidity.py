import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import entry_masks
import f006_ema_50_200_entry_liquidity as experiment


def _bars(volumes, start="2024-01-01", freq="h"):
    idx = pd.date_range(start, periods=len(volumes), freq=freq, tz="UTC")
    close = np.arange(len(volumes), dtype=float) + 10
    return pd.DataFrame({"open": close, "high": close + 1, "low": close - 1, "close": close,
                         "volume": np.asarray(volumes, dtype=float)}, index=idx)


def test_card_targets_ema_50_200_baseline_not_bb_names():
    assert experiment.CONTROL_NAME == "EMA_50_200"
    assert experiment.EXPECTED_MEAN == 72.6693115
    assert experiment.EXPECTED_MEAN not in (95.3217987, 82.900262, 97.2455987)
    assert experiment.EXPECTED_COHORT_N == 330
    assert experiment.EXPECTED_SL_SHARE == 213 / 330
    assert experiment.EXPECTED_LOSING_MONTHS == 7
    assert experiment.EXPECTED_BIG_WINNER_N == 5
    assert experiment.BIG_WINNER_THRESHOLD == 29.9
    assert experiment.WINDOW == 20
    assert experiment.OUT.name == "f006_ema_50_200_entry_liquidity"
    assert experiment.CONTROL_REFERENCE.parent.name == "f006_ema_50_200_entry_htf_direction"
    assert experiment.CHECKSUM_REFERENCE.parent.name == "f006_ema_50_200_abs_atr_gate"


def test_gate_ignores_ema_atr_vol_ratio_candle_strength_depth_and_htf():
    bars = _bars([10] * 20 + [9, 10, 11, 50])
    signal = pd.Series(1, index=bars.index)
    decorated = bars.assign(**{
        # Decoys that would change the result if the gate read them.
        "open": 1e9, "high": 1e9, "low": -1e9,
        "ema50": 1e9, "ema200": -1e9, "ema_50": 1e9, "ema_200": -1e9,
        "atr_14": 0.0, "atr_pct": 0.0,
        "vol_ratio": 0.0, "vol_ma20": 1e12, "quote_volume": 0.0,
    })

    gate = experiment.liquidity_gate(decorated, signal)

    pd.testing.assert_series_equal(gate, experiment.liquidity_gate(bars, signal))
    assert gate.tolist() == [False] * 20 + [False, True, True, True]


def test_below_median_rejects_and_equal_keeps():
    prior = list(range(1, 21))  # median of 1..20 = 10.5
    kept = []
    for volume, direction in ((10.49, 1), (10.5, -1), (10.51, 1)):
        bars = _bars(prior + [volume])
        signal = pd.Series([0] * 20 + [direction], index=bars.index)
        assert experiment.prior_volume_median(bars).iloc[20] == 10.5
        kept.append(bool(experiment.liquidity_gate(bars, signal).iloc[20]))
    assert kept == [False, True, True]


def test_short_window_rejects():
    bars = _bars([1] * 19 + [100])
    signal = pd.Series(1, index=bars.index)

    assert not experiment.liquidity_gate(bars, signal).any()
    assert experiment.liquidity_gate(_bars([1] * 20 + [100]), pd.Series(1, index=_bars([0] * 21).index)).iloc[20]


def test_zero_median_and_missing_volume_reject():
    zero = _bars([0] * 20 + [5])
    assert not experiment.liquidity_gate(zero, pd.Series(1, index=zero.index)).iloc[20]
    missing = _bars([1] * 20 + [np.nan])
    assert not experiment.liquidity_gate(missing, pd.Series(1, index=missing.index)).iloc[20]


def test_signal_bar_is_not_inside_its_window():
    # A huge signal-bar volume would drag a self-inclusive median up only if
    # included; with 20 prior bars of [1]*10 + [3]*10 the prior median is 2.
    bars = _bars([1] * 10 + [3] * 10 + [2])
    assert experiment.prior_volume_median(bars).iloc[20] == 2.0
    assert experiment.liquidity_gate(bars, pd.Series(1, index=bars.index)).iloc[20]
    # Window for bar 21 starts at bar 1: bar 0 dropped, signal bar 20 included.
    nxt = _bars([100] + [1] * 19 + [5, 1])
    assert experiment.prior_volume_median(nxt).iloc[20] == 1.0
    assert experiment.prior_volume_median(nxt).iloc[21] == 1.0
    lone = _bars([1] * 20 + [1000])
    assert experiment.prior_volume_median(lone).iloc[20] == 1.0


def test_liquidity_mask_intersects_one_shot_and_control_is_ungated():
    bars = _bars([1] * 20 + [2, 2, 0.5, 2])
    signal = pd.Series([0] * 20 + [1, 1, -1, -1], index=bars.index)

    gated = experiment.liquidity_entry_mask(bars, signal, gated=True)
    control = experiment.liquidity_entry_mask(bars, signal, gated=False)

    assert gated.iloc[20:].tolist() == [True, False, False, False]
    assert not gated.iloc[:20].any()
    pd.testing.assert_series_equal(control, entry_masks.one_shot_entry_mask(signal))
