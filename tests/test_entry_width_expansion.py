"""
Regression tests for scripts/f006_entry_width_expansion_experiment.py's new logic.

spec/research/F006-hypothesis-entry-width-expansion.md's discriminating check 3: the
width-expansion gate must be causal (no lookahead), same truncation-check pattern
tests/test_donchian.py and tests/test_lorentzian.py already use.
"""
import importlib.util
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_contract  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")

_spec = importlib.util.spec_from_file_location(
    "f006_entry_width_expansion_experiment",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "scripts", "f006_entry_width_expansion_experiment.py"),
)
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)


def _ohlcv():
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


@pytest.mark.parametrize("name", ["DONCHIAN_55", "BB_20_25_breakout"])
@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_width_gate_is_unchanged_by_future_bars(name, prefix):
    df = _ohlcv()
    tail = 20
    now = df.index[min(prefix + tail, len(df) - 1)] + pd.Timedelta(hours=4)
    short_w = exp.width_series(df.iloc[:prefix], "240", name)
    long_w = exp.width_series(df.iloc[: prefix + tail], "240", name)
    short_gate = exp.width_gate(short_w).to_numpy()
    long_gate = exp.width_gate(long_w).to_numpy()[:prefix]
    changed = int((short_gate != long_gate).sum())
    assert changed == 0, f"{name}: {changed}/{prefix} gate bars moved when {tail} future bars appended"


def test_width_gate_never_true_before_its_own_lookback_warms_up():
    df = _ohlcv()
    for name in ("DONCHIAN_55", "BB_20_25_breakout"):
        w = exp.width_series(df, "240", name)
        gate = exp.width_gate(w)
        # rolling(30) on top of a rolling(55) channel (for Donchian) -- nothing can
        # be True before at least 30 non-NaN width values exist.
        first_valid = w.first_valid_index()
        before = gate.loc[: df.index[df.index.get_loc(first_valid) + 28]]
        assert not before.any()
