from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_tracking_docs_cover_ga4_consent_utm_looker_and_qa() -> None:
    ga4 = read_text("tracking/GA4_EVENT_PLAN.md")
    utm = read_text("tracking/UTM_TAXONOMY.md")
    consent = read_text("tracking/CONSENT_MODE_GDPR_NOTES.md")
    qa = read_text("tracking/TRACKING_QA_CHECKLIST.md")
    looker = read_text("tracking/looker_studio_dashboard_spec.md")
    readme = read_text("README.md")

    for required in [
        "page_view",
        "session_start",
        "generate_lead",
        "sign_up",
        "book_demo",
        "purchase",
        "BigQuery Export Mock Shape",
        "Custom Dimensions",
    ]:
        assert required in ga4

    for required in [
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "2026_q2_it_leadgen_smb",
        "paid_social",
        "GA4 default channel grouping",
    ]:
        assert required in utm

    for required in [
        "analytics_storage",
        "ad_storage",
        "ad_user_data",
        "ad_personalization",
        "not legal advice",
        "observed conversions",
        "modeled or estimated conversions",
    ]:
        assert required in consent

    for required in [
        "Form submit fires once",
        "Thank-you page not duplicated",
        "Consent rejected flow tested",
        "Cross-domain journey documented",
    ]:
        assert required in qa

    for required in [
        "Executive Overview",
        "Channel Performance",
        "Landing Page Performance",
        "Campaign Acquisition / UTM Quality",
        "Conversion Funnel",
        "A/B Test Readout",
        "Consent And Tracking QA",
        "Date range",
        "Device",
    ]:
        assert required in looker

    assert "tracking/GA4_EVENT_PLAN.md" in readme
    assert "tracking/looker_studio_dashboard_spec.md" in readme

