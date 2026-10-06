# F011 · Forced-flow state machine (T2, non-trading)

## Outcome

Each bar of the **5m** T1 frame is assigned exactly one causal participant-stress state, so the
event study (T3) can condition forward returns on state. Deterministic labelling from frozen
rules — no trading, no forward-looking information, no outcome fitting. Spec:
`spec/research/F011-forced-flow-lab.md` §3,§6 (as amended 2026-10-06). Code under
`forced_flow_lab/`.

## Scope

- **Input:** `output/f011_forced_flow/frame_5m/<SYMBOL>.csv.gz` for BTCUSDT and ETHUSDT
  (Train-1 only). Skip `is_warmup` rows. The hourly frame
  (`output/f011_forced_flow/frame/`) is a coarse baseline only — **never** the labelling input.
- Assign one of:
  `NORMAL, LONG_CROWDING, SHORT_CROWDING, LONG_STRESS, SHORT_STRESS,
  LONG_LIQUIDATION_CASCADE, SHORT_LIQUIDATION_CASCADE, LONG_EXHAUSTION, SHORT_EXHAUSTION`.
- Frozen rule sketch (record every exact threshold and lookback in the manifest BEFORE any
  labelling run; crowding ≠ timing; no tuning toward a target state distribution):
  - **CROWDING** = Forced Positioning Score high (`oi_zscore` + `funding_zscore`, long/short by
    sign). Funding updates only every 8h, so it is a *slow* component. `long_short_ratio` may
    serve as a secondary crowding confirmation.
  - **STRESS** = crowded side + adverse `atr_normalized_return` + `delta_oi_pct` < 0 +
    aggressive flow against the crowd (`ofi` / `delta_cvd`).
  - **CASCADE** = stress + OI collapsing per ATR (`fuel` high) + return accelerating against
    the crowd.
  - **EXHAUSTION** = within or just after a cascade, OI deceleration (`oi_acceleration`) +
    collapsing price impact (`sell_impact` for longs, `buy_impact` for shorts) while adverse
    taker flow persists.
  - else **NORMAL**.
- **Primary venue is Bybit.** The `bn_` layer is a robustness cross-check only: keep it as
  separate features, never merge into the Bybit core. OI direction agrees across venues only
  52–60% of the time — do not treat disagreement as noise to average away.
- **Manifest first:** write every exact threshold and lookback, plus a small frozen robustness
  grid of **at most 2 values per key threshold**, into
  `output/f011_forced_flow/states/manifest.json`. That file must be **committed in its own
  commit before any labelling run is executed**. No tuning toward a target state distribution.
- Emit `output/f011_forced_flow/states/<SYMBOL>.csv.gz` (gzipped, kept small): keep only the
  state plus its triggering values — **not** a copy of the frame.
- Report state counts and the **median duration** of each state per symbol. A state that almost
  never fires is a finding and must be reported, not tuned away.
- Unit test: states are a pure function of past/current bars (causal), and every labelled bar
  gets exactly one state. The causality prefix grid must be long enough to reach the
  `oi_zscore` and `funding_zscore` columns past warmup (warmup is 2,016 bars; use a grid such
  as ≥3,000 bars with k past that, not a 2,016/k≤2000 grid that leaves z-scores always null).

## Out of scope

- Any trade, position, PnL, or forward return (that is T3).
- Tuning thresholds to produce a desired state distribution; use frozen, documented values.
- Using liquidation/order-book data (absent — `liquidation_*_vol` are all null) — use the
  OI/price fuel proxy per §3 and the 5m taker-flow proxies (`ofi`, `delta_cvd`, impacts).
- Merging Bybit and Binance into a single feature; the `bn_` layer stays separate.

## Acceptance

- `output/f011_forced_flow/states/{BTCUSDT,ETHUSDT}.csv.gz` label every non-warmup bar with one
  state; outputs are gzipped and contain state + triggering values only.
- `output/f011_forced_flow/states/manifest.json` lists every frozen threshold/lookback and the
  ≤2-value robustness grid, and was committed **before** the labelling run.
- State-count + median-duration summary per symbol is reported (rare states = findings).
- Causality + single-label tests pass with a prefix grid that exercises z-score columns past
  warmup; `python3 -m pytest -q` stays green (hourly-cache-dependent tests may skip when those
  git-ignored caches are absent).

## Notes

The states must be defensible economically, not chosen to look good later. If a state is almost
never triggered on BTC/ETH, report that — it is information about the OI/taker-flow proxy's
limits. Coordinator decision 2026-10-06: T2 runs on the 5m frame (merged at cc9ea1b), not hourly.
