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
| `EMA3_21_50_200` | **FREEZE** | yes (full loop on own trades) | all axes falsified on own trades — entry-vol (autopsy), direction (long-only), exit (exit-class/partial), regime (breadth); every expectancy lever leaves the floor ≥7/12 because the shared regime makes both the losses and the runners | `strategy_profiles/EMA3_21_50_200.md` |
| `BB_20_25_EMA200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/BB_20_25_EMA200.md` |
| `EMA_50_200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/EMA_50_200.md` |
| `EMA3_13_50_200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/EMA3_13_50_200.md` |
| `BB_20_2_EMA200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/BB_20_2_EMA200.md` |
| ~20 swarm families (beta_gate, btc_filter, htf_gap_midfill, liq_range_eqh, multi_tf_pa, vol_regime_wrap, liq_cascade_proxy, session_regime, sube_inv_fvg, …) | FALSIFIED (H2) | partial (old process) | several H1-positive aggregate, but all H2-falsified with the same fat-tail shape; mean-reversion/session/sube negative | `output/f006_cross_family_digest.md` |
| `XS_RS_*` (cross-sectional RS), `ORB_UTC_*`, `ORB_LON/NY_*` (session ORB) | CLOSED / FALSIFIED | yes | new non-catalog signal families; H1 falsified or H2 0/N → closed | `F006-hypothesis-{cross-sectional-rs,opening-range-breakout,orb-session-anchor}.md` |

## 2026-10-02 evening — CORRECTION: catalog5 FREEZE withdrawn (four names → CONDITIONAL)

**FREEZE of the four catalog5 names was WRONG** (owner-locked correction, 2026-10-02 ~22:50
Europe/Warsaw). The binding protocol loop (2026-10-01) requires a full per-name
Observation→Problem→Mechanism→Hypothesis pass. Class-closure ran long-only + breadth levers on
the four remaining names and shared-losing confirmed basket regime — but that does **not**
substitute a full protocol loop on each name for every axis. Remaining names never got that
full pass. FREEZE only when all axes are exhausted on that name's **own** trades under protocol.

**Four names unfrozen to CONDITIONAL.** `BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`,
`BB_20_2_EMA200` are now **CONDITIONAL** (2026-10-02 evening). Only axes actually tested on
each name's own trades stay closed: exit (H-CATALOG5-EXIT-CLASS-01, H-CATALOG5-PARTIAL-EXIT-01
ran on these series); direction lever (long-only cell of H-CATALOG5-CLASS-CLOSURE-01 has
own-trade numbers for each name); regime lever (breadth B40/B60/B80 cells have own-trade
numbers). **Open on these four:** entry-vol/abs-ATR gate (only DNR-by-transfer, never
independently run), position sizing (never tested), other §8 entry structure not yet
pre-registered.

**`EMA3_21_50_200` FREEZE kept.** This name completed a full independent protocol pass on its
own trades (entry-vol autopsy, long-only, breadth-regime), so it remains **FREEZE**.

**Shared-losing-months CONFIRMED still stands** (H-CATALOG5-SHARED-LOSING-MONTHS-01) as a
diagnostic finding (basket regime), but does **not** license class-wide FREEZE — it only
blocks in-class portfolio combination (§8 precondition "losses not strongly correlated" fails).

**Docs corrected:** four `strategy_profiles/*.md`, this journal, `build.md` NOW, new §15
coordinator series report `F006-coordinator-series-report-catalog5-class-closure-correction.md`.

**Historical context (2026-10-02 morning, now superseded by this correction):**
H-CATALOG5-CLASS-CLOSURE-01 completed: long-only + breadth levers on the four remaining names.
No lever lowered pooled floor below 7/12 while meeting retention criteria. That result is
still valid, but it does not exhaust the per-name protocol loop for those four names.

## Shared failure mechanism (established, momentum families)

Across Donchian + the five catalog5 names + the swarm: the edge lives in a few large winners
on high-ATR breakout entries that run to the opposite structural extreme (`signal_reverse`),
while the majority of trades die at the fixed `initial_sl` (0% WR by construction). Every
tested lever that cuts the loss count (take-profit, calm/low-vol entry keep, EMA-trend
confirm, abs-ATR entry gate on Donchian, trailing, partial exit) also cuts the same fat tails
that carry all the aggregate PnL. The unresolved question is whether an **entry-time feature
(no look-ahead)** can separate `initial_sl` deaths from `signal_reverse` runners *without*
being just another proxy for the entry's own volatility/trend state.

## Answered questions (systematic evidence)

**Are the losing months shared across catalog5 names (basket regime) or idiosyncratic?**
ANSWERED (2026-10-02, H-CATALOG5-SHARED-LOSING-MONTHS-01, tip dc9818e): **CONFIRMED shared /
basket regime.** Train-1 losing months cluster tightly across all five FREEZE catalog5 names:
6/12 months with ≥4/5 names losing (vs 3.70 expected by chance), mean pairwise phi 0.79, mean
Pearson r 0.96 (robust ex-outlier 0.68), mean Jaccard 0.85. Symbol-level panel and optional
Donchian sanity checks agree. This is a common basket-regime failure, not name-specific
microstructure. The portfolio-diversification exploration's two-month hint is now systematically
confirmed. However, this **blocks** §8 in-class portfolio combination — the precondition
"losses not strongly correlated" fails. Next = owner decision on §13 non-correlated data or
target revisit (see Next planned step).

## Next planned step (decision point for the owner)

**Catalog5 correction complete.** Four names (`BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`,
`BB_20_2_EMA200`) are now **CONDITIONAL** (FREEZE withdrawn 2026-10-02 evening); `EMA3_21_50_200`
and `DONCHIAN_55_NO_TRAIL` remain **FREEZE** (full protocol pass on own trades). Among
CONDITIONAL catalog5, highest priority = `BB_20_25_EMA200` (best monthly floor 3/12 on one
series, best series-positive rate 9/10, cited in catalog5 monthly note as nearest to checklist).

**Shared-losing-months CONFIRMED still stands** (H-CATALOG5-SHARED-LOSING-MONTHS-01): Train-1
losing months cluster far above chance across all five catalog5 names (6/12 with ≥4/5 losing
vs 3.70 expected; phi 0.79, Pearson 0.96, Jaccard 0.85) — a common basket regime, not
idiosyncratic failures. This **blocks** §8 in-class portfolio diversification (precondition
"losses not strongly correlated" fails). Combining catalog5 names would not improve monthly
regularity. However, this diagnostic finding does **not** license class-wide FREEZE — it only
blocks portfolio combination.

**Next = continue protocol loop on CONDITIONAL catalog5** (one name, one hypothesis, on an
open axis), NOT owner §13-only gate. Highest priority: `BB_20_25_EMA200`, open axis =
entry-vol/abs-ATR own-trades gate (or position sizing). Do not invent new OHLCV axes; do not
start another catalog search. But do **not** jump to §13 non-correlated data — finish the
per-name protocol pass first on the CONDITIONAL names.

> **Infra note (2026-10-02):** both worker channels were down when this ran — codex quota
> exhausted, `claude-bridge` provider `not_ready`. H-CATALOG5-BREADTH-REGIME-01 was therefore
> executed **inline by the coordinator** as a fallback. Restore a worker channel before the next
> experiment so §16 delegation applies.

## Coordinator operating model

- **Work is delegated through Limen**, not done inline. Coordinator writes the pre-registration
  note + a ticket in `spec/features/active/FNNN-slug/ticket.md`, then `limen spawn` a worker;
  reviews the candidate branch; merges or rejects. The coordinator does the *thinking*
  (autopsy, hypothesis design, decision); workers do the *implementation + runs*.
- **Max 2 workers at once.** Check `limen jobs --running` before spawning.
- **Model-level economy.** Implementation/backtest workers that follow a precise spec run on
  the **codex** provider (`--provider openai-codex`, e.g. `gpt-5.6-sol` for causality-sensitive
  code, `gpt-5.3-codex-spark` for routine) to spare the Claude subscription. Reserve Claude
  engine for review or genuinely hard reasoning. Pick the lowest level that will get it right.
- **Two worker channels; test by spawning, not by `pi auth check`.** `--provider openai-codex`
  (separate quota) and `--provider claude-bridge --model claude-sonnet-4-5` (economical Claude)
  both merge. `pi auth check --provider claude-bridge` can falsely report `not_ready` even while
  the bridge is serving the live session — do NOT trust it; the only real test is a spawn. If
  codex returns "usage limit reached", fall back to `claude-bridge` (sonnet-4-5) rather than
  stalling or running inline.
- **§15 report home:** the mandatory end-of-series Coordinator report (protocol §15, Q1–10)
  is recorded in the **§15 Coordinator report** section just below, updated at the end of each
  series, and also delivered to the human in chat.
- **Post-test pipeline is pre-decomposed (protocol §16).** The repeatable work after every
  experiment (metrics §10, monthly §6, registry §14, profile rows, digest) is NOT recomputed by
  hand — copy the ready tickets from `spec/features/_post_test/`, fill four placeholders, and
  dispatch per `spec/features/_post_test/DISPATCH.md` (codex spark, max 2 workers). Reserved for
  the coordinator: the `decision` value, the §15 report, the next hypothesis, the profile
  `status:` line.

## §15 Coordinator report (updated 2026-10-02 evening, after catalog5 FREEZE→CONDITIONAL correction)

1. **Best strategy now?** None promotable. Among CONDITIONAL, `BB_20_25_EMA200` / `EMA_50_200`
   (best monthly floors 3/12 on one series each, best series-positive rates in catalog5).
   `EMA3_21_50_200` and `DONCHIAN_55_NO_TRAIL` remain **FREEZE** (full protocol pass).
2. **Why best?** Best surviving screen + best monthly floor of the catalog5 class; but not
   validated (0/10 series clear §7).
3. **Edge from many trades or few big wins?** Few big wins. EMA3_21: 4 of 402 trades = full net;
   2024-11 alone = +813 of +817; top-3 winners = 97% of net.
4. **Earns when?** High-conviction long breakouts that run to the opposite EMA extreme
   (`signal_reverse`), concentrated in Oct–Nov 2024; longs carry (+875), shorts don't (−58).
5. **Loses when?** Shared basket regime (now systematically confirmed H-CATALOG5-SHARED-LOSING-MONTHS-01,
   not just EMA3_21 within-name hint) — 6/12 Train-1 months have ≥4/5 catalog5 names losing
   together (vs 3.70 chance; phi 0.79, Pearson 0.96); 68.7% of trades die at the fixed stop
   (0% WR by construction).
6. **Rejected hypotheses?** On `EMA3_21_50_200` own trades: entry-vol/abs-ATR gate, exit-class,
   partial-exit, long-only, breadth regime (all independently falsified). On catalog5 class:
   exit-class, partial-exit (ran on all five series); long-only + breadth levers (class-closure
   ran on four names, but that does NOT exhaust per-name protocol pass). Wider class: take-profit,
   trailing, EMA-trend confirm, cross-symbol agreement, loss-cooldown, vol-inverse sizing,
   BTC-ER filter (btc_filter H2-falsified), ~20 swarm families (all H2-falsified).
7. **Unresolved problem?** Monthly regularity. The losses are a shared basket regime
   (systematically confirmed H-CATALOG5-SHARED-LOSING-MONTHS-01: 6/12 months with ≥4/5 names
   losing together, phi 0.79, Pearson 0.96). On `EMA3_21_50_200` (full protocol pass), every
   expectancy-raising lever leaves floor ≥7/12 because the regime makes both losses and runners.
   On the four CONDITIONAL catalog5 names, entry+sizing axes remain open (not independently
   tested on own trades). In-class portfolio combination (§8) is BLOCKED — losses strongly
   correlated.
8. **Next experiment & why?** Continue protocol loop on CONDITIONAL catalog5 (one name, one hyp,
   one open axis). Highest priority: `BB_20_25_EMA200` (best monthly floor / journal cite),
   open axis = entry-vol/abs-ATR own-trades gate (or position sizing). NOT owner §13-only gate.
   Finish per-name protocol pass before moving to non-correlated data.
9. **Why not a random search?** §7 develop-before-abandon. Finish the per-name protocol loop
   first on CONDITIONAL catalog5. §13 (non-correlated data) remains an option after that, but
   requires written non-correlated-mechanism justification + budget + falsification. Random
   widening remains forbidden by §9/§13.
10. **What result confirms/refutes the next hypothesis?** Same bar as before: falsified unless,
    on the frozen Train-1 basket, it lowers the pooled losing-month floor below baseline (7/12
    for most catalog5 names under class-closure; name-specific baseline from autopsy) while
    keeping ≥50% of big-winner PnL and holding for ≥2 carrying symbols.

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
- **2026-10-02** — **H-CATALOG5-BREADTH-REGIME-01 = FALSIFIED**
  (`spec/research/F006-hypothesis-catalog5-breadth-regime.md`, `scripts/f006_breadth_regime_experiment.py`,
  `output/f006_breadth_regime/`). Causal basket-breadth veto (frac of 5 symbols above own EMA200)
  at B∈{0.4,0.6,0.8}: control reproduced baseline exactly (+817/402/7); no B lowers the pooled
  losing-month floor below 7/12 (falsifier a). Expectancy up (2.03→3.06) but tails cut (B80 keeps
  59% big-winner PnL) and per-symbol floors mostly worsen. Regime axis closed on EMA3_21's own
  trades (not by transfer). **`EMA3_21_50_200` → FREEZE** (all axes exhausted on own trades). Run
  **inline by the coordinator** because both worker channels were down (codex quota exhausted,
  claude-bridge not_ready). Next = owner decision on non-correlated data / target (see above).
- **2026-10-02** — **H-CATALOG5-SHARED-LOSING-MONTHS-01 = CONFIRMED** (branch
  limen/2026-10-02-f006-shared-losing-months-decision-prep, FF-merged to origin/main dc9818e).
  Diagnostic answered the open question: Train-1 losing months are SHARED across all five FREEZE
  catalog5 names (basket regime), not idiosyncratic. 6/12 months with ≥4/5 names losing (vs 3.70
  chance), mean phi 0.79, Pearson 0.96, Jaccard 0.85. Symbol-level panel + Donchian sanity
  checks PASS. This CONFIRMED result **blocks in-class diversification** (§8 precondition
  "losses not strongly correlated" fails), but does NOT license class-wide FREEZE. Decision docs
  filled (hypothesis card, journal, build.md NOW).
- **2026-10-02 evening** — catalog5 FREEZE→CONDITIONAL correction (owner-locked). Four names
  unfrozen: `BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`, `BB_20_2_EMA200` now
  **CONDITIONAL**; `EMA3_21_50_200` FREEZE kept (full loop on own trades). Class-closure/
  shared-months do NOT substitute full per-name protocol pass; only axes independently tested
  on each name's own trades stay closed. Entry+sizing still open on the four. Next = protocol
  loop on CONDITIONAL catalog5 (one name, one hyp), highest priority `BB_20_25_EMA200`. Docs:
  four strategy profiles, RESEARCH_JOURNAL, build.md, new §15 report
  `F006-coordinator-series-report-catalog5-class-closure-correction.md`.
