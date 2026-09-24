"""
Regression tests for scripts/f006_entry_cross_symbol_experiment.py's new logic.

spec/research/F006-hypothesis-entry-cross-symbol-agreement.md's discriminating check 4: the
cross-symbol agreement gate must be causal (no lookahead) and must implement the >= MIN_AGREE
threshold exactly, same truncation-check pattern tests/test_entry_width_expansion.py and
tests/test_entry_trend_confirm.py already use.
"""
import importlib.util
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import entry_masks  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "f006_entry_cross_symbol_experiment",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "scripts", "f006_entry_cross_symbol_experiment.py"),
)
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)


def _panel(n=200, seed=0):
    """5 synthetic +1/-1/0 signal series sharing one index, mimicking own_signal_series output."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    return {
        s: pd.Series(rng.choice([-1, 0, 1], size=n), index=idx, dtype=int)
        for s in ["SOLUSDT", "ETHUSDT", "BTCUSDT", "XRPUSDT", "DOGEUSDT"]
    }


def test_gate_is_causal_under_truncation():
    panel = _panel()
    own = panel["BTCUSDT"]
    others = [panel[s] for s in panel if s != "BTCUSDT"]
    prefix = 150
    tail = 20

    def _gate(sig_dict, cut):
        own_c = sig_dict["BTCUSDT"].iloc[:cut]
        others_c = [sig_dict[s].iloc[:cut] for s in sig_dict if s != "BTCUSDT"]
        return exp.cross_symbol_gate(own_c, others_c, exp.MIN_AGREE)

    short_gate = _gate(panel, prefix).to_numpy()
    long_gate = _gate(panel, prefix + tail).to_numpy()[:prefix]
    changed = int((short_gate != long_gate).sum())
    assert changed == 0, f"{changed}/{prefix} gate bars moved when {tail} future bars appended"


def test_gate_never_true_when_own_signal_flat():
    idx = pd.date_range("2024-01-01", periods=10, freq="4h", tz="UTC")
    own = pd.Series(0, index=idx, dtype=int)
    others = [pd.Series(1, index=idx, dtype=int) for _ in range(4)]
    gate = exp.cross_symbol_gate(own, others, min_agree=0)
    assert not gate.any(), "gate must never open when the traded symbol's own signal is flat"


def test_gate_threshold_exact_boundary():
    idx = pd.date_range("2024-01-01", periods=1, freq="4h", tz="UTC")
    own = pd.Series([1], index=idx, dtype=int)
    # exactly 2 of 4 others agree (+1), the rest disagree
    others = [
        pd.Series([1], index=idx, dtype=int),
        pd.Series([1], index=idx, dtype=int),
        pd.Series([-1], index=idx, dtype=int),
        pd.Series([0], index=idx, dtype=int),
    ]
    assert bool(exp.cross_symbol_gate(own, others, min_agree=2).iloc[0]) is True
    assert bool(exp.cross_symbol_gate(own, others, min_agree=3).iloc[0]) is False


def test_gate_counts_only_matching_direction_not_any_nonzero():
    idx = pd.date_range("2024-01-01", periods=1, freq="4h", tz="UTC")
    own = pd.Series([1], index=idx, dtype=int)
    # 3 others are nonzero but disagree in direction (-1); agreement_count must be 0
    others = [pd.Series([-1], index=idx, dtype=int) for _ in range(3)] + [
        pd.Series([0], index=idx, dtype=int)
    ]
    assert bool(exp.cross_symbol_gate(own, others, min_agree=1).iloc[0]) is False


def test_gate_reindexes_others_defensively_when_index_differs():
    idx = pd.date_range("2024-01-01", periods=5, freq="4h", tz="UTC")
    own = pd.Series([1, 1, 1, 1, 1], index=idx, dtype=int)
    other_short_idx = idx[1:]  # missing the first bar
    others = [pd.Series([1, 1, 1, 1], index=other_short_idx, dtype=int)] + [
        pd.Series([1] * 5, index=idx, dtype=int) for _ in range(3)
    ]
    gate = exp.cross_symbol_gate(own, others, min_agree=4)
    # bar 0: the short-index other reindexes to NaN -> filled 0 -> only 3/4 agree -> False at min_agree=4
    assert bool(gate.iloc[0]) is False
    assert bool(gate.iloc[1]) is True
