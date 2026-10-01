"""
scripts/f006_vol_regime_wrap_experiment.py -- F006 H-VOL-REGIME-WRAP-01
(spec/research/F006-hypothesis-vol-regime-wrap.md). Calls the shared harness
(scripts/f006_family_runner.py's run_family()) exactly once. Does not reimplement
the basket/checksums/H1/H2 loop -- see the shared-harness note for why.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import f006_family_runner  # noqa: E402

CANDIDATE_NAMES = ["VOLW_HIGH_BRK_20", "VOLW_LOW_MR_20", "VOLW_HL_20"]

HYPOTHESIS_NOTE = (
    "H-VOL-REGIME-WRAP-01 (spec/research/F006-hypothesis-vol-regime-wrap.md): a "
    "causal realized-vol-percentile regime (LOW/MID/HIGH, hysteresis, W=100, edges "
    "25/75, margin 10) switches a frozen Donchian(20) breakout trigger between "
    "breakout mode (HIGH), inverted/mean-revert mode (LOW), and flat (MID). H1: mean "
    "train1_net_pnl > 0 for at least one of the 3 frozen names across its 10-series "
    "pool. H2 (conditional): at least one series of an H1-passing name clears the "
    "monthly promotion checklist."
)


def main() -> None:
    # vol_regime_wrap.py is already production-registered into
    # strategy.STRATEGY_CATALOG at strategy.py import time (same as donchian.py),
    # so catalog_entries=None here -- run_family must not be asked to re-register
    # an already-registered name (it raises on a name collision).
    manifest = f006_family_runner.run_family(
        family="vol_regime_wrap",
        candidate_names=CANDIDATE_NAMES,
        catalog_entries=None,
        hypothesis_note=HYPOTHESIS_NOTE,
        script_path="scripts/f006_vol_regime_wrap_experiment.py",
    )
    print(f"harness control ({manifest['control_name']}): "
          f"{manifest['harness_control']['rows_compared']} rows, "
          f"{manifest['harness_control']['n_mismatches']} mismatches")
    print(f"no-trail mechanism check: "
          f"{manifest['no_trail_mechanism_check']['runs_with_a_trailing_exit']}/"
          f"{manifest['no_trail_mechanism_check']['runs']} runs had a trailing exit")
    print(f"one-shot violations: {manifest['one_shot_violations']}")
    print(f"h1_table: {json.dumps(manifest['h1_table'], indent=2)}")
    print(f"h1_names_passing: {manifest['h1_names_passing']}")
    print(f"h1_falsified: {manifest['h1_falsified']}")
    print(f"h2_status: {manifest['h2_status']}")
    print(f"h2_names_with_a_passing_series: {manifest['h2_names_with_a_passing_series']}")
    print(f"elapsed: {manifest['elapsed_seconds']}s -> output/f006_vol_regime_wrap/summary/")


if __name__ == "__main__":
    main()
