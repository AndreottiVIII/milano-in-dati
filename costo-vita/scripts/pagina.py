#!/usr/bin/env python3
"""Fase 2 del filone "Quanto costa vivere a Milano": dati aggregati per la pagina web.

Uso (percorsi assoluti):
    python -I -X utf8 <...>/costo-vita/scripts/pagina.py <...>/costo-vita <...>/docs/costo-vita/data

Legge SOLO da costo-vita/pulito/ (nessuno scaricamento) e scrive in docs/costo-vita/data/:
    riepilogo.json                 tutti i numeri della pagina, con l'origine
    indici_annui_2005_100.csv      indice (2005 = 100, medie annue) di 10 voci + indice generale
    serie_mensili_energia.csv      elettricita', gas, benzina, gasolio e indice generale, mensili 2020-2026 (2015 = 100)
    carburanti_milano_mensile.csv  prezzi self di benzina e gasolio, mensili 2015-2026 (euro al litro)
    biglietto_atm.csv              i quattro gradini del biglietto + abbonamenti, con la fonte
    prezzi_gen2021_set2026.csv     8+ prezzi medi in euro (Osservatorio MIMIT), SOLO valori aggregati
    affitto_vs_reddito.csv         affitto OMI (60 m2), reddito mediano interpolato, quota, ore
    milano_vs_italia.csv           inflazione 2000/05/10/15/20 -> 2025, Milano e Italia
Si puo' rilanciare quante volte si vuole: riscrive tutto.
I file grezzi del Ministero (MIMIT) NON vengono ripubblicati: la licenza dei dati non e' scritta.
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

if len(sys.argv) != 3:
    sys.exit(__doc__)
C = Path(sys.argv[1])
OUT = Path(sys.argv[2])
P = C / "pulito"
for p in (C, OUT):
    if not p.is_absolute():
        sys.exit("Servono percorsi assoluti")
OUT.mkdir(parents=True, exist_ok=True)


def rd(name):
    with open(P / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def fl(x):
    x = (x or "").strip()
    if x == "":
        return None
    return float(x)


def wcsv(name, head, rows):
    with open(OUT / name, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(head)
        w.writerows(rows)


def r1(x, d=1):
    return None if x is None else round(x, d)


LOG = []


def check(cond, msg):
    if not cond:
        sys.exit("CONTROLLO FALLITO: " + msg)
    LOG.append("ok: " + msg)


# ----------------------------------------------------------------------------- indici NIC
voci = defaultdict(dict)  # voce -> {periodo: valore}
etich = {}
for r in rd("nic_milano_voci_base2015.csv"):
    v = fl(r["indice_base2015_100"])
    if v is not None and v > 0:  # 0,0 = dato mancante (vedi NOTE)
        voci[r["voce"]][r["periodo"]] = v
    etich[r["voce"]] = r["etichetta"]

gen_ann = {}  # anno -> dict(livello da tassi / vero, italia)
for r in rd("nic_milano_generale_annuo_2000_2025.csv"):
    a = int(r["anno"])
    vero = fl(r["livello_milano_2025_100_da_indice_vero"])
    tassi = fl(r["livello_milano_2025_100_da_tassi"])
    gen_ann[a] = {
        "milano": vero if vero is not None else tassi,
        "italia": fl(r["livello_italia_2025_100_NIC"]),
        "tasso_milano": fl(r["tasso_annuo_milano_ds1821_pct"]),
        "ricostruito": vero is None,
    }


def annuo(serie, anno):
    vals = [v for k, v in serie.items() if k.startswith(str(anno) + "-")]
    return (mean(vals), len(vals)) if vals else (None, 0)


ITEMS = [  # chiave, nome sulla pagina, nota
    ("pane", "Pane", ""),
    ("caffe_prodotto", "Caffè (pacco da casa)", ""),
    ("ristoranti", "Ristoranti e pizzerie", "Dal 2016 la voce comprende anche il bar: la serie ha una rottura."),
    ("affitti", "Affitti (canoni in corso, ISTAT)", "Misura i canoni di tutti i contratti in corso, non i prezzi dei contratti nuovi."),
    ("elettricita", "Energia elettrica", ""),
    ("gas", "Gas di rete", ""),
    ("benzina", "Benzina", ""),
    ("bus_tram_metro", "Bus, tram, metro", "Dal 2011 la voce si chiama «autobus e pullman» e comprende anche l'extraurbano."),
    ("alberghi", "Alberghi", "Prezzi molto stagionali."),
    ("telefonia_mobile", "Telefonia", "Fino al 2010 telefono fisso e cellulare insieme."),
]
indici = {}
mesi_mancanti = {}
base2005 = {}
for k, _, _ in ITEMS:
    s = voci[k]
    b, n = annuo(s, 2005)
    check(b is not None and n == 12, "%s: 12 mesi nel 2005" % k)
    base2005[k] = b
    indici[k] = {}
    for a in range(2005, 2026):
        m, n = annuo(s, a)
        check(n >= 11, "%s %d: almeno 11 mesi su 12 (ha %d; la media usa i mesi presenti)" % (k, a, n))
        indici[k][a] = m / b * 100
g0 = gen_ann[2005]["milano"]
indici["generale"] = {a: gen_ann[a]["milano"] / g0 * 100 for a in range(2005, 2026)}
indici_ita = {a: gen_ann[a]["italia"] / gen_ann[2005]["italia"] * 100 for a in range(2005, 2026)}

# controllo con il riepilogo di fase 1 (variazione 2005 -> 2025)
rie = {r["chiave"]: r for r in rd("riepilogo_indici_voci.csv") if r["tipo"] == "voce Milano"}
for k, _, _ in ITEMS:
    exp = fl(rie[k]["var_pct_2005_2025"])
    got = indici[k][2025] - 100
    check(exp is not None and abs(exp - got) < 0.15, "%s: +%.1f%% 2005-2025 come nel riepilogo (%.1f)" % (k, got, exp))
check(abs((indici["generale"][2025] - 100) - 42.7) < 0.15, "indice generale Milano 2005-2025 +42,7%")

wcsv(
    "indici_annui_2005_100.csv",
    ["anno", "generale_milano"] + [k for k, _, _ in ITEMS] + ["generale_italia"],
    [[a, r1(indici["generale"][a], 2)] + [r1(indici[k][a], 2) for k, _, _ in ITEMS] + [r1(indici_ita[a], 2)] for a in range(2005, 2026)],
)

# ----------------------------------------------------------------------------- indice generale mensile (divisione 00, dal 2011)
gen_mens = {}
div_mi = defaultdict(lambda: defaultdict(dict))
for r in rd("nic_milano_divisioni_base2015.csv"):
    v = fl(r["indice_base2015_100"])
    if v:
        div_mi[int(r["divisione"])][r["periodo"]] = v
gen_mens = div_mi[0]
check(gen_mens["2026-09"] > 127 and gen_mens["2026-09"] < 128, "indice generale Milano set 2026 = %.1f" % gen_mens["2026-09"])

# ----------------------------------------------------------------------------- shock energetico
ENE = [("elettricita", "Energia elettrica"), ("gas", "Gas di rete"), ("benzina", "Benzina"), ("gasolio_auto", "Gasolio per auto")]
mesi = []
y, m = 2020, 1
while (y, m) <= (2026, 9):
    mesi.append("%d-%02d" % (y, m))
    m += 1
    if m == 13:
        y, m = y + 1, 1
mens = {k: [r1(voci[k].get(p), 1) for p in mesi] for k, _ in ENE}
mens["generale"] = [r1(gen_mens.get(p), 1) for p in mesi]
wcsv("serie_mensili_energia.csv", ["mese"] + [k for k, _ in ENE] + ["generale_milano"],
     [[p] + [mens[k][i] for k, _ in ENE] + [mens["generale"][i]] for i, p in enumerate(mesi)])

energia = {}
for k, nome in ENE:
    s = voci[k]
    m21, _ = annuo(s, 2021)
    pk_p = max((p for p in s if "2022-01" <= p <= "2023-12"), key=lambda p: s[p])
    energia[k] = {
        "nome": nome,
        "media_2021": r1(m21, 1),
        "picco": r1(s[pk_p], 1),
        "mese_picco": pk_p,
        "picco_su_2021_pct": r1((s[pk_p] / m21 - 1) * 100, 0),
        "media_2025_su_2021_pct": r1((annuo(s, 2025)[0] / m21 - 1) * 100, 0),
        "set_2026": r1(s["2026-09"], 1),
        "set_2026_su_2021_pct": r1((s["2026-09"] / m21 - 1) * 100, 0),
    }
check(energia["elettricita"]["picco"] == 419.4 and energia["elettricita"]["mese_picco"] == "2022-11", "elettricita' picco 419,4 a nov 2022")
check(energia["gas"]["picco_su_2021_pct"] == 161, "gas picco +161% sul 2021")

rj = json.load(open(P / "riepilogo_costo_vita.json", encoding="utf-8"))
infl_picco = rj["inflazione_mensile_picco_2021_2026"]
check(infl_picco == {"mese": "2022-12", "tasso": 12.0}, "inflazione mensile Milano: picco 12,0% a dicembre 2022 (ds1499, dal riepilogo di fase 1)")
check(gen_ann[2022]["tasso_milano"] == 8.1 and gen_ann[2023]["tasso_milano"] == 6.1, "tassi annui 2022 8,1% e 2023 6,1%")

# ----------------------------------------------------------------------------- ATM
atm = rd("atm_tariffe_storico.csv")


def atm_row(titolo, data):
    for r in atm:
        if r["titolo"] == titolo and r["data_inizio"] == data:
            return r
    sys.exit("riga ATM mancante: %s %s" % (titolo, data))


STEPS = [("2002-01", 1.0, 2002), ("2011-09-01", 1.5, 2011), ("2019-07-15", 2.0, 2019), ("2023-01-09", 2.2, 2023)]
liv = {a: gen_ann[a]["milano"] for a in gen_ann}
gradini = []
for d, p, anno in STEPS:
    r = atm_row("biglietto ordinario", d)
    check(float(r["prezzo_eur"]) == p, "biglietto %s = %.2f" % (d, p))
    gradini.append({"data": d, "prezzo": p, "anno": anno, "in_euro_2025": r1(p * liv[2025] / liv[anno], 2)})
infl_02_25 = liv[2025] / liv[2002]
atm_out = {
    "gradini": gradini,
    "oggi": 2.2,
    "inflazione_2002_2025_pct": r1((infl_02_25 - 1) * 100, 1),
    "biglietto_2002_con_inflazione": r1(1.0 * infl_02_25, 2),
    "aumento_biglietto_pct": 120,
    "mensile": {"prima": 35.0, "dal_2019": 39.0, "oggi": 39.0},
    "annuale_oggi": 330.0,
    "mensile_giovani_oggi": 22.0,
    "indice_istat_autobus": {"2005_2025": r1(indici["bus_tram_metro"][2025] - 100, 1)},
    "inflazione_2011_2025_pct": r1((liv[2025] / liv[2011] - 1) * 100, 1),
}
check(atm_out["biglietto_2002_con_inflazione"] == 1.51, "1 euro del 2002 = 1,51 euro del 2025")
check(atm_row("abbonamento mensile urbano ordinario", "2019-07-15")["prezzo_eur"] == "39.0", "mensile 39 euro dal 2019")
wcsv(
    "biglietto_atm.csv",
    ["data_inizio", "titolo", "prezzo_eur", "nota", "fonte"],
    [[r["data_inizio"], r["titolo"], r["prezzo_eur"], r["nota"], r["fonte"].split(" (copia")[0]] for r in atm],
)

# ----------------------------------------------------------------------------- prezzi MIMIT (solo medie)
pm = defaultdict(dict)  # prodotto -> {(anno,mese): medio}
for r in rd("prezzi_medi_milano_mimit.csv"):
    pm[r["prodotto"]][(int(r["anno"]), int(r["mese"]))] = float(r["prezzo_medio_eur"])
pm["Pane"] = {**pm["Pane Fresco"], **pm["Pane Fresco Con Farina Di Grano"]}  # il Ministero ha rinominato il prodotto nel 2022
PREZZI = [
    ("Caffè Espresso Al Bar", "Caffè espresso al bar", "1 tazzina", 2),
    ("Cappuccino Al Bar", "Cappuccino al bar", "1 tazza", 2),
    ("Panino Al Bar", "Panino al bar", "1 panino", 2),
    ("Pane", "Pane fresco", "1 kg", 2),
    ("Pasto In Pizzeria", "Pasto in pizzeria", "1 pasto", 2),
    ("Pasto Al Fast-food", "Pasto al fast food", "1 pasto", 2),
    ("Taxi - Corsa Per L'aeroporto", "Taxi per l'aeroporto", "1 corsa", 0),
    ("Taglio Capelli Uomo", "Taglio di capelli, uomo", "1 taglio", 2),
    ("Cinema - Biglietto", "Cinema, biglietto", "1 biglietto", 2),
]
gen_a, gen_b = gen_mens["2021-01"], gen_mens["2026-09"]
prezzi = []
for key, nome, unita, dec in PREZZI:
    s = pm[key]
    primo = (2021, 1) if (2021, 1) in s else min(s)
    a, b = s[primo], s[(2026, 9)]
    prezzi.append({
        "nome": nome, "unita": unita, "dec": dec,
        "primo_mese": "%d-%02d" % primo, "gen_2021": a, "set_2026": b,
        "var_pct": r1((b / a - 1) * 100, 1),
        # quanto sarebbe salito se avesse seguito i prezzi in generale (indice generale Milano, stesso periodo)
        "infl_pct": r1((gen_b / gen_mens["%d-%02d" % primo] - 1) * 100, 1),
        "con_inflazione": round(a * gen_b / gen_mens["%d-%02d" % primo], 2),
    })
pr = {p["nome"]: p for p in prezzi}
check(pr["Caffè espresso al bar"]["gen_2021"] == 1.02 and pr["Caffè espresso al bar"]["set_2026"] == 1.26, "espresso 1,02 -> 1,26")
check(pr["Caffè espresso al bar"]["var_pct"] == 23.5, "espresso +23,5%")
check(pr["Pane fresco"]["gen_2021"] == 4.11 and pr["Pane fresco"]["set_2026"] == 4.95, "pane 4,11 -> 4,95")
check(pr["Cinema, biglietto"]["primo_mese"] == "2021-05", "cinema: primo mese rilevato maggio 2021")
infl_gen21_set26 = (gen_b / gen_a - 1) * 100
wcsv(
    "prezzi_gen2021_set2026.csv",
    ["prodotto", "unita", "primo_mese", "prezzo_medio_primo_mese_eur", "prezzo_medio_set_2026_eur", "variazione_pct",
     "inflazione_generale_stesso_periodo_pct", "prezzo_se_fosse_salito_come_l_inflazione_eur"],
    [[p["nome"], p["unita"], p["primo_mese"], p["gen_2021"], p["set_2026"], p["var_pct"], p["infl_pct"], p["con_inflazione"]] for p in prezzi],
)

# ----------------------------------------------------------------------------- carburanti
carb = {}
for r in rd("carburanti_milano_mensile.csv"):
    if r["self_service"] == "si" and r["carburante"] in ("Benzina", "Gasolio"):
        carb.setdefault(r["carburante"], {})[r["mese"]] = float(r["prezzo_mediano_eur_litro_media_mensile"])
cm = []
y, m = 2015, 1
while (y, m) <= (2026, 9):
    cm.append("%d-%02d" % (y, m))
    m += 1
    if m == 13:
        y, m = y + 1, 1
for c in carb:
    check(all(p in carb[c] for p in cm), "%s self: tutti i 141 mesi presenti" % c)
carb_out = {}
for c in ("Benzina", "Gasolio"):
    s = carb[c]
    pk = max((p for p in s if p.startswith("2022")), key=lambda p: s[p])
    carb_out[c.lower()] = {
        "serie": [round(s[p], 3) for p in cm],
        "gen_2015": round(s["2015-01"], 3), "picco_2022": round(s[pk], 3), "mese_picco_2022": pk,
        "dic_2025": round(s["2025-12"], 3), "set_2026": round(s["2026-09"], 3),
        "sopra_picco_2022": s["2026-09"] > s[pk],
        "mesi_sopra_picco_2022": [p for p in cm if p > "2022-12" and s[p] > s[pk]],
    }
check(carb_out["benzina"]["set_2026"] == 2.108 and carb_out["benzina"]["picco_2022"] == 2.053, "benzina self set 2026 2,108 sopra il picco 2022 2,053")
check(carb_out["gasolio"]["set_2026"] == 2.265 and carb_out["gasolio"]["picco_2022"] == 2.002, "gasolio self set 2026 2,265 sopra il picco 2022 2,002")
wcsv("carburanti_milano_mensile.csv", ["mese", "benzina_self_eur_litro", "gasolio_self_eur_litro"],
     [[p, round(carb["Benzina"][p], 3), round(carb["Gasolio"][p], 3)] for p in cm])

# ----------------------------------------------------------------------------- affitto e reddito
ar = rd("affitto_vs_reddito.csv")
rent = []
for r in ar:
    rent.append({
        "anno": int(r["anno"]),
        "affitto": fl(r["affitto_civ_60m2_mese"]),
        "affitto_m2": fl(r["affitto_civ_eur_m2_mese"]),
        "reddito": fl(r["reddito_complessivo_mediano_mese_interpolato"]),
        "quota": fl(r["affitto_civ_su_reddito_mediano_pct"]),
        "ore": fl(r["ore_di_lavoro_per_affitto_civ_mediano"]),
    })
rq = {x["anno"]: x for x in rent}
check(rq[2006]["quota"] == 31.9 and rq[2021]["quota"] == 27.8 and rq[2024]["quota"] == 34.5, "quote affitto/reddito 31,9 - 27,8 - 34,5")
check((rq[2006]["ore"], rq[2021]["ore"], rq[2024]["ore"]) == (55.2, 48.1, 59.7), "ore di lavoro 55 - 48 - 60")
check(min(rent, key=lambda x: x["quota"])["anno"] == 2021, "minimo della quota nel 2021")
# ISTAT (indice 'affitti') e OMI (euro/m2) con 2015 = 100, 2006-2024
ist_a = {a: annuo(voci["affitti"], a)[0] for a in range(2006, 2026)}
istat_2015 = {a: ist_a[a] / ist_a[2015] * 100 for a in ist_a}
omi_2015 = {x["anno"]: x["affitto_m2"] / rq[2015]["affitto_m2"] * 100 for x in rent}
check(abs((istat_2015[2025] - 100) - rj["affitti_istat_vs_omi"]["istat_2015_2025"]) < 0.15, "ISTAT affitti 2015-2025 +24,1%")
rent_cmp = {
    "istat_2015_2025_pct": rj["affitti_istat_vs_omi"]["istat_2015_2025"],
    "omi_2015_2025_pct": rj["affitti_istat_vs_omi"]["omi_2015_2025"],
    "istat_2020_2025_pct": rj["affitti_istat_vs_omi"]["istat_2020_2025"],
    "omi_2020_2025_pct": rj["affitti_istat_vs_omi"]["omi_2020_2025"],
    "omi_2026_s1_m2": 14.40, "omi_2026_s1_60m2": 864,
    "istat": {str(a): r1(istat_2015[a], 1) for a in istat_2015 if a <= 2024},
    "omi": {str(a): r1(omi_2015[a], 1) for a in omi_2015},
}
wcsv(
    "affitto_vs_reddito.csv",
    ["anno", "affitto_60m2_mese_eur_stima_OMI", "affitto_eur_m2_mese_OMI", "reddito_mensile_mediano_interpolato_eur",
     "quota_affitto_su_reddito_pct", "ore_di_lavoro_per_un_affitto", "indice_affitti_ISTAT_2015_100", "affitto_OMI_2015_100"],
    [[x["anno"], x["affitto"], x["affitto_m2"], x["reddito"], x["quota"], x["ore"], r1(istat_2015[x["anno"]], 1), r1(omi_2015[x["anno"]], 1)] for x in rent],
)

# ----------------------------------------------------------------------------- Milano contro Italia
mi_it = []
for a0 in (2000, 2005, 2010, 2015, 2020):
    mi = (gen_ann[2025]["milano"] / gen_ann[a0]["milano"] - 1) * 100
    it = (gen_ann[2025]["italia"] / gen_ann[a0]["italia"] - 1) * 100
    mi_it.append({"da": a0, "milano": r1(mi, 1), "italia": r1(it, 1), "diff": r1(r1(mi, 1) - r1(it, 1), 1)})
exp = {2000: (58.0, 63.3), 2005: (42.7, 44.9), 2010: (31.4, 31.8), 2015: (22.2, 22.6), 2020: (19.2, 19.4)}
for x in mi_it:
    check((x["milano"], x["italia"]) == exp[x["da"]], "Milano vs Italia dal %d: %s" % (x["da"], exp[x["da"]]))
ita_div = defaultdict(dict)
for r in rd("nic_italia_divisioni_base2015.csv"):
    if r["area"] == "IT":
        ita_div[int(r["codice_ecoicop"])][r["periodo"]] = float(r["indice_base2015_100"])
DIVN = {1: "Alimentari e bevande", 4: "Abitazione, acqua, elettricità e combustibili", 7: "Trasporti", 11: "Ristoranti e alberghi"}
divs = []
for d, nome in DIVN.items():
    mi = (annuo(div_mi[d], 2025)[0] / annuo(div_mi[d], 2020)[0] - 1) * 100
    it = (annuo(ita_div[d], 2025)[0] / annuo(ita_div[d], 2020)[0] - 1) * 100
    divs.append({"nome": nome, "milano": r1(mi, 1), "italia": r1(it, 1), "diff": r1(r1(mi, 1) - r1(it, 1), 1)})
exp_d = {1: (21.1, 27.3), 4: (47.5, 43.1), 7: (21.1, 19.5), 11: (30.5, 24.2)}
for d, x in zip(DIVN, divs):
    check((x["milano"], x["italia"]) == exp_d[d], "divisione %d 2020-2025: %s" % (d, exp_d[d]))
wcsv("milano_vs_italia.csv", ["confronto", "periodo_da", "periodo_a", "milano_pct", "italia_pct", "differenza_punti"],
     [["indice generale", x["da"], 2025, x["milano"], x["italia"], x["diff"]] for x in mi_it] +
     [[x["nome"], 2020, 2025, x["milano"], x["italia"], x["diff"]] for x in divs])

# ----------------------------------------------------------------------------- riepilogo.json
riepilogo = {
    "generato_da": "costo-vita/scripts/pagina.py",
    "scaricato": "2026-11-01",
    "ultimo_mese": "2026-09",
    "sorpresa": {
        "quota_2006": rq[2006]["quota"], "quota_2021": rq[2021]["quota"], "quota_2024": rq[2024]["quota"],
        "ore_2006": rq[2006]["ore"], "ore_2021": rq[2021]["ore"], "ore_2024": rq[2024]["ore"],
        "affitto_2006": rq[2006]["affitto"], "affitto_2021": rq[2021]["affitto"], "affitto_2024": rq[2024]["affitto"],
        "reddito_2006": rq[2006]["reddito"], "reddito_2021": rq[2021]["reddito"], "reddito_2024": rq[2024]["reddito"],
        "origine": "pulito/affitto_vs_reddito.csv (affitto: stima OMI; reddito: mediana interpolata dalle classi Irpef del Comune)",
    },
    "affitti": {"serie": rent, "confronto": rent_cmp},
    "indici": {
        "anni": list(range(2005, 2026)),
        "voci": [{"chiave": k, "nome": n, "nota": nt, "valori": [r1(indici[k][a], 1) for a in range(2005, 2026)],
                  "var_pct_2005_2025": r1(indici[k][2025] - 100, 0)} for k, n, nt in ITEMS],
        "generale": {"nome": "Indice generale (tutti i prezzi)", "valori": [r1(indici["generale"][a], 1) for a in range(2005, 2026)],
                     "var_pct_2005_2025": r1(indici["generale"][2025] - 100, 1)},
        "generale_italia": {"valori": [r1(indici_ita[a], 1) for a in range(2005, 2026)], "var_pct_2005_2025": r1(indici_ita[2025] - 100, 1)},
        "generale_ricostruito_fino_al": 2010,
    },
    "atm": atm_out,
    "energia": {
        "mesi": mesi,
        "serie": {k: mens[k] for k in mens},
        "voci": energia,
        "inflazione_mensile_picco": infl_picco,
        "tasso_annuo_2022": gen_ann[2022]["tasso_milano"], "tasso_annuo_2023": gen_ann[2023]["tasso_milano"],
        "generale_media_2021": r1(annuo(gen_mens, 2021)[0], 1), "generale_set_2026": r1(gen_mens["2026-09"], 1),
        "inflazione_mensile_set_2026": 3.7,
    },
    "prezzi": {"righe": prezzi, "inflazione_generale_gen2021_set2026_pct": r1(infl_gen21_set26, 1),
               "origine": "Ministero delle Imprese e del Made in Italy, Osservatorio Prezzi e Tariffe: prezzo medio dei locali rilevati a Milano. Pane: prodotto rinominato dal Ministero nel 2022."},
    "carburanti": {"mesi": cm, **carb_out},
    "milano_italia": {"generale": mi_it, "divisioni_2020_2025": divs},
    "controlli": LOG,
}
with open(OUT / "riepilogo.json", "w", encoding="utf-8") as f:
    json.dump(riepilogo, f, ensure_ascii=False, separators=(",", ":"))
print("\n".join(LOG))
print("scritti:", ", ".join(sorted(p.name for p in OUT.iterdir())))
print("inflazione generale gen 2021 -> set 2026: %.1f%%" % infl_gen21_set26)
