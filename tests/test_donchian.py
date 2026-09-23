"""
Regression tests for the F006 Donchian family (donchian.py).

Three things are actually at stake here, and "it runs" proves none of them:

  1. The signal fires on the EXACT bar the rule says it does. The fixtures below are
     hand-built at n=3 and each expected array was derived by hand from the printed
     channel table before it was written down (spec/research/F006-hypothesis-donchian.md,
     "Signal definitions"), so an off-by-one in the pullback state machine fails here
     rather than quietly changing the experiment's numbers.
  2. No lookahead. The channel at bar i must come from bars [i-n, i-1] only, so the
     value at bar i cannot move when later bars are appended -- the same truncation
     check tests/test_lorentzian.py applies to the Lorentzian adapter, which the
     library's own documented usage fails.
  3. The two failure modes the research note commits to in advance: a pullback that
     never completes must produce NO entry at all, and an overshoot through the far
     channel edge must CANCEL the call rather than fill it.

Plus the additive-only guarantee: the 79 pre-existing catalog entries must produce
bit-identical signals to the commit before donchian.py was wired in.
"""
import hashlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import donchian
import entry_masks
import strategy

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")
PRE_DONCHIAN_FINGERPRINTS = os.path.join(FIXTURES, "catalog_fingerprints_pre_donchian.json")

N = 3  # lookback used by every hand-built fixture: small enough to verify by hand

# Four flat bars: high 10 / low 9 / close 9.5. The channel is NaN until bar 3 and
# then sits at upper=10, lower=9, mid=9.5.
FLAT = [(10.0, 9.0, 9.5)] * 4

# The main fixture, (high, low, close) per bar. Hand-derived channel and expectations:
#   bar 4  close 11.0 > upper 10.0          -> BREAKOUT long, pullback ARMS (emits 0)
#   bar 5  close 10.8 > mid 10.00           -> no touch yet
#   bar 6  close  9.9 <= mid 10.10          -> TOUCH
#   bar 7  close 10.5 > mid 10.35           -> TRIGGER, pullback enters long here
#   bar 8  close 10.6, mid 10.45            -> HOLD
#   bar 9  close  9.6 < lower 9.70          -> BREAKOUT short: long call ends, short ARMS
#   bar 10 close  9.1 < mid 10.15           -> no touch yet (short needs close >= mid)
#   bar 11 close 10.5 >= mid 9.90           -> TOUCH
#   bar 12 close  9.5 < mid 9.90            -> TRIGGER, pullback enters short here
#   bar 13 close  9.8                       -> HOLD
MAIN = FLAT + [
    (11.0, 9.5, 11.0), (11.2, 10.5, 10.8), (10.9, 9.8, 9.9), (10.6, 9.7, 10.5),
    (10.7, 10.0, 10.6), (10.8, 9.5, 9.6), (9.8, 9.0, 9.1), (10.6, 9.0, 10.5),
    (10.6, 9.4, 9.5), (10.0, 9.3, 9.8),
]
MAIN_BREAKOUT = [0, 0, 0, 0, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1]
MAIN_PULLBACK = [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, -1, -1]

# Failure mode A: the breakout runs away and price never returns to the midline.
# The call stays armed for the rest of the series and is never entered.
RUNAWAY = FLAT + [
    (11.0, 9.5, 11.0), (12.0, 10.8, 11.9), (13.0, 11.8, 12.9),
    (14.0, 12.8, 13.9), (15.0, 13.8, 14.9), (16.0, 14.8, 15.9),
]

# Failure mode B1: the pullback touches the midline (bar 6) and then overshoots
# straight through the lower band (bar 7, close 8.0 < lower 9.5) -- which IS the
# opposite breakout, so the long is cancelled unentered instead of being filled.
# Bars 10-11 then make the cancellation observable rather than merely absent: bar 10
# bounces back above the NEW (short) midline of 8.5 without exceeding the upper band,
# which a still-armed long would read as its trigger and fill at +1; the correct
# machine reads it as the short call's TOUCH and enters -1 on bar 11.
OVERSHOOT_AFTER_TOUCH = FLAT + [
    (11.0, 9.5, 11.0), (11.2, 10.5, 10.8), (10.9, 9.8, 9.9),
    (10.0, 7.9, 8.0), (8.5, 7.5, 7.6), (8.0, 7.0, 7.1),
    (10.0, 9.5, 9.5), (9.0, 7.8, 8.0),
]

# Failure mode B2: the overshoot happens on the very first bar after the breakout,
# before any touch (bar 5, close 8.5 < lower 9.0). Same outcome: cancel, not fill.
OVERSHOOT_WITHOUT_TOUCH = FLAT + [
    (11.0, 9.5, 11.0), (10.0, 8.4, 8.5), (9.0, 8.0, 8.2), (8.8, 7.9, 8.0),
]


def _frame(bars):
    idx = pd.date_range("2024-01-01", periods=len(bars), freq="4h", tz="UTC")
    df = pd.DataFrame(bars, columns=["high", "low", "close"], index=idx)
    df["open"] = df["close"]
    df["volume"] = 1.0
    return df[["open", "high", "low", "close", "volume"]]


def _ohlcv():
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


# ── the channel itself ────────────────────────────────────────────────────

def test_channel_excludes_the_current_bar():
    df = _frame(MAIN)
    ch = donchian.donchian_channel(df, N)
    # bar 4 makes a new high of 11.0; its own upper band must still be 10.0, the
    # max high of bars 1-3. If .shift(1) were dropped this reads 11.0 and the
    # breakout at bar 4 could never fire at all.
    assert ch["upper"].iloc[4] == 10.0
    assert ch["lower"].iloc[4] == 9.0
    assert ch["mid"].iloc[4] == 9.5
    # warm-up: the first n bars have no channel
    assert ch.iloc[:N].isna().all().all()
    assert not ch.iloc[N:].isna().any().any()


def test_upper_is_never_below_lower_so_the_two_breakout_conditions_cannot_both_fire():
    # max(high) >= min(low) by construction, and the signal compares a single scalar
    # close against both, so "close > upper AND close < lower" is unreachable. This
    # is what makes the breakout rule unambiguous; it is asserted, not assumed (the
    # note's pre-registered text wrongly described this as an arbitrary tie-break).
    df = _ohlcv()
    for n in donchian.TURTLE_LOOKBACKS:
        ch = donchian.donchian_channel(df, n)
        valid = ch.dropna()
        assert (valid["upper"] >= valid["lower"]).all()
        both = (df["close"] > ch["upper"]) & (df["close"] < ch["lower"])
        assert not both.any()


# ── the exact bars ────────────────────────────────────────────────────────

def test_breakout_fires_on_the_hand_verified_bars():
    sig = donchian.sig_donchian_breakout(_frame(MAIN), N)
    assert sig.tolist() == MAIN_BREAKOUT
    # stated again as the bars where the state CHANGES, so a series that happened to
    # hold the right values for the wrong reason cannot pass on the array alone
    changes = [i for i in range(1, len(sig)) if sig.iloc[i] != sig.iloc[i - 1]]
    assert changes == [4, 9]


def test_pullback_fires_on_the_hand_verified_bars_not_on_the_breakout_bar():
    sig = donchian.sig_donchian_pullback(_frame(MAIN), N)
    assert sig.tolist() == MAIN_PULLBACK
    # the load-bearing difference from the raw breakout: bar 4 breaks out and bar 9
    # breaks down, and the pullback variant is FLAT on both of them
    assert sig.iloc[4] == 0 and sig.iloc[9] == 0
    # it enters three bars later, on the midline re-cross, in the breakout's direction
    assert sig.iloc[7] == 1 and sig.iloc[6] == 0
    assert sig.iloc[12] == -1 and sig.iloc[11] == 0


def test_pullback_holds_through_a_midline_cross_back():
    # bar 13 closes at 9.8, exactly at mid (9.8), i.e. no longer below it -- the short
    # entered at bar 12 must still be held. Only the opposite breakout ends a call.
    df = _frame(MAIN)
    ch = donchian.donchian_channel(df, N)
    assert ch["mid"].iloc[13] == pytest.approx(9.8) and df["close"].iloc[13] == 9.8
    assert donchian.sig_donchian_pullback(df, N).iloc[13] == -1


# ── the two pre-registered failure modes ──────────────────────────────────

def test_a_pullback_that_never_completes_is_never_entered():
    df = _frame(RUNAWAY)
    breakout = donchian.sig_donchian_breakout(df, N)
    pullback = donchian.sig_donchian_pullback(df, N)
    # the raw breakout is long from bar 4 to the end of the series ...
    assert breakout.tolist() == [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
    # ... and the pullback variant never trades it at all: no bar limit, no late fill
    assert pullback.tolist() == [0] * len(df)


def test_an_overshoot_after_the_touch_cancels_the_call_instead_of_filling_it():
    df = _frame(OVERSHOOT_AFTER_TOUCH)
    pullback = donchian.sig_donchian_pullback(df, N)
    breakout = donchian.sig_donchian_breakout(df, N)
    # bar 6 touched the midline, so the trigger was armed; bar 7 blew through the
    # lower band instead of re-crossing upward
    assert breakout.tolist() == [0, 0, 0, 0, 1, 1, 1, -1, -1, -1, -1, -1]
    # never long anywhere: the failed breakout is not bought, not on the overshoot
    # bar and not on the bar-10 bounce back through the midline either
    assert (pullback != 1).all()
    # the short call that replaced it runs its own touch (bar 10) / trigger (bar 11)
    assert pullback.tolist() == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1]


def test_an_overshoot_before_any_touch_cancels_the_call_too():
    df = _frame(OVERSHOOT_WITHOUT_TOUCH)
    assert donchian.sig_donchian_breakout(df, N).tolist() == [0, 0, 0, 0, 1, -1, -1, -1]
    assert donchian.sig_donchian_pullback(df, N).tolist() == [0] * len(df)


# ── causality: no lookahead ───────────────────────────────────────────────

@pytest.mark.parametrize("n", donchian.TURTLE_LOOKBACKS)
@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_signal_at_bar_i_is_unchanged_by_future_bars(n, prefix):
    """The ticket's explicit check: truncating the series at bar i+20 must not move
    the value at bar i. Both variants, both Turtle lookbacks, three cut points."""
    df = _ohlcv()
    tail = 20
    for fn in (donchian.sig_donchian_breakout, donchian.sig_donchian_pullback):
        short = fn(df.iloc[:prefix], n).to_numpy()
        long = fn(df.iloc[: prefix + tail], n).to_numpy()[:prefix]
        changed = int((short != long).sum())
        assert changed == 0, (
            f"{fn.__name__}(n={n}): {changed}/{prefix} bars moved when {tail} future bars were appended"
        )


def test_pullback_state_always_agrees_with_the_breakout_direction_on_real_data():
    """Invariant the state machine must never break: a held pullback position is in
    the direction of the breakout call that armed it, on every bar of the call."""
    df = _ohlcv()
    for n in donchian.TURTLE_LOOKBACKS:
        breakout = donchian.sig_donchian_breakout(df, n)
        pullback = donchian.sig_donchian_pullback(df, n)
        live = pullback != 0
        assert live.any(), f"n={n}: the pullback variant never entered on the fixture"
        assert (pullback[live] == breakout[live]).all()
        # and it is the strictly more selective variant: fewer bars in the market
        assert int(live.sum()) < int((breakout != 0).sum())


# ── engine wiring ─────────────────────────────────────────────────────────

def test_catalog_gained_four_donchian_entries_and_left_the_other_79_bit_identical():
    for name in ("DONCHIAN_20", "DONCHIAN_55", "DONCHIAN_PULLBACK_20", "DONCHIAN_PULLBACK_55"):
        assert callable(strategy.STRATEGY_CATALOG[name])
    # 79 F005 baseline entries + 2 Lorentzian (F006) + 4 Donchian (this slice)
    assert "LORENTZIAN_default" in strategy.STRATEGY_CATALOG
    assert "LORENTZIAN_raw" in strategy.STRATEGY_CATALOG
    assert len(strategy.STRATEGY_CATALOG) == 85

    # Value-level, not name-level: every pre-existing entry's signal on the shared
    # fixture must hash to what it hashed to at the commit before donchian.py was
    # wired in (fixtures/catalog_fingerprints_pre_donchian.json, 79 names).
    with open(PRE_DONCHIAN_FINGERPRINTS) as f:
        expected = json.load(f)
    assert len(expected) == 79
    work = strategy.add_indicators(_ohlcv())
    for name, digest in sorted(expected.items()):
        sig = pd.Series(strategy.STRATEGY_CATALOG[name](work)).fillna(0).astype(int)
        got = hashlib.sha256(sig.to_numpy().tobytes()).hexdigest()[:16]
        assert got == digest, f"{name} changed: {got} != {digest}"


def test_donchian_runs_through_the_engine_with_the_one_shot_mask():
    """End-to-end on the path the experiment uses: signal -> entry_masks -> engine."""
    df = _ohlcv()
    for name in ("DONCHIAN_20", "DONCHIAN_PULLBACK_20"):
        sig = entry_masks.strategy_signal_series(df, name, interval="240")
        mask = entry_masks.one_shot_entry_mask(sig)
        masked = be.run_backtest(df, name, interval="240", entry_regime_mask=mask)
        assert masked.metrics["n_trades"] <= int(mask.sum())
        # the mask index must line up with the engine's own frame, or it would
        # silently block every entry instead of gating them
        assert sig.index.equals(masked.equity_curve.index)
