# Digital Campaign Performance Dashboard

Marketing & CRM analytics case study for Performance/Digital Marketing, CRM/Marketing-Automation and E-commerce roles. **Hybrid data, fully disclosed:** CRM/retention/CLV/lifecycle run on the real UCI *Online Retail II* dataset (CC BY 4.0); campaign/attribution/consent use clearly-labelled deterministic simulation (no public source exists for those). See `data/DATA_CARD.md`.

## Dashboard preview

![Campaign dashboard preview](assets/campaign_dashboard_preview.png)

## What this project shows

- I can define and explain campaign KPIs.
- I can organize campaign data into readable reporting views.
- I can compare performance by channel, device, audience and landing page.
- I can run a small A/B testing analysis with uplift, confidence interval, p-value, Bayesian summary and rollout recommendation.
- I can build multi-touch attribution (first/last/linear/position-based plus a data-driven **Markov removal-effect** model) and show how the channel ranking — and the budget decision — changes versus last-click.
- I can turn attribution into a **saturation-aware budget reallocation** with a square-root response curve, an explicit assumption and a conservative, bounded recommendation.
- I can run a full **CRM lifecycle analysis on real public data** (UCI *Online Retail II*, CC BY 4.0): RFM segmentation → automation flows, cohort retention curves, and historical CLV by country, with small-n markets pooled rather than over-claimed.
- I can build a **hybrid lifecycle + lead-scoring + GDPR-consent** analysis: the lifecycle (New/Repeat/At risk/Dormant/Churned) is derived from **real** purchase behaviour, while the engagement/consent layer is a **clearly-labelled simulated overlay** keyed to the real customers — because no permissive public dataset carries consent — with consent kept as a hard gate separate from the score.
- I can document attribution logic, funnel/cohort SQL and CRM-style lifecycle metrics without overstating the data source.
- I work **hybrid and honest**: real public data where it exists (CRM/retention/CLV/lifecycle on Online Retail II, prepared by `src/prepare_real_data.py` with provenance + SHA256), clearly-labelled deterministic simulation only where no public dataset exists (campaign/attribution/consent). See `data/DATA_CARD.md` and `data/REAL_DATA_PROVENANCE.md`.
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
- RFM segmentation, cohort retention and historical CLV by country (real data)
- Real purchase-based lifecycle + simulated lead scoring & GDPR consent suppression
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
| CRM & retention (REAL) | `analysis/crm_retention.md`, `src/crm_retention.py` | RFM quintile segmentation → automation flows, monthly cohort retention and historical CLV by country, on real Online Retail II data with small-n markets pooled |
| CRM lifecycle & lead scoring (hybrid) | `analysis/crm_lifecycle.md`, `src/crm_lifecycle.py` | Real purchase-based lifecycle + a disclosed simulated engagement/consent overlay; transparent 0-100 lead score with reasons; GDPR consent as a hard gate separate from the score |
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

**Hybrid, by design and disclosed.** The CRM / retention / CLV / lifecycle analyses run on **real public data** — UCI *Online Retail II* (CC BY 4.0), see `data/REAL_DATA_PROVENANCE.md`. The campaign-performance, A/B, multi-touch attribution, budget-reallocation and the engagement/consent overlay use **clearly-labelled deterministic simulation**, because no permissive public dataset carries advertising spend, multi-touch journeys or marketing consent (`data/DATA_CARD.md`). No real company, client, advertising-platform, GA4 or personal data is used or claimed.

## Repository structure

| Path | Purpose |
| --- | --- |
| `data/campaign_performance_sample.csv` | Simulated campaign performance sample with KPI fields (seeded generator output). |
| `data/landing_page_sample.csv` | Simulated landing page performance sample. |
| `data/ab_test_conversion_sample.csv` | Simulated landing-page A/B test sample. |
| `data/conversion_paths_sample.csv` | Simulated multi-touch conversion paths (journeys, conversions, revenue) for attribution. |
| `data/online_retail_orders.csv` | **REAL** orders prepared from UCI Online Retail II for RFM, retention, CLV and lifecycle. |
| `data/REAL_DATA_PROVENANCE.md` | Source URL, CC BY 4.0 attribution, cleaning rules, counts and SHA256 of the real dataset. |
| `data/crm_engagement_overlay.csv` | **Simulated** engagement/consent overlay keyed to the real customer IDs (disclosed). |
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
| `src/prepare_real_data.py` | Downloads (SHA256-pinned) and cleans UCI Online Retail II into `data/online_retail_orders.csv` + provenance. |
| `src/generate_crm_data.py` | Generates the disclosed simulated engagement/consent overlay, keyed to the real customer IDs. |
| `src/analyze_ab_test.py` | Rebuilds the A/B test JSON and markdown reports. |
| `src/build_summary.py` | Rebuilds the markdown reports from the CSV files. |
| `src/campaign_deep_dive.py` | Variance-aware trend, uplift-over-time, segmentation and cross-source reconciliation. |
| `src/attribution.py` | First/last/linear/position-based and data-driven Markov removal-effect attribution. |
| `src/budget_reallocation.py` | Saturation-aware, attribution-driven budget reallocation recommendation. |
| `src/crm_retention.py` | RFM, cohort retention and CLV-by-country on the **real** Online Retail II data. |
| `src/crm_lifecycle.py` | **Real** purchase-based lifecycle + disclosed simulated lead-scoring/consent overlay. |
| `src/build_dashboard.py` | Builds the Excel workbook/PNG; neutralizes CSV formula-injection on every text cell. |
| `src/validate_data.py` | Validates schema, required values and KPI calculations across all sample CSVs. |
| `analysis/campaign_deep_dive.md` | Deep-dive readout: weekly volatility, uplift-over-time, segment economics, reconciliation. |
| `analysis/attribution.md` | Multi-touch attribution readout and last-click vs data-driven credit shift. |
| `analysis/budget_reallocation.md` | Saturation-aware reallocation recommendation with stated assumptions. |
| `analysis/crm_retention.md` | REAL RFM segments → automation, cohort retention and CLV-by-country readout. |
| `analysis/crm_lifecycle.md` | REAL lifecycle funnel + disclosed simulated lead-score/consent overlay and priority list. |
| `tests/test_campaign_deep_dive.py` | Checks the deep-dive metrics, reconciliation and formula-injection hardening. |
| `tests/test_attribution.py` | Checks credit conservation, the Markov chain and the bounded reallocation. |
| `tests/test_crm_retention.py` | Real-data checks: RFM partition, cohort anchoring, CLV identity, dynamic reference date. |
| `tests/test_crm_lifecycle.py` | Real lifecycle partition, score bounds, the consent gate, overlay keys onto real IDs. |
| `tests/test_tracking_docs.py` | Verifies that tracking evidence covers GA4, consent, UTM, QA and Looker Studio artifacts. |

## How to run

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python src/prepare_real_data.py      # downloads + cleans UCI Online Retail II (once)
python src/generate_campaign_data.py
python src/generate_crm_data.py      # simulated engagement/consent overlay on the real customers
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
