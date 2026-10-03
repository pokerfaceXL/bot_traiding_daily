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

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
