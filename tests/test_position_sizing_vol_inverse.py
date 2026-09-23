"""
Regression tests for scripts/f006_position_sizing_vol_inverse_experiment.py's new logic.

spec/research/F006-hypothesis-position-sizing-vol-inverse.md's discriminating check 4: the
stake multiplier (atr_pct / atr_ref / mult) must be causal (no lookahead), same truncation-check
pattern tests/test_entry_width_expansion.py and tests/test_entry_trend_confirm.py already use.
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
    "f006_position_sizing_vol_inverse_experiment",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "scripts", "f006_position_sizing_vol_inverse_experiment.py"),
)
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)


def _ohlcv():
    df = pd.read_csv(OHLCV, index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_mult_series_is_unchanged_by_future_bars(prefix):
    df = _ohlcv()
    full_mult = exp.stake_multiplier_series(df, interval="240")
    truncated_mult = exp.stake_multiplier_series(df.iloc[:prefix], interval="240")

    common_idx = truncated_mult.index
    pd.testing.assert_series_equal(
        full_mult.loc[common_idx], truncated_mult, check_names=False,
    )


def test_mult_is_always_within_bounds():
    df = _ohlcv()
    mult = exp.stake_multiplier_series(df, interval="240")
    assert (mult >= exp.MULT_LO - 1e-9).all()
    assert (mult <= exp.MULT_HI + 1e-9).all()
    assert mult.notna().all()  # never NaN, even during warm-up (fallback = 1.0)


def test_mult_defaults_to_one_before_atr_ref_warms_up():
    df = _ohlcv()
    mult = exp.stake_multiplier_series(df, interval="240")
    # ATR_REF_MIN_PERIODS=30: before the 30th bar, atr_ref is NaN and the
    # fallback (mult=1.0, i.e. plain baseline stake) must apply.
    assert (mult.iloc[:exp.ATR_REF_MIN_PERIODS - 1] == 1.0).all()


def test_mult_is_not_trivially_constant_on_a_real_ohlcv_fixture():
    # Guards against the degenerate case the hypothesis note's stake_cv check exists to
    # catch: on this fixture (real, if short, OHLCV data) volatility must vary enough
    # across bars that the multiplier isn't just an elaborate way of writing 1.0 everywhere.
    df = _ohlcv()
    mult = exp.stake_multiplier_series(df, interval="240")
    warmed_up = mult.iloc[exp.ATR_REF_MIN_PERIODS:]
    assert warmed_up.std() > 0.01
