"""Validate the prepared Online Retail II orders before any analysis runs."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "data" / "online_retail_orders.csv"

ORDERS_COLUMNS = {
    "customer_id",
    "order_id",
    "order_date",
    "cohort_month",
    "signup_date",
    "country",
    "order_value_gbp",
    "n_items",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_orders(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("orders file has no rows")
    missing = ORDERS_COLUMNS - set(rows[0])
    if missing:
        raise ValueError(f"orders file is missing columns: {sorted(missing)}")
    for row_number, row in enumerate(rows, start=2):
        if not row["customer_id"]:
            raise ValueError(f"Missing customer_id in orders row {row_number}")
        if float(row["order_value_gbp"]) <= 0:
            raise ValueError(f"Non-positive order value in orders row {row_number}")
        if int(row["n_items"]) <= 0:
            raise ValueError(f"Non-positive n_items in orders row {row_number}")
        if row["order_date"] < row["signup_date"]:
            raise ValueError(f"Order before signup in orders row {row_number}")
        if not row["signup_date"].startswith(row["cohort_month"]):
            raise ValueError(f"cohort_month != signup_date in orders row {row_number}")


def main() -> None:
    rows = read_rows(ORDERS_PATH)
    validate_orders(rows)
    print(f"Validated {len(rows)} order rows.")


if __name__ == "__main__":
    main()
