"""
tests/test_multi_tf_pa.py -- regression tests for the F006 multi-TF PA family (multi_tf_pa.py).

Tests spec/research/F006-hypothesis-multi-tf-pa.md's frozen definitions. Three things are at
stake and "it runs" proves none of them:

  1. HTF bias fires on the EXACT bar the rule says: constant across every bar of a forming HTF
     block, recomputed only at block completion, from exactly the two prior completed blocks
     (never carried forward, never peeking at the still-forming block itself).
  2. No lookahead: a value at LTF bar i must not move when later bars are appended or perturbed,
     checked both generically (real fixture, large prefixes) and specifically at a HTF block
     boundary (the seam most likely to leak).
  3. Strict-cross semantics (no refire while price merely stays past a level) and the PIN name's
     "0 if HTF undefined" clause.

`multi_tf_pa.py` is not wired into strategy.py (research-only, runtime-registered by
scripts/f006_family_runner.py), so it is deliberately NOT added to
tests/test_signal_family_contract.py's FAMILIES list (that file documents the same rule for
every other unmerged sibling module). The signal-domain / no-input-mutation checks that file
provides generically are duplicated here as a fast local regression guard only.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import multi_tf_pa  # noqa: E402

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
OHLCV = os.path.join(FIXTURES, "ohlcv_sample.csv")  # 600 4h bars


def _ohlcv() -> pd.DataFrame:
    return pd.read_csv(OHLCV, index_col=0, parse_dates=True)


ALL_NAMES = list(multi_tf_pa.catalog_entries().items())


# ── HTF-block hand-derived fixture ──────────────────────────────────────────
# 20 hourly bars = 5 completed 4h blocks. (high, low, close) per bar, block boundaries at
# 4/8/12/16. Block (high, low): block0=(100,90), block1=(105,95), block2=(110,101),
# block3=(95,85), block4=(unused as a P1/P2 comparator -- it is the last block).
#
# Hand-derived bias per block, from block1 vs block0, block2 vs block1, block3 vs block2:
#   block0 bars (0-3):  bias=0   (no completed block yet)
#   block1 bars (4-7):  bias=0   (only ONE completed block behind -- P2 undefined)
#   block2 bars (8-11): bias=+1  (block1 HH+HL vs block0: 105>100 and 95>90)
#   block3 bars (12-15):bias=+1  (block2 HH+HL vs block1: 110>105 and 101>95)
#   block4 bars (16-19):bias=-1  (block3 LH+LL vs block2: 95<110 and 85<101)
_OHLC = [
    (99.5, 98.5, 99), (100, 98, 99.5), (99.5, 90, 91), (92, 91, 91.5),          # block0
    (96, 95.5, 96), (105, 95, 104), (104.5, 96, 97), (98, 95.2, 97.5),          # block1
    (103, 101.5, 102.5), (106, 102, 106), (110, 105, 108), (109, 101, 107),     # block2
    (93, 90, 91), (95, 89, 93), (94, 85, 90), (91, 86, 90.5),                   # block3
    (91, 86, 90), (90, 83, 83), (84, 80, 81), (82, 79, 80),                     # block4
]
_EXPECTED_BIAS = [0.0] * 8 + [1.0] * 8 + [-1.0] * 4
# MTFP_HTF_BLOCK: bias gates everything in blocks 0/1 to 0 regardless of any incidental cross.
# In block2 the level (block1's high/low = 105/95) is strict-crossed up at bar 9 (close 106 > 105,
# prev close 102.5 <= 105) and never refires (bar10 close 108 > 105 but prev close 106 is ALSO
# > 105, so the "prev <= level" half is false). In block3 the level (block2's 110/101) is never
# reached. In block4 the level (block3's low = 85) is strict-crossed down at bar 17 (close 83 < 85,
# prev close 90 >= 85) and never refires.
_EXPECTED_BLOCK_SIGNAL = [0.0] * 9 + [1.0] + [0.0] * 7 + [-1.0] + [0.0] * 2


def _hand_fixture() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01T00:00:00", periods=len(_OHLC), freq="1h")
    return pd.DataFrame(
        {
            "open": [c for _h, _l, c in _OHLC],
            "high": [h for h, _l, _c in _OHLC],
            "low": [l for _h, l, _c in _OHLC],
            "close": [c for _h, _l, c in _OHLC],
            "volume": [100.0] * len(_OHLC),
        },
        index=idx,
    )


def test_htf_freq_infers_4h_blocks_from_hourly_spacing_and_daily_from_4h_spacing():
    hourly_idx = pd.date_range("2024-01-01", periods=10, freq="1h")
    fourh_idx = pd.date_range("2024-01-01", periods=10, freq="4h")
    assert multi_tf_pa._htf_freq(hourly_idx) == "4h"
    assert multi_tf_pa._htf_freq(fourh_idx) == "1D"


def test_bias_is_constant_per_htf_block_and_matches_hand_derived_sequence():
    df = _hand_fixture()
    bias, _prior_high, _prior_low = multi_tf_pa._htf_bias_and_block_levels(df)
    assert bias.tolist() == _EXPECTED_BIAS


def test_htf_block_signal_matches_hand_derived_sequence():
    df = _hand_fixture()
    sig = multi_tf_pa.sig_htf_block(df)
    assert sig.tolist() == _EXPECTED_BLOCK_SIGNAL


def test_no_lookahead_into_the_still_forming_htf_block():
    """Perturbing only the LATER bars of a currently-forming HTF block must not move the
    bias/signal already assigned to EARLIER bars of that same block or any prior block --
    the seam a per-bar `transform` (rather than a shift on the block-level series) would leak
    through, since a `transform` recomputed over the whole (perturbed) block would change every
    bar of the block, including ones before the perturbation.
    """
    df = _hand_fixture()
    full_bias, _fh, _fl = multi_tf_pa._htf_bias_and_block_levels(df)
    full_sig = multi_tf_pa.sig_htf_block(df)

    # bar 9 is the second bar of block2 (bars 8-11); perturb bars 10-11 (later in the SAME
    # still-forming block) and confirm bar 9's already-decided bias/signal does not move.
    perturbed = df.copy()
    perturbed.iloc[10:12, perturbed.columns.get_indexer(["open", "high", "low", "close"])] *= 5.0
    p_bias, _ph, _pl = multi_tf_pa._htf_bias_and_block_levels(perturbed)
    p_sig = multi_tf_pa.sig_htf_block(perturbed)
    assert p_bias.iloc[:10].tolist() == full_bias.iloc[:10].tolist()
    assert p_sig.iloc[:10].tolist() == full_sig.iloc[:10].tolist()


@pytest.mark.parametrize("name,fn", ALL_NAMES, ids=[n for n, _ in ALL_NAMES])
def test_signal_domain_is_minus1_zero_plus1(name, fn):
    df = _ohlcv()
    sig = pd.Series(fn(df))
    assert len(sig) == len(df)
    assert sig.index.equals(df.index)
    non_nan = sig.dropna()
    assert non_nan.isin([-1, 0, 1]).all(), (
        f"{name} emitted a value outside {{-1, 0, 1}}: "
        f"{sorted(non_nan[~non_nan.isin([-1, 0, 1])].unique())}"
    )


@pytest.mark.parametrize("name,fn", ALL_NAMES, ids=[n for n, _ in ALL_NAMES])
def test_input_frame_is_never_mutated(name, fn):
    df = _ohlcv()
    before = df.copy(deep=True)
    fn(df)
    pd.testing.assert_frame_equal(df, before)


@pytest.mark.parametrize("name,fn", ALL_NAMES, ids=[n for n, _ in ALL_NAMES])
@pytest.mark.parametrize("prefix", [150, 300, 450])
def test_prefix_truncation_and_future_perturbation_do_not_move_the_past(name, fn, prefix):
    df = _ohlcv()
    full = pd.Series(fn(df)).fillna(0)
    assert full.ne(0).any(), f"{name}: vacuous fixture, test would pass trivially"

    truncated = pd.Series(fn(df.iloc[:prefix])).fillna(0)
    assert truncated.tolist() == full.iloc[:prefix].tolist(), (
        f"{name}: a bar before {prefix} changed when the frame was truncated"
    )

    perturbed = df.copy()
    cols = perturbed.columns.get_indexer(["open", "high", "low", "close"])
    perturbed.iloc[prefix:, cols] *= 50.0
    if "volume" in perturbed.columns:
        perturbed.iloc[prefix:, perturbed.columns.get_loc("volume")] *= 500.0
    moved = pd.Series(fn(perturbed)).fillna(0)
    assert moved.iloc[:prefix].tolist() == full.iloc[:prefix].tolist(), (
        f"{name}: a bar before {prefix} changed when future bars were perturbed"
    )


def test_strict_cross_does_not_refire_while_price_stays_past_the_level():
    df = _hand_fixture()
    sig = multi_tf_pa.sig_htf_block(df)
    # bars 10-11 stay above the (already-crossed) level 105 without ever dropping back below
    # it first -- must not refire. Same for bars 18-19 staying below the crossed level 85.
    assert sig.iloc[10] == 0.0
    assert sig.iloc[11] == 0.0
    assert sig.iloc[18] == 0.0
    assert sig.iloc[19] == 0.0


def test_htf_brk_variants_use_their_own_n_and_gate_by_bias():
    df = _hand_fixture()
    entries = multi_tf_pa.catalog_entries()
    for n, name in ((20, "MTFP_HTF_BRK20"), (10, "MTFP_HTF_BRK10"), (5, "MTFP_HTF_BRK5")):
        sig = entries[name](df)
        bias, _ph, _pl = multi_tf_pa._htf_bias_and_block_levels(df)
        high, low, close = df["high"], df["low"], df["close"]
        level_up = high.rolling(n).max().shift(1)
        level_dn = low.rolling(n).min().shift(1)
        cross_up = (close > level_up) & (close.shift(1) <= level_up.shift(1))
        cross_dn = (close < level_dn) & (close.shift(1) >= level_dn.shift(1))
        expected = pd.Series(0.0, index=df.index)
        expected = expected.mask((bias == 1.0) & cross_up, 1.0)
        expected = expected.mask((bias == -1.0) & cross_dn, -1.0)
        assert sig.tolist() == expected.tolist(), name
        # every fired bar must be bias-consistent
        fired = sig[sig != 0]
        for ts, val in fired.items():
            assert bias.loc[ts] == val, f"{name} fired {val} at {ts} against bias {bias.loc[ts]}"


def test_pin_gates_strictly_by_bias_and_emits_zero_when_undefined(monkeypatch):
    """Isolates PIN's own condition/gating from bias correctness (covered above): bias is
    stubbed to a hand-picked array, and three bars share IDENTICAL pin-candle geometry -- one
    with bias undefined (0), one with bias=+1, one (mirrored short) with bias=-1 -- so only the
    gate, not the geometry, differs between the fired and unfired bars.
    """
    n = 30
    idx = pd.date_range("2024-01-01", periods=n, freq="1h")
    # flat baseline: rolling(20) low/high settle at 48/52, never itself pin-shaped.
    open_ = [50.0] * n
    high = [52.0] * n
    low = [48.0] * n
    close = [50.0] * n

    # long-pin candle: low touches the rolling floor (48), close in the upper third of [48,54].
    for i in (20, 25):
        high[i] = 54.0
        low[i] = 48.0
        close[i] = 53.0
    # short-pin candle: high touches the rolling ceiling (54, set by bars 20/25 above), close in
    # the lower third of [46,55].
    high[27] = 55.0
    low[27] = 46.0
    close[27] = 47.0

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": [100.0] * n},
        index=idx,
    )

    fake_bias = pd.Series(0.0, index=idx)
    fake_bias.iloc[25] = 1.0
    fake_bias.iloc[27] = -1.0
    fake_extra = pd.Series(np.nan, index=idx)

    def fake_bias_and_levels(_df):
        return fake_bias, fake_extra, fake_extra

    monkeypatch.setattr(multi_tf_pa, "_htf_bias_and_block_levels", fake_bias_and_levels)
    sig = multi_tf_pa.sig_htf_pin(df)

    assert sig.iloc[20] == 0.0, "identical pin geometry with undefined bias must emit 0"
    assert sig.iloc[25] == 1.0, "long pin geometry with bias=+1 must fire +1"
    assert sig.iloc[27] == -1.0, "short pin geometry with bias=-1 must fire -1"
    # nothing else on the flat baseline should ever satisfy the pin geometry
    other = sig.drop(sig.index[[20, 25, 27]])
    assert (other == 0.0).all()
