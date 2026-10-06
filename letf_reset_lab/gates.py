"""Gate 0 (data) for F012-R2A, prereg §5/§7. Gates 1-5 run only if Gate 0 passes."""
from __future__ import annotations

import pandas as pd

from . import calendar as cal

BITX_COVERAGE_MIN = 0.90
PRICE_COVERAGE_MIN = 0.95


def required_bars(d: pd.Timestamp) -> dict[str, list[pd.Timestamp]]:
    """5m bar opens (UTC) needed for the primary signal and outcome on day d (prereg §3/§4)."""
    if cal.day_class(d) == "placebo":
        start = cal.et(d - pd.Timedelta(days=1), 16)
    else:
        start = cal.close_time(cal.prev_session(d))
    return {"coinbase": [start.tz_convert("UTC"), cal.et(d, 15).tz_convert("UTC")],
            "bybit": [cal.et(d, 15).tz_convert("UTC"), cal.et(d, 16).tz_convert("UTC")]}


def price_coverage(cb: pd.DataFrame, by: pd.DataFrame) -> pd.DataFrame:
    have = {"coinbase": set(cb.timestamp), "bybit": set(by.timestamp)}
    rows = []
    for d in cal.all_days():
        cls = cal.day_class(d)
        if cls == "early_close":
            continue
        need = required_bars(d)
        miss = [f"{v}@{ts.isoformat()}" for v, tss in need.items() for ts in tss if ts not in have[v]]
        rows.append({"date": d, "class": cls, "covered": not miss, "missing_bars": ";".join(miss)})
    return pd.DataFrame(rows)


def gate0(aum_panel: pd.DataFrame, pcov: pd.DataFrame, pit_status: dict[str, str]) -> dict:
    sess = cal.sessions()
    bx = aum_panel[aum_panel.fund == "BITX"].set_index("date")
    bitx_ok = bx.status.isin(["ok", "stale"])
    bitx_cov = float(bitx_ok.mean())
    us = pcov[pcov["class"] == "us"]
    price_cov = float(us.covered.mean())
    contradicted = [f for f, s in pit_status.items() if s == "CONTRADICTED"]
    reasons = []
    if bitx_cov < BITX_COVERAGE_MIN:
        reasons.append(f"BITX PIT AUM coverage {bitx_cov:.1%} < {BITX_COVERAGE_MIN:.0%}")
    if price_cov < PRICE_COVERAGE_MIN:
        reasons.append(f"5m price coverage {price_cov:.1%} < {PRICE_COVERAGE_MIN:.0%}")
    if contradicted:
        reasons.append(f"PIT CONTRADICTED: {contradicted}")
    per_fund = {}
    for f, g in aum_panel.groupby("fund"):
        live = g[g.status != "absent"]
        per_fund[f] = {"sessions": int(len(g)), "absent_prelaunch": int((g.status == "absent").sum()),
                       "ok": int((g.status == "ok").sum()), "stale": int((g.status == "stale").sum()),
                       "missing": int((g.status == "missing").sum()),
                       "coverage_of_live": float(live.status.isin(["ok", "stale"]).mean()) if len(live) else None,
                       "pit_status": pit_status.get(f)}
    return {"gate": 0, "verdict": "KILL" if reasons else "PASS", "reasons": reasons,
            "n_sessions": int(len(sess)), "bitx_pit_coverage": bitx_cov,
            "bitx_sessions_covered": int(bitx_ok.sum()),
            "price_coverage_us": price_cov, "price_us_days": int(len(us)),
            "price_coverage_placebo": float(pcov[pcov["class"] == "placebo"].covered.mean()),
            "price_placebo_days": int((pcov["class"] == "placebo").sum()),
            "per_fund": per_fund}
