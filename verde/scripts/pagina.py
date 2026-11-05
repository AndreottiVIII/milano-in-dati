"""Scrive i file dati della pagina "Parchi e verde" (docs/verde/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <verde_dir> <milano_in_dati_dir> <docs_dir>

Legge verde/pulito/ (da build.py) e il file dei poligoni dei NIL; ricalcola alcuni totali dai file per controllo (assert).
Scrive in <docs_dir>/verde/data/: nil.geojson (confini NIL semplificati con i valori), parchi.geojson (i parchi del Comune ds89, uniti per parco e semplificati),
nil_verde.csv, parchi_ds89.csv, aree_ds339_localizzate.csv, ds1323_pulito.csv, schede_per_anno.csv, riepilogo.json (tutti i numeri della pagina, con l'origine).
Nessun dato personale. I punti degli alberi non vengono usati qui (solo le quote per quartiere gia' calcolate in build.py).
"""
import sys, os, json, shutil, warnings
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely import make_valid

warnings.filterwarnings("ignore")
V, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(V, "pulito")
OUT = os.path.join(DOCS, "verde", "data")
os.makedirs(OUT, exist_ok=True)
AVV = []


def check(nome, calc, atteso, tol=0.0):
    ok = abs(calc - atteso) <= tol
    if not ok:
        AVV.append(nome)
    print(("ok  " if ok else "!!  ") + f"{nome}: {calc} (atteso {atteso})")


C = json.load(open(os.path.join(PU, "controlli.json"), encoding="utf8"))
CONF = json.load(open(os.path.join(PU, "confronti.json"), encoding="utf8"))
nv = pd.read_csv(os.path.join(PU, "nil_verde.csv"), sep=";")
assert len(nv) == 88
S = pd.read_csv(os.path.join(PU, "serie_citta.csv"), sep=";")
SP = pd.read_csv(os.path.join(PU, "schede_per_anno.csv"), sep=";")

# controlli: i totali di build.py tornano con la tabella
check("somma verde B (km2)", round(nv.verde_B_m2.sum() / 1e6, 3), C["standard9_B"]["citta_km2"], 0.002)
check("somma verde A (km2)", round(nv.verde_A_m2.sum() / 1e6, 3), C["standard9_A"]["citta_km2"], 0.002)
check("residenti", int(nv.abitanti_2024.sum()), C["popolazione_2024_ds205"])
check("m2 per abitante B citta'", round(nv.verde_B_m2.sum() / nv.abitanti_2024.sum(), 2), C["standard9_B"]["citta_m2_ab"], 0.006)
check("NIL sotto 9 (B, classifica)", int(((nv.in_classifica == 1) & (nv.m2_ab_B < 9)).sum()), C["standard9_B"]["sotto_9"])

nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}


def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]


def R(x, d=1):
    return None if pd.isna(x) else round(float(x), d)


feats = []
for r in nv.sort_values("nome").itertuples():
    g = mapping(geom[int(r.id_nil)].simplify(0.00003, preserve_topology=True))
    p = {"i": int(r.id_nil), "n": r.nome, "ab": int(r.abitanti_2024), "abkm2": R(r.abitanti_per_km2, 0), "cl": int(r.in_classifica),
         "vA": R(r.verde_A_m2, 0), "mA": R(r.m2_ab_A, 1), "pA": R(r.pct_area_A, 1),
         "vB": R(r.verde_B_m2, 0), "mB": R(r.m2_ab_B, 1), "pB": R(r.pct_area_B, 1),
         "mBs": R(r.m2_ab_B_senza_grandi, 1), "mAs": R(r.m2_ab_A_senza_grandi, 1),
         "pk": r.parco_piu_grande if isinstance(r.parco_piu_grande, str) else "", "pkq": R(r.parco_piu_grande_quota_A_pct, 0),
         "min": R(r.min_parco_mediana, 1), "mt": R(r.metri_parco_circa, 0), "q5": R(r.quota_entro5min_pct, 0), "q10": R(r.quota_entro10min_pct, 0), "q15": R(r.quota_entro15min_pct, 0),
         "alb": R(r.alberi_per_1000ab, 0), "albkm2": R(r.alberi_per_km2, 0), "suolo": R(r.suolo_consumato_2025_pct, 1), "cal": R(r.calore_esposizione, 2), "ivs": R(r.indice_verde_spotted, 1),
         "gi": int(r.gioco_n), "ca": int(r.cani_n), "co": int(r.condivisi_n), "or": int(r.orti_n), "s16": int(r.schede_2016_2024), "s06": int(r.schede_2006_2015), "s05": int(r.schede_fino_2005),
         "osm": R(r.osm_park_m2_ab, 1)}
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# parchi del Comune (ds89) uniti per parco
d89 = json.load(open(os.path.join(V, "raw", "comune_ds89", "parchi.geojson"), encoding="utf8"))
by = {}
for f in d89["features"]:
    p = f["properties"]
    by.setdefault((p["ZONA"], p["CODICE_ARE"]), {"n": p["PARCO"].title(), "g": []})["g"].append(make_valid(shape(f["geometry"])))
pf = []
for k, v in by.items():
    g = unary_union(v["g"]).simplify(0.00003, preserve_topology=True)
    gm = mapping(g)
    pf.append({"type": "Feature", "properties": {"n": v["n"]}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": pf}, open(os.path.join(OUT, "parchi.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

for f in ["nil_verde.csv", "parchi_ds89.csv", "aree_ds339_localizzate.csv", "ds1323_pulito.csv", "schede_per_anno.csv", "serie_citta.csv"]:
    shutil.copyfile(os.path.join(PU, f), os.path.join(OUT, f))

# ---- riepilogo.json
rk = nv[nv.in_classifica == 1]
S2 = S.set_index("anno")
d14, d24 = S2.loc[2014], S2.loc[2024]
sp = SP[(SP.anno >= 2006)].groupby("anno").schede.sum()
sp_all = SP.groupby("anno").schede.sum()
tipi = SP.groupby("tipo").schede.sum().to_dict()
rim = {
    "meta": {
        "nota": "Tutti i numeri della pagina 'Parchi e verde'. Origine = file in verde/pulito/ (e programmi verde/scripts/build.py, pagina.py).",
        "scaricato": "2026-11-02 (Comune di Milano ds89, ds52, ds724, ds2186, ds2187, ds2811, OpenStreetMap/Overpass); 2026-11-01 (ds339, ds1323, ds2926, ds2927, ds2484, ds2813: pagina alberi)",
        "residenti": "ds205 anno 2024, alberi/pulito/nil_alberi.csv",
    },
    "citta": {
        "residenti": C["popolazione_2024_ds205"], "km2": C["area_citta_km2_poligoni_nil"],
        "A": C["standard9_A"], "B": C["standard9_B"], "nil_sotto_5000": C["nil_sotto_5000_ab"],
        "ds89": {"pezzi": C["ds89_pezzi"], "parchi": C["ds89_parchi_con_nome"], "somma_pezzi_km2": C["ds89_somma_pezzi_km2"], "unione_km2": C["ds89_unione_km2"], "oltre_40ha": C["parchi_oltre_40ha"]},
        "ds339": {"aree": C["ds339_aree"], "km2": C["ds339_totale_km2"], "classi123_aree": C["ds339_classi_1_2_3_aree"], "classi123_km2": C["ds339_classi_1_2_3_km2"],
                  "per_classe_km2": C["ds339_per_classe_km2"], "in_ds89_aree": C["ds339_cl123_in_ds89_aree"], "non_in_ds89_aree": C["ds339_non_in_ds89_aree"], "non_in_ds89_km2": C["ds339_non_in_ds89_km2"],
                  "localizzate_alberi_aree": C["localizzate_con_alberi_aree"], "localizzate_alberi_km2": C["localizzate_con_alberi_km2"], "localizzate_poligono_aree": C["localizzate_con_poligono_aree"],
                  "su_piu_nil": C["localizzate_su_piu_nil_aree"], "non_localizzate_aree": C["non_localizzate_aree"], "non_localizzate_km2": C["non_localizzate_km2"],
                  "non_localizzate_top": C["non_localizzate_top"], "senza_superficie": C["ds339_senza_superficie"], "convalida_alberi": C["convalida_alberi_su_ds89"]},
        "distanza": C["distanza_citta"],
    },
    "serie": {
        "ds1323_2011_2024": S.round(1).to_dict("records"),
        "parchi_attrezzato_km2_2014": round(d14.ds1323_parchi_attrezzato_mq / 1e6, 2), "parchi_attrezzato_km2_2024": round(d24.ds1323_parchi_attrezzato_mq / 1e6, 2),
        "crescita_2014_2024_km2": round((d24.ds1323_parchi_attrezzato_mq - d14.ds1323_parchi_attrezzato_mq) / 1e6, 2),
        "crescita_2014_2024_pct": round(100 * (d24.ds1323_parchi_attrezzato_mq / d14.ds1323_parchi_attrezzato_mq - 1), 1),
        "ds1323_anomalie": {"righe_5_campi": C["ds1323_righe_anomale"], "valori_vuoti": C["ds1323_valori_vuoti"]},
        "istat_mq_ab_2011": 17.2, "istat_mq_ab_2023": 18.8, "istat_pct_2011": 12.0, "istat_pct_2023": 14.1,
    },
    "schede": {"per_tipo": {k: int(v) for k, v in tipi.items()}, "per_anno": {int(k): int(v) for k, v in sp_all.items()},
               "per_anno_tipo": {int(a): {t: int(n) for t, n in g.groupby("tipo").schede.sum().items()} for a, g in SP.groupby("anno")}, "totali": C["schede_totali"],
               "dal_2016": int(SP[SP.anno >= 2016].schede.sum()), "tra_2006_2015": int(SP[(SP.anno >= 2006) & (SP.anno <= 2015)].schede.sum())},
    "confronti": CONF,
    "osm": C["osm"],
    "decreto": {"titolo": "Decreto interministeriale 2 aprile 1968, n. 1444, art. 3", "lettera_c": "mq 9,00 di aree per spazi pubblici attrezzati a parco e per il gioco e lo sport, effettivamente utilizzabili per tali impianti con esclusione di fasce verdi lungo le strade",
                "totale": "mq 18 per abitante (insediato o da insediare) per spazi pubblici o riservati alle attivita' collettive, a verde pubblico o a parcheggio",
                "fonte": "https://www.bosettiegatti.eu/info/norme/statali/1968_1444.htm (trascrizione del testo; verificato il 2/11/2026)"},
    "civici": {"residenziali": C["civici_residenziali"], "senza_tempo_parco": C["civici_residenziali_senza_tempo_parco"], "senza_nil": C["civici_residenziali_senza_nil"]},
    "nil_senza_verde": {"A": C["nil_senza_verde_A"], "B": C["nil_senza_verde_B"]},
}
def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if (np.isnan(o) or np.isinf(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    return o


json.dump(clean(rim), open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, allow_nan=False)
print("avvisi:", AVV)
print({f: os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)})
