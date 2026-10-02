# F006 · H-BB-20-25-XSYM-AGREE-SIZING-01 (T0-run)

## Outcome

Implement and run the pre-registered cross-symbol agreement **position sizing** experiment on
`BB_20_25_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-25-xsym-agree-sizing.md`. Fill `## Result`; leave
`## Decision` blank for the coordinator. Do not change profile `status:` (keep CONDITIONAL).

## Scope

- Adapt the stake_series pattern from `scripts/f006_position_sizing_vol_inverse_experiment.py`
  and the agreement inputs from `scripts/f006_entry_cross_symbol_experiment.py` into a thin
  sibling `scripts/f006_bb_20_25_xsym_agree_sizing.py` for catalog name `BB_20_25_EMA200` only.
- Basket = frozen F006 5-symbol × 2-interval Train-1. NO_TRAIL, max_sl_pct=0.03, one-shot.
- Control arm: `stake_series=None` (uniform 100) — must match abs-ATR-gate / catalog5 control
  mean ≈ +82.90 before trusting sized arm.
- Sized arm: single pre-registered formula
  `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)` with `n_agree` = count of other 4 symbols whose
  persistent `BB_20_25_EMA200` signal equals this symbol's nonzero direction on the same bar.
- Hard checks: n_trades invariant per series; stake_cv > 0.05; report winner−loser mean mult gap.
- Artifacts under `output/f006_bb_20_25_xsym_agree_sizing/` (results, cell_summary, manifest,
  run.log, per-series raw).
- Fill the pre-registration note's `## Result`. Do **not** write `## Decision` or FREEZE.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR-based sizing, entry gates, validation/holdout, formula retuning.
- Merging to main.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report matched figure).
- Sized arm reported vs pre-declared falsifiers (a)–(e); `number_of_trials = 1`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (shared basket regime may make agreement weights correlated with
the same months that already lose). Run honestly; do not widen the formula after seeing results.
