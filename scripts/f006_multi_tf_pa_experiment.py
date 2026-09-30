"""
scripts/f006_multi_tf_pa_experiment.py -- F006 multi-TF PA family (H-MULTI-TF-PA-01), Train-1
only. Tests spec/research/F006-hypothesis-multi-tf-pa.md via the shared harness
(scripts/f006_family_runner.py) -- this script does not reimplement the basket, checksums,
NO_TRAIL exit geometry, harness control, or H1/H2 checks; those are run_family's job.

    .venv_test/bin/python scripts/f006_multi_tf_pa_experiment.py

Reads multi_tf_pa.py/f006_family_runner.py and changes neither. Writes only
output/f006_multi_tf_pa/. Zero network connections.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import f006_family_runner  # noqa: E402
import multi_tf_pa  # noqa: E402

CANDIDATE_NAMES = [
    "MTFP_HTF_BRK20",
    "MTFP_HTF_BRK10",
    "MTFP_HTF_BRK5",
    "MTFP_HTF_BLOCK",
    "MTFP_HTF_PIN",
]

HYPOTHESIS_NOTE = "spec/research/F006-hypothesis-multi-tf-pa.md"


def main() -> dict:
    manifest = f006_family_runner.run_family(
        family="multi_tf_pa",
        candidate_names=CANDIDATE_NAMES,
        catalog_entries=multi_tf_pa.catalog_entries(),
        hypothesis_note=HYPOTHESIS_NOTE,
        script_path=__file__,
    )
    print(f"harness control ({manifest['control_name']}): "
          f"{manifest['harness_control']['rows_compared']} rows, "
          f"{manifest['harness_control']['n_mismatches']} mismatches")
    print(f"no-trail mechanism check: "
          f"{manifest['no_trail_mechanism_check']['runs_with_a_trailing_exit']}/"
          f"{manifest['no_trail_mechanism_check']['runs']} runs had a trailing exit")
    print(f"one-shot violations: {manifest['one_shot_violations']}")
    print("h1_table:")
    print(json.dumps(manifest["h1_table"], indent=2))
    print(f"h1_names_passing: {manifest['h1_names_passing']}")
    print(f"h1_falsified: {manifest['h1_falsified']}")
    print(f"h2_status: {manifest['h2_status']}")
    print(f"h2_names_with_a_passing_series: {manifest['h2_names_with_a_passing_series']}")
    print(f"elapsed: {manifest['elapsed_seconds']}s -> output/f006_multi_tf_pa/summary/")
    return manifest


if __name__ == "__main__":
    main()
