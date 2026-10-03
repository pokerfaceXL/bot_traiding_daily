# F006 — H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01 (pre-registered)

> Pre-registered **before** running Validation-1. Train-1
> `H-BB-20-2-XSYM-AGREE-SIZING-01` is **NOT FALSIFIED / REFINE** on this
> name's own trades (tip `1774a8a`, review PASS
> `2026-10-03-f006-bb202-xsym-agree-sizing-rev-dff7bccd`). §3.10 and §11 say
> that pass is not enough. This note freezes the same formula and asks
> whether it still beats the uniform-stake control on this name's
> Validation-1 entries. No retune. Holdout stays closed. Do not FREEZE.
>
> `BB_20_25_EMA200` Val-1 of a same-shaped formula is **FALSIFIED (c)** at
> `89e936a`. That result is not this test. Do not copy its control mean
> (−1.371), its sized mean (−0.401), its mult gap (−0.026), its n=139, or
> its 2/3 month count onto this card as an expected result. Do not declare
> this run falsified because that one failed, and do not declare it passed
> because this name's Train-1 passed.

experiment_id: H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
On Train-1 own trades the causal agreement stake (fill bar i uses n_agree
from closed bar i-1; mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0); leading
stake 100; agreement counted on BB_20_2_EMA200's own persistent signal)
was NOT FALSIFIED. Control mean +95.3217987 (replay max abs diff 0.0),
Train-1-entry n=756, entry-net +834.347778, pooled entry-month floor 7/12.
Sized mean +146.632696, n=756, entry-net +1287.265355, floor 6/12, pooled
mult gap +0.086642, stake_cv 0.491784. Entry-vol on this name is already
FALSIFIED (a)+(c) at f7ac677. Exit, long-only, and breadth are already
closed on this name. The sizing result has not been seen on any later
window. The floor move was one month (2024-06) and ~110% of the entry-net
gain was 2024-11. Those are caveats, not new falsifiers and not a reason
to skip validation.

Problem:
A Train-1 pass can be a sample accident. Promotion or FREEZE from Train-1
alone would violate §11. §7 says a passed sizing arm is validated before
it is abandoned for a new entry axis. The open question is whether the
same frozen weights help on the next chronological window of this name.

Mechanism:
Unchanged. The stake uses only agreement known when the entry was queued.
If that agreement truly marks basket-aligned runners on this name, the
same frozen weights should still raise Validation-1 mean PnL versus
uniform stake, without raising the short Validation-1 losing-month count,
and with a positive winner-minus-loser multiplier gap.

Hypothesis:
On this name's Validation-1 entries, the identical causal stake formula
beats uniform stake=100 on mean net PnL, does not increase the pooled
losing-month count, and keeps mean(mult|winner) > mean(mult|loser).

Change to test:
NONE. Same rules as scripts/f006_bb_20_2_xsym_agree_sizing.py. One
continuous backtest per series from warmup through Validation-1 end, then
score only Validation-1 entries. Do not fit anything on Validation-1.
Do not change the multiplier formula or the one-bar shift. Agreement is
this name's signal, not BB_20_25_EMA200.

Baseline:
Uniform stake=100 on the same continuous run. Sanity gate, before trusting
Validation-1, on the Train-1 slice of that longer control run:
  - mean train1_net_pnl within relative 0.25% of |+95.3217987|
    (allowance 0.0025 * 95.3217987 = 0.2383045). Reference is this name's
    catalog replay in
    output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json
    (control_replay.control_mean_train1_net_pnl = 95.3217987), not the
    rounded 95.321799 display and not +82.900262.
  - Train-1-entry n = 756 exact
    (2024-03-01 <= entry_time < 2025-03-01).
Do NOT use an absolute 1e-6 gate on the 10-series mean. On the other
name, that absolute gate stopped a faithful continuous run because the
short Train-1 backtest force-closes at end_of_data inside the last
Train-1 bucket on 240m, while the continuous run keeps those positions
open. The relative 0.25% band is the pre-registered control check for
this run, chosen before scoring, for that reason only. It is not a new
trial. If the gate fails, STOP. Do not interpret Validation-1. Do not
widen 0.25%. Do not change falsifiers (a)-(e) to make a close gate pass.

Metrics (pre-declared), Validation-1 entries only
(2025-03-01 <= entry_time < 2025-06-01 UTC):
1. mean val1 net PnL across 10 series (primary)
2. pooled losing entry-month count out of the 3 Validation-1 months
   (2025-03, 2025-04, 2025-05)
3. n_trades invariant on Validation-1 entries per series, and on total
   closed trades of the continuous run
4. pooled mean(mult|winner) - mean(mult|loser) on Validation-1-entry
   closed trades
5. stake_cv on Validation-1 entries (pooled, and every series > 0.05)
6. big-winner contribution at net>=29.9 (informational; recomputed on
   this run, do not import +1251.654084 or the other name's $65.07)
7. month contribution of the entry-net difference (informational only)
8. number_of_trials = 1 (the formula is already frozen; this is not a
   new trial of a new rule)

Expected improvement:
Sized mean val1 net > this name's Validation-1 control AND pooled
losing-month count <= this name's Validation-1 control count AND pooled
mult gap > 0, with n_trades invariant and stake_cv > 0.05.

Falsification condition (any one => FALSIFIED):
(a) sized mean val1 net <= this name's Validation-1 control; OR
(b) pooled Validation-1 losing-month count > this name's control count; OR
(c) pooled mult gap <= 0; OR
(d) n_trades invariant broken; OR
(e) stake_cv <= 0.05.
These are the same five conditions used on a Validation-1 sizing check.
They are not loosened: no negative gap allowance, no extra losing month
allowed, no lower stake_cv floor, no dropped condition. (b) is
non-worsening on a 3-month window, not a silent drop of the gap test.
Do not add a post-hoc November-concentration falsifier inside this run.
Do not change the formula after seeing Validation-1.
Do not declare this falsified because BB_20_25 Val-1 failed.

Data split:
Score Validation-1 only. The backtest may include warmup and Train-1 so
that positions entering Validation-1 are causal, but bars at or after
2025-06-01 must not be loaded into the engine. Holdout (entry >=
2026-03-01) is forbidden. Do not print holdout rows. Do not open
Validation-2 in this run.

Budget:
One frozen formula. Control + sized arm. No grid. No second mechanism.
```

decision_if_pass: stay CONDITIONAL; this formula survives Validation-1 on
  BB_20_2_EMA200; next window would be Validation-2 of the same formula,
  still not holdout, still not FREEZE; other §8 entry structure stays open
  but is not next until that validation is decided
decision_if_fail: close this xsym-agree formula on BB_20_2_EMA200 (the
  Train-1 pass did not generalize). Stay CONDITIONAL. Do not FREEZE. Do not
  retune 0.5 / 0.375 / 2.0. Next open axis is one not-yet-run §8 entry
  structure on this name, with a new written mechanism. Not a jump to
  EMA_50_200 or EMA3_13_50_200. Not evidence about those names. Not a
  Val-2 of this formula.

## Result

**NOT FALSIFIED — none of (a)–(e) fired.** number_of_trials = 1.

Script `scripts/f006_bb_20_2_xsym_agree_sizing_val1.py` was run at commit `321b053`
with `F006_DATA_CACHE` pointing at the main-checkout `data_cache`. Artifacts are under
`output/f006_bb_20_2_xsym_agree_sizing_val1/`: `summary/results.csv`,
`summary/cell_summary.json`, `summary/manifest.json`, `summary/run.log`, and `raw/`.
The shared long protocol caches (2024-01-26 .. 2026-09-01) were verified against
`EXPECTED_CHECKSUMS` in `scripts/f006_bb_20_25_xsym_agree_sizing.py` (OHLCV identity).
Engine bars were 2024-01-26 <= ts < 2025-06-01, with one continuous backtest per series
and `now=2025-06-01`. Scored entries: 2025-03-01 <= entry_time < 2025-06-01. No holdout
row was loaded into the engine or printed.

Gate (control arm, Train-1 slice; checked before any Validation-1 scoring):

| check | reference | observed | tolerance | pass |
|---|---|---|---|---|
| mean train1_net_pnl (10 series) | 95.3217987 | 95.463371 (diff 0.141572) | relative 0.0025 (0.2383045) | yes |
| Train-1-entry n | 756 | 756 | exact | yes |

The gate difference is entirely 240m (+0.260 to +0.304 per series, the short Train-1 run's
`end_of_data` close in the last Train-1 bucket); all five 60m series match exactly, and
Train-1-entry n matches per series.

Validation-1 entries, 10 series:

| metric | control (stake 100) | sized | falsifier |
|---|---|---|---|
| mean val1-entry net PnL | -9.270577 | -4.002329 | (a) sized > control: not fired |
| val1-entry net total | -92.705774 | -40.023292 | |
| val1-entry n / total closed | 211 / 1031 | 211 / 1031 | (d) invariant holds on all series: not fired |
| pooled entry-month net 2025-03 / 04 / 05 | -70.78 / -84.82 / +62.89 | -94.91 / -98.48 / +153.37 | |
| pooled losing months (of 3) | 2 | 2 | (b) 2 <= 2: not fired |
| pooled mean mult winners / losers | | 1.161765 / 1.135156 | |
| pooled mult gap | | **+0.026608** | (c) > 0: not fired |
| stake_cv pooled / series min | | 0.481509 / 0.375467 | (e) all > 0.05: not fired |
| big winners at net >= 29.9 (info) | 1, sum 32.61 | 4, sum 187.11 (65.21 on control's key) | |

Entry-net difference by month (sized − control, informational): 2025-03 −24.14,
2025-04 −13.67, 2025-05 +90.49.

Per series, val1-entry net (control -> sized; series mult gap):

| series | n | control | sized | gap |
|---|---|---|---|---|
| SOL 240 | 5 | +1.13 | +8.30 | +0.500 |
| ETH 240 | 6 | +19.36 | +53.67 | +1.125 |
| BTC 240 | 8 | -2.29 | -15.95 | -0.696 |
| XRP 240 | 11 | -2.37 | +1.65 | +0.172 |
| DOGE 240 | 10 | -3.26 | +7.57 | +0.281 |
| SOL 60 | 32 | -15.51 | -30.84 | -0.149 |
| ETH 60 | 35 | -18.62 | +19.52 | +0.349 |
| BTC 60 | 30 | -19.74 | -25.77 | -0.263 |
| XRP 60 | 34 | -28.08 | -48.76 | -0.375 |
| DOGE 60 | 40 | -23.33 | -9.41 | +0.211 |

Each series has one Validation-1 `end_of_data` exit at the 2025-06-01 engine cut.

Reading: by the pre-declared rule the frozen weights survive Validation-1 on this name.
Caveats (not falsifiers, not grounds to change the verdict): both arms are negative on
mean; the pooled gap is small (+0.027) and negative on 4/10 series; sized lost more than
control in 2025-03 and 2025-04, and the whole entry-net gain is 2025-05 (+90.49 on a
+52.68 total), largely from scaled big winners (ETH 240, ETH 60).

## Decision

**CONDITIONAL** (2026-10-03 ~12:35 Europe/Warsaw). Coordinator confirms the Result:
**NOT FALSIFIED** on `BB_20_2_EMA200` Validation-1 entries. `decision_if_pass`
is stay CONDITIONAL and continue to Validation-2 of the same frozen formula.
Claude review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-val-ab5c3864` on
tip `7e18786` (FF-merged onto `origin/main` from `738b9ff`). This is not a
FREEZE and not a holdout.

Pre-declared checks, matched to
`output/f006_bb_20_2_xsym_agree_sizing_val1/summary/cell_summary.json`
(number_of_trials = 1, formula frozen
`mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`, fill bar i uses closed
bar i−1). The Train-1 gate was checked before Validation-1 scoring:

- control mean train1_net_pnl **95.463371** vs reference **95.3217987**
  (abs diff 0.141572 ≤ allowance 0.23830449675 = 0.25% of |reference|).
  Train-1-entry n **756** exact. Gate PASS.
- sized mean val1-entry net **-4.002329** > control **-9.270577** — (a) not fired
- pooled losing months **2 ≤ 2** — (b) not fired
- pooled mult gap **+0.026608** (1.161765 vs 1.135156) — (c) not fired
- val1-entry n / total closed **211 / 1031**, invariant on all series — (d) not fired
- stake_cv **0.481509** (series min 0.375467) — (e) not fired

Caveats, not extra falsifiers and not a reason to skip the next window or
to FREEZE: both means are negative; sized lost more than control in
2025-03 (−24.137407) and 2025-04 (−13.665664); the entry-net gain is
concentrated in 2025-05 (+90.485553 against a +52.682482 total); the gap
is small and negative on 4/10 series. §11 is not finished (Validation-2,
Validation-3, Validation-4, and holdout are still ahead; holdout stays
closed). §3.10 and §7 say do not abandon this passed arm for a new entry
axis before the next named validation. Status stays **CONDITIONAL**. Do
not retune 0.5 / 0.375 / 2.0. Do not copy `BB_20_25_EMA200` (that name is
FREEZE on its own loop). Next =
`H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01` (same frozen formula, this name's
Validation-2 entries only: 2025-06-01 ≤ entry < 2025-09-01, F005 protocol
§3.2).
