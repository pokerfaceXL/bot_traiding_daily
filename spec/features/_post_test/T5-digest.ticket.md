# {{EXPERIMENT_ID}} · T5 cross-family digest refresh

## Outcome

The cross-family digest includes {{EXPERIMENT_ID}} so the portfolio-level view stays current.
Mechanical regeneration, no judgment.

## Scope

- Run `python3 scripts/f006_cross_family_digest.py` so it imports the new
  `output/{{OUTPUT_DIR}}/` artifacts.
- Verify the digest's control-sanity line still PASSES (DONCHIAN_55 runner self-check within
  tolerance); if it does not, stop and report rather than committing.
- Commit the regenerated `output/f006_cross_family_digest.{json,md}` only.

## Out of scope

- Interpreting the digest, ranking families, or drawing conclusions — coordinator only.
- Editing the profile, registry, build.md; re-running the experiment.

## Acceptance

- `output/f006_cross_family_digest.md` lists {{EXPERIMENT_ID}} (or its family) and the
  control-sanity line reads PASS.
- `python3 -m pytest -q tests/test_cross_family_digest.py` passes.

## Notes

If control sanity fails, that signals a harness/data regression upstream of this experiment —
do not mask it; report to the coordinator.
