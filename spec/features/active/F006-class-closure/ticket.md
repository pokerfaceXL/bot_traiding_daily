# F006 · catalog5 class closure on own evidence (H-CATALOG5-CLASS-CLOSURE-01)

## Outcome

Each of the four remaining CONDITIONAL catalog5 names (`BB_20_25_EMA200`, `EMA_50_200`,
`EMA3_13_50_200`, `BB_20_2_EMA200`) gets its own-trade answer to whether any decisive lever lowers
its monthly floor, so the coordinator can freeze (or keep) it on own evidence instead of by
analogy to `EMA3_21_50_200`. Follow the frozen spec in
`spec/research/F006-hypothesis-catalog5-class-closure.md` exactly — do not add levers, names, or
grid points, and do not touch validation/holdout.

## Scope

- Generalize `scripts/f006_breadth_regime_experiment.py` into a script that loops over the four
  names above and, per name, runs: baseline (no gate), long-only (direction==1 table filter), and
  breadth-regime veto B∈{0.4,0.6,0.8} using the identical causal breadth definition already in
  that script. Reuse the family harness (`f006_family_runner`) constants and `run_backtest` the
  same way — no new engine, no network.
- Per name × lever compute: pooled losing-month floor (by entry-month, of 12), net, mean/trade,
  n_trades, big-winner PnL (net≥29.9) + retention vs that name's own baseline, #symbols
  net-positive, per-symbol losing-month floor.
- For each name, apply the per-name falsification rule from the spec and emit a one-line verdict
  (exhausted → FREEZE candidate, or an exception → keep).
- Write results under `output/f006_class_closure/` and fill the pre-registration note's `## Result`.

## Out of scope

- The `decision` / status for any profile, and the §15 report — coordinator only.
- Any new lever, name, threshold, or data; re-tuning; editing other profiles or build.md.

## Acceptance

- Each name's baseline reproduces its own catalog5 figures (sanity), and `output/f006_class_closure/`
  holds a per-name × lever table plus a per-name verdict.
- The pre-registration `## Result` is filled; `python3 -m pytest -q` stays green.

## Notes

Expect confirmation of exhaustion (one shared regime factor), but run it honestly — if any name
shows a lever that lowers its own floor while keeping ≥50% of its winners for ≥2 carriers, flag it
as an exception, do not bury it.
