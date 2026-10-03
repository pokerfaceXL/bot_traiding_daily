# F006 · H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01 (T0-run)

## Outcome

Run the pre-registered Validation-4 check in
`spec/research/F006-hypothesis-bb-20-2-xsym-agree-sizing-val4.md`. Fill
`## Result`. Leave `## Decision` blank. Do not change `BB_20_2_EMA200`
profile status (keep CONDITIONAL). Do not FREEZE. Do not edit the journal,
`spec/build.md`, or `.pi/config.json`. Do not copy any `BB_20_25_EMA200`
number, and do not copy this name's Validation-1, Validation-2, or
Validation-3 means, onto this run as a target.

## Scope

- New sibling script `scripts/f006_bb_20_2_xsym_agree_sizing_val4.py`. Reuse
  the causal multiplier from `scripts/f006_bb_20_2_xsym_agree_sizing.py`
  (one-bar shift, leading stake 100, agreement on `BB_20_2_EMA200`). Do not
  retune `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`.
  `number_of_trials = 1`.
- Load the shared long protocol cache the way
  `scripts/f006_bb_20_2_xsym_agree_sizing_val3.py` loads it (warmup
  `2024-01-26T00:00:00Z` through the frozen file that ends at holdout
  `2026-09-01T00:00:00Z`). The `EXPECTED_CHECKSUMS` table in
  `scripts/f006_bb_20_25_xsym_agree_sizing.py` is the OHLCV identity of that
  shared long file, not that name's PnL. Verify the file against those
  hashes. Do **not** verify the long file against
  `output/f006_bb_20_2_abs_atr_gate/grid_freeze.json` (that table is the
  short Train-1 slice). Do **not** import +82.900262 or n=512.
- Pass the engine only bars with timestamp < 2026-03-01. One continuous
  backtest per series. `now=2026-03-01`. Score metrics only on entries with
  2025-12-01 <= entry_time < 2026-03-01 (F005 protocol §3.2 Validation 4:
  calendar 2025-12, 2026-01, 2026-02). Do not print holdout rows. Do not
  score holdout (entry >= 2026-03-01). There is no Validation-5.
- Sanity gate, **before** any Validation-4 scoring, on the Train-1 slice of
  the control arm. Exactly one gate:
  - mean `train1_net_pnl` within relative 0.25% of |+95.3217987|
    (allowance 0.23830449675). Reference is
    `output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json`
    field `control_replay.control_mean_train1_net_pnl`.
  - Train-1-entry n = 756 exact.
  - Do **not** use absolute 1e-6. Do **not** retarget the reference to the
    continuous observation 95.463371. Do **not** widen 0.25% if this run
    is outside it. If the gate fails, STOP, write the gate failure, and
    do not score Validation-4. Do not edit falsifiers (a)–(e).
  - Check the gate before any Validation-4 aggregation. Do not repeat the
    Val-3 script order, where per-series Validation-3 metrics were computed
    before the gate call (review note, nonblocking, on
    `scripts/f006_bb_20_2_xsym_agree_sizing_val3.py`). If the gate fails,
    do not publish a Validation-4 verdict.
  - Do **not** add a gate on Validation-3 entry means (+1.772572 /
    +8.007368) or on Validation-3 entry PnL. Those rows include
    `end_of_data` closes at the 2025-12-01 cut (`results.csv`
    `n_val3_end_of_data_exits` sums to 7); this longer run may realize
    them later. That move is not a falsifier. Do not gate on Validation-1
    or Validation-2 means either.
- Report control vs sized on the pre-declared falsifiers (a)–(e). (b) is
  non-worsening of the 3-month losing count (2025-12, 2026-01, 2026-02).
  Do not drop (c). Do not add a thin-margin, October-concentration, or
  6/10-series falsifier. Do not loosen (a)–(e).
- Artifacts under `output/f006_bb_20_2_xsym_agree_sizing_val4/` (results,
  cell_summary, manifest, run.log, per-series raw).
- If this worktree has no `data_cache` CSVs, point the run at the main
  checkout cache (`F006_DATA_CACHE=/home/limen/bot_traiding_daily/bot_traiding_daily/data_cache`).
  Do not copy validation ranges into git. Do not commit `data_cache`.

## Out of scope

- Holdout, formula changes, other names, profile status, Decision, journal,
  merge to main. No Validation-5.
- Abs-ATR retune, candle strength, breakout depth, HTF direction.
- Do not commit `.pi/config.json` or
  `spec/features/active/F006-catalog5-unfreeze-correction/`.

## Acceptance

- Train-1 control sanity gate uses the relative 0.25% band and n=756, is
  checked before Validation-4 aggregation, and either passes or stops
  without a Validation-4 verdict.
- If the gate passes, Validation-4 arms are reported against (a)–(e) with
  the verdict the numbers support.
- `## Result` filled, `## Decision` empty, profile status still CONDITIONAL.
- `python3 -m pytest -q` green. A focused test only if you add a new helper.
- Commit on the limen branch.

## Notes

Run honestly. A Validation-3 pass on this name does not license changing
the formula when Validation-4 is ugly, and the thin Validation-3 means,
the 6/10 series split, and the 2025-10 concentration do not license
writing FALSIFIED before these numbers exist. The other name's Val-1
failure and FREEZE do not license skipping the gate. Negative or
near-zero prior-window means are a caveat on the prior card, not a
target and not an extra falsifier.
