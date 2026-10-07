"""F013 discovery gate helpers — pure, no network."""
import numpy as np
import pandas as pd
import pytest

from delisting_lab import f013_core as C
from delisting_lab import f013_gates as G
from delisting_lab.catalog import parse_datetimes
from delisting_lab.f013_placebo import draw_pseudo_p
from delisting_lab.f013_sample import primary_window, token_clusters

T0 = pd.Timestamp("2024-06-01 08:00", tz="UTC")


def bars(n=200, start=T0, step=1.0):
    idx = pd.date_range(start, periods=n, freq="1min")
    o = 100 + step * np.arange(n)
    return pd.DataFrame({"open": o, "high": o + 1, "low": o - 1, "close": o + 0.5, "quote_volume": 1.0,
                         "count": 1.0}, index=idx)


def test_bar_open_at_first_bar_at_or_after():
    b = bars()
    t, p = C.bar_open_at(b, T0 + pd.Timedelta(minutes=5, seconds=1))
    assert t == T0 + pd.Timedelta(minutes=6) and p == 106
    t, p = C.bar_open_at(b, T0 + pd.Timedelta(minutes=5))
    assert p == 105


def test_bar_open_at_respects_max_wait():
    b = bars().drop(bars().index[10:100])
    t, p = C.bar_open_at(b, T0 + pd.Timedelta(minutes=12))
    assert t is None and np.isnan(p)


def test_close_before_is_causal():
    b = bars()
    # bar starting 08:04 ends 08:05 → last bar ended at or before 08:05:30
    assert C.close_before(b, T0 + pd.Timedelta(minutes=5, seconds=30)) == 104.5
    assert C.close_before(b, T0 + pd.Timedelta(minutes=5)) == 104.5


def test_first_tick_at():
    tk = pd.DataFrame({"ts": [T0 + pd.Timedelta(seconds=s) for s in (1, 9, 12, 40)], "price": [1, 2, 3, 4.0]})
    assert C.first_tick_at(tk, T0 + pd.Timedelta(seconds=10))[1] == 3
    assert C.first_tick_at(tk, T0 + pd.Timedelta(minutes=10))[0] is None


def test_short_bp_and_funding_window():
    assert C.short_bp(100, 90) == pytest.approx(1000)
    assert C.short_bp(100, 110) == pytest.approx(-1000)
    f = pd.DataFrame({"rate": [0.001, -0.002, 0.003]},
                     index=[T0, T0 + pd.Timedelta(hours=8), T0 + pd.Timedelta(hours=16)])
    # (entry, exit] excludes the print at entry
    assert C.funding_bp(f, T0, T0 + pd.Timedelta(hours=16)) == pytest.approx(10.0)


def test_exit_target_and_primary_window():
    eff = T0 + pd.Timedelta(hours=30)
    assert C.exit_target(T0, eff) == eff - pd.Timedelta(hours=1)
    assert C.exit_target(T0, T0 + pd.Timedelta(days=10)) == T0 + pd.Timedelta(hours=72)
    e, x = primary_window(T0 + pd.Timedelta(seconds=7), eff)
    assert e == T0 + pd.Timedelta(minutes=6) and x == eff - pd.Timedelta(hours=1)
    assert primary_window(T0, T0 + pd.Timedelta(minutes=110)) is None


def test_cluster_boot_resamples_clusters():
    v = [10, 10, 10, -5]
    cl = ["a", "a", "a", "b"]
    b = C.cluster_boot(v, cl, n_boot=2000)
    # only three possible pooled means: all-a 10, all-b -5, mixed (30-5)/4
    assert set(np.round(np.unique(b), 6)) <= {10.0, -5.0, 6.25}
    assert C.cluster_boot(v, cl, n_boot=50, seed=13).tolist() == C.cluster_boot(v, cl, n_boot=50, seed=13).tolist()


def test_tail_stats():
    v = np.array([100.0, 1, 1, 1, -1, -1, 2, 3, 0, 0])
    ts = C.tail_stats(v)
    assert ts["median"] == pytest.approx(1.0)
    assert ts["mean_ex_top1"] == pytest.approx(np.sort(v)[::-1][1:].mean())
    assert ts["top1_share_of_sum"] == pytest.approx(100 / v.sum())


def test_ols_beta_and_fallback():
    x = np.linspace(-1, 1, 300)
    assert C.ols_beta(2 * x + 0.1, x)[0] == pytest.approx(2.0)
    assert C.ols_beta(2 * x[:50], x[:50]) == (1.0, 50)


def test_restriction_times_binance_phrase():
    txt = "Users are not allowed to open new positions for the aforementioned contracts starting from 2024-03-26 08:30 (UTC)."
    ts = C.restriction_times(txt, parse_datetimes)
    assert ts == [int(pd.Timestamp("2024-03-26 08:30", tz="UTC").value // 10**6)]
    assert C.restriction_times("All open positions will be closed.", parse_datetimes) == []


def test_notice_bins_frozen():
    assert [C.notice_bin(h) for h in (1, 24, 24.1, 72, 100, 168, 169)] == \
        ["(0,24h]", "(0,24h]", "(24h,72h]", "(24h,72h]", "(72h,168h]", "(72h,168h]", ">168h"]


def test_token_clusters_merge_within_30d():
    df = pd.DataFrame({"base": ["X", "X", "X", "Y"],
                       "first_publicly_observable_ts": [T0, T0 + pd.Timedelta(days=20), T0 + pd.Timedelta(days=60), T0]})
    c = token_clusters(df)
    assert c[0] == c[1] != c[2] and c[3] == "Y-0"


def test_pseudo_p_draws_respect_window_and_blocks():
    P = pd.Timestamp("2024-09-01", tz="UTC")
    blk = [P - pd.Timedelta(days=50)]
    d = draw_pseudo_p(P, blk, np.random.default_rng(13), n=200)
    assert len(d) == 200
    assert all(P - pd.Timedelta(days=90) <= x <= P - pd.Timedelta(days=10) for x in d)
    assert all(abs(x - blk[0]) > pd.Timedelta(days=10) for x in d)


def _scored(gross, fund=0.0, n_clusters=30):
    n = len(gross)
    return pd.DataFrame({"event_id": [f"e{i}" for i in range(n)], "gross": gross, "fund": fund,
                         "day_batch_cluster_id": [f"c{i % n_clusters}" for i in range(n)],
                         "has_funding": True})


def test_gate_d_rule():
    assert G.gate_d(_scored(np.full(60, 200.0))).status == "PASS"
    assert G.gate_d(_scored(np.full(60, 100.0))).status == "PASS"  # net@34 = 66, net@75 = 25
    assert G.gate_d(_scored(np.full(60, 60.0))).status == "FAIL"   # mean net@75 < 0


def test_gate_e_funding_trade_fails():
    s = _scored(np.full(60, 20.0), fund=80.0)  # net@34 = 66, ex-funding = -14
    assert G.gate_e(s).status == "FAIL"
    assert G.gate_e(_scored(np.full(60, 200.0), fund=10.0)).status == "PASS"
