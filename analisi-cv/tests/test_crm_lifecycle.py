"""Checks for the purchase-based lifecycle stages."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import crm_lifecycle as cl  # noqa: E402

RESULT = cl.run()
CUSTOMERS = cl.lifecycle()


def test_every_customer_gets_exactly_one_stage() -> None:
    assert RESULT["customers"] == len(CUSTOMERS) > 0
    assert sum(s["customers"] for s in RESULT["stages"]) == RESULT["customers"]
    assert {s["stage"] for s in RESULT["stages"]} <= set(cl.LIFECYCLE_ORDER)
    assert abs(sum(s["revenue_share"] for s in RESULT["stages"]) - 1.0) < 0.001


def test_stage_boundaries() -> None:
    assert cl.stage_for(0, 1) == "New"
    assert cl.stage_for(90, 1) == "New"
    assert cl.stage_for(90, 2) == "Repeat"
    assert cl.stage_for(91, 5) == "At risk"
    assert cl.stage_for(180, 1) == "At risk"
    assert cl.stage_for(181, 1) == "Dormant"
    assert cl.stage_for(365, 1) == "Dormant"
    assert cl.stage_for(366, 9) == "Churned"


def test_revenue_is_labelled_in_gbp() -> None:
    md = cl._md(RESULT)
    assert "GBP" in md and "EUR" not in md
