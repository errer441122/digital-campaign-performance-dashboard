# Campaign Deep Dive

Sample: 48 campaign rows, 8 landing-page rows, 2 A/B rows.

## Weekly trend & volatility

| Week | Clicks | Conv. | Cost | Revenue | Conv. rate | CPA | ROAS | WoW conv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-06 | 5,417 | 408 | EUR 5,782 | EUR 33,652 | 7.53% | EUR 14.17 | 5.82 | — |
| 2026-04-13 | 5,821 | 437 | EUR 6,272 | EUR 36,129 | 7.51% | EUR 14.35 | 5.76 | +7.1% |
| 2026-04-20 | 5,733 | 443 | EUR 6,024 | EUR 36,697 | 7.73% | EUR 13.60 | 6.09 | +1.4% |
| 2026-04-27 | 6,451 | 487 | EUR 7,014 | EUR 40,470 | 7.55% | EUR 14.40 | 5.77 | +9.9% |
| 2026-05-04 | 6,008 | 455 | EUR 6,459 | EUR 37,435 | 7.57% | EUR 14.20 | 5.80 | -6.6% |
| 2026-05-11 | 6,259 | 485 | EUR 6,780 | EUR 39,179 | 7.75% | EUR 13.98 | 5.78 | +6.6% |

Conversions slope **+13.8/week** (R² 0.73); coefficient of variation — conversions 6.1%, ROAS 2.0%, CPA 1.9%. Verdict: **trend-led growth** — the rise is explained by a stable upward slope, not week-to-week noise.

## Uplift over time (vs week-1 baseline)

Baseline week 2026-04-06: conversion rate 7.53%, ROAS 5.82.

| Week | Conv. rate | CR uplift | ROAS | ROAS uplift |
| --- | ---: | ---: | ---: | ---: |
| 2026-04-06 | 7.53% | +0.0% | 5.82 | +0.0% |
| 2026-04-13 | 7.51% | -0.3% | 5.76 | -1.0% |
| 2026-04-20 | 7.73% | +2.6% | 6.09 | +4.7% |
| 2026-04-27 | 7.55% | +0.2% | 5.77 | -0.9% |
| 2026-05-04 | 7.57% | +0.5% | 5.80 | -0.4% |
| 2026-05-11 | 7.75% | +2.9% | 5.78 | -0.7% |

By the last week, conversion rate is **+2.9%** and ROAS **-0.7%** vs the opening week.

## Audience-segment economics

| Segment | Conv. | Conv. rate | CPA | ROAS | Conv. share | Action |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Existing customers | 768 | 10.83% | EUR 2.97 | 28.00 | 28% | Protect / scale |
| High-intent prospects | 1,120 | 9.02% | EUR 14.70 | 5.98 | 41% | Optimize |
| Lookalike audience | 537 | 5.22% | EUR 22.38 | 3.44 | 20% | Diagnose / cap |
| Local prospects | 290 | 4.91% | EUR 26.08 | 2.61 | 11% | Diagnose / cap |

### Strongest segment × channel cells

| Segment | Channel | Conv. | Conv. rate | ROAS | Action |
| --- | --- | ---: | ---: | ---: | --- |
| Existing customers | Email | 768 | 10.83% | 28.00 | Protect / scale |
| High-intent prospects | Paid Search | 1,120 | 9.02% | 5.98 | Optimize |
| Lookalike audience | Paid Social | 537 | 5.22% | 3.44 | Diagnose / cap |
| Local prospects | Display | 290 | 4.91% | 2.61 | Diagnose / cap |

## Cross-source reconciliation

| Check | Status | Detail |
| --- | --- | --- |
| campaign landing pages exist in landing_page_sample | PASS | all 4 campaign pages covered |
| campaign conversions reconcile across channel and segment cuts | PASS | grand=2715, by_channel=2715, by_segment=2715 |
| campaign vs landing-page conversion volume (independent samples) | INFO | campaign=2715, landing=2756 (separate simulated samples; reported, not asserted equal) |
| A/B file is one experiment with traffic split ~ 1.0 | PASS | experiments=['lp_checkout_2026w16'], split_sum=1.0 |
| landing-page conversion_rate matches conversions/sessions | PASS | all rows consistent |

## Boundary

Simulated portfolio data only; no real advertising-platform, client, CRM, GA4 or user data. Weekly cuts are observational and the three CSVs are independent simulated samples — the reconciliation checks internal consistency and shared keys, not equality across samples.
