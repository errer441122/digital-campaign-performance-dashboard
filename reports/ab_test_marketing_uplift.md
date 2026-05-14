# Marketing A/B Test: Landing Page Conversion Uplift

## Test setup

This mini-project simulates a landing-page A/B test for a paid campaign. The primary metric is conversion rate; revenue per session is used as a business guardrail.

| Variant | Sessions | Conversions | Conversion rate | Revenue/session |
| --- | ---: | ---: | ---: | ---: |
| A - Control landing page | 8,400 | 462 | 5.50% | EUR 4.85 |
| B - Short-form landing page | 8,200 | 533 | 6.50% | EUR 5.93 |

## Statistical readout

- Absolute uplift: 1.00%
- Relative uplift: 18.18%
- Frequentist test: two-proportion z-test
- z-score: 2.7137
- p-value: 0.006654
- 95% confidence interval for conversion-rate uplift: 0.28% to 1.72%
- Bayesian summary: probability that variant B beats variant A is 99.66%

## Recommendation

Ship variant B with a guarded rollout. Keep a short guardrail period after rollout: monitor mobile conversion rate, revenue per session, CPA and refund/cancellation signals before scaling budget.

## Boundary

This is simulated portfolio evidence only. It does not use real advertising-platform exports, client data, CRM records, GA4 account data or user-level tracking.
