# Signal/loss autopsy — EMA3_21_50_200, EMA3_13_50_200, BB_20_2_EMA200 (NO_TRAIL)

date: 2026-09-30
base: catalog5_trio autopsy blotters (this job's producing commit)
cohort: train1_entry=True

## EMA3_21_50_200

cohort n = 402 (of pooled closed trades)

### Executive answers

1. **Win/loss decomposition.** win_rate=19.7% (79 wins / 323 losses), avg_winner=22.84, avg_loser=-3.06, breakeven_win_rate_pct=11.804917690333966.
2. **Exit reason mix.** initial_sl 276 (69%), signal_reverse 117 (29%), end_of_data 9.
3. **Concentration.** 7/12 entry-months negative. calm_rate=0.432836.
4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl=1.71329, on signal_reverse=1.085323. forward_agreement wins=0.721519, losses=0.473684 (post-entry diagnostic, not an entry filter).
5. **Distinguishable at entry?** ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 autopsy (higher on stops).
6. **Concentration.** top-10 winners = 64.2% of gross wins; 4 highest-ranked trades (of 402) sum to the full pooled net PnL.

### Comparisons

| slice | n | net sum | mean | WR% |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 402 | +817.03 | +2.032 | 19.7% |
| wins | 79 | +1804.64 | +22.844 | 100.0% |
| losses | 323 | -987.61 | -3.058 | 0.0% |
| initial_sl | 276 | -916.34 | -3.320 | 0.0% |
| signal_reverse | 117 | +1554.18 | +13.284 | 59.8% |
| MFE >= p75 | 101 | +1689.67 | +16.729 | 67.3% |
| quick_reverse | 1 | -0.67 | -0.668 | 0.0% |

## EMA3_13_50_200

cohort n = 423 (of pooled closed trades)

### Executive answers

1. **Win/loss decomposition.** win_rate=18.9% (80 wins / 343 losses), avg_winner=22.76, avg_loser=-3.06, breakeven_win_rate_pct=11.84948940810371.
2. **Exit reason mix.** initial_sl 292 (69%), signal_reverse 122 (29%), end_of_data 9.
3. **Concentration.** 7/12 entry-months negative. calm_rate=0.43026.
4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl=1.766591, on signal_reverse=1.099284. forward_agreement wins=0.7, losses=0.489796 (post-entry diagnostic, not an entry filter).
5. **Distinguishable at entry?** ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 autopsy (higher on stops).
6. **Concentration.** top-10 winners = 63.8% of gross wins; 3 highest-ranked trades (of 423) sum to the full pooled net PnL.

### Comparisons

| slice | n | net sum | mean | WR% |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 423 | +771.28 | +1.823 | 18.9% |
| wins | 80 | +1820.53 | +22.757 | 100.0% |
| losses | 343 | -1049.24 | -3.059 | 0.0% |
| initial_sl | 292 | -969.45 | -3.320 | 0.0% |
| signal_reverse | 122 | +1560.93 | +12.794 | 58.2% |
| MFE >= p75 | 106 | +1692.03 | +15.963 | 65.1% |
| quick_reverse | 1 | -1.35 | -1.353 | 0.0% |

## BB_20_2_EMA200

cohort n = 756 (of pooled closed trades)

### Executive answers

1. **Win/loss decomposition.** win_rate=24.9% (188 wins / 568 losses), avg_winner=12.50, avg_loser=-2.67, breakeven_win_rate_pct=17.59163247261646.
2. **Exit reason mix.** initial_sl 358 (47%), signal_reverse 388 (51%), end_of_data 10.
3. **Concentration.** 7/12 entry-months negative. calm_rate=0.521164.
4. **Entry diagnostics (calm/ATR).** mean atr_pct on initial_sl=1.76226, on signal_reverse=1.079084. forward_agreement wins=0.723404, losses=0.401408 (post-entry diagnostic, not an entry filter).
5. **Distinguishable at entry?** ATR% separates initial_sl from signal_reverse similarly to the DONCHIAN_55 autopsy (higher on stops).
6. **Concentration.** top-10 winners = 50.7% of gross wins; 4 highest-ranked trades (of 756) sum to the full pooled net PnL.

### Comparisons

| slice | n | net sum | mean | WR% |
| --- | ---: | ---: | ---: | ---: |
| all Train-1 | 756 | +834.35 | +1.104 | 24.9% |
| wins | 188 | +2349.94 | +12.500 | 100.0% |
| losses | 568 | -1515.59 | -2.668 | 0.0% |
| initial_sl | 358 | -1188.62 | -3.320 | 0.0% |
| signal_reverse | 388 | +1813.23 | +4.673 | 45.9% |
| MFE >= p75 | 189 | +2238.10 | +11.842 | 83.1% |
| quick_reverse | 2 | -4.98 | -2.489 | 0.0% |

## Cross-name comparison (trio only)

| name | n | WR% | avg_winner | avg_loser | initial_sl share | loss months | calm_rate | top10 win share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA3_21_50_200 | 402 | 19.7% | 22.84 | -3.06 | 69% | 7/12 | 0.432836 | 64.2% |
| EMA3_13_50_200 | 423 | 18.9% | 22.76 | -3.06 | 69% | 7/12 | 0.43026 | 63.8% |
| BB_20_2_EMA200 | 756 | 24.9% | 12.50 | -2.67 | 47% | 7/12 | 0.521164 | 50.7% |

## Cross-name comparison vs EMA_50_200 / BB_20_25_EMA200 / DONCHIAN_55 (reference)

| name | n | WR% | avg_winner | avg_loser | initial_sl share | loss months | calm_rate | top10 win share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EMA3_21_50_200 | 402 | 19.7% | 22.84 | -3.06 | 69% | 7/12 | 0.432836 | 64.2% |
| EMA3_13_50_200 | 423 | 18.9% | 22.76 | -3.06 | 69% | 7/12 | 0.43026 | 63.8% |
| BB_20_2_EMA200 | 756 | 24.9% | 12.50 | -2.67 | 47% | 7/12 | 0.521164 | 50.7% |
| EMA_50_200 (ref) | 330 | 20.6% | 20.11 | -2.98 | 65% | 7/12 | 0.372727 | 70.8% |
| BB_20_25_EMA200 (ref) | 512 | 25.0% | 14.30 | -2.92 | 58% | 7/12 | 0.5 | 52.9% |
| DONCHIAN_55 (ref) | 447 | 27.5% | 12.76 | -3.08 | 62% | 7/12 | — | — |

**Hypothesis check (shared shape across all 5 catalog5 leads).** All three names in this autopsy show the same fat-tail structure already found in EMA_50_200, BB_20_25_EMA200, and DONCHIAN_55: avg_winner is several multiples of |avg_loser|, initial_sl exits dominate the loss side, and a small number of trades account for a disproportionate share of gross wins (top-10 winners ranked EMA3_21_50_200 (64.2%), EMA3_13_50_200 (63.8%), BB_20_2_EMA200 (50.7%)). No name in the trio shows a qualitatively different (non-fat-tail) edge mechanism at the trade level; the shape is consistent across all 5 catalog5 NO_TRAIL leads autopsied so far.

Artifacts: `trades/<name>_train1_trades.csv`, `monthly/<name>_monthly.csv`, `summary.json`.

