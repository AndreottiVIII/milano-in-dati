"""Pulisce i dati grezzi sugli aeroporti -> pulito/ (CSV con ';' e punto decimale).

Fonti:
  Eurostat (CC BY 4.0), raw/eurostat/*.json (JSON-stat): dal 2004 per i tre aeroporti di Milano e per la somma degli aeroporti italiani
  ENAC, pulito/enac_serie_1994_2003.csv (da 03_estrai_enac.py): serie 1994-2003 (Annuario statistico 2003)
  ENAC, pulito/enac_controllo.csv: Tavola APT 1 dei rapporti 2007, 2010, 2024, 2025 (solo controllo)

Scrive: annuale.csv, italia_annuale.csv, mensile.csv, controlli.txt

uso: python -I -X utf8 04_pulisci.py <cartella aeroporti assoluta>
"""
import collections
import csv
import json
import itertools
import os
import sys

base = sys.argv[1]
RAW = os.path.join(base, "raw", "eurostat")
OUT = os.path.join(base, "pulito")
AP = {"IT_LIML": "Linate", "IT_LIMC": "Malpensa", "IT_LIME": "Bergamo"}
FIRST = 2004   # primo anno affidabile in Eurostat (prima: flag 'u' = poco affidabile, e buchi 1999-2001)
log = []


def flat(name):
    d = json.load(open(os.path.join(RAW, name + ".json"), encoding="utf-8"))
    ids = d["id"]
    cats = [list(d["dimension"][k]["category"]["index"].keys()) for k in ids]
    vals, st = d["value"], d.get("status", {})
    for pos, combo in enumerate(itertools.product(*cats)):
        v = vals.get(str(pos)) if isinstance(vals, dict) else vals[pos]
        s = st.get(str(pos)) if isinstance(st, dict) else None
        yield dict(zip(ids, combo)), v, s


def w(path, head, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        c = csv.writer(f, delimiter=";", lineterminator="\n")
        c.writerow(head)
        for r in rows:
            c.writerow(["" if v is None else v for v in r])


def leggi(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig", newline=""), delimiter=";"))


# ---------------- Eurostat annuale, tutti gli aeroporti italiani
PAX = {}      # (aeroporto ICAO, anno, copertura) -> (valore, flag)
for cov in ("TOTAL", "NAT", "INTL", "INTL_IEU27_2020", "INTL_XEU27_2020"):
    for k, v, s in flat(f"avia_paoa_A_pax_tutti_{cov}"):
        if k["rep_airp"].startswith("IT_"):
            PAX[(k["rep_airp"], int(k["time"]), cov)] = (v, s)
VOLI, MERCI = {}, {}
for k, v, s in flat("avia_paoa_A_voli_tutti"):
    if k["rep_airp"].startswith("IT_"):
        VOLI[(k["rep_airp"], int(k["time"]))] = (v, s)
for k, v, s in flat("avia_gooa_A_merci_tutti"):
    if k["rep_airp"].startswith("IT_"):
        MERCI[(k["rep_airp"], int(k["time"]))] = (v, s)

# ---------------- ENAC 1994-2003
enac = {}
for r in leggi(os.path.join(OUT, "enac_serie_1994_2003.csv")):
    enac[(r["aeroporto"], int(r["anno"]))] = (int(r["movimenti"]), int(r["passeggeri"]), int(r["cargo_tonnellate"]), int(r["pagina_pdf_annuario_2003"]))

# ---------------- annuale per i tre aeroporti
rows = []
for icao, nome in AP.items():
    for anno in range(1994, 2026):
        if anno < FIRST:
            e = enac.get((nome, anno))
            if not e:
                continue
            rows.append((nome, anno, e[1], None, None, None, None, e[0], e[2], "ENAC", "ENAC", "ENAC"))
        else:
            g = lambda cov: PAX.get((icao, anno, cov), (None, None))[0]
            rows.append((nome, anno, g("TOTAL"), g("NAT"), g("INTL"), g("INTL_IEU27_2020"), g("INTL_XEU27_2020"),
                         VOLI.get((icao, anno), (None, None))[0], MERCI.get((icao, anno), (None, None))[0], "Eurostat", "Eurostat", "Eurostat"))
w(os.path.join(OUT, "annuale.csv"),
  ["aeroporto", "anno", "passeggeri", "nazionali", "internazionali", "internazionali_ue", "internazionali_extra_ue",
   "movimenti_o_voli", "cargo_tonnellate", "fonte_passeggeri", "fonte_movimenti", "fonte_cargo"], rows)
log.append("annuale.csv: ENAC (Annuario 2003) per 1994-2003, Eurostat dal 2004; dal 2004 nazionali+internazionali = totale: controllo sotto")
bad = []
for r in rows:
    if r[1] >= FIRST and None not in (r[2], r[3], r[4]) and abs(r[3] + r[4] - r[2]) > 2:
        bad.append((r[0], r[1], r[2], r[3] + r[4]))
    if r[1] >= FIRST and None not in (r[4], r[5], r[6]) and abs(r[5] + r[6] - r[4]) > 2:
        bad.append(("ue+extra", r[0], r[1], r[4], r[5] + r[6]))
log.append(f"  controllo nazionali + internazionali = totale (e UE + extra UE = internazionali), 2004-2025, tre aeroporti: {len(bad)} eccezioni {bad[:4]}")

# ---------------- Italia: somma degli aeroporti (Eurostat dal 2004), ENAC prima
ita_enac = {a: v for (n, a), v in enac.items() if n == "Italia"}
rows = []
for anno in range(1994, 2026):
    if anno < FIRST:
        e = ita_enac.get(anno)
        if e:
            rows.append((anno, e[1], None, None, e[0], e[2], None, "ENAC"))
    else:
        tot = [(a, PAX.get((a, anno, "TOTAL"))) for a in {k[0] for k in PAX}]
        tot = [(a, x[0]) for a, x in tot if x and x[0]]
        nat = sum(PAX.get((a, anno, "NAT"), (0,))[0] or 0 for a, _ in tot)
        intl = sum(PAX.get((a, anno, "INTL"), (0,))[0] or 0 for a, _ in tot)
        voli = sum((VOLI.get((a, anno), (0,))[0] or 0) for a, _ in tot)
        merci = sum((MERCI.get((a, anno), (0,))[0] or 0) for a, _ in tot)
        rows.append((anno, sum(v for _, v in tot), nat, intl, voli, merci, len(tot), "Eurostat"))
w(os.path.join(OUT, "italia_annuale.csv"), ["anno", "passeggeri", "nazionali", "internazionali", "movimenti_o_voli", "cargo_tonnellate", "n_aeroporti", "fonte"], rows)

# ---------------- mensile per i tre aeroporti (Eurostat)
M = collections.defaultdict(dict)
def agg(name, key, cov=None, unit=None):
    for k, v, s in flat(name):
        if "-" in k["time"] and "Q" not in k["time"] and k["rep_airp"] in AP and k["freq"] == "M":
            if cov and k["tra_cov"] != cov:
                continue
            if unit and k["unit"] != unit:
                continue
            a, m = k["time"].split("-")
            if int(a) >= FIRST:
                M[(AP[k["rep_airp"]], int(a), int(m))][key] = v
for cov, key in (("TOTAL", "pax"), ("NAT", "nat"), ("INTL", "intl")):
    agg("avia_paoa_M_pax", key, cov, "PAS")
agg("avia_paoa_M_voli", "voli", "TOTAL", "FLIGHT")
agg("avia_gooa_M_merci", "merci", "TOTAL", "T")
w(os.path.join(OUT, "mensile.csv"), ["aeroporto", "anno", "mese", "passeggeri", "nazionali", "internazionali", "voli", "cargo_tonnellate"],
  [(a, y, m, d.get("pax"), d.get("nat"), d.get("intl"), d.get("voli"), d.get("merci")) for (a, y, m), d in sorted(M.items())])
ultimo = max((y, m) for (a, y, m) in M if M[(a, y, m)].get("pax"))
log.append(f"mensile.csv: {len(M)} righe aeroporto-mese, ultimo mese con dati: {ultimo[0]}-{ultimo[1]:02d}")
# somma dei 12 mesi = totale annuo?
dif = []
for icao, nome in AP.items():
    for anno in range(FIRST, 2026):
        s = sum(M[(nome, anno, m)].get("pax") or 0 for m in range(1, 13))
        a = PAX.get((icao, anno, "TOTAL"), (None,))[0]
        if a and abs(s - a) > 1:
            dif.append((nome, anno, s, a))
log.append(f"controllo somma dei 12 mesi = totale annuo (passeggeri), 2004-2025, tre aeroporti: {len(dif)} differenze {dif[:3]}")

# ---------------- controllo Eurostat contro ENAC (anni 2001-2003 inclusi quelli di Eurostat con flag 'u')
ctl = leggi(os.path.join(OUT, "enac_controllo.csv"))
lines = []
nome2icao = {v: k for k, v in AP.items()}
for r in ctl:
    anno, ap = int(r["anno"]), r["aeroporto"]
    if ap == "Italia":
        es = next(x[1] for x in rows if x[0] == anno) if any(x[0] == anno for x in rows) else None
        esm = next(x[5] for x in rows if x[0] == anno)
        lines.append((ap, anno, "passeggeri", int(r["passeggeri"]), es, f"ENAC p.{r['pagina_pdf']}"))
        lines.append((ap, anno, "cargo t", float(r["cargo_tonnellate"]), esm, f"ENAC p.{r['pagina_pdf']}"))
    else:
        icao = nome2icao[ap]
        lines.append((ap, anno, "passeggeri", int(r["passeggeri"]), PAX[(icao, anno, "TOTAL")][0], f"ENAC p.{r['pagina_pdf']}"))
        lines.append((ap, anno, "cargo t", float(r["cargo_tonnellate"]), MERCI.get((icao, anno), (None,))[0], f"ENAC p.{r['pagina_pdf']}"))
        lines.append((ap, anno, "movimenti ENAC / voli Eurostat", int(r["movimenti_commerciali"]), VOLI.get((icao, anno), (None,))[0], f"ENAC p.{r['pagina_pdf']}"))
for (ap, anno), (m, p, c, pg) in sorted(enac.items(), key=lambda x: (x[0][1], x[0][0])):
    if anno in (2001, 2002, 2003) and ap in nome2icao:
        icao = nome2icao[ap]
        lines.append((ap, anno, "passeggeri", p, PAX.get((icao, anno, "TOTAL"), (None,))[0], f"ENAC Annuario 2003 p.{pg}"))
        lines.append((ap, anno, "cargo t", c, MERCI.get((icao, anno), (None,))[0], f"ENAC Annuario 2003 p.{pg}"))
with open(os.path.join(OUT, "controllo_eurostat_enac.csv"), "w", encoding="utf-8", newline="") as f:
    cw = csv.writer(f, delimiter=";", lineterminator="\n")
    cw.writerow(["aeroporto", "anno", "misura", "ENAC", "Eurostat", "differenza_pct", "fonte_enac"])
    for ap, anno, mis, en, es, src in lines:
        diff = None if not es or not en else round((es / en - 1) * 100, 2)
        cw.writerow([ap, anno, mis, en, es, diff, src])
        log.append(f"  controllo {ap} {anno} {mis}: ENAC {en} / Eurostat {es} ({'-' if diff is None else str(diff) + '%'}) [{src}]")
open(os.path.join(OUT, "controlli.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
