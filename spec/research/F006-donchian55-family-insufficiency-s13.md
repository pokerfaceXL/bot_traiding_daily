# F006 — DONCHIAN_55_NO_TRAIL family insufficiency (COORDINATOR_RESEARCH_PROTOCOL §13)

> Documentation/analysis only. No new strategy family is spawned by this note; it only
> answers whether/when one is allowed for the FREEZE'd `DONCHIAN_55_NO_TRAIL` profile.
> `spec/COORDINATOR_RESEARCH_PROTOCOL.md` does not exist on disk in this worktree (checked
> via `find`); §13 is referenced only by name in
> `spec/research/F006-hypothesis-donchian-abs-atr-entry-gate.md` (its `decision_if_fail`
> line) and `spec/research/strategy_profiles/DONCHIAN_55_NO_TRAIL.md` ("Allowed next
> experiments" / status rationale) as "a genuinely non-correlated mechanism justified per
> COORDINATOR_RESEARCH_PROTOCOL §13, written as a new pre-registered hypothesis note before
> any implementation." This note answers exactly that gate using the existing autopsy and
> ABS-ATR-gate evidence; it does not invent or start a new mechanism.

## Why existing family is insufficient

The `DONCHIAN_55_NO_TRAIL` profile (`spec/research/strategy_profiles/DONCHIAN_55_NO_TRAIL.md`)
is FREEZE'd because every single-axis entry/exit/sizing refinement tried within the same
mechanism — persistent Donchian-55 breakout, hold to opposite extreme or initial stop,
`NO_TRAIL` exit geometry — has been tested and falsified or rejected: trailing/boundary
sweep, stop-width, entry width-expansion gate, EMA50/200 trend confirm, cross-symbol
agreement, loss-recency cooldown, take-profit, vol-inverse sizing, calm/low-ATR-percentile
keep, and (most recently) an absolute ATR%(14) entry gate
(`H-DONCHIAN-ABS-ATR-ENTRY-GATE-01`, 5 pre-registered thresholds, 0/5 passed). The autopsy
(`output/f006_signal_autopsy/control_on/autopsy/*_DONCHIAN_55.csv`, Train-1, n=447) shows the
family's edge has one shape: 275/447 trades (61.5%) die at `initial_sl` for a pooled −913,
while 168 `signal_reverse` exits (37.6% of trades) produce +1441, nearly all of the aggregate
net. Every axis tested so far tries to separate these two populations using information
available *at entry* on the *same* Donchian-55 signal — trend agreement, volatility
percentile, absolute volatility level — and every one of them fails for the same underlying
reason (next section), not for lack of tuning within that axis.

## What mechanism is missing

All exhausted axes share one property: they gate or reweight the *existing* Donchian-55
breakout signal using features that are statistically correlated with the breakout's own
volatility state, not causally independent of it. The ABS-ATR-gate result makes this
quantitative: absolute ATR% at entry is higher on `initial_sl` deaths (≈1.63%) than on
`signal_reverse` runners (≈1.05%), so cutting high-ATR entries looks promising in isolation —
but every threshold that cut the `initial_sl` share by ≥10pp also removed more than half of
the baseline big-winner PnL (best case: 13.75pp stop-share reduction at the cost of 51.8%
lost big-winner PnL), and the one threshold that preserved 83.4% of big-winner PnL (T=2.0%)
barely moved the stop share (5.39pp). This mirrors the earlier EMA-trend-confirm result (which
destroyed the profile's edge entirely, +58→−3.6) and the calm/low-ATR-percentile-keep
counterfactual (which also destroyed the edge by removing the same runners). What is missing
is not a better threshold on the same feature axis — it is a signal that identifies
"this specific breakout will travel to the opposite extreme" using information that does not
move in lockstep with the breakout's own volatility, i.e. something orthogonal to the ATR/
trend-strength axis that both feeds the entry (a wide/strong move looks more "tradeable") and
determines whether the trade is a stop-out or a runner (the same volatility that triggers entry
also determines whether the move continues or snaps back). No such orthogonal signal has been
tested; every axis tried so far measures a facet of "how big/strong was this breakout,"
which is the same thing that both causes entry and predicts the entry/exit split.

## Why a next family would need to be different

A next mechanism is only justified if it does not re-test a repackaged form of "was this
breakout large/strong/trending," because that axis is now closed on both its trend-confirm
(EMA50/200) and volatility (percentile and absolute-ATR%) forms, and both closures leave the
same trade-off signature: any filter that meaningfully thins the `initial_sl` population also
removes most of the fat-tail `signal_reverse` winners, because both populations are drawn from
the same "breakout fired" event and current features cannot distinguish which one is about to
happen without also filtering out the very extremity that makes a runner a runner. A next
family — if pursued — would need to use information genuinely independent of that shared
volatility/strength axis: for example, cross-asset or market-structure context unrelated to
this instrument's own recent range (something the exhausted cross-symbol-agreement axis
touched only lightly and only on direction agreement, not volatility-independent structure),
order-flow/liquidity features, or a different exit/position mechanism entirely (not "which
breakouts to take" but "how to size or hold once taken") that does not require distinguishing
stop-outs from runners at entry at all. This note does not select or pre-register any of
these — it only states the disqualifying property a next mechanism must avoid.

## What evidence would reject that next direction

A next-family hypothesis for this profile should be pre-registered (same discipline as
`H-DONCHIAN-ABS-ATR-ENTRY-GATE-01`) with an explicit falsification condition analogous to
that note's: the candidate mechanism is rejected if, on the frozen Train-1 basket, (a) mean
train1_net_pnl does not exceed the ungated baseline (+58.387) at every tested setting, or
(b) any setting that meaningfully reduces the `initial_sl` share (≥10pp, matching the bar
already used) also removes >50% of the baseline's big-winner PnL (same 36-trade, ≥$10
big-winner set already computed and reproducible from
`output/f006_donchian_abs_atr_gate/manifest.json`), or (c) the monthly losing-month count does
not improve below the persistent 7/12 floor seen at every ABS-ATR threshold. Reproducing this
same stop-share/big-winner trade-off with a differently-sourced feature would confirm the
trade-off is structural to the mechanism (breakout-triggers-on-extremity), not an artifact of
the specific feature tried, and would close the door on further per-feature attempts at this
profile without a mechanism-level change (e.g. position-level, not entry-level).

## What is the maximum initial research budget

Consistent with the ABS-ATR gate's own budget discipline (a fixed, small, pre-declared grid,
no widening after seeing results): a next-family hypothesis for this profile, if and when
proposed, should be capped at a single pre-registered test on the existing frozen Train-1
5×2 basket — at most 5 parameter/threshold cells (same size as the ABS-ATR grid), one
mechanism, no new data fetch, no new symbols/intervals, Train-1 only. If that budget does not
clear the falsification bar above, this profile stays FREEZE'd and no further per-cell
widening or a second family attempt is authorized without a fresh, separately-justified §13
note — matching the "no widening without a new written non-correlated mechanism
justification" rule already stated in the frozen profile.
