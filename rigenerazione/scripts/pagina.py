"""Scrive i file dati della pagina "I progetti di rigenerazione" (docs/rigenerazione/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <rigenerazione_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): rigenerazione/pulito/{ambiti_progetti.csv, nil_rigenerazione.csv, tipi.csv, riepilogo.json},
rigenerazione/raw/pgt/*.geojson (PGT Milano 2030, Tavola R02, CC BY 4.0), i confini NIL di citta-15-minuti.
Scrive in <docs_dir>/rigenerazione/data/: riepilogo.json, ambiti.geojson (un poligono per progetto, semplificato), nil.geojson,
progetti.csv, nil.csv, tipi.csv. Nessun dato del servizio "Mappa dei progetti di Rigenerazione urbana" (Atlante).
"""
import sys, os, json
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

R, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU, RAW = os.path.join(R, "pulito"), os.path.join(R, "raw", "pgt")
OUT = os.path.join(DOCS, "rigenerazione", "data"); os.makedirs(OUT, exist_ok=True)

AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
prog = pd.read_csv(os.path.join(PU, "ambiti_progetti.csv"), sep=";")
nil = pd.read_csv(os.path.join(PU, "nil_rigenerazione.csv"), sep=";")
tipi = pd.read_csv(os.path.join(PU, "tipi.csv"), sep=";")

# ------------------------------------------------ controlli di coerenza
check("progetti", len(prog), RIEP["n_progetti"])
check("somma ha progetti >= unione (sovrapposizioni)", int(prog.area_ha.sum() >= RIEP["unione_ha"]), 1)
check("ha ambiti per NIL = unione", round(nil.ambiti_ha.sum(), 0), round(RIEP["unione_ha"], 0), 3)
check("nuovo suolo per NIL = citta' (244,18)", round(nil.nuovo_nil_ha.sum(), 2), round(RIEP["suolo"]["citta"]["nuovo"], 2), 0.05)
check("nuovo suolo negli ambiti per NIL", round(nil.nuovo_in_ambiti_ha.sum(), 1), round(RIEP["suolo"]["ambiti"]["nuovo"], 1), 0.1)
check("raster ambiti ha vs unione", round(RIEP["suolo"]["ambiti"]["ha"], 0), round(RIEP["unione_ha"], 0), 5)

# ------------------------------------------------ ambiti.geojson: un poligono per progetto
feats = json.load(open(os.path.join(RAW, "r02_provvedimenti_in_itinere.geojson"), encoding="utf8"))["features"]
by = {}
for f in feats:
    if not f["geometry"] or not f["geometry"].get("coordinates"): continue
    p = f["properties"]
    g = shape(f["geometry"]); g = g if g.is_valid else g.buffer(0)
    by.setdefault((p["tipopianif"], (p["nome"] or "").strip() or "(senza nome)"), []).append(g)
key = {(r.tipo, r.nome): r for r in prog.itertuples()}
assert set(by) == set(key), (len(by), len(key))
out = []
for k, gs in by.items():
    r = key[k]; g = unary_union(gs).simplify(0.00003, preserve_topology=True)
    out.append({"type": "Feature", "geometry": mapping(shapely.set_precision(g, 0.000001)),
                "properties": {"n": r.nome, "t": r.tipo, "g": r.gruppo, "s": r.stato, "ha": round(float(r.area_ha), 2), "q": r.nil if isinstance(r.nil, str) else "",
                               "nu": round(float(r.nuovo_2012_2025_ha), 2), "c12": None if pd.isna(r.consumato_2012_pct) else round(float(r.consumato_2012_pct), 1)}})
out.sort(key=lambda f: -f["properties"]["ha"])  # i grandi sotto, i piccoli sopra
out.reverse()
json.dump({"type": "FeatureCollection", "features": out}, open(os.path.join(OUT, "ambiti.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------ nil.geojson
nf = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
nd = nil.set_index("id_nil")
def num(v, d=2):
    return None if pd.isna(v) else round(float(v), d)
nfe = []
for f in nf["features"]:
    i = int(f["properties"]["ID_NIL"]); r = nd.loc[i]
    g = shape(f["geometry"]).simplify(0.00004, preserve_topology=True)
    nfe.append({"type": "Feature", "geometry": mapping(shapely.set_precision(g, 0.000001)), "properties": {
        "i": i, "n": r.nil, "ha": num(r.area_ha, 1), "am": num(r.ambiti_ha, 1), "ap": num(r.ambiti_pct, 1), "np": int(r.n_progetti), "nu": num(r.nuovo_nil_ha, 2),
        "nua": num(r.nuovo_in_ambiti_ha, 2), "pv": num(r.prezzo_var, 1), "ab": num(r.nuove_abitazioni_ogni_1000_abitanti_2024, 1), "na": None if pd.isna(r.nuove_abitazioni_2014_2024) else int(r.nuove_abitazioni_2014_2024),
        "res": None if pd.isna(r.residenti_2024) else int(r.residenti_2024), "cl": 0 if pd.isna(r.in_classifica) else int(r.in_classifica),
        "al": num(r.quota_canone_ALER_2016_pct, 2), "c12": num(r.consumato_2012_ambiti_pct, 1)}})
json.dump({"type": "FeatureCollection", "features": nfe}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------ csv pubblici
pub = prog[["tipo", "gruppo", "nome", "stato", "n_poligoni", "area_ha", "nil", "nuovo_2012_2025_ha", "ripristino_2012_2025_ha", "consumato_2012_pct", "consumato_2025_pct"]].copy()
pub.columns = ["tipo_nel_file", "gruppo", "nome", "stato_nel_PGT_2020", "poligoni", "ettari", "quartiere_prevalente", "suolo_nuovo_2012_2025_ha", "suolo_restituito_2012_2025_ha", "suolo_consumato_2012_pct", "suolo_consumato_2025_pct"]
pub.round(2).to_csv(os.path.join(OUT, "progetti.csv"), sep=";", index=False)
cols = ["id_nil", "nil", "area_ha", "ambiti_ha", "ambiti_pct", "n_progetti", "nuovo_nil_ha", "nuovo_in_ambiti_ha", "residenti_2024", "prezzo_var", "nuove_abitazioni_2014_2024", "nuove_abitazioni_ogni_1000_abitanti_2024", "quota_canone_ALER_2016_pct"]
nil[cols].round(3).to_csv(os.path.join(OUT, "nil.csv"), sep=";", index=False)
tipi.round(2).to_csv(os.path.join(OUT, "tipi.csv"), sep=";", index=False)

# ------------------------------------------------ riepilogo.json per la pagina
top = prog.sort_values("area_ha", ascending=False).head(20)
topn = prog.sort_values("nuovo_2012_2025_ha", ascending=False).head(8)
nl = nil.sort_values("ambiti_pct", ascending=False)
ok = nil[nil.in_classifica == 1]
RIEP2 = {k: RIEP[k] for k in ["data_download", "nil_ha_totali", "n_poligoni", "n_record_file", "senza_geometria", "n_progetti", "n_nomi", "somma_ha", "unione_ha", "quota_sovrapposta_pct",
                              "ambiti_pct_citta", "gruppi", "stati", "stati_progetti", "suolo", "correlazioni", "confronto_gruppi_nil", "pa_obbligatori", "ers", "grandi_funzioni",
                              "rig_ambientale", "r10_rigenerazione"]}
RIEP2["top_progetti"] = [{"nome": r.nome, "tipo": r.tipo, "stato": r.stato, "ha": r.area_ha, "nil": r.nil, "nuovo": r.nuovo_2012_2025_ha, "c12": None if pd.isna(r.consumato_2012_pct) else r.consumato_2012_pct} for r in top.itertuples()]
RIEP2["top_nuovo_suolo"] = [{"nome": r.nome, "tipo": r.tipo, "ha": r.area_ha, "nuovo": r.nuovo_2012_2025_ha, "nil": r.nil} for r in topn.itertuples()]
RIEP2["nil_top"] = [{"nil": r.nil, "pct": r.ambiti_pct, "ha": r.ambiti_ha, "np": int(r.n_progetti)} for r in nl.head(12).itertuples()]
RIEP2["n_nil_con_ambiti"] = int((nil.ambiti_ha > 0.5).sum()); RIEP2["n_nil_oltre10"] = int((ok.ambiti_pct >= 10).sum()); RIEP2["n_nil_ok"] = int(len(ok))
RIEP2["nil_nuovo_in_ambiti"] = [{"nil": r.nil, "nuovo": r.nuovo_nil_ha, "dentro": r.nuovo_in_ambiti_ha} for r in nil.sort_values("nuovo_nil_ha", ascending=False).head(8).itertuples()]
RIEP2["aler"] = {"med_alta": RIEP["confronto_gruppi_nil"][0]["aler_med"], "med_bassa": RIEP["confronto_gruppi_nil"][1]["aler_med"]}
RIEP2["file"] = {n: os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT) if n != "riepilogo.json"}
json.dump(RIEP2, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"), default=float)
tot = sum(os.path.getsize(os.path.join(OUT, n)) for n in os.listdir(OUT))
print("dimensione data/:", round(tot / 1e6, 2), "MB")
assert tot < 3e6, tot
if AVVISI:
    print("\n".join(AVVISI)); sys.exit(1)
print("tutto ok")
