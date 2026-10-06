# F013 · Structural-edge identification brief (after F012 close)

> PO decision request: ChatGPT PO session `f006-chatgpt-po`, 2026-10-06.
> **Identification only.** No strategy, backtest, collector or bulk download. This note is a desk
> audit plus free availability/timestamp probes (§2). Train-1 (2024-03-01 → 2025-02-28) defines
> coverage. Validation windows 1–4 and the holdout stay untouched. No paid data is proposed, and no
> human was contacted. Collectors (`f011-liq-collector`, `f012-deribit-book.timer`,
> `f012-farside-etf.timer`) are untouched.

## Verdict: **NO CANDIDATE**

None of the five mechanisms audited here has a free point-in-time source covering ≥ 90% of the
Train-1 requirement for the input that carries the compulsion. Two of them also fail compulsion or
family independence before PIT matters. No mechanism has event frequency low enough, with enough
power, to justify a lower PIT bar written before results (§4). F013 therefore names **no candidate
for preregistration**. STOP. Any further test needs a separate PO decision.

---

## 0. Binding context

| Item | Status | Source |
| --- | --- | --- |
| F012 program | **CLOSED, NO CANDIDATE**. C01/C02 = mechanism-identification FAIL; C03/R2-A = PIT-data FAIL (R2-A gates 1–5 not tested) | `spec/features/done/F012-structural-edge/outcome.md` |
| Closed families (not reopened) | F011 liquidation cascades (incl. DeFi liquidation-level maps), catalog trend/MR, funding carry/clock, spread capture, OI fade, 5m cross-venue basis, tick lead-lag | `spec/build.md`, F012 round-1 §0, round-2 §1 |
| Not reproposed | C01–C16 (round-1 reasons stand), R2-A (PIT FAIL; same fund set, same missing field), R2-D/R2-E (n < 40 by construction) | F012 notes |
| R2-B / R2-C | May appear only after an equal-terms re-evaluation. R2-B is **N5** below. R2-C's CEX form is unchanged (collateral outstanding is not public) and is **not** re-entered. Its on-chain analogue is **N3** | round-2 §2, §5 |
| Cost | Primary **≈ 9.92 bp RT** taker; maker bound ≈ 5.12 bp; stress 50/75/100 bp only. 34 bp obsolete | `F012-owner-cost-hurdle.md` |
| Excluded as "compulsion" | symbol shuffle, OHLCV transforms, loose informational signals, stigma events | owner prompt |

**PIT rule applied to every candidate.** The required coverage is measured on the input that carries
the compulsion (usually the forced **quantity**, not just the trigger). A later snapshot,
interpolation, or unlabeled proxy does not count. Coverage is judged from free sources only, with
the timestamp proving that the value was public before the trade.

**Order of work (owner):** (A) PIT audit of free data and timestamps → (B) identifiability → (C)
economic test design. A candidate that fails (A) gets no (C) design beyond its Gate 0.

---

## 1. Candidates (5, all previously untested)

### N1 — Crypto-exchange leveraged tokens (Bybit Leveraged Tokens, Gate.io 3L/3S)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant / constraint | The exchange issuing the token. It must keep effective leverage inside a published band through a scheduled daily rebalance plus a threshold rebalance. The trade is arithmetic: ΔE = L(L−1)·NAV·outstanding·r since the last rebalance. This is R2-A's mechanism on a 24/7 crypto venue |
| 2 | PIT trigger | Underlying return since the last rebalance (cached 5m bars) **and** outstanding × NAV per token as of the last rebalance |
| 3 | Direction / horizon / instrument | Same sign as r; from trigger time to the issuer's fixed rebalance time; Bybit USDT perp of the underlying |
| 4 | Free source + PIT proof | **Audit (2026-10-06):** Bybit `/v5/spot-lever-token/info` and `/reference?ltCoin=BTC3L` return **HTTP 404** (endpoints retired). Gate `/api/v4/spot/currencies/BTC3L` returns current metadata only. No outstanding or NAV history field and no history endpoint was found. No free archive of daily outstanding was found |
| 5 | Coverage / episodes (pre-outcome) | Quantity coverage ≈ **0%** of Train-1 days (no history source). Trigger price coverage is 100% (cached). Episodes would be about 365 days, but none is usable without the quantity |
| 6 | Entry / hurdle | Entry at the 5m open after the trigger, exit at the rebalance timestamp; net after 9.92 bp RT |
| 7 | Gate 0 / kill | Gate 0: free daily outstanding × NAV with as-of ≤ trigger for ≥ 90% of Train-1 days for tokens carrying ≥ 80% of the summed LT exposure → otherwise KILL. Kill after Gate 0: predicted \|ΔE\| median < 1% of Bybit perp $-volume in the window; no placebo (non-rebalance hours) difference |

**(A) result: FAIL.** No free PIT quantity. N1 differs from R2-A only in venue, and it fails on the
same missing field (daily outstanding).

### N2 — CME Bitcoin futures performance-bond (margin) increases

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant / constraint | Holders of CME BTC/MBT futures. On the effective date the clearing house raises the initial/maintenance requirement. Accounts below the new level must post cash or cut size. Only under-margined accounts are compelled, so the compulsion is partial |
| 2 | PIT trigger | CME Clearing Advisory publication time (effective date is usually the next business day) |
| 3 | Direction / horizon / instrument | Reduction of the net-leveraged side. The only free direction input is the weekly CFTC COT report (Tuesday as-of, Friday release), so direction is ambiguous: leveraged funds are net short, asset managers net long. Horizon: advisory → effective close. Instrument: Bybit BTCUSDT (the forced flow happens on CME, so this is a cross-venue transfer) |
| 4 | Free source + PIT proof | **Audit:** `cmegroup.com/clearing/risk-management/historical-margins.html` and the CmeWS margins service return **HTTP 403**, with a message that scripted access breaches CME's Data Terms of Use. So no free *permitted* automated source exists. Wayback CDX was temporarily offline during the probe. COT history is free and PIT, but it only gives direction context |
| 5 | Coverage / episodes (pre-outcome) | Advisory coverage: **not establishable** on permitted free access. BTC margin changes are, by desk estimate (not verified), a few to a few dozen per year. That is below 40 independent episodes in Train-1 on any plausible count, and it is not verifiable |
| 6 | Entry / hurdle | Entry at the 5m open after advisory publication, exit at the effective-date close; net after 9.92 bp RT |
| 7 | Gate 0 / kill | Gate 0: a complete, permitted, free list of BTC margin advisories with publication timestamps for ≥ 90% of Train-1 changes **and** ≥ 40 increase events → otherwise KILL |

**(A) result: FAIL** (no permitted free source; episode count below power even if one existed).

### N3 — DeFi governance collateral-parameter cuts (Aave v3 LT/LTV reductions, reserve freezes)

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant / constraint | Borrowers posting token X on Aave. When the liquidation threshold falls, health factor falls by the same rule. Positions pushed below HF 1 become liquidatable by anyone, so their collateral is sold. This is the on-chain analogue of R2-C, and here the position data is public |
| 2 | PIT trigger | Governance payload queued in the timelock (block timestamp), or a Risk Steward forum post before execution |
| 3 | Direction / horizon / instrument | Short X from the queue time to execution + 1h; Bybit X-USDT perp |
| 4 | Free source + PIT proof | Trigger: on-chain events are PIT by block time and free through public RPC/explorers. **Quantity:** HF-at-new-LT per position needs historical archive state at queue time, and free archive RPC access over a year is **unverified**. **Audit:** `bgd-labs/aave-proposals-v3` `src/` now holds 28 payload folders, all from 2026, so Train-1 payloads exist only in git history/on-chain logs (not probed further: that would be study-sized) |
| 5 | Coverage / episodes (pre-outcome) | Trigger ≈ complete in principle. Quantity coverage **unverified (treated as 0% for Gate 0)**. LT cuts on collateral that also has a Bybit perp in Train-1 are a minority of risk updates. ≥ 40 independent events is not established |
| 6 | Entry / hurdle | 5m open after the queue event; net after 9.92 bp RT vs matched collateral tokens |
| 7 | Gate 0 / kill | Gate 0: free archive state reproducing forced collateral (HF < 1 after the change) for ≥ 90% of events, **and** ≥ 40 events with a Bybit perp → otherwise KILL. Kill after: median forced collateral < 1% of Bybit perp daily $-volume (the expected outcome: risk-parameter proposals are sized to avoid forced liquidations, so the compelled quantity is likely near zero by design — a stated hypothesis, not a measured fact) |

**(A) result: FAIL** (forced quantity not PIT-verified). It is also **not independent of a closed family**:
the forced flow is a liquidation, the DeFi liquidation-level map closed in round 2.

### N4 — Ethena USDe delta-hedge on mint/redeem

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant / constraint | Ethena must stay delta-neutral. Each USDe mint backed by ETH/BTC collateral requires an equal short perp, and each redeem requires closing one |
| 2 | PIT trigger | Mint/Redeem events on Ethereum (block-timestamped, free) |
| 3 | Direction / horizon / instrument | Mint → short perp pressure, redeem → buy. Minutes. Bybit ETH/BTC perps |
| 4 | Free source + PIT proof | On-chain events are free and PIT. Ethena's public API returned **HTTP 403** to an unauthenticated probe (not needed) |
| 5 | Coverage / episodes | Event coverage ≈ complete; thousands of events |
| 6 | Entry / hurdle | Would be the 5m open after the mint block |
| 7 | Gate 0 / kill | Pre-identification KILL, independent of PIT: mints are RFQ'd against market makers who hedge **at or before** the mint lands on chain. The trigger is therefore observed at or after the flow (anti-F011 class C), and the trade is the funding/basis carry trade (closed family) |

**(B) result: REJECT** before PIT matters (post-flow trigger; funding-carry family).

### N5 — R2-B re-evaluated on equal terms: Bybit perp risk-limit / leverage-tier changes

| # | Item | Answer |
| --- | --- | --- |
| 1 | Participant / constraint | Holders above the new tier limit at T_eff must add margin, reduce, or be force-reduced. Only accounts above the limit are compelled, and the exchange does not publish how many there are |
| 2 | PIT trigger | Official notice publish time (announcement API / article page), with T_eff in the body |
| 3 | Direction / horizon / instrument | The crowded side. That side can only be signed with OI/funding proxies, which are closed families. Notice → T_eff − 1h; Bybit perp of the symbol |
| 4 | Free source + PIT proof | **Audit (`output/f013_brief_probe/probe_summary.json`):** `/v5/announcements/index` serves only the newest **5,000** items. The oldest is **2024-12-02 17:45 UTC**, so the API covers **88 / 365 = 24%** of Train-1 (12 "Risk Limit Adjustment" titles in that window). Wayback CDX holds 1,976 distinct Bybit article URLs captured in Train-1, 16 with `risk-limit` in the slug. That is a crawl sample, so the completeness of the notice universe **cannot be certified**. Over-limit notional: **not public** |
| 5 | Coverage / episodes (pre-outcome) | Trigger coverage: certified 24% (API) + unknown share via Wayback. Quantity coverage 0%. Several titles are limit *increases* or new-listing calibrations, which compel nobody. Reduction-only events are not certifiably ≥ 40 |
| 6 | Entry / hurdle | 5m open after notice; exit T_eff − 1h; net after 9.92 bp RT vs matched non-notified perps |
| 7 | Gate 0 / kill | Gate 0: certified ≥ 90% notice coverage with publish timestamps **and** ≥ 40 reduction events **and** a free PIT measure of over-limit notional → otherwise KILL. Kill after: effect equal on spot (C02 confound) |

**(A) result: FAIL.** Trigger coverage 24% certified; forced quantity unobservable. R2-B's round-2 weaknesses are confirmed, and nothing new rescues it.

---

## 2. Probes actually run for this brief (2026-10-06, availability/timestamps only)

| Probe | Result |
| --- | --- |
| Bybit `/v5/announcements/index`, paged to the end | 5,000 items max; oldest 2024-12-02T17:45:45Z |
| Wayback CDX `announcements.bybit.com/en-US/article/*`, 2024-03-01 → 2025-03-01, collapsed | 1,976 URLs; 16 `risk-limit`; 137 `leverage` |
| Bybit `/v5/spot-lever-token/info`, `/reference?ltCoin=BTC3L` | HTTP 404 |
| Gate `/api/v4/spot/currencies/BTC3L` | HTTP 200, current metadata only |
| CME historical margins page, CmeWS margins | HTTP 403, Data Terms of Use anti-scraping message |
| GitHub `bgd-labs/aave-proposals-v3` `src/` | 28 folders, all 2026; 0 Train-1 |
| `api.ethena.fi` | HTTP 403 |

Summary written to `output/f013_brief_probe/probe_summary.json`. No price, outcome or event-study data
was pulled. Nothing was scored.

---

## 3. Ranking (1–5, 5 = best; decision support only)

| Rank | ID | Compulsion directness | Free PIT feasibility | Sample power | Independence from closed families | Falsification cost (5 = cheap) | Total | Stage reached |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | N1 Exchange LT reset | 5 (arithmetic mandate) | 1 (no history; endpoints 404) | 4 (daily) | 3 (R2-A sibling; R2-A untested, not refuted) | 4 | 17 | (A) FAIL |
| 2 | N5 R2-B risk-limit cut | 2 (only over-limit holders; size unseen) | 2 (24% certified) | 2 | 2 (direction needs OI/funding) | 3 | 11 | (A) FAIL |
| 3 | N3 Aave collateral cut | 3 (HF rule; likely ≈ 0 compelled) | 2 (trigger yes, quantity unverified) | 2 | 1 (liquidation family) | 2 | 10 | (A) FAIL |
| 4 | N2 CME margin hike | 2 (top-up allowed) | 1 (403 by terms) | 1 | 3 | 2 | 9 | (A) FAIL |
| 5 | N4 Ethena hedge | 4 (mandate) | 4 (on-chain) | 5 | 1 (carry family) | 3 | 17 → **void** | (B) REJECT: post-flow trigger |

N4's raw total is high, but it is voided by the anti-F011 rule: a trigger seen at or after the flow is
the F011 failure itself. The ordering in the table follows the stage reached first, then the total.

---

## 4. Lower-PIT-bar exception: not invoked

The owner allows a bar below 90% only if, before results, event frequency and minimum power justify
it. No candidate qualifies:
- N1, N3: quantity coverage is ~0%/unverified, not merely below 90%.
- N2: no permitted source. Even the full event count is below 40.
- N5: certified coverage is 24%. That window holds 12 risk-limit titles in total, not all of them
  reductions, so even the certified sample is below 40. No power argument supports a lower bar.
- N4: rejected on identification, so PIT is moot.

## 5. Choice

**NO CANDIDATE.** Why: every audited mechanism with a direct, rule-defined compulsion (N1, N3, N5)
fails because the forced **quantity** has no free point-in-time history, and the two with
complete free PIT data (N4 trigger, N2 COT context) fail compulsion or family independence.

The common pattern, carried over from C03 and R2-A, is that in crypto the free data shows *that* a
constrained participant exists, but not *how much* it must trade, at daily PIT resolution. This brief
records the pattern and does not propose paid data.

## 6. STOP

No strategy, backtest, collector or bulk download was started. Existing collectors are unchanged.
R2-B/R2-C are not started (R2-B re-evaluated above as N5 and failed (A)). F011 cascades, catalog
MR, funding carry and spread capture were not reopened. The next step is a PO decision; this brief
does not choose one.
