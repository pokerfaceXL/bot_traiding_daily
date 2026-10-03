# F006 Val-1 — Train-1 gate question (worker → coordinator)

The pre-registered gate ("Train-1 slice of the longer control run must reproduce mean
train1_net_pnl +82.90 within 1e-6, n=512") FAILED: observed 83.048644, n=512.

Cause: the reference value 82.900262 includes exit costs from an `end_of_data` force-close
at the Train-1 data end. On 240m that close lands at 2025-02-28 20:00 inside the 2025-02
bucket, about +0.30 per 240m series. In a run that continues into Validation-1 those
positions stay open, so the equity-based Train-1 PnL cannot match within 1e-6. The 60m
series match exactly, and trade count matches.

Decision needed (product / pre-registration amendment, not a worker call):
1. Accept the gate as failed and close this Val-1 attempt, or
2. Amend the gate before any Validation-1 scoring to a window-invariant check. Examples:
   (i) Train-1 PnL from trades *closed* before 2025-03-01 plus an exact match on
   Train-1-entry keys; or (ii) the 60m-exact / 240m equity through 2025-02-28 16:00.
   Then rerun `python3 scripts/f006_bb_20_25_xsym_agree_sizing_val1.py` after editing
   its gate block. The script is ready and the multiplier `now` bug is fixed.

At the time of the gate-failure run, Validation-1 metrics had not been written to any artifact.

## Decided (2026-10-03, coordinator, before Validation-1 scoring) — not open

Gate amended: the absolute 1e-6 tolerance on the 10-series mean is now relative 0.25% of
|reference mean|. n=512 stays exact. The round-to-2dp equality was dropped. Falsifiers
(a)-(e), the frozen formula, the one-bar shift, the data split, and number_of_trials = 1
are unchanged. This is not a new trial. Script `GATE_REL_TOL = 0.0025` (commit `548e390`);
the rerun gate passed (diff 0.148382 <= 0.207251, n=512). Result is in the hyp card.
