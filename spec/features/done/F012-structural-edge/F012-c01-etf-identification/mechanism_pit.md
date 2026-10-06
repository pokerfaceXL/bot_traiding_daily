# F012-C01 — mechanism reconstruction + PIT timeline (Train-1: 2024-03-01 → 2025-03-01)

Verification legend: **[V]** checked in this run against a primary/issuer source;
**[M]** from prior knowledge of prospectuses, not re-verified here — confirm before relying.

## 1. Create/redeem chain during Train-1 (cash model)

| Stage | Time (ET) | Actor | What happens | Public? |
| --- | --- | --- | --- | --- |
| Order | by **18:00 ET on T-1** (IBIT "Cash Order Cutoff Time") **[V]** | AP → issuer/transfer agent | AP submits cash create/redeem order for trade date T | No (private) |
| AP hedge | T-1 evening → T session | AP / MM | AP is long/short ETF shares vs. investors; hedges with CME futures, perps or spot OTC **[M]** | No |
| Issuer execution | T, targeting the 16:00 ET benchmark; "trade-at-benchmark" fills concentrated in the 15:00–16:00 ET calculation window **[M]** | Issuer's bitcoin trading counterparty / prime broker (Coinbase Prime for most) | Buys (create) / sells (redeem) BTC for NAV | No |
| NAV | **16:00 ET T** | Issuer | NAV struck on benchmark rate | NAV yes, flow no |
| Shares/holdings files | evening T → morning T+1 | Issuer websites | Shares outstanding / BTC held | Yes |
| Farside row T | late T → morning T+1 (UK) | Farside | Issuer flow in $M + Total; same-day row blank/0.0 until filled | Yes |
| Settlement | T+1 | AP ↔ trust | Cash vs. shares | — |

Benchmarks (all struck 16:00 ET):

| Issuer | Fund | Benchmark | Notes |
| --- | --- | --- | --- |
| BlackRock | IBIT | CME CF BRRNY (15:00–16:00 ET calculation window) **[V]** | Dominant Train-1 flow; cash cutoff 18:00 ET T-1 **[V]** |
| Fidelity | FBTC | Fidelity Bitcoin Reference Rate **[M]** | Self-custody (Fidelity Digital Assets) **[M]** |
| Grayscale | GBTC / BTC (mini, from 2024-07-31) | CoinDesk Bitcoin Price Index (XBX) **[M]** | GBTC = structural redemption stock from 2024-01 conversion |
| ARK/21Shares | ARKB | CME CF BRRNY **[M]** | |
| Bitwise | BITB | CME CF BRRNY **[M]** | |
| VanEck / Franklin / Invesco / Valkyrie-CoinShares / WisdomTree | HODL / EZBC / BTCO / BRRR / BTCW | issuer-specific 16:00 ET reference rates **[M]** | Small Train-1 flows |
| Morgan Stanley | MSBT | — | Not listed in Train-1 (empty Farside column) |

Material per-issuer timing differences: benchmark constituent sets differ (CF vs CoinDesk vs
Fidelity), but every fund targets 16:00 ET, so the mechanically justified narrow window is
**15:00–16:00 ET on T** (the BRRNY window), matching the brief's sketch.

## 2. Effective dates / regime notes

| Date | Change | Train-1 effect |
| --- | --- | --- |
| 2024-01-11 | US spot BTC ETFs begin trading (cash-only creations) | Before Train-1 start; history only |
| 2024-07-31 | Grayscale BTC mini-trust launches (GBTC spin-off) **[M]** | Inside Train-1; adds `BTC` column |
| 2024-11-19 | IBIT options list **[M]** | Inside Train-1; extra MM hedging channel |
| **2025-07-29** | SEC approves **in-kind** creations/redemptions (IBIT in-kind cutoff 15:59 ET on T) **[V]** | **Post–Train-1** — regime note only: weakens the compulsory cash-buy at NAV; any Train-1 result would need a persistence check after it |

## 3. Who knows what, when (PIT)

Machine-readable table: `output/f012_c01_etf/pit_timeline.csv` (source / publication /
earliest-live timestamps for every candidate input).

Key consequence: the order that *creates* flow on T is fixed by 18:00 ET T-1, **before** the
public can see Farside row T-1. The public's best pre-window observable is therefore
row T-1 (and older) → Gate A is a persistence/forecasting question.

`earliest_live_availability_timestamp` of Farside row T-1 is set to **T 15:00 UTC**.
Evidence: the collector snapshot at 2026-10-06 14:52 UTC already held a complete
2026-10-05 row while the 2026-10-06 row showed 0.0 with blank issuers. Only one observed
vintage exists (collector began 2026-10-06); historical publication times are not recoverable
from free data, so this stamp is an assumption with ≥ 4 h margin before 15:00 ET (19:00/20:00 UTC).
The brief's ~20:00 UTC same-day stamp is **not** used: same-day rows are routinely incomplete.

Caveats:
- The Farside history is a current snapshot, not vintages; later revisions to past rows (if any)
  are invisible, which can only flatter Gate A.
- Same-day ETF trading and BTC moves after 09:30 ET T are excluded as predictors (they may
  reflect AP hedging). The overnight BTC return to 09:30 ET T is used only in a flagged model.
- No free PIT source for the official daily premium/discount file; a premium proxy built from
  IBIT close vs. Coinbase BTC at 16:00 ET (demeaned over 20 days) is used instead.
