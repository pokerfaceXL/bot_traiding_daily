# {{EXPERIMENT_ID}} · T4 profile row update

## Outcome

`{{PROFILE}}` reflects {{EXPERIMENT_ID}}'s measured result in its data sections, so the profile
stays the single trade-derived record — without the coordinator editing numbers by hand. Data
transcription only, no judgment.

## Scope

- Read T1/T2 outputs under `output/{{OUTPUT_DIR}}/posttest/` and `{{PROFILE}}`.
- Update the profile's data-bearing sections from those numbers: the **Core metrics** table, the
  **Stability** bullets (symbol/interval/period), and add one row to **Tested modifications**
  naming {{EXPERIMENT_ID}}, the one change tested, and the measured outcome (metrics only, e.g.
  "mean/trade +X, losing months A→B, big-winner PnL kept Y%").
- Keep the edit minimal and surgical; do not restructure the file.

## Out of scope

- The profile `status:` line and the "Status rationale" verdict — coordinator only.
- Any claim about whether the result passes/fails or what to do next.
- Editing the registry, build.md, digest; re-running anything.

## Acceptance

- `git diff {{PROFILE}}` touches only Core metrics, Stability, and one new Tested-modifications
  row; `status:` and Status rationale are unchanged.
- Every number added matches T1/T2 output exactly.

## Notes

If a metric contradicts an existing profile figure, flag it in the Tested-modifications row
rather than silently overwriting unrelated sections.
