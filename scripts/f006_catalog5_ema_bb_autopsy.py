"""Signal/loss autopsy for EMA_50_200 and BB_20_25_EMA200 (F006 catalog5 leads).

Thin caller of f006_family_runner.run_family with autopsy=True -- reproduces the
DONCHIAN_55 harness control and writes per-entry blotters under
output/f006_signal_autopsy/catalog5_ema_bb/. Both candidate names are already
registered in strategy.STRATEGY_CATALOG (catalog_entries=None); no new indicators,
no parameter sweep, no holdout access.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import f006_family_runner as runner  # noqa: E402

FAMILY = "catalog5_ema_bb"
CANDIDATE_NAMES = ["EMA_50_200", "BB_20_25_EMA200"]
NOTE = "spec/research/F006-hypothesis-catalog5-ema-bb-autopsy.md"


def main() -> None:
    manifest = runner.run_family(
        family=FAMILY,
        candidate_names=CANDIDATE_NAMES,
        catalog_entries=None,
        hypothesis_note=NOTE,
        script_path=__file__,
        autopsy=True,
    )
    print(f"harness control ({manifest['control_name']}): "
          f"{manifest['harness_control']['rows_compared']} rows, "
          f"{manifest['harness_control']['n_mismatches']} mismatches")
    print(f"no-trail mechanism check: "
          f"{manifest['no_trail_mechanism_check']['runs_with_a_trailing_exit']}/"
          f"{manifest['no_trail_mechanism_check']['runs']} runs had a trailing exit")
    print(f"h1_table: {json.dumps(manifest['h1_table'], indent=2)}")
    print(f"signal_autopsy summary: output/f006_signal_autopsy/{FAMILY}/summary.json")
    print(f"elapsed: {manifest['elapsed_seconds']}s -> output/f006_signal_autopsy/{FAMILY}/")


if __name__ == "__main__":
    main()
