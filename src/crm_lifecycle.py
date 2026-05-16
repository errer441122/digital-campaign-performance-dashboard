"""Customer lifecycle + lead scoring + GDPR consent — **hybrid** analysis.

Two clearly separated layers:

A. **Customer lifecycle (REAL).** Derived purely from real purchase
   behaviour in `data/online_retail_orders.csv` (Online Retail II, UCI,
   CC BY 4.0): recency and frequency map every customer to New / Repeat /
   At risk / Dormant / Churned. No pre-purchase funnel stages
   (Subscriber/Lead/MQL/SQL) — those need marketing-engagement data the
   transactional dataset does not contain.

B. **Lead scoring & consent (SIMULATED, disclosed).** Online Retail II has
   no engagement signals and no consent status, and no permissive public
   dataset carries per-contact consent. So the lead score and the GDPR
   suppression gate run on the clearly-labelled synthetic overlay
   (`data/crm_engagement_overlay.csv`, keyed to the real customer IDs).
   Consent is a hard gate, never a score term.

Pure standard library.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from crm_retention import read_orders, reference_date

ROOT = Path(__file__).resolve().parents[1]
OVERLAY_PATH = ROOT / "data" / "crm_engagement_overlay.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "crm_lifecycle.md"
METRICS_PATH = ANALYSIS_DIR / "crm_lifecycle_metrics.json"

LIFECYCLE_ORDER = ["New", "Repeat", "At risk", "Dormant", "Churned"]
STAGE_ACTION = {
    "New": "Onboarding / second-purchase nudge",
    "Repeat": "Loyalty / cross-sell flow",
    "At risk": "Win-back sequence",
    "Dormant": "Reactivation offer",
    "Churned": "Low-cost reactivation, then sunset",
}


def real_lifecycle() -> dict[str, dict[str, object]]:
    """Per-customer lifecycle from REAL purchase recency/frequency."""
    orders = read_orders()
    as_of = reference_date(orders)
    agg: dict[str, dict[str, object]] = {}
    for o in orders:
        a = agg.setdefault(o["customer_id"], {"orders": 0, "last": o["order_date"], "monetary": 0.0})
        a["orders"] += 1
        a["monetary"] += o["order_value_eur"]
        if o["order_date"] > a["last"]:
            a["last"] = o["order_date"]

    out: dict[str, dict[str, object]] = {}
    for cid, a in agg.items():
        recency = (as_of - a["last"]).days
        if recency <= 90:
            stage = "Repeat" if a["orders"] >= 2 else "New"
        elif recency <= 180:
            stage = "At risk"
        elif recency <= 365:
            stage = "Dormant"
        else:
            stage = "Churned"
        out[cid] = {
            "orders": a["orders"],
            "recency_days": recency,
            "monetary_eur": round(a["monetary"], 2),
            "stage": stage,
        }
    return out


def read_overlay() -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    with OVERLAY_PATH.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[r["customer_id"]] = {
                "consent": r["consent_status"],
                "page_views": int(r["page_views"]),
                "key_page_views": int(r["key_page_views"]),
                "email_clicks": int(r["email_clicks"]),
                "form_submits": int(r["form_submits"]),
                "demo_request": int(r["demo_request"]),
                "webinar_signup": int(r["webinar_signup"]),
            }
    return out


def lead_score(e: dict[str, object]) -> dict[str, object]:
    """Transparent capped additive score (0-100) with a reason."""
    parts: list[tuple[str, int]] = []
    if e["demo_request"]:
        parts.append(("demo request", 25))
    if e["key_page_views"]:
        parts.append((f"{e['key_page_views']} key-page views", min(24, 6 * e["key_page_views"])))
    if e["form_submits"]:
        parts.append((f"{e['form_submits']} form submits", min(18, 9 * e["form_submits"])))
    if e["email_clicks"]:
        parts.append((f"{e['email_clicks']} email clicks", min(15, 3 * e["email_clicks"])))
    if e["webinar_signup"]:
        parts.append(("webinar signup", 8))
    if e["page_views"]:
        parts.append((f"{e['page_views']} page views", min(10, e["page_views"])))
    raw = sum(p[1] for p in parts)
    score = max(0, min(100, raw))
    pos = sorted(parts, key=lambda p: -p[1])[:3]
    return {"score": score, "reason": "; ".join(p[0] for p in pos) or "no engagement signals"}


def run() -> dict[str, object]:
    lifecycle = real_lifecycle()
    overlay = read_overlay()
    total = len(lifecycle)

    by_stage: dict[str, list[str]] = defaultdict(list)
    for cid, lc in lifecycle.items():
        by_stage[lc["stage"]].append(cid)

    enriched = {}
    for cid, lc in lifecycle.items():
        e = overlay.get(cid)
        sc = lead_score(e) if e else {"score": 0, "reason": "no overlay"}
        eligible = bool(e) and e["consent"] == "opted_in"
        enriched[cid] = {**lc, "score": sc["score"], "reason": sc["reason"],
                         "consent": e["consent"] if e else "unknown",
                         "campaign_eligible": eligible}

    funnel = []
    for stage in LIFECYCLE_ORDER:
        ids = by_stage.get(stage, [])
        n = len(ids)
        if n == 0:
            continue
        elig = sum(1 for c in ids if enriched[c]["campaign_eligible"])
        funnel.append({
            "stage": stage,
            "customers": n,
            "share": round(n / total, 4),
            "avg_lead_score": round(sum(enriched[c]["score"] for c in ids) / n, 1),
            "campaign_eligible": elig,
            "suppressed": n - elig,
            "recommended_action": STAGE_ACTION[stage],
        })

    supp: dict[str, int] = defaultdict(int)
    for c in enriched.values():
        if not c["campaign_eligible"]:
            supp[c["consent"]] += 1
    eligible_total = sum(1 for c in enriched.values() if c["campaign_eligible"])

    # Priority: real at-risk/dormant value customers who are reachable.
    reachable_value = sorted(
        [c for c in enriched.values()
         if c["campaign_eligible"] and c["stage"] in ("At risk", "Dormant")],
        key=lambda c: c["monetary_eur"], reverse=True,
    )[:10]
    top = [
        {"stage": c["stage"], "monetary_eur": c["monetary_eur"],
         "lead_score": c["score"], "why": c["reason"]}
        for c in reachable_value
    ]

    return {
        "real_dataset": "Online Retail II (UCI, CC BY 4.0)",
        "overlay": "SIMULATED engagement/consent (disclosed) keyed to real customer IDs",
        "customers": total,
        "lifecycle_funnel_real": funnel,
        "consent_overlay": {
            "eligible": eligible_total,
            "eligible_rate": round(eligible_total / total, 4),
            "suppressed": total - eligible_total,
            "suppressed_by_reason": dict(supp),
        },
        "priority_reachable_value_accounts": top,
        "scoring_model": {
            "demo_request": 25, "key_page_view": "6 each (cap 24)",
            "form_submit": "9 each (cap 18)", "email_click": "3 each (cap 15)",
            "webinar_signup": 8, "page_view": "1 each (cap 10)",
            "note": "Lifecycle is REAL (purchase-based); score/consent are a "
                    "disclosed synthetic overlay. Consent is a hard gate, "
                    "never a score term.",
        },
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# Customer Lifecycle, Lead Scoring & Consent (hybrid)\n")
    L.append(
        f"**Lifecycle is REAL** — derived from purchase behaviour of "
        f"{r['customers']:,} customers in *Online Retail II* (UCI, CC BY 4.0). "
        f"**Lead score and consent are a disclosed SIMULATED overlay** keyed "
        f"to the real customer IDs (no public dataset carries engagement or "
        f"consent — see `data/DATA_CARD.md` / `data/REAL_DATA_PROVENANCE.md`).\n"
    )

    L.append("## A. Customer lifecycle — REAL (purchase recency/frequency)\n")
    L.append("| Stage | Customers | Share | Avg lead score* | Reachable* | Suppressed* | Recommended action |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for f in r["lifecycle_funnel_real"]:
        L.append(
            f"| {f['stage']} | {f['customers']:,} | {f['share']:.0%} | "
            f"{f['avg_lead_score']:.0f} | {f['campaign_eligible']:,} | "
            f"{f['suppressed']:,} | {f['recommended_action']} |"
        )
    L.append("")
    L.append("_\\* lead score / reachable / suppressed come from the simulated overlay (Section B)._\n")

    co = r["consent_overlay"]
    L.append("## B. Lead scoring & GDPR consent — SIMULATED overlay (disclosed)\n")
    L.append(
        f"On the synthetic overlay, **{co['eligible']:,} of {r['customers']:,} "
        f"customers ({co['eligible_rate']:.0%}) are campaign-eligible** "
        f"(`opted_in`). {co['suppressed']:,} are suppressed: "
        + ", ".join(f"{v:,} {k}" for k, v in sorted(co["suppressed_by_reason"].items()))
        + ". A high lead score never overrides missing consent.\n"
    )

    L.append("## Priority: reachable high-value lapsing customers\n")
    L.append(
        "Real At-risk/Dormant customers ranked by **real** lifetime spend, "
        "filtered to consent-eligible (simulated) — the list a CRM team would "
        "action first.\n"
    )
    L.append("| Stage | Real spend | Lead score* | Why* |")
    L.append("| --- | ---: | ---: | --- |")
    for t in r["priority_reachable_value_accounts"]:
        L.append(
            f"| {t['stage']} | EUR {t['monetary_eur']:,.0f} | "
            f"{t['lead_score']} | {t['why']} |"
        )
    L.append("")

    L.append("## Boundary\n")
    L.append(
        "Hybrid by necessity: the lifecycle is real public transactional "
        "data (Online Retail II, UCI, CC BY 4.0); the engagement and consent "
        "columns are clearly-labelled simulated overlay because no permissive "
        "public dataset carries them. The simulated part is disclosed in "
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
