# F006 · H-BB-20-25-ABS-ATR-ENTRY-GATE-01 (T0-run)

## Outcome

Implement and run the pre-registered abs-ATR entry gate on `BB_20_25_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-25-abs-atr-entry-gate.md`. Earn the entry-vol axis on this
name's own trades (it was only DNR-by-transfer before). Fill `## Result`; leave `## Decision`
blank for the coordinator.

## Scope

- Adapt `scripts/f006_donchian_abs_atr_gate.py` (or a thin sibling
  `scripts/f006_bb_20_25_abs_atr_gate.py`) to run the same five-threshold Train-1 ablation for
  catalog name `BB_20_25_EMA200` via the family harness / `f006_family_runner`. Same ATR gate
  definition (`donchian.atr_pct_entry_gate` / SMA TR/close on closed signal bar), same control-
  first then freeze-median-then-grid discipline.
- Basket = frozen F006 5-symbol × 2-interval Train-1. NO_TRAIL, max_sl_pct=0.03, one-shot.
- T grid (frozen before gated cells): {median ATR% of this name's ungated Train-1 entries,
  1.0%, 1.25%, 1.5%, 2.0%}.
- Big-winner definition: freeze **net≥29.9** (class-closure consistency) before the run.
- Write artifacts under `output/f006_bb_20_25_abs_atr_gate/` (results, cell_summary, grid_freeze,
  manifest, run.log).
- Fill the pre-registration note's `## Result` with the control + 5-T table and pass/fail vs
  the pre-declared falsifiers. Do **not** write `## Decision` or change profile `status:`.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Other catalog5 names, other levers, validation/holdout, grid widening.
- Merging to main.

## Acceptance

- Control reproduces this name's ungated Train-1 baseline (report the matched figure).
- All 5 T cells reported; `number_of_trials = 5`; median frozen to disk before gated eval.
- `## Result` filled; `python3 -m pytest -q` stays green.
- Commit on the limen branch.

## Notes

Expect possible falsification (Donchian + EMA3_21 entry-vol both failed), but run honestly —
if any T lowers the pooled floor while keeping ≥50% big-winner PnL and ≥10 trades/series mean,
flag it clearly; do not bury an exception.
