# F011 · Forced-flow event frame (T1, non-trading)

## Outcome

A clean, causal, per-hour feature frame for BTCUSDT + ETHUSDT that turns raw OHLCV + open
interest + funding into participant-state variables, so later tasks can label states and run the
event study. Pure data engineering — no trading, no signal, no labels yet. Full spec:
`spec/research/F011-forced-flow-lab.md` §3,§7. New code lives under `forced_flow_lab/`; do not
touch the live bot, `strategy.py`, or the catalog.

## Scope

- Load from cache (reuse `data_contract` / existing loaders; honour closed-candle, checksum,
  no-silent-gap rules): hourly OHLCV, hourly OI (`data_cache/open_interest/`), funding
  (`data_cache/funding/`), Train-1 span, BTCUSDT + ETHUSDT (keep it generic for 5 symbols).
- Align all series on the hourly close grid; forward-fill funding to the hour it applies to,
  flagging any fill. Emit per bar, using only data at or before that bar: return, ATR,
  realized_vol, volume; ΔOI, OI_zscore (rolling), OI_acceleration (d²); funding_zscore;
  fuel = |ΔOI| / ATR; price_impact = |Δprice| / volume; and the rolling z-score windows used.
- Write the frame to `output/f011_forced_flow/frame/<SYMBOL>.csv` + a manifest (window,
  checksums, rolling-window params). Add a unit test proving causality (truncating the input at
  bar i leaves every feature at bar i unchanged).

## Out of scope

- Any state label, signal, trade, or backtest (that is T2/T3).
- Liquidations / basis / taker / order-book features — not in the repo; leave typed-but-empty
  columns noting owner-gated acquisition, do not fabricate proxies beyond §3's OI/price ones.
- Editing production code or the strategy catalog.

## Acceptance

- `output/f011_forced_flow/frame/{BTCUSDT,ETHUSDT}.csv` exist with every §3 feature, aligned on
  the hourly grid, no NaN past warm-up, funding fills flagged.
- Causality test passes; `python3 -m pytest -q` stays green.

## Notes

Rolling z-score windows are a frozen choice recorded in the manifest, not a tunable — pick a
sensible fixed lookback and document it; no fitting to outcomes here.
