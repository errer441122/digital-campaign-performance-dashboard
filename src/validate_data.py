"""Validate the simulated digital campaign sample data."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
LANDING_PATH = ROOT / "data" / "landing_page_sample.csv"
AB_TEST_PATH = ROOT / "data" / "ab_test_conversion_sample.csv"
PATHS_PATH = ROOT / "data" / "conversion_paths_sample.csv"
REAL_ORDERS_PATH = ROOT / "data" / "online_retail_orders.csv"
OVERLAY_PATH = ROOT / "data" / "crm_engagement_overlay.csv"

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


REAL_ORDERS_COLUMNS = {
    "customer_id",
    "order_id",
    "order_date",
    "cohort_month",
    "signup_date",
    "country",
    "order_value_eur",
    "n_items",
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


def validate_real_orders_rows(rows: list[dict[str, str]]) -> None:
    """Real Online Retail II orders (prepared by prepare_real_data.py)."""
    for row_number, row in enumerate(rows, start=2):
        if not row["customer_id"]:
            raise ValueError(f"Missing customer_id in orders row {row_number}")
        if float(row["order_value_eur"]) <= 0:
            raise ValueError(f"Non-positive order value in orders row {row_number}")
        if int(row["n_items"]) <= 0:
            raise ValueError(f"Non-positive n_items in orders row {row_number}")
        if row["order_date"] < row["signup_date"]:
            raise ValueError(f"Order before signup in orders row {row_number}")
        if not row["signup_date"].startswith(row["cohort_month"]):
            raise ValueError(f"cohort_month != signup_date in orders row {row_number}")


OVERLAY_COLUMNS = {
    "customer_id",
    "consent_status",
    "consent_source",
    "page_views",
    "key_page_views",
    "email_clicks",
    "form_submits",
    "demo_request",
    "webinar_signup",
}
CONSENT_STATES = {"opted_in", "opted_out", "unknown"}


def validate_overlay_rows(rows: list[dict[str, str]]) -> None:
    """SIMULATED engagement/consent overlay keyed to real customer IDs."""
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        cid = row["customer_id"]
        if not cid:
            raise ValueError(f"Missing customer_id in overlay row {row_number}")
        if cid in seen:
            raise ValueError(f"Duplicate customer_id in overlay row {row_number}")
        seen.add(cid)
        if row["consent_status"] not in CONSENT_STATES:
            raise ValueError(f"Invalid consent_status in overlay row {row_number}")
        for field in ("demo_request", "webinar_signup"):
            if row[field] not in ("0", "1"):
                raise ValueError(f"{field} must be 0/1 in overlay row {row_number}")
        for field in ("page_views", "key_page_views", "email_clicks", "form_submits"):
            if int(row[field]) < 0:
                raise ValueError(f"Negative {field} in overlay row {row_number}")
        if int(row["key_page_views"]) > int(row["page_views"]):
            raise ValueError(f"key_page_views exceeds page_views in overlay row {row_number}")
        if row["consent_status"] == "unknown" and row["consent_source"] != "unknown":
            raise ValueError(f"unknown consent must have unknown source in overlay row {row_number}")


def main() -> None:
    campaign_rows = read_rows(CAMPAIGN_PATH)
    landing_rows = read_rows(LANDING_PATH)
    ab_test_rows = read_rows(AB_TEST_PATH)
    path_rows = read_rows(PATHS_PATH)
    real_orders = read_rows(REAL_ORDERS_PATH)
    overlay_rows = read_rows(OVERLAY_PATH)
    require_columns(campaign_rows, CAMPAIGN_COLUMNS, "campaign data")
    require_columns(landing_rows, LANDING_COLUMNS, "landing page data")
    require_columns(ab_test_rows, AB_TEST_COLUMNS, "A/B test data")
    require_columns(path_rows, PATHS_COLUMNS, "conversion-path data")
    require_columns(real_orders, REAL_ORDERS_COLUMNS, "real Online Retail II orders")
    require_columns(overlay_rows, OVERLAY_COLUMNS, "engagement/consent overlay")
    validate_campaign_rows(campaign_rows)
    validate_landing_rows(landing_rows)
    validate_ab_test_rows(ab_test_rows)
    validate_path_rows(path_rows)
    validate_real_orders_rows(real_orders)
    validate_overlay_rows(overlay_rows)
    # The overlay must key onto the real customers, not invent IDs.
    real_ids = {r["customer_id"] for r in real_orders}
    overlay_ids = {r["customer_id"] for r in overlay_rows}
    if overlay_ids - real_ids:
        raise ValueError("Overlay contains customer_ids absent from the real orders")
    print(
        f"Validated {len(campaign_rows)} campaign rows, {len(landing_rows)} landing rows, "
        f"{len(ab_test_rows)} A/B rows, {len(path_rows)} conversion-path rows, "
        f"{len(real_orders)} REAL order rows and {len(overlay_rows)} overlay rows."
    )


if __name__ == "__main__":
    main()
