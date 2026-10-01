# F006 — H-EMA3-21-LONG-ONLY-01 (pre-registered)

> Pre-registered **before** computing the decisive test (long-only monthly floor + per-symbol
> monthly stability). The direction *net* asymmetry (longs +875 / shorts −58) and the fact that
> all big winners are longs are **observations** from the autopsy
> (`spec/research/F006-ema3-21-autopsy.md`), not the test. The test is whether removing the
> short book also fixes the **monthly irregularity** without cutting the long fat tails.

experiment_id: H-EMA3-21-LONG-ONLY-01
date: 2026-10-01
base_strategy: EMA3_21_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_21_50_200 is aggregate-Train-1-positive (+817 net) but 7/12 months losing, 19.6% WR,
68.7% initial_sl. Longs net +875 (mean +4.61); shorts net −58 (mean −0.27) and, excluding
end_of_data boundary trades, −237. All 7 big winners (net ≥ 29.9) are longs. The entry-vol
axis is falsified on this name (atr_percentile/calm identical for deaths vs runners).

Problem:
The short book is a systematically negative-EV subset dragging expectancy and adding losing
months, while contributing none of the fat-tail winners.

Mechanism:
Crypto momentum has a long-vol asymmetry: up-legs trend to the opposite Donchian/EMA extreme
(signal_reverse runners), down-legs mean-revert / short-squeeze and hit the fixed stop. So the
long and short sides of the same EMA-cross are not symmetric; the edge is structurally long.

Hypothesis:
Taking only long entries (ignoring short signals; longs' entries/exits are unchanged because
in NO_TRAIL one-shot a short is never a prerequisite for the next long) improves expectancy AND
monthly regularity without removing the long fat-tail winners.

Change to test:
ONE change — direction filter: long-only. No change to entry indicator, stop, exit, sizing,
costs, capital, or basket.

Baseline:
EMA3_21_50_200 NO_TRAIL, both directions, Train-1 pooled, same trade table.

Metrics (pre-declared):
net PnL, mean/trade (expectancy), WR, n_trades, pooled losing-month floor (of 12),
per-symbol losing-month floor, big-winner PnL retained (sum of net ≥ 29.9), #symbols
net-positive, concentration (top-3 winners' share of net).

Expected improvement:
Expectancy up (shorts are negative-EV); big-winner PnL retained ≈ 100% (winners are longs);
pooled losing months reduced below 7; and improvement spread over ≥2 carrying symbols.

Falsification condition (any one ⇒ FALSIFIED / not CONTINUE):
(a) mean/trade does not exceed baseline; OR
(b) big-winner PnL retained < 90% (long-only unexpectedly drops long tails); OR
(c) pooled losing-month floor does not improve (stays ≥ 7/12); OR
(d) the net improvement is carried by a single symbol (fails for ≥4 of 5 symbols); OR
(e) per-symbol losing-month floor does not improve for the carrying symbols (XRP, DOGE).

Data split:
Train-1 only (2024-03 … 2025-02 entry cohort). No validation/holdout touched. If Train-1
passes all gates, the confirmation step is a fresh engine run with a long-only entry mask
(validates the table-filter faithfulness) before any validation-window evaluation.

Method note:
Development test computed by filtering the immutable trade table to direction==1. This is a
faithful long-only result for NO_TRAIL one-shot: a long position exits on the opposite
(bullish→bearish) cross = a short *signal*, which does not require opening a short; the next
long entry occurs at the next bullish cross regardless of whether shorts were taken, so long
trades' records are identical with or without the short book.

number_of_trials: 1 (single direction filter; no parameter grid)
```

## Result

Train-1 pooled, `python3 scripts/f006_ema3_21_autopsy.py` + direction filter on the same table.

| metric | baseline (both dir) | long-only | gate |
| --- | ---: | ---: | --- |
| n trades | 402 | 190 | — |
| net PnL | +817.0 | +875.2 | — |
| mean / trade | +2.03 | **+4.61** | (a) PASS (expectancy up) |
| WR | 19.7% | 18.4% | — |
| big-winner PnL retained | 100% | **96.8%** | (b) PASS (≥90%) |
| pooled losing months | 7/12 | **9/12** | (c) **FAIL** (not improved) |
| #symbols net-positive | 3/5 | 3/5 | (d) PASS (not single-symbol) |
| per-symbol losing-month floor (carriers) | XRP 9, DOGE 6 | XRP 8, DOGE **9** | (e) **FAIL** (DOGE worse) |

Per-symbol net (both → long-only): XRP 532→568, DOGE 340→269, SOL 40→69, BTC −39→−3, ETH
−56→−29. Losing-month floor rose for 4 of 5 symbols (BTC 7→9, DOGE 6→9, ETH 7→9, SOL 5→6;
only XRP 9→8). Long-only monthly net stays dominated by 2024-11 (+845.9) and 2024-10 (+291.4);
top-3 winners still 91% of net.

**Mechanism of the failure:** the short book is net-negative overall but it was *winning in
some of the months where longs lose* — i.e. it provided partial monthly hedging. Removing it
raises expectancy (negative-EV subset gone, long tails kept) but **concentrates** the result
even harder into the two long-runner months, leaving more months with no offsetting gain. On
this basket, expectancy and monthly regularity are in direct tension; long-only trades
regularity away for EV.

## Decision

```yaml
decision: FALSIFIED
reason: >
  Falsifiers (c) and (e) tripped: pooled losing-month floor worsened 7/12 -> 9/12 and the
  carrying-symbol floor worsened (DOGE 6 -> 9), despite expectancy rising (+2.03 -> +4.61) and
  96.8% of big-winner PnL retained. Long-only improves EV but not the daily-regularity goal
  (TRACK), because the short book was partially hedging the long-losing months.
kept_finding: >
  Long-only is a legitimate higher-EV variant and a candidate PORTFOLIO COMPONENT input for
  F007 (mean/trade 4.61, tails intact); it is not a fix for monthly regularity. Do not retest
  long-only for the regularity goal without new info.
next_action: >
  The remaining live, causal lever identified by the autopsy is the SHARED-REGIME structure
  (section 4: 6/12 months have >=4/5 symbols down together). A single-axis entry-time
  refinement cannot address a basket-wide regime; the licensed next step is a separately
  pre-registered causal regime signal (portfolio-level veto/weight, protocol section 8 regime
  filter / section 13), with no look-ahead, defined before implementation. Not launched by
  this experiment.
number_of_trials: 1
```
