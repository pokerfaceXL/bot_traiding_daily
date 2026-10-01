# Research Journal — F006 strategy research

> **Purpose.** Single source of truth for *current* research status and the *next* step, so a
> new coordinator can resume without re-deriving anything. Read this first, then
> `spec/COORDINATOR_RESEARCH_PROTOCOL.md` (binding), then the per-strategy profiles in
> `spec/research/strategy_profiles/`. Individual `spec/research/F006-hypothesis-*.md` notes are
> immutable *historical* records of single experiments — trust them for "what was run", but
> trust **this journal + the profiles** for "what is true now".

## How to read the record

- **Protocol binding date: 2026-10-01.** From this date every experiment follows
  `COORDINATOR_RESEARCH_PROTOCOL.md` strictly: one base strategy, one hypothesis, one change,
  pre-registered metrics + falsification condition, decision logged. "On the basis of result X
  I suspect Y, therefore I test Z."
- **Before 2026-10-01** the project was run under a looser process (earlier coordination,
  incl. a prior agent). Much of that work is sound and reused, but some *status* conclusions
  were reached by analogy rather than by an independent protocol pass. Those are being
  corrected as each strategy is properly re-examined — see the 2026-10-01 correction below.

## Current strategy status (authoritative)

| strategy | status | researched under protocol? | one-line reason | profile |
| --- | --- | --- | --- | --- |
| `DONCHIAN_55_NO_TRAIL` | **FREEZE** | yes (own trades) | every single-axis entry/exit/sizing lever tested on its *own* trades and falsified, incl. its own abs-ATR entry gate; edge is a few fat-tail runners, any filter that cuts losses also cuts those | `strategy_profiles/DONCHIAN_55_NO_TRAIL.md` |
| `EMA3_21_50_200` | **CONDITIONAL** | no (entry axis only DNR-by-transfer) | aggregate-Train-1-positive, best monthly floor of the batch (3/12); exit axis genuinely closed, entry axis never autopsied on its own trades | `strategy_profiles/EMA3_21_50_200.md` |
| `BB_20_25_EMA200` | **CONDITIONAL** | no (entry axis only DNR-by-transfer) | aggregate-positive, 3/12 best floor (tied); exit closed, entry reopened | `strategy_profiles/BB_20_25_EMA200.md` |
| `EMA_50_200` | **CONDITIONAL** | no (entry axis only DNR-by-transfer) | aggregate-positive, 3/12 best floor (tied); exit closed, entry reopened | `strategy_profiles/EMA_50_200.md` |
| `EMA3_13_50_200` | **CONDITIONAL** | no (entry axis only DNR-by-transfer) | aggregate-positive, ≥4/12 floor; exit closed, entry reopened | `strategy_profiles/EMA3_13_50_200.md` |
| `BB_20_2_EMA200` | **CONDITIONAL** | no (entry axis only DNR-by-transfer) | aggregate-positive but worst floor of the five (≥5/12); exit closed, entry reopened | `strategy_profiles/BB_20_2_EMA200.md` |
| ~20 swarm families (beta_gate, btc_filter, htf_gap_midfill, liq_range_eqh, multi_tf_pa, vol_regime_wrap, liq_cascade_proxy, session_regime, sube_inv_fvg, …) | FALSIFIED (H2) | partial (old process) | several H1-positive aggregate, but all H2-falsified with the same fat-tail shape; mean-reversion/session/sube negative | `output/f006_cross_family_digest.md` |
| `XS_RS_*` (cross-sectional RS), `ORB_UTC_*`, `ORB_LON/NY_*` (session ORB) | CLOSED / FALSIFIED | yes | new non-catalog signal families; H1 falsified or H2 0/N → closed | `F006-hypothesis-{cross-sectional-rs,opening-range-breakout,orb-session-anchor}.md` |

## 2026-10-01 — correction: catalog5 FREEZE withdrawn → CONDITIONAL

**What was wrong.** On 2026-09-30 the five catalog5 EMA/BB `NO_TRAIL` names were moved
CONDITIONAL → FREEZE. That move leaned on closing the **entry axis** as DNR *by transfer* from
`DONCHIAN_55` (`H-CATALOG5-ABS-ATR-ENTRY-GATE-01`): because an absolute-ATR% entry gate failed
on Donchian, it was declared do-not-retest on the five by analogy, **without an independent
autopsy of each name's own trades**.

**Why it's corrected.** Under the now-binding protocol, closing an axis by analogy is not a
research pass. Each CONDITIONAL strategy must be examined on its *own* trade-level evidence
before any axis is declared exhausted. The five are therefore back to **CONDITIONAL**.

**What genuinely stays closed (do not retest without new info).**
- Exit axis on the catalog5 class: `H-CATALOG5-EXIT-CLASS-01` (full-position TP/TRAIL vs
  NO_TRAIL) FALSIFIED (a)(b)(c); `H-CATALOG5-PARTIAL-EXIT-01` (partial scale-out) FALSIFIED
  (a)(b). Both were run on these names' own data. Full NO_TRAIL is their best exit geometry.
- `DONCHIAN_55_NO_TRAIL` stays FREEZE: it *was* exhausted on its own trades (its own abs-ATR
  entry gate was actually run and falsified, not transferred).

**Corrected docs:** the five `strategy_profiles/*.md`; correction banners added to
`F006-catalog5-family-insufficiency-s13.md` and `F006-coordinator-series-report-catalog5-autopsy.md`;
`build.md` NOW. Historical experiment notes left verbatim.

## Shared failure mechanism (established, momentum families)

Across Donchian + the five catalog5 names + the swarm: the edge lives in a few large winners
on high-ATR breakout entries that run to the opposite structural extreme (`signal_reverse`),
while the majority of trades die at the fixed `initial_sl` (0% WR by construction). Every
tested lever that cuts the loss count (take-profit, calm/low-vol entry keep, EMA-trend
confirm, abs-ATR entry gate on Donchian, trailing, partial exit) also cuts the same fat tails
that carry all the aggregate PnL. The unresolved question is whether an **entry-time feature
(no look-ahead)** can separate `initial_sl` deaths from `signal_reverse` runners *without*
being just another proxy for the entry's own volatility/trend state.

## Open question the record cannot yet answer

Are the **losing months shared across the frozen/conditional families** (a common market
regime when all breakout momentum fails) or idiosyncratic per name/symbol? The
portfolio-diversification exploration hinted the two worst months were correlated on 5
hand-picked series, but this has never been tested systematically across all catalog5 names ×
symbols from the per-trade autopsy tables. The answer decides whether the next licensed step
is a portfolio-level regime mechanism (§8 regime filter / F007) or a per-name entry autopsy.

## Next planned step (not yet run)

The `EMA3_21_50_200` protocol pass is **done** (autopsy + one experiment, below). It closed the
entry-vol and direction axes on this name's own trades and pointed to one remaining lever:

- **Causal regime signal, class-wide (F007 territory).** The losing months are shared across
  the basket (autopsy §4: 6/12 months have ≥4/5 symbols net-negative together), so a per-name,
  single-axis entry/exit/sizing refinement cannot fix monthly regularity. The only licensed
  next step is a **separately pre-registered** causal regime signal (portfolio-level veto or
  weight, no look-ahead; protocol §8 regime filter / §13), defined with metrics + falsification
  **before** implementation. It is scoped against the whole catalog5 NO_TRAIL class, not one
  profile. **Not yet written** — next coordinator action is to draft that pre-registration.
- Before committing to the regime axis, consider whether the same autopsy (direction asymmetry,
  shared-regime months) reproduces on a second catalog5 name (e.g. `EMA_50_200`, which shares
  the 3/12 floor) — if it does, the regime lever is the right class-wide bet; if direction
  asymmetry does *not* reproduce, revisit.
- **Do not** run a broad search or a new family: protocol §13 gate is not cleared (no written
  non-correlated-mechanism justification with budget + falsification exists yet).

## Chronological log

- **2026-10-01** — Merged all outstanding research branches to `main` (FF of 11 commits +
  6 exit-grid-sparse merges + XS_RS/ORB_UTC cherry-picks + integration fixups; 460 tests
  pass). Pushed to `origin/main`. See `build.md` NOW.
- **2026-10-01** — Protocol made binding. Corrected catalog5 FREEZE → CONDITIONAL. Started
  this journal. Next: independent protocol autopsy of `EMA3_21_50_200`.
- **2026-10-01** — **`EMA3_21_50_200` autopsy done** (`spec/research/F006-ema3-21-autopsy.md`,
  `scripts/f006_ema3_21_autopsy.py`). Findings: (1) entry-vol axis independently FALSIFIED on
  its own trades (atr_percentile/calm identical for initial_sl vs signal_reverse) — confirms
  the Donchian transfer, now earned; (2) NEW causal direction asymmetry (longs +875 / shorts
  −58, all big winners long); (3) losing months are shared-regime (6/12 with ≥4/5 symbols
  down together).
- **2026-10-01** — **H-EMA3-21-LONG-ONLY-01 = FALSIFIED**
  (`spec/research/F006-hypothesis-ema3-21-long-only.md`). Long-only raises expectancy
  (+2.03→+4.61/trade) and keeps 96.8% of fat tails, but worsens the losing-month floor
  (7→9/12) because the short book partially hedged long-losing months — expectancy and daily
  regularity are in tension. Kept as a higher-EV **F007 portfolio-component** input, not a
  regularity fix. `EMA3_21_50_200` stays **CONDITIONAL**; entry-vol + direction now both closed
  on its own trades; remaining lever = class-wide causal regime signal (see Next planned step).
