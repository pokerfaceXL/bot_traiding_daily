# F011 — Forced-Flow Lab (participant modelling, non-trading first)

> The new direction (spec/vision.md). We do not predict price; we model market participants and
> the situations in which they lose the freedom to choose. The question every component answers:
> **"who will be forced to buy or sell if X happens?"** Forced flow (liquidations, stop-runs,
> margin calls, hedging, funding pressure) is mechanical, so more predictable than price. This
> note is the program spec + the first falsifiable, **non-trading** hypotheses. Binding research
> rules stay `spec/COORDINATOR_RESEARCH_PROTOCOL.md`; production stays untouched; new work lives
> in a separate `forced_flow_lab/` namespace, never in the live bot's path.

## 1. The forced participant

| participant | what forces action | action |
| --- | --- | --- |
| leveraged long | price down → margin call / liquidation | sells |
| leveraged short | price up → liquidation | buys |
| market maker | inventory/delta shift | hedges |
| arb trader | spot/perp/futures dislocation | buys one, sells other |
| carry trader | funding/basis shift | unwinds hedge |
| option dealer | delta/gamma shift | buys/sells underlying |
| trend / CTA-like | level break / vol target | changes exposure |
| ETF / fund | inflow/outflow/rebalance | executes flow |

**First target: leveraged longs/shorts** — in crypto they leave the most measurable traces
(open interest, funding, liquidations). The others come later, only if the method proves out.

## 2. We build a market STATE, not a BUY/SELL signal

A classic bot sees price +3% + momentum → BUY. We see: *new leveraged longs entered
aggressively* (price +3%, OI +12%, funding strongly positive, perp premium rising, spot volume
flat). That is a different fact — it is **potential energy**: many longs, high leverage, similar
entry prices. If price turns down: stops → sells → liquidations → more sells. The loop
`price move → forced flow → price move → forced flow` is the phenomenon we hunt.

## 3. Key variables are participant-state, not price

- **Forced Positioning Score** (crowding, a *state*, not timing): e.g.
  `FPS_long = z(ΔOI) + z(Funding) + z(PerpPremium) + z(LongCrowding) − z(SpotConfirmation)`.
  FPS_long≈0 normal, ≈2 many longs, ≈4 very crowded. **Crowding ≠ timing — we never short on
  crowding alone** (the classic contrarian failure).
- **ForcedFlow** ≈ normalized `(|ΔOI| / ATR) × Liquidations × OrderFlowImbalance` — the "fuel".
  Two identical −3% candles differ entirely: OI −1% = ordinary selling; OI −18% = the market
  just removed huge leverage. Same candle, opposite microstructure.
- **Derivatives matter more than levels:** `dLiquidations/dt`, `dOI/dt`, `d²Price/dt²` →
  acceleration = cascade, deceleration = exhaustion.
- **Price Impact** = `ΔPrice / ForcedSellVolume`. If a wall of forced selling moves price only
  slightly, someone is absorbing supply — often more valuable than any oscillator.

## 4. The trigger X

WHO = leveraged longs, WHY = liquidation/stop; the missing piece is **X = trigger**. Example:
longs built between 98.5k–101k, stress region ~95k–97k. Price drifts down while **OI stays high
(longs haven't left)**; then at ~97.5k aggressive selling, negative order-flow imbalance, rising
sell volume, **OI collapsing**, liquidation volume rising — that confluence is X.

## 5. Two strategies from one mechanism (GATED — not built yet)

- **A — Liquidation Cascade (SHORT).** Don't catch the start; wait for confirmation (crowded
  longs → trigger → OI collapse → liquidation acceleration) → SHORT, ride the *middle* of the
  cascade (e.g. take −2% out of a −7% move), not the whole thing.
- **B — Liquidation Exhaustion (LONG).** After the cascade, liquidations decelerate and price
  stops making new lows despite continued market sells → the forced sellers are flushed → LONG.

One mechanism, two trades: `cascade → SHORT`, then `exhaustion → LONG`. Both are *gated on a
proven statistical edge* (§8); neither is implemented in this note.

## 6. State machine (the model)

Per observation, a causal feature vector (see §7 data) → one state:
`NORMAL · LONG_CROWDING · SHORT_CROWDING · LONG_STRESS · SHORT_STRESS ·
LONG_LIQUIDATION_CASCADE · SHORT_LIQUIDATION_CASCADE · LONG_EXHAUSTION · SHORT_EXHAUSTION`.
This is a state machine over participant stress, not a trading indicator. The economic story of a
trade is a path: `LONG_CROWDING → LONG_STRESS → CASCADE (SHORT) → EXHAUSTION (LONG)`.

## 7. Data — what we have vs what is owner-gated

**Available now (in cache, within the F002 offline boundary):**
- OHLCV candles (5 symbols, Train-1 span) — price, return, ATR, realized vol, volume.
- **Open interest**, hourly, 5 symbols, 2024-01-26 → 2025-03-01 (`data_cache/open_interest/`) —
  ΔOI, OI z-score, OI acceleration, and the "fuel" `|ΔOI|/ATR`.
- **Funding**, 5 symbols (`data_cache/funding/`) — funding z-score, crowding sign.

**NOT in repo — needs owner-gated acquisition (API, F002 decision):**
- Liquidations (long/short volume) — central to cascade/exhaustion sharpness.
- Perp–spot basis / perp premium (needs spot feed).
- Taker buy/sell split, CVD, order-book imbalance/depth.

**Consequence for sequencing:** the first event study is runnable NOW on OHLCV+OI+funding, using
**OI-collapse-per-ATR** as the forced-deleveraging proxy and `|Δprice|/volume` as a coarse
price-impact proxy. Liquidations/order-flow/basis are the sharpening upgrade and are the main
thing to acquire if Stage 1 shows signal.

## 8. Staged plan (owner's; falsify early, trade late)

- **Stage 0 — data audit.** Done (§7): OHLCV+OI+funding available; liquidations/basis/taker/
  order-book owner-gated. Start with BTCUSDT + ETHUSDT.
- **Stage 1 — non-trading lab + event study.** Build the causal feature frame and state labels;
  answer the two pre-registered questions below. **No trading.** Ticket set: F011 T1–T3.
- **Stage 2 — strategy (gated on a Stage-1 edge).** Pre-register Strategy A then B, backtest in
  our engine with our costs/capital/rules, no look-ahead. Not ticketed until Stage 1 passes.
- **Stage 3 — ML, last.** Only `P(cascade | state)` and `P(exhaustion | cascade)` — never a raw
  BUY/SELL classifier. Gated on Stage 2.

## 9. Pre-registered Stage-1 hypotheses (non-trading event study)

> **Pre-run amendment 2026-10-06 (coordinator decision).** Resolution is **5m** instead of
> hourly. Input states come from `output/f011_forced_flow/frame_5m/` → T2 states (not the
> hourly frame). Horizons: **+5m / +15m / +30m / +60m / +4h** (and **+8h** for EXHAUSTION).
> Cost band: **34 bps round trip** (10 commission + 5 half-spread + 2 slippage per side); an
> edge must beat the baseline by more than this band. Taker flow (`ofi` / `delta_cvd` /
> `buy_impact` / `sell_impact`) is added to the STRESS and EXHAUSTION definitions (see T2
> ticket). Event = state entry, not every bar in the state. Falsification rules otherwise
> stay the same (both symbols; beat baseline by more than the cost band at ≥1 horizon;
> frozen grid, no widening-to-fit). The original hourly text below is **superseded** by this
> amendment and is kept only for the audit trail.

### Original §9 text (superseded 2026-10-06)

> ## 9. Pre-registered Stage-1 hypotheses (non-trading event study)
> 
> Frozen before the run. Train-1 only, BTCUSDT + ETHUSDT (extendable to 5), hourly, causal, no
> look-ahead. These test whether forced-flow *state* carries a forward edge — not a strategy.
> 
> ```text
> H-FORCEDFLOW-CONTINUATION-01 (cascade continuation):
> Observation: crowded-long state (high OI z + positive funding z) followed by a down-trigger with
>   OI collapsing should precede FURTHER down-move (forced selling begets forced selling).
> Test: label bars entering LONG_STRESS/CASCADE (crowding high, return<0, ΔOI<<0 per ATR); measure
>   the distribution of forward signed return at +1h/+4h vs the unconditional baseline for the same
>   symbol/period.
> Falsified unless: conditional mean forward return is negative and its magnitude beats the
>   unconditional baseline at >=1 horizon by more than a realistic cost band, and it holds on both
>   BTC and ETH (not one symbol).
> 
> H-FORCEDFLOW-EXHAUSTION-01 (cascade exhaustion):
> Observation: after a large OI drop during a down-move, continued selling that stops producing
>   proportional price decline (price-impact collapse) marks the end of forced selling.
> Test: among cascade bars, label EXHAUSTION where OI deceleration + price-impact (|Δprice|/volume)
>   falls sharply while sell pressure persists; measure forward signed return at +1h/+4h/+8h vs
>   baseline.
> Falsified unless: conditional mean forward return is positive and beats the unconditional
>   baseline at >=1 horizon by more than a cost band, on both BTC and ETH.
> ```
> 
> Metrics for both: conditional vs unconditional forward-return mean/median, hit rate, dispersion,
> n events, per-symbol split, and robustness to the state-threshold (small frozen grid, no
> widening-to-fit). A clean negative is a valid, kept result — it tells us the OI-only proxy is
> too coarse and that liquidation/order-flow data is required before Stage 2.

### Result (T3, 2026-10-06)

Event study on the 5m T2 states, Train-1 (2024-02-02 → 2025-02-28), BTCUSDT + ETHUSDT. Code
`forced_flow_lab/event_study.py`; tables, verdict and method in `output/f011_forced_flow/event_study/`
(`report.md`, `verdict.json`, `cells.csv`, one CSV per hypothesis).

- **H-FORCEDFLOW-CONTINUATION-01: no edge.** 0 of 10 primary cells, and 0 of 60 incl. the frozen
  grid, beat the baseline by > 34 bps. Signed conditional means are −13.4…+0.1 bps; hit rates are
  0.43–0.46 at every horizon on both symbols. Stress/cascade entries are followed by a small *reversal*,
  not continuation, and it is far below the cost band (largest |excess| 13 bps, ETH +4h, t = −1.8).
- **H-FORCEDFLOW-EXHAUSTION-01: no edge.** 0 of 12 primary cells, and 0 of 72 incl. grid, pass.
  BTC is ≤ +0.4 bps excess at every horizon. ETH is +2…+7 bps up to 60m (n = 41–90, |t| ≤ 1.5), then
  turns negative (−67 bps at +8h, n = 38). It does not hold on both symbols and never nears the band.
- **Cells tested:** 22 primary (5 + 6 horizons × 2 symbols); 132 including the 5 one-at-a-time grid
  variants. Largest excess in any cell: +20.4 bps (exhaustion, ETH, 60m, `stress_return_atr=2.5`, n = 20).
- **Method:** event = state entry (STRESS→CASCADE on one side counts as one episode). Overlap: greedy
  non-overlapping per hypothesis × symbol × horizon (keep only if t ≥ previous kept t + h). Forward return
  is close_t → close_{t+h}, and an event is dropped if its window passes the last labelled bar. Returns
  are signed by the predicted direction. Baseline: unconditional same-symbol forward return, weighted by
  the events' side mix. Pass: signed mean > 0 and excess > 34 bps RT at the same horizon on both symbols.
- **Caveat:** liquidation columns are null across Train-1, so CASCADE/EXHAUSTION rely on an OI/ATR fuel
  proxy plus 5m taker flow. They are not observed forced orders, and there is no order-book depth. This null
  says the OI + taker-flow proxy carries no tradable state edge at 5m. It does not rule out an edge in
  liquidation-driven flow measured directly.

### Decision

_Left for the coordinator._

## 9b. Pre-registered T4 diagnostics (2026-10-06)

Owner order after T3 no-edge (0/22 primary, 0/132 grid vs 34 bps RT): **one final diagnostic
study on existing 5m data; no paid feeds; keep the liquidation collector running.** Frozen
before any T4 run. Train-1 only, BTCUSDT + ETHUSDT; validation/holdout untouched. Reuse frozen
T2 thresholds (`output/f011_forced_flow/states/manifest.json`); no new threshold tuning. Event =
state entry. Long/short mirrored by sign and pooled; also report the per-side split (ETH short
cascades are rare). Event classes: CROWDING, STRESS, **DELEVERAGING** (= union of STRESS and
CASCADE entries — OI-declining forced states; stated explicitly, no new rule), CASCADE,
EXHAUSTION. Horizons: +5m / +15m / +30m / +1h / +4h. Ticket:
`spec/features/active/F011-forced-flow-diagnostics/ticket.md`.

**Matched baseline (Test 1):** non-event bars, same symbol, same hour-of-day, same trailing
24h realized-vol decile at t; exclude ±4h around any event; ~20 baselines per event, seeded.
Cost reference 34 bps RT is context only for Test 1 (does event magnitude dwarf costs).

```text
H-FORCEDFLOW-DIAG-MAGNITUDE-01 (distribution / vol response):
Test: for each class × horizon, compare signed-return distribution (mean/median/q05/q25/q50/
  q75/q95), absolute-return mean/median, forward realized vol, MFE, MAE, MFE+MAE, and
  MFE/(MFE+MAE) — event vs matched baseline (ratio, difference, bootstrap 95% CI, 2000
  resamples, block or event-level), per symbol and per half of Train-1.
POSITIVE only if, for some class and horizon, mean |return| OR forward realized vol exceeds
  baseline by ratio ≥ 1.25 with CI excluding 1, on BOTH symbols AND both halves.

H-FORCEDFLOW-DIAG-CONTINUATION-SPLIT-01 (cascade continuation vs reversal):
Outcome: sign of +1h forward return in the cascade direction (>0 = continuation); robustness
  at +30m.
Features (pre-event / current; no threshold search — effect sizes are the output):
  prior OI build-up (24h ΔOI%); oi_zscore; OI-decline speed (delta_oi_pct last 3 bars,
  ATR-normalised); funding_rate + funding_zscore; long_short_ratio + long_account_share;
  CVD / taker imbalance (sum ofi/delta_cvd over last 3 and 12 bars); initial price shock
  (atr_normalized_return of entry bar and last 3 bars); realized vol + regime decile;
  BTC regime (24h/7d return sign; above/below 200-bar EMA on 1h-resampled BTC);
  hour-of-day bucket (Asia/EU/US) + weekday; cross-asset confirmation (other symbol in
  STRESS/CASCADE within ±15m).
Report: Cliff's delta + bootstrap CI (continuous); risk difference (categorical); group n;
  count of features tested.
POSITIVE only if ≥1 feature has |Cliff's δ| ≥ 0.33 (or risk difference ≥ 15 pp) with the same
  sign on BOTH symbols AND both halves, CIs excluding 0.

H-FORCEDFLOW-DIAG-PRECASCADE-01 (event prediction, not direction):
Target y_h = 1 if a CASCADE entry occurs within next h ∈ {15m, 30m, 60m}, for bars NOT already
  in STRESS-after-OI-collapse or CASCADE.
Features at close of bar t only: CROWDING/STRESS flags + oi_zscore, funding_zscore, ΔOI speed,
  taker imbalance, realized vol, L/S ratio (causal; bars ≤ t).
Models: (a) rule baselines P(cascade|CROWDING), P(cascade|STRESS); (b) L2 logistic regression
  on standardized features, fixed C=1.0, no tuning.
Split: time-ordered fit first 60% of Train-1 / evaluate last 40%; report both.
Metrics: base rate, precision, recall (rules; logistic at top 1%/5% score cutoffs), PR-AUC,
  lift = PR-AUC / base rate, precision/base-rate at cutoffs.
POSITIVE only if OOS PR-AUC lift ≥ 2.0 at some horizon on BOTH symbols, with ≥20 positive
  events in the test period (flag if fewer).
```

Overall: report total number of tests and cells. If all three are NEGATIVE, the program-note
recommendation is to **ARCHIVE** the forced-flow strategy (state that in Result). Worker fills
`### Result` below and leaves `### Decision` empty. Outputs under
`output/f011_forced_flow/diagnostics/`.

### Result

T4 run 2026-10-06 on the frozen T2 states, Train-1 (2024-02-02 → 2025-02-28), BTCUSDT + ETHUSDT. Code
`forced_flow_lab/diagnostics.py`; tables, verdicts, seeds and method in `output/f011_forced_flow/diagnostics/`
(`report.md`, `verdict.json`, `manifest.json`, `test1_magnitude.csv.gz`, `test2_continuation_split.csv.gz`,
`test3_precascade.csv`, per-event files). Baseline sampling seed 20261006; bootstraps 2000 resamples.

- **H-FORCEDFLOW-DIAG-MAGNITUDE-01: NEGATIVE.** No class × horizon has mean |return| or forward realized
  vol ≥ 1.25× the matched baseline with CI lo > 1 on all four symbol × half cells. Closest: STRESS /
  DELEVERAGING at +5m (|ret| ratios 1.17 / 1.42 / 1.21 / 1.24 for BTC H1/H2, ETH H1/H2). The effect fades to
  ~1.0–1.15 by +15m…+4h. CASCADE and EXHAUSTION (n ≈ 16–29 per half) are noisy, and their ratios flip across
  halves. Mean |return| reaches the 34 bps cost band only at +4h (≈ 78–101 bps), where the matched
  baseline is the same size.
- **H-FORCEDFLOW-DIAG-CONTINUATION-SPLIT-01: NEGATIVE.** 29 features tested (15 continuous Cliff's δ +
  14 categorical risk differences), 116 gate cells (CASCADE, +1h). 18 single cells clear effect + CI, but no
  feature has the same sign on both symbols and both halves. Large effects flip sign between halves (e.g.
  BTC realized-vol δ +0.49 in H1, −0.54 in H2). Continuation / reversal group n is 4–15 per symbol × half. The +30m robustness check and the
  non-gating DELEVERAGING context are also NEGATIVE (DELEVERAGING: 0 cells clear the gate).
- **H-FORCEDFLOW-DIAG-PRECASCADE-01: NEGATIVE (flagged).** The logistic model (C = 1.0, fit on the first
  60%) has OOS PR-AUC lift ≥ 2 on both symbols at every horizon (BTC 7.0 / 4.0 / 3.3, ETH 9.9 / 6.9 / 6.1 at
  15 / 30 / 60m). But the 40% test segment holds only 11 (BTC) and 18 (ETH) CASCADE entries, below the
  pre-registered 20, so the gate is not met. Two caveats: (i) if y = 1 *bars* (33–214) were counted instead
  of cascade entries, Test 3 would read POSITIVE; (ii) the lift is largely by construction. A CASCADE needs
  an active crowd side plus STRESS conditions, so the CROWDING/STRESS flags (the largest coefficients, and
  rule lifts of 1.1–11.6) are antecedents of the label, not independent forecasts. The open question for
  the coordinator is in `output/f011_forced_flow/diagnostics/QUESTION.md`.
- **Counts:** 3 tests; 1194 reported cells (Test 1 450, Test 2 696, Test 3 48); 222 gate cells
  (100 + 116 + 6).
- **Recommendation: all three pre-registered tests are NEGATIVE → ARCHIVE the forced-flow strategy**
  (program note). This rests on the Test-3 positive-event count being read as cascade entries (see caveat
  above). Liquidation columns remain null on Train-1, so this is a verdict on the OI + taker-flow proxy, not
  on directly observed liquidation flow.

### Decision

_Left for the coordinator._

## 10. Scope guards

- Non-trading until Stage 1 produces a statistical edge. No orders, no positions, no promotion.
- Separate `forced_flow_lab/` namespace; the live bot and `strategy.py` catalog are untouched.
- Reuse the data contract (closed candles, checksums, no silent gaps) and the F005 Train-1 split;
  validation/holdout untouched.
- This supersedes nothing already frozen — it is the §13 non-correlated mechanism the frozen
  momentum class needed. Do not reopen EMA/BB/Donchian or the swarm.
