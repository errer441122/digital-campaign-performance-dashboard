# UTM Taxonomy

This taxonomy defines how campaign links should be named before launch so GA4, Looker Studio and downstream campaign reports can group traffic consistently.

## Required Parameters

| Parameter | Rule | Example |
| --- | --- | --- |
| `utm_source` | Platform, sender or publisher from a controlled list | `google`, `meta`, `linkedin`, `newsletter`, `display_network` |
| `utm_medium` | Acquisition medium from a controlled list | `cpc`, `paid_social`, `email`, `display`, `organic_social` |
| `utm_campaign` | `yyyy_qx_market_objective_audience` | `2026_q2_it_leadgen_smb` |
| `utm_content` | `creative_format_message_variant` | `search_text_ad_value_prop_a` |
| `utm_term` | Keyword, topic or audience segment when relevant | `marketing_automation_tool` |

## Controlled Values

| Channel | Allowed `utm_source` examples | Allowed `utm_medium` values |
| --- | --- | --- |
| Paid Search | `google`, `bing` | `cpc`, `paid_search` |
| Paid Social | `meta`, `linkedin`, `tiktok` | `paid_social` |
| Email | `newsletter`, `crm`, `marketing_cloud` | `email` |
| Display | `display_network`, `programmatic`, `dv360` | `display` |
| Organic Social | `linkedin`, `meta`, `youtube` | `organic_social` |
| Referral or partner | `partner_site`, `affiliate` | `referral`, `affiliate` |

## Naming Convention

```text
utm_source=google
utm_medium=cpc
utm_campaign=2026_q2_it_leadgen_smb
utm_content=search_text_ad_value_prop_a
utm_term=marketing_automation_tool
```

Recommended full URL pattern:

```text
https://example.com/demo?utm_source=google&utm_medium=cpc&utm_campaign=2026_q2_it_leadgen_smb&utm_content=search_text_ad_value_prop_a&utm_term=marketing_automation_tool
```

## Valid And Invalid Examples

| Status | Example | Reason |
| --- | --- | --- |
| Valid | `utm_source=linkedin&utm_medium=paid_social&utm_campaign=2026_q2_it_leadgen_smb&utm_content=carousel_case_study_a` | Lowercase, controlled source/medium and campaign includes date, market, objective and audience. |
| Valid | `utm_source=newsletter&utm_medium=email&utm_campaign=2026_q2_it_retention_customers&utm_content=html_offer_b` | Email traffic is separated from paid media and has stable campaign naming. |
| Invalid | `utm_source=Google&utm_medium=CPC&utm_campaign=Spring Campaign` | Uppercase values and spaces fragment reporting. |
| Invalid | `utm_source=meta&utm_medium=paid-social&utm_campaign=leadgen` | Medium is not the controlled `paid_social`; campaign lacks date, market and audience. |
| Invalid | `utm_source=linkedin&utm_medium=paid_social` | Missing `utm_campaign`, so campaign reporting and QA fail. |

## Quality Checks

- Required fields present: `utm_source`, `utm_medium`, `utm_campaign`.
- All values lowercase.
- No spaces, accents or unencoded special characters.
- No mixed separators such as `paid-social`, `paid social` and `paid_social`.
- `utm_campaign` includes year, quarter, market, objective and audience.
- `utm_source` and `utm_medium` map to the expected GA4 default channel grouping.
- `utm_content` identifies creative or message variant without creating a new campaign for every asset.
- Campaign link survives redirects without dropping UTM parameters.
- Campaign registry includes owner, market, landing page, start date, end date, expected conversion and QA status.

## Campaign Registry Fields

| Field | Purpose |
| --- | --- |
| `campaign_id` | Stable join key across UTM taxonomy, GA4 events, CRM exports and dashboards. |
| `utm_campaign` | Public campaign name used in URLs and analytics tools. |
| `owner` | Business owner accountable for naming and launch quality. |
| `market` | Country or region. |
| `objective` | Lead generation, newsletter growth, retention, trial, demo or revenue. |
| `landing_page` | Expected destination URL. |
| `expected_key_event` | GA4 key event such as `generate_lead`, `sign_up`, `book_demo` or `purchase`. |
| `qa_status` | Pre-launch tracking status: `pass`, `review` or `blocked`. |

