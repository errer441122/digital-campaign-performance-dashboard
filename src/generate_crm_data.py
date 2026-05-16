"""Generate a **clearly-labelled SIMULATED** engagement + consent overlay,
keyed to the **real** customers in `data/online_retail_orders.csv`.

Why this is synthetic: Online Retail II is transactional only — it has no
email/website engagement signals and no marketing-consent status, and no
permissive public dataset carries per-contact consent. So the lead-scoring
and GDPR-suppression demo runs on a disclosed synthetic overlay attached to
the real customer IDs (hybrid, per the project decision). The customer's
*lifecycle* in `crm_lifecycle.py` is derived from the **real** purchase
behaviour; only the engagement/consent columns here are simulated.

Deterministic: a fixed seed plus a per-customer hash, so re-running
reproduces the file byte-for-byte. Pure standard library.
"""

from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORDERS_PATH = ROOT / "data" / "online_retail_orders.csv"
OVERLAY_PATH = ROOT / "data" / "crm_engagement_overlay.csv"

SEED = 20260516
CONSENT_SOURCES = ["signup_form", "newsletter", "gated_content", "event", "import"]


def _real_customers() -> list[str]:
    seen: dict[str, None] = {}
    with ORDERS_PATH.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            seen.setdefault(r["customer_id"], None)
    return sorted(seen)


def _rng_for(customer_id: str) -> random.Random:
    """Per-customer deterministic RNG: stable regardless of row order."""
    h = hashlib.sha256(f"{SEED}:{customer_id}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def build_overlay() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for cid in _real_customers():
        rng = _rng_for(cid)
        intent = _clamp01(rng.gauss(0.42, 0.20))
        r = rng.random()
        if r < 0.62 + 0.2 * intent:
            consent = "opted_in"
        elif r < 0.80:
            consent = "opted_out"
        else:
            consent = "unknown"
        opted_in = consent == "opted_in"
        rows.append(
            {
                "customer_id": cid,
                "consent_status": consent,
                "consent_source": "unknown" if consent == "unknown" else rng.choice(CONSENT_SOURCES),
                "page_views": max(0, int(round(rng.gauss(2 + 14 * intent, 3)))),
                "key_page_views": max(0, int(round(rng.gauss(3.2 * intent, 1.0)))),
                "email_clicks": (max(0, int(round(rng.gauss(6 * intent, 2)))) if opted_in else 0),
                "form_submits": max(0, min(3, int(round(rng.gauss(1.5 * intent, 0.8))))),
                "demo_request": 1 if rng.random() < (intent ** 2) * 1.1 else 0,
                "webinar_signup": 1 if rng.random() < intent * 0.30 else 0,
            }
        )
    # key_page_views must not exceed page_views
    for row in rows:
        row["key_page_views"] = min(row["key_page_views"], row["page_views"])
    rows.sort(key=lambda r: r["customer_id"])
    return rows


def main() -> None:
    rows = build_overlay()
    OVERLAY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OVERLAY_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(
        f"Wrote SIMULATED engagement/consent overlay for {len(rows):,} real "
        f"customers to {OVERLAY_PATH.relative_to(ROOT)} (seed={SEED})."
    )


if __name__ == "__main__":
    main()
