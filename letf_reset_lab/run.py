"""One-command reproduction of F012-R2A: python3 -m letf_reset_lab.run

Fetches (cached), builds the PIT AUM panel, runs gates in prereg order and stops at the first KILL.
Writes output/f012_r2a_letf_reset/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from . import aum, fetch
from . import calendar as cal
from .gates import gate0, price_coverage

OUT = Path("output/f012_r2a_letf_reset")
LEVERAGE = {"BITX": 2, "BITU": 2, "SBIT": -2}
PIT_TIMELINE = [
    # fund, L, source, url, as-of rule, publication evidence, PIT status rule
    ("BITX", 2, "Volatility Shares fund page (current snapshot only; no daily history file)",
     fetch.BITX_PAGE, "page shows 'Net Assets as of D' = D close",
     "Wayback capture time (UTC) = latest possible publication", "PIT by capture; sparse"),
    ("BITX", 2, "Volatility Shares premium/discount PDF", "https://www.volatilityshares.com/download-premium-discount.php?ukey=bitx",
     "chart of premium/discount only", "n/a", "no NAV x shares history -> unusable"),
    ("BITX", 2, "Volatility Shares holdings XLS", "https://www.volatilityshares.com/download-holdings-usbanks.php?fund=bitx",
     "current holdings, no date or shares field", "3 Train-1 captures", "unusable for AUM"),
    ("BITU", 2, "ProShares issuer history CSV (NAV, shares, AUM)", fetch.PROSHARES_URL.format(t="BITU"),
     "row D = D close", "downloaded 2026-10-06; assumed public D 20:00 ET", "UNVERIFIED-LABELED"),
    ("SBIT", -2, "ProShares issuer history CSV (NAV, shares, AUM)", fetch.PROSHARES_URL.format(t="SBIT"),
     "row D = D close", "downloaded 2026-10-06; assumed public D 20:00 ET", "UNVERIFIED-LABELED"),
    ("ALL", None, "SEC EDGAR N-PORT", "https://www.sec.gov/cgi-bin/browse-edgar", "monthly holdings",
     "EDGAR acceptance time", "monthly only -> never daily AUM (prereg §5.3)"),
]
LEVERAGE_EVIDENCE = {
    "BITX": "volatilityshares.com/bitx: '2x Bitcoin ETF' (archived Train-1 title '2x Bitcoin Strategy ETF')",
    "BITU": "proshares.com BITU: 'daily investment results ... two times (2x) the daily performance of the Bloomberg Bitcoin Index'",
    "SBIT": "proshares.com SBIT: 'daily investment results ... -2x the daily performance of its underlying benchmark'",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- AUM sources (prereg §5 hierarchy)
    wb = fetch.bitx_wayback()
    wb.to_csv(OUT / "bitx_wayback_captures.csv", index=False)
    hist = {t: fetch.proshares_nav(t) for t in ("BITU", "SBIT")}
    for t, h in hist.items():
        h[(h.date >= "2024-03-01") & (h.date <= "2025-02-28")].to_csv(OUT / f"proshares_{t}_train1.csv", index=False)
    # ProShares archived fund pages render NAV/shares via JS: no comparable Train-1 capture exists,
    # and the history CSV itself has no Train-1 Wayback capture -> UNVERIFIED-LABELED (prereg §5).
    pit_status = {"BITX": "PIT-BY-CAPTURE", "BITU": "UNVERIFIED-LABELED", "SBIT": "UNVERIFIED-LABELED"}
    obs = {"BITX": aum.bitx_obs(wb),
           "BITU": aum.issuer_history_obs(hist["BITU"]),
           "SBIT": aum.issuer_history_obs(hist["SBIT"])}
    launch = {"BITX": None, "BITU": hist["BITU"].date.min(), "SBIT": hist["SBIT"].date.min()}
    pan = aum.panel(obs, launch)
    pan.to_csv(OUT / "aum_pit_panel.csv", index=False)
    pd.DataFrame(PIT_TIMELINE, columns=["fund", "L", "source", "url", "as_of_rule", "publication_evidence",
                                        "pit_status"]).to_csv(OUT / "pit_timeline.csv", index=False)

    # BITX sanity: captured NAV vs Yahoo close on the as-of date (consistency, not PIT)
    yb = fetch.yahoo_daily("BITX")
    chk = wb[wb.parsed].merge(yb.rename(columns={"date": "as_of", "close": "yahoo_close"}), on="as_of", how="left")
    chk["nav_vs_close_pct"] = 100 * (chk.nav / chk.yahoo_close - 1)
    chk[["served_ts", "as_of", "nav", "yahoo_close", "nav_vs_close_pct"]].to_csv(OUT / "bitx_nav_vs_yahoo.csv", index=False)

    # Calendar cross-check: hard-coded NYSE sessions vs BITX Yahoo trading dates
    ysess = set(yb.date)
    sess = cal.sessions()
    cal_check = {"hardcoded_sessions": int(len(sess)), "yahoo_bitx_sessions": int(len(ysess)),
                 "in_hardcoded_not_yahoo": [str(d.date()) for d in sess if d not in ysess],
                 "in_yahoo_not_hardcoded": [str(d.date()) for d in sorted(ysess) if d not in set(sess)]}

    # ---- price coverage (Gate 0 second leg)
    cb, by = fetch.coinbase_5m(), fetch.bybit_5m()
    pcov = price_coverage(cb, by)
    pcov.to_csv(OUT / "price_coverage.csv", index=False)

    g0 = gate0(pan, pcov, pit_status)
    bx = pan[pan.fund == "BITX"]
    g0["bitx_distinct_as_of"] = sorted(str(d.date()) for d in obs["BITX"].as_of.unique())
    g0["bitx_covered_dates"] = [str(d.date()) for d in bx[bx.status.isin(["ok", "stale"])].date]
    g0["bitx_wayback_captures"] = {"cdx_rows": int(len(fetch.wayback_index(fetch.BITX_PAGE))),
                                   "distinct_served": int(len(wb)), "parsed": int(wb.parsed.sum()),
                                   "pit_valid": int(len(obs["BITX"]))}
    g0["calendar_check"] = cal_check
    g0["leverage_evidence"] = LEVERAGE_EVIDENCE
    (OUT / "gate0_coverage.json").write_text(json.dumps(g0, indent=2, default=str))

    gates = {"0": g0["verdict"]}
    if g0["verdict"] == "KILL":
        gates.update({k: "NOT REACHED" for k in "12345"})
        verdict, killed = "FAIL", "Gate 0 (Data)"
    else:  # prereg: gates 1-5 would run here; not implemented because not reached in this study
        raise SystemExit("Gate 0 passed: gates 1-5 must be implemented per prereg before scoring.")

    inputs = sorted(p for p in fetch.CACHE.rglob("*") if p.is_file())
    (OUT / "inputs_sha256.json").write_text(json.dumps({str(p): sha256(p) for p in inputs}, indent=2))
    summary = {"study": "F012-R2A LETF daily reset identification", "train1": list(cal.TRAIN1),
               "prereg": "spec/features/active/F012-r2a-letf-reset-identification/prereg.md",
               "verdict": verdict, "killed_by": killed, "gates": gates, "gate0_reasons": g0["reasons"],
               "bitx_pit_coverage": g0["bitx_pit_coverage"], "price_coverage_us": g0["price_coverage_us"],
               "pit_status": pit_status, "cost_primary_bp_rt": 9.92,
               "outcomes_scored": False}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
