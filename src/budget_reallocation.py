"""Budget-reallocation recommendation driven by data-driven attribution.

Pairs paid spend (from the campaign CSV) with Markov-attributed conversions
(from `attribution.py`) to propose a single bounded reallocation between
**acquisition** paid channels.

Two judgement calls a recruiter should notice:

1. Diminishing returns are modelled explicitly. Each channel's response is
   a square-root saturation curve `conv = k * spend ** 0.5` fitted to its
   observed (spend, attributed-conversions) point. The recommended move is
   the one that maximises *net* conversions under those curves inside a
   capped band — not a naive "highest average ratio wins" rule, which would
   over-fund a near-saturated channel.

2. Email is excluded as a *recipient*. Its attributed efficiency is high
   because email volume scales with list quality and send strategy, not
   with media budget — pouring acquisition money into it does not buy more
   sends. It is reported and protected, not reallocated into.

Pure standard library; consumes `analysis/attribution_metrics.json`.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_PATH = ROOT / "data" / "campaign_performance_sample.csv"
ATTRIBUTION_METRICS = ROOT / "analysis" / "attribution_metrics.json"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "budget_reallocation.md"
METRICS_PATH = ANALYSIS_DIR / "budget_reallocation_metrics.json"

PAID_CHANNELS = ("Paid Search", "Paid Social", "Email", "Display")
# Email volume is not media-spend-elastic, so it cannot receive acquisition
# budget at its observed efficiency. It is protected, not a reallocation
# recipient.
ACQUISITION_CHANNELS = ("Paid Search", "Paid Social", "Display")
REALLOCATION_CAP = 0.15  # max fraction of total paid spend that may move
DONOR_DRAWDOWN_CAP = 0.5  # never remove more than half a channel's own budget


def paid_spend() -> dict[str, float]:
    spend: dict[str, float] = defaultdict(float)
    with CAMPAIGN_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["channel"] in PAID_CHANNELS:
                spend[row["channel"]] += float(row["cost_eur"])
    return {c: round(spend[c], 2) for c in PAID_CHANNELS}


def attributed() -> dict[str, dict[str, float]]:
    data = json.loads(ATTRIBUTION_METRICS.read_text(encoding="utf-8"))
    credit = data["markov"]["credit"]
    return {
        c: {
            "conversions": credit[c]["conversions"],
            "revenue_eur": credit[c]["revenue_eur"],
        }
        for c in PAID_CHANNELS
    }


def _curve_k(conv: float, spend: float) -> float:
    """Fit conv = k * spend ** 0.5 through the observed point."""
    return conv / (spend ** 0.5) if spend > 0 else 0.0


def _conv_at(k: float, spend: float) -> float:
    return k * (spend ** 0.5) if spend > 0 else 0.0


def run() -> dict[str, object]:
    spend = paid_spend()
    attrib = attributed()
    total_spend = round(sum(spend.values()), 2)

    rows = []
    for c in PAID_CHANNELS:
        s = spend[c]
        conv = attrib[c]["conversions"]
        rev = attrib[c]["revenue_eur"]
        rows.append(
            {
                "channel": c,
                "spend_eur": s,
                "attr_conversions": round(conv, 2),
                "attr_revenue_eur": round(rev, 2),
                "attr_conv_per_1k_eur": round(conv / s * 1000, 3) if s else 0.0,
                "attr_roas": round(rev / s, 3) if s else 0.0,
                "marginal_conv_per_1k_eur": round(0.5 * conv / s * 1000, 3) if s else 0.0,
                "reallocatable": c in ACQUISITION_CHANNELS,
            }
        )
    rows.sort(key=lambda r: r["marginal_conv_per_1k_eur"], reverse=True)

    acq = {r["channel"]: r for r in rows if r["reallocatable"]}
    k = {c: _curve_k(attrib[c]["conversions"], spend[c]) for c in ACQUISITION_CHANNELS}
    rev_per_conv = {
        c: (attrib[c]["revenue_eur"] / attrib[c]["conversions"])
        if attrib[c]["conversions"]
        else 0.0
        for c in ACQUISITION_CHANNELS
    }

    # Donor = lowest marginal efficiency, recipient = highest, among
    # acquisition channels. Then grid-search the move size that maximises
    # net conversions under the saturation curves, inside the cap.
    ranked = sorted(ACQUISITION_CHANNELS, key=lambda c: 0.5 * attrib[c]["conversions"] / spend[c])
    donor, recipient = ranked[0], ranked[-1]
    max_move = round(
        min(total_spend * REALLOCATION_CAP, spend[donor] * DONOR_DRAWDOWN_CAP), 2
    )

    best = {"move": 0.0, "net_conv": 0.0, "net_rev": 0.0}
    steps = 200
    for i in range(1, steps + 1):
        move = max_move * i / steps
        lost = _conv_at(k[donor], spend[donor]) - _conv_at(k[donor], spend[donor] - move)
        gained = _conv_at(k[recipient], spend[recipient] + move) - _conv_at(
            k[recipient], spend[recipient]
        )
        net_conv = gained - lost
        if net_conv > best["net_conv"]:
            net_rev = gained * rev_per_conv[recipient] - lost * rev_per_conv[donor]
            best = {"move": round(move, 2), "net_conv": net_conv, "net_rev": net_rev}

    has_move = best["net_conv"] > 0.5
    recommendation = (
        f"Shift EUR {best['move']:,.0f} from {donor} to {recipient} "
        f"(bounded at {REALLOCATION_CAP:.0%} of paid spend / "
        f"{DONOR_DRAWDOWN_CAP:.0%} of the donor budget). Protect {donor}'s "
        f"remaining budget and hold Email — its volume is list-driven, not "
        f"spend-driven."
        if has_move
        else "No reallocation improves net conversions inside the safe band: "
        "acquisition channels are already close to equal marginal "
        "efficiency. Hold the current split and revisit after the next test."
    )

    return {
        "total_paid_spend_eur": total_spend,
        "reallocation_cap_pct": REALLOCATION_CAP,
        "donor_drawdown_cap_pct": DONOR_DRAWDOWN_CAP,
        "response_model": "conv = k * spend ** 0.5 (per-channel sqrt saturation)",
        "channels": rows,
        "email_excluded_reason": (
            "Email attributed efficiency is structurally high because email "
            "volume scales with list quality and send strategy, not media "
            "spend; it is protected, not a reallocation recipient."
        ),
        "donor": donor if has_move else None,
        "recipient": recipient if has_move else None,
        "move_eur": best["move"] if has_move else 0.0,
        "expected_incremental_conversions": round(best["net_conv"], 1) if has_move else 0.0,
        "expected_incremental_revenue_eur": round(best["net_rev"], 2) if has_move else 0.0,
        "recommendation": recommendation,
        "assumption": (
            "Square-root saturation fitted through one observed point per "
            "channel; it captures diminishing returns directionally but is "
            "not an estimated response curve from a spend-variation test."
        ),
    }


def _md(r: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# Budget Reallocation (attribution-driven, saturation-aware)\n")
    L.append(
        f"Total paid spend EUR {r['total_paid_spend_eur']:,.0f}. Channels are "
        f"ranked by **marginal** Markov-attributed conversions per EUR 1,000 "
        f"under a square-root saturation curve — not last-click average ROAS, "
        f"which would over-fund a near-saturated channel.\n"
    )
    L.append("| Channel | Spend | Attr. conv. | Attr. ROAS | Marginal conv / EUR 1k | Reallocatable |")
    L.append("| --- | ---: | ---: | ---: | ---: | :--: |")
    for e in r["channels"]:
        flag = "yes" if e["reallocatable"] else "held"
        L.append(
            f"| {e['channel']} | EUR {e['spend_eur']:,.0f} | "
            f"{e['attr_conversions']:,.0f} | {e['attr_roas']:.2f} | "
            f"{e['marginal_conv_per_1k_eur']:.2f} | {flag} |"
        )
    L.append("")
    L.append(f"_{r['email_excluded_reason']}_\n")
    L.append("## Recommendation\n")
    L.append(f"**{r['recommendation']}**\n")
    if r["donor"]:
        L.append(
            f"Expected effect under the saturation model: "
            f"**+{r['expected_incremental_conversions']:,.0f} net conversions** "
            f"and **EUR {r['expected_incremental_revenue_eur']:,.0f} net "
            f"revenue** (move EUR {r['move_eur']:,.0f}, "
            f"{r['donor']} → {r['recipient']}). The figure is modest by "
            f"construction: both curves flatten, so the safe band is small.\n"
        )
    L.append("## Assumption & limit\n")
    L.append(r["assumption"] + "\n")
    L.append("## Boundary\n")
    L.append(
        "Simulated portfolio data only. A directional planning figure under "
        "a stated saturation assumption, not a guaranteed outcome or a "
        "causal experiment result.\n"
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
