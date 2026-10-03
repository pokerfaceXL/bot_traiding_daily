import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import f006_bb_20_2_xsym_agree_sizing as sizing  # noqa: E402


def test_multiplier_is_frozen_formula_shifted_one_closed_bar():
    idx = pd.date_range("2024-03-01", periods=5, freq="4h", tz="UTC")
    own = pd.Series([1, 1, -1, 0, 1], index=idx)
    others = [
        pd.Series([1, 1, -1, -1, 1], index=idx),
        pd.Series([1, -1, -1, 0, 1], index=idx),
        pd.Series([0, 1, -1, 0, 1], index=idx),
        pd.Series([1, 1, 1, 0, 1], index=idx),
    ]
    mult = sizing.agreement_multiplier_series(own, others)
    # closed-bar n_agree = [3, 3, 3, 0, 4] -> [1.625, 1.625, 1.625, 0.5, 2.0], then shifted
    assert pd.isna(mult.iloc[0])
    assert mult.iloc[1:].tolist() == pytest.approx([1.625, 1.625, 1.625, 0.5])
