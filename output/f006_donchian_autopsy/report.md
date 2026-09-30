# Signal/loss autopsy — DONCHIAN_55_NO_TRAIL

date: 2026-09-30
base: control_on autopsy blotters on main (f925a47)
cohort: train1_entry=True (n=447 of 476 closed trades)

Artifacts: `donchian55_notrail_trades_train1.csv`, `donchian55_notrail_monthly.csv`

## Executive answers

1. **Are losses concentrated in regimes?** Partly. 7/12 entry-months are negative; bad months show high `initial_sl` share (often >60%) and basket-wide red, not a single-symbol crash. Available entry tags (`calm`, ATR percentile) do **not** cleanly isolate a “safe” regime — keeping calm entries destroys PnL.
2. **False breakouts?** Yes as the dominant loss engine: 275/447 `initial_sl` (all losses). Strict proxy MFE<1% & `initial_sl`: 103 trades (23%). But 67% of all losses had MFE>1% first — many are failed extensions, not instant failures.
3. **Distinguishable at entry (no look-ahead)?** Weakly. Absolute `atr_pct` averages ≈1.63 on `initial_sl` vs ≈1.05 on `signal_reverse`. `calm` / ATR-percentile / slow-trend agreement are **not** good gates (latter already falsified; calm keep removes runners). `forward_agreement` differs (wins 0.70 vs losses 0.36) but is a **post-entry** diagnostic — not an entry filter.
4. **Shared loss traits?** Almost always full initial stop (~−3.32), short hold vs winners, higher absolute ATR%, little directional asymmetry inside the stop cohort.
5. **Filter removing most losses vs big wins?** Filters that remove most stops (calm keep, trend confirm, TP) also remove or blunt the fat winners that create aggregate edge.
6. **Entry / exit / sizing / symbol / interval / allocation?** Primary defect: **entry selection** into stops, sitting on top of a strategy whose economics **require fat winners** under NO_TRAIL (already the best exit geometry found). Sizing and TP already falsified. Symbol/interval allocation secondary (XRP/DOGE help; SOL/240 hurts) — do not cherry-pick symbols as “the fix”.
7. **Did prior rejected filters target the same problem?** Yes — they tried to raise “entry quality” or regularity and repeatedly cut the fresh-breakout runners that are the edge.
8. **Next test justified?** Yes: one new axis that matches the stop-vs-runner split **without** reusing EMA-agreement or calm-percentile: absolute ATR% entry gate. If falsified → raise status toward FREEZE and document insufficiency before any new family.

## Cohort metrics

See strategy profile. Harness control mean `train1_net_pnl` = **+58.3870526**.

## Comparisons requested

| slice | n | net sum | mean | WR |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 447 | +570.21 | +1.276 | 27.5% |
| wins | 123 | +1569.74 | +12.76 | 100% |
| losses | 324 | −999.53 | −3.085 | 0% |
| initial_sl | 275 | −913.02 | −3.320 | 0% |
| signal_reverse | 168 | +1440.53 | +8.575 | 70.8% |
| MFE ≥ p75 | 112 | +1496.29 | +13.36 | 87.5% |
| quick_reverse | 0 | — | — | — |

Monthly and per-series tables: CSV artifacts + profile.

## Counterfactual entry-known filters (diagnostic only)

| keep rule | n | net | mean | big winners (≥10) removed |
| --- | ---: | ---: | ---: | --- |
| calm=True | 225 | +22.3 | +0.10 | 20/36 (PnL removed ≈819) |
| atr_pctile>0.5 | 222 | +547.9 | +2.47 | 16/36 |
| atr_pct≤median | 224 | +378.4 | +1.69 | 16/36 |
| long only | 219 | +595.7 | +2.72 | 19/36 |
| interval=60 | 352 | +391.8 | +1.11 | 8/36 |

## One hypothesis (only)

See `spec/research/F006-hypothesis-donchian-abs-atr-entry-gate.md` (to be landed by limen) / draft below in coordinator workspace.
