# Consent Mode And GDPR Notes

This portfolio does not implement legal compliance and is not legal advice. It documents measurement implications and analytics implementation controls for a consent-aware campaign setup.

## Consent Mode Signals

| Signal | Denied behavior | Measurement implication |
| --- | --- | --- |
| `analytics_storage` | Analytics cookies are not written or read. | User and session observability can be reduced; reporting may rely on cookieless pings or modeled estimates depending on setup. |
| `ad_storage` | Advertising cookies are not written or read. | Ads conversion measurement and remarketing identifiers may be limited. |
| `ad_user_data` | User data cannot be sent to Google advertising services for ads purposes. | Enhanced conversions and audience features may be restricted. |
| `ad_personalization` | Data cannot be used for ads personalization. | Remarketing and personalized ad activation may be limited. |

## Cookie Categories

| Category | Example use | Analytics handling |
| --- | --- | --- |
| Strictly necessary | Security, load balancing, form operation | Usually outside analytics opt-in, but should be documented by privacy owner. |
| Analytics | GA4 measurement, dashboarding, aggregate behavior analysis | Controlled by `analytics_storage`. |
| Advertising | Ads measurement, remarketing, conversion linking | Controlled by `ad_storage`, `ad_user_data` and `ad_personalization`. |
| Functional | Preferences, non-essential personalization | Keep separate from GA4 event parameters unless explicitly needed and approved. |

## Practical Measurement Notes

- Set denied defaults before analytics or advertising tags fire for EEA/UK traffic.
- Send consent updates only after the consent banner or CMP records the user's choice.
- Do not send personal data such as email, phone, name, account ID or free-text form fields to GA4 parameters.
- Consent gaps can reduce observable conversions and change attribution quality.
- Dashboard interpretation should separate observed conversions from modeled or estimated conversions.
- Consent state should be part of QA evidence so analysts can explain conversion-count differences across tools.
- Internal traffic and debug events should be excluded or flagged before executive reporting.

## Reporting Interpretation

| Scenario | What the dashboard should say |
| --- | --- |
| Consent granted | Events and conversions are observable according to the implemented tags and configured retention. |
| Analytics denied | Treat user-level and session-level metrics as incomplete; avoid over-interpreting drop-offs. |
| Ads denied | Avoid treating ads-platform conversions as complete truth; compare with CRM or backend conversion counts where available. |
| Partial consent | Segment diagnostic reporting by consent state where possible. |
| Unknown consent state | Flag as measurement quality risk, not as a performance insight. |

## QA Matrix

| Test state | Expected analytics behavior |
| --- | --- |
| Accept all | GA4 `page_view`, CTA event and key event fire with expected parameters. |
| Reject all | Tags respect denied storage; no analytics or ads cookies are written. |
| Analytics only | GA4 measurement works while ads storage and personalization remain denied. |
| Ads only | Advertising settings follow consent, but analytics reporting remains limited if `analytics_storage` is denied. |
| Change consent mid-session | Consent update is sent and subsequent hits reflect the latest state. |

