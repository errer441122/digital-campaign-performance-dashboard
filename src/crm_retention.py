"""CRM & retention analysis on the **real** Online Retail II dataset.

Runs on `data/online_retail_orders.csv`, prepared by `prepare_real_data.py`
from the UCI *Online Retail II* dataset (CC BY 4.0) — real UK online-retail
transactions, Dec 2009 - Dec 2011. See `data/REAL_DATA_PROVENANCE.md`.

Four standard lifecycle artefacts a CRM / e-commerce / customer-insights
team ships:

1. **RFM segmentation** — quintile Recency/Frequency/Monetary scores mapped
   to named lifecycle segments.
2. **Cohort retention** — monthly repeat-purchase retention by signup month.
3. **Historical CLV by country** — revenue per acquired customer (Online
   Retail II has no media/channel field, so the real breakdown is by
   country; the channel/CPA-vs-LTV bridge lives on the clearly-labelled
   simulated side).
4. **Lifecycle → automation map** — the flow each RFM segment should enter.

The reference date for recency is the dataset's last order date + 1 day
(standard RFM convention), not a hard-coded constant. Pure standard library.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "data" / "online_retail_orders.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "crm_retention.md"
METRICS_PATH = ANALYSIS_DIR / "crm_retention_metrics.json"

# Countries with fewer customers than this are not ranked on their own (the
# CLV estimate would be too noisy); they are pooled and reported separately.
MIN_CUSTOMERS_FOR_CLV = 30
COHORT_MAX_OFFSET = 6


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
                    "country": r["country"],
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
    "New / promising": ("Welcome / onboarding series", "Recent first order, low freq/value"),
    "Needs attention": ("Targeted reactivation offer", "Recency slipping"),
    "At risk": ("Win-back sequence", "Recency in 2nd quintile"),
    "Can't lose them": ("High-touch reactivation", "High value, lapsed"),
    "Hibernating": ("Low-cost reactivation then sunset", "Low recency and value"),
}


def reference_date(orders: list[dict[str, object]]) -> date:
    """Standard RFM convention: last observed order date + 1 day."""
    return max(o["order_date"] for o in orders) + timedelta(days=1)


def rfm(orders: list[dict[str, object]], as_of: date) -> dict[str, object]:
    by_customer: dict[str, dict[str, object]] = {}
    for o in orders:
        c = by_customer.setdefault(
            o["customer_id"],
            {
                "country": o["country"],
                "orders": 0,
                "monetary": 0.0,
                "last": o["order_date"],
            },
        )
        c["orders"] += 1
        c["monetary"] += o["order_value_eur"]
        if o["order_date"] > c["last"]:
            c["last"] = o["order_date"]

    recency = {c: (as_of - v["last"]).days for c, v in by_customer.items()}
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
    for o in orders:
        cohort = o["cohort_month"]
        cohort_customers[cohort].add(o["customer_id"])
        offset = _month_index(cohort, o["order_date"])
        if 0 <= offset <= COHORT_MAX_OFFSET:
            active[(cohort, offset)].add(o["customer_id"])

    table = []
    for cohort in sorted(cohort_customers):
        base = len(cohort_customers[cohort])
        row = {"cohort_month": cohort, "customers": base, "retention": []}
        for k in range(COHORT_MAX_OFFSET + 1):
            row["retention"].append(
                round(len(active[(cohort, k)]) / base, 4) if base else 0.0
            )
        table.append(row)
    return {"max_offset": COHORT_MAX_OFFSET, "cohorts": table}


def clv_by_country(rfm_result: dict[str, object]) -> dict[str, object]:
    by_customer = rfm_result["_by_customer"]
    agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"customers": 0, "orders": 0.0, "revenue": 0.0}
    )
    for v in by_customer.values():
        a = agg[v["country"]]
        a["customers"] += 1
        a["orders"] += v["orders"]
        a["revenue"] += v["monetary"]

    ranked, pooled = [], {"countries": 0, "customers": 0, "revenue": 0.0}
    for country, a in agg.items():
        n = int(a["customers"])
        row = {
            "country": country,
            "customers": n,
            "orders_per_customer": round(a["orders"] / n, 2),
            "avg_order_value_eur": round(a["revenue"] / a["orders"], 2),
            "historical_clv_eur": round(a["revenue"] / n, 2),
        }
        if n >= MIN_CUSTOMERS_FOR_CLV:
            ranked.append(row)
        else:
            pooled["countries"] += 1
            pooled["customers"] += n
            pooled["revenue"] += a["revenue"]
    ranked.sort(key=lambda r: r["historical_clv_eur"], reverse=True)
    pooled["revenue"] = round(pooled["revenue"], 2)
    return {"ranked": ranked, "small_n_pooled": pooled, "min_customers": MIN_CUSTOMERS_FOR_CLV}


def run() -> dict[str, object]:
    orders = read_orders()
    as_of = reference_date(orders)
    rfm_result = rfm(orders, as_of)
    clv = clv_by_country(rfm_result)
    cohorts = cohort_retention(orders)
    rfm_public = {k: v for k, v in rfm_result.items() if k != "_by_customer"}
    return {
        "dataset": "Online Retail II (UCI, CC BY 4.0) — real",
        "orders": len(orders),
        "reference_date": as_of.isoformat(),
        "rfm": rfm_public,
        "cohort_retention": cohorts,
        "clv_by_country": clv,
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# CRM & Retention (real data)\n")
    L.append(
        f"**{r['orders']:,} real orders** from "
        f"{r['rfm']['total_customers']:,} customers — *Online Retail II* "
        f"(UCI, CC BY 4.0), see `data/REAL_DATA_PROVENANCE.md`. Recency "
        f"reference date: {r['reference_date']} (last order + 1 day).\n"
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
        "are the share of the cohort that placed another order in that month "
        "offset. Late cohorts are right-censored (fewer observable months).\n"
    )

    clv = r["clv_by_country"]
    L.append("## Historical CLV by country\n")
    L.append(
        f"Online Retail II has no media/channel field, so lifetime value is "
        f"broken down by **country**. Only countries with ≥ "
        f"{clv['min_customers']} customers are ranked (smaller ones are too "
        f"noisy to compare).\n"
    )
    L.append("| Country | Customers | Orders/customer | AOV | Historical CLV |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for c in clv["ranked"]:
        L.append(
            f"| {c['country']} | {c['customers']:,} | "
            f"{c['orders_per_customer']:.2f} | EUR {c['avg_order_value_eur']:.2f} | "
            f"EUR {c['historical_clv_eur']:.2f} |"
        )
    L.append("")
    p = clv["small_n_pooled"]
    L.append(
        f"_{p['countries']} smaller countries ({p['customers']:,} customers, "
        f"EUR {p['revenue']:,.0f} revenue) are pooled and not ranked._\n"
    )
    if clv["ranked"]:
        best, worst = clv["ranked"][0], clv["ranked"][-1]
        L.append(
            f"Among comparable markets, **{best['country']}** shows the "
            f"highest historical CLV (EUR {best['historical_clv_eur']:,.0f}) "
            f"and **{worst['country']}** the lowest "
            f"(EUR {worst['historical_clv_eur']:,.0f}). Acquisition and CRM "
            f"treatment should weigh realised lifetime value by market, not "
            f"first-order value alone.\n"
        )

    L.append("## Boundary\n")
    L.append(
        "Real public transactional data (Online Retail II, UCI, CC BY 4.0) — "
        "no synthetic values in this analysis. Provenance and cleaning rules: "
        "`data/REAL_DATA_PROVENANCE.md`. Relationships are observational, not "
        "causal; the data is one UK retailer 2009-2011 and does not "
        "generalise to other businesses.\n"
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
