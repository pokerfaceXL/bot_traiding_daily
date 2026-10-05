# F011 · Forced-flow 5m feature frame (T1b, non-trading)

## Outcome

The 5m version of the forced-flow frame for BTCUSDT + ETHUSDT over Train-1
(2024-01-26T00:00Z .. 2025-02-28T23:55Z), built only from free sources verified in
`output/f011_forced_flow/coverage/report.md` (branch `grok/f011-plan-c`, merge first).
Owner plan C (2026-10-05): the 5m frame, not the 1h one, is the base for the first serious
event study. Pure data engineering: no labels, signals or backtests.

## Scope

- Inputs: Bybit 5m OI (pick and document ONE convention: `openInterest` vs
  `singleOpenInterest`, which differ by exactly 2x), Bybit 5m account ratio, Bybit 5m OHLCV,
  cached funding (8h, forward-filled and flagged), Bybit trade archive reduced to 5m
  taker_buy_vol, taker_sell_vol, OFI=(B-S)/(B+S), CVD, trade_count; Binance 5m metrics +
  5m klines as a separate cross-venue layer (prefixed `bn_`, never substituted for Bybit OI).
- Trade archive is processed in STREAMING mode: download one day, reduce to 5m, write the
  5m day result, delete the raw file, then the next day. Never keep more than one raw day on
  disk. Before each day, check free disk space and stop cleanly if it is under 10 GB.
  Resumable: skip days whose 5m output already exists and checksum-verifies.
- Per-bar features (causal, only data at or before the bar): return_5m/15m/60m,
  ATR-normalised return, realized_vol, ΔOI, ΔOI%, OI_zscore, OI_acceleration, funding and its
  z-score, long/short ratio and its change, taker flow fields, ΔCVD, fuel=|ΔOI|/ATR,
  sell_impact=|Δprice|/taker_sell_vol and buy_impact likewise. Liquidation columns stay
  typed-but-null (live collector data starts 2026-10-05, outside Train-1).
- Output: `output/f011_forced_flow/frame_5m/<SYMBOL>.parquet` (or csv.gz) + manifest
  (sources, OI convention, checksums, rolling windows as frozen choices). Reduced per-day trade
  aggregates under `data_cache/bybit_trades_5m/` (git-ignored).
- Causality unit test as for the 1h frame; reconciliation test that 5m OI at full hours equals
  the cached 1h OI.

## Out of scope

State labels, event study, signals, trading. Paid data. Live bot / strategy.py / catalog.

## Acceptance

Both symbols have 115,200 rows, no NaN past warm-up, gaps listed (expected 0), disk never
dropped under the guard, raw trade files absent after the run, pytest green.
