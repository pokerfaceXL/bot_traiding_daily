"""PIT AUM panel A_{i,t-1} per prereg §5 (as-of <= t-1, published before 15:00 ET on t, carry <= 3 sessions)."""
from __future__ import annotations

import pandas as pd

from . import calendar as cal

MAX_STALE = 3  # sessions of carry-forward before a fund-day is MISSING


def staleness(as_of: pd.Timestamp, t: pd.Timestamp, sess: pd.DatetimeIndex) -> int:
    """Sessions s with as_of < s <= prev_session(t). 0 means the value is the t-1 close."""
    prev = cal.prev_session(t)
    return int(((sess > as_of) & (sess <= prev)).sum())


def pick_pit(obs: pd.DataFrame, t: pd.Timestamp, sess: pd.DatetimeIndex) -> dict:
    """Latest observation usable at 15:00 ET on session t.

    obs columns: as_of (date), aum, available_utc (tz-aware time the value was observably public).
    A value is usable iff available_utc <= 15:00 ET on t and as_of <= prev_session(t).
    """
    cutoff = cal.et(t, 15).tz_convert("UTC")
    prev = cal.prev_session(t)
    ok = obs[(obs.available_utc <= cutoff) & (obs.as_of <= prev)]
    if ok.empty:
        return {"as_of": pd.NaT, "aum": float("nan"), "stale": None, "status": "missing"}
    row = ok.sort_values(["as_of", "available_utc"]).iloc[-1]
    st = staleness(row.as_of, t, sess)
    return {"as_of": row.as_of, "aum": float(row.aum), "stale": st,
            "status": "ok" if st == 0 else ("stale" if st <= MAX_STALE else "missing")}


def bitx_obs(wb: pd.DataFrame) -> pd.DataFrame:
    """Wayback captures -> observations. A capture proves publication no later than its capture time.

    Captures whose displayed as-of date is after the capture's ET date are dropped (cannot be PIT).
    """
    w = wb[wb.parsed].copy()
    w["available_utc"] = w.capture_utc
    cap_et_date = w.capture_utc.dt.tz_convert(cal.ET).dt.tz_localize(None).dt.normalize()
    w["pit_valid"] = w.as_of <= cap_et_date
    w["aum"] = w.net_assets
    return w[w.pit_valid][["as_of", "aum", "available_utc"]]


def issuer_history_obs(hist: pd.DataFrame) -> pd.DataFrame:
    """Issuer history row dated D is the D close, published that evening (as-of rule, labelled).

    available_utc = D 20:00 ET, a conservative evening publication assumption (UNVERIFIED-LABELED).
    """
    h = hist.copy()
    h["as_of"] = h.date
    h["available_utc"] = [cal.et(d, 20).tz_convert("UTC") for d in h.date]
    return h[["as_of", "aum", "available_utc"]]


def panel(obs_by_fund: dict[str, pd.DataFrame], launch: dict[str, pd.Timestamp | None]) -> pd.DataFrame:
    """Per (session, fund) PIT AUM with status ok|stale|missing|absent (absent = before first NAV row)."""
    sess = cal.sessions()
    rows = []
    for t in sess:
        for fund, obs in obs_by_fund.items():
            first = launch.get(fund)
            if first is not None and cal.prev_session(t) < first:
                rows.append({"date": t, "fund": fund, "as_of": pd.NaT, "aum": 0.0, "stale": None, "status": "absent"})
                continue
            rows.append({"date": t, "fund": fund, **pick_pit(obs, t, sess)})
    return pd.DataFrame(rows)
