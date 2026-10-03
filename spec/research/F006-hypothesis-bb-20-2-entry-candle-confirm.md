# F006 — H-BB-20-2-ENTRY-CANDLE-CONFIRM-01 (pre-registered)

> Pre-registered **before** implementing or running the gate. After
> `H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01` **FALSIFIED (c)** (`139ed3d`), journal +
> profile close that xsym-agree formula on `BB_20_2_EMA200` and name the next
> open axis as a not-yet-run §8 **entry-structure** hypothesis on this name's
> own trades. Entry-vol/abs-ATR is closed (FALSIFIED (a)+(c), tip `f7ac677`);
> the xsym sizing *formula* is closed; exit / direction / breadth levers
> already closed. This card is **not** a Val-5 of the closed stake and does
> **not** retune it. `BB_20_25_EMA200` is FREEZE on its own loop; its candle
> result at `e70161d` (and that name's T=0.70 numbers) is **not** this test.
> Do not copy that name's control mean (+82.90), n=512, initial_sl 58.01%, or
> pass/fail onto this card as an expected result.

experiment_id: H-BB-20-2-ENTRY-CANDLE-CONFIRM-01
date: 2026-10-03
base_strategy: BB_20_2_EMA200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
BB_20_2_EMA200 stays CONDITIONAL after H-BB-20-2-XSYM-AGREE-SIZING-VAL4-01
FALSIFIED (c) (tip 139ed3d; pooled mult gap -0.102941). Entry-vol/abs-ATR
own-trades gate FALSIFIED (a)+(c) tip f7ac677. Exit-class / partial-exit /
long-only / breadth already closed on this name's own-trade evidence.
Autopsy (Train-1 n=756): initial_sl 358/756 (47.35%) at 0% WR; signal_reverse
carries profit; avg winner +12.50 / avg loser -2.67. The signal itself is
close-beyond-band + EMA200 agree; it does not require the signal bar to close
decisively in the breakout direction relative to its own high-low range.
Abs-ATR rejected high absolute volatility; the closed stake rejected a
cross-symbol agreement multiplier on Val-4. Neither asked whether the
breakout candle's close location (candle confirmation) separates stop-outs
from runners on THIS name.

Problem:
Most trades still die at the fixed initial_sl; pooled Train-1 losing-month
floor is 7/12; 0/10 series clear §7. Closed levers (vol gate, one sizing
formula, exit, direction, breadth) did not fix regularity. We need one
remaining §8 entry-structure change on THIS name, orthogonal to absolute
ATR% and to the closed stake, written before the run.

Mechanism:
A BB pierce that closes near the mid of its own bar (weak / dojish
confirmation) is more likely a transient wick-through that reverses into the
initial stop. A pierce that closes near the favourable extreme of the bar
(strong directional close) commits more of the bar's range to the breakout
side and is more likely to travel to the opposite structural extreme
(signal_reverse). Candle close-strength is computed only from the closed
signal bar's OHLC — causal, no look-ahead, and not an absolute-volatility
threshold and not a stake multiplier.

Hypothesis:
Adding a single causal entry gate that rejects a BB_20_2_EMA200 one-shot
signal when the signal bar's directional close-strength is below a
pre-registered threshold T will raise mean Train-1 net PnL versus the ungated
NO_TRAIL baseline AND cut the initial_sl share among remaining trades, while
retaining enough big-winner PnL that the pooled losing-month floor can
improve — earned on this name's own trades.

Change to test:
ONE entry refinement only (§8 candle confirmation). On the closed signal bar:

  range = high - low
  close_strength_long  = (close - low)  / range   # undefined / fail if range == 0
  close_strength_short = (high - close) / range
  keep iff:
    direction == +1 and close_strength_long  >= T
    direction == -1 and close_strength_short >= T
    (range == 0 ⇒ reject)

Intersect with the existing one-shot entry mask (same pattern as
scripts/f006_bb_20_2_abs_atr_gate.py). No exit, sizing, symbol, interval,
direction, breadth, or ATR-threshold changes. NO_TRAIL unchanged. Exits
continue to use the ungated persistent signal (same as abs-ATR gate harness).

Baseline:
Ungated BB_20_2_EMA200 NO_TRAIL on the frozen 5-symbol × 2-interval Train-1
basket. Control must reproduce this name's catalog / abs-ATR / xsym control
figures before trusting gated cells:
  - mean train1_net_pnl = +95.3217987 (10 series)
  - Train-1 entry cohort n = 756, entry net ≈ +834.347778
  - initial_sl share ≈ 0.473545 (47.35%)
  - big-winner PnL at net≥29.9 ≈ 1251.654084 (12 trades)
  - pooled losing entry-months = 7/12
Reference source: output/f006_bb_20_2_abs_atr_gate/cell_summary.csv control
row (and matching xsym control_replay). Do NOT import +82.900262 or n=512.

Metrics (pre-declared):
1. mean train1_net_pnl across 10 series (primary) / pooled net and net/trade
2. initial_sl share among closed Train-1-entry trades
3. n_trades (reject thin: mean n_trades/series < 10)
4. pooled losing-month floor (of 12, by entry-month)
5. big-winner PnL retained vs ungated baseline (freeze big winner = net≥29.9 before run)
6. #symbols net-positive / per-symbol losing-month floor (informational)
7. number_of_trials (threshold grid size)

Expected improvement:
Mean train1_net_pnl > baseline AND initial_sl share down ≥10pp AND ≥50% of
big-winner PnL retained AND pooled losing-month floor strictly below this
name's ungated floor (7/12 on the pooled control — confirm in control cell
before comparing).

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ baseline at every T; OR
(b) every non-thin T removes >50% of baseline big-winner PnL; OR
(c) initial_sl share fails to fall ≥10pp at the best-PnL T; OR
(d) pooled losing-month floor does not improve (stays ≥ baseline floor) at
    every T that otherwise passes (a)–(c); OR
(e) improvement is only from collapsing to <10 trades/series mean.
Do not widen T after seeing results without a new written hypothesis.
Do not declare this falsified because BB_20_25 candle failed, and do not
declare it passed because that name's T=0.70 raised mean PnL.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If a T looks promising, schedule a separate validation run later — do not
tune on it now.

Budget:
T grid fixed before run:
{0.50, 0.60, 0.70, 0.80, 0.90} — max 5 trials.
Control (ungated) + 5 gated cells. Report all cells. Pick at most one T for
any follow-up. The grid shape matches the licensed §8 candle-confirm pattern
used elsewhere; it is not a copy of another name's winning T.
```

decision_if_pass: REFINE (update BB_20_2_EMA200 profile metrics; consider validation)
decision_if_fail: keep CONDITIONAL; mark candle-confirm entry-structure axis closed on this
  name's own trades; next open §8 entry-structure variant (breakout depth / HTF direction)
  with a new written mechanism — still develop-not-abandon on this name; do not FREEZE

## Result

Run: `F006_DATA_CACHE=<main checkout>/data_cache python3 scripts/f006_bb_20_2_entry_candle_confirm.py`
(code at base `89326fc`; artifacts `output/f006_bb_20_2_entry_candle_confirm/`: `grid_freeze.json`
written after control check and before any gated cell, `manifest.json`, `cell_summary.csv`,
`results.csv`, `run.log`, per-cell `raw/` + `blotters/`). Train-1 only; validation/holdout not loaded.
`number_of_trials = 5`; T grid `{0.50, 0.60, 0.70, 0.80, 0.90}` and big winner = baseline trade
net≥29.9 frozen before the gated cells. NO_TRAIL violations 0; matched-trade economics mismatches 0.

**Control reproduction (exact).** 10/10 series replay `output/f006_notrail_monthly_catalog5`
train1_net_pnl + n_trades (max diff 0); matches the abs-ATR control row
(`output/f006_bb_20_2_abs_atr_gate/cell_summary.csv`): mean train1_net_pnl **+95.3217987**,
entry n **756**, entry net **+834.347778**, initial_sl share **0.473545**, big-winner PnL
**1251.654084** (12 trades), pooled losing entry-months **7/12**.

| cell | mean train1 net | entry net | n entry | n/series | initial_sl share | Δ pp | big-win kept (n) | big-win PnL kept | frac kept | losing months | +symbols |
|---|---|---|---|---|---|---|---|---|---|---|---|
| control | 95.321799 | 834.347778 | 756 | 75.6 | 0.473545 | 0.00 | 12 | 1251.654084 | 1.000 | 7 | 3 |
| T=0.50 | 93.307710 | 814.206896 | 743 | 74.3 | 0.475101 | −0.16 | 12 | 1251.654084 | 1.000 | 7 | 3 |
| T=0.60 | **95.771777** | 838.857640 | 720 | 72.0 | 0.468056 | +0.55 | 12 | 1251.654084 | 1.000 | 7 | 4 |
| T=0.70 | 91.296740 | 794.121398 | 677 | 67.7 | 0.475628 | −0.21 | 10 | 1072.154243 | 0.857 | 7 | 3 |
| T=0.80 | 83.762086 | 718.726237 | 605 | 60.5 | 0.502479 | −2.89 | 7 | 960.685388 | 0.768 | 7 | 3 |
| T=0.90 | 53.331293 | 484.339324 | 409 | 40.9 | 0.557457 | −8.39 | 3 | 280.658584 | 0.224 | **6** | 3 |

(Big-winner retention = baseline net≥29.9 trades surviving by symbol/interval/entry_time/direction,
as frozen. Informational only: net≥29.9 PnL inside each gated cohort itself — the abs-ATR card's
measure — is 1251.65 / 1251.65 / 1208.24 / 1161.81 / 761.08 for T=0.50…0.90, because gating frees
the position for later one-shot entries that were blocked in the control.)

Pre-declared falsifiers:
- (a) mean ≤ baseline at every T — **not triggered**: T=0.60 beats control by +0.449978/series (+0.47%).
- (b) every non-thin T removes >50% big-winner PnL — **not triggered** (T=0.50–0.80 keep ≥76.8%).
- (c) initial_sl share fails to fall ≥10pp at the best-PnL T — **TRIGGERED**: best-PnL T=0.60
  drops initial_sl by only 0.55pp (47.35% → 46.81%). No T drops it at all beyond 0.55pp; T≥0.70
  *raises* it (up to +8.39pp at T=0.90).
- (d) floor does not improve at every T that otherwise passes (a)–(c) — vacuous (no T passes (a)–(c));
  pooled floor stays 7/12 at T=0.50–0.80.
- (e) improvement only from <10 trades/series — **not triggered** (T=0.60 at 72.0/series).

**Outcome vs falsifiers: FALSIFIED (c).** 0/5 cells pass all checks. The mechanism's predicted
effect (strong-close pierces stop out less) is absent on this name: initial_sl share is flat or
rising as T tightens.

**Flag (not buried):** T=0.90 is the only cell that lowers the pooled losing-month floor (7 → 6/12)
and it is not thin (40.9 trades/series), but it keeps only 22.4% of the frozen baseline big-winner
PnL (60.8% on the informational in-cohort measure), cuts mean train1 net to 53.33 (−44%), and raises
initial_sl share +8.39pp. It fails (a)-per-cell, the frozen 50% retention check, and (c); it is not
an exception under the pre-registered definition.

## Decision

**FALSIFIED (c).** Checked 2026-10-03 ~14:36 Europe/Warsaw against
`output/f006_bb_20_2_entry_candle_confirm/cell_summary.csv` on the FF-merged
tip `88b0ee3` (review PASS
`2026-10-03-f006-bb202-entry-candle-confirm--2b310688`, FF from `89326fc`).
Result numbers match the artifact after ordinary rounding. Control is exact:
mean train1_net_pnl +95.3217987, entry n 756, entry net +834.347778,
initial_sl share 0.473545, big-winner PnL 1251.654084 (12 trades), pooled
losing entry-months 7/12.

(a) does not fire: T=0.60 mean 95.7717772 is +0.449978/series above control.
(b) does not fire: non-thin T=0.50–0.80 keep ≥76.8% of frozen big-winner PnL.
**(c) FIRED** at the best-PnL T: T=0.60 initial_sl share 0.468056, drop
0.548942pp (required ≥10pp). No T drops the share by ≥10pp; T≥0.70 raises it.
(d) is vacuous (no T passes (a)–(c)); floor stays 7/12 at T=0.50–0.80.
(e) does not fire (T=0.60 is 72.0 trades/series). `number_of_trials = 5`.
0/5 cells pass. T=0.90 lowers the floor to 6/12 but fails (a), the 50%
big-winner retention check (22.4% kept), and (c); it is not an exception.

Per `decision_if_fail`: close the candle close-strength axis on
`BB_20_2_EMA200` own trades. Do not retune T. Stay **CONDITIONAL**. Do not
FREEZE: breakout depth, HTF direction, and liquidity are still open on this
name. `BB_20_25_EMA200` FREEZE and its candle FALSIFIED (c) at `e70161d` do
not transfer. Do not jump to `EMA_50_200` or `EMA3_13_50_200`. Next = one
new written §8 breakout-depth hypothesis on this name's own Train-1 trades
(profile order: candle, then breakout depth, then HTF; liquidity after that).
Not a copy of `BB_20_25_EMA200` depth results and not that name's +82.90
control.
