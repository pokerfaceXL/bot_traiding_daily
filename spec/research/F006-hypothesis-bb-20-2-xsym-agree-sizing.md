# F006 — H-BB-20-2-XSYM-AGREE-SIZING-01 (pre-registered)

> Pre-registered **before** implementing or running the sized arm.
> `H-BB-20-2-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** on this name's
> own trades (`f7ac677`). Entry-vol / abs-ATR stays closed. Do not retune T.
> `BB_20_25_EMA200` is **FREEZE**. Its xsym sizing Train-1 pass (`1c9ff7e`)
> and Val-1 fail (`89e936a`) close that formula on **that name only**. They
> are not this test. Do not copy that name's control mean (+82.900262), its
> sized mean (+147.71), its floor move (7/12→5/12), its mult gap (+0.119),
> or its stake_cv (0.526) onto this card as an expected result.
> Position sizing has never been run on `BB_20_2_EMA200` under protocol.

experiment_id: H-BB-20-2-XSYM-AGREE-SIZING-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-ABS-ATR-ENTRY-GATE-01
FALSIFIED (a)+(c) on own trades (tip f7ac677). Control mean +95.3217987/series
reproduced (sum +953.217987, 10 series, 8/10 positive). Best abs-ATR cell
t_2_0 mean +64.0461, initial_sl drop 3.45pp. Cells that cut initial_sl ≥10pp
kept ~39% of this name's big-winner PnL (12 trades, +1251.654084, net≥29.9)
and sat near +50/series. Exit, long-only, and breadth already ran on this
name's own series and did not clear the monthly floor. The ungated book is
still aggregate-positive. §8 allows a sizing test only after the signal itself
has an edge; that precondition holds. It does not hold as a license to mask
a negative-EV signal, and this test must not do that.

Problem:
Monthly regularity is unresolved (abs-ATR control entry-month floor 7/12;
0/10 series clear §7). An ATR-magnitude entry gate removes the same
signal_reverse runners that carry the aggregate PnL. This name has no
own-trades sizing result. A stake rule that keeps every trade can reweight
entries without the sample-starvation that boolean gates use.

Mechanism:
Basket breakouts that coincide with the same nonzero direction on peer
symbols are more likely to be the regime-aligned runners; idiosyncratic
single-symbol fires are more likely to be initial_sl deaths. Because
strategy_signal_series is a persistent directional state per (symbol,
interval), the count of the other four basket symbols whose BB_20_2_EMA200
signal matches the traded symbol's nonzero direction on the closed bar is a
causal, bar-aligned agreement score. It is not an ATR threshold and not a
fitted cutoff from another name's PnL. Scaling stake by that score keeps
n_trades invariant and raises the relative weight of consensus entries.

The stake band is structural, not a threshold mined on BB_20_25:
n_agree ∈ {0,1,2,3,4} maps linearly onto [0.5, 2.0],
mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
because (2.0 − 0.5) / 4 = 0.375. That arithmetic is the same shape used on
the other name. Using it here is the own-trades test of this mechanism. It
is not a claim that the other name's Train-1 pass or Val-1 fail already
answered this name.

Hypothesis:
Replacing uniform stake=100 with stake=100*mult(n_agree), where n_agree is
the number of the other 4 basket symbols whose BB_20_2_EMA200 persistent
signal equals the traded symbol's nonzero direction on the same interval,
will raise mean Train-1 net PnL versus the uniform-stake control AND
strictly lower this name's pooled losing-month floor, with
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
scripts/f006_bb_20_25_xsym_agree_sizing.py; point the signal name at
BB_20_2_EMA200.

Freeze this single formula before the run. No post-hoc retuning.
number_of_trials = 1 (one sized formula). Report the uniform control and
this one sized arm only.

Baseline:
Uniform stake=100 BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol ×
2-interval Train-1 basket. The control arm (stake_series=None) must
reproduce all 10 train1_net_pnl rows in
output/f006_notrail_monthly_catalog5/summary/results.csv for strategy
BB_20_2_EMA200 (mean +95.3217987/series, sum +953.217987) and match
n_trades, before the sized arm is trusted. Do not match +82.900262.
Use the Train-1 caches the abs-ATR control just matched
(checksums in output/f006_bb_20_2_abs_atr_gate/grid_freeze.json,
*_20240126T000000Z_20250301T000000Z.csv). Do not use the sibling script's
EXPECTED_CHECKSUMS table; those hashes are a different slice. Do not load
*_20260901* or *_20200325*.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. pooled losing-month floor (of 12, by entry-month, same definition as the
   abs-ATR harness on this name). Confirm the control floor in this run.
   The abs-ATR control measured 7/12; that is an observation to confirm,
   not an imported pass line from BB_20_25.
3. n_trades invariant: n_trades_sized == n_trades_baseline for every series
   (hard), both closed trades and Train-1-entry keys
4. mean(mult|winner) − mean(mult|loser) on Train-1-entry closed trades
5. stake_cv across Train-1 entries (must be > 0.05)
6. big-winner contribution (net≥29.9) versus this name's uniform control
   (informational). Recompute the set on this run's ungated blotter. The
   abs-ATR freeze observed 12 trades / +1251.654084; confirm, do not import
   the other name's $968.02 set.
7. number_of_trials = 1

Expected improvement:
Mean train1_net_pnl > this name's uniform control AND pooled losing-month
floor strictly below this name's control floor AND
mean(mult|winner) > mean(mult|loser), with n_trades invariant and
stake_cv > 0.05.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ this name's uniform baseline; OR
(b) pooled losing-month floor does not improve (stays ≥ this name's
    control floor); OR
(c) mean(mult|winner) − mean(mult|loser) ≤ 0; OR
(d) n_trades invariant broken on any series; OR
(e) stake_cv ≤ 0.05 (degenerate near-uniform weights).
Do not change the mult formula after seeing results without a new written
hypothesis. Do not declare this falsified because BB_20_25 Val-1 failed.
Do not declare it passed because BB_20_25 Train-1 passed.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the sized arm passes, a separate validation run is a later hypothesis.
Do not open it in this run.

Budget:
One pre-registered formula. Control + sized arm only. Report both.
No grid. No second mechanism.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; sizing stays
  open until a separate validation; do not open holdout in this run; do not
  FREEZE)
decision_if_fail: this xsym-agree formula is closed on BB_20_2_EMA200 own
  trades. Worker must not set FREEZE and must not change profile status.
  Entry structure on this name stays open for the coordinator. Do not retune
  0.5 / 0.375 / 2.0 inside this run. Do not treat the result as evidence
  about EMA_50_200 or EMA3_13_50_200.

## Result

(empty — worker fills after the run)

## Decision

(empty — coordinator only)
