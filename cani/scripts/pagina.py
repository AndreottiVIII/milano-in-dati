"""Scrive i file dati della pagina "Cani di Milano" (docs/cani/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <cani_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): cani/pulito/*.csv e riepilogo.json, cani/raw/comune_ds52/ds52_aree_fruizione_cani.geojson (poligoni),
il file dei poligoni NIL di citta-15-minuti e censimenti/pulito/nil_2021_anagrafica.csv (nomi dei NIL).
Scrive in <docs_dir>/cani/data/: riepilogo.json (tutti i numeri della pagina, con origine), aree.geojson (423 aree cani,
poligoni semplificati di circa 1 m), nil.geojson (88 quartieri semplificati), e copie dei csv puliti.
ds52 e' CC BY: le aree si possono ripubblicare. Nessun dato su singoli cani esiste o e' ripubblicato.
"""
import sys, os, json, csv, shutil
import pandas as pd
import shapely
from shapely.geometry import shape, mapping

C, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(C, "pulito")
OUT = os.path.join(DOCS, "cani", "data")
os.makedirs(OUT, exist_ok=True)
assert int(shapely.__version__.split(".")[0]) >= 2

AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

def R(x, d=1):
    return None if x is None or pd.isna(x) else round(float(x), d)

RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
aree = pd.read_csv(os.path.join(PU, "aree_cani.csv"), sep=";")
per_nil = pd.read_csv(os.path.join(PU, "aree_cani_per_nil.csv"), sep=";")
per_mun = pd.read_csv(os.path.join(PU, "aree_cani_per_municipio.csv"), sep=";")
serie = pd.read_csv(os.path.join(PU, "serie_aree_cani_per_anno_scheda.csv"), sep=";")
stampa = pd.read_csv(os.path.join(PU, "totali_pubblicati.csv"), sep=";")
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
NOMI = dict(zip(ana.nil, ana.nil_nome))

# ------------------------------------------------------------ controlli contro la fase 1
check("aree", len(aree), RIEP["ds52"]["righe"])
check("mq totali", round(aree.area_mq.sum()), RIEP["ds52"]["mq_totali"], 1)
check("id_area distinti", aree.id_area.nunique(), RIEP["ds52"]["id_area_unici"])
check("NIL senza aree e < 5000", int(((per_nil.aree_cani == 0)).sum()), 12)
check("NIL in classifica", int((per_nil.abitanti_2024_ds205 >= 5000).sum()), 64)
check("righe con data convenzionale", int(aree.flag_data_convenzionale.sum()), RIEP["ds52"]["righe_con_data_convenzionale"])
check("aree per 100mila 2024", round(100000 * len(aree) / RIEP["ds205_totali"]["2024"], 1), RIEP["comune_aree"]["aree_per_100mila_2024"], 0.05)
check("serie 2024", int(serie.aree_con_scheda_entro_anno.iloc[-1]), RIEP["serie_aree"]["2024"])
check("somma aree per NIL", int(per_nil.aree_cani.sum()), 423)
check("somma aree per municipio", int(per_mun.aree_cani.sum()), 423)

# ------------------------------------------------------------ aree.geojson
raw = json.load(open(os.path.join(C, "raw", "comune_ds52", "ds52_aree_fruizione_cani.geojson"), encoding="utf8"))
gmap = {}
for f in raw["features"]:
    gmap[int(f["properties"]["obj_id"])] = shape(f["geometry"])
check("poligoni ds52", len(gmap), 423)

def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]

def geom_json(g, tol):
    s = g.simplify(tol, preserve_topology=True)
    if s.is_empty or not s.is_valid:
        s = g
    gj = mapping(s)
    return {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}

feats = []
for _, r in aree.sort_values("obj_id").iterrows():
    p = {"i": int(r.obj_id), "l": r.localita, "m": int(r.municipio), "mq": int(round(r.area_mq)),
         "a": None if pd.isna(r.anno_scheda) else int(r.anno_scheda), "c": int(r.flag_data_convenzionale),
         "n": int(r.id_nil), "x": round(float(r.lon), 5), "y": round(float(r.lat), 5)}
    feats.append({"type": "Feature", "properties": p, "geometry": geom_json(gmap[int(r.obj_id)], 0.00001)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "aree.geojson"), "w", encoding="utf8"),
          ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------ nil.geojson
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
mun_per_nil = aree.groupby("id_nil").municipio.agg(lambda s: sorted(set(int(x) for x in s))).to_dict()
nfeats, nrows = [], []
for _, r in per_nil.sort_values("nil").iterrows():
    i = int(r.id_nil)
    nome = NOMI.get(i) or str(r.nil).title()
    cl = 1 if r.abitanti_2024_ds205 >= 5000 else 0
    p = {"i": i, "n": nome, "ab": int(r.abitanti_2024_ds205), "km2": R(r.area_km2, 2), "a": int(r.aree_cani), "mq": int(r.mq_aree_cani),
         "p": R(r.aree_cani_per_100mila_ab, 1) if cl else None, "mm": R(r.mq_aree_cani_per_abitante, 2) if cl else None,
         "ap": None if pd.isna(r.abitanti_per_area_cani) else int(r.abitanti_per_area_cani), "cl": cl, "mun": mun_per_nil.get(i, [])}
    nfeats.append({"type": "Feature", "properties": p, "geometry": geom_json(geom[i], 0.00003)})
    nrows.append({"id_nil": i, "nil": nome, "abitanti_2024_ds205": p["ab"], "area_km2": R(r.area_km2, 3), "aree_cani": p["a"], "mq_aree_cani": p["mq"],
                  "aree_cani_per_100mila_ab": p["p"], "mq_aree_cani_per_abitante": p["mm"], "abitanti_per_area_cani": p["ap"],
                  "in_classifica_almeno_5000_abitanti": cl})
json.dump({"type": "FeatureCollection", "features": nfeats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"),
          ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(nrows).to_csv(os.path.join(OUT, "aree_cani_per_nil.csv"), index=False, sep=";")
NIL = {p["properties"]["i"]: p["properties"] for p in nfeats}

# ------------------------------------------------------------ riepilogo.json
ab24 = RIEP["ds205_totali"]["2024"]
cl = [p for p in NIL.values() if p["cl"] == 1]
cl.sort(key=lambda p: p["p"])
check("NIL in classifica (lista)", len(cl), 64)

def row_nil(p):
    return {"i": p["i"], "n": p["n"], "aree": p["a"], "ab": p["ab"], "p": p["p"], "mm": p["mm"], "mq": p["mq"]}

bot = [row_nil(p) for p in cl[:8]]
top = [row_nil(p) for p in cl[::-1][:8]]
check("minimo", cl[0]["p"], 4.6, 0.05)
check("massimo", cl[-1]["p"], 79.2, 0.05)
check("rapporto max/min", round(cl[-1]["p"] / cl[0]["p"]), 17)
check("De Angeli nome", int(cl[0]["n"].lower().startswith("de angeli")), 1)
check("Lorenteggio massimo", int(cl[-1]["n"].lower().startswith("lorenteggio")), 1)
sei = [p["n"] for p in cl[:6]]
check("i sei con meno aree: ", len(sei), 6)

pop_nil_senza = [p for p in NIL.values() if p["cl"] == 0]
senza_aree = [p for p in NIL.values() if p["a"] == 0]
check("NIL senza aree", len(senza_aree), 12)
check("NIL con meno di 5000", len(pop_nil_senza), 24)
check("senza aree tutti sotto 5000", sum(1 for p in senza_aree if p["cl"] == 0), 12)

mun_rows = []
for _, r in per_mun.iterrows():
    m = int(r.municipio)
    g = aree[aree.municipio == m]
    grandi = g[g.area_mq > 10000]
    mun_rows.append({"m": m, "aree": int(r.aree_cani), "mq": int(r.mq_aree_cani), "id_area": int(r.id_area_distinti),
                     "ab": int(r.abitanti_censimento_2023), "p": R(r.aree_cani_per_100mila_ab, 1), "mm": R(r.mq_per_abitante, 3),
                     "ap": int(r.abitanti_per_area_cani),
                     "grandi_n": int(len(grandi)), "grandi_mq": int(round(grandi.area_mq.sum())),
                     "mq_senza_grandi_per_ab": R((g.area_mq.sum() - grandi.area_mq.sum()) / r.abitanti_censimento_2023, 3)})
mm = {r["m"]: r for r in mun_rows}
check("municipio 9 m2 per ab", mm[9]["mm"], 1.142, 0.001)
check("municipio 3 m2 per ab", mm[3]["mm"], 0.235, 0.001)

# serie
sr = [{"anno": int(r.anno), "aree": int(r.aree_con_scheda_entro_anno), "mq": int(r.mq), "ab": int(r.abitanti_ds205),
       "p": R(r.aree_per_100mila_ab, 1), "nuove": int(r.nuove_schede_nell_anno)} for _, r in serie.iterrows()]
check("2011", sr[0]["aree"], 200)
check("2024", sr[-1]["aree"], 422)
ab_crescita = round(100 * (sr[-1]["ab"] / sr[0]["ab"] - 1), 1)
check("crescita residenti 2011-2024 %", ab_crescita, 4.9, 0.05)
aree_crescita = round(100 * (sr[-1]["aree"] / sr[0]["aree"] - 1), 1)
n_2003 = int((aree.anno_scheda == 2003).sum())
n_entro_2010 = int((aree.anno_scheda <= 2010).sum())
check("schede 2003", n_2003, 77)
# controllo coerenza: 200 al 2011 = <=2010 + nuove 2011
check("coerenza 2011", n_entro_2010 + sr[0]["nuove"], sr[0]["aree"])

# stampa
st = []
for _, r in stampa.iterrows():
    st.append({"anno": r.anno_riferimento, "ambito": r.ambito, "grandezza": r.grandezza, "valore": int(r.valore), "fonte": r.fonte,
               "per100": None if pd.isna(r.cani_per_100_abitanti_ds205) else float(r.cani_per_100_abitanti_ds205)})

osm = RIEP["osm"]
RIS = {
    "scaricato": "1 novembre 2026",
    "comune": {"aree": len(aree), "id_area": int(aree.id_area.nunique()), "mq": int(round(aree.area_mq.sum())),
               "mq_mediana": R(aree.area_mq.median(), 0), "mq_media": R(aree.area_mq.mean(), 0),
               "ab_2024": ab24, "per100k": RIEP["comune_aree"]["aree_per_100mila_2024"], "ab_per_area": RIEP["comune_aree"]["abitanti_per_area_ds205_2024"],
               "mq_per_ab": RIEP["comune_aree"]["mq_per_abitante_2024"],
               "origine": "aree_cani.csv (423 righe, campo area_mq); abitanti ds205 2024 in riepilogo.json fase 1 (campo ds205_totali.2024)"},
    "nil": {"n": len(NIL), "in_classifica": len(cl), "sotto_5000": len(pop_nil_senza), "senza_aree": len(senza_aree),
            "meno": bot, "piu": top, "rapporto": round(cl[-1]["p"] / cl[0]["p"]),
            "mediana_p": R(pd.Series([p["p"] for p in cl]).median(), 1),
            "multi_municipio": RIEP["ds52"]["nil_con_aree_in_piu_municipi"],
            "max_assoluto": [{"n": p["n"], "aree": p["a"], "p": p["p"], "mm": p["mm"]} for p in sorted(NIL.values(), key=lambda p: -p["a"])[:3]],
            "origine": "aree_cani_per_nil.csv (campi aree_cani, abitanti_2024_ds205, aree_cani_per_100mila_ab); solo NIL con almeno 5.000 abitanti"},
    "municipi": mun_rows,
    "municipi_origine": "aree_cani_per_municipio.csv; abitanti = censimento permanente 2023 (censimenti/pulito/indicatori_municipi.csv, campo pop)",
    "serie": sr,
    "serie_nota": {"crescita_ab_pct": ab_crescita, "crescita_aree_pct": aree_crescita, "riga_senza_data": int(aree.anno_scheda.isna().sum()),
                   "convenzionali": int(aree.flag_data_convenzionale.sum()), "schede_2003": n_2003, "schede_entro_2010": n_entro_2010,
                   "data_max": "20/9/2024",
                   "origine": "serie_aree_cani_per_anno_scheda.csv; conteggio per anno di data_ini (campo data_scheda in aree_cani.csv)"},
    "stampa": st,
    "stampa_rapporti": {"lombardia_abitanti_per_cane": 5.6, "milano_abitanti_per_cane_stampa": 11,
                        "milano_per100_calcolato_2020": 8.49, "lombardia_per100": 17.9,
                        "milano_abitanti_per_cane_calcolato": round(100 / 8.49, 1),
                        "origine": "cani/NOTE.md par. 4.5: rapporti riportati dalla stampa (Legambiente X rapporto via Il Giorno 17/1/2022), non stanno in nessun csv; 17,9 e 8,49 per 100 sono del 2020 (8,49 calcolato da noi: 118.292 / residenti ds205 2020)"},
    "legambiente_2020": {"aree": 403, "abitanti_per_area": 3411, "ds52_scheda_fino_2020": 383,
                         "origine": "cani/NOTE.md par. 4.1 (Legambiente X rapporto, dati 2020); 383 = serie_aree_cani_per_anno_scheda.csv, anno 2020"},
    "legambiente_xv": {"comuni_che_sanno": 316, "comuni": 771, "pct": round(100 * 316 / 771),
                       "origine": "cani/NOTE.md par. 6.4 (XV rapporto Legambiente Animali in Citta, PDF in cani/raw/legambiente): 316 comuni su 771 sanno quanti cani hanno in anagrafe"},
    "patentino": {"razze": 27, "dal": "febbraio 2020", "origine": "cani/NOTE.md par. 6.9 (regolamento comunale); nessun dato aperto sui cani con patentino"},
    "osm": {"elementi": osm["elementi"], "dentro_milano": osm["dentro_confini_milano"], "entro_50m": osm["dentro_milano_entro_50m_da_ds52"],
            "ds52_con_osm": osm["aree_ds52_con_osm_entro_50m"], "origine": "riepilogo.json fase 1, campo osm (OpenStreetMap leisure=dog_park, ODbL, 1/11/2026)"},
    "trappole": {"aree_sotto_100": RIEP["ds52"]["aree_mq_sotto_100"], "aree_sopra_10000": RIEP["ds52"]["aree_mq_sopra_10000"],
                 "punto_csv_fuori_poligono": RIEP["ds52"]["punto_csv_fuori_poligono"], "nil_per_vicinanza": RIEP["ds52"]["nil_per_vicinanza"]},
    "grandi_aree": [{"l": r.localita, "m": int(r.municipio), "mq": int(round(r.area_mq))} for _, r in aree[aree.area_mq > 10000].sort_values("area_mq", ascending=False).iterrows()],
    "ds205": {str(a): v for a, v in RIEP["ds205_totali"].items()},
}
json.dump(RIS, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------ copie dei csv
for nome in ["aree_cani.csv", "aree_cani_per_municipio.csv", "serie_aree_cani_per_anno_scheda.csv", "totali_pubblicati.csv"]:
    shutil.copyfile(os.path.join(PU, nome), os.path.join(OUT, nome))

for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
if AVVISI:
    print("\nAVVISI:")
    for a in AVVISI:
        print(" ", a)
    sys.exit(1)
print("\ntutti i controlli ok")
