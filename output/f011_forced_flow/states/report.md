# F011 T2 — forced-flow states on the 5m frame (Train-1, non-trading)

Labeller: `forced_flow_lab/label_states.py`. Frozen rules: `manifest.json` (committed 7e5af5e, before any labelling run).
Rows: every non-warmup 5m bar (113,184 per symbol). Venue: Bybit only in rules; `bn_doi_w` is a separate cross-check column.
Files `<SYMBOL>.csv.gz` hold state + triggering values only (no OHLCV/frame copy). No forward returns, PnL, or trades.

## State counts and median duration (primary thresholds)

### BTCUSDT

| state | bars | share | runs | median duration | max run |
|---|---:|---:|---:|---:|---:|
| NORMAL | 83209 | 73.517% | 746 | 5.0 bars (25 min) | 3509 |
| LONG_CROWDING | 15842 | 13.997% | 773 | 11.0 bars (55 min) | 138 |
| SHORT_CROWDING | 12714 | 11.233% | 652 | 11.0 bars (55 min) | 159 |
| LONG_STRESS | 714 | 0.631% | 498 | 1.0 bars (5 min) | 6 |
| SHORT_STRESS | 543 | 0.480% | 393 | 1.0 bars (5 min) | 5 |
| LONG_LIQUIDATION_CASCADE | 27 | 0.024% | 27 | 1.0 bars (5 min) | 1 |
| SHORT_LIQUIDATION_CASCADE | 19 | 0.017% | 19 | 1.0 bars (5 min) | 1 |
| LONG_EXHAUSTION | 72 | 0.064% | 61 | 1.0 bars (5 min) | 2 |
| SHORT_EXHAUSTION | 44 | 0.039% | 32 | 1.0 bars (5 min) | 3 |

- Binance OI also fell over the stress window on 64.6% of 1303 stress/cascade bars (separate venue, not merged).
- `long_short_ratio` z-score agreed with the FPS crowd side on 43.1% of crowding bars.

### ETHUSDT

| state | bars | share | runs | median duration | max run |
|---|---:|---:|---:|---:|---:|
| NORMAL | 85768 | 75.777% | 621 | 6.0 bars (30 min) | 3136 |
| LONG_CROWDING | 17566 | 15.520% | 803 | 11.0 bars (55 min) | 200 |
| SHORT_CROWDING | 8630 | 7.625% | 382 | 12.0 bars (60 min) | 185 |
| LONG_STRESS | 811 | 0.717% | 545 | 1.0 bars (5 min) | 5 |
| SHORT_STRESS | 258 | 0.228% | 199 | 1.0 bars (5 min) | 4 |
| LONG_LIQUIDATION_CASCADE | 42 | 0.037% | 41 | 1.0 bars (5 min) | 2 |
| SHORT_LIQUIDATION_CASCADE | 4 | 0.004% | 4 | 1.0 bars (5 min) | 1 |
| LONG_EXHAUSTION | 95 | 0.084% | 82 | 1.0 bars (5 min) | 3 |
| SHORT_EXHAUSTION | 10 | 0.009% | 8 | 1.0 bars (5 min) | 2 |

- Binance OI also fell over the stress window on 69.0% of 1114 stress/cascade bars (separate venue, not merged).
- `long_short_ratio` z-score agreed with the FPS crowd side on 41.1% of crowding bars.

## One-at-a-time robustness grid (counts only; primary output unchanged)

### BTCUSDT

| variant | LONG CROWDING | SHORT CROWDING | LONG STRESS | SHORT STRESS | LONG CASCADE | SHORT CASCADE | LONG EXHAUSTION | SHORT EXHAUSTION |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| primary | 15842 | 12714 | 714 | 543 | 27 | 19 | 72 | 44 |
| fps_threshold=3.0 | 6282 | 3989 | 312 | 190 | 14 | 2 | 36 | 3 |
| stress_return_atr=2.5 | 16281 | 13073 | 212 | 159 | 15 | 8 | 37 | 19 |
| ofi_threshold=0.2 | 16027 | 12864 | 479 | 373 | 21 | 15 | 56 | 35 |
| fuel_percentile=0.99 | 15872 | 12730 | 748 | 566 | 5 | 3 | 16 | 12 |
| exhaustion_impact_ratio=0.25 | 15851 | 12722 | 717 | 544 | 27 | 19 | 54 | 28 |

### ETHUSDT

| variant | LONG CROWDING | SHORT CROWDING | LONG STRESS | SHORT STRESS | LONG CASCADE | SHORT CASCADE | LONG EXHAUSTION | SHORT EXHAUSTION |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| primary | 17566 | 8630 | 811 | 258 | 42 | 4 | 95 | 10 |
| fps_threshold=3.0 | 7960 | 3101 | 378 | 87 | 25 | 2 | 64 | 3 |
| stress_return_atr=2.5 | 18149 | 8774 | 200 | 72 | 18 | 2 | 46 | 4 |
| ofi_threshold=0.2 | 17756 | 8704 | 600 | 163 | 40 | 3 | 87 | 8 |
| fuel_percentile=0.99 | 17610 | 8633 | 854 | 263 | 10 | 1 | 26 | 1 |
| exhaustion_impact_ratio=0.25 | 17584 | 8630 | 815 | 258 | 42 | 4 | 67 | 9 |

## Findings (reported, not tuned away)

- Cascades are rare: BTC 27 long / 19 short, ETH 42 long / **4 short** in ~13 months of 5m bars; at `fuel_percentile=0.99` ETH short cascade drops to 1 and short exhaustion to 1. Without liquidation data the OI/ATR fuel proxy plus taker flow seldom co-fires with a crowded side.
- Stress, cascade and exhaustion are 1-bar events (median 5 min; stress max 4–6 bars). Crowding is a slow regime (median ~55–60 min, max 11–17 h), consistent with the 8h funding component.
- Exhaustion outnumbers cascade because it can fire on several bars within 12 bars after one cascade.
- ETH is long-skewed: long-side crowding/stress/cascade dominate short-side counts; BTC is closer to balanced.
- `long_short_ratio` (account share) agrees with the OI+funding crowd side on only ~41–43% of crowding bars — it is not a confirmation of FPS on this sample and stays out of the rules.
- Binance OI direction agrees with Bybit's falling OI on 65% (BTC) / 69% (ETH) of stress/cascade bars, slightly above the 52–60% unconditional agreement; one-third of Bybit stress events are not echoed on Binance.
- Before bar 2,029 `fuel_pct` is NaN (fuel needs 14 ATR bars + 2,016-bar rank window), so cascades cannot fire on the first 13 labelled bars (documented missing-value rule).
