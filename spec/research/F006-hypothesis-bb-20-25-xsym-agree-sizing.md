# F006 — H-BB-20-25-XSYM-AGREE-SIZING-01 (pre-registered)

> Pre-registered **before** implementing or running the sized arm. Position sizing was never
> tested on `BB_20_25_EMA200` under protocol. ATR-magnitude levers are closed on this name
> (abs-ATR entry gate FALSIFIED tip `3788f11`); this hyp uses an **orthogonal** cross-symbol
> agreement signal applied as continuous stake weights (not a boolean entry gate).

experiment_id: H-BB-20-25-XSYM-AGREE-SIZING-01
date: 2026-10-02
base_strategy: BB_20_25_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_25_EMA200 stays CONDITIONAL after H-BB-20-25-ABS-ATR-ENTRY-GATE-01 FALSIFIED (a) on own
trades (tip 3788f11): every keep-low-ATR threshold cut mean Train-1 net PnL below +82.90 while
runners co-located with the high-ATR mass. Exit / direction / breadth levers already closed on
this name's own-trade evidence. Vol-inverse ATR% sizing was FALSIFIED on related NO_TRAIL leads
(DONCHIAN_55 / BB_20_25_breakout / DONCHIAN_PULLBACK_55) with winner−loser mult gap ≈ 0 and the
Decision explicitly named cross-sectional signal agreement as the remaining orthogonal sizing
lever. Cross-symbol agreement as a boolean entry gate previously moved win rate the right way
(+2.82pp at MIN_AGREE=2 on those leads) but thinned sample and did not clear §7 monthly; it was
never applied as continuous stake sizing on BB_20_25_EMA200.

Problem:
Monthly regularity remains unresolved (pooled losing-month floor 7/12; 0/10 series clear §7).
ATR-magnitude entry filters and inverse sizing amplify the same failure (discount elevated-vol
breakouts that carry fat tails). We need a non-ATR lever that can reweight months without
removing runners.

Mechanism:
Crypto-basket breakouts that coincide with same-direction lean across peer symbols are more
likely regime-aligned runners; idiosyncratic single-symbol fires are more likely stop-outs.
Because `strategy_signal_series` is a persistent directional state per (symbol, interval), the
count of other basket symbols matching the traded symbol's nonzero direction at the entry bar
is a causal, bar-aligned agreement score. Scaling stake by that score (via stake_series) keeps
every trade (n_trades invariant) while raising relative weight of consensus entries — the same
information the boolean gate used, applied as weight instead of exclusion so sample-starvation
cannot manufacture a false monthly pass.

Hypothesis:
Replacing uniform stake=100 with stake=100*mult(n_agree), where n_agree = number of the other 4
basket symbols whose BB_20_25_EMA200 persistent signal equals the traded symbol's nonzero
direction on the same closed bar / same interval, will raise mean Train-1 net PnL versus the
uniform-stake control AND strictly lower the pooled losing-month floor, with mean(mult|winner)
> mean(mult|loser).

Change to test:
ONE position-sizing change only via backtest_engine.run_backtest stake_series hook.
No entry gate, exit, symbol, interval, direction, or breadth changes. NO_TRAIL unchanged.
Agreement definition matches scripts/f006_entry_cross_symbol_experiment.py's cross_symbol_gate
inputs (persistent normalized signals, index-aligned), but outputs a continuous multiplier
instead of a boolean mask:

  n_agree ∈ {0,1,2,3,4}
  mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
  # → 0→0.50, 1→0.875, 2→1.25, 3→1.625, 4→2.00
  stake_series = 100.0 * mult  (aligned to engine work index; fillna(100.0))

Freeze this single formula before the run — no post-hoc retuning. Optional reported cells may
include the uniform control and this one sized arm only (number_of_trials = 1 sized formula).

Baseline:
Uniform stake=100 BB_20_25_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1 basket.
Control arm (stake_series=None) must reproduce catalog5 / abs-ATR-gate control figures for this
name (mean train1_net_pnl ≈ +82.90 across 10 series; pooled entry cohort n=512 net ≈ +709.85 —
report which and match exactly before trusting the sized arm).

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. pooled losing-month floor (of 12, by entry-month)
3. n_trades invariant: n_trades_sized == n_trades_baseline for every series (hard)
4. mean(mult|winner) − mean(mult|loser) on Train-1-entry closed trades (mechanism check)
5. stake_cv across entries (must be > 0.05 — genuineness: formula must actually vary)
6. big-winner PnL (net≥29.9) vs baseline (informational; sizing should not need to "retain" by
   dropping trades — report weighted contribution)
7. number_of_trials = 1 (single pre-registered formula)

Expected improvement:
Mean train1_net_pnl > baseline AND pooled losing-month floor strictly below baseline floor
(7/12 on ungated control — confirm in control arm) AND mean(mult|winner) > mean(mult|loser).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline; OR
(b) pooled losing-month floor does not improve (stays ≥ baseline floor); OR
(c) mean(mult|winner) − mean(mult|loser) ≤ 0 (mechanism absent / wrong direction); OR
(d) n_trades invariant broken on any series; OR
(e) stake_cv ≤ 0.05 (degenerate near-uniform weights).
Do not change the mult formula after seeing results without a new written hypothesis.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.

Budget:
One pre-registered formula (above). Control + sized arm only. Report both. No grid widening.
```

decision_if_pass: REFINE (update BB_20_25_EMA200 profile; consider validation / floor check)
decision_if_fail: keep CONDITIONAL; mark position-sizing (xsym-agree formula) closed on this name;
  next = either a different non-ATR sizing signal with new written mechanism, or move to next
  highest CONDITIONAL name's open entry-vol own-trades axis (prefer BB_20_2_EMA200 or EMA_50_200)

## Result

**Run_id:** `scripts/f006_bb_20_25_xsym_agree_sizing.py` @ `10e41d3`, 2026-10-02T22:17:25Z
**Artifacts:** `output/f006_bb_20_25_xsym_agree_sizing/`
**Outcome:** NOT FALSIFIED — the sized arm passes every pre-registered condition (a)–(e).
**number_of_trials:** 1 (single pre-registered formula).

### Control arm (stake_series=None, uniform 100)

- mean train1_net_pnl: **+82.90** across 10 series.
- all closed trades including warmup: n=560.
- Train-1-entry cohort: n=512, net=**+709.85**, net/trade=+1.386.
- pooled entry-month losing floor: **7/12**, exactly reproducing the abs-ATR ungated control.

### Sized arm (mult=clip(0.5+0.375*n_agree,0.5,2.0))

- mean train1_net_pnl: **+103.00** across 10 series (+24.2% versus control).
- all closed trades including warmup: n=560.
- Train-1-entry cohort: n=512, net=**+906.18**, net/trade=+1.770.
- pooled entry-month losing floor: **4/12**, improving by three months from the 7/12 control.
- pooled mean(mult|winner) - mean(mult|loser): **+0.169922** (0.798828 - 0.628906).
- Train-1-entry stake_cv: **0.543649** pooled; every series exceeds 0.05 (range 0.375971–0.636071).
- trade-count invariant: PASS for every series, both total closed trades (560=560) and
  Train-1-entry trades (512=512), with matching entry keys.
- per-series entry-month floors: SOL/240 7→7, ETH/240 7→6, BTC/240 6→6, XRP/240 9→8,
  DOGE/240 6→6, SOL/60 3→2, ETH/60 6→4, BTC/60 9→8, XRP/60 7→7, DOGE/60 5→3.
  Six series improve and four are unchanged; none worsens.

### Big-winner contribution (Train-1-entry cohort, net_pnl >= 29.9)

- baseline: 10 trades, net **+968.02**.
- sized arm by its own threshold: 9 trades, net **+892.70**.
- sized PnL on the baseline big-winner entry keys: **+864.35**.

### Falsification assessment

(a) mean train1_net_pnl <= baseline: does not fire (103.00 > 82.90).
(b) pooled losing-month floor does not improve: does not fire (4/12 < 7/12).
(c) pooled mean(mult|winner) - mean(mult|loser) <= 0: does not fire (+0.169922).
(d) n_trades invariant broken: does not fire (all per-series invariants pass).
(e) stake_cv <= 0.05: does not fire (pooled 0.543649; every series > 0.05).

**Verdict:** NOT FALSIFIED / passes the pre-registered bar. The frozen agreement formula raises
mean Train-1 net PnL, reduces the correctly pooled entry-month losing floor from 7/12 to 4/12,
and assigns higher average multipliers to winners while retaining every trade. This is a Train-1
result only; validation and any profile decision remain outside this run.

## Decision

(empty — coordinator only after Result)
