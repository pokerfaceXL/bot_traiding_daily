# F012-C03 — pre-registration (frozen before any bulk unlock download or scoring)

Written 2026-10-06. Before this file, the only unlock data touched was a feasibility probe:
`emissionsProtocolsList` (slug list) and ONE protocol file (`arbitrum`), to learn the schema.
No Train-1 event was counted, sized, or priced before this freeze.

## 1. The single free schedule source (frozen)
**DefiLlama emissions dataset**, static public files that back the free defillama.com/unlocks
pages:
- list: `https://defillama-datasets.llama.fi/emissionsProtocolsList`
- per protocol: `https://defillama-datasets.llama.fi/emissions/{slug}`
- snapshot: downloaded once on 2026-10-06, cached raw under `data_cache/f012_c03/emissions/`
  (git-ignored). No other schedule source is mixed in. No Tokenomist / Messari / CryptoRank UI
  scraping (their terms prohibit it; their APIs are paid).

Probe facts recorded at freeze time (these drive the PIT verdict and are not results):
- The equivalent JSON API `api.llama.fi/emissions` returns **HTTP 402 (paid plan)**. The
  datasets bucket is public and unauthenticated. TOS caveat: a paywalled API mirror exists, so
  using the bucket is low-volume, one-off, cached, and research-only. Flagged as a risk, not
  hidden.
- The open-source adapter repo (`github.com/DefiLlama/emissions-adapters`), which once held
  the schedule code with git history, now returns **404** (private or removed). No free
  versioned history of the schedules can be reached.
- Wayback Machine: **"Temporarily Offline"** on 2026-10-06; `available` returned no snapshot
  for the dataset URL. Even when online, archived dynamic JSON is sparse and not a systematic
  as-of history.

**Revision policy and look-ahead risks:** the files hold today's curated schedule. Unknowns:
when each protocol was added; whether amounts or dates were edited after the fact to match
on-chain reality; whether postponed or cancelled cliffs were deleted or moved. Coverage
favours protocols that are notable today (inclusion survivorship).

## 2. Gate 0 criteria (frozen)
Gate 0 PASS needs ALL of:
- (0a) free schedule, no paid API or prohibited scrape → judged from §1;
- (0b) **PIT history**: as-of versions of the schedule (versioned history, or an archive that
  verifies ≥ 80% of a random 30-event sample *before* their event date);
- (0c) n ≥ 60 LARGE (≥ 1% circ) cliff token-days in Train-1 with a Bybit linear perp listed
  before day −1;
- (0d) recipient coverage (non-UNKNOWN) ≥ 70% of events.
**Automatic kill (brief):** if (0b) fails → Gate 0 FAIL → **overall FAIL**. The full coverage
report and BUY / DO NOT BUY are still produced.

## 3. Hindsight upper bound (only if 0b fails, and only to inform BUY / DO NOT BUY)
If 0b fails, Gates 1, 2, 3, 6 and 7 run on the hindsight schedule, labelled
**UB (hindsight upper bound)**. They cannot make any gate PASS. Look-ahead in a revised schedule
mostly *helps* find an effect (dates and sizes match reality), so a null UB result means a
paid PIT copy is very unlikely to show one. A positive UB result could be look-ahead.

**BUY rule (frozen):** recommend BUY (paid PIT schedule history) only if, on UB, the Gate-7
cell (or LARGE when that cell has < 20 tokens) shows, in a pre-registered window (PRE or POST),
a mean abnormal return vs matched controls ≤ −(cost) with a token-cluster 95% CI upper bound
< 0 at owner-tier cost, **and** it is more negative than SMALL (the 95% CI of the difference
excludes 0), with ≥ 20 unique tokens. Otherwise DO NOT BUY. Either way, list the exact missing
fields.

## 4. Event definition (frozen)
- Use `metadata.events` with `unlockType == "cliff"` and a timestamp in Train-1. Linear
  emissions are not cliffs. Rows with a non-positive token count are dropped.
- Section = text after "from " in `description`. Several cliffs for the same token on the same
  UTC day → one **token-day event**: tokens summed; recipient = the type holding the most
  tokens; `mixed` flag kept.
- First vs recurring: an event is "first" if the token has no cliff in the 180 days before.
- Day 0 = UTC date of the timestamp. Daily bars close at 00:00 UTC.

## 5. Recipient mapping (frozen; regex on section label first, then DefiLlama category)
- TEAM: label ~ team|contributor|advisor|core|founder|employee|insider; or category `insiders`
  with no investor words in the label.
- VC: label ~ investor|seed|private|strategic|backer|venture|vc|series|pre-seed|angel|kol;
  or category `privateSale`.
- ECOSYSTEM: label ~ ecosystem|treasury|foundation|dao|community|grant|reserve|incentive|reward|
  staking|liquidity mining|development|growth|partner; or category `noncirculating` /
  `farming`.
- OTHER: category `publicSale` / `airdrop` / `liquidity`, or label ~ airdrop|public|ido|ico|
  launchpad|sale|liquidity|market making.
- UNKNOWN: none of the above (kept as a first-class category; never imputed).
- **HIGH-SELL** = TEAM ∪ VC. Rationale: fund-life and mark-to-market duties (VC) and
  compensation liquidity (team) give an *ability and motive* to sell. ECOSYSTEM / treasury is
  governed and slow-moving. OTHER is dispersed and already mostly liquid.

## 6. Size and absorption (frozen)
- `pct_circ` = event tokens / schedule-circulating at day −1 (sum of `documentedData`
  cumulative unlocked across all sections). This is schedule-implied circulating supply, not
  market data: free historical circulating supply for Train-1 is unavailable (the CoinGecko
  free tier reaches back only 365 days).
- LARGE = pct_circ ≥ **1%** (brief X = 1%); SMALL = 0 < pct_circ < 1%. No other cut.
- `usd_adv` = tokens × close(−8) / mean daily quote volume over days −37…−8 on the price venue.
  **LOW ABSORPTION** = usd_adv ≥ **1.0** (the unlock is worth at least one full day of turnover,
  so it cannot be absorbed inside one day of normal flow). Depth: no free historical order-book
  data for these alts → reported as INFEASIBLE.

## 7. Prices, universe, short availability (frozen)
- Token → ticker: the DefiLlama `gecko_id` if present, else CoinGecko free `coins/list`
  (`include_platform=true`) matched on contract address from `metadata.token`. Ticker → venue
  symbol `{SYMBOL}USDT`. Ambiguous or unmatched tokens are dropped and counted.
- Prices: Binance spot daily klines (data.binance.vision, which keeps delisted symbols) →
  fallback Binance UM perp → fallback Bybit linear (public kline REST). The venue used is
  recorded. Need ≥ 60 days of bars before day 0 and ≥ 30 after, or partial windows are
  flagged and excluded from that window only.
- Short availability: Bybit linear perp (primary) or Binance UM perp with its first bar before
  day −1. Reported as eligible / total.
- Survivorship: delisted symbols stay in (the vision archives keep them). Inclusion in
  DefiLlama is itself a survivorship risk → caveat.

## 8. Event study (frozen)
- AR vs BTC: log(token) − log(BTCUSDT), beta = 1 (primary); beta-adjusted with OLS beta on
  days −120…−31 as secondary.
- Windows (close-to-close): **PRE** = −31→−1, **AT** = −1→+1, **POST** = +1→+30; also
  EARLY-PRE −31→−15 and LATE-PRE −15→−1. A full −30…+30 CAR path is reported.
- Matched non-event controls: for each event, up to 5 tokens from the priced universe with
  no cliff ≥ 0.1% circ within ±45 days, nearest in log 30-day ADV at day −31. Same calendar
  windows. Abnormal-vs-control = event CAR − mean control CAR.
- Inference: token-cluster bootstrap (5000), 95% CI. Events on the same token are never
  treated as independent. Counts reported: events / unique tokens / first vs recurring.

## 9. Gates 6–8 (frozen)
- Gate 6: continuous first — OLS of window AR (vs controls) on log10(pct_circ) with
  token-cluster bootstrap slope CI; then LARGE vs SMALL vs controls. No grid.
- Gate 7: cell = LARGE ∧ LOW ABSORPTION ∧ HIGH-SELL vs the rest of LARGE; report n, tokens,
  mean, CI. No other cuts.
- Gate 8 families and earliest realistic entry:
  A = schedule-calendar (entry close −31, short through −1);
  B = into the cliff (entry close −2, exit close +1);
  C = post-cliff continuation (entry close +1, exit close +14);
  D = on-chain-triggered (after an observed transfer to an exchange; never earlier than that
  transfer's block time).
  Costs: owner tier 9.9 bp RT primary; stress 34 / 50 / 75 / 100. Perp funding is NOT modelled
  (daily-close study) → caveat; this is not a strategy backtest.

## 10. Overall decision
FAIL if Gate 0 fails (automatic kill), or if UB / PIT shows no conditional effect clearly
stronger than generic "unlock = bearish". CONDITIONAL only if Gate 0 passes and Gates 3/6/7
show a conditional effect whose earliest PIT entry survives owner-tier cost but not stress.
PASS only if Gate 0 passes and Gates 3/6/7/8 hold at owner tier and 34 bp.
