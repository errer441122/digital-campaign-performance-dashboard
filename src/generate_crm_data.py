"""Deterministic generator for the simulated CRM order sample.

Customer-level orders used by `crm_retention.py` for RFM segmentation,
cohort retention and historical CLV. The interesting structure — deliberate
and disclosed — is that acquisition channel drives retention and lifetime
value: Email and Organic acquire customers who repeat; Display and Paid
Social acquire cheaper but thinner customers. That is the bridge between
the media analysis and the CRM analysis: a channel can win on last-click
CPA and still lose on lifetime value.

Single fixed seed; byte-stable output. Pure standard library.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "data" / "crm_orders_sample.csv"

SEED = 20260516
COHORT_MONTHS = ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
ANALYSIS_DATE = date(2026, 5, 31)

# Per-channel customer quality: how many customers acquired, repeat
# propensity, average order value and a monthly retention hazard. Email and
# Organic acquire fewer but stickier, higher-value customers.
CHANNELS = {
    "Email": {"customers": 150, "repeat_p": 0.62, "aov": 86.0, "retention": 0.80},
    "Organic Search": {"customers": 170, "repeat_p": 0.55, "aov": 82.0, "retention": 0.74},
    "Paid Search": {"customers": 210, "repeat_p": 0.42, "aov": 78.0, "retention": 0.62},
    "Direct": {"customers": 90, "repeat_p": 0.50, "aov": 84.0, "retention": 0.70},
    "Paid Social": {"customers": 180, "repeat_p": 0.30, "aov": 64.0, "retention": 0.48},
    "Display": {"customers": 130, "repeat_p": 0.24, "aov": 58.0, "retention": 0.40},
}


def _signup_date(rng: random.Random, cohort: str) -> date:
    year, month = (int(p) for p in cohort.split("-"))
    return date(year, month, rng.randint(1, 28))


def build_orders() -> list[dict[str, object]]:
    rng = random.Random(SEED)
    rows: list[dict[str, object]] = []
    customer_seq = 0

    for channel, cfg in CHANNELS.items():
        for _ in range(cfg["customers"]):
            customer_seq += 1
            customer_id = f"C{customer_seq:05d}"
            cohort = rng.choice(COHORT_MONTHS)
            signup = _signup_date(rng, cohort)

            # First order at signup.
            order_date = signup
            order_no = 1
            while True:
                aov = max(5.0, rng.gauss(cfg["aov"], cfg["aov"] * 0.28))
                rows.append(
                    {
                        "customer_id": customer_id,
                        "acquisition_channel": channel,
                        "cohort_month": cohort,
                        "signup_date": signup.isoformat(),
                        "order_id": f"{customer_id}-{order_no}",
                        "order_date": order_date.isoformat(),
                        "order_value_eur": round(aov, 2),
                    }
                )
                # Repeat? propensity decays with each additional order
                # (retention hazard) and is bounded by the analysis window.
                p_next = cfg["repeat_p"] * (cfg["retention"] ** (order_no - 1))
                if rng.random() > p_next:
                    break
                gap_days = int(rng.gauss(34, 12))
                gap_days = max(7, gap_days)
                order_date = order_date + timedelta(days=gap_days)
                if order_date > ANALYSIS_DATE:
                    break
                order_no += 1

    rows.sort(key=lambda r: (r["customer_id"], r["order_date"]))
    return rows


def main() -> None:
    rows = build_orders()
    ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with ORDERS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    customers = len({r["customer_id"] for r in rows})
    print(f"Wrote {len(rows)} orders for {customers} customers (seed={SEED}).")


if __name__ == "__main__":
    main()
