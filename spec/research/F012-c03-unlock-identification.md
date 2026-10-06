# F012-C03 — Token unlock cliff: identification / data feasibility

**Decision: FAIL.** Gate 0 failed on PIT history (0b), which triggers the brief's automatic
kill. **DO NOT BUY.**

Pre-registration: `spec/features/active/F012-c03-unlock-identification/prereg.md`, frozen
at `150fafd` before any bulk download or scoring. Train-1 only (2024-03-01 → 2025-03-01 UTC).
Code: `unlock_lab/`. Tables: `output/f012_c03_unlock/`. No data was purchased, no strategy
was backtested, and nothing was optimised.

**One-sentence causal conclusion:** on free data, only the first link of the chain (a known
cliff) exists, and only as a revised hindsight schedule (10% of a random 30-event sample
verified from a pre-event archive snapshot), while transfers and sales cannot be observed at
all; even with hindsight schedules, bigger cliffs underperform matched alts mainly in the last
~2 weeks and at the cliff, and the pre-registered high-sell × low-absorption interaction adds
nothing — so there is no conditional effect beyond "bigger unlock = somewhat more bearish".

## Free-data coverage (report fields)

| Field | Value |
| --- | --- |
| Schedule source (frozen) | DefiLlama emissions dataset, static public files (`defillama-datasets.llama.fi/emissions/{slug}`), snapshot 2026-10-06, 372 protocols |
| Train-1 cliff token-days | **4,032** events across **152** unique tokens (3,967 / 117 with a valid schedule-implied % circ) |
| LARGE (≥ 1% circ) | 636 events / 94 tokens |
| First vs recurring (180 d) | 86 first / 3,946 recurring (LARGE: 21 first) |
| Recipient coverage (non-UNKNOWN) | **91.9%** (ECOSYSTEM 3,179 · TEAM 247 · VC 228 · OTHER 53 · UNKNOWN 325) |
| On-chain coverage | **0%** (no recipient wallet addresses in the source; Etherscan needs an API key; wallet labels are paid) |
| PIT reliability | **LOW / unverified**: random-30 sample verified 3/30 = **10%** from a Wayback snapshot taken before the event (bar ≥ 80%) |
| Priced (survivorship-safe) | 169 / 372 protocols have a Binance spot / Binance UM / Bybit linear USDT market; scored with full −31…+30 window and matched controls: **2,489 events / 68 tokens** (LARGE 285 / 56) |
| Short availability (perp listed before day −1) | all events **2,524 / 4,032** (72 / 152 tokens); LARGE **305 / 636** (59 tokens, all with Bybit); scored set 2,472 / 2,489 |

## Gate outcomes

| Gate | Outcome | Key evidence |
| --- | --- | --- |
| 0 Data feasibility | **FAIL** (0b) | 0a PASS with a TOS caveat · **0b FAIL 10% < 80%** · 0c PASS (305 LARGE with Bybit perp, 59 tokens) · 0d PASS 91.9% |
| 1 Supply shock | UB-DESCRIPTIVE | distributions below; depth INFEASIBLE free |
| 2 Recipient type | UB-DESCRIPTIVE | 91.9% labelled; labels themselves were revised (see Gate 2) |
| 3 Pre-unlock pricing | UB only — no PASS possible | vs controls, LARGE underperformance sits in days −15→+1, not −31→−15 |
| 4 On-chain realization | **INFEASIBLE** (free) | 0% coverage |
| 5 Signal classes | A unverified · B infeasible · C rejected | see Gate 5 |
| 6 First falsification | UB: size gradient present, not PIT → no PASS | slope negative; LARGE − SMALL significant only in LATE_PRE / AT |
| 7 Interaction | **FAIL (UB)** | cell − other LARGE ≈ 0 in every window |
| 8 Earliest entry | UB only; D INFEASIBLE | family A needs a schedule that was PIT ≥ 31 d before the cliff, which free data cannot verify |
| BUY rule (prereg §3) | **not met → DO NOT BUY** | cell PRE vs controls −358 bp [−896, +256]; cell − SMALL PRE −242 [−775, +403], POST −438 [−935, +179] |

"UB" = hindsight upper bound (prereg §3): run on the revised schedule only to inform
BUY / DO NOT BUY. It can never turn a gate into PASS.

### Gate 0 — data feasibility (FAIL)

- **0a free source:** the data is free, but the equivalent JSON API (`api.llama.fi/emissions`)
  returns HTTP 402 (paid plan). The datasets bucket behind the free unlocks pages was read
  once, in low volume, cached, for research only. This is a **TOS grey zone**, flagged, not
  hidden. Tokenomist / Messari / CryptoRank were not scraped (paid APIs; UI scraping
  prohibited).
- **0b PIT history: FAIL.** The schedule repo that once held git history
  (`DefiLlama/emissions-adapters`) now returns 404. The Wayback Machine was offline at freeze
  time and later came back. Archived `defillama.com/unlocks/{slug}` pages embed the as-of
  schedule in `__NEXT_DATA__`, so a test was possible
  (`unlock_lab/pit_check.py`, match = cliff ±1 UTC day, tokens ±10%):
  - random 30 (frozen seed): **3 VERIFIED**, 14 event absent from the latest pre-event
    snapshot, 10 with no snapshot before the event, 3 unparseable → **10%**.
  - secondary LARGE 30: 7 VERIFIED (23%); 21 had no snapshot. **Where a parseable pre-event
    snapshot existed, LARGE amounts matched exactly in 7 of 9.**
  - archive breadth (CDX prefix listing, a lower bound): 53 / 152 event tokens and
    2,342 / 4,032 events have any snapshot before the event day; 232 / 638 LARGE.
  - revision evidence: 41 / 372 protocol files carry notes such as "calibrated against actual
    on-chain supply" or "future unlocks extrapolated". Arbitrum's April 2024 page filed its
    investors under `insiders`; today they are `privateSale`.
- Revision policy: snapshot only, no as-of versions. Look-ahead risks: protocols added after
  their cliffs; amounts calibrated after the fact; cancelled or postponed cliffs silently
  removed; inclusion favours tokens that are notable today.
- Automatic kill applies → **overall FAIL** whatever the later gates show.

### Gate 1 — supply-shock distributions (`gate1_distributions.csv`)

| Metric | q25 | q50 | q75 | q90 | q95 | share ≥ cut |
| --- | --- | --- | --- | --- | --- | --- |
| pct_circ (all 3,967) | 0.00% | 0.04% | 0.40% | 2.3% | 5.1% | 16.0% ≥ 1% |
| pct_circ TEAM / VC | 0.24% / 0.14% | 0.91% / 0.16% | 2.4% / 3.1% | 7.9% / 4.7% | — | 43.7% / 41.4% |
| usd_value (2,523) | $4.7k | $17k | $409k | $7.4M | $43M | — |
| usd_adv (2,505) | 0.001 | 0.007 | 0.068 | 0.65 | 1.66 | 7.7% ≥ 1 day ADV |

Most cliffs are tiny monthly ECOSYSTEM emissions. TEAM, VC and OTHER cliffs are one to two
orders of magnitude larger. The only cut used is the brief's frozen X = 1%; absorption is
frozen at usd_adv ≥ 1. Depth: no free historical alt order books → INFEASIBLE.

### Gate 2 — recipient type

Coverage is 91.9% non-UNKNOWN (UNKNOWN kept as its own category, 325 events / 8 tokens).
631 token-days mix recipients, and the dominant type by tokens is used. Uncertainty: DefiLlama
often merges team and investors under `insiders`, and the archive shows those labels being
re-categorised over time. Labels are hindsight labels, not PIT.

### Gate 3 — pre-unlock pricing (UB; `gate3_windows.csv`, `gate3_car_path.csv`)

Abnormal return in bp, token-cluster bootstrap 95% CI:

| Group (events / tokens) | Window | vs BTC | vs matched controls |
| --- | --- | --- | --- |
| ALL (2,489 / 68) | PRE −31→−1 | −1,141 [−1,384, −996] | −145 [−304, −34] |
| LARGE (285 / 56) | EARLY_PRE −31→−15 | −691 | **−64 [−298, +161]** |
| LARGE | LATE_PRE −15→−1 | −789 | **−309 [−470, −135]** |
| LARGE | AT −1→+1 | −160 | **−99 [−186, −18]** |
| LARGE | POST +1→+30 | −1,412 | −239 [−523, +78] |
| SMALL (2,204 / 30) | PRE / AT / POST | −1,097 / −67 / −998 | −115 / +10 / +90 (all CIs ∋ 0) |

**When:** almost all of the "vs BTC" drop is the Train-1 alt-vs-BTC bleed. Matched non-event
alts fall nearly as much. Against controls, the LARGE path is flat until about day −15. It then
falls about 300 bp into the cliff and about 100 bp across it (CAR −374 at −1, −473 at +1).
The post-cliff drift is not significant. The literature's "front-run from −30 d" was tested
and **not supported** for days −31…−15; any underperformance is concentrated in the last two
weeks.
By recipient vs controls: TEAM POST −508 [−771, −158] and AT −118 [−228, −25]; VC LATE_PRE
−341 [−540, −147]; ECOSYSTEM ≈ 0 everywhere. These are subgroup reads on 14–18 tokens and
were not pre-registered as tests.

### Gate 4 — on-chain realization (INFEASIBLE free)

Scheduled supply is all the free source provides. It contains no recipient custody addresses
and no transfer data. Realized sellable flow (custody → exchange deposit) needs per-allocation
wallet addresses plus exchange address labels (Arkham / Nansen: paid; Etherscan: key and
per-chain work, and still no labels). Coverage 0%. Transfer ≠ sale in any case.

### Gate 5 — signal classes

- **A (structural, predictive, PIT):** schedule date × size × recipient, known before the cliff.
  Only valid if the schedule was public as-of. **Unverified on free data** (Gate 0b).
- **B (PIT-observable intermediate flow):** recipient transfer to an exchange after unlock but
  before sale. **INFEASIBLE free** (Gate 4).
- **C (post / definitional):** price reaction at or after the cliff, or flows inferred after
  the fact. **Rejected** as a structural predictor.

### Gate 6 — first falsification (UB; `gate6_7_tests.csv`)

Continuous first: the slope of AR vs controls on log10(pct_circ), in bp per decade:
PRE −160 [−233, −62] · EARLY_PRE −60 [−113, +24] · LATE_PRE −100 [−156, −45] ·
AT −29 [−56, −11] · POST −101 [−224, −11].
LARGE − SMALL: PRE −258 [−565, +67] · LATE_PRE **−246 [−414, −49]** · AT **−110 [−205, −22]** ·
POST −329 [−669, +50]. There is a size gradient on hindsight data. It is not PIT, and in the
frozen BUY windows (PRE, POST) LARGE − SMALL CIs include 0.

### Gate 7 — interaction (FAIL, UB)

Cell = LARGE ∧ usd_adv ≥ 1 ∧ HIGH-SELL (TEAM ∪ VC): 76 events / 20 tokens.
Cell − other LARGE: PRE +22 [−590, +690] · LATE_PRE +79 · AT +13 · POST −149 [−648, +394].
Cell vs controls PRE −358 [−896, +256]. **The mechanism-specific interaction adds nothing over
plain size.** HIGH-SELL LARGE events are no worse than other LARGE events.

### Gate 8 — earliest realistic entry (UB; `gate8_families.csv`)

Net of costs, bp; the "excess vs matched controls" leg (short token / long controls, 2 legs of
cost) isolates the unlock part. Short-only and BTC-hedged legs mostly earn the Train-1 alt
bleed (ALL short-only family A +563 at owner tier), which is regime beta, not unlock.

| Family | Earliest realistic entry | LARGE excess, owner 9.9 | LARGE excess, 34 | Cell excess, owner |
| --- | --- | --- | --- | --- |
| A calendar | close −31, *only if the schedule was public by then* (free data cannot verify) | +360 [+59, +666] | +312 [+14, +622] | +320 [−313, +872] |
| B into cliff | close −2 | +96 [+9, +193] | +48 [−34, +146] | +133 [−62, +321] |
| C post-cliff | close +1 | −14 [−238, +192] | −62 | +106 [−268, +453] |
| D on-chain | after the transfer's block time + label latency | INFEASIBLE free | — | — |

Stress 50 / 75 / 100 is in the CSV. LARGE family A excess: 50 bp +280 [−12, +594] ·
75 bp +230 [−80, +530] · 100 bp +180 [−130, +489]. The CI includes 0 from 50 bp. Family B
LARGE goes negative from 75 bp.
Perp funding is not modelled (daily closes); this is not a strategy backtest. All rows carry
schedule look-ahead.

## Mandatory cross-cutting

- **Short availability:** 2,524 / 4,032 events (72 / 152 tokens) had a Bybit or Binance USDT
  perp listed before day −1; LARGE 305 / 636 (59 tokens). Bybit's REST returns no history for
  delisted perps, so Bybit eligibility is a lower bound. Binance UM uses vision archives,
  which keep delisted symbols.
- **Survivorship:** prices come from archives that keep delisted symbols. The schedule universe
  is DefiLlama's *current* list (inclusion survivorship), and 203 / 372 protocols have no
  Binance/Bybit USDT market, so they are dropped from pricing.
- **Independence:** 2,489 scored events come from only 68 tokens (2,146 are monthly ECOSYSTEM
  emissions from 45 tokens). All inference is token-clustered. First LARGE cliffs: n = 8
  (uninformative).
- **Success bar:** a conditional interpretable effect ≫ generic "unlock = bearish" was **not
  found**. The only structure is a size gradient, which is the generic thesis.

## BUY / DO NOT BUY

**DO NOT BUY.** The frozen BUY rule (prereg §3) failed on the hindsight upper bound. With 20
tokens the cell qualifies, but its PRE / POST CI vs controls includes 0, and so does cell −
SMALL. Paid PIT data could only remove look-ahead, which mostly *helps* an effect show up.
Fields missing from free data that any reopening would need:

1. As-of schedule versions per cliff: first-public timestamp, date, token amount, recipient
   label, and the revision log (≥ 31 days before the cliff for family A).
2. History of postponed or cancelled cliffs (announced, then moved or removed).
3. Daily market circulating supply for Train-1 (CoinGecko free reaches back 365 days only).
4. Team / VC / investor separation where the source merges them under `insiders`.
5. Per-allocation custody wallet addresses plus exchange deposit-address labels, giving
   realized custody → exchange transfers with block times (Gate 4 / family D).
6. Historical alt order-book depth (±1–2%) around cliffs (absorption beyond ADV).

Owner question, not acted on: a **free** partial PIT re-test exists. Archived pre-event
snapshots cover 232 / 638 LARGE events, and matched exactly in 7 / 9 where parseable. It could
be pre-registered as a new candidate on the LARGE subset. Nothing has been started.

## Caveats

- Hindsight schedule throughout; every Gate 1–8 number is an upper bound, not PIT evidence.
- TOS grey zone for the DefiLlama datasets bucket (paid API mirror exists); read once, cached,
  not redistributed (raw cache git-ignored).
- Ticker mapping uses CoinGecko id → symbol → `{SYMBOL}USDT`; symbol collisions are possible
  and were not price-verified.
- % circ is schedule-implied (sum of documented sections), not market circulating supply.
  Example: PYTH 2024-05-19 at 142%, which is consistent with reality.
- Controls are matched on ADV only (not sector or beta); a beta-adjusted variant is in
  `gate3_windows.csv` (`vs_BTC_beta`).
- Wayback CDX was intermittent; the coverage counts are lower bounds. During the run, a process
  outside this job overwrote `data_cache/f012_c03/pit.log` with a one-line message (the
  log only; the CSVs had already been written at 17:53, and the summary was rebuilt from
  those CSVs).
- C01/C02 code, outputs, tickets and the parked note were not touched; collectors
  `f011-liq-collector`, `f012-deribit-book.timer` and `f012-farside-etf.timer` are active and
  unchanged; no next candidate was started.

## Reproduce

```
python3 -m unlock_lab.fetch       # schedule snapshot + CoinGecko list (data_cache/f012_c03/)
python3 -m unlock_lab.catalog     # Train-1 cliff token-days
python3 -m unlock_lab.prices      # Binance vision / Bybit daily, short availability
python3 -m unlock_lab.study       # Gates 1,3,6,7,8 tables
python3 -m unlock_lab.pit_check   # Gate 0b Wayback verification (random30 / large30 CSVs)
python3 -m unlock_lab.coverage    # gate0_coverage.json, gate0_pit_summary.json
```
`coverage.py` needs the cached CDX prefix listing `data_cache/f012_c03/wayback_cdx.txt`
(`web.archive.org/cdx/search/cdx?url=defillama.com/unlocks&matchType=prefix&from=2023&to=2025`).
