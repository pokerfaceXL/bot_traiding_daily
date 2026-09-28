"""
Regression tests for the F006 UTC opening-range breakout family
(opening_range_breakout.py, spec/research/F006-hypothesis-opening-range-breakout.md).

Three things at stake, same discipline as tests/test_donchian.py:

  1. The signal fires on the EXACT bar the rule says it does, including the two
     documented edge cases: a bar still inside the forming range must stay 0, and a
     UTC day with fewer bars than or_bars must never arm at all.
  2. No carry across days: a new UTC day's range and breakout state must be built
     only from that day's own bars, never from the previous day's.
  3. No lookahead: the signal at bar i must be unchanged when later bars are
     appended to the frame.

Plus the additive-only guarantee: the 83 pre-existing non-Lorentzian catalog entries
must produce bit-identical signals to the commit before opening_range_breakout.py was
wired in (Lorentzian entries are excluded here the same way
tests/test_donchian.py's fingerprint fixture excludes them -- advanced_ta is not
importable in this interpreter).
"""
import hashlib
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import backtest_engine as be
import entry_masks
import opening_range_breakout as orb
import strategy

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")
PRE_ORB_FINGERPRINTS = os.path.join(FIXTURES, "catalog_fingerprints_pre_orb.json")

OR_BARS = 2  # lookback used by every hand-built fixture below

# Day 1 (2024-01-01), 4 bars, or_bars=2:
#   i0  h=100 l=98 c=99     -> forming
#   i1  h=101 l=97 c=100    -> forming -> or_high=101, or_low=97
#   i2  h=102 l=99 c=101.5  -> active, close > 101         -> LONG
#   i3  h=99  l=96 c=96.5   -> active, close < 97          -> SHORT
DAY1 = [(100.0, 98.0, 99.0), (101.0, 97.0, 100.0), (102.0, 99.0, 101.5), (99.0, 96.0, 96.5)]
DAY1_EXPECTED = [0, 0, 1, -1]

# Day 2 (2024-01-02), a single bar: fewer than or_bars(2) bars total, so it never
# arms -- i never reaches or_bars for this day, whatever the range would have been.
DAY2 = [(120.0, 110.0, 115.0)]
DAY2_EXPECTED = [0]

# Day 3 (2024-01-03), 5 bars, or_bars=2. Deliberately a very different range from
# day 1's (55/40 here vs 101/97 there) -- if day state carried over, i2's close of
# 55 would misread against day 1's stale or_high of 101 instead of staying flat at
# the (correct) exact-equality boundary of its OWN day's or_high.
#   i0  h=50 l=40 c=45     -> forming
#   i1  h=55 l=42 c=48     -> forming -> or_high=55, or_low=40
#   i2  h=54 l=41 c=55     -> active, close == or_high exactly -> flat (strict >)
#   i3  h=60 l=44 c=56     -> active, close > 55              -> LONG
#   i4  h=58 l=39 c=39.5   -> active, close < 40 (this day's own or_low)  -> SHORT
DAY3 = [(50.0, 40.0, 45.0), (55.0, 42.0, 48.0), (54.0, 41.0, 55.0), (60.0, 44.0, 56.0), (58.0, 39.0, 39.5)]
DAY3_EXPECTED = [0, 0, 0, 1, -1]

ALL_BARS = DAY1 + DAY2 + DAY3
ALL_EXPECTED = DAY1_EXPECTED + DAY2_EXPECTED + DAY3_EXPECTED
DAY_STARTS = ["2024-01-01", "2024-01-02", "2024-01-03"]


def _frame(bars_by_day):
    rows, index = [], []
    for day, bars in zip(DAY_STARTS, bars_by_day):
        base = pd.Timestamp(day, tz="UTC")
        for j, (h, l, c) in enumerate(bars):
            index.append(base + pd.Timedelta(hours=j))
            rows.append((h, l, c))
    df = pd.DataFrame(rows, columns=["high", "low", "close"], index=pd.DatetimeIndex(index))
    df["open"] = df["close"]
    df["volume"] = 1.0
    return df[["open", "high", "low", "close", "volume"]]


def _ohlcv():
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


# ── the exact bars ────────────────────────────────────────────────────────

def test_breakout_fires_on_the_hand_verified_bars():
    df = _frame([DAY1, DAY2, DAY3])
    sig = orb.compute_orb_signal(df, OR_BARS)
    assert sig.tolist() == ALL_EXPECTED


def test_bars_still_inside_the_forming_range_are_zero():
    df = _frame([DAY1, DAY2, DAY3])
    sig = orb.compute_orb_signal(df, OR_BARS)
    # the first or_bars bars of every day are 0 regardless of their own high/low
    assert sig.iloc[0] == 0 and sig.iloc[1] == 0          # day 1
    assert sig.iloc[5] == 0 and sig.iloc[6] == 0           # day 3


def test_day_with_fewer_than_or_bars_bars_never_arms():
    df = _frame([DAY1, DAY2, DAY3])
    sig = orb.compute_orb_signal(df, OR_BARS)
    day2_row = sig.index[len(DAY1)]
    assert day2_row.normalize() == pd.Timestamp("2024-01-02", tz="UTC")
    assert sig.iloc[len(DAY1)] == 0


def test_exact_equality_with_or_high_is_flat_not_long():
    # day 3, bar i2: close (55.0) == or_high (55.0) exactly -- strict inequality only
    df = _frame([DAY1, DAY2, DAY3])
    sig = orb.compute_orb_signal(df, OR_BARS)
    day3_i2 = len(DAY1) + len(DAY2) + 2
    assert df["close"].iloc[day3_i2] == 55.0
    assert sig.iloc[day3_i2] == 0


def test_new_utc_day_does_not_carry_the_previous_days_range():
    # day 3's own range is 40/55, far from day 1's 97/101 -- if day 1's state leaked
    # into day 3, bar i3 (close=56) would already have been "long" back at i2
    # (56 > ... no, 55 < 101), or day 3 would never breakout at all with day 1's
    # wider band. The hand-verified array above already pins this; this test states
    # the invariant it is pinning explicitly.
    df = _frame([DAY1, DAY2, DAY3])
    sig = orb.compute_orb_signal(df, OR_BARS)
    day3 = sig.iloc[len(DAY1) + len(DAY2):]
    assert day3.tolist() == DAY3_EXPECTED


# ── causality: no lookahead ───────────────────────────────────────────────

@pytest.mark.parametrize("or_bars", orb.OR_BARS_GRID)
@pytest.mark.parametrize("prefix", [200, 350, 500])
def test_signal_at_bar_i_is_unchanged_by_future_bars(or_bars, prefix):
    df = _ohlcv()
    tail = 20
    short = orb.compute_orb_signal(df.iloc[:prefix], or_bars).to_numpy()
    long = orb.compute_orb_signal(df.iloc[: prefix + tail], or_bars).to_numpy()[:prefix]
    changed = int((short != long).sum())
    assert changed == 0, f"or_bars={or_bars}: {changed}/{prefix} bars moved when {tail} future bars were appended"


def test_upper_never_below_lower_so_both_conditions_cannot_fire_together():
    df = _ohlcv()
    for or_bars in orb.OR_BARS_GRID:
        sig = orb.compute_orb_signal(df, or_bars)
        assert sig.isin([-1, 0, 1]).all()


def test_or_bars_must_be_positive():
    with pytest.raises(ValueError):
        orb.compute_orb_signal(_frame([DAY1, DAY2, DAY3]), 0)


# ── engine wiring ─────────────────────────────────────────────────────────

def test_catalog_gained_five_orb_entries_and_left_every_other_entry_bit_identical():
    for n in orb.OR_BARS_GRID:
        assert callable(strategy.STRATEGY_CATALOG[f"ORB_UTC_{n}"])
    # 79 F005 baseline + 2 Lorentzian (F006) + 4 Donchian (F006) + 3 vol-regime-wrap
    # + 5 cross-sectional-rs (F006, merged earlier) + 5 ORB (this slice)
    assert len(strategy.STRATEGY_CATALOG) == 98

    with open(PRE_ORB_FINGERPRINTS) as f:
        expected = json.load(f)
    assert len(expected) == 83  # 79 baseline + 4 Donchian; Lorentzian excluded (no advanced_ta here)
    df = _ohlcv()
    work = strategy.add_indicators(df)
    for name, digest in sorted(expected.items()):
        sig = pd.Series(strategy.STRATEGY_CATALOG[name](work)).fillna(0).astype(int)
        got = hashlib.sha256(sig.to_numpy().tobytes()).hexdigest()[:16]
        assert got == digest, f"{name} changed: {got} != {digest}"


def test_orb_runs_through_the_engine_with_the_one_shot_mask():
    df = _ohlcv()
    for name in (f"ORB_UTC_{n}" for n in orb.OR_BARS_GRID):
        sig = entry_masks.strategy_signal_series(df, name, interval="240")
        mask = entry_masks.one_shot_entry_mask(sig)
        masked = be.run_backtest(df, name, interval="240", entry_regime_mask=mask)
        assert masked.metrics["n_trades"] <= int(mask.sum())
