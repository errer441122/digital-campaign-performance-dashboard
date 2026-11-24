"""Did the campaign bring orders, or would those accounts have ordered anyway?

In B2B the order comes in by phone, by email or through a sales rep and ends up in the
ERP. The email tool never sees it. Two steps, two ERP exports:

    python src/campaign_check.py plan    --orders orders.csv --campaign "Spring catalogue"
    python src/campaign_check.py measure --plan plan/plan.csv --orders orders_later.csv

plan     takes your list of accounts, or proposes the ones that are late against their own
         ordering rhythm; leaves one in five out of the campaign; says in advance how big an
         effect a list of that size can show
measure  when the window is over, compares the two groups on the orders they placed

No model, no AI: a draw, a count and a margin of error. Pure standard library.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import statistics
from datetime import date, timedelta
from pathlib import Path

from erp_export import FileProblem, parse_day, parse_number, read_rows, read_text, to_csv

WINDOW = 60          # days after the start in which an order counts
LEAVE_OUT = 5        # one account in five is left out
MIN_ORDERS = 4       # order days needed before an account has a rhythm
MIN_SILENCE = 14     # days; nobody is late after a weekend
LATE_FACTOR = 2      # late = silent for more than twice its usual gap
MAX_SILENCE = 365    # after a year it is a lost account, not a late one
MIN_HISTORY = 30     # accounts needed to say how many come back by themselves

PLAN_HEADER = ["account", "name", "rep", "group", "last_order", "usual_gap_days", "silent_days",
               "last_12_months", "campaign", "start", "window_days"]
LIST_HEADER = ["account", "name", "rep", "last_order", "usual_gap_days", "silent_days", "last_12_months"]


def load_orders(path: Path) -> dict[str, dict]:
    """account -> {"name", "rep", "rows": [(day, amount)]}. Order lines are fine too."""
    rows, fields = read_rows(path, ("account", "date"))
    accounts: dict[str, dict] = {}
    for line, r in enumerate(rows, start=2):
        if not r["account"]:
            continue
        try:
            day = parse_day(r["date"])
            amount = parse_number(r["amount"]) if "amount" in fields else 1.0
        except FileProblem as e:
            raise FileProblem(f"line {line}: {e}") from None
        if day is None:
            continue
        a = accounts.setdefault(r["account"], {"name": "", "rep": "", "rows": []})
        a["name"], a["rep"] = r.get("name") or a["name"], r.get("rep") or a["rep"]
        a["rows"].append((day, amount))
    if not accounts:
        raise FileProblem("no rows with an account and a date")
    return accounts


def order_days(rows: list, until: date) -> list[date]:
    """Days with an order up to `until`. Credit notes (negative amounts) are not orders."""
    return sorted({d for d, amount in rows if d <= until and amount > 0})


def ordered(rows: list, start: date, window: int) -> tuple[bool, float]:
    """Did the account order in the window after `start`, and for how much (net of credit notes)?"""
    inside = [amount for d, amount in rows if start < d <= start + timedelta(window)]
    return any(x > 0 for x in inside), sum(inside)


def rhythm(rows: list, as_of: date) -> dict | None:
    """How often the account orders and how long it has been silent; None if it has no rhythm yet."""
    days = order_days(rows, as_of)
    if len(days) < MIN_ORDERS:
        return None
    return {"last": days[-1], "silent": (as_of - days[-1]).days,
            "gap": statistics.median((b - a).days for a, b in zip(days, days[1:]))}


def is_late(r: dict | None) -> bool:
    return bool(r) and MIN_SILENCE <= r["silent"] <= MAX_SILENCE and r["silent"] > LATE_FACTOR * r["gap"]


def late_accounts(accounts: dict, as_of: date) -> list[str]:
    return [k for k, a in accounts.items() if is_late(rhythm(a["rows"], as_of))]


def size(rows: list, as_of: date) -> float:
    """What the account bought in the last 12 months."""
    return sum(x for d, x in rows if as_of - timedelta(365) < d <= as_of)


def draw(accounts: dict, chosen: list[str], as_of: date, campaign: str,
         leave_out: int = LEAVE_OUT, key: int = 0) -> dict[str, str]:
    """account -> "contact", "left_out" or "key".

    The accounts are sorted from the biggest and taken `leave_out` at a time; in each handful
    one is left out, so big and small accounts end up in both groups. Which one is decided by
    a hash of the campaign and the account: nobody can choose, and the draw can be repeated.
    The `key` biggest accounts, and the few that do not fill a handful, are always contacted
    and never counted.
    """
    by_size = sorted(chosen, key=lambda k: (-size(accounts[k]["rows"], as_of), k))
    always = key + (len(by_size) - key) % leave_out
    group = {k: "key" for k in by_size[:always]}
    rest = by_size[always:]
    for i in range(0, len(rest), leave_out):
        handful = rest[i:i + leave_out]
        out = min(handful, key=lambda k: hashlib.sha256(f"{campaign}|{k}".encode()).hexdigest())
        group.update({k: "left_out" if k == out else "contact" for k in handful})
    return group


def smallest_visible(n_contact: int, n_out: int, base: float) -> float:
    """Smallest difference a test of this size shows 8 times out of 10 (share of accounts)."""
    return 2.8 * math.sqrt(base * (1 - base) * (1 / n_contact + 1 / n_out))


def usual_return(accounts: dict, as_of: date, window: int, chosen: list[str] | None) -> float | None:
    """Share of accounts like these that ordered in a past window, with no campaign planned here."""
    before = as_of - timedelta(window)
    pool = chosen if chosen is not None else late_accounts(accounts, before)
    if len(pool) < MIN_HISTORY:
        return None
    return sum(ordered(accounts[k]["rows"], before, window)[0] for k in pool) / len(pool)


def make_plan(accounts: dict, as_of: date, campaign: str, window: int = WINDOW, leave_out: int = LEAVE_OUT,
              key: int = 0, chosen: list[str] | None = None) -> dict:
    unknown = [k for k in chosen or [] if k not in accounts]
    picked = [k for k in dict.fromkeys(chosen) if k in accounts] if chosen is not None \
        else late_accounts(accounts, as_of)
    if leave_out < 2:
        raise FileProblem("leave out one account in 2, 3, 4 or 5")
    if len(picked) - key < 2 * leave_out:
        raise FileProblem(f"only {len(picked)} accounts to work with: too few to leave some out")
    group = draw(accounts, picked, as_of, campaign, leave_out, key)
    base = usual_return(accounts, as_of, window, picked if chosen is not None else None)
    testable = len(picked) - key
    sizes = []
    for n in (5, 3, 2):
        out = testable // n
        if out:
            sizes.append({"leave_out": n, "left_out": out, "contact": out * (n - 1),
                          "smallest_visible": smallest_visible(out * (n - 1), out, 0.5 if base is None else base)})
    rows = []
    for k, g in group.items():
        a, r = accounts[k], rhythm(accounts[k]["rows"], as_of)
        days = order_days(a["rows"], as_of)
        rows.append({"account": k, "name": a["name"], "rep": a["rep"], "group": g,
                     "last_order": days[-1].isoformat() if days else "",
                     "usual_gap_days": round(r["gap"]) if r else "",
                     "silent_days": (as_of - days[-1]).days if days else "",
                     "last_12_months": round(size(a["rows"], as_of), 2),
                     "campaign": campaign, "start": as_of.isoformat(), "window_days": window})
    return {"rows": rows, "base": base, "sizes": sizes, "unknown": unknown, "start": as_of, "window": window,
            "leave_out": leave_out, "ends": as_of + timedelta(window),
            "count": {g: sum(r["group"] == g for r in rows) for g in ("contact", "left_out", "key")}}


def plan_files(plan: dict) -> dict[str, str]:
    cells = lambda r, header: [r[h] for h in header]  # noqa: E731
    contact = [r for r in plan["rows"] if r["group"] != "left_out"]
    left = [r for r in plan["rows"] if r["group"] == "left_out"]
    return {"contact.csv": to_csv(LIST_HEADER, [cells(r, LIST_HEADER) for r in contact]),
            "left_out.csv": to_csv(LIST_HEADER, [cells(r, LIST_HEADER) for r in left]),
            "plan.csv": to_csv(PLAN_HEADER, [cells(r, PLAN_HEADER) for r in plan["rows"]])}


def read_plan(path: Path) -> list[dict]:
    text = read_text(path)
    reader = csv.DictReader(io.StringIO(text, newline=""),
                            delimiter=max(",;\t", key=text.split("\n", 1)[0].count))
    if not {"account", "group", "start", "window_days"} <= set(reader.fieldnames or ()):
        raise FileProblem("this is not the plan.csv that the first step writes")
    # to_csv may have put an apostrophe in front of a code that starts with a symbol
    return [dict(r, account=r["account"].removeprefix("'")) for r in reader]


def wilson(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p, d = x / n, 1 + z * z / n
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p + z * z / (2 * n) - half) / d, (p + z * z / (2 * n) + half) / d


def difference(x1: int, n1: int, x0: int, n0: int) -> tuple[float, float, float]:
    """Difference between two shares with its 95% margin of error (Newcombe's method)."""
    p1, p0 = x1 / n1, x0 / n0
    (l1, u1), (l0, u0) = wilson(x1, n1), wilson(x0, n0)
    return p1 - p0, p1 - p0 - math.hypot(p1 - l1, u0 - p0), p1 - p0 + math.hypot(u1 - p1, p0 - l0)


def verdict(low: float, high: float) -> str:
    return "worked" if low > 0 else "hurt" if high < 0 else "no_proof"


def measure(plan_rows: list[dict], accounts: dict, as_of: date | None = None) -> dict:
    start, window = parse_day(plan_rows[0]["start"]), int(plan_rows[0]["window_days"])
    last = as_of or max(d for a in accounts.values() for d, _ in a["rows"])
    ends = start + timedelta(window)
    known = [r["account"] for r in plan_rows if r["account"] in accounts]
    if not known:
        raise FileProblem("no account of the plan is in this export: is it the same account code?")
    if last < ends:
        return {"status": "too_early", "ends": ends, "last": last}
    groups = {}
    for g in ("contact", "left_out"):
        seen = [ordered(accounts[r["account"]]["rows"], start, window) if r["account"] in accounts else (False, 0.0)
                for r in plan_rows if r["group"] == g]
        n, x = len(seen), sum(o for o, _ in seen)
        if not n:
            raise FileProblem(f"the plan has no account in the group {g!r}")
        groups[g] = {"accounts": n, "ordered": x, "share": x / n, "revenue": round(sum(v for _, v in seen), 2)}
    c, o = groups["contact"], groups["left_out"]
    diff, low, high = difference(c["ordered"], c["accounts"], o["ordered"], o["accounts"])
    return {"status": "done", "campaign": plan_rows[0].get("campaign", ""), "start": start, "ends": ends,
            "window": window, "groups": groups, "difference": diff, "low": low, "high": high,
            "verdict": verdict(low, high)}


def points(x: float) -> str:
    return f"{100 * x:+.0f}"


def result_text(m: dict) -> str:
    if m["status"] == "too_early":
        return (f"Too early. The export ends on {m['last']}, the window on {m['ends']}. "
                f"Looking before the end is the easiest way to be fooled.")
    c, o = m["groups"]["contact"], m["groups"]["left_out"]
    say = {"worked": f"The campaign worked: {points(m['low'])} to {points(m['high'])} points more accounts ordered.",
           "hurt": f"The contacted accounts ordered less: {points(m['low'])} to {points(m['high'])} points.",
           "no_proof": f"No proof that it worked: the difference is between {points(m['low'])} and "
                       f"{points(m['high'])} points, so it may be zero."}[m["verdict"]]
    return (f"A campaign report would say: {c['ordered']} of {c['accounts']} contacted accounts ordered again "
            f"({c['share']:.0%}), for {c['revenue']:,.0f}.\n"
            f"Left out of the campaign:    {o['ordered']} of {o['accounts']} ordered anyway ({o['share']:.0%}).\n{say}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="step", required=True)
    a = sub.add_parser("plan")
    a.add_argument("--orders", type=Path, required=True, help="orders or invoices export (CSV)")
    a.add_argument("--campaign", required=True, help="a name; it decides the draw")
    a.add_argument("--list", type=Path, help="CSV with the accounts you want to contact (default: the late ones)")
    a.add_argument("--leave-out", type=int, default=LEAVE_OUT, help="leave out one account in N (5, 3 or 2)")
    a.add_argument("--window", type=int, default=WINDOW, help="days in which an order counts")
    a.add_argument("--key-accounts", type=int, default=0, help="biggest accounts always contacted, never counted")
    a.add_argument("--as-of", default="", help="start date (default: the last date in the export)")
    a.add_argument("--out", type=Path, default=Path("plan"))
    b = sub.add_parser("measure")
    b.add_argument("--plan", type=Path, required=True)
    b.add_argument("--orders", type=Path, required=True, help="a new export, taken after the window")
    b.add_argument("--as-of", default="", help="date the export is complete to (default: its last date)")
    args = p.parse_args(argv)

    try:
        accounts = load_orders(args.orders)
        as_of = parse_day(args.as_of)
        if args.step == "measure":
            print(result_text(measure(read_plan(args.plan), accounts, as_of)))
            return 0
        chosen = [r["account"] for r in read_rows(args.list, ("account",))[0] if r["account"]] if args.list else None
        plan = make_plan(accounts, as_of or max(d for a in accounts.values() for d, _ in a["rows"]), args.campaign,
                         args.window, args.leave_out, args.key_accounts, chosen)
    except FileProblem as e:
        raise SystemExit(f"Cannot use the file: {e}") from None
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in plan_files(plan).items():
        (args.out / name).write_text(text, encoding="utf-8", newline="\n")
    n = plan["count"]
    print(f"{n['contact'] + n['key']} accounts to contact, {n['left_out']} left out until {plan['ends']} -> {args.out}/")
    if plan["unknown"]:
        print(f"{len(plan['unknown'])} accounts of the list are not in the export: {', '.join(plan['unknown'][:5])}")
    if plan["base"] is not None:
        print(f"Without any campaign, {plan['base']:.0%} of accounts like these ordered in the {plan['window']} days before.")
    for s in plan["sizes"]:
        print(f"  leaving out 1 in {s['leave_out']}: the test shows an effect of {100 * s['smallest_visible']:.0f} points or more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
