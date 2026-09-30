# F006 — Higher-timeframe structure gates lower-TF continuation (H-MULTI-TF-PA-01)

> Sections "Observation" through "Method" (including falsification and sample) were written and
> committed BEFORE `multi_tf_pa.py` / `scripts/f006_multi_tf_pa_experiment.py` existed and before
> any backtest was run, per the same pre-registration discipline as every prior F006 hypothesis
> note (`F006-hypothesis-donchian.md`, `F006-hypothesis-cross-sectional-rs.md`,
> `F006-hypothesis-opening-range-breakout.md`, ...). "Run_id", "Result", "Decision" and "Tests"
> are placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.
>
> **Shared harness.** This slice is implemented on top of `scripts/f006_family_runner.py`
> (`spec/research/F006-shared-harness.md`, merged on `main` at `c133fa26d79b5a6989d1f7127700d98b3df3eb80`).
> The frozen `SYMBOLS x INTERVALS` basket, `EXPECTED_CHECKSUMS`, `NO_TRAIL` exit geometry
> (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask, `cooldown_candles=0`,
> `leverage=1`), the `DONCHIAN_55` harness control, the H1 (mean net PnL > 0 across the 10-series
> pool) and H2 (monthly promotion, conditional on H1) checks, and every write under
> `output/f006_<family>/` are **owned by `run_family()`** and are not reimplemented here. This
> note's whole job — per that shared-harness note's "For future F006 tickets" section — is to
> define a signal module with `catalog_entries()`, freeze the candidate names below, and call
> `f006_family_runner.run_family(...)` once from a thin `scripts/f006_multi_tf_pa_experiment.py`.

## Observation

Every F006 family tried so far — the original 85-name catalog sweep, `RVOL_RE_*`, `XS_RS_*`,
`ORB_UTC_*`, `LSWEEP_*`, NR-compression, prior-day high/low, session-VWAP, pivot-breakout,
`BTC_LEAD`, `CVD_DIV`, `KELT_BRK`, `ER_TREND`, `SUPERTREND`, `ICHIMOKU_TK`, `PSAR`, `AROON`,
`CCI`, `STOCH_RSI`, `FISHER`, `WILLR`, `HA_TREND`, `VPVR`, `MFI`, `CMF`, `OBV_DIV`,
`BB_KELT_SQ`, `ZAORSKI_PA`, `ADX_DMI`, `TRIX`, `ULTIMATE_OSC`, `ELDER_RAY`, `REGIME_SW`,
`FORCE_INDEX`, `CHAIKIN_OSC`, the Donchian variants — computes its entry signal from **one
timeframe's own OHLCV**: a rolling extreme, an oscillator threshold, a volume ratio, a session
clock, or (for `ZAORSKI_PA`/`REGIME_SW`) a same-timeframe price-action or volatility-regime
read. `spec/build.md`'s F006 section and this ticket's own catalog list confirm the pattern:
nothing merged or in-flight compares what one timeframe is doing to what a **higher** timeframe
is doing at the same moment. `F006-hypothesis-cross-sectional-rs.md`'s own "Rejected for this
slice" list names this explicitly — *"True multi-TF structure using a higher cached interval:
60→240 is available, but 240 needs 720 and no `*_720_*` manifests exist"* — and defers it rather
than half-building it. This slice does not need a third cached interval: the frozen basket
already carries both `interval=60` and `interval=240` for every symbol, and 240m data has an
exact non-overlapping higher timeframe available for free — the calendar day (6 completed 4h
bars) — without fetching or caching anything new.

**Distinct from every closed/in-flight family in the ticket's catalog list**, mechanically, not
just by name:

- Not another rolling-extreme or oscillator generator on **one** series (Donchian, KELT_BRK,
  NR-compression, ORB, pivot-breakout, session-VWAP all read one timeframe).
- Not `XS_RS`/`BTC_LEAD`/CVD_DIV/MIN_AGREE-style cross-*symbol* agreement — those compare the
  **same** timeframe across different symbols; this compares **different timeframes of the same
  symbol**.
- Not `ZAORSKI_PA` reopened: that family's evidence is gated to a `[14, 17)` UTC-hour window and
  a different level set (session opening range / prior levels within one timeframe); this family
  has no session-hour gate at all and its levels are HTF-block extremes and LTF rolling extremes,
  never a fixed clock window.
- Not a `REGIME_SW` retune: `REGIME_SW` (closed/in-flight elsewhere in the catalog) reads
  same-timeframe volatility/trend regime switches; this family's "regime" is a two-state HTF
  swing-structure bias (higher-high/higher-low vs lower-high/lower-low of completed HTF blocks),
  computed on a **different, coarser** series than the one being traded, and gates entries rather
  than switching between two same-timeframe strategies.
- Sibling in-flight `PCT_B` is not depended on at runtime or in spirit — this family shares no
  code, no level definition and no hypothesis with it.

## Hypothesis

**H1 (new generator, aggregate).** A signal family that first classifies a *higher* timeframe's
completed-block swing structure into a bias (`+1` uptrend structure / `-1` downtrend structure /
`0` undefined-or-mixed), then fires the *lower*-timeframe one-shot continuation or
rejection signal only when it agrees with that bias, produces at least one of the five
pre-registered names below whose **mean net PnL across its 10 `(symbol, interval)` series is
> 0** at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`, one-shot entry mask, `cd=0`,
`leverage=1`) — the same pooling bar every prior F006 H1 check has used.

### HTF definition (frozen before implementation)

- `interval=60` (1h LTF bars) → HTF = **non-overlapping 4h (240m) blocks**, built from the same
  symbol's own OHLCV, calendar-aligned (`floor` to the 4h boundary), not count-aligned — so a
  gap in the LTF series does not desynchronize the block boundary.
- `interval=240` (4h LTF bars) → HTF = **non-overlapping daily (6 × 240m) blocks**, same
  calendar-alignment rule (`floor` to the UTC day boundary).
- A HTF block's high/low is only *usable* starting from the first LTF bar of the **next** HTF
  block — i.e. only after every LTF bar belonging to it has occurred. No signal at LTF bar `i`
  ever reads the still-forming HTF block that bar `i` itself belongs to.
- **HTF bias**, recomputed only when a HTF block completes (constant across every LTF bar of the
  following forming block): letting `P1` = the most recently completed HTF block and `P2` = the
  one before it, bias = `+1` if `P1.high > P2.high` **and** `P1.low > P2.low` (higher-high +
  higher-low); `-1` if `P1.high < P2.high` **and** `P1.low < P2.low` (lower-high + lower-low);
  `0` otherwise (inside bar, outside bar, or fewer than two completed HTF blocks exist yet —
  "undefined" and "mixed" are not distinguished, both are `0`). Bias is **not** carried forward
  from an older completed comparison when the current one is mixed — it is recomputed fresh at
  every HTF block completion from exactly `P1` vs `P2`.
- Causality restated in engine terms: every feature at LTF bar `i` (HTF bias, HTF block
  high/low, LTF rolling extremes) is a function of bars `0..i` only; the signal decided at bar
  `i` is entered on the next bar, exactly like every existing catalog entry and every prior F006
  additive module (`donchian.py`, `lorentzian.py`).
- All crosses below are **strict** (equality does not count as a cross); all other inequalities
  (`bar low <= prior-20 low`, `close >= upper-third boundary`) are written with the non-strict
  operator the ticket specifies and are not "crosses" at all.

### Pre-registered candidate names (exactly these five, encoded before running)

| Name | Definition |
| --- | --- |
| `MTFP_HTF_BRK20` | LTF one-shot long only when HTF bias = `+1` **and** `close` strict-crosses up through the prior-20-LTF-bar high (`high.rolling(20).max().shift(1)`); short only when bias = `-1` **and** `close` strict-crosses down through the prior-20-LTF-bar low (`low.rolling(20).min().shift(1)`); else `0`. |
| `MTFP_HTF_BRK10` | Identical to `MTFP_HTF_BRK20` with `N=10`. |
| `MTFP_HTF_BRK5` | Identical to `MTFP_HTF_BRK20` with `N=5`. |
| `MTFP_HTF_BLOCK` | LTF one-shot continuation on a strict cross of `close` through the prior **completed** HTF block's high (bias `+1`) or low (bias `-1`) — the HTF-block-level analogue of the `BRKn` names, using the just-completed HTF block's own extreme instead of a LTF rolling window. |
| `MTFP_HTF_PIN` | When bias ∈ `{+1, -1}`: long pin/rejection when the bar's own `low <= ` prior-20-LTF-bar low (`shift(1)` rolling) **and** `close` sits in the upper third of that bar's own high-low range, gated to bias `= +1`; short mirror (bar `high >=` prior-20-LTF-bar high, `close` in the lower third of the bar's range, gated to bias `= -1`). Emits `0` whenever HTF bias is undefined (`0`) or the pin condition does not hold. |

Signal domain is `{-1, 0, 1}` on every bar, exactly the shared contract
(`tests/test_signal_family_contract.py`); the shared harness applies the one-shot entry mask on
top, so a "call" is one bar for the cross-based names (`BRK*`, `BLOCK`) by construction, and one
maximal run of an unbroken pin condition for `PIN`.

**H2 (monthly, conditional on H1).** For any name that clears H1, at least one of its 10 series
clears the F005 section-7 monthly promotion checklist (`run_family`'s `promotion_pass`: every
valid month non-negative, all 12 Train-1 months valid, full-window `train1_net_pnl >= 0`, max
drawdown ≤ 50%, `n_trades > 0`).

## Falsification condition (stated before running)

**H1 falsified** if none of the five pre-registered names has positive mean net PnL across its
10-series pool at `NO_TRAIL`.

**H2 falsified** if every H1-clearing name has zero series clearing `promotion_pass`. If H1
fails, H2 is `"not_applicable_h1_failed"` (the shared harness's own `h2_status` value), not
silently passed or skipped.

Do **not** add a sixth name, a different `N`, or an ADX/volatility co-filter after seeing
results. Do **not** depend on `PCT_B` or any other unmerged sibling family. Do **not** reopen
`ZAORSKI_PA`'s `[14, 17)` UTC gate or retune `REGIME_SW`. A negative Result is valid and must be
reported honestly.

## Sample

5 names × 5 symbols × 2 intervals (`240`/`60`) = 50 candidate series, plus `run_family`'s
non-optional `DONCHIAN_55` control on the same 10 `(symbol, interval)` pairs = 60 series total,
Train-1 only, `NO_TRAIL`. Exactly the frozen basket: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `XRPUSDT`,
`DOGEUSDT` × `60m`/`240m`.

## Method

1. Additive module, suggested path `multi_tf_pa.py`, exposing `catalog_entries() ->
   dict[str, Callable[[pd.DataFrame], pd.Series]]` for the five `MTFP_*` names above. Pure OHLC:
   no `advanced-ta` dependency, no third-party import, no change to `strategy.py` or
   `add_indicators` (per the ticket, this family is not merged/wired into production —
   `catalog_entries()` is registered into `strategy.STRATEGY_CATALOG` only at runtime by
   `run_family`, inside the experiment process, the same "never edits `strategy.py`" contract
   `f006_family_runner.register_catalog_entries` already enforces and tests).
2. HTF bias/block-level helper is a private function inside `multi_tf_pa.py`: it infers the LTF
   bar spacing from the frame's own `DatetimeIndex` (median consecutive delta — no `interval`
   string is threaded through `catalog_entries()`'s `fn(df)` signature, matching every other
   family's calling convention in `tests/test_signal_family_contract.py`) and floors timestamps
   to the 4h or 1-day boundary accordingly, then aggregates completed-block high/low with a
   `groupby` + `shift(1)`/`shift(2)` on the block-level series (never a per-bar `transform` used
   before its block has completed) so that every LTF bar in a forming HTF block sees only the
   two previously **completed** blocks.
3. Thin experiment script `scripts/f006_multi_tf_pa_experiment.py`: imports `multi_tf_pa`, builds
   `candidate_names = ["MTFP_HTF_BRK20", "MTFP_HTF_BRK10", "MTFP_HTF_BRK5", "MTFP_HTF_BLOCK",
   "MTFP_HTF_PIN"]`, and calls `f006_family_runner.run_family(family="multi_tf_pa",
   candidate_names=candidate_names, catalog_entries=multi_tf_pa.catalog_entries(),
   hypothesis_note=<pointer to this file>, script_path=__file__)` exactly once. It does not
   reimplement the basket, checksums, exit geometry, harness control, or H1/H2 checks — those are
   `run_family`'s job, unchanged.
4. `tests/test_multi_tf_pa.py`: family-specific formula tests, on top of (not duplicating) the
   shared, family-agnostic `tests/test_signal_family_contract.py`. In particular:
   - a hand-built multi-block OHLC fixture where the expected bias at each LTF bar is derived
     by hand from the printed completed-block high/low table, asserting bias changes **only** on
     the first LTF bar of a new HTF block and is constant across every bar of that block;
   - **no lookahead into the forming HTF block**: mutating only the still-forming block's future
     bars (bars after the current LTF bar but before that HTF block completes) must not move any
     already-computed value at or before the current bar — the same truncation-plus-future-
     perturbation style `tests/test_donchian.py`/`tests/test_lorentzian.py` already use, applied
     specifically at HTF block boundaries rather than generically over the whole frame;
   - strict-cross semantics: a bar that merely stays above/below a level it was already
     above/below the previous bar must not re-fire;
   - `MTFP_HTF_PIN`'s "emit 0 if HTF undefined" clause, asserted on the warm-up bars before two
     HTF blocks have completed;
   - signal domain `{-1, 0, 1}` and no-input-mutation, duplicated locally only as a fast
     regression guard — the authoritative, family-agnostic versions of these two checks stay in
     `tests/test_signal_family_contract.py` and this family is **not** added to that file's
     `FAMILIES` list while unmerged (mirrors the file's own documented "no sibling F006 branch
     module is imported here" rule).
5. Data: the ten bounded Train-1 `data_cache/*_20240126T000000Z_20250301T000000Z.csv` files,
   symlinked from the main checkout's existing frozen cache (never fetched from the network),
   exactly as `spec/research/F006-shared-harness.md` documents for `run_family`'s live proof.
6. After evidence is written under `output/f006_multi_tf_pa/`, refresh
   `scripts/f006_cross_family_digest.py`'s output if the script is present on `main` (it is,
   per this ticket) — additive, no edit to any other family's evidence.
7. No `spec/build.md` edit, no merge to `main`, no production `strategy.py`/`add_indicators`
   change, no holdout access, no network, no retuning after seeing results.

## Run_id

`scripts/f006_multi_tf_pa_experiment.py` via `f006_family_runner.run_family`,
`git_commit_parent = 582f69cc706670e027ac27a62936147bdf45227d`,
`run_started_utc = 2026-09-29T16:31:35Z`, Python 3.10.12, pandas 2.3.3, `n_series = 60`
(5 candidates + `DONCHIAN_55` control, x 10 `(symbol, interval)` series), `elapsed_seconds =
11.3`. Full parameters, checksums, harness-control comparison, H1/H2 tables:
`output/f006_multi_tf_pa/summary/manifest.json`. Per-series rows (60):
`output/f006_multi_tf_pa/summary/results.csv`. Per-series raw JSON (60, including the 12-month
breakdown): `output/f006_multi_tf_pa/raw/`.

## Result

**H1 clears, on all five pre-registered names — the strongest aggregate H1 result any F006
family has produced.** Harness control: `DONCHIAN_55`, 10/10 rows, 0 mismatches against
`output/f006_trailing_boundary/summary/results.csv`. No-trail mechanism check: 0/60 runs
produced a `trailing_sl` exit. One-shot rule: 0 violations (`n_trades <= n_calls` on every run).

| Name | Mean net PnL (10 series) | Profitable series | Total trades |
| --- | ---: | :-: | ---: |
| `MTFP_HTF_BRK20` | **+$45.49** | 7/10 | 978 |
| `MTFP_HTF_BRK10` | +$41.92 | 6/10 | 1270 |
| `MTFP_HTF_BRK5` | +$20.87 | 3/10 | 1387 |
| `MTFP_HTF_BLOCK` | +$36.70 | 6/10 | 1283 |
| `MTFP_HTF_PIN` | +$29.53 | 5/10 | 237 |

All five clear H1 (`h1_falsified = false`). This is the first time every pre-registered name in
a single F006 family has cleared H1 — the catalog-notrail-sweep found 54/77 names positive, but
no single ≤5-name pre-registered family before this one has gone 5/5.

**The result is not evenly spread — it is concentrated in interval and in symbol, and that
concentration is the real finding, not the mean.** Splitting the same 10-series pool by
interval:

| Name | Mean net PnL, 4h (5 series) | Mean net PnL, 1h (5 series) |
| --- | ---: | ---: |
| `MTFP_HTF_BRK20` | **+$101.52** | -$10.54 |
| `MTFP_HTF_BRK10` | **+$107.26** | -$23.43 |
| `MTFP_HTF_BRK5` | **+$84.06** | -$42.31 |
| `MTFP_HTF_BLOCK` | **+$109.69** | -$36.30 |
| `MTFP_HTF_PIN` | +$1.08 | **+$57.98** |

Four of five names (everything except `MTFP_HTF_PIN`) are net **negative** at 1h and the
aggregate H1 pass is carried entirely by 4h; `MTFP_HTF_PIN` is the mirror case, flat at 4h and
positive only at 1h. And within 4h, per-symbol means show two symbols carrying the family:

| Symbol | Mean net PnL, 4h (5 names) | Mean net PnL, 1h (5 names) |
| --- | ---: | ---: |
| `XRPUSDT` | **+$178.27** | **+$76.56** |
| `DOGEUSDT` | **+$184.40** | +$24.05 |
| `BTCUSDT` | +$24.34 | -$39.04 |
| `SOLUSDT` | +$9.76 | -$52.86 |
| `ETHUSDT` | +$6.84 | -$63.31 |

`XRPUSDT` and `DOGEUSDT` are positive in both cells for every name; `BTCUSDT`/`SOLUSDT`/`ETHUSDT`
are small-positive-to-negative at 4h and clearly negative at 1h for four of the five names. The
aggregate mean net PnL that clears H1 is real (computed exactly as pre-registered, no cherry-
picking after the fact — H1 was checked on the full 10-series pool per name, not on a subset),
but it would not have cleared on a basket without `XRPUSDT`/`DOGEUSDT`, and it would not have
cleared on the `60m` interval alone for four of the five names.

**H2 falsified, 0/60 series.** Best single series by monthly losing-month count:
`MTFP_HTF_BRK10`/`SOLUSDT`/4h, 3 losing months of 12 (`train1_net_pnl = +$52.92`, 49 trades, max
drawdown 9.18%) — better than this family's own median but **not** better than the best single
series ever measured in F006 (`DONCHIAN_PULLBACK_55`/`DOGEUSDT`/1h and
`DONCHIAN_55`/`DOGEUSDT`/1h, 2 losing months, per `F006-hypothesis-donchian.md` and
`F006-catalog-notrail-sweep.md`). No series in this family reaches 2 losing months or clears
`promotion_pass` (`n_valid_months=12` on every one of the 60 series; the checklist fails purely
on the losing-month clause).

## Decision

**H1 holds mechanically as pre-registered — a genuinely new generator, HTF swing-structure bias
gating LTF continuation/rejection, produces positive aggregate expectancy on every one of its
five candidate names, the first ≤5-name F006 family to do so.** That is a real, checked result
(harness control exact, zero one-shot violations, zero trailing exits, H1 computed on the full
pre-registered 10-series pool with no post-hoc name pruning) and it should be recorded as such
rather than discounted because H2 falsified — **every** F006 family measured so far has failed
H2's zero-tolerance monthly rule, including this one's own strongest single series.

**What should not be concluded from this run:** that HTF structure gating is a basket-general
edge. It is not, on this evidence. The positive aggregate is carried almost entirely by
`XRPUSDT`/`DOGEUSDT` and by the `240m` interval; `BTCUSDT`/`ETHUSDT`/`SOLUSDT` at `60m` are
negative for four of the five names. A follow-up that re-tuned `N` or added a sixth variant
chasing this concentration would be exactly the "no sixth name / no retune after seeing results"
the falsification section forbids, so none is proposed here.

**Recommendation, stated narrowly:** this family is evidence that a genuinely new mechanism
(cross-timeframe structure, not a same-timeframe rolling extreme/oscillator/volume rule) can
clear H1 where dozens of same-timeframe names have not — but H2's monthly bar remains unclearable
by any F006 mechanism tried to date, momentum or structure-gated. That is now the ninth
independent axis (entry generator, exit geometry, entry filter, position sizing, re-entry
cooldown, take-profit, cross-symbol agreement, mean-reversion, and now cross-timeframe gating) to
clear H1 partially or fully and fail H2, which is itself information: the monthly zero-tolerance
criterion, not any one signal family, may be the binding constraint, and that is a decision for
the ticket owner rather than a further F006 slice on this family.

**What is reusable regardless of that conclusion:** `multi_tf_pa.py`'s HTF bias/block-level
helper (`_htf_bias_and_block_levels`) is causal by construction (tested at the block-boundary
seam specifically, not just generically), free of any third-party dependency, and available at
no cost to any later slice that wants a HTF-structure gate on a different LTF generator. It is
**not** wired into `strategy.py` and must stay that way until (if ever) a coordinator decision
merges it.

**Falsification verdict, restated for the record**: H1 **not falsified** (5/5 names positive,
against the falsification bar of "none positive"). H2 **falsified** (0/60 series clear
`promotion_pass`, against the bar of "every H1-clearing name has zero clearing series" — met).

## Tests

`tests/test_multi_tf_pa.py` (32 new tests): HTF frequency inference (1h→4h blocks, 4h→daily
blocks); a 20-bar hand-derived fixture asserting `_htf_bias_and_block_levels`'s bias is constant
per HTF block and matches a by-hand comparison of completed blocks 0-4 (`0,0,0,0, 0,0,0,0,
1,1,1,1, 1,1,1,1, -1,-1,-1,-1`); `MTFP_HTF_BLOCK`'s exact signal on the same fixture
(`0×9, +1@bar9, 0×7, -1@bar17, 0×2`); a dedicated no-lookahead-into-the-forming-block test that
perturbs only later bars of a still-forming HTF block and asserts every earlier bar's bias/signal
is unchanged; strict-cross-does-not-refire on the same fixture; `MTFP_HTF_BRK20/10/5` cross-
checked against an independently re-derived expected series with the bias-consistency invariant
asserted on every fired bar; `MTFP_HTF_PIN`'s bias-gating isolated via a monkeypatched bias
series so three bars share **identical** pin-candle geometry and only the gate differs (bias
undefined → 0, `+1` → fires long, `-1` → fires short); signal-domain (`{-1, 0, 1}`) and
no-input-mutation checks parametrized over all five names on the real 600-bar 4h fixture; generic
prefix-truncation and future-perturbation causality checks (prefixes 150/300/450), the same style
`tests/test_donchian.py`/`tests/test_lorentzian.py` use, parametrized over all five names.

Not added to `tests/test_signal_family_contract.py`'s `FAMILIES` list: `multi_tf_pa.py` is an
unmerged sibling module, and that file documents (and enforces via its own `FAMILIES` list) that
no unmerged sibling module is imported there.

Full suite, before and after this slice, on this worktree's `.venv_test` (Python 3.10.12,
system-site-packages, no network — `.venv_test` did not exist in this fresh worktree and was
built locally rather than symlinked from the main checkout, per harness discipline; `pip` was not
needed since `pandas`/`numpy`/`pytest` are already present as system packages matching the
versions used elsewhere in this ticket's evidence):

| | Baseline (this slice's tests excluded) | With this slice |
| --- | --- | --- |
| `pytest tests/` | 220 passed, 8 skipped | **253 passed, 7 skipped** |

33 net new passing tests (32 new in `tests/test_multi_tf_pa.py`, plus one pre-existing
`test_signal_family_contract.py` test —
`test_run_family_always_covers_the_frozen_basket_and_control` — that was previously skipped for
lack of local CSVs and now runs live once this slice's symlinked
`data_cache/*_20240126T000000Z_20250301T000000Z.{csv,manifest.json}` files exist, unrelated to
`multi_tf_pa.py` itself). No behaviour change in any pre-existing test.
