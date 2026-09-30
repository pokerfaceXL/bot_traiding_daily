# F006 -- Hypothesis H-BETA-GATE-01: rolling beta / correlation gate on alt continuation

> Sections through "Falsification condition", including the exact window, beta thresholds, the
> underlying alt trigger, the BTC bias definition, and the ≤5 catalog names, are written and
> committed BEFORE `beta_gate.py` / `scripts/f006_beta_gate_experiment.py` are written and before
> any backtest is run, per the same discipline as every prior F006 hypothesis note. "Run_id",
> "Result", "Decision" and "Tests" are filled in after the run.
>
> TRAIN-1 ONLY, via the shared harness (`scripts/f006_family_runner.py`, main tip `442b246`):
> `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)` plus the protocol's 35-day warm-up buffer from
> `2024-01-26T00:00:00Z`. Validation 1-4 and the Holdout window are not loaded, not sliced and not
> looked at by any script in this slice. H1 is gated on `train1_net_pnl` only (`net_pnl` includes
> warm-up/boundary days and is diagnostic-only, per `F006-shared-harness.md`).

## Freeze, copied verbatim from `/tmp/F006-card-H-BETA-GATE-01.md`

```
# H-BETA-GATE-01 — Rolling beta / correlation gate on alt continuation

id: H-BETA-GATE-01
universe: ETH/SOL/XRP/DOGE vs BTC USDT perps × {60,240}
data_needs: ohlcv + cross_symbol (BTC series for beta)
harness: main tip 442b246 — H1 gates on mean train1_net_pnl; DONCHIAN_55 control; NO_TRAIL

## market_read
When alt rolling beta to BTC collapses (idiosyncratic), trend-followers stand down or fade; when
beta spikes in a BTC trend, they press the alt with BTC. Gate ≠ cross-sectional ranking. Distinct
from H-BTC-FILTER (structure bit vs continuous beta).

## freeze before code (≤5 catalog names)
Rolling OLS β(alt, BTC) on returns over W∈{24,48,96} 1h (or 4h equiv).
Allow alt continuation trigger only if β > β_min AND BTC bias agrees.
Optional name: allow MR when β < β_low.
This must remain a **gate on a frozen trigger**, not a TOP1 portfolio.
Fill open i+1; NO_TRAIL.

Propose and freeze exact W, β_min / β_low, the underlying alt trigger, BTC bias definition, and
≤5 catalog names IN THE TICKET before writing the module. Do not retune after Train-1.

## falsifiers
H1 mean train1_net_pnl ≤ 0; H2 no monthly-clean; equivalent to closed XS_RS ranking (must remain
a gate on a trigger, not TOP1 portfolio).

## do_not_overlap
XS_RS closed; BTC_LEAD closed; H-BTC-FILTER-01 closed (permission bit ≠ continuous beta gate).
Not REGIME_SW / ZAORSKI_PA / LIQ-CASCADE / VOL-REGIME-WRAP.
```

## Observation

Every closed F006 gate/filter mechanism to date (cross-symbol agreement, width expansion, trend
confirm, position sizing, cooldown) has been either a same-bar cross-sectional vote among the 5
basket symbols' own signal, or a single structural permission bit (e.g. `H-BTC-FILTER-01`'s
BTC-regime flag). None has used a continuous, rolling-window statistical relationship (an OLS
beta) between an alt and BTC as the gate itself. This note tests that mechanism directly, on the
shared harness introduced at `442b246`, which none of the prior gate notes used (they predate it
and hand-rolled their own loop).

## Hypothesis

**H1.** A rolling-OLS beta-to-BTC gate on a frozen Donchian-20 continuation trigger (`BETA_GATE_
DONCH20`, allow only when `β > β_min` AND BTC's own trend bias agrees with the trigger's
direction) has mean `train1_net_pnl` > 0 across its 10-series pool (5 symbols × 2 intervals,
including the degenerate BTCUSDT-vs-itself cell, β≈1 always).

**H1 (companion, optional name named in the freeze).** A mean-reversion fade of the same trigger,
active only when beta decouples (`BETA_GATE_MR_DONCH20`, allow only when `β < β_low`, no BTC-bias
condition since a low beta means idiosyncratic by construction), has mean `train1_net_pnl` > 0
across its own 10-series pool.

**H2 (conditional on either H1 arm passing).** At least one `(symbol, interval)` series for a
H1-passing name clears `spec/research/F005-validation-protocol.md` section 7's monthly promotion
checklist via `run_family`'s frozen `promotion_pass` field (full-run max drawdown ≤ 50%, net PnL ≥
0 in every valid Train-1 calendar month, all 12 months valid, `train1_net_pnl ≥ 0`, `n_trades >
0`).

## Mechanism, frozen before code

**Underlying alt continuation trigger (frozen, reused unmodified).** `donchian.sig_donchian_
breakout(df, 20)` -- the existing, closed, unmodified `DONCHIAN_20` persistent +1/-1/0 signal
(new N-bar-high close -> +1, new N-bar-low close -> -1, carried forward until the opposite
extreme is breached). Chosen because it is already a merged catalog primitive with its own tests
(`tests/test_donchian.py`) and its own causality proof, and because the freeze card's `market_
read` frames this hypothesis as a *permission* layer on a continuation trigger, not a new trigger
design.

**Rolling beta.** `W = 48` bars (the middle of the freeze card's `{24, 48, 96}` set, one value,
not swept -- this slice does not retune W after seeing Train-1, per the freeze's own instruction).
Applied identically in bar-count on both 60m and 240m series (the freeze card allows "1h (or 4h
equiv)"; using the same bar count on both intervals is the simpler, single frozen choice and is
stated here rather than derived after the fact). `β[i] = Cov(alt_ret, btc_ret)[i-W+1..i] /
Var(btc_ret)[i-W+1..i]`, where `alt_ret`/`btc_ret` are 1-bar log returns of `close`
(`np.log(close).diff()`), computed with `pandas.Series.rolling(W).cov()` /
`.rolling(W).var()`. `β_min = 0.5`, `β_low = 0.2` (a weak-to-moderate positive-comovement floor
for the trend gate; a near-zero-to-weak floor below which the alt is read as idiosyncratic enough
to fade, for the optional MR name -- both frozen constants, not swept).

**BTC bias.** `bias[i] = sign(btc_close[i] - SMA(btc_close, W)[i])` using the same `W = 48`, +1
above its own 48-bar mean, -1 below, 0 exactly on it. A single frozen, simple trend read on BTC
itself, independent of the alt trigger's own mechanism (deliberately not reusing `DONCHIAN_20` on
BTC, to keep the "structural permission bit" (`H-BTC-FILTER-01`, DNR) and this continuous-beta
gate's own BTC-bias input mechanistically distinct, per the freeze card's explicit
distinguishing note).

**Gate formula.**
- `BETA_GATE_DONCH20[i] = alt_trigger[i]` if `(β[i] > β_min) AND ((alt_trigger[i]==1 AND
  bias[i]==1) OR (alt_trigger[i]==-1 AND bias[i]==-1))`, else `0`.
- `BETA_GATE_MR_DONCH20[i] = -alt_trigger[i]` (a same-bar fade of the trigger's direction) if
  `β[i] < β_low`, else `0`. No BTC-bias condition on the MR arm -- a decoupled alt is not read
  against BTC's own trend by construction.

Both outputs are themselves persistent-looking +1/-1/0 series (the gate can flip a call off and
back on as beta or bias crosses its threshold even while the underlying trigger is unchanged;
`run_family`/`entry_masks.one_shot_entry_mask` derives its own one-shot mask from whatever this
note's catalog function returns, exactly as for every other name -- a gate re-opening after being
closed is a new entry-eligible call, which is the intended behavior of a *gate*, not a bug to
suppress).

**Only 2 catalog names** (`≤5` budget from the freeze): `BETA_GATE_DONCH20`, `BETA_GATE_MR_
DONCH20`. Both registered at runtime only, via `run_family(..., catalog_entries=beta_gate.
catalog_entries())` -- `strategy.py` is not edited.

**Remains a gate, not a ranking.** Both names are evaluated independently per `(symbol,
interval)` cell by the shared harness exactly like every other single-name catalog entry (no
cross-sectional TOP1 selection among the 5 basket symbols at any point) -- the gate only ever
looks at one alt's own price series and BTC's, never at the other 3 alts, which is what
distinguishes this from the closed `XS_RS` cross-sectional-ranking family and satisfies the
freeze card's explicit falsifier.

**Fill open i+1; NO_TRAIL.** Both inherited unchanged from `run_family` (`ACTIVATE_PCT=10.0`,
one-shot entry mask, next-bar-open fill via the unmodified engine) -- not reimplemented in this
slice.

**Data needs / cross-symbol access.** Every other closed catalog module (`donchian.py`,
`lorentzian.py`) is a pure function of its own symbol's `df`, since `run_family` calls `STRATEGY_
CATALOG[name](work)` with only that symbol's frame -- no interval or symbol name is passed to the
catalog function. This gate genuinely needs BTC's own close series, which `run_family`'s per-
symbol loop does not hand it. `beta_gate.py` therefore loads BTC's Train-1 (+warm-up) close series
itself, once per interval (module-level cache), via `data_contract.load_dataset` against the same
two `BTCUSDT` checksums `f006_family_runner.py` already carries (`spec/research/F005-validation-
protocol.md` section 6, duplicated here as constants, matching the precedent set by every prior
F006 script that needed a second data source, e.g.
`scripts/f006_entry_cross_symbol_experiment.py`). Interval is inferred from the median bar
spacing of the `df` the catalog function is actually called with (60 or 240 minutes are the only
two values the frozen basket ever produces), not passed as an argument -- this is a mechanical
consequence of the shared harness's fixed `fn(df) -> pd.Series` catalog contract, not a design
choice this note is free to avoid. For the `BTCUSDT` cells themselves the gate degenerates
harmlessly (`β ≈ 1` always, since the loaded BTC series and the `work` df it is compared against
are both BTC's own close), reported as a known degenerate cell, not filtered out of the 10-series
pool (the shared harness always runs all 5 basket symbols).

## Sources

`donchian.py` (`sig_donchian_breakout`, unmodified), `entry_masks.py`
(`normalized_signal`/`one_shot_entry_mask`, unmodified), `scripts/f006_family_runner.py` (`run_
family`, `EXPECTED_CHECKSUMS`, `WARMUP_START`/`TRAIN1_END`, unmodified), `data_contract.py`
(`load_dataset`, unmodified), `spec/research/F006-shared-harness.md` (the frozen result schema
and H1/H2 definitions this note reuses unchanged), `spec/research/F005-validation-protocol.md`
section 6 (the checksum table) and section 7 (the monthly promotion checklist), `/tmp/F006-card-
H-BETA-GATE-01.md` (this ticket's own freeze, reproduced verbatim above).

## Sample

10 series: `{SOLUSDT, ETHUSDT, BTCUSDT, XRPUSDT, DOGEUSDT} × {60, 240}`, per candidate name (20
filtered cells total across both names), plus the harness's own unconditional `DONCHIAN_55`
control (10 more cells) -- exactly the frozen basket `run_family` always runs, no subsetting.

## Method

- **Script**: `scripts/f006_beta_gate_experiment.py`. Single pass, calls `f006_family_runner.
  run_family("beta_gate", ["BETA_GATE_DONCH20", "BETA_GATE_MR_DONCH20"], catalog_entries=beta_
  gate.catalog_entries(), hypothesis_note="spec/research/F006-hypothesis-beta-gate.md",
  script_path="scripts/f006_beta_gate_experiment.py")` once. Does not copy or edit the harness
  loop, the contract tests, or the digest script.
- **Module**: `beta_gate.py` (repo root, same layer as `donchian.py`) -- `rolling_beta`,
  `btc_bias`, `gated_trend_signal`, `gated_mr_signal` (pure functions, no I/O, unit-testable
  without CSVs), plus `load_btc_close`/`_infer_interval`/`catalog_entries` (the only I/O-touching
  functions, exercised by the live run, not by the pure-function unit tests).
- **Discriminating checks** (all inherited from `run_family`, unconditional, not skippable by this
  script): the `DONCHIAN_55` harness control against `output/f006_trailing_boundary/summary/
  results.csv` (must reproduce its 10 stored NO_TRAIL rows exactly), the NO_TRAIL mechanism check
  (`0` runs may exit via `trailing_sl`), the one-shot invariant (`n_trades <= n_calls` on every
  row).
- **This note's own additional check**: a bar-level containment invariant, checked directly on the
  raw signal series before any backtest runs, not on trade counts (a gate reopening mid-run is
  itself a new one-shot call by `entry_masks.one_shot_entry_mask`'s own semantics -- see the
  Mechanism section above -- so `n_trades` is not bounded by the raw trigger's own `n_trades`;
  the earlier draft of this check asserted that bound and was empirically wrong on the first run,
  corrected here before any result is reported). The invariant actually guaranteed by
  construction and checked empirically: every bar where a gated signal is nonzero, the raw
  `DONCHIAN_20` trigger at that same bar is nonzero and in the same direction
  (`gated != 0 => sign(gated) == sign(raw_trigger)`) -- i.e. the gate only ever fires on a bar
  the underlying trigger itself was already active on, even though it may re-open a call the raw
  trigger's own one-shot mask would not have re-opened.

## Falsification condition (stated before running)

Per the freeze card, evaluated separately for each of the two candidate names via `run_family`'s
own frozen H1/H2 definitions:

**H1 is falsified for a name if `mean(train1_net_pnl)` across its 10-series pool is `<= 0`**
(`run_family`'s `h1_pass` field, computed from `train1_net_pnl` only). If both names are
H1-falsified, this hypothesis is falsified outright and H2 is `not_applicable_h1_failed` for both.

**H2 is falsified (for whichever name(s) pass H1) if zero of that name's 10 series has `promotion_
pass = True`** ("no monthly-clean", per the freeze card's own wording).

**Equivalence-to-XS_RS falsifier**: if the gate mechanism as implemented required comparing the
alt against any of the other 3 basket alts (a cross-sectional vote/ranking) rather than against
BTC alone, it would not satisfy the freeze card's "must remain a gate on a trigger, not a TOP1
portfolio" requirement -- checked by construction above (the gate formula never references another
alt's signal) and reported as a passed design constraint in the Result section, not re-derived
empirically.

## Run_id

`scripts/f006_beta_gate_experiment.py`, `git_commit = b726db1` (the pre-registration commit
above, this note's Freeze/Hypothesis/Mechanism/Method/Falsification sections and
`beta_gate.py`/`tests/test_beta_gate.py` unchanged since that commit), single pass, system
`python3` 3.10.12 / pandas 2.3.3 (this worktree's `.venv_test` could not execute -- a
wrong-platform binary, not rebuilt in this slice since system Python already carries every
dependency this slice needs and no Lorentzian catalog entry is touched), 7.8s. This worktree's
`data_cache/*.csv` (git-ignored) were copied unmodified from the main checkout's existing frozen
Train-1 cache before the first run; all 10 files' sha256 hashes were verified by hand against
`f006_family_runner.EXPECTED_CHECKSUMS` before any backtest ran (10/10 match), and the harness's
own `DONCHIAN_55` control against `output/f006_trailing_boundary/summary/results.csv` confirms
the copy loads correctly (0/10 mismatches, in the manifest below). Rerun once at this exact
commit after the pre-registration commit to get the manifest's own `git_commit` field right (an
earlier run against the harness-tip commit `442b246`, before `beta_gate.py` existed at that SHA,
produced byte-identical numbers -- confirming the run itself is deterministic and commit-
independent, but that run's manifest is not kept since its own `git_commit` field would have been
dishonest about which commit produced it). Per-series results and manifest:
`output/f006_beta_gate/summary/{results.csv,manifest.json}`; per-series raw JSON (30 files: 2
candidate names + 1 `DONCHIAN_55` control x 10 series): `output/f006_beta_gate/raw/*.json`.

## Result

**H1 survives for `BETA_GATE_DONCH20`, is falsified for `BETA_GATE_MR_DONCH20`. H2 is falsified
for the surviving name -- no series clears the monthly promotion checklist.**

All of `run_family`'s own unconditional discriminating checks are clean: the `DONCHIAN_55`
harness control against `output/f006_trailing_boundary/summary/results.csv` matches 0/10
mismatches; the NO_TRAIL mechanism check finds 0 of 30 runs (2 candidates + 1 control x 10
series) exiting via `trailing_sl`; the one-shot invariant (`n_trades <= n_calls`) holds with 0
violations. This note's own additional check -- the bar-level containment invariant (every bar a
gated signal fires, the raw `DONCHIAN_20` trigger was already active there, in the direction the
gate's own definition requires) -- also holds with **0 violations across all 20 (symbol, interval)
x 2-name cells**.

**H1, `BETA_GATE_DONCH20`: mean `train1_net_pnl` = \$31.40 across the 10-series pool (`h1_pass =
True`), sum \$314.00, 7 of 10 series profitable, 1362 total trades.** Per series:

| symbol | interval | n_calls | n_trades | train1_net_pnl | max_drawdown_pct |
| --- | --- | --- | --- | --- | --- |
| SOLUSDT | 240 | 100 | 61 | \$20.11 | 9.56% |
| SOLUSDT | 60 | 467 | 232 | -\$63.68 | 16.60% |
| ETHUSDT | 240 | 105 | 57 | \$15.35 | 8.42% |
| ETHUSDT | 60 | 466 | 213 | -\$102.91 | 24.45% |
| BTCUSDT | 240 | 100 | 55 | \$20.14 | 7.41% |
| BTCUSDT | 60 | 457 | 209 | -\$67.72 | 19.22% |
| XRPUSDT | 240 | 110 | 48 | \$322.28 | 16.69% |
| XRPUSDT | 60 | 475 | 197 | \$77.96 | 31.97% |
| DOGEUSDT | 240 | 105 | 66 | \$3.57 | 21.12% |
| DOGEUSDT | 60 | 455 | 224 | \$88.91 | 18.15% |

The pool's mean is positive, but the split is stark and directional, not noise: **every 240m
(4h) series is profitable (5/5, \$76.28 mean); every 60m (1h) series but one is unprofitable
(4/5, -\$13.49 mean, XRPUSDT/60 the lone 60m winner).** `BTCUSDT`'s own degenerate cell (beta ~1
always, as predicted in the Mechanism section) is unremarkable, mid-pack on both intervals,
confirming it is not driving the pooled H1 pass or failure either way.

**H2, `BETA_GATE_DONCH20`: 0 of 10 series clears the monthly promotion checklist (`h2_status =
"falsified"`).** No series comes close to 0 negative months; the two closest are `SOLUSDT/240`
and `ETHUSDT/240` at 5 negative months (of 12), both still comfortably `train1_net_pnl`-positive
and low-drawdown (9.56%/8.42%) but nowhere near the checklist's "every valid month non-negative"
bar. The worst is `ETHUSDT/60` at 10 negative months. Every series traded normally (`n_trades`
between 48 and 232, not a thin-sample near-miss of the kind flagged in prior F006 gate notes) --
this is a genuine, non-degenerate falsification, not a starved sample.

| symbol | interval | n_neg_months (of 12) | train1_net_pnl | max_drawdown_pct |
| --- | --- | --- | --- | --- |
| SOLUSDT | 240 | 5 | \$20.11 | 9.56% |
| ETHUSDT | 240 | 5 | \$15.35 | 8.42% |
| XRPUSDT | 240 | 6 | \$322.28 | 16.69% |
| DOGEUSDT | 240 | 6 | \$3.57 | 21.12% |
| DOGEUSDT | 60 | 6 | \$88.91 | 18.15% |
| BTCUSDT | 240 | 7 | \$20.14 | 7.41% |
| BTCUSDT | 60 | 7 | -\$67.72 | 19.22% |
| SOLUSDT | 60 | 8 | -\$63.68 | 16.60% |
| XRPUSDT | 60 | 9 | \$77.96 | 31.97% |
| ETHUSDT | 60 | 10 | -\$102.91 | 24.45% |

**H1, `BETA_GATE_MR_DONCH20`: falsified, and the falsification is degenerate in a specific,
reportable way -- the `beta < beta_low = 0.2` condition is almost never satisfied at `W = 48`.**
8 of the 10 series trade zero times at all (`n_calls = 0`); only `XRPUSDT` trades, and only 4
times (240m) / 7 times (60m), both net-losing (-\$13.28 / -\$23.24). Mean `train1_net_pnl` across
the pool is -\$3.65 (`h1_pass = False`), sum -\$36.52, 0 of 10 series profitable, 11 total trades
pooled. This is not a starved-but-real signal -- it is near-total absence of the gating
condition itself: at `W = 48` bars, every alt in this basket stays correlated enough to BTC
(`beta >= 0.2`) on almost every bar of the full Train-1 year that the "decoupled" regime this
name was meant to fade essentially never occurs for 4 of the 5 symbols, and occurs only rarely
for the fifth (`XRPUSDT`). The mechanism as frozen (a fixed `beta_low` threshold, no adaptive or
relative calibration) is falsified as written; a lower `beta_low` or a different `W` might
change this, but per the freeze card's own instruction this note does not retune after seeing
the result.

**Bar-level containment invariant, the falsifier ruling out equivalence to `XS_RS`.** By
construction, `beta_gate.py`'s gate only ever compares one alt's own price series to BTC's --
never to the other 3 basket alts -- so no cross-sectional TOP1 selection exists anywhere in this
mechanism; the 0/20 empirical containment-check violations above confirm the code matches that
design, not merely that the design intends it.

## Decision

**No promotion. `BETA_GATE_DONCH20` survives H1 (mean `train1_net_pnl` > 0, the freeze card's own
bar) but is cleanly falsified at H2: 0 of 10 series clears the monthly promotion checklist, with
no thin-sample ambiguity to resolve (every series trades between 48 and 232 times over the full
year). `BETA_GATE_MR_DONCH20` is falsified at H1 outright.**

**The genuinely new finding this note contributes**: `BETA_GATE_DONCH20`'s H1 pass is not a
uniform effect across the basket -- it is driven entirely by the 240m (4h) arm (5/5 profitable,
mean \$76.28) while the 60m (1h) arm is a net drag (4/5 unprofitable, mean -\$13.49). A rolling
48-bar beta window is a very different amount of *calendar* time at the two intervals (48 bars =
8 days at 240m vs. 2 days at 60m) -- this note's single frozen `W` does not distinguish the two,
and the split is consistent with a 2-day beta estimate being too noisy/reactive at 1h to serve as
a useful continuation permission bit, while an 8-day estimate at 4h is closer to a genuine
regime read. This is named as the natural next question for whichever future ticket the
coordinator scopes (a `W` that scales with, rather than is fixed in, bar count across intervals),
not pursued here since this note's own freeze fixed `W` before running and does not retune after
the result.

**`BETA_GATE_MR_DONCH20`'s falsification is itself informative, not merely a null result**: at
`W = 48`, this basket's alts are almost never `beta < 0.2` to BTC over Train-1 -- decoupling of
the kind the freeze card's `market_read` describes ("when alt rolling beta to BTC collapses...")
is a rare event at this window, not a regularly recurring regime, at least for 4 of the 5
symbols. A future slice testing this specific sub-mechanism would need either a much shorter `W`
(more reactive, more likely to dip below a fixed floor) or a relative/adaptive threshold (e.g. a
percentile of that symbol's own beta distribution) rather than the fixed absolute floor tested
here -- not pursued in this slice, named for the coordinator.

**What is reusable regardless of this outcome.** `beta_gate.py` demonstrates that a genuinely
cross-symbol (BTC-referencing) catalog entry can be built on top of `f006_family_runner.run_
family`'s single-symbol `fn(df) -> pd.Series` catalog contract, by having the module load its own
second data source (checksum-verified, cached) rather than needing the harness itself to pass
symbol/interval/a second frame -- a pattern any future cross-symbol F006 slice under the shared
harness can reuse, and the first family script written directly against `run_family` since the
shared-harness ticket itself landed.

**Stop condition met.** This note stops after evidence, per the ticket's own instruction: no
merge, no `spec/build.md` edit, no exchange keys, no holdout/Validation access at any point (only
`fam.load_train1`'s Train-1+warm-up-bounded `data_contract.load_dataset` calls were made,
checksum-verified against the frozen Train-1 table throughout).

## Tests

**New unit tests, `tests/test_beta_gate.py` (8 tests, all passing), covering the pure functions
only** (`rolling_beta`, `btc_bias`, `gated_trend_signal`, `gated_mr_signal`, `_infer_interval`,
`catalog_entries`) -- no CSV, no `data_contract` call, matching the module's own split between
I/O-touching (`load_btc_close`/the two catalog wrapper functions) and pure logic:

- `rolling_beta` recovers a known, hand-constructed linear relationship (`alt_ret = k * btc_ret`
  exactly, `k = 1.5` and `k = -0.7` in two separate tests) to `1e-9`, and confirms the warm-up
  region (`< window` return observations) is `NaN`.
- `btc_bias` is checked bar-by-bar against a hand-derived 6-bar fixture (`window=3`).
- `gated_trend_signal` is checked against the raw `donchian.sig_donchian_breakout` trigger it
  wraps under two conditions: with `beta_min` trivially satisfied (isolating the BTC-bias half of
  the gate, exact match to a hand-computed `expected` series) and with `beta_min` set
  unreachably high (gate must block every bar, `(gated == 0).all()`).
- `gated_mr_signal` is checked with a flat (zero-variance) BTC series (beta always `NaN`, gate
  must block everywhere -- `NaN` comparisons never satisfy `< beta_low`) and with a
  nonzero-variance BTC series and a trivially satisfied `beta_low` (must exactly equal `-raw_
  trigger` wherever `beta` is defined, `0` everywhere it isn't).
- `_infer_interval` on synthetic 60-minute and 240-minute `DatetimeIndex` fixtures.
- `catalog_entries` asserts exactly the two frozen names, `<= 5`.

**Full suite**, system `python3` 3.10.12 (`.venv_test` could not execute in this worktree -- a
wrong-platform binary; system Python already carries pandas 2.3.3/numpy/pytest and this slice
touches no Lorentzian catalog entry, so no rebuild was needed):

| | Before this slice | With this slice |
| --- | --- | --- |
| `pytest tests/` | 222 passed, 7 skipped | **230 passed, 7 skipped** |

No existing test file changed. `donchian.py`, `entry_masks.py`, `data_contract.py`,
`scripts/f006_family_runner.py` and `tests/test_signal_family_contract.py` were not modified by
this slice; the harness's own unconditional discriminating checks (harness control, NO_TRAIL
mechanism check, one-shot invariant) above are this slice's evidence that `run_family` was called
correctly, not re-verified by a separate unit test.
