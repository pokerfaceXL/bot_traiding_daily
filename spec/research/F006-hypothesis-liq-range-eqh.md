# F006 hypothesis — liq-range / EQH-EQL SMC-inspired (public YT)

**Hypothesis:** `H-LIQ-RANGE-EQH-01`  
**Status:** pre-registered before implementation and Train-1.  
**Scope:** Train-1 only, 2024-03-01 through 2025-03-01; no validation or holdout data may be read. This is SMC-inspired public-YT research, **not** a Stasiak recreation or clone.

## Observation and method

**Observation (public market-read):** In consolidations, EQH/EQL pool retail stops. Price often sweeps the pool then closes back inside the range. Discretionary SMC/YT language: fade the grab / trade the reclaim, not the chase.

**Method (mechanical, OHLCV):** Detect a causal range from confirmed swings → require EQH or EQL (≥2 equals near the box edge) → require a pierce beyond the EQ level → require a subsequent close back inside → emit fade. Fill next open. NO_TRAIL.

## Frozen contract

| Rule | Freeze |
| --- | --- |
| Causality | Decisions on closed bars ≤ `i` only |
| Fill | Earliest fill = **open of `i+1`** |
| Pivots | **No centered `[i-lb, i+lb]`**. Left window + confirmation lag only |
| Exit | Harness **NO_TRAIL** first (no partial/BE ladder in v1) |
| Data | `ohlcv` only |
| Universe | BTC/ETH/SOL/XRP/DOGE USDT perps × `{60, 240}` |
| Names | ≤5 catalog entries, frozen **before** module code / Train-1 |
| Peek | Train-1 only; no holdout / Validation |

### ATR

`ATR14[t]` is Wilder ATR(14) using bars ≤ `t`.

### Causal pivots

Parameters: confirmation lag `L` (also used as left half-width).

At bar `i`, swing **high** is confirmed at `p = i - L` iff:

1. `p >= L`;
2. `high[p] >= max(high[p-L : p])` (equivalently `high[p] >= high[k]` for every `k ∈ [p-L, p-1]`);
3. `high[p] > max(high[p+1 : i+1])` (strictly greater than all highs on `(p, i]`).

Swing **low** mirrors this with `low` and `<=` / `<`. Pivot `p` is unknown before `i = p + L`; store `confirm_time(p) = p + L`.

### Range box

Let `SH` = latest confirmed swing high and `SL` = latest confirmed swing low with `confirm_time ≤ i`.

- `range_top = high[SH]`, `range_bot = low[SL]`; require `range_top > range_bot`.
- `width_atr = (range_top - range_bot) / ATR14[i]`.
- `age = i - min(confirm_time(SH), confirm_time(SL))`.
- `range_valid = (W_MIN <= width_atr <= W_MAX) and (N_MIN <= age <= N_MAX)`.
- Proximity: `close[i] ∈ [range_bot - 0.25*ATR14[i], range_top + 0.25*ATR14[i]]`.

Shared constants: `W_MIN=1.5`, `W_MAX=8.0`, `N_MIN=8`, `N_MAX=64`. If the range is not valid, emit 0.

### EQH / EQL pools

`EPS` is in ATR units.

EQH candidates are confirmed swing highs with `confirm_time ≤ i` and `high[p] ∈ [range_top - EPS*ATR14[i], range_top + EPS*ATR14[i]]`. Require a subset of at least two whose pairwise absolute price difference is at most `EPS*ATR14[i]`. `EQH_level = max(prices in that subset)`.

EQL mirrors the rule near `range_bot`; `EQL_level = min(subset)`. A missing pool leaves that side silent.

### Sweep, reclaim, and signal

**Short (EQH):** find the latest unused sweep `s` with `high[s] >= EQH_level + SWEEP_EPS * ATR14[s]`. Find reclaim `r`, `s < r ≤ i`, `r-s ≤ R_MAX`, where `close[r] < EQH_level` and `close[r] <= range_top`. On the first reclaim (`i == r`) emit −1, consume the EQH event, and start cooldown. Fill at `open[i+1]`.

**Long (EQL):** mirror this: `low[s] <= EQL_level - SWEEP_EPS * ATR14[s]`; reclaim must satisfy `close[r] > EQL_level` and `close[r] >= range_bot`; emit +1 and consume the EQL event.

If both sides would fire on one bar, emit 0. After any emit, suppress new emits for `C` bars. The WICK name additionally requires that the sweep close did not close beyond its EQ line (`close[s] <= EQH_level` for shorts, `close[s] >= EQL_level` for longs).

### Dead-vol veto

All names emit flat when `ATR14[i] / close[i] < 0.002`.

## Frozen catalog

| name | L | EPS | SWEEP_EPS | R_MAX | C | extra |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `RANGE_EQH_RECLAIM_L2` | 2 | 0.20 | 0.05 | 3 | 6 | primary |
| `RANGE_EQH_RECLAIM_L3` | 3 | 0.20 | 0.05 | 3 | 6 | lag ablation |
| `RANGE_EQH_RECLAIM_WIDE` | 2 | 0.30 | 0.05 | 5 | 6 | denser |
| `RANGE_EQH_RECLAIM_TIGHT` | 2 | 0.15 | 0.10 | 2 | 8 | stricter |
| `RANGE_EQH_RECLAIM_WICK` | 2 | 0.20 | 0.05 | 3 | 6 | wick-only sweep |

No name or constant may be added, tuned, or changed after Train-1. Exit geometry is harness `NO_TRAIL`; sizing and risk use harness defaults. No partial or 1R/2R/3R ladder is part of the module.

## Non-overlap and exclusions

- **LSWEEP:** distinct through range box + EQ≥2 + reclaim-inside + fade.
- **H-SMC-SWEEP-DISPLACEMENT-01:** no HTF, FVG, or displacement retest.
- **REGIME_SW_***: not an HHHL↔BB switch and must not retune that geometry.
- This does not reopen ORB, NR-compression, prior-day HL, session-VWAP, pivot-breakout, or ZAORSKI_PA.
- v1 excludes centered swing windows, EMA200/pinbar/engulf/big-body primary triggers, ATR impulse zones, PDH/PDL first-class liquidity, FVG/imbalance/fib/OB retests, HTF bias, session filters, funding/OI/heatmap, and branding claiming Stasiak fidelity.

## Falsifiers and decision

1. H1 fails if mean net Train-1 PnL across the 10-series pool is ≤ 0.
2. H1 fails if mean trades per series after filters is < 10.
3. H2 fails if no series is monthly-clean under the harness rule.
4. Any lookahead in pivot, EQ, or range formation fails the experiment.
5. The mechanism fails if an ablation without EQH/EQL≥2 (fade any range pierce/reclaim) is no worse on H1.
6. The experiment fails if review judges its geometry equivalent to closed `LSWEEP`.
7. Post-hoc Train-1 constant changes fail the process.

Run `scripts/f006_family_runner.py` through `run_family` against its `DONCHIAN_55` control. Stop after Train-1 evidence; do not merge.

## Sources

Public-only inspiration: Crypto Stasiak YouTube `sEHJ7lYCSPY`; free SMC videos `BGC3-kIYqDE` and `Jqud4SeQ4Qo`; public EQ-sweep/reclaim guides (Backtrex and Medium liquidity-sweep #3). Paid Discord/CST PRO was not used.

## Train-1 evidence and decision

Run: `python3 scripts/f006_liq_range_eqh_experiment.py`, at code tip `85c192c070f6cc8c13f888b157f6eb3866c3d28b` (recorded in the rerun manifest). The harness loaded only its bounded warm-up plus Train-1 CSVs, reproduced `DONCHIAN_55` for all 10 control rows with 0 mismatches, found 0 trailing exits in 60 runs, and found 0 one-shot violations. The ten bounded Train-1 cache paths are tracked relative symlinks to the shared main-checkout cache, so a sibling Limen worktree can run this evidence without a manual cache setup. Raw per-series results, monthly rows, and manifest are retained in `output/f006_liq_range_eqh/`.

H1 below is recomputed from `train1_net_pnl` (not the harness's whole loaded warm-up-plus-Train-1 `net_pnl`) across the required 10-series pool.

| frozen name | mean Train-1 net PnL (10 series) | mean trades/series | H1 |
| --- | ---: | ---: | --- |
| `RANGE_EQH_RECLAIM_L2` | $54.13 | 55.7 | pass |
| `RANGE_EQH_RECLAIM_L3` | -$4.14 | 99.4 | falsified |
| `RANGE_EQH_RECLAIM_WIDE` | $64.32 | 58.8 | pass |
| `RANGE_EQH_RECLAIM_TIGHT` | $39.51 | 51.2 | pass |
| `RANGE_EQH_RECLAIM_WICK` | $31.28 | 44.3 | pass |

H2 is falsified by the harness: no series among the four Train-1 H1-passing names passed its monthly promotion checklist; every frozen name has zero monthly-clean series. The family stops here: constants and names remain frozen, no validation/holdout data was loaded, and this candidate is not merged or promoted.
