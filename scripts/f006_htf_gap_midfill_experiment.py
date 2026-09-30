"""Run the pre-registered F006 HTF FVG midfill family on frozen Train-1 only."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import htf_gap_midfill
from f006_family_runner import run_family


FAMILY = "htf_gap_midfill"
CANDIDATE_NAMES = ("HTF_FVG_MID_R1", "HTF_FVG_MID_R2", "HTF_FVG_MID_R3")
HYPOTHESIS_NOTE = "spec/research/F006-hypothesis-htf-gap-midfill.md"


def main() -> None:
    manifest = run_family(
        FAMILY,
        CANDIDATE_NAMES,
        catalog_entries=htf_gap_midfill.catalog_entries(),
        hypothesis_note=HYPOTHESIS_NOTE,
        script_path="scripts/f006_htf_gap_midfill_experiment.py",
    )
    candidate_rows = manifest["h1_table"]
    average_trades = {
        row["strategy"]: row["n_trades_total"] / row["n_series"]
        for row in candidate_rows
    }
    print("harness control: {} rows, {} mismatches".format(
        manifest["harness_control"]["rows_compared"], manifest["harness_control"]["n_mismatches"]
    ))
    print("H1 (Train-1 net PnL):", json.dumps(candidate_rows, indent=2))
    print("H2:", manifest["h2_status"])
    print("average trades/series:", json.dumps(average_trades, sort_keys=True))
    print("evidence: output/f006_htf_gap_midfill/summary/")


if __name__ == "__main__":
    main()
