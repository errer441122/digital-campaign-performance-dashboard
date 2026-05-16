# Digital Campaign Performance Dashboard

Simulated digital campaign analytics case study for junior Web/Digital/Campaign Analyst roles.

## Dashboard preview

![Campaign dashboard preview](assets/campaign_dashboard_preview.png)

## What this project shows

- I can define and explain campaign KPIs.
- I can organize campaign data into readable reporting views.
- I can compare performance by channel, device, audience and landing page.
- I can run a small A/B testing analysis with uplift, confidence interval, p-value, Bayesian summary and rollout recommendation.
- I can build multi-touch attribution (first/last/linear/position-based plus a data-driven **Markov removal-effect** model) and show how the channel ranking — and the budget decision — changes versus last-click.
- I can turn attribution into a **saturation-aware budget reallocation** with a square-root response curve, an explicit assumption and a conservative, bounded recommendation.
- I can run a full **CRM lifecycle analysis**: RFM segmentation mapped to automation flows, cohort retention curves, and historical CLV by acquisition channel — showing a channel can win on last-click CPA and still lose on lifetime value.
- I can build a **lifecycle-stage engine + lead scoring + GDPR consent gate**: rule-based Subscriber→Lead→MQL→SQL→Customer/Churn/Reactivation staging, a transparent 0-100 lead score with a per-contact reason, and consent treated as a hard suppression gate kept *separate from the score*.
- I can document attribution logic, funnel/cohort SQL and CRM-style lifecycle metrics without overstating the data source.
- I generate the sample data from a single seeded, documented generator (`data/DATA_CARD.md`) — no hand-tuned numbers.
- I can define a GA4 tracking plan with event names, parameters, key events, audiences, custom dimensions and a BigQuery-style export shape.
- I can document Consent Mode/GDPR measurement implications, UTM taxonomy governance and practical tracking QA cases.
- I can translate the same marketing model into Power BI, Tableau and Looker Studio-ready artifact specs.
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
- Multi-touch attribution (first/last/linear/position-based + Markov data-driven)
- Marginal efficiency and saturation-aware budget reallocation
- RFM segmentation, cohort retention and historical CLV by channel
- Lifecycle stages, lead scoring and GDPR consent suppression
- Attribution logic
- Funnel, cohort and CRM lifecycle SQL evidence
- GA4 key event mapping
- Consent Mode/GDPR tracking controls
- UTM taxonomy compliance
- Looker Studio dashboard specification
- Tracking QA status

## Marketing analyst evidence

| Evidence | Where to look | What it demonstrates |
| --- | --- | --- |
| Campaign dashboard | `dashboard/campaign_dashboard.xlsx`, `assets/campaign_dashboard_preview.png` | CTR, CPC, conversion rate, CPA, ROAS, revenue, landing-page and weekly trend reporting |
| A/B testing | `reports/ab_test_marketing_uplift.md`, `src/analyze_ab_test.py` | Conversion uplift, 95% confidence interval, p-value, Bayesian probability and recommendation |
| Campaign deep dive | `analysis/campaign_deep_dive.md`, `src/campaign_deep_dive.py` | Variance-aware weekly trend (slope, R², coefficient of variation), uplift-over-time vs baseline, audience-segment and segment×channel economics with per-segment action, and a cross-source reconciliation of the CSVs |
| Multi-touch attribution | `analysis/attribution.md`, `src/attribution.py` | First/last/linear/position-based credit plus a data-driven Markov removal-effect model (absorbing chain solved analytically); quantifies how last-click over-credits closers and starves assists |
| Budget reallocation | `analysis/budget_reallocation.md`, `src/budget_reallocation.py` | Saturation-aware (sqrt response) reallocation between acquisition channels driven by attributed efficiency, with Email protected as non-spend-elastic and a bounded, conservative recommendation |
| CRM & retention | `analysis/crm_retention.md`, `src/crm_retention.py` | RFM quintile segmentation mapped to automation flows, monthly cohort retention by signup month, and historical CLV by acquisition channel (CPA-vs-LTV bridge to the media analysis) |
| CRM lifecycle & lead scoring | `analysis/crm_lifecycle.md`, `src/crm_lifecycle.py` | Rule-based lifecycle staging, transparent 0-100 lead score with per-contact reasons, and a GDPR consent suppression gate kept separate from the score; sales-ready pipeline split by consent |
| GA4/tracking plan | `tracking/GA4_EVENT_PLAN.md`, `tracking/TRACKING_QA_CHECKLIST.md` | GA4 event model, key events, parameters, audiences, BigQuery-style export shape and QA cases |
| UTM and consent governance | `tracking/UTM_TAXONOMY.md`, `tracking/CONSENT_MODE_GDPR_NOTES.md` | Campaign URL taxonomy, source/medium controls, Consent Mode signals and GDPR-aware measurement boundaries |
| SQL evidence | `sql/SQL_EVIDENCE.md`, `sql/marketing_analytics_evidence.sql` | Joins, CTEs, window functions, funnel, CRM lifecycle, attribution and KPI aggregation |
| BI evidence | `bi/README.md`, `bi/powerbi/model.bim`, `bi/powerbi/report_spec.json`, `bi/tableau/campaign_performance_workbook.twb`, `bi/looker_studio/report_spec.md`, `tracking/looker_studio_dashboard_spec.md` | Power BI semantic model/report spec, Tableau workbook skeleton and Looker Studio dashboard specification for mainstream BI review |

## Recruiter 5-minute route

1. Open `reports/executive_summary.md`
2. Review `reports/ab_test_marketing_uplift.md`, then `analysis/attribution.md`, `analysis/budget_reallocation.md`, `analysis/crm_retention.md` and `analysis/crm_lifecycle.md`
3. Open `sql/SQL_EVIDENCE.md`
4. Read `tracking/GA4_EVENT_PLAN.md`, `tracking/UTM_TAXONOMY.md`, `tracking/CONSENT_MODE_GDPR_NOTES.md` and `tracking/TRACKING_QA_CHECKLIST.md`
5. Review `bi/README.md`, `bi/looker_studio/report_spec.md` and `tracking/looker_studio_dashboard_spec.md`
6. Check `dashboard/campaign_dashboard.xlsx`
7. Read `docs/kpi_dictionary.md` and `docs/assumptions_and_limits.md`

## Boundaries

This is a portfolio case study using simulated data only. It does not claim access to real company, client, user, advertising-platform, CRM, GA4 or analytics account data.

## Repository structure

| Path | Purpose |
| --- | --- |
| `data/campaign_performance_sample.csv` | Simulated campaign performance sample with KPI fields (seeded generator output). |
| `data/landing_page_sample.csv` | Simulated landing page performance sample. |
| `data/ab_test_conversion_sample.csv` | Simulated landing-page A/B test sample. |
| `data/conversion_paths_sample.csv` | Simulated multi-touch conversion paths (journeys, conversions, revenue) for attribution. |
| `data/crm_orders_sample.csv` | Simulated customer-level orders (cohort, channel, value) for RFM, retention and CLV. |
| `data/crm_contacts_sample.csv` | Simulated contact-level CRM table (engagement signals + consent) for lifecycle staging and lead scoring. |
| `data/DATA_CARD.md` | Generative model, seed and disclosed assumptions for the simulated data. |
| `requirements.txt` | Pinned Python dependencies for workbook generation and tests. |
| `dashboard/campaign_dashboard.xlsx` | Excel dashboard workbook for quick review. |
| `sql/SQL_EVIDENCE.md` | Ten reviewer-friendly SQL queries using the committed sample CSVs. |
| `sql/marketing_analytics_evidence.sql` | Runnable DuckDB companion file for the SQL evidence. |
| `tracking/GA4_EVENT_PLAN.md` | GA4 event model, key events, parameters, audiences, custom dimensions and BigQuery-style export shape for a live implementation. |
| `tracking/UTM_TAXONOMY.md` | UTM naming convention, source/medium controls, valid/invalid examples and campaign registry fields. |
| `tracking/CONSENT_MODE_GDPR_NOTES.md` | Consent Mode signals, cookie categories and consent-aware measurement interpretation. |
| `tracking/TRACKING_QA_CHECKLIST.md` | Pre-launch web analytics QA cases for UTMs, redirects, forms, consent states and conversion duplication. |
| `tracking/looker_studio_dashboard_spec.md` | Looker Studio page, source, control and metric specification for a GA4-style campaign dashboard. |
| `reports/executive_summary.md` | Stakeholder-style summary and recommendations. |
| `reports/weekly_campaign_insights.md` | Weekly trend notes by campaign period. |
| `reports/ab_test_marketing_uplift.md` | A/B test readout with uplift, confidence interval, p-value, Bayesian summary and recommendation. |
| `bi/` | Power BI, Tableau and Looker Studio text artifacts for mainstream BI evidence. |
| `docs/kpi_dictionary.md` | KPI definitions, formulas and interpretation notes. |
| `docs/assumptions_and_limits.md` | Scope boundaries and simulated-data assumptions. |
| `docs/recruiter_5_min_route.md` | Fast route for recruiters and hiring managers. |
| `src/generate_campaign_data.py` | Seeded, documented generator for the campaign, landing and conversion-path CSVs. |
| `src/generate_crm_data.py` | Seeded generator for the customer-level CRM order sample and the contact-level CRM table. |
| `src/analyze_ab_test.py` | Rebuilds the A/B test JSON and markdown reports. |
| `src/build_summary.py` | Rebuilds the markdown reports from the CSV files. |
| `src/campaign_deep_dive.py` | Variance-aware trend, uplift-over-time, segmentation and cross-source reconciliation. |
| `src/attribution.py` | First/last/linear/position-based and data-driven Markov removal-effect attribution. |
| `src/budget_reallocation.py` | Saturation-aware, attribution-driven budget reallocation recommendation. |
| `src/crm_retention.py` | RFM segmentation, cohort retention and historical CLV by acquisition channel. |
| `src/crm_lifecycle.py` | Lifecycle-stage engine, transparent lead scoring and GDPR consent suppression gate. |
| `src/build_dashboard.py` | Builds the Excel workbook/PNG; neutralizes CSV formula-injection on every text cell. |
| `src/validate_data.py` | Validates schema, required values and KPI calculations across all sample CSVs. |
| `analysis/campaign_deep_dive.md` | Deep-dive readout: weekly volatility, uplift-over-time, segment economics, reconciliation. |
| `analysis/attribution.md` | Multi-touch attribution readout and last-click vs data-driven credit shift. |
| `analysis/budget_reallocation.md` | Saturation-aware reallocation recommendation with stated assumptions. |
| `analysis/crm_retention.md` | RFM segments → automation, cohort retention and CLV-by-channel readout. |
| `analysis/crm_lifecycle.md` | Lifecycle funnel, lead-score reasons, consent suppression and sales-ready pipeline. |
| `tests/test_campaign_deep_dive.py` | Checks the deep-dive metrics, reconciliation and formula-injection hardening. |
| `tests/test_attribution.py` | Checks credit conservation, the Markov chain and the bounded reallocation. |
| `tests/test_crm_retention.py` | Checks RFM partitioning, cohort anchoring and the CLV identity. |
| `tests/test_crm_lifecycle.py` | Checks funnel partitioning, score bounds, the consent gate and recovered structure. |
| `tests/test_tracking_docs.py` | Verifies that tracking evidence covers GA4, consent, UTM, QA and Looker Studio artifacts. |

## How to run

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python src/generate_campaign_data.py
python src/generate_crm_data.py
python src/validate_data.py
python src/analyze_ab_test.py
python src/build_summary.py
python src/campaign_deep_dive.py
python src/attribution.py
python src/budget_reallocation.py
python src/crm_retention.py
python src/crm_lifecycle.py
python src/build_dashboard.py
```

To run the SQL evidence after installing DuckDB:

```bash
duckdb < sql/marketing_analytics_evidence.sql
```
