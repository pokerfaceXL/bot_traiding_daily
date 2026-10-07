# F014 hypothesis registry (FROZEN before scoring)

sha256 (canonical JSON of registry_payload): `b742d3fbf8266ea21d930f0e630d1af22831c49494f62b6b4522f6320daac690`

Family m = 56 (28 hyps x 2 required assets, primary horizon), BH q <= 0.1.

| # | id | fam | state | expected | d | horizons (primary first) | target | expression | req assets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | H-PS-REV-UP | A | r_1h(t) > 0 AND |r_1h(t)| > q80 of trailing 720 |r_1h| | negative fwd return | -1 | [1, 2, 4] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 2 | H-PS-REV-DN | A | r_1h(t) < 0 AND |r_1h(t)| > q80 of trailing 720 |r_1h| | positive fwd return | +1 | [1, 2, 4] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 3 | H-PS-TREND-UP | A | close_t > max(high_{t-20..t-1}) | positive fwd return | +1 | [1, 2, 4] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 4 | H-PS-TREND-DN | A | close_t < min(low_{t-20..t-1}) | negative fwd return | -1 | [1, 2, 4] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 5 | H-PS-RANGE-LOC | A | loc_t = (close-low)/(high-low) of bar t > q80 of trailing 720 loc | positive fwd return | +1 | [1, 2, 4] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 6 | H-PS-RANGE-LOC-DN | A | loc_t < q20 of trailing 720 loc | negative fwd return | -1 | [1, 2, 4] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 7 | H-PS-VOL-COMPRESS | A | sigma24_t (std of last 24 1h log returns) < q20 of trailing 720 sigma24 | higher vol-normalised forward move | +1 | [4, 1, 2, 12] | y = |fwd log return_h| / (sigma24_t * sqrt(h)) (unitless); |r|, MFE, MAE reported | none (non-directional; a straddle is not available on linear perps) (NON-TRADABLE) | BTCUSDT, ETHUSDT |
| 8 | H-PS-GAP-CONT | A | population = 00:00 UTC bars only; g = log return of the 00:00-01:00 bar; state = |g| > q80 of |g| over the previous 30 00:00 bars (causal) | same-sign continuation over next 4h | +1 | [4, 1, 2, 12] | y = sign(g) * fwd log return_h | position sign(g) at 01:00 UTC | BTCUSDT, ETHUSDT |
| 9 | H-DER-FUND-HI | B | funding_t (last settled, aligned) > q80 of trailing 720 aligned funding | negative fwd return | -1 | [4, 12, 1, 2] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 10 | H-DER-FUND-LO | B | funding_t < q20 of trailing 720 aligned funding | positive fwd return | +1 | [4, 12, 1, 2] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 11 | H-DER-FUND-DELTA | B | dF = funding_t - funding_{t-24}; dF > 0 AND dF > q80 of trailing 720 dF | negative fwd return | -1 | [4, 12, 1, 2] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 12 | H-DER-OI-UP-PX-UP | B | dOI4 = ln(OI_t/OI_{t-4}) > q80 of trailing 720 dOI4 AND r_4h(t) > 0 | negative fwd return | -1 | [4, 1, 2, 12] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 13 | H-DER-OI-UP-PX-DN | B | dOI4 > q80 AND r_4h(t) < 0 | positive fwd return | +1 | [4, 1, 2, 12] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 14 | H-DER-OI-DOWN-CAPIT | B | dOI4 < q20 AND r_4h(t) < q20 of trailing 720 r_4h | positive bounce | +1 | [1, 2, 4] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 15 | H-DER-OI-FLAT-MOVE | B | |dOI1| = |ln(OI_t/OI_{t-1})| < q20 of trailing 720 |dOI1| AND |r_1h(t)| > q80 of trailing 720 |r_1h| | mean reversion next 1-2h | -1 | [1, 2] | y = sign(r_1h(t)) * fwd log return_h (d = -1: reversal) | position -sign(r_1h(t)) | BTCUSDT, ETHUSDT |
| 16 | H-OF-BUYRATIO-HI | C | buyRatio_t (Bybit account ratio 5m, last row <= bar open) > q80 of trailing 720 | negative fwd return | -1 | [1, 2, 4] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 17 | H-OF-BUYRATIO-LO | C | buyRatio_t < q20 of trailing 720 | positive fwd return | +1 | [1, 2, 4] | y = own forward log return (bp) | long on state bar | BTCUSDT, ETHUSDT |
| 18 | H-OF-BUYRATIO-SPIKE | C | dBR4 = buyRatio_t - buyRatio_{t-4} > q80 of trailing 720 dBR4 | negative fwd return | -1 | [1, 2, 4] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 19 | H-XS-ETH-BTC-REV | D | e_t = r_X(t) - beta_t r_BTC(t), beta_t = OLS slope over bars t-720..t-1; e_t > q80 of trailing 720 e | negative fwd residual | -1 | [1, 2, 4] | y = r_X,fwd_h - beta_t * r_BTC,fwd_h (bp) | short X / long beta BTC (pair) | ETHUSDT, SOLUSDT |
| 20 | H-XS-ETH-BTC-REV-DN | D | e_t < q20 of trailing 720 e | positive fwd residual | +1 | [1, 2, 4] | y = r_X,fwd_h - beta_t * r_BTC,fwd_h (bp) | long X / short beta BTC (pair) | ETHUSDT, SOLUSDT |
| 21 | H-XS-BTC-LEAD | D | |r_BTC(t)| > q80 of trailing 720 |r_BTC| | same-sign follower return next 1h | +1 | [1, 2] | y = sign(r_BTC(t)) * r_X,fwd_h | position sign(r_BTC(t)) in follower X | ETHUSDT, SOLUSDT |
| 22 | H-XS-SOL-BTC-REV | D | |e_t| > q80 of trailing 720 |e| (residual as in H-XS-ETH-BTC-REV) | residual reverts | -1 | [1, 2, 4] | y = sign(e_t) * (r_X,fwd_h - beta_t r_BTC,fwd_h) | position -sign(e_t) in pair | SOLUSDT, ETHUSDT |
| 23 | H-VOL-REGIME-DIR | E | population = bars with a trend state (TS = +1 if H-PS-TREND-UP, -1 if H-PS-TREND-DN); S = sigma24_t > q80 (high vol); bars with sigma24 between q20 and q80 excluded | trend-follow return lower in high-vol than low-vol regime | -1 | [1, 2, 4] | y = TS_t * fwd log return_h | trend-follow (position TS_t) only in low-vol regime | BTCUSDT, ETHUSDT |
| 24 | H-VOL-SPIKE-DRIFT | E | |r_1h(t)| > q95 of trailing 720 |r_1h| | negative drift next 2-4h | -1 | [2, 4, 1, 12] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 25 | H-VOL-OF-VOL | E | vov_t = std of |r_1h| over last 24 bars > q80 of trailing 720 vov | negative mean drift 4h (and elevated |fwd r|, secondary) | -1 | [4, 1, 2, 12] | y = own forward log return (bp) | short on state bar | BTCUSDT, ETHUSDT |
| 26 | H-TIME-US-OPEN | F | forward window starts 13:00 or 14:00 UTC (bar t open hour in {12, 13}) | directional edge differs from other hours (two-sided); |r| secondary | +0 | [1, 2] | y = own forward log return (bp) | position sign(b_BTC) on state bars | BTCUSDT, ETHUSDT |
| 27 | H-TIME-ASIA | F | forward window starts 00:00-03:00 UTC (bar t open hour in {23, 0, 1, 2}) | directional edge differs (two-sided); |r| secondary | +0 | [1, 2] | y = own forward log return (bp) | position sign(b_BTC) on state bars | BTCUSDT, ETHUSDT |
| 28 | H-TIME-FUNDING-HOUR | F | forward window starts within +-1h of a funding settlement 00/08/16 UTC (bar t open hour in {22, 23, 6, 7, 14, 15}); target signed by last settled funding | price moves against the funding-paying side | +1 | [1, 2] | y = -sign(funding_t) * fwd log return_h (funding_t == 0 -> excluded) | position -sign(funding_t) on state bars | BTCUSDT, ETHUSDT |

## Why / notes

- **H-PS-REV-UP** — short-horizon overreaction to large up bars.
- **H-PS-REV-DN** — short-horizon overreaction to large down bars.
- **H-PS-TREND-UP** — momentum continuation after range breakout (IC/state test, not a Donchian strategy reopen).
- **H-PS-TREND-DN** — momentum continuation.
- **H-PS-RANGE-LOC** — close near the high = unabsorbed buying. Note: bars with high == low have loc undefined (NaN, excluded)
- **H-PS-RANGE-LOC-DN** — close near the low = unabsorbed selling.
- **H-PS-VOL-COMPRESS** — volatility compression precedes expansion. Note: fails C5 by construction; kept for information and multiplicity
- **H-PS-GAP-CONT** — day-roll repricing (UTC day open) continues. Note: crypto has no session gap; the 00:00 UTC bar return is the frozen proxy
- **H-DER-FUND-HI** — crowded longs pay and unwind.
- **H-DER-FUND-LO** — crowded shorts.
- **H-DER-FUND-DELTA** — crowding acceleration.
- **H-DER-OI-UP-PX-UP** — new leveraged longs chase -> long-squeeze risk.
- **H-DER-OI-UP-PX-DN** — new shorts pile in -> short-squeeze risk.
- **H-DER-OI-DOWN-CAPIT** — capitulation / forced deleveraging exhausts sellers.
- **H-DER-OI-FLAT-MOVE** — price move without positioning change = thin-book move.
- **H-OF-BUYRATIO-HI** — retail long crowding is contrarian.
- **H-OF-BUYRATIO-LO** — retail short crowding is contrarian.
- **H-OF-BUYRATIO-SPIKE** — fast retail long build-up is contrarian.
- **H-XS-ETH-BTC-REV** — idiosyncratic relative moves revert (relative value). Note: required pair: X = ETH (primary), replication X = SOL; cost multiplier 1 + |beta_t|
- **H-XS-ETH-BTC-REV-DN** — relative value reversion. Note: X = ETH primary, X = SOL replication; cost multiplier 1 + |beta_t|
- **H-XS-BTC-LEAD** — BTC leads alt repricing. Note: follower X = ETH (primary) and SOL (replication)
- **H-XS-SOL-BTC-REV** — symmetric residual reversion. Note: X = SOL primary, X = ETH replication; cost multiplier 1 + |beta_t|
- **H-VOL-REGIME-DIR** — in high vol noise dominates breakouts. Note: b = mean(y|high vol) - mean(y|low vol); tradable gross = mean(y | low vol) (d applied to the regime contrast, the expression itself is long TS)
- **H-VOL-SPIKE-DRIFT** — risk-off after shock.
- **H-VOL-OF-VOL** — unstable volatility = risk-off.
- **H-TIME-US-OPEN** — US cash open flow.
- **H-TIME-ASIA** — Asia session flow.
- **H-TIME-FUNDING-HOUR** — payers of funding de-risk around settlement (inventory management).

## Protocol

```json
{
  "bar": "1h (Bybit linear OHLCV, timestamp = bar open, UTC)",
  "decision": "at close of bar t (= timestamp_t + 1h); all state inputs known by then",
  "forward_return": "y_h = 1e4 * ln(close_{t+h} / close_t) in bp; NaN if t+h outside the loaded Train-1 file",
  "horizons_reported": [
    1,
    2,
    4,
    12
  ],
  "lookback_bars": 720,
  "quantile_rule": "threshold_t = rolling(720, min_periods=720) quantile of the state variable over bars t-720..t-1 (shift 1, causal); 'top 20%' = value > q80 strictly; 'bottom 20%' = value < q20 strictly; 'top 5%' = value > q95 strictly",
  "vol_window_bars": 24,
  "breakout_window_bars": 20,
  "aux_alignment": "funding / OI / account-ratio rows are attached to bar t only if their timestamp <= bar-open timestamp_t (>= 1h before the decision; conservative, no same-bar peek)",
  "primary_test": "OLS y = a + b*S over the hypothesis population (S = state indicator); b = mean(y|S) - mean(y|population & not S); two-sided p from Newey-West HAC SE (Bartlett, 24 lags), normal approximation",
  "hac_lags": 24,
  "ic": "Spearman rank correlation of the hypothesis' continuous score with y over the population (diagnostic; criterion 1 accepts b sign OR IC sign)",
  "min_state_n_full": 30,
  "min_state_n_block": 10,
  "fdr": {
    "method": "Benjamini-Hochberg",
    "family": "one primary test per (hypothesis, required asset) at the primary horizon; required assets = 2 (see each hypothesis' replication pair) -> m = 28 x 2 = 56; SKIPPED or INSUFFICIENT tests stay in the family with p = 1",
    "m": 56,
    "q_max": 0.1,
    "secondary": "all non-primary horizons and the optional third asset are reported, NOT in the family"
  },
  "cost_bp_rt": {
    "primary_owner_tier": 9.9,
    "stress_historical": 34.0
  },
  "cost_rule": "one RT per hypothetical state-bar trade (overlapping state bars each pay a full RT); pair expressions (residual) pay RT x (1 + |beta_t|) averaged over state bars",
  "tradable_gross": "gross_bp = mean over state bars of d * y (d = predicted direction of the expression)",
  "success": [
    "C1 sign: b sign == d OR IC sign == d, on BOTH required assets",
    "C2 FDR: BH q <= 0.10 on BOTH required-asset primary tests (family m = 56)",
    "C3 stability: block b sign == d in >= 3 of 4 quarterly blocks, on BOTH required assets",
    "C4 replication: both required assets have b sign == d (third asset optional, bonus only)",
    "C5 economics: tradable expression with gross_bp - 9.9 * cost_mult > 0 on BOTH required assets (net @34 reported as stress); non-tradable hypotheses fail C5 by construction"
  ],
  "robustness_score": "mean_asset(n_blocks_ok)/4 + 1{C4} + 1{C2} + clip(min_asset((gross - 9.9*cm)/(9.9*cm)), 0, 1); survivors ranked by this score, never by max return; at most 3 recommended",
  "two_sided_hyps": "for d = 0 hypotheses (time-of-day) the predicted sign is set to sign(b_BTC) on the full discovery window; ETH and blocks must then agree"
}
```
