"""Scrive i file dati della pagina "Parcheggi" (docs/parcheggi/data/). Si puo' rilanciare.

Uso (percorsi assoluti):
  python -I -X utf8 pagina.py <parcheggi_dir> <milano_in_dati_dir> <docs_dir>

Legge (fase 1, dopo analisi.py): parcheggi/pulito/riepilogo.json, nil_parcheggi.csv, ambiti.csv, interscambio.csv, parcheggi_ufficiali.csv,
raw/comune_ds83/sosta_ambiti.geojson (perimetri degli ambiti), poligoni NIL di citta-15-minuti.
Scrive in <docs_dir>/parcheggi/data/: riepilogo.json, nil.geojson, nil.csv, ambiti.geojson, ambiti.csv, interscambio.csv, parcheggi_ufficiali.csv.
Dati aggregati (per quartiere, per ambito, per parcheggio). Nessun file OSM grezzo, nessuna riga di parcheggi OSM: solo totali per quartiere.
Il PDF di ATM non viene copiato: della tabella tariffe si riportano solo i valori (nel riepilogo.json).
"""
import sys, os, json, shutil
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping

PD, MD, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(PD, "pulito"); RAW = os.path.join(PD, "raw")
OUT = os.path.join(DOCS, "parcheggi", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

R = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
nil = pd.read_csv(os.path.join(PU, "nil_parcheggi.csv"), sep=";")
amb = pd.read_csv(os.path.join(PU, "ambiti.csv"), sep=";")
ic = pd.read_csv(os.path.join(PU, "interscambio.csv"), sep=";")
pk = pd.read_csv(os.path.join(PU, "parcheggi_ufficiali.csv"), sep=";")
assert len(nil) == 88 and nil.id_nil.is_unique

# ---------------------------------------------------------------- controlli sui numeri
S = R["sintesi"]; ipo = R["ipotesi"]
check("stalli totali", ipo["stalli_su_strada_totale"], 297000)
check("quote sommano 100", round(sum(ipo["quote_percento"].values()), 1), 100.0, 0.05)
check("somma stalli stimati per NIL", float(nil.posti_strada_stima.sum()), 297000, 1)
check("somma km strade NIL", float(nil.km_in_ambiti.sum() + nil.km_fuori_ambiti.sum()), R["strade"]["km_totali_entro_comune"], 0.2)
check("area stalli km2", S["area_stalli_su_strada_km2"], 297000 * 12 / 1e6, 0.01)
check("somma posti ds342", int(pk.n_posti.sum()), 11351)
check("somma posti interscambio in citta'", int(ic[ic.nil >= 0].posti.sum()), 16753)
check("ambiti n", len(amb), 36)
check("abitanti totali", int(nil.abitanti_2024.sum()), R["citta"]["abitanti_2024"])
check("area citta' km2", round(float(nil.area_km2.sum()), 2), R["citta"]["area_km2"], 0.02)

# ---------------------------------------------------------------- NIL: geojson per la pagina
nilgeo = json.load(open(os.path.join(MD, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
assert set(geom) == set(int(i) for i in nil.id_nil)
def R1(x, d=1):
    return None if pd.isna(x) else round(float(x), d)
def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
feats, rows = [], []
for _, r in nil.sort_values("nil").iterrows():
    i = int(r.id_nil)
    p = {"i": i, "n": r.nil, "ab": int(r.abitanti_2024), "km2": R1(r.area_km2, 2), "cl": int(r.in_classifica),
         "qa": R1(r.quota_area_in_ambiti_pct, 1), "kin": R1(r.km_in_ambiti, 1), "kout": R1(r.km_fuori_ambiti, 1),
         "ps": int(round(r.posti_strada_stima)), "pr": int(round(r.posti_regolamentati_stima)),
         "qs": R1(r.quota_area_stalli_pct, 2), "ma": R1(r.m2_stalli_per_abitante, 2) if r.in_classifica else None,
         "raso": R1(100 * r.osm_fuori_strada_a_raso_km2 / r.area_km2, 2), "rasoha": R1(100 * r.osm_fuori_strada_a_raso_km2, 1),
         "ic": int(r.posti_interscambio_ds45), "pk": int(r.posti_parcheggi_pubblici_ds342),
         "cic": R1(r.ciclabili_km, 1), "cica": R1(1e6 * r.ciclabili_area_stima_km2, 0), "ped": R1(1e6 * r.aree_pedonali_km2, 0)}
    g = geom[i].simplify(0.00003, preserve_topology=True)
    gj = mapping(g)
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    rows.append({"id_nil": i, "nil": r.nil, "area_km2": R1(r.area_km2, 3), "abitanti_2024": int(r.abitanti_2024),
                 "quota_area_in_ambiti_pct": R1(r.quota_area_in_ambiti_pct, 1), "km_strade_in_ambiti": R1(r.km_in_ambiti, 1), "km_strade_fuori_ambiti": R1(r.km_fuori_ambiti, 1),
                 "STIMA_posti_su_strada": int(round(r.posti_strada_stima)), "STIMA_posti_regolamentati": int(round(r.posti_regolamentati_stima)),
                 "STIMA_quota_area_quartiere_pct": R1(r.quota_area_stalli_pct, 2), "STIMA_m2_stalli_per_abitante": R1(r.m2_stalli_per_abitante, 2) if r.in_classifica else None,
                 "osm_parcheggi_a_raso_km2": R1(r.osm_fuori_strada_a_raso_km2, 4), "osm_parcheggi_in_struttura_km2": R1(r.osm_fuori_strada_struttura_km2, 4),
                 "osm_ingressi_parcheggi": int(r.osm_ingressi_parcheggi), "posti_parcheggi_pubblici_ds342": int(r.posti_parcheggi_pubblici_ds342),
                 "posti_interscambio_ds45": int(r.posti_interscambio_ds45), "ciclabili_km": R1(r.ciclabili_km, 1), "ciclabili_area_stima_m2": R1(1e6 * r.ciclabili_area_stima_km2, 0),
                 "aree_pedonali_m2": R1(1e6 * r.aree_pedonali_km2, 0), "in_classifica_almeno_5000_abitanti": int(r.in_classifica)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";")

# ---------------------------------------------------------------- ambiti: geojson per la pagina
ag = json.load(open(os.path.join(RAW, "comune_ds83", "sosta_ambiti.geojson"), encoding="utf8"))
amap = amb.set_index("ambito")
af = []
for f in ag["features"]:
    n = int(f["properties"]["ambito"]); a = amap.loc[n]
    g = shape(f["geometry"]).simplify(0.00004, preserve_topology=True)
    gj = mapping(g)
    af.append({"type": "Feature", "properties": {"a": n, "n": f["properties"]["nome"], "c": a.cerchia, "t": None if pd.isna(a.tariffa_eur_h) else float(a.tariffa_eur_h)},
               "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": af}, open(os.path.join(OUT, "ambiti.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
amb.to_csv(os.path.join(OUT, "ambiti.csv"), index=False, sep=";")
ic.rename(columns={"Nome": "nome", "TAB1": "descrizione_posti", "INFO": "collegamento", "Zona": "zona_municipio", "nil": "id_nil"}).to_csv(os.path.join(OUT, "interscambio.csv"), index=False, sep=";")
pk.rename(columns={"nome": "nome", "n_posti": "posti", "nil": "id_nil"}).to_csv(os.path.join(OUT, "parcheggi_ufficiali.csv"), index=False, sep=";")

# ---------------------------------------------------------------- punti: interscambio e parcheggi pubblici
pk_full = pd.read_csv(os.path.join(RAW, "comune_ds342", "ds342_park_pub.csv"), sep=";")
def linea(t):
    w = t.replace("CORRISPONDENZA", "").split()
    w = [x if (x.startswith("MM") or x in ("FNM",)) else x.lower() for x in w]
    o = " ".join(w).replace("ferrovie nord", "Ferrovie Nord").replace("metrotranvia nord", "metrotranvia Nord")
    return o[:1].upper() + o[1:]
def nome(t):
    return t.title().replace(" Di ", " di ").replace(" Da ", " da ")
punti_ic = [{"n": nome(r.Nome), "p": int(r.posti), "l": linea(r.INFO), "lat": round(r.LAT_Y_4326, 5), "lon": round(r.LONG_X_4326, 5), "fc": int(r.nil < 0)} for r in ic.itertuples()]
punti_pk = [{"n": r.nome, "p": int(r.n_posti), "t": r.tipo.capitalize(), "lat": round(r.LAT_Y_4326, 5), "lon": round(r.LONG_X_4326, 5)} for r in pk_full.itertuples()]

# ---------------------------------------------------------------- riepilogo.json (tutti i numeri della pagina)
cl = nil[nil.in_classifica == 1]
perc = lambda x: round(float(x), 1)
tipi = [
    ["blu", "Strisce blu (a pagamento)", ipo["quote_percento"]["blu"], S["stalli_per_tipo"]["blu"], S["area_per_tipo_km2"]["blu"]],
    ["gialli", "Strisce gialle (residenti)", ipo["quote_percento"]["gialli_residenti"], S["stalli_per_tipo"]["gialli_residenti"], S["area_per_tipo_km2"]["gialli_residenti"]],
    ["disabili", "Posti per disabili", ipo["quote_percento"]["disabili"], S["stalli_per_tipo"]["disabili"], S["area_per_tipo_km2"]["disabili"]],
    ["cs", "Carico e scarico merci", ipo["quote_percento"]["carico_scarico"], S["stalli_per_tipo"]["carico_scarico"], S["area_per_tipo_km2"]["carico_scarico"]],
    ["aut", "Veicoli autorizzati", ipo["quote_percento"]["autorizzati"], S["stalli_per_tipo"]["autorizzati"], S["area_per_tipo_km2"]["autorizzati"]],
    ["lib", "Strisce bianche (senza regole)", ipo["quote_percento"]["liberi"], S["stalli_per_tipo"]["liberi"], S["area_per_tipo_km2"]["liberi"]]]
camp = S["campi_calcio_7140m2"]
camp_tipo = [round(camp * t[2] / 100) for t in tipi]
camp_tipo[-1] += camp - sum(camp_tipo)          # arrotondamento: la somma deve fare 499/500
ciclo = R["ciclabili"]; ped = R["aree_pedonali"]
verde_m2 = R["verde_mq_per_abitante_2023"]
ab = R["citta"]["abitanti_2024"]
cerchie = []
for c, g in amb.groupby("cerchia", sort=False):
    cerchie.append({"cerchia": c, "ambiti": [int(a) for a in sorted(g.ambito)], "area_km2": round(float(g.area_km2.sum()), 2), "tariffa": None if pd.isna(g.tariffa_eur_h.iloc[0]) else float(g.tariffa_eur_h.iloc[0])})
ESTR = R["nil_estremi"]
riep = {
    "generato": "pagina.py; dati scaricati il 1/11/2026",
    "ipotesi": {"m2_per_stallo": ipo["m2_per_stallo"], "stalli_totali": ipo["stalli_su_strada_totale"], "campo_calcio_m2": 7140},
    "citta": {"area_km2": R["citta"]["area_km2"], "abitanti_2024": ab, "autovetture_2025": R["auto"]["autovetture_2025_ds529"], "autovetture_2024_aci": R["auto"]["autovetture_2024_aci"],
              "autovetture_2011": R["auto"]["serie_autovetture"]["2011"], "autovetture_2023": R["auto"]["serie_autovetture"]["2023"], "motocicli_2025": R["auto"]["motocicli_2025_ds529"]},
    "sintesi": {"area_km2": S["area_stalli_su_strada_km2"], "quota_citta_pct": S["quota_citta_pct"], "campi": camp, "m2_per_abitante": S["m2_per_abitante"], "m2_per_autovettura": S["m2_per_autovettura"],
                "stalli_per_autovettura": S["stalli_su_strada_per_autovettura"], "autovetture_per_stallo": S["autovetture_per_stallo"], "autovetture_per_1000_ab": S["autovetture_per_1000_abitanti"],
                "volte_ciclabili": S["rapporto_stalli_strada_su_ciclabili_area"], "volte_pedonali": S["rapporto_stalli_su_aree_pedonali_area"],
                "sensibilita_km2": S["sensibilita_area_km2"], "verde_m2_per_abitante_2023": verde_m2,
                "verde_su_sosta_volte": round(verde_m2 / S["m2_per_abitante"], 1), "ufficiali_posti": S["parcheggi_ufficiali_posti"],
                "ufficiali_ogni_100_auto": round(100 * S["parcheggi_ufficiali_posti"] / R["auto"]["autovetture_2025_ds529"], 1)},
    "tipi": [{"k": t[0], "nome": t[1], "pct": t[2], "stalli": t[3], "area_km2": t[4], "campi": c} for t, c in zip(tipi, camp_tipo)],
    "ambiti": {"n": R["ambiti"]["n"], "area_km2": R["ambiti"]["area_unione_km2"], "quota_citta_pct": R["ambiti"]["quota_citta_pct"], "cerchie": cerchie,
               "km_in": R["strade"]["km_in_ambiti"], "km_fuori": R["strade"]["km_fuori_ambiti"], "km_tot": R["strade"]["km_totali_entro_comune"],
               "quota_km_in_pct": perc(100 * R["strade"]["km_in_ambiti"] / R["strade"]["km_totali_entro_comune"])},
    "modello": R["modello"],
    "controllo_osm": R["controllo_osm_tag"], "osm_tag_strade": R["osm_tag_parcheggio_su_strade"],
    "osm_fuori_strada": R["osm_fuori_strada"], "osm_su_strada": R["osm_su_strada_mappata"], "osm_ingressi": R["osm_ingressi_parcheggi"]["n_in_citta"], "osm_garage": R["osm_garage_edifici"],
    "ufficiali": R["ufficiali"],
    "ciclabili": {"km": ciclo["km_totali"], "area_km2": ciclo["area_stimata_km2"], "piste_km": ciclo["per_tipologia_km"]["ciclabile sede propria"], "corsie_km": ciclo["per_tipologia_km"]["ciclabile segnaletica"]},
    "pedonali": {"area_km2": ped["area_km2"], "n": ped["n_aree"]},
    "nil": {"n": len(nil), "n_classifica": int(len(cl)), "mediana_m2_ab": ESTR["m2_per_abitante_mediano"], "min_max": ESTR["m2_per_abitante_min_max"],
            "quota_area_min": ESTR["piu_bassa_quota_area"][-1], "quota_area_max": ESTR["piu_alta_quota_area"][0],
            "quota_area_stalli_pct_citta": round(100 * S["area_stalli_su_strada_km2"] / R["citta"]["area_km2"], 2)},
    "interscambio_punti": punti_ic, "parcheggi_pubblici_punti": punti_pk,
    "tariffe": [
        {"zona": "Area C / Bastioni", "ambiti": "1, 3, 4, 5, 6, 7", "euro_h": 3.0, "orario": "8-19 tutti i giorni; 19-24 solo le prime 2 ore; 24-8 gratis", "note": "massimo 2 ore consecutive per ambito (dal 1/11/2023)"},
        {"zona": "Cerchia filoviaria", "ambiti": "2, 9-23", "euro_h": 2.0, "orario": "giorni feriali 8-19; in alcune zone anche festivi e fino alle 24", "note": "alcune vie con limite di 1 ora"},
        {"zona": "Cerchia extra-filoviaria", "ambiti": "8, 25, 30-36, 40, 42, 43", "euro_h": 1.2, "orario": "giorni feriali 8-19; in alcune zone tutti i giorni", "note": "10 euro al giorno nelle zone dello stadio e dell'ippodromo, nei giorni di eventi"},
        {"zona": "Interscambio (via Impastato)", "ambiti": "38", "euro_h": None, "orario": "tutti i giorni 6-1", "note": "a fasce: 1,50 euro fino a 5 ore, 2 fino a 10, 2,50 fino a 15, 4 fino a 19"},
        {"zona": "Bus turistici", "ambiti": "-", "euro_h": 8.0, "orario": "dipende dal posteggio (via del Burchiello, Porta Venezia, via Valtellina, via Carbonera)", "note": "8 euro l'ora"}],
    "pass": {"extra_filoviaria_mese": 50, "extra_filoviaria_anno": 500, "con_abbonamento_atm_mese": 40, "con_abbonamento_atm_anno": 400, "nota": "abbonamenti della cerchia extra-filoviaria, da ATM; non verificati sul sito del Comune"},
}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("totale", tot, "byte")
check("dati sotto 3 MB", int(tot < 3_000_000), 1)
check("campi per tipo sommano", sum(camp_tipo), camp)
print("AVVISI:", AVVISI if AVVISI else "nessuno")
if AVVISI:
    sys.exit(1)
