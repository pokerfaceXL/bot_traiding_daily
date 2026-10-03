# F006 — H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01 (pre-registered)

> Pre-registered **before** running Validation-3. Validation-2
> `H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01` is **NOT FALSIFIED** on this
> name's own trades (tip `7798bbb`, Claude review PASS
> `2026-10-03-f006-bb202-xsym-agree-sizing-val-c1c25e2f`, FF-merged from
> `1eced44`). `decision_if_pass` on that card is stay CONDITIONAL and
> continue to Validation-3 of the same formula (F005 protocol §3.2:
> 2025-09-01 ≤ entry < 2025-12-01). Coordinator protocol §3.10 and §11
> say one more window is still required. This note freezes the same
> formula and asks whether it still beats the uniform-stake control on
> this name's Validation-3 entries. No retune. Holdout stays closed.
> Do not FREEZE. Do not open Validation-4 in this run. The thin
> Validation-2 margin is a caveat on the prior card, not a new stop
> rule and not a reason to skip this window.
>
> Dates below are the frozen F005 protocol §3.2 row **Validation 3**,
> not a new split: 2025-09-01T00:00:00Z ≤ entry < 2025-12-01T00:00:00Z
> (calendar 2025-09, 2025-10, 2025-11). Do not invent another window.
>
> `BB_20_25_EMA200` is **FREEZE** on its own loop. Its Val-1 of a
> same-shaped formula is **FALSIFIED (c)** at `89e936a`. That result is
> not this test. Do not copy its control mean, its sized mean, its mult
> gap, its n, or its month count onto this card as an expected result.
> Do not copy this name's Validation-2 means (+2.331879 / +2.551244) or
> its Validation-1 means (−9.270577 / −4.002329) as an expected
> Validation-3 result either. Do not declare this run falsified because
> another window or another name failed, and do not declare it passed
> because Train-1, Validation-1, or Validation-2 passed.

experiment_id: H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
On this name's own trades the causal agreement stake (fill bar i uses
n_agree from closed bar i-1; mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0);
leading stake 100; agreement counted on BB_20_2_EMA200's own persistent
signal) was NOT FALSIFIED on Train-1 (tip 1774a8a: control mean
+95.3217987, sized +146.632696, floor 7/12 → 6/12, mult gap +0.086642,
n=756), NOT FALSIFIED on Validation-1 (tip 7e18786), and NOT FALSIFIED
on Validation-2 (tip 7798bbb). Validation-2 artifacts in
output/f006_bb_20_2_xsym_agree_sizing_val2/summary/cell_summary.json:
gate observed Train-1 mean 95.463371 vs reference 95.3217987 (diff
0.141572, allowance 0.23830449675), Train-1-entry n=756; control mean
val2-entry net +2.331879; sized mean +2.551244; losing months 2 and 2;
pooled mult gap +0.031667; val2-entry n 195; total closed 1226;
stake_cv 0.514115 (series min 0.428358). The margin is thin (+0.219365
per series) and the entry-net gain is concentrated in 2025-07
(+12.112764). Those are caveats, not new falsifiers. Entry-vol on this
name is already FALSIFIED (a)+(c) at f7ac677. Exit, long-only, and
breadth are already closed on this name. The sizing result has not been
seen on Validation-3.

Problem:
A pass on Train-1 plus two 3-month windows can still be a sample accident,
and Validation-2's gain is thin and one-month concentrated. FREEZE or
holdout from Validation-2 alone would violate §11. The Val-2 card's
decision_if_pass does not set a margin floor and does not stop. §7 says
a passed sizing arm is validated on the next named window before it is
abandoned for a new entry axis. The open question is whether the same
frozen weights help on Validation-3 of this name.

Mechanism:
Unchanged. The stake uses only agreement known when the entry was queued.
If that agreement truly marks basket-aligned runners on this name, the
same frozen weights should still raise Validation-3 mean PnL versus
uniform stake, without raising the short Validation-3 losing-month count,
and with a positive winner-minus-loser multiplier gap.

Hypothesis:
On this name's Validation-3 entries, the identical causal stake formula
beats uniform stake=100 on mean net PnL, does not increase the pooled
losing-month count, and keeps mean(mult|winner) > mean(mult|loser).

Change to test:
NONE. Same rules as scripts/f006_bb_20_2_xsym_agree_sizing.py. One
continuous backtest per series from warmup through Validation-3 end, then
score only Validation-3 entries. Do not fit anything on Validation-3.
Do not change the multiplier formula or the one-bar shift. Agreement is
this name's signal, not BB_20_25_EMA200.

Baseline:
Uniform stake=100 on the same continuous run. Sanity gate, before trusting
Validation-3, on the Train-1 slice of that longer control run. Exactly one
gate, the same shape as Validation-2:
  - mean train1_net_pnl within relative 0.25% of |+95.3217987|
    (allowance 0.0025 * 95.3217987 = 0.23830449675). Reference is this
    name's catalog replay in
    output/f006_bb_20_2_xsym_agree_sizing/summary/cell_summary.json
    (control_replay.control_mean_train1_net_pnl = 95.3217987), not the
    rounded 95.321799 display, not the Validation-2 continuous-run
    observation 95.463371, and not +82.900262. Do not retarget the
    reference onto 95.463371. That observation already sits inside this
    band; changing the reference would be a new gate trial.
  - Train-1-entry n = 756 exact
    (2024-03-01 <= entry_time < 2025-03-01).
Do NOT use an absolute 1e-6 gate on the 10-series mean. The relative
0.25% band is the pre-registered control check, chosen before scoring,
for the same reason as Validation-1 and Validation-2: a short Train-1
backtest force-closes at end_of_data inside the last Train-1 bucket on
240m, while the continuous run keeps those positions open. It is not a
new trial. If the gate fails, STOP. Do not interpret Validation-3. Do not
widen 0.25%. Do not change falsifiers (a)-(e) to make a close gate pass.
Do NOT add a second gate that requires the Validation-2 entry-mean to
match +2.331879 or +2.551244, or the Validation-2 entry n path to be
frozen in PnL. The Validation-2 run force-closed end_of_data exits at
2025-09-01 (results.csv n_val2_end_of_data_exits sums to 6). A run that
continues through 2025-12-01 will realize those positions later, so
Validation-2 entry nets may move. That movement is expected. It is not a
falsifier, not a gate, and not a reason to score or to refuse to score
Validation-3. Do not add a gate on the Validation-1 means either.

Metrics (pre-declared), Validation-3 entries only
(2025-09-01 <= entry_time < 2025-12-01 UTC):
1. mean val3 net PnL across 10 series (primary)
2. pooled losing entry-month count out of the 3 Validation-3 months
   (2025-09, 2025-10, 2025-11)
3. n_trades invariant on Validation-3 entries per series, and on total
   closed trades of the continuous run
4. pooled mean(mult|winner) - mean(mult|loser) on Validation-3-entry
   closed trades
5. stake_cv on Validation-3 entries (pooled, and every series > 0.05)
6. big-winner contribution at net>=29.9 (informational; recomputed on
   this run, do not import 199.523967, 161.542970, 168.273303,
   +1251.654084, +187.114893, or the other name's figures)
7. month contribution of the entry-net difference (informational only)
8. number_of_trials = 1 (the formula is already frozen; this is not a
   new trial of a new rule)

Expected improvement:
Sized mean val3 net > this name's Validation-3 control AND pooled
losing-month count <= this name's Validation-3 control count AND pooled
mult gap > 0, with n_trades invariant and stake_cv > 0.05.
There is no minimum margin. Do not add one after seeing the numbers.

Falsification condition (any one => FALSIFIED):
(a) sized mean val3 net <= this name's Validation-3 control; OR
(b) pooled Validation-3 losing-month count > this name's control count; OR
(c) pooled mult gap <= 0; OR
(d) n_trades invariant broken; OR
(e) stake_cv <= 0.05.
These are the same five conditions used on the Validation-1 and
Validation-2 sizing checks. They are not loosened: no negative gap
allowance, no extra losing month allowed, no lower stake_cv floor, no
dropped condition. (b) is non-worsening on a 3-month window, not a silent
drop of the gap test. Do not add a post-hoc July-concentration,
May-concentration, or thin-margin falsifier inside this run. Do not
change the formula after seeing Validation-3. Do not declare this
falsified because BB_20_25 Val-1 failed or because this name's
Validation-2 margin was thin.

Data split:
Score Validation-3 only. The backtest may include warmup, Train-1,
Validation-1, and Validation-2 so that positions entering Validation-3
are causal, but bars at or after 2025-12-01 must not be loaded into the
engine. Holdout (entry >= 2026-03-01) is forbidden. Do not print holdout
rows. Do not open Validation-4 (2025-12-01 <= entry < 2026-03-01) in
this run. Do not score those entries.

Budget:
One frozen formula. Control + sized arm. No grid. No second mechanism.
```

decision_if_pass: stay CONDITIONAL; this formula survives Validation-3 on
  BB_20_2_EMA200; next window would be Validation-4 of the same formula
  (F005 protocol §3.2: 2025-12-01 <= entry < 2026-03-01), still not
  holdout, still not FREEZE; other §8 entry structure stays open but is
  not next until that validation is decided
decision_if_fail: close this xsym-agree formula on BB_20_2_EMA200 (the
  Train-1, Validation-1, and Validation-2 passes did not keep generalizing).
  Stay CONDITIONAL. Do not FREEZE. Do not retune 0.5 / 0.375 / 2.0. Next
  open axis is one not-yet-run §8 entry structure on this name, with a new
  written mechanism. Not a jump to EMA_50_200 or EMA3_13_50_200. Not
  evidence about those names. Not a Validation-4 of this formula. Not
  holdout.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
