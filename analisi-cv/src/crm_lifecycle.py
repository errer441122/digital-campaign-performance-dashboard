"""Customer lifecycle stages from purchase behaviour.

Runs on `data/online_retail_orders.csv` (Online Retail II, UCI, CC BY 4.0).
Recency and order count put every customer into one stage: New, Repeat,
At risk, Dormant or Churned. The same thresholds drive the win-back segment
in the klaviyo-lifecycle-lab repo.

Pure standard library.
"""

from __future__ import annotations

import json
from pathlib import Path

from crm_retention import read_orders, reference_date

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "crm_lifecycle.md"
METRICS_PATH = ANALYSIS_DIR / "crm_lifecycle_metrics.json"

LIFECYCLE_ORDER = ["New", "Repeat", "At risk", "Dormant", "Churned"]
STAGE_RULE = {
    "New": "last order within 90 days, 1 order",
    "Repeat": "last order within 90 days, 2+ orders",
    "At risk": "last order 91-180 days ago",
    "Dormant": "last order 181-365 days ago",
    "Churned": "last order more than 365 days ago",
}
STAGE_ACTION = {
    "New": "Onboarding / second-purchase nudge",
    "Repeat": "Loyalty / cross-sell flow",
    "At risk": "Win-back sequence",
    "Dormant": "Reactivation offer",
    "Churned": "Low-cost reactivation, then sunset",
}


def stage_for(recency_days: int, orders: int) -> str:
    if recency_days <= 90:
        return "Repeat" if orders >= 2 else "New"
    if recency_days <= 180:
        return "At risk"
    if recency_days <= 365:
        return "Dormant"
    return "Churned"


def lifecycle(orders: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    """Per-customer stage from purchase recency and frequency (UCI file by default)."""
    orders = orders if orders is not None else read_orders()
    as_of = reference_date(orders)
    agg: dict[str, dict[str, object]] = {}
    for o in orders:
        a = agg.setdefault(o["customer_id"], {"orders": 0, "last": o["order_date"], "monetary": 0.0})
        a["orders"] += 1
        a["monetary"] += o["order_value_gbp"]
        if o["order_date"] > a["last"]:
            a["last"] = o["order_date"]

    out: dict[str, dict[str, object]] = {}
    for cid, a in agg.items():
        recency = (as_of - a["last"]).days
        out[cid] = {
            "orders": a["orders"],
            "recency_days": recency,
            "monetary_gbp": round(a["monetary"], 2),
            "stage": stage_for(recency, a["orders"]),
        }
    return out


def run(orders: list[dict[str, object]] | None = None) -> dict[str, object]:
    customers = lifecycle(orders)
    total = len(customers)
    total_revenue = sum(c["monetary_gbp"] for c in customers.values())

    stages = []
    for stage in LIFECYCLE_ORDER:
        members = [c for c in customers.values() if c["stage"] == stage]
        if not members:
            continue
        revenue = sum(c["monetary_gbp"] for c in members)
        stages.append({
            "stage": stage,
            "rule": STAGE_RULE[stage],
            "customers": len(members),
            "share": round(len(members) / total, 4),
            "revenue_gbp": round(revenue, 2),
            "revenue_share": round(revenue / total_revenue, 4),
            "recommended_action": STAGE_ACTION[stage],
        })

    return {
        "dataset": "Online Retail II (UCI, CC BY 4.0)",
        "customers": total,
        "stages": stages,
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# Customer lifecycle stages\n")
    L.append(
        f"Purchase recency and order count for {r['customers']:,} customers in "
        f"*Online Retail II* (UCI, CC BY 4.0). Revenue is each stage's historical "
        f"spend, so it shows what is at stake, not a forecast.\n"
    )
    L.append("| Stage | Rule | Customers | Share | Historical revenue | Revenue share | Recommended action |")
    L.append("| --- | --- | ---: | ---: | ---: | ---: | --- |")
    for s in r["stages"]:
        L.append(
            f"| {s['stage']} | {s['rule']} | {s['customers']:,} | {s['share']:.0%} | "
            f"GBP {s['revenue_gbp']:,.0f} | {s['revenue_share']:.0%} | {s['recommended_action']} |"
        )
    L.append("")
    L.append(
        "The thresholds are a convention, not something this dataset proves. "
        "Relationships are observational, not causal.\n"
    )
    return "\n".join(L)


def main() -> None:
    result = run()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    REPORT_PATH.write_text(_md(result), encoding="utf-8", newline="\n")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)} and {METRICS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
