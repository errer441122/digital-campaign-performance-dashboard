"""Da dove vengono due regole del foglio: numeri su 36.969 ordini veri di un grossista (UCI, CC BY 4.0).

    python prove/prove.py      riscrive prove/README.md
"""

import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

QUI = Path(__file__).parent
sys.path.insert(0, str(QUI.parent / "analisi-cv" / "src"))
import crm_retention as cr  # noqa: E402

DATI = QUI.parent / "analisi-cv" / "data" / "online_retail_orders.csv"
num = lambda x: f"{x:,.0f}".replace(",", ".")  # noqa: E731
pct = lambda x: f"{100 * x:.1f}%".replace(".", ",")  # noqa: E731

righe = list(csv.DictReader(open(DATI, encoding="utf-8")))
annullati = {r["order_id"]: float(r["value_gbp"]) for r in csv.DictReader(open(QUI / "annullati_stesso_giorno.csv", encoding="utf-8"))}
trovati = [r for r in righe if r["order_id"] in annullati]
assert len(trovati) == len(annullati) and all(abs(float(r["order_value_gbp"]) - annullati[r["order_id"]]) < 0.01 for r in trovati)
grandi = sorted(righe, key=lambda r: -float(r["order_value_gbp"]))[:4]


def champions(ordini):
    r = cr.run(ordini)["rfm"]
    s = next(x for x in r["segments"] if x["segment"] == "Champions")
    ricavo = "revenue_gbp" if "revenue_gbp" in s else "revenue"
    return r["total_customers"], sum(x[ricavo] for x in r["segments"]), s["customers"] / r["total_customers"], s[ricavo] / sum(x[ricavo] for x in r["segments"])


tutti = cr.read_orders()
togli = {(r["customer_id"], r["order_date"], round(float(r["order_value_gbp"]), 2)): 0 for r in trovati}
for r in trovati:
    togli[r["customer_id"], r["order_date"], round(float(r["order_value_gbp"]), 2)] += 1
netti = []
for o in tutti:
    k = (o["customer_id"], o["order_date"].isoformat(), round(o["order_value_gbp"], 2))
    if togli.get(k, 0):
        togli[k] -= 1
    else:
        netti.append(o)
assert len(tutti) - len(netti) == len(annullati)
prima, dopo = champions(tutti), champions(netti)

storia = defaultdict(list)
for r in righe:
    storia[r["customer_id"]].append(date.fromisoformat(r["order_date"]))
tornati = []
for oggi in (date(2010, 12, 1), date(2011, 3, 1), date(2011, 6, 1)):
    fermi = [c for c, g in storia.items() if min(g) <= oggi and (oggi - max(x for x in g if x <= oggi)).days > 180]
    tornati.append((oggi, len(fermi), sum(any(oggi < x <= oggi + timedelta(180) for x in storia[c]) for c in fermi)))

testo = [
    "# Da dove vengono due regole", "",
    f"Ordini veri: {num(len(righe))} di {num(len(storia))} clienti di un grossista inglese, dicembre 2009 - dicembre 2011 (Chen, D., *Online Retail II*, UCI, CC BY 4.0).", "",
    "## Un ordine annullato non è un ordine", "",
    f"{len(annullati)} ordini sono stati annullati per intero lo stesso giorno: valgono {num(sum(annullati.values()))} sterline. Tra questi ci sono **i due ordini più grandi di tutto l'archivio**.", "",
    "| Ordine | Data | Valore | Annullato lo stesso giorno |", "| --- | --- | ---: | --- |",
]
testo += [f"| {r['order_id']} | {r['order_date']} | £{num(float(r['order_value_gbp']))} | {'sì' if r['order_id'] in annullati else 'no'} |" for r in grandi]
testo += [
    "", "**Da dove viene la regola.** L'analisi citata nel mio CV toglieva le righe di annullamento, ma non gli ordini annullati: li contava come vendite. Per questo nel foglio un ordine annullato vale zero e una nota di credito si toglie dall'ordine a cui si riferisce.", "",
    "| | Come nel CV | Senza gli ordini annullati |", "| --- | ---: | ---: |",
    f"| Clienti | {num(prima[0])} | {num(dopo[0])} |", f"| Fatturato | £{num(prima[1])} | £{num(dopo[1])} |",
    f"| Champions, quota di clienti | {pct(prima[2])} | {pct(dopo[2])} |", f"| Champions, quota di fatturato | {pct(prima[3])} | {pct(dopo[3])} |", "",
    "Le due percentuali del CV reggono. Il fatturato totale era gonfiato di quasi mezzo milione.", "",
    "## Chi torna da solo non è un cliente della campagna", "",
    "Clienti fermi da più di 180 giorni, e quanti hanno ordinato nei 180 giorni dopo. Nei dati non c'è nessuna campagna.", "",
    "| Alla data | Clienti fermi | Tornati da soli | Quota |", "| --- | ---: | ---: | ---: |",
]
testo += [f"| {g.strftime('%d/%m/%Y')} | {num(f)} | {num(t)} | {t / f:.0%} |" for g, f, t in tornati]
testo += ["", "Tra uno su cinque e uno su tre torna comunque. Per questo nel foglio chi torna sta in una colonna a parte e il suo ordine non è attribuito alla campagna.", ""]
(QUI / "README.md").write_text("\n".join(testo), encoding="utf-8", newline="\n")
print("\n".join(testo))
