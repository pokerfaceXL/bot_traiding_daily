# F006 · H-BB-20-2-XSYM-AGREE-SIZING-01 (T0-run)

## Outcome

Implement and run the pre-registered cross-symbol agreement sizing test on
`BB_20_2_EMA200` exactly per
`spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing.md`.
Earn the sizing axis on this name's own trades. Fill `## Result`; leave
`## Decision` blank. Do not change profile `status:` (keep CONDITIONAL).
Do not FREEZE. Do not reopen abs-ATR. Do not copy any `BB_20_25_EMA200`
sized result onto this run.

## Scope

- Write a thin sibling `scripts/f006_bb_20_2_xsym_agree_sizing.py` adapting
  `scripts/f006_bb_20_25_xsym_agree_sizing.py`.
- `NAME = "BB_20_2_EMA200"`. Agreement is counted on this name's persistent
  signal, not on `BB_20_25_EMA200`.
- One sized formula, frozen:
  `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)` with `n_agree ∈ {0,1,2,3,4}`.
  `number_of_trials = 1`. No grid. The 0.5 and 2.0 ends are the stake band
  `(2.0-0.5)/4 = 0.375`. They are not a threshold fitted on the other name's
  PnL, and they are not that name's pass/fail.
- Causal fill alignment, same as the sibling after its review fix: stake at
  fill bar i is agreement from the prior closed bar. First bar uses uniform
  stake 100. No fill reads its own bar's close.
- Control arm `stake_series=None` must reproduce all 10 `train1_net_pnl`
  rows and `n_trades` of `BB_20_2_EMA200` in
  `output/f006_notrail_monthly_catalog5/summary/results.csv` before the sized
  arm is scored. Expected mean **+95.3217987** (sum **+953.217987**). Do
  **not** use +82.900262.
- Data: only the frozen Train-1 caches
  `*_20240126T000000Z_20250301T000000Z.csv`. Checksums must match
  `output/f006_bb_20_2_abs_atr_gate/grid_freeze.json`. Do **not** reuse the
  sibling script's `EXPECTED_CHECKSUMS` (different slice). Do not download.
  Do not load `*_20260901*` or `*_20200325*`. If the worktree has no
  `data_cache`, run against the main checkout's cache without copying
  validation ranges and without writing artifacts outside this worktree's
  `output/f006_bb_20_2_xsym_agree_sizing/`.
- Confirm the control entry-month floor in this run. Do not assume 7/12 and
  do not import the other name's 5/12 sized floor.
- Big-winner note is informational (net≥29.9 on this run's ungated blotter).
  Do not import $968.02.
- Artifacts under `output/f006_bb_20_2_xsym_agree_sizing/` (control and sized
  summaries, a manifest with the frozen formula and the control-match diff,
  run.log, per-series raw / blotters as the sibling does).
- Fill `## Result` with control vs sized arm and pass/fail vs falsifiers
  (a)–(e). Do **not** write `## Decision` or change profile `status:`.
- `python3 -m pytest -q` stays green. Add a focused test only if you add a
  new helper; do not retune an existing test to this name's numbers.

## Out of scope

- Profile status / journal NOW / §15 / Decision — coordinator only.
- Abs-ATR retune, candle strength, breakout depth, HTF direction, long-only,
  validation/holdout, a second multiplier, any other catalog name.
- Merging to main. Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Control reproduces this name's 10 catalog5 Train-1 `train1_net_pnl` rows
  (mean +95.3217987). Report the matched figure and the max abs diff.
- Causal one-bar shift is in the script and stated in the Result.
- Both arms reported; formula frozen; `n_trades` invariant checked per series.
- `## Result` filled; `## Decision` still empty; profile status still
  CONDITIONAL.
- Commit on the limen branch.

## Notes

The other name's sizing formula passed Train-1 and failed validation. That
is not this result. Run the one formula honestly. If the sized arm beats
this name's control on the pre-declared checks, say so. Do not invent a
second change. Do not set FREEZE even if every falsifier fires.
