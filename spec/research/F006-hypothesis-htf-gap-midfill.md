# F006 — HTF FVG magnet with midfill continuation (H-HTF-GAP-MIDFILL-01)

> This pre-registration, including the frozen catalog names and numeric thresholds below, is
> written before the signal module, experiment script, or Train-1 run. Train-1 only:
> `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`, with the protocol warm-up beginning
> `2024-01-26T00:00:00Z`. Validation and holdout data must not be loaded or inspected.

## Observation

An unfinished higher-timeframe fair-value gap (FVG) can be a price magnet. The proposed
trade is not a sweep/fade: after price first returns to the FVG midpoint, it requires a
continuation/rejection close in the causal HTF direction. This is distinct from `LSWEEP`
(wick at a swing), `H-LIQ-RANGE-EQH-01` (equal-level reclaim fade), and
`H-MULTI-TF-PA-01` (prior-N break/pin): the open FVG and its midfill state are the entry
object. It uses no session, ORB, prior-day high/low, VWAP, regime-switch, or Zaorski rule.

Source hypothesis: public Sube Trading Polska chart narration, harvested 2026-09-29;
URLs: https://www.youtube.com/watch?v=e--U4sbXC6Q and
https://www.youtube.com/watch?v=PpQSH-jJbUQ. This is an OHLCV-only test, not a claim that
video commentary establishes an edge.

## Frozen mechanism and thresholds

Input timestamps are UTC bar opens. Construct **causal, non-overlapping UTC epoch blocks**
from the input series: four 60-minute bars form one 4-hour HTF block; three 240-minute bars
form one 12-hour HTF block. A block becomes observable only after its final input bar closes;
no partial block contributes to an HTF candle. Aggregate OHLC as first open, max high, min
low, final close.

On completed HTF candles `c1,c2,c3`, create an FVG at completion of `c3`:

- Bull gap: `c3.low > c1.high`; `gap_bot=c1.high`, `gap_top=c3.low`, direction `+1`.
- Bear gap: `c3.high < c1.low`; `gap_bot=c3.high`, `gap_top=c1.low`, direction `-1`.
- `mid = 0.5 * (gap_top + gap_bot)`. A gap is fully filled and permanently inactive when a
  later input bar has `low <= gap_bot` (bull) or `high >= gap_top` (bear). The creation bar
  cannot trigger; evaluation begins on later input bars.

The causal HTF bias at an input bar is `+1` if the latest completed HTF close exceeds the
close **3 completed HTF blocks** earlier, `-1` if it is below, and `0` otherwise. A gap may
trigger only when its own direction equals this current bias.

For each gap ID, evaluate its first later bar whose `[low, high]` touches `mid`; that touch
**consumes the gap ID even when the current bias is opposite or zero**. If it also fully fills
the gap, or its current bias is not the gap direction, retire it without a signal and never
reconsider a later touch after a bias flip. Otherwise start its single pending midfill state.
A bull continuation close is `close > open`; a bear continuation close is `close < open`.
On the permitted touching bar and the following `R_MAX - 1` input bars, emit the gap direction
on the first continuation close. Independently, on the touching bar, emit the gap direction
for a far-side reject when the wick crossed mid and close returned toward bias: bull
`low <= mid and close > mid`; bear `high >= mid and close < mid`. A gap is one-shot: a
signal, expiry, full fill, or first touch under a non-permitting bias retires it. When more
than one gap qualifies on a bar, use only the most recently created gap; all other qualifying
gaps remain unconsumed. The engine fills at the next bar open; the shared harness applies its
one-shot entry mask and frozen `NO_TRAIL` geometry.

Frozen catalog grid (three names; no tuning after results):

| Name | `R_MAX` input bars | HTF blocks | Bias lookback |
| --- | ---: | --- | ---: |
| `HTF_FVG_MID_R1` | 1 | 4h on 60m; 12h on 240m | 3 |
| `HTF_FVG_MID_R2` | 2 | 4h on 60m; 12h on 240m | 3 |
| `HTF_FVG_MID_R3` | 3 | 4h on 60m; 12h on 240m | 3 |

Strict comparisons above, midpoint factor `0.5`, block sizes `4`/`3`, and this three-name
`R_MAX={1,2,3}` grid are all numeric thresholds for this slice. No calendar-month regime
bit, volume, session clock, target, trailing stop, or additional filter is permitted.

## Hypotheses and falsification

**H1.** At least one frozen name has mean Train-1 net PnL greater than zero over the shared
10-series pool under the shared harness’s `NO_TRAIL` geometry.

**H2.** Conditional on H1, at least one H1-clearing name has a series that passes the shared
monthly promotion checklist (12 valid months, each non-negative, Train-1 net PnL non-negative,
DD at most 50%, and trades present).

H1 is falsified if no name has positive pooled mean net PnL. H2 is falsified if no H1-clearing
name has a monthly-clean series; if H1 fails it is not applicable. The family is also rejected
as too sparse if its average trades per candidate series is below 10. It fails the mechanism
claim if results are identical to a plain HTF prior-N break or if prefix/future-perturbation
checks reveal FVG/block lookahead. `DONCHIAN_55` is the required shared-harness control, not a
candidate.

## Method

1. Add an isolated signal module with pure `compute_htf_fvg_midfill_signal` and
   `catalog_entries`; runtime-register only through `run_family` (do not edit `strategy.py`).
2. Add formula/causality tests for block completion, FVG creation/fill, both directions,
   one-shot midfill, expiry, and future perturbation.
3. Run one script calling `scripts/f006_family_runner.py` / `run_family` with the three frozen
   names and save Train-1 evidence under `output/f006_htf_gap_midfill/`.
4. Record the result and stop. Do not open Validation/Holdout, merge, or retune.

## Run_id

`output/f006_htf_gap_midfill/summary/manifest.json` — frozen 10-series Train-1 run.

## Result

The shared `DONCHIAN_55` control reproduced 10/10 rows with zero mismatches; all 40
candidate/control runs had zero trailing exits and zero one-shot violations. H1 passed for
all frozen names using **Train-1-only** `train1_net_pnl`: R1 mean `$26.7072` (358 trades),
R2 `$23.7520` (397), and R3 `$23.8136` (401), respectively 35.8/39.7/40.1 trades per
candidate series, so sparsity did not falsify the family. These corrected figures also retire
a gap on its first midpoint touch under opposite bias, rather than letting a later bias flip
reuse it. The earlier warm-up-inclusive H1 figures were superseded when the shared harness
was corrected to gate only on Train-1 PnL. H2 is falsified: zero of 30 candidate series was
monthly-clean; the best negative-month count was five, despite all 12 months being valid.

## Decision

Stop this slice at the pre-registered grid. The FVG midfill mechanism clears the aggregate
Train-1 bar but does not meet the monthly criterion; no Validation/Holdout data was opened and
no parameter or mechanism retune follows from this result.

## Tests

`python3 -m pytest -q tests/test_htf_gap_midfill.py tests/test_signal_family_contract.py`
passed: 58 passed after the shared H1 gate correction. The formula tests cover causal block completion, both FVG directions,
full-fill cancellation, R_MAX expiry, first-touch consumption under opposite bias, one-shot state, and prefix/future perturbation.
`python3 scripts/f006_htf_gap_midfill_experiment.py` completed with the control and H1/H2
results above using only the ten bounded Train-1 cache CSVs symlinked from the main checkout.
