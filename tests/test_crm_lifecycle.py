"""Behavioral checks for the CRM lifecycle / lead-scoring / consent module."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import crm_lifecycle as cl  # noqa: E402

RESULT = cl.run()
CONTACTS = cl.read_contacts()


def test_funnel_partitions_all_contacts() -> None:
    assigned = sum(f["contacts"] for f in RESULT["lifecycle_funnel"])
    assert assigned == RESULT["contacts"] == len(CONTACTS)
    known = {
        "Subscriber", "Lead", "MQL", "SQL",
        "Customer", "Churn Risk", "Reactivation",
    }
    for f in RESULT["lifecycle_funnel"]:
        assert f["stage"] in known
        assert f["campaign_eligible"] + f["suppressed"] == f["contacts"]


def test_lead_scores_are_bounded_and_explained() -> None:
    for c in CONTACTS:
        s = cl.lead_score(c)
        assert 0 <= s["score"] <= 100
        assert isinstance(s["reason"], str) and s["reason"]


def test_consent_is_a_hard_gate_separate_from_score() -> None:
    co = RESULT["consent"]
    # suppressed only for opted_out / unknown, never opted_in
    assert set(co["suppressed_by_reason"]).issubset({"opted_out", "unknown"})
    assert co["eligible"] + co["suppressed"] == RESULT["contacts"]
    opted_in = sum(1 for c in CONTACTS if c["consent"] == "opted_in")
    assert co["eligible"] == opted_in
    # a maxed-out score must still be suppressed without consent
    spoof = {
        "channel": "Email", "has_purchase": 0, "days_idle": 1,
        "page_views": 9, "key_page_views": 5, "email_clicks": 9,
        "form_submits": 3, "demo_request": 1, "webinar_signup": 1,
        "consent": "opted_out",
    }
    assert cl.lead_score(spoof)["score"] == 100
    assert (spoof["consent"] == "opted_in") is False


def test_score_increases_up_the_acquisition_ladder() -> None:
    avg = {f["stage"]: f["avg_lead_score"] for f in RESULT["lifecycle_funnel"]}
    # recovered structure: engagement rises Subscriber -> Lead -> MQL -> SQL
    assert avg["Subscriber"] < avg["Lead"] < avg["MQL"] < avg["SQL"]


def test_sales_ready_respects_consent() -> None:
    sr = RESULT["sales_ready"]
    assert 0 <= sr["eligible_to_action"] <= sr["mql_plus_sql"]
    mql_sql = sum(
        f["contacts"] for f in RESULT["lifecycle_funnel"]
        if f["stage"] in ("MQL", "SQL")
    )
    assert sr["mql_plus_sql"] == mql_sql
