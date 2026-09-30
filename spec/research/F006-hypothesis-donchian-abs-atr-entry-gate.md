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

## Result

Train-1 only; all five pre-registered thresholds evaluated on the full frozen 5×2 basket (50 candidate runs + 10 control runs). The forced-off gate reproduced all 10 control rows exactly, including mean train1_net_pnl **+58.3870526**. The median of the 447 control Train-1 entries' ATR% was **1.1600820232399194%**, written to `output/f006_donchian_abs_atr_gate/grid_freeze.json` before any gated result. `number_of_trials = 5`; no grid extension.

| T (%) | Mean train1_net_pnl | Pooled entry net | Net / entry | Entries / series | initial_sl share | Drop (pp) | Big-winner PnL retained | Losing entry-months | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Ungated control | +58.387053 | +570.205729 | +1.275628 | 44.7 | 61.5213% | — | 100% | 7/12 | control |
| Median: 1.1600820232399194 | +38.956993 | +378.371159 | +1.689157 | 22.4 | 47.7679% | 13.7534 | 48.1984% | 6/12 | no |
| 1.0 | +29.961843 | +297.386136 | +1.625061 | 18.3 | 44.8087% | 16.7125 | 37.5131% | 7/12 | no |
| 1.25 | +36.310822 | +344.740646 | +1.384501 | 24.9 | 49.7992% | 11.7221 | 48.1984% | 5/12 | no |
| 1.5 | +31.783318 | +304.202733 | +1.024252 | 29.7 | 52.8620% | 8.6593 | 51.2706% | 7/12 | no |
| 2.0 | +60.301989 | +588.653341 | +1.603960 | 36.7 | 56.1308% | 5.3905 | 83.4489% | 7/12 | no |

PnL in the primary column uses the unchanged harness's daily Train-1 equity changes; pooled entry net, stop shares, counts, and months use trades entered in `[2024-03-01, 2025-03-01)` UTC. Those two PnL cohorts are deliberately not conflated. The 36 baseline big winners sum to +1218.439488; retention matches symbol/interval/entry timestamp/direction, with identical exit timestamp, reason, and net PnL verified. No candidate is thin on the pre-declared basket-mean criterion, including zero-trade series in the denominator.

ATR uses `100 * SMA(true_range, 14) / close` on the closed signal bar, matching the autopsy's one-bar-shifted feature at the next-open fill. The gate intersects the original one-shot mask, never changes the persistent signal used for exits, and cannot defer a rejected breakout until volatility falls. All 60 runs retained NO_TRAIL; no trailing/TP exits or retained-trade economics mismatches occurred.

Artifacts: `output/f006_donchian_abs_atr_gate/results.csv` (all 60 series rows), `cell_summary.csv`, `manifest.json`, `grid_freeze.json`, each cell's `summary.json`, raw monthly summaries and blotters, and `run.log`. Reproduction: `python3 scripts/f006_donchian_abs_atr_gate.py` with the checksum-locked Train-1 cache. Implementation source commit: `e15b2ba`; source and data hashes are in the manifest.

## Decision

**FALSIFIED; DONCHIAN_55_NO_TRAIL: CONDITIONAL → FREEZE.** Zero of five thresholds meets all four requirements. At the best PnL threshold (2.0%), the +1.914936 mean improvement and 83.45% big-winner retention do not compensate for a stop-share reduction of only 5.39pp. The three thresholds that reduce stop share by at least 10pp lose more than half of baseline big-winner PnL and lower mean PnL. Monthly concentration remains unresolved (best-PnL cell still has 7/12 losing entry-months). No threshold selected for validation; no validation/holdout loaded, no new family started, and no widening without a new written non-correlated mechanism justification (§13).
