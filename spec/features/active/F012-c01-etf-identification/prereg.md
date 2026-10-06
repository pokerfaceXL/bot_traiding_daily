# F012-C01 — pre-registered gate criteria (written before any gate result was computed)

Train-1 only: US trading days T with 2024-03-01 ≤ T < 2025-03-01 (Farside rows with all
issuer cells blank = market holiday, dropped → 250 days). Pre-Train-1 Farside history
(2024-01-11…2024-02-29) is used only as lag/rolling *input history*, never as a scored day.
Chronological folds inside Train-1: F1 = first third (fit), F2 = second third (model
selection), F3 = last third (untouched test). Walk-forward = expanding refit each day after
a 60-day burn-in (reported alongside, never used for selection).

## Target and observables (PIT)
- Target `y_T` = Farside BTC `Total` for trade date T ($M). Never a predictor for T.
- PIT inputs for T must be live before T 15:00 UTC (≥ 4 h before the 15:00 ET window):
  `y_{T-1}`, `mean(y_{T-5..T-1})`, `IBIT_{T-1}`, `GBTC_{T-1}`, BTC return 16:00 ET T-2 → 16:00 ET T-1
  (Coinbase), prior-day ETF dollar volume z-score (Yahoo IBIT+FBTC+GBTC+ARKB+BITB, T-1 close),
  prior-day IBIT premium proxy (log IBIT close / BTC 16:00 ET minus its trailing 20-day mean).
- Overnight BTC return 16:00 ET T-1 → 09:30 ET T is a *flagged* pre-open input, reported in a
  separate model only (pre-ETF-session, but APs could pre-hedge).
- Same-day BTC moves after 09:30 ET T are never predictors.

## Models
M0 expanding mean (benchmark) · M1 `y_{T-1}` · M2 5-day mean · M3 OLS on all PIT inputs ·
M3o = M3 + overnight return (flagged, not eligible as primary).
Primary model = the one of {M1, M2, M3} with lowest MAE on F2 when fitted on F1. Scored on F3
and walk-forward.

## Gate A (Observable → ETF_Flow). PASS iff all on F3 for the primary model:
(a) OOS R² vs M0 > 0 **and** Spearman ρ(pred, y) > 0 with p < 0.05;
(b) "Large-flow day" = |y_T| ≥ expanding 80th pct of past |y| (PIT). Sign accuracy on large days
    ≥ 0.60 with one-sided binomial p < 0.05 vs 0.5, and ≥ M0's sign accuracy on the same days;
(c) Lift: P(large | |pred| ≥ expanding 80th pct of past |pred|) / P(large) ≥ 1.5.
Holm over the p-values of (a) and (b). Else **Gate A FAIL → STOP**.

## Gate B (NAV window). Only if A passes.
Direction d_T = sign(primary pred). Primary window [15:00, 16:00) America/New_York on T
(CME CF BRRNY / issuer NAV fix 16:00 ET; brief §C01). Primary venue Coinbase BTC-USD spot
(BRRNY constituent); Bybit perp (frame) and Binance perp secondary.
AR_T = window log return − trailing 20-trading-day mean of the same window (PIT).
High-pred days = |pred| ≥ expanding 67th pct of past |pred|.
PASS iff: (1) mean d·AR on high-pred days > 0, p < 0.05 (t and bootstrap) on F2∪F3 OOS and
walk-forward; (2) time-scrambled permutation p < 0.05; (3) the window ranks top-2 of the 24
hourly ET windows by t-stat of d·AR; (4) adjacent hours 14–15 and 16–17 ET weaker than window.
Placebos reported: wrong TOD, scrambled, next-day, weekend/holiday, low-pred days.
Reverse causality (lead/lag with PIT stamps) reported; informs CONDITIONAL vs PASS.

## Gate C (tradeability). Only if B passes.
Entry 15:05 ET (one 5m bar latency) Bybit BTCUSDT perp, exit 16:00 ET close, 1× notional.
PASS iff mean net (gross − 9.9 bp RT owner tier) > 0 with bootstrap 95% CI lower > 0 on F3.
Also reported: gross, net of 34 bp, maker bound ~5.1 bp/side context. No leverage rescue.

Overall: FAIL if any gate fails; PASS if A+B+C pass cleanly; CONDITIONAL if all pass but a
robustness check (by-period, leave-out-top-k, reverse causality) materially weakens it.
