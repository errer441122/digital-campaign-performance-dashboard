"""I risultati salvati nel foglio da Excel sono quelli attesi. Il collaudo completo, con le modifiche
a dati e regole, e' verifica-excel.ps1: gira su Windows con Excel, qui no."""

import csv
import re
from pathlib import Path

import pytest
from openpyxl import load_workbook

QUI = Path(__file__).resolve().parents[1]
VALORI = load_workbook(QUI / "campagna-ordini.xlsx", data_only=True)
FORMULE = load_workbook(QUI / "campagna-ordini.xlsx")
ATTESI = list(csv.DictReader(open(QUI / "casi-attesi.csv", encoding="utf-8-sig"), delimiter=";"))
LEAD = {r[0].value: r for r in VALORI["Lead"].iter_rows(min_row=6, max_row=305) if r[0].value}


@pytest.mark.parametrize("a", ATTESI, ids=lambda a: f"{a['ID']} {a['Caso']}")
def test_caso(a):
    r = LEAD[a["ID"]]
    assert (r[9].value, round(r[12].value or 0, 2), r[14].value) == (a["Esito"], float(a["Attribuibili"]), a["Si può contattare"])
    assert len(r[10].value) > 5  # ogni esito ha un perché


def test_i_lead_e_gli_euro_quadrano():
    t = VALORI["Riepilogo"][16]
    assert t[1].value == len(ATTESI) and t[10].value == "sì" and t[17].value == "sì"
    assert [round(t[i].value, 2) for i in (12, 13, 14, 15, 16)] == [22767.5, 4000, 21000, 6000, 53767.5]


def test_nessuna_formula_in_errore():
    for ws in VALORI:
        for riga in ws.iter_rows():
            for c in riga:
                assert not (isinstance(c.value, str) and c.value.startswith("#")), (ws.title, c.coordinate, c.value)


def test_chi_ha_detto_no_non_va_ai_commerciali():
    lista = {r[0].value for r in VALORI["Per i commerciali"].iter_rows(min_row=6, max_row=155)}
    assert not lista & {a["ID"] for a in ATTESI if a["Si può contattare"] != "sì"}
    assert not lista & {a["ID"] for a in ATTESI if a["Esito"] in ("Da decidere", "Da correggere", "Doppione", "Escluso")}


def test_i_risultati_sono_formule_e_non_valori_incollati():
    ws = FORMULE["Lead"]
    for c in (ws["J6"], ws["K6"], ws["M6"], ws["O6"], ws["J305"]):
        assert str(c.value).startswith("="), c.coordinate


def test_solo_funzioni_che_ha_anche_excel_2013():
    nuove = re.compile(r"\b(XLOOKUP|FILTER|UNIQUE|LET|MAXIFS|TEXTJOIN|IFS|SWITCH)\(")
    for ws in FORMULE:
        for riga in ws.iter_rows(min_row=1, max_row=12):
            for c in riga:
                if isinstance(c.value, str) and c.value.startswith("="):
                    assert not nuove.search(c.value.replace("COUNTIFS(", "").replace("SUMIFS(", "")), (ws.title, c.coordinate)
