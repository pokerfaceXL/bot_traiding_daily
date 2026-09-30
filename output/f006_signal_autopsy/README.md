# Optional signal autopsy — evidence and handoff

`run_family(..., autopsy=True)` now writes closed-trade blotters and retrospective entry diagnostics. Default callers emit neither autopsy files nor new summary CSV columns. Execution, strategy code, H1/H2 gates and daily-equity `train1_net_pnl` are unchanged. The pre-registration is `spec/research/F006-hypothesis-signal-autopsy.md` (committed before module code); the supplied analytics-gap note was unavailable.

## Evidence

Producing code is commit `71397054e407f99df348f9d43014039129ad17ba`. `manifest.json` records immutable closed tips, archived module hashes, frozen diagnostics, data checksums, and the packaging commit. It deliberately references a preceding evidence commit rather than attempting a self-referential Git SHA.

The batch replay completed six digest-listed families plus DONCHIAN_55 through the current shared runner: 140 simulation rows, including 10 autopsy-off rows. All seven enabled control comparisons equal the off-path control on every summary column except elapsed time. Mean control Train-1 PnL remains **58.3870526**. Six candidate replays exactly match archived per-series PnL, trade count, win rate, drawdown, final equity and Train-1 PnL; all retain H2 falsified.

Independent artifact checks reconciled **130 blotters / 7,965 trades** against summary counts and net PnL, checked nonnegative excursions and exits strictly before 2025-03-01, and verified six archived source hashes. Repeated controls account for part of that trade count. The off run has no autopsy directory. Ten targeted pytest cases passed before replay. Replay emitted one pandas concat FutureWarning, not an error. Full-suite output is captured after the final metadata commit at `/tmp/f006-signal-autopsy-review/pytest.log`; the final handoff states its actual result.

## Interpretation and reproduction

`report.md` contains pooled descriptive tags, not promotion decisions. Tags use Train-1 **entry cohorts**; blotters also retain warmup entries. ATR calmness is causal at entry; forward agreement is explicitly retrospective. Null horizons/history are excluded from denominators. SL/TP MFE/MAE exclude unknowable exit-bar extremes and are labelled conservative lower bounds in percent of entry price.

Run `python3 scripts/f006_signal_autopsy_batch.py --output output/f006_signal_autopsy_rerun` with the six source tips available in Git and the ten bounded Train-1 cache CSVs. Sources are also archived verbatim under `sources/`. Only the bounded CSVs were copied from the main checkout; no full-history cache, holdout, network fetch, dependency installation, or environment symlink was used. The existing system Python environment supplied dependencies.

Implementation seam: `scripts/f006_signal_autopsy.py` computes diagnostics; the runner hook only observes completed results; `scripts/f006_signal_autopsy_batch.py` imports immutable historical signals, never historical harnesses. No merge, follow-up spawn, or overnight-routine change. Review remains the next action; no implementation slice is intentionally deferred.
