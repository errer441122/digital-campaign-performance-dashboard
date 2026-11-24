"""Try the check on campaigns that never happened, on real orders.

The public wholesale data (36,969 orders, 5,878 accounts) contains no campaign, so the right
answer is known: no effect. Six campaigns back to back, 60 days each, so no order is counted twice.
Three questions:

1. What would a normal campaign report have claimed?
2. How often is the check fooled? (300 made-up campaigns for each start date)
3. How big must a real effect be for the check to see it? (an effect is added by hand)

Writes docs/campaign_check.json (read by the page) and analysis/campaign_check.md.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

import campaign_check as cc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "online_retail_orders.csv"
STARTS = [date(2010, 12, 1) + timedelta(cc.WINDOW * i) for i in range(6)]
NAMES, PLANTED_NAMES = 300, 100
EFFECTS, LEAVE_OUTS = (0.10, 0.15, 0.20), (5, 3, 2)


def lift(account: str, campaign: str, share: float, effect: float) -> bool:
    """Whether a made-up effect turns this non-ordering account into an ordering one."""
    u = int(hashlib.sha256(f"effect|{campaign}|{account}".encode()).hexdigest()[:12], 16) / 16 ** 12
    return u < effect / (1 - share)


def run() -> dict:
    accounts = cc.load_orders(DATA)
    months, fooled, planted = [], {n: [0, 0, 0] for n in LEAVE_OUTS}, {}
    for start in STARTS:
        late = cc.late_accounts(accounts, start)
        came = {k: cc.ordered(accounts[k]["rows"], start, cc.WINDOW) for k in late}
        share = sum(o for o, _ in came.values()) / len(late)
        plan = cc.make_plan(accounts, start, "backtest")
        m = cc.measure(plan["rows"], accounts)
        months.append({"start": start.isoformat(), "late": len(late), "contact": m["groups"]["contact"],
                       "left_out": m["groups"]["left_out"], "difference": m["difference"],
                       "low": m["low"], "high": m["high"], "verdict": m["verdict"]})
        for n in LEAVE_OUTS:
            for i in range(NAMES):
                name = f"fake {i}"
                g = cc.draw(accounts, late, start, name, n)
                c = [k for k in late if g[k] == "contact"]
                o = [k for k in late if g[k] == "left_out"]
                xc, xo = sum(came[k][0] for k in c), sum(came[k][0] for k in o)
                _, low, high = cc.difference(xc, len(c), xo, len(o))
                fooled[n][0] += 1
                fooled[n][1] += low > 0
                fooled[n][2] += high < 0
                if i < PLANTED_NAMES:
                    for e in EFFECTS:
                        x = xc + sum(not came[k][0] and lift(k, name, share, e) for k in c)
                        _, low, _ = cc.difference(x, len(c), xo, len(o))
                        p = planted.setdefault((n, e), [0, 0])
                        p[0] += 1
                        p[1] += low > 0
    pool = {g: {f: round(sum(m[g][f] for m in months), 2) for f in ("accounts", "ordered", "revenue")}
            for g in ("contact", "left_out")}
    for g in pool.values():
        g["share"] = g["ordered"] / g["accounts"]
    diff, low, high = cc.difference(pool["contact"]["ordered"], pool["contact"]["accounts"],
                                    pool["left_out"]["ordered"], pool["left_out"]["accounts"])
    orders = sum(len(a["rows"]) for a in accounts.values())
    return {
        "data": {"orders": orders, "accounts": len(accounts), "currency": "GBP"},
        "rule": {"window": cc.WINDOW, "leave_out": cc.LEAVE_OUT, "late_factor": cc.LATE_FACTOR},
        "campaigns": months,
        "pooled": {**pool, "difference": diff, "low": low, "high": high, "verdict": cc.verdict(low, high)},
        "fooled": [{"leave_out": n, "campaigns": t, "called_worked": w, "called_hurt": h}
                   for n, (t, w, h) in fooled.items()],
        "seen": [{"leave_out": n, "effect": e, "campaigns": t, "seen": s} for (n, e), (t, s) in planted.items()],
    }


def rounded(x):
    if isinstance(x, float):
        return round(x, 4)
    if isinstance(x, dict):
        return {k: rounded(v) for k, v in x.items()}
    return [rounded(v) for v in x] if isinstance(x, list) else x


def markdown(r: dict) -> str:
    c, o = r["pooled"]["contact"], r["pooled"]["left_out"]
    out = [
        "# Six campaigns that never happened", "",
        f"Real orders: {r['data']['orders']:,} from {r['data']['accounts']:,} accounts of a UK wholesaler "
        "(UCI *Online Retail II*). No campaign is in the data, so the right answer is: no effect.", "",
        f"Every {r['rule']['window']} days for a year, the accounts that were late against their own ordering rhythm were \"contacted\" "
        f"(nothing was sent), one in {r['rule']['leave_out']} was left out, and the orders of the next "
        f"{r['rule']['window']} days were counted.", "",
        "| Start | Contacted | Ordered | Share | Their orders | Left out | Ordered | Share | Difference, points (margin) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    line = lambda label, m: (  # noqa: E731
        f"| {label} | {m['contact']['accounts']:,} | {m['contact']['ordered']:,} | {m['contact']['share']:.0%} | "
        f"GBP {m['contact']['revenue']:,.0f} | {m['left_out']['accounts']:,} | {m['left_out']['ordered']:,} | "
        f"{m['left_out']['share']:.0%} | {cc.points(m['difference'])} ({cc.points(m['low'])} to {cc.points(m['high'])}) |")
    out += [line(m["start"], m) for m in r["campaigns"]] + [line("**All six**", r["pooled"])]
    out += ["", f"**What a campaign report would have claimed:** {c['ordered']:,} times an account came back, "
            f"GBP {c['revenue']:,.0f} of orders. **What the left-out accounts say:** {o['share']:.0%} of them "
            f"ordered too, against {c['share']:.0%}. The campaigns did nothing, because there were none.", "",
            "## How often the check is fooled", "",
            f"{NAMES} made-up campaign names for each of the six dates, so {NAMES * len(STARTS):,} different draws.", "",
            "| Left out | Campaigns | Called \"worked\" | Called \"hurt\" |", "| --- | ---: | ---: | ---: |"]
    out += [f"| 1 in {f['leave_out']} | {f['campaigns']:,} | {f['called_worked']} ({f['called_worked'] / f['campaigns']:.1%}) | "
            f"{f['called_hurt']} ({f['called_hurt'] / f['campaigns']:.1%}) |" for f in r["fooled"]]
    out += ["", "With a 95% margin, about 2.5% on each side is expected.", "",
            "## How big an effect it can see", "",
            "An effect is added by hand: some contacted accounts that did not order are counted as if they had. "
            "Share of campaigns in which the check says \"worked\":", "",
            "| Left out | +10 points | +15 points | +20 points |", "| --- | ---: | ---: | ---: |"]
    for n in LEAVE_OUTS:
        cells = [s for s in r["seen"] if s["leave_out"] == n]
        out.append(f"| 1 in {n} | " + " | ".join(f"{int(100 * s['seen'] / s['campaigns'] + 0.5)}%" for s in cells) + " |")
    out += ["", "On lists of 200 to 700 accounts, a small effect stays invisible. The plan says so before the campaign starts.", ""]
    return "\n".join(out)


def main() -> None:
    r = rounded(run())
    (ROOT / "docs" / "campaign_check.json").write_text(json.dumps(r, indent=1) + "\n", encoding="utf-8", newline="\n")
    (ROOT / "analysis" / "campaign_check.md").write_text(markdown(r), encoding="utf-8", newline="\n")
    print(json.dumps(r["pooled"], indent=1))


if __name__ == "__main__":
    main()
