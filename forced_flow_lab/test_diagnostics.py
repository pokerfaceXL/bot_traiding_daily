"""F011 T4 diagnostics: causality of Test-3 / Test-2 features, forward windows, baselines, gates."""
import numpy as np
import pandas as pd
import pytest

from forced_flow_lab import diagnostics as dg

STATES = ["NORMAL", "LONG_CROWDING", "SHORT_CROWDING", "LONG_STRESS", "SHORT_STRESS",
          "LONG_LIQUIDATION_CASCADE", "SHORT_LIQUIDATION_CASCADE", "LONG_EXHAUSTION"]


def synthetic(n=600, seed=0):
    rng = np.random.default_rng(seed)
    index = pd.date_range("2024-02-02", periods=n, freq="5min", tz="UTC")
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, n)))
    frame = pd.DataFrame({
        "close": close, "high": close * 1.001, "low": close * 0.999,
        "open_interest": 1e4 + rng.normal(0, 50, n).cumsum(),
        "oi_zscore": rng.normal(size=n), "funding_zscore": rng.normal(size=n),
        "funding_rate": rng.normal(0, 1e-4, n), "delta_oi_pct": rng.normal(0, 0.1, n),
        "atr": np.abs(rng.normal(0.2, 0.05, n)), "ofi": rng.uniform(-1, 1, n),
        "delta_cvd": rng.normal(size=n), "atr_normalized_return": rng.normal(size=n),
        "realized_vol": np.abs(rng.normal(0.002, 0.0005, n)),
        "long_short_ratio": np.exp(rng.normal(0, 0.1, n)), "long_account_share": rng.uniform(0.4, 0.6, n),
    }, index=index)
    state = pd.Series(rng.choice(STATES, n), index=index)
    return frame, state


def scramble_after(frame, state, t, seed=1):
    rng = np.random.default_rng(seed)
    f2, s2 = frame.copy(), state.copy()
    tail = f2.index[t + 1:]
    for col in f2.columns:
        f2.loc[tail, col] = f2.loc[tail, col].to_numpy() * rng.uniform(0.5, 2.0, len(tail)) + rng.normal(size=len(tail))
    s2.loc[tail] = rng.choice(STATES, len(tail))
    return f2, s2


@pytest.mark.parametrize("t", [20, 150, 431])
def test_precascade_features_use_only_bars_up_to_t(t):
    frame, state = synthetic()
    full = dg.precascade_features(frame, state)
    f2, s2 = scramble_after(frame, state, t)
    changed = dg.precascade_features(f2, s2)
    truncated = dg.precascade_features(frame.iloc[: t + 1], state.iloc[: t + 1])
    pd.testing.assert_frame_equal(full.iloc[: t + 1], changed.iloc[: t + 1])
    pd.testing.assert_frame_equal(full.iloc[: t + 1], truncated)
    assert list(full.columns) == dg.PRECASCADE_FEATURES


@pytest.mark.parametrize("t", [40, 300])
def test_event_features_use_only_bars_up_to_t(t):
    frame, state = synthetic()
    full = dg.event_features(frame)
    f2, _ = scramble_after(frame, state, t)
    pd.testing.assert_frame_equal(full.iloc[: t + 1], dg.event_features(f2).iloc[: t + 1])


def test_btc_regime_uses_completed_hours_only():
    frame, state = synthetic(n=12 * 24 * 12)  # 12 days so the 1h EMA200 warms up
    full = dg.btc_regime(frame)
    for t in (12 * 24 * 9 + 5, 12 * 24 * 10 + 11):
        f2, _ = scramble_after(frame, state, t)
        pd.testing.assert_frame_equal(full.iloc[: t + 1], dg.btc_regime(f2).iloc[: t + 1])
    # The EMA value at bar t must not include the hour bar t belongs to unless t closes it.
    assert full.btc_ema200_1h.notna().any()


def test_forward_paths_window_is_t_plus_1_to_t_plus_h():
    close = np.array([100.0, 101.0, 99.0, 102.0, 100.0])
    high = close + 0.5
    low = close - 0.5
    p = dg.forward_paths(close, high, low, 2)
    assert p["ret"][0] == pytest.approx(99 / 100 - 1)
    assert p["up"][0] == pytest.approx(101.5 / 100 - 1)
    assert p["dn"][0] == pytest.approx(1 - 98.5 / 100)
    assert np.isnan(p["ret"][3]) and np.isnan(p["ret"][4])
    lr = np.diff(np.log(close))
    assert p["rv"][1] == pytest.approx(np.sqrt(np.mean(lr[1:3] ** 2)))


def test_directional_mirrors_mfe_mae():
    close = np.array([100.0, 98.0, 97.0])
    p = dg.forward_paths(close, close + 0.0, close - 0.0, 2)
    down = dg.directional(p, np.array([0]), np.array([-1.0]))
    up = dg.directional(p, np.array([0]), np.array([1.0]))
    assert down["signed_ret"][0] == pytest.approx(0.03)
    assert down["mfe"][0] == pytest.approx(0.03) and down["mae"][0] == 0
    assert up["mfe"][0] == 0 and up["mae"][0] == pytest.approx(0.03)
    assert down["excursion"][0] == up["excursion"][0]


def test_exclusion_mask_covers_plus_minus_window():
    state = pd.Series(["NORMAL"] * 200)
    state.iloc[100] = "LONG_STRESS"
    m = dg.exclusion_mask(state, n_bars=48)
    assert m[52:149].all() and not m[51] and not m[149]


def test_baselines_match_hour_and_decile_and_respect_pool():
    rng = np.random.default_rng(0)
    hour = np.tile(np.arange(24), 50)
    dec = np.repeat(np.arange(10), 120)
    pool = np.ones(len(hour), dtype=bool)
    pool[:10] = False
    picks = dg.sample_baselines(np.array([5, 700]), hour, dec, pool, rng, k=20)
    for p, b in zip([5, 700], picks):
        assert len(b) > 0 and (hour[b] == hour[p]).all() and (dec[b] == dec[p]).all() and pool[b].all()


def test_cliffs_delta_and_risk_difference():
    assert dg.cliffs_delta(np.array([3.0, 4.0]), np.array([1.0, 2.0])) == 1.0
    assert dg.cliffs_delta(np.array([1.0, 2.0]), np.array([1.0, 2.0])) == 0.0
    x = np.array([1, 1, 0, 0.0])
    y = np.array([1, 1, 0, 1.0])
    assert dg.risk_diff(x, y) == pytest.approx(0.5)
    lo, hi = dg.cliffs_boot(np.arange(10.0) + 100, np.arange(10.0), np.random.default_rng(0))
    assert lo == hi == 1.0


def test_precascade_targets_and_eligibility():
    s = pd.Series(["NORMAL", "LONG_CROWDING", "LONG_STRESS", "LONG_LIQUIDATION_CASCADE",
                   "LONG_STRESS", "NORMAL", "LONG_STRESS", "NORMAL"])
    y, eligible, entry = dg.precascade_targets(s, 2)
    assert entry.tolist() == [False, False, False, True, False, False, False, False]
    assert y[:6].tolist() == [0, 1, 1, 0, 0, 0] and np.isnan(y[6:]).all()
    # cascade bar and the STRESS bar after it in the same episode are ineligible; fresh STRESS is eligible
    assert eligible.tolist() == [True, True, True, False, False, True, True, True]


def test_verdict_gates_need_both_symbols_and_halves():
    rows = []
    for sym in dg.SYMBOLS:
        for per in ("H1", "H2"):
            rows.append({"symbol": sym, "class": "STRESS", "side": "pooled", "period": per, "horizon": "5m",
                         "abs_ret_ratio": 1.3, "abs_ret_ratio_lo": 1.05, "fwd_rv_ratio": 1.0,
                         "fwd_rv_ratio_lo": 0.9})
    t1 = pd.DataFrame(rows)
    assert dg.test1_verdict(t1)["verdict"] == "POSITIVE"
    t1.loc[3, "abs_ret_ratio_lo"] = 0.99
    assert dg.test1_verdict(t1)["verdict"] == "NEGATIVE"
    t3 = pd.DataFrame([{"symbol": s, "model": "logistic_l2_C1", "segment": "test_40", "cutoff": "top1%",
                        "horizon": "15m", "lift": 3.0, "pr_auc": 0.01, "base_rate": 0.003,
                        "n_cascade_entries": n, "n_positive_bars": 3 * n} for s, n in zip(dg.SYMBOLS, (25, 19))])
    v = dg.test3_verdict(t3)
    assert v["verdict"] == "NEGATIVE" and v["per_horizon"]["15m"]["ETHUSDT"]["few_positives_flag"]
    t3.loc[1, "n_cascade_entries"] = 20
    assert dg.test3_verdict(t3)["verdict"] == "POSITIVE"
