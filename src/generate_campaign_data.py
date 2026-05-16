"""Deterministic generator for the simulated campaign sample data.

Replaces the previous hand-built CSVs (which were perfectly linear: flat
conversion rate, ROAS and R^2 = 1.00) with a reproducible synthetic dataset
that has realistic week-to-week volatility, a mid-flight promo spike, a
Display soft patch, and a landing-page test win that lifts Paid Search
conversion rate from week 4 — so the deep dive actually has signal to find.

A single fixed seed makes the output byte-stable; the data card in
`data/DATA_CARD.md` documents the generative model. Pure standard library.

Channels map 1:1 to audience segments and landing pages so the ROAS
ordering (Email/Existing > Search/High-intent > Social/Lookalike >
Display/Local) is preserved by construction:

    Paid Search  -> High-intent prospects -> /promo
    Paid Social  -> Lookalike audience    -> /collection
    Email        -> Existing customers    -> /service-booking
    Display      -> Local prospects       -> /store-locator
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CAMPAIGN_PATH = DATA_DIR / "campaign_performance_sample.csv"
LANDING_PATH = DATA_DIR / "landing_page_sample.csv"
PATHS_PATH = DATA_DIR / "conversion_paths_sample.csv"

SEED = 20260516
WEEKS = ["2026-04-06", "2026-04-13", "2026-04-20", "2026-04-27", "2026-05-04", "2026-05-11"]
DEVICES = ("Mobile", "Desktop")

# Per-channel base economics (per channel-device-week, before weekly dynamics).
# Tuned so blended ROAS by segment keeps Existing > High-intent > Lookalike > Local.
CHANNELS = {
    "Paid Search": {
        "campaign": "Spring Promo",
        "segment": "High-intent prospects",
        "landing_page": "/promo",
        "impressions": 19000,
        "ctr": 0.050,
        "cpc": 1.30,
        "cr": 0.086,
        "aov": 88.0,
    },
    "Paid Social": {
        "campaign": "New Collection Awareness",
        "segment": "Lookalike audience",
        "landing_page": "/collection",
        "impressions": 26500,
        "ctr": 0.030,
        "cpc": 1.18,
        "cr": 0.052,
        "aov": 78.0,
    },
    "Email": {
        "campaign": "Service Renewal",
        "segment": "Existing customers",
        "landing_page": "/service-booking",
        "impressions": 9200,
        "ctr": 0.060,
        "cpc": 0.32,
        "cr": 0.108,
        "aov": 84.0,
    },
    "Display": {
        "campaign": "Store Locator Push",
        "segment": "Local prospects",
        "landing_page": "/store-locator",
        "impressions": 31000,
        "ctr": 0.015,
        "cpc": 1.30,
        "cr": 0.050,
        "aov": 68.0,
    },
}


def _weekly_scale(rng: random.Random, channel: str, week_idx: int) -> float:
    """Demand multiplier: gentle upward trend + idiosyncratic noise + events."""
    trend = 1.0 + 0.028 * week_idx
    noise = rng.gauss(1.0, 0.045)
    event = 1.0
    if channel in ("Paid Search", "Paid Social") and week_idx == 3:
        event *= 1.12  # mid-flight promo push
    if channel == "Display" and week_idx == 2:
        event *= 0.91  # seasonal soft patch
    return max(0.6, trend * noise * event)


def _cr_multiplier(channel: str, week_idx: int) -> float:
    """Paid Search landing-page test (variant B) rolls out from week 4."""
    if channel == "Paid Search" and week_idx >= 3:
        return 1.065
    return 1.0


def _round(value: float, places: int) -> float:
    return float(f"{value:.{places}f}")


def build_campaign_rows() -> list[dict[str, object]]:
    rng = random.Random(SEED)
    rows: list[dict[str, object]] = []
    for week_idx, date in enumerate(WEEKS):
        for channel, base in CHANNELS.items():
            scale = _weekly_scale(rng, channel, week_idx)
            cr_mult = _cr_multiplier(channel, week_idx)
            for device in DEVICES:
                dev_skew = 1.05 if device == "Mobile" else 0.95
                impressions = int(round(base["impressions"] * scale * dev_skew))
                ctr = base["ctr"] * rng.gauss(1.0, 0.03)
                clicks = max(1, int(round(impressions * ctr)))
                cpc = base["cpc"] * rng.gauss(1.0, 0.03)
                cost = clicks * cpc
                cr = base["cr"] * cr_mult * rng.gauss(1.0, 0.04)
                conversions = max(1, int(round(clicks * cr)))
                aov = base["aov"] * rng.gauss(1.0, 0.03)
                revenue = conversions * aov

                rows.append(
                    {
                        "date": date,
                        "channel": channel,
                        "campaign": base["campaign"],
                        "audience_segment": base["segment"],
                        "device": device,
                        "landing_page": base["landing_page"],
                        "impressions": impressions,
                        "clicks": clicks,
                        "cost_eur": _round(cost, 2),
                        "conversions": conversions,
                        "revenue_eur": _round(revenue, 2),
                        "ctr": _round(clicks / impressions, 4),
                        "cpc": _round(cost / clicks, 2),
                        "conversion_rate": _round(conversions / clicks, 4),
                        "cpa": _round(cost / conversions, 2),
                        "roas": _round(revenue / cost, 2),
                    }
                )
    return rows


def build_landing_rows(campaign_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Independent landing-page sample, kept internally consistent."""
    issues = {
        "/promo": ("Good traffic, slightly weaker checkout completion", "Keep budget stable and test shorter mobile form"),
        "/collection": ("Awareness traffic converts below search and email", "Tighten audience and add product proof above the fold"),
        "/service-booking": ("Strong conversion, low CPC", "Protect email list quality and test SMS reminder"),
        "/store-locator": ("High bounce and low CTR", "Improve local relevance and page speed on mobile"),
    }
    bounce = {"/promo": 0.36, "/collection": 0.45, "/service-booking": 0.27, "/store-locator": 0.50}
    duration = {"/promo": 124, "/collection": 95, "/service-booking": 167, "/store-locator": 70}

    by_page_device: dict[tuple[str, str], dict[str, float]] = {}
    for r in campaign_rows:
        key = (str(r["landing_page"]), str(r["device"]))
        agg = by_page_device.setdefault(key, {"clicks": 0, "conversions": 0, "revenue": 0.0})
        agg["clicks"] += int(r["clicks"])
        agg["conversions"] += int(r["conversions"])
        agg["revenue"] += float(r["revenue_eur"])

    rng = random.Random(SEED + 1)
    rows: list[dict[str, object]] = []
    for (page, device), agg in sorted(by_page_device.items()):
        # Sessions exceed paid clicks (organic/direct also land here).
        sessions = int(round(agg["clicks"] * rng.uniform(1.05, 1.20)))
        conversions = int(round(agg["conversions"] * rng.uniform(0.92, 1.05)))
        conversions = min(conversions, sessions)
        dev_bounce = bounce[page] + (0.02 if device == "Mobile" else -0.02)
        rows.append(
            {
                "landing_page": page,
                "device": device,
                "sessions": sessions,
                "bounce_rate": _round(dev_bounce, 4),
                "avg_session_duration_sec": duration[page] + (-12 if device == "Mobile" else 14),
                "conversions": conversions,
                "revenue_eur": _round(agg["revenue"] * rng.uniform(0.95, 1.05), 2),
                "conversion_rate": _round(conversions / sessions, 4),
                "primary_issue": issues[page][0],
                "recommendation": issues[page][1],
            }
        )
    return rows


# Multi-touch journey templates: realistic assist patterns. Display and Paid
# Social are upper-funnel assists; Email and Paid Search close. Organic Search
# and Direct appear as unpaid touchpoints. `journeys` = total journeys on this
# path, `conversions` = how many of them converted.
PATH_TEMPLATES = [
    ("Paid Search", 1400, 196, 92.0),
    ("Email", 1100, 178, 86.0),
    ("Paid Social", 1600, 96, 80.0),
    ("Display", 2100, 71, 70.0),
    ("Organic Search", 1300, 121, 88.0),
    ("Direct", 900, 99, 90.0),
    ("Display>Paid Search", 760, 137, 95.0),
    ("Paid Social>Paid Search", 690, 124, 93.0),
    ("Display>Paid Social>Paid Search", 540, 113, 96.0),
    ("Paid Social>Email", 520, 109, 88.0),
    ("Display>Email", 480, 91, 84.0),
    ("Organic Search>Paid Search", 610, 134, 94.0),
    ("Paid Search>Email", 430, 116, 97.0),
    ("Display>Paid Social>Email", 360, 76, 86.0),
    ("Paid Social>Display>Paid Search", 320, 67, 95.0),
    ("Direct>Paid Search", 380, 87, 93.0),
    ("Display>Organic Search>Email", 290, 58, 85.0),
    ("Paid Social>Organic Search>Paid Search", 270, 59, 94.0),
    ("Email>Paid Search", 240, 71, 99.0),
    ("Display>Display>Paid Search", 210, 38, 92.0),
]


def build_path_rows() -> list[dict[str, object]]:
    rng = random.Random(SEED + 2)
    rows: list[dict[str, object]] = []
    for idx, (path, journeys, conv, aov) in enumerate(PATH_TEMPLATES, start=1):
        jitter_j = int(round(journeys * rng.uniform(0.95, 1.05)))
        jitter_c = min(jitter_j, int(round(conv * rng.uniform(0.95, 1.05))))
        rows.append(
            {
                "path_id": f"p{idx:03d}",
                "path": path,
                "journeys": jitter_j,
                "conversions": jitter_c,
                "revenue_eur": _round(jitter_c * aov * rng.uniform(0.97, 1.03), 2),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    campaign = build_campaign_rows()
    landing = build_landing_rows(campaign)
    paths = build_path_rows()
    _write_csv(CAMPAIGN_PATH, campaign)
    _write_csv(LANDING_PATH, landing)
    _write_csv(PATHS_PATH, paths)
    print(
        f"Wrote {len(campaign)} campaign rows, {len(landing)} landing rows, "
        f"{len(paths)} conversion-path rows (seed={SEED})."
    )


if __name__ == "__main__":
    main()
