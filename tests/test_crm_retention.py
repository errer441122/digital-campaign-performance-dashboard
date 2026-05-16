"""Behavioral checks for CRM & retention on the REAL Online Retail II data.

These assert methodological correctness and internal consistency — not a
hand-known structure — because the input is now a real public dataset.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import crm_retention as cr  # noqa: E402

ORDERS = cr.read_orders()
RESULT = cr.run()
KNOWN_SEGMENTS = {
    "Champions", "Loyal customers", "New / promising", "Needs attention",
    "At risk", "Can't lose them", "Hibernating",
}


def test_runs_on_real_dataset() -> None:
    assert "real" in RESULT["dataset"].lower()
    assert RESULT["orders"] == len(ORDERS) > 0


def test_reference_date_is_last_order_plus_one_day() -> None:
    expected = max(o["order_date"] for o in ORDERS) + timedelta(days=1)
    assert RESULT["reference_date"] == expected.isoformat()


def test_rfm_segments_partition_all_customers() -> None:
    segs = RESULT["rfm"]["segments"]
    assert {s["segment"] for s in segs}.issubset(KNOWN_SEGMENTS)
    assert sum(s["customers"] for s in segs) == RESULT["rfm"]["total_customers"]
    assert abs(sum(s["customer_share"] for s in segs) - 1.0) < 0.01


def test_cohort_retention_anchored_and_bounded() -> None:
    co = RESULT["cohort_retention"]
    for c in co["cohorts"]:
        assert len(c["retention"]) == co["max_offset"] + 1
        assert abs(c["retention"][0] - 1.0) < 1e-9  # M0 = acquisition month
        assert all(0.0 <= x <= 1.0 for x in c["retention"])


def test_clv_by_country_is_ranked_thresholded_and_consistent() -> None:
    clv = RESULT["clv_by_country"]
    ranked = clv["ranked"]
    scores = [c["historical_clv_eur"] for c in ranked]
    assert scores == sorted(scores, reverse=True)
    for c in ranked:
        assert c["customers"] >= clv["min_customers"]
        implied = c["orders_per_customer"] * c["avg_order_value_eur"]
        assert abs(implied - c["historical_clv_eur"]) <= max(2.0, c["historical_clv_eur"] * 0.02)
    assert clv["small_n_pooled"]["countries"] >= 0
