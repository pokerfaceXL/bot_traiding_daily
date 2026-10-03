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

Validation-1 metrics have not been written to any artifact.
