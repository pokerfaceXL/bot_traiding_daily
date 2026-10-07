"""F014 alpha discovery lab — no network, synthetic frames only."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alpha_discovery_lab import data as D
from alpha_discovery_lab import run as R
from alpha_discovery_lab import states as S
from alpha_discovery_lab import stats as St
from alpha_discovery_lab.registry import HYPOTHESES, PROTOCOL, registry_sha256

IDX = pd.date_range("2024-01-26", "2025-03-01", freq="1h", inclusive="left", tz="UTC")


def frame(seed: int, rets: np.ndarray | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.006, len(IDX)) if rets is None else rets
    close = 100 * np.exp(np.cumsum(r))
    op = np.r_[100.0, close[:-1]]
    wig = np.abs(rng.normal(0, 0.002, len(IDX)))
    df = pd.DataFrame({"open": op, "close": close, "high": np.maximum(op, close) * (1 + wig),
                       "low": np.minimum(op, close) * (1 - wig), "volume": 1.0}, index=IDX)
    df["funding"] = np.repeat(rng.normal(1e-4, 5e-5, len(IDX) // 8 + 1), 8)[: len(IDX)]
    df["oi"] = 1e4 * np.exp(np.cumsum(rng.normal(0, 0.003, len(IDX))))
    df["buyratio"] = 0.6 + 0.05 * np.sin(np.arange(len(IDX)) / 50) + rng.normal(0, 0.01, len(IDX))
    return df


def frames(seed=0):
    return {s: frame(seed + i) for i, s in enumerate(D.SYMBOLS)}


# ---------------------------------------------------------------- stats
def test_bh_matches_hand_computation():
    q = St.bh_qvalues([0.01, 0.04, 0.03, 0.5])
    assert q == pytest.approx([0.04, 0.0533333, 0.0533333, 0.5], rel=1e-4)


def test_hac_lag0_equals_ols_white_and_detects_shift():
    rng = np.random.default_rng(1)
    s = (rng.random(4000) < 0.2).astype(float)
    y = rng.normal(0, 1, 4000) + 0.3 * s
    t = St.hac_state_test(y, s, lags=0)
    assert t["b"] == pytest.approx(y[s == 1].mean() - y[s == 0].mean())
    assert t["p"] < 1e-6
    t24 = St.hac_state_test(rng.normal(0, 1, 4000), s, lags=24)
    assert t24["p"] > 0.001


def test_mfe_mae_direction():
    px = pd.DataFrame({"close": [100.0, 101, 99], "high": [100.0, 102, 100], "low": [100.0, 98, 97]})
    mfe, mae = St.mfe_mae(px, pd.Series([1.0, 1, 1]), 2)
    assert mfe[0] == pytest.approx(1e4 * np.log(1.02))
    assert mae[0] == pytest.approx(1e4 * np.log(0.97))
    mfe_s, _ = St.mfe_mae(px, pd.Series([-1.0, -1, -1]), 2)
    assert mfe_s[0] == pytest.approx(-1e4 * np.log(0.97))


# ---------------------------------------------------------------- causality (the discriminating check)
@pytest.mark.parametrize("hid", [h["id"] for h in HYPOTHESES])
def test_state_and_score_ignore_the_future(hid):
    """Corrupting every bar after t* must not change pop/S/score at or before t*."""
    F = frames(3)
    cut = pd.Timestamp("2024-09-15 12:00", tz="UTC")
    G = {}
    for s, df in F.items():
        g = df.copy()
        late = g.index > cut
        g.loc[late, ["open", "high", "low", "close"]] *= 3.0
        g.loc[late, "funding"] = -0.01
        g.loc[late, "oi"] *= 0.1
        g.loc[late, "buyratio"] = 0.99
        G[s] = g
    asset = next(h for h in HYPOTHESES if h["id"] == hid)["required_assets"][0]
    a, b = S.build(hid, F, asset), S.build(hid, G, asset)
    upto = F[asset].index <= cut
    pd.testing.assert_series_equal(a.pop[upto], b.pop[upto])
    pd.testing.assert_series_equal(a.S[upto], b.S[upto])
    pd.testing.assert_series_equal(a.score[upto], b.score[upto], check_names=False)


def test_quantile_threshold_excludes_current_bar():
    x = pd.Series(np.arange(1000, dtype=float))
    q = S.q_past(x, 0.8)
    assert np.isnan(q[719]) and q[720] == pytest.approx(np.quantile(np.arange(720), 0.8))


def test_align_aux_uses_only_rows_at_or_before_bar_open():
    bars = pd.date_range("2024-03-01", periods=10, freq="1h", tz="UTC")
    f = pd.Series([1.0, 2.0], index=[bars[0], bars[8] + pd.Timedelta("1min")])
    out = D.align_aux(bars, f)
    assert (out.iloc[:9] == 1.0).all() and out.iloc[9] == 2.0


def test_loader_clips_at_validation_start(tmp_path):
    idx = pd.date_range("2025-02-28 22:00", periods=4, freq="1h", tz="UTC")
    pd.DataFrame({"timestamp": idx, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}).to_csv(
        tmp_path / f"BTCUSDT_60_{D.TRAIN1}.csv", index=False)
    df = D.load_ohlcv(tmp_path, "BTCUSDT")
    assert df.index.max() < D.T_END and len(df) == 2


# ---------------------------------------------------------------- pipeline
def _planted_reversal(seed):
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.006, len(IDX))
    for t in range(1, len(r)):
        if r[t - 1] > 0.009:  # large up bar -> strong next-bar reversal
            r[t] -= 0.006
    return r


def test_pipeline_recovers_planted_reversal_and_counts_family(monkeypatch):
    F = {"BTCUSDT": frame(10, _planted_reversal(10)), "ETHUSDT": frame(11, _planted_reversal(11)),
         "SOLUSDT": frame(12)}
    monkeypatch.setattr(R, "check_frozen", lambda: registry_sha256())
    res = R.run(F)
    v = {x["hyp_id"]: x for x in res["verdicts"]}
    assert v["H-PS-REV-UP"]["survives"], v["H-PS-REV-UP"]
    assert not v["H-PS-VOL-COMPRESS"]["C5"]  # non-tradable fails C5 by construction
    prim = [r for r in res["ledger"] if r["primary"] and r["role"] == "required"]
    assert len(prim) == PROTOCOL["fdr"]["m"] == 56
    assert {r["hyp_id"] for r in res["ledger"]} == {h["id"] for h in HYPOTHESES}


def test_missing_aux_is_skipped_but_stays_in_family(monkeypatch):
    F = frames(20)
    for df in F.values():
        df["buyratio"] = np.nan
    monkeypatch.setattr(R, "check_frozen", lambda: registry_sha256())
    res = R.run(F)
    sk = [r for r in res["ledger"] if r["hyp_id"] == "H-OF-BUYRATIO-HI" and r["primary"]]
    assert sk and all(r["status"] == "SKIPPED" and r["p"] == 1.0 and "q" in r for r in sk)
    assert not any(v["survives"] for v in res["verdicts"] if v["hyp_id"].startswith("H-OF"))
