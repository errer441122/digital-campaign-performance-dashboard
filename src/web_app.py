"""What the browser page (docs/index.html) calls.

The page runs this repository's Python in the browser (Pyodide), so it uses the same
functions, and the same tests cover it, as the command line. A file that cannot be used
comes back as {"error": "..."} with the reason. Nothing here opens a network connection.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import backtest
import campaign_check as cc
from erp_export import FileProblem, parse_day, read_rows


def _guarded(fn):
    def run(*args):
        try:
            return json.dumps(fn(*args), default=str)
        except FileProblem as e:
            return json.dumps({"error": str(e)})
    return run


def _last(accounts: dict):
    return max(d for a in accounts.values() for d, _ in a["rows"])


@_guarded
def plan(orders_path: str, campaign: str, as_of: str = "", window: int = cc.WINDOW, leave_out: int = cc.LEAVE_OUT,
         key: int = 0, list_path: str = "") -> dict:
    accounts = cc.load_orders(Path(orders_path))
    chosen = [r["account"] for r in read_rows(Path(list_path), ("account",))[0] if r["account"]] if list_path else None
    p = cc.make_plan(accounts, parse_day(as_of) or _last(accounts), campaign.strip() or "campaign",
                     int(window), int(leave_out), int(key), chosen)
    contact = [r for r in p["rows"] if r["group"] != "left_out"]
    return {**{k: p[k] for k in ("base", "sizes", "count", "start", "ends", "window", "leave_out")},
            "unknown": len(p["unknown"]), "files": cc.plan_files(p), "header": cc.LIST_HEADER,
            "preview": [[r[h] for h in cc.LIST_HEADER] for r in contact[:12]]}


@_guarded
def measure(plan_path: str, orders_path: str, as_of: str = "") -> dict:
    return cc.measure(cc.read_plan(Path(plan_path)), cc.load_orders(Path(orders_path)), parse_day(as_of))


@_guarded
def demo(orders_path: str, start: str, effect: float = 0.0) -> dict:
    """Plan on a past date of the public data and measure straight away. With `effect`, some
    contacted accounts that did not order get an invented order: the other answer, on purpose."""
    accounts, day = cc.load_orders(Path(orders_path)), parse_day(start)
    p = cc.make_plan(accounts, day, "demo")
    if effect:
        contact = [r["account"] for r in p["rows"] if r["group"] == "contact"]
        share = sum(cc.ordered(accounts[k]["rows"], day, cc.WINDOW)[0] for k in contact) / len(contact)
        for k in contact:
            rows = accounts[k]["rows"]
            if not cc.ordered(rows, day, cc.WINDOW)[0] and backtest.lift(k, "demo", share, float(effect)):
                rows.append((day + timedelta(10), max(x for _, x in rows)))
    contact = [r for r in p["rows"] if r["group"] != "left_out"]
    return {**cc.measure(p["rows"], accounts), "effect": float(effect), "base": p["base"], "count": p["count"],
            "sizes": p["sizes"], "header": cc.LIST_HEADER, "preview": [[r[h] for h in cc.LIST_HEADER] for r in contact[:8]]}
