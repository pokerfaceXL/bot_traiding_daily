# Coordinator Series Report — H-EMA3-13-50-200-HTF-DIRECTION-01 (§15)

> **Date:** 2026-10-03 ~22:36 Europe/Warsaw
> **Experiment:** H-EMA3-13-50-200-HTF-DIRECTION-01
> **Tip / merge:** `c70777a` (FF to origin/main; parent of this Decision). Review PASS job
> `2026-10-03-f006-ema31350200-entry-htf-direc-8f002b67` (engine claude). Coding tip job `5f16b53c`.
> **Artifacts:** `output/f006_ema3_13_50_200_entry_htf_direction/`
> **Card:** `spec/research/F006-hypothesis-ema3-13-50-200-entry-htf-direction.md`

## Summary

HTF direction on `EMA3_13_50_200` **FALSIFIED (a)+(c)+(d)**. Control mean
**+91.1483016** reproduced (max abs diff 0.0, n=423, initial_sl 292/423,
big winners 9 / +1131.9561537333418, floor 7/12). Gated htf_4 mean **+39.2303418**
(delta **-51.9179598**/series), n=362 (36.2/series). Initial_sl share
**rose 2.792471559369414 pp** (0.6903073286052009 to 0.7182320441988951,
260/362). Big-winner PnL retained **0.5556713331636377** (6 / +628.9955850277897), so about
44.43% was removed, not >50%. (a) fires because the mean fell. (b) does
not fire because retention is above 50%. (c) fires because initial_sl
share rose instead of falling >=10pp. (d) fires: this card's (d) is the
standalone floor sentence ("does not improve (stays >= baseline floor)"),
and the floor stayed 7/12. That is not the depth card's reachability rule.
(e) does not fire: 36.2 trades/series. Status stays **CONDITIONAL**. Do
not FREEZE. Not REJECT (ungated Train-1 book stays aggregate-positive).
Next = `H-EMA3-13-50-200-ENTRY-LIQUIDITY-01` on this name's reproduced
baseline +91.1483016 / n=423. This is not the `EMA_50_200` HTF result
(that mean was +20.7369913 with (a)+(b)+(c)+(d)). Do not import
+20.7369913 or +72.6693115.

## Q1–10

1. **Best strategy now?** None promotable. `EMA_50_200`, `BB_20_2_EMA200`,
   `BB_20_25_EMA200`, `EMA3_21_50_200`, and `DONCHIAN_55_NO_TRAIL` stay
   **FREEZE**. The only unfinished catalog5 name is `EMA3_13_50_200`
   (**CONDITIONAL**).
2. **Why that name?** Its own-trades loop is still open. HTF direction
   cut the mean and raised the stop-out share while keeping just over half
   of big-winner PnL, so that axis is closed and the name is not. The
   screen (mean +91.1483016, n=423, 0/10 clear §7) is this name's.
   `EMA_50_200` FREEZE is not evidence here.
3. **Edge from many trades or few big wins?** Few big wins. Ungated Train-1
   entries: 9 trades with net>=29.9 sum to +1131.9561537333418 against cohort
   net +771.2836172145886 (n=423). Gated cell kept 6 of those trades
   (+628.9955850277897, fraction 0.5556713331636377).
4. **Earns when?** Ungated `signal_reverse` runners. Requiring the prior
   closed 4-bar HTF candle to agree did not separate them from stop-outs:
   the gated mean fell by 51.9179598/series and the initial_sl share rose.
5. **Loses when?** The fixed `initial_sl` (0% WR) is a larger share of the
   gated cohort (71.82320441988951%, 260/362) than of the control
   (69.03073286052009%, 292/423). The pooled floor stays 7/12.
6. **Rejected hypotheses?** Add: **H-EMA3-13-50-200-HTF-DIRECTION-01 =
   FALSIFIED (a)+(c)+(d)** at `c70777a`. (b)(e) did not fire. Already closed
   on this name: abs-ATR **FALSIFIED (a)+(c)** `46e4509` / Decision
   `3318658` ((d) not reachable), xsym-agree formula **FALSIFIED (b)**
   `34e2c4a` / Decision `396a3c2` (flat floor, no Val), candle confirm
   **FALSIFIED (a)+(b)+(c)** `9dbcf0d` / Decision `079b697`, breakout
   depth **FALSIFIED (c) only** `c388392` / Decision `07fb827` ((d) not
   reachable), exit-class, partial-exit, long-only, breadth. Not closed
   here: liquidity (last licensed axis). Other names' HTF results do not
   transfer. `EMA_50_200` HTF was (a)+(b)+(c)+(d) at +20.7369913; this
   name's gated mean is +39.2303418 and (b) did not fire.
7. **Unresolved problem?** §7 monthly regularity on this name. Whether the
   signal bar itself traded on above-median base volume is still untested
   on these trades. In-class portfolio combination stays BLOCKED.
8. **Next experiment and why?** **H-EMA3-13-50-200-ENTRY-LIQUIDITY-01.**
   The HTF card's decision_if_fail names liquidity. One §8 change,
   Train-1, this name's control +91.1483016 / n=423. Not an HTF retune.
   Not FREEZE in this Decision. Not holdout. Not another name's measured
   liquidity mean. If liquidity later fails on this name's own trades and
   every licensed axis is cited while the ungated book stays
   aggregate-positive, FREEZE may be written then at §4 level C (not
   REJECT). A passing cell keeps CONDITIONAL.
9. **Why not random new strategies?** §7 develop-not-abandon and §13:
   the last licensed axis on `EMA3_13_50_200` is liquidity. Do not FREEZE
   this name now. Do not start funding-carry, spread-capture, catalog
   mean-reversion, a new family, or another catalog name. Shared-losing
   blocks in-class portfolio combination; it does not license FREEZE or
   REJECT of this name (ungated Train-1 stays aggregate-positive).
10. **What would confirm or falsify the next hyp?** Pre-registered before
    the run on `EMA3_13_50_200` only. Binary prior-20 median base-volume
    gate, `number_of_trials = 1`. A pass needs mean Train-1 net above
    +91.1483016, initial_sl share down >=10pp, >=50% of this name's
    big-winner PnL retained (9 / +1131.9561537333418), pooled floor
    strictly below 7/12, and >=10 trades/series. Any one of (a)–(e) fails
    it. On that card (d) is the standalone floor sentence. Do not import
    +66.5789284 or +97.2455987.
