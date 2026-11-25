# Customer lifecycle stages

Purchase recency and order count for 5,878 customers in *Online Retail II* (UCI, CC BY 4.0). Revenue is each stage's historical spend, so it shows what is at stake, not a forecast.

| Stage | Rule | Customers | Share | Historical revenue | Revenue share | Recommended action |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| New | last order within 90 days, 1 order | 365 | 6% | GBP 139,190 | 1% | Onboarding / second-purchase nudge |
| Repeat | last order within 90 days, 2+ orders | 2,524 | 43% | GBP 13,886,457 | 80% | Loyalty / cross-sell flow |
| At risk | last order 91-180 days ago | 588 | 10% | GBP 1,059,343 | 6% | Win-back sequence |
| Dormant | last order 181-365 days ago | 787 | 13% | GBP 1,052,124 | 6% | Reactivation offer |
| Churned | last order more than 365 days ago | 1,614 | 27% | GBP 1,294,436 | 7% | Low-cost reactivation, then sunset |

The thresholds are a convention, not something this dataset proves. Relationships are observational, not causal.
