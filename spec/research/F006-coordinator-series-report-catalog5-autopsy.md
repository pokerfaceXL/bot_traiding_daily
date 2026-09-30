# F006 — Coordinator series report: catalog5 shared-class autopsy (COORDINATOR_RESEARCH_PROTOCOL §15)

Mandatory end-of-series report, covering the Donchian autopsy + catalog5 dual/trio autopsy +
this job's §13 finalization series.

> **Update (2026-09-30):** after this report, `H-CATALOG5-EXIT-CLASS-01` (tip `923de9c`,
> FALSIFIED (a)(b)(c)) and `H-CATALOG5-PARTIAL-EXIT-01` (tip `3d4edd4`, FALSIFIED (a)(b))
> exhausted the licensed exit-grid and partial-exit axes, with the entry-vol axis already DNR.
> All five catalog5 profiles referred to below as CONDITIONAL are now **FREEZE** (not
> REJECT); remaining §13 work needs order-flow/OI data or a new family outside this `NO_TRAIL`
> class — see the addendum in `spec/research/F006-catalog5-family-insufficiency-s13.md`.
> Answers 1-10 below are kept as written at the time.

1. **Która strategia jest obecnie najlepsza?** None is promotable — no profile in this
   repository has cleared the protocol §7 monthly promotion checklist. Among the six
   `NO_TRAIL` catalog5/Donchian profiles (the only strategy profiles on disk), the
   full-slice-sweep best by rank is `EMA3_21_50_200` (10/10 series positive, top-ranked among
   77 catalog names screened), with `BB_20_25_EMA200` close behind on Train-1-window
   consistency (9/10 series positive). `DONCHIAN_55_NO_TRAIL` is the only one FREEZE'd; the
   other five, including `EMA3_21_50_200`, stay CONDITIONAL.
2. **Dlaczego jest najlepsza?** `EMA3_21_50_200`'s edge is aggregate-positive across the
   widest span of series/symbols in the batch and ranks highest in the original 77-name
   catalog sweep, but "best" here means best surviving screen, not validated — it shares the
   same `initial_sl`-dominated, fat-tail-dependent shape as the other four and fails the
   monthly-regularity bar exactly like them (0/10 series clear §7).
3. **Czy przewaga pochodzi z wielu transakcji, czy kilku dużych wygranych?** From a handful of
   large winners, for all six names, not from many transactions. Every autopsy shows
   `initial_sl` exits at 0% win rate dominating trade count (47-69% of entries) while a small
   top-N winner set (2-10 trades) accounts for 50-71% of gross wins; `EMA3_21_50_200` itself
   has 4 of 402 trades summing to its full pooled net PnL.
4. **W jakich warunkach zarabia?** When a breakout/trend-entry signal (Donchian extreme,
   EMA cross, triple-EMA cross, or Bollinger-EMA breakout) fires during an elevated-ATR regime
   that then continues in the signal's direction to the opposite structural extreme
   (`signal_reverse` exit) — these are the rare, high-ATR entries that become runners.
5. **W jakich warunkach traci?** When the same kind of elevated-ATR entry snaps back instead
   of continuing, hitting the fixed `NO_TRAIL` `max_sl_pct=0.03` stop (`initial_sl` exit,
   majority of trades, 0% WR by construction) — entry-time features cannot yet distinguish
   this case from case 4 because both draw from the same "signal fired during high volatility"
   population, and 7/12 Train-1 entry-months are net-negative for every one of the five
   CONDITIONAL names.
6. **Które hipotezy zostały odrzucone?** For `DONCHIAN_55_NO_TRAIL`: trend-confirm (EMA50/200
   agreement), calm/low-ATR-percentile keep, trailing/boundary sweep, stop-width sweep, entry
   width-expansion gate, cross-symbol agreement, loss-recency cooldown, take-profit,
   vol-inverse sizing, and `H-DONCHIAN-ABS-ATR-ENTRY-GATE-01` (absolute ATR%(14) entry gate,
   0/5 thresholds passed) — all FALSIFIED or REJECTED. For the other five catalog5 names:
   `H-CATALOG5-ABS-ATR-ENTRY-GATE-01` is now DNR (do-not-retest) on all five per this job's §13
   note — the shared entry-ATR asymmetry confirms the same axis that failed on Donchian, so it
   is not independently retested per name.
7. **Jaki problem pozostaje nierozwiązany?** No entry-time feature has been found, across five
   independent signal generators, that separates `initial_sl` deaths from `signal_reverse`
   runners without also being correlated with the entry's own volatility/trend-strength state
   — the exact state that both triggers entry and determines the stop/runner split. Monthly
   regularity (7/12 losing months) is also unresolved for every CONDITIONAL name.
8. **Jaki jest następny eksperyment i dlaczego?** None is pre-registered by this job. Per the
   finalized `spec/research/F006-catalog5-family-insufficiency-s13.md`, the only licensed next
   step for any of the five CONDITIONAL profiles is a single pre-registered test of a
   genuinely non-correlated mechanism (cross-asset/market-structure context, order-flow/
   liquidity features) or a written-justified exit-class change (not an entry filter) — none
   of which has been selected or scoped yet; that selection is future work, not part of this
   finalization job.
9. **Dlaczego nie testuje teraz kolejnych losowych strategii?** Protocol §13 condition 1 is met
   (the current `NO_TRAIL` family has been probed on its main axes and the failure has a
   shared mechanism across five independent signal generators), but §13 requires the next
   family to be *justified in writing* with a falsification condition and budget before any
   implementation — a requirement this job's note satisfies as a gate, not as a green light to
   start an arbitrary new search. Widening to unrelated random strategies without that
   written mechanism justification would violate the "no widening without a new written
   non-correlated mechanism" discipline already established for `DONCHIAN_55_NO_TRAIL`.
10. **Jaki wynik potwierdziłby lub obalił następną hipotezę?** As stated in
    `spec/research/F006-catalog5-family-insufficiency-s13.md`: a candidate next-family
    mechanism is falsified if, on the frozen Train-1 5×2 basket, (a) mean `train1_net_pnl`
    does not exceed the ungated baseline at every tested setting, or (b) any setting that
    reduces the `initial_sl` share by ≥10pp also removes >50% of that name's baseline
    big-winner PnL, or (c) the 7/12 losing-month floor does not improve — capped at 5
    threshold cells, Train-1 only, no widening after seeing results.
