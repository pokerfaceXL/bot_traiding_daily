# Signal autopsy — Train-1 entry cohorts

Retrospective descriptions only; no strategy tuning or H1/H2 changes. Rates exclude null diagnostics.
Stop/TP MFE/MAE are conservative lower bounds; warmup entries are excluded from tags.

| Existing strategy | Entries | Calm rate/tag | Forward agreement rate/tag | Quick reverse rate/tag |
| --- | ---: | --- | --- | --- |
| DONCHIAN_55 | 447 | 0.5033557046979866 / strong (n=447) | 0.4563758389261745 / weak (n=447) | 0.0 / strong (n=447) |
| BTC_FILTER_ER20_DONCHIAN_20 | 560 | 0.5053571428571428 / strong (n=560) | 0.44285714285714284 / weak (n=560) | 0.0 / strong (n=560) |
| RANGE_EQH_RECLAIM_WIDE | 548 | 0.5072992700729927 / strong (n=548) | 0.5311355311355311 / strong (n=546) | 0.0 / strong (n=548) |
| VOLW_HIGH_BRK_20 | 814 | 0.0773955773955774 / weak (n=814) | 0.4668304668304668 / weak (n=814) | 0.030712530712530713 / strong (n=814) |
| MTFP_HTF_BRK20 | 899 | 0.5517241379310345 / strong (n=899) | 0.4688195991091314 / weak (n=898) | 0.0 / strong (n=899) |
| LIQ_CASCADE_20_120_6_R15_V25_C75 | 209 | 0.5741626794258373 / strong (n=209) | 0.507177033492823 / strong (n=209) | 0.0 / strong (n=209) |
| BETA_GATE_DONCH20 | 1252 | 0.5583067092651757 / strong (n=1252) | 0.49440894568690097 / weak (n=1252) | 0.00878594249201278 / strong (n=1252) |
