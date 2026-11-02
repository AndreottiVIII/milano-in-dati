"""Povertà educativa - FASE 1: pulizia e riepiloghi. Legge raw/ (non fidato, solo letto) e scrive pulito/.

Uso (percorsi assoluti, si può rilanciare):
  python -I -X utf8 build.py <poverta-educativa_dir> <milano-in-dati_dir>

Fonti lette:
  poverta-educativa/raw/istat/sdmx_*.csv           ISTAT IstatData (SDMX), flusso 47_850_DF_DCIS_SERVSOCEDU1_6 e _3 (servizi per la prima infanzia, comuni)
  poverta-educativa/raw/miur/ALUTEMPOSCUOLA*.csv   MIM, alunni primaria/sec. I per tempo scuola (DS0090 statale, DS0100 paritaria)
  poverta-educativa/raw/miur/EDIAMBFUNZSTA*.csv    MIM, ambienti funzionali degli edifici (mensa), solo scuole statali
  poverta-educativa/raw/invalsi/report_generale_unito_dispersione_e_eccellenti_agg_2025.csv   INVALSI open data
  scuole/raw/miur/SCUANAGRAFE*.csv                 MIM, anagrafe scuole (comune, CAP) - già scaricata dal filone "scuole"
  scuole/raw/comune_ds47/ds47_nidi_infanzia.csv    Comune di Milano, nidi (sedi 2016-2019)
  scuole/pulito/miur_scuole_anagrafica.csv         NIL delle scuole MIM (filone "scuole")
  scuole/pulito/residenti_nil_fascia_cittadinanza_ds27.csv   residenti per NIL e fascia d'età (Comune ds27)
  redditi/pulito/cap_milano_media_euro2025.csv, mef_comuni_2000_2024.csv   redditi (filone "redditi")
  benessere/pulito/bes_lungo.csv                   Bes dei territori ISTAT (filone "benessere")
  citta-15-minuti/...                              confini NIL, collegamento CAP-NIL
"""
import sys, os, json, glob
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from scipy.stats import spearmanr

PE, P = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(PE, "raw"), os.path.join(PE, "pulito")
SC = os.path.join(P, "scuole")
os.makedirs(PU, exist_ok=True)
CONTROLLI = {}
AVVISI = []

def check(nome, calcolato, atteso, tol=0.0):
    ok = abs(calcolato - atteso) <= tol
    CONTROLLI[nome] = {"calcolato": float(calcolato), "atteso": float(atteso), "ok": bool(ok)}
    if not ok: AVVISI.append(nome)
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

def save(df, nome, **kw):
    df.to_csv(os.path.join(PU, nome), sep=";", index=False, **kw)
    print("scritto", nome, len(df))

# ---------------------------------------------------------------- le 14 città metropolitane (capoluoghi): codice ISTAT comune, codice catastale
CITTA = [  # nome, istat, catastale
    ("Torino", "001272", "L219"), ("Milano", "015146", "F205"), ("Genova", "010025", "D969"), ("Venezia", "027042", "L736"),
    ("Bologna", "037006", "A944"), ("Firenze", "048017", "D612"), ("Roma", "058091", "H501"), ("Napoli", "063049", "F839"),
    ("Bari", "072006", "A662"), ("Reggio Calabria", "080063", "H224"), ("Palermo", "082053", "G273"), ("Messina", "083048", "F158"),
    ("Catania", "087015", "C351"), ("Cagliari", "092009", "B354")]
NOME_ISTAT = {i: n for n, i, c in CITTA}; NOME_ISTAT.update({"IT": "Italia", "ITC4": "Lombardia"})
NOME_CAT = {c: n for n, i, c in CITTA}
SEI = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze"]

# ================================================================ 1. NIDI (ISTAT)
def leggi_sdmx(f):
    d = pd.read_csv(os.path.join(RAW, "istat", f), dtype=str)
    d["v"] = pd.to_numeric(d.OBS_VALUE, errors="coerce")
    d["anno"] = d.TIME_PERIOD.astype(int)
    return d

a = leggi_sdmx("sdmx_SERVSOCEDU1_6.csv")      # 6 città, tutti i tipi di titolare (1 privato, 2 pubblico, 9 totale)
a = a[(a.TYPE_SOCIO_EDUC_SERVICE == "ALL") & (a.TYPE_MANAGEMENT == "ALL")]
a["area"] = a.REF_AREA.map(NOME_ISTAT)
rows = []
for (area, anno), g in a.groupby(["area", "anno"]):
    def val(dt, h):
        x = g[(g.DATA_TYPE == dt) & (g.HOLDER_SECTOR_PUBPRIV == h)].v
        return float(x.iloc[0]) if len(x) else np.nan
    rows.append(dict(area=area, anno=anno, p100_tot=val("P_100CH_Y0_2", "9"), p100_pub=val("P_100CH_Y0_2", "2"), p100_priv=val("P_100CH_Y0_2", "1"),
                     posti_tot=val("AUTP", "9"), posti_pub=val("AUTP", "2"), posti_priv=val("AUTP", "1"),
                     servizi_tot=val("SERV", "9"), servizi_pub=val("SERV", "2"), servizi_priv=val("SERV", "1")))
nidi = pd.DataFrame(rows)
u = leggi_sdmx("sdmx_SERVSOCEDU1_3.csv"); u = u[(u.TYPE_SOCIO_EDUC_SERVICE == "ALL") & (u.TYPE_MANAGEMENT == "ALL")]
u["area"] = u.REF_AREA.map(NOME_ISTAT)
us = u[u.DATA_TYPE == "USSSPM"].pivot_table(index=["area", "anno"], values="v", aggfunc="first").rename(columns={"v": "utenti_servizi_comuni"}).reset_index()
sp = u[u.DATA_TYPE == "TOTEXP"].pivot_table(index=["area", "anno"], values="v", aggfunc="first").rename(columns={"v": "spesa_comune_euro"}).reset_index()
nidi = nidi.merge(us, on=["area", "anno"], how="left").merge(sp, on=["area", "anno"], how="left")
nidi["bambini_0_2_impliciti"] = (nidi.posti_tot / nidi.p100_tot * 100).round(0)       # denominatore usato da ISTAT, ricavato
nidi["quota_posti_privati_pct"] = (100 * nidi.posti_priv / nidi.posti_tot).round(1)
nidi["utenti_servizi_comuni_per100"] = (100 * nidi.utenti_servizi_comuni / nidi.bambini_0_2_impliciti).round(1)
nidi = nidi.sort_values(["area", "anno"]).reset_index(drop=True)
save(nidi, "nidi_6citta_serie.csv")
# controllo: totale = pubblico + privato
chk = (nidi.posti_pub + nidi.posti_priv - nidi.posti_tot).abs().max()
check("nidi: posti pubblici + privati = totale (max scarto, 6 città x 12 anni)", chk, 0, 0)

b = leggi_sdmx("sdmx_SERVSOCEDU1_6_14capoluoghi_IT.csv")
b["area"] = b.REF_AREA.map(NOME_ISTAT)
nb = b.pivot_table(index=["area", "anno"], columns="DATA_TYPE", values="v", aggfunc="first").reset_index().rename(columns={"P_100CH_Y0_2": "p100_tot", "AUTP": "posti_tot"})
nb = nb.sort_values(["area", "anno"])
save(nb, "nidi_14citta_italia_serie.csv")
# i due file devono coincidere sulle 6 città
m = nidi.merge(nb, on=["area", "anno"], suffixes=("", "_b"))
check("nidi: p100 totale coincide tra i due scarichi ISTAT (max scarto)", (m.p100_tot - m.p100_tot_b).abs().max(), 0, 0.001)

# Milano: denominatore ISTAT contro residenti 0-2 del Comune (ds27)
r27 = pd.read_csv(os.path.join(SC, "pulito", "residenti_nil_fascia_cittadinanza_ds27.csv"), sep=";")
r02 = r27[r27.fascia_eta == "0-2"].assign(t=lambda x: x.stranieri + x.italiani).groupby("anno").t.sum()
imp24 = float(nidi[(nidi.area == "Milano") & (nidi.anno == 2024)].bambini_0_2_impliciti.iloc[0])
print("Milano 0-2: ISTAT implicito 2024", imp24, " Comune ds27 2024", r02[2024], " 2025", r02[2025])
CONTROLLI["milano_0_2"] = {"istat_implicito_2024": imp24, "comune_ds27_2024": int(r02[2024]), "comune_ds27_2025": int(r02[2025])}

# ================================================================ 2. MILANO: sedi di nido per municipio e NIL (Comune ds47, 2018/19)
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
anag = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
mun_prev = dict(zip(anag.nil, anag.municipio_prevalente)); nil_nome = dict(zip(anag.nil, anag.nil_nome))
assert set(geom) == set(anag.nil) and len(geom) == 88

d47 = pd.read_csv(os.path.join(SC, "raw", "comune_ds47", "ds47_nidi_infanzia.csv"), sep=";", dtype=str)
# una riga per (anno, sede): il file ha una riga per ogni fascia d'età (lattanti, medio/grandi, sezione primavera) di ogni sede
sedi = d47.drop_duplicates(["CODANNOSCOLASTICO", "NOME_LUNGO"]).copy()
sedi["lon"] = pd.to_numeric(sedi.LONG_WGS84.str.replace(",", "."), errors="coerce"); sedi["lat"] = pd.to_numeric(sedi.LAT_WGS84.str.replace(",", "."), errors="coerce")
def nil_di(r):
    if pd.isna(r.lon): return np.nan
    p = Point(r.lon, r.lat)
    for k, g in geom.items():
        if g.contains(p): return k
    return np.nan
sedi["id_nil"] = sedi.apply(nil_di, axis=1)
sedi["municipio"] = pd.to_numeric(sedi.MUNICIPIO, errors="coerce")
sedi["gestione"] = np.where(sedi.TIPO_STRUTTURA.str.startswith("Comunale"), "comunale", "privato")
sedi["anno_sc"] = sedi.CODANNOSCOLASTICO.map({"1617": "2016/17", "1718": "2017/18", "1819": "2018/19"})
sedi["con_posizione"] = sedi.lon.notna()
save(sedi[["anno_sc", "NOME_LUNGO", "TIPO_STRUTTURA", "gestione", "municipio", "id_nil", "CAP"]].rename(columns={"NOME_LUNGO": "sede"}), "nidi_milano_sedi_ds47.csv")
check("ds47: righe con municipio (2018/19, su tutte le sedi)", int(sedi[sedi.anno_sc == "2018/19"].municipio.notna().sum()), int((sedi.anno_sc == "2018/19").sum()), 0)
CONTROLLI["ds47_sedi_per_anno"] = {k: int(v) for k, v in sedi.groupby("anno_sc").size().items()}
CONTROLLI["ds47_sedi_senza_posizione_2018_19"] = int((~sedi[sedi.anno_sc == "2018/19"].con_posizione).sum())

res = r27.assign(t=lambda x: x.stranieri + x.italiani)
res02 = res[res.fascia_eta == "0-2"].pivot_table(index="id_nil", columns="anno", values="t", aggfunc="sum")
s19 = sedi[sedi.anno_sc == "2018/19"]
# NIL
nil = pd.DataFrame({"id_nil": sorted(geom)})
nil["nil"] = nil.id_nil.map(nil_nome); nil["municipio"] = nil.id_nil.map(mun_prev)
nil["res_0_2_2018"] = nil.id_nil.map(res02[2018]).fillna(0).astype(int)
nil["res_0_2_2024"] = nil.id_nil.map(res02[2024]).fillna(0).astype(int)
sn = s19[s19.con_posizione].groupby("id_nil").size()
nil["sedi_nido_2018_19"] = nil.id_nil.map(sn).fillna(0).astype(int)
nil["sedi_nido_per_1000_0_2"] = np.where(nil.res_0_2_2018 >= 150, (1000 * nil.sedi_nido_2018_19 / nil.res_0_2_2018.replace(0, np.nan)).round(1), np.nan)
# municipio (tutte le sedi, anche senza posizione); residenti 0-2 = somma dei NIL con quel municipio prevalente (approssimazione)
mun = s19.groupby("municipio").agg(sedi=("sede" if "sede" in s19 else "NOME_LUNGO", "size"), comunali=("gestione", lambda s: int((s == "comunale").sum()))).reset_index()
mun["private"] = mun.sedi - mun.comunali
mun["res_0_2_2018"] = mun.municipio.map(nil.groupby("municipio").res_0_2_2018.sum())
mun["sedi_per_1000_0_2"] = (1000 * mun.sedi / mun.res_0_2_2018).round(2)
mun["municipio"] = mun.municipio.astype(int)
save(mun, "nidi_milano_municipi_2018_19.csv")
check("residenti 0-2 2018: somma NIL = somma municipi", int(nil.res_0_2_2018.sum()), int(mun.res_0_2_2018.sum()), 0)

# ================================================================ 3. TEMPO PIENO e MENSA (MIM)
S = os.path.join(SC, "raw", "miur"); R = os.path.join(RAW, "miur")
def anagrafe(tag, ys):
    nome = "SCUANAGRAFESTAT" if tag == "STA" else "SCUANAGRAFEPAR"
    f = glob.glob(os.path.join(S, f"{nome}{ys}*.csv"))[0]
    return pd.read_csv(f, dtype=str, usecols=["CODICESCUOLA", "CODICECOMUNESCUOLA", "CAPSCUOLA"]).drop_duplicates("CODICESCUOLA")

tp = []
for y in range(2015, 2025):
    ys = f"{y}{str(y+1)[2:]}"
    for tag, gest in (("STA", "statale"), ("PAR", "paritaria")):
        f = glob.glob(os.path.join(R, f"ALUTEMPOSCUOLA{tag}{ys}*.csv"))[0]
        d = pd.read_csv(f, dtype=str)
        d = d[d.ORDINESCUOLA == "SCUOLA PRIMARIA"].copy()
        d["n"] = d.ALUNNIMASCHI.astype(int) + d.ALUNNIFEMMINE.astype(int)
        d = d.merge(anagrafe(tag, ys), on="CODICESCUOLA", how="left")
        check(f"tempo scuola {y}/{y+1} {gest}: alunni di scuole senza comune in anagrafe", int(d.CODICECOMUNESCUOLA.isna().sum()), 0, 0)
        d["gestione"] = gest; d["anno"] = y
        tp.append(d)
TP = pd.concat(tp, ignore_index=True)
TP["tempo_pieno"] = TP.TEMPOSCUOLA.eq("TEMPO PIENO")
TP["citta"] = TP.CODICECOMUNESCUOLA.map(NOME_CAT)
def agg_tp(x):
    return pd.Series({"alunni": x.n.sum(), "alunni_tempo_pieno": x.loc[x.tempo_pieno, "n"].sum()})
tc = TP[TP.citta.notna()].groupby(["anno", "citta", "gestione"]).apply(agg_tp, include_groups=False).reset_index()
ital = TP.groupby(["anno", "gestione"]).apply(agg_tp, include_groups=False).reset_index().assign(citta="Italia")
altro = TP[TP.citta.isna()].groupby(["anno", "gestione"]).apply(agg_tp, include_groups=False).reset_index().assign(citta="Italia, altri comuni")
tc = pd.concat([tc, ital, altro], ignore_index=True)
tot = tc.groupby(["anno", "citta"])[["alunni", "alunni_tempo_pieno"]].sum().reset_index().assign(gestione="totale")
tc = pd.concat([tc, tot], ignore_index=True)
tc["tempo_pieno_pct"] = (100 * tc.alunni_tempo_pieno / tc.alunni).round(2)
tc = tc.sort_values(["citta", "gestione", "anno"]).reset_index(drop=True)
save(tc, "tempo_pieno_primaria_citta_serie.csv")
t24 = tc[(tc.anno == 2024) & (tc.gestione == "totale")].set_index("citta").alunni
check("tempo pieno: Italia 2024 = 14 città + altri comuni (alunni primaria st.+par.)", t24["Italia"], t24.drop(["Italia"]).sum(), 0)

# Milano, scuole 2024/25 con NIL e CAP
mil = TP[(TP.anno == 2024) & (TP.citta == "Milano")].copy()
nilmim = pd.read_csv(os.path.join(SC, "pulito", "miur_scuole_anagrafica.csv"), sep=";", usecols=["codice_mecc", "id_nil"]).drop_duplicates("codice_mecc")
mil = mil.merge(nilmim, left_on="CODICESCUOLA", right_on="codice_mecc", how="left")
ms = mil.groupby(["CODICESCUOLA", "gestione", "CAPSCUOLA", "id_nil"], dropna=False).apply(agg_tp, include_groups=False).reset_index()
ms["tempo_pieno_pct"] = (100 * ms.alunni_tempo_pieno / ms.alunni).round(1)
# mensa (solo statali): "SI" se almeno un edificio della scuola ha uno spazio mensa
amb = pd.read_csv(os.path.join(R, "EDIAMBFUNZSTA202120242520250806.csv"), dtype=str)
mens = amb.groupby("CODICESCUOLA").MENSA.apply(lambda s: "SI" if (s == "SI").any() else ("NO" if (s == "NO").any() else "ND")).rename("mensa")
ms = ms.merge(mens, on="CODICESCUOLA", how="left")
ms.loc[ms.gestione != "statale", "mensa"] = "non rilevata (paritaria)"
ms["mensa"] = ms.mensa.fillna("manca nel file")
save(ms.drop(columns=["CODICESCUOLA"]).rename(columns={"CAPSCUOLA": "cap"}), "tempo_pieno_milano_scuole_2024_25_senza_codici.csv")
check("Milano 2024/25: alunni primaria (st+par) nel file tempo scuola", int(ms.alunni.sum()), 52353, 0)
CONTROLLI["milano_2024_alunni_senza_nil"] = int(ms[ms.id_nil.isna()].alunni.sum())

# mensa nelle 14 città + Italia (statali, primaria, 2024/25)
st = TP[(TP.anno == 2024) & (TP.gestione == "statale")]
sc_st = st.groupby(["CODICESCUOLA", "CODICECOMUNESCUOLA"]).n.sum().reset_index().merge(mens, on="CODICESCUOLA", how="left")
sc_st["citta"] = sc_st.CODICECOMUNESCUOLA.map(NOME_CAT).fillna("Italia, altri comuni")
sc_st["mensa"] = sc_st.mensa.fillna("manca nel file")
mc = sc_st.pivot_table(index="citta", columns="mensa", values="n", aggfunc="sum", fill_value=0)
for c in ("SI", "NO", "ND", "manca nel file"):
    if c not in mc: mc[c] = 0
mc["alunni"] = mc[["SI", "NO", "ND", "manca nel file"]].sum(axis=1)
tot_it = mc.sum(); tot_it.name = "Italia"; mc = pd.concat([mc, tot_it.to_frame().T])
mc["pct_alunni_in_scuole_con_mensa"] = (100 * mc["SI"] / mc.alunni).round(1)
mc["pct_alunni_scuole_non_nel_file_edilizia"] = (100 * mc["manca nel file"] / mc.alunni).round(1)
mc = mc.reset_index().rename(columns={"index": "citta"})
save(mc, "mensa_primaria_statale_2024_25_citta.csv")

# ================================================================ 4. INVALSI: dispersione implicita (grado 8 e 13)
iv = pd.read_csv(os.path.join(RAW, "invalsi", "report_generale_unito_dispersione_e_eccellenti_agg_2025.csv"), sep=";", decimal=",", encoding="cp1252")
iv.columns = ["id", "terr", "sub", "den", "grado", "anno", "disp", "vdisp", "ecc", "vecc", "cop"]
iv.loc[iv.disp == 999, "disp"] = np.nan; iv.loc[iv.ecc == 999, "ecc"] = np.nan
nomi_iv = {"MILANO": "Milano", "ROMA": "Roma", "TORINO": "Torino", "NAPOLI": "Napoli", "BOLOGNA": "Bologna", "FIRENZE": "Firenze", "GENOVA": "Genova",
           "VENEZIA": "Venezia", "BARI": "Bari", "PALERMO": "Palermo", "CATANIA": "Catania", "MESSINA": "Messina", "REGGIO DI CALABRIA": "Reggio Calabria", "CAGLIARI": "Cagliari"}
cp = iv[(iv.terr == "Comune plesso") & (iv["sub"] == "Totale") & iv.den.str.upper().isin(nomi_iv)].copy()
cp["citta"] = cp.den.str.upper().map(nomi_iv)
# controllo: ogni città ha al massimo una riga per anno-grado
check("invalsi: righe doppie città-anno-grado", int(cp.duplicated(["citta", "anno", "grado"]).sum()), 0, 0)
it = iv[(iv.terr == "Italia") & (iv["sub"] == "Totale")].assign(citta="Italia")
lm = iv[(iv.terr == "Regione") & (iv["sub"] == "Totale") & (iv.den.str.upper() == "LOMBARDIA")].assign(citta="Lombardia")
dis = pd.concat([cp, it, lm])[["citta", "grado", "anno", "disp", "ecc", "cop"]].sort_values(["citta", "grado", "anno"])
save(dis, "invalsi_dispersione_citta_serie.csv")
# per origine: il file non la dà per i singoli comuni, ma per Italia e per provincia (Milano = provincia/Città metropolitana)
oi = iv[(iv.terr == "Italia")].assign(citta="Italia")
op = iv[(iv.terr == "Provincia") & (iv.den.str.upper() == "MILANO")].assign(citta="Provincia di Milano")
orig = pd.concat([oi, op])
orig = orig[orig["sub"].str.strip().isin(["Nativo", "Straniero I generazione", "Straniero II generazione", "Totale"])]
orig = orig[["citta", "sub", "grado", "anno", "disp", "cop"]].sort_values(["citta", "grado", "sub", "anno"])
orig["sub"] = orig["sub"].str.strip()
save(orig, "invalsi_dispersione_per_origine.csv")

# ================================================================ 5. Bes dei territori (città metropolitane)
bes = pd.read_csv(os.path.join(P, "benessere", "pulito", "bes_lungo.csv"), low_memory=False,
                  usecols=["codice", "indicatore", "unita", "sesso", "territorio", "tipo_territorio", "citta_metropolitana", "anno", "valore", "polarita"])
cod = {"02IST001": "4-5 anni a scuola (%)", "02IST006-N22": "NEET 15-29 anni (%)", "12SER002": "Bambini nei servizi comunali per l'infanzia (%)",
       "02IST010P": "Competenza numerica non adeguata, 3ª media (%)", "02IST011P": "Competenza alfabetica non adeguata, 3ª media (%)"}
bb = bes[bes.codice.isin(cod) & (bes.sesso == "Totale") & (bes.tipo_territorio.isin(["provincia", "italia"]))]
cm = bb[(bb.citta_metropolitana == True) | (bb.tipo_territorio == "italia")]
cm = cm.assign(indicatore_breve=cm.codice.map(cod))
save(cm[["codice", "indicatore_breve", "territorio", "anno", "valore", "polarita"]].sort_values(["codice", "territorio", "anno"]), "bes_istruzione_citta_metropolitane.csv")
CONTROLLI["bes_territori_cm"] = sorted(cm[cm.tipo_territorio == "provincia"].territorio.unique().tolist())

# ================================================================ 6. Redditi
mef = pd.read_csv(os.path.join(P, "redditi", "pulito", "mef_comuni_2000_2024.csv"), dtype={"istat": str}, usecols=["anno", "istat", "comune", "contribuenti", "reddito_complessivo_eur"])
mef = mef[(mef.anno == 2024) & mef.istat.isin([i for _, i, _ in CITTA])].copy()
mef["citta"] = mef.istat.map(NOME_ISTAT)
mef["reddito_medio_contribuente_eur"] = (mef.reddito_complessivo_eur / mef.contribuenti).round(0)
save(mef[["citta", "istat", "contribuenti", "reddito_medio_contribuente_eur"]].sort_values("reddito_medio_contribuente_eur", ascending=False), "reddito_citta_2024.csv")
check("reddito Milano 2024 per contribuente (filone redditi: 40.316 per il 2025 correnti?)", float(mef[mef.citta == "Milano"].reddito_medio_contribuente_eur.iloc[0]), 40316, 400)

inc = pd.read_csv(os.path.join(P, "redditi", "pulito", "cap_milano_media_euro2025.csv")); inc["cap"] = inc.cap.astype(str)
inc = inc.set_index("cap")["2024"]
# CAP: tempo pieno e quota paritaria
mil["n"] = mil.n.astype(float)
cap = mil.groupby("CAPSCUOLA").apply(lambda x: pd.Series({
    "alunni": x.n.sum(), "tempo_pieno_pct_tot": 100 * x.loc[x.tempo_pieno, "n"].sum() / x.n.sum(),
    "alunni_statali": x.loc[x.gestione == "statale", "n"].sum(),
    "tempo_pieno_pct_statali": (100 * x.loc[(x.gestione == "statale") & x.tempo_pieno, "n"].sum() / x.loc[x.gestione == "statale", "n"].sum()) if (x.gestione == "statale").any() else np.nan,
    "quota_paritaria_pct": 100 * x.loc[x.gestione == "paritaria", "n"].sum() / x.n.sum()}), include_groups=False).reset_index().rename(columns={"CAPSCUOLA": "cap"})
cap["reddito_medio_euro2025"] = cap.cap.map(inc)
cap = cap.round(1)
save(cap, "milano_cap_tempo_pieno_reddito_2024_25.csv")
okc = cap.dropna(subset=["reddito_medio_euro2025"])
CONTROLLI["cap_n"] = len(okc)
rho_tot = spearmanr(okc.tempo_pieno_pct_tot, okc.reddito_medio_euro2025)
rho_st = spearmanr(okc.dropna(subset=["tempo_pieno_pct_statali"]).tempo_pieno_pct_statali, okc.dropna(subset=["tempo_pieno_pct_statali"]).reddito_medio_euro2025)
rho_par = spearmanr(okc.quota_paritaria_pct, okc.reddito_medio_euro2025)
def ic(x, y, n=5000, seed=7):
    rng = np.random.default_rng(seed); x = np.asarray(x); y = np.asarray(y); r = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x)); r.append(spearmanr(x[i], y[i])[0])
    return [round(float(np.nanpercentile(r, 2.5)), 2), round(float(np.nanpercentile(r, 97.5)), 2)]
CONTROLLI["spearman_cap"] = {
    "tempo_pieno_tot_vs_reddito": [round(float(rho_tot[0]), 2), round(float(rho_tot[1]), 4), ic(okc.tempo_pieno_pct_tot, okc.reddito_medio_euro2025)],
    "tempo_pieno_statali_vs_reddito": [round(float(rho_st[0]), 2), round(float(rho_st[1]), 4)],
    "quota_paritaria_vs_reddito": [round(float(rho_par[0]), 2), round(float(rho_par[1]), 4), ic(okc.quota_paritaria_pct, okc.reddito_medio_euro2025)]}

# reddito stimato per NIL: media dei redditi dei CAP, pesata con i civici del NIL in ogni CAP (collegamento del filone citta-15-minuti)
col = pd.read_csv(os.path.join(P, "citta-15-minuti", "collegamento_CAP_NIL_tabella_civici_stimati.csv"))
col["ID_NIL"] = col.ID_NIL.astype(int); col = col.set_index("ID_NIL")
w = col.div(col.sum(axis=1), axis=0)
ok = [c for c in w.columns if c in inc.index]
nil["reddito_stimato_euro2025"] = nil.id_nil.map((w[ok] * inc[ok]).sum(axis=1) / w[ok].sum(axis=1)).round(0)
nil["quota_civici_nel_cap_principale_pct"] = nil.id_nil.map((100 * w.max(axis=1)).round(0))

# NIL: tempo pieno e mensa (primaria), 2024/25
def nilagg(x):
    return pd.Series({"alunni_primaria": x.alunni.sum(), "tp_pct_tot": 100 * x.alunni_tempo_pieno.sum() / x.alunni.sum(),
                      "alunni_statali": x.loc[x.gestione == "statale", "alunni"].sum(),
                      "tp_pct_statali": (100 * x.loc[x.gestione == "statale", "alunni_tempo_pieno"].sum() / x.loc[x.gestione == "statale", "alunni"].sum()) if (x.gestione == "statale").any() else np.nan,
                      "quota_paritaria_pct": 100 * x.loc[x.gestione == "paritaria", "alunni"].sum() / x.alunni.sum(),
                      "mensa_pct_statali": (100 * x.loc[(x.gestione == "statale") & (x.mensa == "SI"), "alunni"].sum() / x.loc[x.gestione == "statale", "alunni"].sum()) if (x.gestione == "statale").any() else np.nan})
msn = ms.dropna(subset=["id_nil"]).copy(); msn["id_nil"] = msn.id_nil.astype(int)
nn = msn.groupby("id_nil").apply(nilagg, include_groups=False).reset_index().round(1)
nil = nil.merge(nn, on="id_nil", how="left")
nil["alunni_primaria"] = nil.alunni_primaria.fillna(0).astype(int)
save(nil, "milano_nil_poverta_educativa.csv")
CONTROLLI["nil_con_scuole_primarie"] = int((nil.alunni_primaria > 0).sum())
CONTROLLI["nil_tempo_pieno_statali_min_max"] = [float(nil.tp_pct_statali.min()), float(nil.tp_pct_statali.max())]
sc_st_mil = ms[ms.gestione == "statale"]
CONTROLLI["milano_statali_unita_sotto_50pct_tp"] = int((sc_st_mil.tempo_pieno_pct < 50).sum())
CONTROLLI["milano_statali_unita"] = int(len(sc_st_mil))

# sedi per NIL e reddito stimato (solo NIL con almeno 150 bambini 0-2)
nn2 = nil.dropna(subset=["sedi_nido_per_1000_0_2", "reddito_stimato_euro2025"])
r1 = spearmanr(nn2.sedi_nido_per_1000_0_2, nn2.reddito_stimato_euro2025)
CONTROLLI["spearman_nil_sedi_nido_reddito"] = [round(float(r1[0]), 2), round(float(r1[1]), 4), len(nn2), ic(nn2.sedi_nido_per_1000_0_2, nn2.reddito_stimato_euro2025)]

json.dump({"controlli": CONTROLLI, "avvisi": AVVISI}, open(os.path.join(PU, "controlli_build.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
print("AVVISI:", AVVISI if AVVISI else "nessuno")
