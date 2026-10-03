# F006 — H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01 (pre-registered)

> Pre-registered **before** running Validation-1. The Train-1 causal sizing formula
> `H-BB-20-25-XSYM-AGREE-SIZING-01` passed every pre-registered condition (tip `1c9ff7e`).
> §11 says that pass is not enough. This note freezes the same formula and asks whether
> it still beats the uniform-stake control on Validation-1. No retune. Holdout stays closed.

experiment_id: H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01
date: 2026-10-03
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
On Train-1 own trades the causal agreement stake (fill bar i uses n_agree from closed bar
i-1; mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0); leading stake 100) was NOT FALSIFIED.
Control mean +82.90, Train-1-entry n=512, net +709.85, pooled entry-month floor 7/12.
Sized mean +147.71, n=512, net +1344.18, floor 5/12, pooled mult gap +0.119, stake_cv 0.526.
Entry-vol on this name is already FALSIFIED (3788f11). Direction and breadth are already
closed on this name's class-closure cells. The sizing result has not been seen on any
later window.

Problem:
A Train-1 pass can be a sample accident. Promotion or FREEZE from Train-1 alone would
violate §11. The floor is still 5/12, so monthly regularity is not solved; the open
question is whether the same weights help on the next chronological window.

Mechanism:
Unchanged. The stake uses only agreement known when the entry was queued. If that
agreement truly marks basket-aligned runners, the same frozen weights should still raise
Validation-1 mean PnL versus uniform stake without making the short Validation-1 month
count worse and without a non-positive winner-loser multiplier gap.

Hypothesis:
On Validation-1 entries, the identical causal stake formula beats uniform stake=100 on
mean net PnL, does not increase the pooled losing-month count, and keeps
mean(mult|winner) > mean(mult|loser).

Change to test:
NONE. Same script rules as the Train-1 causal run. One continuous backtest per series
from warmup through Validation-1 end, then score only Validation-1 entries. Do not fit
anything on Validation-1. Do not change the multiplier formula or the one-bar shift.

Baseline:
Uniform stake=100 on the same continuous run. Sanity gate, before trusting Validation-1:
the Train-1 slice of that longer control run must still reproduce mean train1_net_pnl
+82.90 (tolerance 1e-6 on the 10-series mean) and Train-1-entry n=512. If it does not,
STOP. Do not interpret Validation-1.

Metrics (pre-declared), Validation-1 entries only
(2025-03-01 <= entry_time < 2025-06-01 UTC):
1. mean val1 net PnL across 10 series (primary)
2. pooled losing entry-month count out of the 3 Validation-1 months (2025-03, 2025-04, 2025-05)
3. n_trades invariant on Validation-1 entries per series, and on total closed trades
4. pooled mean(mult|winner) - mean(mult|loser) on Validation-1-entry closed trades
5. stake_cv on Validation-1 entries (pooled, and every series > 0.05)
6. big-winner contribution at net>=29.9 (informational)
7. number_of_trials = 1 (the formula is already frozen; this is not a new trial of a new rule)

Expected improvement:
Sized mean val1 net > control AND pooled losing-month count <= control's count
AND pooled mult gap > 0.

Falsification condition (any one => FALSIFIED):
(a) sized mean val1 net <= control; OR
(b) pooled Validation-1 losing-month count > control count; OR
(c) pooled mult gap <= 0; OR
(d) n_trades invariant broken; OR
(e) stake_cv <= 0.05.
Do not change the formula after seeing Validation-1.

Data split:
Score Validation-1 only. The backtest may include warmup and Train-1 so that positions
entering Validation-1 are causal, but bars at or after 2025-06-01 must not be loaded into
the engine. Holdout (entry >= 2026-03-01) is forbidden. Do not print holdout rows.

Budget:
One frozen formula. Control + sized arm. No grid.
```

decision_if_pass: stay CONDITIONAL; formula survives Validation-1; next window would be
  Validation-2 of the same formula, still not holdout, still not FREEZE
decision_if_fail: close this xsym-agree formula on this name (Train-1 pass did not
  generalize); stay CONDITIONAL; next open axis is a not-yet-run §8 entry structure on
  this name with a new written mechanism, not a jump to another catalog name

## Result

**STOP — Train-1 control sanity gate FAILED. Validation-1 was not scored or interpreted.**
Falsifiers (a)–(e) were not evaluated. number_of_trials = 1 (spent on this gate run).

Script `scripts/f006_bb_20_25_xsym_agree_sizing_val1.py`. Artifacts are under
`output/f006_bb_20_25_xsym_agree_sizing_val1/` (results.csv, cell_summary.json,
manifest.json, run.log, raw/). The run used checksum-verified protocol caches. Engine
bars were 2024-01-26 <= ts < 2025-06-01, with one continuous backtest per series and `now=2025-06-01`.

Gate (control arm, Train-1 slice of the continuous run):

| check | pre-registered | observed | pass |
|---|---|---|---|
| mean train1_net_pnl (10 series) | 82.900262 ± 1e-6 | 83.048644 (diff +0.148382) | NO |
| Train-1-entry n | 512 | 512 | yes |

Per series, the 60m series reproduce exactly (diff 0.000000). The five 240m series are
higher by +0.304 / +0.304 / +0.308 / +0.304 / +0.260 (SOL / ETH / BTC / XRP / DOGE).
Diagnosis: the Train-1 run ended its data at 2025-03-01, so every series force-closed one
open position at the last bar (`exit_reason=end_of_data`; 240m at 2025-02-28 20:00). That
close paid exit costs in the 2025-02 equity. In the continuous run the same positions are
still open, so 2025-02 equity carries mark-to-market without exit costs. The 60m force-close
bar (23:00) settles outside the Train-1 day buckets, which is why the 60m series match. The
gate metric is therefore not window-invariant. The mismatch is a property of the
pre-registered gate definition, not evidence of engine or data drift; trade count and
checksums match. Even so, the gate as written fails, and the card says STOP.

Implementation note: `compute_agreement_multiplier_series` in the Train-1 script read the
module-level `NOW=2025-03-01`. On a longer frame that leaves every post-Train-1 multiplier
NaN, so the stake falls back to 100. The function gained an optional `now=` kwarg (default
unchanged; Train-1 output re-run and identical apart from timing fields). An earlier bugged
pass of this script printed Validation-1 control numbers to the worker console before the
gate-first restructure. Its sized arm was identical to control because of this bug. Those
numbers are not recorded here and were not used.

Open question for the coordinator:
`spec/features/active/F006-bb-20-25-xsym-agree-sizing-val1/QUESTION-gate.md`.

## Decision

(empty — coordinator only after Result)
