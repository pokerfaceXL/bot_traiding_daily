# F006 · H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 breakout-depth entry gate on `BB_20_25_EMA200`
exactly per `spec/research/F006-hypothesis-bb-20-25-entry-breakout-depth.md`. Earn one
remaining entry-structure axis on this name's own trades (entry-vol, the xsym sizing
formula, and candle close-strength are already closed). Fill `## Result`; leave
`## Decision` blank for the coordinator. Do not change profile `status:` (keep
CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_25_entry_breakout_depth.py` adapting the
  control-first / grid harness from `scripts/f006_bb_20_25_entry_candle_confirm.py`.
  Same basket, NO_TRAIL, max_sl_pct=0.03, one-shot.
- Gate (ONE change): on the closed signal bar, keep only when band-normalized depth
  beyond `bb_20_2.5` is ≥ D:
  - width = upper - lower; width <= 0 ⇒ reject
  - long: `(close - upper) / width >= D`
  - short: `(lower - close) / width >= D`
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_25_EMA200`. Exits use the
  ungated persistent signal (identical to the candle gate). Do not use ATR. Do not use
  `(close-low)/(high-low)`.
- D grid (frozen before gated cells): `{0.02, 0.05, 0.10, 0.25, 0.50}`. Control = ungated.
- Big-winner definition: freeze **net≥29.9** before the run.
- Control must reproduce mean Train-1 net PnL +82.900262 (n=512 cohort, initial-SL
  share 0.580078125, big-winner PnL 968.020732, floor 7/12) before trusting gated cells.
- Artifacts under `output/f006_bb_20_25_entry_breakout_depth/` (results, cell_summary,
  grid_freeze, manifest, run.log, per-series raw / blotters as needed).
- Fill the pre-registration note's `## Result` with the control + 5-D table and pass/fail
  vs the pre-declared falsifiers (a)–(e). Do **not** write `## Decision` or change profile
  `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, candle-strength retune, sizing (incl. any retune of
  the closed xsym formula), HTF direction, validation/holdout, grid widening.
- The old width-expansion / squeeze gate. This is penetration depth, not band width
  versus its own mean.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched figure).
- All 5 D cells reported; `number_of_trials = 5`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (deep closes may be the same high-vol mass the abs-ATR
gate already failed to separate). Run honestly — if any D lowers the pooled floor while
keeping ≥50% big-winner PnL and ≥10 trades/series mean, flag it clearly; do not bury an
exception. Do not invent a second change.
