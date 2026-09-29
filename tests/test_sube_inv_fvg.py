"""Causality and block-boundary checks for H-SUBE-INV-FVG-01."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sube_inv_fvg as sinv


def _bars(n=360, freq="4h"):
    idx = pd.date_range("2024-01-01", periods=n, freq=freq, tz="UTC")
    x = np.arange(n, dtype=float)
    close = 100 + np.sin(x / 7) * 8 + x * .03
    return pd.DataFrame({"open": close - .2, "high": close + 1,
                         "low": close - 1, "close": close, "volume": 1}, index=idx)


def test_completed_five_day_block_requires_every_constituent_bar():
    df = _bars(120)
    assert len(sinv.completed_blocks(df, 240, sinv.HTF_MIN)) == 3
    # A hole invalidates the whole five-day block rather than silently spanning it.
    assert len(sinv.completed_blocks(df.drop(df.index[50]), 240, sinv.HTF_MIN)) == 2


def test_signals_are_unchanged_when_future_bars_are_appended():
    df = _bars(480)
    short = sinv.compute_signals(df.iloc[:390], 240)
    long = sinv.compute_signals(df, 240)
    for name in sinv.NAMES:
        assert short[name].equals(long[name].iloc[:390])


def test_frozen_names_and_no_midfill_geometry():
    assert sinv.NAMES == ("SINV_FIRST_FVG", "SINV_MSS_CLOSE", "SINV_MSS_IN_FVG",
                          "SINV_FIRST_H4", "SINV_FIRST_SMT")
    source = open(sinv.__file__, encoding="utf-8").read().lower()
    assert "midpoint" not in source
    assert "0.5 *" not in source


def test_h4_blocks_are_epoch_aligned_and_complete():
    df = _bars(12, "1h")
    blocks = sinv.completed_blocks(df, 60, sinv.H4_MIN)
    assert list(blocks["id"]) == [int(df.index[0].timestamp() // 60 // 240) + n for n in range(3)]
    assert list(blocks["complete_at"]) == [df.index[3], df.index[7], df.index[11]]
