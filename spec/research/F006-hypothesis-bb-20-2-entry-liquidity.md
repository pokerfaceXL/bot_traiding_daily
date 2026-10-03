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

## Decision
