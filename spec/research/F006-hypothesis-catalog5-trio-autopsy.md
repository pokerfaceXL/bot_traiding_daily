# F006 — catalog5 EMA3_21_50_200 / EMA3_13_50_200 / BB_20_2_EMA200 signal/loss autopsy

date: 2026-09-30
base: main dba0b41 (EMA_50_200 / BB_20_25_EMA200 dual autopsy, catalog5 profiles updated)
producing job: 2026-09-30-f006-catalog5-trio-autopsy

## Observation

The dual autopsy (`spec/research/F006-hypothesis-catalog5-ema-bb-autopsy.md`,
`output/f006_catalog5_dual_autopsy/report.md`) found `EMA_50_200` and `BB_20_25_EMA200` share
the same fat-tail/`initial_sl`-dominated shape already confirmed and then falsified-on-gate
for `DONCHIAN_55_NO_TRAIL`. The remaining three CONDITIONAL catalog5 leads —
`EMA3_21_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200` — had no trade-level blotter and each
profile's "Allowed next experiments" section named the same re-run of the existing autopsy
harness as its only authorized next step. Given the dual result, this job tests whether the
remaining three also share the same shape, using the identical unmodified harness.

**Explicit scope note (per handoff):** `H-CATALOG5-ABS-ATR-ENTRY-GATE-01`
(pre-registered in the dual-autopsy note) is **not implemented or retested here**. That axis
is already falsified on `DONCHIAN_55_NO_TRAIL`
(`spec/research/F006-hypothesis-donchian-abs-atr-entry-gate.md`, 0/5 thresholds passed), and
both the dual autopsy and this trio autopsy show the same stop/runner ATR shape (`initial_sl`
entries at higher mean ATR% than `signal_reverse` entries, in every one of the five catalog5
names now autopsied). Retesting the mirror gate on any of the five names without a genuinely
new, non-correlated mechanism would re-run a result already predicted and already falsified —
this axis is **DNR (do not retest)** pending such a mechanism.

## Method

Re-run of the existing signal-autopsy mechanism (`scripts/f006_signal_autopsy.py`,
`trade_stats.win_loss_decomposition`), applied to three already-catalogued names, not a new
indicator search:

1. `scripts/f006_catalog5_trio_autopsy.py` calls `f006_family_runner.run_family(family=
   "catalog5_trio", candidate_names=["EMA3_21_50_200", "EMA3_13_50_200", "BB_20_2_EMA200"],
   catalog_entries=None, autopsy=True)`. Reproduces the frozen 5-symbol × 2-interval Train-1
   basket and the `DONCHIAN_55` harness control (matched exactly, 10/10 rows, 0 mismatches).
   No trailing exit fired under NO_TRAIL (0/40 runs). Output:
   `output/f006_signal_autopsy/catalog5_trio/`.
2. `scripts/f006_catalog5_trio_autopsy_report.py` pools the three names' `train1_entry=True`
   blotters across all 10 series each, computes win/loss decomposition, monthly net PnL, exit
   mix, entry ATR%/calm diagnostics, and a concentration metric (top-10-winners share of gross
   wins; number of top-ranked trades whose cumulative sum reaches the full pooled net PnL) —
   the same questions the dual autopsy and `output/f006_donchian_autopsy/report.md` answered.
   Also loads `output/f006_catalog5_dual_autopsy/summary.json` and
   `output/f006_donchian_autopsy/donchian55_autopsy_summary.json` to render one cross-name
   table against all five catalog5 leads plus the frozen reference. Output:
   `output/f006_catalog5_trio_autopsy/{report.md,summary.json,trades/*,monthly/*}`.

No new catalog entries, no parameter sweep, no holdout access (Train-1 slice only, same
frozen checksums as every prior F006 script).

## Result

The three h1_table sums reproduce the aggregate `train1_net_pnl` figures already recorded in
each profile's core-metrics table exactly (`EMA3_21_50_200`: +957.2508;
`EMA3_13_50_200`: +911.4830; `BB_20_2_EMA200`: +953.2180).

| name | n (Train-1 entries) | WR% | avg_winner | avg_loser | initial_sl share | loss months | top-10-winner share of gross wins | trades to reach full net PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA3_21_50_200 | 402 | 19.7% | +22.84 | -3.06 | 69% | 7/12 | 64.2% | 4 / 402 |
| EMA3_13_50_200 | 423 | 18.9% | +22.76 | -3.06 | 69% | 7/12 | 63.8% | 3 / 423 |
| BB_20_2_EMA200 | 756 | 24.9% | +12.50 | -2.67 | 47% | 7/12 | 50.7% | 4 / 756 |
| EMA_50_200 (ref) | 330 | 20.6% | +20.11 | -2.98 | 65% | 7/12 | 70.8% | 2 / 330 |
| BB_20_25_EMA200 (ref) | 512 | 25.0% | +14.30 | -2.92 | 58% | 7/12 | 52.9% | 4 / 512 |
| DONCHIAN_55 (ref) | 447 | 27.5% | +12.76 | -3.08 | 62% | 7/12 | — | — |

Full per-name answers (exit mix, ATR entry diagnostics, MFE-tail slice, quick_reverse):
`output/f006_catalog5_trio_autopsy/report.md`.

**Hypothesis check.** All three trio names share the same fat-tail structure already found in
`EMA_50_200`, `BB_20_25_EMA200`, and `DONCHIAN_55`: avg_winner is 5-9x |avg_loser|,
`initial_sl` exits are the dominant loss engine (47-69% of entries, 0% win rate), 7/12 Train-1
entry-months are net negative in every one of the five names now autopsied, and mean entry
ATR%(14) is higher on `initial_sl` exits than on `signal_reverse` exits for all five. The
two `EMA3` variants (`EMA3_21_50_200`, `EMA3_13_50_200`) are near-identical at the pooled
level (avg_winner 22.84 vs 22.76, WR 19.7% vs 18.9%, exit mix 69%/29% both), consistent with
the profiles' shared middle-EMA signal logic. `BB_20_2_EMA200` is the least concentrated name
of all five (50.7% top-10-winner share vs 52.9-70.8% elsewhere), confirming that profile's a
priori inference from its lower breakeven gap and higher trade count — but it is still
fat-tail dependent (avg winner ~4.7x |avg loser|, `initial_sl` still the dominant loss mode).
No name in the trio, or in the full set of five catalog5 leads autopsied to date, shows a
qualitatively different (non-fat-tail) edge mechanism at the trade level.

## Decision

All three profiles updated to reflect measured (not inferred) win/loss decomposition, exit
mix, and concentration fields; status stays **CONDITIONAL** for all three — the autopsy is
diagnostic, not a mechanism test, matching the discipline followed for `EMA_50_200` and
`BB_20_25_EMA200`. `H-CATALOG5-ABS-ATR-ENTRY-GATE-01` is **not implemented** (DNR, see scope
note above).

Because all five catalog5 NO_TRAIL leads now share the same fat-tail/`initial_sl`-dominated
shape at the trade level — the identical shape already found for the FREEZE'd
`DONCHIAN_55_NO_TRAIL` — a draft §13 family-insufficiency note covering the whole shared
NO_TRAIL catalog fat-tail class (not just one name) is written at
`spec/research/F006-catalog5-family-insufficiency-s13-draft.md`. It is **documentation only**:
no profile in this job moves to FREEZE, no gate is implemented, and the note itself states it
requires review/finalization before any status change relies on it.

## Not retested (DNR)

**H-CATALOG5-ABS-ATR-ENTRY-GATE-01** stays pre-registered but unimplemented for all five
catalog5 leads. Evidence against retesting it without a new axis: it is falsified on
`DONCHIAN_55_NO_TRAIL` (0/5 thresholds passed), and every one of the five catalog5 autopsies
(this one plus the dual autopsy) reproduces the same entry-ATR asymmetry the Donchian gate
test was built on (`initial_sl` entries at higher mean ATR% than `signal_reverse` entries).
Running the same gate mechanism on a sixth-through-tenth combination of (name × threshold)
would not test a new hypothesis — it would re-measure a trade-off already characterized and
already failing the same pass bar. Any future job proposing this axis again must first state
what is different about the specific name's ATR distribution that would change the outcome;
absent that, it remains DNR.
