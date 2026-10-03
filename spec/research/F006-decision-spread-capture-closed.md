# F006 — Decision: spread-capture CLOSED (no sweep)

date: 2026-10-03
decision: REJECT the spread-capture family before any parameter (protocol kill condition, not a Train-1 grid)
number_of_trials: 0

The owner kept the calendar-green goal (2026-10-03). That returns the two
parked families under their written conditions. It does not reopen a catalog
name, catalog mean-reversion, or an unnamed new family.

## Measurement

Public Bybit v5 linear tickers and instruments-info, `retCode` 0, server
time 1791062518420 (2026-10-03 23:21:58.420 Europe/Warsaw). Basket is this
project Train-1 symbols. Top of book was one tick on every name. Spread
bps = (ask - bid) / mid * 10000. The bar is 10 bps commission + 5 bps
half-spread + 2 bps slippage = 17 bps.

| symbol | bid | ask | spread bps | tick | one-tick bps |
| --- | --- | --- | --- | --- | --- |
| BTCUSDT | 84663.4 | 84663.5 | 0.011811 | 0.1 | 0.011811 |
| ETHUSDT | 2686.44 | 2686.45 | 0.037224 | 0.01 | 0.037224 |
| SOLUSDT | 119.58 | 119.59 | 0.836225 | 0.01 | 0.836260 |
| XRPUSDT | 1.4876 | 1.4877 | 0.672201 | 0.0001 | 0.672224 |
| DOGEUSDT | 0.09287 | 0.09288 | 1.076716 | 0.00001 | 1.076774 |

Widest inside spread is DOGEUSDT at 1.076716 bps. That does not cover 17 bps.
One tick is the entire inside spread on every name, and one tick itself is
below 17 bps, so this is not a momentary tight print under a wide book.

## Decision

Spread-capture is closed. No parameter sweep. No spawn. Do not raise trade
frequency to paint a green day. Catalog mean-reversion stays closed
(already aggregate-negative on Train-1). The other parked family is
`H-FUNDING-CARRY-01`, and only with funding inside the harness.
