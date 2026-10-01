# F006 — H-CATALOG5-BREADTH-REGIME-01 (pre-registered)

> Pre-registered **before** any breadth-regime module exists. Definitions below are frozen
> pre-code. Grounded in `spec/research/F006-ema3-21-autopsy.md` §4 (losing months are shared:
> 6/12 months have ≥4/5 basket symbols net-negative together). This is the one remaining
> licensed lever after the per-name entry-vol and direction axes were falsified on EMA3_21's own
> trades. It must NOT be closed "by transfer" from the Donchian `btc_filter` result
> (H-BTC-FILTER-01, H2-falsified) — that is a different family (Donchian alts), a different
> regime measure (BTC directional-efficiency ER20), and the same discipline that reopened the
> catalog5 entry axis forbids closing this one by analogy.

experiment_id: H-CATALOG5-BREADTH-REGIME-01
date: 2026-10-01
base_strategy: EMA3_21_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_21_50_200 is aggregate-positive (+817 Train-1 net) but 7/12 months losing, and the losses
are shared across the basket: 6/12 months have >=4/5 of the 5 symbols net-negative together
(Aug/Sep 2024 = 5/5). Per-name single-axis levers (entry-vol, direction/long-only, exit-grid,
partial-exit) are all falsified; long-only even worsened the floor (7->9/12) by removing a
partially-hedging short book. So the lever must act on the basket REGIME, not the per-name
entry.

Problem:
Breakout-momentum entries across the whole basket fail together in choppy / broadly-declining
regimes. A per-name strategy cannot see the basket state at its decision bar.

Mechanism:
When few basket symbols are in an uptrend (low breadth), new momentum breakouts are more likely
false (mean-reversion/chop regime); when breadth is high, breakouts run to the opposite extreme.
Breadth is a market-regime context, not a return forecast for any one symbol.

Hypothesis:
Gating EMA3_21 entries on a causal basket-breadth regime (take entries only when breadth is high
enough) lowers the losing-month floor WITHOUT removing the fat-tail winners.

Change to test:
ONE gate — a basket-breadth entry veto. No change to entry indicator, stop, exit, sizing, costs,
capital, or basket.

Breadth definition (causal, no look-ahead) — FROZEN:
At each decision bar i, breadth(i) = (# of the 5 basket symbols {BTCUSDT, ETHUSDT, SOLUSDT,
XRPUSDT, DOGEUSDT} whose close at bar i is above that symbol's own EMA200 at bar i) / 5, using
ONLY closes at or before bar i for every symbol, on the SAME interval as the traded series.
Missing/warm-up symbol (fewer than 200 closed bars, or unaligned bar) counts as NOT above
(contributes 0 to the numerator). Breadth is evaluated at the entry decision bar; the entry is
taken only if breadth(i) >= B, otherwise the strategy stays flat and waits for the next signal.
Exits are unchanged (an open position is never force-closed by breadth).

Parameter grid (FROZEN, 3 cells, no widening after seeing results):
B in {0.4, 0.6, 0.8}.

Baseline:
EMA3_21_50_200 NO_TRAIL, both directions, Train-1 pooled, no breadth gate (B=0 equivalent),
same costs/capital/basket.

Metrics (pre-declared, per protocol §10):
net PnL, mean/trade, n_trades, pooled losing-month floor (of 12), per-symbol losing-month floor,
big-winner PnL retained (sum of net >= 29.9 vs baseline's), #symbols net-positive, exit mix.

Expected improvement:
Some B lowers the pooled losing-month floor below 7/12 while keeping the Oct/Nov long runners.

Falsification condition (ANY one ⇒ FALSIFIED, not CONTINUE):
(a) no B in the grid lowers the pooled losing-month floor below 7/12; OR
(b) the B with the best floor removes >50% of baseline big-winner PnL (tail-cutting — the
    long-only / vol-gate failure mode); OR
(c) the net improvement is carried by a single symbol (fails for >=4 of 5 symbols); OR
(d) n_trades at the best-floor B drops >60% vs baseline (starvation, protocol §5).

Data split:
Train-1 only (2024-03 … 2025-02 entry cohort). Validation/holdout untouched. If a B passes all
gates on Train-1, the next step is a separate validation-window pre-registration — NOT retuning B
on validation/holdout.

number_of_trials: 3 (single breadth gate, 3 frozen thresholds)
```

## Result

(filled by worker run)

## Decision

(filled by coordinator after review)
