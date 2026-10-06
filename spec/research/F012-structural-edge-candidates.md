# F012 · Structural-edge candidate selection

> Research phase only. **No strategy implementation. No backtest. No trading.**
> Owner brief 2026-10-06. F011 forced-flow / liquidation cascades is **ARCHIVED**
> (do not continue; do not buy liquidation data; do not touch `f011-liq-collector`).
>
> Lesson from F011: identifying a forced participant is useless if we only see them
> **after** price has already absorbed the flow.
>
> Thesis: find participants whose future trading becomes constrained, predictable,
> or mechanically necessary when observable conditions occur — and ask whether we
> can observe the **cause** before the flow is priced.
>
> Central question: **WHO must buy or sell, WHY, WHEN, and can we see the cause early enough?**

Generated 2026-10-06 Europe/Warsaw (UTC+2) by the F012 research phase on limen /
research box. Empirical probes: Bybit, Deribit, Farside, Coinbase, Upbit, Binance
(from limen; box is geo-restricted for Binance), HypurrScan, SEC EDGAR, DefiLlama.
No paid services signed up; nothing purchased.

---

## 0. Binding context and closed results (do not re-propose)

| Prior result | Status | Implication for F012 |
| --- | --- | --- |
| Catalog candle trend (6 names) | FREEZE | No RSI/MACD/MA/candle families |
| Catalog mean reversion | negative | No generic MR |
| Funding carry | FALSIFIED | Do not re-open pure carry |
| Spread capture | CLOSED (spread ≪ 17 bp/side) | Do not chase inside-spread |
| 1h OI fade | FALSIFIED | Do not re-open OI-fade |
| F011 5m cascade / exhaustion | 0/132 cells beat 34 bp; ARCHIVE | No liquidation-cascade strategy |
| Bybit–Binance 5m basis | \|basis\| p95 ≈ 4–5 bp; >34 bp rare | No 5m cross-venue level arb |
| Tick lead-lag | Out of latency league | No HFT venue race |

**Cost hurdle (binding):** 34 bp round trip = 10 commission + 5 half-spread + 2 slippage
**per side**. Sensitivity note: Bybit VIP0 USDT-perp is 5.5 bp taker / 2 bp maker
([fee structure](https://www.bybit.com/en/help-center/article/Trading-Fee-Structure));
where useful we quote a one-line net at measured realistic costs, but **34 bp remains
the go/no-go hurdle**.

**Data split (F005, frozen):** Train-1 = 2024-03-01 → 2025-03-01 UTC (warm-up from
2024-01-26). Validation windows 1–4 and Holdout 2026-03 → 2026-09 stay **untouched**.
F012 falsification uses **Train-1 only**.

---

## 1. Candidate generation (≥10 structural mechanisms)

No indicators. Each candidate is a **participant + constraint + observable cause**.
Willingness to reject all is preserved through §7.

| ID | Mechanism (short name) | Domain |
| --- | --- | --- |
| C01 | Spot ETF NAV-window AP hedging conditioned on prior-day public flow | US spot BTC/ETH ETF |
| C02 | Exchange delisting forced unwind | Bybit/Binance perps |
| C03 | Token unlock / vesting cliff supply | Mid-cap tokens |
| C04 | Deribit max-pain pinning at options expiry | Options |
| C05 | Deribit dealer charm/gamma hedging into expiry | Options |
| C06 | Dated-futures basis convergence into delivery | Bybit/Binance/CME quarterlies |
| C07 | Perp funding settlement clock microstructure | Perps |
| C08 | Funding/basis arb unwind when funding flips | Perps |
| C09 | Spot/perp dislocation mean-revert / lead-lag | Cross-product |
| C10 | Stablecoin mint/burn → spot buy/sell | On-chain stables |
| C11 | Coinbase premium / Upbit Kimchi lead-lag | Cross-venue |
| C12 | Corporate treasury ATM buying (MSTR-style) after 8-K | Equities→BTC |
| C13 | Miner scheduled selling | Hashrate/rewards |
| C14 | Vol-targeting / systematic deleveraging | Systematic funds |
| C15 | Hyperliquid public TWAP remaining-slice flow | On-chain L1 perps |
| C16 | Crypto index / benchmark rebalancing | Index |

Supporting scoreboard: `output/f012_candidates/scoring.csv`.

---

## 2. Causal chains and the 11 questions

For each candidate: OBSERVABLE CONDITION → PARTICIPANT CONSTRAINED → MECHANICAL
INCENTIVE/OBLIGATION → EXPECTED FLOW → EXPECTED IMPACT → TRADEABLE WINDOW.
Any candidate that cannot answer the 11 questions convincingly is rejected in §3.

### C01 — Spot ETF NAV-window AP hedging (prior-day flow)

**Chain.** Day-t US spot ETF net flow becomes public (Farside / issuer sites, after
US cash close). Authorized participants (APs) who must create/redeem against a NAV
tied to the CME CF BRRNY / IBIT VWAP **3–4pm ET** window are expected to buy (create)
or sell (redeem) bitcoin/ether in that hour on day t+1 (and hedge via CME). Prior
flow persists (empirical AC1 ≈ 0.53 on BTC Farside totals; see §4 probes), so day-t
flow is a pre-flow signal for day-t+1 NAV-window pressure.

| # | Answer |
| --- | --- |
| 1 Who | APs / ETF issuers hedging cash (pre Jul-2025) or in-kind (post) creations/redemptions |
| 2 Why | Must deliver NAV-accurate BTC/ETH for baskets; inventory risk around the fix |
| 3 Cause | Prior-day net creation/redemption demand (public flow print) |
| 4 When | Next US session 15:00–16:00 America/New_York |
| 5 Direction | Sign(prior-day net flow): + → buy pressure; − → sell |
| 6 Size | Farside BTC Train-1: median \|Total\| ≈ **$168M/day**, p90 ≈ **$588M**, max ~$1.4B (probe 2026-10-06). Bybit BTCUSDT 24h turnover probe ≈ **$3.8B**; Binance fapi 24h quote ≈ **$9.4B**. A $200–600M directional AP window is order 2–15% of venue day volume → plausible multi-bp impact, not guaranteed ≥34 bp |
| 7 Observable before | Day-t Farside/issuer totals; ETF share volume; CME BTIC/fix activity |
| 8 Lead | ~15–20h from evening flow print to next 15:00 ET |
| 9 Not priced? | Contested. Coinbase Institutional notes 3–4pm ET volume surge after ETF launch; SSRN 7545019 finds **lagged flows do not positively predict returns once the return window starts after the flow is public** — returns lead flows more than flows lead returns |
| 10 Who arbs | APs themselves, CME basis desks, systematic "ETF flow" funds |
| 11 Persist? | Mechanical NAV window persists, but **in-kind creations approved 2025-07-29** (SEC) weaken cash-buy compulsion; flow→return channel may be thinner post-change |

**Anti-F011 class: A (PRE-FLOW)** if entry is after day-t print and before day-t+1 15:00 ET.
**Risk:** already studied; regime break Jul-2025.

### C02 — Exchange delisting forced unwind

**Chain.** Venue publishes a delisting notice at T with last-trade / settlement at T+Δ.
Holders of the perpetual (and often spot) **must** close or be force-settled. Between
T and T+Δ the market faces predictable inventory liquidation, typically net selling of
longs and covering of shorts into settlement rules (venue-specific).

| # | Answer |
| --- | --- |
| 1 Who | Open-interest holders on the named contract; MMs providing exit liquidity |
| 2 Why | Contract ceases; remaining positions are settled/cancelled under exchange rules |
| 3 Cause | Official delisting/removal announcement with effective timestamp |
| 4 When | From first public notice through last trade / delivery; often multi-day |
| 5 Direction | Primary: short the named perp after announcement (sell pressure into unwind). Secondary: fade overshoot into settlement if shorts cover |
| 6 Size | Entire OI of the contract must exit. Example scale: mid-cap Bybit perps often $5–100M OI vs thin depth; forced flow ≫ normal day volume near the deadline. Majors almost never delist |
| 7 Observable before | Announcement title + body + effective time (Bybit announcements API; Binance CMS catalog 161; archive pages) |
| 8 Lead | Empirically often **2–14 days** (Bybit delist notices probed 2026-10; Binance catalog 161 has full history from 2022-02, 439 articles, 76 in Train-1) |
| 9 Not priced? | Headline is public; first minutes are priced. Residual edge, if any, is in **multi-day forced inventory** and settlement mechanics, not surprise |
| 10 Who arbs | Event-driven alts desks, MM inventory desks |
| 11 Persist? | Venues continuously list/delist; rules remain. Survivorship of symbols in live APIs is a data hazard (mitigated by Bybit trade archive retaining delisted CSVs, e.g. LOOMUSDT, MATICUSDT still listed under `public.bybit.com/trading/`) |

**Anti-F011 class: A (PRE-FLOW).**
**Cleanest causal forced-flow among free datasets.** Product caveat: edge lives on
doomed alts, not the current liquid basket — F012 tests the **thesis**, not yet the
production basket.

### C03 — Token unlock / vesting cliff

**Chain.** Public vesting schedule makes large recipient cohorts (team, investors,
ecosystem) able to sell at known UTC dates. Keyrock study of >16k unlocks: ~90%
negative for price; declines often begin ~30 days **before** the cliff (front-running
+ hedging); team unlocks worst (~−25% avg in their cut).

| # | Answer |
| --- | --- |
| 1 Who | Unlock recipients (team / VC / ecosystem) and hedgers of unlock inventory |
| 2 Why | Newly liquid tokens; often compensation/treasury needs (team) or portfolio rules (funds) — **ability**, not always obligation |
| 3 Cause | Calendar unlock / emission event |
| 4 When | Concentrated in days −30…+14 around cliff (literature); largest mechanical spot hits near cliff for unsophisticated sellers |
| 5 Direction | Net sell pressure into/around unlock |
| 6 Size | Weekly unlocks often cited ~$600M aggregate; single cliffs can be several % of float |
| 7 Observable before | Schedules (Tokenomist, Messari Token Unlocks — **paid**); project docs / TokenUnlocks.datepicker scrapes (fragile) |
| 8 Lead | Weeks (schedule) ; economic lead may already be in price 30d prior |
| 9 Not priced? | Largely anticipated; Keyrock's own advice is exit −30d / re-enter +14d — that path is crowded |
| 10 Who arbs | Unlock calendars, MM OTC desks, funds hedging with perps |
| 11 Persist? | Vesting calendars continue, but datasets are commercial and pre-pricing intensifies |

**Anti-F011 class: A**, but soft constraint + paid data + already-priced risk.

### C04 — Deribit max-pain pinning

Max pain = strike minimising aggregate option-holder intrinsic. Folklore: dealers pin spot there.

| # | Answer (compressed) |
| --- | --- |
| 1–5 | Dealers? / pin to K* / at expiry / toward K* — **identity of side unknown from OI alone** |
| 6 | BTC options OI probe 2026-10-06: ~358k BTC contracts across chain; large monthlies dominate |
| 7–8 | OI snapshot hours before expiry |
| 9–11 | Cayø Largo (2026-09): **919 Deribit expiries** — settlement nearer to **spot 6h earlier** than to max pain (median 0.53% vs 1.23%; max pain closer only 24.3%). Weak ~55% tilt 1d out, gone by 6h. **Rejected.** |

**Class: C (POST/definitional).** Reject.

### C05 — Deribit dealer charm / gamma hedging

| # | Answer |
| --- | --- |
| 1 Who | Option dealers hedging delta as charm/gamma concentrates |
| 2 Why | Inventory risk / Greek neutrality mandates |
| 3 Cause | Expiry proximity + signed dealer exposure |
| 4–5 | Into expiry; sign(dealer gamma/charm) — **not observable from public OI** |
| 6 | Potentially large on monthly BTC/ETH expiries |
| 7 | Need dealer sign or taker-flow-signed exposure (commercial / hard) |
| 8 | Hours to 1–2 days |
| 9–11 | Equity literature shows positioning effects; crypto public data lacks dealer sign. Without it, this collapses toward C04. **Reject until signed exposure exists.** |

**Class: A in theory, data-infeasible → reject for F012.**

### C06 — Dated-futures basis → delivery

| # | Answer |
| --- | --- |
| 1–5 | Basis traders / hedgers roll or deliver into expiry; basis → 0 |
| 6 | **Fatal:** Bybit BTCUSDT-25DEC26 OI ≈ **$18M** vs BTCUSDT perp OI ≈ **$4.9B** (probe). Binance BTCUSDT_261225 OI ≈ 584 BTC vs perp ~95k BTC. Flow too small vs 34 bp on the liquid perp we trade |
| 7–11 | Schedules free; effect real but capacity inadequate |

**Class: A. Reject on magnitude/capacity.**

### C07 — Funding settlement clock

| # | Answer |
| --- | --- |
| 1–5 | Crowded side pays funding at 00/08/16 UTC (Bybit/Binance default); inventory shuffle around stamps |
| 6 | Funding transfers are large in aggregate but **per-stamp price move** historically unstable (public event studies; project already FALSIFIED pure funding carry) |
| 7–8 | Clock is known with certainty; rate known ~hours ahead on Bybit |
| 9–11 | Crowded, low residual after costs |

**Class: B. Reject** (re-opens closed carry family without a new constraint).

### C08 — Funding/basis arb unwind

When funding flips from rich to poor, cash-and-carry books unwind. Related to C07/closed carry.
**Class: B. Reject** as insufficiently new vs closed results.

### C09 — Spot/perp dislocation

Prior F011 basis work: 5m Bybit–Binance \|basis\| p95 4–5 bp. **Reject.** Class B/C.

### C10 — Stablecoin mint/burn

USDC/USDT/USDe supply changes (DefiLlama free daily history deep — USDT tokens series from 2017, 3234 daily points probed). Mint often **follows** demand (POST or simultaneous). Lead minutes on-chain ≠ reliable ≥34 bp on Bybit BTC after costs.
**Class: A weak. Reject** for lead/priced ambiguity.

### C11 — Coinbase / Upbit premium lead-lag

Coinbase BTC-USD 5m history exists (probe 2018+). Upbit KRW-BTC 5m exists. Premium is observable, but trading the **reaction on Bybit** is a latency/arb game; prior basis study kills slow versions.
**Class: B. Reject.**

### C12 — MSTR-style treasury ATM after 8-K

SEC EDGAR CIK 0001050446: 48 Form 8-K in Train-1; many accepted ~17:00–18:00 UTC (after US cash). Filings often **report already-executed** BTC purchases → mostly **POST-FLOW**.
**Class: C. Reject.**

### C13 — Miner selling

Hashprice / difficulty known, but "must sell" is soft and wallets are opaque.
**Class: C. Reject.**

### C14 — Vol-targeting deleveraging

Realized vol spike → systematic funds cut risk. Participant set diffuse; crypto AUM in classic vol-target is unclear; signal overlaps price.
**Class: B. Reject** for F012 (may revisit with named fund flow data).

### C15 — Hyperliquid public TWAP

Once a TWAP is posted on HL, remaining slices are mechanical. HypurrScan `GET /twap/*` returned **573** recent TWAP records, **345** without `ended`/`error` (probe). Active BTC (asset 0) TWAP gross daily rate ≈ **$5.2M/day** vs HL/major CEX day volumes of hundreds of millions to billions → **too small** on BTC; also **wrong venue** for our Bybit bot unless we assume cross-venue impact.
**Class: A. Reject on magnitude + venue.**

### C16 — Index rebalance

Scheduled; free calendars sparse; crypto index AUM historically small vs spot/perp liquidity.
**Class: A. Reject on magnitude.**

---

## 3. Anti-F011 filter summary

| ID | Name | Class | Survive? | One-line reason |
| --- | --- | --- | --- | --- |
| C01 | ETF NAV-window × prior flow | A | **YES** | Pre-flow public print; large $; literature mixed; regime break Jul-2025 |
| C02 | Delisting forced unwind | A | **YES** | Clearest free forced-flow with announcement lead |
| C03 | Token unlock cliff | A | **YES** | Calendar pre-flow; soft constraint; paid data; pre-priced |
| C04 | Max-pain pin | C | no | Empirically loses to "spot already there" |
| C05 | Dealer charm/gamma | A* | no | Needs dealer sign we do not have |
| C06 | Dated futures expiry | A | no | OI ≪ perp; capacity fail |
| C07 | Funding clock | B | no | Re-opens closed carry; impact < hurdle likely |
| C08 | Funding/basis unwind | B | no | Not new vs closed carry |
| C09 | Spot/perp dislocation | B | no | F011 basis already killed 5m level |
| C10 | Stablecoin mint/burn | A | no | Lead ambiguous; often simultaneous |
| C11 | CB/Upbit premium | B | no | Latency league / prior basis |
| C12 | MSTR 8-K | C | no | Filings often post-purchase |
| C13 | Miner sell | C | no | Constraint soft; wallets opaque |
| C14 | Vol-target delever | B | no | Diffuse participant; weak crypto ID |
| C15 | HL public TWAP | A | no | BTC TWAP << liquidity; wrong venue |
| C16 | Index rebalance | A | no | Capacity |

\*C05 is theoretically A but operationally rejected for data.

---

## 4. Data feasibility (survivors) + empirical verification

### Already available in project

| Dataset | Fields | Res | Depth | Notes |
| --- | --- | --- | --- | --- |
| `output/f011_forced_flow/frame_5m/{BTC,ETH}USDT.csv.gz` | Bybit OHLCV, OI, L/S, funding, taker flow; Binance `bn_*` | 5m | Train-1 (~800d) | Point-in-time via `available_at`; liq cols empty historically |
| `data_cache/*_60_*` / `*_240_*` | OHLCV | 1h/4h | warm-up→holdout | 5 liquid USDT perps |
| `data_cache/funding/` | funding_rate | 8h | Train-1 | 0 gaps in coverage report |
| Live Bybit allLiquidation | liq events | tick | since 2026-10-05 19:26Z | **Do not touch collector**; unused for F012 |

### Free-public (verified with probes)

| Dataset | Source | Fields | Res | Hist depth | Reliability | Gaps | Size est. | PIT? | Look-ahead risks | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| US spot BTC/ETH ETF daily flows | [farside.co.uk](https://farside.co.uk/bitcoin-etf-flow-all-data/) (HTML table) | per-issuer + Total $M | daily | BTC from **2024-01-11** (702 rows to 2026-10-06); ETH from **2024-07-23** (564 rows) | Good; same source widely cited | Weekends/holidays blank; same-day row often "-" until publish | <100 KB/CSV | Day-t Total known only after US close / Farside update — **must lag to next session** | Using same-day Total with UTC midnight candle = look-ahead | $0 |
| Bybit delist/list announcements | `GET /v5/announcements` (type=delistings); total **482** | title, ts, url | event | Multi-year | Official | Pagination/rate limits | KB–MB | Announcement `dateTimestamp` is PIT | Parsing effective time from body needs care | $0 |
| Binance delist catalog | CMS `catalogId=161` | title, releaseDate, code | event | From **2022-02-17**, 439 articles; **76 in Train-1** | Official | HTTP 429 under fast paging (observed) | KB–MB | releaseDate PIT | Title≠effective time | $0 |
| Bybit trade archive (incl. delisted) | `public.bybit.com/trading/<SYMBOL>/` | tick trades | tick | e.g. LOOMUSDT 2023-09→2024-09; MATICUSDT 2021-06→2024-09 still listed | High | Large downloads — **do not bulk-pull**; sample days only | GB/symbol | Tick time PIT | Selecting only "interesting" delists after seeing outcomes = bias | $0 |
| Bybit instruments (Closed) | `/v5/market/instruments-info?status=Closed` | symbol, launch/delivery | meta | 1000+ closed linears returned | High | REST does not return klines for delisted (`LOOMUSDT` kline list empty) — use archive | small | status now ≠ PIT list | Survivorship if universe = currently Trading only | $0 |
| Deribit option book summary | `/public/get_book_summary_by_currency` | OI, mark, bid/ask, underlying per instrument | snapshot | Live; trades history API returns 2019+ samples | High | No free historical OI surface — **collect-forward** | ~400 KB/raw snap; slim+gz much less | Snapshot time PIT | Rebuilding past GEX from trades alone is lossy | $0 |
| Deribit option trades history | `history.deribit.com/.../get_last_trades_by_currency_and_time` | trade tape | tick | Probe: BTC options **2024-06-12 ≈ 18.4k trades / 19 reqs** | High | Heavy to backfill full Train-1 | ~tens of GB if full | Trade ts PIT | — | $0 |
| Coinbase BTC-USD candles | Exchange API | OHLCV | 1m/5m | Probe: 2018-01 works | High | Rate limits | moderate | Candle open PIT | — | $0 |
| Upbit KRW-BTC candles | Upbit API | OHLCV | 5m | Probe Train-1 OK | High | KRW FX needed for premium | moderate | PIT | — | $0 |
| DefiLlama stablecoin supply | `stablecoins.llama.fi` | circulating daily | daily | USDT from 2017 (3234 pts) | Good | Emissions/unlocks API **402 paid** | MB | Daily close PIT | — | $0 free; unlocks paid |
| SEC EDGAR submissions | `data.sec.gov` | 8-K acceptance times | event | MSTR/Strategy 211 recent 8-K; 48 in Train-1 | Official | User-Agent required | KB | acceptanceDateTime PIT | Body may describe past buys | $0 |

### Collect-forward (recommended)

| Dataset | Why | Cap |
| --- | --- | --- |
| Slim Deribit BTC/ETH option book summaries | Enables any future options-constraint work; free only live | **2 GB** hard + free-space stop |
| Daily Farside BTC/ETH flow snapshot | Tiny; keeps survivor C01 point-in-time without hand downloads | ≪1 MB |

### Paid (do **not** buy now)

| Vendor | Use | Notes |
| --- | --- | --- |
| Tokenomist / Messari Token Unlocks | C03 schedules | Free trial exists; not activated |
| Laevitas / Amberdata / similar | Dealer-signed GEX | Needed for C05 |
| Coinglass historical liq | F011 path | **NO-GO** per archive decision |

### Probe log (what was actually hit)

1. **Farside BTC/ETH HTML** — HTTP 200; pandas `read_html`; BTC AC1(Total)=0.531, sign-persist=0.674 on Train-1; ETH shorter, AC1=0.393 on Train-1.
2. **Bybit tickers** — BTCUSDT OI value ~$4.9B, 24h turnover ~$3.8B; dated futures OI $2–19M.
3. **Binance fapi from limen** — BTCUSDT 24h quoteVolume ~$9.4B; box geo-blocked.
4. **Deribit book summary** — 940 BTC option instruments; total OI ~358k BTC.
5. **Deribit history trades** — 2019-01 and 2024-03 windows return trades; day-count probe above.
6. **HypurrScan `/twap/*`** — 573 rows / 345 active; BTC TWAP ~$5.2M/day gross.
7. **Bybit announcements** — delistings total 482; Closed instruments 1000+; archive retains delisted CSVs; REST kline empty for delisted.
8. **Binance CMS 161** — 439 delist articles, earliest 2022-02-17; 76 in Train-1; rate-limit 429 under aggressive paging.
9. **SEC EDGAR MSTR** — 48 Train-1 8-K; acceptance hours cluster ~17–18 UTC.
10. **DefiLlama** — stables free; `/emissions` → 402 paid.
11. **Coinbase / Upbit** — historical candles OK.

Artifacts: `output/f012_candidates/farside_{BTC,ETH}_daily_total.csv`, `scoring.csv`.

---

## 5. Scoring (survivors) — decision support only

Scale 0–5 on 14 criteria (higher better; complexity & paid-dependence & already-priced are **inverted** so 5 = easy/cheap/not-priced).

| Criterion | C02 Delist | C01 ETF NAV | C03 Unlock |
| --- | --- | --- | --- |
| 1 Causal strength | 5 | 3 | 3 |
| 2 Signal before flow | 5 | 4 | 5 |
| 3 Lead time | 4 | 3 | 5 |
| 4 Flow magnitude | 4 | 5 | 4 |
| 5 Data quality | 4 | 4 | 2 |
| 6 Historical availability | 4 | 4 | 2 |
| 7 Backtestability | 4 | 4 | 2 |
| 8 Persistence | 4 | 2 | 4 |
| 9 Capacity / liquidity | 2 | 5 | 3 |
| 10 Robustness BTC/ETH/markets | 1 | 3 | 3 |
| 11 Impl. complexity (inv) | 4 | 3 | 3 |
| 12 Paid-data dependence (inv) | 5 | 5 | 1 |
| 13 Already-priced risk (inv) | 3 | 2 | 2 |
| 14 Edge vs 34 bp (ex ante) | 3 | 2 | 3 |
| **Total** | **52** | **49** | **42** |

### Qualitative assessment (formula does **not** pick the winner)

**C02 Delisting — strongest causal test of the F012 thesis.**
The announcement is an unambiguous constraint with multi-day lead, free event data,
and a trade archive that **retains delisted symbols** (survivorship solvable). The
score is dragged down by capacity (alts) and near-zero BTC/ETH robustness — this may
never be a production sleeve on the current basket. It is still the right **first
falsification**: if even this forced unwind cannot clear 34 bp net, weaker A-class
stories are unlikely to.

**C01 ETF NAV-window — best product-fit survivor, weakest identification.**
Dollar flows are enormous and the 15:00–16:00 ET window is a real microstructure fact
(Coinbase Institutional; CME volume share). But identification of **directional** edge
from **lagged public** flows is disputed (SSRN 7545019), and in-kind (2025-07-29)
breaks the cash-AP channel that made the story cleanest. Treat as second priority:
cheap to test on Train-1 overlapping Jan-2024+, but expect a high chance of kill.

**C03 Token unlocks — calendar A-class with commercial data gravity.**
Literature is supportive of negative drift, but the drift starts a month early (so
"observe before priced" is partially false), and clean schedules are paid. Keep as
third only if C02/C01 both die and the owner accepts a paid-data decision later.

---

## 6. Falsification tests — top 3 (cheapest kill experiments)

Shared rules for all three:

- **H0:** no economically meaningful edge after costs.
- **H1:** mechanism creates measurable, tradeable effect.
- **Costs:** 34 bp RT binding; also report net at Bybit VIP0 taker 5.5×2 + 5 half-spread + 2 slip = **25 bp RT** as sensitivity only.
- **Slippage:** +2 bp/side already in the 34 bp pack; no extra unless ADV fraction >1% (then scale slip = 2 × max(1, notional/(0.01·ADV))).
- **Split:** Train-1 only for this kill test. Validation/holdout untouched.
- **No** parameter optimisation, **no** threshold grids, **no** ML.
- Always report **gross** and **net** mean return per event (bps). **No Sharpe / win-rate hiding.**
- Clustered events: collapse to one event per (symbol, announcement_id) or per day as defined; Newey–West / block bootstrap for CIs.
- BTC/ETH correlation: for multi-asset panels, report BTC-beta residual returns as robustness, not as a free look.

### F012 primary — C02 Delisting forced unwind

| Item | Definition |
| --- | --- |
| **Event** | Bybit (primary) or Binance linear/perp **delisting announcement** in Train-1 with parseable `effective_ts` > `announce_ts` |
| **Signal timestamp** | `announce_ts` = official release time (API `dateTimestamp` / CMS `releaseDate`) |
| **Entry timestamp** | First **closed** 5m/1h bar open **strictly after** `announce_ts` on the named symbol (Bybit archive). If only daily bars, next UTC day open |
| **Horizons** | Hold to (a) +24h, (b) +72h, (c) midpoint to effective, (d) 1h before effective — **four pre-registered, not a grid** |
| **Direction** | Primary registered trade: **short** the delisted perp from entry through horizon (forced long unwind hypothesis). Secondary diagnostic (not a pass gate): long into final 24h before effective (short-cover) |
| **Control** | Matched non-delisted same-sector / similar ADV symbols on same entry timestamps; and time-scrambled announce dates within Train-1 |
| **Min sample** | **n ≥ 40** independent Bybit USDT-perp delist events in Train-1 with archive coverage; if n<40, expand with Binance CMS-161 perpetual delists that have Bybit-traded mirrors, still requiring PIT announce |
| **Independence** | One event per (venue, symbol, effective_day); multi-symbol batch announcements → one event per symbol but cluster-adjust by announcement_id |
| **Success** | Net mean return of primary short **> 0** after 34 bp at ≥1 registered horizon, with one-sided p<0.05 vs control (block bootstrap), and gross also >0 |
| **Kill** | Net mean ≤0 at all four horizons after 34 bp; **or** net>0 only on gross and dies after costs; **or** effect concentrated in first 5–15m (we cannot capture); **or** n gate fails and cannot be filled without paid data |

**Realistic cost sensitivity line:** recompute net at 25 bp RT; success still requires 34 bp clear.

### Second — C01 ETF NAV-window × prior flow

| Item | Definition |
| --- | --- |
| **Event** | US ETF trading day t with Farside BTC Total ≠ 0 (and separately ETH once listed) |
| **Signal** | Day-t Total first knowable after US cash close — operationally **20:00 UTC** conservative stamp on day t (document if Farside publish lag differs) |
| **Entry** | Next day 15:00 America/New_York (19:00 UTC standard; 18:00 when US DST) on Bybit BTCUSDT (ETHUSDT for ETH flows) |
| **Exit** | 16:00 America/New_York same day (one-hour hold) |
| **Direction** | sign(day-t Total): + long, − short |
| **Control** | (i) same hour on days with Total=0/missing; (ii) 14:00–15:00 and 16:00–17:00 adjacent hours; (iii) sign-scrambled flows |
| **Min n** | ≥200 BTC sessions in Train-1 with known prior-day flow (BTC ETF starts 2024-01-11; Train-1 overlap ~261 weekdays — OK) |
| **Success** | Net mean hour return >0 after 34 bp; beats control hours; survives HAC/clustered by week |
| **Kill** | Net ≤0 after 34 bp; or only works pre-2025-07-29 and dies post (regime); or equal to adjacent-hour control |

### Third — C03 Token unlock cliff

| Item | Definition |
| --- | --- |
| **Event** | Unlock ≥ X% circulating **without choosing X from data** — freeze **X = 1% of circulating** from a **single free** schedule source agreed before download (else **do not run** — paid dependency) |
| **Signal / entry** | 00:00 UTC on day −7 (pre-registered); alt diagnostic day 0 (not a pass gate) |
| **Horizons** | −7→0, 0→+7, −7→+14 close-to-close on Bybit perp if listed else reject event |
| **Direction** | Short |
| **Control** | Same token random non-unlock windows; size-matched tokens without unlock |
| **Min n** | ≥60 events on Bybit-listed names in Train-1 |
| **Success / kill** | Same cost rule as C02. **Automatic kill** if free schedule source cannot supply PIT history without scraping TOS-violating UIs or paid APIs |

---

## 7. Selection

### Recommended F012: **C02 — Exchange delisting forced unwind**

**Causal thesis (required form):**

> Because a venue publishes a delisting notice at time T that names a last-trade or
> settlement time T+Δ, holders of that perpetual become constrained to close (or be
> force-settled) during (T, T+Δ]. We can observe the notice before the forced closing
> flow, and historical trade archives for delisted symbols allow us to test whether
> that window creates market impact large enough to exceed 34 bp round-trip costs.

**2nd:** C01 ETF NAV-window × prior-day flow (product-fit; identification risk).
**3rd:** C03 Token unlock cliffs (calendar A; paid/pre-priced risk).

**Rejected:** C04–C16 with reasons in §3 table.

**Product note (owner decision, not a kill):** a pass on C02 proves the structural-edge
method on alts; mapping onto the liquid basket may require listing/delisting-adjacent
mechanisms (maintenance margin changes, reduce-only windows, innovate listings) or an
explicit basket expansion. That mapping is **out of scope** for this research phase.

If C02's kill criteria fire on Train-1, proceed to C01's kill test before declaring
"no candidate deserves implementation." Only if C01 and C02 both die (and C03 remains
blocked on free data) conclude:

> **No candidate currently deserves implementation.**

That sentence is **not** the present conclusion — C02 deserves the cheap falsification.

---

## 8. STOP before implementation

This document and `output/f012_candidates/*` are the research artifacts.
Collectors (optional, free prospective only) are documented in
`f012_collectors/README.md`. They do **not** trade, do **not** touch
`f011-liq-collector`, store raw observations with timestamps, and enforce a **2 GB**
disk cap with free-space stop.

### Open owner decisions

1. Approve F012 = C02 falsification experiment (no strategy code yet)?
2. If C02 passes on alts: allow basket expansion vs search for liquid-major analogue?
3. Activate any paid unlock API for C03 only after C02/C01 resolve?
4. Keep or stop the new F012 collectors independently of F012 go/no-go?

### Test-count budget for F012 kill phase

| Experiment | Registered tests | Notes |
| --- | --- | --- |
| C02 primary | 4 horizons × 1 direction = **4** | +1 diagnostic long-into-expiry **not** counted as pass gate |
| C02 controls | 2 control constructions reported alongside, not separate searches | |
| C01 | 1 hour window × 1 rule = **1** (+ adjacent-hour controls) | BTC primary; ETH replication pre-registered as **1** extra |
| C03 | 3 horizons × 1 direction = **3** | Only if free PIT schedule exists |
| **Total if all run** | **≤ 9** primary tests | FDR: require C02 alone to clear before spending C01/C03 budget |

False-discovery: treat the four C02 horizons as one family (pass if any clears **and**
the family-wise bootstrap still rejects H0 under max-t). Do not mine extra horizons.

---

## Appendix A — Probe commands (reproducible)

```bash
# Farside
curl -A 'Mozilla/5.0' -o /tmp/farside_btc.html https://farside.co.uk/bitcoin-etf-flow-all-data/

# Bybit delist announcements
curl 'https://api.bybit.com/v5/announcements/index?locale=en-US&type=delistings&limit=5'

# Deribit OI snapshot
curl 'https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=option'

# HypurrScan TWAPs
curl 'https://api.hypurrscan.io/twap/*'

# Archive presence for delisted
curl -s https://public.bybit.com/trading/LOOMUSDT/ | head
```

## Appendix B — References (hypothesis generators, not proof)

- Owner brief F012 / F011 archive decision (2026-10-06).
- Coinbase Institutional, "Trading Activity from a US Lens" (ETF 3–4pm ET volume).
- SSRN 7545019 — Fabus et al., timestamp alignment of ETF flows vs BTC returns.
- Keyrock, "From Locked to Liquidity" (~16k unlocks).
- Cayø Largo, "Does Max Pain Work for Deribit Options?" (919 expiries, 2026-09).
- SEC press release 2025-101 — in-kind creations/redemptions for crypto ETPs (2025-07-29).
- Project specs: `spec/vision.md`, `spec/COORDINATOR_RESEARCH_PROTOCOL.md`,
  `spec/research/F005-validation-protocol.md`, `spec/research/F011-forced-flow-lab.md`.
