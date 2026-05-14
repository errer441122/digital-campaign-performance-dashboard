"""Validate the simulated digital campaign sample data."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
LANDING_PATH = ROOT / "data" / "landing_page_sample.csv"

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


def main() -> None:
    campaign_rows = read_rows(CAMPAIGN_PATH)
    landing_rows = read_rows(LANDING_PATH)
    require_columns(campaign_rows, CAMPAIGN_COLUMNS, "campaign data")
    require_columns(landing_rows, LANDING_COLUMNS, "landing page data")
    validate_campaign_rows(campaign_rows)
    validate_landing_rows(landing_rows)
    print(f"Validated {len(campaign_rows)} campaign rows and {len(landing_rows)} landing page rows.")


if __name__ == "__main__":
    main()
