"""Scrive la pagina "Medici e farmacie" (docs/medici-farmacie/): file dati + index.html.

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <medici-farmacie> <milano-in-dati> <docs>
Prima va lanciato analizza.py (scrive pulito/).
Legge: pulito/*.csv, pulito/riepilogo_analisi.json, i poligoni dei NIL di citta-15-minuti, l'elenco regionale delle farmacie (ds501, CC0),
  scripts/pagina_template.html.
Scrive in <docs>/medici-farmacie/: index.html e data/ (riepilogo.json, nil.geojson, nil.csv, municipi.csv, farmacie.json, farmacie_serie_citta.csv,
  medici_eta_citta.csv, medici_uscite_per_anno.csv, ambiti_carenti_municipi_2022.csv).
Solo dati aggregati: nessun medico singolo (nome, data di nascita, codici) e' scritto, ne' per quartiere ne' altrove.
"""
import sys, os, json, glob, shutil
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

M, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(M, "pulito")
OUT = os.path.join(DOCS, "medici-farmacie", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

R = json.load(open(os.path.join(PU, "riepilogo_analisi.json"), encoding="utf8"))
nt = pd.read_csv(os.path.join(PU, "nil_medici_farmacie.csv"))
mu = pd.read_csv(os.path.join(PU, "municipi.csv"))
sr = pd.read_csv(os.path.join(PU, "farmacie_serie_citta.csv"))
geo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in geo["features"]}
assert len(nt) == 88 and set(geom) == set(nt.id_nil)

# controlli sui totali
check("MMG attivi", R["mmg_attivi"], 999); check("MMG titolari + provvisori", R["mmg_titolari"] + R["mmg_provvisori"], R["mmg_attivi"])
check("MMG localizzati = somma NIL", int(nt.mmg_attivi.sum()), R["mmg_localizzati"])
check("MMG localizzati = attivi - sedi di servizio", R["mmg_attivi"] - R["mmg_provvisori_in_sedi_di_servizio"], R["mmg_localizzati"])
check("PLS = somma NIL", int(nt.pls_attivi.sum()), R["pls_attivi"])
check("farmacie = somma NIL", int(nt.farmacie.sum()), R["farmacie_elenco_regionale"])
check("residenti = somma NIL", int(nt.residenti_2025.sum()), R["residenti_2025"])
check("fasce di eta' titolari = totale", sum(R["mmg_eta_titolari"][k] for k in ("meno_di_50", "50_59", "60_64", "65_69", "70_piu")), R["mmg_titolari"])
check("serie farmacie 2025", int(sr[sr.anno == 2025].farmacie_aperte.iloc[0]), 427)

def r_(x, d=1):
    return None if pd.isna(x) else round(float(x), d)
def mn(x):
    """minuti a piedi: 99 = nessun servizio entro il limite di calcolo (circa 43 minuti)"""
    return None if pd.isna(x) or x >= 90 else round(float(x), 1)

def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
feats = []
for r in nt.sort_values("nil").itertuples(index=False):
    d = r._asdict()
    p = {"i": int(r.id_nil), "n": r.nil, "mu": int(r.municipio), "ab": int(r.residenti_2025), "a14": int(r.residenti_14piu_2025), "b13": int(r.residenti_0_13_2025),
         "r05": int(r.residenti_2005), "r15": int(r.residenti_2015),
         "mm": int(r.mmg_attivi), "mt": int(r.mmg_titolari), "mp": int(r.mmg_provvisori),
         "m65": None if pd.isna(r.mmg_titolari_65_piu) else int(r.mmg_titolari_65_piu), "m70": None if pd.isna(r.mmg_titolari_70_piu) else int(r.mmg_titolari_70_piu),
         "pl": int(r.pls_attivi), "fa": int(r.farmacie),
         "m1000": r_(r.mmg_per_1000_14piu, 2), "mt1000": r_(r.mmg_titolari_per_1000_14piu, 2), "p1000": r_(r.pls_per_1000_bambini_0_13, 2),
         "f10k": r_(r.farmacie_ogni_10000_residenti, 2),
         "rpf05": r_(r.residenti_per_farmacia_2005, 0), "rpf15": r_(r.residenti_per_farmacia_2015, 0), "rpf25": r_(r.residenti_per_farmacia_2025, 0),
         "cop": r_(r.posti_tutti_1500_su_residenti_14piu, 2),
         "fmin": mn(r.farmacia_min_mediano), "f5": r_(r.farmacia_quota_oltre5min, 3), "f10": r_(r.farmacia_quota_oltre10min, 3), "f15": r_(r.farmacia_quota_oltre15min, 3),
         "dmin": mn(r.medico_min_mediano), "d10": r_(r.medico_quota_oltre10min, 3), "d15": r_(r.medico_quota_oltre15min, 3),
         "cl": 1 if r.residenti_2025 >= 5000 else 0}
    g = mapping(geom[int(r.id_nil)].simplify(0.00003, preserve_topology=True))
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# csv per chi vuole scaricare
cols = {"id_nil": "id_nil", "nil": "quartiere_nil", "municipio": "municipio_prevalente", "residenti_2025": "residenti_2025", "residenti_14piu_2025": "residenti_14_anni_e_piu_2025",
        "residenti_0_13_2025": "residenti_0_13_anni_2025", "residenti_2015": "residenti_2015", "residenti_2005": "residenti_2005",
        "mmg_attivi": "medici_famiglia_localizzati", "mmg_titolari": "di_cui_titolari", "mmg_provvisori": "di_cui_incaricati_provvisori",
        "mmg_titolari_65_piu": "titolari_65_anni_e_piu_solo_se_almeno_10_medici", "mmg_titolari_70_piu": "titolari_70_anni_e_piu_solo_se_almeno_10_medici",
        "mmg_per_1000_14piu": "medici_famiglia_ogni_1000_residenti_14_e_piu", "posti_tutti_1500_su_residenti_14piu": "posti_a_1500_assistiti_diviso_residenti_14_e_piu",
        "pls_attivi": "pediatri_libera_scelta", "pls_per_1000_bambini_0_13": "pediatri_ogni_1000_bambini_0_13",
        "farmacie": "farmacie", "farmacie_ogni_10000_residenti": "farmacie_ogni_10000_residenti", "residenti_per_farmacia_2005": "residenti_per_farmacia_2005_stesse_farmacie",
        "residenti_per_farmacia_2015": "residenti_per_farmacia_2015_stesse_farmacie", "residenti_per_farmacia_2025": "residenti_per_farmacia_2025",
        "farmacia_min_mediano": "minuti_a_piedi_farmacia_mediana", "farmacia_quota_oltre5min": "quota_residenti_farmacia_oltre_5_min", "farmacia_quota_oltre10min": "quota_residenti_farmacia_oltre_10_min",
        "farmacia_quota_oltre15min": "quota_residenti_farmacia_oltre_15_min",
        "medico_min_mediano": "minuti_a_piedi_ambulatorio_medico_mediana", "medico_quota_oltre10min": "quota_residenti_ambulatorio_oltre_10_min", "medico_quota_oltre15min": "quota_residenti_ambulatorio_oltre_15_min"}
out = nt[list(cols)].rename(columns=cols)
for c in ("minuti_a_piedi_farmacia_mediana", "minuti_a_piedi_ambulatorio_medico_mediana"):
    out.loc[out[c] >= 90, c] = np.nan
out.to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";", decimal=",")
shutil.copy(os.path.join(PU, "municipi.csv"), os.path.join(OUT, "municipi.csv"))
for f in ("farmacie_serie_citta.csv", "medici_eta_citta.csv", "medici_uscite_per_anno.csv", "ambiti_carenti_municipi_2022.csv"):
    shutil.copy(os.path.join(PU, f), os.path.join(OUT, f))

# farmacie (elenco regionale, CC0): punto, nome, indirizzo - sono esercizi commerciali con indirizzo pubblico
fc = pd.read_csv(glob.glob(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "farmacie", "*.csv"))[0], sep=";", dtype=str)
farm = [[round(float(a), 5), round(float(b), 5), str(n).strip().title(), str(i).strip().title(), int(float(k))]
        for a, b, n, i, k in zip(fc.LONGITUDINE, fc.LATITUDINE, fc.DESCRIZIONE_FARMACIA, fc.INDIRIZZO, fc.ID_NIL)]
json.dump({"campi": ["lon", "lat", "nome", "indirizzo", "id_nil"], "fonte": "Elenco regionale delle farmacie, Comune di Milano ds501 (CC0), aggiornato il 15/10/2026", "farmacie": farm},
          open(os.path.join(OUT, "farmacie.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# riepilogo: tutti i numeri della pagina, con l'origine
uscite = pd.read_csv(os.path.join(PU, "medici_uscite_per_anno.csv"))
ut = uscite[uscite.gruppo == "MMG titolari"]
riep = dict(R)
riep["meta"] = {"scaricato_medici": "2026-10-29 (file del Comune, ds234 e ds235)", "scaricato_farmacie_ministero": "2026-11-02", "farmacie_elenco_regionale": "2026-10-29 (citta-15-minuti)",
                "scaricato_ats": "2026-11-02", "residenti_anno": 2025, "massimale_mmg": 1500, "nil": 88, "soglia_residenti_confronti": 5000, "minuti_per_metro_m": 75,
                "pagina_generata_da": "medici-farmacie/scripts/pagina.py"}
riep["uscite_mmg_titolari"] = [{"anno": int(r.anno), "compiono_70": int(r.compiono_70_anni_nell_anno), "cumulato": int(r.gia_70_o_piu_o_compiono_70_nell_anno_cumulato)} for r in ut.itertuples()]
riep["municipi"] = mu.to_dict("records")
riep["origine"] = {
    "mmg_*": "raw/comune_mmg/20261029_mmg_final.csv (Comune di Milano ds234, CC BY-NC); attivi = campo attivo=1; un medico = una riga (ambulatorio principale); titolare = tipoMedico 'MMG', provvisorio = 'Incaricato provvisorio di Assistenza Primaria'",
    "pls_*": "raw/comune_pls/20261029_pls_final.csv (Comune di Milano ds235, CC BY-NC); stesse regole",
    "mmg_provvisori_in_sedi_di_servizio": "analizza.py: provvisori con sede in un indirizzo (campi via+civico) che ne ospita 5 o piu'",
    "eta": "campo dataNascita (solo per calcolare l'eta' al 29/10/2026: non e' ripubblicato); fasce e anni in pulito/medici_eta_citta.csv e medici_uscite_per_anno.csv",
    "residenti": "popolazione/pulito/residenti_nil_anno_eta_genere.csv (Comune di Milano ds27, residenti al 31/12 per eta' singola); 14 e piu' / 0-13",
    "farmacie_elenco_regionale": "citta-15-minuti/raw/comune_milano/farmacie (ds501, CC0, 15/10/2026): 422 punti con coordinate",
    "farmacie_serie": "raw/salute_gov/FRM_FARMA_5_20261031.csv (Ministero della Salute, IODL v2.0): righe di Milano (comune=MILANO, provincia MI) con data_inizio_validita e data_fine_validita, unite per cod_farmacia",
    "cammino_*": "citta-15-minuti/out/civici_tempi.csv: min_farmacie, min_medici (rete pedonale OpenStreetMap, 4,5 km/h), 46.885 civici residenziali pesati con i residenti 2025 del quartiere",
    "posti_carenti_2022": "raw/ats_carenti/ambiti_carenti_AP_bandi_regione.pdf (bandi.regione.lombardia.it, ATS Milano)"}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)

shutil.copy(os.path.join(M, "scripts", "pagina_template.html"), os.path.join(DOCS, "medici-farmacie", "index.html"))
print("\nFILE:")
tot = 0
for f in sorted(os.listdir(OUT)):
    s = os.path.getsize(os.path.join(OUT, f)); tot += s
    print(f"  {f:40s} {s/1024:8.1f} KB")
print(f"  totale {tot/1024:.1f} KB")
if AVVISI:
    print("\nATTENZIONE:"); [print("  ", a) for a in AVVISI]; sys.exit(1)
print("controlli tutti ok")
