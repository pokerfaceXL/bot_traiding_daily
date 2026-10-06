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

## 10. Scope guards

- Non-trading until Stage 1 produces a statistical edge. No orders, no positions, no promotion.
- Separate `forced_flow_lab/` namespace; the live bot and `strategy.py` catalog are untouched.
- Reuse the data contract (closed candles, checksums, no silent gaps) and the F005 Train-1 split;
  validation/holdout untouched.
- This supersedes nothing already frozen — it is the §13 non-correlated mechanism the frozen
  momentum class needed. Do not reopen EMA/BB/Donchian or the swarm.
