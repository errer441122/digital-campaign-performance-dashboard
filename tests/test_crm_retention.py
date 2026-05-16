"""Behavioral checks for the CRM & retention analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import crm_retention as crm  # noqa: E402

RESULT = crm.run()


def test_rfm_segments_partition_all_customers() -> None:
    total = RESULT["rfm"]["total_customers"]
    assigned = sum(s["customers"] for s in RESULT["rfm"]["segments"])
    assert assigned == total
    known = {
        "Champions",
        "Loyal customers",
        "New / promising",
        "Needs attention",
        "At risk",
        "Can't lose them",
        "Hibernating",
    }
    for s in RESULT["rfm"]["segments"]:
        assert s["segment"] in known
        assert s["automation_flow"] and s["trigger"]


def test_cohort_retention_is_anchored_and_bounded() -> None:
    for c in RESULT["cohort_retention"]["cohorts"]:
        assert abs(c["retention"][0] - 1.0) < 1e-9  # M0 is acquisition month
        assert all(0.0 <= x <= 1.0 for x in c["retention"])


def test_clv_ranking_reflects_disclosed_channel_quality() -> None:
    clv = RESULT["clv_by_channel"]
    ranked = [c["acquisition_channel"] for c in clv]
    # disclosed structure: Email/Organic acquire higher-LTV customers than
    # Display/Paid Social
    assert ranked[0] == "Email"
    assert ranked[-1] == "Display"
    assert clv[0]["historical_clv_eur"] > clv[-1]["historical_clv_eur"]


def test_clv_identity_holds() -> None:
    for c in RESULT["clv_by_channel"]:
        implied = c["orders_per_customer"] * c["avg_order_value_eur"]
        assert abs(implied - c["historical_clv_eur"]) < 1.5
