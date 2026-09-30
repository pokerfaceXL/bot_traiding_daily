# H-BTC-PERM-CASCADE-01 — BTC permission × CASCADE continuation on alts

## Observation

BTC_FILTER ER20×Donchian N20 (+73.65 Train-1) and LIQ_CASCADE R15_V25 (+25.40) independently cleared aggregate Train-1 but failed monthly cleanliness. Their composition may discard wrong-regime alt continuation signals. This is next-test-plan T2, not a reopening of either parent.

## Hypothesis

Contemporaneous causal BTC ER20 permission matching an alt CASCADE trauma continuation signal improves regime selection. BTC is permission input only, never a candidate trade. The ungated alt-only ablation attributes the gate's effect.

## Falsifiers

- H1 fails when mean train1_net_pnl across the ten-series pool is <= 0 in NO_TRAIL. H1 uses train1_net_pnl, not monthly mean PnL.
- Reject a candidate whose mean signals/series-month exceeds 8.
- Any lookahead in ER, alignment, compression percentile, or expansion baselines invalidates the result.
- Donchian alt triggers, Sube FVG/MSS, EQH reclaim, fade, BTC_LEAD lag-return, vol-HIGH BOS, and retuning after Train-1 are forbidden.
- Holdout and Validation remain unopened. SBPA remains DNR, CASCADE-FADE blocked, VHBOS DNR.

## Method

Frozen before module code from `/tmp/F006-card-H-BTC-PERM-CASCADE-01.md` and `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md`. Base: main `eaf4add`. Use `scripts/f006_family_runner.py` / `run_family`, with DONCHIAN_55 control (expected mean train1_net_pnl approximately +58.387). Trade only ETH/SOL/XRP/DOGE USDT perps × {60,240}; keep BTC's two forced-flat diagnostic rows in the ten-series pool. Session filters off.

### BTC permission (frozen parent e518682)

At aligned bar i, ER20 = (close[i] - close[i-20]) / sum(abs(diff(close[i-20:i+1]))), using BTC closes <= i only. Permission +1 at ER20 >= threshold, -1 at ER20 <= -threshold, otherwise 0. Warm-up, zero denominator, or missing BTC means 0. Default threshold 0.30; ER40 uses 0.40. Matching alt direction passes; neutral/opposing permission suppresses. BTC is always forced flat, including NOGATE.

### CASCADE trauma continuation (frozen parent 80c013c)

On alt OHLCV only, R = high-low. Compression C_t = sum(R[t-19:t+1]); arm when C_t <= empirical 20th percentile of the prior 120 C values. Arm lasts exactly the next six bars; a new compression refreshes it. While armed, expansion requires R_i > RANGE_MULT × mean(R[i-20:i]) AND volume_i > VOLUME_MULT × mean(volume[i-20:i]); both baselines exclude i. A close in the top CLOSE_FRACTION threshold of the range emits long, bottom emits short, using the parent's exact close-location convention. Consume the arm on emission. N=20, lookback=120, arm=6, continuation only. Harness fills open i+1, one-shot. Compose after the trauma machine: emit cascade direction only when BTC permission equals it, except NOGATE.

### Frozen catalog (exactly five names)

| Name | RANGE_MULT | VOLUME_MULT | CLOSE_FRACTION | BTC ER20 threshold |
| --- | --- | --- | --- | --- |
| BPC_R15_V25_C75 | 1.5 | 2.5 | 0.75 | 0.30 |
| BPC_R18_V20_C75 | 1.8 | 2.0 | 0.75 | 0.30 |
| BPC_R18_V30_C75 | 1.8 | 3.0 | 0.75 | 0.30 |
| BPC_R15_V25_NOGATE | 1.5 | 2.5 | 0.75 | no gate (attribution only) |
| BPC_R15_V25_ER40 | 1.5 | 2.5 | 0.75 | 0.40 |

### Frozen exit grid and evaluation

| Cell | Parameters |
| --- | --- |
| NO_TRAIL | activate_pct=10.0, take_profit_multiple=None |
| TP_x2 | activate_pct=10.0, take_profit_multiple=2.0 |
| TRAIL_a0.06_t0.04 | activate_pct=0.06, trail_pct=0.04 |
| TRAIL_a0.03_t0.02 | activate_pct=0.03, trail_pct=0.02 |

Rank exit cells by win_rate descending; report train1_net_pnl/H1, n_trades, mean trades/series, max_drawdown_pct, exit mix, and both H2 policies for every cell. NO_TRAIL remains primary H1 research geometry. Report H2 conditional on H1, with raw diagnostics retained. Legacy H2 requires all 12 data-valid months clean. Sparse `h2_sparse_absent_zero_trade` assigns trades by exit month, treats zero-trade months as ABSENT/neutral, and passes a series only if every scored month has net_pnl >= 0, series max_dd <= 50%, train1_net_pnl >= 0, and n_trades > 0. No 12-scored-month requirement. Density preference >=~20 trades/series, <15 thin-series flag; density alone is not DNR before exit-grid and dual H2. Exits do not add signal entries or cure mechanism sparsity.

Evidence goes under `output/f006_btc_perm_cascade/`, recording producing commit and packaging tip SHA. Additive module, experiment, and unit tests only; do not change strategy.py or spec/build.md. No merge, no follow-up spawn, no production changes. Stop after evidence and pytest.
