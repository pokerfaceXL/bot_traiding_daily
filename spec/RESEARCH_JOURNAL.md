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
| `BB_20_25_EMA200` | **FREEZE** | yes (own trades) | every licensed axis closed on own trades, last was HTF direction FALSIFIED (a)+(c)+(d) at `3495b16` (−$12.38/series, SL +2.44pp, floor still 7/12); not a class closure | `strategy_profiles/BB_20_25_EMA200.md` |
| `EMA_50_200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/EMA_50_200.md` |
| `EMA3_13_50_200` | **CONDITIONAL** | partial (class levers only; full per-name loop incomplete) | FREEZE withdrawn — class-closure/shared-months ≠ full protocol pass; entry+sizing still open | `strategy_profiles/EMA3_13_50_200.md` |
| `BB_20_2_EMA200` | **CONDITIONAL** | partial (class levers + own-trades entry-vol FALSIFIED; xsym sizing Train-1 NOT FALSIFIED; Val-1 NOT FALSIFIED; Val-2 NOT FALSIFIED; Val-3 NOT FALSIFIED; Val-4 next; other entry structure open) | Val-3 NOT FALSIFIED at `cf00663` (mean +1.772572→+8.007368, months 2≤2, gap +0.179831); caveats not a floor; do not FREEZE; Val-4 next | `strategy_profiles/BB_20_2_EMA200.md` |
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

**BB_20_25 loop closed.** `BB_20_25_EMA200` is **FREEZE** (2026-10-03 ~10:56 Europe/Warsaw)
after HTF direction FALSIFIED (a)+(c)+(d) at `3495b16`. `EMA3_21_50_200` and
`DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Remaining CONDITIONAL catalog5, in journal
priority: `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`. Highest
priority now = `BB_20_2_EMA200` (entry-vol FALSIFIED at `f7ac677`; xsym sizing Train-1 NOT FALSIFIED at `1774a8a`; Val-1 NOT FALSIFIED at `7e18786`; Val-2 NOT FALSIFIED at `7798bbb`; Val-3 NOT FALSIFIED at `cf00663`; Validation-4 next; other entry structure still open). Do not treat the BB_20_25 loop as those names' tests.

**Shared-losing-months CONFIRMED still stands** (H-CATALOG5-SHARED-LOSING-MONTHS-01): Train-1
losing months cluster far above chance across all five catalog5 names (6/12 with ≥4/5 losing
vs 3.70 expected; phi 0.79, Pearson 0.96, Jaccard 0.85) — a common basket regime, not
idiosyncratic failures. This **blocks** §8 in-class portfolio diversification (precondition
"losses not strongly correlated" fails). Combining catalog5 names would not improve monthly
regularity. However, this diagnostic finding does **not** license class-wide FREEZE — it only
blocks portfolio combination.

**BB_20_2 sizing Val-3 NOT FALSIFIED; name stays CONDITIONAL.**
`H-BB-20-2-ABS-ATR-ENTRY-GATE-01` remains **FALSIFIED (a)+(c)** at `f7ac677`.
`H-BB-20-2-XSYM-AGREE-SIZING-01` remains **NOT FALSIFIED / REFINE** at `1774a8a`.
`H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01` remains **NOT FALSIFIED** at `7e18786`.
`H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01` remains **NOT FALSIFIED** at `7798bbb`.
`H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01` is **NOT FALSIFIED** at `cf00663`
(Claude review PASS `2026-10-03-f006-bb202-xsym-agree-sizing-val-607c9de9`,
FF from `7144b8f`). Gate PASS: Train-1 mean 95.463371 vs 95.3217987
(diff 0.141572 ≤ 0.23830449675), n=756. Val-3 mean +1.772572 → +8.007368;
losing months 2≤2; mult gap +0.179831; n 181/1407; stake_cv 0.455172.
Means are thin; 6/10 series improve; entry-net gain is mostly 2025-10
(+57.076733) and 2025-09 is worse under sizing (−11.868494). Seven
force-closes at the 2025-12-01 cut. No pre-registered margin floor.
`decision_if_pass` is continue to Validation-4, not holdout and not a
stop. Do not FREEZE: §11 still has Validation-4 and holdout, and other
§8 entry structure is still open. Do not abandon this arm for a new
entry axis before Validation-4 (§7, §3.10). `BB_20_25_EMA200` remains
**FREEZE** on its own loop; do not copy it. Do not jump to `EMA_50_200`
or `EMA3_13_50_200`. Exit on `BB_20_2_EMA200` stays closed. Holdout stays
closed.

**Next = `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01`** (pre-registered;
ticket `spec/features/active/F006-bb202-xsym-agree-sizing-val4-01/ticket.md`).
Same frozen formula. Score this name's Validation-4 entries only
(2025-12-01 ≤ entry < 2026-03-01, F005 protocol §3.2, named by the Val-3
card's `decision_if_pass`). Control gate is relative 0.25% of |+95.3217987|
and Train-1-entry n=756 exact — not absolute 1e-6, and not a retarget onto
95.463371. Falsifiers (a)–(e) are not loosened. Not holdout. Not a new family.

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

## §15 Coordinator report (updated 2026-10-03 ~13:40 Europe/Warsaw, BB_20_2 xsym sizing Val-3)

This series: `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing-val3.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing-val2.md`.
`BB_20_25_EMA200` stays **FREEZE** on its own loop and is not a class closure.

`H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01` is **NOT FALSIFIED** at `cf00663`.
Decision = **CONDITIONAL** / continue (`decision_if_pass`). Do not FREEZE.
The card does not stop on thin means or one-month concentration. Next is
pre-registered `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01`. Not holdout.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. The frozen sizing arm cleared Train-1, Validation-1, Validation-2, and Validation-3 and is not finished under §11. Screen is this name's, not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins. Val-3 sized big winners at net≥29.9 are 3 trades / 148.010545 (control 1 / 38.364839). Most of the entry-net gain is 2025-10 (+57.076733).
4. **Earns when?** `signal_reverse` runners, and on this window when stake scaled the 2025-10 basket. Winner mult above loser mult (+0.179831).
5. **Loses when?** Both arms are small on the mean (control +1.772572, sized +8.007368). Sized was worse in 2025-09 (−11.868494). Shared basket regime and `initial_sl` are unchanged. Losing-month count did not rise (2≤2) but did not fall. 4/10 series do not improve.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `f7ac677`. Exit, long-only, breadth closed. This sizing formula is not rejected. BB_20_25 closures, including its Val-1 `89e936a` and its FREEZE, do not transfer.
7. **Unresolved problem?** Whether the weights keep helping on Validation-4. Monthly regularity is not solved. The Validation-3 gain is thin on the mean, 6/10 series, and concentrated in 2025-10. Seven force-closes at 2025-12-01. §11 validation is not complete. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01`. Val-3 `decision_if_pass` names Validation-4 of the same formula, not holdout and not a stop. §3.10 and §11: next frozen window before another axis. §7: do not abandon the arm first. Window is F005 §3.2 Validation 4 (2025-12-01 ≤ entry < 2026-03-01). Not FREEZE. Not holdout.
9. **Why not a random search?** One licensed axis on this name has four passes and the next protocol window already named by the card. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not open a new entry gate in parallel. Do not open holdout.
10. **What result confirms/refutes the next hypothesis?** On the Val-4 card. Control gate: relative 0.25% of |+95.3217987| and Train-1-entry n=756 exact, before any Validation-4 scoring. Pass: sized mean above that window's own control, losing-month count not higher, mult gap > 0, n invariant, stake_cv > 0.05. Any of (a)–(e) fails it. Falsifiers are not loosened. Holdout is not opened.

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

- **2026-10-03 ~10:20 Europe/Warsaw** — **H-BB-20-25-ENTRY-BREAKOUT-DEPTH-01 = FALSIFIED (a)+(c)**.
  Tip `0685ce5` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb2025-entry-breakout-depth-2dd8bcfc`. Control +82.900262 / n=512 /
  initial-SL 58.01% / floor 7/12 reproduced. Best D=0.02 mean +71.985313 (−$10.91/series),
  initial-SL share 58.07% (rose, required drop 10pp), D=0.50 zero trades. Decision =
  **FALSIFIED (a)+(c)**. `BB_20_25_EMA200` stays **CONDITIONAL**. Do not FREEZE.
  Breakout depth is closed on this name's own trades; HTF direction is not. §15:
  `spec/research/F006-coordinator-series-report-bb-20-25-entry-breakout-depth.md`.

- **2026-10-03 ~10:20 Europe/Warsaw** — **H-BB-20-25-ENTRY-HTF-DIRECTION-01 pre-registered**
  (§8 HTF direction on CONDITIONAL `BB_20_25_EMA200` own trades; prior fully closed
  4-bar HTF candle must agree; Train-1 only; one binary gate). Not a retune of D, not
  candle close-strength, not abs-ATR, not long-only, not a Val-2 of the closed xsym
  formula. Do not FREEZE before this axis has an own-trades result. Ticket
  `spec/features/active/F006-bb2025-entry-htf-direction-01/ticket.md`.

- **2026-10-03 ~10:56 Europe/Warsaw** — **H-BB-20-25-ENTRY-HTF-DIRECTION-01 = FALSIFIED (a)+(c)+(d)**.
  Tip `3495b16` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb2025-entry-htf-direction--364758a0`. Control +82.900262 / n=512 /
  initial-SL 58.01% / floor 7/12 reproduced. Gated htf_4 mean +70.515667 (−$12.38/series),
  initial-SL 60.45% (+2.44 pp), big-winner PnL retained 96.4%, floor 7/12, 44.5
  trades/series. (b) and (e) did not fire. Decision = **FALSIFIED (a)+(c)+(d)**.
  Every licensed axis on `BB_20_25_EMA200` now has an own-trades citation, so the
  profile is **FREEZE** (not REJECT; ungated book still aggregate-positive). Not a
  class closure. §15 loop report:
  `spec/research/F006-coordinator-series-report-bb-20-25-loop.md`.

- **2026-10-03 ~10:56 Europe/Warsaw** — **H-BB-20-2-ABS-ATR-ENTRY-GATE-01 pre-registered**
  (entry-vol / abs-ATR on CONDITIONAL `BB_20_2_EMA200` own trades; T = this name's
  median plus 1.0/1.25/1.5/2.0%; Train-1 only; control mean +95.3217987). Not a
  transfer of `3788f11` or of the HTF result. Exit on this name stays closed.
  Ticket `spec/features/active/F006-bb202-abs-atr-01/ticket.md`.

- **2026-10-03 ~11:22 Europe/Warsaw** — **H-BB-20-2-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)+(c)**.
  Tip `f7ac677` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb202-abs-atr-review-59bf2edf`. Control +95.3217987 / n=756 /
  initial-SL 47.35% / floor 7/12 reproduced (max abs train1 diff 0). Best
  T=t_2_0 mean +64.0461, initial-SL drop 3.45pp, big-winner PnL retained 72.3%
  on the published metric. (b), (d), (e) did not decide the cell. Decision =
  **FALSIFIED (a)+(c)**. `BB_20_2_EMA200` stays **CONDITIONAL**. Do not FREEZE.
  Entry-vol / abs-ATR is closed on this name's own trades. Sizing and other
  §8 entry structure are not. Not a class closure. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-abs-atr-entry-gate.md`.

- **2026-10-03 ~11:22 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-01 pre-registered**
  (position sizing on CONDITIONAL `BB_20_2_EMA200` own trades; one formula
  `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`; causal one-bar shift;
  Train-1 only; control mean +95.3217987). Not an abs-ATR retune. Not a
  transfer of the BB_20_25 sizing result. Entry structure on this name stays
  open. Do not FREEZE. Ticket
  `spec/features/active/F006-bb202-xsym-agree-sizing-01/ticket.md`.

- **2026-10-03 ~11:57 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-01 = NOT FALSIFIED / REFINE**.
  Tip `1774a8a` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb202-xsym-agree-sizing-rev-dff7bccd`. Control +95.3217987
  reproduced (max abs diff 0). Sized mean +146.632696. Floor 7/12 → 6/12
  (only 2024-06 flips). Mult gap +0.086642. stake_cv 0.491784. n=756
  invariant. (a)–(e) clear. ~110% of the entry-net gain is 2024-11. Decision
  = **REFINE** (`decision_if_pass`). `BB_20_2_EMA200` stays **CONDITIONAL**.
  Do not FREEZE. Not a transfer of the BB_20_25 Val-1 fail. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing.md`.

- **2026-10-03 ~11:57 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01 pre-registered**
  (Validation-1 of the frozen causal stake on CONDITIONAL `BB_20_2_EMA200`
  own trades; same formula; entries 2025-03-01 ≤ entry < 2025-06-01).
  Control gate is relative 0.25% of |+95.3217987| and Train-1-entry n=756
  exact. Falsifiers (a)–(e) not loosened. Not holdout. Not a new entry axis.
  Not FREEZE. Ticket
  `spec/features/active/F006-bb202-xsym-agree-sizing-val1-01/ticket.md`.

- **2026-10-03 ~12:35 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL1-01 = NOT FALSIFIED**.
  Tip `7e18786` FF-merged to `origin/main` from `738b9ff`. Claude review PASS
  `2026-10-03-f006-bb202-xsym-agree-sizing-val-ab5c3864`. Gate PASS: Train-1
  mean 95.463371 vs 95.3217987 (diff 0.141572 ≤ 0.2383045), n=756 exact.
  Val-1 mean −9.270577 → −4.002329; losing months 2≤2; mult gap +0.026608;
  n 211/1031; stake_cv 0.481509. (a)–(e) clear. Both means negative; entry-net
  gain concentrated in 2025-05. Decision = **CONDITIONAL** (`decision_if_pass`).
  `BB_20_2_EMA200` stays **CONDITIONAL**. Do not FREEZE. Not holdout. Not a
  copy of the BB_20_25 FREEZE. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing-val1.md`.

- **2026-10-03 ~12:35 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01 pre-registered**
  (Validation-2 of the frozen causal stake on CONDITIONAL `BB_20_2_EMA200`
  own trades; same formula; entries 2025-06-01 ≤ entry < 2025-09-01, F005
  protocol §3.2). Control gate is relative 0.25% of |+95.3217987| and
  Train-1-entry n=756 exact. Falsifiers (a)–(e) not loosened. Not holdout.
  Not Validation-3. Not a new entry axis. Not FREEZE. Ticket
  `spec/features/active/F006-bb202-xsym-agree-sizing-val2-01/ticket.md`.

- **2026-10-03 ~13:13 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL2-01 = NOT FALSIFIED**.
  Tip `7798bbb` FF-merged to `origin/main` from `1eced44`. Claude review PASS
  `2026-10-03-f006-bb202-xsym-agree-sizing-val-c1c25e2f`. Gate PASS: Train-1
  mean 95.463371 vs 95.3217987 (diff 0.141572 ≤ 0.23830449675), n=756 exact.
  Val-2 mean +2.331879 → +2.551244; losing months 2≤2; mult gap +0.031667;
  n 195/1226; stake_cv 0.514115. (a)–(e) clear. Margin thin (+0.219365/series);
  entry-net gain is 2025-07. No pre-registered floor. Decision = **CONDITIONAL**
  / continue (`decision_if_pass` → Validation-3, not holdout). `BB_20_2_EMA200`
  stays **CONDITIONAL**. Do not FREEZE. Not a copy of the BB_20_25 FREEZE. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing-val2.md`.

- **2026-10-03 ~13:13 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01 pre-registered**
  (Validation-3 of the frozen causal stake on CONDITIONAL `BB_20_2_EMA200`
  own trades; same formula; entries 2025-09-01 ≤ entry < 2025-12-01, F005
  protocol §3.2, named by the Val-2 card). Control gate is relative 0.25% of
  |+95.3217987| and Train-1-entry n=756 exact. Falsifiers (a)–(e) not loosened.
  Not holdout. Not Validation-4. Not a new entry axis. Not FREEZE. Ticket
  `spec/features/active/F006-bb202-xsym-agree-sizing-val3-01/ticket.md`.

- **2026-10-03 ~13:40 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL3-01 = NOT FALSIFIED**.
  Tip `cf00663` FF-merged to `origin/main` from `7144b8f`. Claude review PASS
  `2026-10-03-f006-bb202-xsym-agree-sizing-val-607c9de9`. Gate PASS: Train-1
  mean 95.463371 vs 95.3217987 (diff 0.141572 ≤ 0.23830449675), n=756 exact.
  Val-3 mean +1.772572 → +8.007368; losing months 2≤2; mult gap +0.179831;
  n 181/1407; stake_cv 0.455172. (a)–(e) clear. Means thin; 6/10 series;
  entry-net gain mostly 2025-10; 2025-09 worse under sizing; 7 force-closes.
  No pre-registered floor. Decision = **CONDITIONAL** / continue
  (`decision_if_pass` → Validation-4, not holdout). `BB_20_2_EMA200` stays
  **CONDITIONAL**. Do not FREEZE. Not a copy of the BB_20_25 FREEZE. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-xsym-agree-sizing-val3.md`.

- **2026-10-03 ~13:40 Europe/Warsaw** — **H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01 pre-registered**
  (Validation-4 of the frozen causal stake on CONDITIONAL `BB_20_2_EMA200`
  own trades; same formula; entries 2025-12-01 ≤ entry < 2026-03-01, F005
  protocol §3.2, named by the Val-3 card). Control gate is relative 0.25% of
  |+95.3217987| and Train-1-entry n=756 exact. Falsifiers (a)–(e) not loosened.
  Not holdout. Not a new family. Not FREEZE. Ticket
  `spec/features/active/F006-bb202-xsym-agree-sizing-val4-01/ticket.md`.
