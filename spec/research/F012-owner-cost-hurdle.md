# F012 · Binding owner cost hurdle (2026-10-06)

Owner correction: **Derivatives fees are BINDING** for go/no-go reporting.

| component | value |
|---|---|
| taker fee | 0.0440% = **4.4 bps**/side |
| maker fee | 0.0200% = **2.0 bps**/side |
| measured basket half-spread + impact | **≈ 0.56 bps**/side |
| **owner-tier RT (taker)** | 2 × (4.4 + 0.56) = **≈ 9.92 bp** |
| **owner-tier RT (maker bound)** | 2 × (2.0 + 0.56) = **≈ 5.12 bp** |

**Primary** success / cost tables must use owner-tier RT (~9.9 taker; also show maker bound).
**Stress only:** 50 / 75 / 100 bp RT.
**34 bp** was an old harness assumption; it may appear as a **historical reference only**,
clearly labeled obsolete for owner decisions. Do not treat 34 bp as the primary hurdle.

Applies to F012-C02 and subsequent F012 candidates unless the owner revises fees again.
