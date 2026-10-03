# F006 · H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 (T0-run)

## Outcome

Implement and run the pre-registered abs-ATR entry gate on `EMA3_13_50_200`
exactly per `spec/research/F006-hypothesis-ema3-13-50-200-abs-atr-entry-gate.md`.
Earn the entry-vol axis on this name's own trades (it was only
DNR-by-transfer, and that closure was withdrawn). Fill `## Result`; leave
`## Decision` blank for the coordinator. Do not change profile `status:`
(keep CONDITIONAL). Do not FREEZE. Do not copy any `EMA_50_200`,
`BB_20_2_EMA200`, or `BB_20_25_EMA200` result, median, or baseline onto
this run.

## Scope

- Write a thin sibling `scripts/f006_ema3_13_50_200_abs_atr_gate.py` adapting
  `scripts/f006_ema_50_200_abs_atr_gate.py`. Same ATR definition
  (`donchian.atr_pct_entry_gate`, SMA true-range / close on the closed signal
  bar). Same control-first, freeze-median, then grid discipline. The signal
  is catalog `EMA3_13_50_200` = `sig_ema3_cross(df, 13, 50, 200)`, not
  `sig_ema_cross(50, 200)` and not a Bollinger band.
- Point the control at this name:
  - `CONTROL_NAME = "EMA3_13_50_200"`
  - reference = `output/f006_notrail_monthly_catalog5/summary/results.csv`
  - expected mean train1_net_pnl = **91.1483016** (sum 911.483016, 10 rows,
    exact match on `train1_net_pnl` before any gated cell)
  - do **not** use `EXPECTED_MEAN = 72.6693115` and do **not** use
    `EXPECTED_MEAN = 95.3217987` and do **not** use `EXPECTED_MEAN = 82.900262`
- Basket = frozen F006 5-symbol × 2-interval. NO_TRAIL, max_sl_pct=0.03,
  one-shot. Intersect the gate with this name's one-shot entry mask the same
  way the sibling intersects its own name. No second filter.
- T grid frozen before gated cells: {median ATR% of **this name's** ungated
  Train-1 entries, 1.0%, 1.25%, 1.5%, 2.0%}. `number_of_trials = 5`.
  Do not reuse 1.22268881066447, 1.176636%, or 1.165%. Do not hardcode the
  autopsy median 1.3050960028982004; freeze the control blotter median to disk.
- Big-winner definition: freeze **net≥29.9** on this name's ungated blotter
  before gated cells. Autopsy observation is 9 trades summing to
  +1131.95615373334168. Do not import another name's big-winner set. If the
  frozen set disagrees with that observation, stop and report.
- Expected Train-1 entry cohort, from
  `output/f006_catalog5_trio_autopsy/trades/EMA3_13_50_200_train1_trades.csv`:
  n=423, entry net +771.2836172145888236, initial_sl 292/423. If the harness
  control disagrees, stop and report. Do not retune.
- Report the control entry-month losing-month floor from the harness. The
  autopsy observation is 7/12. Do not assume it, and do not assume a
  per-series calendar floor (4–9) is the pooled floor.
- Use only the frozen Train-1 caches already in `data_cache/`
  (`*_20240126T000000Z_20250301T000000Z.csv`). Do not download. Do not load
  `*_20260901*` or `*_20200325*`. If the worktree has no `data_cache`, run
  against the main checkout's cache without copying validation ranges and
  without writing artifacts outside this worktree's
  `output/f006_ema3_13_50_200_abs_atr_gate/`.
- Artifacts under `output/f006_ema3_13_50_200_abs_atr_gate/` (results, cell_summary,
  grid_freeze, manifest, run.log, per-series raw / blotters as the sibling
  script does).
- Fill the pre-registration note's `## Result` with the control + 5-T table
  and pass/fail vs falsifiers (a)–(e). Do **not** write `## Decision` or
  change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new gate helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- `EMA_50_200` (FREEZE), `BB_20_2_EMA200` (FREEZE), and
  `BB_20_25_EMA200` (FREEZE). Sizing, candle strength, breakout depth, HTF
  direction, liquidity, long-only, validation/holdout, grid widening.
- Funding-carry, spread-capture, catalog mean-reversion.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's 10 catalog5 Train-1 `train1_net_pnl` rows
  (mean +91.1483016). Report the matched figure.
- Entry cohort matches n=423 / net +771.2836172145888236 / initial_sl 292/423,
  or the run stops with a report instead of a retune.
- All 5 T cells reported; median frozen to disk before gated eval.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

Other names' abs-ATR gates failed. That is not this result. `EMA_50_200`
FREEZE is not this name's FREEZE. Run the five cells honestly. If any T
beats this name's control on the pre-declared checks, say so. Do not invent
a second change. Do not set FREEZE even if every cell fails.
