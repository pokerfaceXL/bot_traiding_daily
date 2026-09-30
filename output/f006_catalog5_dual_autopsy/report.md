# Signal/loss autopsy — EMA_50_200 and BB_20_25_EMA200 (NO_TRAIL)

date: 2026-09-30
base: catalog5_ema_bb autopsy blotters (this job's producing commit)
cohort: train1_entry=True

## EMA_50_200

cohort n = 330 (of pooled closed trades)

### Executive answers

1. **Win/loss decomposition.** win_rate=20.6% (68 wins / 262 losses), avg_winner=20.11, avg_loser=-2.98, breakeven_win_rate_pct=12.896784386880883.
2. **Exit reason mix.** initial_sl 213 (65%), signal_reverse 112 (34%), end_of_data 5.
3. **Concentration.** 7/12 entry-months negative. calm_rate=0.372727.
4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl=1.746539, on signal_reverse=1.059194. forward_agreement wins=0.735294, losses=0.477099 (post-entry diagnostic, not an entry filter).
5. **Distinguishable at entry?** ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 autopsy (higher on stops).
6. **Concentration.** top-10 winners = 70.8% of gross wins; 2 highest-ranked trades (of 330) sum to the full pooled net PnL.

### Comparisons

| slice | n | net sum | mean | WR% |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 330 | +587.39 | +1.780 | 20.6% |
| wins | 68 | +1367.54 | +20.111 | 100.0% |
| losses | 262 | -780.15 | -2.978 | 0.0% |
| initial_sl | 213 | -707.11 | -3.320 | 0.0% |
| signal_reverse | 112 | +1217.11 | +10.867 | 56.2% |
| MFE >= p75 | 83 | +1264.58 | +15.236 | 66.3% |
| quick_reverse | 11 | -16.15 | -1.468 | 0.0% |

## BB_20_25_EMA200

cohort n = 512 (of pooled closed trades)

### Executive answers

1. **Win/loss decomposition.** win_rate=25.0% (128 wins / 384 losses), avg_winner=14.30, avg_loser=-2.92, breakeven_win_rate_pct=16.946025509246144.
2. **Exit reason mix.** initial_sl 297 (58%), signal_reverse 205 (40%), end_of_data 10.
3. **Concentration.** 7/12 entry-months negative. calm_rate=0.5.
4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl=1.703431, on signal_reverse=1.064983. forward_agreement wins=0.804688, losses=0.445312 (post-entry diagnostic, not an entry filter).
5. **Distinguishable at entry?** ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 autopsy (higher on stops).
6. **Concentration.** top-10 winners = 52.9% of gross wins; 4 highest-ranked trades (of 512) sum to the full pooled net PnL.

### Comparisons

| slice | n | net sum | mean | WR% |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 512 | +709.85 | +1.386 | 25.0% |
| wins | 128 | +1830.02 | +14.297 | 100.0% |
| losses | 384 | -1120.17 | -2.917 | 0.0% |
| initial_sl | 297 | -986.01 | -3.320 | 0.0% |
| signal_reverse | 205 | +1532.48 | +7.475 | 57.6% |
| MFE >= p75 | 128 | +1724.02 | +13.469 | 78.9% |
| quick_reverse | 0 | — | — | — |

## Cross-name comparison

| name | n | WR% | avg_winner | avg_loser | initial_sl share | loss months | calm_rate | top10 win share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA_50_200 | 330 | 20.6% | 20.11 | -2.98 | 65% | 7/12 | 0.372727 | 70.8% |
| BB_20_25_EMA200 | 512 | 25.0% | 14.30 | -2.92 | 58% | 7/12 | 0.5 | 52.9% |

**Hypothesis check (concentration vs regularity).** EMA_50_200 is the more top-heavy of the two (top-10 winners = 70.8% of gross wins vs BB_20_25_EMA200's 52.9%), matching the profiles' a priori ranking. Both names remain fat-tail dependent: avg_winner is 5-7x |avg_loser| and initial_sl exits are the dominant loss engine for both, the same shape already found for DONCHIAN_55_NO_TRAIL. Neither name shows a qualitatively different (non-fat-tail) edge mechanism at the trade level.

Artifacts: `trades/<name>_train1_trades.csv`, `monthly/<name>_monthly.csv`, `summary.json`.

