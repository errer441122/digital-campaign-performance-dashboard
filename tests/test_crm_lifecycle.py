"""Behavioral checks for the hybrid lifecycle module:
REAL purchase-based lifecycle + disclosed SIMULATED engagement/consent overlay.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import crm_lifecycle as cl  # noqa: E402

RESULT = cl.run()
OVERLAY = cl.read_overlay()
LIFECYCLE = cl.real_lifecycle()
KNOWN_STAGES = {"New", "Repeat", "At risk", "Dormant", "Churned"}


def test_real_lifecycle_partitions_all_customers() -> None:
    assert RESULT["customers"] == len(LIFECYCLE) > 0
    assigned = sum(f["customers"] for f in RESULT["lifecycle_funnel_real"])
    assert assigned == RESULT["customers"]
    for f in RESULT["lifecycle_funnel_real"]:
        assert f["stage"] in KNOWN_STAGES
        assert f["campaign_eligible"] + f["suppressed"] == f["customers"]


def test_lead_score_is_bounded_and_explained() -> None:
    for e in OVERLAY.values():
        s = cl.lead_score(e)
        assert 0 <= s["score"] <= 100
        assert isinstance(s["reason"], str) and s["reason"]


def test_consent_is_a_hard_gate_separate_from_score() -> None:
    co = RESULT["consent_overlay"]
    assert set(co["suppressed_by_reason"]).issubset({"opted_out", "unknown"})
    assert co["eligible"] + co["suppressed"] == RESULT["customers"]
    opted_in = sum(1 for v in OVERLAY.values() if v["consent"] == "opted_in")
    assert co["eligible"] == opted_in
    spoof = {
        "page_views": 30, "key_page_views": 9, "email_clicks": 9,
        "form_submits": 3, "demo_request": 1, "webinar_signup": 1,
    }
    assert cl.lead_score(spoof)["score"] == 100  # score never encodes consent


def test_overlay_keys_onto_real_customers_only() -> None:
    real_ids = set(LIFECYCLE)
    assert set(OVERLAY).issubset(real_ids)


def test_priority_list_is_reachable_lapsing_value() -> None:
    for t in RESULT["priority_reachable_value_accounts"]:
        assert t["stage"] in ("At risk", "Dormant")
        assert t["monetary_eur"] > 0
        assert 0 <= t["lead_score"] <= 100
