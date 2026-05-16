"""Behavioral checks for multi-touch attribution and budget reallocation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import attribution  # noqa: E402
import budget_reallocation as budget  # noqa: E402

ATTR = attribution.run()
PATHS = attribution.read_paths()
TOTAL_CONV = sum(r["conversions"] for r in PATHS)


def test_rule_based_models_conserve_total_credit() -> None:
    for model in ("first_touch", "last_touch", "linear", "position_based"):
        allocated = sum(
            v["conversions"] for v in ATTR["rule_based"][model].values()
        )
        assert abs(allocated - TOTAL_CONV) < 1.0, model


def test_markov_base_probability_is_a_probability() -> None:
    p = ATTR["markov"]["base_conversion_probability"]
    assert 0.0 < p < 1.0


def test_markov_credit_sums_to_total_conversions() -> None:
    allocated = sum(c["conversions"] for c in ATTR["markov"]["credit"].values())
    assert abs(allocated - TOTAL_CONV) < TOTAL_CONV * 0.001


def test_last_touch_over_credits_closers_vs_markov() -> None:
    shift = {s["channel"]: s["delta_conversions"] for s in ATTR["credit_shift_vs_last_touch"]}
    # closing channels lose credit, assisting channels gain it
    assert shift["Paid Search"] < 0
    assert shift["Display"] > 0
    assert shift["Paid Social"] > 0


def test_budget_reallocation_is_bounded_and_email_is_held() -> None:
    r = budget.run()
    cap = r["total_paid_spend_eur"] * r["reallocation_cap_pct"]
    assert r["move_eur"] <= cap + 1e-6
    assert r["donor"] != "Email" and r["recipient"] != "Email"
    held = [c for c in r["channels"] if c["channel"] == "Email"][0]
    assert held["reallocatable"] is False


def test_budget_reallocation_net_gain_is_non_negative_and_modest() -> None:
    r = budget.run()
    assert r["expected_incremental_conversions"] >= 0.0
    # saturation model must not reproduce the naive constant-efficiency blow-up
    assert r["expected_incremental_conversions"] < TOTAL_CONV * 0.1
