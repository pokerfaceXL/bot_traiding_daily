# F011 T4 — open question for the coordinator

Test 3 (H-FORCEDFLOW-DIAG-PRECASCADE-01) gate: "OOS PR-AUC lift ≥ 2.0 at some horizon on BOTH symbols,
with at least 20 positive events in the test period."

The worker counted **positive events = CASCADE entries in the 40% test segment** (BTC 11, ETH 18). Under that
reading the gate fails, so Test 3 is NEGATIVE and the overall recommendation is ARCHIVE.

If "positive events" means **y_h = 1 bars** (BTC 33 / 66 / 132, ETH 54 / 108 / 214 at 15 / 30 / 60m), every
horizon passes on both symbols (logistic lift BTC 7.0 / 4.0 / 3.3, ETH 9.9 / 6.9 / 6.1). Test 3 then reads
POSITIVE, and the "all NEGATIVE → ARCHIVE" condition no longer holds.

Context: the lift is mostly by construction. A CASCADE requires crowd_side + STRESS conditions + fuel, so the
CROWDING/STRESS flags are antecedents of the label. In the test segment, the CROWDING-only rule alone reaches
lift 1.9–3.7.

Decision needed: which count applies to the ≥ 20 gate, and whether the tautology caveat changes the
ARCHIVE call.
