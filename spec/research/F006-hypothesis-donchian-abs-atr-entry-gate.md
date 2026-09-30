# H-DONCHIAN-ABS-ATR-ENTRY-GATE-01

```text
Observation:
DONCHIAN_55_NO_TRAIL on Train-1 is aggregate-positive (harness mean train1_net_pnl +58.387; blotter train1_entry n=447 net ≈ +570), but 275/447 trades die at initial_sl (sum ≈ −913, WR 0%) while 168 signal_reverse exits produce nearly all profits (WR ≈ 71%, sum ≈ +1441). Without 2024-11 the pooled net flips negative (≈ −110). Absolute atr_pct at entry averages ≈1.63 on initial_sl vs ≈1.05 on signal_reverse. Prior “quality” gates (EMA trend confirm, calm/low ATR-percentile keep, TP) remove or blunt the same runners that create the edge.

Problem:
Most trades are capped stop-outs; aggregate edge depends on rare channel runners. We lack an entry-time rule that reduces stop-outs without cutting those runners. Monthly regularity remains failed (7/12 losing entry-months).

Mechanism:
Noisy breakouts that fail into the initial stop tend to fire when absolute ATR% is elevated, whereas breakouts that later travel to the opposite Donchian extreme more often begin at lower absolute ATR%. This is distinct from ATR *percentile*/calm (already harmful if used as a keep-calm rule) and from slow EMA agreement (already falsified).

Hypothesis:
Adding a single causal entry gate that rejects a DONCHIAN_55 breakout when ATR%(14) on the signal bar exceeds a pre-registered threshold will raise mean Train-1 net PnL across the 10-series basket versus the ungated NO_TRAIL baseline and cut the initial_sl share among remaining trades, without requiring trend agreement and without using post-entry tags.

Change to test:
One entry refinement only: `atr_pct <= T` required to take the Donchian signal (else flat). No exit, sizing, symbol, or interval changes. NO_TRAIL unchanged.

Baseline:
Ungated DONCHIAN_55_NO_TRAIL harness control — mean train1_net_pnl +58.3870526 on the frozen 5×2 basket; same costs/one-shot/mask.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary)
2. pooled net PnL and net/trade
3. initial_sl share among closed trades
4. n_trades (must not collapse to thin sample: reject if mean n_trades/series < 10)
5. count of losing Train-1 months (pooled entry-month table) — informational, not sole pass
6. fraction of baseline “big winners” (net_pnl≥10 on ungated blotter) retained
7. number_of_trials counted (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down by ≥10 percentage points AND ≥50% of big-winner PnL retained.

Falsification condition:
Any of: mean train1_net_pnl ≤ baseline at every T; or every non-thin T removes >50% of baseline big-winner PnL; or initial_sl share fails to fall ≥10pp at the best T; or improvement is only from collapsing to <10 trades/series. Do not widen T after seeing results without a new written hypothesis.

Data split:
Development = Train 1 only (same freeze as control_on autopsy). No validation/holdout peek. If a T looks promising, schedule a separate validation run later — do not tune on it now.

Budget:
T grid fixed before run: {median_train1_atr_pct_of_entries, 1.0%, 1.25%, 1.5%, 2.0%} — max 5 trials. Report all cells. Pick at most one T for any follow-up.
```

decision_if_pass: REFINE (write new profile metrics; consider validation)
decision_if_fail: FREEZE or CONDITIONAL→FREEZE for DONCHIAN_55_NO_TRAIL pending a non-correlated mechanism justification (§13)
