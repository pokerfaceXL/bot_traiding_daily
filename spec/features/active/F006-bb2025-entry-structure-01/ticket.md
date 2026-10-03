# F006 · H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 (T0-run)

## Outcome

Implement and run the pre-registered §8 candle-confirmation entry gate on `BB_20_25_EMA200`
exactly per `spec/research/F006-hypothesis-bb-20-25-entry-candle-confirm.md`. Earn one
entry-structure axis on this name's own trades (entry-vol and the xsym sizing formula are
already closed). Fill `## Result`; leave `## Decision` blank for the coordinator. Do not
change profile `status:` (keep CONDITIONAL). Do not FREEZE.

## Scope

- Write a thin sibling `scripts/f006_bb_20_25_entry_candle_confirm.py` adapting the control-
  first / grid harness pattern from `scripts/f006_bb_20_25_abs_atr_gate.py` and
  `scripts/f006_family_runner.py`. Same basket, NO_TRAIL, max_sl_pct=0.03, one-shot.
- Gate (ONE change): on the closed signal bar, keep only when directional close-strength
  ≥ T:
  - long: `(close - low) / (high - low) >= T`
  - short: `(high - close) / (high - low) >= T`
  - `high == low` ⇒ reject
  Intersect with `entry_masks.one_shot_entry_mask` of `BB_20_25_EMA200`. Exits use the
  ungated persistent signal (identical to abs-ATR gate).
- T grid (frozen before gated cells): `{0.50, 0.60, 0.70, 0.80, 0.90}`. Control = ungated.
- Big-winner definition: freeze **net≥29.9** before the run.
- Control must reproduce mean Train-1 net PnL ≈ +82.90 (catalog5 / abs-ATR / xsym control)
  before trusting gated cells.
- Artifacts under `output/f006_bb_20_25_entry_candle_confirm/` (results, cell_summary,
  grid_freeze, manifest, run.log, per-series raw / blotters as needed).
- Fill the pre-registration note's `## Result` with the control + 5-T table and pass/fail
  vs the pre-declared falsifiers (a)–(e). Do **not** write `## Decision` or change profile
  `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, ATR gates, sizing (incl. any retune of the closed xsym formula),
  validation/holdout, grid widening, breakout-depth / HTF variants.
- Merging to main.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched figure).
- All 5 T cells reported; `number_of_trials = 5`.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (fat-tail runners may also have strong closes). Run honestly —
if any T lowers the pooled floor while keeping ≥50% big-winner PnL and ≥10 trades/series
mean, flag it clearly; do not bury an exception. Do not invent a second change.
