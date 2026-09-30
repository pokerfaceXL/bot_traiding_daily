"""Entry-only ATR gate: causality, inclusive threshold, replay, and scoring guards."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import backtest_engine
import donchian
import entry_masks
import f006_donchian_abs_atr_gate as experiment
import f006_family_runner as harness
import f006_signal_autopsy as autopsy


def bars():
    df = pd.read_csv(ROOT / "tests/fixtures/ohlcv_sample.csv", index_col=0, parse_dates=True)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df


@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_gate_prefix_and_future_mutation(prefix):
    df = bars()
    expected = donchian.atr_pct_entry_gate(df.iloc[:prefix], 1.25)
    pd.testing.assert_series_equal(expected, donchian.atr_pct_entry_gate(df, 1.25).iloc[:prefix])
    df.iloc[prefix:, df.columns.get_indexer(["high", "low", "close"])] *= 10
    pd.testing.assert_series_equal(expected, donchian.atr_pct_entry_gate(df, 1.25).iloc[:prefix])


def test_signal_bar_atr_matches_next_fill_autopsy_and_is_inclusive():
    df = pd.DataFrame({"high": [100.5] * 30, "low": [99.5] * 30, "close": [100.] * 30})
    gate = donchian.atr_pct_entry_gate(df, 1.0)
    assert not gate.iloc[:13].any()
    assert gate.iloc[13:].all()  # exactly 1.0%, inclusive
    assert not donchian.atr_pct_entry_gate(df, 0.999).any()
    df.loc[20, "high"] = 120  # current signal bar, not prior bar
    assert not donchian.atr_pct_entry_gate(df, 1.0).iloc[20]
    gate = donchian.atr_pct_entry_gate(df, 1.5)
    expected_at_fill = autopsy.entry_calmness(df).atr_pct.le(1.5)
    pd.testing.assert_series_equal(gate.shift(1, fill_value=False), expected_at_fill, check_names=False)


@pytest.mark.parametrize("threshold", [0, -1, np.nan, np.inf])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        donchian.atr_pct_entry_gate(bars(), threshold)


def test_mask_no_delayed_entry_and_unclosed_bar_excluded():
    df = bars()
    signal = entry_masks.strategy_signal_series(df, "DONCHIAN_55", "240", now=harness.NOW)
    one_shot = entry_masks.one_shot_entry_mask(signal)
    pd.testing.assert_series_equal(experiment.entry_mask(df, "240", None), one_shot)
    gated = experiment.entry_mask(df, "240", 1.0)
    assert not (gated & ~one_shot).any()
    # A bar opening at the evaluation instant cannot be used, even if it breaks out.
    extra = df.iloc[-1:].copy()
    extra.index = pd.DatetimeIndex([harness.NOW], name=df.index.name)
    extra[["high", "low", "close"]] *= 100
    pd.testing.assert_series_equal(gated, experiment.entry_mask(pd.concat([df, extra]), "240", 1.0))


def replay(df, mask):
    return backtest_engine.run_backtest(
        df, "DONCHIAN_55", interval="240", now=harness.NOW,
        initial_equity=harness.INITIAL_EQUITY, stake=harness.STAKE,
        max_sl_pct=harness.MAX_SL_PCT, activate_pct=harness.ACTIVATE_PCT,
        trail_pct=harness.TRAIL_PCT, cooldown_candles=harness.COOLDOWN,
        entry_regime_mask=mask, **harness.FIXED_PARAMS,
    )


def test_forced_off_control_replay_and_retained_exit_economics():
    df = bars()
    sig = entry_masks.strategy_signal_series(df, "DONCHIAN_55", "240", now=harness.NOW)
    control = replay(df, entry_masks.one_shot_entry_mask(sig))
    forced_off = replay(df, experiment.entry_mask(df, "240", None))
    pd.testing.assert_frame_equal(control.trades, forced_off.trades)
    pd.testing.assert_frame_equal(control.equity_curve, forced_off.equity_curve)
    assert control.metrics == forced_off.metrics
    assert len(control.trades) > 0
    threshold = float(autopsy.entry_calmness(df).atr_pct.median())
    gated = replay(df, experiment.entry_mask(df, "240", threshold))
    assert 0 < len(gated.trades) < len(control.trades)
    before = control.trades.set_index(["entry_time", "direction"])
    after = gated.trades.set_index(["entry_time", "direction"])
    pd.testing.assert_frame_equal(before.loc[after.index, ["exit_time", "exit_reason", "net_pnl"]],
                                  after[["exit_time", "exit_reason", "net_pnl"]])
    assert not gated.trades.exit_reason.isin(["trailing_sl", "take_profit"]).any()
