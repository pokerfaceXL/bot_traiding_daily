# F011 T4 — forced-flow diagnostics (5m, Train-1, non-trading)

Code: `forced_flow_lab/diagnostics.py` (method in its docstring). Seeds and gates: `manifest.json`. Verdicts and counts: `verdict.json`. Inputs: frozen T2 states + `frame_5m`, BTCUSDT + ETHUSDT, Train-1 labelled rows only (2024-02-02 → 2025-02-28); halves split at the labelled-bar midpoint.

## Verdicts

- **H-FORCEDFLOW-DIAG-MAGNITUDE-01: NEGATIVE**
- **H-FORCEDFLOW-DIAG-CONTINUATION-SPLIT-01: NEGATIVE**
- **H-FORCEDFLOW-DIAG-PRECASCADE-01: NEGATIVE**
- **Recommendation (program note): ARCHIVE**

Tests: 3. Cells: 1194 total (Test 1 450, Test 2 696, Test 3 48); gate cells 222 (Test 1 100 = 5 classes × 5 horizons × 2 symbols × 2 halves, pooled sides, each checked on |ret| and fwd vol; Test 2 116 = 29 features × 2 symbols × 2 halves, CASCADE +1h; Test 3 6 = 3 horizons × 2 symbols, logistic OOS).

## Test 1 — magnitude / vol vs matched baseline (pooled sides)

Ratio event/baseline of mean |return| and of mean forward realized vol (RMS of 5m log returns over t+1..t+h); [95% event-level bootstrap CI]. Gate: ratio ≥ 1.25 and CI lo > 1 in all four symbol × half cells. Full per-side / per-half / all-metric table: `test1_magnitude.csv.gz`.

| class | horizon | metric | BTC H1 | BTC H2 | ETH H1 | ETH H2 | BTC full n | ETH full n | BTC mean |r| bps | ETH mean |r| bps |
|---|---|---|---|---|---|---|---:|---:|---:|---:|
| CROWDING | 5m | abs_ret | 1.14 [1.05, 1.24] | 1.07 [0.99, 1.15] | 1.08 [0.99, 1.18] | 1.08 [1.00, 1.16] | 1425 | 1185 | 11.8 | 14.8 |
| CROWDING | 5m | fwd_rv | 1.14 [1.05, 1.24] | 1.07 [0.99, 1.15] | 1.08 [0.99, 1.18] | 1.08 [1.00, 1.16] | 1425 | 1185 | 11.8 | 14.8 |
| CROWDING | 15m | abs_ret | 1.14 [1.05, 1.23] | 1.11 [1.02, 1.20] | 0.99 [0.90, 1.08] | 0.98 [0.91, 1.06] | 1357 | 1114 | 20.2 | 23.5 |
| CROWDING | 15m | fwd_rv | 1.13 [1.06, 1.20] | 1.12 [1.05, 1.19] | 1.01 [0.95, 1.07] | 1.04 [0.98, 1.10] | 1357 | 1114 | 20.2 | 23.5 |
| CROWDING | 30m | abs_ret | 1.14 [1.04, 1.24] | 1.04 [0.94, 1.13] | 0.96 [0.87, 1.05] | 0.97 [0.89, 1.05] | 1223 | 1017 | 27.1 | 32.2 |
| CROWDING | 30m | fwd_rv | 1.13 [1.07, 1.19] | 1.08 [1.02, 1.14] | 1.01 [0.95, 1.06] | 1.04 [0.99, 1.09] | 1223 | 1017 | 27.1 | 32.2 |
| CROWDING | 1h | abs_ret | 1.09 [0.99, 1.20] | 1.08 [0.97, 1.19] | 1.03 [0.91, 1.15] | 1.02 [0.92, 1.13] | 1034 | 868 | 38.2 | 47.3 |
| CROWDING | 1h | fwd_rv | 1.10 [1.05, 1.16] | 1.07 [1.01, 1.13] | 1.01 [0.95, 1.06] | 1.06 [1.00, 1.13] | 1034 | 868 | 38.2 | 47.3 |
| CROWDING | 4h | abs_ret | 1.19 [1.05, 1.35] | 1.16 [1.02, 1.31] | 1.03 [0.90, 1.19] | 1.08 [0.95, 1.23] | 559 | 508 | 81.0 | 100.4 |
| CROWDING | 4h | fwd_rv | 1.07 [1.02, 1.13] | 1.08 [1.02, 1.14] | 0.97 [0.92, 1.03] | 1.05 [0.99, 1.12] | 559 | 508 | 81.0 | 100.4 |
| STRESS | 5m | abs_ret | 1.17 [1.06, 1.28] | 1.42 [1.23, 1.66] | 1.21 [1.07, 1.37] | 1.24 [1.11, 1.38] | 891 | 744 | 13.2 | 16.7 |
| STRESS | 5m | fwd_rv | 1.17 [1.06, 1.28] | 1.42 [1.23, 1.67] | 1.21 [1.07, 1.37] | 1.24 [1.11, 1.38] | 891 | 744 | 13.2 | 16.7 |
| STRESS | 15m | abs_ret | 1.19 [1.06, 1.33] | 1.16 [1.03, 1.30] | 1.07 [0.95, 1.20] | 1.09 [0.98, 1.22] | 863 | 721 | 20.5 | 25.9 |
| STRESS | 15m | fwd_rv | 1.22 [1.13, 1.31] | 1.26 [1.14, 1.40] | 1.10 [1.02, 1.19] | 1.18 [1.09, 1.28] | 863 | 721 | 20.5 | 25.9 |
| STRESS | 30m | abs_ret | 1.15 [1.03, 1.29] | 1.12 [1.01, 1.25] | 1.01 [0.89, 1.13] | 1.08 [0.98, 1.19] | 820 | 683 | 27.8 | 34.9 |
| STRESS | 30m | fwd_rv | 1.16 [1.09, 1.25] | 1.17 [1.08, 1.28] | 1.03 [0.96, 1.10] | 1.10 [1.03, 1.17] | 820 | 683 | 27.8 | 34.9 |
| STRESS | 1h | abs_ret | 1.20 [1.06, 1.35] | 1.08 [0.94, 1.22] | 1.02 [0.87, 1.18] | 1.11 [0.99, 1.25] | 727 | 604 | 39.3 | 49.6 |
| STRESS | 1h | fwd_rv | 1.14 [1.08, 1.21] | 1.10 [1.02, 1.19] | 1.04 [0.96, 1.12] | 1.07 [1.01, 1.15] | 727 | 604 | 39.3 | 49.6 |
| STRESS | 4h | abs_ret | 1.14 [0.99, 1.32] | 1.10 [0.97, 1.23] | 1.08 [0.94, 1.22] | 1.10 [0.94, 1.26] | 454 | 390 | 78.0 | 101.2 |
| STRESS | 4h | fwd_rv | 1.07 [1.00, 1.13] | 1.06 [1.00, 1.13] | 0.98 [0.92, 1.04] | 1.07 [0.99, 1.15] | 454 | 390 | 78.0 | 101.2 |
| DELEVERAGING | 5m | abs_ret | 1.17 [1.06, 1.28] | 1.39 [1.21, 1.63] | 1.19 [1.06, 1.34] | 1.26 [1.14, 1.40] | 911 | 758 | 13.2 | 16.8 |
| DELEVERAGING | 5m | fwd_rv | 1.17 [1.06, 1.28] | 1.39 [1.21, 1.64] | 1.19 [1.06, 1.34] | 1.26 [1.14, 1.40] | 911 | 758 | 13.2 | 16.8 |
| DELEVERAGING | 15m | abs_ret | 1.22 [1.10, 1.36] | 1.16 [1.03, 1.29] | 1.05 [0.93, 1.17] | 1.14 [1.02, 1.26] | 881 | 735 | 20.9 | 25.8 |
| DELEVERAGING | 15m | fwd_rv | 1.23 [1.14, 1.32] | 1.24 [1.12, 1.37] | 1.10 [1.02, 1.18] | 1.20 [1.11, 1.29] | 881 | 735 | 20.9 | 25.8 |
| DELEVERAGING | 30m | abs_ret | 1.17 [1.05, 1.30] | 1.11 [1.00, 1.23] | 1.00 [0.87, 1.13] | 1.08 [0.98, 1.19] | 833 | 694 | 28.0 | 34.7 |
| DELEVERAGING | 30m | fwd_rv | 1.16 [1.09, 1.24] | 1.16 [1.07, 1.25] | 1.03 [0.96, 1.10] | 1.11 [1.05, 1.18] | 833 | 694 | 28.0 | 34.7 |
| DELEVERAGING | 1h | abs_ret | 1.18 [1.04, 1.32] | 1.08 [0.95, 1.22] | 1.04 [0.90, 1.19] | 1.07 [0.96, 1.19] | 740 | 615 | 39.4 | 49.5 |
| DELEVERAGING | 1h | fwd_rv | 1.14 [1.07, 1.20] | 1.10 [1.02, 1.18] | 1.05 [0.98, 1.12] | 1.06 [1.00, 1.13] | 740 | 615 | 39.4 | 49.5 |
| DELEVERAGING | 4h | abs_ret | 1.12 [0.97, 1.29] | 1.12 [0.98, 1.25] | 1.05 [0.90, 1.21] | 1.12 [0.96, 1.30] | 460 | 396 | 77.6 | 100.1 |
| DELEVERAGING | 4h | fwd_rv | 1.06 [0.99, 1.12] | 1.05 [0.98, 1.12] | 0.96 [0.90, 1.03] | 1.07 [1.00, 1.14] | 460 | 396 | 77.6 | 100.1 |
| CASCADE | 5m | abs_ret | 1.37 [0.92, 1.91] | 0.97 [0.65, 1.38] | 1.41 [1.00, 1.92] | 1.25 [0.76, 1.80] | 46 | 45 | 13.4 | 20.4 |
| CASCADE | 5m | fwd_rv | 1.37 [0.92, 1.91] | 0.97 [0.65, 1.38] | 1.41 [0.99, 1.92] | 1.25 [0.76, 1.80] | 46 | 45 | 13.4 | 20.4 |
| CASCADE | 15m | abs_ret | 1.66 [1.13, 2.25] | 0.94 [0.56, 1.45] | 1.18 [0.81, 1.59] | 0.97 [0.59, 1.53] | 46 | 44 | 24.6 | 26.2 |
| CASCADE | 15m | fwd_rv | 1.60 [1.22, 1.99] | 1.01 [0.77, 1.35] | 1.32 [1.09, 1.55] | 1.29 [1.04, 1.52] | 46 | 44 | 24.6 | 26.2 |
| CASCADE | 30m | abs_ret | 1.37 [0.95, 1.80] | 0.98 [0.63, 1.39] | 0.84 [0.50, 1.26] | 1.07 [0.66, 1.59] | 46 | 44 | 31.8 | 31.9 |
| CASCADE | 30m | fwd_rv | 1.47 [1.13, 1.85] | 1.00 [0.80, 1.21] | 1.22 [1.03, 1.40] | 1.18 [0.94, 1.42] | 46 | 44 | 31.8 | 31.9 |
| CASCADE | 1h | abs_ret | 0.91 [0.65, 1.20] | 0.97 [0.59, 1.45] | 0.96 [0.67, 1.31] | 0.87 [0.56, 1.28] | 45 | 43 | 33.5 | 43.2 |
| CASCADE | 1h | fwd_rv | 1.46 [1.13, 1.83] | 1.00 [0.83, 1.18] | 1.21 [1.01, 1.42] | 1.10 [0.87, 1.36] | 45 | 43 | 33.5 | 43.2 |
| CASCADE | 4h | abs_ret | 0.95 [0.58, 1.35] | 1.39 [0.95, 2.03] | 0.76 [0.45, 1.14] | 0.99 [0.66, 1.40] | 42 | 41 | 80.3 | 83.6 |
| CASCADE | 4h | fwd_rv | 1.19 [0.96, 1.47] | 0.94 [0.81, 1.08] | 1.01 [0.88, 1.14] | 0.96 [0.81, 1.13] | 42 | 41 | 80.3 | 83.6 |
| EXHAUSTION | 5m | abs_ret | 1.39 [0.97, 1.88] | 0.94 [0.67, 1.24] | 1.34 [1.04, 1.66] | 1.23 [0.95, 1.54] | 93 | 90 | 12.3 | 17.9 |
| EXHAUSTION | 5m | fwd_rv | 1.39 [0.97, 1.88] | 0.94 [0.67, 1.24] | 1.34 [1.04, 1.66] | 1.23 [0.95, 1.54] | 93 | 90 | 12.3 | 17.9 |
| EXHAUSTION | 15m | abs_ret | 1.43 [1.05, 1.86] | 0.87 [0.66, 1.12] | 1.07 [0.80, 1.39] | 1.21 [0.82, 1.67] | 83 | 82 | 21.8 | 27.6 |
| EXHAUSTION | 15m | fwd_rv | 1.48 [1.10, 1.90] | 0.91 [0.72, 1.10] | 1.14 [0.95, 1.33] | 1.28 [1.00, 1.59] | 83 | 82 | 21.8 | 27.6 |
| EXHAUSTION | 30m | abs_ret | 1.41 [0.96, 1.86] | 0.75 [0.53, 0.98] | 0.86 [0.59, 1.21] | 1.14 [0.81, 1.49] | 61 | 65 | 30.4 | 33.5 |
| EXHAUSTION | 30m | fwd_rv | 1.31 [1.04, 1.63] | 0.93 [0.77, 1.11] | 1.11 [0.92, 1.32] | 1.12 [0.92, 1.36] | 61 | 65 | 30.4 | 33.5 |
| EXHAUSTION | 1h | abs_ret | 0.81 [0.55, 1.12] | 0.60 [0.30, 1.05] | 1.03 [0.63, 1.48] | 1.22 [0.84, 1.74] | 43 | 41 | 27.0 | 48.9 |
| EXHAUSTION | 1h | fwd_rv | 1.44 [1.08, 1.93] | 0.92 [0.75, 1.10] | 1.23 [1.02, 1.50] | 1.16 [0.93, 1.42] | 43 | 41 | 27.0 | 48.9 |
| EXHAUSTION | 4h | abs_ret | 0.86 [0.55, 1.20] | 1.27 [0.84, 1.78] | 0.95 [0.56, 1.36] | 0.98 [0.71, 1.28] | 40 | 39 | 80.0 | 92.3 |
| EXHAUSTION | 4h | fwd_rv | 1.15 [0.94, 1.38] | 0.94 [0.80, 1.07] | 1.03 [0.91, 1.15] | 0.94 [0.81, 1.09] | 40 | 39 | 80.0 | 92.3 |

Cost context (34 bps RT): mean |return| reaches the band only at +4h (≈ 78–101 bps for every class), where the matched baseline is of the same size; event-specific magnitude never dwarfs costs.

## Test 2 — CASCADE continuation vs reversal (+1h outcome; gating)

Effect = Cliff's δ (continuous; continuation vs reversal) or risk difference P(cont|X=1) − P(cont|X=0) (categorical, one-vs-rest). `*` = |effect| ≥ gate and 95% CI excludes 0. Group n per cell and +30m / DELEVERAGING tables: `test2_continuation_split.csv.gz`.

Group n (cont / rev): BTCUSDT full 27/18; BTCUSDT H1 14/14; BTCUSDT H2 13/4; ETHUSDT full 14/29; ETHUSDT H1 7/14; ETHUSDT H2 7/15.

| feature | kind | BTC H1 | BTC H2 | ETH H1 | ETH H2 | BTC full | ETH full |
|---|---|---:|---:|---:|---:|---:|---:|
| oi_build_24h | continuous | 0.37 | -0.15 | 0.02 | 0.03 | 0.26 | 0.01 |
| oi_zscore | continuous | 0.20 | 0.50* | -0.41 | 0.05 | 0.33 | -0.19 |
| oi_decline_speed | continuous | -0.11 | 0.12 | 0.06 | -0.14 | -0.06 | 0.00 |
| funding_rate | continuous | 0.10 | 0.35 | -0.47 | -0.10 | 0.09 | -0.32 |
| funding_zscore | continuous | -0.04 | -0.31 | 0.37 | -0.58* | -0.14 | -0.14 |
| long_short_ratio | continuous | 0.17 | 0.08 | -0.29 | 0.24 | 0.15 | -0.01 |
| long_account_share | continuous | 0.17 | 0.08 | -0.29 | 0.24 | 0.15 | -0.01 |
| ofi_sum_3 | continuous | -0.43* | 0.42 | 0.20 | -0.01 | -0.03 | 0.12 |
| ofi_sum_12 | continuous | 0.17 | -0.27 | -0.08 | -0.33 | 0.05 | -0.17 |
| dcvd_sum_3 | continuous | 0.00 | 0.04 | -0.22 | 0.10 | 0.04 | -0.05 |
| dcvd_sum_12 | continuous | 0.14 | 0.00 | -0.24 | -0.09 | 0.07 | -0.16 |
| shock_entry | continuous | -0.01 | 0.15 | -0.33 | -0.31 | -0.02 | -0.33 |
| shock_3 | continuous | 0.02 | -0.04 | -0.47 | -0.03 | -0.01 | -0.19 |
| realized_vol | continuous | 0.49* | -0.54 | 0.41 | 0.30 | 0.18 | 0.34 |
| rv_decile | continuous | 0.53* | -0.48 | 0.33 | 0.20 | 0.23 | 0.26 |
| btc_24h_with_cascade | categorical | 0.00 | -0.23 | -0.32 | -0.16 | -0.18 | -0.23 |
| btc_7d_with_cascade | categorical | 0.08 | -0.15 | 0.70* | -0.11 | 0.00 | 0.01 |
| btc_ema_with_cascade | categorical | 0.00 | -0.02 | 0.21 | -0.21 | -0.07 | -0.03 |
| hour_asia | categorical | 0.00 | 0.27* | 0.23 | -0.37* | 0.00 | 0.01 |
| hour_eu | categorical | 0.48* | -0.16 | 0.00 | 0.03 | 0.26 | 0.01 |
| hour_us | categorical | -0.36* | 0.05 | -0.23 | 0.15 | -0.26 | -0.02 |
| weekday_mon | categorical | 0.00 | — | 0.18 | -0.33* | -0.11 | 0.01 |
| weekday_tue | categorical | 0.29 | 0.31* | -0.23 | 0.40 | 0.33 | 0.01 |
| weekday_wed | categorical | 0.12 | -0.12 | 0.14 | -0.33* | 0.03 | 0.06 |
| weekday_thu | categorical | 0.54* | -0.35 | 0.00 | -0.15 | 0.08 | -0.09 |
| weekday_fri | categorical | 0.00 | 0.29* | -0.35* | 0.09 | 0.14 | 0.01 |
| weekday_sat | categorical | -0.37 | -0.30 | — | 0.02 | -0.37 | 0.01 |
| weekday_sun | categorical | -0.29 | 0.25* | 0.18 | -0.33* | -0.22 | 0.01 |
| cross_asset_confirm | categorical | 0.00 | -0.30 | 0.00 | 0.25 | -0.11 | 0.15 |

Non-gating context: test2_CASCADE_30m: NEGATIVE (18 single cells meet effect+CI); test2_DELEVERAGING_1h: NEGATIVE (0 single cells meet effect+CI); test2_DELEVERAGING_30m: NEGATIVE (0 single cells meet effect+CI). `long_short_ratio` and `long_account_share` are monotone transforms of each other (identical δ).

## Test 3 — pre-cascade prediction (time-ordered 60/40)

`n_casc` = CASCADE entries in the segment (the pre-registered ≥ 20 positive-event requirement is applied to this count); `pos bars` = y=1 bars. Full table incl. top-5% cutoff and coefficients: `test3_precascade.csv`.

| symbol | h | segment | model | n_casc | pos bars | base rate | precision | recall | prec/base | PR-AUC | lift |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 15m | fit_60 | rule_P(cascade|CROWDING) | 35 | 105 | 0.00155 | 0.0042 | 0.73 | 2.7 | 0.0035 | 2.24 |
| BTCUSDT | 15m | fit_60 | rule_P(cascade|STRESS) | 35 | 105 | 0.00155 | 0.0208 | 0.16 | 13.5 | 0.0047 | 3.02 |
| BTCUSDT | 15m | fit_60 | logistic_l2_C1 top1% | 35 | 105 | 0.00155 | 0.0221 | 0.14 | 14.3 | 0.0145 | 9.38 |
| BTCUSDT | 15m | test_40 | rule_P(cascade|CROWDING) | 11 | 33 | 0.00073 | 0.0029 | 0.88 | 3.9 | 0.0026 | 3.59 |
| BTCUSDT | 15m | test_40 | rule_P(cascade|STRESS) | 11 | 33 | 0.00073 | 0.0094 | 0.12 | 12.9 | 0.0018 | 2.44 |
| BTCUSDT | 15m | test_40 | logistic_l2_C1 top1% | 11 | 33 | 0.00073 | 0.0132 | 0.18 | 18.2 | 0.0051 | 7.02 |
| BTCUSDT | 30m | fit_60 | rule_P(cascade|CROWDING) | 35 | 209 | 0.00308 | 0.0091 | 0.81 | 3.0 | 0.0080 | 2.59 |
| BTCUSDT | 30m | fit_60 | rule_P(cascade|STRESS) | 35 | 209 | 0.00308 | 0.0282 | 0.11 | 9.2 | 0.0058 | 1.90 |
| BTCUSDT | 30m | fit_60 | logistic_l2_C1 top1% | 35 | 209 | 0.00308 | 0.0309 | 0.10 | 10.0 | 0.0197 | 6.40 |
| BTCUSDT | 30m | test_40 | rule_P(cascade|CROWDING) | 11 | 66 | 0.00146 | 0.0059 | 0.89 | 4.0 | 0.0054 | 3.70 |
| BTCUSDT | 30m | test_40 | rule_P(cascade|STRESS) | 11 | 66 | 0.00146 | 0.0094 | 0.06 | 6.4 | 0.0019 | 1.33 |
| BTCUSDT | 30m | test_40 | logistic_l2_C1 top1% | 11 | 66 | 0.00146 | 0.0088 | 0.06 | 6.1 | 0.0058 | 3.96 |
| BTCUSDT | 60m | fit_60 | rule_P(cascade|CROWDING) | 35 | 413 | 0.00609 | 0.0189 | 0.85 | 3.1 | 0.0170 | 2.79 |
| BTCUSDT | 60m | fit_60 | rule_P(cascade|STRESS) | 35 | 413 | 0.00609 | 0.0343 | 0.07 | 5.6 | 0.0080 | 1.31 |
| BTCUSDT | 60m | fit_60 | logistic_l2_C1 top1% | 35 | 413 | 0.00609 | 0.0457 | 0.08 | 7.5 | 0.0335 | 5.51 |
| BTCUSDT | 60m | test_40 | rule_P(cascade|CROWDING) | 11 | 132 | 0.00292 | 0.0115 | 0.88 | 3.9 | 0.0105 | 3.59 |
| BTCUSDT | 60m | test_40 | rule_P(cascade|STRESS) | 11 | 132 | 0.00292 | 0.0094 | 0.03 | 3.2 | 0.0031 | 1.07 |
| BTCUSDT | 60m | test_40 | logistic_l2_C1 top1% | 11 | 132 | 0.00292 | 0.0066 | 0.02 | 2.3 | 0.0097 | 3.34 |
| ETHUSDT | 15m | fit_60 | rule_P(cascade|CROWDING) | 27 | 79 | 0.00116 | 0.0039 | 0.81 | 3.4 | 0.0034 | 2.94 |
| ETHUSDT | 15m | fit_60 | rule_P(cascade|STRESS) | 27 | 79 | 0.00116 | 0.0187 | 0.15 | 16.1 | 0.0038 | 3.29 |
| ETHUSDT | 15m | fit_60 | logistic_l2_C1 top1% | 27 | 79 | 0.00116 | 0.0339 | 0.29 | 29.1 | 0.0424 | 36.44 |
| ETHUSDT | 15m | test_40 | rule_P(cascade|CROWDING) | 18 | 54 | 0.00119 | 0.0031 | 0.57 | 2.6 | 0.0023 | 1.92 |
| ETHUSDT | 15m | test_40 | rule_P(cascade|STRESS) | 18 | 54 | 0.00119 | 0.0413 | 0.31 | 34.6 | 0.0138 | 11.57 |
| ETHUSDT | 15m | test_40 | logistic_l2_C1 top1% | 18 | 54 | 0.00119 | 0.0199 | 0.17 | 16.6 | 0.0118 | 9.86 |
| ETHUSDT | 30m | fit_60 | rule_P(cascade|CROWDING) | 27 | 157 | 0.00231 | 0.0080 | 0.83 | 3.5 | 0.0070 | 3.04 |
| ETHUSDT | 30m | fit_60 | rule_P(cascade|STRESS) | 27 | 157 | 0.00231 | 0.0265 | 0.11 | 11.4 | 0.0049 | 2.13 |
| ETHUSDT | 30m | fit_60 | logistic_l2_C1 top1% | 27 | 157 | 0.00231 | 0.0722 | 0.31 | 31.2 | 0.0518 | 22.37 |
| ETHUSDT | 30m | test_40 | rule_P(cascade|CROWDING) | 18 | 108 | 0.00239 | 0.0075 | 0.69 | 3.1 | 0.0059 | 2.49 |
| ETHUSDT | 30m | test_40 | rule_P(cascade|STRESS) | 18 | 108 | 0.00239 | 0.0510 | 0.19 | 21.4 | 0.0118 | 4.96 |
| ETHUSDT | 30m | test_40 | logistic_l2_C1 top1% | 18 | 108 | 0.00239 | 0.0243 | 0.10 | 10.2 | 0.0164 | 6.85 |
| ETHUSDT | 60m | fit_60 | rule_P(cascade|CROWDING) | 27 | 313 | 0.00461 | 0.0164 | 0.85 | 3.6 | 0.0146 | 3.17 |
| ETHUSDT | 60m | fit_60 | rule_P(cascade|STRESS) | 27 | 313 | 0.00461 | 0.0312 | 0.06 | 6.8 | 0.0063 | 1.37 |
| ETHUSDT | 60m | fit_60 | logistic_l2_C1 top1% | 27 | 313 | 0.00461 | 0.1370 | 0.30 | 29.7 | 0.0849 | 18.40 |
| ETHUSDT | 60m | test_40 | rule_P(cascade|CROWDING) | 18 | 214 | 0.00473 | 0.0172 | 0.80 | 3.6 | 0.0148 | 3.12 |
| ETHUSDT | 60m | test_40 | rule_P(cascade|STRESS) | 18 | 214 | 0.00473 | 0.0583 | 0.11 | 12.3 | 0.0107 | 2.27 |
| ETHUSDT | 60m | test_40 | logistic_l2_C1 top1% | 18 | 214 | 0.00473 | 0.0221 | 0.05 | 4.7 | 0.0288 | 6.09 |

Gate status: logistic OOS lift ≥ 2.0 on both symbols at every horizon, but the test segment holds only 11 (BTC) / 18 (ETH) CASCADE entries < 20 → flagged, gate not met → NEGATIVE. Counting y=1 bars instead of entries (33–214) would flip Test 3 to POSITIVE; the lift is also largely by construction — a CASCADE requires an active crowd side + STRESS conditions, so the CROWDING/STRESS flags (largest logistic coefficients) are antecedents of the label, not independent predictors.

