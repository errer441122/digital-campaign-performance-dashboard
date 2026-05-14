# Looker Studio Dashboard Spec

This is a Looker Studio dashboard specification for a campaign measurement layer. It is not a published Looker Studio report and it does not connect to a live GA4, Google Ads, CRM or client data source.

## Data Sources

| Source | Fields | Current status |
| --- | --- | --- |
| Simulated GA4-style events table | `event_date`, `event_name`, `session_id`, `source`, `medium`, `campaign`, `landing_page`, `campaign_id`, `form_id`, `value`, `currency`, consent fields | Blueprint only; no live GA4 export committed. |
| Campaign performance CSV | Impressions, clicks, cost, conversions, revenue, CTR, CPC, CPA, ROAS, channel, audience, device and campaign | Current simulated portfolio data in `data/campaign_performance_sample.csv`. |
| Landing page CSV | Landing page, device, sessions, bounce rate, duration, conversions and conversion rate | Current simulated portfolio data in `data/landing_page_sample.csv`. |
| A/B test CSV | Variant, sessions, conversions, revenue, primary metric and traffic split | Current simulated portfolio data in `data/ab_test_conversion_sample.csv`. |
| UTM campaign registry | `campaign_id`, UTM fields, owner, objective, market, launch date and QA status | Defined in `UTM_TAXONOMY.md`. |
| Tracking QA log | Test case, environment, consent state, expected event and actual status | Defined in `TRACKING_QA_CHECKLIST.md`. |

## Pages

| Page | Purpose | Core visuals |
| --- | --- | --- |
| Executive Overview | Show campaign outcome and trend at a glance. | Conversion scorecards, ROAS scorecard, weekly trend, best channel and recommendation note. |
| Channel Performance | Compare traffic, cost and conversion quality by channel. | Channel table, source/medium heatmap, conversion-rate bar chart, CPA and ROAS cards. |
| Landing Page Performance | Identify landing pages with strong or weak conversion behavior. | Landing-page table, bounce-rate chart, duration, conversion rate and recommendation field. |
| Campaign Acquisition / UTM Quality | Validate campaign taxonomy and acquisition grouping. | UTM compliance table, invalid source/medium alerts, campaign registry status. |
| Conversion Funnel | Track movement from impression and click to landing visit and conversion. | Funnel chart, stage conversion rates, drop-off table by campaign. |
| A/B Test Readout | Present experiment or observational channel comparison. | Variant scorecards, uplift, confidence interval, p-value and Bayesian probability. |
| Consent And Tracking QA | Separate performance signals from measurement quality issues. | Consent-state summary, QA pass/fail table, duplicate conversion checks. |

## Core Controls

| Control | Applies to |
| --- | --- |
| Date range | All pages |
| Channel | Executive, channel, funnel and acquisition pages |
| Campaign | All campaign-level pages |
| Device | Landing page, funnel and QA pages |
| Landing page | Landing page and funnel pages |
| Consent status | QA, funnel and executive diagnostic views |
| Audience segment | Channel, executive and acquisition pages |

## Metrics And Calculated Fields

| Metric | Formula or source | Notes |
| --- | --- | --- |
| CTR | `clicks / impressions` | Current simulated campaign KPI. |
| CPC | `cost_eur / clicks` | Current simulated campaign KPI. |
| CPA | `cost_eur / conversions` | Current simulated campaign KPI. |
| ROAS | `revenue_eur / cost_eur` | Current simulated campaign KPI. |
| Landing-page conversion rate | `conversions / sessions` | Current simulated landing-page KPI. |
| Lead conversion rate | `generate_lead / landing_visits` | Future GA4-style implementation KPI. |
| UTM validity rate | `valid_utm_links / total_campaign_links` | Pre-launch campaign governance metric. |
| Tracking QA pass rate | `passed_tracking_cases / total_tracking_cases` | Release-readiness metric. |
| Observed conversion count | Count of key events where measurement is allowed and observable | Keep separate from modeled or estimated conversions. |

## Portfolio Boundary

The current workbook and reports use simulated campaign data. This Looker Studio spec demonstrates how the same campaign analytics model would be presented for GA4-style events, UTM governance, consent-aware interpretation and tracking QA in a real implementation.

