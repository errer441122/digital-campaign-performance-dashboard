# Digital Campaign Performance Dashboard

Simulated digital campaign analytics case study for junior Web/Digital/Campaign Analyst roles.

## Dashboard preview

![Campaign dashboard preview](assets/campaign_dashboard_preview.png)

## What this project shows

- I can define and explain campaign KPIs.
- I can organize campaign data into readable reporting views.
- I can compare performance by channel, device, audience and landing page.
- I can run a small A/B testing analysis with uplift, confidence interval, p-value, Bayesian summary and rollout recommendation.
- I can document attribution logic, funnel/cohort SQL and CRM-style lifecycle metrics without overstating the data source.
- I can translate the same marketing model into Power BI and Tableau-ready artifact specs.
- I can turn metrics into practical optimization recommendations.
- I can document assumptions, limitations and next steps.

## KPI covered

- Impressions
- Clicks
- CTR
- CPC
- Conversions
- Conversion rate
- CPA
- Revenue
- ROAS
- Landing page performance
- Weekly trend
- A/B testing conversion uplift
- Attribution logic
- Funnel, cohort and CRM lifecycle SQL evidence

## Marketing analyst evidence

| Evidence | Where to look | What it demonstrates |
| --- | --- | --- |
| Campaign dashboard | `dashboard/campaign_dashboard.xlsx`, `assets/campaign_dashboard_preview.png` | CTR, CPC, conversion rate, CPA, ROAS, revenue, landing-page and weekly trend reporting |
| A/B testing | `reports/ab_test_marketing_uplift.md`, `src/analyze_ab_test.py` | Conversion uplift, 95% confidence interval, p-value, Bayesian probability and recommendation |
| SQL evidence | `../sql/SQL_EVIDENCE.md`, `../sql/marketing_analytics_evidence.sql` | Joins, CTEs, window functions, funnel, cohort, CRM lifecycle, attribution and KPI aggregation |
| BI evidence | `bi/README.md`, `bi/powerbi/model.bim`, `bi/powerbi/report_spec.json`, `bi/tableau/campaign_performance_workbook.twb` | Power BI semantic model/report spec and Tableau workbook skeleton for mainstream BI review |

## Recruiter 5-minute route

1. Open `reports/executive_summary.md`
2. Review `reports/ab_test_marketing_uplift.md`
3. Open `../sql/SQL_EVIDENCE.md`
4. Review `bi/README.md`
5. Check `dashboard/campaign_dashboard.xlsx`
6. Read `docs/kpi_dictionary.md` and `docs/assumptions_and_limits.md`

## Boundaries

This is a portfolio case study using simulated data only. It does not claim access to real company, client, user, advertising-platform, CRM, GA4 or analytics account data.

## Repository structure

| Path | Purpose |
| --- | --- |
| `data/campaign_performance_sample.csv` | Simulated campaign performance sample with KPI fields. |
| `data/landing_page_sample.csv` | Simulated landing page performance sample. |
| `data/ab_test_conversion_sample.csv` | Simulated landing-page A/B test sample. |
| `dashboard/campaign_dashboard.xlsx` | Excel dashboard workbook for quick review. |
| `reports/executive_summary.md` | Stakeholder-style summary and recommendations. |
| `reports/weekly_campaign_insights.md` | Weekly trend notes by campaign period. |
| `reports/ab_test_marketing_uplift.md` | A/B test readout with uplift, confidence interval, p-value, Bayesian summary and recommendation. |
| `bi/` | Power BI and Tableau text artifacts for mainstream BI evidence. |
| `docs/kpi_dictionary.md` | KPI definitions, formulas and interpretation notes. |
| `docs/assumptions_and_limits.md` | Scope boundaries and simulated-data assumptions. |
| `docs/recruiter_5_min_route.md` | Fast route for recruiters and hiring managers. |
| `src/analyze_ab_test.py` | Rebuilds the A/B test JSON and markdown reports. |
| `src/build_summary.py` | Rebuilds the markdown reports from the CSV files. |
| `src/validate_data.py` | Validates schema, required values and KPI calculations. |
