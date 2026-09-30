"""Hand-derived discriminators for the frozen permission × trauma composition."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import btc_perm_cascade as bpc
from scripts import f006_btc_perm_cascade_experiment as grid

QUIET = (101., 99., 100., 100.)
LONG = (110., 100., 109., 300.)
SHORT = (100., 90., 91., 300.)
# Raises compression above its threshold but is not an expansion event.
WAIT = (101.5, 98.5, 100., 100.)


def frame(bars):
    df = pd.DataFrame(bars, columns=["high", "low", "close", "volume"],
                      index=pd.date_range("2024-01-01", periods=len(bars), freq="h", tz="UTC"))
    df["open"] = df.close
    return df


def context(df, direction=1):
    return pd.DataFrame({"close": 1000 + direction * np.arange(len(df))}, index=df.index)


def cascade(bars):
    return bpc.cascade_direction(frame(bars), 1.5, 2.5, .75)


def test_exact_frozen_names_and_runtime_only_catalog():
    df = frame([QUIET] * 160)
    before = set(grid.runner.strategy.STRATEGY_CATALOG)
    entries = bpc.catalog_entries({"60": context(df), "240": context(df)})
    assert set(entries) == {"BPC_R15_V25_C75", "BPC_R18_V20_C75", "BPC_R18_V30_C75",
                            "BPC_R15_V25_NOGATE", "BPC_R15_V25_ER40"}
    assert len(entries) == 5
    assert set(grid.runner.strategy.STRATEGY_CATALOG) == before


@pytest.mark.parametrize("direction", [1, -1])
def test_er20_warmup_sign_zero_path_missing_and_prefix_causality(direction):
    df = context(frame([QUIET] * 180), direction)
    full = bpc.btc_er_permission(df)
    assert full.iloc[:20].eq(0).all()
    assert full.iloc[20:].eq(direction).all()
    pd.testing.assert_series_equal(bpc.btc_er_permission(df.iloc[:101]), full.iloc[:101])
    df.iloc[101:, 0] = 10**8
    pd.testing.assert_series_equal(bpc.btc_er_permission(df).iloc[:101], full.iloc[:101])
    df.close = 10
    assert bpc.btc_er_permission(df).eq(0).all()
    df.iloc[30, 0] = np.nan
    assert bpc.btc_er_permission(df).eq(0).all()


def test_er40_is_stricter_than_er30():
    # 13 upward, 7 downward unit steps -> ER=.30, with nonzero path.
    prices = np.r_[100, 100 + np.cumsum([1] * 13 + [-1] * 7)]
    df = pd.DataFrame({"close": prices})
    assert bpc.btc_er_permission(df, .30).iloc[-1] == 1
    assert bpc.btc_er_permission(df, .40).iloc[-1] == 0
    df.close = -df.close
    assert bpc.btc_er_permission(df, .30).iloc[-1] == -1


@pytest.mark.parametrize("trauma,direction", [(LONG, 1), (SHORT, -1)])
def test_arm_and_consume_with_matching_opposing_neutral_gate(trauma, direction):
    df = frame([QUIET] * 140 + [trauma, trauma])
    assert bpc.cascade_direction(df, 1.5, 2.5, .75).iloc[-2:].tolist() == [direction, 0]
    for permission in (direction, -direction, 0):
        out = bpc.signal(df, context(df, permission), "BPC_R15_V25_C75")
        assert out.iloc[-2:].tolist() == ([direction, 0] if permission == direction else [0, 0])
    # The ungated ablation ignores opposing BTC but still consumes its arm.
    assert bpc.signal(df, context(df, -direction), "BPC_R15_V25_NOGATE").iloc[-2:].tolist() == [direction, 0]


def test_rejected_event_consumes_arm_even_if_permission_later_agrees(monkeypatch):
    df = frame([QUIET] * 140 + [LONG, LONG])
    permission = pd.Series(0, index=df.index)
    permission.iloc[-1] = 1
    monkeypatch.setattr(bpc, "btc_er_permission", lambda *args: permission)
    assert bpc.signal(df, context(df), "BPC_R15_V25_C75").eq(0).all()


@pytest.mark.parametrize("waits,expected", [(5, 1), (6, 0)])
def test_arm_lasts_exactly_next_six_bars(waits, expected):
    assert cascade([QUIET] * 140 + [WAIT] * waits + [LONG]).iloc[-1] == expected


def test_new_compression_refreshes_arm_and_requires_full_prior_120_values():
    assert cascade([QUIET] * 139 + [LONG]).eq(0).all()
    assert cascade([QUIET] * 145 + [WAIT] * 5 + [LONG]).iloc[-1] == 1


def test_strict_expansion_baselines_and_close_boundaries():
    df = frame([QUIET] * 140 + [LONG])
    f = bpc.cascade_features(df).iloc[-1]
    assert f.prior_range_mean == 2
    assert f.prior_volume_mean == 100
    assert f.compression_threshold == 40
    # Equality is insufficient for either expansion multiple; pressure uses >=/<=.
    assert cascade([QUIET] * 140 + [(103., 100., 103., 300.)]).iloc[-1] == 0
    assert cascade([QUIET] * 140 + [(110., 100., 109., 250.)]).iloc[-1] == 0
    assert cascade([QUIET] * 140 + [(110., 100., 107.5, 300.)]).iloc[-1] == 1
    assert cascade([QUIET] * 140 + [(110., 100., 102.5, 300.)]).iloc[-1] == -1
    assert cascade([QUIET] * 140 + [(110., 100., 105., 300.)]).iloc[-1] == 0


def test_missing_btc_timestamp_is_neutral_not_forward_filled():
    df = frame([QUIET] * 140 + [LONG])
    btc = context(df)
    assert bpc.signal(df, btc, bpc.NAMES[0]).iloc[-1] == 1
    assert bpc.signal(df, btc.iloc[:-1], bpc.NAMES[0]).iloc[-1] == 0


@pytest.mark.parametrize("name", bpc.NAMES)
def test_btc_is_flat_even_ablation_and_composition_is_prefix_causal(name):
    df = frame([QUIET] * 140 + [(110., 100., 109., 400.)] + [QUIET] * 40 + [SHORT])
    btc = context(df)
    before = df.copy(deep=True)
    assert bpc.signal(df, df.copy(), name).eq(0).all()
    full = bpc.signal(df, btc, name)
    assert full.iloc[140] != 0  # non-vacuous prefix test
    pd.testing.assert_series_equal(bpc.signal(df.iloc[:141], btc.iloc[:141], name), full.iloc[:141])
    btc.iloc[141:, 0] = -100000
    pd.testing.assert_series_equal(bpc.signal(df, btc, name).iloc[:141], full.iloc[:141])
    pd.testing.assert_frame_equal(df, before)


def test_trauma_can_emit_inside_prior_channel_not_donchian():
    bars = [QUIET] * 140
    bars[125] = (200., 198., 199., 100.)  # identical range; prior channel ceiling far above event
    df = frame(bars + [LONG])
    assert df.close.iloc[-1] < df.high.iloc[-21:-1].max()
    assert bpc.signal(df, context(df), bpc.NAMES[0]).iloc[-1] == 1
    # Conversely a price breakout without volume trauma emits nothing.
    assert cascade([QUIET] * 140 + [(110., 100., 109., 100.)]).iloc[-1] == 0


def test_rank_uses_weighted_wr_and_train1_not_warmup_pnl():
    name = bpc.NAMES[0]
    common = dict(strategy=name, max_drawdown_pct=1, legacy_h2=False,
                  h2_sparse_absent_zero_trade=True, net_pnl=999)
    results = pd.DataFrame([
        {**common, "exit_cell": "NO_TRAIL", "n_trades": 1, "n_wins": 1, "train1_net_pnl": 1},
        {**common, "exit_cell": "NO_TRAIL", "n_trades": 9, "n_wins": 0, "train1_net_pnl": 1},
        {**common, "exit_cell": "TP_x2", "n_trades": 10, "n_wins": 4, "train1_net_pnl": -1},
    ])
    rank = grid.rank_table(results, {name: 8.01}, {name: True})
    assert rank.exit_cell.tolist() == ["TP_x2", "NO_TRAIL"]
    assert rank.win_rate.tolist() == [40, 10]
    assert not rank.iloc[0].h1_pass
    assert rank.iloc[0].sparse_h2_after_h1 == 0
    assert rank.spam_rejected.all()
