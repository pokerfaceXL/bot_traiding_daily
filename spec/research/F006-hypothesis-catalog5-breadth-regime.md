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

Train-1 pooled, `python3 scripts/f006_breadth_regime_experiment.py`
(`output/f006_breadth_regime/`). **Control passed:** the BASELINE cell reproduces the EMA3_21
autopsy exactly (402 trades, +817.0 net, 7/12 losing months, +1100 big-winner PnL, 3/5 symbols
positive), so the harness replication is sound.

| cell | n | net | mean/trade | pooled losing mo | big-winner PnL | big kept % | n_trades vs base % | #sym net+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BASELINE | 402 | +817.0 | 2.03 | 7 | 1100.0 | 100 | 100 | 3 |
| B40 | 269 | +691.7 | 2.57 | 8 | 926.5 | 84.2 | 66.9 | 3 |
| B60 | 230 | +689.7 | 3.00 | 9 | 926.5 | 84.2 | 57.2 | 3 |
| B80 | 185 | +566.3 | 3.06 | **7** | 653.5 | 59.4 | 46.0 | 3 |

Per-symbol losing-month floor (baseline → B80): SOL 5→4, ETH 7→8, BTC 7→7, XRP 9→8,
DOGE 6→7 — worse or flat for 3 of 5; the two carriers (XRP, DOGE) do not both improve.

**Falsifier (a) tripped:** no threshold lowers the pooled losing-month floor below the baseline
7/12 (best is B80, still 7). Same mechanism as long-only and the vol gate: breadth is another
volatility/trend-state proxy, so gating on it raises expectancy (2.03 → 3.06/trade) by thinning
marginal entries but does not separate the losing months from the runner months — the shared
regime produces both. B80 already trims 41% of big-winner PnL (falsifier (b) would trip for any
lower floor).

## Decision

```yaml
experiment_id: H-CATALOG5-BREADTH-REGIME-01
date: 2026-10-02
base_strategy: EMA3_21_50_200 (NO_TRAIL)
hypothesis: causal basket-breadth entry veto lowers the losing-month floor without cutting the long fat-tail winners
change_tested: entry veto, take entry only if breadth(i) >= B; breadth = frac of 5 symbols with close>own EMA200 at bar i (causal)
parameters: B in {0.4, 0.6, 0.8}
data_split: Train-1 only (2024-03..2025-02 entry cohort); validation/holdout untouched
baseline: EMA3_21_50_200 NO_TRAIL both-dir Train-1 (reproduced exactly as control)
metrics_before: {net: 817.0, mean_per_trade: 2.03, n_trades: 402, pooled_losing_months: 7, big_winner_pnl: 1100.0, symbols_net_positive: 3}
metrics_after: {best_floor_cell: B80, net: 566.3, mean_per_trade: 3.06, n_trades: 185, pooled_losing_months: 7, big_winner_pnl: 653.5, big_kept_pct: 59.4}
oos_result: not run (failed Train-1 gate)
cost_model: unchanged (commission 10bps, half-spread 5bps, slippage 2bps, leverage 1, stake 100, equity 500)
number_of_trials: 3
result: no threshold lowers the pooled losing-month floor below 7/12; expectancy up, regularity unchanged, tails partly cut
decision: FALSIFIED
reason: >
  Falsifier (a): no B lowers the pooled losing-month floor below baseline (7/12). Breadth is a
  volatility/trend proxy; it raises expectancy by thinning entries but cannot separate the
  losing months from the runner months because the shared basket regime produces both. Closed
  on EMA3_21's OWN trades (not by transfer from btc_filter), per the no-transfer discipline.
next_action: >
  EMA3_21_50_200 -> FREEZE: entry-vol (own autopsy), direction/long-only, exit-class,
  partial-exit, and now breadth-regime are all falsified on its own trades. The only remaining
  licensed lever is a genuinely NON-correlated mechanism (order-flow / open-interest /
  liquidation / cross-asset context) that needs data not in the repo -- an owner decision
  (acquire data) or a target/tolerance revisit, not another entry/exit/sizing/regime axis.
```
