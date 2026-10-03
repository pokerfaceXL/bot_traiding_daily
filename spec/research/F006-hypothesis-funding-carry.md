# F006 — H-FUNDING-CARRY-01 (pre-registered)

> Pre-registered **before** any carry run. The owner kept the calendar-green
> goal on 2026-10-03. That returns the two parked families under their
> written conditions. Spread-capture is already closed in
> `spec/research/F006-decision-spread-capture-closed.md` (widest measured
> inside spread 1.076716 bps on DOGEUSDT versus the 17 bps bar; no sweep).
> This card is the other parked family. It is not a catalog name, not
> catalog mean-reversion, and not a new unnamed family.

experiment_id: H-FUNDING-CARRY-01
date: 2026-10-03
base_strategy: flat cash on the same Train-1 frames (no catalog signal)
number_of_trials: 1

```text
Why existing family is insufficient:
Every catalog5 name and DONCHIAN_55_NO_TRAIL is FREEZE. Each name closed
every licensed axis on its own trades. The shared edge is a few fat-tail
runners, and Train-1 losing months are one basket regime (shared-losing
CONFIRMED, tip dc9818e: phi 0.79). That shape does not serve a
calendar-green day goal. The owner kept that goal. In-class portfolio
stays blocked because losses are strongly correlated.

What mechanism is missing:
A cashflow that is the funding rate itself, not a directional breakout and
not a catalog signal.

Why this family is different:
The position is held only to receive the next Bybit linear funding
settlement. It does not use STRATEGY_CATALOG price signals, mean-reversion,
or spread capture.

What evidence would reject it:
(a) Train-1 mean across the five series of (sum funding_pnl - sum
total_costs) <= 0, which is the flat baseline of 0.
(b) one funding-sign-reversal Warsaw day wipes the green days, defined
below.
A backtest that does not apply funding is INVALID, not a pass and not a
falsification of (a) or (b).

What is the maximum initial research budget:
One position rule, five symbols, 60-minute bars only, Train-1 only.
number_of_trials = 1. No rate threshold, no hold-length grid, no fee grid,
no symbol drop.
```

```text
Observation:
backtest_engine.run_backtest already accepts funding_events and
equity.Portfolio.close_position books costs.funding_pnl into net_pnl.
scripts/f006_family_runner.py _run_one does not pass funding_events,
so the default is () and F006 NO_TRAIL runs have no funding cashflow.
spec/research/F006-shared-harness.md states total_costs is commission
+ spread + slippage, no funding. There is no local funding-rate series.
Spread-capture cannot be the calendar mechanism: the 2026-10-03 23:21:58
Europe/Warsaw Bybit top of book is one tick and at most 1.076716 bps
against a 17 bps cost bar.

Problem:
The calendar-green goal is still the goal, and every tested breakout
family leaves an uneven month floor because losses and runners share one
regime. The parked alternative that is still open is being paid the
funding rate. Without funding inside the harness that test is invalid.

Mechanism:
Bybit linear USDT perps settle a funding rate on a timestamp. The side
opposite the payers receives that rate. The only rate knowable without
look-ahead, from the public settlement history, is the previous
settlement. Hold the receiving side of that previous rate across exactly
the next settlement, then flat. Price PnL is not the mechanism. The
cashflow that can confirm the mechanism is funding_pnl minus the harness
costs (commission 10 bps, half-spread 5 bps, slippage 2 bps).

Hypothesis:
On this project own Train-1 basket, one causal rule — short across the
next settlement when the previous settled funding rate is > 0, long when
it is < 0, flat when it is 0 or missing — has Train-1 mean
(funding_pnl - total_costs) > 0 versus flat cash at 0, and no single
funding-sign-reversal Warsaw day wipes the sum of the positive days on
that same metric. The test counts only if funding_events from the cached
Bybit settlement history are passed into run_backtest.
```

## Frozen rule (one change versus flat)

- Symbols: SOLUSDT, ETHUSDT, BTCUSDT, XRPUSDT, DOGEUSDT.
- Interval: 60 only. Do not also run 240.
- Window: warmup from WARMUP_START 2024-01-26T00:00:00Z, score only
  Train-1 months 2024-03 through 2025-02, slice end TRAIN1_END
  2025-03-01T00:00:00Z. Do not load validation or holdout bars.
- Costs, unchanged: commission_rate_bps=10, half_spread_bps=5,
  slippage_bps=2, leverage=1, stake=100, initial_equity=500,
  max_sl_pct=0.03, activate_pct=10, trail_pct=0.04, cooldown=0.
  Do not retune the protective stop.
- Funding events: settled Bybit linear funding history
  (/v5/market/funding/history, category linear) for those five symbols,
  cached with a checksum. Pass (timestamp, rate) pairs into
  run_backtest funding_events. Rate is the decimal the exchange settled
  (0.0001 = 1 bp), matching costs.funding_payment.
- Position, one rule: let r_prev be the latest settlement with timestamp
  strictly before the decision bar close. If r_prev > 0, short. If
  r_prev < 0, long. If r_prev == 0 or there is no previous settlement,
  stay flat. Enter at the next bar open after that decision. Exit so the
  position is open for exactly the next settlement
  (entry_time <= funding_timestamp < exit_time) and is flat before the
  one after that. Do not use the settlement about to be received as the
  decision sign. Do not use a price indicator. Do not grid a rate
  threshold.
- Baseline: the same script with an empty entry mask, funding events
  still loaded. Flat must show 0 trades, funding_pnl 0, total_costs 0,
  Train-1 net 0. That 0 is the baseline. Do not use a catalog name mean
  as the baseline.

## Invalid unless funding is applied

Before any strategy score, reconcile one hold that contains exactly one
cached funding timestamp: engine funding_pnl must match
costs.funding_payment(direction, notional, rate) within 1e-9, and
net_pnl must equal gross_pnl - total_costs + funding_pnl. If
funding_events is empty, or a hold that covers a non-zero settlement
books funding_pnl == 0, write Result INVALID and stop. Do not label
(a) or (b). Do not report that run as evidence.

## Falsifiers

Score only Train-1. Per series, M = sum(funding_pnl) - sum(total_costs).
The reported figure is the unweighted mean of M across the five symbols.
Price gross_pnl is reported and cannot flip a fail into a pass.

- (a) mean M <= 0 (baseline 0).
- (b) one reversal day wipes the green days. A symbol-day (Europe/Warsaw,
  the regularity.py clock) is a reversal day if any settlement on that
  day has a sign different from the previous settlement. Attribute each
  trade funding_pnl - total_costs to the Warsaw day of the funding
  timestamp inside the hold; if the protective stop closes the trade with
  no funding event inside the hold, attribute -total_costs to the Warsaw
  day of the exit. Let W be the worst reversal-day sum across the five
  symbols, and G the sum of all positive day-level values. (b) fires if
  W <= -G.
- Both may fire. Label them literally. No other letters.

## decision_if_fail

Close funding-carry. No hold-length retune, no rate threshold, no fee
change, no symbol drop, no second interval. Spread-capture stays closed.
Do not start catalog mean-reversion. Do not invent another family. Do not
unfreeze a catalog name. Do not open holdout. The calendar-green goal
stays the owner goal; this card does not name a replacement mechanism.

## decision_if_pass

Worker does not promote and does not open Val-1. Leave Decision blank.
A pass is mean M > 0 and (b) not fired, with the reconciliation green
and funding events actually applied.

## Out of scope

Catalog signals, catalog mean-reversion, spread-capture, a new family,
holdout, validation, editing strategy.py on disk (runtime registration
only, the family-runner pattern), .pi/config.json, and
spec/features/active/F006-catalog5-unfreeze-correction/.

## Result

Run: `python3 scripts/f006_funding_carry.py` (funding cache written once by
`--fetch`; artifacts `output/f006_funding_carry/`). `number_of_trials = 1`,
60-minute Train-1 bars only (`f006_family_runner.load_train1`, checksums equal
the protocol section 6 values). Every arm passed the cached settlements as
`funding_events` into `backtest_engine.run_backtest`; the script refuses an
empty event list.

Funding cache: `data_cache/funding/<SYM>_funding_20240126T000000Z_20250301T000000Z.csv`
plus `data_cache/funding/manifest.json` (sha256 per file). Public Bybit v5
`/v5/market/funding/history`, category linear. 1200 settlements per symbol,
2024-01-26 00:00 to 2025-02-28 16:00 UTC, uniform 8h spacing, no gaps.
Mean settled rate +1.01 bp (BTC) to +1.36 bp (DOGE).

Timing as implemented. For settlement T_k: decision bar opens T_k-2h. r_prev
is the latest settlement before its close at T_k-1h, so it is T_{k-1}. Entry
fills at the T_k-1h open. The exit is a signal reversal on the bar opening at
T_k+1h. The engine records `exit_time` as that bar's index, so
`entry <= T_k < exit` and T_{k+1} = T_k+8h falls outside the hold. A
spot-check (SOLUSDT short, 2024-05-17 23:00 to 2024-05-18 01:00 UTC, r_prev
+0.0001 at 16:00) booked funding_pnl +0.01 = 100 × 0.0001.

Control (empty entry mask, 1200 events loaded per symbol): 0 trades, net 0,
final equity 500 on 5/5. Baseline = 0.

Reconciliation runs on every carry hold, before scoring. 5,418 holds contain
exactly one settlement. On each, engine funding_pnl equals
`costs.funding_payment(direction, notional, rate)` with max abs error 0.0.
`net = gross - costs + funding` holds with max abs error 0.0. No hold contains
two settlements. 248 holds (all initial_sl exits) closed before their
settlement and booked funding 0. Not INVALID.

| symbol | Train-1 trades | funding_pnl | total_costs | M | price gross | net |
|---|---|---|---|---|---|---|
| SOLUSDT | 1094 | +11.1153 | 350.0053 | -338.8900 | +38.7287 | -300.1613 |
| ETHUSDT | 1095 | +10.9344 | 350.3917 | -339.4573 | -0.8564 | -340.3137 |
| BTCUSDT | 1016 | +10.0208 | 325.1342 | -315.1134 | -35.3360 | -350.4494 |
| XRPUSDT | 1095 | +10.5913 | 350.4628 | -339.8715 | +40.0096 | -299.8619 |
| DOGEUSDT | 846 | +9.8945 | 270.8529 | -260.9583 | -90.7738 | -351.7321 |

**Mean M = -318.858103 <= 0. (a) FIRED.** On a 100 notional, one settlement
averages about +1 bp of funding. The round trip costs about 32 bps
(10+10 commission, 5+5 half-spread, 2 slippage), plus the effect of price
moves on exit notional.

(b): all 1716 Train-1 symbol-days are negative. G (sum of positive days) = 0.
The worst reversal day is W = -1.038216 (SOLUSDT, 2025-02-22). There are 520
reversal symbol-days. W <= -G, so **(b) FIRED**, trivially, because no day
was green.

**FALSIFIED (a)+(b).**

Note: the M figures for BTCUSDT and DOGEUSDT are truncated, not
re-weighted. The engine skips an entry once equity falls below the 100
margin (`InsufficientMarginError`, documented engine contract). DOGE equity
reached 98.02 on 2024-12-07 (249 skipped); BTC reached 99.57 on 2025-02-02
(78 skipped). Each skipped hold would have added about -0.3, so the verdict
cannot flip. Warm-up (Jan 26 to Feb 29 2024, scored separately) M is about
-32 per symbol.

## Decision

