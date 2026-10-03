# F006 — H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 (pre-registered)

> Pre-registered **before** implementing or running the sized arm.
> `H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** on this
> name's own trades (`46e4509`). (d) was not reachable. Entry-vol / abs-ATR
> stays closed. Do not retune T. `EMA_50_200` is **FREEZE** after its own
> liquidity result (`48aef9f`). Its xsym sizing Train-1 result (`48d03b0`,
> FALSIFIED (b), sized mean +126.744211, floor stayed 7/12, no Val-1) closes
> that formula on **that name only**. `BB_20_2_EMA200` Train-1 pass
> (`1774a8a`) and Val-4 fail (`139ed3d`), and `BB_20_25_EMA200` Train-1 pass
> (`1c9ff7e`) and Val-1 fail (`89e936a`), likewise close those names only.
> They are not this test. Do not copy +72.6693115, +95.3217987, +82.900262,
> or +126.744211, and do not copy another name's floor move, mult gap, or
> stake_cv onto this card as an expected result. Position sizing has never
> been run on `EMA3_13_50_200` under protocol. Do not FREEZE this name.

experiment_id: H-EMA3-13-50-200-XSYM-AGREE-SIZING-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01
FALSIFIED (a)+(c) on own trades (tip 46e4509). (d) was not reachable: no T
passed (a)–(c). Control mean +91.1483016/series reproduced from this
experiment's artifacts (output/f006_ema3_13_50_200_abs_atr_gate/; sum
+911.483016, 10 series; entry cohort n=423, +771.2836172145886, initial_sl
292/423, floor 7/12, big winners 9 / +1131.9561537333418). Best abs-ATR cell
t_2_0 mean +83.4087526 (delta −7.739549/series), n=337, initial_sl drop
4.04557 pp, big-winner PnL kept 85.1%. The flat 7/12 floor is informational
on that card, not a (d) fire. Exit, long-only, and breadth already ran on
this name's own series and did not clear the monthly floor. The ungated book
is still aggregate-positive. §8 allows a sizing test only after the signal
itself has an edge; that precondition holds. It does not license masking a
negative-EV signal. EMA_50_200's sized mean +126.744211 is not this name's
expectation.

Problem:
Monthly regularity is unresolved (abs-ATR control entry-month floor 7/12;
0/10 series clear §7). An ATR-magnitude entry gate removes the same
signal_reverse runners that carry the aggregate PnL. This name has no
own-trades sizing result. A stake rule that keeps every trade can reweight
entries without the sample-starvation that boolean gates use.

Mechanism:
Basket triple-EMA crosses (`sig_ema3_cross(13, 50, 200)`) that coincide with
the same nonzero direction on peer symbols are more likely to be the
regime-aligned runners; idiosyncratic single-symbol fires are more likely to
be initial_sl deaths. Because strategy_signal_series is a persistent
directional state per (symbol, interval), the count of the other four basket
symbols whose EMA3_13_50_200 signal matches the traded symbol's nonzero
direction on the closed bar is a causal, bar-aligned agreement score. It is
not an ATR threshold, not `sig_ema_cross(50, 200)`, and not a fitted cutoff
from another name's PnL. Scaling stake by that score keeps n_trades invariant
and raises the relative weight of consensus entries.

The stake band is structural, rewritten for this name, not a threshold mined
on EMA_50_200, BB_20_2, or BB_20_25, and not that name's +126.744211 result:
n_agree ∈ {0,1,2,3,4} maps linearly onto [0.5, 2.0],
mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
because (2.0 − 0.5) / 4 = 0.375. That arithmetic is the structural band.
Using it here is the own-trades test of this mechanism on EMA3_13_50_200.
It is not a claim that another name's Train-1 result or validation fail
already answered this name.

Hypothesis:
Replacing uniform stake=100 with stake=100*mult(n_agree), where n_agree is
the number of the other 4 basket symbols whose EMA3_13_50_200 persistent
signal equals the traded symbol's nonzero direction on the same interval,
will raise mean Train-1 net PnL versus the uniform-stake control AND strictly
lower this name's pooled losing-month floor, with
mean(mult|winner) > mean(mult|loser).

Change to test:
ONE position-sizing change only, via backtest_engine.run_backtest
stake_series. No entry gate, no abs-ATR, no exit, symbol, interval,
direction, or breadth change. NO_TRAIL unchanged.

  n_agree ∈ {0,1,2,3,4}
  mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
  # → 0→0.50, 1→0.875, 2→1.25, 3→1.625, 4→2.00
  stake_series = 100.0 * mult, aligned to the engine fill bar.

Causal alignment (required): a signal at bar i close fills at bar i+1 open.
stake_series at the fill bar must be the agreement observed at the prior
closed bar. The first bar has no prior agreement and uses the uniform $100
stake. Do not read the fill bar's own close. Reuse the one-bar shift in
scripts/f006_ema_50_200_xsym_agree_sizing.py (or the BB sibling); point the
signal name at EMA3_13_50_200. Do not reuse that script's EXPECTED_MEAN.

Freeze this single formula before the run. No post-hoc retuning.
number_of_trials = 1 (one sized formula). Report the uniform control and
this one sized arm only.

Baseline:
Uniform stake=100 EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol × 2-interval
Train-1 basket. The control arm (stake_series=None) must reproduce all 10
train1_net_pnl rows in
output/f006_notrail_monthly_catalog5/summary/results.csv for strategy
EMA3_13_50_200 (mean **+91.1483016**/series, sum **+911.483016**) and match
n_trades, before the sized arm is trusted. That figure is also the
reproduced control from output/f006_ema3_13_50_200_abs_atr_gate/ — use it as
this name's baseline going forward. Do not match +72.6693115. Do not match
+95.3217987. Do not match +82.900262. Do not match +126.744211. Use the
Train-1 caches the abs-ATR control just matched (checksums in
output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json,
*_20240126T000000Z_20250301T000000Z.csv). Do not reuse another script's
EXPECTED_CHECKSUMS table. Do not load *_20260901* or *_20200325*.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. pooled losing-month floor (of 12, by entry-month, same definition as the
   abs-ATR harness on this name). Confirm the control floor in this run.
   The abs-ATR control measured 7/12; that is an observation to confirm,
   not an imported pass line from another name.
3. n_trades invariant: n_trades_sized == n_trades_baseline for every series
   (hard), both closed trades and Train-1-entry keys
4. mean(mult|winner) − mean(mult|loser) on Train-1-entry closed trades
5. stake_cv across Train-1 entries (must be > 0.05)
6. big-winner contribution (net≥29.9) versus this name's uniform control
   (informational). Recompute the set on this run's ungated blotter. The
   abs-ATR freeze observed 9 trades / +1131.9561537333418; confirm, do not
   import another name's set (not 5 / +843.7639016181568).
7. number_of_trials = 1

Expected improvement:
Mean train1_net_pnl > this name's uniform control (+91.1483016) AND pooled
losing-month floor strictly below this name's control floor AND
mean(mult|winner) > mean(mult|loser), with n_trades invariant and
stake_cv > 0.05.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ this name's uniform baseline (+91.1483016); OR
(b) pooled losing-month floor does not improve (stays ≥ this name's
    control floor); OR
(c) mean(mult|winner) − mean(mult|loser) ≤ 0; OR
(d) n_trades invariant broken on any series; OR
(e) stake_cv ≤ 0.05 (degenerate near-uniform weights).
A flat month floor is (b) on this card: the sentence says a non-improving
floor falsifies. If (b) fires, the formula is closed and no validation
window is opened. Do not change the mult formula after seeing results
without a new written hypothesis. Do not declare this falsified because
EMA_50_200 sizing was FALSIFIED (b), or because BB_20_2 Val-4 or BB_20_25
Val-1 failed. Do not declare it passed because either BB name's Train-1
passed or because EMA_50_200's sized mean was +126.744211.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the sized arm passes, a separate validation run is a later hypothesis.
Do not open it in this run. A validation window is allowed only if a later
Decision says this arm passed.

Budget:
One pre-registered formula. Control + sized arm only. Report both.
No grid. No second mechanism.
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; sizing stays
  open until a separate validation; do not open holdout in this run; do not
  FREEZE; status stays CONDITIONAL)
decision_if_fail: this xsym-agree formula is closed on EMA3_13_50_200 own
  trades. Worker must not set FREEZE and must not change profile status.
  The name stays CONDITIONAL. The following open axis is candle confirm
  (entry structure) on this name only. Do not retune 0.5 / 0.375 / 2.0
  inside this run. Do not treat the result as evidence about EMA_50_200 or
  either BB name. Do not reopen abs-ATR. Do not open a validation window:
  the card allows one only if the arm passes. Do not start funding-carry,
  spread-capture, or catalog mean-reversion.

## Result

(empty — worker only)

## Decision

(empty — coordinator only)
