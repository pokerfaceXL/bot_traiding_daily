# F006 — H-BB-20-2-ENTRY-LIQUIDITY-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-BB-20-2-ENTRY-HTF-DIRECTION-01` **FALSIFIED (a)+(c)+(d)** (`dd86dd0`),
> journal + profile close HTF direction on `BB_20_2_EMA200` and name the
> last open licensed axis as a not-yet-run §8 **liquidity** hypothesis on
> this name's own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c),
> tip `f7ac677`); the xsym sizing *formula* is closed (Val-4 `139ed3d`
> FALSIFIED (c)); candle close-strength is closed (`88b0ee3`); breakout
> depth is closed (`27fa7f6`); HTF direction is closed (`dd86dd0`). Exit /
> long-only direction / breadth already closed. This card is **not** a
> retune of the 4-bar HTF length, **not** a Val-5 of the closed stake,
> **not** long-only, and **not** an ATR gate. `BB_20_25_EMA200` is FREEZE
> on its own loop. That profile's last named axis was HTF; its loop report
> treated "liquidity" and "price versus range" as §8 examples that were
> **not** separately licensed there. This profile named liquidity as still
> open, so the axis is licensed **here**. There is no prior liquidity card
> on either BB name. Do not copy `3495b16`, control +82.900262, n=512, or
> any BB_20_25 cell onto this card as an expected result. Do not use
> `bb_20_2.5_*`. Do not reuse `BB_20_2_VOL12` / `sig_bb_breakout_vol`'s
> `vol_ratio > 1.2` (volume / SMA(20)), and do not reuse the closed
> `RVOL_RE_*` family (SMA volume multiples 2.0 / 2.5 / 3.0 plus range/ATR
> plus close location — a different generator, H2-falsified, not this
> name's gate). Every threshold below is written for this card.

experiment_id: H-BB-20-2-ENTRY-LIQUIDITY-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-ENTRY-HTF-DIRECTION-01
FALSIFIED (a)+(c)+(d) (tip dd86dd0). The single gated cell htf_4 mean
+75.8615895 versus control +95.3217987 (−19.4602092/series). Initial_sl
share rose +2.790851pp (0.47354497354497355 to 0.501453488372093, 358/756
to 345/688) against a required 10pp drop. Frozen big-winner PnL retained
was 83.0% (9/12, 1038.6112330239332 of 1251.654084307187). The pooled
floor went 7/12 → 8/12. Entry-vol, the xsym sizing formula, candle
close-strength, breakout depth, and HTF direction are already closed on
this name's own trades. Exit / long-only direction / breadth are already
closed. The signal is close-beyond-band + same-timeframe EMA200 agree
(`sig_bb_breakout_ema`, period 20, k=2.0). None of the closed gates asked
whether the signal bar itself traded with at least the typical base volume
of the same 20-bar window the band already uses.

Problem:
Most trades still die at the fixed initial_sl (358/756, 47.35%, 0% WR on
the ungated Train-1 cohort). A band pierce printed on a thin bar is
treated the same as a pierce printed on a bar with ordinary participation.
HTF direction, depth, and candle location did not separate stop-outs from
runners on this name. One remaining §8 entry change on THIS name,
orthogonal to absolute ATR%, to close-location inside the bar, to
band-penetration depth, to the prior HTF candle, and to the closed stake.

Mechanism:
The fixed initial stop is the death of a pierce that the market did not
trade. Base volume on the signal bar, compared with the median base volume
of the prior 20 fully closed native bars of the same series, is a
participation check inside the band's own sample. A bar at or above that
median has at least typical liquidity for this symbol and interval; a bar
below it is a thin print. The window excludes the signal bar, so the
threshold is known before the bar's volume is used as a decision. This is
not an ATR percentile, not volume/SMA × 1.2, not a range expansion, not
(close-low)/(high-low), not band depth, not HTF direction, and not
"drop all shorts". It does not read another symbol.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 one-shot
signal when the signal bar's base volume is below the median base volume
of the prior 20 closed native bars will raise mean Train-1 net PnL versus
the ungated NO_TRAIL baseline AND cut the initial_sl share among remaining
trades, while retaining enough big-winner PnL that the pooled losing-month
floor can improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 liquidity condition). From the closed bars
of the same symbol and the same interval already loaded for Train-1
(do not load another cache file, do not download, do not read *_20260901*
or *_20200325*):

  Use the native base `volume` column only. Do not convert to quote
  volume. Do not read `vol_ratio` or `vol_ma20`.

  For a signal bar at index i (the bar whose open time is the signal):
    window = volume[i-20 : i]   # 20 bars strictly before the signal bar
    if len(window) < 20: reject
    med = median(window)
    if med is not finite or med <= 0: reject
    keep iff volume[i] >= med

  The signal bar is not inside the window. Ties at the median are kept.
  A missing volume rejects.

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_bb_20_2_entry_htf_direction.py). No exit, sizing, symbol,
interval, long-only, breadth, ATR-threshold, candle-strength,
breakout-depth, or HTF-direction changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as the HTF harness).
Do not use ATR. Do not use an EMA for this gate. Do not read bb_20_2.5_*.
Do not implement vol_ratio > 1.2. The lookback 20 is this name's Bollinger
period, used as the band's own sample, not a transferred RVOL multiple.
Binary gate. Do not grid the multiple and do not grid the window.

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym / candle
/ breakout-depth / HTF control figures before trusting the gated cell:
  - mean train1_net_pnl = +95.3217987 (10 series)
  - Train-1 entry cohort n = 756, entry net ≈ +834.347778
  - initial_sl share ≈ 0.47354497354497355 (358/756)
  - big-winner PnL at net≥29.9 ≈ 1251.654084307187 (12 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_bb_20_2_entry_htf_direction/cell_summary.csv
control row. Do NOT import +82.900262, n=512, initial_sl 0.580078,
big-winner 968.020732, or any BB_20_25 cell (including +70.515667).

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials = 1 (this gate is binary; do not add a multiple grid)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of
big-winner PnL retained AND pooled losing-month floor strictly below this
name's ungated floor (7/12 on the pooled control — confirm in the control
cell before comparing) AND mean trades/series ≥ 10.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline; OR
(b) the gate removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor); OR
(e) mean trades/series < 10.
Do not add a second multiple, a second window, or a quote-volume conversion
after seeing the result without a new written hypothesis.
Do not declare this falsified because another name never ran liquidity, and
do not declare it passed because `BB_20_2_VOL12` or `RVOL_RE_*` exists in
the catalog or in an old family note.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the gate looks promising, schedule a separate validation run later — do
not tune on it now.

Budget:
One gated cell plus the ungated control. number_of_trials = 1.
No parameter sweep.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider a separate validation later; do not open holdout in this run; do not FREEZE on the pass alone)
decision_if_fail: liquidity is the last open licensed axis this profile names, once HTF direction is closed. Worker must not set FREEZE and must not change profile status. If the falsifiers fire on this name's own trades, protocol §4 level C allows **FREEZE** at this experiment's own Decision (ungated Train-1 book stays aggregate-positive, so not REJECT). That FREEZE is not written in this pre-registration and is not written by the worker. Portfolio combination is not a remaining axis: shared-losing months (`dc9818e`) fail the §8 precondition. Price-versus-range is not a separately named axis here (candle close-strength already tested location in the bar). Do not open `EMA_50_200` or `EMA3_13_50_200` inside this run. Do not treat the BB_20_25 ruling (liquidity was only a §8 example on that name, because HTF was its last named axis) as this name's closure. Do not retune the window or the median rule inside this run. Do not start a new signal family.

## Result

Run: `F006_DATA_CACHE=<main checkout>/data_cache python3 scripts/f006_bb_20_2_entry_liquidity.py`
(script + test committed before the run at `9199195`; artifacts in
`output/f006_bb_20_2_entry_liquidity/`; `grid_freeze.json` written before the
gated cell; `number_of_trials = 1`, single binary cell `liq_med20`).
The gate reads only the native base `volume` column of the same closed
Train-1 series: keep iff signal-bar volume >= median volume of the 20 closed
native bars strictly before it (signal bar excluded; <20 prior bars, missing
volume, or median not finite / <= 0 rejects; ties kept). It reads no
`bb_20_2.5_*`, no band, no ATR, no EMA, no `vol_ratio` / `vol_ma20`, no
quote volume, no candle strength, no breakout depth, no HTF direction. Exits
use the ungated persistent signal; NO_TRAIL violations 0; matched-trade
economics mismatches 0.

Control (ungated) reproduced exactly: catalog5 monthly replay 10/10
(n_trades equal, train1_net_pnl within 1e-6), and the HTF-direction control
row (`output/f006_bb_20_2_entry_htf_direction/cell_summary.csv`) matched:
mean **+95.3217987**, entry n **756**, entry net **+834.347778**, initial_sl
share **0.473545** (358/756), big-winner PnL (net≥29.9) **1251.654084**
(12 trades), pooled losing entry-months **7/12**.

Gate activity (Train-1 one-shot signals, all 10 series): 2498 one-shot
signals; 2372 at or above the prior-20 median, 126 below → 126 rejected
(5.0%); 0 rejected for short window / non-positive median. A close beyond
the 2σ band almost always prints on at-least-median volume, so the
closed-trade cohort shrinks only 756 → 742.

| cell | mean train1 net | entry n | n/series | entry net | initial_sl | Δ SL pp | big winners kept | BW PnL kept | kept % | losing months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | +95.321799 | 756 | 75.6 | +834.347778 | 0.473545 | 0.00 | 12/12 | 1251.654 | 100.0% | 7/12 |
| liq_med20 | +97.245599 | 742 | 74.2 | +853.585778 | 0.474394 | −0.08 | 12/12 | 1251.654 | 100.0% | 6/12 |

Gated per-symbol train1 net (control in parentheses): BTC −31.807
(−35.123), DOGE +405.526 (+389.419), ETH −15.737 (−15.250), SOL +131.958
(+131.956), XRP +482.517 (+482.215); 3/5 net-positive (unchanged). The floor
improvement is one month: 2024-04 flips from −5.17 to +5.01; every other
month keeps its sign (2024-09 worsens −60.43 → −73.07).

Falsifiers (pre-declared):
- (a) mean ≤ baseline — false (+97.245599 vs +95.321799, +1.923800/series).
- (b) removes >50% big-winner PnL — false (100% retained, 12/12).
- (c) initial_sl share fails to fall ≥10pp — **TRUE** (share *rises*
  0.08pp, 0.473545 → 0.474394, 358/756 → 352/742).
- (d) pooled losing-month floor does not improve — false (7/12 → 6/12).
- (e) mean trades/series < 10 — false (74.2).

**Outcome: FALSIFIED (c).** No passing cell. The gate is nearly inert on
this name: it removes 14 closed trades, none of them big winners, and does
not change the stop-out rate. The +1.92/series mean gain and the one-month
floor gain come from removing a handful of small trades (a sub-$6 swing in
2024-04), not from separating stop-outs from runners — the mechanism the
card claimed.

## Decision

**FALSIFIED (c).** Checked 2026-10-03 ~16:20 Europe/Warsaw against
`output/f006_bb_20_2_entry_liquidity/cell_summary.csv`, `manifest.json`,
and the Train-1 blotters (`train1_entry` only) on the FF-merged tip
`776e167` (parent `df38f08`; review PASS
`2026-10-03-f006-bb202-entry-liquidity-revie-ac02a80e`). The Result table
matches those artifacts after ordinary rounding (gated mean
+97.2455987 prints as +97.245599; the initial_sl move of +0.084856pp
prints as 0.08pp). Blotter recount: control 358/756, `liq_med20` 352/742.

Control is exact: mean train1_net_pnl **+95.3217987** (sum 953.217987
across 10 series), entry n **756**, entry net **+834.347778**, initial_sl
**358/756 = 0.47354497354497355**, big-winner PnL **1251.654084307187**
(12 trades, net≥29.9), pooled losing entry-months **7/12**.

(a) does not fire. The only gated cell `liq_med20` mean train1_net_pnl is
**+97.2455987** (sum 972.455987), which is **+1.923800/series** versus
+95.3217987. Entry n 742, entry net +853.585778.
(b) does not fire. Frozen baseline big-winner PnL retained is
**1251.654084307187** of 1251.654084307187 (**12/12**, fraction 1.0).
**(c) FIRES.** `liq_med20` initial_sl share is **352/742 =
0.4743935309973046**, which is **+0.084856pp** versus
0.47354497354497355 (`initial_sl_share_drop_pp` =
−0.08485574523310335). The required move is a drop of ≥10pp. The share
rose. The +1.923800/series mean increase does not override this
pre-registered falsifier.
(d) does not fire. Pooled losing entry-months go **7/12 → 6/12**. 2024-04
flips from −5.171705 to +5.007853. 2024-09 worsens from −60.434073 to
−73.066464. The floor improvement is real and is not what (c) asked for.
(e) does not fire. Mean trades/series is 74.2 (≥10). `number_of_trials = 1`.
0/1 cells pass. Per-symbol train1 net (control in parentheses): BTC
−31.807 (−35.123), DOGE +405.526 (+389.419), ETH −15.737 (−15.250), SOL
+131.958 (+131.956), XRP +482.517 (+482.215); 3/5 net-positive, unchanged.

Per `decision_if_fail`: close the liquidity axis on `BB_20_2_EMA200` own
trades. Do not retune the 20-bar median rule. Do not open a quote-volume
conversion or a second window.

**Strategy status:** **FREEZE**. Every axis licensed on
`spec/research/strategy_profiles/BB_20_2_EMA200.md` now has an own-trades
citation: exit (`923de9c`, `3d4edd4`), long-only and breadth (`f420078`,
this name's cells), entry-vol (`f7ac677`), the xsym sizing formula
(`139ed3d`), candle close-strength (`88b0ee3`), breakout depth
(`27fa7f6`), HTF direction (`dd86dd0`), and liquidity (`776e167`). This is
closure on this name's own trades, not a class closure and not an analogy
to `BB_20_25_EMA200`. It is not evidence for `EMA_50_200` or
`EMA3_13_50_200`.

§4 level C permits FREEZE and level D does not permit REJECT. The ungated
Train-1 book stays aggregate-positive (mean +95.3217987). Further
development would require a remaining licensed axis; none remains.
Price-versus-range is not separately licensed (candle close-strength
already tested location in the bar). Shared-losing months (`dc9818e`)
block §8 portfolio combination and do not license this FREEZE. The book
is unstable across symbols (3/5 entry-cohort symbols net-positive; 8/10
Train-1 series positive), 0/10 series pass the monthly promotion check,
and the sizing formula failed its own Validation-4. FREEZE means keep the
ungated book and stop tuning this name.

**reason:** falsifier (c). Signal-bar base volume versus the prior-20
median did not separate `initial_sl` deaths from `signal_reverse` runners.
The stop share rose by 0.084856pp. The mean rose by only +1.923800/series,
and the one-month floor gain is not the pre-registered 10pp stop-out cut.

**next_action:** stop the `BB_20_2_EMA200` loop. Next CONDITIONAL catalog5
name is `EMA_50_200` (not `EMA3_13_50_200`). Its first open own-trades
axis, in the same order this loop used, is entry-vol / abs-ATR
(DNR-by-transfer only; never run on that name). Pre-register
`H-EMA-50-200-ABS-ATR-ENTRY-GATE-01` on that name's own Train-1 control
(catalog5 mean +72.6693115, sum +726.693115). Do not treat this liquidity
result, or +95.3217987, or +82.900262, as that name's baseline.
