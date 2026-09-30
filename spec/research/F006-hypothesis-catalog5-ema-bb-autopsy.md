# F006 — catalog5 EMA_50_200 / BB_20_25_EMA200 signal/loss autopsy

date: 2026-09-30
base: main d32eda8 (DONCHIAN_55_NO_TRAIL FREEZE + catalog5 CONDITIONAL profiles)
producing job: 2026-09-30-f006-catalog5-dual-autopsy

## Observation

`spec/research/strategy_profiles/EMA_50_200.md` and `BB_20_25_EMA200.md`, both CONDITIONAL
(aggregate-Train-1-positive, monthly-promotion-failing, no trade-level blotter), named the
same "allowed next experiment" already used to diagnose `DONCHIAN_55_NO_TRAIL`: build a
per-trade win/loss decomposition on the existing Train-1 trades and read exit-reason mix,
concentration, and entry diagnostics. The profiles picked these two names as opposite ends of
the catalog5 aggregate spectrum — `EMA_50_200` (fewest trades of the top 5, widest
breakeven-win-rate gap, a priori most Donchian-like fat-tail candidate) versus
`BB_20_25_EMA200` (best series-positive rate, smallest worst-series magnitude, a priori most
"regular" candidate) — to test whether that aggregate-shape ranking predicts trade-level
concentration, or whether it does not generalize.

## Method

Re-run of the existing signal-autopsy mechanism (`scripts/f006_signal_autopsy.py`,
`trade_stats.win_loss_decomposition`), applied to two already-catalogued names, not a new
indicator search:

1. `scripts/f006_catalog5_ema_bb_autopsy.py` calls `f006_family_runner.run_family(family=
   "catalog5_ema_bb", candidate_names=["EMA_50_200", "BB_20_25_EMA200"], catalog_entries=None,
   autopsy=True)`. Reproduces the frozen 5-symbol × 2-interval Train-1 basket and the
   `DONCHIAN_55` harness control (matched exactly, 10/10 rows, 0 mismatches). No trailing exit
   fired under NO_TRAIL (0/30 runs). Output:
   `output/f006_signal_autopsy/catalog5_ema_bb/`.
2. `scripts/f006_catalog5_dual_autopsy_report.py` pools the two names' `train1_entry=True`
   blotters across all 10 series each, computes win/loss decomposition, monthly net PnL, exit
   mix, entry ATR%/calm diagnostics, and a concentration metric (top-10-winners share of gross
   wins; number of top-ranked trades whose cumulative sum reaches the full pooled net PnL) —
   the same questions `output/f006_donchian_autopsy/report.md` answered for `DONCHIAN_55`.
   Output: `output/f006_catalog5_dual_autopsy/{report.md,summary.json,trades/*,monthly/*}`.

No new catalog entries, no parameter sweep, no holdout access (Train-1 slice only, same
frozen checksums as every prior F006 script).

## Result

Both names reproduce the aggregate `train1_net_pnl` sums already recorded in their CONDITIONAL
profiles exactly (EMA_50_200: +726.6931; BB_20_25_EMA200: +829.0026), confirming the pooled
blotter is built from the same trades the profiles' aggregate metrics were computed from.

| name | n (Train-1 entries) | WR% | avg_winner | avg_loser | initial_sl share | loss months | top-10-winner share of gross wins | trades to reach full net PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA_50_200 | 330 | 20.6% | +20.11 | -2.98 | 65% | 7/12 | 70.8% | 2 / 330 |
| BB_20_25_EMA200 | 512 | 25.0% | +14.30 | -2.92 | 58% | 7/12 | 52.9% | 4 / 512 |
| DONCHIAN_55 (reference) | 447 | 27.5% | +12.76 | -3.09 | 61.5% | 7/12 | — | — |

Full per-name answers (exit mix, ATR entry diagnostics, MFE-tail slice, quick_reverse):
`output/f006_catalog5_dual_autopsy/report.md`.

**Hypothesis check.** The profiles' a priori concentration ranking is confirmed at the trade
level: `EMA_50_200` is more top-heavy (70.8% of gross wins from its top 10 winners, full
pooled net PnL reached by only 2 trades) than `BB_20_25_EMA200` (52.9%, 4 trades). But the
magnitude of that difference is small relative to what both names share: for both, avg_winner
is 5-7x |avg_loser|, `initial_sl` is the dominant exit reason (58-65% of entries, 0% win rate),
7/12 Train-1 entry-months are net negative, and absolute entry ATR% is higher on `initial_sl`
exits than on `signal_reverse` exits (EMA_50_200: 1.75 vs 1.06; BB_20_25_EMA200: 1.70 vs 1.06)
— the same shape `output/f006_donchian_autopsy/report.md` found for `DONCHIAN_55_NO_TRAIL`.
Neither catalog5 name shows a qualitatively different (non-fat-tail) edge mechanism; "more
regular" (`BB_20_25_EMA200`) is a matter of degree, not kind.

## Decision

Both profiles updated to reflect measured (not inferred) win/loss decomposition, exit mix, and
concentration fields; status stays **CONDITIONAL** for both — the autopsy is diagnostic, not a
mechanism test, matching how `DONCHIAN_55_NO_TRAIL` itself stayed CONDITIONAL after its own
autopsy and only moved to FREEZE after a pre-registered entry-gate test was run and falsified
(`spec/research/F006-hypothesis-donchian-abs-atr-entry-gate.md`).

## Pre-registered next test (NOT implemented in this job)

**H-CATALOG5-ABS-ATR-ENTRY-GATE-01** (draft only — a future job must write the full
pre-registration, run it, and record its own decision before any implementation):

- **Change to test**: one causal entry gate per name — reject the signal on entry bars where
  ATR%(14) exceeds a pre-registered threshold T, else flat. No exit/sizing/symbol/interval
  changes, NO_TRAIL unchanged. Same mechanism already tested (and falsified) for
  `DONCHIAN_55_NO_TRAIL`, applied here to two different signal generators — not a re-run of the
  same falsified result, since the gate's effect depends on each name's own entry-ATR
  distribution, but the prior falsification is the strongest prior for the expected outcome and
  should be stated as such before running.
- **Candidate T grid**: {median Train-1 entry ATR% per name, 1.0%, 1.25%, 1.5%, 2.0%} — the
  same 5-point structure used for the Donchian gate, for comparability.
- **Pre-declared pass bar** (borrowed from the Donchian gate's four criteria): mean
  `train1_net_pnl` > ungated baseline AND `initial_sl` share down ≥10pp AND ≥50% of baseline
  big-winner (net_pnl≥10) PnL retained AND not thin (≥10 trades/series mean).
- **Expected outcome given this autopsy's evidence**: likely falsification by the same
  trade-off already measured for Donchian (thresholds that meaningfully cut `initial_sl` share
  also cut the fat-tail winners), but this is a prediction, not a substitute for running the
  grid — the two names' ATR distributions and stop/reverse separation are not identical to
  Donchian's, and `BB_20_25_EMA200`'s lower concentration leaves more room for a threshold to
  work without gutting the edge.
- **If falsified for both names**: both profiles move toward FREEZE, following the Donchian
  precedent, once no other single-axis mechanism remains untested for either name.
