"""The draw, the rule and the verdict, on small files written by hand and on the real data."""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import backtest  # noqa: E402
import campaign_check as cc  # noqa: E402
import erp_export as erp  # noqa: E402
import web_app  # noqa: E402

START = date(2026, 3, 1)
DATA = ROOT / "data" / "online_retail_orders.csv"


def every(days, n, until, amount=100.0):
    """n orders, one every `days` days, the last one on `until`."""
    return [(until - timedelta(days * i), amount) for i in range(n)]


def book(n=100):
    """n accounts ordering every 20 days and silent for 60: all late. Bigger number, bigger account."""
    return {f"A{i:03d}": {"name": f"Company {i}", "rep": "Rossi", "rows": every(20, 8, START - timedelta(60), 100 + i)}
            for i in range(n)}


# ---------- reading what an ERP writes

@pytest.mark.parametrize("text, value", [
    ("49.90", 49.9), ("49,90", 49.9), ("1.234,56", 1234.56), ("1,234.56", 1234.56), ("€ 1.234,56", 1234.56),
    ("-49,90", -49.9), ("49,90-", -49.9), ("", 0.0), ("n.d.", 0.0)])
def test_numbers_as_erps_write_them(text, value):
    assert erp.parse_number(text) == pytest.approx(value)


def test_italian_export_with_semicolons_and_a_credit_note(tmp_path):
    f = tmp_path / "ordini.csv"
    f.write_text("﻿Codice cliente;Ragione sociale;Agente;Data documento;Importo\n"
                 "C1;Rossi Srl;Bianchi;05/01/2026;1.200,50\nC1;Rossi Srl;Bianchi;20/01/2026;300,00-\n", encoding="utf-8")
    c1 = cc.load_orders(f)["C1"]
    assert (c1["name"], c1["rep"]) == ("Rossi Srl", "Bianchi")
    assert c1["rows"] == [(date(2026, 1, 5), 1200.5), (date(2026, 1, 20), -300.0)]
    assert cc.order_days(c1["rows"], START) == [date(2026, 1, 5)]  # the credit note is not an order


def test_a_file_without_the_columns_says_what_is_missing(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("colore,prezzo\nrosso,1\n", encoding="utf-8")
    with pytest.raises(erp.FileProblem, match="account.*colore, prezzo"):
        cc.load_orders(f)
    f.write_text("cliente,data\nA,31-31-2026\n", encoding="utf-8")
    with pytest.raises(erp.FileProblem, match="line 2.*31-31-2026"):
        cc.load_orders(f)


# ---------- who is late

@pytest.mark.parametrize("gap, silent, late", [
    (28, 75, True), (28, 56, False), (90, 120, False),   # its own rhythm decides, not a fixed number of days
    (3, 13, False), (3, 14, True), (60, 400, False)])    # not after a weekend, not after a year
def test_late_means_late_against_its_own_rhythm(gap, silent, late):
    assert cc.is_late(cc.rhythm(every(gap, 5, START - timedelta(silent)), START)) is late


def test_an_account_with_three_orders_has_no_rhythm_yet():
    assert cc.rhythm(every(10, 3, START - timedelta(90)), START) is None


# ---------- the draw

def test_one_in_five_is_left_out_across_every_size():
    accounts = book(103)
    g = cc.draw(accounts, list(accounts), START, "Spring")
    count = {v: list(g.values()).count(v) for v in ("key", "left_out", "contact")}
    assert count == {"key": 3, "left_out": 20, "contact": 80}
    assert {k for k, v in g.items() if v == "key"} == {"A102", "A101", "A100"}  # the biggest, always contacted
    ranked = sorted((k for k in accounts if g[k] != "key"), reverse=True)
    assert all(sum(g[k] == "left_out" for k in ranked[i:i + 5]) == 1 for i in range(0, 100, 5))


def test_the_draw_can_be_repeated_and_depends_only_on_the_campaign():
    accounts = book()
    a = cc.draw(accounts, list(accounts), START, "Spring")
    assert a == cc.draw(accounts, list(reversed(list(accounts))), START, "Spring")
    assert a != cc.draw(accounts, list(accounts), START, "Autumn")


def test_key_accounts_are_contacted_and_not_counted():
    p = cc.make_plan(book(), START, "Spring", key=10)
    assert p["count"] == {"contact": 72, "left_out": 18, "key": 10}


def test_your_own_list_is_used_and_unknown_codes_are_reported():
    accounts = book()
    p = cc.make_plan(accounts, START, "Fair", chosen=[f"A{i:03d}" for i in range(40)] + ["A001", "NOPE"])
    assert sum(p["count"].values()) == 40 and p["unknown"] == ["NOPE"]


def test_too_few_accounts_is_an_error_not_a_plan():
    with pytest.raises(erp.FileProblem, match="too few"):
        cc.make_plan(book(9), START, "Spring")


# ---------- the verdict

def test_margin_of_error_matches_the_published_example():
    # Newcombe (1998), method 10, 56/70 against 48/80: +0.2000, 0.0524 to 0.3339
    d, low, high = cc.difference(56, 70, 48, 80)
    assert (round(d, 4), round(low, 4), round(high, 4)) == (0.2, 0.0524, 0.3339)


def campaign(tmp_path, effect):
    """Plan, files, then a second export in which a share of each group has ordered."""
    accounts = book(200)
    p = cc.make_plan(accounts, START, "Spring")
    f = tmp_path / "plan.csv"
    f.write_text(cc.plan_files(p)["plan.csv"], encoding="utf-8")
    for g, share in (("contact", 0.30 + effect), ("left_out", 0.30)):
        members = [r["account"] for r in p["rows"] if r["group"] == g]
        for k in members[:round(len(members) * share)]:
            accounts[k]["rows"].append((START + timedelta(60), 500.0))      # last day that counts
        accounts[members[-1]]["rows"].append((START + timedelta(61), 500.0))  # one day too late
    return cc.read_plan(f), accounts


@pytest.mark.parametrize("effect, says", [(0, "no_proof"), (0.30, "worked"), (-0.25, "hurt")])
def test_verdict(tmp_path, effect, says):
    m = cc.measure(*campaign(tmp_path, effect))
    assert (m["status"], m["verdict"]) == ("done", says)
    assert m["groups"]["contact"]["accounts"] == 160 and m["groups"]["left_out"]["accounts"] == 40
    assert m["difference"] == pytest.approx(effect, abs=0.01)


def test_looking_too_early_gives_no_result(tmp_path):
    rows, accounts = campaign(tmp_path, 0.30)
    m = cc.measure(rows, accounts, START + timedelta(59))
    assert m["status"] == "too_early" and "groups" not in m


def test_another_companys_export_is_refused(tmp_path):
    rows, _ = campaign(tmp_path, 0)
    with pytest.raises(erp.FileProblem, match="same account code"):
        cc.measure(rows, {"Z9": {"name": "", "rep": "", "rows": [(START, 1.0)]}})


def test_a_code_that_looks_like_a_formula_survives_the_round_trip(tmp_path):
    accounts = {f"-{k}": a for k, a in book(20).items()}
    f = tmp_path / "plan.csv"
    f.write_text(cc.plan_files(cc.make_plan(accounts, START, "Spring"))["plan.csv"], encoding="utf-8")
    assert "'-A000" in f.read_text(encoding="utf-8")
    assert {r["account"] for r in cc.read_plan(f)} == set(accounts)


def test_command_line_end_to_end(tmp_path, capsys):
    orders = tmp_path / "orders.csv"
    orders.write_text("account,order_date,amount\n" + "".join(
        f"{k},{d},{x}\n" for k, a in book(60).items() for d, x in a["rows"]), encoding="utf-8")
    cc.main(["plan", "--orders", str(orders), "--campaign", "Spring", "--as-of", "2026-03-01", "--out", str(tmp_path / "p")])
    assert "48 accounts to contact, 12 left out until 2026-04-30" in capsys.readouterr().out
    cc.main(["measure", "--plan", str(tmp_path / "p" / "plan.csv"), "--orders", str(orders), "--as-of", "2026-05-01"])
    assert "No proof" in capsys.readouterr().out


# ---------- the real data and the page

def test_the_page_shows_the_published_numbers():
    r = json.loads((ROOT / "docs" / "campaign_check.json").read_text(encoding="utf-8"))
    page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    c, o = r["pooled"]["contact"], r["pooled"]["left_out"]
    fooled = next(f for f in r["fooled"] if f["leave_out"] == 5)
    for shown in (f"{c['ordered']:,}", f"{c['accounts']:,}", f"{c['share']:.0%}", f"{o['share']:.0%}",
                  f"{o['ordered']:,}", f"{o['accounts']:,}", f"£{c['revenue']:,.0f}", f"{fooled['campaigns']:,}"):
        assert shown in page, shown


def test_demo_says_no_proof_and_the_invented_effect_says_worked():
    start = backtest.STARTS[3].isoformat()
    plain, invented = json.loads(web_app.demo(str(DATA), start)), json.loads(web_app.demo(str(DATA), start, 0.2))
    assert plain["verdict"] == "no_proof"
    assert invented["verdict"] == "worked" and invented["groups"]["left_out"] == plain["groups"]["left_out"]


def test_a_bad_file_comes_back_as_an_error_not_a_crash(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("a,b\n1,2\n", encoding="utf-8")
    assert "column not found" in json.loads(web_app.plan(str(f), "x"))["error"]
    assert "plan.csv" in json.loads(web_app.measure(str(f), str(f)))["error"]
