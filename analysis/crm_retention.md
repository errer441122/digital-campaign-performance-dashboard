# CRM & Retention

1,357 simulated orders, 930 customers, six monthly cohorts.

## RFM lifecycle segments → automation

| Segment | Customers | Share | Revenue | Automation flow | Trigger |
| --- | ---: | ---: | ---: | --- | --- |
| Champions | 177 | 19% | EUR 32,800 | VIP & referral flow | RFM in top quintiles |
| Loyal customers | 140 | 15% | EUR 20,155 | Cross-sell & loyalty tier | ≥2 orders, recent |
| At risk | 186 | 20% | EUR 19,735 | Win-back sequence | No order 45–90 days |
| New / promising | 160 | 17% | EUR 10,274 | Welcome / onboarding series | First order < 30 days |
| Hibernating | 140 | 15% | EUR 9,850 | Low-cost reactivation then sunset | No order > 90 days |
| Can't lose them | 46 | 5% | EUR 6,370 | High-touch reactivation | High value, lapsed |
| Needs attention | 81 | 9% | EUR 5,406 | Targeted reactivation offer | Recency slipping |

## Cohort retention (repeat-purchase, by signup month)

| Cohort | Customers | M0 | M1 | M2 | M3 | M4 | M5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2025-12 | 152 | 100% | 32% | 13% | 7% | 1% | 1% |
| 2026-01 | 167 | 100% | 29% | 15% | 8% | 3% | 0% |
| 2026-02 | 169 | 100% | 31% | 15% | 4% | 0% | 0% |
| 2026-03 | 153 | 100% | 36% | 13% | 0% | 0% | 0% |
| 2026-04 | 147 | 100% | 31% | 0% | 0% | 0% | 0% |
| 2026-05 | 142 | 100% | 0% | 0% | 0% | 0% | 0% |

M0 is the acquisition month (100% by construction); later columns are the share of the cohort that purchased again in that month.

## Historical CLV by acquisition channel

| Channel | Customers | Orders/customer | AOV | Historical CLV |
| --- | ---: | ---: | ---: | ---: |
| Email | 150 | 1.70 | EUR 86.38 | EUR 146.85 |
| Organic Search | 170 | 1.62 | EUR 82.90 | EUR 134.10 |
| Paid Search | 210 | 1.51 | EUR 78.62 | EUR 118.68 |
| Direct | 90 | 1.43 | EUR 81.93 | EUR 117.43 |
| Paid Social | 180 | 1.25 | EUR 67.12 | EUR 83.90 |
| Display | 130 | 1.20 | EUR 58.79 | EUR 70.55 |

**Email** acquires the highest-lifetime-value customers and **Display** the lowest. A channel can win on last-click CPA and still lose on lifetime value — acquisition budget and CRM treatment should be set on CLV, not first-order economics alone (see `analysis/budget_reallocation.md`).

## Boundary

Simulated portfolio data only; no real CRM, e-commerce or customer data. Channel→retention structure is disclosed in `data/DATA_CARD.md`; relationships are observational, not causal.
