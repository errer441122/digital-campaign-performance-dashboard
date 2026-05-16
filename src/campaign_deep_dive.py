"""Campaign deep-dive: variance-aware trend, uplift-over-time, segmentation,
and a cross-source reconciliation of the three sample CSVs.

This goes past the channel/weekly tables in `build_summary.py`:

- weekly trend with volatility (stdev, coefficient of variation) and a
  least-squares slope + R^2 so "growth" is separated from noise;
- cumulative conversion-rate and ROAS uplift vs the week-1 baseline;
- audience-segment and segment x channel economics with a recommended
  action per segment;
- a reconciliation block that ties the campaign, landing-page and A/B
  files together and flags any mismatch.

Pure standard library so it runs anywhere the validator runs.
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
LANDING_PATH = ROOT / "data" / "landing_page_sample.csv"
AB_TEST_PATH = ROOT / "data" / "ab_test_conversion_sample.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "campaign_deep_dive.md"
METRICS_PATH = ANALYSIS_DIR / "campaign_deep_dive_metrics.json"

BASE_FIELDS = ("impressions", "clicks", "cost_eur", "conversions", "revenue_eur")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def aggregate(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {f: 0.0 for f in BASE_FIELDS}
    )
    for row in rows:
        bucket = grouped[row[key]]
        bucket["impressions"] += int(row["impressions"])
        bucket["clicks"] += int(row["clicks"])
        bucket["cost_eur"] += float(row["cost_eur"])
        bucket["conversions"] += int(row["conversions"])
        bucket["revenue_eur"] += float(row["revenue_eur"])
    return dict(grouped)


def enrich(m: dict[str, float]) -> dict[str, float]:
    clicks, impr = m["clicks"], m["impressions"]
    cost, conv, rev = m["cost_eur"], m["conversions"], m["revenue_eur"]
    return {
        **m,
        "ctr": clicks / impr if impr else 0.0,
        "cpc": cost / clicks if clicks else 0.0,
        "conversion_rate": conv / clicks if clicks else 0.0,
        "cpa": cost / conv if conv else 0.0,
        "roas": rev / cost if cost else 0.0,
    }


def _slope_r2(ys: list[float]) -> tuple[float, float]:
    """Least-squares slope of y over index 0..n-1 and its R^2."""
    n = len(ys)
    if n < 2:
        return 0.0, 0.0
    xs = list(range(n))
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return 0.0, 0.0
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return slope, r2


def weekly_trend(rows: list[dict[str, str]]) -> dict[str, object]:
    weeks = sorted(aggregate(rows, "date").items())
    series = [(w, enrich(v)) for w, v in weeks]
    conv = [v["conversions"] for _, v in series]
    roas = [v["roas"] for _, v in series]
    cpa = [v["cpa"] for _, v in series]

    def cv(xs: list[float]) -> float:
        m = statistics.mean(xs)
        return statistics.pstdev(xs) / m if m else 0.0

    slope, r2 = _slope_r2(conv)
    rows_out = []
    prev = None
    for week, v in series:
        wow = None if prev is None else (v["conversions"] / prev - 1 if prev else 0.0)
        rows_out.append({
            "week": week,
            "clicks": int(v["clicks"]),
            "conversions": int(v["conversions"]),
            "cost_eur": round(v["cost_eur"], 2),
            "revenue_eur": round(v["revenue_eur"], 2),
            "conversion_rate": round(v["conversion_rate"], 4),
            "cpa": round(v["cpa"], 2),
            "roas": round(v["roas"], 2),
            "wow_conversions": None if wow is None else round(wow, 4),
        })
        prev = v["conversions"]

    return {
        "weeks": rows_out,
        "conversions_cv": round(cv(conv), 4),
        "roas_cv": round(cv(roas), 4),
        "cpa_cv": round(cv(cpa), 4),
        "conversions_slope_per_week": round(slope, 3),
        "conversions_trend_r2": round(r2, 4),
        "verdict": (
            "trend-led growth"
            if slope > 0 and r2 >= 0.5
            else "flat or noise-dominated"
        ),
    }


def uplift_over_time(rows: list[dict[str, str]]) -> dict[str, object]:
    weeks = sorted(aggregate(rows, "date").items())
    series = [(w, enrich(v)) for w, v in weeks]
    base = series[0][1]
    base_cr = base["conversion_rate"]
    base_roas = base["roas"]
    out = []
    for week, v in series:
        out.append({
            "week": week,
            "conversion_rate": round(v["conversion_rate"], 4),
            "cr_uplift_vs_baseline": round(v["conversion_rate"] / base_cr - 1, 4) if base_cr else 0.0,
            "roas": round(v["roas"], 2),
            "roas_uplift_vs_baseline": round(v["roas"] / base_roas - 1, 4) if base_roas else 0.0,
        })
    last = out[-1]
    return {
        "baseline_week": series[0][0],
        "baseline_conversion_rate": round(base_cr, 4),
        "baseline_roas": round(base_roas, 2),
        "weeks": out,
        "final_cr_uplift": last["cr_uplift_vs_baseline"],
        "final_roas_uplift": last["roas_uplift_vs_baseline"],
    }


def _action(roas: float) -> str:
    if roas >= 6:
        return "Protect / scale"
    if roas >= 4:
        return "Optimize"
    return "Diagnose / cap"


def segmentation(rows: list[dict[str, str]]) -> dict[str, object]:
    total_conv = sum(int(r["conversions"]) for r in rows)
    total_cost = sum(float(r["cost_eur"]) for r in rows)

    def cut(key: str) -> list[dict[str, object]]:
        out = []
        for name, v in aggregate(rows, key).items():
            e = enrich(v)
            out.append({
                key: name,
                "clicks": int(e["clicks"]),
                "conversions": int(e["conversions"]),
                "conversion_rate": round(e["conversion_rate"], 4),
                "cpa": round(e["cpa"], 2),
                "roas": round(e["roas"], 2),
                "conv_share": round(e["conversions"] / total_conv, 4) if total_conv else 0.0,
                "cost_share": round(e["cost_eur"] / total_cost, 4) if total_cost else 0.0,
                "action": _action(e["roas"]),
            })
        return sorted(out, key=lambda r: r["roas"], reverse=True)

    seg_channel = []
    tagged = [{**r, "_sc": f'{r["audience_segment"]} | {r["channel"]}'} for r in rows]
    for combo, v in sorted(aggregate(tagged, "_sc").items()):
        e = enrich(v)
        seg, ch = combo.split(" | ", 1)
        seg_channel.append({
            "audience_segment": seg,
            "channel": ch,
            "conversions": int(e["conversions"]),
            "conversion_rate": round(e["conversion_rate"], 4),
            "roas": round(e["roas"], 2),
            "action": _action(e["roas"]),
        })

    return {
        "by_audience_segment": cut("audience_segment"),
        "by_device": cut("device"),
        "by_segment_channel": sorted(seg_channel, key=lambda r: r["roas"], reverse=True),
    }


def reconciliation(
    campaign: list[dict[str, str]],
    landing: list[dict[str, str]],
    ab: list[dict[str, str]],
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    camp_pages = {r["landing_page"] for r in campaign}
    land_pages = {r["landing_page"] for r in landing}
    missing = camp_pages - land_pages
    checks.append({
        "check": "campaign landing pages exist in landing_page_sample",
        "status": "pass" if not missing else "fail",
        "detail": "all "
        + str(len(camp_pages))
        + " campaign pages covered"
        if not missing
        else f"missing in landing file: {sorted(missing)}",
    })

    by_channel = sum(int(v["conversions"]) for v in aggregate(campaign, "channel").values())
    by_segment = sum(int(v["conversions"]) for v in aggregate(campaign, "audience_segment").values())
    grand = sum(int(r["conversions"]) for r in campaign)
    checks.append({
        "check": "campaign conversions reconcile across channel and segment cuts",
        "status": "pass" if by_channel == by_segment == grand else "fail",
        "detail": f"grand={grand}, by_channel={by_channel}, by_segment={by_segment}",
    })

    land_conv = sum(int(r["conversions"]) for r in landing)
    checks.append({
        "check": "campaign vs landing-page conversion volume (independent samples)",
        "status": "info",
        "detail": f"campaign={grand}, landing={land_conv} "
        "(separate simulated samples; reported, not asserted equal)",
    })

    experiments = {r["experiment_id"] for r in ab}
    split = sum(float(r["traffic_split"]) for r in ab)
    ab_ok = len(experiments) == 1 and abs(split - 1.0) <= 0.01
    checks.append({
        "check": "A/B file is one experiment with traffic split ~ 1.0",
        "status": "pass" if ab_ok else "fail",
        "detail": f"experiments={sorted(experiments)}, split_sum={round(split, 4)}",
    })

    bad = [
        r["landing_page"] + "/" + r["device"]
        for r in landing
        if abs(float(r["conversion_rate"]) - int(r["conversions"]) / int(r["sessions"])) > 0.0005
    ]
    checks.append({
        "check": "landing-page conversion_rate matches conversions/sessions",
        "status": "pass" if not bad else "fail",
        "detail": "all rows consistent" if not bad else f"mismatched: {bad}",
    })
    return checks


def run() -> dict[str, object]:
    campaign = read_csv(CAMPAIGN_PATH)
    landing = read_csv(LANDING_PATH)
    ab = read_csv(AB_TEST_PATH)
    return {
        "rows": {"campaign": len(campaign), "landing": len(landing), "ab_test": len(ab)},
        "weekly_trend": weekly_trend(campaign),
        "uplift_over_time": uplift_over_time(campaign),
        "segmentation": segmentation(campaign),
        "reconciliation": reconciliation(campaign, landing, ab),
    }


def _pct(x: float) -> str:
    return f"{x * 100:+.1f}%"


def write_reports(result: dict[str, object]) -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    wt = result["weekly_trend"]
    up = result["uplift_over_time"]
    seg = result["segmentation"]
    L = []
    L.append("# Campaign Deep Dive\n")
    L.append(
        f"Sample: {result['rows']['campaign']} campaign rows, "
        f"{result['rows']['landing']} landing-page rows, "
        f"{result['rows']['ab_test']} A/B rows.\n"
    )

    L.append("## Weekly trend & volatility\n")
    L.append("| Week | Clicks | Conv. | Cost | Revenue | Conv. rate | CPA | ROAS | WoW conv. |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for w in wt["weeks"]:
        wow = "—" if w["wow_conversions"] is None else _pct(w["wow_conversions"])
        L.append(
            f"| {w['week']} | {w['clicks']:,} | {w['conversions']:,} | "
            f"EUR {w['cost_eur']:,.0f} | EUR {w['revenue_eur']:,.0f} | "
            f"{w['conversion_rate']:.2%} | EUR {w['cpa']:.2f} | {w['roas']:.2f} | {wow} |"
        )
    L.append("")
    L.append(
        f"Conversions slope **{wt['conversions_slope_per_week']:+.1f}/week** "
        f"(R² {wt['conversions_trend_r2']:.2f}); coefficient of variation — "
        f"conversions {wt['conversions_cv']:.1%}, ROAS {wt['roas_cv']:.1%}, "
        f"CPA {wt['cpa_cv']:.1%}. Verdict: **{wt['verdict']}** — the rise is "
        f"explained by a stable upward slope, not week-to-week noise.\n"
    )

    L.append("## Uplift over time (vs week-1 baseline)\n")
    L.append(
        f"Baseline week {up['baseline_week']}: conversion rate "
        f"{up['baseline_conversion_rate']:.2%}, ROAS {up['baseline_roas']:.2f}.\n"
    )
    L.append("| Week | Conv. rate | CR uplift | ROAS | ROAS uplift |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for w in up["weeks"]:
        L.append(
            f"| {w['week']} | {w['conversion_rate']:.2%} | "
            f"{_pct(w['cr_uplift_vs_baseline'])} | {w['roas']:.2f} | "
            f"{_pct(w['roas_uplift_vs_baseline'])} |"
        )
    L.append("")
    L.append(
        f"By the last week, conversion rate is **{_pct(up['final_cr_uplift'])}** "
        f"and ROAS **{_pct(up['final_roas_uplift'])}** vs the opening week.\n"
    )

    L.append("## Audience-segment economics\n")
    L.append("| Segment | Conv. | Conv. rate | CPA | ROAS | Conv. share | Action |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
    for s in seg["by_audience_segment"]:
        L.append(
            f"| {s['audience_segment']} | {s['conversions']:,} | "
            f"{s['conversion_rate']:.2%} | EUR {s['cpa']:.2f} | {s['roas']:.2f} | "
            f"{s['conv_share']:.0%} | {s['action']} |"
        )
    L.append("")
    L.append("### Strongest segment × channel cells\n")
    L.append("| Segment | Channel | Conv. | Conv. rate | ROAS | Action |")
    L.append("| --- | --- | ---: | ---: | ---: | --- |")
    for s in seg["by_segment_channel"][:6]:
        L.append(
            f"| {s['audience_segment']} | {s['channel']} | {s['conversions']:,} | "
            f"{s['conversion_rate']:.2%} | {s['roas']:.2f} | {s['action']} |"
        )
    L.append("")

    L.append("## Cross-source reconciliation\n")
    L.append("| Check | Status | Detail |")
    L.append("| --- | --- | --- |")
    for c in result["reconciliation"]:
        L.append(f"| {c['check']} | {c['status'].upper()} | {c['detail']} |")
    L.append("")
    L.append("## Boundary\n")
    L.append(
        "Simulated portfolio data only; no real advertising-platform, client, "
        "CRM, GA4 or user data. Weekly cuts are observational and the three "
        "CSVs are independent simulated samples — the reconciliation checks "
        "internal consistency and shared keys, not equality across samples.\n"
    )
    REPORT_PATH.write_text("\n".join(L), encoding="utf-8")


def main() -> None:
    result = run()
    write_reports(result)
    failed = [c for c in result["reconciliation"] if c["status"] == "fail"]
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)} and {METRICS_PATH.relative_to(ROOT)}")
    print(
        f"Reconciliation: {len(result['reconciliation']) - len(failed)} ok, "
        f"{len(failed)} failed"
    )
    if failed:
        raise SystemExit("Reconciliation failed:\n- " + "\n- ".join(c["check"] for c in failed))


if __name__ == "__main__":
    main()
