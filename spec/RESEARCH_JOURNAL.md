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
| `EMA_50_200` | **FREEZE** | yes (own trades) | every licensed axis closed on own trades, last was liquidity FALSIFIED (a)+(c)+(d) at `48aef9f` (gated +66.5789284, −6.0903831/series, SL drop 1.165173pp, floor still 7/12); not a class closure; not REJECT | `strategy_profiles/EMA_50_200.md` |
| `EMA3_13_50_200` | **CONDITIONAL** | partial (class levers + own-trades entry-vol FALSIFIED (a)+(c) at `46e4509`; (d) not reachable) | abs-ATR closed on own trades; sizing still open; next `H-EMA3-13-50-200-XSYM-AGREE-SIZING-01` on reproduced baseline +91.1483016; do not FREEZE | `strategy_profiles/EMA3_13_50_200.md` |
| `BB_20_2_EMA200` | **FREEZE** | yes (own trades) | every licensed axis closed on own trades, last was liquidity FALSIFIED (c) at `776e167` (+1.923800/series, SL share +0.084856pp, floor 7/12→6/12); not a class closure | `strategy_profiles/BB_20_2_EMA200.md` |
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

**BB_20_2 loop closed.** `BB_20_2_EMA200` is **FREEZE** (2026-10-03 ~16:20 Europe/Warsaw)
after liquidity FALSIFIED (c) at `776e167`. `BB_20_25_EMA200`, `EMA3_21_50_200`,
and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**. Remaining CONDITIONAL catalog5, in
journal priority: `EMA_50_200`, then `EMA3_13_50_200`. Do not treat the
`BB_20_2_EMA200` loop as those names' tests.

**Shared-losing-months CONFIRMED still stands** (H-CATALOG5-SHARED-LOSING-MONTHS-01): Train-1
losing months cluster far above chance across all five catalog5 names (6/12 with at least 4/5 losing
vs 3.70 expected; phi 0.79, Pearson 0.96, Jaccard 0.85) — a common basket regime, not
idiosyncratic failures. This **blocks** section 8 in-class portfolio diversification (precondition
"losses not strongly correlated" fails). Combining catalog5 names would not improve monthly
regularity. However, this diagnostic finding does **not** license class-wide FREEZE — it only
blocks portfolio combination. It is not why `BB_20_2_EMA200` is FREEZE, and it does not license
FREEZE of `EMA_50_200`.

**EMA_50_200 abs-ATR FALSIFIED (a)+(c); name stays CONDITIONAL.**
`H-EMA-50-200-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** at `80e7fa6`
(review PASS `2026-10-03-f006-ema50200-abs-atr-01-review-b2995d9a`).
Control exact from this experiment's artifacts: +72.6693115 / n=330 /
initial_sl 213/330 = 0.6454545454545455 / big-winner PnL 843.7639016181568 /
floor 7/12. Best cell t_2_0 mean +64.4604139; initial_sl drop 6.73pp;
big-winner retained 83.6% (4/5); floor stays 7/12. (a)(c) fire; (b)(e) do
not; (d) unreachable. First closed own-trades axis on this name in this
loop. Do not FREEZE. Do not start `EMA3_13_50_200`. Baseline going forward =
reproduced control **+72.6693115** from `output/f006_ema_50_200_abs_atr_gate/`.
Section 15: `spec/research/F006-coordinator-series-report-ema-50-200-abs-atr-entry-gate.md`.

**EMA_50_200 xsym sizing FALSIFIED (b); name stays CONDITIONAL.**
`H-EMA-50-200-XSYM-AGREE-SIZING-01` is **FALSIFIED (b)** at `48d03b0`
(review PASS `2026-10-03-f006-ema50200-xsym-agree-sizing--f8969a7a`).
Control exact +72.6693115 (max abs diff 0.0). Sized mean +126.744211
(delta +54.0748995/series). Floor stayed 7/12. Mult gap +0.132984.
Stake_cv 0.413344. n=330 invariant. (a)(c)(d)(e) did not fire. The card's
(b) says a non-improving floor falsifies and decision_if_fail closes the
formula. BB_20_2 Train-1 was REFINE because its floor moved 7/12 to 6/12;
that precedent does not apply. No Val-1. Do not FREEZE. Do not start
`EMA3_13_50_200`. Baseline stays reproduced control **+72.6693115**.
Section 15: `spec/research/F006-coordinator-series-report-ema-50-200-xsym-agree-sizing.md`.

**EMA_50_200 candle confirm FALSIFIED (a)+(c); name stays CONDITIONAL.**
`H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01` is **FALSIFIED (a)+(c)** at `778f373`
(review PASS `2026-10-03-f006-ema50200-entry-candle-confi-ec9e0935`).
Control exact +72.6693115 (max abs diff 0.0), n=330, initial_sl 213/330 =
0.6454545454545455, floor 7/12, big winners 5 / +843.7639016181568. Best
T=0.50 mean +45.0267104 (delta −27.6426011/series). Initial_sl share rose
2.9672358098754015 pp to 133/197. Every T lowers the mean. (b)(d)(e) did
not fire. Do not FREEZE. Do not start `EMA3_13_50_200`. Baseline stays
reproduced control **+72.6693115**. Section 15:
`spec/research/F006-coordinator-series-report-ema-50-200-entry-candle-confirm.md`.

**Next = `H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01`** (pre-registered;
ticket `spec/features/active/F006-ema50200-entry-breakout-depth-01/ticket.md`).
One §8 breakout-depth entry gate on this name's own Train-1 trades.
Depth = directional (close vs ema200) / ema200. D grid
`{0.02, 0.05, 0.10, 0.25, 0.50}` is the licensed shape, not another name's
measured depth means and not a copied winning D. Control must reproduce
+72.6693115 / n=330 / initial_sl 213/330 / floor 7/12 / big-winner 5 /
+843.7639016181568. `number_of_trials = 5`. Not a candle retune. Not an
abs-ATR retune. Not a Val-1 of the closed stake. Not `EMA3_13_50_200`.
Not holdout. Not FREEZE in this commit. If this gate later fails,
decision_if_fail keeps CONDITIONAL and names HTF direction as the following
open axis.

**EMA_50_200 HTF direction FALSIFIED (a)+(b)+(c)+(d); name stays CONDITIONAL.**
`H-EMA-50-200-ENTRY-HTF-DIRECTION-01` is **FALSIFIED (a)+(b)+(c)+(d)** at `3a7c094`
(review PASS `2026-10-03-f006-ema50200-entry-htf-directio-1f19b4cb`).
Control exact +72.6693115 (max abs diff 0.0), n=330, initial_sl 213/330 =
0.6454545454545455, floor 7/12, big winners 5 / +843.7639016181568. Gated
htf_4 mean +20.7369913 (delta −51.9323202/series), n=239, initial_sl share
rose 2.818562190947127 pp (161/239), big-winner PnL kept 44.0%
(3 / +371.1233324523375), floor stayed 7/12. The card's (d) sentence
("pooled losing-month floor does not improve (stays >= baseline floor)")
fires. (e) did not. Do not FREEZE. Do not start `EMA3_13_50_200`. Do not
open a validation window. Baseline stays reproduced control **+72.6693115**.
Section 15: `spec/research/F006-coordinator-series-report-ema-50-200-entry-htf-direction.md`.

**Next = `H-EMA-50-200-ENTRY-LIQUIDITY-01`** (pre-registered;
ticket `spec/features/active/F006-ema50200-entry-liquidity-01/ticket.md`).
One §8 liquidity entry gate on this name's own Train-1 trades. Keep a
one-shot signal iff the signal bar's base volume is at least the median of
the prior 20 closed bars (signal bar excluded). Not `vol_ratio > 1.2`.
The 20-bar median is the licensed shape, not another name's measured
liquidity cell and not a copied pass/fail. Control must reproduce
+72.6693115 / n=330 / initial_sl 213/330 / floor 7/12 / big-winner 5 /
+843.7639016181568. `number_of_trials = 1`. Not an HTF retune. Not a depth
retune. Not a candle retune. Not an abs-ATR retune. Not a Val-1 of the
closed stake. Not `EMA3_13_50_200`. Not holdout. Not FREEZE in this commit.
Liquidity is the last licensed axis. If that gate is later falsified on
this name's own trades, §4 level C allows FREEZE only at that Decision
(ungated book stays aggregate-positive; not REJECT).

**EMA_50_200 liquidity FALSIFIED (a)+(c)+(d); name is FREEZE.**
`H-EMA-50-200-ENTRY-LIQUIDITY-01` is **FALSIFIED (a)+(c)+(d)** at `48aef9f`
(review PASS `2026-10-03-f006-ema50200-entry-liquidity-re-1cb84b84`).
Control exact +72.6693115 (max abs diff 0.0), n=330, initial_sl 213/330 =
0.6454545454545455, floor 7/12, big winners 5 / +843.7639016181568. Gated
liq_med20 mean +66.5789284 (delta −6.0903831/series), n=213, initial_sl
share fell 1.1651728553137009 pp (135/213 = 0.6338028169014085), big-winner
PnL kept 100% (5 / +843.7639016181568), floor stayed 7/12. Applied
sentences: "(a) mean train1_net_pnl <= baseline"; "(c) initial_sl share
fails to fall >=10pp"; "(d) pooled losing-month floor does not improve
(stays >= baseline floor)". (b) and (e) did not fire (21.3 trades/series).
Every licensed axis on this name is now closed on its own trades. Status
**FREEZE**. Not REJECT: ungated Train-1 stays aggregate-positive. Not a
class closure and not evidence for `EMA3_13_50_200`. Section 15:
`spec/research/F006-coordinator-series-report-ema-50-200-entry-liquidity.md`.

**Next = `H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-abs-atr-01/ticket.md`).
One §8 abs-ATR entry gate on `EMA3_13_50_200` own Train-1 trades, the first
still-open licensed axis on that profile. `atr_pct <= T` with T in {this
name's Train-1 entry median, 1.0%, 1.25%, 1.5%, 2.0%}. Control must
reproduce catalog5 mean **+91.1483016** (sum +911.483016) from
`output/f006_notrail_monthly_catalog5/summary/results.csv`. Autopsy
observation, not the test: n=423, initial_sl 292/423, entry net
+771.2836172145888236, big winners 9 / +1131.95615373334168, floor
observation 7/12. Do not copy +72.6693115, +95.3217987, or +82.900262.
`number_of_trials = 5`. Not a liquidity retune. Not funding-carry. Not
spread-capture. Not catalog mean-reversion. Not holdout. Not FREEZE in
this commit. `EMA3_13_50_200` stays CONDITIONAL.


**EMA3_13_50_200 abs-ATR FALSIFIED (a)+(c); name stays CONDITIONAL.**
`H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** at `46e4509`
(review PASS `2026-10-03-f006-ema31350200-abs-atr-01-revi-850be7e5`).
Control exact +91.1483016 (max abs diff 0.0), n=423, initial_sl 292/423,
floor 7/12, big winners 9 / +1131.9561537333418. Best t_2_0 mean +83.4087526
(delta −7.739549/series), n=337, initial_sl drop 4.04557 pp, big-winner PnL
kept 85.1%. (a) and (c) fired. (b) and (e) did not. (d) is not reachable:
no T passes (a)–(c); the flat 7/12 floor is informational only. Do not write
(d) into the label. Do not FREEZE. This is the first closed own-trades axis
on this name in this loop. Not evidence for other names. Baseline going
forward = reproduced control **+91.1483016**. Section 15:
`spec/research/F006-coordinator-series-report-ema3-13-50-200-abs-atr-entry-gate.md`.

**Next = `H-EMA3-13-50-200-XSYM-AGREE-SIZING-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-xsym-agree-sizing-01/ticket.md`).
One §8 position-sizing change on `EMA3_13_50_200` own Train-1 trades.
`mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)` on this name's persistent
signal. `number_of_trials = 1`. Control must reproduce **+91.1483016**.
Do not copy +72.6693115 or +126.744211. A non-improving floor falsifies (b)
on that card and closes the formula with no validation window. If it fails,
decision_if_fail stays CONDITIONAL and names candle confirm. Not an abs-ATR
retune. Not funding-carry. Not spread-capture. Not catalog mean-reversion.
Not holdout. Not FREEZE in this commit.

> **Infra note (2026-10-02):** both worker channels were down when breadth-regime ran — codex quota
> exhausted, `claude-bridge` provider `not_ready`. That fallback is historical. This next
> experiment is delegated (section 16), engine claude, not spark.

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

## §15 Coordinator report (updated 2026-10-03 ~15:41 Europe/Warsaw, BB_20_2 HTF direction closed)

This run: `spec/research/F006-coordinator-series-report-bb-20-2-entry-htf-direction.md`.
Prior series: `spec/research/F006-coordinator-series-report-bb-20-2-entry-breakout-depth.md`.
`BB_20_25_EMA200` stays **FREEZE** on its own loop and is not a class closure.

`H-BB-20-2-ENTRY-HTF-DIRECTION-01` is **FALSIFIED (a)+(c)+(d)** at `dd86dd0`.
Decision = close HTF direction; stay **CONDITIONAL**. Do not FREEZE.
Do not retune the 4-bar length. Next is pre-registered `H-BB-20-2-ENTRY-LIQUIDITY-01`.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `BB_20_2_EMA200`, then `EMA_50_200`, then `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. Entry-vol, the xsym-agree formula, candle close-strength, breakout depth, and HTF direction are closed here. Liquidity remains open and is the last named axis. Screen is this name's (+95.3217987), not a BB_20_25 transfer.
3. **Edge from many trades or few big wins?** Few big wins. Frozen big-winner set is 12 trades / 1251.654084307187. `htf_4` kept 9/12 (1038.6112330239332, 83.0%) and still lost −19.4602092/series.
4. **Earns when?** `signal_reverse` runners. The prior closed 4-bar HTF candle did not identify them: the stop-out share rose.
5. **Loses when?** Most trades still die at the fixed `initial_sl` (50.15% gated, from 47.35%). The pooled floor worsens 7/12 → 8/12. 2025-01 flips from a small gain to a loss.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `f7ac677`. Xsym-agree formula **FALSIFIED (c)** on Val-4 `139ed3d`. Candle close-strength **FALSIFIED (c)** `88b0ee3`. Breakout depth **FALSIFIED (a)+(c)** `27fa7f6`. HTF direction **FALSIFIED (a)+(c)+(d)** `dd86dd0`. Exit, long-only, breadth closed. BB_20_25 closures do not transfer.
7. **Unresolved problem?** Whether signal-bar base volume versus the prior-20 median separates stop-outs from runners on this name. Monthly regularity unsolved. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-BB-20-2-ENTRY-LIQUIDITY-01`. Profile order after HTF is liquidity, and nothing else is named. One change, Train-1, this name's control. Not FREEZE. Not holdout. Not an HTF retune. Not `vol_ratio > 1.2`.
9. **Why not a random search?** §7 develop-not-abandon while the named liquidity axis remains on this name. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Do not reopen closed axes. Do not copy BB_20_25 HTF numbers (`3495b16`). Liquidity was an unlicensed example on that FREEZE profile; it is a named axis here.
10. **What result confirms/refutes the next hypothesis?** On the liquidity card. Control must reproduce +95.3217987, n=756, initial_sl 0.47354497354497355, big-winner 1251.654084307187, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it. Binary gate, `number_of_trials = 1`. A falsification on this name's own trades would allow §4 level C FREEZE at that Decision; this commit does not set it.

## Chronological log

- **2026-10-03 ~15:41 Europe/Warsaw** — **H-BB-20-2-ENTRY-HTF-DIRECTION-01 = FALSIFIED (a)+(c)+(d)**.
  Tip `dd86dd0` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb202-entry-htf-direction-r-911650ed`. Control +95.3217987 /
  n=756 / initial_sl 0.47354497354497355 (358/756) / big-winner PnL
  1251.654084307187 / floor 7/12 reproduced. Gated `htf_4` mean +75.8615895
  (−19.4602092/series), initial_sl share rose +2.790851pp to
  0.501453488372093 (345/688), frozen big-winner PnL retained 83.0% (9/12),
  floor 7/12 → 8/12, 68.8 trades/series. Decision = **FALSIFIED (a)+(c)+(d)**.
  `BB_20_2_EMA200` stays **CONDITIONAL**. Do not FREEZE. HTF direction is
  closed on this name's own trades; liquidity is not. Not a copy of
  `3495b16`. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-entry-htf-direction.md`.

- **2026-10-03 ~15:41 Europe/Warsaw** — **H-BB-20-2-ENTRY-LIQUIDITY-01 pre-registered**
  (§8 liquidity on CONDITIONAL `BB_20_2_EMA200` own trades; signal-bar base
  volume ≥ median of the prior 20 closed bars; Train-1 only; binary gate;
  control mean +95.3217987, n=756). Not an HTF retune, not abs-ATR, not a
  Val-5 of the closed xsym formula, not long-only, not `vol_ratio > 1.2`,
  not the `BB_20_25_EMA200` HTF cell at `3495b16`. Last named open axis.
  Do not FREEZE in this commit. Ticket
  `spec/features/active/F006-bb202-entry-liquidity-01/ticket.md`.

- **2026-10-03 ~15:08 Europe/Warsaw** — **H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01 = FALSIFIED (a)+(c)**.
  Tip `27fa7f6` FF-merged to `origin/main`. Review PASS
  `2026-10-03-f006-bb202-entry-breakout-depth--14238167`. Control +95.3217987 /
  n=756 / initial_sl 0.473545 (358/756) / big-winner PnL 1251.654084 / floor
  7/12 reproduced. Best D=0.02 mean +87.8448967 (−7.476902/series), initial_sl
  share rose +1.010625pp to 0.483651 (355/734), frozen big-winner PnL retained
  82.2% (9/12), floor 6/12 not otherwise qualifying, 73.4 trades/series.
  Decision = **FALSIFIED (a)+(c)**. `BB_20_2_EMA200` stays **CONDITIONAL**.
  Do not FREEZE. Breakout depth is closed on this name's own trades; HTF
  direction and liquidity are not. Not a copy of `0685ce5`. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-entry-breakout-depth.md`.

- **2026-10-03 ~15:08 Europe/Warsaw** — **H-BB-20-2-ENTRY-HTF-DIRECTION-01 pre-registered**
  (§8 HTF direction on CONDITIONAL `BB_20_2_EMA200` own trades; prior fully
  closed 4-bar HTF candle must agree; Train-1 only; binary gate;
  control mean +95.3217987, n=756). Not a depth retune, not abs-ATR, not a
  Val-5 of the closed xsym formula, not long-only, not liquidity, not the
  `BB_20_25_EMA200` HTF cell at `3495b16`. Liquidity stays open. Do not
  FREEZE. Ticket
  `spec/features/active/F006-bb202-entry-htf-direction-01/ticket.md`.

- **2026-10-03 ~14:36 Europe/Warsaw** — **H-BB-20-2-ENTRY-CANDLE-CONFIRM-01 = FALSIFIED (c)**.
  Tip `88b0ee3` FF-merged to `origin/main` from `89326fc`. Review PASS
  `2026-10-03-f006-bb202-entry-candle-confirm--2b310688`. Control +95.3217987 /
  n=756 / initial_sl 0.473545 / big-winner PnL 1251.654084 / floor 7/12
  reproduced. Best T=0.60 mean +95.771777 (+$0.449978/series), initial_sl
  drop 0.548942pp (required ≥10pp), big-winner PnL retained 100%, floor
  stays 7/12, 72.0 trades/series. Decision = **FALSIFIED (c)**.
  `BB_20_2_EMA200` stays **CONDITIONAL**. Do not FREEZE. Candle close-strength
  is closed on this name's own trades; breakout depth, HTF direction, and
  liquidity are not. Not a copy of `e70161d`. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-entry-candle-confirm.md`.

- **2026-10-03 ~14:36 Europe/Warsaw** — **H-BB-20-2-ENTRY-BREAKOUT-DEPTH-01 pre-registered**
  (§8 breakout depth on CONDITIONAL `BB_20_2_EMA200` own trades; D∈
  {0.02, 0.05, 0.10, 0.25, 0.50} as a fraction of `bb_20_2.0` width; Train-1
  only; control mean +95.3217987). Not a candle retune, not abs-ATR, not a
  Val-5 of the closed xsym formula, not HTF, not `bb_20_2.5`. HTF direction
  and liquidity stay open. Do not FREEZE. Ticket
  `spec/features/active/F006-bb202-entry-breakout-depth-01/ticket.md`.

- **2026-10-03 ~14:05 Europe/Warsaw** — **`H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01` Decision FALSIFIED (c)** at `139ed3d` (gate PASS; mean +12.32→+16.22; months 2≤2; gap −0.102941). Formula closed. Stay CONDITIONAL. Do not FREEZE. Pre-registered `H-BB-20-2-ENTRY-CANDLE-CONFIRM-01`. §15 series report written.

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

- **2026-10-03 ~16:20 Europe/Warsaw** — **H-BB-20-2-ENTRY-LIQUIDITY-01 = FALSIFIED (c)**.
  Tip `776e167` FF-merged to `origin/main` (parent `df38f08`). Review PASS
  `2026-10-03-f006-bb202-entry-liquidity-revie-ac02a80e`. Control +95.3217987 / n=756 /
  initial_sl 0.47354497354497355 (358/756) / floor 7/12 reproduced. Gated liq_med20
  mean +97.2455987 (+1.923800/series); initial_sl share rose +0.084856pp to
  0.4743935309973046 (352/742); big-winner PnL retained 100% (12/12); floor 7/12 to 6/12;
  74.2 trades/series. (a)(b)(d)(e) did not fire. (c) fired. Decision = **FALSIFIED (c)**.
  Every licensed axis on `BB_20_2_EMA200` now has an own-trades citation, so the
  profile is **FREEZE** (not REJECT; ungated book still aggregate-positive). Not a
  class closure. Not evidence for other names. §15:
  `spec/research/F006-coordinator-series-report-bb-20-2-entry-liquidity.md`.

- **2026-10-03 ~16:20 Europe/Warsaw** — **H-EMA-50-200-ABS-ATR-ENTRY-GATE-01 pre-registered**
  (entry-vol / abs-ATR on CONDITIONAL `EMA_50_200` own trades; T = this name's
  median plus 1.0/1.25/1.5/2.0%; Train-1 only; control mean +72.6693115 from
  this name's catalog5 rows, sum +726.693115). Not a transfer of `f7ac677`,
  `3788f11`, +95.3217987, or +82.900262. Exit on this name stays closed.
  Do not FREEZE. Do not start `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-abs-atr-01/ticket.md`.

- **2026-10-03 ~16:47 Europe/Warsaw** — **H-EMA-50-200-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)+(c)**.
  Tip `80e7fa6` FF-merged to `origin/main` (parent `5fdd5a8`). Review PASS
  `2026-10-03-f006-ema50200-abs-atr-01-review-b2995d9a`. Control +72.6693115 / n=330 /
  initial_sl 213/330 (64.55%) / floor 7/12 / big-winner 5 / +843.7639016181568
  reproduced from `output/f006_ema_50_200_abs_atr_gate/`. Best t_2_0 mean
  +64.4604139; initial_sl drop 6.73pp; big-winner retained 83.6%; floor 7/12.
  (a)(c) fired; (b)(e) did not; (d) unreachable. Decision = **FALSIFIED (a)+(c)**.
  Profile stays **CONDITIONAL** (first closed own-trades axis on this name;
  sizing and other entry structure still open). Do not FREEZE. Not evidence
  for other names. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-abs-atr-entry-gate.md`.

- **2026-10-03 ~16:47 Europe/Warsaw** — **H-EMA-50-200-XSYM-AGREE-SIZING-01 pre-registered**
  (position sizing on CONDITIONAL `EMA_50_200` own trades; one formula
  `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`; Train-1 only; control mean
  +72.6693115 from this name's reproduced abs-ATR / catalog5 baseline). Not a
  transfer of `1774a8a`, `139ed3d`, `1c9ff7e`, or `89e936a`. Entry-vol on this
  name stays closed. Do not FREEZE. Do not start `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-xsym-agree-sizing-01/ticket.md`.

- **2026-10-03 ~17:25 Europe/Warsaw** — **H-EMA-50-200-XSYM-AGREE-SIZING-01 = FALSIFIED (b)**.
  Tip `48d03b0` FF-merged to `origin/main` (parent `5af9b88`). Review PASS
  `2026-10-03-f006-ema50200-xsym-agree-sizing--f8969a7a`. Control +72.6693115 /
  n=330 / floor 7/12 reproduced from `output/f006_ema_50_200_xsym_agree_sizing/`.
  Sized mean +126.744211 (delta +54.0748995/series); floor stayed 7/12; mult gap
  +0.132984; stake_cv 0.413344. (b) fired; (a)(c)(d)(e) did not. Decision =
  **FALSIFIED (b)**. Profile stays **CONDITIONAL**. The formula is closed. Not
  a Val window (card opens validation only if the sized arm passes; BB_20_2
  Train-1 REFINE was a floor improvement 7/12 to 6/12). Do not FREEZE. Not
  evidence for other names. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-xsym-agree-sizing.md`.

- **2026-10-03 ~17:25 Europe/Warsaw** — **H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 pre-registered**
  (candle confirm on CONDITIONAL `EMA_50_200` own trades; T grid
  {0.50, 0.60, 0.70, 0.80, 0.90}; Train-1 only; control mean +72.6693115 from
  this name's reproduced baseline). Not a transfer of `88b0ee3` or `e70161d`.
  Entry-vol and the xsym formula on this name stay closed. Do not FREEZE.
  Do not start `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-entry-candle-confirm-01/ticket.md`.


- **2026-10-03 ~17:58 Europe/Warsaw** — **H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01 = FALSIFIED (a)+(c)**.
  Tip `778f373` FF-merged to `origin/main` (parent `5321033`). Review PASS
  `2026-10-03-f006-ema50200-entry-candle-confi-ec9e0935`. Control +72.6693115 /
  n=330 / initial_sl 213/330 = 0.6454545454545455 / floor 7/12 / big-winner
  5 / +843.7639016181568 reproduced from
  `output/f006_ema_50_200_entry_candle_confirm/`. Best T=0.50 mean +45.0267104
  (delta −27.6426011/series); initial_sl share rose 2.9672358098754015 pp to
  133/197; floor 8/12 at that T. (a)(c) fired; (b)(d)(e) did not. Decision =
  **FALSIFIED (a)+(c)**. Profile stays **CONDITIONAL**. Candle confirm is
  closed. Do not FREEZE. Not evidence for other names. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-entry-candle-confirm.md`.

- **2026-10-03 ~17:58 Europe/Warsaw** — **H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 pre-registered**
  (breakout depth on CONDITIONAL `EMA_50_200` own trades; depth = (close vs
  ema200) / ema200; D grid {0.02, 0.05, 0.10, 0.25, 0.50}; Train-1 only;
  control mean +72.6693115 from this name's reproduced baseline). Not a
  transfer of BB_20_2 or BB_20_25 depth cells. Candle confirm, entry-vol, and
  the xsym formula on this name stay closed. Do not FREEZE. Do not start
  `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-entry-breakout-depth-01/ticket.md`.

- **2026-10-03 ~18:26 Europe/Warsaw** — **H-EMA-50-200-ENTRY-BREAKOUT-DEPTH-01 = FALSIFIED (a)+(c)**.
  Tip `485de51` FF-merged to `origin/main` (git parent `a243176`; prior Decision `4e32994`). Review PASS
  `2026-10-03-f006-ema50200-entry-breakout-dep-00ab01c3`. Control +72.6693115 /
  n=330 / initial_sl 213/330 = 0.6454545454545455 / floor 7/12 / big-winner
  5 / +843.7639016181568 reproduced from
  `output/f006_ema_50_200_entry_breakout_depth/`. Best D=0.02 mean +63.0343180
  (delta −9.6349935/series); initial_sl share rose 9.600886917960082 pp to
  152/205; floor 8/12 at that D. D=0.25 and D=0.50 took zero trades (vacuous).
  (a)(c) fired; (b)(e) did not; (d) vacuous. Decision =
  **FALSIFIED (a)+(c)**. Profile stays **CONDITIONAL**. Breakout depth is
  closed. Do not FREEZE. Not evidence for other names. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-entry-breakout-depth.md`.

- **2026-10-03 ~18:26 Europe/Warsaw** — **H-EMA-50-200-ENTRY-HTF-DIRECTION-01 pre-registered**
  (HTF direction on CONDITIONAL `EMA_50_200` own trades; prior fully closed
  4-bar HTF candle must agree; Train-1 only; one gated cell;
  `number_of_trials = 1`; control mean +72.6693115 / n=330 from this name's
  reproduced baseline). Not a transfer of another name's HTF mean or
  pass/fail. Breakout depth, candle confirm, entry-vol, and the xsym formula
  on this name stay closed. Liquidity stays open after this axis. FREEZE is
  allowed only at that later liquidity experiment's own Decision, not now.
  Do not start `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-entry-htf-direction-01/ticket.md`.

- **2026-10-03 ~18:56 Europe/Warsaw** — **H-EMA-50-200-ENTRY-HTF-DIRECTION-01 = FALSIFIED (a)+(b)+(c)+(d)**.
  Tip `3a7c094` FF-merged to `origin/main` (git parent `54706a6`; prior Decision `925eee1`). Review PASS
  `2026-10-03-f006-ema50200-entry-htf-directio-1f19b4cb`. Control +72.6693115 /
  n=330 / initial_sl 213/330 = 0.6454545454545455 / floor 7/12 / big-winner
  5 / +843.7639016181568 reproduced from
  `output/f006_ema_50_200_entry_htf_direction/`. Gated htf_4 mean +20.7369913
  (delta −51.9323202/series); initial_sl share rose 2.818562190947127 pp to
  161/239; big-winner PnL kept 44.0% (3 / +371.1233324523375); floor stayed
  7/12. (a)(b)(c)(d) fired; (e) did not. The (d) sentence is "pooled
  losing-month floor does not improve (stays >= baseline floor)". Decision =
  **FALSIFIED (a)+(b)+(c)+(d)**. Profile stays **CONDITIONAL**. HTF direction
  is closed. Do not FREEZE. Not a validation window. Not evidence for other
  names. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-entry-htf-direction.md`.

- **2026-10-03 ~18:56 Europe/Warsaw** — **H-EMA-50-200-ENTRY-LIQUIDITY-01 pre-registered**
  (liquidity on CONDITIONAL `EMA_50_200` own trades; keep a one-shot signal
  iff signal-bar base volume >= median of the prior 20 closed bars, signal
  bar excluded; Train-1 only; one gated cell; `number_of_trials = 1`;
  control mean +72.6693115 / n=330 from this name's reproduced baseline).
  Not `vol_ratio > 1.2`. Not a transfer of `776e167` or of another name's
  liquidity mean or pass/fail. HTF direction, breakout depth, candle
  confirm, entry-vol, and the xsym formula on this name stay closed.
  Liquidity is the last licensed axis. FREEZE is allowed only at that
  experiment's own Decision, not now. Do not start `EMA3_13_50_200`. Ticket
  `spec/features/active/F006-ema50200-entry-liquidity-01/ticket.md`.

- **2026-10-03 ~19:38 Europe/Warsaw** — **H-EMA-50-200-ENTRY-LIQUIDITY-01 = FALSIFIED (a)+(c)+(d)**.
  Tip `48aef9f` FF-merged to `origin/main` (git parent `4f98274`; harness
  `57689fd`). Review PASS
  `2026-10-03-f006-ema50200-entry-liquidity-re-1cb84b84`. Control +72.6693115 /
  n=330 / initial_sl 213/330 = 0.6454545454545455 / floor 7/12 / big-winner
  5 / +843.7639016181568 reproduced from
  `output/f006_ema_50_200_entry_liquidity/`. Gated liq_med20 mean +66.5789284
  (delta −6.0903831/series); initial_sl share fell 1.1651728553137009 pp to
  135/213; big-winner PnL kept 100% (5 / +843.7639016181568); floor stayed
  7/12. (a)(c)(d) fired; (b)(e) did not. Decision = **FALSIFIED (a)+(c)+(d)**.
  Profile **FREEZE**. Not REJECT. Not a class closure. Not evidence for
  `EMA3_13_50_200`. §15:
  `spec/research/F006-coordinator-series-report-ema-50-200-entry-liquidity.md`.

- **2026-10-03 ~19:38 Europe/Warsaw** — **H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 pre-registered**
  (entry-vol / abs-ATR on CONDITIONAL `EMA3_13_50_200` own trades; `atr_pct
  <= T`; T = this name's Train-1 entry median plus 1.0/1.25/1.5/2.0%;
  Train-1 only; `number_of_trials = 5`; control mean +91.1483016 / sum
  +911.483016 from this name's catalog5 rows). Not a transfer of +72.6693115
  or +95.3217987. Not a transfer of the `EMA_50_200` FREEZE. Sizing and other
  entry structure stay open after this axis. Do not FREEZE in this commit.
  Ticket `spec/features/active/F006-ema31350200-abs-atr-01/ticket.md`.

- **2026-10-03 ~20:10 Europe/Warsaw** — **H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01 = FALSIFIED (a)+(c)**.
  Tip `46e4509` FF-merged to `origin/main` (parent `d74c5dd`). Review PASS
  `2026-10-03-f006-ema31350200-abs-atr-01-revi-850be7e5`. Control +91.1483016 /
  n=423 / initial_sl 292/423 / floor 7/12 / big-winner 9 / +1131.9561537333418
  reproduced from `output/f006_ema3_13_50_200_abs_atr_gate/`. Best t_2_0 mean
  +83.4087526 (delta −7.739549/series); initial_sl drop 4.04557 pp; big-winner
  PnL kept 85.1%; floor stayed 7/12. (a)(c) fired; (b)(e) did not; (d) not
  reachable. Decision = **FALSIFIED (a)+(c)**. Profile stays **CONDITIONAL**.
  Do not FREEZE. Not evidence for other names. §15:
  `spec/research/F006-coordinator-series-report-ema3-13-50-200-abs-atr-entry-gate.md`.

- **2026-10-03 ~20:10 Europe/Warsaw** — **H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 pre-registered**
  (position sizing on CONDITIONAL `EMA3_13_50_200` own trades; structural
  `clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`; Train-1 only; `number_of_trials = 1`;
  control mean +91.1483016 from this name's reproduced baseline). Not a
  transfer of +126.744211 or of any BB sizing result. A flat floor falsifies
  (b) and closes the formula with no Val window. Entry-vol on this name stays
  closed. If sizing fails, candle confirm is next and the name stays
  CONDITIONAL. Do not FREEZE. Ticket
  `spec/features/active/F006-ema31350200-xsym-agree-sizing-01/ticket.md`.
