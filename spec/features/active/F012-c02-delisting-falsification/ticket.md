# F012-C02 · Delisting forced-unwind falsification / event study

> **OWNER-APPROVED** as falsification/event study ONLY — NOT yet a trading strategy.
> Stop after exactly one decision: **PASS | CONDITIONAL | FAIL**.
> Do NOT optimize a pass. Do NOT proceed to C01/C03.
> Keep collectors unchanged: `f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`.

Prior research: commit `d44de5a`, `spec/research/F012-structural-edge-candidates.md`,
`output/f012_candidates/`. Train-1 only: 2024-03-01 → 2025-03-01 UTC.

## Outcome

A pre-registered falsification study that tests whether exchange perpetual delisting
creates a **tradeable forced-unwind edge AFTER realistic observation latency**, or whether
the announcement is priced too quickly (information effect only). Write the decision to
`spec/RESEARCH_JOURNAL.md` + a research note. Commit + push.

## Causal hypotheses (test separately — do NOT assume delisting → SHORT)

Perps have both longs and shorts; delisting forces OI→0, not a guaranteed directional sell.

**H1 — Announcement repricing:** Delisting announcement causes statistically significant
negative repricing that remains tradeable AFTER the announcement is publicly observable.

**H2 — Pre-deadline forced unwind:** As `effective_ts` approaches, forced position closure
produces additional predictable price/order-flow effects BEYOND the initial announcement
repricing.

## Scope

### Event catalog
- Sources: Bybit announcements API `type=delistings` (~482 total, ~91 Train-1);
  Binance CMS catalogId=161 (~439 total, ~76 Train-1).
- For every event preserve: `exchange`, `symbol`, `announcement_ts`, `effective_ts`,
  announcement source URL/id, `first_publicly_observable_ts`,
  `notice_duration = effective_ts − announcement_ts`, contract type (perp/spot/etc),
  available OI/funding/trade data flags, spot listing/delisting status if available.
- Use exact timestamps from API `dateTimestamp`/`publishTime`/`publishDate`/`releaseDate`
  and article body times — **NOT** day-rounded article dates when exact stamps exist.
- Strategy must not receive information before it was publicly observable.
- Assign `event_id` + `announcement_cluster_id` (same exchange announcement = one cluster).
- Report both #symbols and #independent announcement clusters.
- `n≥40` refers primarily to independent usable announcement clusters.

### Market data (survivorship-safe)
- Bybit REST kline returns empty for Closed symbols — use `public.bybit.com/trading/{SYMBOL}/`
  daily trade archives (or equivalent) and aggregate to 1m where needed; process in batches;
  delete raw archives after aggregation (disk floor ~10–20 GB free; currently ~31 GB free).
- Binance: `data.binance.vision` futures klines / aggTrades for delisted USD-M perps where available;
  fapi historical endpoints where they still serve Closed symbols.
- Do **not** silently discard events without trade history — report missing-event rate explicitly.
- Compare included vs excluded where possible.
- BTC (or appropriate) benchmark for market adjustment from existing Train-1 caches.

### Immediate announcement response
Measure cumulative returns from `announcement_ts` at:
`+1m, +5m, +15m, +30m, +1h, +4h, +12h, +24h, +72h`.
Also: first-trade price after announcement; first executable price after realistic
detection/processing delay; MFE; MAE; volume; OI where available; funding;
spread/liquidity proxies.
**Critical:** How much of the total delisting effect occurs before a realistic strategy could enter?

### Realistic signal latency (no zero-latency)
Entry assumptions: announcement+10s, +30s, +60s, first completed 1m bar, first completed 5m bar.
Only use resolutions actually supported by historical data.
If edge disappears with realistic latency → reject C02 for H1.

### Separate announcement alpha from unwind alpha
Decompose: `announcement_ts → early repricing` AND `post-repricing → effective_ts`.
Question: does price continue to drift after the information shock?
If nearly all negative return is immediate and subsequent E[R]≈0 → efficient news pricing,
no forced-unwind trading edge (H2 FAIL).

### OI study
Where hist OI exists: announcement → OI decay trajectory → effective_ts.
Normalize OI to pre-announcement level. Does faster/slower OI decay predict subsequent return?

### Directional conditioning (exploratory, small set — NO threshold grid)
Economically justified vars only: pre-announcement funding sign/magnitude; pre-announcement
price trend; OI vs recent history; notice duration; liquidity/volume; market-cap/liquidity
class if PIT obtainable; exchange; spot remains listed vs spot also delisted.
Main question: does pre-existing positioning determine unwind direction?
Exploratory unless n supports confirmatory inference.

### Controls
- Matched controls + time-scrambled controls.
- Broad crypto market: `AR_token = R_token − β × R_market`, with β estimated using ONLY
  pre-event information (BTC or appropriate benchmark).

### Costs
Hurdle floors: **34, 50, 75, 100 bp RT**. Delisting assets may have worse execution.
Estimate empirical execution around announcements (spread if reconstructable, volume
deterioration, slippage proxy, extreme gaps).
Strategy that works only at 34 bp on collapsing low-liquidity contracts must NOT pass.

### Identification test (CRITICAL)
Where data allow, separate DELISTING INFORMATION EFFECT from PERP FORCED-UNWIND EFFECT.
For events where perp is delisted but spot remains tradeable, compare post-announcement:
1) affected perpetual
2) same token spot
3) perp-spot basis
4) OI decay in the derivative

If spot and perp fall together immediately with no abnormal derivative-specific behavior →
informational repricing, NOT forced-unwind.
If after common repricing the derivative shows additional abnormal behavior as OI→0
(basis, aggressive flow, impact not mirrored by spot) → stronger forced-unwind evidence.

Also compare where possible: perp-only delistings; spot+perp delistings; events where spot
remains listed on major external venues.
Do not require this where hist spot unavailable, but **report coverage explicitly**.

Strongest C02 is NOT "delisting announcements predict falling token prices."
It IS: "after public information has been incorporated into spot, the known derivative
shutdown deadline creates an additional predictable and tradeable flow before effective_ts."
Evidence for the first without the second = **FAILURE of the forced-flow hypothesis**,
even if a naive announcement-short backtest is profitable.

### Tail concentration
Report mean, median, trimmed mean, win rate, return quantiles, bootstrap CIs,
contribution of top 1/3/5 events to total PnL. Re-run excluding best 1, 3, 5 trades.

### Success criteria (PASS only if ALL hold in spirit)
- Sufficient independent clusters (target n≥40 usable clusters).
- Economically meaningful effect.
- Statistically credible vs matched control.
- Positive after realistic costs (not only 34 bp on collapsing names).
- Not driven by handful of extreme tokens.
- Broadly stable across Binance/Bybit where sample allows.
- Clear separation announcement repricing vs subsequent tradeable drift.
- **MOST IMPORTANT:** large negative announcement return is NOT success if it occurs
  before simulated entry.

### Decision — exactly one
- **PASS** — tradeable structural edge warrants strategy development.
- **CONDITIONAL** — interesting effect but needs a specific observable pre-event condition
  + independent validation.
- **FAIL** — announcement priced too quickly, post-announcement unwind has no sufficient
  directional edge, costs kill it, or evidence insufficient.
If FAIL → archive C02. Do not optimize into profitability.

## Deliverables

1. This ticket (pre-reg) under `spec/features/active/F012-c02-delisting-falsification/`.
2. Event catalog with all timeline fields + missingness report under
   `output/f012_c02_delisting/` (e.g. `event_catalog.csv`, `missingness.md`).
3. Study code under e.g. `f012_c02/` or `delisting_lab/` + compact outputs under
   `output/f012_c02_delisting/` (summaries/tables; do not hoard raw archives).
4. Decision writeup in `spec/RESEARCH_JOURNAL.md` + research note
   `spec/research/F012-c02-delisting-falsification.md` classifying PASS | CONDITIONAL | FAIL
   with justifying tables.
5. Commit + push to `origin/main` after review PASS (FF preferred).

## Out of scope

- Optimizing entry rules, thresholds, or filters to force a pass.
- C01 / C03 / any other F012 candidate.
- Touching live collectors or F011 liquidation collector.
- Validation / holdout windows (Train-1 only).
- Paying for data.
- `git reset --hard`. Leave host dirt alone (`.pi/config.json`,
  `F006-catalog5-unfreeze-correction/`, `__pycache__`).

## Acceptance

- Catalog + missingness report exist; missing-event rate reported.
- H1 and H2 tested separately with latency sensitivity.
- Perp-vs-spot identification coverage + result reported (or explicit unavailability).
- Cost table at 34/50/75/100 bp.
- Tail concentration / leave-out top 1/3/5.
- Exactly one of PASS | CONDITIONAL | FAIL written in journal + research note.
- Collectors still running unchanged.
- `python3 -m pytest -q` stays green (new unit tests for parsing/causality as needed).

## Notes for implementer

- Prefer exact ms timestamps; parse article bodies for `effective_ts` and symbol lists.
- One announcement may cover multiple symbols → one `announcement_cluster_id`, many `event_id`s.
- Disk-safe: batch download → aggregate → delete raw; never drop free disk below ~10–20 GB.
- PATH includes `/home/limen/.npm-global/bin`. No `rg` on host — use `grep`.
- If hist 1m unavailable for a symbol, degrade gracefully to coarser bars and flag resolution.

## Result (2026-10-06) — **FAIL**

Full note: `spec/research/F012-c02-delisting-falsification.md`; tables: `output/f012_c02_delisting/`.

- **Sample:** 82 Train-1 perp delisting events; **80 usable** (missing-event rate **2.4%**; ZKUSDT, MONUSDT Bybit);
  **61 article / 44 day-batch clusters** (n≥40 met). Identification coverage: 46/80 with same-token spot.
- **H1 (announcement repricing):** CAR from announcement −258 bp @1m, −561 @5m, −990 @24h, −1705 @eff−1h (mean).
  Share gone before entry: 25% (10s) … 37% (bar5m). Bar5m short → eff−1h raw +972 bp [CI +242, +1728], minus matched
  ctrl +872 [+239, +1514]; → +24h +389 [+36, +743]. Time-scrambled placebo paired p=0.099 (+24h), 0.130 (+72h).
- **H2 (pre-deadline unwind):** eff−24h→eff−1h abnormal drift −93 bp [−327, +139]; eff−1h→eff−1m −44 [−185, +64].
  OI → 0.52× by eff−1h but Spearman(OI decay, later drift) = 0.013 (p 0.91). Flow imbalance post-4h ≈ 0. **H2 FAIL.**
- **Identification:** perp − spot ann+24h→eff−1h **+119 bp [−63, +458]** (median +10; wrong sign for forced selling);
  basis median ≈ 0 throughout; spot-only delistings with perp still trading fall −2020 bp to eff−1h.
  Decline is informational, common to spot and perp — not derivative forced flow.
- **Costs (owner tier 4.4 bp taker/side + measured spread/impact, median 22 bp RT, + funding −116 bp for shorts):**
  bar5m short → eff−1h +834 bp [+66, +1596]; +24h/+72h/mid CIs include 0; with +50 bp floor eff−1h CI [+13, +1581].
  Per venue eff−1h: Bybit [−56, +1736], Binance [−444, +2330] — not stable. 34/50/75/100 bp table in `costs_primary.csv`.
- **Tails (eff−1h, 50 bp):** mean +922, median +570, win 66%; top1/3/5 = 14/32/48% of sum; ex-top5 mean +508 bp.
- **Decision:** **FAIL** — forced-unwind identification fails (the ticket's most important criterion), H2 fails,
  venue stability and placebo fail. The profitable naive short is an information/stigma drift shared by spot,
  which the pre-registration defines as failure of the forced-flow hypothesis. C02 archived; no optimization.
- Collectors `f011-liq-collector`, `f012-deribit-book.timer`, `f012-farside-etf.timer`: active, untouched.
