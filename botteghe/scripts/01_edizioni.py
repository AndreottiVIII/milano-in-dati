"""Legge tutte le edizioni scaricate dei due elenchi e scrive una tabella lunga normalizzata: pulito/edizioni_lunga.csv
  Elenco B (Regione Lombardia, Negozi e Locali Storici, >=40 anni): copie Wayback 2019-2026 + corrente (CKAN/Socrata 2026-10)
  Elenco A (Albo Botteghe Storiche del Comune, >=50 anni): ds290 (2017) e ds2858 (2024)
Uso: python -I -X utf8 01_edizioni.py <botteghe abs>"""
import sys, os, csv, json, io, datetime, re
B = sys.argv[1]
R = B + "/raw"
rows = []
def num(x):
    try: return float(str(x).replace(",", "."))
    except: return None
def add(el, ed, data_ed, **k):
    d = dict(elenco=el, edizione=ed, data_edizione=data_ed, id="", tipo="", ric="", indirizzo="", denom="", insegna="", anno_inizio="", anno_ric="", cat="", lon=None, lat=None, nil="", stato="", genere="", municipio="")
    d.update(k); rows.append(d)
def csvread(path, delim=None):
    t = open(path, encoding="utf-8-sig").read()
    if delim is None: delim = ";" if t.count(";") > t.count(",") else ("\t" if t.count("\t") > t.count(",") else ",")
    return list(csv.DictReader(io.StringIO(t), delimiter=delim))
# --- Elenco B, copie Wayback
def b_new(r, ed, dt):
    add("B_regione", ed, dt, id=r.get("ID_NLS"), tipo=r.get("TIPO", ""), ric=r.get("RIC"), indirizzo=r.get("INDIR_ORIG"), denom=r.get("DENOM_IMPRES"), insegna=r.get("INSEGNA"),
        anno_inizio=r.get("INIZIO_ATT"), anno_ric=r.get("ANNO_RICONOSCIMENTO", ""), cat=r.get("CAT_MERC", ""), lon=num(r.get("geo_x")), lat=num(r.get("geo_y")), nil=r.get("NIL", ""), municipio=r.get("MUNICIPIO", ""))
W = R + "/wayback/"
for f, dt in [("mi_20190723.csv", "2019-07-23"), ("mi_20240502.csv", "2024-05-02"), ("mi_20250421.csv", "2025-04-21")]:
    for r in csvread(W + f):
        if f == "mi_20190723.csv":
            # nel 2019 geo_y/geo_x sono scambiati (geo_y = longitudine ~9, geo_x = latitudine ~45)
            r2 = dict(r); r2["geo_x"], r2["geo_y"] = r["geo_y"], r["geo_x"]; r = r2
            # solo Milano? la copia 2019 non ha COMUNE: tutte le righe dell'elenco comunale
        b_new(r, f[3:11], dt)
for f, dt in [("mi_20190823.json", "2019-08-23"), ("mi_20191024.json", "2019-10-24"), ("mi_20200810.json", "2020-08-10")]:
    d = json.load(open(W + f, encoding="utf-8"))
    cols = [c["fieldName"] for c in d["meta"]["view"]["columns"]]
    for rr in d["data"]:
        r = dict(zip(cols, rr))
        add("B_regione", f[3:11], dt, id=r.get("id_nls"), ric=r.get("ric"), indirizzo=r.get("indir_orig"), denom=r.get("denom_impres"), insegna=r.get("insegna"), anno_inizio=r.get("inizio_att"), lon=num(r.get("geo_y")), lat=num(r.get("geo_x")))
for f, dt in [("mi_20241130.json", "2024-11-30"), ("mi_20260207.json", "2026-02-07")]:
    for r in json.load(open(W + f, encoding="utf-8")): b_new(r, f[3:11], dt)
# corrente (CKAN ds612 scaricato 2026-11-01, file del 2026-10-19)
for r in csvread(R + "/comune/ds612/ds612_elenco_attivita_storiche_g4x3-hs9b_final.csv"):
    b_new(r, "20261019", "2026-10-19")
# dataset Socrata pccq-vbbq (stesso elenco, ultimo aggiornamento righe 2022-09-15): le coordinate sono rotte, si tengono solo gli ID
for r in csvread(R + "/lombardia/pccq-vbbq/pccq-vbbq.csv"):
    add("B_regione", "20220915", "2022-09-15", id=r.get("ID_NLS"), ric=r.get("RIC"), indirizzo=r.get("INDIR_ORIG"), denom=r.get("DENOM_IMPRES"), insegna=r.get("INSEGNA"), anno_inizio=r.get("INIZIO_ATT"))
# --- Elenco A, Albo comunale
for r in csvread(R + "/comune/ds290/ds290_economia_botteghe_storiche_2017__.csv"):
    ind = (r["INDIRIZZO"] + " " + r["CIVICO"]).strip()
    add("A_albo", "2017", "2017-11-15", id=r["id"], insegna=r["TARGA"], genere=r["GENERE MERCEOLOGICO"], anno_inizio=r["ANNO_ISTITUZIONE"], indirizzo=ind, municipio=r["MUNICIPIO"], nil=r["NIL"], lon=num(r["LONG_X_4326"]), lat=num(r["LAT_Y_4326"]))
for r in csvread(R + "/comune/ds2858/ds290_economia_botteghe_storiche_2024.csv"):
    add("A_albo", "2024", "2024-12-03", id=r["N."], insegna=r["TARGA"], genere=r["GENERE MERCEOLOGICO"], anno_inizio=r["ANNO"], stato=r["STATO"], indirizzo=r["INDIRIZZO"], municipio=r["MUNICIPIO"], nil=r["NIL"], lon=num(r["LONG_X_4326"]), lat=num(r["LAT_Y_4326"]))
os.makedirs(B + "/pulito", exist_ok=True)
keys = list(rows[0].keys())
with open(B + "/pulito/edizioni_lunga.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
import collections
c = collections.Counter((r["elenco"], r["edizione"]) for r in rows)
for k, v in sorted(c.items()): print(k, v)
