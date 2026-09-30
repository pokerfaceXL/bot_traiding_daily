# BTC permission × CASCADE — Train-1 evidence

The BTC-gated composition does not clear the frozen primary H1 gate. All four gated names have negative mean Train-1 PnL under NO_TRAIL. The alt-only ungated ablation clears H1 but has no passing series under either H2 policy. No candidate qualifies for promotion under the pre-registered primary geometry. This is not a rejection based on density alone: all four exits and both H2 policies were evaluated.

| Name | NO_TRAIL mean Train-1 PnL | Highest-WR exit | WR (%) | That exit's mean Train-1 PnL |
| --- | ---: | --- | ---: | ---: |
| BPC_R15_V25_C75 | -9.795055 | TRAIL_a0.03_t0.02 | 34.2857 | -6.438997 |
| BPC_R18_V20_C75 | -10.924493 | TRAIL_a0.03_t0.02 | 39.5349 | -6.810683 |
| BPC_R18_V30_C75 | -7.552117 | TP_x2 (WR tie with tight trail) | 35.8491 | +0.598250 |
| BPC_R15_V25_NOGATE | +26.997528 | TRAIL_a0.03_t0.02 | 39.6135 | -19.228810 |
| BPC_R15_V25_ER40 | -5.613537 | TRAIL_a0.03_t0.02 | 34.0426 | -4.717449 |

The sole positive gated exit cell, R18/V30 TP_x2, has one series passing both legacy and sparse H2: XRPUSDT/240, one trade, +5.689, one scored exit month. That is a raw exit-cell diagnostic, not a primary H1 pass or validation result. Its corresponding NO_TRAIL name fails H1. No other exit cell has any raw H2-passing series under either rule.

NO_TRAIL gated density is 4.5–7.9 trades per ten-series-pool member (5.625–9.875 per alt-only member), all thin. The ablation has 17.4 per pool member / 21.75 per alt. No name violates the spam guard: 0.4375–2.1042 emitted signals per alt-series-month, below 8. The denominator excludes BTC. The BTC gate changes the R15/V25 primary mean PnL from +26.997528 to -9.795055; the stricter gate gives -5.613537. This is not evidence that permission improved continuation selection.

## Evidence map and semantics

- `summary/results.csv`, `summary/manifest.json`, `raw/*.json`: unchanged shared `run_family` output, 50 candidate rows plus 10 DONCHIAN_55 control rows.
- `exit_grid/results.csv`: 200 candidate series/cell rows, all 20 name×exit combinations; includes exit histograms, PnL, density, drawdown and dual H2.
- `exit_grid/rank_by_name.csv`: trade-weighted win-rate ranking across exits per name. Raw H2 counts and per-cell H1-conditional counts are distinct; `primary_no_trail_h1` retains the frozen gate. Ties use exit-cell name ordering, not PnL selection.
- `exit_grid/monthly.csv`: legacy equity-month metrics plus realized exit-month sparse metrics. Europe/Warsaw month boundaries; zero exits are ABSENT. These two PnL definitions intentionally differ.
- `exit_grid/trades.csv`: complete candidate trade ledger. Metrics `win_rate`/`n_trades` follow the harness and include warm-up; H1 uses only `train1_net_pnl`. `train1_exit_n_trades` and `train1_exit_net_pnl` are separately exposed.
- Exit changes retain identical signal hashes and call masks, not necessarily identical executed trades: earlier exits can free the engine to take later existing calls. They do not add signal entries or cure mechanism sparsity.
- `exit_grid/manifest.json`: source hashes, producing commit, packaging tip, input checksums, frozen grid and checks. The packaging tip is the immutable evidence commit, recorded by a subsequent metadata commit to avoid a self-referential Git SHA.

## Discriminating checks actually run

- Shared control reproduced mean Train-1 +58.387052600: 10 reference rows, zero mismatches.
- Exit-loop NO_TRAIL reproduced all 50 candidate rows from `run_family`, including legacy H2. BTC was flat in all 40 candidate exit rows; zero one-shot violations.
- Frozen-parent equivalence check: all 30 complete Train-1 CASCADE traces equal `80c013c`, all four BTC ER threshold/interval traces equal `e518682`, and all 50 composed traces equal the frozen-parent composition. It loads only the bounded Train-1 cache.
- Scoped pytest: 27 passed. The first run had 1 failure / 26 passes because the causal fixture's volume equaled (rather than exceeded) the strict 3.0 multiple. Raising fixture volume fixed the non-vacuous causality test; entry logic was not changed.
- Tests distinguish inside-channel trauma from Donchian, exact six-bar expiry, refresh/consume, rejection consuming the arm, missing timestamp neutrality, prefix causality, BTC-flat NOGATE, strict threshold boundaries, weighted WR and Train-1 H1, and sparse month behavior.

Reviewer copies, logs and the executable frozen-parent checker are outside the worktree at `/home/limen/bot_traiding_daily/artifacts/f006-btc-perm-cascade/`. Reproduce with `python3 scripts/f006_btc_perm_cascade_experiment.py` from a clean checkout containing the ten bounded cache CSVs; it verifies their frozen checksums. Only those Train-1 CSVs were copied into this worktree. Python is `python3` here (`python` is absent); no dependencies were installed.

No holdout/Validation was loaded, no parent branch merged, no production catalog or harness modified. SBPA remains DNR; CASCADE-FADE remains blocked. No follow-up was spawned and no merge performed. Coordinator review is the next action; no implementation slice remains.
