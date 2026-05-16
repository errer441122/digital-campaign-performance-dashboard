# Campaign Deep Dive

Sample: 48 campaign rows, 8 landing-page rows, 2 A/B rows.

## Weekly trend & volatility

| Week | Clicks | Conv. | Cost | Revenue | Conv. rate | CPA | ROAS | WoW conv. |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04-06 | 5,444 | 386 | EUR 5,780 | EUR 32,500 | 7.09% | EUR 14.97 | 5.62 | — |
| 2026-04-13 | 5,635 | 399 | EUR 5,982 | EUR 33,638 | 7.08% | EUR 14.99 | 5.62 | +3.4% |
| 2026-04-20 | 5,824 | 413 | EUR 6,185 | EUR 34,775 | 7.09% | EUR 14.97 | 5.62 | +3.5% |
| 2026-04-27 | 6,014 | 426 | EUR 6,387 | EUR 35,912 | 7.08% | EUR 14.99 | 5.62 | +3.1% |
| 2026-05-04 | 6,206 | 440 | EUR 6,589 | EUR 37,050 | 7.09% | EUR 14.98 | 5.62 | +3.3% |
| 2026-05-11 | 6,397 | 453 | EUR 6,792 | EUR 38,188 | 7.08% | EUR 14.99 | 5.62 | +2.9% |

Conversions slope **+13.5/week** (R² 1.00); coefficient of variation — conversions 5.5%, ROAS 0.0%, CPA 0.1%. Verdict: **trend-led growth** — the rise is explained by a stable upward slope, not week-to-week noise.

## Uplift over time (vs week-1 baseline)

Baseline week 2026-04-06: conversion rate 7.09%, ROAS 5.62.

| Week | Conv. rate | CR uplift | ROAS | ROAS uplift |
| --- | ---: | ---: | ---: | ---: |
| 2026-04-06 | 7.09% | +0.0% | 5.62 | +0.0% |
| 2026-04-13 | 7.08% | -0.1% | 5.62 | +0.0% |
| 2026-04-20 | 7.09% | +0.0% | 5.62 | +0.0% |
| 2026-04-27 | 7.08% | -0.1% | 5.62 | +0.0% |
| 2026-05-04 | 7.09% | -0.0% | 5.62 | +0.0% |
| 2026-05-11 | 7.08% | -0.1% | 5.62 | +0.0% |

By the last week, conversion rate is **-0.1%** and ROAS **+0.0%** vs the opening week.

## Audience-segment economics

| Segment | Conv. | Conv. rate | CPA | ROAS | Conv. share | Action |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Existing customers | 756 | 10.50% | EUR 3.11 | 27.39 | 30% | Protect / scale |
| High-intent prospects | 966 | 8.00% | EUR 15.94 | 5.64 | 38% | Optimize |
| Lookalike audience | 508 | 4.99% | EUR 23.63 | 3.39 | 20% | Diagnose / cap |
| Local prospects | 287 | 4.73% | EUR 27.74 | 2.52 | 11% | Diagnose / cap |

### Strongest segment × channel cells

| Segment | Channel | Conv. | Conv. rate | ROAS | Action |
| --- | --- | ---: | ---: | ---: | --- |
| Existing customers | Email | 756 | 10.50% | 27.39 | Protect / scale |
| High-intent prospects | Paid Search | 966 | 8.00% | 5.64 | Optimize |
| Lookalike audience | Paid Social | 508 | 4.99% | 3.39 | Diagnose / cap |
| Local prospects | Display | 287 | 4.73% | 2.52 | Diagnose / cap |

## Cross-source reconciliation

| Check | Status | Detail |
| --- | --- | --- |
| campaign landing pages exist in landing_page_sample | PASS | all 4 campaign pages covered |
| campaign conversions reconcile across channel and segment cuts | PASS | grand=2517, by_channel=2517, by_segment=2517 |
| campaign vs landing-page conversion volume (independent samples) | INFO | campaign=2517, landing=2517 (separate simulated samples; reported, not asserted equal) |
| A/B file is one experiment with traffic split ~ 1.0 | PASS | experiments=['lp_checkout_2026w16'], split_sum=1.0 |
| landing-page conversion_rate matches conversions/sessions | PASS | all rows consistent |

## Boundary

Simulated portfolio data only; no real advertising-platform, client, CRM, GA4 or user data. Weekly cuts are observational and the three CSVs are independent simulated samples — the reconciliation checks internal consistency and shared keys, not equality across samples.
