"""F012-C02: announcement parsing + causality of the event-study price/entry helpers."""
import numpy as np
import pandas as pd

from delisting_lab import analysis as A
from delisting_lab.catalog import (binance_article_events, bybit_article_events, observable_times,
                                   parse_datetimes, perp_symbols)

T = pd.Timestamp


def _ms(s):
    return int(T(s, tz="UTC").value // 10**6)


def test_parse_bybit_and_binance_datetime_forms():
    got = [ts for _, ts in parse_datetimes("delisting the BNXUSDT Perpetual Contract at Mar 17, 2025, 9:00AM UTC.")]
    assert got == [_ms("2025-03-17 09:00")]
    got = [ts for _, ts in parse_datetimes("Contracts at 12AM UTC on Jun 7, 2024.")]
    assert got == [_ms("2024-06-07 00:00")]
    got = [ts for _, ts in parse_datetimes("settlement ... at 2025-01-22 09:00 (UTC). The contract")]
    assert got == [_ms("2025-01-22 09:00")]
    got = [ts for _, ts in parse_datetimes("after 8AM UTC on Mar 11, 2025 and 12:30PM UTC on Mar 12, 2025")]
    assert got == [_ms("2025-03-11 08:00"), _ms("2025-03-12 12:30")]


def test_observable_times_rule():
    d = _ms("2025-02-27 10:47")
    assert observable_times(d, d + 37_000) == (d, d + 37_000, "")
    assert observable_times(d, d - 3_000_000) == (d - 3_000_000, d, "")  # earlier push → ann earlier, obs = later
    a, o, flag = observable_times(d, d + 97 * 86_400_000)  # later edit ignored
    assert (a, o) == (d, d) and flag.startswith("publishTime_gap")


def test_binance_token_delist_extracts_perps_and_spot():
    text = ("we have decided to delist and cease trading on all spot trading pairs for the following token(s) at "
            "2025-02-24 03:00 (UTC):\nAirDAO (AMB)\n\nCLV (CLV)\n\nPlease Note:\n"
            "Binance Futures will close all positions and conduct an automatic settlement on the AMBUSDT and "
            "STMXUSDT USDⓈ-M Perpetual Contracts at 2025-02-21 09:00 (UTC). The contracts will be delisted.")
    r = binance_article_events("Binance Will Delist AMB, CLV, STMX, VITE on 2025-02-24", text)
    assert r["category"] == "token_delist"
    assert r["perps"] == [("AMBUSDT", _ms("2025-02-21 09:00")), ("STMXUSDT", _ms("2025-02-21 09:00"))]
    assert r["spot_tokens"] == ["AMB", "CLV"] and r["spot_eff"] == _ms("2025-02-24 03:00")


def test_binance_pair_removal_is_not_an_event():
    r = binance_article_events("Notice of Removal of Spot Trading Pairs - 2025-02-28", "anything")
    assert r["category"] == "pair_or_product_removal" and not r["perps"]


def test_bybit_perp_article():
    r = bybit_article_events("Delisting of FETUSDT, OCEANUSDT, and AGIXUSDT Perpetual Contracts", "",
                             "Bybit will be delisting ... at Jun 7, 2024, 10:00AM UTC.")
    assert [s for s, _ in r["perps"]] == ["FETUSDT", "OCEANUSDT", "AGIXUSDT"]
    assert {e for _, e in r["perps"]} == {_ms("2024-06-07 10:00")}
    assert perp_symbols("1000IQ50USDT and 10000STARLUSDT") == ["1000IQ50USDT", "10000STARLUSDT"]


# ---------------------------------------------------------------- causality
def _event(bars_close, ann="2024-06-01 10:00:30", obs=None, eff="2024-06-03 10:00"):
    ann = T(ann, tz="UTC")
    obs = T(obs, tz="UTC") if obs else ann
    idx = pd.date_range("2024-06-01 09:00", periods=len(bars_close), freq="1min", tz="UTC")
    bars = pd.DataFrame({"open": bars_close, "high": bars_close, "low": bars_close, "close": bars_close,
                         "quote_volume": 1.0, "count": 1}, index=idx)
    ev = pd.Series({"event_id": "X", "announcement_ts": ann, "first_publicly_observable_ts": obs,
                    "effective_ts": T(eff, tz="UTC")})
    btc = pd.Series(1.0, index=pd.date_range("2024-05-01", "2024-07-01", freq="1min", tz="UTC"))
    d = A.EventData.__new__(A.EventData)
    d.ev, d.bars, d.ticks, d.h1, d.oi, d.fund, d.spot, d.btc = ev, bars, None, None, None, None, None, btc
    d.close = pd.Series(bars.close.values, index=bars.index + A.MIN)
    d.spot_close = None
    return d


def test_px_uses_only_completed_bars():
    closes = np.arange(1.0, 200.0)
    d = _event(closes)
    t = T("2024-06-01 10:00:30", tz="UTC")  # inside bar 10:00 (index 60, close 61)
    assert d.px(t) == 60.0  # bar 09:59 (ended 10:00) — never the still-open 10:00 bar
    assert d.px(T("2024-06-01 10:01", tz="UTC")) == 61.0


def test_entry_is_anchored_on_observable_time_not_announcement():
    closes = np.arange(1.0, 300.0)
    d = _event(closes, ann="2024-06-01 10:00:30", obs="2024-06-01 10:20:10")
    t, p = d.entry("bar5m")
    assert t == T("2024-06-01 10:30", tz="UTC") and p == d.px(t)
    t1, _ = d.entry("bar1m")
    assert t1 == T("2024-06-01 10:22", tz="UTC")
    t60, _ = d.entry("60s")  # no ticks → degrade to next completed 1m bar after obs
    assert t60 >= d.ev.first_publicly_observable_ts


def test_horizons_never_extend_past_effective():
    closes = np.full(4000, 10.0)
    d = _event(closes, eff="2024-06-02 10:00")  # 23.5h notice
    m = A.event_metrics(d)
    assert np.isnan(m["car_24h"]) and np.isnan(m["car_72h"])
    assert np.isnan(m["short_bar5m_+24h"]) and np.isnan(m["short_bar5m_+72h"])
    assert m["short_bar5m_eff-1h"] == 0.0


def test_short_funding_counts_only_settlements_inside_holding_window():
    idx = pd.to_datetime(["2024-05-01 00:00", "2024-05-01 08:00", "2024-05-01 16:00"], utc=True)
    f = pd.DataFrame({"rate": [0.001, -0.002, 0.004]}, index=idx)
    t0, t1 = pd.Timestamp("2024-05-01 00:00", tz="UTC"), pd.Timestamp("2024-05-01 08:00", tz="UTC")
    assert A.short_funding(f, t0, t1) == -0.002  # 00:00 excluded (entered at it), 08:00 included
    assert np.isnan(A.short_funding(None, t0, t1))


def test_owner_cost_and_multiplier():
    assert A.contract_multiplier("10000NFTUSDT") == 10000 and A.contract_multiplier("GALUSDT") == 1
    assert abs(A.owner_rt_cost(6.0, 20.0) * 1e4 - (8.8 + 3.0 + 10.0)) < 1e-9
    assert abs(A.owner_rt_cost(np.nan, -1.0) * 1e4 - 8.8) < 1e-9
