# F012-C02 · Delisting forced-unwind falsification — decision: **FAIL**

> Primary cost hurdle = binding owner-tier RT **≈9.92 bp** (taker) / **≈5.12 bp** (maker).
> 34 bp is obsolete historical reference. See `F012-owner-cost-hurdle.md`.

Pre-registration: `spec/features/active/F012-c02-delisting-falsification/ticket.md` (commit `c48165a`).
Train-1 only (2024-03-01 → 2025-03-01 UTC). Code: `delisting_lab/`. Tables: `output/f012_c02_delisting/`.
Criteria were not changed after seeing data. Inference: cluster bootstrap on `day_batch_cluster_id`
(same exchange, announcements within 2h), 5000 draws, 95% CI. Returns are log returns in bp.

## Sample

| item | value |
|---|---|
| Train-1 perp delisting events (Bybit + Binance USD-M) | 82 |
| article clusters / day-batch clusters | 63 / 45 |
| usable events (p0 + primary entry + eff-1h exit) | **80** (missing-event rate **2.4%**: ZKUSDT, MONUSDT on Bybit) |
| usable article clusters / day-batch clusters | **61 / 44** (n≥40 target met on both) |
| usable events with same-token spot (identification) | 46 (Binance spot 34, Bybit spot 12) |
| spot-only delistings where perp kept trading (information-only comparator) | 8 |
| matched-control pool (Binance perps, lowest Feb-2024 liquidity, survived Train-1) | 40 |

Market data: Bybit `public.bybit.com/trading` tick archives → 1m + taker flow; Binance
`data.binance.vision` 1m klines + aggTrades; OI 5m; funding; BTC benchmark (β from 1h,
[ann−21d, ann−1d] only). Raw archives deleted after aggregation; free disk stayed ≥ 32.9 GB.

## H1 — announcement repricing, and how much is left after realistic latency

Entries anchored on `first_publicly_observable_ts` (never earlier). Long-sign CAR from the last
pre-announcement trade (subset `all`, n=80, 44 clusters):

| horizon from announcement | mean | median | 95% CI |
|---|---|---|---|
| pre-1d (before announcement) | −456 | −203 | [−751, −188] |
| first trade | −1 | 0 | [−4, +1] |
| +1m | −258 | −12 | [−445, −107] |
| +5m | −561 | −343 | [−760, −386] |
| +1h | −704 | −372 | [−1004, −435] |
| +24h | −990 | −523 | [−1505, −501] |
| eff−1h | −1705 | −1104 | [−2547, −878] |

Share of the announcement→eff−1h move that is gone before entry (mean pre-entry CAR / mean total):
10s 25% · 30s 30% · 60s 33% · bar1m 36% · bar5m 37%. Two-thirds of the decline happens AFTER
any realistic entry, so H1's narrow statement (negative repricing remains tradeable after
observability) holds in raw terms:

| short from latency → eff−1h (raw) | mean | median | 95% CI | minus matched ctrl |
|---|---|---|---|---|
| 10s | +1168 | +896 | [+429, +1925] | – |
| 60s | +1037 | +762 | [+285, +1813] | +924 [+300, +1555] |
| bar1m | +988 | +737 | [+250, +1780] | – |
| bar5m (primary) | +972 | +620 | [+242, +1728] | +872 [+239, +1514] |
| bar5m → +24h | +389 | +159 | [+36, +743] | +343 [+48, +640] |

Time-scrambled placebo (same symbol, pseudo-announcements in [ann−21d, ann−4d]): event-minus-placebo
paired mean +316 bp at +24h (Wilcoxon p=0.099) and +540 bp at +72h (p=0.130) — **not credible vs
placebo** at the pre-registered short horizons.

## H2 — pre-deadline forced unwind beyond the announcement repricing

Abnormal (β-adjusted) long-sign drift, subset `all`:

| window | mean | median | 95% CI | vs matched ctrl |
|---|---|---|---|---|
| ann+24h → eff−1h | −740 | −562 | [−1370, −184] | −692 [−1262, −127] |
| **eff−24h → eff−1h** (deadline approach) | −93 | −220 | [−327, +139] | −166 [−476, +118] |
| eff−1h → eff−1m | −44 | +9 | [−185, +64] | – |

OI falls to median 0.88× pre-announcement after 24h and 0.52× at eff−1h, but OI decay does **not**
predict subsequent return: Spearman(oi_norm_24h, drift ann+24h→eff−1h) = 0.013 (p=0.91, n=79).
Taker flow imbalance from ann+4h → eff is ≈0 (mean −0.005). The deadline window itself shows no
significant drift. **H2 FAIL.**

## Identification — perp vs same-token spot (CRITICAL)

46 usable events have spot 1m; 39 are perp-only delistings with spot still listed.

| group | metric | n | mean | median | 95% CI |
|---|---|---|---|---|---|
| all with spot | perp CAR +24h / spot CAR +24h | 46 | −940 / −833 | −460 / −467 | – |
| all with spot | perp CAR eff−1h / spot CAR eff−1h | 46 | −1800 / −1807 | −1108 / −1130 | – |
| all with spot | **perp − spot, ann+24h → eff−1h** | 45 | **+119** | +10 | [−63, +458] |
| perp-only delist | perp − spot, ann+24h → eff−1h | 38 | +130 | +7 | [−85, +537] |
| all with spot | basis (multiplier-adjusted) pre / 24h / eff−24h / eff−1h, median | 46 | – | 0 / −8 / 0 / +6 | – |
| spot-only delist, perp continues (no forced unwind) | CAR eff−1h | 8 | −2020 | −1441 | – |
| spot-only delist, perp continues | drift ann+24h → eff−1h | 8 | −3 | +9 | – |

Spot and perp fall together, by the same amount, through the whole notice window. The derivative
does not underperform spot as OI→0 (point estimate is the wrong sign for forced selling), the
basis stays ≈0, and taker flow is balanced. Tokens whose SPOT is delisted while the perp keeps
trading fall just as hard. The post-announcement decline is an **information / delisting-stigma
effect on the token**, not a derivative forced-flow effect. Per the pre-registration: "Evidence for
the first without the second = FAILURE of the forced-flow hypothesis, even if a naive
announcement-short backtest is profitable."

## Costs — PRIMARY = binding owner-tier RT (≈9.92 taker / ≈5.12 maker)

Owner correction 2026-10-06: Derivatives fees are BINDING. See
`spec/research/F012-owner-cost-hurdle.md`. Primary go/no-go uses basket
owner-tier RT = 2×(fee + 0.56 bp half-spread+impact) → **9.92 bp taker**, **5.12 bp maker**.
Stress: 50/75/100. **34 bp is historical-reference only (obsolete for owner decisions).**
Tables: `costs_primary.csv`, `costs_latency_owner_primary.csv`, `costs_owner_primary.csv`.
Event-measured delisting-asset spreads (median ~22 bp RT) are secondary only
(`costs_event_measured_secondary.csv` if present) — not the primary hurdle.

Primary family: short at bar5m entry. Funding carry on these names is a cost to shorts
(mean −116 bp to eff−1h).

| subset | exit | owner taker 9.92 mean / median / 95% CI | + funding mean | maker 5.12 mean |
|---|---|---|---|---|
| all | +24h | +379 / +150 / [+20, +723] | +342 | +384 |
| all | **eff−1h** | **+962 / +610 / [+240, +1716]** | **+847** | **+967** |

Stress 50/75/100 at eff−1h (all): mean +922 / +897 / +872. Venue-split remains non-significant alone.

**Cost hurdle does not flip the decision:** even at ~9.9 bp the FAIL rests on failed
identification (perp−spot≈0), H2 (deadline drift CI includes 0), placebo, and venue instability —
not on the old 34 bp floor.

## Tail concentration (bar5m short → eff−1h, **owner taker 9.92 bp RT**, `tails_primary.csv`)

| subset | n | mean | median | trim10 | win | top1/3/5 share of sum | mean ex top1/3/5 |
|---|---|---|---|---|---|---|---|
| all | 80 | +922 | +570 | +794 | 66% | 14% / 32% / 48% | +802 / +647 / +508 |
| tokens ex migration ex index | 66 | +1274 | +782 | +1141 | 70% | 12% / 28% / 42% | +1133 / +955 / +794 |

Top events: AMB@bybit, REEF@bybit, OMG@binance, AMB@binance, AKRO@bybit. q5 = −3046 bp.

## Exploratory conditioning (not confirmatory)

Pre-announcement funding > 0 (65 events) vs ≤ 0 (15): mean post-24h drift −822 vs −389 bp;
Spearman(funding, drift) −0.25 (p=0.03). Pre-7d trend: ρ=+0.24 (p=0.04) — prior losers keep
falling. Migration/redenomination events (12) show no decline (+65 bp). Notice duration, OI vs
3-day history and liquidity: no relationship. With one-shot exploratory tests these do not
support a pre-event positioning condition for an unwind direction.

## Decision against the pre-registered criteria

| criterion | result |
|---|---|
| ≥40 usable independent clusters | met (44 day-batch / 61 article) |
| economically meaningful effect | met for the naive hold-to-eff−1h short |
| credible vs matched control | met vs matched controls; **not met** vs time-scrambled placebo (p 0.10/0.13) |
| positive after realistic costs (owner-tier ~9.9) | eff−1h pooled survives owner RT + funding; **does not rescue FAIL** |
| not driven by a handful of tokens | met (ex-top5 still +508 bp) |
| stable across Binance/Bybit | **not met** (neither venue significant alone; Binance medians negative short-horizon) |
| separation announcement vs subsequent drift | drift continues post-entry, but it is common to spot → informational |
| forced-unwind identification (MOST IMPORTANT for C02) | **not met**: perp − spot ≈ 0 (+119 bp, wrong sign), basis ≈ 0, flow balanced, OI decay non-predictive, spot-only delistings fall as much |

**FAIL** (reaffirmed after owner-tier ~9.9 bp primary recompute). The C02 mechanism — a known
derivative shutdown deadline creating additional predictable flow after information is in spot —
is not present. The naive post-announcement short remains profitable at owner-tier RT because
delisted tokens keep losing value on spot and perp alike; that is an information/stigma drift, not
the pre-registered forced-unwind edge, and it fails identification, H2, venue stability and the
placebo test. Lowering the hurdle from 34→9.9 bp does not change those failures. C02 is archived.
Per the ticket, no optimization; C01/C03 not started.

## Reproduce

```
python3 -m delisting_lab.market_data     # resumable, skips cached events, disk floor 15 GB
python3 -m delisting_lab.controls        # matched-control pool
python3 -m delisting_lab.run_study       # writes output/f012_c02_delisting/*
```
