# GA4 Event Plan

This is a measurement blueprint for a live campaign implementation. It does not claim access to a live GA4 property, Google Tag Manager container, BigQuery export, CMP, CRM or advertising account.

## Event Naming Rules

- Prefer GA4 recommended events when they fit the business action.
- Use lowercase snake case for custom events and parameters.
- Do not send email, phone, name, account ID, free-text notes or other personal data as event parameters.
- Keep conversion events stable across campaigns so trend and benchmark reporting remains comparable.
- Register high-value custom parameters as custom dimensions only when they are needed for reporting.

## Core Event Map

| Business action | GA4 event | Required parameters | Conversion? | Notes |
| --- | --- | --- | --- | --- |
| Campaign landing visit | `page_view` | `page_location`, `page_referrer`, `utm_source`, `utm_medium`, `utm_campaign`, `landing_page` | No | Used for campaign traffic quality and landing-page performance. |
| New campaign session | `session_start` | `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`, `campaign_id` | No | Supports source/medium/campaign analysis and default channel grouping. |
| Primary CTA click | `select_content` or `cta_click` | `cta_id`, `cta_text`, `cta_position`, `page_type`, `campaign_id` | No | Use `select_content` when it is enough; use `cta_click` if CTA reporting needs a dedicated event. |
| Lead form submit | `generate_lead` | `form_id`, `campaign_id`, `landing_page`, `lead_type`, `consent_analytics_storage` | Yes | Main lead conversion. Fire only after successful submission. |
| Newsletter signup | `sign_up` | `method`, `campaign_id`, `landing_page`, `source_medium` | Optional | Lifecycle entry event when newsletter growth is a campaign objective. |
| Demo booking | `book_demo` | `form_id`, `campaign_id`, `landing_page`, `lead_type`, `booking_type` | Yes | Qualified conversion for B2B campaign flows. |
| Purchase or paid conversion | `purchase` | `transaction_id`, `value`, `currency`, `campaign_id`, `items` | Yes | Include only when the site has ecommerce or paid conversion tracking. |
| Scroll depth milestone | `scroll` or `scroll_depth` | `percent_scrolled`, `page_type`, `campaign_id` | No | Micro-conversion for landing-page engagement diagnostics. |
| Consent state change | `consent_update` | `analytics_storage`, `ad_storage`, `ad_user_data`, `ad_personalization`, `consent_region` | No | Diagnostic event for QA or internal reporting; do not include personal data. |

## Conversions And Audiences

| Item | Configuration | Reporting use |
| --- | --- | --- |
| Primary key event | Mark `generate_lead` as a GA4 key event | Campaign conversion rate and lead volume. |
| Qualified key event | Mark `book_demo` or CRM-qualified lead import as a key event when available | Performance quality beyond raw form volume. |
| Revenue event | Mark `purchase` as ecommerce conversion only when ecommerce data exists | Revenue and value-based reporting. |
| Audience: engaged campaign visitors | Users with `page_view` from campaign UTMs and engagement threshold met | Remarketing or lifecycle analysis where allowed by consent. |
| Audience: lead intent, no conversion | Users with CTA click or high scroll depth but no `generate_lead` | Landing-page and nurture optimization. |
| Audience: consent denied | Sessions with denied analytics or ads storage | Measurement quality diagnostics, not user targeting. |

## Custom Dimensions

| Parameter | Scope | Why it matters |
| --- | --- | --- |
| `campaign_id` | Event | Joins GA4-style events to campaign registry and UTM governance. |
| `landing_page` | Event | Landing-page conversion and QA reporting. |
| `form_id` | Event | Form-level conversion diagnostics. |
| `lead_type` | Event | Distinguishes newsletter, demo, sales, trial or content leads. |
| `cta_position` | Event | Measures above-the-fold, sticky, footer or inline CTA behavior. |
| `consent_analytics_storage` | Event | Separates observed measurement from consent-limited sessions. |

## BigQuery Export Mock Shape

The repository does not include a real GA4 BigQuery export. A future mock or public demo export should preserve this minimum analytical shape:

| Field | Example | Use |
| --- | --- | --- |
| `event_date` | `20260514` | Date filtering and trend reporting. |
| `event_timestamp` | `1778784000000000` | Event ordering and session reconstruction. |
| `user_pseudo_id` | `pseudo_123` | Anonymous user-level stitching where allowed. |
| `ga_session_id` | `987654321` | Session-level funnel analysis. |
| `event_name` | `generate_lead` | Event filtering and key-event reporting. |
| `page_location` | `https://example.com/landing?utm_source=google...` | Landing page and UTM validation. |
| `source`, `medium`, `campaign` | `google`, `cpc`, `2026_q2_it_leadgen_smb` | Channel and campaign attribution. |
| `campaign_id` | `cmp_2026_q2_it_smb_leads` | Join key to campaign registry. |
| `form_id` | `lead_form_primary` | Form QA and conversion diagnostics. |
| `value`, `currency` | `250.00`, `EUR` | Revenue or qualified-value reporting when applicable. |
| `analytics_storage`, `ad_storage` | `granted`, `denied` | Consent-aware interpretation. |

## Current Dataset Mapping

| Current simulated-data field | GA4-style analogue |
| --- | --- |
| `impressions` | Ad-platform delivery metric, not a native GA4 event. |
| `clicks` | Campaign traffic entering tracked landing pages. |
| `landing_page` | `page_location` or landing-page content group. |
| `conversions` | `generate_lead`, `sign_up`, `book_demo` or `purchase`, depending on the business flow. |
| `channel` | Default channel group, source/medium or campaign channel. |
| `campaign` | `utm_campaign` or campaign registry name. |
| `revenue_eur` | Ecommerce or offline value imported only when sourced and permitted. |
| `conversion_rate` | Key events divided by sessions, users, clicks or landing visits depending on denominator definition. |

