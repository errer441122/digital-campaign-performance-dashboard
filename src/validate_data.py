"""Validate the simulated digital campaign sample data."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
LANDING_PATH = ROOT / "data" / "landing_page_sample.csv"
AB_TEST_PATH = ROOT / "data" / "ab_test_conversion_sample.csv"
PATHS_PATH = ROOT / "data" / "conversion_paths_sample.csv"
CRM_PATH = ROOT / "data" / "crm_orders_sample.csv"

CAMPAIGN_COLUMNS = {
    "date",
    "channel",
    "campaign",
    "audience_segment",
    "device",
    "landing_page",
    "impressions",
    "clicks",
    "cost_eur",
    "conversions",
    "revenue_eur",
    "ctr",
    "cpc",
    "conversion_rate",
    "cpa",
    "roas",
}

LANDING_COLUMNS = {
    "landing_page",
    "device",
    "sessions",
    "bounce_rate",
    "avg_session_duration_sec",
    "conversions",
    "revenue_eur",
    "conversion_rate",
    "primary_issue",
    "recommendation",
}

AB_TEST_COLUMNS = {
    "experiment_id",
    "variant",
    "variant_label",
    "sessions",
    "conversions",
    "revenue_eur",
    "primary_metric",
    "traffic_split",
    "notes",
}


PATHS_COLUMNS = {
    "path_id",
    "path",
    "journeys",
    "conversions",
    "revenue_eur",
}


CRM_COLUMNS = {
    "customer_id",
    "acquisition_channel",
    "cohort_month",
    "signup_date",
    "order_id",
    "order_date",
    "order_value_eur",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require_columns(rows: list[dict[str, str]], expected: set[str], name: str) -> None:
    if not rows:
        raise ValueError(f"{name} has no rows")
    actual = set(rows[0])
    missing = expected - actual
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")


def close_enough(actual: float, expected: float, tolerance: float) -> bool:
    return abs(actual - expected) <= tolerance


def validate_campaign_rows(rows: list[dict[str, str]]) -> None:
    for row_number, row in enumerate(rows, start=2):
        impressions = int(row["impressions"])
        clicks = int(row["clicks"])
        cost = float(row["cost_eur"])
        conversions = int(row["conversions"])
        revenue = float(row["revenue_eur"])

        if min(impressions, clicks, conversions) < 0 or min(cost, revenue) < 0:
            raise ValueError(f"Negative value in campaign row {row_number}")
        if clicks > impressions:
            raise ValueError(f"Clicks exceed impressions in row {row_number}")

        checks = {
            "ctr": (clicks / impressions, 0.0002),
            "cpc": (cost / clicks, 0.01),
            "conversion_rate": (conversions / clicks, 0.0002),
            "cpa": (cost / conversions, 0.02),
            "roas": (revenue / cost, 0.02),
        }
        for field, (expected, tolerance) in checks.items():
            actual = float(row[field])
            if not close_enough(actual, expected, tolerance):
                raise ValueError(
                    f"{field} mismatch in row {row_number}: expected {expected:.4f}, got {actual}"
                )


def validate_landing_rows(rows: list[dict[str, str]]) -> None:
    for row_number, row in enumerate(rows, start=2):
        sessions = int(row["sessions"])
        conversions = int(row["conversions"])
        bounce_rate = float(row["bounce_rate"])
        conversion_rate = float(row["conversion_rate"])
        if not 0 <= bounce_rate <= 1:
            raise ValueError(f"Bounce rate out of range in landing row {row_number}")
        if conversions > sessions:
            raise ValueError(f"Conversions exceed sessions in landing row {row_number}")
        if not close_enough(conversion_rate, conversions / sessions, 0.0002):
            raise ValueError(f"Conversion rate mismatch in landing row {row_number}")


def validate_ab_test_rows(rows: list[dict[str, str]]) -> None:
    variants = {row["variant"] for row in rows}
    if variants != {"A", "B"}:
        raise ValueError(f"A/B test must contain variants A and B, got {sorted(variants)}")
    for row_number, row in enumerate(rows, start=2):
        sessions = int(row["sessions"])
        conversions = int(row["conversions"])
        revenue = float(row["revenue_eur"])
        traffic_split = float(row["traffic_split"])
        if sessions <= 0:
            raise ValueError(f"Sessions must be positive in A/B row {row_number}")
        if conversions < 0 or conversions > sessions:
            raise ValueError(f"Invalid conversions in A/B row {row_number}")
        if revenue < 0:
            raise ValueError(f"Negative revenue in A/B row {row_number}")
        if not 0 < traffic_split < 1:
            raise ValueError(f"Traffic split out of range in A/B row {row_number}")


def validate_path_rows(rows: list[dict[str, str]]) -> None:
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        path_id = row["path_id"]
        if path_id in seen_ids:
            raise ValueError(f"Duplicate path_id in conversion-path row {row_number}")
        seen_ids.add(path_id)

        touchpoints = [c.strip() for c in row["path"].split(">")]
        if not all(touchpoints):
            raise ValueError(f"Empty touchpoint in conversion-path row {row_number}")

        journeys = int(row["journeys"])
        conversions = int(row["conversions"])
        revenue = float(row["revenue_eur"])
        if journeys <= 0:
            raise ValueError(f"Journeys must be positive in path row {row_number}")
        if conversions < 0 or conversions > journeys:
            raise ValueError(f"Invalid conversions in path row {row_number}")
        if revenue < 0:
            raise ValueError(f"Negative revenue in path row {row_number}")
        if conversions == 0 and revenue > 0:
            raise ValueError(f"Revenue without conversions in path row {row_number}")


def validate_crm_rows(rows: list[dict[str, str]]) -> None:
    for row_number, row in enumerate(rows, start=2):
        if not row["customer_id"]:
            raise ValueError(f"Missing customer_id in CRM row {row_number}")
        value = float(row["order_value_eur"])
        if value <= 0:
            raise ValueError(f"Non-positive order value in CRM row {row_number}")
        if row["order_date"] < row["signup_date"]:
            raise ValueError(f"Order before signup in CRM row {row_number}")
        if not row["signup_date"].startswith(row["cohort_month"]):
            raise ValueError(f"cohort_month does not match signup_date in CRM row {row_number}")


def main() -> None:
    campaign_rows = read_rows(CAMPAIGN_PATH)
    landing_rows = read_rows(LANDING_PATH)
    ab_test_rows = read_rows(AB_TEST_PATH)
    path_rows = read_rows(PATHS_PATH)
    crm_rows = read_rows(CRM_PATH)
    require_columns(campaign_rows, CAMPAIGN_COLUMNS, "campaign data")
    require_columns(landing_rows, LANDING_COLUMNS, "landing page data")
    require_columns(ab_test_rows, AB_TEST_COLUMNS, "A/B test data")
    require_columns(path_rows, PATHS_COLUMNS, "conversion-path data")
    require_columns(crm_rows, CRM_COLUMNS, "CRM order data")
    validate_campaign_rows(campaign_rows)
    validate_landing_rows(landing_rows)
    validate_ab_test_rows(ab_test_rows)
    validate_path_rows(path_rows)
    validate_crm_rows(crm_rows)
    print(
        f"Validated {len(campaign_rows)} campaign rows, {len(landing_rows)} landing page rows, "
        f"{len(ab_test_rows)} A/B test rows, {len(path_rows)} conversion-path rows "
        f"and {len(crm_rows)} CRM order rows."
    )


if __name__ == "__main__":
    main()
