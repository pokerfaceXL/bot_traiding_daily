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
Gate amendment (2026-10-03, coordinator, before Validation-1 scoring): absolute 1e-6 on the 10-series mean is relaxed to relative 0.25% of |reference mean| (n=512 stays exact; the round-to-2dp equality is dropped) because the continuous run omits the short-run end_of_data force-close inside the 2025-02 bucket on 240m only (60m diffs are 0); falsifiers (a)-(e) and the frozen formula are unchanged; this is not a new trial.

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

**FALSIFIED — condition (c): pooled Validation-1 mult gap = -0.026331 (<= 0).**
Conditions (a), (b), (d), and (e) did not fire. number_of_trials = 1.

Script `scripts/f006_bb_20_25_xsym_agree_sizing_val1.py` was run at commit `548e390`.
Artifacts are under `output/f006_bb_20_25_xsym_agree_sizing_val1/`: `summary/results.csv`,
`summary/cell_summary.json`, `summary/manifest.json`, `summary/run.log`, and `raw/`. The run
used checksum-verified protocol caches. Engine bars were 2024-01-26 <= ts < 2025-06-01, with
one continuous backtest per series and `now=2025-06-01`. Scored entries:
2025-03-01 <= entry_time < 2025-06-01.

Gate (control arm, Train-1 slice; amended tolerance above):

| check | reference | observed | tolerance | pass |
|---|---|---|---|---|
| mean train1_net_pnl (10 series) | 82.900262 | 83.048644 (diff 0.148382) | relative 0.0025 (0.207251) | yes |
| Train-1-entry n | 512 | 512 | exact | yes |

Validation-1 entries, 10 series:

| metric | control (stake 100) | sized | falsifier |
|---|---|---|---|
| mean val1-entry net PnL | -1.371447 | -0.400552 | (a) sized > control: not fired |
| val1-entry net total | -13.714473 | -4.005522 | |
| val1-entry n / total closed | 139 / 699 | 139 / 699 | (d) invariant holds on all series: not fired |
| pooled entry-month net 2025-03 / 04 / 05 | -64.04 / -54.47 / +104.80 | -59.74 / -91.39 / +147.13 | |
| pooled losing months (of 3) | 2 | 2 | (b) 2 <= 2: not fired |
| pooled mean mult winners / losers | | 1.006757 / 1.033088 | |
| pooled mult gap | | **-0.026331** | **(c) <= 0: FIRED** |
| stake_cv pooled / series min | | 0.471586 / 0.353424 | (e) all > 0.05: not fired |
| big winners at net >= 29.9 (info) | 2, sum 65.07 | 2, sum 105.68 | |

Per series, val1-entry net (control -> sized; series mult gap):

| series | n | control | sized | gap |
|---|---|---|---|---|
| SOL 240 | 4 | -6.60 | -7.01 | +0.125 |
| ETH 240 | 4 | +26.00 | +37.50 | +0.938 |
| BTC 240 | 5 | +6.47 | -4.24 | -0.563 |
| XRP 240 | 7 | +1.78 | +0.75 | +0.188 |
| DOGE 240 | 4 | +16.68 | +17.78 | 0.000 |
| SOL 60 | 26 | -30.84 | -43.75 | -0.079 |
| ETH 60 | 21 | +21.29 | +49.41 | +0.113 |
| BTC 60 | 20 | -13.23 | -26.65 | -0.313 |
| XRP 60 | 24 | -22.91 | -26.45 | -0.104 |
| DOGE 60 | 24 | -12.36 | -1.34 | +0.188 |

Each series has one Validation-1 `end_of_data` exit at the 2025-06-01 engine cut.

Reading: on Validation-1, the frozen weights put slightly more stake on losers than on
winners. The higher sized mean comes from a few large winners (the ETH series and the
2025-05 big winners). Agreement did not separate winners from losers as the mechanism
requires. Both arms are negative on mean, and both have 2/3 losing months.

## Decision

**FALSIFIED** (2026-10-03 morning, Europe/Warsaw). Coordinator confirms the Result.
The frozen causal formula does not generalize: falsifier (c) fired (pooled
Validation-1 mult gap **-0.026331**). (a), (b), (d), and (e) did not fire.
number_of_trials = 1. Close `H-BB-20-25-XSYM-AGREE-SIZING-01` on this name.
Stay **CONDITIONAL**. Do **not** FREEZE. Do not open holdout. Do not retune.
Do not jump to another catalog name.

The Train-1 control stop (mean 83.048644 vs 82.900262, n=512) was a methodology
artifact: the short Train-1 run force-closes at `end_of_data` inside the 2025-02
bucket on 240m (~+0.26 to +0.31 per series); the continuous run keeps those
positions open. All five 60m series matched exactly. That is the same frozen arm,
not a different experiment. Before any Validation-1 scoring, the absolute 1e-6
mean tolerance was relaxed to relative 0.25% of |reference mean| (allowance
0.207251; observed diff 0.148382; n=512 stayed exact). Falsifiers (a)-(e) were
not changed. Reviews: gate-stop **PASS** `d255f0e`
(`2026-10-03-f006-bb2025-xsym-agree-sizing-va-d8413e48`); rescore **PASS**
`89e936a` (`2026-10-03-f006-bb2025-xsym-agree-sizing-va-9a56d56a`). FF-merged onto main at `89e936a`.

Validation-1 entries (2025-03-01 <= entry < 2025-06-01): control mean **-1.371447**
(n=139, net -13.71, losing months 2/3); sized mean **-0.400552** (same n, net
-4.01, losing months 2/3); stake_cv 0.472. Sized mean is higher only because a
few large winners were scaled; losers carried the higher average multiplier.
The mechanism (agreement marks winners) did not hold on this window.

Next action (not spawned here): one not-yet-run §8 entry-structure hypothesis on
`BB_20_25_EMA200`, with a new written mechanism, pre-registered before any run.
Not a new family, not another catalog name, not Validation-2 of this formula.
