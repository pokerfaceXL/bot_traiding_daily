"""F011 T3 event study: state-entry extraction, overlap policy, look-ahead-free returns."""
import numpy as np
import pandas as pd
import pytest

from forced_flow_lab import event_study as es

CONT = es.HYPOTHESES["H-FORCEDFLOW-CONTINUATION-01"]["sides"]
EXH = es.HYPOTHESES["H-FORCEDFLOW-EXHAUSTION-01"]["sides"]


def series(states, closes=None):
    index = pd.date_range("2024-02-02", periods=len(states), freq="5min", tz="UTC")
    closes = closes if closes is not None else 100.0 + np.arange(len(states))
    return pd.Series(states, index=index), pd.Series(closes, index=index, dtype=float)


def test_entry_is_first_bar_and_stress_to_cascade_is_one_episode():
    state, _ = series(["NORMAL", "LONG_STRESS", "LONG_LIQUIDATION_CASCADE", "LONG_STRESS", "NORMAL",
                       "SHORT_STRESS", "SHORT_STRESS", "LONG_CROWDING", "LONG_STRESS"])
    ev = es.entries(state, CONT)
    assert ev.pos.tolist() == [1, 5, 8]
    assert ev.direction.tolist() == [-1, +1, -1]


def test_long_to_short_switch_is_a_new_entry():
    state, _ = series(["LONG_EXHAUSTION", "SHORT_EXHAUSTION", "SHORT_EXHAUSTION"])
    ev = es.entries(state, EXH)
    assert ev.pos.tolist() == [0, 1] and ev.direction.tolist() == [+1, -1]


def test_forward_return_uses_close_t_to_close_t_plus_h_and_drops_tail():
    _, close = series(["NORMAL"] * 5, [100.0, 110.0, 99.0, 120.0, 90.0])
    fwd = es.forward_returns(close, 2)
    assert fwd[:3] == pytest.approx([-0.01, 120 / 110 - 1, 90 / 99 - 1])
    assert np.isnan(fwd[3:]).all()
    assert np.isnan(es.forward_returns(close, 5)).all()


def test_no_look_ahead_past_window_and_no_event_past_data_end():
    states = ["NORMAL"] * 20
    for p in (2, 15, 18):
        states[p] = "LONG_STRESS"
    state, close = series(states)
    h = 3
    ev = es.events(state, close, CONT, h)
    # entry at 18 needs close[21] which does not exist: dropped, never truncated.
    assert ev.pos.tolist() == [2, 15]
    assert (ev.pos + h <= len(state) - 1).all()
    # Perturbing any close outside [t, t+h] of every kept event leaves its return unchanged.
    used = set()
    for p in ev.pos:
        used |= set(range(p, p + h + 1))
    shocked = close.copy()
    for i in set(range(len(close))) - used:
        shocked.iloc[i] *= 7.0
    again = es.events(state, shocked, CONT, h)
    assert again.fwd.tolist() == pytest.approx(ev.fwd.tolist())


def test_non_overlapping_greedy_per_horizon():
    pos = np.array([0, 2, 3, 6, 7, 20])
    assert pos[es.non_overlapping(pos, 3)].tolist() == [0, 3, 6, 20]
    assert pos[es.non_overlapping(pos, 1)].tolist() == pos.tolist()


def test_signing_continuation_long_side_down_is_positive():
    states = ["NORMAL", "LONG_STRESS", "NORMAL", "NORMAL", "SHORT_STRESS", "NORMAL", "NORMAL"]
    closes = [100, 100, 90, 90, 90, 99, 99]
    state, close = series(states, closes)
    ev = es.events(state, close, CONT, 1)
    assert ev.signed.tolist() == pytest.approx([0.10, 0.10])


def test_cell_beats_band_only_by_more_than_cost_and_in_predicted_direction():
    fwd_all = np.zeros(100)
    ev = pd.DataFrame({"direction": [-1, -1], "fwd": [-0.004, -0.004]})
    ev["signed"] = ev.direction * ev.fwd
    assert es.cell(ev, fwd_all)["beats_cost_band"]
    ev["fwd"] = [-0.0034, -0.0034]
    ev["signed"] = ev.direction * ev.fwd
    assert not es.cell(ev, fwd_all)["beats_cost_band"]  # equal to band is not "more than"


def test_verdict_requires_same_horizon_on_both_symbols():
    rows = [
        {"variant": "primary", "hypothesis": "H", "symbol": "BTCUSDT", "horizon": "5m", "beats_cost_band": True},
        {"variant": "primary", "hypothesis": "H", "symbol": "ETHUSDT", "horizon": "5m", "beats_cost_band": False},
        {"variant": "primary", "hypothesis": "H", "symbol": "BTCUSDT", "horizon": "4h", "beats_cost_band": False},
        {"variant": "primary", "hypothesis": "H", "symbol": "ETHUSDT", "horizon": "4h", "beats_cost_band": True},
        {"variant": "fps_threshold=3.0", "hypothesis": "H", "symbol": "ETHUSDT", "horizon": "5m", "beats_cost_band": True},
    ]
    v = es.verdict(pd.DataFrame(rows))
    assert v["H"]["edge"] is False
    rows[1]["beats_cost_band"] = True
    assert es.verdict(pd.DataFrame(rows))["H"]["edge"] is True
