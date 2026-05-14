"""Analyze the simulated landing-page A/B test sample."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "ab_test_conversion_sample.csv"
REPORTS_DIR = ROOT / "reports"
JSON_PATH = REPORTS_DIR / "ab_test_marketing_uplift.json"
MD_PATH = REPORTS_DIR / "ab_test_marketing_uplift.md"


def normal_cdf(value: float) -> float:
    return 0.5 * math.erfc(-value / math.sqrt(2))


def read_variants() -> dict[str, dict[str, float | str]]:
    with DATA_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    variants: dict[str, dict[str, float | str]] = {}
    for row in rows:
        sessions = int(row["sessions"])
        conversions = int(row["conversions"])
        variants[row["variant"]] = {
            "label": row["variant_label"],
            "sessions": sessions,
            "conversions": conversions,
            "revenue_eur": float(row["revenue_eur"]),
            "conversion_rate": conversions / sessions,
            "revenue_per_session": float(row["revenue_eur"]) / sessions,
        }
    if set(variants) != {"A", "B"}:
        raise ValueError("Expected exactly variants A and B")
    return variants


def analyze() -> dict[str, object]:
    variants = read_variants()
    a = variants["A"]
    b = variants["B"]

    sessions_a = int(a["sessions"])
    sessions_b = int(b["sessions"])
    conversions_a = int(a["conversions"])
    conversions_b = int(b["conversions"])
    rate_a = float(a["conversion_rate"])
    rate_b = float(b["conversion_rate"])

    absolute_uplift = rate_b - rate_a
    relative_uplift = absolute_uplift / rate_a

    pooled_rate = (conversions_a + conversions_b) / (sessions_a + sessions_b)
    pooled_se = math.sqrt(pooled_rate * (1 - pooled_rate) * (1 / sessions_a + 1 / sessions_b))
    z_score = absolute_uplift / pooled_se
    p_value = math.erfc(abs(z_score) / math.sqrt(2))

    unpooled_se = math.sqrt(
        rate_a * (1 - rate_a) / sessions_a + rate_b * (1 - rate_b) / sessions_b
    )
    ci_lower = absolute_uplift - 1.96 * unpooled_se
    ci_upper = absolute_uplift + 1.96 * unpooled_se

    posterior_mean_a = (conversions_a + 1) / (sessions_a + 2)
    posterior_mean_b = (conversions_b + 1) / (sessions_b + 2)
    posterior_var_a = (
        (conversions_a + 1)
        * (sessions_a - conversions_a + 1)
        / ((sessions_a + 2) ** 2 * (sessions_a + 3))
    )
    posterior_var_b = (
        (conversions_b + 1)
        * (sessions_b - conversions_b + 1)
        / ((sessions_b + 2) ** 2 * (sessions_b + 3))
    )
    posterior_diff_mean = posterior_mean_b - posterior_mean_a
    posterior_diff_sd = math.sqrt(posterior_var_a + posterior_var_b)
    probability_b_beats_a = normal_cdf(posterior_diff_mean / posterior_diff_sd)

    recommendation = (
        "Ship variant B with a guarded rollout"
        if p_value < 0.05 and ci_lower > 0 and probability_b_beats_a > 0.95
        else "Keep testing before rollout"
    )

    return {
        "experiment_id": "lp_checkout_2026w16",
        "primary_metric": "conversion_rate",
        "variant_a": round_metrics(a),
        "variant_b": round_metrics(b),
        "absolute_uplift": round(absolute_uplift, 6),
        "relative_uplift": round(relative_uplift, 6),
        "z_score": round(z_score, 4),
        "p_value_two_tailed": round(p_value, 6),
        "confidence_interval_95": {
            "lower": round(ci_lower, 6),
            "upper": round(ci_upper, 6),
        },
        "bayesian_probability_b_beats_a": round(probability_b_beats_a, 6),
        "recommendation": recommendation,
        "boundary": "Simulated portfolio data; no real advertising, client, CRM, GA4 or user data.",
    }


def round_metrics(metrics: dict[str, float | str]) -> dict[str, float | int | str]:
    return {
        "label": str(metrics["label"]),
        "sessions": int(metrics["sessions"]),
        "conversions": int(metrics["conversions"]),
        "revenue_eur": round(float(metrics["revenue_eur"]), 2),
        "conversion_rate": round(float(metrics["conversion_rate"]), 6),
        "revenue_per_session": round(float(metrics["revenue_per_session"]), 4),
    }


def fmt_pct(value: float) -> str:
    return f"{value:.2%}"


def build_markdown(results: dict[str, object]) -> str:
    variant_a = results["variant_a"]
    variant_b = results["variant_b"]
    if not isinstance(variant_a, dict) or not isinstance(variant_b, dict):
        raise TypeError("Variant results must be dictionaries")

    ci = results["confidence_interval_95"]
    if not isinstance(ci, dict):
        raise TypeError("Confidence interval must be a dictionary")

    return f"""# Marketing A/B Test: Landing Page Conversion Uplift

## Test setup

This mini-project simulates a landing-page A/B test for a paid campaign. The primary metric is conversion rate; revenue per session is used as a business guardrail.

| Variant | Sessions | Conversions | Conversion rate | Revenue/session |
| --- | ---: | ---: | ---: | ---: |
| A - {variant_a['label']} | {variant_a['sessions']:,} | {variant_a['conversions']:,} | {fmt_pct(float(variant_a['conversion_rate']))} | EUR {float(variant_a['revenue_per_session']):.2f} |
| B - {variant_b['label']} | {variant_b['sessions']:,} | {variant_b['conversions']:,} | {fmt_pct(float(variant_b['conversion_rate']))} | EUR {float(variant_b['revenue_per_session']):.2f} |

## Statistical readout

- Absolute uplift: {fmt_pct(float(results['absolute_uplift']))}
- Relative uplift: {fmt_pct(float(results['relative_uplift']))}
- Frequentist test: two-proportion z-test
- z-score: {float(results['z_score']):.4f}
- p-value: {float(results['p_value_two_tailed']):.6f}
- 95% confidence interval for conversion-rate uplift: {fmt_pct(float(ci['lower']))} to {fmt_pct(float(ci['upper']))}
- Bayesian summary: probability that variant B beats variant A is {fmt_pct(float(results['bayesian_probability_b_beats_a']))}

## Recommendation

{results['recommendation']}. Keep a short guardrail period after rollout: monitor mobile conversion rate, revenue per session, CPA and refund/cancellation signals before scaling budget.

## Boundary

This is simulated portfolio evidence only. It does not use real advertising-platform exports, client data, CRM records, GA4 account data or user-level tracking.
"""


def main() -> None:
    results = analyze()
    REPORTS_DIR.mkdir(exist_ok=True)
    JSON_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    MD_PATH.write_text(build_markdown(results), encoding="utf-8")
    print(f"Wrote {JSON_PATH.name} and {MD_PATH.name}")


if __name__ == "__main__":
    main()
