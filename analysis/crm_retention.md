# CRM & Retention (real data)

**36,969 real orders** from 5,878 customers — *Online Retail II* (UCI, CC BY 4.0), see `data/REAL_DATA_PROVENANCE.md`. Recency reference date: 2011-12-10 (last order + 1 day).

## RFM lifecycle segments → automation

| Segment | Customers | Share | Revenue | Automation flow | Trigger |
| --- | ---: | ---: | ---: | --- | --- |
| Champions | 1,565 | 27% | EUR 12,697,321 | VIP & referral flow | RFM in top quintiles |
| Loyal customers | 966 | 16% | EUR 2,329,998 | Cross-sell & loyalty tier | ≥2 orders, recent |
| At risk | 1,176 | 20% | EUR 1,450,319 | Win-back sequence | Recency in 2nd quintile |
| Can't lose them | 140 | 2% | EUR 438,495 | High-touch reactivation | High value, lapsed |
| Hibernating | 1,035 | 18% | EUR 414,128 | Low-cost reactivation then sunset | Low recency and value |
| New / promising | 547 | 9% | EUR 227,005 | Welcome / onboarding series | Recent first order, low freq/value |
| Needs attention | 449 | 8% | EUR 186,165 | Targeted reactivation offer | Recency slipping |

## Cohort retention (repeat-purchase, by signup month)

| Cohort | Customers | M0 | M1 | M2 | M3 | M4 | M5 | M6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009-12 | 955 | 100% | 35% | 33% | 43% | 38% | 36% | 38% |
| 2010-01 | 383 | 100% | 21% | 31% | 31% | 26% | 30% | 26% |
| 2010-02 | 374 | 100% | 24% | 22% | 29% | 25% | 20% | 19% |
| 2010-03 | 443 | 100% | 19% | 23% | 24% | 23% | 20% | 25% |
| 2010-04 | 294 | 100% | 19% | 19% | 16% | 18% | 22% | 28% |
| 2010-05 | 254 | 100% | 16% | 17% | 17% | 18% | 26% | 21% |
| 2010-06 | 270 | 100% | 17% | 19% | 20% | 23% | 29% | 13% |
| 2010-07 | 186 | 100% | 16% | 18% | 30% | 29% | 14% | 11% |
| 2010-08 | 162 | 100% | 20% | 30% | 32% | 17% | 12% | 10% |
| 2010-09 | 243 | 100% | 23% | 23% | 12% | 9% | 10% | 14% |
| 2010-10 | 377 | 100% | 26% | 15% | 12% | 9% | 8% | 13% |
| 2010-11 | 325 | 100% | 18% | 9% | 10% | 8% | 9% | 13% |
| 2010-12 | 76 | 100% | 9% | 5% | 9% | 12% | 7% | 5% |
| 2011-01 | 71 | 100% | 17% | 21% | 20% | 21% | 15% | 15% |
| 2011-02 | 124 | 100% | 16% | 15% | 19% | 22% | 15% | 15% |
| 2011-03 | 179 | 100% | 18% | 22% | 20% | 22% | 15% | 21% |
| 2011-04 | 106 | 100% | 25% | 20% | 20% | 18% | 24% | 18% |
| 2011-05 | 111 | 100% | 23% | 24% | 16% | 22% | 21% | 26% |
| 2011-06 | 108 | 100% | 23% | 21% | 27% | 20% | 29% | 8% |
| 2011-07 | 102 | 100% | 22% | 30% | 27% | 34% | 16% | 0% |
| 2011-08 | 106 | 100% | 27% | 31% | 26% | 17% | 0% | 0% |
| 2011-09 | 189 | 100% | 27% | 38% | 15% | 0% | 0% | 0% |
| 2011-10 | 221 | 100% | 32% | 16% | 0% | 0% | 0% | 0% |
| 2011-11 | 191 | 100% | 14% | 0% | 0% | 0% | 0% | 0% |
| 2011-12 | 28 | 100% | 0% | 0% | 0% | 0% | 0% | 0% |

M0 is the acquisition month (100% by construction); later columns are the share of the cohort that placed another order in that month offset. Late cohorts are right-censored (fewer observable months).

## Historical CLV by country

Online Retail II has no media/channel field, so lifetime value is broken down by **country**. Only countries with ≥ 30 customers are ranked (smaller ones are too noisy to compare).

| Country | Customers | Orders/customer | AOV | Historical CLV |
| --- | ---: | ---: | ---: | ---: |
| Germany | 107 | 7.38 | EUR 547.07 | EUR 4039.09 |
| France | 93 | 6.56 | EUR 579.64 | EUR 3801.93 |
| Spain | 39 | 3.87 | EUR 718.74 | EUR 2782.83 |
| United Kingdom | 5,349 | 6.27 | EUR 438.96 | EUR 2752.37 |

_37 smaller countries (290 customers, EUR 2,126,713 revenue) are pooled and not ranked._

Among comparable markets, **Germany** shows the highest historical CLV (EUR 4,039) and **United Kingdom** the lowest (EUR 2,752). Acquisition and CRM treatment should weigh realised lifetime value by market, not first-order value alone.

## Boundary

Real public transactional data (Online Retail II, UCI, CC BY 4.0) — no synthetic values in this analysis. Provenance and cleaning rules: `data/REAL_DATA_PROVENANCE.md`. Relationships are observational, not causal; the data is one UK retailer 2009-2011 and does not generalise to other businesses.
