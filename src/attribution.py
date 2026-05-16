"""Multi-touch attribution on the simulated conversion-path sample.

Rule-based models (first-touch, last-touch, linear, position-based 40/20/40)
plus a data-driven **Markov removal-effect** model that solves an absorbing
Markov chain analytically (no third-party linear-algebra dependency).

The point a hiring manager should take away: last-click systematically
over-credits closing channels (Paid Search, Email) and starves upper-funnel
assists (Display, Paid Social). The Markov model re-weights credit by each
channel's *causal contribution to reaching a conversion*, which changes the
ranking — and therefore the budget decision (see `budget_reallocation.py`).

Pure standard library.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS_PATH = ROOT / "data" / "conversion_paths_sample.csv"
ANALYSIS_DIR = ROOT / "analysis"
REPORT_PATH = ANALYSIS_DIR / "attribution.md"
METRICS_PATH = ANALYSIS_DIR / "attribution_metrics.json"

START, CONVERSION, NULL = "(start)", "(conversion)", "(null)"


def read_paths() -> list[dict[str, object]]:
    with PATHS_PATH.open(newline="", encoding="utf-8") as handle:
        rows = []
        for r in csv.DictReader(handle):
            rows.append(
                {
                    "path": [c.strip() for c in r["path"].split(">")],
                    "journeys": int(r["journeys"]),
                    "conversions": int(r["conversions"]),
                    "revenue_eur": float(r["revenue_eur"]),
                }
            )
        return rows


def channels(rows: list[dict[str, object]]) -> list[str]:
    seen: dict[str, None] = {}
    for r in rows:
        for c in r["path"]:
            seen.setdefault(c, None)
    return sorted(seen)


# ----------------------------- rule-based -------------------------------- #

def rule_based(rows: list[dict[str, object]]) -> dict[str, dict[str, dict[str, float]]]:
    models = ("first_touch", "last_touch", "linear", "position_based")
    credit = {m: defaultdict(lambda: {"conversions": 0.0, "revenue_eur": 0.0}) for m in models}

    for r in rows:
        path, conv, rev = r["path"], r["conversions"], r["revenue_eur"]
        if conv <= 0:
            continue
        n = len(path)

        def add(model: str, weights: list[float]) -> None:
            for ch, w in zip(path, weights):
                credit[model][ch]["conversions"] += conv * w
                credit[model][ch]["revenue_eur"] += rev * w

        add("first_touch", [1.0] + [0.0] * (n - 1))
        add("last_touch", [0.0] * (n - 1) + [1.0])
        add("linear", [1.0 / n] * n)

        if n == 1:
            pos = [1.0]
        elif n == 2:
            pos = [0.5, 0.5]
        else:
            mid = [0.2 / (n - 2)] * (n - 2)
            pos = [0.4] + mid + [0.4]
        add("position_based", pos)

    return {m: {k: dict(v) for k, v in d.items()} for m, d in credit.items()}


# --------------------------- data-driven Markov -------------------------- #

def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for a small dense system."""
    n = len(vector)
    a = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        piv = a[col][col]
        if abs(piv) < 1e-15:
            continue
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col] / piv
            for c in range(col, n + 1):
                a[r][c] -= factor * a[col][c]
    return [a[i][n] / a[i][i] if abs(a[i][i]) > 1e-15 else 0.0 for i in range(n)]


def _transition_counts(rows: list[dict[str, object]]) -> dict[tuple[str, str], float]:
    t: dict[tuple[str, str], float] = defaultdict(float)
    for r in rows:
        path, journeys, conv = r["path"], r["journeys"], r["conversions"]
        non_conv = max(0, journeys - conv)
        # converting journeys: start -> ... -> last -> conversion
        seq_c = [START] + path + [CONVERSION]
        for i in range(len(seq_c) - 1):
            t[(seq_c[i], seq_c[i + 1])] += conv
        # non-converting journeys: start -> ... -> last -> null
        seq_n = [START] + path + [NULL]
        for i in range(len(seq_n) - 1):
            t[(seq_n[i], seq_n[i + 1])] += non_conv
    return t


def _conversion_probability(
    trans: dict[tuple[str, str], float], chans: list[str], removed: str | None = None
) -> float:
    """P(reach conversion from start) in the absorbing Markov chain.

    Removing a channel = routing every transition into it straight to NULL.
    """
    transient = [START] + [c for c in chans if c != removed]
    idx = {s: i for i, s in enumerate(transient)}
    n = len(transient)

    out_total: dict[str, float] = defaultdict(float)
    for (src, _dst), w in trans.items():
        if src in idx:
            out_total[src] += w

    # (I - Q) x = r_conv  ->  x[start] = P(conversion)
    a = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    b = [0.0] * n
    for (src, dst), w in trans.items():
        if src not in idx:
            continue
        total = out_total[src]
        if total <= 0:
            continue
        p = w / total
        target = NULL if dst == removed else dst
        if target == CONVERSION:
            b[idx[src]] += p
        elif target == NULL:
            continue
        elif target in idx:
            a[idx[src]][idx[target]] -= p
        # transition into the removed channel -> treated as NULL (drop)
    x = _solve(a, b)
    return max(0.0, x[idx[START]])


def markov(rows: list[dict[str, object]]) -> dict[str, object]:
    chans = channels(rows)
    trans = _transition_counts(rows)
    base_p = _conversion_probability(trans, chans)
    total_conv = sum(r["conversions"] for r in rows)
    total_rev = sum(r["revenue_eur"] for r in rows)

    removal: dict[str, float] = {}
    for ch in chans:
        p_without = _conversion_probability(trans, chans, removed=ch)
        removal[ch] = 0.0 if base_p <= 0 else max(0.0, 1.0 - p_without / base_p)

    denom = sum(removal.values()) or 1.0
    credit = {
        ch: {
            "removal_effect": round(removal[ch], 6),
            "weight": round(removal[ch] / denom, 6),
            "conversions": round(total_conv * removal[ch] / denom, 2),
            "revenue_eur": round(total_rev * removal[ch] / denom, 2),
        }
        for ch in chans
    }
    return {
        "base_conversion_probability": round(base_p, 6),
        "total_conversions": total_conv,
        "total_revenue_eur": round(total_rev, 2),
        "credit": credit,
    }


# ------------------------------- assembly -------------------------------- #

def run() -> dict[str, object]:
    rows = read_paths()
    chans = channels(rows)
    rb = rule_based(rows)
    mk = markov(rows)

    table = []
    for ch in chans:
        row = {"channel": ch}
        for m in ("first_touch", "last_touch", "linear", "position_based"):
            row[m] = round(rb[m].get(ch, {"conversions": 0.0})["conversions"], 2)
        row["markov_data_driven"] = mk["credit"][ch]["conversions"]
        table.append(row)

    last = {r["channel"]: r["last_touch"] for r in table}
    mkv = {r["channel"]: r["markov_data_driven"] for r in table}
    last_rank = sorted(last, key=lambda c: last[c], reverse=True)
    mkv_rank = sorted(mkv, key=lambda c: mkv[c], reverse=True)

    shifts = []
    for ch in chans:
        delta = mkv[ch] - last[ch]
        shifts.append(
            {
                "channel": ch,
                "last_touch": last[ch],
                "markov": mkv[ch],
                "delta_conversions": round(delta, 2),
                "delta_pct_vs_last_touch": round(delta / last[ch], 4) if last[ch] else None,
            }
        )
    shifts.sort(key=lambda r: r["delta_conversions"])

    return {
        "channels": chans,
        "rows": len(rows),
        "rule_based": {
            m: {ch: {k: round(v, 4) for k, v in rb[m][ch].items()} for ch in rb[m]}
            for m in rb
        },
        "markov": mk,
        "comparison_table": table,
        "last_touch_ranking": last_rank,
        "markov_ranking": mkv_rank,
        "credit_shift_vs_last_touch": shifts,
    }


def _md(result: dict[str, object]) -> str:
    L: list[str] = []
    L.append("# Multi-Touch Attribution\n")
    L.append(
        f"Sample: {result['rows']} distinct conversion paths across "
        f"{len(result['channels'])} channels "
        f"({', '.join(result['channels'])}).\n"
    )

    L.append("## Conversion credit by model\n")
    L.append("| Channel | First touch | Last touch | Linear | Position 40/20/40 | Markov (data-driven) |")
    L.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for r in sorted(result["comparison_table"], key=lambda x: x["markov_data_driven"], reverse=True):
        L.append(
            f"| {r['channel']} | {r['first_touch']:,.0f} | {r['last_touch']:,.0f} | "
            f"{r['linear']:,.0f} | {r['position_based']:,.0f} | "
            f"{r['markov_data_driven']:,.0f} |"
        )
    L.append("")

    mk = result["markov"]
    L.append(
        f"Markov base conversion probability **{mk['base_conversion_probability']:.4f}**; "
        f"credit is allocated by each channel's normalised *removal effect* "
        f"(the relative drop in conversion probability when that channel is "
        f"deleted from every path).\n"
    )

    L.append("## Last-touch vs data-driven: where credit moves\n")
    L.append("| Channel | Last touch | Markov | Δ conv. | Δ vs last touch |")
    L.append("| --- | ---: | ---: | ---: | ---: |")
    for s in result["credit_shift_vs_last_touch"]:
        pct = "—" if s["delta_pct_vs_last_touch"] is None else f"{s['delta_pct_vs_last_touch']:+.0%}"
        L.append(
            f"| {s['channel']} | {s['last_touch']:,.0f} | {s['markov']:,.0f} | "
            f"{s['delta_conversions']:+,.0f} | {pct} |"
        )
    L.append("")
    losers = [s["channel"] for s in result["credit_shift_vs_last_touch"] if s["delta_conversions"] < 0][:2]
    winners = [s["channel"] for s in reversed(result["credit_shift_vs_last_touch"]) if s["delta_conversions"] > 0][:2]
    L.append(
        f"Last-touch over-credits the closing channels "
        f"({', '.join(losers) or 'none'}) and under-credits the assisting "
        f"channels ({', '.join(winners) or 'none'}). Optimising budget on "
        f"last-touch alone would defund the upper-funnel touchpoints that "
        f"*cause* the closes — the reallocation model uses the data-driven "
        f"credit instead.\n"
    )

    L.append("## Boundary\n")
    L.append(
        "Simulated portfolio paths only; no real ad-platform, GA4, CRM or "
        "user-level data. The Markov model assumes a first-order chain and "
        "treats observed path frequencies as transition probabilities — it "
        "quantifies contribution under that model, it is not a causal "
        "experiment.\n"
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
