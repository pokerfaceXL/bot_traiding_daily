"""
Regression tests for scripts/f006_entry_trend_confirm_experiment.py's new logic.

spec/research/F006-hypothesis-entry-trend-confirm.md's discriminating check 3: the
ema50-vs-ema200 trend gate must be causal (no lookahead), same truncation-check pattern
tests/test_donchian.py and tests/test_entry_width_expansion.py already use.
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")

_spec = importlib.util.spec_from_file_location(
    "f006_entry_trend_confirm_experiment",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "scripts", "f006_entry_trend_confirm_experiment.py"),
)
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)


def _ohlcv():
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_trend_series_is_unchanged_by_future_bars(prefix):
    df = _ohlcv()
    tail = 20
    short_t = exp.trend_series(df.iloc[:prefix], "240").to_numpy()
    long_t = exp.trend_series(df.iloc[: prefix + tail], "240").to_numpy()[:prefix]
    changed = int((short_t != long_t).sum())
    assert changed == 0, f"{changed}/{prefix} trend bars moved when {tail} future bars appended"


def test_trend_gate_never_true_before_ema200_warms_up():
    df = _ohlcv()
    trend = exp.trend_series(df, "240")
    sig = pd.Series(1, index=df.index, dtype=int)  # always-long dummy signal
    gate = exp.trend_gate(sig, trend)
    first_valid = trend.replace(0, np.nan).first_valid_index()
    before = gate.loc[: df.index[df.index.get_loc(first_valid) - 1]] if first_valid is not None else gate
    assert not before.any()


def test_trend_gate_only_true_where_signal_and_trend_agree():
    df = _ohlcv()
    trend = exp.trend_series(df, "240")
    rng = np.random.default_rng(0)
    sig = pd.Series(rng.choice([-1, 0, 1], size=len(df)), index=df.index, dtype=int)
    gate = exp.trend_gate(sig, trend)
    # every True bar must have sig == trend and sig != 0
    mismatches = int(((gate) & ~((sig == trend) & (sig != 0))).sum())
    assert mismatches == 0
    # every bar where sig == trend and sig != 0 must be True (no false negatives)
    should_be_true = (sig == trend) & (sig != 0)
    missed = int((should_be_true & ~gate).sum())
    assert missed == 0


def test_trend_gate_false_when_both_signal_and_trend_are_flat():
    df = _ohlcv()
    trend = exp.trend_series(df, "240")
    flat_at = trend[trend == 0].index
    assert len(flat_at) > 0, "fixture must contain an ema200 warm-up window (trend == 0)"
    sig = pd.Series(0, index=df.index, dtype=int)
    gate = exp.trend_gate(sig, trend)
    assert not gate.loc[flat_at].any(), "gate must never open a call when both trend and signal are flat (0)"
