# F011 · Forced-flow diagnostics (T4, non-trading)

## Outcome

One final diagnostic study on existing 5m data (no paid feeds) after T3 found no directional
edge (0/22 primary, 0/132 grid cells vs 34 bps). Answer three pre-registered questions: (1) do
forced-flow state entries produce abnormal magnitude / vol / excursion vs a matched baseline;
(2) which pre-event features separate cascade continuation from reversal; (3) can CASCADE entry
be predicted from causal pre-cascade features with meaningful PR-AUC lift. Spec:
`spec/research/F011-forced-flow-lab.md` §9b. Code under `forced_flow_lab/`. Owner order
2026-10-06: keep the liquidation collector running; do not acquire paid data.

## Scope

### Inputs

- `output/f011_forced_flow/frame_5m/<SYMBOL>.csv.gz` and
  `output/f011_forced_flow/states/<SYMBOL>.csv.gz` from **main**, Train-1 only, BTCUSDT +
  ETHUSDT. Validation / holdout untouched.
- Reuse the frozen T2 thresholds in `output/f011_forced_flow/states/manifest.json`. **No new
  threshold tuning.**
- Event = **state entry** (same definition as T3). Long and short are mirrored by sign and
  pooled; also report the per-side split (ETH short cascades n≈4 is small — report it, do not
  invent a new rule).
- Event classes: **CROWDING, STRESS, DELEVERAGING, CASCADE, EXHAUSTION**.
  **DELEVERAGING** = union of STRESS and CASCADE entries (OI-declining forced states). State
  this explicitly; no new labelling rule.

### Horizons

`+5m, +15m, +30m, +1h, +4h`.

### Matched baseline (every metric in Test 1)

For each event at time t on symbol S:
- Non-event bars of the same symbol and same hour-of-day.
- Same trailing 24h realized-vol decile at t.
- Exclude ±4h around any event.
- Sample about **20 baselines per event**, seeded (record the seed in the manifest / report).

Cost reference stays **34 bps round trip** — used only as context in Test 1 (whether event
magnitude dwarfs costs), not as a pass gate here.

---

### Test 1 — Distribution and volatility response

Per class × horizon × symbol (and per half of Train-1):
- Signed return: mean, median, quantiles 5/25/50/75/95.
- Absolute return: mean and median.
- Forward realized vol.
- MFE, MAE, total excursion (MFE+MAE), and MFE/(MFE+MAE).
- Each compared event vs matched baseline: ratio, difference, bootstrap 95% CI (**2000**
  resamples, block or event-level), per symbol and per half of Train-1.

**POSITIVE** only if, for some class and horizon, mean absolute return **or** forward realized
vol exceeds baseline by a ratio ≥ **1.25** with the CI excluding 1, on **BOTH** symbols **AND**
both halves of Train-1.

---

### Test 2 — Cascade continuation vs reversal

- Outcome: sign of the **+1h** forward return in the cascade direction (>0 = continuation).
  Robustness check at **+30m**.
- Compare pre-event / current distributions of these features between continuation and
  reversal groups:
  - prior OI build-up (24h ΔOI%)
  - `oi_zscore`
  - speed of OI decline (`delta_oi_pct` over the last 3 bars, ATR-normalised)
  - `funding_rate` and `funding_zscore`
  - `long_short_ratio` and `long_account_share`
  - CVD and taker imbalance (sum of `ofi` / `delta_cvd` over the last 3 and 12 bars)
  - initial price shock (`atr_normalized_return` of the entry bar and of the last 3 bars)
  - realized vol and its regime decile
  - BTC regime (BTC 24h and 7d return sign; BTC above/below its 200-bar EMA on the
    1h-resampled series)
  - hour-of-day bucket (Asia / EU / US) and weekday
  - cross-asset confirmation (whether the other symbol is in STRESS/CASCADE within ±15m)
- Report effect sizes: **Cliff's delta** with bootstrap CI for continuous features; **risk
  difference** for categorical. Include group n.
- **No threshold search.** The effect sizes themselves are the output.
- **POSITIVE** only if at least one feature has |Cliff's delta| ≥ **0.33** (or a risk
  difference ≥ **15 pp**) with the same sign on **BOTH** symbols **AND** both halves, with CIs
  excluding 0. **Report how many features were tested.**

---

### Test 3 — Pre-cascade prediction (event prediction, not direction)

- Target `y_h = 1` if a CASCADE entry occurs within the next `h ∈ {15m, 30m, 60m}`, for bars
  **not** already in STRESS-after-OI-collapse or CASCADE.
- Features use only information available at the close of bar t: CROWDING/STRESS flags plus
  the continuous state variables (`oi_zscore`, `funding_zscore`, ΔOI speed, taker imbalance,
  realized vol, L/S ratio).
- Models:
  - (a) Rule baselines: `P(cascade | CROWDING)` and `P(cascade | STRESS)`.
  - (b) L2 logistic regression on standardized features, fixed `C=1.0`, **no tuning**.
- Time-ordered split: fit on the first **60%** of Train-1; evaluate on the last **40%**.
  Report both.
- Report: base rate, precision, recall (rule baselines; logistic at its top 1% / 5% score
  cutoffs), PR-AUC, lift = PR-AUC / base rate, plus precision/base rate at the cutoffs.
- **POSITIVE** only if out-of-sample PR-AUC lift ≥ **2.0** at some horizon on **BOTH**
  symbols, with at least **20** positive events in the test period. Flag if positives are
  fewer.

---

### Overall reporting

- Report the **total number of tests and cells**.
- If all three tests are **NEGATIVE**, the program-note recommendation is to **ARCHIVE** the
  forced-flow strategy — state that explicitly in `### Result`.
- Fill §9b `### Result`; leave `### Decision` empty for the coordinator.
- Outputs → `output/f011_forced_flow/diagnostics/` (gzipped / kept small).
- `python3 -m pytest -q` stays green, including a **causality test** that Test-3 features use
  only bars ≤ t.

## Out of scope

- Any trade, position, PnL curve, or Stage-2 strategy.
- New threshold tuning or widening the T2 grid.
- Paid data acquisition; liquidation/order-book feeds beyond what already exists (liq columns
  remain null on Train-1).
- Touching validation / holdout.
- Stopping or respawning the live liquidation collector.

## Acceptance

- `output/f011_forced_flow/diagnostics/` holds Test 1–3 tables, a cell/test count, and a
  one-line POSITIVE/NEGATIVE per test; §9b `### Result` filled; `### Decision` left empty.
- Matched baseline, both-symbols + both-halves gates, and the three POSITIVE criteria above
  are applied as written.
- Causality test for Test-3 features passes; pytest green.

## Notes

T3 found no directional edge. This ticket asks whether the same states still carry *any*
measurable distributional / predictive content on free data. A clean triple-NEGATIVE is a
valid kept result and licenses an ARCHIVE recommendation.
