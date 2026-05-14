"""Build markdown summaries from the simulated campaign CSV files."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
REPORTS_DIR = ROOT / "reports"


def read_campaign_rows() -> list[dict[str, str]]:
    with CAMPAIGN_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def aggregate(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = defaultdict(
        lambda: {"impressions": 0, "clicks": 0, "cost_eur": 0.0, "conversions": 0, "revenue_eur": 0.0}
    )
    for row in rows:
        group = grouped[row[key]]
        group["impressions"] += int(row["impressions"])
        group["clicks"] += int(row["clicks"])
        group["cost_eur"] += float(row["cost_eur"])
        group["conversions"] += int(row["conversions"])
        group["revenue_eur"] += float(row["revenue_eur"])
    return grouped


def enrich(metrics: dict[str, float]) -> dict[str, float]:
    clicks = metrics["clicks"]
    impressions = metrics["impressions"]
    cost = metrics["cost_eur"]
    conversions = metrics["conversions"]
    revenue = metrics["revenue_eur"]
    return {
        **metrics,
        "ctr": clicks / impressions,
        "cpc": cost / clicks,
        "conversion_rate": conversions / clicks,
        "cpa": cost / conversions,
        "roas": revenue / cost,
    }


def fmt_eur(value: float) -> str:
    return f"EUR {value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1%}"


def total_metrics(rows: list[dict[str, str]]) -> dict[str, float]:
    return {
        "impressions": sum(int(row["impressions"]) for row in rows),
        "clicks": sum(int(row["clicks"]) for row in rows),
        "cost_eur": sum(float(row["cost_eur"]) for row in rows),
        "conversions": sum(int(row["conversions"]) for row in rows),
        "revenue_eur": sum(float(row["revenue_eur"]) for row in rows),
    }


def build_executive_summary(rows: list[dict[str, str]]) -> str:
    total = enrich(total_metrics(rows))
    by_channel = {channel: enrich(values) for channel, values in aggregate(rows, "channel").items()}
    best_roas = max(by_channel.items(), key=lambda item: item[1]["roas"])
    highest_volume = max(by_channel.items(), key=lambda item: item[1]["conversions"])
    lowest_efficiency = min(by_channel.items(), key=lambda item: item[1]["roas"])

    channel_lines = "\n".join(
        f"| {channel} | {int(values['clicks']):,} | {int(values['conversions']):,} | {fmt_pct(values['conversion_rate'])} | {fmt_eur(values['cost_eur'])} | {values['roas']:.2f} |"
        for channel, values in sorted(by_channel.items())
    )

    return f"""# Executive Summary

## Campaign readout

This simulated six-week campaign sample generated {int(total['clicks']):,} clicks, {int(total['conversions']):,} conversions, {fmt_eur(total['revenue_eur'])} revenue and {total['roas']:.2f} blended ROAS.

## Main observations

- {best_roas[0]} has the strongest ROAS at {best_roas[1]['roas']:.2f}, driven by high-intent traffic and low CPC.
- {highest_volume[0]} contributes the highest conversion volume with {int(highest_volume[1]['conversions']):,} conversions.
- {lowest_efficiency[0]} has the lowest ROAS at {lowest_efficiency[1]['roas']:.2f}; it should be reviewed for audience quality, landing page speed and budget allocation.

## Channel view

| Channel | Clicks | Conversions | Conversion rate | Cost | ROAS |
| --- | ---: | ---: | ---: | ---: | ---: |
{channel_lines}

## Practical recommendations

- Protect budget for high-intent Search and retention Email activity while monitoring saturation.
- Improve Display and Store Locator traffic quality before scaling spend.
- Use landing page review to separate media problems from page-experience problems.
- Keep reporting simple: weekly trend, channel split, device split and landing page action tracker.

## Boundary

This report uses simulated portfolio data only and does not claim access to real advertising, client, user or analytics data.
"""


def build_weekly_insights(rows: list[dict[str, str]]) -> str:
    by_week = {week: enrich(values) for week, values in aggregate(rows, "date").items()}
    lines = "\n".join(
        f"| {week} | {int(values['clicks']):,} | {int(values['conversions']):,} | {fmt_eur(values['cost_eur'])} | {fmt_eur(values['revenue_eur'])} | {values['roas']:.2f} |"
        for week, values in sorted(by_week.items())
    )

    first_week = by_week[min(by_week)]
    last_week = by_week[max(by_week)]
    conversion_change = last_week["conversions"] - first_week["conversions"]
    roas_change = last_week["roas"] - first_week["roas"]

    return f"""# Weekly Campaign Insights

## Trend summary

Conversions increased by {conversion_change:.0f} from the first to the last simulated week. Blended ROAS moved by {roas_change:.2f} points over the same period.

| Week | Clicks | Conversions | Cost | Revenue | ROAS |
| --- | ---: | ---: | ---: | ---: | ---: |
{lines}

## Interpretation

- Growth is volume-led: spend, traffic and conversions rise gradually week by week.
- Blended ROAS is stable, which suggests the simulated campaign scales without a major efficiency drop.
- The next reporting view should split this trend by channel and landing page before changing budget.
"""


def main() -> None:
    rows = read_campaign_rows()
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "executive_summary.md").write_text(build_executive_summary(rows), encoding="utf-8")
    (REPORTS_DIR / "weekly_campaign_insights.md").write_text(build_weekly_insights(rows), encoding="utf-8")
    print("Wrote executive_summary.md and weekly_campaign_insights.md")


if __name__ == "__main__":
    main()
