# Tracking QA Checklist

Use this checklist before launching a campaign landing page or adding a new tracked conversion. It is written for implementation review, not as evidence that this repository contains a live production tag setup.

## Pre-Launch Checks

| Check | Pass criteria | Evidence to keep |
| --- | --- | --- |
| UTM parameters present | `utm_source`, `utm_medium` and `utm_campaign` are present on every paid, email or partner campaign URL. | Campaign-link QA sheet or registry export. |
| UTM values lowercase | No uppercase, spaces, inconsistent separators or unmanaged synonyms. | UTM validation output. |
| Source/medium mapping valid | Each source/medium pair maps to the intended GA4 default channel group. | Controlled taxonomy review. |
| Redirects preserve UTMs | Landing page URL keeps UTM parameters after redirects, consent redirects or locale redirects. | Browser/network test capture. |
| Landing page fires once | Initial `page_view` fires once per page load in DebugView or network inspection. | GA4 DebugView or Tag Assistant screenshot. |
| CTA click captured | Primary CTA click sends expected event and parameters. | Debug event payload. |
| Form submit fires once | Successful form submit sends one `generate_lead` event, not zero and not two. | Debug event payload and test log. |
| Form validation protected | Failed validation does not fire a conversion event. | Negative test log. |
| Thank-you page not duplicated | Refreshing thank-you page does not duplicate conversion, or deduplication rule is documented. | Refresh test result. |
| Conversion parameters complete | Conversion contains `campaign_id`, `landing_page`, `form_id` and relevant `lead_type`. | Event parameter payload. |
| Consent accepted flow tested | Accepted consent allows expected analytics behavior. | CMP state plus tag result. |
| Consent rejected flow tested | Rejected consent prevents disallowed storage and respects denied state. | Cookie/storage inspection. |
| Partial consent tested | Analytics-only and ads-only choices behave as configured. | CMP state plus network result. |
| Internal traffic flagged | Office, staging and QA traffic is excluded or labeled. | Filter or debug flag evidence. |
| Cross-domain journey documented | If form, checkout or booking is on another domain, linker and referral handling are documented. | Cross-domain test notes. |

## Core Tracking Cases

| Case | Steps | Expected result |
| --- | --- | --- |
| Tagged first visit | Open campaign URL with valid UTMs. | `page_view` contains landing URL and campaign parameters. |
| CTA engagement | Click hero and mid-page CTA. | CTA event includes text, position, campaign ID and page type. |
| Lead conversion | Submit valid lead form. | One `generate_lead` key event fires with form and campaign parameters. |
| Newsletter signup | Submit newsletter form. | `sign_up` fires with method and campaign context. |
| Demo booking | Complete demo-booking flow. | `book_demo` or qualified conversion event fires once. |
| Consent denied landing | Reject analytics and advertising storage before navigating. | Disallowed cookies are not written; reporting is interpreted as consent-limited. |
| UTM broken link | Test uppercase, missing campaign or invalid medium. | QA flags the link before launch. |
| Redirect path | Visit campaign URL that redirects to localized landing page. | UTMs survive and session attribution remains intact. |

## QA Log Template

| Field | Example |
| --- | --- |
| `test_case_id` | `qa_utm_redirect_001` |
| `environment` | `staging` |
| `browser_device` | `Chrome desktop` |
| `consent_state` | `analytics_storage=granted; ad_storage=denied` |
| `campaign_url` | `https://example.com/demo?utm_source=google&utm_medium=cpc&utm_campaign=2026_q2_it_leadgen_smb` |
| `expected_event` | `generate_lead` |
| `actual_status` | `pass` |
| `notes` | `Form event fired once with form_id and campaign_id.` |

