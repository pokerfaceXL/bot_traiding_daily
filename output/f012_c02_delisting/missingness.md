# F012-C02 missingness report (Train-1 2024-03-01 → 2025-03-01)

## Catalog rows by exchange × contract_type × category

| exchange | contract_type | category | rows |
|---|---|---|---|
| binance | linear_perp | perp_delist | 18 |
| binance | linear_perp | token_delist | 7 |
| binance | spot | token_delist | 33 |
| bybit | linear_perp | perp_delist | 57 |
| bybit | spot | token_delist | 48 |

## Perp delisting events: data availability

| exchange | has_perp_1m | has_ticks_ann | has_perp_1h | has_oi | has_funding | has_spot_1m |
|---|---|---|---|---|---|---|
| binance | 25/25 | 25/25 | 25/25 | 25/25 | 25/25 | 18/25 |
| bybit | 55/57 | 55/57 | 53/57 | 54/57 | 54/57 | 33/57 |

**Usable (p0 + primary entry + eff-1h exit)**: 80/82 → missing-event rate 2.4%.

Excluded events (not silently dropped):

| event_id | exchange | symbol | notice_duration_h |
|---|---|---|---|
| BYBIT-202406030807-ZKUSDT | bybit | ZKUSDT | 87.87 |
| BYBIT-202502271009-MONUSDT | bybit | MONUSDT | 166.8 |

Included vs excluded: median notice 143.6h vs 127.4h; bybit share 69% vs 100%.

## Spot coverage for identification

| exchange | spot_venue | events |
|---|---|---|
| binance | binance_spot | 15 |
| binance | bybit_spot | 3 |
| binance | nan | 7 |
| bybit | binance_spot | 22 |
| bybit | bybit_spot | 11 |
| bybit | nan | 24 |
