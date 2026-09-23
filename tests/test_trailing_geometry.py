"""
The trailing-stop geometry spec/research/F006-hypothesis-trailing-sweep.md's explanation
rests on, pinned against backtest_engine rather than asserted in prose.

The note's finding is that pooled `avg_winner` is essentially a function of
`max(activate_pct, trail_pct)` alone, because a position cannot be closed by the trail
until it has moved `activate_pct` in its favour, and the trail then sits at
`best_price * (1 - trail_pct)`. That implies a floor on the trailing stop LEVEL:

    level / entry >= (1 + activate_pct) * (1 - trail_pct)      (long; mirrored for short)

These tests check that floor holds for four (activate, trail) pairs spanning the note's
grid -- and, just as importantly, that the floor is a statement about the stop LEVEL and
not about the realised exit price. The first version of the claim in the note said the
latter and it was wrong: `execution.resolve_stop_take_within_bar` fills at the bar's open
when the bar gaps through the stop, so a gap fill can realise materially less than the
level (on Train-1 BTCUSDT 1h at 0.06/0.01, 34 of 43 trailing exits were gap fills and 24
of those realised below the floor, while 0 of 43 stop LEVELS did). The test pins both
halves, so the distinction cannot quietly rot back into the wrong claim.

TWO FRAMES, both deterministic, no RNG: the committed 600-bar `ohlcv_sample.csv`, and the
same bars with their log-returns multiplied by 3 (`_amplified`). The fixture's realised
moves are too small to arm a 6% activation threshold, so without the amplified frame the
two cells the note calls best would be untested-by-skip rather than checked.

No engine behaviour is changed or expected to change here; this is a characterisation
test of the mechanics the note reasons about.
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be

OHLCV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ohlcv_sample.csv")

# (activate_pct, trail_pct): the baseline, the tightest cell, and the two the note's
# result section calls best -- spanning both the "trail binds on arming" and the
# "trail wider than the initial stop" regimes.
CELLS = [(0.01, 0.01), (0.03, 0.02), (0.06, 0.01), (0.06, 0.04)]
FRAMES = ["fixture", "amplified"]


def _fixture_frame():
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


def _amplified(df, scale=3.0):
    """The same bars with every log-return scaled by `scale`; wicks scale with them.

    Deterministic and gap-free by construction (each bar opens at the previous close),
    which is what makes the non-gap half of the floor check testable at all.
    """
    close = df["close"].to_numpy(dtype=float)
    log_returns = np.diff(np.log(close), prepend=np.log(close[0]))
    new_close = close[0] * np.exp(np.cumsum(scale * log_returns))
    new_open = np.concatenate([[close[0]], new_close[:-1]])
    body_high = np.maximum(df["open"], df["close"]).to_numpy(dtype=float)
    body_low = np.minimum(df["open"], df["close"]).to_numpy(dtype=float)
    upper_wick = (df["high"].to_numpy(dtype=float) / body_high - 1) * scale
    lower_wick = (1 - df["low"].to_numpy(dtype=float) / body_low) * scale
    return pd.DataFrame({
        "open": new_open,
        "high": np.maximum(new_open, new_close) * (1 + upper_wick),
        "low": np.minimum(new_open, new_close) * (1 - lower_wick),
        "close": new_close,
        "volume": df["volume"].to_numpy(dtype=float),
    }, index=df.index)


def _run(frame, activate_pct, trail_pct, max_sl_pct=0.03):
    df = _fixture_frame()
    if frame == "amplified":
        df = _amplified(df)
    return be.run_backtest(
        df, "EMA_8_21", interval="240", now=df.index[-1] + pd.Timedelta(hours=4),
        initial_equity=500.0, stake=100.0, leverage=1.0, max_sl_pct=max_sl_pct,
        activate_pct=activate_pct, trail_pct=trail_pct,
        commission_rate_bps=10.0, half_spread_bps=5.0, slippage_bps=2.0,
    )


def _signed_return(trades, price_column):
    return (trades[price_column] / trades["entry_price"] - 1) * trades["direction"]


def _lock_in_floor(activate_pct, trail_pct):
    return (1 + activate_pct) * (1 - trail_pct) - 1


def test_amplified_frame_is_a_valid_ohlc_series():
    """Guard on the test's own scaffolding: bars must still bracket their bodies."""
    df = _amplified(_fixture_frame())
    assert (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-9).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1) + 1e-9).all()
    assert (df["low"] > 0).all()
    assert len(df) == len(_fixture_frame())
    # it is meaningfully wider than the source, which is the whole point
    assert df["close"].max() / df["close"].min() > _fixture_frame()["close"].max() / _fixture_frame()["close"].min()


@pytest.mark.parametrize("frame", FRAMES)
@pytest.mark.parametrize("activate_pct,trail_pct", CELLS)
def test_trailing_stop_level_never_sits_below_the_lock_in_floor(frame, activate_pct, trail_pct):
    result = _run(frame, activate_pct, trail_pct)
    trailing = result.trades[result.trades["exit_reason"] == "trailing_sl"]
    if trailing.empty:
        pytest.skip(f"{frame} produces no trailing_sl exit at {activate_pct}/{trail_pct}")

    floor = _lock_in_floor(activate_pct, trail_pct)
    levels = _signed_return(trailing, "trailing_sl")
    assert (levels >= floor - 1e-9).all(), (
        f"{int((levels < floor - 1e-9).sum())} of {len(trailing)} trailing stops sit below "
        f"the (1+a)(1-t) floor of {floor:.4%}; min was {levels.min():.4%}"
    )


@pytest.mark.parametrize("frame", FRAMES)
@pytest.mark.parametrize("activate_pct,trail_pct", CELLS)
def test_a_non_gap_trailing_exit_realises_at_least_the_floor(frame, activate_pct, trail_pct):
    """The exit price only meets the floor when the bar did not gap through the stop."""
    result = _run(frame, activate_pct, trail_pct)
    trailing = result.trades[result.trades["exit_reason"] == "trailing_sl"]
    clean = trailing[~trailing["is_gap_fill"].astype(bool)]
    if clean.empty:
        pytest.skip(f"{frame} produces no non-gap trailing_sl exit at {activate_pct}/{trail_pct}")

    floor = _lock_in_floor(activate_pct, trail_pct)
    realised = _signed_return(clean, "exit_price")
    assert (realised >= floor - 1e-9).all(), (
        f"{int((realised < floor - 1e-9).sum())} of {len(clean)} non-gap trailing exits "
        f"realised less than {floor:.4%}; min was {realised.min():.4%}"
    )


def test_raising_activate_pct_raises_the_smallest_trailing_winner():
    """The mechanism the note's max(a, t) reading depends on, stated as a comparison.

    At a = 0.06 the trail cannot arm until the position is 6% up, so the worst trailing
    exit it can produce is far better than at a = 0.01 -- which is why avg_winner tracks
    max(activate_pct, trail_pct) rather than either parameter on its own.
    """
    tight = _run("amplified", 0.01, 0.01).trades
    late = _run("amplified", 0.06, 0.01).trades
    tight_levels = _signed_return(tight[tight["exit_reason"] == "trailing_sl"], "trailing_sl")
    late_levels = _signed_return(late[late["exit_reason"] == "trailing_sl"], "trailing_sl")
    assert not tight_levels.empty and not late_levels.empty

    assert late_levels.min() > tight_levels.min()
    assert late_levels.min() >= _lock_in_floor(0.06, 0.01) - 1e-9
    assert tight_levels.min() >= _lock_in_floor(0.01, 0.01) - 1e-9


def test_a_trail_wider_than_the_initial_stop_leaves_the_initial_stop_binding_below_1pct():
    """trail_pct = 0.04 against max_sl_pct = 0.03: the trail only binds above +1.04%.

    _active_sl takes max(initial_sl, trailing_sl) for a long, so until
    best_price * 0.96 exceeds entry * 0.97 the initial stop is still the live one and any
    stop-out is labelled "initial_sl". This is the one column of the note's grid where
    arming and binding are different events, so it is pinned rather than reasoned about.
    """
    trades = _run("amplified", 0.01, 0.04, max_sl_pct=0.03).trades
    assert len(trades) > 0

    stopped = trades[trades["exit_reason"] == "initial_sl"]
    assert not stopped.empty
    # every initial_sl exit's live level is the -3% initial stop, not a trail in disguise
    assert (_signed_return(stopped, "initial_sl") + 0.03).abs().max() < 1e-9

    trailing = trades[trades["exit_reason"] == "trailing_sl"]
    assert not trailing.empty
    # a labelled trailing exit must have a trailing level strictly better than the
    # initial stop -- that is exactly the engine's labelling rule -- and therefore, in
    # this column, better than +1.04% is impossible to claim for anything below it
    assert (_signed_return(trailing, "trailing_sl") > _signed_return(trailing, "initial_sl")).all()
    assert (_signed_return(trailing, "trailing_sl") > -0.03).all()
