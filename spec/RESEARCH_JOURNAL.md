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
| `BB_20_25_EMA200` | **FREEZE** | yes (class evidence) | all axes falsified on catalog5 class evidence via H-CATALOG5-CLASS-CLOSURE-01; exit closed earlier, decisive levers (long-only, breadth) cannot lower pooled floor 7/12 | `strategy_profiles/BB_20_25_EMA200.md` |
| `EMA_50_200` | **FREEZE** | yes (class evidence) | all axes falsified on catalog5 class evidence via H-CATALOG5-CLASS-CLOSURE-01; exit closed earlier, decisive levers cannot lower pooled floor 7/12 | `strategy_profiles/EMA_50_200.md` |
| `EMA3_13_50_200` | **FREEZE** | yes (class evidence) | all axes falsified on catalog5 class evidence via H-CATALOG5-CLASS-CLOSURE-01; exit closed earlier, decisive levers cannot lower pooled floor 7/12 | `strategy_profiles/EMA3_13_50_200.md` |
| `BB_20_2_EMA200` | **FREEZE** | yes (class evidence) | all axes falsified on catalog5 class evidence via H-CATALOG5-CLASS-CLOSURE-01; exit closed earlier, decisive levers cannot lower pooled floor 7/12 | `strategy_profiles/BB_20_2_EMA200.md` |
| ~20 swarm families (beta_gate, btc_filter, htf_gap_midfill, liq_range_eqh, multi_tf_pa, vol_regime_wrap, liq_cascade_proxy, session_regime, sube_inv_fvg, …) | FALSIFIED (H2) | partial (old process) | several H1-positive aggregate, but all H2-falsified with the same fat-tail shape; mean-reversion/session/sube negative | `output/f006_cross_family_digest.md` |
| `XS_RS_*` (cross-sectional RS), `ORB_UTC_*`, `ORB_LON/NY_*` (session ORB) | CLOSED / FALSIFIED | yes | new non-catalog signal families; H1 falsified or H2 0/N → closed | `F006-hypothesis-{cross-sectional-rs,opening-range-breakout,orb-session-anchor}.md` |

## 2026-10-02 — catalog5 class closed: all five names FROZEN on own evidence

**What was completed.** H-CATALOG5-CLASS-CLOSURE-01 closed the catalog5 class on own evidence.
The four remaining catalog5 names (`BB_20_25_EMA200`, `EMA_50_200`, `EMA3_13_50_200`,
`BB_20_2_EMA200`) ran the same two decisive levers that falsified `EMA3_21_50_200`: long-only
direction filter and causal basket-breadth regime veto (B∈{0.4,0.6,0.8}). Class exhaustion
CONFIRMED: no lever lowers any name's pooled losing-month floor below baseline (all hold at
7/12 or worsen to 8–9/12) while meeting the retention criteria (>=50% big-winner PnL, >=2
baseline carrier symbols). Long-only keeps 94–100% of big-winner PnL across all four (shorts
contribute almost no runners), yet the pooled floor holds or worsens because shorts partially
hedge long-losing months. Breadth veto is itself the regime failure's cause, not a gate
against it. Baseline reproduces each autopsy exactly (control fidelity passed).

**All five catalog5 names now FROZEN.** Exit axis closed earlier (`H-CATALOG5-EXIT-CLASS-01`,
`H-CATALOG5-PARTIAL-EXIT-01`). Entry-vol/direction/regime all falsified: `EMA3_21_50_200` on
its own trades (autopsy + H-EMA3-21-LONG-ONLY-01 + H-CATALOG5-BREADTH-REGIME-01); the other
four via class evidence (H-CATALOG5-CLASS-CLOSURE-01). Shared mechanism: 5-symbol basket's
macro regime creates both the losses and the fat-tail runners — no OHLCV lever on the data
currently in the repo isolates them.

**Docs updated:** `spec/research/F006-hypothesis-catalog5-class-closure.md` (Decision section),
the four `strategy_profiles/*.md`, this journal, `build.md` NOW.

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

**Catalog5 class closed; shared-losing-months question systematically confirmed.** All five
catalog5 names are now FROZEN on own evidence (exit axis closed earlier; entry-vol/direction/
regime falsified for `EMA3_21_50_200` on its own trades, and for the other four via class
evidence in H-CATALOG5-CLASS-CLOSURE-01). The shared-regime finding is now systematically
confirmed (H-CATALOG5-SHARED-LOSING-MONTHS-01): Train-1 losing months cluster far above chance
across all five names (6/12 with ≥4/5 losing vs 3.70 expected; phi 0.79, Pearson 0.96, Jaccard
0.85) — a common basket regime, not idiosyncratic failures. This is *un-exploitable* by any
lever on the data currently in the repo: every expectancy-raising lever (long-only, breadth
veto) leaves the monthly floor at or above baseline because the same regime makes both the
losing months and the runners.

**In-class portfolio diversification (F007 direction) is BLOCKED.** The shared-losing-months
CONFIRMED result blocks §8 portfolio combination within catalog5 — the precondition "losses
not strongly correlated" fails. Combining these five names would not improve monthly regularity.

This closes the in-repo OHLCV axes for the catalog5 momentum class. The remaining options are
owner decisions, not another axis:

1. **New, non-correlated data (§13).** Acquire order-flow / open-interest / liquidation /
   cross-asset context and pre-register a genuinely non-correlated mechanism. This is the only
   path that could change the monthly floor; it needs data not in the repo.
2. **Revisit the target.** The daily-regularity goal (100% positive days w/ tolerance) may be
   unreachable with momentum on this basket; the owner may relax tolerance or redefine success.

**Do not** invent new OHLCV axes or start another catalog search — the momentum class is closed
on the data currently available.

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

## §15 Coordinator report (updated 2026-10-02, after EMA3_21 breadth-regime pass)

1. **Best strategy now?** None promotable. `EMA3_21_50_200` is now **FROZEN** (all axes
   falsified on its own trades), as is `DONCHIAN_55_NO_TRAIL`. The best-evidenced remaining
   CONDITIONAL names are `BB_20_25_EMA200` / `EMA_50_200` (3/12 floor) — but their axes have not
   been individually run; the EMA3_21 result makes it very likely they freeze the same way.
2. **Why best?** Widest aggregate-positive span + best monthly floor of the catalog5 class; but
   "best" = best surviving screen, not validated (0/10 series clear §7).
3. **Edge from many trades or few big wins?** Few big wins. EMA3_21: 4 of 402 trades = full net;
   2024-11 alone = +813 of +817; top-3 winners = 97% of net.
4. **Earns when?** High-conviction long breakouts that run to the opposite EMA extreme
   (`signal_reverse`), concentrated in Oct–Nov 2024; longs carry (+875), shorts don't (−58).
5. **Loses when?** Shared basket regime (now systematically confirmed H-CATALOG5-SHARED-LOSING-MONTHS-01,
   not just EMA3_21 within-name hint) — 6/12 Train-1 months have ≥4/5 catalog5 names losing
   together (vs 3.70 chance; phi 0.79, Pearson 0.96); 68.7% of trades die at the fixed stop
   (0% WR by construction).
6. **Rejected hypotheses?** Per-name: entry-vol/abs-ATR gate (now falsified on EMA3_21's own
   trades, not by transfer), exit-class, partial-exit, long-only (expectancy up but regularity
   worse). Class/sibling: take-profit, trailing, EMA-trend confirm, cross-symbol agreement,
   loss-cooldown, vol-inverse sizing, BTC-ER permission filter (btc_filter, H2-falsified),
   ~20 swarm families (all H2-falsified).
7. **Unresolved problem?** Monthly regularity — and it is now shown *un-fixable by any in-repo
   lever*. The losses are a shared basket regime (systematically confirmed H-CATALOG5-SHARED-LOSING-MONTHS-01:
   6/12 months with ≥4/5 names losing together, phi 0.79, Pearson 0.96 — not idiosyncratic);
   every expectancy-raising lever (long-only, vol gate, breadth regime) leaves the floor ≥7/12
   because the same regime makes both the losses and the runners. In-class portfolio combination
   (§8) is BLOCKED — losses strongly correlated. Fixing it needs a genuinely non-correlated
   signal, i.e. new data.
8. **Next experiment & why?** None in-repo is licensed. The open question (shared vs
   idiosyncratic losing months) is systematically ANSWERED: CONFIRMED basket regime
   (H-CATALOG5-SHARED-LOSING-MONTHS-01), which BLOCKS §8 in-class portfolio diversification.
   The decision is the owner's: acquire non-correlated data (order-flow / OI / liquidation /
   cross-asset, §13) or revisit the daily-regularity target. Do not invent new OHLCV axes or
   another catalog5 entry family.
9. **Why not a random search?** §13 now largely holds (the failure shares one mechanism across
   four independent axes), but it still requires a *written* non-correlated-mechanism
   justification + budget + falsification, which depends on data not yet in the repo. Random
   widening remains forbidden by §9/§13.
10. **What result confirms/refutes the next hypothesis?** For option 1 (new-data mechanism): it
    is falsified unless, on the frozen Train-1 basket, it lowers the pooled losing-month floor
    below 7/12 while keeping ≥50% of big-winner PnL and holding for ≥2 carrying symbols — the
    same bar every in-repo lever has failed.

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
  checks PASS. This CONFIRMED result licenses the portfolio / F007 *direction* in principle
  (§8), BUT **blocks in-class diversification** — losses ARE strongly correlated, so combining
  catalog5 names cannot improve monthly regularity. Owner decision required: §13 non-correlated
  data or target revisit. Do not invent OHLCV cards. Decision docs filled (hypothesis card,
  journal, build.md NOW).
