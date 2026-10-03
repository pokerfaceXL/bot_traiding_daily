# F006 — H-EMA3-13-50-200-XSYM-AGREE-SIZING-01 (pre-registered)

> Pre-registered **before** implementing or running the sized arm.
> `H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** on this
> name's own trades (`46e4509`). (d) was not reachable. Entry-vol / abs-ATR
> stays closed. Do not retune T. `EMA_50_200` is **FREEZE** after its own
> liquidity result (`48aef9f`). Its xsym sizing Train-1 result (`48d03b0`,
> FALSIFIED (b), sized mean +126.744211, floor stayed 7/12, no Val-1) closes
> that formula on **that name only**. `BB_20_2_EMA200` Train-1 pass
> (`1774a8a`) and Val-4 fail (`139ed3d`), and `BB_20_25_EMA200` Train-1 pass
> (`1c9ff7e`) and Val-1 fail (`89e936a`), likewise close those names only.
> They are not this test. Do not copy +72.6693115, +95.3217987, +82.900262,
> or +126.744211, and do not copy another name's floor move, mult gap, or
> stake_cv onto this card as an expected result. Position sizing has never
> been run on `EMA3_13_50_200` under protocol. Do not FREEZE this name.

experiment_id: H-EMA3-13-50-200-XSYM-AGREE-SIZING-01
date: 2026-10-03
base_strategy: EMA3_13_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA3_13_50_200 stays CONDITIONAL after H-EMA3-13-50-200-ABS-ATR-ENTRY-GATE-01
FALSIFIED (a)+(c) on own trades (tip 46e4509). (d) was not reachable: no T
passed (a)–(c). Control mean +91.1483016/series reproduced from this
experiment's artifacts (output/f006_ema3_13_50_200_abs_atr_gate/; sum
+911.483016, 10 series; entry cohort n=423, +771.2836172145886, initial_sl
292/423, floor 7/12, big winners 9 / +1131.9561537333418). Best abs-ATR cell
t_2_0 mean +83.4087526 (delta −7.739549/series), n=337, initial_sl drop
4.04557 pp, big-winner PnL kept 85.1%. The flat 7/12 floor is informational
on that card, not a (d) fire. Exit, long-only, and breadth already ran on
this name's own series and did not clear the monthly floor. The ungated book
is still aggregate-positive. §8 allows a sizing test only after the signal
itself has an edge; that precondition holds. It does not license masking a
negative-EV signal. EMA_50_200's sized mean +126.744211 is not this name's
expectation.

Problem:
Monthly regularity is unresolved (abs-ATR control entry-month floor 7/12;
0/10 series clear §7). An ATR-magnitude entry gate removes the same
signal_reverse runners that carry the aggregate PnL. This name has no
own-trades sizing result. A stake rule that keeps every trade can reweight
entries without the sample-starvation that boolean gates use.

Mechanism:
Basket triple-EMA crosses (`sig_ema3_cross(13, 50, 200)`) that coincide with
the same nonzero direction on peer symbols are more likely to be the
regime-aligned runners; idiosyncratic single-symbol fires are more likely to
be initial_sl deaths. Because strategy_signal_series is a persistent
directional state per (symbol, interval), the count of the other four basket
symbols whose EMA3_13_50_200 signal matches the traded symbol's nonzero
direction on the closed bar is a causal, bar-aligned agreement score. It is
not an ATR threshold, not `sig_ema_cross(50, 200)`, and not a fitted cutoff
from another name's PnL. Scaling stake by that score keeps n_trades invariant
and raises the relative weight of consensus entries.

The stake band is structural, rewritten for this name, not a threshold mined
on EMA_50_200, BB_20_2, or BB_20_25, and not that name's +126.744211 result:
n_agree ∈ {0,1,2,3,4} maps linearly onto [0.5, 2.0],
mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
because (2.0 − 0.5) / 4 = 0.375. That arithmetic is the structural band.
Using it here is the own-trades test of this mechanism on EMA3_13_50_200.
It is not a claim that another name's Train-1 result or validation fail
already answered this name.

Hypothesis:
Replacing uniform stake=100 with stake=100*mult(n_agree), where n_agree is
the number of the other 4 basket symbols whose EMA3_13_50_200 persistent
signal equals the traded symbol's nonzero direction on the same interval,
will raise mean Train-1 net PnL versus the uniform-stake control AND strictly
lower this name's pooled losing-month floor, with
mean(mult|winner) > mean(mult|loser).

Change to test:
ONE position-sizing change only, via backtest_engine.run_backtest
stake_series. No entry gate, no abs-ATR, no exit, symbol, interval,
direction, or breadth change. NO_TRAIL unchanged.

  n_agree ∈ {0,1,2,3,4}
  mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
  # → 0→0.50, 1→0.875, 2→1.25, 3→1.625, 4→2.00
  stake_series = 100.0 * mult, aligned to the engine fill bar.

Causal alignment (required): a signal at bar i close fills at bar i+1 open.
stake_series at the fill bar must be the agreement observed at the prior
closed bar. The first bar has no prior agreement and uses the uniform $100
stake. Do not read the fill bar's own close. Reuse the one-bar shift in
scripts/f006_ema_50_200_xsym_agree_sizing.py (or the BB sibling); point the
signal name at EMA3_13_50_200. Do not reuse that script's EXPECTED_MEAN.

Freeze this single formula before the run. No post-hoc retuning.
number_of_trials = 1 (one sized formula). Report the uniform control and
this one sized arm only.

Baseline:
Uniform stake=100 EMA3_13_50_200 NO_TRAIL on the frozen 5-symbol × 2-interval
Train-1 basket. The control arm (stake_series=None) must reproduce all 10
train1_net_pnl rows in
output/f006_notrail_monthly_catalog5/summary/results.csv for strategy
EMA3_13_50_200 (mean **+91.1483016**/series, sum **+911.483016**) and match
n_trades, before the sized arm is trusted. That figure is also the
reproduced control from output/f006_ema3_13_50_200_abs_atr_gate/ — use it as
this name's baseline going forward. Do not match +72.6693115. Do not match
+95.3217987. Do not match +82.900262. Do not match +126.744211. Use the
Train-1 caches the abs-ATR control just matched (checksums in
output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json,
*_20240126T000000Z_20250301T000000Z.csv). Do not reuse another script's
EXPECTED_CHECKSUMS table. Do not load *_20260901* or *_20200325*.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. pooled losing-month floor (of 12, by entry-month, same definition as the
   abs-ATR harness on this name). Confirm the control floor in this run.
   The abs-ATR control measured 7/12; that is an observation to confirm,
   not an imported pass line from another name.
3. n_trades invariant: n_trades_sized == n_trades_baseline for every series
   (hard), both closed trades and Train-1-entry keys
4. mean(mult|winner) − mean(mult|loser) on Train-1-entry closed trades
5. stake_cv across Train-1 entries (must be > 0.05)
6. big-winner contribution (net≥29.9) versus this name's uniform control
   (informational). Recompute the set on this run's ungated blotter. The
   abs-ATR freeze observed 9 trades / +1131.9561537333418; confirm, do not
   import another name's set (not 5 / +843.7639016181568).
7. number_of_trials = 1

Expected improvement:
Mean train1_net_pnl > this name's uniform control (+91.1483016) AND pooled
losing-month floor strictly below this name's control floor AND
mean(mult|winner) > mean(mult|loser), with n_trades invariant and
stake_cv > 0.05.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ this name's uniform baseline (+91.1483016); OR
(b) pooled losing-month floor does not improve (stays ≥ this name's
    control floor); OR
(c) mean(mult|winner) − mean(mult|loser) ≤ 0; OR
(d) n_trades invariant broken on any series; OR
(e) stake_cv ≤ 0.05 (degenerate near-uniform weights).
A flat month floor is (b) on this card: the sentence says a non-improving
floor falsifies. If (b) fires, the formula is closed and no validation
window is opened. Do not change the mult formula after seeing results
without a new written hypothesis. Do not declare this falsified because
EMA_50_200 sizing was FALSIFIED (b), or because BB_20_2 Val-4 or BB_20_25
Val-1 failed. Do not declare it passed because either BB name's Train-1
passed or because EMA_50_200's sized mean was +126.744211.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the sized arm passes, a separate validation run is a later hypothesis.
Do not open it in this run. A validation window is allowed only if a later
Decision says this arm passed.

Budget:
One pre-registered formula. Control + sized arm only. Report both.
No grid. No second mechanism.
```

decision_if_pass: REFINE (update EMA3_13_50_200 profile metrics; sizing stays
  open until a separate validation; do not open holdout in this run; do not
  FREEZE; status stays CONDITIONAL)
decision_if_fail: this xsym-agree formula is closed on EMA3_13_50_200 own
  trades. Worker must not set FREEZE and must not change profile status.
  The name stays CONDITIONAL. The following open axis is candle confirm
  (entry structure) on this name only. Do not retune 0.5 / 0.375 / 2.0
  inside this run. Do not treat the result as evidence about EMA_50_200 or
  either BB name. Do not reopen abs-ATR. Do not open a validation window:
  the card allows one only if the arm passes. Do not start funding-carry,
  spread-capture, or catalog mean-reversion.

## Result

Run: `F006_DATA_CACHE=<main checkout>/data_cache python3 scripts/f006_ema3_13_50_200_xsym_agree_sizing.py`
at harness commit `0f7b608`. Artifacts: `output/f006_ema3_13_50_200_xsym_agree_sizing/`
(`summary/{results.csv,cell_summary.json,manifest.json,run.log,control_train1_entry_blotter.csv,sized_train1_entry_blotter.csv}`,
`raw/<SYMBOL>_<interval>.json`). Only the 10 frozen Train-1 caches
(`*_20240126T000000Z_20250301T000000Z.csv`) were loaded. Their checksums equal
`output/f006_ema3_13_50_200_abs_atr_gate/grid_freeze.json` (`checksums_match_abs_atr_grid_freeze: true`).
No validation or holdout bars were loaded. number_of_trials = 1.

Formula (frozen, unchanged): `mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`, where n_agree is
the number of the other 4 basket symbols whose `EMA3_13_50_200` persistent signal equals the
traded symbol's nonzero direction on the same interval.
Causal alignment: the closed-bar multiplier is shifted forward one row (`.shift(1)`), so
the stake at fill bar i comes from the agreement at closed bar i−1. The first bar falls back to
uniform stake 100. Post-run check: 423/423 sized Train-1 entries have
`stake == 100 * mult(prior closed bar)`. 40/423 differ from the fill bar's own-close
multiplier, so no fill reads its own bar's close.

Control gate (stake_series=None): all 10 catalog5 `EMA3_13_50_200` `train1_net_pnl` rows were
reproduced, max abs diff **0.0**. n_trades equal on all 10. Mean **+91.1483016**/series
(sum +911.483016). Entry cohort n=423, net +771.283617, 459 total closed trades.
Control pooled entry-month losing floor confirmed in this run: **7/12**. Big winners
(net ≥ 29.9, this run's control blotter): **9 / +1131.956154**, which matches the abs-ATR
freeze observation.

| metric | control (uniform 100) | sized (xsym agree) |
|---|---|---|
| mean train1_net_pnl / series | +91.148302 | **+127.142706** (Δ +35.994404) |
| Train-1-entry trades | 423 | 423 |
| Train-1-entry net / per trade | +771.283617 / +1.823366 | +1075.237926 / +2.541934 |
| pooled losing-month floor (of 12) | 7 | **7** |
| pooled stake_cv | — | 0.429331 (all 10 series > 0.05; min 0.338418) |
| mean mult winners / losers | — | 1.273438 / 1.187682 (gap **+0.085755**) |
| big winners (≥29.9) count / sum | 9 / +1131.956154 | 14 / +1678.744869 (sized PnL on the control's 9 keys: +1485.937533) |

Pooled entry-month net, control → sized: 2024-03 −53.20→−70.52, 04 −85.03→−82.77,
05 −81.65→−98.94, 06 +30.34→+23.60, 07 +43.62→+30.73, 08 −99.50→−123.25, 09 −28.27→−31.96,
10 +258.07→+163.94, 11 +812.27→+1299.61, 12 −37.20→−67.09, 2025-01 −114.35→−154.04,
02 +126.17→+185.92. The same 7 months lose in both arms. Sizing amplified six of the seven
losing months and grew the 2024-11 runner month.

Per series, sized vs control: sized is higher on 7/10 series. It is lower on SOL240
(−15.93 vs −14.95), ETH240 (−38.15 vs −35.12), and DOGE240/DOGE60 (149.76 vs 208.85;
40.11 vs 201.20). Per-series entry-month floors moved SOL60 3→2 and BTC60 7→6, but DOGE60
went 6→7. The pooled floor did not move.

Note: the sized mean +127.142706 is this name's own computed figure from this run. It is
close to `EMA_50_200`'s +126.744211 only by coincidence; nothing was copied.

Falsifiers:
- (a) mean sized +127.142706 > control +91.1483016 → **not fired**
- (b) pooled losing-month floor 7 → 7 (no strict improvement) → **FIRED**
- (c) winner−loser mean mult +0.085755 > 0 → **not fired**
- (d) n_trades invariant held on all 10 series (total and Train-1-entry keys) → **not fired**
- (e) stake_cv 0.429331 > 0.05 (every series > 0.05) → **not fired**

**Verdict: FALSIFIED (b).** The mean rose, but the monthly floor did not improve. Under
the card, this formula is closed on EMA3_13_50_200 own trades, and no validation window
opens. Profile status was not changed.

## Decision

**FALSIFIED (b).** Checked 2026-10-03 ~20:40 Europe/Warsaw against
`output/f006_ema3_13_50_200_xsym_agree_sizing/summary/cell_summary.json`,
`summary/results.csv`, and `summary/manifest.json` on the FF-merged tip
`34e2c4a` (parent `0f7b608`; review PASS
`2026-10-03-f006-ema31350200-xsym-01-review-197231de`, engine claude).
Control replay max abs train1 diff is 0.0. The manifest records one fired
falsifier: pooled losing-month floor did not improve (7 >= 7).

Applied sentence, from this card: "(b) pooled losing-month floor does not
improve (stays ≥ this name's control floor)". The card also says: "A flat
month floor is (b) on this card: the sentence says a non-improving floor
falsifies. If (b) fires, the formula is closed and no validation window is
opened." A flat 7/12 is that sentence, not a near-miss. The series-higher
count is not in (b). decision_if_fail closes this xsym-agree formula on
`EMA3_13_50_200` own trades and names candle confirm as the following open
axis. The data-split sentence opens a later validation hypothesis only if
the sized arm passes. It did not pass, so no Val-1 is written. §7
develop-not-abandon keeps this name in the loop (status **CONDITIONAL**,
next licensed axis) and does not keep a failed formula open.

Pre-declared checks (number_of_trials = 1, formula frozen
`mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`, fill bar uses the prior
closed bar):

- control mean **+91.1483016** (replay max abs diff 0.0, sum +911.483016),
  Train-1-entry n=**423**, entry-net **+771.283617**, total closed trades
  459, pooled entry-month floor **7/12**, big winners **9 / +1131.956154**
- sized mean **+127.142706** (delta **+35.994404**/series vs +91.1483016),
  entry-net **+1075.237926**, floor **7/12**
- pooled mean(mult|winner) minus mean(mult|loser) **+0.085755** (1.273438 vs
  1.187682), stake_cv **0.429331** (every series > 0.05; min 0.338418)
- n_trades invariant held on all 10 series (459 closed and 423 Train-1-entry keys)
- series with sized train1_net_pnl strictly above control: **6/10**
  (BTC240, XRP240, SOL60, ETH60, BTC60, XRP60). Lower on SOL240, ETH240,
  DOGE240, DOGE60. The Result text says 7/10. That line is wrong. The same
  Result paragraph lists those four lower series, so it contradicts itself.
  `results.csv` is the count. (b) does not depend on the series count, so
  the falsifier label is unchanged.
- same seven entry-months lose in both arms (2024-03, -04, -05, -08, -09,
  -12, 2025-01)

(a) does not fire: +127.142706 > +91.1483016. (b) fires: the floor stays
7/12 (7 >= 7). (c) does not fire: gap +0.085755. (d) does not fire.
(e) does not fire: stake_cv 0.429331.

This is not the `EMA_50_200` sized mean +126.744211 (`48d03b0`). The two
figures are close by coincidence; nothing was copied. It is not the
`BB_20_2_EMA200` Train-1 sizing verdict (`1774a8a`, floor moved, REFINE)
and not the `BB_20_25_EMA200` Train-1 pass (`1c9ff7e`). Abs-ATR on this
name stays **FALSIFIED (a)+(c)** at Decision `3318658` / tip `46e4509`.
(d) was not reachable there and is not this label.

**Strategy status:** **CONDITIONAL**. Do not FREEZE. This xsym-agree formula
is closed on this name. No validation window. Entry-vol stays FALSIFIED
(a)+(c) (`46e4509` / Decision `3318658`). Exit, long-only, and breadth stay
closed. Candle confirm is the next open axis and is pre-registered in this
commit, not yet run. Breakout depth, HTF direction, and liquidity stay open
after that. Do not retune 0.5 / 0.375 / 2.0. Holdout stays closed. Do not
start funding-carry, spread-capture, or catalog mean-reversion. Do not
treat `48d03b0`, `1774a8a`, or `89e936a` as this result. Baseline remains
the reproduced control **+91.1483016**.

**reason:** falsifier (b). Sizing raises mean Train-1 net (+91.1483016 to
+127.142706) and skews stake toward winners (gap +0.085755), but the pooled
losing-month floor does not improve (7/12 to 7/12).

**next_action:** one candle-confirm entry gate on this name only,
`H-EMA3-13-50-200-ENTRY-CANDLE-CONFIRM-01`. Not a Val-1 of this formula.
Not an abs-ATR retune. Baseline remains the reproduced control
**+91.1483016** (n=423).

