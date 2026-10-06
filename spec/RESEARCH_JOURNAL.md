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
| `EMA3_13_50_200` | **FREEZE** | yes (own trades) | every licensed axis closed on own trades, last was liquidity FALSIFIED (a)+(c)+(d) at `3d9d787` (gated +65.550842, −25.5974596/series, SL share rose 2.5289001670028455 pp, big-winner PnL kept 0.787784961973293, floor still 7/12); not a class closure; not REJECT | `strategy_profiles/EMA3_13_50_200.md` |
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

## Next planned step (2026-10-06 — F012 CLOSED NO CANDIDATE; F013 brief NO CANDIDATE)

F012 structural edge is **CLOSED, NO CANDIDATE** (`spec/features/done/F012-structural-edge/outcome.md`).
Keep the two FAIL kinds apart: C01 and C02 are **mechanism-identification FAILs** (data existed). C03 and
R2-A are **PIT-data FAILs** (Gate 0). R2-A gates 1–5 were **not tested** and no outcome was scored, so
neither mechanism is refuted. The identification-only successor brief
`spec/research/F013-structural-edge-identification-brief.md` audited 5 new mechanisms PIT-first
(exchange leveraged tokens, CME margin hikes, Aave collateral cuts, Ethena hedge, R2-B re-evaluated).
Verdict: **NO CANDIDATE**, because the forced quantity has no free PIT history (N1/N3/N5), access is
forbidden by terms (N2), or the trigger is post-flow and in the carry family (N4). Next step = **PO decision
only**. Do not auto-start R2-B/R2-C or any brief candidate, do not buy data, and leave the collectors unchanged.

## Next planned step (superseded 2026-10-06 — was F011 ARCHIVED; §13 new direction)

F011 forced-flow strategy **ARCHIVED** (§9b Decision). All catalog profiles FREEZE; no licensed
open axis remains. Protocol next step: **§13 owner/trader approval of a new research direction**
(record Why existing family insufficient / missing mechanism / reject evidence / budget). Keep
Bybit liq collector running for possible later `H-PRECASCADE-LIQ-01` only — no spawn until
owner names the next family. Do not buy paid liq data now.

## Next planned step (superseded 2026-10-05 — was H-NONCANDLE-SLEEVE-01 OI frozen, spawn T0)

Trader kierunku named Bybit linear open interest as the one source.
Fetched `/v5/market/open-interest` category=linear intervalTime=1h for
BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT into
`data_cache/open_interest/` (not candle cache, not funding). Repo
constants confirmed: WARMUP_START 2024-01-26T00:00:00Z, TRAIN1_END
2025-03-01T00:00:00Z (`scripts/f006_family_runner.py`). Coverage PASS:
9600 hourly rows per symbol from 2024-01-26T00:00:00Z through
2025-02-28T23:00:00Z, gaps=0.

**Card:** `H-NONCANDLE-SLEEVE-01` now has exactly one frozen rule (written
before any result): position for hour t is the opposite sign of the prior
hour's OI change (sign=-1 if OI[t-1]>OI[t-2], +1 if OI[t-1]<OI[t-2],
flat if equal or missing). `number_of_trials = 1`. No threshold, no grid.
Baseline flat cash 0. Costs = existing harness. INVALID unless the OI
series is consumed (not a candle proxy). Falsifiers unchanged: (a) Train-1
mean after costs <= 0; (b) Warsaw exit-month sum of net_pnl over
2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12 <= 0.
`decision_if_fail` closes this sleeve's first mechanism only; does not
unfreeze catalog names or open a catalog portfolio. Do not touch
EMA/BB/Donchian, catalog mean-reversion, spread, funding carry, XS_RS,
ORB, swarm. Note:
`spec/research/F006-hypothesis-noncandle-sleeve.md`. Ticket:
`spec/features/active/F006-noncandle-sleeve-01/ticket.md`.

## Next planned step (superseded 2026-10-04 ~00:35 — was INVALID / no source at 00:27)

Trader kierunku approved one non-candle book. The search found no loadable
source. Candle cache columns are `timestamp, open, high, low, close, volume`
(`scripts/f006_family_runner.py` `load_train1`). Funding
(`scripts/f006_funding_carry.py` `load_funding`) is not one of the four
sources and is already **FALSIFIED (a)+(b)**, mean M -318.858103, Decision
`03d49bd`. `liq_range_eqh.py` and `btc_filter.py` are candle proxies.
`output/f006_shared_losing_months/summary.json` `ge_5_of_5` months match the
owner list: 2024-03, 2024-04, 2024-05, 2024-08, 2024-09, 2024-12 (same as
`ge_4_of_5`; `ge_3_of_5` adds 2025-01 and is not used).

**Card:** `H-NONCANDLE-SLEEVE-01` is **INVALID**. First line: add that
source to the harness, else the test is invalid. No named file, so no
spawn and no data hunt. `number_of_trials = 1` unspent. Baseline flat cash
0. Falsifiers, unfired: (a) Train-1 mean after costs <= 0; (b) sleeve net
after costs summed over those six Warsaw exit months <= 0. `decision_if_fail`
closes this sleeve's first mechanism only after a real run; it does not
unfreeze catalog names and does not open a catalog portfolio. Do not touch
EMA/BB/Donchian filters, catalog mean-reversion, spread capture, funding
carry, XS_RS / ORB / swarm. Note:
`spec/research/F006-hypothesis-noncandle-sleeve.md`. Ticket:
`spec/features/active/F006-noncandle-sleeve-01/ticket.md`.

## Next planned step (superseded 2026-10-04 — was owner direction at 23:51; the approved direction found no source)

Both parked families are closed. Spread-capture stays closed (no sweep;
widest DOGEUSDT inside spread 1.076716 bps < 17). `H-FUNDING-CARRY-01` is
**FALSIFIED (a)+(b)** at `d2c32ba` / manifest restamp `aaa0c85` (review PASS
`2026-10-03-f006-funding-carry-01-review-f57f13bc`). Funding was inside the
harness. Mean M = -318.858103. Flat-cash baseline is 0. Catalog5 names stay
**FREEZE**. Catalog mean-reversion stays closed. Do not start a new family.
Do not write a card. Do not spawn. §7 and §8 do not license an experiment
on one named strategy own trades that is still open. The calendar-green
goal stays the owner goal. **Next step is an owner direction.**

## Next planned step (superseded 2026-10-03 ~23:35 Europe/Warsaw — calendar-green stays; funding-carry was the open card)

The owner kept the calendar-green goal. That returns the two parked
families under their written conditions. It does not reopen a catalog
name and it does not start catalog mean-reversion or an unnamed family.

**Spread-capture is CLOSED. No sweep. No spawn.** Bybit v5 linear top of
book at server time 1791062518420 (2026-10-03 23:21:58.420 Europe/Warsaw)
was one tick on BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, and DOGEUSDT. Widest
inside spread is DOGEUSDT 1.076716 bps (bid 0.09287 / ask 0.09288). The
bar is 10 bps commission + 5 bps half-spread + 2 bps slippage = 17 bps.
1.076716 does not cover 17. Note:
`spec/research/F006-decision-spread-capture-closed.md`.

**Next experiment:** `H-FUNDING-CARRY-01` only. The F006 runner does not
pass `funding_events` (`backtest_engine.run_backtest` default `()`), and
there is no local funding series, so the first line of work is: add
funding to the harness, else the test is invalid. Do not run a carry
backtest that omits funding. One change, Train-1, flat-cash baseline 0,
falsifiers (a) mean (funding_pnl - total_costs) <= 0 and (b) one
funding-sign-reversal Warsaw day wipes the green days.
`number_of_trials = 1`. Card:
`spec/research/F006-hypothesis-funding-carry.md`. Ticket:
`spec/features/active/F006-funding-carry-01/ticket.md`.

## Next planned step (superseded 2026-10-03 — owner gate before the calendar-green answer)

**Every catalog5 name is FREEZE.** `EMA3_13_50_200` is **FREEZE**
after liquidity FALSIFIED (a)+(c)+(d) at `3d9d787` (2026-10-03 ~23:11 Europe/Warsaw). `EMA_50_200`,
`BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, and
`DONCHIAN_55_NO_TRAIL` stay **FREEZE**. No CONDITIONAL catalog name remains,
and none has an open licensed entry axis. Next name is an **owner decision**
(§13 non-correlated data, or a revisit of the calendar-green goal). Do not
invent a catalog name. Do not pre-register funding-carry, spread-capture, or
catalog mean-reversion. Do not start a new family in this commit.

**Shared-losing-months CONFIRMED still stands** (H-CATALOG5-SHARED-LOSING-MONTHS-01): Train-1
losing months cluster far above chance across all five catalog5 names (6/12 with at least 4/5 losing
vs 3.70 expected; phi 0.79, Pearson 0.96, Jaccard 0.85) — a common basket regime, not
idiosyncratic failures. This **blocks** section 8 in-class portfolio diversification (precondition
"losses not strongly correlated" fails). Combining catalog5 names would not improve monthly
regularity. However, this diagnostic finding does **not** license class-wide FREEZE — it only
blocks portfolio combination. It is not why `BB_20_2_EMA200` is FREEZE, and it does not license
FREEZE of `EMA_50_200` or of `EMA3_13_50_200`.

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

**EMA3_13_50_200 xsym sizing FALSIFIED (b); name stays CONDITIONAL.**
`H-EMA3-13-50-200-XSYM-AGREE-SIZING-01` is **FALSIFIED (b)** at `34e2c4a`
(review PASS `2026-10-03-f006-ema31350200-xsym-01-review-197231de`).
Control exact +91.1483016 (max abs diff 0.0), n=423, floor 7/12, big winners
9 / +1131.956154. Sized mean +127.142706 (delta +35.994404/series). Floor
stayed 7/12. Mult gap +0.085755. Stake_cv 0.429331. n invariant. (a)(c)(d)(e)
did not fire. The card's (b) says a non-improving floor falsifies and
decision_if_fail closes the formula. No Val-1. Series higher is **6/10**
(Result text said 7/10; `results.csv` says 6; not part of (b)). Do not
FREEZE. Baseline stays reproduced control **+91.1483016**. Not +126.744211.
Section 15: `spec/research/F006-coordinator-series-report-ema3-13-50-200-xsym-agree-sizing.md`.

**Next = `H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-entry-candle-confirm-01/ticket.md`).
One §8 candle-confirm entry gate on `EMA3_13_50_200` own Train-1 trades.
Close-strength on the closed signal bar. T grid `{0.50, 0.60, 0.70, 0.80, 0.90}`
is the licensed shape, not another name's winning T. Control must reproduce
+91.1483016 / n=423 / initial_sl 292/423 / floor 7/12 / big-winner 9 /
+1131.9561537333418. `number_of_trials = 5`. Not a Val-1 of the closed stake.
Not an abs-ATR retune. Not holdout. Not FREEZE in this commit. If this gate
later fails, decision_if_fail keeps CONDITIONAL and names breakout depth as
the following open axis. Do not start funding-carry, spread-capture, or
catalog mean-reversion.

**EMA3_13_50_200 candle confirm FALSIFIED (a)+(b)+(c); name stays CONDITIONAL.**
`H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01` is **FALSIFIED (a)+(b)+(c)** at `9dbcf0d`
(review PASS `2026-10-03-f006-ema31350200-entry-candle-co-c5a12ffc`).
Control exact +91.1483016 (max abs diff 0.0), n=423, initial_sl 292/423,
floor 7/12, big winners 9 / +1131.9561537333418. Best T=0.50 mean +51.7526015
(delta −39.3957001/series), n=316, initial_sl share rose 2.8047101774545946 pp
to 227/316. Big-winner PnL retained 0.48671028537156213, which removes
51.32897146284379%. Card (b) says every non-thin T removes >50% of baseline
big-winner PnL; that sentence fires. (a) and (c) also fire. (d) is not
reachable. (e) does not fire. Do not FREEZE. Baseline stays reproduced
control **+91.1483016**. Not +45.0267104. Section 15:
`spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-candle-confirm.md`.

**Next = `H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-entry-breakout-depth-01/ticket.md`).
One §8 breakout-depth entry gate on `EMA3_13_50_200` own Train-1 trades.
Depth = directional `(close - ema200) / ema200` on the closed one-shot bar.
D grid `{0.02, 0.05, 0.10, 0.25, 0.50}` is the licensed shape, not another
name's winning D. Control must reproduce +91.1483016 / n=423 / initial_sl
292/423 / floor 7/12 / big-winner 9 / +1131.9561537333418.
`number_of_trials = 5`. Not a candle retune. Not an abs-ATR retune. Not a
Val-1 of the closed stake. Not holdout. Not FREEZE in this commit. If this
gate later fails, decision_if_fail keeps CONDITIONAL and names HTF direction
as the following open axis. Do not start funding-carry, spread-capture, or
catalog mean-reversion.

**EMA3_13_50_200 breakout depth FALSIFIED (c) only; name stays CONDITIONAL.**
`H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01` is **FALSIFIED (c) only** at `c388392`
(review PASS `2026-10-03-f006-ema31350200-entry-breakout--c183b475`).
Control exact +91.1483016 (max abs diff 0.0), n=423, initial_sl 292/423,
floor 7/12, big winners 9 / +1131.9561537333418. Best D=0.02 mean +94.4530527
(delta +3.3047511/series), n=322, initial_sl share rose 7.987900679852578 pp
to 248/322 = 0.7701863354037267. Big-winner PnL retained 0.894213522771771
(6 / +1012.2104998530759), which removes about 10.58%, not >50%. Card (b)
needs every non-thin D to remove >50%; D=0.02 does not, so (b) does not fire.
(a) does not fire (mean rose). (d) is not reachable (no D passes (a)-(c)).
(e) does not fire (32.2 trades/series). Do not FREEZE. Not REJECT. Baseline
stays reproduced control **+91.1483016**. Not +63.0343180. Section 15:
`spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-breakout-depth.md`.

**Next = `H-EMA3-13-50-200-HTF-DIRECTION-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-entry-htf-direction-01/ticket.md`).
One §8 HTF-direction entry gate on `EMA3_13_50_200` own Train-1 trades.
Prior fully closed 4-bar HTF candle must agree. Binary gate.
`number_of_trials = 1`. Control must reproduce +91.1483016 / n=423 / initial_sl
292/423 / floor 7/12 / big-winner 9 / +1131.9561537333418.
Not a depth retune. Not a candle retune. Not an abs-ATR retune. Not a
Val-1 of the closed stake. Not holdout. Not FREEZE in this commit. If this
gate later fails, decision_if_fail keeps CONDITIONAL and names liquidity
as the following open axis. Do not start funding-carry, spread-capture, or
catalog mean-reversion.


**EMA3_13_50_200 HTF direction FALSIFIED (a)+(c)+(d); name stays CONDITIONAL.**
`H-EMA3-13-50-200-HTF-DIRECTION-01` is **FALSIFIED (a)+(c)+(d)** at `c70777a`
(review PASS `2026-10-03-f006-ema31350200-entry-htf-direc-8f002b67`).
Control exact +91.1483016 (max abs diff 0.0), n=423, initial_sl 292/423,
floor 7/12, big winners 9 / +1131.9561537333418. Gated htf_4 mean +39.2303418
(delta −51.9179598/series), n=362, initial_sl share rose 2.792471559369414 pp
to 260/362 = 0.7182320441988951. Big-winner PnL retained 0.5556713331636377
(6 / +628.9955850277897), which removes about 44.43%, not >50%. Card (b)
does not fire. (a) fires (mean fell). (c) fires (share rose). (d) fires:
this card's (d) is the standalone floor sentence ("does not improve (stays
>= baseline floor)"), and the floor stayed 7/12 — unlike the depth card
where (d) was unreachable. (e) does not fire (36.2 trades/series). Do not
FREEZE. Not REJECT. Baseline stays reproduced control **+91.1483016**. Not
+20.7369913. Section 15:
`spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-htf-direction.md`.

**Next = `H-EMA3-13-50-200-ENTRY-LIQUIDITY-01`** (pre-registered;
ticket `spec/features/active/F006-ema31350200-entry-liquidity-01/ticket.md`).
One §8 liquidity entry gate on `EMA3_13_50_200` own Train-1 trades.
Prior-20 median of native base volume. Binary gate.
`number_of_trials = 1`. Control must reproduce +91.1483016 / n=423 / initial_sl
292/423 / floor 7/12 / big-winner 9 / +1131.9561537333418.
Not an HTF retune. Not a depth retune. Not a candle retune. Not an
abs-ATR retune. Not a Val-1 of the closed stake. Not holdout. Not FREEZE
in this commit. Liquidity is the last licensed axis. If it later fails on
this name's own trades and every licensed axis is cited while the ungated
book stays aggregate-positive, FREEZE may be written then at §4 level C
(not REJECT). A passing cell keeps CONDITIONAL. Do not start funding-carry,
spread-capture, or catalog mean-reversion.


**EMA3_13_50_200 liquidity FALSIFIED (a)+(c)+(d); name is FREEZE.**
`H-EMA3-13-50-200-ENTRY-LIQUIDITY-01` is **FALSIFIED (a)+(c)+(d)** at `3d9d787`
(review PASS `2026-10-03-f006-ema31350200-entry-liquidity-9a01df13`).
Control exact +91.1483016 (max abs diff 0.0), n=423, initial_sl 292/423 =
0.6903073286052009, floor 7/12, big winners 9 / +1131.9561537333418. Gated
liq_med20 mean +65.550842 (artifact 65.55084200000002; delta −25.5974596/series),
n=327 (32.7/series), initial_sl share rose 2.5289001670028455 pp
(234/327 = 0.7155963302752294), big-winner PnL kept 0.787784961973293
(6 / +891.7380355242556), floor stayed 7/12. Applied sentences: "(a) mean
train1_net_pnl <= baseline"; "(c) initial_sl share fails to fall >=10pp";
"(d) pooled losing-month floor does not improve (stays >= baseline floor)".
The card also says "A flat floor falsifies (d) on this card", so (d) stays
in the label. (b) and (e) did not fire. Every licensed axis on this name is
now closed on its own trades. Status **FREEZE** (§4 level C). Not REJECT:
ungated Train-1 stays aggregate-positive. Not a class closure. No next
pre-registration: the next name is an owner decision. Section 15:
`spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-liquidity.md`.

> **Infra note (2026-10-02):** both worker channels were down when breadth-regime ran — codex quota
> exhausted, `claude-bridge` provider `not_ready`. That fallback is historical. There is no current ticket and no spawn: the next name is an owner decision. Do not treat this 2026-10-02 note as a live delegation.

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

## §15 Coordinator report (updated 2026-10-04 ~00:27 Europe/Warsaw, non-candle sleeve INVALID)

`H-NONCANDLE-SLEEVE-01` OI source cached and frozen rule written. Spawn T0 to implement the frozen rule only.
The approved direction needs one source the catalog candles do not have.
That source is not in the harness.

1. **Best strategy now?** None promotable. Every catalog5 name and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**.
2. **Why that name?** No catalog name has an open licensed axis. Entry axes are falsified. Both parked families are closed.
3. **Edge from many trades or few big wins?** The frozen breakout book is still a few big wins. This sleeve has no trades.
4. **Earns when?** Not known. There is no non-candle series to condition on.
5. **Loses when?** Catalog book: shared basket regime, the six months in `summary.json` `ge_5_of_5`. Carry: every Warsaw symbol-day. Spread: inside spread 1.076716 bps < 17.
6. **Rejected hypotheses?** Funding-carry **FALSIFIED (a)+(b)** (`03d49bd`, mean M -318.858103). Spread-capture **closed**, no sweep. Catalog mean-reversion stays closed. XS_RS / ORB / swarm stay closed. This sleeve is not rejected; it was not run.
7. **Unresolved problem?** A book that is positive after costs inside those six shared losing months. Section 8 portfolio stays blocked. The missing piece is the source, not another candle filter.
8. **Next experiment & why?** `H-NONCANDLE-SLEEVE-01` T0: implement the frozen OI fade rule on the cached Bybit linear open-interest series. One change. Do not pick a new rule.
9. **Why not a random search?** Section 13 is on the card. Existing families are insufficient for the reasons in that block. Inventing a second family or a candle proxy would not be the approved direction.
10. **What result confirms or refutes it?** Nothing was scored. (a) Train-1 mean after costs <= 0. (b) six-month Warsaw exit-month sum of `net_pnl` <= 0. A run that does not consume the non-candle source is INVALID, not a confirmation.

## §15 archive (2026-10-03 ~23:51 Europe/Warsaw, funding-carry closed)

`H-FUNDING-CARRY-01` is **FALSIFIED (a)+(b)**. Funding-carry is closed.
Spread-capture stays closed. No catalog name was unfrozen. No next card.

1. **Best strategy now?** None promotable. Every catalog5 name and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**.
2. **Why that name?** No catalog name has an open licensed axis. Both parked families are now closed on their written tests.
3. **Edge from many trades or few big wins?** The frozen breakout book is still a few big wins. Funding-carry is not an edge: about +$10 funding per symbol against about 270 to 350 of round-trip costs.
4. **Earns when?** Not on this carry rule. Train-1 funding_pnl is positive and small. The breakout book earns on ungated `signal_reverse` runners.
5. **Loses when?** Carry loses on every one of 1716 Warsaw symbol-days (costs dominate one settlement). Breakout book: shared basket regime, floor still uneven. Spread-capture loses the 17 bps cost bar before any fill.
6. **Rejected hypotheses?** Funding-carry **FALSIFIED (a)+(b)** (`d2c32ba` / `aaa0c85`). Spread-capture **REJECT / closed**, no sweep. Catalog mean-reversion stays aggregate-negative and is not reopened. Catalog axes unchanged.
7. **Unresolved problem?** Calendar-green. Breakout families are frozen, in-class portfolio is blocked, and neither parked family is the mechanism.
8. **Next experiment & why?** None. The next step is an owner direction. Do not invent a family. Do not unfreeze a catalog name. Do not start catalog mean-reversion.
9. **Why not a random search?** §7 and §8 do not license a new experiment. Every catalog name is FREEZE on its own trades. Shared-losing blocks in-class portfolio. §13 is not met by this card: `decision_if_fail` says do not invent another family.
10. **What result confirms or refutes it?** Nothing is pre-registered. This card result is mean M -318.858103 <= 0, and W -1.038216 <= -G with G = 0. Empty funding would have been INVALID; funding was applied.

## §15 archive (2026-10-03 ~23:35 Europe/Warsaw, spread-capture closed; funding-carry pre-registered)

Spread-capture measured and closed with no run. Funding-carry is the one
pre-registered card. No catalog name was unfrozen.

1. **Best strategy now?** None promotable. Every catalog5 name and `DONCHIAN_55_NO_TRAIL` stay **FREEZE**.
2. **Why that name?** No catalog name has an open licensed axis. The owner kept the calendar-green goal, which is the written condition for the two parked families. Spread-capture failed its no-sweep bar.
3. **Edge from many trades or few big wins?** Still the frozen breakout book: few big wins. Spread-capture was not run. Carry is not yet run.
4. **Earns when?** Not known for carry. The breakout book earns on ungated `signal_reverse` runners.
5. **Loses when?** Breakout book: shared basket regime, floor still uneven. Spread-capture loses the cost bar before any fill: inside spread <= 1.076716 bps versus 17 bps.
6. **Rejected hypotheses?** Spread-capture **REJECT / closed**, no sweep, measurement 2026-10-03 23:21:58.420 Europe/Warsaw. Catalog axes unchanged. Catalog mean-reversion stays aggregate-negative and is not reopened.
7. **Unresolved problem?** Calendar-green, with breakout families frozen and in-class portfolio blocked. Spread-capture cannot be the mechanism.
8. **Next experiment & why?** `H-FUNDING-CARRY-01`. It is the remaining parked family. First line: add funding to the harness, else the test is invalid. One rule, Train-1, flat baseline 0.
9. **Why not a random search?** §13 block is on the card. The existing family is insufficient because every licensed axis is closed and the month floor is the shared regime. This is not a new unnamed family and not catalog mean-reversion.
10. **What result confirms or refutes it?** (a) mean of (funding_pnl - total_costs) across the five 60-minute series <= 0 falsifies. (b) one Warsaw funding-sign-reversal day wiping the sum of positive days on that metric falsifies. Empty `funding_events` is INVALID, not a result.

## §15 archive (2026-10-03 ~23:11 Europe/Warsaw, EMA3_13_50_200 liquidity closed; name FREEZE)

This run: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-liquidity.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-htf-direction.md`.

`H-EMA3-13-50-200-ENTRY-LIQUIDITY-01` is **FALSIFIED (a)+(c)+(d)** at `3d9d787`.
Decision = close liquidity and **FREEZE** `EMA3_13_50_200` (§4 level C). Not REJECT.
Do not retune the 20-bar median. No next card.

1. **Best strategy now?** None promotable. Every catalog5 name is **FREEZE**, including `EMA3_13_50_200`. `DONCHIAN_55_NO_TRAIL` stays FREEZE. No CONDITIONAL catalog name remains.
2. **Why that name?** It was the last open name. Its own-trades loop is now closed. Screen is this name's (+91.1483016, n=423, 0/10 clear §7), not an `EMA_50_200` transfer.
3. **Edge from many trades or few big wins?** Few big wins. Control big-winner set is 9 trades / +1131.9561537333418 against entry net +771.2836172145886. Gated liq_med20 kept 6 / +891.7380355242556 (0.787784961973293).
4. **Earns when?** Ungated `signal_reverse` runners. The prior-20 base-volume median did not separate them from stop-outs: liq_med20 cut the mean by −25.5974596/series.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`, and the share rose from 292/423 (0.6903073286052009) to 234/327 (0.7155963302752294), +2.5289001670028455 pp. The pooled floor stays 7/12.
6. **Rejected hypotheses?** Liquidity **FALSIFIED (a)+(c)+(d)** `3d9d787`. (b)(e) did not fire. (d) kept because this card's floor sentence says a flat floor falsifies. Abs-ATR **FALSIFIED (a)+(c)** `46e4509` / Decision `3318658` (not (d)). Xsym **FALSIFIED (b)** `34e2c4a` / Decision `396a3c2`. Candle **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision `079b697`. Breakout depth **FALSIFIED (c) only** `c388392` / Decision `07fb827`. HTF **FALSIFIED (a)+(c)+(d)** `c70777a` / Decision `a99a460`. Exit, long-only, breadth closed. Other names' liquidity closures do not transfer.
7. **Unresolved problem?** Monthly regularity, with no licensed axis left on this name or on any other catalog5 name. In-class portfolio combination stays BLOCKED. The next mechanism is an owner decision.
8. **Next experiment & why?** None. The journal's exhausted-catalog step is an owner decision (§13 or the calendar-green goal). Do not invent a name. Do not pre-register funding-carry, spread-capture, or catalog mean-reversion. Do not start a new family.
9. **Why not a random search?** §13. A new family is not started without the owner's written justification. Catalog mean-reversion is already aggregate-negative on Train-1. Shared-losing blocks in-class portfolio and does not license this FREEZE or a REJECT.
10. **What result confirms/refutes the next hypothesis?** Nothing is pre-registered, so there is no line. Do not import +66.5789284, +72.6693115, +97.2455987, or +95.3217987.

## §15 archive (2026-10-03 ~22:36 Europe/Warsaw, EMA3_13_50_200 HTF direction closed)

This run: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-htf-direction.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-breakout-depth.md`.
`EMA_50_200` stays **FREEZE** on its own loop and is not a class closure.

`H-EMA3-13-50-200-HTF-DIRECTION-01` is **FALSIFIED (a)+(c)+(d)** at `c70777a`.
Decision = close HTF direction; stay **CONDITIONAL**. Do not FREEZE. Not REJECT.
Do not retune the 4-bar length. Next is pre-registered `H-EMA3-13-50-200-ENTRY-LIQUIDITY-01`.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`EMA_50_200`, `BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. Entry-vol, the xsym-agree formula, candle close-strength, breakout depth, and HTF direction are closed here. Liquidity is the last named axis. Screen is this name's (+91.1483016, n=423), not an `EMA_50_200` transfer.
3. **Edge from many trades or few big wins?** Few big wins. Control big-winner set is 9 trades / +1131.9561537333418 against entry net +771.2836172145886. Gated htf_4 kept 6 / +628.9955850277897 (0.5556713331636377).
4. **Earns when?** Ungated `signal_reverse` runners. HTF agreement did not separate them from stop-outs: htf_4 cut the mean by −51.9179598/series and raised the initial_sl share.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`, and the share rose from 292/423 (0.6903073286052009) to 260/362 (0.7182320441988951), +2.792471559369414 pp. The pooled floor stays 7/12.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `46e4509` / Decision `3318658` ((d) not reachable). Xsym-agree formula **FALSIFIED (b)** `34e2c4a` / Decision `396a3c2`. Candle confirm **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision `079b697`. Breakout depth **FALSIFIED (c) only** `c388392` / Decision `07fb827` ((d) not reachable). HTF direction **FALSIFIED (a)+(c)+(d)** `c70777a`. (b)(e) did not fire. (d) kept because this card's floor sentence is standalone. Exit, long-only, breadth closed. Other names' HTF closures do not transfer.
7. **Unresolved problem?** Whether the signal bar itself traded on above-median base volume on this name. Monthly regularity unsolved. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-EMA3-13-50-200-ENTRY-LIQUIDITY-01`. decision_if_fail and the profile name liquidity after a failed HTF gate. One change, Train-1, this name's control. Not FREEZE now. Not holdout. Not another name's measured liquidity mean. FREEZE only at that later Decision if falsified with every licensed axis cited and ungated book aggregate-positive (§4 level C, not REJECT). A pass keeps CONDITIONAL.
9. **Why not a random search?** §7 develop-not-abandon while liquidity remains on this name. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not reopen closed axes.
10. **What result confirms/refutes the next hypothesis?** On the liquidity card. Control must reproduce +91.1483016, n=423, initial_sl 292/423, big-winner 9 / +1131.9561537333418, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it. On that card (d) is the standalone floor sentence. `number_of_trials = 1`.

## §15 archive (2026-10-03 ~22:06 Europe/Warsaw, EMA3_13_50_200 breakout depth closed)


This run: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-breakout-depth.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-candle-confirm.md`.
`EMA_50_200` stays **FREEZE** on its own loop and is not a class closure.

`H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01` is **FALSIFIED (c) only** at `c388392`.
Decision = close breakout depth; stay **CONDITIONAL**. Do not FREEZE. Not REJECT.
Do not retune D. Next is pre-registered `H-EMA3-13-50-200-HTF-DIRECTION-01`.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`EMA_50_200`, `BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. Entry-vol, the xsym-agree formula, candle close-strength, and breakout depth are closed here. HTF direction is the next named axis. Screen is this name's (+91.1483016, n=423), not an `EMA_50_200` transfer.
3. **Edge from many trades or few big wins?** Few big wins. Control big-winner set is 9 trades / +1131.9561537333418 against entry net +771.2836172145886. Best D kept 6 / +1012.2104998530759 (0.894213522771771).
4. **Earns when?** Ungated `signal_reverse` runners. Depth did not separate them from stop-outs: D=0.02 raised the mean by only +3.3047511/series and raised the initial_sl share.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`, and the share rose from 292/423 (0.6903073286052009) to 248/322 (0.7701863354037267), +7.987900679852578 pp. The pooled floor stays 7/12.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `46e4509` / Decision `3318658` ((d) not reachable). Xsym-agree formula **FALSIFIED (b)** `34e2c4a` / Decision `396a3c2`. Candle confirm **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision `079b697`. Breakout depth **FALSIFIED (c) only** `c388392`. (a)(b)(e) did not fire. (d) not reachable. Exit, long-only, breadth closed. Other names' depth closures do not transfer.
7. **Unresolved problem?** Whether the prior closed higher-timeframe candle agrees with the signal on this name. Monthly regularity unsolved. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-EMA3-13-50-200-HTF-DIRECTION-01`. decision_if_fail and the profile name HTF direction after a failed depth gate. One change, Train-1, this name's control. Not FREEZE. Not holdout. Not another name's measured htf_4 mean. Liquidity stays open after this axis.
9. **Why not a random search?** §7 develop-not-abandon while HTF direction, then liquidity, remain on this name. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not reopen closed axes.
10. **What result confirms/refutes the next hypothesis?** On the HTF card. Control must reproduce +91.1483016, n=423, initial_sl 292/423, big-winner 9 / +1131.9561537333418, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it. On that card (d) is the standalone floor sentence. `number_of_trials = 1`.

## §15 archive (2026-10-03 ~21:17 Europe/Warsaw, EMA3_13_50_200 candle confirm closed)

This run: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-candle-confirm.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-ema3-13-50-200-xsym-agree-sizing.md`.
`EMA_50_200` stays **FREEZE** on its own loop and is not a class closure.

`H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01` is **FALSIFIED (a)+(b)+(c)** at `9dbcf0d`.
Decision = close candle confirm; stay **CONDITIONAL**. Do not FREEZE.
Do not retune T. Next is pre-registered `H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01`.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`EMA_50_200`, `BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. Entry-vol, the xsym-agree formula, and candle close-strength are closed here. Breakout depth is the next named axis. Screen is this name's (+91.1483016, n=423), not an `EMA_50_200` transfer.
3. **Edge from many trades or few big wins?** Few big wins. Control big-winner set is 9 trades / +1131.9561537333418 against entry net +771.2836172145886. Best T kept 4 / +550.9347026116507 (48.671%).
4. **Earns when?** Ungated `signal_reverse` runners. Close-strength did not identify them: the best T cut the mean by 39.3957001/series.
5. **Loses when?** Most remaining trades still die at the fixed `initial_sl`, and the share rose from 292/423 (69.03073286052009%) to 227/316 (71.83544303797468%). The pooled floor stays 7/12.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `46e4509` ((d) not reachable). Xsym-agree formula **FALSIFIED (b)** `34e2c4a` (flat floor, no Val). Candle confirm **FALSIFIED (a)+(b)+(c)** `9dbcf0d`. Exit, long-only, breadth closed. Other names' candle closures do not transfer.
7. **Unresolved problem?** Whether distance of the close beyond ema200 separates stop-outs from runners on this name. Monthly regularity unsolved. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01`. decision_if_fail and the profile name breakout depth after a failed candle gate. One change, Train-1, this name's control. Not FREEZE. Not holdout. Not a copied winning D.
9. **Why not a random search?** §7 develop-not-abandon while breakout depth, HTF direction, and liquidity remain on this name. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not reopen closed axes.
10. **What result confirms/refutes the next hypothesis?** On the depth card. Control must reproduce +91.1483016, n=423, initial_sl 292/423, big-winner 9 / +1131.9561537333418, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp at the best-PnL D AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it. On that card (b) is big-winner removal (>50% removed), not a flat floor. `number_of_trials = 5`.

## §15 archive (2026-10-03 ~20:40 Europe/Warsaw, EMA3_13_50_200 xsym sizing closed)

This run: `spec/research/F006-coordinator-series-report-ema3-13-50-200-xsym-agree-sizing.md`.
Prior on this name: `spec/research/F006-coordinator-series-report-ema3-13-50-200-abs-atr-entry-gate.md`.
`EMA_50_200` stays **FREEZE** on its own loop and is not a class closure.

`H-EMA3-13-50-200-XSYM-AGREE-SIZING-01` is **FALSIFIED (b)** at `34e2c4a`.
Decision = close this sizing formula; stay **CONDITIONAL**. Do not FREEZE.
Do not open a validation window. Do not retune 0.5 / 0.375 / 2.0. Next is
pre-registered `H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01`.

1. **Best strategy now?** None promotable. FREEZE names unchanged (`EMA_50_200`, `BB_20_2_EMA200`, `BB_20_25_EMA200`, `EMA3_21_50_200`, `DONCHIAN_55_NO_TRAIL`). Active CONDITIONAL name is `EMA3_13_50_200`.
2. **Why that name?** Own-trades loop in progress. Entry-vol and the xsym-agree formula are closed here. Candle confirm is the next named axis. Screen is this name's (+91.1483016, n=423), not an `EMA_50_200` transfer.
3. **Edge from many trades or few big wins?** Few big wins. Control big-winner set is 9 trades / +1131.956154 against entry net +771.283617. Sizing grew 2024-11 and did not clear a losing month.
4. **Earns when?** Weighted `signal_reverse` runners. Mult gap +0.085755. Mean rose +35.994404/series. 6/10 series are higher (not the Result's 7/10).
5. **Loses when?** The same 7/12 entry-months lose after sizing, six of them by more. SOL240, ETH240, DOGE240, DOGE60 are lower.
6. **Rejected hypotheses?** Entry-vol **FALSIFIED (a)+(c)** `46e4509` ((d) not reachable). Xsym-agree formula **FALSIFIED (b)** `34e2c4a`. Exit, long-only, breadth closed. Other names' closures do not transfer.
7. **Unresolved problem?** Whether signal-bar close location separates stop-outs from runners on this name. Monthly regularity unsolved. In-class portfolio combination stays BLOCKED.
8. **Next experiment & why?** `H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01`. decision_if_fail and the profile name candle confirm after a failed sizing formula. One change, Train-1, this name's control. Not FREEZE. Not holdout. Not a Val-1. Not a copied winning T.
9. **Why not a random search?** §7 develop-not-abandon while candle confirm, breakout depth, HTF direction, and liquidity remain on this name. Do not start funding-carry, spread-capture, or catalog mean-reversion. Do not reopen closed axes.
10. **What result confirms/refutes the next hypothesis?** On the candle card. Control must reproduce +91.1483016, n=423, initial_sl 292/423, big-winner 9 / +1131.956154, floor 7/12. Pass needs mean above control AND initial_sl drop ≥10pp at the best-PnL T AND ≥50% big-winner PnL retained AND floor strictly below 7/12, without collapsing below 10 trades/series. Any of (a)–(e) fails it. On that card (b) is big-winner removal, not a flat floor. `number_of_trials = 5`.


## §15 archive (2026-10-03 ~15:41 Europe/Warsaw, BB_20_2 HTF direction closed)


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

- **2026-10-04 ~00:35 Europe/Warsaw** — **H-NONCANDLE-SLEEVE-01 OI cached + frozen rule**.
  Bybit linear OI 1h for five Train-1 symbols in `data_cache/open_interest/`
  (9600 rows/symbol, gaps=0, WARMUP_START..TRAIN1_END). Frozen rule: opposite
  sign of prior-hour OI change; `number_of_trials = 1`; baseline flat cash 0;
  INVALID unless OI consumed. Spawn T0 (claude). Ticket
  `spec/features/active/F006-noncandle-sleeve-01/ticket.md`.

- **2026-10-04 ~00:27 Europe/Warsaw** — **H-NONCANDLE-SLEEVE-01 pre-registered INVALID**.
  Trader kierunku approved one non-candle book. No order-flow, open-interest,
  liquidation, or non-candle cross-asset series is loadable. Funding stays
  closed (mean M -318.858103, Decision `03d49bd`). Shared-losing months match
  `summary.json` `ge_5_of_5`: 2024-03, 2024-04, 2024-05, 2024-08, 2024-09,
  2024-12. First line: add that source to the harness, else the test is
  invalid. No spawn. `number_of_trials = 1` unspent. Do not unfreeze catalog
  names. Do not open a catalog portfolio. Ticket
  `spec/features/active/F006-noncandle-sleeve-01/ticket.md`.

- **2026-10-03 ~23:51 Europe/Warsaw** — **H-FUNDING-CARRY-01 = FALSIFIED (a)+(b)**.
  Funding was passed into `run_backtest` (1200 events per symbol; 5,416 of
  5,666 trades have non-zero funding_pnl; control flat at 0). Mean M =
  -318.858103. G = 0, W = -1.038216. The 162 exit-bar settlements the
  engine misses under `ts < exit_time` are +2.591955 on Train-1 and cannot
  flip (a) or (b); not INVALID. Family closed. Spread-capture stays closed.
  No next card. Next step is an owner direction. No spawn.

- **2026-10-03 ~22:36 Europe/Warsaw** — **H-EMA3-13-50-200-HTF-DIRECTION-01 = FALSIFIED (a)+(c)+(d)**.
  Tip `c70777a` FF-merged to `origin/main` (parent of this Decision; harness
  `4f02415`).
  Review PASS `2026-10-03-f006-ema31350200-entry-htf-direc-8f002b67`. Control
  +91.1483016 / n=423 / initial_sl 292/423 / floor 7/12 / big winners 9 /
  +1131.9561537333418 reproduced. Gated htf_4 mean +39.2303418
  (−51.9179598/series), initial_sl share rose 2.792471559369414 pp to
  260/362 = 0.7182320441988951, big-winner PnL retained 0.5556713331636377
  (6 / +628.9955850277897; about 44.43% removed; card (b) does not fire).
  (a) fires (mean fell). (c) fires (share rose). (d) fires: this card's
  floor sentence is standalone and the floor stayed 7/12. (e) does not
  fire (36.2 trades/series). Decision = **FALSIFIED (a)+(c)+(d)**. HTF
  axis closed. `EMA3_13_50_200` stays **CONDITIONAL**. Do not FREEZE.
  Not REJECT. Not +20.7369913. §15:
  `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-htf-direction.md`.

- **2026-10-03 ~22:36 Europe/Warsaw** — **H-EMA3-13-50-200-ENTRY-LIQUIDITY-01 pre-registered**
  (§8 liquidity on CONDITIONAL `EMA3_13_50_200` own trades; prior-20
  median of native base volume; binary gate; Train-1 only; control mean
  +91.1483016, n=423). Not an HTF retune, not a depth retune, not a
  candle retune, not an abs-ATR retune, not a Val-1, not funding-carry,
  spread-capture, or catalog mean-reversion. Liquidity is the last
  licensed axis. If it fails, FREEZE may be written at that Decision at
  §4 level C (not REJECT) when every licensed axis is cited and the
  ungated book stays aggregate-positive. A pass keeps CONDITIONAL. Do
  not FREEZE in this commit. Ticket
  `spec/features/active/F006-ema31350200-entry-liquidity-01/ticket.md`.

- **2026-10-03 ~22:06 Europe/Warsaw** — **H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01 = FALSIFIED (c) only**.
  Tip `c388392` FF-merged to `origin/main` (parent of this Decision).
  Review PASS `2026-10-03-f006-ema31350200-entry-breakout--c183b475`. Control
  +91.1483016 / n=423 / initial_sl 292/423 / floor 7/12 / big winners 9 /
  +1131.9561537333418 reproduced. Best D=0.02 mean +94.4530527
  (+3.3047511/series), initial_sl share rose 7.987900679852578 pp to
  248/322 = 0.7701863354037267, big-winner PnL retained 0.894213522771771
  (6 / +1012.2104998530759; about 10.58% removed; card (b) does not fire).
  (a) does not fire (mean rose). (d) not reachable. (e) does not fire
  (32.2 trades/series). Decision = **FALSIFIED (c) only**. Depth axis closed.
  `EMA3_13_50_200` stays **CONDITIONAL**. Do not FREEZE. Not REJECT.
  Not +63.0343180. §15:
  `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-breakout-depth.md`.

- **2026-10-03 ~22:06 Europe/Warsaw** — **H-EMA3-13-50-200-HTF-DIRECTION-01 pre-registered**
  (§8 HTF direction on CONDITIONAL `EMA3_13_50_200` own trades; prior fully
  closed 4-bar HTF candle must agree; binary gate; Train-1 only; control mean
  +91.1483016, n=423). Not a depth retune, not a candle retune, not an
  abs-ATR retune, not a Val-1, not funding-carry, spread-capture, or catalog
  mean-reversion. If it fails, decision_if_fail stays CONDITIONAL and names
  liquidity. Do not FREEZE. Ticket
  `spec/features/active/F006-ema31350200-entry-htf-direction-01/ticket.md`.

- **2026-10-03 ~21:17 Europe/Warsaw** — **H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 = FALSIFIED (a)+(b)+(c)**.
  Tip `9dbcf0d` FF-merged to `origin/main` (parent `8145008`; pre-reg `396a3c2`).
  Review PASS `2026-10-03-f006-ema31350200-entry-candle-co-c5a12ffc`. Control
  +91.1483016 / n=423 / initial_sl 292/423 / floor 7/12 / big winners 9 /
  +1131.9561537333418 reproduced. Best T=0.50 mean +51.7526015
  (−39.3957001/series), initial_sl share rose 2.8047101774545946 pp to
  227/316, big-winner PnL retained 0.48671028537156213 (51.32897146284379%
  removed; card (b) "removes >50%" fires). (d) not reachable. (e) does not
  fire. Decision = **FALSIFIED (a)+(b)+(c)**. Candle axis closed.
  `EMA3_13_50_200` stays **CONDITIONAL**. Do not FREEZE. Not +45.0267104.
  §15: `spec/research/F006-coordinator-series-report-ema3-13-50-200-entry-candle-confirm.md`.

- **2026-10-03 ~21:17 Europe/Warsaw** — **H-EMA3-13-50-200-ENTRY-BREAKOUT-DEPTH-01 pre-registered**
  (§8 breakout depth on CONDITIONAL `EMA3_13_50_200` own trades; directional
  `(close - ema200) / ema200` ≥ D; D grid {0.02, 0.05, 0.10, 0.25, 0.50} as
  licensed shape, not another name's winning D; Train-1 only; control mean
  +91.1483016, n=423). Not a candle retune, not an abs-ATR retune, not a
  Val-1, not funding-carry, spread-capture, or catalog mean-reversion. If it
  fails, decision_if_fail stays CONDITIONAL and names HTF direction. Do not
  FREEZE. Ticket `spec/features/active/F006-ema31350200-entry-breakout-depth-01/ticket.md`.

- **2026-10-03 ~20:40 Europe/Warsaw** — **H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 = FALSIFIED (b)**.
  Tip `34e2c4a` FF-merged to `origin/main` (parent `0f7b608`). Review PASS
  `2026-10-03-f006-ema31350200-xsym-01-review-197231de`. Control +91.1483016 /
  n=423 / floor 7/12 / big winners 9 / +1131.956154 reproduced. Sized mean
  +127.142706 (+35.994404/series), mult gap +0.085755, stake_cv 0.429331,
  floor stayed 7/12. Series higher 6/10 (Result text said 7/10). Decision =
  **FALSIFIED (b)**. Formula closed. No validation window. `EMA3_13_50_200`
  stays **CONDITIONAL**. Do not FREEZE. Not +126.744211. §15:
  `spec/research/F006-coordinator-series-report-ema3-13-50-200-xsym-agree-sizing.md`.

- **2026-10-03 ~20:40 Europe/Warsaw** — **H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01 pre-registered**
  (§8 candle confirm on CONDITIONAL `EMA3_13_50_200` own trades; directional
  close-strength ≥ T; T grid {0.50, 0.60, 0.70, 0.80, 0.90} as licensed shape,
  not another name's winning T; Train-1 only; control mean +91.1483016, n=423).
  Not a Val-1 of the closed xsym formula, not an abs-ATR retune, not
  funding-carry, spread-capture, or catalog mean-reversion. If it fails,
  decision_if_fail stays CONDITIONAL and names breakout depth. Do not FREEZE.
  Ticket `spec/features/active/F006-ema31350200-entry-candle-confirm-01/ticket.md`.

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

- **2026-10-05 evening** — Coordination of F011 taken over by Grok (Limen) from Claude (rate-limited). Owner decision: plan C — max free resolution first (5m OI, trades->taker flow, long/short ratio; Bybit + Binance), no paid vendor yet; hourly OI frame = coarse baseline only, never a go/no-go verdict. Live Bybit liquidation collector starts now. Tickets: F011-data-coverage (T0 recon), F011-liq-collector.

- **2026-10-05 20:40** — F011-data-coverage and F011-liq-collector are DONE on branch grok/f011-plan-c (tip 3101d78), done directly by the coordinator while workers were down; collector deployed as systemd user service f011-liq-collector (do NOT respawn these tickets or start a second collector). Review F011-plan-c-review d541f1e0 running; after PASS merge, next = F011-forced-flow-frame-5m. Coverage: free 5m Bybit OI/account-ratio + trade archive + Binance metrics/klines cover all Train-1 with 0 gaps.

- **2026-10-05 20:55** — **H-NONCANDLE-SLEEVE-01 = FALSIFIED (a)+(b)** (review PASS 4df434ed, tip 44bd854 rebased onto main). Train-1 mean −276.30, shared-months sum −1381.49, OI consumption verified. 1h OI-fade mechanism closed; no catalog unfreeze/portfolio. Coarse 1h baseline only — not a verdict on F011 forced-flow (plan C, 5m).

- **2026-10-06 morning Europe/Warsaw** — **F011 5m frame merged; T2/T3 moved to 5m.** Frame
  `output/f011_forced_flow/frame_5m/{BTCUSDT,ETHUSDT}.csv.gz` (115200 rows each) merged at
  `cc9ea1b` after review `0a6f729a` PASS. Coordinator decision: T2 (state machine) and T3
  (event study) run on the 5m frame, not hourly — taker flow / impacts / 5m OI now exist;
  hourly remains a coarse baseline only. Tickets
  `F011-forced-flow-{states,event-study}` rewritten; `F011-forced-flow-lab.md` §9 amended
  (horizons +5m/+15m/+30m/+60m/+4h, +8h for EXHAUSTION; cost band 34 bps RT; taker flow in
  STRESS/EXHAUSTION). Non-blocking review notes recorded: rebuild needs ~25 GB temp +
  re-download; consider Git LFS / external store before committing more binaries; the 2
  pre-existing `test_causality` failures in fresh worktrees come from missing git-ignored
  hourly caches (not from the 5m diff). Causality prefix grid for T2 must reach past warmup
  so `oi_zscore` / `funding_zscore` are exercised.

- **2026-10-06 afternoon Europe/Warsaw** — **F011 ARCHIVE (coordinator final).** T4 diagnostics
  merged at `8da3a91`: Tests 1–3 NEGATIVE. Test-3 "≥20 positive events" read as independent
  CASCADE *entries* (BTC 11, ETH 18 in test segment) → gate fails; lift also largely
  definitional (`P(cascade|STRESS)` ~11.6). T3 already no directional edge vs 34 bps. Per
  owner pre-committed rule → **ARCHIVE** forced-flow strategy; paid historical liq **NO-GO**.
  Recorded unresolved only: `H-PRECASCADE-LIQ-01` (crowding-only → real-liq-defined cascade;
  needs ≥50 episodes/symbol + monetisation vs 34 bps on free collector data before any
  purchase). Collector kept running (~0.75d so far: BTC ~291 / ETH ~123 flattened events;
  rough cascade-like 5m bursts ~4–5/day). Closest Test-1 miss (CASCADE +15m vol 3/4) noted as
  context only. Tickets T2–T4 → `spec/features/done/`. Next = protocol §13 new direction
  (owner/trader); no open licensed axis on existing strategy profiles.

- **2026-10-06 evening Europe/Warsaw** — **F012 research phase opened** per owner brief 2026-10-06; F011 archived; collector unchanged (`f011-liq-collector` left running, not touched). Candidate-selection study committed at `spec/research/F012-structural-edge-candidates.md` (≥16 mechanisms, anti-F011 A/B/C filter, data feasibility with live probes, scoring, falsification designs). Recommendation: **C02 exchange delisting forced unwind** (2nd C01 ETF NAV-window × prior flow; 3rd C03 token unlock cliffs). Optional free collectors: `f012-deribit-book.timer`, `f012-farside-etf.timer` under `f012_collectors/` (2 GB / 64 MB caps; stop via `systemctl --user stop f012-deribit-book.timer f012-farside-etf.timer`). No strategy implementation; no backtest; validation/holdout untouched.


- **2026-10-06 night Europe/Warsaw** — **F012-C02 delisting forced-unwind falsification: FAIL.** Pre-registered in `c48165a`, criteria unchanged. 80/82 Train-1 perp delistings usable (2.4% missing), 61 article / 44 day-batch clusters. Delisted tokens keep falling after realistic entry (bar5m short → eff−1h +972 bp raw, owner-tier net incl. funding +834 bp [CI +66, +1596]), but perp and same-token spot fall together (perp − spot ann+24h→eff−1h +119 bp [−63, +458], basis ≈ 0, flow balanced), OI decay does not predict drift (ρ 0.013), the deadline window shows no drift (eff−24h→eff−1h −93 bp [−327, +139]), spot-only delistings fall as hard, neither venue is significant alone and the time-scrambled placebo test is not significant (p 0.10/0.13). Information/stigma drift, not forced flow → C02 archived. Note: `spec/research/F012-c02-delisting-falsification.md`; tables `output/f012_c02_delisting/`. No optimization; C01/C03 not started; collectors untouched.

- **2026-10-06 evening Europe/Warsaw** — **F012-C02 cost primary corrected to owner-tier ~9.9 bp RT** (owner Derivatives fees binding: taker 4.4 + basket half-spread+impact 0.56 → RT 9.92; maker bound 5.12). Stress 50/75/100; 34 bp labeled historical-reference obsolete. Tables recomputed (`costs_primary.csv`, `costs_latency_owner_primary.csv`, `tails_primary.csv`). **Decision remains FAIL** — identification (perp−spot≈0) and H2 (deadline drift CI∋0) unchanged by the lower hurdle. Note: `spec/research/F012-owner-cost-hurdle.md`. No C01/C03; collectors untouched.

- **2026-10-06 night Europe/Warsaw** — **F012-C01 ETF NAV-window × prior flow identification gate: Decision FAIL** (GATE A = FAIL, GATE B = NOT REACHED, GATE C = NOT REACHED). Criteria were pre-registered in `spec/features/active/F012-c01-etf-identification/prereg.md` (`0dbfdd2`) before any result. Train-1: 250 US trading days. The study used free data only (Farside snapshot, Coinbase 5m, Yahoo ETF daily, F011 5m frame). Mechanism: IBIT cash orders for T are due by 18:00 ET T-1, the NAV/BRRNY window is 15:00–16:00 ET T, and Farside row T goes public only late T to T+1, so the public pre-window input is row T-1. On the untouched fold F3 (2024-10-28 → 2025-02-28, n 84) the primary model M3 (chosen on F2) gives OOS R² 0.43 vs expanding mean, Spearman 0.66, and 0.89 sign accuracy on large days (M0 0.75). The **large-day lift was 1.38 < 1.5**. F3's flow regime tripled (median |flow| $367M), so the PIT "large" threshold flagged 52% of days. Walk-forward and F2∪F3 lifts (1.70 / 1.76) were not used to override the result. Sign predictability is mostly IBIT trend persistence. Flow ≈ 1.8× Coinbase window volume, so size is not the issue. Open owner question: amend criterion (c) as a new pre-registration, or keep C01 archived. Note `spec/research/F012-c01-etf-identification.md`; tables `output/f012_c01_etf/`. The parked delisting note exists and was not expanded. No optimization, C02 untouched, no C03, collectors untouched, no data purchased.

- **2026-10-06 night Europe/Warsaw** — **F012-C03 token-unlock-cliff identification / data feasibility: Decision FAIL** (Gate 0 FAIL on 0b PIT history → automatic kill; **DO NOT BUY**). Pre-registered in `spec/features/active/F012-c03-unlock-identification/prereg.md` (`150fafd`) before any bulk download. Single free schedule source: DefiLlama emissions dataset files (the API mirror is paid, HTTP 402, so this is a TOS grey zone; the old adapter git repo is now 404). Train-1: 4,032 cliff token-days / 152 tokens (LARGE ≥ 1% circ 636 / 94); recipient coverage 91.9%; on-chain coverage 0%; short availability 2,524/4,032 (LARGE 305/636, 59 tokens). PIT: archived pre-event `defillama.com/unlocks` pages verified only **3/30 = 10%** of a random sample (bar 80%); LARGE sample 7/30 (7/9 where a parseable snapshot existed); labels and amounts are revised over time. Hindsight upper bound (2,489 priced events / 68 tokens, matched controls, token-cluster CI): LARGE underperforms controls only from day −15 (LATE_PRE −309 bp, AT −99; EARLY_PRE −64 ∋ 0, so no −30 d front-run); there is a size gradient (LARGE − SMALL significant only in LATE_PRE / AT); the pre-registered LARGE × usd/ADV ≥ 1 × team/VC cell adds nothing over other LARGE events; the frozen BUY rule failed (cell PRE vs controls −358 [−896, +256]). Owner question only (not started): a free Wayback-based PIT re-test of the LARGE subset (232/638 events have a pre-event snapshot). Note `spec/research/F012-c03-unlock-identification.md`; tables `output/f012_c03_unlock/`; code `unlock_lab/`. C01/C02 untouched; collectors active and unchanged; no next candidate started; no data purchased.

- **2026-10-06 night Europe/Warsaw** — **F012-R2A leveraged-ETF daily reset (BITX/BITU/SBIT) identification: Decision FAIL**. Gate 0 KILL: BITX PIT AUM covers 29/250 sessions (11.6%) against a 90% bar. Gates 1–5 were not reached and no outcome was scored. Pre-registered in `spec/features/active/F012-r2a-letf-reset-identification/prereg.md` (`686f6ee`) before any AUM download. Volatility Shares publishes only a current BITX snapshot: no daily NAV×shares history, the premium/discount PDF has no shares, and the holdings XLS has no date or shares. Wayback gives 10 served captures with 9 distinct as-of dates in Train-1, all PIT-valid; NAV vs Yahoo close is within ±0.34%. Several CDX timestamps redirect to later snapshots, so the lab uses the served timestamp to avoid look-ahead. N-PORT is monthly only. ProShares BITU/SBIT history is free and complete (229 live sessions) but `UNVERIFIED-LABELED`. 5m price coverage is 100% (247 US / 115 placebo). The missing field is daily BITX shares outstanding with PIT timestamps. A proxy is forbidden, and no purchase is proposed. Per round-2 §5 → **NO CANDIDATE** for F012 round 2 pending a new owner brief; R2-B/R2-C were not started. Note `spec/research/F012-r2a-letf-reset-identification.md`; tables `output/f012_r2a_letf_reset/`; code `letf_reset_lab/` (`python3 -m letf_reset_lab.run`). Collectors untouched.

- **2026-10-06 night Europe/Warsaw** — **F012 CLOSED: NO CANDIDATE** (PO `f006-chatgpt-po`). Standalone outcome `spec/features/done/F012-structural-edge/outcome.md` covers C01–C03 + R2-A. It separates mechanism-identification FAILs (C01 Gate A lift 1.38 < 1.5, B/C not reached; C02 perp − spot ≈ 0, informational/stigma) from PIT-data FAILs (C03 Gate 0 10% < 80%, DO NOT BUY; R2-A Gate 0 BITX AUM 11.6% < 90%, **gates 1–5 not tested, no outcome scored**). Active F012 tickets were moved, unchanged, to `spec/features/done/F012-structural-edge/`; research notes untouched. Identification-only brief `spec/research/F013-structural-edge-identification-brief.md`: 5 previously untested mechanisms (N1 exchange leveraged tokens, N2 CME margin hikes, N3 Aave collateral-parameter cuts, N4 Ethena USDe hedge, N5 = R2-B re-evaluated on equal terms), PIT audit first. Free probes: Bybit announcements API serves only items from 2024-12-02, which is 24% of Train-1. Bybit LT endpoints return 404. CME returns 403 under its Data Terms. Aave payload tree is pruned. Summary in `output/f013_brief_probe/probe_summary.json`. Verdict **NO CANDIDATE**; lower-PIT-bar exception not invoked. STOP: no strategy/backtest/collector, collectors untouched, R2-B/R2-C not started, no paid data.

- **2026-10-06 night Europe/Warsaw** — **Collector portfolio review (PO mandate, one-shot).** After F012 CLOSE + F013 NO CANDIDATE. Standalone note `spec/research/F013-collector-portfolio-review-2026-10-06.md`. Board: **structural-edge PARKED — evidence constrained** (`spec/build.md` NOW/NEXT). Decision table:

  | collector | recommendation | reopen / sunset |
  | --- | --- | --- |
  | `f011-liq-collector` | **REVIEW_AT_N** | Trigger: ≥50 independent liq-defined cascade episodes/symbol for `H-PRECASCADE-LIQ-01` + PO decision; earliest date **2026-10-20** Europe/Warsaw; control owner ChatGPT PO; measurement owner Limen coordinator |
  | `f012-deribit-book.timer` | **SUNSET** | Safe stop: `systemctl --user stop/disable` timer (+ oneshot if running); **preserve** `data_cache/f012/deribit_book/` — **not executed this ticket** |
  | `f012-farside-etf.timer` | **SUNSET** | Safe stop: stop/disable timer; **preserve** `data_cache/f012/etf_flows/` — **not executed this ticket** |

  Rationale: liq collector still serves an open gate (sample-limited); Deribit unsigned book cannot fix C04/C05 blockers; Farside flows cannot repair C01 identification FAIL. Scope guards held: no F011 cascade resume, no catalog MR/funding/spread reopen, no new alpha family, no strategy/backtest/new collector, thresholds unchanged, cost ≈9.9 bp RT, free PIT remains. **STOP. Services still running.**
