# F013 Gate D — Cost ladder (KILL)

**Status: FAIL** · discovery = C02 Train-1 (contaminated) · net@34 = mean net bp at 34 bp RT incl. funding · CI = day-batch cluster bootstrap 95 % (10 000, seed 13) unless the row says otherwise.

| split | cost_bp | n | n_clusters | mean | median | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|
| 9.9 bp RT (context only) | 9.9 | 55 | 32 | 552.6 | 384.0 | -173.0 | 1206.9 |
| 34 bp RT | 34.0 | 55 | 32 | 528.5 | 359.9 | -197.1 | 1182.8 |
| 50 bp RT | 50.0 | 55 | 32 | 512.5 | 343.9 | -213.1 | 1166.8 |
| 75 bp RT | 75.0 | 55 | 32 | 487.5 | 318.9 | -238.1 | 1141.8 |
| 100 bp RT | 100.0 | 55 | 32 | 462.5 | 293.9 | -263.1 | 1116.8 |
| 150 bp RT | 150.0 | 55 | 32 | 412.5 | 243.9 | -313.1 | 1066.8 |
| 200 bp RT | 200.0 | 55 | 32 | 362.5 | 193.9 | -363.1 | 1016.8 |

- Breakeven RT cost (mean gross + funding) = 562.5 bp.
- Decision: net@34 CI lower = -197.1 bp (needs > 0); mean net@75 = 487.5 bp (needs > 0).
- Context (not decision): eligible sample before Gate K exclusion, n = 73 (37 day-batch clusters): net@34 mean 492.4 bp, CI [-143.8, 1090.6].
