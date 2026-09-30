# F006 — catalog5 NO_TRAIL shared fat-tail class: family insufficiency (DRAFT, COORDINATOR_RESEARCH_PROTOCOL §13)

> **DRAFT — documentation only, not finalized.** This note is written per this job's
> instruction ("if all 5 catalog5 leads share the Donchian loss shape, draft a §13
> family-insufficiency note"). It is modeled on the finalized
> `spec/research/F006-donchian55-family-insufficiency-s13.md` but covers *five* names at
> once, none of which are FREEZE'd. No profile status changes because of this note. It does
> not authorize any new experiment by itself; a future job must review, finalize (or reject)
> it, and get it accepted before it can license anything. `spec/COORDINATOR_RESEARCH_PROTOCOL.md`
> is not present on disk in this worktree; §13 is referenced only by name, following the same
> convention as the Donchian note.

## Why a shared-class note, not five per-name notes

Five catalog5 `NO_TRAIL` leads have now been autopsied at the trade level:
`DONCHIAN_55_NO_TRAIL` (FREEZE'd), `EMA_50_200`, `BB_20_25_EMA200`, `EMA3_21_50_200`,
`EMA3_13_50_200`, `BB_20_2_EMA200` (all five CONDITIONAL). All five show the same shape:

| name | initial_sl share (Train-1) | avg_winner / \|avg_loser\| | loss months (of 12) |
| --- | ---: | ---: | ---: |
| DONCHIAN_55_NO_TRAIL | 62% | ~4.1x | 7 |
| EMA_50_200 | 65% | ~6.7x | 7 |
| BB_20_25_EMA200 | 58% | ~4.9x | 7 |
| EMA3_21_50_200 | 69% | ~7.5x | 7 |
| EMA3_13_50_200 | 69% | ~7.4x | 7 |
| BB_20_2_EMA200 | 47% | ~4.7x | 7 |

(sources: `output/f006_donchian_autopsy/`, `output/f006_catalog5_dual_autopsy/`,
`output/f006_catalog5_trio_autopsy/`.) Every name is `initial_sl`-dominated on the loss side
(0% WR on that exit), fat-tail-dependent on the win side (a handful of trades produce most of
the net PnL), and has exactly 7/12 net-negative Train-1 entry-months — not approximately the
same shape, the *same count* across five independently-generated signal families (Donchian
breakout, dual-EMA, triple-EMA ×2, Bollinger-EMA ×2). A per-name §13 note would repeat the
same argument five times; the shared shape argues the insufficiency is a property of the
`NO_TRAIL` exit geometry class (fixed `max_sl_pct=0.03`, unreachable trail activation) applied
to any trend/breakout-style entry signal on this Train-1 5×2 basket, not a property of any one
signal generator.

## Why existing family is insufficient (shared)

For `DONCHIAN_55_NO_TRAIL`, every single-axis refinement tried on the *same* signal
(trailing/boundary sweep, stop width, entry width-expansion gate, EMA50/200 trend confirm,
cross-symbol agreement, loss-recency cooldown, take-profit, vol-inverse sizing,
calm/low-ATR-percentile keep, absolute ATR% entry gate) was tested and falsified or rejected
(`spec/research/F006-donchian55-family-insufficiency-s13.md`). For the other four names, only
the autopsy (diagnostic) and the ATR-entry-asymmetry observation have been made — no gate has
been implemented or tested on them. What is shared across all five, and what makes the
Donchian conclusion relevant to the other four without re-running their own gate tests, is the
*entry-ATR asymmetry itself*: in every one of the five autopsies, mean entry ATR%(14) on
`initial_sl` exits is higher than on `signal_reverse` exits (Donchian ≈1.63 vs 1.05;
EMA_50_200 1.75 vs 1.06; BB_20_25_EMA200 1.70 vs 1.06; EMA3_21_50_200 1.71 vs 1.09;
EMA3_13_50_200 1.77 vs 1.10; BB_20_2_EMA200 1.76 vs 1.08). This is the exact asymmetry the
Donchian ABS-ATR gate was built to exploit, and it failed there because any threshold that
meaningfully thinned the high-ATR (`initial_sl`-heavy) population also removed most of the
fat-tail winners — both populations are drawn from the same "signal fired during an elevated-
volatility regime" event, and current ATR-based features cannot separate "this elevated-
volatility entry will stop out" from "this elevated-volatility entry will run" without also
filtering out the volatility that makes a runner a runner.

## What mechanism is missing (shared)

Same as the Donchian §13 finding, generalized: all five names' `initial_sl`/`signal_reverse`
split is not separable *at entry* using any feature that is itself a function of the entry
signal's own volatility or trend-strength state — because that state is exactly what both (a)
triggers the entry (a stronger/wider move looks more "signal-worthy" across all five
generator types) and (b) determines the entry/exit split (the same volatility that triggers
entry also determines whether price continues or snaps back). This property does not depend
on the specific entry rule (Donchian breakout, EMA cross, triple-EMA cross, Bollinger
breakout) — it is a property of pairing any breakout/trend-following-style entry with a fixed,
symmetric, non-trailing stop-loss-only exit (`NO_TRAIL`) on this instrument/timeframe basket.

## Why a next family would need to be different (shared)

A next mechanism justified by this note would need to avoid re-testing a repackaged form of
"how large/strong/volatile was this entry" against any of the five names, because that axis
is closed for `DONCHIAN_55_NO_TRAIL` in both its trend-confirm and volatility forms, and the
same asymmetry (without yet being gate-tested) is present in the other four. Candidates that
would be genuinely non-correlated with the shared axis, if pursued (not selected here):
cross-asset/market-structure context unrelated to the instrument's own recent range,
order-flow/liquidity features, or a change to the *exit* mechanism (not "which entries to
take" but "how to size or hold once taken," e.g. partial exits or volatility-adaptive holding
— a different problem class than entry filtering) that does not require distinguishing
stop-outs from runners at entry at all. This draft does not select or pre-register any of
these for any of the five names.

## What evidence would reject that next direction (shared)

A next-family hypothesis invoking this note should be pre-registered per name (or per shared
mechanism, if it applies across names) with an explicit falsification condition analogous to
the Donchian gate's: rejected if (a) mean `train1_net_pnl` does not exceed the ungated
baseline at every tested setting for the target name(s), or (b) any setting that meaningfully
reduces the `initial_sl` share (≥10pp) also removes >50% of that name's baseline big-winner
PnL, or (c) the 7/12 losing-month floor does not improve. Reproducing the same trade-off with
a differently-sourced, non-ATR feature on any of the five names would strengthen the case that
the trade-off is structural to `NO_TRAIL` + trend/breakout entries generally, not an artifact
of one signal generator.

## What is the maximum initial research budget (shared)

Same discipline as the finalized Donchian §13 note: capped at a single pre-registered test per
proposed mechanism (not per name), at most 5 parameter/threshold cells, on the existing frozen
Train-1 5×2 basket, no new data fetch, no new symbols/intervals, Train-1 only. If proposed
against multiple names at once, the pre-registration must state in advance whether it is one
shared mechanism tested identically across names (preferred, since the insufficiency argument
here is that the class — not any one name — needs a new axis) or five independent tests, and
must not widen after seeing per-name results.

## Status of this draft

Not reviewed, not finalized, not accepted. No profile in this job (or the prior dual-autopsy
job) changes status because of this note — all five CONDITIONAL profiles listed above remain
CONDITIONAL, and `DONCHIAN_55_NO_TRAIL` remains FREEZE'd under its own already-finalized §13
note. This draft exists so a future job does not need to re-derive the shared-shape
observation from five separate autopsy reports before deciding whether a next-family test is
worth proposing.
