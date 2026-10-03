# F006 — H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01 (pre-registered)

> Pre-registered **before** running Validation-4. Validation-3
> `H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01` is **NOT FALSIFIED** on this
> name's own trades (tip `cf00663`, Claude review PASS
> `2026-10-03-f006-bb202-xsym-agree-sizing-val-607c9de9`, FF-merged from
> `7144b8f`). `decision_if_pass` on that card is stay CONDITIONAL and
> continue to Validation-4 of the same formula (F005 protocol §3.2:
> 2025-12-01 ≤ entry < 2026-03-01). Coordinator protocol §3.10 and §11
> say one more window is still required. This note freezes the same
> formula and asks whether it still beats the uniform-stake control on
> this name's Validation-4 entries. No retune. Holdout stays closed.
> Do not FREEZE. Do not open holdout in this run. The thin Validation-3
> means, the 6/10 series split, and the 2025-10 concentration are
> caveats on the prior card, not a new stop rule and not a reason to
> skip this window.
>
> Dates below are the frozen F005 protocol §3.2 row **Validation 4**,
> not a new split: 2025-12-01T00:00:00Z ≤ entry < 2026-03-01T00:00:00Z
> (calendar 2025-12, 2026-01, 2026-02). Do not invent another window.
> There is no Validation-5.
>
> `BB_20_25_EMA200` is **FREEZE** on its own loop. Its Val-1 of a
> same-shaped formula is **FALSIFIED (c)** at `89e936a`. That result is
> not this test. Do not copy its control mean, its sized mean, its mult
> gap, its n, or its month count onto this card as an expected result.
> Do not copy this name's Validation-3 means (+1.772572 / +8.007368),
> its Validation-2 means (+2.331879 / +2.551244), or its Validation-1
> means (−9.270577 / −4.002329) as an expected Validation-4 result
> either. Do not declare this run falsified because another window or
> another name failed, and do not declare it passed because Train-1,
> Validation-1, Validation-2, or Validation-3 passed.

experiment_id: H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
On this name's own trades the causal agreement stake (fill bar i uses
n_agree from closed bar i-1; mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0);
leading stake 100; agreement counted on BB_20_2_EMA200's own persistent
signal) was NOT FALSIFIED on Train-1 (tip 1774a8a: control mean
+95.3217987, sized +146.632696, floor 7/12 → 6/12, mult gap +0.086642,
n=756), NOT FALSIFIED on Validation-1 (tip 7e18786), NOT FALSIFIED on
Validation-2 (tip 7798bbb), and NOT FALSIFIED on Validation-3 (tip
cf00663). Validation-3 artifacts in
output/f006_bb_20_2_xsym_agree_sizing_val3/summary/cell_summary.json:
gate observed Train-1 mean 95.463371 vs reference 95.3217987 (diff
0.141572, allowance 0.23830449675), Train-1-entry n=756; control mean
val3-entry net +1.772572; sized mean +8.007368; losing months 2 and 2;
pooled mult gap +0.179831; val3-entry n 181; total closed 1407;
stake_cv 0.455172 (series min 0.301511). Means are thin. 6/10 series
improve. The entry-net gain is concentrated in 2025-10 (+57.076733),
and 2025-09 is worse under sizing (−11.868494). results.csv
n_val3_end_of_data_exits sums to 7 at the 2025-12-01 cut. Those are
caveats, not new falsifiers. Entry-vol on this name is already
FALSIFIED (a)+(c) at f7ac677. Exit, long-only, and breadth are already
closed on this name. The sizing result has not been seen on Validation-4.

Problem:
A pass on Train-1 plus three 3-month windows can still be a sample
accident, and Validation-3's gain is thin on the mean, only 6/10 series,
and one-month concentrated. FREEZE or holdout from Validation-3 alone
would violate §11. The Val-3 card's decision_if_pass does not set a
margin floor and does not stop. §7 says a passed sizing arm is validated
on the next named window before it is abandoned for a new entry axis.
The open question is whether the same frozen weights help on
Validation-4 of this name.

Mechanism:
Unchanged. The stake uses only agreement known when the entry was queued.
If that agreement truly marks basket-aligned runners on this name, the
same frozen weights should still raise Validation-4 mean PnL versus
uniform stake, without raising the short Validation-4 losing-month count,
and with a positive winner-minus-loser multiplier gap.

Hypothesis:
On this name's Validation-4 entries, the identical causal stake formula
beats uniform stake=100 on mean net PnL, does not increase the pooled
losing-month count, and keeps mean(mult|winner) > mean(mult|loser).

Change to test:
NONE. Same rules as scripts/f006_bb_20_2_xsym_agree_sizing.py. One
continuous backtest per series from warmup through Validation-4 end, then
score only Validation-4 entries. Do not fit anything on Validation-4.
Do not change the multiplier formula or the one-bar shift. Agreement is
this name's signal, not BB_20_25_EMA200.

Baseline:
Uniform stake=100 on the same continuous run. Sanity gate, before trusting
Validation-4, on the Train-1 slice of that longer control run. Exactly one
gate, the same shape as Validation-3:
  - mean train1_net_pnl within relative 0.25% of |+95.3217987|
    (allowance 0.0025 * 95.3217987 = 0.23830449675). Reference is this
    name's catalog replay in
    output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json
    (control_replay.control_mean_train1_net_pnl = 95.3217987), not the
    rounded 95.321799 display, not the continuous-run observation
    95.463371, and not +82.900262. Do not retarget the reference onto
    95.463371. That observation already sits inside this band; changing
    the reference would be a new gate trial.
  - Train-1-entry n = 756 exact
    (2024-03-01 <= entry_time < 2025-03-01).
Do NOT use an absolute 1e-6 gate on the 10-series mean. The relative
0.25% band is the pre-registered control check, chosen before scoring,
for the same reason as Validation-1, Validation-2, and Validation-3: a
short Train-1 backtest force-closes at end_of_data inside the last
Train-1 bucket on 240m, while the continuous run keeps those positions
open. It is not a new trial. If the gate fails, STOP. Do not interpret
Validation-4. Do not widen 0.25%. Do not change falsifiers (a)-(e) to
make a close gate pass.
Do NOT add a second gate that requires the Validation-3 entry-mean to
match +1.772572 or +8.007368, or the Validation-3 entry n path to be
frozen in PnL. The Validation-3 run force-closed end_of_data exits at
2025-12-01 (results.csv n_val3_end_of_data_exits sums to 7). A run that
continues through 2026-03-01 will realize those positions later, so
Validation-3 entry nets may move. That movement is expected. It is not a
falsifier, not a gate, and not a reason to score or to refuse to score
Validation-4. Do not add a gate on the Validation-1 or Validation-2
means either.

Metrics (pre-declared), Validation-4 entries only
(2025-12-01 <= entry_time < 2026-03-01 UTC):
1. mean val4 net PnL across 10 series (primary)
2. pooled losing entry-month count out of the 3 Validation-4 months
   (2025-12, 2026-01, 2026-02)
3. n_trades invariant on Validation-4 entries per series, and on total
   closed trades of the continuous run
4. pooled mean(mult|winner) - mean(mult|loser) on Validation-4-entry
   closed trades
5. stake_cv on Validation-4 entries (pooled, and every series > 0.05)
6. big-winner contribution at net>=29.9 (informational; recomputed on
   this run, do not import 38.364839, 148.010545, 62.342863, 199.523967,
   161.542970, 168.273303, +1251.654084, +187.114893, or the other
   name's figures)
7. month contribution of the entry-net difference (informational only)
8. number_of_trials = 1 (the formula is already frozen; this is not a
   new trial of a new rule)

Expected improvement:
Sized mean val4 net > this name's Validation-4 control AND pooled
losing-month count <= this name's Validation-4 control count AND pooled
mult gap > 0, with n_trades invariant and stake_cv > 0.05.
There is no minimum margin. Do not add one after seeing the numbers.

Falsification condition (any one => FALSIFIED):
(a) sized mean val4 net <= this name's Validation-4 control; OR
(b) pooled Validation-4 losing-month count > this name's control count; OR
(c) pooled mult gap <= 0; OR
(d) n_trades invariant broken; OR
(e) stake_cv <= 0.05.
These are the same five conditions used on the Validation-1, Validation-2,
and Validation-3 sizing checks. They are not loosened: no negative gap
allowance, no extra losing month allowed, no lower stake_cv floor, no
dropped condition. (b) is non-worsening on a 3-month window, not a silent
drop of the gap test. Do not add a post-hoc October-concentration,
September-worsening, 6/10-series, July-concentration, May-concentration,
or thin-margin falsifier inside this run. Do not change the formula after
seeing Validation-4. Do not declare this falsified because BB_20_25 Val-1
failed or because this name's Validation-3 means were thin.

Data split:
Score Validation-4 only. The backtest may include warmup, Train-1,
Validation-1, Validation-2, and Validation-3 so that positions entering
Validation-4 are causal, but bars at or after 2026-03-01 must not be
loaded into the engine. Holdout (entry >= 2026-03-01, through
2026-09-01) is forbidden. Do not print holdout rows. Do not score
holdout. There is no Validation-5; do not invent one.

Budget:
One frozen formula. Control + sized arm. No grid. No second mechanism.
```

decision_if_pass: stay CONDITIONAL; this formula survives Validation-4 on
  BB_20_2_EMA200. The remaining F005 protocol §3.2 split is Holdout
  (2026-03-01 <= entry < 2026-09-01). Protocol §11 opens holdout only
  after a freeze. This pass does not FREEZE and does not authorize
  opening holdout. A later coordinator decision is required before
  holdout. Other §8 entry structure stays open but is not next until
  Validation-4 is decided
decision_if_fail: close this xsym-agree formula on BB_20_2_EMA200 (the
  Train-1, Validation-1, Validation-2, and Validation-3 passes did not
  keep generalizing). Stay CONDITIONAL. Do not FREEZE. Do not retune
  0.5 / 0.375 / 2.0. Next open axis is one not-yet-run §8 entry
  structure on this name, with a new written mechanism. Not a jump to
  EMA_50_200 or EMA3_13_50_200. Not evidence about those names. Not a
  holdout of this formula.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
