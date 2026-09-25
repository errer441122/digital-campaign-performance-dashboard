"""Build the public web dashboard (`docs/index.html`, served by GitHub Pages).

One self-contained HTML file: inline SVG charts, no JavaScript, no CDN, light
and dark mode. Every number is read from the JSON the analysis scripts write,
so the page cannot drift from `analysis/` and `reports/` — CI regenerates it
and fails if the committed copy differs.

Run after crm_retention.py, attribution.py, budget_reallocation.py and
analyze_ab_test.py. Pure standard library.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "index.html"
REPO = "https://github.com/errer441122/digital-campaign-performance-dashboard"

# Sequential blue ramp (light -> dark) for the retention heatmap.
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
        "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281"]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _money(v: float, cur: str) -> str:
    if v >= 1e6:
        return f"{cur} {v / 1e6:.1f}M"
    if v >= 1e4:
        return f"{cur} {v / 1e3:.0f}k"
    return f"{cur} {v:,.0f}"


def hbars(rows: list[tuple[str, float, str]], fmt, series: str = "--series-1") -> str:
    """Horizontal bars: (label, value, tooltip). Single series, value labels at the bar end."""
    label_w, bar_w, row_h = 150, 380, 30
    vmax = max(v for _, v, _ in rows) or 1
    h = row_h * len(rows)
    out = [f'<svg viewBox="0 0 {label_w + bar_w + 90} {h}" role="img" class="chart">']
    for i, (label, v, tip) in enumerate(rows):
        y = i * row_h
        w = max(2, v / vmax * bar_w)
        out.append(
            f'<g><title>{escape(tip)}</title>'
            f'<rect x="0" y="{y}" width="{label_w + bar_w + 90}" height="{row_h}" fill="transparent"/>'
            f'<text x="{label_w - 8}" y="{y + 19}" text-anchor="end" class="lbl">{escape(label)}</text>'
            f'<rect x="{label_w}" y="{y + 7}" width="{w:.1f}" height="16" rx="3" fill="var({series})"/>'
            f'<text x="{label_w + w + 6:.1f}" y="{y + 19}" class="val">{escape(fmt(v))}</text></g>'
        )
    out.append(f'<line x1="{label_w}" x2="{label_w}" y1="0" y2="{h}" class="axis"/></svg>')
    return "".join(out)


def paired_bars(rows: list[tuple[str, float, float]]) -> str:
    """Two series per category (last touch vs Markov), 2px gap between the pair."""
    label_w, bar_w, row_h = 150, 380, 44
    vmax = max(max(a, b) for _, a, b in rows) or 1
    h = row_h * len(rows)
    out = [f'<svg viewBox="0 0 {label_w + bar_w + 90} {h}" role="img" class="chart">']
    for i, (label, a, b) in enumerate(rows):
        y = i * row_h
        out.append(f'<text x="{label_w - 8}" y="{y + 25}" text-anchor="end" class="lbl">{escape(label)}</text>')
        for j, (v, s, name) in enumerate(((a, "--series-1", "Last touch"), (b, "--series-2", "Markov"))):
            w = max(2, v / vmax * bar_w)
            yy = y + 6 + j * 16
            out.append(
                f'<g><title>{escape(label)} — {name}: {v:,.0f} conversions</title>'
                f'<rect x="{label_w}" y="{yy}" width="{w:.1f}" height="14" rx="3" fill="var({s})"/>'
                f'<text x="{label_w + w + 6:.1f}" y="{yy + 11}" class="val">{v:,.0f}</text></g>'
            )
    out.append(f'<line x1="{label_w}" x2="{label_w}" y1="0" y2="{h}" class="axis"/></svg>')
    return "".join(out)


def heatmap(cohorts: list[dict], max_offset: int) -> str:
    """Cohort x month-offset table; M0 is 100% by construction so it is not coloured."""
    later = [x for c in cohorts for x in c["retention"][1:]]
    lo, hi = min(later), max(later)
    head = "".join(f"<th>M{k}</th>" for k in range(max_offset + 1))
    body = []
    for c in cohorts:
        cells = [f'<td class="m0">{c["retention"][0]:.0%}</td>']
        for k, x in enumerate(c["retention"][1:], start=1):
            step = round((x - lo) / (hi - lo) * (len(RAMP) - 1)) if hi > lo else 0
            ink = "#ffffff" if step >= 6 else "#0b0b0b"
            cells.append(
                f'<td style="background:{RAMP[step]};color:{ink}" '
                f'title="{c["cohort_month"]} cohort, month {k}: {x:.1%} placed another order">{x:.0%}</td>'
            )
        body.append(f'<tr><th scope="row">{c["cohort_month"]}</th><td class="n">{c["customers"]:,}</td>{"".join(cells)}</tr>')
    return (f'<div class="scroll"><table class="heat"><thead><tr><th>Cohort</th><th>Customers</th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def build() -> str:
    crm = _load("analysis/crm_retention_metrics.json")
    attr = _load("analysis/attribution_metrics.json")
    budget = _load("analysis/budget_reallocation_metrics.json")
    ab = _load("reports/ab_test_marketing_uplift.json")

    segs = crm["rfm"]["segments"]
    total_rev = sum(s["revenue_gbp"] for s in segs)
    top = max(segs, key=lambda s: s["revenue_gbp"])
    clv = crm["clv_by_country"]["ranked"]
    uk = next((c for c in clv if c["country"] == "United Kingdom"), clv[-1])
    best = clv[0]

    seg_chart = hbars(
        [(s["segment"], s["revenue_gbp"],
          f'{s["segment"]}: {s["customers"]:,} customers ({s["customer_share"]:.0%}), '
          f'GBP {s["revenue_gbp"]:,.0f} → {s["automation_flow"]}') for s in segs],
        lambda v: _money(v, "GBP"))
    seg_table = "".join(
        f'<tr><td>{escape(s["segment"])}</td><td class="n">{s["customers"]:,}</td>'
        f'<td class="n">{s["revenue_gbp"] / total_rev:.0%}</td><td>{escape(s["automation_flow"])}</td></tr>'
        for s in segs)
    clv_chart = hbars(
        [(c["country"], c["historical_clv_gbp"],
          f'{c["country"]}: {c["customers"]:,} customers, {c["orders_per_customer"]:.2f} orders each, '
          f'AOV GBP {c["avg_order_value_gbp"]:,.2f}') for c in clv],
        lambda v: f"GBP {v:,.0f}")

    comp = sorted(attr["comparison_table"], key=lambda r: r["markov_data_driven"], reverse=True)
    attr_chart = paired_bars([(r["channel"], r["last_touch"], r["markov_data_driven"]) for r in comp])
    shifts = attr["credit_shift_vs_last_touch"]
    loser, winner = shifts[0], shifts[-1]

    a, b = ab["variant_a"], ab["variant_b"]
    ci = ab["confidence_interval_95"]

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CRM & Campaign Dashboard</title>
<meta name="description" content="RFM, cohort retention and CLV on real Online Retail II data, plus attribution and A/B testing on disclosed simulated data.">
<style>
:root {{
  color-scheme: light;
  --page: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --ring: rgba(11,11,11,0.10);
  --series-1: #2a78d6; --series-2: #eb6834; --real: #006300; --sim: #8a5a00;
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --ring: rgba(255,255,255,0.10);
    --series-1: #3987e5; --series-2: #d95926; --real: #0ca30c; --sim: #fab219;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --ring: rgba(255,255,255,0.10);
  --series-1: #3987e5; --series-2: #d95926; --real: #0ca30c; --sim: #fab219;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 32px 16px 48px; }}
h1 {{ font-size: 28px; margin: 0 0 4px; letter-spacing: -0.01em; }}
h2 {{ font-size: 18px; margin: 0 0 4px; }}
.sub {{ color: var(--ink-2); margin: 0 0 24px; max-width: 70ch; }}
.tag {{ display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: .06em;
  text-transform: uppercase; padding: 2px 8px; border-radius: 999px; border: 1px solid currentColor; }}
.tag.real {{ color: var(--real); }} .tag.sim {{ color: var(--sim); }}
.kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.kpi, .card {{ background: var(--surface); border: 1px solid var(--ring); border-radius: 10px; padding: 16px 18px; }}
.kpi b {{ display: block; font-size: 28px; line-height: 1.2; margin: 4px 0 2px; }}
.kpi span {{ color: var(--ink-2); font-size: 13px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 16px; margin-bottom: 16px; }}
@media (max-width: 520px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.card p {{ color: var(--ink-2); margin: 4px 0 12px; font-size: 14px; }}
.card .take {{ color: var(--ink); margin-top: 12px; }}
.chart {{ width: 100%; height: auto; display: block; }}
.chart .lbl {{ fill: var(--ink-2); font-size: 13px; }}
.chart .val {{ fill: var(--ink); font-size: 12px; font-variant-numeric: tabular-nums; }}
.chart .axis {{ stroke: var(--axis); stroke-width: 1; }}
.legend {{ display: flex; gap: 16px; font-size: 13px; color: var(--ink-2); margin-bottom: 8px; }}
.legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid var(--grid); }}
td.n, .heat td {{ text-align: right; font-variant-numeric: tabular-nums; }}
.heat td {{ border: 2px solid var(--surface); }}
.heat td.m0 {{ color: var(--muted); }}
.scroll {{ overflow-x: auto; }}
details {{ margin-top: 12px; }} summary {{ cursor: pointer; color: var(--ink-2); font-size: 13px; }}
.ab {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
.ab b {{ display: block; font-size: 22px; }}
footer {{ color: var(--ink-2); font-size: 13px; margin-top: 32px; }}
a {{ color: var(--series-1); }}
</style>
</head>
<body>
<main>
<h1>CRM & Campaign Performance</h1>
<p class="sub">Which customers deserve which CRM action, and where should media budget move?
<span class="tag real">Real data</span> UCI Online Retail II, {crm["orders"]:,} orders, prices in GBP.
<span class="tag sim">Simulated</span> campaign, attribution and A/B sections, labelled on every card.</p>

<section class="kpis" aria-label="Headline figures (real data)">
  <div class="kpi"><span>Real customers analysed</span><b>{crm["rfm"]["total_customers"]:,}</b><span>{crm["orders"]:,} orders, 2009–2011</span></div>
  <div class="kpi"><span>{escape(top["segment"])} share of revenue</span><b>{top["revenue_gbp"] / total_rev:.0%}</b><span>from {top["customer_share"]:.0%} of customers</span></div>
  <div class="kpi"><span>Highest CLV market</span><b>GBP {best["historical_clv_gbp"]:,.0f}</b><span>{escape(best["country"])} vs GBP {uk["historical_clv_gbp"]:,.0f} {escape(uk["country"])}</span></div>
  <div class="kpi"><span>A/B test (simulated)</span><b>{ab["relative_uplift"]:+.0%}</b><span>conversion rate, p = {ab["p_value_two_tailed"]:.3f}</span></div>
</section>

<div class="grid">
<section class="card">
  <span class="tag real">Real</span>
  <h2>Revenue by RFM segment</h2>
  <p>Each segment maps to one automation flow. Hover a bar for the numbers.</p>
  {seg_chart}
  <p class="take">{escape(top["segment"])} are {top["customer_share"]:.0%} of customers and {top["revenue_gbp"] / total_rev:.0%} of revenue: protect them with a VIP flow before spending on acquisition.</p>
  <details><summary>Table view</summary><table><thead><tr><th>Segment</th><th>Customers</th><th>Revenue share</th><th>Automation flow</th></tr></thead><tbody>{seg_table}</tbody></table></details>
</section>
<section class="card">
  <span class="tag real">Real</span>
  <h2>Historical CLV by country</h2>
  <p>Revenue per customer, markets with at least {crm["clv_by_country"]["min_customers"]} customers.</p>
  {clv_chart}
  <p class="take">A customer in {escape(best["country"])} is worth {best["historical_clv_gbp"] / uk["historical_clv_gbp"] - 1:.0%} more over their lifetime than one in {escape(uk["country"])}: judge acquisition cost by market, not by first order.</p>
</section>
</div>

<section class="card" style="margin-bottom:16px">
  <span class="tag real">Real</span>
  <h2>Cohort retention</h2>
  <p>Share of each signup-month cohort that ordered again k months later. Darker = higher retention. Later cohorts are right-censored.</p>
  {heatmap(crm["cohort_retention"]["cohorts"][:13], crm["cohort_retention"]["max_offset"])}
</section>

<div class="grid">
<section class="card">
  <span class="tag sim">Simulated</span>
  <h2>Last-touch vs data-driven attribution</h2>
  <div class="legend"><span><i style="background:var(--series-1)"></i>Last touch</span><span><i style="background:var(--series-2)"></i>Markov removal effect</span></div>
  {attr_chart}
  <p class="take">Last touch over-credits {escape(loser["channel"])} ({loser["delta_conversions"]:+,.0f} conversions under Markov) and under-credits {escape(winner["channel"])} ({winner["delta_conversions"]:+,.0f}).</p>
</section>
<section class="card">
  <span class="tag sim">Simulated</span>
  <h2>Landing-page A/B test</h2>
  <div class="ab">
    <div><span>A · control</span><b>{a["conversion_rate"]:.2%}</b></div>
    <div><span>B · short form</span><b>{b["conversion_rate"]:.2%}</b></div>
    <div><span>Uplift (95% CI)</span><b>{ab["absolute_uplift"] * 100:+.2f} pp</b><span>[{ci["lower"] * 100:+.2f}, {ci["upper"] * 100:+.2f}] pp</span></div>
  </div>
  <p class="take"><b>{escape(ab["recommendation"])}.</b> Two-proportion z = {ab["z_score"]:.2f}, p = {ab["p_value_two_tailed"]:.4f}; P(B beats A) = {ab["bayesian_probability_b_beats_a"]:.1%}.</p>
  <h2 style="margin-top:20px">Budget move</h2>
  <p class="take">{escape(budget["recommendation"])}</p>
</section>
</div>

<footer>
Generated by <code>src/build_web_dashboard.py</code> from the committed analysis outputs; every figure is checked again with pandas, DuckDB and statsmodels in
<a href="{REPO}/blob/main/notebooks/cross_check.ipynb">the cross-check notebook</a>.
Real data: Chen, D. (2019) <i>Online Retail II</i>, UCI ML Repository, CC BY 4.0 — <a href="{REPO}/blob/main/data/REAL_DATA_PROVENANCE.md">provenance</a>.
Simulated data is disclosed in the <a href="{REPO}/blob/main/data/DATA_CARD.md">data card</a>. <a href="{REPO}">Source code</a>.
</footer>
</main>
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
