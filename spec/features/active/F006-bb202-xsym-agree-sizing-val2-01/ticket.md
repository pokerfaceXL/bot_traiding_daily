# F006 · H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01 (T0-run)

## Outcome

Run the pre-registered Validation-2 check in
`spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing-val2.md`. Fill
`## Result`. Leave `## Decision` blank. Do not change `BB_20_2_EMA200`
profile status (keep CONDITIONAL). Do not FREEZE. Do not edit the journal,
`spec/build.md`, or `.pi/config.json`. Do not copy any `BB_20_25_EMA200`
number, and do not copy this name's Validation-1 means, onto this run as
a target.

## Scope

- New sibling script `scripts/f006_bb_20_2_xsym_agree_sizing_val2.py`. Reuse
  the causal multiplier from `scripts/f006_bb_20_2_xsym_agree_sizing.py`
  (one-bar shift, leading stake 100, agreement on `BB_20_2_EMA200`). Do not
  retune `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`.
  `number_of_trials = 1`.
- Load the shared long protocol cache the way
  `scripts/f006_bb_20_2_xsym_agree_sizing_val1.py` loads it (warmup
  `2024-01-26T00:00:00Z` through the frozen file that ends at holdout
  `2026-09-01T00:00:00Z`). The `EXPECTED_CHECKSUMS` table in
  `scripts/f006_bb_20_25_xsym_agree_sizing.py` is the OHLCV identity of that
  shared long file, not that name's PnL. Verify the file against those
  hashes. Do **not** verify the long file against
  `output/f006_bb_20_2_abs_atr_gate/grid_freeze.json` (that table is the
  short Train-1 slice). Do **not** import +82.900262 or n=512.
- Pass the engine only bars with timestamp < 2025-09-01. One continuous
  backtest per series. `now=2025-09-01`. Score metrics only on entries with
  2025-06-01 <= entry_time < 2025-09-01 (F005 protocol §3.2 Validation 2:
  calendar 2025-06, 2025-07, 2025-08). Do not print holdout rows. Do not
  score Validation-3 or Validation-4.
- Sanity gate, **before** any Validation-2 scoring, on the Train-1 slice of
  the control arm. Exactly one gate:
  - mean `train1_net_pnl` within relative 0.25% of |+95.3217987|
    (allowance 0.23830449675). Reference is
    `output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json`
    field `control_replay.control_mean_train1_net_pnl`.
  - Train-1-entry n = 756 exact.
  - Do **not** use absolute 1e-6. Do **not** retarget the reference to the
    Validation-1 continuous observation 95.463371. Do **not** widen 0.25%
    if this run is outside it. If the gate fails, STOP, write the gate
    failure, and do not score Validation-2. Do not edit falsifiers (a)–(e).
  - Do **not** add a gate on Validation-1 entry mean (−9.270577) or on
    Validation-1 entry PnL. Those rows include an `end_of_data` close at
    the 2025-06-01 cut; this longer run may realize them later. That move
    is not a falsifier.
- Report control vs sized on the pre-declared falsifiers (a)–(e). (b) is
  non-worsening of the 3-month losing count (2025-06, 2025-07, 2025-08).
  Do not drop (c). Do not add a new falsifier. Do not loosen (a)–(e).
- Artifacts under `output/f006_bb_20_2_xsym_agree_sizing_val2/` (results,
  cell_summary, manifest, run.log, per-series raw).
- If this worktree has no `data_cache` CSVs, point the run at the main
  checkout cache (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`).
  Do not copy validation ranges into git. Do not commit `data_cache`.

## Out of scope

- Holdout, Validation-3/4, formula changes, other names, profile status,
  Decision, journal, merge to main.
- Abs-ATR retune, candle strength, breakout depth, HTF direction.
- Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Train-1 control sanity gate uses the relative 0.25% band and n=756, and
  either passes or stops without a Validation-2 verdict.
- If the gate passes, Validation-2 arms are reported against (a)–(e) with
  the verdict the numbers support.
- `## Result` filled, `## Decision` empty, profile status still CONDITIONAL.
- `python3 -m pytest -q` green. A focused test only if you add a new helper.
- Commit on the limen branch.

## Notes

Run honestly. A Validation-1 pass on this name does not license changing
the formula when Validation-2 is ugly. The other name's Val-1 failure and
FREEZE do not license skipping the gate or writing FALSIFIED before these
numbers exist. Negative Validation-1 means are a caveat on the prior
card, not a target and not an extra falsifier.
