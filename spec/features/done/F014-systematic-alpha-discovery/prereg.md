# F014 · Systematic alpha discovery — pre-registration (FROZEN 2026-10-07, before any scoring)

Authority: owner mandate 2026-10-07 Europe/Warsaw (ChatGPT PO skipped by owner instruction).
Machine-readable freeze: `alpha_discovery_lab/registry.py` → `output/f014_discovery/hypothesis_registry.json`
(sha256 of the canonical registry payload is stored there; the runner refuses to score if it changes).
Copy: `spec/features/active/F014-systematic-alpha-discovery/prereg.md` (identical text).

## 1. Splits (UTC, [start, end))

| split | window | use |
| --- | --- | --- |
| WARMUP | 2024-01-26 → 2024-03-01 | indicators / rolling quantiles only; no state scored |
| DISCOVERY (Train-1) | 2024-03-01 → 2025-03-01 | **only window scored here** |
| VALIDATION | 2025-03-01 → 2026-03-01 | FROZEN — not loaded, not scored |
| FINAL HOLDOUT | 2026-03-01 → 2026-09-01 | FROZEN — never opened |

Only the Train-1 files (`*_20240126T000000Z_20250301T000000Z`) are read; the loader hard-clips every series to
`< 2025-03-01`. Forward returns that would need a bar at/after 2025-03-01 are NaN and dropped.

Stability blocks (by decision bar): Q1 2024-03-01→06-01, Q2 06-01→09-01, Q3 09-01→12-01, Q4 2024-12-01→2025-03-01.

## 2. Data (what exists; gaps documented in `output/f014_discovery/datasets_inventory.md`)

- 1h OHLCV BTC/ETH/SOL (Bybit linear, bar-open timestamps) — primary bar.
- Funding (Bybit, 8h settled rate) and OI 1h (Bybit) BTC/ETH/SOL, Train-1 only.
- Account ratio 5m (Bybit `buyRatio`) BTC/ETH only, Train-1 only → Family C has no third asset.
- Not used: liquidations (live only since ~2026-10-05), 5m OHLCV (2-day samples), F012 Deribit/ETF (read-only, preserved).
- No new data fetched.

## 3. PIT / execution conventions

- Decision at the close of bar t; forward return y_h = 1e4 · ln(close_{t+h}/close_t) bp, h ∈ {1, 2, 4, 12}.
- Regime quantiles: rolling 720-bar (30 d) window over bars t−720..t−1 (shift 1, min_periods 720). "Top 20 %" = value
  strictly above q80, "bottom 20 %" strictly below q20, "top 5 %" strictly above q95. No lookback search.
- Aux series (funding, OI, buyRatio) attached to bar t only from rows timestamped ≤ bar-open t (≥ 1 h before decision).
- 24-bar realised vol, 20-bar prior-range breakout, 30-d trailing OLS beta (bars t−720..t−1) for residuals.

## 4. Primary test, FDR family, success criteria

- Each hypothesis defines a population, a binary state S ⊂ population, a target y (own forward return unless stated)
  and a predicted direction d. Primary statistic: b = mean(y|S) − mean(y|population∖S) from OLS y = a + b·S with
  Newey–West HAC SE (Bartlett, 24 lags), two-sided normal p. Spearman IC of the continuous state score vs y is reported
  (diagnostic).
- **FDR family (frozen):** one primary test per (hypothesis, required asset) at the hypothesis' primary horizon (first
  listed). Required assets = BTC + ETH, except Family D (pairs/followers: ETH and SOL, see registry). m = 28 × 2 = **56**.
  SKIPPED / INSUFFICIENT (< 30 state bars) tests stay in the family with p = 1. Benjamini–Hochberg; q ≤ 0.10.
  Secondary horizons and the optional third asset are reported but are **not** in the family.
- A hypothesis **SURVIVES** discovery only if ALL hold:
  1. C1 sign — b sign = d OR IC sign = d, on both required assets;
  2. C2 FDR — BH q ≤ 0.10 on both required-asset primary tests;
  3. C3 stability — block b sign = d in ≥ 3/4 quarterly blocks on both required assets (block with < 10 state bars = not OK);
  4. C4 replication — both required assets have b sign = d;
  5. C5 economics — tradable expression gross = mean over state bars of d·y; gross − 9.9 bp × cost_mult > 0 on both
     required assets (cost_mult = 1, or 1 + |β| for pair trades). Net @34 bp reported as stress/historical.
     Non-tradable hypotheses (H-PS-VOL-COMPRESS) fail C5 by construction.
- Two-sided hypotheses (H-TIME-US-OPEN, H-TIME-ASIA, d = 0): predicted sign := sign(b_BTC) on full discovery; ETH and
  blocks must agree.
- Robustness score (ranking only, never max return): mean_asset(blocks_ok)/4 + 1{C4} + 1{C2} +
  clip(min_asset((gross − 9.9·cm)/(9.9·cm)), 0, 1). At most 3 recommendations.

## 5. Registry (28 primary IDs — no additions after scoring starts)

Full definitions (state formula, why, expected effect, horizons, target, expression, required assets) in
`output/f014_discovery/hypothesis_registry.md`. Summary:

| family | ids |
| --- | --- |
| A price structure | H-PS-REV-UP, H-PS-REV-DN, H-PS-TREND-UP, H-PS-TREND-DN, H-PS-RANGE-LOC, H-PS-RANGE-LOC-DN, H-PS-VOL-COMPRESS, H-PS-GAP-CONT |
| B derivatives | H-DER-FUND-HI, H-DER-FUND-LO, H-DER-FUND-DELTA, H-DER-OI-UP-PX-UP, H-DER-OI-UP-PX-DN, H-DER-OI-DOWN-CAPIT, H-DER-OI-FLAT-MOVE |
| C positioning | H-OF-BUYRATIO-HI, H-OF-BUYRATIO-LO, H-OF-BUYRATIO-SPIKE |
| D cross-market | H-XS-ETH-BTC-REV, H-XS-ETH-BTC-REV-DN, H-XS-BTC-LEAD, H-XS-SOL-BTC-REV |
| E vol regime | H-VOL-REGIME-DIR, H-VOL-SPIKE-DRIFT, H-VOL-OF-VOL |
| F time | H-TIME-US-OPEN, H-TIME-ASIA, H-TIME-FUNDING-HOUR |

Declared interpretations (frozen here because the mandate wording admits several):
- H-PS-GAP-CONT: crypto has no session gap; proxy = the 00:00–01:00 UTC bar's own log return g; population = 00:00
  bars; large = |g| above q80 of the previous 30 such bars; y = sign(g)·fwd; primary horizon 4h.
- H-PS-VOL-COMPRESS: target = |fwd r_h| / (σ24·√h) (expansion relative to recent vol); primary 4h; non-tradable.
- H-DER-OI-FLAT-MOVE uses the 1h ΔOI to match r_1h. H-DER-OI-UP-* primary 4h; H-DER-OI-DOWN-CAPIT primary 1h.
- Family D replication: the required "pair" is ETH-vs-BTC and SOL-vs-BTC (BTC is the hedge/leader leg, so BTC cannot
  be its own replication). H-XS-SOL-BTC-REV = symmetric |residual| reversion with SOL primary, ETH replication.
- H-VOL-REGIME-DIR: population = trend-state bars with σ24 in its top or bottom 20 %; b = mean(TS·fwd | high vol) −
  mean(TS·fwd | low vol), d = −1; tradable expression = trend-follow in the low-vol regime (gross = mean TS·fwd | low vol).
- H-TIME-*: state is defined by the start hour of the forward window (US open 13:00–15:00 UTC; Asia 00:00–04:00 UTC;
  funding ±1h around 00/08/16 UTC). H-TIME-FUNDING-HOUR target is signed by the last settled funding (y = −sign(f)·fwd).

## 6. Outputs and stop

Ledger (`ledger.jsonl` / `ledger.csv`) records every (hypothesis, asset, horizon) attempt including SKIPPED and
INSUFFICIENT rows, with distributional stats (mean, median, q10/q25/q75/q90, P(r>0), mean |r|, MFE, MAE) for state
and complement. `fdr_report.*`, `survivors_ranked.*`, `discovery_summary.json`, `STATUS.md`.
**STOP after discovery.** Validation needs explicit owner approval; holdout stays sealed.
