# F012 empirical probes (2026-10-06 Europe/Warsaw)

All probes are read-only, few requests, no purchases, no paid sign-ups.

| Probe | Host | Result |
| --- | --- | --- |
| Farside BTC/ETH HTML → daily Total | box | BTC 702 rows from 2024-01-11; Train-1 AC1=0.531, \|median\|=$168.4M; ETH from 2024-07-23 |
| Bybit linear tickers + dated futures OI | box | BTCUSDT OI~$4.9B; dated Dec26 OI~$18M |
| Binance fapi 24h ticker | limen | BTCUSDT quoteVolume~$9.4B (box geo-blocked) |
| Deribit BTC option book summary | box | 940 instruments; OI sum ~358k BTC |
| Deribit history option trades 2024-06-12 | box | 18439 trades / 19 pages |
| HypurrScan `/twap/*` | box | 573 records, 345 active; BTC TWAP ~$5.2M/day gross |
| Bybit announcements delistings | box | total 482 |
| Bybit instruments status=Closed | box | 1000 returned; REST kline empty for LOOM/MATIC; archive HTML lists daily gz |
| Binance CMS catalogId=161 | limen | 439 articles from 2022-02-17; 76 in Train-1; 429 if paged too fast |
| SEC EDGAR CIK 1050446 8-K | box | 48 Train-1 filings; acceptance often 17–18 UTC |
| DefiLlama stables / emissions | box | stables free (USDT 3234 days); emissions API 402 paid |
| Coinbase / Upbit 5m history | box | both return Train-1 windows |

CSVs: `farside_BTC_daily_total.csv`, `farside_ETH_daily_total.csv`, `scoring.csv`.
