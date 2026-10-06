"""F011 T2 state labels: causal prefix invariance and exactly-one-state per bar.

The synthetic grid is 3,744 bars (13 days) so that prefixes k > 2,016 reach
non-null oi_zscore/funding_zscore/fuel_pct past warm-up.
"""
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from forced_flow_lab import build_frame_5m as bf
from forced_flow_lab import label_states as ls
from forced_flow_lab.test_frame_5m import synthetic_inputs

MANIFEST = ls.load_manifest()
# Loosened thresholds only so that synthetic noise visits non-NORMAL branches;
# causality is a property of the code path, not of the threshold values.
LOOSE = {"fps_threshold": 0.5, "stress_return_atr": 0.3, "ofi_threshold": 0.02,
         "fuel_percentile": 0.7, "exhaustion_impact_ratio": 0.9}


@pytest.fixture(scope="module")
def synthetic():
    index = bf.grid("2024-01-26", "2024-02-08")
    inputs = synthetic_inputs(index)
    return index, inputs, bf.compute_frame(inputs, index)


def test_manifest_frozen_grid_at_most_two_values():
    grid = {k: v for k, v in MANIFEST["robustness_grid"].items() if k != "design"}
    assert set(grid) == set(MANIFEST["thresholds"])
    for key, values in grid.items():
        assert 1 <= len(values) <= 2 and MANIFEST["thresholds"][key] in values


@pytest.mark.parametrize("thresholds", [MANIFEST["thresholds"], LOOSE], ids=["frozen", "loose"])
def test_states_prefix_causal(synthetic, thresholds):
    index, inputs, frame = synthetic
    lookbacks = MANIFEST["lookbacks_bars"]
    full = ls.compute_states(frame, thresholds, lookbacks)
    # A look-ahead can only show at a prefix's last row, so also cut right after
    # bars whose full-sample state is a stress-family or exhaustion state.
    eventful = np.flatnonzero(~full.state.isin(["NORMAL", "LONG_CROWDING", "SHORT_CROWDING"]))
    for k in sorted({2100, 2600, 3200, *(eventful[eventful >= bf.WARMUP] + 1).tolist()}):
        assert frame.oi_zscore.iloc[bf.WARMUP:k].notna().all()
        assert frame.funding_zscore.iloc[bf.WARMUP:k].notna().all()
        prefix_inputs = {key: value.loc[value.index <= index[k - 1]] for key, value in inputs.items()}
        prefix = ls.compute_states(bf.compute_frame(prefix_inputs, index[:k]), thresholds, lookbacks)
        overlap = full.iloc[:k]
        assert prefix.state.equals(overlap.state), f"state changed when truncated after bar {k}"
        for column in prefix.columns.drop("state"):
            a, b = prefix[column].astype(float), overlap[column].astype(float)
            assert (a.isna() == b.isna()).all(), f"{column} NaN pattern diverged at k={k}"
            np.testing.assert_allclose(a[a.notna()], b[b.notna()], rtol=1e-12, err_msg=f"{column} k={k}")


def test_loose_thresholds_visit_every_stage(synthetic):
    """Guards the causality test against vacuously comparing all-NORMAL output."""
    _, _, frame = synthetic
    states = ls.compute_states(frame, LOOSE, MANIFEST["lookbacks_bars"]).state.iloc[bf.WARMUP:]
    assert {"SHORT_CROWDING", "SHORT_STRESS", "SHORT_LIQUIDATION_CASCADE", "SHORT_EXHAUSTION"} <= set(states)


def mirrored(frame):
    """Same market seen from the other side: funding, price moves and flow flip sign."""
    m = frame.copy()
    m["funding_zscore"] = -m.funding_zscore
    m["atr_normalized_return"] = -m.atr_normalized_return
    m["ofi"] = -m.ofi
    m["buy_impact"], m["sell_impact"] = frame.sell_impact, frame.buy_impact
    return m


def test_long_side_mirrors_short_side(synthetic):
    _, _, frame = synthetic
    lookbacks = MANIFEST["lookbacks_bars"]
    a = ls.compute_states(frame, LOOSE, lookbacks).state
    b = ls.compute_states(mirrored(frame), LOOSE, lookbacks).state
    swap = {s: s.replace("LONG", "~").replace("SHORT", "LONG").replace("~", "SHORT") for s in ls.STATES}
    assert b.equals(a.map(swap))
    assert "LONG_EXHAUSTION" in set(b) and "LONG_LIQUIDATION_CASCADE" in set(b)


def test_every_non_warmup_bar_has_exactly_one_known_state(synthetic):
    _, _, frame = synthetic
    for override in ({}, LOOSE):
        states = ls.label(frame, MANIFEST, **override)
        assert len(states) == int((~frame.is_warmup).sum())
        assert states.index.equals(frame.index[~frame.is_warmup])
        assert states.state.notna().all() and states.state.isin(ls.STATES).all()


def test_bn_layer_never_changes_labels(synthetic):
    _, _, frame = synthetic
    scrambled = frame.copy()
    for column in [c for c in frame.columns if c.startswith("bn_")]:
        scrambled[column] = scrambled[column].to_numpy()[::-1]
    a = ls.compute_states(frame, LOOSE, MANIFEST["lookbacks_bars"]).state
    b = ls.compute_states(scrambled, LOOSE, MANIFEST["lookbacks_bars"]).state
    assert a.equals(b)


def test_durations_median_run_length():
    s = pd.Series(["NORMAL", "NORMAL", "LONG_STRESS", "NORMAL", "NORMAL", "NORMAL", "NORMAL"])
    d = ls.durations(s)
    assert d["NORMAL"] == {"runs": 2, "median_bars": 3.0, "median_minutes": 15.0, "max_bars": 4}
    assert d["LONG_STRESS"]["median_bars"] == 1.0


# ----------------------------------------------------------------- integration
@pytest.mark.parametrize("symbol", list(ls.SYMBOLS))
def test_built_states_cover_every_non_warmup_bar(symbol):
    path = ls.OUTPUT / f"{symbol}.csv.gz"
    if not path.exists():
        pytest.skip(f"labelled states absent: {path}")
    with gzip.open(path, "rt") as fh:
        states = pd.read_csv(fh, index_col=0, parse_dates=True)
    assert len(states) == 115200 - bf.WARMUP
    assert states.state.isin(ls.STATES).all()
    assert len(states.columns) < 20 and "close" not in states.columns
