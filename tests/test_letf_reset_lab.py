"""F012-R2A lab: calendar, capture parsing and PIT AUM selection (no network)."""
import pandas as pd

from letf_reset_lab import aum
from letf_reset_lab import calendar as cal
from letf_reset_lab.fetch import parse_bitx_capture
from letf_reset_lab.gates import gate0, required_bars


def test_train1_has_250_sessions_and_day_classes():
    assert len(cal.sessions()) == 250
    assert cal.day_class(pd.Timestamp("2024-03-02")) == "placebo"        # Saturday
    assert cal.day_class(pd.Timestamp("2025-01-09")) == "placebo"        # Carter mourning
    assert cal.day_class(pd.Timestamp("2024-11-29")) == "early_close"
    assert cal.prev_session(pd.Timestamp("2024-04-01")) == pd.Timestamp("2024-03-28")  # Good Friday skip


def test_signal_start_is_prior_close_dst_aware():
    mon = required_bars(pd.Timestamp("2024-03-11"))      # first Monday after DST start
    assert mon["coinbase"][0] == pd.Timestamp("2024-03-08 21:00", tz="UTC")   # Fri 16:00 EST
    assert mon["coinbase"][1] == pd.Timestamp("2024-03-11 19:00", tz="UTC")   # Mon 15:00 EDT
    after_early = required_bars(pd.Timestamp("2024-12-26"))
    assert after_early["coinbase"][0] == pd.Timestamp("2024-12-24 18:00", tz="UTC")  # 13:00 EST close
    sat = required_bars(pd.Timestamp("2024-03-09"))
    assert sat["coinbase"][0] == pd.Timestamp("2024-03-08 21:00", tz="UTC")


def test_parse_bitx_capture():
    html = ("<div>Net Assets as of 12/03/2024</div> <b>$3,299,605,044.01</b> NAV <i>$58.04</i> "
            "Shares Outstanding 56,850,000 Premium")
    rec = parse_bitx_capture(html)
    assert rec["as_of"] == pd.Timestamp("2024-12-03") and rec["shares"] == 56_850_000
    assert parse_bitx_capture("<p>nothing here</p>") is None


def _obs(as_of, avail_utc, val=1e9):
    return pd.DataFrame({"as_of": [pd.Timestamp(as_of)], "aum": [val],
                         "available_utc": [pd.Timestamp(avail_utc, tz="UTC")]})


def test_pick_pit_rejects_lookahead_and_counts_staleness():
    sess = cal.sessions()
    t = pd.Timestamp("2024-12-05")  # Thursday
    # value for 12-04 close published 12-05 01:00 UTC -> fresh
    assert aum.pick_pit(_obs("2024-12-04", "2024-12-05 01:00"), t, sess)["status"] == "ok"
    # value captured after 15:00 ET on t is not usable
    assert aum.pick_pit(_obs("2024-12-04", "2024-12-05 20:30"), t, sess)["status"] == "missing"
    # as-of == t itself is never usable
    assert aum.pick_pit(_obs("2024-12-05", "2024-12-05 10:00"), t, sess)["status"] == "missing"
    # 12-02 close used on 12-05: sessions 12-03, 12-04 in between -> stale 2
    r = aum.pick_pit(_obs("2024-12-02", "2024-12-03 01:00"), t, sess)
    assert r["status"] == "stale" and r["stale"] == 2
    # older than 3 sessions -> missing (not zero)
    r = aum.pick_pit(_obs("2024-11-26", "2024-11-27 01:00"), t, sess)
    assert r["status"] == "missing" and r["stale"] > aum.MAX_STALE


def test_bitx_obs_drops_capture_showing_future_as_of():
    wb = pd.DataFrame({"parsed": [True, True], "as_of": pd.to_datetime(["2024-09-05", "2024-05-02"]),
                       "net_assets": [1.0, 2.0],
                       "capture_utc": pd.to_datetime(["2024-08-12 03:00", "2024-05-03 08:00"], utc=True)})
    o = aum.bitx_obs(wb)
    assert list(o.as_of) == [pd.Timestamp("2024-05-02")]


def test_gate0_kills_on_bitx_coverage():
    sess = cal.sessions()
    pan = pd.DataFrame({"date": sess, "fund": "BITX", "status": ["ok"] * 100 + ["missing"] * 150})
    pcov = pd.DataFrame({"date": sess, "class": "us", "covered": True})
    g = gate0(pan, pcov, {"BITX": "PIT-BY-CAPTURE"})
    assert g["verdict"] == "KILL" and "BITX" in g["reasons"][0]
    pan["status"] = "ok"
    assert gate0(pan, pcov, {"BITX": "PIT-BY-CAPTURE"})["verdict"] == "PASS"
