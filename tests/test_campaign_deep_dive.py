"""Behavioral checks for the campaign deep dive and the CSV-injection
hardening in the dashboard builder."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import campaign_deep_dive as deep  # noqa: E402
import build_dashboard  # noqa: E402

RESULT = deep.run()


def test_reconciliation_has_no_failures() -> None:
    statuses = [c["status"] for c in RESULT["reconciliation"]]
    assert "fail" not in statuses
    assert any(s == "pass" for s in statuses)


def test_weekly_trend_quantifies_signal_vs_noise() -> None:
    wt = RESULT["weekly_trend"]
    assert len(wt["weeks"]) >= 6
    assert wt["conversions_slope_per_week"] > 0
    assert 0.0 <= wt["conversions_trend_r2"] <= 1.0001
    assert wt["conversions_cv"] >= 0.0
    # week 1 has no WoW; later weeks do
    assert wt["weeks"][0]["wow_conversions"] is None
    assert wt["weeks"][-1]["wow_conversions"] is not None


def test_uplift_over_time_is_anchored_to_first_week() -> None:
    up = RESULT["uplift_over_time"]
    assert up["weeks"][0]["week"] == up["baseline_week"]
    assert abs(up["weeks"][0]["cr_uplift_vs_baseline"]) < 1e-9
    assert len(up["weeks"]) == len(RESULT["weekly_trend"]["weeks"])


def test_segmentation_is_ranked_and_complete() -> None:
    seg = RESULT["segmentation"]["by_audience_segment"]
    roas = [s["roas"] for s in seg]
    assert roas == sorted(roas, reverse=True)
    assert {s["audience_segment"] for s in seg} == {
        "Existing customers",
        "High-intent prospects",
        "Lookalike audience",
        "Local prospects",
    }
    # retention email economics should top the ROAS ranking
    assert seg[0]["audience_segment"] == "Existing customers"
    for s in seg:
        assert s["action"] in {"Protect / scale", "Optimize", "Diagnose / cap"}


def test_formula_injection_is_neutralized() -> None:
    n = build_dashboard.neutralize_spreadsheet_formula
    assert n("=cmd|' /c calc'!A1") == "'=cmd|' /c calc'!A1"
    assert n("+1+1") == "'+1+1"
    assert n("-2+3") == "'-2+3"
    assert n("@SUM(A1)") == "'@SUM(A1)"
    # benign content is left untouched
    assert n("/promo") == "/promo"
    assert n("Keep budget stable") == "Keep budget stable"
