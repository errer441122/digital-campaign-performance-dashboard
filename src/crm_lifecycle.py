"""CRM lifecycle, lead scoring and consent-aware suppression.

Three things a CRM / Marketing Automation team actually ships:

1. **Lifecycle-stage engine** — rule-based assignment of every contact to
   Subscriber / Lead / MQL / SQL (non-buyers) or Customer / Churn Risk /
   Reactivation (buyers). (No "Opportunity" stage: it needs open-deal CRM
   data this simulation does not contain — modelled stages only.)
2. **Lead scoring** — a transparent 0-100 additive model with capped
   per-signal contributions and a human-readable reason per contact.
3. **Consent / GDPR suppression** — a hard gate, *separate from the score*:
   only `opted_in` contacts are campaign-eligible; `opted_out` / `unknown`
   are suppressed with a stated reason. Score never "buys back" consent.

Pure standard library; consumes `data/crm_contacts_sample.csv`.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTACTS_PATH = ROOT / "data" / "crm_contacts_sample.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "crm_lifecycle.md"
METRICS_PATH = ANALYSIS_DIR / "crm_lifecycle_metrics.json"

MQL_THRESHOLD = 30  # marketing-qualified: engaged but not yet sales-ready
CHANNEL_QUALITY = {
    "Email": 6, "Organic Search": 6, "Direct": 4,
    "Paid Search": 3, "Paid Social": 1, "Display": 0,
}
STAGE_ACTION = {
    "Customer": "Loyalty / cross-sell flow",
    "Churn Risk": "Win-back sequence",
    "Reactivation": "Low-cost reactivation, then sunset",
    "SQL": "Sales handoff (create sales task)",
    "MQL": "Nurturing campaign",
    "Lead": "Educational nurture",
    "Subscriber": "Welcome journey",
}
STAGE_ORDER = ["Subscriber", "Lead", "MQL", "SQL", "Customer", "Churn Risk", "Reactivation"]


def read_contacts() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    with CONTACTS_PATH.open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            out.append(
                {
                    "contact_id": r["contact_id"],
                    "channel": r["acquisition_channel"],
                    "has_purchase": int(r["has_purchase"]),
                    "days_idle": int(r["days_since_last_activity"]),
                    "consent": r["consent_status"],
                    "page_views": int(r["page_views"]),
                    "key_page_views": int(r["key_page_views"]),
                    "email_clicks": int(r["email_clicks"]),
                    "form_submits": int(r["form_submits"]),
                    "demo_request": int(r["demo_request"]),
                    "webinar_signup": int(r["webinar_signup"]),
                }
            )
    return out


def lead_score(c: dict[str, object]) -> dict[str, object]:
    """Transparent additive score with capped contributions and a reason."""
    parts: list[tuple[str, int]] = []
    if c["demo_request"]:
        parts.append(("demo request", 25))
    if c["key_page_views"]:
        parts.append((f"{c['key_page_views']} key-page views", min(24, 6 * c["key_page_views"])))
    if c["form_submits"]:
        parts.append((f"{c['form_submits']} form submits", min(18, 9 * c["form_submits"])))
    if c["email_clicks"]:
        parts.append((f"{c['email_clicks']} email clicks", min(15, 3 * c["email_clicks"])))
    if c["webinar_signup"]:
        parts.append(("webinar signup", 8))
    cq = CHANNEL_QUALITY.get(c["channel"], 0)
    if cq:
        parts.append((f"channel {c['channel']}", cq))

    d = c["days_idle"]
    if d <= 30:
        parts.append(("active in last 30d", 12))
    elif d <= 90:
        parts.append(("active in last 90d", 5))
    elif d > 180:
        parts.append((f"inactive {d}d", -12))

    raw = sum(p[1] for p in parts)
    score = max(0, min(100, raw))
    pos = sorted([p for p in parts if p[1] > 0], key=lambda p: -p[1])[:3]
    neg = [p for p in parts if p[1] < 0]
    reason = "; ".join(p[0] for p in pos + neg) or "no engagement signals"
    return {"score": score, "reason": reason}


def lifecycle_stage(c: dict[str, object], score: int) -> str:
    if c["has_purchase"]:
        if c["days_idle"] <= 90:
            return "Customer"
        if c["days_idle"] <= 180:
            return "Churn Risk"
        return "Reactivation"
    # SQL is genuinely sales-ready (narrow); MQL is the broader marketing-
    # qualified pool, so a realistic funnel has MQL >> SQL.
    if c["demo_request"] or (c["key_page_views"] >= 3 and c["form_submits"] >= 1):
        return "SQL"
    if score >= MQL_THRESHOLD:
        return "MQL"
    if c["form_submits"] >= 1 or c["page_views"] >= 4 or c["email_clicks"] >= 2:
        return "Lead"
    return "Subscriber"


def run() -> dict[str, object]:
    contacts = read_contacts()
    enriched = []
    for c in contacts:
        sc = lead_score(c)
        stage = lifecycle_stage(c, sc["score"])
        eligible = c["consent"] == "opted_in"
        enriched.append({**c, **sc, "stage": stage, "campaign_eligible": eligible})

    total = len(enriched)
    by_stage: dict[str, list[dict[str, object]]] = defaultdict(list)
    for e in enriched:
        by_stage[e["stage"]].append(e)

    funnel = []
    for stage in STAGE_ORDER:
        rows = by_stage.get(stage, [])
        n = len(rows)
        if n == 0:
            continue
        elig = sum(1 for r in rows if r["campaign_eligible"])
        funnel.append({
            "stage": stage,
            "contacts": n,
            "share": round(n / total, 4),
            "avg_lead_score": round(sum(r["score"] for r in rows) / n, 1),
            "campaign_eligible": elig,
            "suppressed": n - elig,
            "recommended_action": STAGE_ACTION[stage],
        })

    supp_reason: dict[str, int] = defaultdict(int)
    for e in enriched:
        if not e["campaign_eligible"]:
            supp_reason[e["consent"]] += 1
    eligible_total = sum(1 for e in enriched if e["campaign_eligible"])

    top = sorted(
        [e for e in enriched if e["campaign_eligible"]],
        key=lambda e: e["score"], reverse=True,
    )[:10]
    top_sample = [
        {"contact_id": e["contact_id"], "channel": e["channel"], "stage": e["stage"],
         "lead_score": e["score"], "reason": e["reason"]}
        for e in top
    ]

    mql_sql = sum(len(by_stage.get(s, [])) for s in ("MQL", "SQL"))
    sales_ready_eligible = sum(
        1 for e in enriched if e["stage"] in ("MQL", "SQL") and e["campaign_eligible"]
    )

    return {
        "contacts": total,
        "lifecycle_funnel": funnel,
        "consent": {
            "eligible": eligible_total,
            "eligible_rate": round(eligible_total / total, 4),
            "suppressed": total - eligible_total,
            "suppressed_by_reason": dict(supp_reason),
        },
        "sales_ready": {
            "mql_plus_sql": mql_sql,
            "eligible_to_action": sales_ready_eligible,
        },
        "top_eligible_contacts": top_sample,
        "scoring_model": {
            "demo_request": 25, "key_page_view": "6 each (cap 24)",
            "form_submit": "9 each (cap 18)", "email_click": "3 each (cap 15)",
            "webinar_signup": 8, "channel_quality": CHANNEL_QUALITY,
            "recency": "<=30d +12, <=90d +5, >180d -12",
            "mql_threshold": MQL_THRESHOLD,
            "note": "Consent is a separate hard gate, not a score term.",
        },
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# CRM Lifecycle, Lead Scoring & Consent\n")
    L.append(
        f"{r['contacts']:,} simulated contacts assigned to lifecycle stages by "
        f"rule, scored 0-100, and gated by consent. Lead score and consent are "
        f"independent: a high score never overrides a missing opt-in.\n"
    )

    L.append("## Lifecycle funnel\n")
    L.append("| Stage | Contacts | Share | Avg lead score | Campaign-eligible | Suppressed | Recommended action |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for f in r["lifecycle_funnel"]:
        L.append(
            f"| {f['stage']} | {f['contacts']:,} | {f['share']:.0%} | "
            f"{f['avg_lead_score']:.0f} | {f['campaign_eligible']:,} | "
            f"{f['suppressed']:,} | {f['recommended_action']} |"
        )
    L.append("")

    co = r["consent"]
    by = co["suppressed_by_reason"]
    L.append("## Consent / GDPR suppression\n")
    L.append(
        f"**{co['eligible']:,} of {r['contacts']:,} contacts "
        f"({co['eligible_rate']:.0%}) are campaign-eligible** (`opted_in`). "
        f"{co['suppressed']:,} are suppressed: "
        + ", ".join(f"{v:,} {k}" for k, v in sorted(by.items()))
        + ". Suppressed contacts are excluded from every email/automation "
        f"action regardless of lead score.\n"
    )

    sr = r["sales_ready"]
    L.append("## Sales-ready pipeline\n")
    L.append(
        f"{sr['mql_plus_sql']:,} contacts are MQL or SQL; "
        f"**{sr['eligible_to_action']:,}** of them are consent-eligible and can "
        f"be actioned now (nurture or sales handoff). The rest are real demand "
        f"that is legally unreachable until consent is captured — a data-"
        f"collection problem, not a targeting one.\n"
    )

    L.append("## Top consent-eligible contacts by lead score\n")
    L.append("| Contact | Channel | Stage | Score | Why |")
    L.append("| --- | --- | --- | ---: | --- |")
    for t in r["top_eligible_contacts"]:
        L.append(
            f"| {t['contact_id']} | {t['channel']} | {t['stage']} | "
            f"{t['lead_score']} | {t['reason']} |"
        )
    L.append("")

    L.append("## Executive summary\n")
    L.append(
        f"Of {r['contacts']:,} contacts, {co['eligible_rate']:.0%} are legally "
        f"reachable. The actionable priority is the {sr['eligible_to_action']:,} "
        f"consent-eligible MQL/SQL contacts (sales handoff + nurture); Churn "
        f"Risk and Reactivation buyers need retention flows; the largest "
        f"lever on reachable volume is improving opt-in capture on the "
        f"weak-consent acquisition channels, not buying more traffic.\n"
    )
    L.append("## Boundary\n")
    L.append(
        "Simulated portfolio data only; no real CRM, marketing-automation or "
        "personal data. The channel→intent→consent structure is disclosed in "
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
