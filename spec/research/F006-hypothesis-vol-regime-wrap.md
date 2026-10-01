# F006 — Hypothesis: realized-vol-percentile regime wraps a frozen Donchian trigger

> Sections up to and including "Freeze (stated before any code)" and "Falsification condition"
> were written and committed BEFORE the signal module / experiment script existed and before any
> backtest ran, per the same pre-registration discipline as every prior F006 hypothesis note.
> "Run_id", "Result", "Decision", and "Tests" are placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice, run through `scripts/f006_family_runner.py`'s
> `run_family()` (shared harness, `spec/research/F006-shared-harness.md`, main tip `442b246`):
> `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)` plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. H1 gates on `train1_net_pnl`, never diagnostic full-run `net_pnl`.
> Validation 1-4 and the Holdout window are not loaded, not sliced and not looked at.

## Owner freeze card (verbatim, `/tmp/F006-card-H-VOL-REGIME-WRAP-01.md`)

```
# H-VOL-REGIME-WRAP-01 — Realized-vol regime wraps a frozen PA trigger

id: H-VOL-REGIME-WRAP-01
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}
data_needs: ohlcv only
harness: main tip 442b246 — H1 gates on mean train1_net_pnl; DONCHIAN_55 control; NO_TRAIL

## market_read
Same setup trades differently in low-vol grind vs high-vol expansion. Prop / bot literature cuts
frequency or flips to breakout-only when realized vol percentile is high. Learns from REGIME_SW
failure: do **not** retune HHHL↔BB switch — wrap a *different* non-DNR trigger under
pre-registered vol buckets.

## freeze before code (≤5 catalog names)
Causal realized vol percentile (ATR% or stdev of returns; lookback frozen). Buckets LOW / MID /
HIGH with hysteresis.
Attach **one** frozen simple trigger that is **not** prior-day HL, not ORB, not Zaorski HHHL, not
LSWEEP, not REGIME_SW geometry.
Names (examples to freeze in ticket): trigger only in HIGH (breakout mode); only in LOW
(mean-revert mode); MID flat / no-trade. ≤5 names.
Fill open i+1; NO_TRAIL.

Propose and freeze exact vol lookback, percentile edges, hysteresis, the single trigger
definition, and ≤5 catalog names IN THE TICKET before writing the module. Do not retune after
Train-1.

## falsifiers
H1 mean train1_net_pnl ≤ 0; H2 no monthly-clean; bucket uses future bars; reopens
ER_TREND/ADX as the *trade* rather than regime label; reopens REGIME_SW HHHL↔BB geometry.

## do_not_overlap
ER_TREND / ADX_DMI closed as trade families — ER/ATR **only as regime label**.
Not REGIME_SW geometry retune. Not ORB / prior-day HL / session-VWAP / ZAORSKI_PA / LSWEEP /
BB_KELT_SQ / KELT_BRK.
```

## Observation

`spec/research/F006-hypothesis-entry-regime-filter.md` falsified an ADX14-threshold entry gate
on the *existing* trend/momentum catalog (net-PnL gain traced to trade-count reduction, not
selection quality; zero of 500 runs profitable). `spec/build.md`'s stated F006 direction after
that and after `spec/research/F006-hypothesis-donchian.md` is new *generator* mechanisms, not
another filter tuned on the same signal family. Realized-vol-percentile regime switching is a
different generator-level mechanism from a static indicator threshold: it changes *which mode*
(breakout vs mean-revert vs flat) a trigger operates in as a function of a causal, hysteresis-
smoothed vol state, rather than gating the same directional call on/off with a fixed threshold.
The owner's card explicitly rules out retuning the closed `REGIME_SW` HHHL↔BB switch — this
hypothesis wraps a *different*, DNR-clean base trigger (Donchian breakout, already a closed,
merged F006 catalog entry, `donchian.py`) instead.

## Hypothesis

**H1 (aggregate, gated on `train1_net_pnl`).** A causal realized-vol-percentile regime label
(LOW/MID/HIGH, with hysteresis) that switches a frozen Donchian(20) breakout trigger between
breakout mode (HIGH), mean-revert/faded mode (LOW), and flat (MID) produces at least one of the
three frozen names below whose **mean `train1_net_pnl` across the 10 `(symbol, interval)`
series is > 0** at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask,
`cooldown_candles=0`, `leverage=1`), via `scripts/f006_family_runner.py`'s `run_family()`.

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10 series
clears the shared harness's Train-1 monthly promotion checklist (`promotion_pass` in
`_run_one`'s frozen schema: `max_drawdown_pct <= 50`, all valid months net-PnL >= 0, 12/12 valid
months, `train1_net_pnl >= 0`, `n_trades > 0`).

## Freeze (stated before any code)

**Realized-vol proxy.** `atr_pct[i] = ATR14[i] / close[i]`, where `ATR14` is the Wilder-style
`ewm(span=14, adjust=False).mean()` of true range over bars `0..i` only — the same smoothing
convention `strategy.py`'s `add_indicators` uses for `atr14`, but computed self-contained inside
the new module from raw OHLC (no `add_indicators` dependency, matching `donchian.py`'s and
`lorentzian.py`'s additive-module pattern). Causal: `ewm` at bar `i` is a function of bars
`0..i` only.

**Vol percentile.** `pct[i]` = the percentage of values in the trailing window
`atr_pct[max(0, i-99) .. i]` (window `W = 100` bars, inclusive of bar `i` itself) that are
`<= atr_pct[i]`. `pct[i]` is `NaN` while fewer than `W` bars are available (bars `0..98`).
Causal: every value the rank at bar `i` compares against is drawn from bars `<= i`; appending
bars after `i` cannot change `pct[i]` (rolling-window rank, not a global/expanding
min-max — no L1-style whole-frame leak of the kind `lorentzian.py`'s docstring warns about).

**Buckets + hysteresis (single left-to-right state machine, one pass, no relabeling of past
bars).** Edges `LOW_EDGE = 25`, `HIGH_EDGE = 75` (percentile points); hysteresis margin
`HYST = 10` points, so a bucket exit requires crossing back past `edge ∓ HYST`, not merely past
the edge itself:

- Regime starts at `MID` (also `MID` while `pct[i]` is `NaN`, i.e. bars `0..98`).
- From `MID`: enter `HIGH` if `pct[i] >= 75`; enter `LOW` if `pct[i] <= 25`; else stay `MID`.
- From `HIGH`: exit to `LOW` if `pct[i] <= 25`; exit to `MID` if `pct[i] < 65` (`75 - HYST`);
  else stay `HIGH`.
- From `LOW`: exit to `HIGH` if `pct[i] >= 75`; exit to `MID` if `pct[i] > 35` (`25 + HYST`);
  else stay `LOW`.

**Frozen base trigger (the ONE attached simple trigger).** `donchian.sig_donchian_breakout(df,
20)` — Donchian(20) breakout, already a closed, merged F006 catalog entry (`DONCHIAN_20`,
`donchian.py`). Not prior-day HL, not ORB, not Zaorski HHHL, not LSWEEP, not `REGIME_SW`
geometry — satisfies the card's DNR list. Called as the raw module function, not through
`strategy.STRATEGY_CATALOG`, so this module depends only on an already-merged sibling family,
per the shared-harness "must not depend on any unmerged sibling family module at runtime" rule.

**Wrap logic (≤ 5 frozen catalog names — 3 used):**

| Name | HIGH bucket | MID bucket | LOW bucket |
| --- | --- | --- | --- |
| `VOLW_HIGH_BRK_20` | Donchian(20) direction as-is (breakout mode) | 0 | 0 |
| `VOLW_LOW_MR_20` | 0 | 0 | **inverted** Donchian(20) direction (fade the breakout — mean-revert mode) |
| `VOLW_HL_20` | Donchian(20) direction as-is | 0 | inverted Donchian(20) direction |

`ER_TREND`/`ADX_DMI` are not used anywhere in this generator; realized-vol-percentile is used
only as the regime label switching *which mode* the Donchian trigger runs in, never as the trade
signal itself — no ER/ADX closed-family trade reopens here.

**Fill / geometry.** Fill at bar `open[i+1]` (one-shot entry mask + `run_family`'s own next-bar
engine fill, unchanged), `NO_TRAIL` (owned by `run_family`: `activate_pct=10.0`, `trail_pct`
moot since it never arms, `max_sl_pct=0.03`, `cooldown_candles=0`, `leverage=1`).

No parameter in this section (`ATR_P=14`, `W=100`, `LOW_EDGE=25`, `HIGH_EDGE=75`, `HYST=10`,
Donchian `n=20`) is retuned after Train-1 results are seen.

## Falsification condition (stated before running)

**H1 falsified** if none of the three frozen names has mean `train1_net_pnl > 0` across its
10-series pool.

**H2 falsified** if every H1-clearing name has zero series with `promotion_pass = True`. If H1
fails, H2 is "not applicable — H1 failed", not silently passed/failed.

Also falsified (mechanism-level, checked by tests / the shared contract, not by results): the
regime label uses a future bar (contract's causality/future-perturbation test on
`tests/test_signal_family_contract.py`, parametrized over this family), or the module trades
ER/ADX directly, or it retunes `REGIME_SW`'s HHHL↔BB switch geometry (it does not — no
`REGIME_SW` code is touched or imported).

## Sample

3 names × 5 symbols (`SOLUSDT`/`ETHUSDT`/`BTCUSDT`/`XRPUSDT`/`DOGEUSDT`) × 2 intervals
(`240`/`60`) = 30 series, Train-1 only, via `run_family()`. Plus `run_family`'s always-on
`DONCHIAN_55` harness control (10 series) proving the run reproduces the frozen NO_TRAIL numbers
before trusting the new names — `run_family` owns this; it is not a caller-configurable
kwarg.

## Method

1. New additive module `vol_regime_wrap.py`, same pattern as `donchian.py`/`lorentzian.py`:
   exposes `catalog_entries() -> dict[str, Callable[[pd.DataFrame], pd.Series]]`, is imported and
   `STRATEGY_CATALOG.update(...)`-registered at the bottom of `strategy.py`, changes nothing in
   any existing entry, imports `donchian` (already-merged sibling) for the base trigger only.
2. Unit tests, `tests/test_vol_regime_wrap.py`: hand-built OHLCV fixture proving (a) `atr_pct`/
   `pct` match a hand-derived table at a small window, (b) the hysteresis state machine's exact
   bucket transitions on a hand-built vol path (enter HIGH, stay through a dip that doesn't clear
   the hysteresis band, exit at the hysteresis edge; same for LOW), (c) `VOLW_HIGH_BRK_20`/
   `VOLW_LOW_MR_20`/`VOLW_HL_20` emit the frozen table above bucket-by-bucket, (d) no lookahead
   (prefix truncation + future-bar perturbation, same discipline as `tests/test_donchian.py`),
   (e) additive-only regression (registering the family leaves every other catalog entry
   byte-identical, mirrors `tests/test_signal_family_contract.py`'s generic check for this
   family too since it is parametrized over "every family module currently registered in
   production").
3. Experiment script `scripts/f006_vol_regime_wrap_experiment.py`: registers
   `vol_regime_wrap.catalog_entries()`, calls `f006_family_runner.run_family(family=
   "vol_regime_wrap", candidate_names=["VOLW_HIGH_BRK_20", "VOLW_LOW_MR_20", "VOLW_HL_20"],
   catalog_entries=vol_regime_wrap.catalog_entries(), hypothesis_note=..., script_path=...)`
   exactly once. Does not copy the harness loop, does not reimplement `SYMBOLS`/`INTERVALS`/
   `EXPECTED_CHECKSUMS`/`_run_one`/`verify_harness_control`/H1/H2.
4. Evidence under `output/f006_vol_regime_wrap/{raw,summary}/` per the frozen result schema.
   Manifest's `git_commit` must be the commit that produced the run; if the packaging/evidence
   commit differs from the run commit, the note says so honestly rather than papering over it.
5. Fill Result / Decision / Run_id / Tests after the run; commit evidence. Stop after evidence —
   no merge, no `spec/build.md` edit, no holdout access, no exchange keys, no network.

## Run_id

Script: `scripts/f006_vol_regime_wrap_experiment.py`. `run_timestamp_utc = 2026-09-29`.
`git_commit = 7deae4f4383d53ff03d312b72e0957ec82d114c3` (the commit that added
`vol_regime_wrap.py`/the experiment script/the tests and produced these numbers --
`output/f006_vol_regime_wrap/summary/manifest.json`'s own `git_commit` field records
this exactly; the experiment was re-run after that commit specifically so the
manifest would not point at the ticket-only pre-registration commit). Packaging tip
for this evidence commit: `spec/research/F006-hypothesis-vol-regime-wrap.md`'s own
Result/Decision fill-in commit is necessarily one commit AFTER `7deae4f` (this file
cannot commit itself), so the packaging tip SHA on the branch will be newer than
`git_commit` -- noted honestly per the ticket's instruction, not implying the code
changed between the two commits (`vol_regime_wrap.py`/`strategy.py`/the experiment
script/`tests/test_vol_regime_wrap.py`/`tests/test_donchian.py` are unchanged
between them). `elapsed_seconds = 10.4`, `n_series = 40` (3 candidates + `DONCHIAN_55`
control, x 10 symbol/interval series). Full parameters/checksums:
`output/f006_vol_regime_wrap/summary/manifest.json`. Full per-series results:
`output/f006_vol_regime_wrap/summary/results.csv` (40 rows, committed directly).
Harness control (`DONCHIAN_55`): 10/10 rows matched `output/f006_trailing_boundary/
summary/results.csv` with 0 mismatches. NO_TRAIL mechanism check: 0/40 runs produced
a `trailing_sl` exit. One-shot violations: 0/40.

## Result

**H1 (mean `train1_net_pnl` across the 10-series pool):**

| Strategy | Mean train1_net_pnl | Sum | Profitable series | Total trades | H1 |
| --- | ---: | ---: | ---: | ---: | --- |
| `VOLW_HIGH_BRK_20` | **+$59.65** | $596.51 | 5/10 | 886 | **PASS** |
| `VOLW_LOW_MR_20` | -$2.88 | -$28.77 | 4/10 | 1245 | FAIL |
| `VOLW_HL_20` | **+$1.40** | $13.98 | 4/10 | 2264 | **PASS** |

**H1 clears** for `VOLW_HIGH_BRK_20` (mean +$59.65/series, driven mostly by
`XRPUSDT`/`DOGEUSDT` on both intervals: +$272.42, +$205.23, +$199.49, +$123.65
against three losing series on `SOLUSDT`/`ETHUSDT` in the -$27 to -$80 range) and,
more marginally, for the combined `VOLW_HL_20` (mean +$1.40, effectively a coin
flip in aggregate: `BTCUSDT_240` +$68.97 and `XRPUSDT_240` +$138.44 offset by
`SOLUSDT_60` -$92.82 and `XRPUSDT_60` -$98.52). `VOLW_LOW_MR_20` (the LOW-bucket
fade-only variant) is aggregate-negative and falsified on its own -- fading the
Donchian(20) breakout in the LOW-vol bucket does not work as a standalone mode at
these frozen parameters.

**H2 (monthly promotion checklist, H1-passing names only):** checked across all 20
series of `VOLW_HIGH_BRK_20` + `VOLW_HL_20` (`output/f006_vol_regime_wrap/summary/
manifest.json`'s `h2_table`). **Zero of 20 series pass.** Every series has at least
3 negative-PnL valid months out of 12 (range 3-10 negative months; the best case,
`BTCUSDT_240` on `VOLW_HL_20`, still has 3 losing months and the aggregate-best
`XRPUSDT_240`/`VOLW_HIGH_BRK_20` has 6). No series comes close to the zero-tolerance
"every valid month net-PnL >= 0" bar despite several clearing the much weaker H1
aggregate-positive bar.

**Falsification check:** H1 is NOT falsified (2 of 3 frozen names clear
mean-train1-net-PnL > 0). H2 IS falsified (0/20 H1-passing series clear the monthly
checklist). The mechanism-level falsifiers (future-bar bucket, ER/ADX-as-trade,
`REGIME_SW` geometry reopened) do not apply -- none occurred; `tests/
test_vol_regime_wrap.py`'s causality tests and the module's design (no ER/ADX
import, no `REGIME_SW` import) rule them out structurally, not just empirically.

## Decision

**H1 clears, H2 does not -- the same pattern as every prior F006 hypothesis that has
cleared H1 on this basket.** The vol-regime wrap on a frozen Donchian(20) trigger
produces real, non-trivial aggregate Train-1 edge for `VOLW_HIGH_BRK_20`
(concentrated in `XRPUSDT`/`DOGEUSDT`, the two higher-beta names in the basket,
consistent with the market-read mechanism -- breakout-only in the HIGH-vol bucket
suits the more volatile names), but that edge is not clean enough month-to-month to
clear the zero-tolerance monthly bar on any of its 10 series (nor on `VOLW_HL_20`'s
10). `VOLW_LOW_MR_20`'s standalone failure additionally rules out "fade the
breakout trigger in the LOW-vol bucket" as a working mean-revert mode at these
frozen edges/hysteresis -- the market-read's mean-revert half of the mechanism is
not supported here, only the breakout-in-HIGH-vol half shows aggregate promise.

**Do not retune** `LOW_EDGE`/`HIGH_EDGE`/`HYSTERESIS`/`PCT_WINDOW`/`ATR_PERIOD`/
Donchian `n` after this Train-1 result, per the ticket's freeze. This closes
H-VOL-REGIME-WRAP-01 at these frozen parameters: real aggregate H1 edge on the
breakout-only wrap, no clean monthly series, consistent with every other F006
family's H1-clears/H2-fails outcome so far. A narrow, pre-justified follow-up this
Result itself surfaces (not pursued in this slice, per "stop after evidence"): the
HIGH-bucket breakout mode's edge concentrates in exactly 2 of 5 symbols
(XRPUSDT/DOGEUSDT), which is a symbol-selection signal the aggregate H1 number
hides -- a future ticket could test whether a narrower symbol subset (not a
retuned threshold) produces a cleaner monthly series, but that is a new
pre-registration, not this one.

## Tests

`tests/test_vol_regime_wrap.py` (17 tests, all new, all passing): `atr_pct`/
`vol_percentile` verified against an independently written reference
implementation (plain-Python loop, not `pandas.rolling().apply()`); the hysteresis
state machine's exact transitions on a hand-built vol path (forced MID during
warm-up, a single contiguous HIGH run, eventual LOW tail once the wide-range phase
ages out of the trailing window, HIGH fully ends before the LOW tail begins); the
three wrapped names' bucket-by-bucket output verified against `vol_regime`'s own
bucket array and `donchian.sig_donchian_breakout`'s direction on the shared
600-bar fixture; no-lookahead (prefix truncation at 150/300/450 + future-bar
perturbation, parametrized over all 3 names); no input-frame mutation; additive-only
registration (a 15-name sample of pre-existing catalog entries unchanged) and exact
name-set check. `tests/test_donchian.py`'s hardcoded catalog-count assertion
updated 85 -> 88 (79 F005 baseline + 2 Lorentzian + 4 Donchian + 3 this slice) --
a family-specific regression test, not the shared
`tests/test_signal_family_contract.py`/harness/digest files, which were not
touched. Full suite: `pytest tests/` -> 239 passed, 7 skipped (baseline 170
passed/7 skipped per the shared-harness note, +69 from prior F006 slices/this one
since main tip; the live frozen-basket/control test in
`tests/test_signal_family_contract.py` runs, not skips, here because the bounded
Train-1 CSVs were symlinked from the main checkout's `data_cache` per the ticket's
hard rules). No regression in any pre-existing test.
