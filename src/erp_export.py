"""Read an ERP export the way ERPs and Excel really write it.

Comma, semicolon or tab; decimal commas; DD/MM/YYYY dates; SAP's trailing minus
("49,90-"); headers in English or Italian. Pure standard library.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

# For each field, the headers it can have. The first one found in the file wins.
HEADERS = {
    "account": ("account", "account_code", "customer_id", "customer_code", "customer", "client",
                "codice_cliente", "cod_cliente", "cliente", "company", "azienda", "ragione_sociale"),
    "name": ("name", "account_name", "customer_name", "company_name", "ragione_sociale", "nome"),
    "date": ("order_date", "invoice_date", "document_date", "date",
             "data_ordine", "data_fattura", "data_documento", "data"),
    "amount": ("amount", "order_value", "net_amount", "value", "total", "order_value_gbp", "order_value_eur",
               "importo", "imponibile", "totale", "valore"),
    "rep": ("rep", "sales_rep", "agent", "owner", "agente", "commerciale"),
}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


class FileProblem(ValueError):
    """Something in the user's file that the user can fix."""


def header_key(text: str) -> str:
    """'Codice Cliente' -> 'codice_cliente', 'Quantità' -> 'quantita'."""
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", plain.lower()).strip("_")


def parse_day(text: str) -> date | None:
    text = (text or "").strip()
    if not text:
        return None
    head = text.split()[0].split("T")[0]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(head, fmt).date()
        except ValueError:
            pass
    raise FileProblem(f"the date {text!r} is neither YYYY-MM-DD nor DD/MM/YYYY")


def parse_number(text: str) -> float:
    """'49.90', '49,90', '1.234,56', '1,234.56', '-49,90' and SAP's '49,90-'."""
    t = "".join(ch for ch in (text or "") if ch.isdigit() or ch in ",.-")
    if not any(ch.isdigit() for ch in t):
        return 0.0
    negative = "-" in t
    t = t.replace("-", "")
    if "," in t and "." in t:  # the separator that comes last is the decimal one
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    else:
        t = t.replace(",", ".")
    try:
        return -float(t) if negative else float(t)
    except ValueError:
        raise FileProblem(f"{text!r} is not a number") from None


def read_text(path: Path) -> str:
    """UTF-8, or the Windows encoding older Excel versions save in."""
    raw = Path(path).read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def read_rows(path: Path, needed: tuple[str, ...]) -> tuple[list[dict[str, str]], set[str]]:
    """Rows with the fields of HEADERS as keys, and which fields the file has."""
    text = read_text(path)
    first = text.split("\n", 1)[0]
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=max(",;\t", key=first.count))
    by_key = {header_key(h): h for h in (reader.fieldnames or []) if h}
    column = {}
    for field, names in HEADERS.items():
        found = next((by_key[n] for n in names if n in by_key), None)
        if found:
            column[field] = found
    missing = [f for f in needed if f not in column]
    if missing:
        wanted = "; ".join(f"{f}: {', '.join(HEADERS[f][:4])}..." for f in missing)
        raise FileProblem(f"column not found ({wanted}). The file has: {', '.join(by_key) or 'no header'}")
    rows = [{f: (r.get(h) or "").strip() for f, h in column.items()} for r in reader]
    return rows, set(column)


def safe(cell: object) -> object:
    """A text Excel would run as a formula gets a leading apostrophe."""
    return "'" + cell if isinstance(cell, str) and cell.startswith(FORMULA_START) else cell


def to_csv(header: list[str], rows: list[list[object]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows([[safe(c) for c in row] for row in rows])
    return buf.getvalue()
