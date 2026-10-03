# F006 · H-NONCANDLE-SLEEVE-01 (T0)

Implement the frozen open-interest fade rule on Train-1. One change. Do not pick a new rule.

## Outcome

Add a Train-1 harness that reads the cached Bybit linear open-interest series
under `data_cache/open_interest/` and applies the frozen rule from
`spec/research/F006-hypothesis-noncandle-sleeve.md` exactly:

Position for hour t is the opposite sign of the prior hour's open-interest
change: sign = -1 if OI[t-1] > OI[t-2], +1 if OI[t-1] < OI[t-2], flat if
equal or if either OI value is missing.

Write Result on the card. Costs use the existing harness cost model.
Baseline is flat cash 0. `number_of_trials = 1`. No threshold, no grid.

The run is **INVALID** unless it actually consumes the OI series (not
candles as a substitute). Before scoring, show that entries change when OI
is shuffled or zeroed with candles fixed, and that omitting OI refuses to
score.

## Scope

- Symbols: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT. Interval 60 only.
- Window: WARMUP_START 2024-01-26T00:00:00Z through TRAIN1_END
  2025-03-01T00:00:00Z. Score Train-1 months 2024-03 through 2025-02.
- Read `data_cache/open_interest/<SYM>_oi_1h_20240126T000000Z_20250301T000000Z.csv`.
- Falsifiers: (a) Train-1 mean after costs <= 0; (b) Warsaw exit-month sum
  of net_pnl over {2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12}
  <= 0; INVALID if OI is not consumed.
- `decision_if_fail`: close this sleeve's first mechanism. Do not unfreeze
  catalog names. Do not open a catalog portfolio.

## Out of scope

- Picking a new rule, threshold, or grid.
- Liquidations, order flow, trades, funding reuse, candle proxies.
- EMA/BB/Donchian filters, catalog mean-reversion, spread, funding carry,
  XS_RS, ORB, swarm, catalog portfolio, unfreeze, holdout, Val-1.
- `.pi/config.json` and `F006-catalog5-unfreeze-correction/`.
- `git reset --hard`.

## Result

Await T0. Frozen rule written before any result. OI coverage passed
(9600 hourly rows per symbol, gaps=0).
