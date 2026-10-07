# F013 Gate B — Latency decay (ROUTE)

**Status: PASS** · discovery = C02 Train-1 (contaminated) · net@34 = mean net bp at 34 bp RT incl. funding · CI = day-batch cluster bootstrap 95 % (10 000, seed 13) unless the row says otherwise.

| split | source | median_entry_lag_s | n_missing | gross_mean | n | n_clusters | mean | median | ci_lo | ci_hi |
|---|---|---|---|---|---|---|---|---|---|---|
| P+10s | ticks | 10.2 | 0 | 887.4 | 55 | 32 | 720.0 | 424.2 | -11.7 | 1370.8 |
| P+30s | ticks | 30.1 | 0 | 792.0 | 55 | 32 | 624.6 | 417.7 | -113.3 | 1276.9 |
| P+60s | ticks | 60.1 | 0 | 765.5 | 55 | 32 | 598.1 | 370.1 | -160.5 | 1270.6 |
| P+1m | 1m bar open | 98.0 | 0 | 674.9 | 55 | 32 | 507.5 | 312.3 | -246.5 | 1179.8 |
| P+5m | 1m bar open | 338.0 | 0 | 695.9 | 55 | 32 | 528.5 | 359.9 | -197.1 | 1182.8 |
| P+15m | 1m bar open | 938.0 | 0 | 680.4 | 55 | 32 | 513.0 | 316.1 | -193.1 | 1157.1 |

- Events without tick support at P+10s: 0 (listed, not imputed): 
