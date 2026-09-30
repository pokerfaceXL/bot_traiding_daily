# F006 — H-ORB-SESSION-ANCHOR-01: London/NY session-anchored opening-range breakout

> Sections "Observation" through "Method" (including falsification) were copied from the frozen
> card `/tmp/F006-card-H-ORB-SESSION-ANCHOR-01.md` and committed BEFORE any new signal module /
> experiment script was written and before any backtest was run, per the same pre-registration
> discipline as every prior F006 hypothesis note. "Run_id", "Result", "Decision" and "Tests" are
> placeholders filled in after the run.
>
> TRAIN-1 ONLY, same window as every F006 slice: `[2024-03-01T00:00:00Z, 2025-03-01T00:00:00Z)`
> plus the protocol's 35-day warm-up buffer from `2024-01-26T00:00:00Z`. Validation 1-4 and the
> Holdout window are not loaded, not sliced and not looked at.

```yaml
id: H-ORB-SESSION-ANCHOR-01
name: Session-anchored ORB (London / NY open) — new generator family ORB_LON_* / ORB_NY_*
universe: BTC/ETH/SOL/XRP/DOGE USDT perps × {60,240}  # frozen Train-1 5×2 basket
data_needs: [ohlcv]  # checksum-locked Train-1 cache only; no new symbols/data
entries: NEW additive catalog names ORB_LON_* / ORB_NY_* (session-clock OR, not UTC-day OR_BARS retune)
exit: NO_TRAIL only first (same geometry as prior ORB_UTC_*)
h2: dual legacy + h2_sparse_absent_zero_trade (zero-trade months = ABSENT/neutral)
aggregation: mean train1_net_pnl across 10 (symbol, interval) series per name (H1 bar)
base_tip: origin/main 3d4edd4
license: Decision on limen/2026-09-28-f006-opening-range-breakout-2a0ca90b tip 239d3cf — separately pre-registered follow-up (narrower-than-day London/NY anchors avoiding 240-bar collision)
```

## License

`spec/research/F006-hypothesis-opening-range-breakout.md`'s Decision (branch
`limen/2026-09-28-f006-opening-range-breakout-2a0ca90b`, tip `239d3cf`) closed the `ORB_UTC_*`
family at `NO_TRAIL` on the Train-1 5×2 basket and named exactly one separately pre-registered
follow-up: a narrower-than-day session anchor (London/NY open) that does not collide with `240`'s
exact 6-bar UTC day. This note is that follow-up and nothing else. It does **not** reopen
`ORB_UTC_*` (no `OR_BARS` retune, no change to those names' semantics), and does not reopen
catalog5 NO_TRAIL FREEZE, ABS-ATR, DONCHIAN, EXIT-CLASS, PARTIAL-EXIT, HTFP or CASCADE.

## Observation (pre-registered)

`ORB_UTC_*` (UTC calendar-day opening range, `OR_BARS` ∈ {1,2,3,4,6}) was H1-falsified on branch
`limen/2026-09-28-f006-opening-range-breakout-2a0ca90b` tip `239d3cf`: no name had positive mean
`train1_net_pnl` across the 10-series pool at `NO_TRAIL`. Decision closed that family at that
geometry/basket and explicitly forbade inventing extra `OR_BARS` or alternate anchors *after
seeing results*, while naming a **separately pre-registered** follow-up: a narrower-than-day
session anchor (London/NY open) that would not collide with `240`'s exact 6-bar UTC day (the
`ORB_UTC_6` degenerate-zero artifact).

This card is that follow-up. Mechanism stays opening-range breakout; the change is the **clock
anchor** of the OR window, not a re-grid of failed `ORB_UTC_*` bar counts.

## Mechanism

Additive signal family (sibling module to the unmerged `opening_range_breakout.py`; register new
`STRATEGY_CATALOG` names via `catalog_entries()` — do **not** alter behavior of existing
`ORB_UTC_*` entries if present on tip, and do **not** stuff into `add_indicators`).

For each UTC calendar day `D` and each pre-registered name:

1. **OR window** = fixed clock interval in UTC (table below). Bars whose **open** falls in
   `[T_start, T_end)` on day `D` contribute to `or_high = max(high)`, `or_low = min(low)`.
2. If **zero** bars of the series have open in that window on day `D`, that day **never arms**
   (signal 0 all day) — document as interval/structure artifact; do **not** invent mid-slice
   fixes (partial-bar OR, OR_BARS fallback, etc.).
3. Once the OR window has ended (first bar with open `>= T_end` on `D`, or equivalently after all
   OR-window bars are known), for subsequent bars on `D` with open `>= T_end`:
   - Long (+1) when `close > or_high`
   - Short (−1) when `close < or_low`
   - Else 0
   - Strict inequalities only.
4. At the first bar of a new UTC day, previous day's state is discarded (no carry).
5. Persistent-state signal; family one-shot mask applied by harness as elsewhere.
6. Causality: OR high/low use only bars with open in the OR window on the same day; breakout uses
   only current close vs completed range. No future bars.
7. Exit geometry: **`NO_TRAIL` only** first (`activate_pct=10.0`, `max_sl_pct=0.03`, `cd=0`,
   `leverage=1`) — same as prior ORB. No TP/trail grid in this slice.

### Frozen cells (exactly 5 — pre-registered; do not widen after seeing results)

| # | Name | Anchor | OR window (UTC, half-open) |
| --- | --- | --- | --- |
| 1 | `ORB_LON_1H` | London open | `[07:00, 08:00)` |
| 2 | `ORB_LON_2H` | London open | `[07:00, 09:00)` |
| 3 | `ORB_LON_3H` | London open | `[07:00, 10:00)` |
| 4 | `ORB_NY_1H` | NY open | `[13:30, 14:30)` |
| 5 | `ORB_NY_2H` | NY open | `[13:30, 15:30)` |

Budget: **≤5 cells total** across anchors × OR length. These five are the entire grid.

**Structure note, stated before running (derived from the bar grid, not from any result):** the
Bybit cache bars open on the hour (`60`: every hour; `240`: 00/04/08/12/16/20 UTC). Therefore:

- On `60`, `ORB_NY_1H` `[13:30, 14:30)` contains exactly the `14:00` bar and `ORB_NY_2H`
  `[13:30, 15:30)` contains the `14:00` and `15:00` bars — the half-hour anchor is honored
  literally by the half-open rule on bar **open** times; no partial-bar logic is added.
- On `240`, `ORB_LON_1H`/`ORB_LON_2H` (`[07:00,08:00)` / `[07:00,09:00)`) contain the `08:00`
  bar only for `2H` (`08:00 ∈ [07:00,09:00)`), and `1H` contains **no** bar → `ORB_LON_1H/240`
  never arms (all-zero rows expected). `ORB_LON_3H/240` contains only `08:00`, identical OR to
  `ORB_LON_2H/240`. `ORB_NY_1H/240` (`[13:30,14:30)`) and `ORB_NY_2H/240` (`[13:30,15:30)`)
  contain **no** 4h bar open → never arm (all-zero rows expected).
- These zero/duplicate rows are reported as interval/structure artifacts per Mechanism rule 2,
  and they still count in the 10-series mean (a zero row contributes 0), same as the prior
  note's `ORB_UTC_6/240` rows. No fix is invented mid-slice.

**Not in scope:** re-tuning `ORB_UTC_*` `OR_BARS`; mixing BB/Donchian/EMA/RVOL/XS gates; London+NY
combined signals; mid-slice OR length invention.

## Hypothesis

**H1 (aggregate).** At least one of the 5 frozen names has mean `train1_net_pnl` across its 10
`(symbol, interval)` series **> 0** at `NO_TRAIL` (`activate_pct=10.0`, `max_sl_pct=0.03`,
one-shot entry mask, `cd=0`, `leverage=1`).

**H2 (monthly, conditional on H1).** For any H1-clearing name, at least one of its 10 series
clears **legacy H2** (F005 section-7 monthly promotion checklist: `n_trades > 0`, every valid month
non-negative, all 12 Train-1 months valid, `train1_net_pnl >= 0`, DD ≤ 50%) or
**`h2_sparse_absent_zero_trade`** (score only months with exit-month `n_trades > 0`; zero-trade
months ABSENT/neutral; all scored months `net_pnl >= 0`, DD ≤ 50%, `train1_net_pnl >= 0`,
`n_trades > 0`), per `/tmp/F006-eval-policy-sparse-h2-and-exits-2026-09-29.md` section B. Both
are always reported. Sparse month bucket: trade **exit** month (Europe/Warsaw calendar, same
bucketing as `scripts/f006_catalog5_exit_class_grid.py`'s `sparse_months`), Train-1 months only.

## Eval / reporting

- **H1:** mean `train1_net_pnl` across the 10 `(symbol, interval)` series for that name **> 0** at
  `NO_TRAIL`.
- Report per name: mean `train1_net_pnl`, mean `n_trades`, max DD; note any 240 (or 60) never-arm
  / zero-trade series as density/structure notes.
- **H2 (conditional on H1):** for any H1-clearing name, report **legacy H2** and
  **`h2_sparse_absent_zero_trade`** (zero-trade months = ABSENT/neutral). Same discipline as
  `spec/research/F006-hypothesis-opening-range-breakout.md`.
- Harness control: re-run `DONCHIAN_55` (shared runner's frozen 10-row control) to prove the
  script matches stored numbers.
- Evidence under `output/f006_orb_session_anchor/`; manifest records producing commit.

## Falsification (pre-registered — same discipline as F006-hypothesis-opening-range-breakout.md)

- **H1 falsified** if **no** pre-registered name has positive mean `train1_net_pnl` across its
  10-series pool at `NO_TRAIL`.
- **H2 falsified** if every H1-clearing name fails monthly under both legacy and sparse rules as
  applicable (same discipline as prior ORB note). If H1 fails, H2 is **"not applicable — H1
  failed"**, not silently passed/failed.

Do **not** invent extra OR windows / anchors / gates after seeing results. A negative Result is
valid and must be reported honestly.

## Sample

5 names × 5 symbols × 2 intervals (`240`/`60`) = 50 series, Train-1 only, plus the shared
runner's `DONCHIAN_55` harness control. No Validation/holdout. No merge from this job.

## Method

1. Additive module `orb_session_anchor.py` exposing
   `compute_session_orb_signal(df, start, end) -> pd.Series` (+1/0/−1) and `catalog_entries()`
   returning exactly the five frozen names. Registered into `strategy.STRATEGY_CATALOG` at
   runtime by `scripts/f006_family_runner.register_catalog_entries` (shared-harness convention:
   never by editing `strategy.py`). Does not import or depend on the unmerged
   `opening_range_breakout.py`. No live trading, no API keys.
2. Experiment script `scripts/f006_orb_session_anchor_experiment.py` calling
   `f006_family_runner.run_family(...)` (checksums, one-shot mask, `NO_TRAIL`, DONCHIAN_55
   control, H1 on `train1_net_pnl`), then a second pass over the same 50 cells computing legacy
   H2 and `h2_sparse_absent_zero_trade` per series. Output under `output/f006_orb_session_anchor/`.
3. Unit tests: window arming, never-arm day, new-day reset, causality (future bars appended do
   not change past signal), strict inequality at `or_high`/`or_low`, catalog names exact.
4. Fill Result / Decision / Run_id / Tests after the run; commit evidence.

## Run_id

`scripts/f006_orb_session_anchor_experiment.py`, system Python 3.10.12 (pandas 2.3.3), single
pass, ~21s: `f006_family_runner.run_family` over 5 candidate names × 5 symbols × 2 intervals
(50 rows) + the runner's frozen `DONCHIAN_55` 10-row harness control, then a second engine pass
over the same 50 cells for legacy + sparse H2 (pass-2 `net_pnl`/`train1_net_pnl` asserted equal
to pass 1 row for row). Producing commit (in `manifest.json`):
`689fee3a2b76cce283187e5d6d35e168a838cd98`. Evidence: `output/f006_orb_session_anchor/`
(`summary/results.csv`, `summary/manifest.json`, `summary/h2_dual.{csv,json}`, `raw/*.json`).

The git-ignored frozen Train-1 CSVs (`data_cache/*_20240126T000000Z_20250301T000000Z.csv`) were
**copied** (not symlinked) into this worktree from the host checkout's `data_cache/`; the
runner's checksum check against F005 protocol section 6 passed for all 10 pairs.

## Result

**H1 is falsified. All 5 names have negative mean `train1_net_pnl` over their 10-series pool at
`NO_TRAIL`:**

| Name | OR window (UTC) | mean train1_net_pnl | sum | profitable series | mean n_trades | mean on 60 only | max DD % | zero-trade series |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `ORB_LON_1H` | `[07:00,08:00)` | -$54.07 | -$540.72 | 1/10 | 252.2 | -$108.14 | 43.60 | all 5 × `240` |
| `ORB_LON_2H` | `[07:00,09:00)` | -$83.97 | -$839.72 | 1/10 | 327.5 | -$100.95 | 40.83 | none |
| `ORB_LON_3H` | `[07:00,10:00)` | -$86.52 | -$865.17 | 1/10 | 303.9 | -$106.04 | 38.09 | none |
| `ORB_NY_1H` | `[13:30,14:30)` | -$51.28 | -$512.77 | 0/10 | 149.4 | -$102.55 | 31.83 | all 5 × `240` |
| `ORB_NY_2H` | `[13:30,15:30)` | -$35.73 | -$357.26 | 2/10 | 114.7 | -$71.45 | 37.19 | all 5 × `240` |

(`mean n_trades` includes the zero rows; on `60` alone it is 504.4 / 417.2 / 370.0 / 298.8 /
229.4.) The only profitable series: `ORB_LON_1H` DOGE/60 +$3.85; `ORB_LON_2H` and `ORB_LON_3H`
XRP/240 +$0.83 (same row, see below); `ORB_NY_2H` DOGE/60 +$4.09 and XRP/60 +$19.70. Mean
win rate across the 50 cells is 20.2% (max 33.9%).

Checks (all recorded in `manifest.json`): harness control `DONCHIAN_55` 10 rows vs
`output/f006_trailing_boundary/summary/results.csv` — 0 mismatches; `NO_TRAIL` mechanism —
0/60 runs had a `trailing_sl` exit; one-shot — 0 violations.

**Structure artifacts, exactly as pre-stated in Mechanism (not adjusted):** on `240` (bars open
00/04/08/12/16/20 UTC) no bar opens in `[07:00,08:00)`, `[13:30,14:30)` or `[13:30,15:30)`, so
`ORB_LON_1H`, `ORB_NY_1H` and `ORB_NY_2H` never arm on any `240` series (10/10 zero-trade rows,
contributing $0 to their means), and `ORB_LON_2H/240` ≡ `ORB_LON_3H/240` (single `08:00` OR bar;
identical rows). The zeros *flatter* those three names' means; restricted to `60` alone every
name is still ≤ -$71 mean, so H1 would fail with or without the `240` rows.

**H2: not applicable — H1 failed** for every one of the 5 names. For completeness
`summary/h2_dual.csv` scores all 50 cells anyway: 0/50 clear legacy H2 and 0/50 clear
`h2_sparse_absent_zero_trade` (the latter bucketed by exit month, Europe/Warsaw, zero-exit
months ABSENT).

## Decision

**Close the session-anchored ORB family (`ORB_LON_*` / `ORB_NY_*`) at `NO_TRAIL` on the Train-1
5×2 basket.** Together with `ORB_UTC_*` (tip `239d3cf`) this closes opening-range breakout as a
generator on this basket: moving the anchor from the UTC day start to the London or NY open did
not turn any cell aggregate-positive — on `60` every name loses about $70–110 per series, the same
magnitude as `ORB_UTC_1..4`. The license named in `239d3cf`'s Decision has been used; this note
names **no** further ORB follow-up (no other anchors, OR lengths, gates, or exit grid on these
entries — an exit grid cannot add entries and the sparse-H2 pass already finds 0/50 cells).
`ORB_UTC_*` and every other DNR family listed in the card stay closed and untouched.

## Tests

`tests/test_orb_session_anchor.py` (new, 9 tests, all passing): frozen names exact (no
`ORB_UTC_*`); London 2H arming on hand-built hourly day (pre-window bars and OR bars stay 0,
breakout +1/−1, strict equality at `or_high` and `or_low` stays 0); NY half-hour anchor on
hourly bars (`[13:30,14:30)` = the 14:00 bar only; 2H needs the 16:00 bar to trade); never-arm
on a 4h grid for `[07:00,08:00)` and `[13:30,15:30)` while `[07:00,09:00)` arms on the 08:00 bar;
new-day reset with a day missing its OR bar never arming; causality (truncation at 3 points ×
5 names, signal prefix unchanged); fixture 4h structure (LON_1H/NY_* all-zero, LON_2H fires and
equals LON_3H); import does not mutate `STRATEGY_CATALOG` (runtime registration only); invalid
window rejected.

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/test_orb_session_anchor.py tests/test_signal_family_contract.py tests/test_donchian.py tests/test_sube_exit_grid.py` | 86 passed |
