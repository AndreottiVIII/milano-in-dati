"""Scrive i file dati e la pagina "BikeMi e bici in citta'" in <docs_dir>/bici/ . Si puo' rilanciare.

Uso (percorsi assoluti):
  python -I -X utf8 pagina.py <bici_dir> <docs_dir>

Legge:  bici/pulito/*.csv, bici/pulito/riepilogo.json (da analisi.py), bici/raw/comune/ds60_itinerari_ciclabili.geojson,
        bici/scripts/pagina_template.html
Scrive: <docs_dir>/bici/index.html e <docs_dir>/bici/data/{riepilogo.json, ciclabili.json, stazioni.json,
        bikemi_serie.csv, ciclabili_km_per_anno.csv, stazioni_bikemi.csv, stazioni_movimento_2013.csv, profilo_orario_2011_2013.csv,
        giorno_settimana_2013.csv, mese_2013.csv, temperatura_2013_feriali.csv}
Dati aggregati: nessun dato di singoli utenti esiste nelle fonti. Il feed in tempo reale di BikeMi (GBFS) NON viene ripubblicato:
in pagina compaiono solo i totali della fotografia del 2 novembre 2026.
"""
import sys, os, json, csv, shutil
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping

B, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(B, "pulito")
OUT = os.path.join(DOCS, "bici", "data")
os.makedirs(OUT, exist_ok=True)

R = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
ser = pd.read_csv(os.path.join(PU, "bikemi_serie.csv"), sep=";")
km = pd.read_csv(os.path.join(PU, "ciclabili_km_per_anno.csv"), sep=";")

# --- riepilogo.json della pagina: i numeri dell'analisi + le due tabelle usate dai grafici
P = dict(R)
P["serie"] = json.loads(ser.where(ser.notna(), None).to_json(orient="records"))
P["km_anno"] = json.loads(km.to_json(orient="records"))
oth = pd.read_csv(os.path.join(PU, "altri_sharing_noleggi_giorno.csv"), sep=";")
P["altri_sharing"] = json.loads(oth.where(oth.notna(), None).to_json(orient="records"))
json.dump(P, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# --- stazioni (ds65) con l'indice di movimento 2013 dove le stazioni si abbinano per numero
st = pd.read_csv(os.path.join(B, "raw", "comune", "ds65_1.csv"), sep=";", dtype={"numero": str})
mv = pd.read_csv(os.path.join(PU, "stazioni_movimento_2013.csv"), sep=";", dtype={"numero_ds65": str})
mv = mv.dropna(subset=["numero_ds65"]).set_index("numero_ds65").indice_per_giorno
st["indice_2013"] = st.numero.map(mv).round(1)
st.drop(columns=["Location"]).to_csv(os.path.join(OUT, "stazioni_bikemi.csv"), sep=";", index=False, encoding="utf8")
rows = []
for r in st.itertuples():
    rows.append([r.numero, r.nome, round(r.LONG_X_4326, 5), round(r.LAT_Y_4326, 5), int(r.stalli),
                 (None if pd.isna(r.anno) else int(r.anno)), int(r.zd_attuale), r.tipo,
                 (None if pd.isna(r.indice_2013) else float(r.indice_2013))])
json.dump({"campi": ["numero", "nome", "lon", "lat", "stalli", "anno", "municipio", "tipo", "indice_2013"], "righe": rows},
          open(os.path.join(OUT, "stazioni.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# --- itinerari ciclabili: geometrie semplificate (circa 3 m), 5 decimali
g = json.load(open(os.path.join(B, "raw", "comune", "ds60_itinerari_ciclabili.geojson"), encoding="utf8"))
TIP = {"ciclabile sede propria": 0, "ciclabile segnaletica": 1, "promiscuo pedoni": 2, "promiscuo veicoli": 3}
feats = []
for f in g["features"]:
    p = f["properties"]
    geom = shape(f["geometry"]).simplify(0.00003, preserve_topology=False)
    if geom.is_empty: continue
    m = mapping(geom)
    def rnd(c):
        return [round(c[0], 5), round(c[1], 5)]
    if m["type"] == "LineString":
        co = [[rnd(c) for c in m["coordinates"]]]
    else:
        co = [[rnd(c) for c in ln] for ln in m["coordinates"]]
    feats.append({"type": "Feature", "geometry": {"type": "MultiLineString", "coordinates": co},
                  "properties": {"t": TIP[p["tipologia"]], "a": int(p["fine_lavor"]), "n": p["anagrafica"].title(),
                                 "l": int(p["lunghezza"]), "o": int(p["norma"] == "ordinanza lavori stradali")}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "ciclabili.json"), "w", encoding="utf8"),
          ensure_ascii=False, separators=(",", ":"))

# --- csv per chi vuole scaricare
for nome in ("bikemi_serie.csv", "ciclabili_km_per_anno.csv", "stazioni_movimento_2013.csv", "profilo_orario_2011_2013.csv",
             "giorno_settimana_2013.csv", "mese_2013.csv", "temperatura_2013_feriali.csv", "stazioni_cumulate_per_anno_installazione.csv"):
    shutil.copyfile(os.path.join(PU, nome), os.path.join(OUT, nome))

# --- pagina
tpl = open(os.path.join(B, "scripts", "pagina_template.html"), encoding="utf8").read()
os.makedirs(os.path.join(DOCS, "bici"), exist_ok=True)
open(os.path.join(DOCS, "bici", "index.html"), "w", encoding="utf8", newline="\n").write(tpl)
for fn in os.listdir(OUT):
    print(fn, os.path.getsize(os.path.join(OUT, fn)))
