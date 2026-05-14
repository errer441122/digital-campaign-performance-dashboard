# Looker Studio Report Specification

This is a text specification for how the simulated campaign model would be represented in Looker Studio. It is not a published report URL and it does not connect to a live GA4, Google Ads, CRM or client data source.

## Data Sources

| Source | Role |
| --- | --- |
| `data/campaign_performance_sample.csv` | Main channel, campaign, device, cost and revenue reporting. |
| `data/landing_page_sample.csv` | Landing-page diagnostics and conversion-rate reporting. |
| `data/ab_test_conversion_sample.csv` | A/B test readout and statistical result narrative. |
| Future GA4-style events table | Sessions, users, key events, landing-page events and consent-state diagnostics. |
| Future UTM campaign registry | Source/medium/campaign taxonomy, owner, launch date and QA status. |

## Pages

| Page | Audience question | Core visuals |
| --- | --- | --- |
| Executive Overview | Are campaign results improving and which channel leads? | Spend, revenue, ROAS, conversions, weekly trend and top-channel summary. |
| Channel Performance | Which channel has the strongest cost and conversion profile? | Channel KPI table, CPA bar chart, ROAS bar chart and device filter. |
| Landing Page Performance | Which landing pages need optimization? | Landing-page table, bounce rate, duration and conversion-rate comparison. |
| A/B Test Readout | Is the observed variant uplift material? | Variant scorecards, uplift, confidence interval, p-value and Bayesian probability. |
| Tracking Readiness | Would a live campaign be measurable before launch? | UTM checklist, GA4 event checklist, consent-mode QA status and broken-parameter exceptions. |

## Controls

| Control | Applies to |
| --- | --- |
| Date range | All pages |
| Channel | Executive and channel pages |
| Campaign | Executive, acquisition and tracking pages |
| Device | Channel and landing-page pages |
| Landing page | Landing-page and funnel pages |
| Audience segment | Executive and channel pages |

## Boundary

This artifact demonstrates dashboard design and stakeholder reporting structure. It should be read alongside `../../tracking/looker_studio_dashboard_spec.md` for the GA4, UTM, consent and QA extension.
