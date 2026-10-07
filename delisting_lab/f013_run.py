"""F013 discovery runner: Gates B–N, P, Q on Gate-A-usable C02 Train-1 events (prereg §6, §9).

Gates are evaluated in prereg order B, C, …, N, P, Q. The run STOPS at the first FAIL (KILL gate
or thesis-mismatch / Gate F FAIL): later gates are recorded NOT_RUN and the validation window
stays closed. Gate O is never scored here.

Run: python3 -m delisting_lab.f013_run
Writes output/f013_delisting_info/{event_table.csv, gate_<x>_*.{csv,md}, summary.json}.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from delisting_lab import f013_gates as G
from delisting_lab.f013_events import build_table
from delisting_lab.f013_sample import load_events
from delisting_lab.f013_timestamp_audit import OUT

ORDER = list("BCDEFGHIJKLMNPQ")
FAIL_STOPS = {"FAIL"}


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def write_gate(r: G.GateResult) -> None:
    name = f"gate_{r.gate.lower()}_{slug(r.title)}"
    r.table.to_csv(OUT / f"{name}.csv", index=False)
    md = [f"# F013 Gate {r.gate} — {r.title} ({r.kind})", "",
          f"**Status: {r.status}** · discovery = C02 Train-1 (contaminated) · net@34 = mean net bp at 34 bp RT incl. "
          "funding · CI = day-batch cluster bootstrap 95 % (10 000, seed 13) unless the row says otherwise.", "",
          G.fmt(r.table), ""] + [f"- {n}" for n in r.notes]
    (OUT / f"{name}.md").write_text("\n".join(md) + "\n")


def excluded_scored(t: pd.DataFrame) -> pd.DataFrame:
    x = t[~t.in_primary_universe]
    x = x[~x.insufficient_notice.fillna(True) & x.eligible.fillna(False).astype(bool) & x.gross.notna()]
    return x[(x.turnover_24h >= G.K_MIN_TURNOVER) & (x.zero_vol_share_24h <= G.K_MAX_ZERO_SHARE)]


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    ev = load_events(include_excluded=True)
    t = build_table(ev)
    t["delist_type_m"] = t.delist_type.replace({"spot_delisted_perp_live": "spot_and_perp"})
    t.to_csv(OUT / "event_table.csv", index=False)
    f = G.funnel(t)
    s = f["scored"]
    runners = {
        "B": lambda: G.gate_b(s), "C": lambda: G.gate_c(f), "D": lambda: G.gate_d(s), "E": lambda: G.gate_e(s),
        "F": lambda: G.gate_f(s), "G": lambda: G.gate_g(s), "H": lambda: G.gate_h(s), "I": lambda: G.gate_i(s),
        "J": lambda: G.gate_j(s), "K": lambda: G.gate_k(f), "L": lambda: G.gate_l(s),
        "M": lambda: G.gate_m(s, excluded_scored(t)), "N": lambda: G.gate_n(s), "Q": lambda: G.gate_q(s),
    }
    from delisting_lab.f013_placebo import gate_p
    runners["P"] = lambda: gate_p(s, ev)

    results, stopped = {}, None
    for g in ORDER:
        if stopped:
            results[g] = {"status": "NOT_RUN", "reason": f"stopped after Gate {stopped} FAIL"}
            continue
        r = runners[g]()
        write_gate(r)
        results[g] = {"kind": r.kind, "title": r.title, "status": r.status, "notes": r.notes,
                      **{k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in r.metrics.items()}}
        print(f"Gate {g} {r.title}: {r.status}", flush=True)
        if r.status in FAIL_STOPS:
            stopped = g
    rob = G.robustness_pass_only(s)
    rob.to_csv(OUT / "robustness_gate_a_pass_only.csv", index=False)

    fails = [g for g, r in results.items() if r["status"] == "FAIL"]
    routes = [g for g, r in results.items() if r["status"] == "ROUTE_CONDITIONAL"]
    decision = "FAIL" if fails else ("CONDITIONAL" if routes else "PASS_DISCOVERY_PENDING_GATE_O")
    summary = {
        "track": "F013", "phase": "discovery (C02 Train-1, contaminated)", "window": "[2024-03-01, 2025-03-01)",
        "validation_opened": False, "holdout_opened": False,
        "funnel": {k: int(len(v)) for k, v in f.items()},
        "scored_day_batch_clusters": int(s.day_batch_cluster_id.nunique()),
        "primary_net34_mean_bp": float(G.net(s, 34).mean()),
        "primary_gross_mean_bp": float(s.gross.mean()), "primary_funding_mean_bp": float(s.fund.fillna(0).mean()),
        "gates": results, "first_fail": stopped, "discovery_outcome": decision,
        "pass_only_robustness": rob.to_dict(orient="records"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in ("funnel", "primary_net34_mean_bp", "first_fail", "discovery_outcome")},
                     indent=1))
    return summary


if __name__ == "__main__":
    main()
