# Cross-family digest enrichment — review notes

The digest covers ten frozen-schema families using archived Train-1 artifacts only. No experiment was rerun, no holdout was opened, and no strategy was promoted. The task's `next-test-plan §(a)` pointer was not present under `spec/`; the supplied implementation task governs this slice.

## Artifact provenance

Each imported directory is byte-identical to its tree at the specified tip (verified with `git diff --exit-code <tip> HEAD -- <directory>` after import commit `41149a1`). Only these output trees were imported; neither experiment implementations nor SBPA tip `7f6f683` were imported.

| source tip | directory under output/ |
| --- | --- |
| 7341182 | f006_vol_regime_wrap |
| 54fd498 | f006_beta_gate |
| 80c013c | f006_liq_cascade_proxy |
| 785d5cf | f006_liq_range_eqh |
| be71095 | f006_htf_gap_midfill |
| e518682 | f006_btc_filter |
| 3fc50ec | f006_multi_tf_pa |
| 01ef194 | f006_session_regime |

`f006_runner_selfcheck` and `f006_sube_inv_fvg` remain identical to base `6f2c4db`. The latter's root summary is the frozen family summary already on main, not an aggregation of its separate exit-grid artifacts.

## Reading and regenerating

Run `python3 scripts/f006_cross_family_digest.py` from the repository root. This writes `output/f006_cross_family_digest.{json,md}`. The CLI fails if the runner self-check control is absent or fails sanity; custom `--glob` selections must include it.

- H1 values and within-family ranking use `results.csv`'s `train1_net_pnl`; historical manifest H1 values remain in JSON as `manifest_h1_table`. Incomplete candidate CSV data falls back explicitly to the manifest.
- H2 uses archived `promotion_pass` rows only for names passing Train-1 H1, with nonnegative series Train-1 PnL. It is a family-level status, not a claim that each name passed. Original H2 status and source are retained in JSON.
- Per-name statistics and thin-series flags prevent the control's trade count from hiding sparse candidates. Family aggregates include control rows and are labelled accordingly. These trade/WR/DD/exit statistics cover the archived simulation, including warm-up/boundary where present; no new Train-1-only exit histogram is inferred.
- Only runner_selfcheck's CSV currently contains the full five exit columns and profit factor / Calmar / USD drawdown. Other frozen CSVs contain only `exit_trailing_sl`; absence of the remaining exit columns does not mean zero exits. None currently contains phase-fit scores. The helper emits these means when supplied, with missing/nonfinite observations excluded and unavailable means represented by null.
- DONCHIAN_55 in runner_selfcheck: 10 CSV rows, mean Train-1 **+58.3870526**, delta from +58.39 **-0.0029474**. Stored harness comparison: 10 rows, zero mismatches. Sanity tolerance is $0.01. This is an archived-artifact check, not a fresh experiment.

## Checks and next action

`PYTHONPATH=.:scripts python3 -m pytest -q tests/test_cross_family_digest.py`: **9 passed**. Adversarial fixtures reverse manifest and diagnostic full-run PnL rankings to prove CSV Train-1 preference, exercise H1's strict-positive boundary and H2 gating, distinguish missing exit columns from zero counts, verify optional means and thin-series boundaries, and force control failures including CLI nonzero exit. The artifact integration test requires all ten named families and the exact observed control mean.

Digest generation reports **31 directories: 10 frozen, 20 legacy, 1 other; control PASS**. `git diff --check` is clean. The full-suite result will be recorded outside the worktree after the candidate commit, alongside copied reviewer artifacts at:

`/home/limen/bot_traiding_daily/bot_traiding_daily/.limen/jobs/2026-09-29-f006-digest-enrichment-c56d3d9b/artifacts/digest-enrichment/`

Next action: independent review of the limen branch; do not merge to production. The optional separate one-pager was not added; per-name metrics are in the digest itself. No further implementation slice is required by this task.
