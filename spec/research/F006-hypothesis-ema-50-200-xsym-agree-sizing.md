# F006 — H-EMA-50-200-XSYM-AGREE-SIZING-01 (pre-registered)

> Pre-registered **before** implementing or running the sized arm.
> `H-EMA-50-200-ABS-ATR-ENTRY-GATE-01` is **FALSIFIED (a)+(c)** on this name's
> own trades (`80e7fa6`). Entry-vol / abs-ATR stays closed. Do not retune T.
> `BB_20_2_EMA200` is **FREEZE** after its own liquidity result (`776e167`).
> Its xsym sizing Train-1 pass (`1774a8a`) and Val-4 fail (`139ed3d`) close
> that formula on **that name only**. `BB_20_25_EMA200` Train-1 pass
> (`1c9ff7e`) and Val-1 fail (`89e936a`) likewise close that name only. They
> are not this test. Do not copy either name's control mean (+95.3217987 or
> +82.900262), sized means, floor moves, mult gaps, or stake_cv onto this
> card as an expected result. Position sizing has never been run on
> `EMA_50_200` under protocol.

experiment_id: H-EMA-50-200-XSYM-AGREE-SIZING-01
date: 2026-10-03
base_strategy: EMA_50_200 (NO_TRAIL, max_sl_pct=0.03, one-shot entry, signal_reverse exit)

```text
Observation:
EMA_50_200 stays CONDITIONAL after H-EMA-50-200-ABS-ATR-ENTRY-GATE-01
FALSIFIED (a)+(c) on own trades (tip 80e7fa6). Control mean +72.6693115/series
reproduced from this experiment's artifacts
(output/f006_ema_50_200_abs_atr_gate/; sum +726.693115, 10 series, 7/10
positive; entry cohort n=330, +587.3851786486205, initial_sl 213/330,
floor 7/12, big winners 5 / +843.7639016181568). Best abs-ATR cell t_2_0
mean +64.4604139, initial_sl drop 6.73pp. Cells that cut initial_sl ≥10pp
kept 3.6–44.0% of this name's big-winner PnL and sat at +0.66…+34.75/series.
Exit, long-only, and breadth already ran on this name's own series and did
not clear the monthly floor. The ungated book is still aggregate-positive.
§8 allows a sizing test only after the signal itself has an edge; that
precondition holds. It does not license masking a negative-EV signal.

Problem:
Monthly regularity is unresolved (abs-ATR control entry-month floor 7/12;
0/10 series clear §7). An ATR-magnitude entry gate removes the same
signal_reverse runners that carry the aggregate PnL. This name has no
own-trades sizing result. A stake rule that keeps every trade can reweight
entries without the sample-starvation that boolean gates use.

Mechanism:
Basket EMA 50/200 crosses that coincide with the same nonzero direction on
peer symbols are more likely to be the regime-aligned runners;
idiosyncratic single-symbol fires are more likely to be initial_sl deaths.
Because strategy_signal_series is a persistent directional state per
(symbol, interval), the count of the other four basket symbols whose
EMA_50_200 signal matches the traded symbol's nonzero direction on the
closed bar is a causal, bar-aligned agreement score. It is not an ATR
threshold and not a fitted cutoff from another name's PnL. Scaling stake by
that score keeps n_trades invariant and raises the relative weight of
consensus entries.

The stake band is structural, rewritten for this name, not a threshold
mined on BB_20_2 or BB_20_25:
n_agree ∈ {0,1,2,3,4} maps linearly onto [0.5, 2.0],
mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)
because (2.0 − 0.5) / 4 = 0.375. That arithmetic is the structural band.
Using it here is the own-trades test of this mechanism on EMA_50_200. It is
not a claim that another name's Train-1 pass or validation fail already
answered this name.

Hypothesis:
Replacing uniform stake=100 with stake=100*mult(n_agree), where n_agree is
the number of the other 4 basket symbols whose EMA_50_200 persistent signal
equals the traded symbol's nonzero direction on the same interval, will
raise mean Train-1 net PnL versus the uniform-stake control AND strictly
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
scripts/f006_bb_20_2_xsym_agree_sizing.py (or the BB_20_25 sibling); point
the signal name at EMA_50_200.

Freeze this single formula before the run. No post-hoc retuning.
number_of_trials = 1 (one sized formula). Report the uniform control and
this one sized arm only.

Baseline:
Uniform stake=100 EMA_50_200 NO_TRAIL on the frozen 5-symbol × 2-interval
Train-1 basket. The control arm (stake_series=None) must reproduce all 10
train1_net_pnl rows in
output/f006_notrail_monthly_catalog5/summary/results.csv for strategy
EMA_50_200 (mean **+72.6693115**/series, sum **+726.693115**) and match
n_trades, before the sized arm is trusted. That figure is also the
reproduced control from output/f006_ema_50_200_abs_atr_gate/ — use it as
this name's baseline going forward. Do not match +95.3217987. Do not match
+82.900262. Use the Train-1 caches the abs-ATR control just matched
(checksums in output/f006_ema_50_200_abs_atr_gate/grid_freeze.json,
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
   abs-ATR freeze observed 5 trades / +843.7639016181568; confirm, do not
   import another name's set.
7. number_of_trials = 1

Expected improvement:
Mean train1_net_pnl > this name's uniform control (+72.6693115) AND pooled
losing-month floor strictly below this name's control floor AND
mean(mult|winner) > mean(mult|loser), with n_trades invariant and
stake_cv > 0.05.

Falsification condition (any one ⇒ FALSIFIED):
(a) mean train1_net_pnl ≤ this name's uniform baseline; OR
(b) pooled losing-month floor does not improve (stays ≥ this name's
    control floor); OR
(c) mean(mult|winner) − mean(mult|loser) ≤ 0; OR
(d) n_trades invariant broken on any series; OR
(e) stake_cv ≤ 0.05 (degenerate near-uniform weights).
Do not change the mult formula after seeing results without a new written
hypothesis. Do not declare this falsified because BB_20_2 Val-4 or
BB_20_25 Val-1 failed. Do not declare it passed because either name's
Train-1 passed.

Data split:
Train-1 only (2024-03-01 ≤ entry < 2025-03-01 UTC). No validation/holdout.
If the sized arm passes, a separate validation run is a later hypothesis.
Do not open it in this run.

Budget:
One pre-registered formula. Control + sized arm only. Report both.
No grid. No second mechanism.
```

decision_if_pass: REFINE (update EMA_50_200 profile metrics; sizing stays
  open until a separate validation; do not open holdout in this run; do not
  FREEZE)
decision_if_fail: this xsym-agree formula is closed on EMA_50_200 own
  trades. Worker must not set FREEZE and must not change profile status.
  The name stays CONDITIONAL. The following open axis is candle confirm
  (entry structure). Do not retune 0.5 / 0.375 / 2.0 inside this run. Do not
  treat the result as evidence about EMA3_13_50_200. Do not start
  EMA3_13_50_200. Do not reopen abs-ATR.

## Result

Run: `scripts/f006_ema_50_200_xsym_agree_sizing.py` at `5af9b88` (first run at
`67af347` with the script uncommitted; the rerun matched it apart from timestamps, SHA and timings), cache = main checkout `data_cache`
Train-1 files `*_20240126T000000Z_20250301T000000Z.csv` only (request ends at
2025-03-01; no `*_20260901*` / `*_20200325*` loaded). All 10 checksums equal
`output/f006_ema_50_200_abs_atr_gate/grid_freeze.json`
(`checksums_match_abs_atr_grid_freeze: true`). Artifacts:
`output/f006_ema_50_200_xsym_agree_sizing/` (`summary/{results.csv,
cell_summary.json, manifest.json, run.log, control_train1_entry_blotter.csv,
sized_train1_entry_blotter.csv}`, `raw/<symbol>_<interval>.json`).
number_of_trials = 1; formula frozen `clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`,
n_agree counted on EMA_50_200's own persistent signal across the other 4 symbols.

Causal alignment: closed-bar multiplier is `.shift(1)` onto the engine fill bar;
the first bar is `fillna(100.0)`. Independent re-check over the sized blotter:
330/330 Train-1-entry stakes equal the multiplier of the bar before the fill bar;
21/330 would differ if the fill bar's own close were read, so the check
discriminates.

Control match (gate before scoring): 10/10 rows of
`output/f006_notrail_monthly_catalog5/summary/results.csv` (EMA_50_200), max abs
`train1_net_pnl` diff **0.0**, `n_trades` all equal. Replayed mean
**+72.6693115** (sum +726.693115).

| metric | control (stake 100) | sized |
|---|---|---|
| mean train1_net_pnl / series | +72.669312 | **+126.744211** |
| series positive | 7/10 | 7/10 |
| closed trades (all) | 364 | 364 |
| Train-1-entry trades | 330 | 330 |
| Train-1-entry net / per trade | +587.385179 / +1.779955 | +1034.000818 / +3.133336 |
| pooled losing entry-months | **7/12** | **7/12** |
| mean mult winners / losers | — | 1.365809 / 1.232824 |
| winner − loser mult gap | — | **+0.132984** |
| pooled stake_cv (all 10 series > 0.05) | — | 0.413344 (yes; per-series 0.314–0.595) |
| big winners net≥29.9 (count / net) | 5 / +843.763902 | 10 / +1477.682389 |
| sized net on control's 5 big-winner keys | — | +1287.249988 |

Control entry-month floor confirmed in this run: 7/12 (2024-03, -04, -05, -08,
-09, -12, 2025-01). Sized arm loses in the same 7 months, each slightly deeper
except 2024-09 (−28.73 → −25.87). Big-winner set recomputed on this run's
uniform blotter: 5 trades / +843.763902, same as the abs-ATR freeze. 2024-11
carries most of the aggregate (+816.81 control → +1308.88 sized). Per series,
sized beats control on 8/10 and loses on ETHUSDT/240 (−39.79 → −45.97) and
DOGEUSDT/60 (+198.46 → +96.90). BTCUSDT/240 and BTCUSDT/60 are still negative.

Falsifiers:
- (a) mean ≤ baseline: **not fired** (+126.744211 > +72.669312).
- (b) pooled losing-month floor not improved: **FIRED** (7 ≥ 7).
- (c) winner − loser mult gap ≤ 0: **not fired** (+0.132984).
- (d) n_trades invariant broken: **not fired** (10/10 series, total and
  Train-1-entry keys identical).
- (e) stake_cv ≤ 0.05: **not fired** (0.413344; every series > 0.05).

Verdict: **FALSIFIED (b)** on EMA_50_200 own trades. Sizing raises mean and
pooled net and skews stake toward winners, but it doesn't reduce the losing-month
floor. The gain is concentrated in 2024-11 and the
big-winner set. Profile status untouched (CONDITIONAL). Decision left to the coordinator.

## Decision

**FALSIFIED (b).** Checked 2026-10-03 ~17:25 Europe/Warsaw against
`output/f006_ema_50_200_xsym_agree_sizing/summary/cell_summary.json` on the
FF-merged tip `48d03b0` (parent `5af9b88`; review PASS
`2026-10-03-f006-ema50200-xsym-agree-sizing--f8969a7a`). The Result table matches
that artifact after ordinary rounding. Control replay max abs train1 diff is
0.0. The manifest records one fired falsifier: pooled losing-month floor did
not improve (7 >= 7).

This is not the `BB_20_2_EMA200` Train-1 sizing verdict. On that card (b) did
not fire (floor 7/12 to 6/12), so decision_if_pass was REFINE and protocol
§3.10 / §11 required validation before another axis (tip `1774a8a`, Decision
**REFINE / NOT FALSIFIED**). Here (b) fires.

Pre-declared checks (number_of_trials = 1, formula frozen
`mult = clip(0.5 + 0.375 * n_agree, 0.5, 2.0)`, fill bar uses the prior
closed bar):

- control mean **+72.6693115** (replay max abs diff 0.0, sum +726.693115,
  7/10 positive), Train-1-entry n=330, entry-net **+587.385179**, pooled
  entry-month floor **7/12**
- sized mean **+126.744211** (delta **+54.0748995**/series vs +72.6693115),
  7/10 positive, entry-net **+1034.000818** (+3.133336/trade), floor **7/12**
- pooled mean(mult|winner) minus mean(mult|loser) **+0.132984** (1.365809 vs
  1.232824), stake_cv **0.413344** (every series > 0.05)
- n_trades invariant held (364 closed and 330 Train-1-entry keys)
- big winners (informational, net>=29.9): control 5 / +843.763902; sized
  10 / +1477.682389; sized net on the control's 5 keys +1287.249988
- 2024-11 entry-month net +816.808826 to +1308.876889 (concentration; not
  an extra falsifier)

(a) does not fire: +126.744211 > +72.6693115. (b) fires: the floor stays
7/12 (7 >= 7). The same seven entry-months lose (2024-03, -04, -05, -08,
-09, -12, 2025-01). (c) does not fire: gap +0.132984. (d) does not fire.
(e) does not fire: stake_cv 0.413344.

Applied sentence, from this card: "(b) pooled losing-month floor does not
improve (stays >= this name's control floor)". A flat 7/12 is that sentence,
not a near-miss. decision_if_fail closes this xsym-agree formula on
`EMA_50_200` own trades and names candle confirm as the following open axis.
The data-split sentence opens a later validation hypothesis only "If the
sized arm passes". It did not pass, so no Val-1 is written. Protocol §3.10
and the BB_20_2 Decision's "do not abandon a passed sizing arm" apply when
the pre-registered checks do not fire. §7 develop-not-abandon keeps this
name in the loop (status **CONDITIONAL**, next licensed axis) and does not
keep a failed formula open.

**Strategy status:** **CONDITIONAL**. Do not FREEZE. This xsym-agree formula
is closed on this name. Entry-vol stays FALSIFIED (a)+(c) (`80e7fa6` /
Decision `67af347`). Exit, long-only, and breadth stay closed. Candle
confirm, breakout structure, HTF direction, and liquidity have not been
pre-registered here. Do not start `EMA3_13_50_200`. Do not retune
0.5 / 0.375 / 2.0. Holdout stays closed. Do not copy +95.3217987 or
+82.900262. Do not treat `1774a8a` or `139ed3d` as this result.

**reason:** falsifier (b). Sizing raises mean Train-1 net and skews stake
toward winners, but the pooled losing-month floor does not improve.

**next_action:** one candle-confirm entry gate on this name only,
`H-EMA-50-200-ENTRY-CANDLE-CONFIRM-01`. Not a Val-1 of this formula. Not an
abs-ATR retune. Baseline remains the reproduced control **+72.6693115**.
