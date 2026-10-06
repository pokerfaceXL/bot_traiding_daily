# F011 T3 — forced-flow state-entry event study (5m, Train-1, non-trading)

Code: `forced_flow_lab/event_study.py`. Input: T2 states `output/f011_forced_flow/states/<SYMBOL>.csv.gz` + `close` from `frame_5m` (labelled rows only). No orders, positions, sizing or PnL.

## Method

- **Event = state entry**: first bar of a run in the side's state set (continuation: STRESS or CASCADE per side, so STRESS→CASCADE is one episode; exhaustion: EXHAUSTION per side).
- **Timing / look-ahead**: label at bar t is known at its close; forward return = close_{t+h}/close_t − 1. Events whose t+h is past the last labelled bar (2025-02-28 23:55 UTC) are dropped, never truncated.
- **Overlap policy**: per hypothesis × symbol × horizon, entries (long and short sides in one stream) are thinned greedily in time order: an entry is kept only if t ≥ previous kept t + h. `n_entries_raw` is the unthinned count; `n_events` is what the statistics use.
- **Signed return**: × predicted direction (continuation LONG side −1 / SHORT +1; exhaustion LONG +1 / SHORT −1), so positive = hypothesis direction.
- **Baseline**: unconditional forward return over every labelled bar of the same symbol with a complete window (overlapping), signed with the events' side mix.
- **Pass rule (§9)**: signed conditional mean > 0 AND excess mean over baseline > 34 bps (34 bps RT cost band) at the same horizon on **both** BTCUSDT and ETHUSDT, primary thresholds. The frozen one-at-a-time T2 grid is reported as robustness; it cannot create a pass on its own.
- **Cells tested**: 22 primary (continuation 5 horizons × 2 symbols + exhaustion 6 horizons × 2 symbols); 132 including the 5 frozen grid variants.

## Verdict

- **H-FORCEDFLOW-CONTINUATION-01: NO EDGE** — horizons passing on both symbols: none; cells beating the band across all 132: 0.
- **H-FORCEDFLOW-EXHAUSTION-01: NO EDGE** — horizons passing on both symbols: none; cells beating the band across all 132: 0.

## H-FORCEDFLOW-CONTINUATION-01 (primary thresholds; returns in bps, signed)

### BTCUSDT

| horizon | raw entries | n events | long-side | mean | base mean | excess mean | median | base median | hit rate | base hit | std | t | beats band |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m | 911 | 911 | 509 | +0.1 | -0.0 | +0.1 | -1.0 | -0.0 | 0.456 | 0.499 | 23.7 | +0.17 | no |
| 15m | 911 | 881 | 489 | -0.5 | -0.0 | -0.5 | -1.9 | -0.0 | 0.451 | 0.499 | 33.9 | -0.45 | no |
| 30m | 911 | 833 | 457 | -1.1 | -0.0 | -1.0 | -2.9 | -0.0 | 0.445 | 0.499 | 43.3 | -0.70 | no |
| 60m | 911 | 740 | 406 | -1.4 | -0.1 | -1.4 | -5.4 | -0.1 | 0.443 | 0.499 | 63.0 | -0.63 | no |
| 4h | 911 | 460 | 251 | -2.4 | -0.3 | -2.1 | -8.4 | -0.3 | 0.443 | 0.498 | 112.5 | -0.46 | no |

### ETHUSDT

| horizon | raw entries | n events | long-side | mean | base mean | excess mean | median | base median | hit rate | base hit | std | t | beats band |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m | 758 | 758 | 559 | -0.7 | -0.0 | -0.7 | -2.2 | -0.1 | 0.443 | 0.498 | 25.5 | -0.74 | no |
| 15m | 758 | 735 | 540 | -2.3 | -0.0 | -2.2 | -3.7 | -0.1 | 0.434 | 0.498 | 38.8 | -1.57 | no |
| 30m | 758 | 694 | 505 | -5.6 | -0.1 | -5.5 | -5.5 | -0.3 | 0.441 | 0.496 | 50.5 | -2.89 | no |
| 60m | 758 | 615 | 446 | -1.8 | -0.1 | -1.7 | -4.1 | -0.4 | 0.459 | 0.495 | 76.4 | -0.59 | no |
| 4h | 758 | 396 | 281 | -13.4 | -0.4 | -13.0 | -18.3 | -1.0 | 0.432 | 0.496 | 146.4 | -1.82 | no |

## H-FORCEDFLOW-EXHAUSTION-01 (primary thresholds; returns in bps, signed)

### BTCUSDT

| horizon | raw entries | n events | long-side | mean | base mean | excess mean | median | base median | hit rate | base hit | std | t | beats band |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m | 93 | 93 | 61 | -2.3 | +0.0 | -2.3 | +0.0 | +0.0 | 0.495 | 0.500 | 20.4 | -1.09 | no |
| 15m | 93 | 83 | 53 | -3.7 | +0.1 | -3.7 | +3.5 | +0.0 | 0.530 | 0.501 | 33.2 | -1.00 | no |
| 30m | 93 | 61 | 40 | -9.0 | +0.1 | -9.1 | +1.1 | +0.1 | 0.525 | 0.501 | 47.4 | -1.48 | no |
| 60m | 93 | 43 | 25 | -6.4 | +0.1 | -6.6 | -3.7 | +0.1 | 0.442 | 0.501 | 40.3 | -1.05 | no |
| 4h | 93 | 40 | 23 | +0.9 | +0.5 | +0.4 | +0.2 | +0.5 | 0.500 | 0.503 | 111.8 | +0.05 | no |
| 8h | 93 | 39 | 22 | +0.2 | +0.9 | -0.7 | +14.1 | +0.8 | 0.590 | 0.504 | 133.2 | +0.01 | no |

### ETHUSDT

| horizon | raw entries | n events | long-side | mean | base mean | excess mean | median | base median | hit rate | base hit | std | t | beats band |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5m | 90 | 90 | 82 | +2.2 | +0.0 | +2.2 | +4.1 | +0.1 | 0.567 | 0.503 | 24.5 | +0.86 | no |
| 15m | 90 | 82 | 74 | +6.8 | +0.0 | +6.8 | +8.3 | +0.2 | 0.646 | 0.503 | 40.5 | +1.52 | no |
| 30m | 90 | 65 | 58 | +2.7 | +0.1 | +2.6 | +4.5 | +0.4 | 0.585 | 0.506 | 46.3 | +0.47 | no |
| 60m | 90 | 41 | 37 | +6.1 | +0.2 | +5.9 | +17.7 | +0.8 | 0.659 | 0.508 | 64.4 | +0.61 | no |
| 4h | 90 | 39 | 35 | -7.5 | +0.7 | -8.2 | +8.9 | +1.8 | 0.513 | 0.508 | 119.9 | -0.39 | no |
| 8h | 90 | 38 | 34 | -65.6 | +1.4 | -67.0 | -35.8 | +3.3 | 0.421 | 0.511 | 179.4 | -2.26 | no |

## Robustness — excess mean (bps) over baseline per frozen grid variant (n events)

### H-FORCEDFLOW-CONTINUATION-01

| symbol | horizon | primary | exhaustion_impact_ratio=0.25 | fps_threshold=3.0 | fuel_percentile=0.99 | ofi_threshold=0.2 | stress_return_atr=2.5 |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5m | +0.1 (911) | +0.1 (911) | +1.0 (358) | +0.2 (909) | -0.1 (665) | +0.4 (283) |
| BTCUSDT | 15m | -0.5 (881) | -0.5 (881) | +0.6 (348) | -0.5 (881) | +0.6 (648) | +2.4 (273) |
| BTCUSDT | 30m | -1.0 (833) | -1.0 (833) | +1.8 (324) | -1.0 (834) | +0.2 (628) | +3.6 (265) |
| BTCUSDT | 60m | -1.4 (740) | -1.4 (740) | +3.3 (292) | -1.4 (740) | +0.8 (566) | +4.5 (250) |
| BTCUSDT | 4h | -2.1 (460) | -2.1 (460) | +1.2 (194) | -2.1 (460) | +2.3 (383) | +8.3 (211) |
| ETHUSDT | 5m | -0.7 (758) | -0.7 (758) | -2.0 (329) | -0.5 (755) | -0.7 (585) | -0.0 (211) |
| ETHUSDT | 15m | -2.2 (735) | -2.2 (735) | -4.4 (321) | -2.2 (734) | -2.8 (563) | -3.5 (209) |
| ETHUSDT | 30m | -5.5 (694) | -5.5 (694) | -7.3 (303) | -5.5 (694) | -7.1 (539) | -7.6 (204) |
| ETHUSDT | 60m | -1.7 (615) | -1.7 (615) | -4.2 (273) | -1.7 (615) | -3.7 (491) | -10.3 (196) |
| ETHUSDT | 4h | -13.0 (396) | -13.0 (396) | -23.4 (182) | -13.0 (396) | -14.4 (342) | -14.0 (170) |

### H-FORCEDFLOW-EXHAUSTION-01

| symbol | horizon | primary | exhaustion_impact_ratio=0.25 | fps_threshold=3.0 | fuel_percentile=0.99 | ofi_threshold=0.2 | stress_return_atr=2.5 |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 5m | -2.3 (93) | -2.9 (70) | -5.5 (33) | -0.4 (21) | -1.7 (73) | -3.5 (44) |
| BTCUSDT | 15m | -3.7 (83) | -4.5 (64) | -6.7 (30) | -0.0 (18) | -3.9 (64) | -7.5 (39) |
| BTCUSDT | 30m | -9.1 (61) | -6.3 (50) | -17.1 (22) | -13.1 (12) | -9.9 (48) | -17.7 (31) |
| BTCUSDT | 60m | -6.6 (43) | -0.8 (38) | -12.7 (14) | -13.9 (8) | -6.0 (34) | -20.3 (21) |
| BTCUSDT | 4h | +0.4 (40) | +3.3 (36) | -7.0 (13) | -60.9 (8) | +6.6 (31) | -15.4 (20) |
| BTCUSDT | 8h | -0.7 (39) | +1.0 (35) | -11.1 (13) | -86.2 (8) | +8.4 (30) | -36.4 (19) |
| ETHUSDT | 5m | +2.2 (90) | +0.2 (66) | +6.1 (55) | +3.7 (26) | +2.1 (84) | +1.7 (42) |
| ETHUSDT | 15m | +6.8 (82) | +2.6 (63) | +2.1 (48) | +3.0 (24) | +7.4 (76) | +5.9 (39) |
| ETHUSDT | 30m | +2.6 (65) | +2.1 (55) | +2.2 (39) | -0.6 (18) | +1.8 (60) | +7.4 (31) |
| ETHUSDT | 60m | +5.9 (41) | -0.6 (37) | +4.0 (24) | +12.3 (11) | +2.0 (38) | +20.4 (20) |
| ETHUSDT | 4h | -8.2 (39) | -8.0 (35) | +0.1 (22) | -20.9 (11) | -20.9 (36) | -13.5 (20) |
| ETHUSDT | 8h | -67.0 (38) | -67.7 (34) | -81.3 (21) | -5.1 (11) | -66.7 (35) | -70.1 (20) |

## Notes

- Largest excess mean in all 132 cells: +20.4 bps (H-FORCEDFLOW-EXHAUSTION-01, ETHUSDT, 60m, stress_return_atr=2.5, n=20) — below the 34 bps band.
- Caveat: Bybit liquidation columns are null for the whole Train-1 window, so CASCADE/EXHAUSTION use an OI/ATR fuel proxy plus taker flow (`ofi`, impacts) — not observed forced orders. Order-book depth is absent. This limits how sharply the states isolate forced flow; a null here is evidence about the proxy, not about liquidation-driven flow itself.
- Robustness variants share most events with the primary labelling; they are not independent tests.
