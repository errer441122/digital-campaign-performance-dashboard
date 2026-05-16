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
CONTACTS_PATH = ROOT / "data" / "crm_contacts_sample.csv"

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


# Per-channel contact quality: how many *non-buying* contacts each channel
# brings, the baseline intent level, and the valid-consent rate. Mirrors the
# order-side structure: Email/Organic acquire higher-intent, better-consented
# contacts; Display/Paid Social bring volume with weaker signal.
CONTACT_CHANNELS = {
    "Email": {"non_buyers": 280, "intent": 0.46, "consent_in": 0.88},
    "Organic Search": {"non_buyers": 360, "intent": 0.42, "consent_in": 0.80},
    "Paid Search": {"non_buyers": 520, "intent": 0.38, "consent_in": 0.66},
    "Direct": {"non_buyers": 180, "intent": 0.40, "consent_in": 0.72},
    "Paid Social": {"non_buyers": 560, "intent": 0.27, "consent_in": 0.55},
    "Display": {"non_buyers": 430, "intent": 0.22, "consent_in": 0.48},
}
CONSENT_SOURCES = ["signup_form", "newsletter", "gated_content", "event", "import"]


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _engagement(rng: random.Random, intent: float, opted_in: bool) -> dict[str, int]:
    """Engagement counts rise with latent intent; email activity also needs
    a valid opt-in to be plausible."""
    page_views = max(0, int(round(rng.gauss(2 + 14 * intent, 3))))
    key_page_views = max(0, min(page_views, int(round(rng.gauss(3.5 * intent, 1.0)))))
    email_clicks = max(0, int(round(rng.gauss(6 * intent, 2)))) if opted_in else 0
    form_submits = max(0, min(3, int(round(rng.gauss(1.6 * intent, 0.8)))))
    demo_request = 1 if rng.random() < (intent ** 2) * 1.1 else 0
    webinar_signup = 1 if rng.random() < intent * 0.30 else 0
    return {
        "page_views": page_views,
        "key_page_views": key_page_views,
        "email_clicks": email_clicks,
        "form_submits": form_submits,
        "demo_request": demo_request,
        "webinar_signup": webinar_signup,
    }


def _consent(rng: random.Random, consent_in_rate: float) -> tuple[str, str]:
    r = rng.random()
    if r < consent_in_rate:
        status = "opted_in"
    elif r < consent_in_rate + (1 - consent_in_rate) * 0.45:
        status = "opted_out"
    else:
        status = "unknown"
    source = "unknown" if status == "unknown" else rng.choice(CONSENT_SOURCES)
    return status, source


def build_contacts(order_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Contact-level CRM table with engagement + consent. Independent RNG so
    the byte-stable order sample is untouched. Buyers are carried over from
    the order sample (referential consistency); non-buyers are added per
    channel."""
    rng = random.Random(SEED + 5)

    # Collapse orders to one record per customer (channel, signup, last order).
    buyers: dict[str, dict[str, object]] = {}
    for r in order_rows:
        cid = r["customer_id"]
        b = buyers.setdefault(
            cid,
            {
                "channel": r["acquisition_channel"],
                "signup": r["signup_date"],
                "last_order": r["order_date"],
            },
        )
        if r["order_date"] > b["last_order"]:
            b["last_order"] = r["order_date"]

    contacts: list[dict[str, object]] = []

    for cid, b in sorted(buyers.items()):
        channel = b["channel"]
        cfg = CONTACT_CHANNELS[channel]
        intent = _clamp01(cfg["intent"] + 0.22 + rng.gauss(0.0, 0.16))
        # Buyers consent at a higher rate than cold contacts.
        status, source = _consent(rng, min(0.97, cfg["consent_in"] + 0.10))
        eng = _engagement(rng, intent, status == "opted_in")
        last_order = date.fromisoformat(str(b["last_order"]))
        days_idle = (ANALYSIS_DATE - last_order).days + max(0, int(rng.gauss(8, 6)))
        contacts.append(
            {
                "contact_id": cid,
                "acquisition_channel": channel,
                "signup_date": b["signup"],
                "has_purchase": 1,
                "days_since_last_activity": max(0, days_idle),
                "consent_status": status,
                "consent_source": source,
                **eng,
            }
        )

    seq = 0
    for channel, cfg in CONTACT_CHANNELS.items():
        for _ in range(cfg["non_buyers"]):
            seq += 1
            intent = _clamp01(cfg["intent"] + rng.gauss(0.0, 0.18))
            status, source = _consent(rng, cfg["consent_in"])
            eng = _engagement(rng, intent, status == "opted_in")
            cohort = rng.choice(COHORT_MONTHS)
            signup = _signup_date(rng, cohort)
            # More engaged contacts have been active more recently.
            days_idle = max(0, int(round(rng.gauss(120 * (1 - intent) + 10, 25))))
            contacts.append(
                {
                    "contact_id": f"L{seq:05d}",
                    "acquisition_channel": channel,
                    "signup_date": signup.isoformat(),
                    "has_purchase": 0,
                    "days_since_last_activity": days_idle,
                    "consent_status": status,
                    "consent_source": source,
                    **eng,
                }
            )

    contacts.sort(key=lambda c: c["contact_id"])
    return contacts


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = build_orders()
    _write_csv(ORDERS_PATH, rows)
    customers = len({r["customer_id"] for r in rows})
    contacts = build_contacts(rows)
    _write_csv(CONTACTS_PATH, contacts)
    print(
        f"Wrote {len(rows)} orders for {customers} customers and "
        f"{len(contacts)} contacts (seed={SEED})."
    )


if __name__ == "__main__":
    main()
