# F006 — EMA3_21_50_200 (NO_TRAIL) independent protocol autopsy

> Protocol pass that the pre-2026-10-01 process never did for this name: the entry axis had only
> been closed as DNR *by transfer* from Donchian. This autopsy is analysis only, on the
> immutable Train-1 trade table (no new backtest). Reproduce:
> `python3 scripts/f006_ema3_21_autopsy.py`.
> Source: `output/f006_catalog5_trio_autopsy/trades/EMA3_21_50_200_train1_trades.csv`
> (402 trades, 10 series = 5 symbols × {60,240}, entry months 2024-03 … 2025-02).
> Causality: features available **at entry** (usable as a filter) = atr_pct, atr_percentile,
> calm, direction, symbol, interval, month. Features computed **after entry** (diagnostic label
> only, never a filter) = forward_agreement, mfe_pct, mae_pct, bars_held, quick_reverse,
> exit_reason, *_pnl.

## 1. Shape (same lumpy-winner class as the rest of the momentum family)

| metric | value |
| --- | ---: |
| n trades | 402 |
| net PnL | +817.03 |
| mean / trade | +2.03 |
| win rate | 19.65% |
| gross / costs | +947.07 / 130.03 |

- Exit economics: `signal_reverse` n=117, WR 59.8%, +1554.2 · `initial_sl` n=276 (68.7%), WR
  0%, −916.3 · `end_of_data` n=9, +179.2 (boundary mark-to-market, not a real closed edge).
- Concentration is extreme: top-1 winner = 41% of net, top-3 = 97%, top-5 = 121%.
  **2024-11 alone = +812.7 of +817.0 total net.** Without it the year is ≈ breakeven.

## 2. Entry-vol axis — independently falsified for THIS name (confirms the transfer, now earned)

Entry-time feature means, `initial_sl` vs `signal_reverse`:

| feature | initial_sl | signal_reverse |
| --- | ---: | ---: |
| atr_pct (raw) | 1.713 | 1.085 |
| **atr_percentile** | **0.563** | **0.560** |
| **calm** | **0.428** | **0.436** |

The raw `atr_pct` gap is a cross-symbol scale artifact (symbols have different absolute ATR%);
the regime-normalized `atr_percentile` and `calm` are **identical** for deaths vs runners, so
volatility state at entry does not separate them. A causal `atr_percentile` gate (mirror of the
Donchian H-ABS-ATR criteria) confirms it: no threshold drops `initial_sl` share by ≥10pp
(max 4.4pp at T≤0.30, which keeps only 23% of big-winner PnL); every gate retaining ≥50% of
big-winner PnL moves the stop share by ≤2pp. **Entry-volatility axis = FALSIFIED for
EMA3_21_50_200 on its own trades**, not by analogy. Same structural trade-off as Donchian.

## 3. NEW: causal direction asymmetry (the Donchian analogy missed this)

| direction | n | net | mean/trade | WR |
| --- | ---: | ---: | ---: | ---: |
| long (+1) | 190 | **+875.2** | +4.61 | 18.4% |
| short (−1) | 212 | **−58.1** | −0.27 | 20.8% |

- **All 7 big winners (net ≥ 29.9) are longs** (+1064.6) bar one short end_of_data boundary
  trade (+35.4). The fat tails that carry the entire edge are longs.
- Short book without the end_of_data boundary trades: `initial_sl` −465.4 + `signal_reverse`
  +228.1 = **−237.3**. Shorts are a negative-EV book, not noise around zero.
- Plausible mechanism: crypto's secular long bias + momentum long-vol asymmetry (up-legs trend
  to the opposite extreme; down-legs mean-revert / short-squeeze and hit the fixed stop).

## 4. NEW: losing months are shared-regime, not idiosyncratic

Per-month, count of symbols (of 5) net-negative:

| month | #neg | month | #neg | month | #neg |
| --- | ---: | --- | ---: | --- | ---: |
| 2024-03 | 4 | 2024-07 | 1 | 2024-11 | 0 |
| 2024-04 | 4 | 2024-08 | **5** | 2024-12 | 3 |
| 2024-05 | 4 | 2024-09 | **5** | 2025-01 | 4 |
| 2024-06 | 1 | 2024-10 | 2 | 2025-02 | 1 |

- Pooled losing months: **7/12**. Six of them (2024-03,04,05,08,09, 2025-01) have ≥4/5 symbols
  down **together** — the losses are a common market regime, not per-symbol noise. Winning
  months (Jun, Jul, Oct, Nov, Feb) are also shared (0–2 symbols down).
- Implication: diversifying across symbols cannot fix the monthly floor (losses co-occur); the
  lever has to be either a causal regime signal (portfolio-level, §8/§13) or a structural
  entry attribute that happens to down-weight the bad-regime trades.

## 5. Protocol §6 answers

- **Losses concentrated in a regime?** Yes — 6 shared-down months; Aug/Sep 2024 all five
  symbols negative.
- **False breakouts?** Yes — 68.7% die at `initial_sl` (0% WR). Many are not instant: losses'
  mean MFE 4.4% (diagnostic), so some trended before dying.
- **Separable at entry (no look-ahead)?** Not by volatility (§2). Yes, partly, by **direction**
  (§3, causal) — shorts are the systematically worse book.
- **Common loser traits?** Shorts + shared-down months. Forward-agreement (label only) is 0.47
  for losers vs 0.72 for winners — confirms losers reverse against entry, but it is not
  available at entry.
- **Would a loss-removing filter also cut big winners?** The volatility gate would (§2). The
  **direction** filter would NOT — big winners are all longs (§3). This is the key difference.
- **Entry / exit / sizing / symbol / interval / allocation?** Exit closed (EXIT-CLASS/
  PARTIAL-EXIT falsified). Entry-vol closed (§2). Remaining live, causal entry levers:
  **direction** (§3) and a **regime** signal (§4). Interval 240 has higher mean/trade (+4.67 vs
  +1.21) but far fewer trades; symbol edge (XRP/DOGE carry) is the same as Donchian.
- **Did prior rejected filters address this problem?** The rejected filters were all
  volatility/trend-strength proxies (§2's axis); none tested the direction asymmetry on this
  name. So the direction axis is genuinely untested, not a re-run.
- **Is another test justified?** Yes — one single-axis, causal, entry-time test on direction,
  grounded in §3, that provably does not cut the fat tails. Pre-registered next:
  `spec/research/F006-hypothesis-ema3-21-long-only.md`.
