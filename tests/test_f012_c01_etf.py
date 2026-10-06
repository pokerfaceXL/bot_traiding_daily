"""F012-C01: Farside parsing, ET/DST windows and point-in-time helpers."""
import numpy as np
import pandas as pd

from etf_lab import data as D
from etf_lab import gates as G


def test_parse_farside_drops_holidays_and_fills_issuer_blanks(tmp_path):
    p = tmp_path / "f.csv"
    p.write_text("date,IBIT,GBTC,Total\n2024-03-28,10.0,,10.0\n2024-03-29,,,0.0\n2024-04-01,-5.0,2.0,-3.0\n")
    d = D.parse_farside(p)
    assert list(d.date.dt.strftime("%Y-%m-%d")) == ["2024-03-28", "2024-04-01"]
    assert d.GBTC.tolist() == [0.0, 2.0]


def test_et_window_is_dst_aware():
    assert D.et_to_utc("2024-03-08", "15:00") == pd.Timestamp("2024-03-08 20:00", tz="UTC")  # EST
    assert D.et_to_utc("2024-03-11", "15:00") == pd.Timestamp("2024-03-11 19:00", tz="UTC")  # EDT
    assert D.et_to_utc("2024-11-04", "16:00") == pd.Timestamp("2024-11-04 21:00", tz="UTC")


def _bars(start="2024-07-01 18:00", n=36):
    idx = pd.date_range(start, periods=n, freq="5min", tz="UTC")
    c = 100 + np.arange(n, dtype=float)
    return pd.DataFrame({"open": c - 0.5, "high": c + 1, "low": c - 1, "close": c, "v": 1.0}, index=idx)


def test_window_bars_half_open_and_price_at_uses_completed_bars():
    b = _bars()
    w = D.window_bars(b, "2024-07-01", "15:00", "16:00")  # EDT → 19:00–20:00 UTC
    assert w.index[0] == pd.Timestamp("2024-07-01 19:00", tz="UTC") and len(w) == 12
    assert w.index[-1] == pd.Timestamp("2024-07-01 19:55", tz="UTC")
    # 19:00 UTC: last completed bar is the one opened 18:55
    assert D.price_at(b, pd.Timestamp("2024-07-01 19:00", tz="UTC")) == b.close.loc["2024-07-01 18:55+00:00"]
    s = D.window_stats(b, "2024-07-01", "15:00", "16:00", "v")
    assert np.isclose(s["ret"], np.log(b.close.iloc[23] / b.open.iloc[12])) and s["vol"] == 12


def test_pit_quantile_flag_uses_only_strictly_past_values():
    x = np.r_[np.ones(20), 5.0, 1.0]
    f = G.pit_quantile_flag(x, 0.8)
    assert not f[:20].any() and f[20] and f[21]  # 1.0 ≥ q80 of past (still 1.0)
    x2 = x.copy()
    x2[21] = 100.0  # a future value must not change earlier flags
    assert (G.pit_quantile_flag(x2, 0.8)[:21] == f[:21]).all()


def test_build_daily_lags_are_strictly_prior(monkeypatch):
    far = pd.DataFrame({"date": pd.to_datetime(["2024-03-01", "2024-03-04", "2024-03-05"]),
                        "Total": [1.0, 2.0, 3.0], "IBIT": [1.0, 1.0, 1.0], "GBTC": [0.0] * 3, "FBTC": [0.0] * 3})
    idx = pd.date_range("2024-02-29", "2024-03-06", freq="5min", tz="UTC")
    cb = pd.DataFrame({"close": np.linspace(100, 110, len(idx))}, index=idx)
    monkeypatch.setattr(D, "etf_daily", lambda: pd.DataFrame(
        {"etf_dollar_vol": [1.0, 2.0, 3.0], "ibit_close": [1.0, 1.0, 1.0]}, index=far.date))
    d = D.build_daily(far, cb)
    assert d.y_lag1.tolist()[1:] == [1.0, 2.0]
    assert (d.obs_live_utc < d.window_start_utc).all()


def test_folds_and_holm():
    f = G.folds(250)
    assert (np.diff(f) >= 0).all() and set(f) == {1, 2, 3} and (f == 3).sum() == 84
    assert np.allclose(G.holm([0.01, 0.04]), [0.02, 0.04])


def test_walk_forward_prediction_never_sees_target_day():
    n = 80
    t1 = pd.DataFrame({c: np.random.default_rng(1).normal(size=n) for c in G.PIT_X})
    t1["y"] = t1.y_lag1 * 2.0
    p1 = G.predict(t1, "M3", walk=True)
    t2 = t1.copy()
    t2.loc[70, "y"] = 1e6  # poisoning y on day 70 must not affect the day-70 prediction
    p2 = G.predict(t2, "M3", walk=True)
    assert np.isclose(p1[70], p2[70]) and not np.isclose(p1[71], p2[71])
