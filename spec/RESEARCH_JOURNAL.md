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

## Next planned step (decision point for the owner)

The `EMA3_21_50_200` protocol loop is **complete and the name is FROZEN** — entry-vol, direction,
exit, and regime are all falsified on its own trades (autopsy + three pre-registered
experiments). The shared-regime finding is confirmed *un-exploitable* by any lever on the data
currently in the repo: breadth, like long-only and the vol gate, raises expectancy but never
lowers the monthly floor, because the same regime makes both the losing months and the runners.

This closes the in-repo axes for the catalog5 momentum class. The remaining options are owner
decisions, not another axis:

1. **New, non-correlated data (§13).** Acquire order-flow / open-interest / liquidation /
   cross-asset context and pre-register a genuinely non-correlated mechanism. This is the only
   path that could change the monthly floor; it needs data not in the repo.
2. **Revisit the target.** The daily-regularity goal (100% positive days w/ tolerance) may be
   unreachable with momentum on this basket; the owner may relax tolerance or redefine success.
3. **Cheap confirmation (optional, in-repo).** Re-run the same four protocol passes on a second
   catalog5 name (e.g. `EMA_50_200`) to confirm the exhaustion is class-wide before freezing the
   whole class. Low value (mechanism already shown 4 independent ways) but fully delegable to
   workers once a worker channel is back.

**Do not** start a broad search or a new family: §13 still requires a *written* non-correlated
mechanism with budget + falsification, which depends on option 1's data.

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
5. **Loses when?** Shared basket regime — 6/12 months have ≥4/5 symbols net-negative together
   (Aug/Sep 2024 = 5/5); 68.7% of trades die at the fixed stop (0% WR).
6. **Rejected hypotheses?** Per-name: entry-vol/abs-ATR gate (now falsified on EMA3_21's own
   trades, not by transfer), exit-class, partial-exit, long-only (expectancy up but regularity
   worse). Class/sibling: take-profit, trailing, EMA-trend confirm, cross-symbol agreement,
   loss-cooldown, vol-inverse sizing, BTC-ER permission filter (btc_filter, H2-falsified),
   ~20 swarm families (all H2-falsified).
7. **Unresolved problem?** Monthly regularity — and it is now shown *un-fixable by any in-repo
   lever*. The losses are a shared basket regime; every expectancy-raising lever (long-only, vol
   gate, breadth regime) leaves the floor ≥7/12 because the same regime makes both the losses and
   the runners. Fixing it needs a genuinely non-correlated signal, i.e. new data.
8. **Next experiment & why?** None in-repo is licensed. The decision is the owner's: acquire
   non-correlated data (order-flow / OI / liquidation / cross-asset, §13) or revisit the
   daily-regularity target. Optional low-value in-repo step: reproduce the four protocol passes
   on `EMA_50_200` to confirm class-wide exhaustion (delegable once a worker channel is back).
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
