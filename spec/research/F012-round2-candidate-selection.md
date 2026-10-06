# F012 · Round-2 structural candidate selection (after C01/C02/C03 FAIL)

> PO decision request: ChatGPT PO session `f006-chatgpt-po`, 2026-10-06.
> This is a **selection note only**. No code, no collector, no backtest, no data download
> beyond the one-line availability probe in §4. Train-1 discipline (F005) unchanged;
> validation windows 1–4 and the 2026-03 → 2026-09 holdout stay untouched.

**Verdict: R2-A, leveraged-ETF daily leverage reset (BTC 2× / −2× US ETFs into the 16:00 ET close), is the single next falsification test.**

---

## 0. Binding context

| Item | Status | Source |
| --- | --- | --- |
| C01 ETF NAV-window × prior-day flow | **FAIL** (Gate A lift 1.38 < 1.5; B/C not reached) | `F012-c01-etf-identification.md` |
| C02 delisting forced unwind | **FAIL** (perp − spot ≈ 0; informational drift, not forced flow) | `F012-c02-delisting-falsification.md` |
| C03 unlock / vesting cliff | **FAIL** (Gate 0 PIT 10% < 80%; DO NOT BUY) | `F012-c03-unlock-identification.md` |
| Delisting informational/event alpha | **PARKED**, not F012 | `F012-delisting-informational-alpha-parked.md` |
| F011 forced-flow / liquidation cascades | **ARCHIVED**; paid liq data NO-GO | `F011-forced-flow-lab.md` §9b |
| Round-1 rejects C04–C16 | stand as rejected (reasons in round-1 §3) | `F012-structural-edge-candidates.md` |
| Closed families | catalog trend/MR, funding carry, spread capture, OI fade, 5m cross-venue basis, tick lead-lag | `spec/build.md`, round-1 §0 |

**Cost gate (binding):** owner-tier **≈ 9.92 bp RT taker** (maker bound ≈ 5.12 bp); stress 50/75/100 bp
reported only. **34 bp is obsolete** and is not used here (`F012-owner-cost-hurdle.md`).

**Not reopened by this note:** C01, C02, C03 (including the free Wayback LARGE-subset re-test
asked about in the C03 note), the parked delisting-information channel, and every closed family.

**Anti-F011 rule (applied to every candidate):** Class A (PRE-FLOW) only. The constraint that takes
the choice away must be visible **before** the forced trades execute. "We see the forced
participant after price has absorbed the flow" = F011 failure = reject.

**What C01–C03 taught (used as filters, not as reasons to retest):**
1. *C01:* forecasting a forced flow from its own lagged prints is not enough. Prefer mechanisms where
   the flow is **computed by rule** from observables, not predicted.
2. *C02:* if the trigger is also news, spot and perp both move and the forced flow cannot be
   separated. Prefer triggers that carry **no information about the asset's value**.
3. *C03:* if the PIT version of the trigger is not free, the test dies at Gate 0. Prefer triggers
   rebuilt from **market data and official, time-stamped records**.

---

## 1. Explicit rejections (not candidates)

| Rejected class | Examples considered | Why rejected |
| --- | --- | --- |
| Information-only events | spot listings (Binance/Upbit/Coinbase), Launchpool/HODLer airdrops, partnership/news | No mechanical constraint: participants are free to act or not. Effect is information pricing |
| Stigma | Binance Monitoring/Seed tag, delisting announcements | The C02 failure mode. The informational part is PARKED and not F012 |
| Price prediction | flow forecasting from flow lags, "smart money" wallet following | C01 lesson: prediction ≠ compulsion |
| OHLCV transforms | any momentum/MR/breakout/volatility rule with no named forced participant | Closed catalog families |
| Paid data | Tokenomist/Messari unlocks, Coinglass liq history, Laevitas/Amberdata signed GEX, Kaiko books, Arkham Pro | Owner rule: no paid data |
| Closed / archived families | funding carry and funding clock, basis unwind, spread capture, liquidation cascades incl. DeFi liquidation-level maps, OI fade | Already falsified or archived |
| Parked | delisting informational / event-driven alpha | Owner rule: do not develop |
| Round-1 rejects | max pain, dealer gamma w/o sign, dated-futures delivery, stablecoin mint, CB/Upbit premium, MSTR 8-K, miners, vol-target, HL TWAP, index rebalance | Reasons in round-1 §3 still hold; nothing new makes them observable or larger |

---

## 2. Candidates (≤ 5, all new vs C01–C16)

Every candidate answers the eight required items. "Episode" = one independent unit of inference.
Unless stated otherwise, every test is: Train-1 only, Bybit USDT perp as the trade venue,
no grids, no horizon search, costs at 9.92 bp RT.

### R2-A — Leveraged-ETF daily leverage reset (BTC 2× / −2× US ETFs)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant | Issuers of US daily-reset leveraged BTC ETFs (BITX 2×, BITU 2×, SBIT −2×) and the swap/CME dealers who hedge them. ETH 2× (ETHU, ETHT) is a replication |
| 2 | Constraint | The prospectus targets L× the **daily** return, so exposure must be reset to L × NAV before each close. The required trade is arithmetic: **ΔExposure = L(L−1) · AUM · r_day**. This is positive for both L = 2 and L = −2, so the trade always has the same sign as the day's return. The issuer cannot skip the reset without breaching its mandate |
| 3 | PIT trigger | At 15:00 ET on a US trading day: (i) BTC return from 16:00 ET of the prior session to 15:00 ET (Coinbase/Bybit 5m, already cached), (ii) prior-day AUM per fund from the latest PIT-public record. Both are known **before** the reset trades, which concentrate into the close |
| 4 | Direction / horizon | Same sign as r_day. Bybit BTCUSDT from 15:00 to 16:00 ET (DST-aware), one hour, one trade per day |
| 5 | Free PIT data / coverage | Prices: Coinbase BTC-USD 5m + F011 Bybit 5m frame (Train-1 complete, cached). Fund daily bars: Yahoo, probed 2026-10-06 (§4): BITX 250 sessions over all of Train-1; BITU/SBIT 229 sessions from 2024-04-02; ETHU 185 sessions from 2024-06-04. AUM: issuer daily NAV × shares outstanding and SEC N-PORT/N-CSR (EDGAR acceptance time = PIT). **Not yet verified free + PIT at daily resolution → Gate 0** |
| 6 | Min independent episodes | ≥ 150 US trading days with full data; ≥ 40 days in the pre-registered large-flow subset (top tercile of \|predicted $ flow\|, threshold built PIT from an expanding history); ≥ 80 weekend/US-holiday placebo days |
| 7 | Cost gate | Net mean per trade > 0 after **9.92 bp RT** on the large-flow subset, with the bootstrap 95% CI lower bound > 0. Maker bound 5.12 bp and stress 50/75/100 bp reported only |
| 8 | Kill rule | §5 (absolute, pre-set) |

**Anti-F011 class: A.** The cause (mandate + realized return + known AUM) is complete at 15:00 ET.
The forced trade has not yet executed. **Main risk (what the test kills):** dealers pre-hedge
continuously through the day, so the 15:00–16:00 window carries no residual pressure.
**Why it is not an OHLCV transform:** the signal includes momentum, so identification rests on
what only this participant explains. These checks are pass gates, not diagnostics:
(i) the same clock on **weekends and US holidays**, when BTC trades but the ETFs do not reset;
(ii) dose-response on PIT AUM × r, since AUM grew across Train-1 and BITU/SBIT launched mid-period;
(iii) the 15:00–16:00 window against adjacent hours.
**Overlap with C01:** same clock hour, different participant and constraint. This is not a C01
reopen and uses no Farside flow.

### R2-B — Venue leverage-cap / risk-limit tier reduction on a live perp

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant | Holders of an existing Bybit/Binance perp whose notional exceeds the new tier limit at the new maximum leverage |
| 2 | Constraint | At effective time T_eff the venue enforces lower max leverage / higher maintenance margin per tier. Over-limit positions must add margin, reduce, or be force-reduced |
| 3 | PIT trigger | Official notice timestamp (Binance CMS futures-update articles; Bybit `/v5/announcements`), with T_eff parsed from the body |
| 4 | Direction / horizon | Reduction of the **crowded** side, signed by PIT funding sign / top-trader L/S before the notice. Window: notice → T_eff (usually 1–3 days) |
| 5 | Free PIT data / coverage | Notices: free and time-stamped. Over-limit notional: **not public**, so the size of the forced flow is unobservable. Prices: Bybit archive / 5m |
| 6 | Min independent episodes | ≥ 40 independent (symbol, notice) events, clustered by notice batch |
| 7 | Cost gate | Net > 0 after 9.92 bp on the notice → T_eff − 1h hold, vs matched non-notified perps |
| 8 | Kill rule | Net ≤ 0 or CI ∋ 0 vs matched controls; or effect equal on spot (information, not margin); or < 40 events |

Class A in form. Weak: the size of the forced flow cannot be seen, the direction depends on a
crowding proxy (close to the closed OI/funding families), and notices often signal venue risk
concerns (C02 confound).

### R2-C — Collateral-ratio cut for token X (Binance margin / Portfolio Margin / loans)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant | Borrowers who post token X as collateral on the venue |
| 2 | Constraint | At T_eff, X's collateral ratio drops. Their margin level falls mechanically, so they must top up, repay, or be liquidated by selling X |
| 3 | PIT trigger | Binance "Will Update Collateral Ratio" notices (CMS, time-stamped), with T_eff in the body |
| 4 | Direction / horizon | Short X perp from notice to T_eff + 1h |
| 5 | Free PIT data / coverage | Notices: free. Collateral outstanding per asset: **not public**. Prices: Bybit archive / 5m |
| 6 | Min independent episodes | ≥ 40 (asset, notice) events, clustered by batch |
| 7 | Cost gate | Net > 0 after 9.92 bp vs matched assets, CI lower bound > 0 |
| 8 | Kill rule | As R2-B, plus kill if perp − spot ≈ 0 (the C02 identification test) |

Class A in form, but the same failure mode as C02: a haircut is a public risk signal, the forced
quantity is invisible, and the spot and perp moves will not separate.

### R2-D — Futures-based BTC ETF monthly CME roll (BITO and LETF futures sleeves)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant | Futures-based BTC ETFs that hold CME front months (BITO; the futures sleeves of the 2× products) |
| 2 | Constraint | Must roll front → next before CME last trade (last Friday of the month) on a published schedule |
| 3 | PIT trigger | CME calendar + daily published holdings |
| 4 | Direction / horizon | Calendar-spread pressure: the front cheapens against the next month in the roll window |
| 5 | Free PIT data / coverage | CME settlement history is free only in part; holdings history is patchy. Bybit perp **has no directional exposure** to the trade |
| 6 | Min independent episodes | 12 rolls in Train-1, below any credible minimum |
| 7 | Cost gate | Not computable on our venue. The flow is a spread on CME, which we cannot trade |
| 8 | Kill rule | Automatic: n < 40 and no Bybit-tradeable direction → reject |

### R2-E — Court/state-mandated disposal of seized or estate BTC (Mt.Gox trustee, German BKA, US Marshals)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant | Trustee or state agency obliged by court order or statute (e.g. German emergency sale) to distribute or sell |
| 2 | Constraint | Legal mandate with a deadline |
| 3 | PIT trigger | Court/agency notices; on-chain transfers from labeled wallets |
| 4 | Direction / horizon | Sell, days to weeks |
| 5 | Free PIT data / coverage | Wallet labels come mostly from Arkham (free UI, TOS grey, paid API). A transfer to an exchange is close to the flow itself (post-decision) |
| 6 | Min independent episodes | **< 10** independent episodes in Train-1 |
| 7 | Cost gate | Not testable at n < 10 |
| 8 | Kill rule | Automatic: n < 40 → reject |

---

## 3. Ranking

Scale 1–5 (5 = best) on the four PO axes. Total is decision support only. The written reasoning decides.

| Rank | ID | Short name | Directness of compulsion | PIT data quality / free availability | Independent episodes | Speed + cost of falsification | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | R2-A | LETF daily leverage reset | **5**: arithmetic mandate, sign known | 4: prices cached; daily AUM PIT = Gate 0 risk | **4**: ~250 days, ~80 large-flow, natural weekend placebo | **5**: cached data, one hour per day, about one job | **18** |
| 2 | R2-B | Leverage-cap tier cut | 3: forced only above limit; size unseen | 3: notices free; exposure invisible | 3: likely 40+ batched | 3: parse notices + archive pulls | 12 |
| 3 | R2-C | Collateral-ratio cut | 3: forced only for borrowers; size unseen | 3: notices free; exposure invisible | 2: fewer, batched | 3 | 11 |
| 4 | R2-D | Futures-ETF CME roll | 4: schedule fixed | 2: holdings patchy | 1: 12 rolls | 1: not tradeable on Bybit | 8 |
| 5 | R2-E | Mandated seized-BTC disposal | 4: legal mandate | 1: labels TOS/paid | 1: < 10 | 2 | 8 |

Why R2-A leads on the C01–C03 lessons:
- *C01:* R2-A computes the flow from a rule. It does not forecast it.
- *C02:* a day's return carries no news about the reset itself, and the weekend placebo separates
  generic momentum from the forced trade.
- *C03:* the inputs are prices plus official AUM, so no schedule vintage is needed.

R2-B and R2-C share C02's confound and have an invisible forced quantity. R2-D and R2-E fail the
episode count by construction.

---

## 4. Probe actually run for this note (availability only)

2026-10-06: Yahoo chart API, daily bars over Train-1 (2024-03-01 → 2025-02-28):
`BITX 250`, `BITU 229` (from 2024-04-02), `SBIT 229` (from 2024-04-02), `ETHU 185` (from 2024-06-04).
**Not probed:** daily AUM / shares-outstanding history, which is the only Gate 0 unknown.
No other downloads. No price data touched.

---

## 5. Choice and absolute kill rule

### Chosen: **R2-A — Leveraged-ETF daily leverage reset**

**Why (one sentence):** it is the only round-2 mechanism whose forced quantity is fully
determined by a public mandate plus observables known before the trade, has a built-in
participant-specific placebo (weekends/holidays), needs no paid data, and can be falsified in one
cheap Train-1 pass on data already cached.

**Causal thesis.** Daily-reset leveraged BTC ETFs must trade L(L−1)·AUM·r_day in the direction
of the day's move before the 16:00 ET close. At 15:00 ET we can compute that quantity from the
realized return and PIT AUM before it executes. If dealers do not fully pre-hedge, the 15:00–16:00
ET hour on US trading days carries signed pressure that is absent on weekends/holidays, scales
with predicted $ flow, and exceeds 9.92 bp RT.

### Pre-registered test definition (to be frozen in an R2-A ticket before any result)

- Universe: BTC (BITX, BITU, SBIT summed by L(L−1)·AUM). ETH (ETHU, ETHT) = **one** replication,
  not a pass gate.
- Signal at 15:00 ET: r = BTC return from the prior session's 16:00 ET to 15:00 ET (Coinbase 5m;
  Bybit as cross-check). Predicted flow F = Σ L(L−1)·AUM_PIT·r.
- Trade: sign(F) on Bybit BTCUSDT, entry at the 15:00 ET 5m open, exit at the 16:00 ET 5m open,
  DST-aware. One trade per US trading day.
- Large-flow subset: \|F\| ≥ expanding-history 67th percentile (PIT, no look-ahead).
- Placebo: same clock and same sign rule on Saturdays, Sundays and US market holidays (F := sign(r) only).
- Adjacent-hour controls: 14:00–15:00 and 16:00–17:00 ET with the same signal.
- Train-1 only. No grids, no alternative windows, no alternative thresholds. Validation/holdout untouched.

### Kill rule (absolute; any one fires → KILL R2-A, archive, no amendment)

| Gate | Kill if |
| --- | --- |
| 0 Data | No free source yields daily AUM (or NAV × shares) for BITX with as-of ≤ t−1 for ≥ 90% of Train-1 sessions; **or** 5m price coverage < 95% of sessions. No paid substitute and no proxy rescue |
| 1 Size | Median \|F\| on the large-flow subset < **1%** of combined Coinbase BTC-USD + Bybit + Binance BTCUSDT perp $-volume in 15:00–16:00 ET |
| 2 Episodes | < 150 eligible US trading days, **or** < 40 large-flow days, **or** < 80 placebo days |
| 3 Identification | Mean signed 15:00–16:00 return on US trading days **minus** placebo days is not > 0 at one-sided p < 0.05 (weekly block bootstrap); **or** the regression slope of signed return on F is not > 0 at p < 0.05; **or** the US-day effect is not larger than in **both** adjacent hours |
| 4 Cost | Large-flow subset net mean after **9.92 bp RT** ≤ 0, **or** its bootstrap 95% CI lower bound ≤ 0 |
| 5 Concentration | Removing the top 5 \|return\| days turns the large-flow net mean ≤ 0 |

Gates run in order and stop at the first KILL, as in C01/C03. A PASS on all gates authorizes
**only** an owner review of a strategy ticket. It does not authorize implementation.

### If R2-A is killed

Do **not** fall through to R2-B/R2-C automatically: both share the C02 confound. The default verdict
after an R2-A KILL is **NO CANDIDATE** for F012 round 2, pending a new owner brief.

---

## 6. STOP

No strategy, collector, backtest, or data pull is started by this note. Collectors
(`f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`) are untouched. The next
step is the owner/coordinator approving R2-A, followed by a pre-registration commit (ticket + frozen
gates above) **before** any result.
