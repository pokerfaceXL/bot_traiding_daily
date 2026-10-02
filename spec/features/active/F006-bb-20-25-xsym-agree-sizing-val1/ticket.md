# F006 · H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01 (T0-run)

## Outcome

Run the pre-registered Validation-1 check in
`spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing-val1.md`. Fill `## Result`.
Leave `## Decision` blank. Do not change `BB_20_25_EMA200` profile status (keep CONDITIONAL).
Do not edit the journal, build.md, or `.pi/config.json`.

## Scope

- New sibling script `scripts/f006_bb_20_25_xsym_agree_sizing_val1.py`. Reuse the causal
  multiplier from `scripts/f006_bb_20_25_xsym_agree_sizing.py` (`compute_agreement_multiplier_series`,
  the one-bar shift). Do not retune `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`.
- Load the same protocol cache the Train-1 script loads (warmup 2024-01-26 through the
  frozen long file), then pass the engine only bars with timestamp < 2025-06-01. One
  continuous backtest per series. Score metrics only on entries with
  2025-03-01 <= entry_time < 2025-06-01.
- Before trusting Validation-1, the Train-1 slice of the control arm on that longer run
  must still show mean train1_net_pnl +82.90 and Train-1-entry n=512. If not, stop.
- Report control vs sized on the pre-declared falsifiers (a)-(e). number_of_trials = 1.
- Artifacts under `output/f006_bb_20_25_xsym_agree_sizing_val1/` (results, cell_summary,
  manifest, run.log, per-series raw).

## Out of scope

- Holdout, Validation-2/3/4, formula changes, other names, profile status, Decision, merge.
- Do not commit `data_cache`. CSV payloads live in the main checkout
  `/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache` if this worktree has only
  manifests; copy the csv files in, do not commit them.

## Acceptance

- Train-1 control sanity gate passes.
- Validation-1 arms reported against (a)-(e) with the verdict the numbers support.
- `## Result` filled, `## Decision` empty, `python3 -m pytest -q` green.
- Commit on the limen branch.

## Notes

Run honestly. A Train-1 pass does not license changing the formula when Validation-1 is ugly.
