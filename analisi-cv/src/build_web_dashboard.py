"""Build the analysis page (`docs/analysis.html`, served by GitHub Pages).

One self-contained HTML file: HTML/CSS charts, no JavaScript, no CDN, no web
fonts, light and dark mode, readable on a phone. Every number is read from
the JSON that `crm_retention.py` and `crm_lifecycle.py` write, so the page
cannot drift from `analysis/`. CI regenerates it and fails if the committed
copy differs.

Run after crm_retention.py and crm_lifecycle.py. Pure standard library.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "docs" / "analysis.html"
REPO = "https://github.com/errer441122/digital-campaign-performance-dashboard"
PAGE = "https://errer441122.github.io/digital-campaign-performance-dashboard/analysis.html"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# RFM segments grouped by the job the CRM team has to do with them. A segment
# the analysis adds later lands in the last group instead of disappearing.
JOBS = [
    ("Protect", "Your best customers. Reward them, do not discount them.",
     ["Champions", "Loyal customers"]),
    ("Develop", "Recent or cooling buyers. The goal is the next order.",
     ["New / promising", "Needs attention"]),
    ("Win back", "They used to buy and stopped. This is where an offer earns its cost.",
     ["At risk", "Can't lose them"]),
    ("Wind down", "Long inactive, low value. One cheap reminder, then stop mailing.",
     ["Hibernating"]),
]

# Heat steps: how much of the accent colour is mixed into the surface. The
# range is capped so the cell text keeps a 4.5:1 contrast in both themes;
# from FLIP on, the dark theme switches to dark text (see tests).
HEAT = [8, 15, 22, 29, 36, 43, 50, 60, 70]
FLIP = 7
# Lifecycle stages run from active to lapsed, so one hue from strong to faint.
STAGE_MIX = [100, 78, 54, 34, 18]

CSS = """
:root {
  color-scheme: light;
  --page: #f4f6f4; --surface: #fbfcfb; --ink: #101614; --ink-2: #47524d; --muted: #6a7570;
  --line: #dde3df; --rest: #d5dcd8; --accent: #0b6e4f; --heat: #145c40; --on-accent: #ffffff;
  --tint: #e7f1ec; --cell-hi: #101614;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0c1210; --surface: #121a17; --ink: #edf2ef; --ink-2: #b9c4be; --muted: #8b9690;
    --line: #25302b; --rest: #2b3833; --accent: #5fd3a4; --heat: #5fd3a4; --on-accent: #06100c;
    --tint: #16241e; --cell-hi: #06100c;
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 76px; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { margin: 0; background: var(--page); color: var(--ink);
  font: 16px/1.6 "Segoe UI Variable Text", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }
a { color: var(--accent); text-underline-offset: 3px; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.wrap { max-width: 1120px; margin: 0 auto; padding: 0 24px; }
.num { font-variant-numeric: tabular-nums; white-space: nowrap; }

.top { position: sticky; top: 0; z-index: 2; background: var(--page); border-bottom: 1px solid var(--line); }
.top .wrap { display: flex; align-items: center; gap: 28px; height: 60px; white-space: nowrap; overflow-x: auto; }
.top b { font-size: 15px; letter-spacing: -0.01em; }
.top nav { display: flex; gap: 22px; font-size: 14.5px; }
.top nav a { color: var(--ink-2); text-decoration: none; }
.top nav a:hover, .top nav a:focus-visible { color: var(--ink); text-decoration: underline; }
.top .src { margin-left: auto; font-size: 14.5px; }

.hero { display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, .8fr); gap: 56px; align-items: center;
  padding: 72px 0 64px; }
.eyebrow { font-size: 12.5px; font-weight: 600; letter-spacing: .09em; text-transform: uppercase; color: var(--accent); margin: 0 0 18px; }
h1 { font-family: "Segoe UI Variable Display", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
  font-size: clamp(32px, 4.2vw, 48px); line-height: 1.08; letter-spacing: -0.03em; font-weight: 650; margin: 0 0 20px;
  text-wrap: balance; }
.lead { font-size: 18px; color: var(--ink-2); max-width: 46ch; margin: 0 0 30px; }
.cta { display: inline-block; background: var(--accent); color: var(--on-accent); text-decoration: none; font-weight: 600;
  font-size: 15.5px; padding: 12px 24px; border-radius: 999px; transition: transform .15s ease; }
.cta.alt { background: transparent; color: var(--accent); border: 1px solid var(--accent); margin-left: 8px; }
.cta:hover { transform: translateY(-1px); }
.cta:active { transform: translateY(1px); }
.cta:focus-visible, a:focus-visible, summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }

.split { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 30px 30px 26px; }
.split figcaption { font-size: 15px; color: var(--ink-2); margin: 0 0 22px; }
.split .row { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 6px 16px; margin-bottom: 22px; }
.split .row span { font-size: 14px; color: var(--ink-2); }
.split .row b { font-size: 40px; line-height: 1; letter-spacing: -0.03em; font-weight: 650; }
.whole { grid-column: 1 / -1; height: 26px; border-radius: 6px; background: var(--rest); overflow: hidden; }
.whole i { display: block; height: 100%; background: var(--accent); border-radius: 6px 0 0 6px; }
.key { display: flex; gap: 20px; font-size: 13.5px; color: var(--ink-2); margin: 0; }
.key i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 7px; vertical-align: -1px; }

.figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line); margin: 0 0 88px; }
.figures div { padding: 26px 24px 24px 0; }
.figures div + div { padding-left: 24px; border-left: 1px solid var(--line); }
.figures dt { font-size: 14px; color: var(--ink-2); }
.figures dd { margin: 4px 0 2px; font-size: 32px; line-height: 1.15; letter-spacing: -0.02em; font-weight: 650; }
.figures small { font-size: 13.5px; color: var(--muted); }

section.block { margin: 0 0 96px; }
h2 { font-family: "Segoe UI Variable Display", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
  font-size: clamp(26px, 3vw, 34px); line-height: 1.15; letter-spacing: -0.025em; font-weight: 650; margin: 0 0 12px; }
.block > p.desc { color: var(--ink-2); max-width: 62ch; margin: 0 0 34px; font-size: 17px; }
.aside { color: var(--ink-2); font-size: 14.5px; max-width: 78ch; margin: 18px 0 0; }

.jobs { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.job { border: 1px solid var(--line); border-radius: 12px; padding: 24px 26px 12px; background: var(--surface); }
.job.lead-job { background: var(--tint); border-color: transparent; }
.job h3 { margin: 0 0 4px; font-size: 20px; letter-spacing: -0.015em; }
.job > p { margin: 0 0 14px; color: var(--ink-2); font-size: 14.5px; }
.seg { padding: 14px 0; }
.seg + .seg { border-top: 1px solid var(--line); }
.seg h4 { margin: 0; font-size: 16px; }
.seg .flow { margin: 0 0 10px; font-size: 14px; color: var(--ink-2); }
.pair { display: grid; grid-template-columns: 84px 1fr; align-items: center; gap: 4px 12px; font-size: 13.5px; color: var(--ink-2); }
.meter { display: flex; align-items: center; gap: 10px; min-width: 0; }
.meter i { display: block; height: 8px; border-radius: 4px; background: var(--accent); min-width: 3px; }
.meter i.soft { opacity: .45; }
.meter span { color: var(--ink); }
.meter em { font-style: normal; color: var(--muted); margin-left: 5px; }

.stack { display: flex; height: 34px; border-radius: 8px; overflow: hidden; gap: 2px; margin: 0 0 22px; }
.stack i { display: block; height: 100%; min-width: 4px; }
.stages { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 24px; }
.stage h3 { margin: 0 0 2px; font-size: 16px; }
.stage h3 i { display: inline-block; width: 11px; height: 11px; border-radius: 3px; margin-right: 8px; }
.stage b { display: block; font-size: 24px; letter-spacing: -0.02em; font-weight: 650; }
.stage p { margin: 6px 0 0; font-size: 13.5px; color: var(--ink-2); line-height: 1.45; }
.stage p.do { color: var(--ink); }
.callout { margin: 34px 0 0; padding: 22px 26px; border-radius: 12px; background: var(--tint); font-size: 17px; max-width: 78ch; }

.curve { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 18px; align-items: end; max-width: 760px; }
.curve div { display: flex; flex-direction: column; justify-content: flex-end; height: 190px; }
.curve b { font-size: 24px; letter-spacing: -0.02em; font-weight: 650; }
.curve i { display: block; background: var(--accent); border-radius: 6px 6px 0 0; margin-top: 6px; }
.curve span { font-size: 13.5px; color: var(--ink-2); border-top: 1px solid var(--line); padding-top: 8px; }
.second { margin-top: 48px; }
.second h3 { margin: 0 0 6px; font-size: 20px; letter-spacing: -0.015em; }
.second .note { margin: 0 0 20px; color: var(--ink-2); font-size: 15px; max-width: 62ch; }
.steps { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 20px; max-width: 900px; }
.steps span { display: block; font-size: 13.5px; color: var(--ink-2); }
.steps b { display: block; font-size: 28px; line-height: 1.2; letter-spacing: -0.02em; font-weight: 650; margin: 2px 0 8px; }
.steps i { display: block; height: 8px; border-radius: 4px; background: var(--accent); min-width: 4px; }
details { margin-top: 30px; }
summary { cursor: pointer; font-weight: 600; font-size: 15px; color: var(--accent); width: fit-content; }
.scroll { overflow-x: auto; margin-top: 16px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { padding: 8px 10px; text-align: left; }
thead th { font-size: 13px; font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--line); }
.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.heat { font-size: 13px; }
.heat th, .heat td { padding: 5px 6px; }
.heat th[scope=row] { font-weight: 500; white-space: nowrap; }
.heat td.c { text-align: center; font-variant-numeric: tabular-nums; border: 2px solid var(--page); color: var(--ink);
  background: color-mix(in srgb, var(--heat) calc(var(--p) * 1%), var(--surface)); }
.heat td.na { border: 2px solid var(--page);
  background: repeating-linear-gradient(135deg, transparent 0 5px, var(--rest) 5px 6px); }
@media (prefers-color-scheme: dark) { .heat td.c.hi { color: var(--cell-hi); } }
.scale { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); margin-top: 12px; flex-wrap: wrap; }
.scale .ramp { width: 150px; height: 10px; border-radius: 5px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--heat) 8%, var(--surface)), color-mix(in srgb, var(--heat) 70%, var(--surface))); }
.scale .na { display: inline-block; width: 22px; height: 12px; border-radius: 3px; vertical-align: -2px; border: 1px solid var(--line);
  background: repeating-linear-gradient(135deg, transparent 0 4px, var(--rest) 4px 5px); }

.markets { max-width: 860px; }
.markets td { padding: 14px 10px; }
.markets tbody tr + tr > * { border-top: 1px solid var(--line); }
.markets th[scope=row] { font-weight: 600; font-size: 16px; white-space: nowrap; }
.markets .meter i { height: 12px; border-radius: 6px; }
.markets .meter span { font-size: 16px; font-weight: 600; }

.next { display: grid; grid-template-columns: minmax(0, 1fr); gap: 0; max-width: 820px; }
.next article { padding: 26px 0; }
.next article + article { border-top: 1px solid var(--line); }
.next h3 { margin: 0 0 8px; font-size: 21px; letter-spacing: -0.015em; }
.next p { margin: 0; color: var(--ink-2); }

footer { border-top: 1px solid var(--line); padding: 30px 0 56px; color: var(--ink-2); font-size: 14.5px; }
footer p { margin: 0 0 8px; max-width: 86ch; }

@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; gap: 36px; padding: 44px 0 44px; }
  .figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .figures div:nth-child(3) { padding-left: 0; border-left: 0; }
  .figures div:nth-child(n+3) { border-top: 1px solid var(--line); }
  .jobs { grid-template-columns: 1fr; }
  .stages { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  section.block { margin-bottom: 68px; }
  .figures { margin-bottom: 64px; }
}
@media (max-width: 520px) {
  .wrap { padding: 0 16px; }
  .top nav { display: none; }
  .split { padding: 22px 20px 20px; }
  .split .row b { font-size: 32px; }
  .figures dd { font-size: 26px; }
  .figures div { padding: 20px 14px 18px 0; }
  .figures div + div { padding-left: 14px; }
  .figures div:nth-child(3) { padding-left: 0; }
  .job { padding: 20px 18px 8px; }
  .stages { grid-template-columns: 1fr; gap: 18px; }
  .curve { gap: 8px; } .curve b { font-size: 18px; } .curve div { height: 150px; }
  .steps { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; } .steps b { font-size: 22px; }
  .callout { padding: 18px 18px; font-size: 16px; }
}
@media print { .top { position: static; } }
"""


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


PUBLIC_PAGE = {
    "title": "CRM retention practice: RFM, lifecycle and repeat purchases",
    "name": "CRM retention practice",
    "eyebrow": "Practice project on public data",
    "who": "customers of a UK online shop",
    "symbol": "£",
    "currency_note": "in pounds, the currency of the data",
    "lifecycle_note": "These are the same rules my Klaviyo win-back flow uses as its trigger.",
    "next_title": "What I would do with this in a real shop",
    "next_note": "These are recommendations, not results. The dataset has no email or advertising data, so nothing here has been tested on customers.",
    "footer": (f'<p>Data: Chen, D. (2019), <i>Online Retail II</i>, UCI Machine Learning Repository, CC BY 4.0. '
               f'<a href="{REPO}/blob/main/analisi-cv/data/REAL_DATA_PROVENANCE.md">Source and cleaning rules</a>.</p>\n'
               f'<p>275 orders cancelled in full on the same day (£472,927) are still counted here; without them Champions are 26.1% of customers and 71.5% of revenue. <a href="{REPO}/tree/main/prove">Details</a>.</p>\n'
               f'<p>All figures describe past orders in a public dataset. They are not forecasts and not client work. '
               f'<a href="{REPO}#readme">How this was built</a>.</p>'),
    "public": True,
    "app_link": "./",  # il foglio campagna-ordini
}
# Country names that read wrong without an article ("in the United Kingdom").
NEEDS_THE = {"United Kingdom", "United States", "Netherlands", "Czech Republic", "United Arab Emirates",
             "Channel Islands", "Philippines"}


def _place(country: str) -> str:
    return f"the {country}" if country in NEEDS_THE else country


def _money(v: float, sym: str = "£") -> str:
    if v >= 1e6:
        return f"{sym}{v / 1e6:.2f}M" if v < 1e7 else f"{sym}{v / 1e6:.1f}M"
    if v >= 1e4:
        return f"{sym}{v / 1e3:.0f}k"
    return f"{sym}{v:,.0f}"


def _month(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def _meter(share: float, label: str, soft: bool = False) -> str:
    """A bar with no background track: its length is `share` of the cell."""
    cls = ' class="soft"' if soft else ""
    return f'<div class="meter"><i{cls} style="width:{max(share, 0.01) * 100:.1f}%"></i><span class="num">{label}</span></div>'


def jobs_grid(segs: list[dict], total_rev: float, sym: str = "£") -> str:
    """RFM segments grouped by CRM job; bars are scaled to the largest share."""
    by_name = {s["segment"]: s for s in segs}
    groups = [(title, why, [by_name.pop(n) for n in names if n in by_name]) for title, why, names in JOBS]
    groups[-1][2].extend(by_name.values())
    top_c = max(s["customer_share"] for s in segs)
    top_r = max(s["revenue_gbp"] for s in segs) / total_rev
    out = []
    for i, (title, why, members) in enumerate(groups):
        if not members:
            continue
        rows = []
        for s in members:
            rev = s["revenue_gbp"] / total_rev
            rows.append(
                f'<div class="seg"><h4>{escape(s["segment"])}</h4><p class="flow">{escape(s["automation_flow"])}</p>'
                f'<div class="pair"><span>Customers</span>'
                f'{_meter(s["customer_share"] / top_c * 0.62, f"""{s["customers"]:,}<em>{s["customer_share"]:.0%}</em>""", soft=True)}'
                f'<span>Revenue</span>'
                f'{_meter(rev / top_r * 0.62, f"""{_money(s["revenue_gbp"], sym)}<em>{rev:.0%}</em>""")}</div></div>'
            )
        cls = "job lead-job" if i == 0 else "job"
        out.append(f'<article class="{cls}"><h3>{title}</h3><p>{why}</p>{"".join(rows)}</article>')
    return f'<div class="jobs">{"".join(out)}</div>'


def lifecycle(stages: list[dict], sym: str = "£") -> str:
    """One part-to-whole bar of customers by stage, with the rule and action under it."""
    mix = [STAGE_MIX[min(i, len(STAGE_MIX) - 1)] for i in range(len(stages))]
    colour = [f"color-mix(in srgb, var(--accent) {m}%, var(--rest))" for m in mix]
    bar = "".join(
        f'<i style="width:{s["share"] * 100:.1f}%;background:{c}" title="{escape(s["stage"])}: {s["customers"]:,} customers ({s["share"]:.0%})"></i>'
        for s, c in zip(stages, colour))
    cols = "".join(
        f'<div class="stage"><h3><i style="background:{c}"></i>{escape(s["stage"])}</h3>'
        f'<b class="num">{s["customers"]:,}</b>'
        f'<p>{s["share"]:.0%} of customers, {_money(s["revenue_gbp"], sym)} spent so far</p>'
        f'<p>{escape(s["rule"]).capitalize()}</p>'
        f'<p class="do">{escape(s["recommended_action"])}</p></div>'
        for s, c in zip(stages, colour))
    return f'<div class="stack" role="img" aria-label="Customers by lifecycle stage">{bar}</div><div class="stages">{cols}</div>'


def average_curve(co: dict) -> list[float]:
    """Customer-weighted repeat rate for months 1..k. The first cohort is left
    out: it also holds customers acquired before the data starts."""
    out = []
    for k in range(1, co["max_offset"] + 1):
        seen = [(c["retention"][k], c["customers"]) for c in co["cohorts"][1:] if c["retention"][k] is not None]
        if not seen:  # a young store: later months are not observed yet
            break
        out.append(sum(r * n for r, n in seen) / sum(n for _, n in seen))
    return out


def curve(avg: list[float]) -> str:
    top = max(avg) or 1  # a store where nobody has come back yet
    return '<div class="curve" role="img" aria-label="Average share of new customers who order again, by month">' + "".join(
        f'<div><b class="num">{x:.0%}</b><i style="height:{x / top * 110:.0f}px"></i><span>Month {k}</span></div>'
        for k, x in enumerate(avg, start=1)) + "</div>"


def second_order(t2: dict) -> str:
    """Share of new customers who have ordered again by each checkpoint day."""
    items = "".join(
        f'<li><span>By day {day}</span><b class="num">{share:.0%}</b><i style="width:{share * 100:.1f}%"></i></li>'
        for day, share in sorted(t2["share_back_by_day"].items(), key=lambda kv: int(kv[0])))  # JSON keys sort as text
    return (f'<div class="second" id="second-order"><h3>How long until the second order</h3>'
            f'<p class="note">Share of new customers who have ordered again by each day after their first purchase.</p>'
            f'<ol class="steps" aria-label="Share of new customers who ordered again, by day">{items}</ol>'
            f'<p class="aside">Half of the customers who come back within a year do it within '
            f'{t2["median_days_if_back"]:.0f} days. Counted on {t2["customers"]:,} customers who all had a full year '
            f'to return; a second invoice on the same day does not count as a second order.</p></div>')


def heatmap(co: dict) -> str:
    """Cohort x month offset. Month 0 (100% by construction) is left out; months
    the data does not fully cover are hatched, not shown as 0%."""
    cohorts, k_max = co["cohorts"], co["max_offset"]
    seen = [x for c in cohorts for x in c["retention"][1:] if x is not None]
    lo, hi = min(seen), max(seen)
    head = "".join(f'<th scope="col" class="n">M{k}</th>' for k in range(1, k_max + 1))
    body = []
    for c in cohorts:
        name = _month(c["cohort_month"])
        cells = []
        for k, x in enumerate(c["retention"][1:], start=1):
            if x is None:
                cells.append(f'<td class="na" title="{name} cohort, month {k}: not fully observed yet"></td>')
                continue
            step = round((x - lo) / (hi - lo) * (len(HEAT) - 1)) if hi > lo else 0
            hi_cls = " hi" if step >= FLIP else ""
            cells.append(f'<td class="c{hi_cls}" style="--p:{HEAT[step]}" '
                         f'title="{name} cohort, month {k}: {x:.1%} ordered again">{x:.0%}</td>')
        body.append(f'<tr><th scope="row">{name}</th><td class="n">{c["customers"]:,}</td>{"".join(cells)}</tr>')
    scale = (f'<div class="scale"><span>{lo:.0%}</span><span class="ramp"></span>'
             f'<span>{hi:.0%} ordered again</span><span><i class="na"></i> month not fully observed yet</span></div>')
    return (f'<div class="scroll"><table class="heat"><caption class="sr">Repeat-purchase rate by signup cohort and month'
            f'</caption><thead><tr><th scope="col">First order in</th><th scope="col" class="n">Customers</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{scale}')


def markets(ranked: list[dict], sym: str = "£") -> str:
    vmax = max(c["historical_clv_gbp"] for c in ranked)
    rows = "".join(
        f'<tr><th scope="row">{escape(c["country"])}</th>'
        f'<td>{_meter(c["historical_clv_gbp"] / vmax * 0.78, f"""{sym}{c["historical_clv_gbp"]:,.0f}""")}</td>'
        f'<td class="n">{c["customers"]:,}</td><td class="n">{c["orders_per_customer"]:.1f}</td>'
        f'<td class="n">{sym}{c["avg_order_value_gbp"]:,.0f}</td></tr>'
        for c in ranked)
    return ('<div class="scroll"><table class="markets"><caption class="sr">Revenue per customer by market</caption>'
            '<thead><tr><th scope="col">Market</th><th scope="col">Revenue per customer</th>'
            '<th scope="col" class="n">Customers</th><th scope="col" class="n">Orders each</th>'
            f'<th scope="col" class="n">Average order</th></tr></thead><tbody>{rows}</tbody></table></div>')


def build(crm: dict | None = None, life: dict | None = None, meta: dict | None = None) -> str:
    """The page for the UCI analysis by default, or for the data and texts given."""
    crm = crm if crm is not None else _load("analysis/crm_retention_metrics.json")
    life = life if life is not None else _load("analysis/crm_lifecycle_metrics.json")
    m = {**PUBLIC_PAGE, **(meta or {})}
    sym = m["symbol"]

    segs = crm["rfm"]["segments"]
    total_rev = sum(s["revenue_gbp"] for s in segs)
    top = max(segs, key=lambda s: s["revenue_gbp"])
    top_rev = top["revenue_gbp"] / total_rev
    customers = crm["rfm"]["total_customers"]
    clv = crm["clv_by_country"]
    ranked = clv["ranked"]
    best = ranked[0] if ranked else None
    # The comparison market: the one with the most customers (the UK in the UCI data).
    home = max(ranked, key=lambda c: c["customers"]) if ranked else None
    compare = best is not None and home is not best
    premium = best["historical_clv_gbp"] / home["historical_clv_gbp"] - 1 if compare else 0.0
    co = crm["cohort_retention"]
    avg = average_curve(co)
    first = _month(co["cohorts"][0]["cohort_month"])
    last_day = date.fromisoformat(crm["reference_date"]) - timedelta(days=1)
    span = f"{first} to {MONTHS[last_day.month - 1]} {last_day.year}"
    pooled = clv["small_n_pooled"]
    stages = life["stages"]
    risk = next((s for s in stages if s["stage"] == "At risk"), None)
    churned = next((s for s in stages if s["stage"] == "Churned"), None)
    t2 = crm["time_to_second_order"]
    has_t2 = bool(t2["customers"]) and t2["median_days_if_back"] is not None
    median_back = f'{t2["median_days_if_back"]:.0f}' if has_t2 else ""
    has_heat = any(x is not None for c in co["cohorts"] for x in c["retention"][1:])

    if m["public"]:
        head_meta = f"""<meta name="description" content="RFM segments, lifecycle stages and repeat purchases for {customers:,} {m["who"]}, on a public dataset (UCI Online Retail II).">
<meta property="og:title" content="CRM retention practice">
<meta property="og:description" content="{top["customer_share"]:.0%} of customers bring {top_rev:.0%} of revenue. RFM segments, lifecycle stages and repeat purchases on a public e-commerce dataset.">
<meta property="og:type" content="website">
<meta property="og:url" content="{PAGE}">
<meta property="og:image" content="{PAGE.rsplit("/", 1)[0]}/preview.png">
<meta name="twitter:card" content="summary_large_image">"""
        source = f'<a class="src" href="{REPO}">Source on GitHub</a>'
    else:
        head_meta = '<meta name="robots" content="noindex">'
        source = ""

    nav = ('<a href="#segments">Segments</a><a href="#lifecycle">Lifecycle</a><a href="#retention">Retention</a>'
           + ('<a href="#markets">Markets</a>' if ranked else "") + '<a href="#next">Next steps</a>')

    if risk:
        risk_tile = f'<dd class="num">{risk["customers"]:,}</dd><small>customers, {_money(risk["revenue_gbp"], sym)} spent so far</small>'
        callout = (f'<p class="callout"><b>{risk["customers"]:,} customers are at risk.</b> Their last order was 91 to 180 days '
                   f'ago and they have spent {_money(risk["revenue_gbp"], sym)} so far. That is the win-back list.</p>')
    else:
        risk_tile = '<dd class="num">0</dd><small>nobody last ordered 91 to 180 days ago</small>'
        callout = '<p class="callout"><b>Nobody is in the win-back window right now.</b> No customer last ordered 91 to 180 days ago.</p>'

    if avg:
        month_one = (f'About one new customer in {round(1 / avg[0])} orders again the following month.' if avg[0]
                     else 'No new customer has ordered again in the month after the first purchase yet.')
        retention = (f'{curve(avg)}\n<p class="aside">{month_one} The average leaves out the {first} group, which also '
                     f'contains customers acquired before the data starts.</p>')
    else:
        retention = '<p class="aside">Not enough history yet: the first month after the first purchase has not been observed for any group.</p>'
    retention += f"\n{second_order(t2)}" if has_t2 else ""
    if has_heat:
        retention += f'\n<details>\n<summary>Show all {len(co["cohorts"])} monthly groups</summary>\n{heatmap(co)}\n</details>'

    if ranked:
        versus = (f' A customer in {escape(best["country"])} has spent {premium:.0%} more than one in {escape(_place(home["country"]))}.'
                  if compare else "")
        markets_section = f"""<section class="block" id="markets">
<h2>What a customer is worth, by market</h2>
<p class="desc">Revenue per customer so far, for markets with at least {clv["min_customers"]} customers.{versus}</p>
{markets(ranked, sym)}
<p class="aside">{pooled["countries"]} smaller markets ({pooled["customers"]:,} customers in total) are too small to rank on their own.</p>
</section>

"""
    else:
        markets_section = ""

    steps = []
    if has_t2:
        steps.append(f"""<article><h3>Send the second-order email before day {median_back}</h3>
<p>Half of the new customers who come back within a year place their second order within {median_back} days, and by day 90, {t2["share_back_by_day"]["90"]:.0%} of new customers have already ordered again. A reminder without a discount fits before day {median_back}; the discount is better kept for the ones still missing after day 90.</p></article>""")
    if risk and churned:
        steps.append(f"""<article><h3>Start the win-back at day 91, not after a year</h3>
<p>Customers who stopped buying three to six months ago are a short list with a recent purchase history. The group silent for more than a year is {churned["customers"] / risk["customers"]:.1f} times larger, and the longer the silence, the harder the return.</p></article>""")
    steps.append("""<article><h3>Keep discounts for the customers who need a reason to return</h3>
<p>Send the offer to the win-back group only. The best customers get early access or a thank-you instead, and long-inactive, low-value customers get one cheap reminder before they leave the mailing list.</p></article>""")
    if compare:
        steps.append(f"""<article><h3>Judge the cost of a new customer by market</h3>
<p>If a customer in {escape(best["country"])} spends {premium:.0%} more over time, paying more to acquire one there can still make sense. One blended target for every country hides that.</p></article>""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{escape(m["title"])}</title>
{head_meta}
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<b>{escape(m["name"])}</b>
<nav aria-label="Sections">{nav}</nav>
{source}
</div></header>
<main class="wrap">

<div class="hero">
<div>
<p class="eyebrow">{escape(m["eyebrow"])}</p>
<h1>{top["customer_share"]:.0%} of customers bring {top_rev:.0%} of revenue.</h1>
<p class="lead">RFM segments, lifecycle stages and repeat purchases for {customers:,} {escape(m["who"])}. One CRM action per group.</p>
<a class="cta" href="#segments">See the segments</a>{f'<a class="cta alt" href="{m["app_link"]}">Campaign orders sheet</a>' if m.get("app_link") else ""}
</div>
<figure class="split">
<figcaption>{escape(top["segment"])} compared with everyone else</figcaption>
<div class="row"><span>Share of customers</span><b class="num">{top["customer_share"]:.0%}</b><div class="whole"><i style="width:{top["customer_share"] * 100:.1f}%"></i></div></div>
<div class="row"><span>Share of revenue</span><b class="num">{top_rev:.0%}</b><div class="whole"><i style="width:{top_rev * 100:.1f}%"></i></div></div>
<p class="key"><span><i style="background:var(--accent)"></i>{escape(top["segment"])}</span><span><i style="background:var(--rest)"></i>Everyone else</span></p>
</figure>
</div>

<dl class="figures">
<div><dt>Customers</dt><dd class="num">{customers:,}</dd><small>{span}</small></div>
<div><dt>Orders</dt><dd class="num">{crm["orders"]:,}</dd><small>returns and cancellations removed</small></div>
<div><dt>Revenue</dt><dd class="num">{_money(total_rev, sym)}</dd><small>{escape(m["currency_note"])}</small></div>
<div><dt>At risk right now</dt>{risk_tile}</div>
</dl>

<section class="block" id="segments">
<h2>Who gets which message</h2>
<p class="desc">RFM scores every customer on how recently, how often and how much they buy. Each segment then gets one flow, so nobody receives a discount they did not need.</p>
{jobs_grid(segs, total_rev, sym)}
</section>

<section class="block" id="lifecycle">
<h2>Where each customer is today</h2>
<p class="desc">Five stages based on the date of the last order. {escape(m["lifecycle_note"])}</p>
{lifecycle(stages, sym)}
{callout}
</section>

<section class="block" id="retention">
<h2>Do customers come back?</h2>
<p class="desc">Average share of new customers who order again in each of the six months after their first purchase.</p>
{retention}
</section>

{markets_section}<section class="block" id="next">
<h2>{escape(m["next_title"])}</h2>
<p class="desc">{escape(m["next_note"])}</p>
<div class="next">
{chr(10).join(steps)}
</div>
</section>

</main>
<footer><div class="wrap">
{m["footer"]}
</div></footer>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    (OUT.parent / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Wrote {OUT.name}")


if __name__ == "__main__":
    main()
