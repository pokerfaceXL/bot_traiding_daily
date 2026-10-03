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
| `BB_20_25_EMA200` | **CONDITIONAL** | partial (entry-vol FALSIFIED; xsym sizing Val-1 FALSIFIED (c); candle-confirm FALSIFIED (c)) | candle close-strength closed on own trades (`e70161d`, T=0.70, SL drop 1.96pp); breakout depth and HTF direction still open; do not FREEZE | `strategy_profiles/BB_20_25_EMA200.md` |
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

**Next = `H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01`** (pre-registered, Train-1 only; ticket
`spec/features/active/F006-bb2025-entry-breakout-depth-01/ticket.md`). Not yet run.
Candle close-strength (`H-BB-20-25-ENTRY-CANDLE-CONFIRM-01`) is **FALSIFIED (c)** at
`e70161d`: best T=0.70 mean +$6.38/series, initial-SL drop 1.96pp vs required 10pp,
big-winner PnL retained 100%, floor still 7/12. That closes one entry variant on this
name's own trades. It does **not** close breakout depth or HTF direction, and it does
**not** license FREEZE or a transfer to the other CONDITIONAL names. Entry-vol stays
FALSIFIED (`3788f11`). The xsym sizing formula stays FALSIFIED (c) on Val-1 (`89e936a`);
do not retune it. Holdout stays closed. Do not jump to §13.

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

## §15 Coordinator report (updated 2026-10-03 ~09:49 Europe/Warsaw, after BB_20_25 candle confirm)

Short series report: `spec/research/F006-coordinator-series-report-bb-20-25-entry-candle-confirm.md`.

Candle close-strength is **FALSIFIED (c)** (`e70161d`). `BB_20_25_EMA200` stays
**CONDITIONAL**. Do not FREEZE. Next experiment is pre-registered 
(not yet run). HTF direction stays open and is not the next test. Q1–Q10 for this
series are in that report. The answers below are the standing cross-name report.


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
   partial-exit, long-only, breadth regime (all independently falsified). On `BB_20_25_EMA200`
   own trades: entry-vol FALSIFIED (a) `3788f11`; xsym sizing formula FALSIFIED (c) `89e936a`;
   candle close-strength FALSIFIED (c) `e70161d`. Exit-class and partial-exit ran on the
   catalog5 series; long-only and breadth have own-trade cells. Those do not close breakout
   depth or HTF direction, and they do not close entry or sizing on the other three
   CONDITIONAL names. Wider class: take-profit, trailing, EMA-trend confirm, cross-symbol
   agreement, loss-cooldown, vol-inverse sizing, BTC-ER filter, ~20 swarm families.
7. **Unresolved problem?** Monthly regularity. The losses are a shared basket regime
   (H-CATALOG5-SHARED-LOSING-MONTHS-01: 6/12 months with ≥4/5 names losing together, phi
   0.79, Pearson 0.96). On `BB_20_25_EMA200`, candle close-strength did not cut initial-SL
   share by 10pp. Breakout depth and HTF direction are still untested on this name's own
   trades. The other three CONDITIONAL names still have entry-vol and sizing untested on
   their own trades. In-class portfolio combination (§8) is BLOCKED.
8. **Next experiment & why?** `H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01`, pre-registered after
   the candle decision: band-normalized close distance beyond `bb_20_2.5`, D in
   {0.02, 0.05, 0.10, 0.25, 0.50}, Train-1 only. Not HTF in the same test, not a retune
   of the candle threshold or the sizing formula, not another catalog name, not FREEZE,
   not holdout.
9. **Why not a random search?** §13 is not met. The name is not exhausted. The next test
   is the next open entry variant on the same name, after a written mechanism. A falsified
   candle gate is not a reason to switch names.
10. **What result confirms/refutes the next hypothesis?** Pre-registered on the breakout-depth
    card. Pass: mean Train-1 net above +82.900262, initial-SL share down ≥10pp at the
    best-PnL D, ≥50% of big-winner PnL retained, pooled floor strictly below 7/12, and
    mean trades/series ≥10. Any one of falsifiers (a)–(e) fails it. Holdout is not opened.

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
- **2026-10-02** — **H-BB-20-25-ABS-ATR-ENTRY-GATE-01 pre-registered** (entry-vol own-trades
  gate on highest-priority CONDITIONAL `BB_20_25_EMA200`). Five-threshold Train-1 ablation
  {median, 1.0%, 1.25%, 1.5%, 2.0%}; big-winner freeze net≥29.9; expect possible falsification
  (Donchian+EMA3_21 entry-vol both failed), but this axis was never independently run on BB's
  own trades.
- **2026-10-02 night** — **H-BB-20-25-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)** (tip `3788f11`,
  review PASS `2026-10-02-f006-bb2025-entry-vol-review-45b3ee8a`, FF-merged to `origin/main`).
  Control mean +82.90 reproduced; all 5 T below baseline. Entry-vol axis closed on
  `BB_20_25_EMA200` own trades. Status stays **CONDITIONAL** (do not FREEZE). Decision +
  profile + §15 report
  `spec/research/F006-coordinator-series-report-bb-20-25-abs-atr-entry-gate.md` filled.
- **2026-10-02 night** — **H-BB-20-25-XSYM-AGREE-SIZING-01 pre-registered** (next open axis =
  position sizing on same name; cross-symbol agreement stake via `stake_series`; orthogonal to
  ATR). Ticket `spec/features/active/F006-bb-20-25-xsym-agree-sizing/ticket.md`.


- **2026-10-03 early** — **H-BB-20-25-XSYM-AGREE-SIZING-01 = NOT FALSIFIED** (Train-1 only).
  Tip `1c9ff7e` FF-merged to `origin/main`. Reviews: metric/lookahead FAIL then causal PASS
  `2026-10-02-f006-bb2025-xsym-agree-sizing-re-ca2e09d0`. Control +82.90, n=512, floor 7/12;
  causal sized +147.71, floor 5/12, mult gap +0.119, stake_cv 0.526. The first FALSIFIED (b)
  at 11/12 is withdrawn (union floor + lookahead). Decision = **REFINE**. `BB_20_25_EMA200`
  stays **CONDITIONAL** (do not FREEZE; validation still open; entry-vol remains FALSIFIED).
  Next was Validation-1, now decided FALSIFIED (c) at `89e936a`. See the 2026-10-03 morning log line.

- **2026-10-03 morning** — **H-BB-20-25-XSYM-AGREE-SIZING-VAL1-01 = FALSIFIED (c)**.
  Tip `89e936a` FF-merged to `origin/main`. Gate-stop review PASS `d255f0e`
  (`2026-10-03-f006-bb2025-xsym-agree-sizing-va-d8413e48`); rescore review PASS `89e936a`
  (`2026-10-03-f006-bb2025-xsym-agree-sizing-va-9a56d56a`). The Train-1 control mismatch
  (mean 83.048644 vs 82.900262, n=512) was the short-run `end_of_data` force-close on 240m;
  before scoring, the absolute 1e-6 gate was relaxed to relative 0.25% of |reference mean|
  (n=512 exact). Falsifiers unchanged. Control mean -1.371, sized mean -0.401, losing
  months 2/3 both, mult gap -0.026. Formula closed on this name. Decision = **FALSIFIED**.
  `BB_20_25_EMA200` stays **CONDITIONAL** (do not FREEZE; entry structure still open;
  entry-vol remains FALSIFIED). Next = one new §8 entry-structure hypothesis, not spawned
  here. §15: `spec/research/F006-coordinator-series-report-bb-20-25-xsym-agree-sizing-val1.md`.

- **2026-10-03 morning** — **H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 pre-registered** (§8 entry-
  structure / candle close-strength gate on CONDITIONAL `BB_20_25_EMA200` own trades; T∈
  {0.50,0.60,0.70,0.80,0.90}; Train-1 only). Not a Val-2 of the closed xsym sizing formula.
  Ticket `spec/features/active/F006-bb2025-entry-structure-01/ticket.md`.

- **2026-10-03 ~09:49 Europe/Warsaw** — **H-BB-20-25-ENTRY-CANDLE-CONFIRM-01 = FALSIFIED (c)**.
  Tip `e70161d` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb2025-entry-structure-revi-3883672f`. Control +82.900262 / n=512 /
  initial-SL 58.01% / floor 7/12 reproduced. Best T=0.70 mean +$6.38/series, initial-SL
  drop 1.96pp (required 10pp), big-winner PnL retained 100%. Decision = **FALSIFIED (c)**.
  `BB_20_25_EMA200` stays **CONDITIONAL**. Do not FREEZE. Candle close-strength is closed
  on this name's own trades; breakout depth and HTF direction are not. Next = one
  breakout-depth hypothesis, not spawned here. §15:
  `spec/research/F006-coordinator-series-report-bb-20-25-entry-candle-confirm.md`.

- **2026-10-03** — **H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01 pre-registered** (§8 breakout
  depth on CONDITIONAL `BB_20_25_EMA200` own trades; D∈{0.02, 0.05, 0.10, 0.25, 0.50}
  as a fraction of `bb_20_2.5` width; Train-1 only). Not a candle retune, not abs-ATR,
  not a Val-2 of the closed xsym formula, not HTF. HTF direction stays open. Do not
  FREEZE. Ticket `spec/features/active/F006-bb2025-entry-breakout-depth-01/ticket.md`.
