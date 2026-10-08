"""Build the public web dashboard (`docs/index.html`, served by GitHub Pages).

One self-contained HTML file: HTML/CSS charts, no JavaScript, no CDN, no web
fonts, light and dark mode, readable on a phone. Every number is read from
the JSON the analysis scripts write, so the page cannot drift from
`analysis/` and `reports/` — CI regenerates it and fails if the committed
copy differs.

Run after crm_retention.py, attribution.py, budget_reallocation.py and
analyze_ab_test.py. Pure standard library.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "index.html"
REPO = "https://github.com/errer441122/digital-campaign-performance-dashboard"
PAGE = "https://errer441122.github.io/digital-campaign-performance-dashboard/"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

# Sequential blue ramp (light -> dark) for the retention heatmap. Cells from
# DARK_FROM onwards take white text.
RAMP = ["#eaf2fd", "#d4e4fb", "#b9d3f7", "#98bef1", "#75a6ea", "#538ce0",
        "#3672cf", "#235ab5", "#184795"]
DARK_FROM = 5

CSS = """
:root {
  color-scheme: light;
  --page: #f5f6f8; --surface: #ffffff; --ink: #0f172a; --ink-2: #475569; --muted: #64748b;
  --line: #e2e8f0; --track: #edf1f6; --shadow: 0 1px 2px rgba(15,23,42,.06);
  --accent: #2563eb; --accent-2: #ea7a2c; --accent-3: #0f9488; --real: #15803d; --sim: #a16207; --hatch: #cbd5e1;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --page: #0b1020; --surface: #121a2b; --ink: #eef2f7; --ink-2: #c3ccd9; --muted: #93a0b4;
    --line: #23304a; --track: #1d2840; --shadow: none;
    --accent: #5b9cf6; --accent-2: #f39a55; --accent-3: #2dc4b0; --real: #4ade80; --sim: #f5c04a; --hatch: #33415c;
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 64px; }
body { margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
a { color: var(--accent); }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.wrap { max-width: 1160px; margin: 0 auto; padding: 0 20px; }
header.top { position: sticky; top: 0; z-index: 2; background: var(--page); background: color-mix(in srgb, var(--page) 88%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); }
header.top .wrap { display: flex; align-items: center; gap: 20px; height: 52px; overflow-x: auto; white-space: nowrap; }
header.top b { font-size: 14px; }
header.top nav { display: flex; gap: 16px; font-size: 14px; }
header.top nav a { color: var(--ink-2); text-decoration: none; }
header.top nav a:hover { color: var(--ink); }
header.top .src { margin-left: auto; font-size: 14px; }
.hero { padding: 36px 0 8px; }
h1 { font-size: clamp(26px, 4vw, 36px); line-height: 1.15; margin: 0 0 10px; letter-spacing: -0.02em; }
.lead { color: var(--ink-2); max-width: 74ch; margin: 0 0 14px; font-size: 16px; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 22px; }
.chip { font-size: 13px; color: var(--ink-2); background: var(--surface); border: 1px solid var(--line);
  border-radius: 999px; padding: 4px 12px; }
.tag { display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
  padding: 2px 8px; border-radius: 999px; border: 1px solid currentColor; vertical-align: 2px; }
.tag.real { color: var(--real); } .tag.sim { color: var(--sim); }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.card, .kpi { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; box-shadow: var(--shadow); }
.kpi { padding: 16px 18px; }
.kpi span { display: block; color: var(--ink-2); font-size: 13px; }
.kpi b { display: block; font-size: 30px; line-height: 1.15; margin: 6px 0 4px; letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums; }
.kpi small { color: var(--muted); font-size: 13px; }
.takeaways { padding: 18px 22px; margin-bottom: 30px; }
.takeaways h2 { font-size: 15px; margin: 0 0 8px; }
.takeaways ol { margin: 0; padding-left: 20px; display: grid; gap: 6px; }
.takeaways li::marker { color: var(--muted); font-weight: 600; }
section.block { margin: 0 0 34px; }
.block > h2 { font-size: 21px; margin: 0 0 4px; letter-spacing: -0.01em; }
.block > p.desc { color: var(--ink-2); margin: 0 0 14px; max-width: 80ch; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.card { padding: 20px 22px; min-width: 0; }
.card h3 { font-size: 16px; margin: 0 0 4px; }
.card .note { color: var(--ink-2); font-size: 14px; margin: 0 0 14px; }
.card .take { margin: 14px 0 0; padding-top: 12px; border-top: 1px solid var(--line); font-size: 14px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { padding: 7px 8px; text-align: left; vertical-align: middle; }
thead th { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em;
  border-bottom: 1px solid var(--line); }
tbody tr + tr > * { border-top: 1px solid var(--line); }
th[scope=row] { font-weight: 600; }
th[scope=row] small { display: block; font-weight: 400; color: var(--muted); font-size: 12.5px; }
.n, .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.cell { display: flex; align-items: center; gap: 10px; }
.bar { flex: 1; min-width: 36px; height: 10px; border-radius: 5px; background: var(--track); overflow: hidden; }
.bar i { display: block; height: 100%; border-radius: 5px; background: var(--accent); }
.bar.alt i { background: var(--accent-2); }
.bar.rev i { background: var(--accent-3); }
.num em { font-style: normal; color: var(--muted); margin-left: 4px; }
.cell .num { min-width: 6.5em; }
.pair { display: grid; grid-template-columns: minmax(0, 1fr) 3.4em; gap: 4px 10px; align-items: center; }
.legend { display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: var(--ink-2); margin: 0 0 8px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.delta { font-weight: 600; }
.scroll { overflow-x: auto; }
.heat { font-size: 13px; }
.heat th, .heat td { padding: 5px 6px; }
.heat td.c { text-align: center; color: #0f1b2d; font-variant-numeric: tabular-nums; border: 2px solid var(--surface); }
.heat td.c.dk { color: #ffffff; }
.heat td.na { text-align: center; color: var(--muted); border: 2px solid var(--surface);
  background: repeating-linear-gradient(135deg, transparent 0 5px, var(--hatch) 5px 6px); }
.scale { display: flex; align-items: center; gap: 10px; font-size: 12.5px; color: var(--muted); margin-top: 10px; flex-wrap: wrap; }
.scale .ramp { width: 160px; height: 10px; border-radius: 5px; }
.scale .na { display: inline-block; width: 22px; height: 12px; border-radius: 3px; vertical-align: -2px;
  background: repeating-linear-gradient(135deg, transparent 0 4px, var(--hatch) 4px 5px); border: 1px solid var(--line); }
.variants { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.variant { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; }
.variant span { display: block; font-size: 13px; color: var(--ink-2); }
.variant b { display: block; font-size: 24px; font-variant-numeric: tabular-nums; margin: 2px 0 6px; }
.variant small { color: var(--muted); }
.ci { position: relative; height: 30px; margin: 6px 0 2px; }
.ci::before { content: ""; position: absolute; left: 0; right: 0; top: 14px; height: 2px; background: var(--track); }
.ci .range { position: absolute; top: 9px; height: 12px; border-radius: 6px; background: color-mix(in srgb, var(--accent) 35%, transparent); }
.ci .pt { position: absolute; top: 6px; width: 4px; height: 18px; margin-left: -2px; border-radius: 2px; background: var(--accent); }
.ci .zero { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; background: var(--ink-2); }
.ci-lbl { position: relative; height: 16px; font-size: 12.5px; color: var(--muted); }
.ci-lbl span { position: absolute; transform: translateX(-50%); }
.stats { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 13.5px; color: var(--ink-2); margin: 12px 0 0; }
.move { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; font-size: 18px; font-weight: 600; margin: 4px 0 10px; }
.move .arrow { color: var(--muted); }
.move .amt { color: var(--accent); font-variant-numeric: tabular-nums; }
footer { color: var(--ink-2); font-size: 13.5px; border-top: 1px solid var(--line); padding: 22px 0 40px; }
footer p { margin: 0 0 8px; max-width: 95ch; }
@media (max-width: 900px) { .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); } .grid { grid-template-columns: 1fr; } }
@media (max-width: 520px) {
  .wrap { padding: 0 14px; } .kpi b { font-size: 24px; } .card { padding: 16px; }
  .variants { grid-template-columns: 1fr; }
  .cell { flex-direction: column; align-items: stretch; gap: 4px; } .cell .num { text-align: left; min-width: 0; }
  .cell .bar { flex: none; }
  th, td { padding: 7px 6px; }
}
@media print { header.top { position: static; } .card, .kpi { box-shadow: none; break-inside: avoid; } }
"""


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _money(v: float, sym: str) -> str:
    if v >= 1e6:
        return f"{sym}{v / 1e6:.1f}M"
    if v >= 1e4:
        return f"{sym}{v / 1e3:.0f}k"
    return f"{sym}{v:,.0f}"


def _signed(v: float, spec: str) -> str:
    """Explicit sign with a true minus (−) instead of a hyphen."""
    return format(v, "+" + spec).replace("-", "−")


def _month(ym: str) -> str:
    y, m = ym.split("-")
    return f"{MONTHS[int(m) - 1]} {y}"


def _bar(share: float, cls: str = "") -> str:
    """A track with a fill of `share` (0..1) of its width."""
    return f'<span class="bar {cls}"><i style="width:{max(share, 0.005) * 100:.1f}%"></i></span>'


def rfm_table(segs: list[dict], total_rev: float) -> str:
    rows = []
    for s in segs:
        rev = s["revenue_gbp"] / total_rev
        rows.append(
            f'<tr><th scope="row">{escape(s["segment"])}<small>{escape(s["automation_flow"])}</small></th>'
            f'<td><div class="cell">{_bar(s["customer_share"])}<span class="num">{s["customers"]:,}'
            f'<em>{s["customer_share"]:.0%}</em></span></div></td>'
            f'<td><div class="cell">{_bar(rev, "rev")}<span class="num">{_money(s["revenue_gbp"], "£")}'
            f'<em>{rev:.0%}</em></span></div></td></tr>'
        )
    return ('<div class="scroll"><table><caption class="sr">Customers and revenue by RFM segment</caption>'
            '<thead><tr><th scope="col">Segment → flow</th><th scope="col">Customers</th>'
            f'<th scope="col">Revenue</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def clv_table(ranked: list[dict]) -> str:
    vmax = max(c["historical_clv_gbp"] for c in ranked)
    rows = "".join(
        f'<tr><th scope="row">{escape(c["country"])}</th>'
        f'<td><div class="cell">{_bar(c["historical_clv_gbp"] / vmax)}'
        f'<span class="num">£{c["historical_clv_gbp"]:,.0f}</span></div></td>'
        f'<td class="n">{c["customers"]:,}</td><td class="n">{c["orders_per_customer"]:.1f}</td>'
        f'<td class="n">£{c["avg_order_value_gbp"]:,.0f}</td></tr>'
        for c in ranked)
    return ('<div class="scroll"><table><caption class="sr">Historical customer lifetime value by country</caption>'
            '<thead><tr><th scope="col">Market</th><th scope="col">Revenue per customer</th>'
            '<th scope="col" class="n">Customers</th><th scope="col" class="n">Orders each</th>'
            f'<th scope="col" class="n">Avg order</th></tr></thead><tbody>{rows}</tbody></table></div>')


def heatmap(co: dict) -> str:
    """Cohort x month offset. M0 (100% by construction) is left out; months
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
                cells.append(f'<td class="na" title="{name} cohort, month {k}: not fully observed yet">–</td>')
                continue
            step = round((x - lo) / (hi - lo) * (len(RAMP) - 1)) if hi > lo else 0
            dark = " dk" if step >= DARK_FROM else ""
            cells.append(f'<td class="c{dark}" style="background:{RAMP[step]}" '
                         f'title="{name} cohort, month {k}: {x:.1%} ordered again">{x:.0%}</td>')
        body.append(f'<tr><th scope="row">{name}</th><td class="n">{c["customers"]:,}</td>{"".join(cells)}</tr>')
    scale = (f'<div class="scale"><span>{lo:.0%}</span>'
             f'<span class="ramp" style="background:linear-gradient(90deg,{",".join(RAMP)})"></span>'
             f'<span>{hi:.0%} ordered again</span><span><i class="na"></i> month not fully observed yet</span></div>')
    return (f'<div class="scroll"><table class="heat"><caption class="sr">Repeat-purchase rate by signup cohort and month'
            f'</caption><thead><tr><th scope="col">Cohort</th><th scope="col" class="n">Customers</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{scale}')


def attribution_table(rows: list[dict], shifts: list[dict]) -> str:
    vmax = max(max(r["last_touch"], r["markov_data_driven"]) for r in rows)
    delta = {s["channel"]: s["delta_conversions"] for s in shifts}
    out = []
    for r in sorted(rows, key=lambda r: r["markov_data_driven"], reverse=True):
        d = delta[r["channel"]]
        out.append(
            f'<tr><th scope="row">{escape(r["channel"])}</th><td><div class="pair">'
            f'{_bar(r["last_touch"] / vmax)}<span class="num">{r["last_touch"]:,.0f}</span>'
            f'{_bar(r["markov_data_driven"] / vmax, "alt")}<span class="num">{r["markov_data_driven"]:,.0f}</span>'
            f'</div></td><td class="n delta">{"▲" if d > 0 else "▼"} {_signed(d, ",.0f")}</td></tr>'
        )
    return ('<div class="legend"><span><i style="background:var(--accent)"></i>Last touch</span>'
            '<span><i style="background:var(--accent-2)"></i>Markov removal effect</span></div>'
            '<div class="scroll"><table><caption class="sr">Conversions credited per channel, last touch vs Markov</caption>'
            '<thead><tr><th scope="col">Channel</th><th scope="col">Conversions credited</th>'
            f'<th scope="col" class="n">Shift</th></tr></thead><tbody>{"".join(out)}</tbody></table></div>')


def ab_card(ab: dict) -> str:
    a, b = ab["variant_a"], ab["variant_b"]
    ci = ab["confidence_interval_95"]
    lo, hi, mid = ci["lower"] * 100, ci["upper"] * 100, ab["absolute_uplift"] * 100
    d_lo, d_hi = min(lo, 0.0), max(hi, 0.0)
    pad = (d_hi - d_lo) * 0.25
    d_lo, d_hi = d_lo - pad, d_hi + pad

    def x(v: float) -> str:
        return f"{(v - d_lo) / (d_hi - d_lo) * 100:.1f}%"

    rmax = max(a["conversion_rate"], b["conversion_rate"])
    tiles = "".join(
        f'<div class="variant"><span>{tag} · {escape(v["label"])}</span><b>{v["conversion_rate"]:.2%}</b>'
        f'{_bar(v["conversion_rate"] / rmax, cls)}<small>{v["conversions"]:,} of {v["sessions"]:,} sessions</small></div>'
        for tag, v, cls in (("A", a, ""), ("B", b, "alt")))
    side = "entirely above zero" if lo > 0 else ("entirely below zero" if hi < 0 else "crosses zero")
    return (f'<div class="variants">{tiles}</div>'
            f'<div class="ci" role="img" aria-label="Uplift {mid:+.2f} percentage points, 95% CI {lo:+.2f} to {hi:+.2f}">'
            f'<span class="range" style="left:{x(lo)};width:calc({x(hi)} - {x(lo)})"></span>'
            f'<span class="zero" style="left:{x(0.0)}"></span><span class="pt" style="left:{x(mid)}"></span></div>'
            f'<div class="ci-lbl"><span style="left:{x(0.0)}">0</span></div>'
            f'<p class="note" style="margin:8px 0 0">Uplift <b>{_signed(mid, ".2f")} pp</b>, 95% CI '
            f'{_signed(lo, ".2f")} to {_signed(hi, ".2f")} pp: {side}.</p>'
            f'<p class="stats"><span>z = {ab["z_score"]:.2f}</span><span>p = {ab["p_value_two_tailed"]:.4f}</span>'
            f'<span>P(B beats A) = {ab["bayesian_probability_b_beats_a"]:.1%}</span>'
            f'<span>relative uplift {_signed(ab["relative_uplift"] * 100, ".0f")}%</span>'
            f'<span>revenue per session €{a["revenue_per_session"]:.2f} → €{b["revenue_per_session"]:.2f}</span></p>'
            f'<p class="take"><b>{escape(ab["recommendation"])}.</b> Guardrails after rollout: mobile conversion rate, '
            f'revenue per session, refunds.</p>')


def budget_card(bd: dict) -> str:
    if not bd["donor"]:
        return f'<p class="take">{escape(bd["recommendation"])}</p>'
    return (f'<div class="move"><span>{escape(bd["donor"])}</span><span class="arrow">→</span>'
            f'<span>{escape(bd["recipient"])}</span><span class="amt">€{bd["move_eur"]:,.0f}</span></div>'
            f'<p class="note">Expected under the saturation model: <b>+{bd["expected_incremental_conversions"]:,.0f} '
            f'conversions</b> and <b>+€{bd["expected_incremental_revenue_eur"]:,.0f}</b> revenue on '
            f'€{bd["total_paid_spend_eur"]:,.0f} of paid spend. The move is capped at '
            f'{bd["reallocation_cap_pct"]:.0%} of paid spend and {bd["donor_drawdown_cap_pct"]:.0%} of the donor budget; '
            f'Email is held because its volume is list-driven, not spend-driven.</p>'
            f'<p class="take">Directional: each curve is fitted through one observed point, so this sizes the next '
            f'spend test rather than replacing it.</p>')


def build() -> str:
    crm = _load("analysis/crm_retention_metrics.json")
    attr = _load("analysis/attribution_metrics.json")
    budget = _load("analysis/budget_reallocation_metrics.json")
    ab = _load("reports/ab_test_marketing_uplift.json")

    segs = crm["rfm"]["segments"]
    total_rev = sum(s["revenue_gbp"] for s in segs)
    top = max(segs, key=lambda s: s["revenue_gbp"])
    top_rev = top["revenue_gbp"] / total_rev
    clv = crm["clv_by_country"]
    best = clv["ranked"][0]
    uk = next((c for c in clv["ranked"] if c["country"] == "United Kingdom"), clv["ranked"][-1])
    premium = best["historical_clv_gbp"] / uk["historical_clv_gbp"] - 1
    co = crm["cohort_retention"]
    first = _month(co["cohorts"][0]["cohort_month"])
    last_day = date.fromisoformat(crm["reference_date"]) - timedelta(days=1)
    span = f"{first} – {MONTHS[last_day.month - 1]} {last_day.year}"
    shifts = attr["credit_shift_vs_last_touch"]
    loser, winner = shifts[0], shifts[-1]
    pooled = clv["small_n_pooled"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>CRM & Campaign Performance Dashboard</title>
<meta name="description" content="RFM segments, cohort retention and customer lifetime value on {crm["rfm"]["total_customers"]:,} real customers (UCI Online Retail II), plus attribution, A/B test and budget model on disclosed simulated data.">
<meta property="og:title" content="CRM & Campaign Performance Dashboard">
<meta property="og:description" content="{top["customer_share"]:.0%} of customers bring {top_rev:.0%} of revenue: RFM, retention and CLV on real e-commerce data, plus attribution and A/B testing.">
<meta property="og:type" content="website">
<meta property="og:url" content="{PAGE}">
<meta property="og:image" content="{PAGE}preview.png">
<meta name="twitter:card" content="summary_large_image">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<b>CRM & Campaign Dashboard</b>
<nav aria-label="Sections"><a href="#customers">Customers</a><a href="#retention">Retention</a><a href="#markets">Markets</a><a href="#media">Media &amp; tests</a></nav>
<a class="src" href="{REPO}">Source ↗</a>
</div></header>
<main class="wrap">
<div class="hero">
<h1>Which customers deserve which CRM action, and where should media budget move?</h1>
<p class="lead">RFM segmentation, cohort retention and lifetime value on a real UK online retailer, followed by
attribution, an A/B test and a budget model on simulated campaign data. Every card says which kind of data it uses.</p>
<div class="chips"><span class="chip"><span class="tag real">Real</span> UCI Online Retail II · {crm["orders"]:,} orders · {span} · GBP</span>
<span class="chip"><span class="tag sim">Simulated</span> campaigns, journeys and A/B test · EUR</span>
<span class="chip">Cross-checked with pandas, DuckDB and statsmodels</span></div>
</div>

<section class="kpis" aria-label="Headline figures, real data">
<div class="kpi"><span>Customers analysed</span><b>{crm["rfm"]["total_customers"]:,}</b><small>{crm["orders"]:,} orders over two years</small></div>
<div class="kpi"><span>Revenue</span><b>{_money(total_rev, "£")}</b><small>identified customers, excl. returns and cancellations</small></div>
<div class="kpi"><span>Revenue from {escape(top["segment"])}</span><b>{top_rev:.0%}</b><small>from {top["customer_share"]:.0%} of customers</small></div>
<div class="kpi"><span>Revenue per customer, {escape(best["country"])}</span><b>£{best["historical_clv_gbp"]:,.0f}</b><small>{_signed(premium * 100, ".0f")}% vs {escape(uk["country"])} (£{uk["historical_clv_gbp"]:,.0f})</small></div>
</section>

<section class="card takeaways" aria-label="Takeaways">
<h2>What the numbers say</h2>
<ol>
<li>Protect <b>{escape(top["segment"])}</b> before buying reach: {top["customer_share"]:.0%} of customers, {top_rev:.0%} of revenue ({escape(top["automation_flow"])}).</li>
<li>Judge acquisition cost by market: a customer in {escape(best["country"])} is worth <b>{premium:.0%} more</b> over their lifetime than one in {escape(uk["country"])}.</li>
<li>Do not fund media on last click: it under-credits {escape(winner["channel"])} by <b>{winner["delta_conversions"]:,.0f} conversions</b> and over-credits {escape(loser["channel"])} by {-loser["delta_conversions"]:,.0f} <span class="tag sim">Simulated</span></li>
</ol>
</section>

<section class="block" id="customers">
<h2>Customers <span class="tag real">Real data</span></h2>
<p class="desc">Recency, frequency and monetary quintiles put every customer into one segment, and each segment into one automation flow.</p>
<div class="card">
<h3>RFM segments: who they are and what they bring</h3>
<p class="note">Bars show each segment's share of all customers and of all revenue.</p>
{rfm_table(segs, total_rev)}
<p class="take">{escape(top["segment"])} are {top["customer_share"]:.0%} of customers and {top_rev:.0%} of revenue. Next by revenue: {escape(segs[1]["segment"])} ({escape(segs[1]["automation_flow"])}) and {escape(segs[2]["segment"])} ({escape(segs[2]["automation_flow"])}).</p>
</div>
</section>

<section class="block" id="retention">
<h2>Retention <span class="tag real">Real data</span></h2>
<p class="desc">Share of each signup-month cohort that ordered again k months later.</p>
<div class="card">
<h3>Repeat purchase by cohort</h3>
<p class="note">The data ends on {last_day.day} {MONTHS[last_day.month - 1]} {last_day.year}, so months after {_month(co["last_complete_month"])} are hatched (not observed yet) instead of shown as 0%. The {first} cohort also contains customers acquired before the data starts, which is why it retains best.</p>
{heatmap(co)}
</div>
</section>

<section class="block" id="markets">
<h2>Markets <span class="tag real">Real data</span></h2>
<p class="desc">Historical revenue per customer for markets with at least {clv["min_customers"]} customers; {pooled["countries"]} smaller markets ({pooled["customers"]:,} customers) are pooled, not ranked.</p>
<div class="card">
<h3>Lifetime value by market</h3>
<p class="note">Revenue per customer = orders per customer × average order value.</p>
{clv_table(clv["ranked"])}
<p class="take">A customer in {escape(best["country"])} is worth {premium:.0%} more than one in {escape(uk["country"])}: a higher acquisition cost can still pay back there.</p>
</div>
</section>

<section class="block" id="media">
<h2>Media &amp; tests <span class="tag sim">Simulated data</span></h2>
<p class="desc">No public dataset carries ad spend, user journeys and experiments together, so this part runs on a disclosed, deterministic simulation.</p>
<div class="grid">
<div class="card">
<h3>Last touch vs data-driven attribution</h3>
<p class="note">Conversions credited to each channel by last click and by a Markov removal-effect model.</p>
{attribution_table(attr["comparison_table"], shifts)}
<p class="take">Last touch over-credits {escape(loser["channel"])} ({_signed(loser["delta_conversions"], ",.0f")}) and under-credits {escape(winner["channel"])} ({_signed(winner["delta_conversions"], ",.0f")}): upper-funnel channels assist conversions that the closer gets credit for.</p>
</div>
<div class="card">
<h3>Landing-page A/B test</h3>
<p class="note">Conversion rate per variant and the uplift's 95% confidence interval.</p>
{ab_card(ab)}
</div>
</div>
<div class="card" style="margin-top:16px">
<h3>Budget move</h3>
<p class="note">Attribution-driven and saturation-aware: a square-root response curve per channel.</p>
{budget_card(budget)}
</div>
</section>
</main>
<footer><div class="wrap">
<p>Generated by <code>src/build_web_dashboard.py</code> from the committed analysis outputs; every headline figure is recomputed with pandas, DuckDB and statsmodels in <a href="{REPO}/blob/main/notebooks/cross_check.ipynb">the cross-check notebook</a>.</p>
<p>Real data: Chen, D. (2019) <i>Online Retail II</i>, UCI Machine Learning Repository, CC BY 4.0 — <a href="{REPO}/blob/main/data/REAL_DATA_PROVENANCE.md">provenance and cleaning rules</a>. Simulated data is disclosed in the <a href="{REPO}/blob/main/data/DATA_CARD.md">data card</a>. Relationships are observational, not causal.</p>
</div></footer>
</body>
</html>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8", newline="\n")
    (OUT.parent / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
