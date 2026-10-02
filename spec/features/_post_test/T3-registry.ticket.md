# {{EXPERIMENT_ID}} · T3 decision-registry skeleton (§14)

## Outcome

A §14 decision-registry YAML block for {{EXPERIMENT_ID}}, fully populated from existing records
EXCEPT the three judgment fields, so the coordinator only has to add the verdict. No judgment,
no computation beyond copying.

## Scope

- Read the pre-registration note for {{EXPERIMENT_ID}}, `{{BASELINE}}`, and the T1/T2 outputs
  under `output/{{OUTPUT_DIR}}/posttest/`.
- Fill the §14 YAML: `experiment_id, date, base_strategy, hypothesis, motivation, change_tested,
  parameters, data_split, baseline, metrics_before, metrics_after, oos_result, cost_model,
  number_of_trials`.
- Leave `decision`, `reason`, `next_action` present but **blank** (the coordinator fills them).
- Append the block to the pre-registration note's `## Result` area (or a `## Registry` section).

## Out of scope

- Writing any value into `decision` / `reason` / `next_action`.
- Recomputing metrics (copy them from T1/T2); editing the profile, build.md, or digest.

## Acceptance

- The pre-registration note contains a §14 YAML block with every non-judgment field filled from
  T1/T2 and the pre-registration, and the three judgment fields left blank.
- `metrics_before` / `metrics_after` match T1 `metrics.json` exactly (no divergent recompute).

## Notes

`decision` must later be one of CONTINUE / REFINE / CONDITIONAL / FREEZE / FALSIFIED /
PROMOTE_TO_VALIDATION / REJECT — but that choice is the coordinator's, not this ticket's.
