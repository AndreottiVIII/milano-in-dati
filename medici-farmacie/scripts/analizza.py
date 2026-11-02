"""Medici di famiglia, pediatri e farmacie di Milano: dal grezzo alle tabelle pulite (pulito/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 analizza.py <medici-farmacie> <milano-in-dati>

Legge:
  raw/comune_mmg/*.csv, raw/comune_pls/*.csv   (Comune di Milano, ds234 e ds235, file del 29/10/2026)
  raw/salute_gov/FRM_FARMA_5_20261031.csv      (Ministero della Salute, elenco farmacie con date di validita')
  <milano-in-dati>/citta-15-minuti/raw/comune_milano/farmacie/*.csv (ds501, elenco regionale delle farmacie con coordinate)
  <milano-in-dati>/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson (88 NIL)
  <milano-in-dati>/citta-15-minuti/out/civici_tempi.csv (minuti a piedi dal civico alla farmacia / al medico piu' vicini, fase 2 di citta-15-minuti)
  <milano-in-dati>/popolazione/pulito/residenti_nil_anno_eta_genere.csv (ds27: residenti per NIL, anno, eta' singola)
Scrive in pulito/: nil_medici_farmacie.csv, farmacie_serie_citta.csv, medici_eta_citta.csv, medici_uscite_per_anno.csv,
  ambiti_carenti_municipi_2022.csv, municipi.csv, riepilogo_analisi.json, analisi_log.txt.
Nessun nome, data di nascita o codice di medico viene scritto: solo conteggi.
"""
import sys, os, glob, json, re
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, Point
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indirizzi import indice_civici, trova

M, P = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(M, "raw"), os.path.join(M, "pulito")
os.makedirs(PU, exist_ok=True)
C15 = os.path.join(P, "citta-15-minuti")
OGGI_MEDICI = pd.Timestamp("2026-10-29")      # data dei file dei medici
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)
R = {}   # riepilogo

# ------------------------------------------------------------------ NIL, residenti
geo = json.load(open(os.path.join(C15, "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
polys = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in geo["features"]}
assert len(polys) == 88
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
mun = pd.read_csv(os.path.join(P, "popolazione", "pulito", "nil_anagrafica.csv"))
muni = dict(zip(mun.id_nil, mun.municipio_prevalente))
pop = pd.read_csv(os.path.join(P, "popolazione", "pulito", "residenti_nil_anno_eta_genere.csv"))
tot_anno = pop.groupby(["anno", "id_nil"]).residenti.sum().unstack(fill_value=0)       # anno x nil
r25 = pop[pop.anno == 2025]
ad = r25[r25.eta >= 14].groupby("id_nil").residenti.sum()
bb = r25[r25.eta < 14].groupby("id_nil").residenti.sum()
R["residenti_2025"] = int(tot_anno.loc[2025].sum()); R["residenti_14piu_2025"] = int(ad.sum()); R["residenti_0_13_2025"] = int(bb.sum())
log("residenti 2025", R["residenti_2025"], "14+", R["residenti_14piu_2025"], "0-13", R["residenti_0_13_2025"])
R["residenti_per_anno_citta"] = {int(a): int(v) for a, v in tot_anno.sum(axis=1).items()}

def nil_di(lon, lat):
    p = Point(lon, lat)
    for i, g in polys.items():
        if g.contains(p):
            return i
    return None

# ------------------------------------------------------------------ medici
civ = pd.read_csv(os.path.join(C15, "out", "civici_tempi.csv"), usecols=["DENOMINAZIONE", "NUMEROCOMPLETO", "ID_NIL", "lon", "lat"])
idx = indice_civici(civ)

def carica_medici(cartella, pref):
    f = glob.glob(os.path.join(RAW, cartella, "*.csv"))[0]
    d = pd.read_csv(f, sep=";")
    n_righe, n_medici = len(d), d.idMedico.nunique()
    nasc = pd.to_datetime(d.dataNascita, utc=True).dt.tz_convert("Europe/Rome").dt.tz_localize(None).dt.normalize()
    d["nascita"] = nasc
    att = d[d.attivo == 1].copy()
    # un medico = una riga: l'ambulatorio principale (se manca, la prima)
    att = att.sort_values(["idMedico", "ambulatorioPrincipale"], ascending=[True, False]).drop_duplicates("idMedico")
    # NIL mancanti (coordinate sbagliate nel file): si cerca l'indirizzo tra i civici
    mancanti = att[att.ID_NIL.isna()]
    for k, r in mancanti.iterrows():
        t = trova(idx, f"{r.via}, {r.civico}")
        assert t is not None, ("indirizzo non trovato", r.via, r.civico)
        att.loc[k, "ID_NIL"] = t[2]
    log(pref, "righe", n_righe, "medici distinti", n_medici, "attivi", len(att), "NIL recuperati dall'indirizzo", len(mancanti))
    att["ID_NIL"] = att.ID_NIL.astype(int)
    att["eta"] = ((OGGI_MEDICI - att.nascita).dt.days / 365.2425)
    att["eta_int"] = np.floor(att.eta).astype(int)
    att["nato_anno"] = att.nascita.dt.year
    att["titolare"] = ~att.tipoMedico.str.startswith("Incaricato")
    # incaricati provvisori con sede in un indirizzo che ne ospita 5 o piu' (per MMG: Via G.B. Grassi 74, Via Stromboli 19, ...):
    # sono sedi di servizio, non ambulatori di quartiere -> non si assegnano al quartiere
    chiave = att.via.astype(str) + "|" + att.civico.astype(str)
    nprov = att[~att.titolare].groupby(chiave[~att.titolare]).size()
    att["sede_servizio"] = (~att.titolare) & (chiave.map(nprov).fillna(0) >= 5)
    R[pref + "_provvisori_in_sedi_di_servizio"] = int(att.sede_servizio.sum())
    R[pref + "_sedi_di_servizio_indirizzi"] = [[k.split("|")[0], k.split("|")[1], int(v)] for k, v in nprov[nprov >= 5].items()]
    R[pref + "_righe_file"] = n_righe; R[pref + "_medici_distinti_file"] = int(n_medici)
    R[pref + "_non_attivi"] = int(d[d.attivo == 0].idMedico.nunique())
    R[pref + "_attivi"] = int(len(att)); R[pref + "_titolari"] = int(att.titolare.sum()); R[pref + "_provvisori"] = int((~att.titolare).sum())
    R[pref + "_ambulatori_distinti"] = int(d[d.attivo == 1][["via", "civico"]].drop_duplicates().shape[0])
    R[pref + "_con_piu_ambulatori"] = int((d[d.attivo == 1].groupby("idMedico").size() > 1).sum())
    return att

mmg = carica_medici("comune_mmg", "mmg")
pls = carica_medici("comune_pls", "pls")
log("MMG titolari", R["mmg_titolari"], "provvisori", R["mmg_provvisori"], "| PLS titolari", R["pls_titolari"], "provvisori", R["pls_provvisori"])

# eta' (soglie) - titolari e provvisori
def fasce(df):
    e = df.eta_int
    return {"meno_di_50": int((e < 50).sum()), "50_59": int(((e >= 50) & (e < 60)).sum()), "60_64": int(((e >= 60) & (e < 65)).sum()),
            "65_69": int(((e >= 65) & (e < 70)).sum()), "70_piu": int((e >= 70).sum()), "totale": int(len(df)),
            "eta_mediana": float(df.eta.median())}
R["mmg_eta_titolari"] = fasce(mmg[mmg.titolare]); R["mmg_eta_provvisori"] = fasce(mmg[~mmg.titolare]); R["mmg_eta_tutti"] = fasce(mmg)
R["pls_eta_titolari"] = fasce(pls[pls.titolare]); R["pls_eta_tutti"] = fasce(pls)
log("MMG titolari eta'", R["mmg_eta_titolari"]); log("MMG provvisori eta'", R["mmg_eta_provvisori"]); log("PLS titolari eta'", R["pls_eta_titolari"])
# chi compie 70 anni in ciascun anno (anno di nascita + 70): i titolari
def uscite(df, nome):
    rows = []
    for y in range(2026, 2036):
        rows.append({"gruppo": nome, "anno": y, "compiono_70_anni_nell_anno": int((df.nato_anno + 70 == y).sum()),
                     "gia_70_o_piu_o_compiono_70_nell_anno_cumulato": int((df.nato_anno + 70 <= y).sum())})
    return rows
us = uscite(mmg[mmg.titolare], "MMG titolari") + uscite(mmg, "MMG tutti") + uscite(pls[pls.titolare], "PLS titolari")
pd.DataFrame(us).to_csv(os.path.join(PU, "medici_uscite_per_anno.csv"), index=False)
pd.DataFrame([dict(gruppo=g, **v) for g, v in [("MMG titolari", R["mmg_eta_titolari"]), ("MMG incaricati provvisori", R["mmg_eta_provvisori"]), ("MMG tutti", R["mmg_eta_tutti"]),
                                              ("PLS titolari", R["pls_eta_titolari"]), ("PLS tutti", R["pls_eta_tutti"])]]).to_csv(os.path.join(PU, "medici_eta_citta.csv"), index=False)

# ------------------------------------------------------------------ farmacie: elenco regionale (Comune, ds501) e storia (Ministero)
fc = pd.read_csv(glob.glob(os.path.join(C15, "raw", "comune_milano", "farmacie", "*.csv"))[0], sep=";", dtype=str)
fc["lon"] = fc.LONGITUDINE.astype(float); fc["lat"] = fc.LATITUDINE.astype(float)
fc["ID_NIL"] = fc.ID_NIL.astype(float).astype(int)
chk = [nil_di(a, b) for a, b in zip(fc.lon, fc.lat)]
assert all(a == b for a, b in zip(chk, fc.ID_NIL)), "NIL dichiarato diverso dal poligono"
R["farmacie_elenco_regionale"] = int(len(fc)); R["farmacie_elenco_regionale_data"] = "15/10/2026"
log("farmacie ds501", len(fc), "NIL coerenti col poligono")
farm_nil = fc.groupby("ID_NIL").size()

sg = pd.read_csv(os.path.join(RAW, "salute_gov", "FRM_FARMA_5_20261031.csv"), sep=";", dtype=str, keep_default_na=False)
mi = sg[(sg.comune == "MILANO") & (sg.sigla_provincia == "MI")].copy()
mi["ini"] = pd.to_datetime(mi.data_inizio_validita, format="%d/%m/%Y")
mi["fine"] = pd.to_datetime(mi.data_fine_validita.replace("-", None), format="%d/%m/%Y")
R["farmacie_ministero_righe_milano"] = int(len(mi)); R["farmacie_ministero_codici"] = int(mi.cod_farmacia.nunique())
# per ogni codice: da quando e fino a quando (i cambi di titolare sono righe nuove: si uniscono)
g = mi.groupby("cod_farmacia").agg(inizio=("ini", "min"), fine=("fine", lambda s: pd.NaT if s.isna().any() else s.max()), n_piva=("p_iva", "nunique"), n_righe=("ini", "size"))
# controllo: nessun buco tra le righe dello stesso codice (oltre 35 giorni)
buchi = 0
for c, gg in mi.sort_values("ini").groupby("cod_farmacia"):
    fine_prec = None
    for r in gg.itertuples():
        if fine_prec is not None and (r.ini - fine_prec).days > 35:
            buchi += 1
        fine_prec = pd.Timestamp("2100-01-01") if pd.isna(r.fine) else (r.fine if fine_prec is None else max(fine_prec, r.fine))
log("codici farmacia Ministero (Milano)", len(g), "buchi tra righe dello stesso codice", buchi)
R["farmacie_ministero_buchi"] = buchi
serie = []
for y in range(2005, 2027):
    t = pd.Timestamp(f"{y}-12-31") if y < 2026 else pd.Timestamp("2026-10-31")
    aperte = int(((g.inizio <= t) & (g.fine.isna() | (g.fine >= t))).sum())
    nuovi = int(((g.inizio.dt.year == y) & (g.inizio > pd.Timestamp("2005-01-01"))).sum())
    chiusi = int((g.fine.dt.year == y).sum())
    res = int(tot_anno.sum(axis=1).get(y, 0)) or None
    serie.append({"data": t.strftime("%Y-%m-%d"), "anno": y, "farmacie_aperte": aperte, "codici_nuovi_nell_anno": nuovi, "codici_chiusi_nell_anno": chiusi,
                  "residenti_31_12": res, "residenti_per_farmacia": (round(res / aperte, 0) if res else None),
                  "farmacie_ogni_100000_residenti": (round(100000 * aperte / res, 1) if res else None)})
sr = pd.DataFrame(serie)
sr.to_csv(os.path.join(PU, "farmacie_serie_citta.csv"), index=False)
log(sr.to_string())
R["farmacie_serie"] = serie
R["farmacie_codici_con_cambio_partita_iva"] = int((g.n_piva > 1).sum())
R["farmacie_codici_totali"] = int(len(g)); R["farmacie_codici_aperti_oggi"] = int(g.fine.isna().sum())
R["farmacie_ministero_aperte_senza_coordinate_dentro_milano"] = int(
    sum(1 for r in mi[mi.data_fine_validita == "-"].itertuples() if nil_di(float(r.longitudine.replace(",", ".")), float(r.latitudine.replace(",", "."))) is None))
log("farmacie Ministero aperte con coordinate fuori Milano:", R["farmacie_ministero_aperte_senza_coordinate_dentro_milano"], "su", int((mi.data_fine_validita == "-").sum()))
tipi = mi.descrizione_tipologia.value_counts().to_dict(); R["farmacie_tipologie_ministero"] = tipi

# ------------------------------------------------------------------ minuti a piedi (civici)
ct = pd.read_csv(os.path.join(C15, "out", "civici_tempi.csv"), usecols=["RESIDENZIALE", "ID_NIL", "min_farmacie", "min_medici", "minBordo_farmacie"])
ct = ct[(ct.RESIDENZIALE == 1) & ct.ID_NIL.notna()].copy()
ct["ID_NIL"] = ct.ID_NIL.astype(int)
ncv = ct.groupby("ID_NIL").size()
res25 = tot_anno.loc[2025]
ct["peso"] = ct.ID_NIL.map(res25) / ct.ID_NIL.map(ncv)
ct = ct[ct.peso.notna() & (ct.peso > 0)].copy()
log("civici residenziali con peso", len(ct), "residenti distribuiti", round(ct.peso.sum()))
R["civici_residenziali_con_peso"] = int(len(ct)); R["residenti_distribuiti_sui_civici"] = int(round(ct.peso.sum()))
MIN_PER_M = 75.0   # 4,5 km/h = 75 m al minuto (stessa velocita' di citta-15-minuti)
def wq(v, w, q):
    o = np.argsort(v); cw = np.cumsum(w[o]); return float(v[o][np.searchsorted(cw, q * cw[-1])])
def stat(df, col):
    v = df[col].fillna(99.0).values; w = df.peso.values
    return {"mediana_min": wq(v, w, .5), "p90_min": wq(v, w, .9), "oltre5": float(w[v > 5].sum() / w.sum()), "oltre10": float(w[v > 10].sum() / w.sum()),
            "oltre15": float(w[v > 15].sum() / w.sum()), "senza": float(w[np.isnan(df[col].values)].sum() / w.sum())}
for col, nome in [("min_farmacie", "farmacia"), ("min_medici", "medico")]:
    s = stat(ct, col)
    R["cammino_" + nome + "_citta"] = {k: round(v, 4) for k, v in s.items()}
    R["cammino_" + nome + "_citta"]["mediana_m"] = round(s["mediana_min"] * MIN_PER_M)
    log("cammino", nome, R["cammino_" + nome + "_citta"])
R["cammino_farmacia_con_bordo_media_min"] = round(float(np.average(ct.minBordo_farmacie.fillna(99), weights=ct.peso)), 2)
R["cammino_farmacia_senza_bordo_media_min"] = round(float(np.average(ct.min_farmacie.fillna(99), weights=ct.peso)), 2)

# ------------------------------------------------------------------ tabella per NIL
rows = []
for i in sorted(polys):
    r = {"id_nil": i, "nil": nomi.get(i, f"NIL {i}"), "municipio": int(muni[i])}
    r["residenti_2025"] = int(res25.get(i, 0)); r["residenti_14piu_2025"] = int(ad.get(i, 0)); r["residenti_0_13_2025"] = int(bb.get(i, 0))
    for y in (2005, 2015):
        r[f"residenti_{y}"] = int(tot_anno.loc[y].get(i, 0))
    a = mmg[(mmg.ID_NIL == i) & ~mmg.sede_servizio]
    r["mmg_attivi"] = len(a); r["mmg_titolari"] = int(a.titolare.sum()); r["mmg_provvisori"] = int((~a.titolare).sum())
    # le fasce di eta' per NIL solo se il NIL ha almeno 10 medici (altrimenti un conteggio puo' indicare una persona)
    ok = len(a) >= 10
    t = a[a.titolare]
    r["mmg_titolari_65_piu"] = int((t.eta_int >= 65).sum()) if ok else None
    r["mmg_titolari_70_piu"] = int((t.eta_int >= 70).sum()) if ok else None
    p = pls[pls.ID_NIL == i]
    r["pls_attivi"] = len(p)
    r["farmacie"] = int(farm_nil.get(i, 0))
    c = ct[ct.ID_NIL == i]
    if len(c):
        for col, nome in [("min_farmacie", "farmacia"), ("min_medici", "medico")]:
            s = stat(c, col)
            r[f"{nome}_min_mediano"] = round(s["mediana_min"], 1); r[f"{nome}_min_p90"] = round(s["p90_min"], 1)
            r[f"{nome}_quota_oltre10min"] = round(s["oltre10"], 4); r[f"{nome}_quota_oltre15min"] = round(s["oltre15"], 4)
            r[f"{nome}_quota_oltre5min"] = round(s["oltre5"], 4)
    rows.append(r)
nt = pd.DataFrame(rows)
nt["mmg_per_1000_14piu"] = np.where(nt.residenti_14piu_2025 > 0, 1000 * nt.mmg_attivi / nt.residenti_14piu_2025.replace(0, np.nan), np.nan)
nt["mmg_titolari_per_1000_14piu"] = np.where(nt.residenti_14piu_2025 > 0, 1000 * nt.mmg_titolari / nt.residenti_14piu_2025.replace(0, np.nan), np.nan)
nt["pls_per_1000_bambini_0_13"] = np.where(nt.residenti_0_13_2025 > 0, 1000 * nt.pls_attivi / nt.residenti_0_13_2025.replace(0, np.nan), np.nan)
nt["farmacie_ogni_10000_residenti"] = np.where(nt.residenti_2025 > 0, 10000 * nt.farmacie / nt.residenti_2025.replace(0, np.nan), np.nan)
for y in (2005, 2015, 2025):
    nt[f"residenti_per_farmacia_{y}"] = np.where((nt.farmacie > 0) & (nt[f"residenti_{y}" if y != 2025 else "residenti_2025"] > 0),
                                                  nt[f"residenti_{y}" if y != 2025 else "residenti_2025"] / nt.farmacie.replace(0, np.nan), np.nan)
# "posti teorici": medici x 1.500 (massimale dell'accordo nazionale) rispetto ai residenti di 14 anni e piu'
nt["posti_teorici_mmg_1500"] = nt.mmg_attivi * 1500
nt["posti_titolari_1500_su_residenti_14piu"] = np.where(nt.residenti_14piu_2025 > 0, nt.mmg_titolari * 1500 / nt.residenti_14piu_2025.replace(0, np.nan), np.nan)
nt["posti_tutti_1500_su_residenti_14piu"] = np.where(nt.residenti_14piu_2025 > 0, nt.mmg_attivi * 1500 / nt.residenti_14piu_2025.replace(0, np.nan), np.nan)
nt = nt.round(4)
nt.to_csv(os.path.join(PU, "nil_medici_farmacie.csv"), index=False)

# controlli di coerenza
assert nt.mmg_attivi.sum() == int((~mmg.sede_servizio).sum()), (nt.mmg_attivi.sum(), len(mmg))
R["mmg_localizzati"] = int(nt.mmg_attivi.sum())
assert nt.pls_attivi.sum() == len(pls)
assert nt.farmacie.sum() == len(fc)
assert nt.residenti_2025.sum() == R["residenti_2025"]
log("controlli: somme per NIL = totali (MMG, PLS, farmacie, residenti)")
R["nil_con_zero_mmg"] = nt[(nt.mmg_attivi == 0) & (nt.residenti_2025 > 0)].nil.tolist()
R["nil_con_zero_pls"] = nt[(nt.pls_attivi == 0) & (nt.residenti_2025 > 0)].nil.tolist()
R["nil_con_zero_farmacie"] = nt[(nt.farmacie == 0) & (nt.residenti_2025 > 0)].nil.tolist()
log("NIL senza MMG", len(R["nil_con_zero_mmg"]), "senza PLS", len(R["nil_con_zero_pls"]), "senza farmacia", len(R["nil_con_zero_farmacie"]))

# citta': rapporti
R["mmg_per_1000_14piu_citta"] = round(1000 * R["mmg_localizzati"] / R["residenti_14piu_2025"], 3)
R["mmg_titolari_per_1000_14piu_citta"] = round(1000 * R["mmg_titolari"] / R["residenti_14piu_2025"], 3)
R["residenti_14piu_per_mmg"] = round(R["residenti_14piu_2025"] / R["mmg_localizzati"], 1)
R["residenti_14piu_per_mmg_tutti_999"] = round(R["residenti_14piu_2025"] / R["mmg_attivi"], 1)
R["residenti_14piu_per_mmg_titolare"] = round(R["residenti_14piu_2025"] / R["mmg_titolari"], 1)
R["pls_per_1000_bambini_citta"] = round(1000 * R["pls_attivi"] / R["residenti_0_13_2025"], 3)
R["bambini_0_13_per_pls"] = round(R["residenti_0_13_2025"] / R["pls_attivi"], 1)
R["farmacie_ogni_10000_residenti_citta"] = round(10000 * len(fc) / R["residenti_2025"], 2)
R["residenti_per_farmacia_citta"] = round(R["residenti_2025"] / len(fc), 0)
R["posti_1500_titolari_su_14piu"] = round(R["mmg_titolari"] * 1500 / R["residenti_14piu_2025"], 3)
R["posti_1500_tutti_su_14piu"] = round(R["mmg_localizzati"] * 1500 / R["residenti_14piu_2025"], 3)
log("MMG per 1000 14+:", R["mmg_per_1000_14piu_citta"], "titolari:", R["mmg_titolari_per_1000_14piu_citta"], "| 14+ per MMG:", R["residenti_14piu_per_mmg"], "per titolare:", R["residenti_14piu_per_mmg_titolare"])
log("posti 1500 / residenti 14+: titolari", R["posti_1500_titolari_su_14piu"], "tutti", R["posti_1500_tutti_su_14piu"])
log("PLS per 1000 bambini 0-13", R["pls_per_1000_bambini_citta"], "bambini per PLS", R["bambini_0_13_per_pls"])

# ------------------------------------------------------------------ municipi (= "ambiti" dell'ATS per Milano citta')
mm = nt.groupby("municipio").agg(residenti_2025=("residenti_2025", "sum"), residenti_14piu_2025=("residenti_14piu_2025", "sum"), residenti_0_13_2025=("residenti_0_13_2025", "sum"),
                                  mmg_attivi=("mmg_attivi", "sum"), mmg_titolari=("mmg_titolari", "sum"), pls_attivi=("pls_attivi", "sum"), farmacie=("farmacie", "sum")).reset_index()
mm["mmg_per_1000_14piu"] = (1000 * mm.mmg_attivi / mm.residenti_14piu_2025).round(3)
mm["mmg_titolari_per_1000_14piu"] = (1000 * mm.mmg_titolari / mm.residenti_14piu_2025).round(3)
mm["pls_per_1000_bambini"] = (1000 * mm.pls_attivi / mm.residenti_0_13_2025).round(3)
mm["farmacie_ogni_10000_residenti"] = (10000 * mm.farmacie / mm.residenti_2025).round(2)
# ambiti carenti (assistenza primaria a ciclo di scelta) ATS Milano: elenco senza data nel testo; metadati del PDF = 9/9/2022
CARENTI = {2: 5, 4: 2, 5: 7, 6: 11, 7: 7, 8: 5, 9: 8}
txt = os.path.join(RAW, "ats_carenti", "a.txt")
if os.path.exists(txt):
    t = open(txt, encoding="latin-1").read()
    blocco = t[t.index("ATS MILANO"):]
    for m_, n_ in CARENTI.items():
        mt = re.search(r"DISTRETTO MILANO: Municipio %d\s+(\d+)" % m_, blocco)
        assert mt and int(mt.group(1)) == n_, ("carenti diversi dal PDF", m_)
    log("posti carenti per Municipio ricontrollati sul testo del PDF")
mm["posti_carenti_ats_2022"] = mm.municipio.map(CARENTI).fillna(0).astype(int)
mm.to_csv(os.path.join(PU, "municipi.csv"), index=False)
pd.DataFrame([{"municipio": k, "posti_carenti_assistenza_primaria": v, "fonte": "ATS Milano / Regione Lombardia, 'Ambiti Territoriali carenti di Assistenza Primaria' (PDF senza data nel testo; metadati: creato 9/9/2022)"} for k, v in CARENTI.items()]).to_csv(
    os.path.join(PU, "ambiti_carenti_municipi_2022.csv"), index=False)
R["posti_carenti_2022_totale_municipi"] = int(sum(CARENTI.values()))

json.dump(R, open(os.path.join(PU, "riepilogo_analisi.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
open(os.path.join(PU, "analisi_log.txt"), "w", encoding="utf8").write("\n".join(LOG))
print("fatto")
