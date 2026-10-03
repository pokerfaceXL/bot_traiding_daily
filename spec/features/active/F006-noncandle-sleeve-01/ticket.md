# F006 · H-NONCANDLE-SLEEVE-01 (no T0)

Add that source to the harness, else the test is invalid.

## Outcome

Do not implement. Do not fetch. Do not spawn. Do not run a backtest.

`spec/research/F006-hypothesis-noncandle-sleeve.md` is pre-registered and
**INVALID**. The catalog candle cache is OHLCV only. Funding is a closed
family, not this source. There is no order-flow, open-interest, liquidation,
or non-candle cross-asset file for the harness to pass in.

A job whose only job is an open-ended data hunt with no named file is out
of scope. Do not invent the file. Do not run a candle-only proxy.

## Scope

- This ticket records the block. It does not add a module, a cache, or a
  script.
- `number_of_trials = 1` remains unspent.
- Falsifiers, for a later run only after a real source file is already
  loadable, are (a) and (b) in the card. Until then the only legal Result
  is INVALID.

## Out of scope

- Any backtest.
- Any network download.
- EMA/BB/Donchian filters, catalog mean-reversion, spread capture, funding
  carry, XS_RS, ORB, swarm, catalog portfolio, unfreeze, holdout.
- `.pi/config.json` and `F006-catalog5-unfreeze-correction/`.
- `git reset --hard`.

## Result

INVALID. Source missing. Not run. (a) and (b) not labeled.
