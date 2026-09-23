# F006 — Hypothesis: re-entry cooldown (`cooldown_candles`) at leverage=1, Train 1 only

> Sections "Observation" … "Falsification condition" were written and committed to this file
> BEFORE the experiment script was run, per the same discipline as
> `spec/research/F006-hypothesis-stop-width.md`, `spec/research/F006-hypothesis-entry-regime-filter.md`
> and `spec/research/F006-lorentzian-causality.md`. "Method", "Run_id", "Result" and "Decision"
> were filled in after the run.
>
> TRAIN-1 ONLY. Per `spec/research/F005-validation-protocol.md` section 7.3, F006 selects on
> train+validation and never opens holdout; this slice restricts itself further, to Train 1
> (`[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`) plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window are not loaded, not sliced and not
> looked at by any script in this slice.

## Observation

`spec/research/F006-lorentzian-causality.md`'s signal-shape diagnostics measured something none
of the previous F006 hypotheses touched. At 4h, the causal Lorentzian classifier changes its
directional state only **58-76 times** over the whole of Train 1, but the engine executes
**270-313 trades** on the same series — 4 to 5 executed trades per directional call. The
mechanism is in `backtest_engine.run_backtest` and is not Lorentzian-specific: a catalog entry is
a *persistent* per-bar state (+1/-1/0), step 2 of the loop stops a position out at
`max_sl_pct=0.03`, and step 4 immediately re-queues an entry on the very next bar because the
state is still non-zero, `pos == 0`, and `cooldown_candles=0` leaves `cooldown_until = -1`. Each
of those re-entries pays a full round trip of commission + half-spread + slippage.

Two prior single-dimension hypotheses on this catalog have been falsified on Train 1: stop width
(`spec/research/F006-hypothesis-stop-width.md`, 0/400 positive runs) and an ADX14 entry regime
filter (`spec/research/F006-hypothesis-entry-regime-filter.md`, 0/500 positive runs). Both
targeted *which* trade is taken or *how wide* its stop is. Neither touched the re-entry loop.
`spec/research/F005-leverage-sensitivity.md` did sweep `cooldown_candles` ∈ {0, 5, 20} and found
it did not help — but **only at `leverage=10`**, where the dominant effect is the speed of the
margin spiral to the ~$100 bankruptcy floor. At `leverage=1` (the F006 research placeholder per
`spec/build.md`, and the setting used by both prior F006 hypothesis experiments), cooldown has
never been tested at all.

## Hypothesis

Raising `cooldown_candles` at `leverage=1` suppresses the mechanically wasteful re-entries the
observation describes — the chain of entries into the *same, unchanged* directional call after
each 3% stop-out — and therefore reduces cost drag and improves net PnL, on both the existing
10-strategy catalog sample and the two new causal Lorentzian entries.

**Predicted effect**: as `cooldown_candles` rises from 0 through 5, 10, 20 to 50, mean trade count
per (symbol, interval, strategy) falls, and mean net PnL improves (becomes less negative, or
positive for at least part of the sample). The improvement should be **larger for series with a
high re-entry rate** — specifically the Lorentzian entries at 4h, where 4-5 trades per directional
call were measured — than for series that were already low-frequency, since the hypothesis
attributes the gain to cutting redundant re-entries rather than to trading less in general.

## Sources

This repo's own prior findings only, no external source:
`spec/research/F006-lorentzian-causality.md` (the 4-5 trades-per-call measurement, the Lorentzian
adapter and its Python 3.11 venv recipe), `spec/research/F006-hypothesis-stop-width.md` and
`spec/research/F006-hypothesis-entry-regime-filter.md` (the 10-strategy sample, the Train-1-only
methodology and the checksum table reused verbatim here),
`spec/research/F005-leverage-sensitivity.md` (the prior cooldown sweep, at leverage=10 only),
`spec/research/F005-baseline.md`, `spec/research/F005-validation-protocol.md` (frozen windows
section 3.2, basket/cost defaults section 6), `spec/build.md` (leverage=1 as the F006 research
placeholder).

## Falsification condition (stated before running)

This hypothesis is **falsified** if mean net PnL across the sampled (symbol, interval, strategy)
combinations does not improve — does not become less negative or positive — as `cooldown_candles`
rises from 0 to 50; **or** if trade count falls without any accompanying net-PnL improvement, i.e.
cooldown merely starves the strategies of trades rather than cutting genuinely wasteful
re-entries. This is the same caveat the ADX-filter note applied to itself: a reduction in trade
count that is not matched by a real PnL gain is not evidence for the mechanism.

A secondary, mechanism-specific check, reported either way but not by itself falsifying: the
improvement should be **larger for the Lorentzian entries (high measured re-entry rate) than for
the catalog sample**. If cooldown helps both groups equally regardless of their re-entry rate,
the "wasteful re-entry" mechanism is not what is producing the effect, and the result is the same
"fewer trades, less cost drag" story the ADX filter already told.

## Method

Same continuous-run methodology, fixed parameter block and checksum discipline as
`scripts/f006_stop_width_experiment.py` at its `max_sl_pct=0.03` row (which is also the block
`scripts/f006_lorentzian_experiment.py` used), with `cooldown_candles` as the only swept
dimension. No engine change was needed or made: `cooldown_candles` has been a
`backtest_engine.run_backtest` parameter since F004.

- **Script**: `scripts/f006_cooldown_experiment.py`.
- **Grid**: `cooldown_candles` ∈ {0, 5, 10, 20, 50} × 12 signal names × 5 symbols × 2 intervals =
  **600 runs**. The 12 names are the 10-strategy sample of
  `spec/research/F006-hypothesis-stop-width.md` (`EMA_8_21`, `EMA_13_34_RSI14_55`, `RSI14_7030`,
  `MACD_12_26_hist`, `MACD_RSI14_50`, `BB_20_25_breakout`, `BB_20_2_RSI14`, `ADX14_DI_20`,
  `STOCH14_cross`, `TS_13_34_200_14`) plus `LORENTZIAN_default` and `LORENTZIAN_raw`.
- **Fixed**: `leverage=1`, `max_sl_pct=0.03`, `atr_multiplier=1.5`, `activate_pct=0.03`,
  `trail_pct=0.02`, `initial_equity=500`, `stake=100`, `commission_rate_bps=10`,
  `half_spread_bps=5`, `slippage_bps=2`, `now` pinned to `2025-03-01T00:00:00Z`.
- **Data**: `data_contract.load_dataset("data_cache", …, "2024-01-26T00:00:00Z",
  "2026-09-01T00:00:00Z")`, all ten checksums verified in-script against
  `spec/research/F005-validation-protocol.md` section 6, then sliced to
  `[2024-01-26T00:00:00Z, 2025-03-01T00:00:00Z)` — warm-up + Train 1 only — before `run_backtest`
  sees it. No network fetch. Regularity deliberately not computed (Train-only exploration).
- **Recorded per run**: net PnL, win rate, n_trades, max_drawdown_pct, `survived = final_equity ≥
  $100`, plus `gross_pnl`, `total_costs` and `n_initial_sl_exits` — the three extra columns exist
  so the "fewer trades, less cost drag" explanation that falsified the ADX filter can be
  *measured* here rather than argued about.
- **Two passes, one schema.** advanced-ta needs Python ≥3.10, so the grid was split by
  interpreter: `--catalog` (500 runs) on the project's Python 3.9 `.venv_test`, `--lorentzian`
  (100 runs) on a standalone Python 3.11 `.venv_lorentzian` built by the recipe in
  `spec/research/F006-lorentzian-causality.md`'s Run_id section, then `--merge` concatenating
  both into one `results.csv`/`manifest.json`. Both passes write identical columns and run the
  same engine over the same data slice; only the interpreter differs.
- **Cross-check built into the run** (the discriminating check for comparability): every
  `cooldown_candles=0` row must reproduce the corresponding stored row of the two prior
  experiments *exactly*, since cooldown=0 is precisely their configuration. **100/100 catalog
  rows matched `output/f006_stop_width/summary/results.csv` (max_sl_pct=0.03) and 20/20
  Lorentzian rows matched `output/f006_lorentzian/summary/results.csv`, 0 mismatches** on
  net_pnl, win_rate, n_trades, max_drawdown_pct and final_equity. The whole grid was also run
  twice (the second time to add the gross/cost columns) and reproduced identical aggregates.

**One engine detail that bounds what this sweep can do**, from `backtest_engine.py` step 2:
`cooldown_until` is set only when `exit_reason == "initial_sl"`. Exits via trailing stop or
signal reversal do **not** start a cooldown, so this lever suppresses re-entry only after the
stop-out chains the observation describes — which is the intended target, but means a large part
of each strategy's trade flow is untouched by it.

## Run_id

`scripts/f006_cooldown_experiment.py`, `git_commit_parent =
d86e2d3ddec9ce91a2730379ffef6d5a161bfe1b`, `n_runs = 600`. Catalog pass: `run_timestamp_utc =
2026-09-23T09:03:38Z`, Python 3.9.25, 500 runs, `elapsed_seconds = 133.0`. Lorentzian pass:
`run_timestamp_utc = 2026-09-23T09:04:39Z`, Python 3.11.16 + advanced-ta 0.1.8, 100 runs,
`elapsed_seconds = 59.5`. pandas 2.3.3 in both. Full parameters, checksums, cross-checks and
aggregate tables: `output/f006_cooldown/summary/manifest.json` (per-pass manifests are embedded
under `pass_manifests`, and also kept as `manifest_catalog.json` / `manifest_lorentzian.json`).
Per-run results, 600 rows: `output/f006_cooldown/summary/results.csv` (per-pass:
`results_catalog.csv`, `results_lorentzian.csv`).

## Result

**Aggregate means, all 120 (symbol, interval, signal) combinations per cooldown value:**

| `cooldown_candles` | Mean net PnL | Mean win rate | Mean n_trades | Mean initial-SL exits | Mean max DD | Survived (≥$100) | Positive net PnL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | -$363.67 | 28.75% | 372.6 | 100.3 | 72.95% | 29/120 | **0/120** |
| 5 | -$342.95 | 29.14% | 366.8 | 90.6 | 68.85% | 46/120 | **0/120** |
| 10 | -$322.55 | 29.49% | 361.6 | 83.0 | 64.83% | 64/120 | **0/120** |
| 20 | -$282.72 | 29.49% | 336.8 | 70.0 | 56.87% | 79/120 | **0/120** |
| 50 | **-$215.40** | 29.37% | 279.0 | 49.4 | **43.49%** | **98/120** | **0/120** |

Mean net PnL improves **monotonically** across the whole sweep, by $148.28 — 40.8% of the
cooldown=0 deficit, an order of magnitude larger than the ADX filter's $17.68 and unlike the
stop-width sweep's flat, non-monotonic result. Max drawdown falls from 72.95% to 43.49%, and
survival rises from 29/120 to 98/120. **Zero of the 600 runs is profitable at any cooldown
value**; the best single run in the entire grid is `BB_20_25_breakout` / ETHUSDT / 4h at
cooldown=50, net **-$43.48**.

**Split catalog vs Lorentzian** (the observation predicted a bigger effect for Lorentzian):

| Group | net PnL @0 | @5 | @10 | @20 | @50 | Δ(0→50) | % of deficit | Survived @0 → @50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| catalog (10 names, 500 runs) | -$357.81 | -$335.29 | -$315.16 | -$277.57 | -$211.46 | +$146.35 | 40.9% | 27/100 → 82/100 |
| Lorentzian (2 names, 100 runs) | -$393.01 | -$381.25 | -$359.53 | -$308.50 | -$235.09 | +$157.92 | 40.2% | 2/20 → 16/20 |
| — `LORENTZIAN_default` alone | -$384.99 | -$369.98 | -$341.72 | -$291.47 | -$202.29 | +$182.70 | 47.5% | 2/10 → 10/10 |
| — `LORENTZIAN_raw` alone | -$401.03 | -$392.52 | -$377.35 | -$325.53 | -$267.90 | +$133.13 | 33.2% | 0/10 → 6/10 |

The predicted Lorentzian-specific advantage is **not** there as a group effect: in percentage of
deficit the two groups improve identically (40.2% vs 40.9%). `LORENTZIAN_default` — the entry
whose 4-5-trades-per-directional-call at 4h motivated the whole hypothesis — does improve more
than the catalog mean (47.5%, and it is the only name that goes from 2/10 to 10/10 survival),
but its stablemate `LORENTZIAN_raw` improves less than the catalog mean (33.2%), so the group
average washes out.

**Per-strategy net PnL (mean over 10 series) by cooldown:**

| Strategy | 0 | 5 | 10 | 20 | 50 | Δ(0→50) | monotone? | Survived @50 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :-: | ---: |
| `RSI14_7030` | -$362.75 | -$258.94 | -$223.67 | -$180.53 | -$117.83 | +$244.92 | yes | 10/10 |
| `TS_13_34_200_14` | -$365.91 | -$347.56 | -$310.05 | -$263.57 | -$163.85 | +$202.06 | yes | 10/10 |
| `EMA_13_34_RSI14_55` | -$379.46 | -$365.50 | -$332.64 | -$277.80 | -$190.60 | +$188.86 | yes | 10/10 |
| `LORENTZIAN_default` | -$384.99 | -$369.98 | -$341.72 | -$291.47 | -$202.29 | +$182.70 | yes | 10/10 |
| `EMA_8_21` | -$399.02 | -$380.21 | -$364.20 | -$310.64 | -$246.22 | +$152.80 | yes | 8/10 |
| `MACD_RSI14_50` | -$393.22 | -$375.83 | -$354.23 | -$307.97 | -$245.49 | +$147.73 | yes | 7/10 |
| `BB_20_2_RSI14` | -$306.23 | -$284.53 | -$272.32 | -$238.99 | -$169.38 | +$136.85 | yes | 10/10 |
| `MACD_12_26_hist` | -$401.56 | -$389.41 | -$370.73 | -$325.83 | -$267.71 | +$133.85 | yes | 6/10 |
| `LORENTZIAN_raw` | -$401.03 | -$392.52 | -$377.35 | -$325.53 | -$267.90 | +$133.13 | yes | 6/10 |
| `ADX14_DI_20` | -$400.65 | -$394.72 | -$373.25 | -$327.30 | -$271.36 | +$129.29 | yes | 6/10 |
| `STOCH14_cross` | -$400.64 | -$400.90 | -$400.51 | -$401.10 | -$336.01 | +$64.63 | **no** | 5/10 |
| `BB_20_25_breakout` | -$168.62 | -$155.31 | -$149.97 | -$141.93 | -$106.11 | +$62.51 | yes | 10/10 |

11 of 12 names improve monotonically; only `STOCH14_cross` is flat until cooldown=50 (it is also
the one name whose trade count *rises* under cooldown, 620 → 710 at cooldown=20).

### Where the improvement actually comes from

The extra columns settle this rather than leaving it to interpretation. Decomposing the $148.28
improvement into saved costs versus better gross outcomes:

| Slice | Δ net PnL (0→50) | of which saved costs | of which gross PnL | mean n_trades 0→50 | mean net PnL **per trade** 0→50 |
| --- | ---: | ---: | ---: | ---: | ---: |
| all 12 names | +$148.28 | +$29.97 | +$118.31 | 372.6 → 279.0 | -$1.078 → -$1.010 |
| catalog | +$146.35 | +$29.88 | +$116.47 | 367.8 → 274.5 | — |
| Lorentzian | +$157.92 | +$30.42 | +$127.49 | 396.6 → 301.6 | — |
| 4h only | +$224.19 (63.7%) | +$56.28 | +$167.91 | 289.6 → 113.8 | **-$1.260 → -$1.266** |
| 1h only | +$72.37 (19.3%) | +$3.66 | +$68.70 | 455.5 → 444.1 | -$0.897 → -$0.754 |

Only ~20% of the gain is saved commission/spread/slippage; the rest is gross PnL. That alone
would look like a win for the mechanism — but the per-trade column says otherwise. **At 4h,
where the effect is by far the largest (63.7% of the deficit), net PnL per trade is flat:
-$1.260 at cooldown=0 versus -$1.266 at cooldown=50.** The entire 4h improvement is 61% fewer
trades (289.6 → 113.8) executed at an unchanged, negative per-trade expectancy. At 1h the
per-trade figure does improve (-$0.897 → -$0.754, +16%), but there the trade count barely moves
(455.5 → 444.1, -2.5%): 50 one-hour candles is about two days, long enough to defer re-entries
but not to remove them, so the 1h slice contributes only 19.3% of deficit reduction.

Across the whole grid, mean net PnL per trade moves from -$1.078 to -$1.010 (+6.3%), and **not
one of the 600 runs, and not one of the 60 (strategy, cooldown) cells, has a positive per-trade
expectancy.** Mean cost per trade is constant at $0.32 across all cooldown values, which also
rules out the obvious confound that near-floor runs trade smaller notional and therefore look
cheaper per trade. Win rate is essentially flat (28.75% → 29.37%, peaking at 29.49%), the same
non-signal the ADX experiment reported. Initial-SL exits fall from 26.9% to 17.7% of all trades,
confirming the gate is doing mechanically what it says.

### Against the falsification condition, honestly

The **stated condition is not met**: mean net PnL *does* improve, monotonically and by a
non-trivial margin, as cooldown rises 0 → 50; and the improvement is not *only* cost saving
(4× more of it is gross PnL than saved fees). On its literal terms the hypothesis survives.

The **mechanism behind it does not survive**. The hypothesis claimed cooldown cuts *genuinely
wasteful* re-entries — trades worse than the strategy's average. If that were true, per-trade
expectancy would improve as those trades are removed. At 4h, the slice with the biggest gain and
the re-entry rate that motivated the experiment, per-trade expectancy is flat to a fraction of a
cent. The trades cooldown removes are, to a good approximation, *average* trades of a
negative-expectancy process. The secondary mechanism check fails too: the Lorentzian group
improves by the same 40% of deficit as the catalog, i.e. the effect does not track the measured
re-entry rate. So the effect is real, sizeable and monotone — and it is still, in substance, the
ADX note's "fewer trades, smaller loss" pattern at a larger scale, not restored edge.

That has a hard consequence: since per-trade expectancy stays negative everywhere, the ceiling of
this lever is **net PnL → $0 as n_trades → 0**. Extrapolating the flat 4h per-trade figure, no
cooldown value can cross into profit; larger cooldowns can only approach not trading at all.

## Decision

**Cooldown helps materially but not enough. It does not justify a Validation-1 check, and it is
not the fix — it is a mitigation, and its best possible outcome is breaking even by not
trading.**

What was established and is reusable: at `leverage=1` — the combination
`spec/research/F005-leverage-sensitivity.md` never tested, having swept cooldown only at
`leverage=10` where the margin spiral dominates — `cooldown_candles` is the largest single-knob
effect measured on this catalog so far (40.8% of the deficit, max DD 72.95% → 43.49%, survival
29/120 → 98/120, 11/12 names monotone, 4h 63.7%), roughly eight times the ADX filter's effect and
unlike the stop-width sweep in being monotone. Future Train experiments on this basket are
better run with `cooldown_candles=20-50` at 4h than at 0: same signals, far less
bankruptcy-floor censoring, so differences between signal generators stay visible instead of all
bottoming out at ~$100. That is a *measurement* recommendation, not a strategy.

What was not established: any path to positive edge. 0/600 runs profitable, best -$43.48,
per-trade expectancy negative in 600/600 runs and flat across the sweep exactly where the effect
is strongest. Four F006 hypotheses have now been tested on Train 1 — wider stops, ADX entry
filter, a genuinely different generator (causal Lorentzian), and re-entry cooldown — and the
invariant across all four is that **mean net PnL per trade is negative for every signal name in
the sample under every parameter setting tried**. Sizing, exits, entry filtering and now entry
*frequency* all move the total loss without moving the per-trade edge.

**Next slice: not another parameter of this family.** Two concrete candidates, in order:

1. **The one-shot entry variant this experiment did not test.** `spec/research/F006-lorentzian-causality.md`
   named two levers: a time-based cooldown (tested here) and firing an entry only on a signal
   *flip* (the library's `startLongTrade`/`startShortTrade` semantics). They are not the same
   thing, and the second is still untested — it removes re-entry into an unchanged call entirely
   rather than deferring it by N bars, and it would also cover the trailing-stop and
   signal-reversal exits that `cooldown_candles` leaves untouched (see the engine detail in
   "Method"). It is cheap, it is the sharpest remaining test of the "wasteful re-entry"
   mechanism, and the per-trade expectancy measured here predicts it will *also* fail to produce
   positive edge — which is exactly why it is worth running: it would settle the re-entry
   question rather than leaving it half-answered.
2. **A different generator family** (Donchian breakout / pullback, per `spec/build.md`), which is
   what the Lorentzian note's own fallback named, since the per-trade-expectancy invariant is a
   statement about the *signals*, not about the engine wrapped around them.

If (1) also leaves per-trade expectancy negative, the honest reading is that no re-entry-shaping
fix exists for this signal set and the budget belongs entirely to (2).
