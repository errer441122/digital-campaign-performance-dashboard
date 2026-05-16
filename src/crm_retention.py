"""CRM & retention analysis on the simulated order sample.

Four standard lifecycle artefacts a CRM / e-commerce / customer-insights
team actually ships:

1. **RFM segmentation** — quintile Recency/Frequency/Monetary scores mapped
   to named lifecycle segments.
2. **Cohort retention** — monthly repeat-purchase retention by signup
   cohort and by acquisition channel.
3. **Historical CLV by acquisition channel** — revenue per acquired
   customer, which reveals that the cheapest last-click channels are not
   the most valuable over a lifetime (the bridge to the media analysis).
4. **Lifecycle → automation map** — the trigger and flow each RFM segment
   should enter (welcome, cross-sell, win-back, sunset).

Pure standard library.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "data" / "crm_orders_sample.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "crm_retention.md"
METRICS_PATH = ANALYSIS_DIR / "crm_retention_metrics.json"

ANALYSIS_DATE = date(2026, 5, 31)


def _d(s: str) -> date:
    y, m, day = (int(p) for p in s.split("-"))
    return date(y, m, day)


def _month_index(cohort: str, order_date: date) -> int:
    cy, cm = (int(p) for p in cohort.split("-"))
    return (order_date.year - cy) * 12 + (order_date.month - cm)


def read_orders() -> list[dict[str, object]]:
    with ORDERS_PATH.open(newline="", encoding="utf-8") as handle:
        rows = []
        for r in csv.DictReader(handle):
            rows.append(
                {
                    "customer_id": r["customer_id"],
                    "acquisition_channel": r["acquisition_channel"],
                    "cohort_month": r["cohort_month"],
                    "signup_date": _d(r["signup_date"]),
                    "order_date": _d(r["order_date"]),
                    "order_value_eur": float(r["order_value_eur"]),
                }
            )
        return rows


def _quintile_scores(values: dict[str, float], reverse: bool) -> dict[str, int]:
    """Rank-based 1..5 score. reverse=True means lower raw value scores higher
    (used for recency: more recent = better)."""
    ordered = sorted(values.items(), key=lambda kv: kv[1], reverse=not reverse)
    n = len(ordered)
    scores: dict[str, int] = {}
    for i, (key, _v) in enumerate(ordered):
        scores[key] = 5 - min(4, int(i * 5 / n))
    return scores


def _segment(r: int, fm: int) -> str:
    if r >= 4 and fm >= 4:
        return "Champions"
    if r >= 3 and fm >= 3:
        return "Loyal customers"
    if r >= 4 and fm <= 2:
        return "New / promising"
    if r == 3 and fm <= 3:
        return "Needs attention"
    if r == 2:
        return "At risk"
    if r <= 1 and fm >= 4:
        return "Can't lose them"
    return "Hibernating"


AUTOMATION = {
    "Champions": ("VIP & referral flow", "RFM in top quintiles"),
    "Loyal customers": ("Cross-sell & loyalty tier", "≥2 orders, recent"),
    "New / promising": ("Welcome / onboarding series", "First order < 30 days"),
    "Needs attention": ("Targeted reactivation offer", "Recency slipping"),
    "At risk": ("Win-back sequence", "No order 45–90 days"),
    "Can't lose them": ("High-touch reactivation", "High value, lapsed"),
    "Hibernating": ("Low-cost reactivation then sunset", "No order > 90 days"),
}


def rfm(orders: list[dict[str, object]]) -> dict[str, object]:
    by_customer: dict[str, dict[str, object]] = {}
    for o in orders:
        c = by_customer.setdefault(
            o["customer_id"],
            {
                "channel": o["acquisition_channel"],
                "orders": 0,
                "monetary": 0.0,
                "last": o["order_date"],
            },
        )
        c["orders"] += 1
        c["monetary"] += o["order_value_eur"]
        if o["order_date"] > c["last"]:
            c["last"] = o["order_date"]

    recency = {c: (ANALYSIS_DATE - v["last"]).days for c, v in by_customer.items()}
    frequency = {c: float(v["orders"]) for c, v in by_customer.items()}
    monetary = {c: v["monetary"] for c, v in by_customer.items()}

    r_score = _quintile_scores(recency, reverse=True)
    f_score = _quintile_scores(frequency, reverse=False)
    m_score = _quintile_scores(monetary, reverse=False)

    seg_counts: dict[str, int] = defaultdict(int)
    seg_revenue: dict[str, float] = defaultdict(float)
    for c, v in by_customer.items():
        fm = round((f_score[c] + m_score[c]) / 2)
        seg = _segment(r_score[c], fm)
        v["segment"] = seg
        seg_counts[seg] += 1
        seg_revenue[seg] += v["monetary"]

    total = len(by_customer)
    segments = [
        {
            "segment": seg,
            "customers": seg_counts[seg],
            "customer_share": round(seg_counts[seg] / total, 4),
            "revenue_eur": round(seg_revenue[seg], 2),
            "automation_flow": AUTOMATION[seg][0],
            "trigger": AUTOMATION[seg][1],
        }
        for seg in sorted(seg_counts, key=lambda s: seg_revenue[s], reverse=True)
    ]
    return {"total_customers": total, "segments": segments, "_by_customer": by_customer}


def cohort_retention(orders: list[dict[str, object]]) -> dict[str, object]:
    cohort_customers: dict[str, set[str]] = defaultdict(set)
    active: dict[tuple[str, int], set[str]] = defaultdict(set)
    max_offset = 5
    for o in orders:
        cohort = o["cohort_month"]
        cohort_customers[cohort].add(o["customer_id"])
        offset = _month_index(cohort, o["order_date"])
        if 0 <= offset <= max_offset:
            active[(cohort, offset)].add(o["customer_id"])

    table = []
    for cohort in sorted(cohort_customers):
        base = len(cohort_customers[cohort])
        row = {"cohort_month": cohort, "customers": base, "retention": []}
        for k in range(max_offset + 1):
            row["retention"].append(
                round(len(active[(cohort, k)]) / base, 4) if base else 0.0
            )
        table.append(row)
    return {"max_offset": max_offset, "cohorts": table}


def clv_by_channel(rfm_result: dict[str, object]) -> list[dict[str, object]]:
    by_customer = rfm_result["_by_customer"]
    agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"customers": 0, "orders": 0.0, "revenue": 0.0}
    )
    for v in by_customer.values():
        a = agg[v["channel"]]
        a["customers"] += 1
        a["orders"] += v["orders"]
        a["revenue"] += v["monetary"]

    out = []
    for ch, a in agg.items():
        n = a["customers"]
        out.append(
            {
                "acquisition_channel": ch,
                "customers": int(n),
                "orders_per_customer": round(a["orders"] / n, 2),
                "avg_order_value_eur": round(a["revenue"] / a["orders"], 2),
                "historical_clv_eur": round(a["revenue"] / n, 2),
            }
        )
    return sorted(out, key=lambda r: r["historical_clv_eur"], reverse=True)


def run() -> dict[str, object]:
    orders = read_orders()
    rfm_result = rfm(orders)
    clv = clv_by_channel(rfm_result)
    cohorts = cohort_retention(orders)
    rfm_public = {k: v for k, v in rfm_result.items() if k != "_by_customer"}
    return {
        "orders": len(orders),
        "rfm": rfm_public,
        "cohort_retention": cohorts,
        "clv_by_channel": clv,
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# CRM & Retention\n")
    L.append(
        f"{r['orders']:,} simulated orders, "
        f"{r['rfm']['total_customers']:,} customers, six monthly cohorts.\n"
    )

    L.append("## RFM lifecycle segments → automation\n")
    L.append("| Segment | Customers | Share | Revenue | Automation flow | Trigger |")
    L.append("| --- | ---: | ---: | ---: | --- | --- |")
    for s in r["rfm"]["segments"]:
        L.append(
            f"| {s['segment']} | {s['customers']:,} | {s['customer_share']:.0%} | "
            f"EUR {s['revenue_eur']:,.0f} | {s['automation_flow']} | {s['trigger']} |"
        )
    L.append("")

    L.append("## Cohort retention (repeat-purchase, by signup month)\n")
    head = " | ".join(f"M{k}" for k in range(r["cohort_retention"]["max_offset"] + 1))
    L.append(f"| Cohort | Customers | {head} |")
    L.append("| --- | ---: | " + " | ".join(["---:"] * (r["cohort_retention"]["max_offset"] + 1)) + " |")
    for c in r["cohort_retention"]["cohorts"]:
        cells = " | ".join(f"{x:.0%}" for x in c["retention"])
        L.append(f"| {c['cohort_month']} | {c['customers']:,} | {cells} |")
    L.append("")
    L.append(
        "M0 is the acquisition month (100% by construction); later columns "
        "are the share of the cohort that purchased again in that month.\n"
    )

    L.append("## Historical CLV by acquisition channel\n")
    L.append("| Channel | Customers | Orders/customer | AOV | Historical CLV |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for c in r["clv_by_channel"]:
        L.append(
            f"| {c['acquisition_channel']} | {c['customers']:,} | "
            f"{c['orders_per_customer']:.2f} | EUR {c['avg_order_value_eur']:.2f} | "
            f"EUR {c['historical_clv_eur']:.2f} |"
        )
    L.append("")
    best = r["clv_by_channel"][0]["acquisition_channel"]
    worst = r["clv_by_channel"][-1]["acquisition_channel"]
    L.append(
        f"**{best}** acquires the highest-lifetime-value customers and "
        f"**{worst}** the lowest. A channel can win on last-click CPA and "
        f"still lose on lifetime value — acquisition budget and CRM "
        f"treatment should be set on CLV, not first-order economics alone "
        f"(see `analysis/budget_reallocation.md`).\n"
    )

    L.append("## Boundary\n")
    L.append(
        "Simulated portfolio data only; no real CRM, e-commerce or "
        "customer data. Channel→retention structure is disclosed in "
        "`data/DATA_CARD.md`; relationships are observational, not causal.\n"
    )
    return "\n".join(L)


def main() -> None:
    result = run()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(_md(result), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)} and {METRICS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
