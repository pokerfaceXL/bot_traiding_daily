# F006 · H-BB-20-2-ABS-ATR-ENTRY-GATE-01 (T0-run)

## Outcome

Implement and run the pre-registered abs-ATR entry gate on `BB_20_2_EMA200`
exactly per `spec/research/F006-hypothesis-bb-20-2-abs-atr-entry-gate.md`.
Earn the entry-vol axis on this name's own trades (it was only DNR-by-transfer).
Fill `## Result`; leave `## Decision` blank for the coordinator. Do not change
profile `status:` (keep CONDITIONAL). Do not FREEZE. Do not copy any
`BB_20_25_EMA200` result, median, or baseline onto this run.

## Scope

- Write a thin sibling `scripts/f006_bb_20_2_abs_atr_gate.py` adapting
  `scripts/f006_bb_20_25_abs_atr_gate.py`. Same ATR definition
  (`donchian.atr_pct_entry_gate`, SMA true-range / close on the closed signal
  bar). Same control-first, freeze-median, then grid discipline.
- Point the control at this name:
  - `CONTROL_NAME = "BB_20_2_EMA200"`
  - reference = `output/f006_notrail_monthly_catalog5/summary/results.csv`
  - expected mean train1_net_pnl = **95.3217987** (sum 953.217987, 10 rows,
    exact match on `train1_net_pnl` before any gated cell)
  - do **not** use `EXPECTED_MEAN = 82.900262` and do **not** use
    `output/f006_signal_autopsy/catalog5_ema_bb/summary/results.csv` (that file
    has no `BB_20_2_EMA200` rows)
- Basket = frozen F006 5-symbol × 2-interval. NO_TRAIL, max_sl_pct=0.03,
  one-shot. Intersect the gate with this name's one-shot entry mask.
- T grid frozen before gated cells: {median ATR% of **this name's** ungated
  Train-1 entries, 1.0%, 1.25%, 1.5%, 2.0%}. `number_of_trials = 5`.
  Do not reuse 1.165%.
- Big-winner definition: freeze **net≥29.9** on this name's ungated blotter
  before gated cells. Do not import the other name's big-winner set.
- Report the control entry-month losing-month floor from the harness. Do not
  assume 7/12 and do not assume the calendar 8/12 observation is that floor.
- Use only the frozen Train-1 caches already in `data_cache/`
  (`*_20240126T000000Z_20250301T000000Z.csv`). Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache without copying validation ranges and
  without writing artifacts outside this worktree's
  `output/f006_bb_20_2_abs_atr_gate/`.
- Artifacts under `output/f006_bb_20_2_abs_atr_gate/` (results, cell_summary,
  grid_freeze, manifest, run.log, per-series raw / blotters as the sibling
  script does).
- Fill the pre-registration note's `## Result` with the control + 5-T table
  and pass/fail vs falsifiers (a)–(e). Do **not** write `## Decision` or
  change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new gate helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- `BB_20_25_EMA200` and the other catalog5 names. Sizing, candle strength,
  breakout depth, HTF direction, long-only, validation/holdout, grid widening.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's 10 catalog5 Train-1 `train1_net_pnl` rows
  (mean +95.3217987). Report the matched figure.
- All 5 T cells reported; median frozen to disk before gated eval.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Other names' abs-ATR gates failed. That is not this result. Run the five
cells honestly. If any T beats this name's control on the pre-declared
checks, say so. Do not invent a second change. Do not set FREEZE even if
every cell fails.
