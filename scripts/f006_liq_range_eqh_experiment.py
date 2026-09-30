"""Run the pre-registered Train-1-only H-LIQ-RANGE-EQH-01 family."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import liq_range_eqh
from f006_family_runner import run_family


if __name__ == "__main__":
    manifest = run_family(
        family="liq_range_eqh",
        candidate_names=list(liq_range_eqh.CATALOG),
        catalog_entries=liq_range_eqh.catalog_entries(),
        hypothesis_note="spec/research/F006-hypothesis-liq-range-eqh.md",
        script_path="scripts/f006_liq_range_eqh_experiment.py",
    )
    print("harness control: {rows_compared} rows, {n_mismatches} mismatches".format(**manifest["harness_control"]))
    print("no-trail mechanism check: {runs_with_a_trailing_exit}/{runs} trailing exits".format(**manifest["no_trail_mechanism_check"]))
    print("H1: " + json.dumps(manifest["h1_table"], indent=2))
    print("H2: " + manifest["h2_status"])
    print("evidence: output/f006_liq_range_eqh/summary/")
