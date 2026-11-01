"""Scrive i file dati della pagina "Le scuole di Milano" (docs/scuole/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <scuole_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge scuole/pulito/*.csv (prodotti da build.py e analisi.py), i poligoni NIL di citta-15-minuti, i nomi dei NIL di censimenti/,
scuole/raw/comune_ds1739-1741 (alunni che vanno a scuola fuori dal proprio NIL).
Scrive in <docs_dir>/scuole/data/: riepilogo.json, scuole.json, nil.geojson, scuole_anno.csv, scuole_confronto_2024.csv,
nil_scuole.csv, serie_per_ordine.csv, concentrazione_indici.csv, confronto_MIM_Comune_quota_stranieri.csv.
Dati aggregati per scuola e anno (istituzioni pubbliche e private): nessun alunno singolo.
"""
import sys, os, re, json, glob
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

S, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = f"{S}/pulito"
OUT = f"{DOCS}/scuole/data"
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")
def nn(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else x
from decimal import Decimal, ROUND_HALF_UP
def r1(x, d=1):
    x = nn(x)
    return None if x is None else float(Decimal(str(round(float(x), 6))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))

C = pd.read_csv(f"{PU}/comune_scuole_anno.csv", sep=";", dtype={"codice_comune": str})
M = pd.read_csv(f"{PU}/miur_scuole_anno.csv", sep=";", dtype={"codice_mecc": str})
RN = pd.read_csv(f"{PU}/residenti_nil_fascia_cittadinanza_ds27.csv", sep=";")
SL = pd.read_csv(f"{PU}/serie_lunga_ordine_gestione.csv", sep=";")
CI = pd.read_csv(f"{PU}/concentrazione_indici.csv", sep=";")
SQ = pd.read_csv(f"{PU}/stranieri_scuole_vs_nil_2024.csv", sep=";", dtype={"codice_comune": str})
SS = pd.read_csv(f"{PU}/stranieri_serie_per_ordine.csv", sep=";")
CQ = pd.read_csv(f"{PU}/confronto_quota_stranieri_MIM_vs_Comune_totali.csv", sep=";")
NB = pd.read_csv(f"{PU}/nascite_e_prima_primaria.csv", sep=";")
RI = pd.read_csv(f"{PU}/iscritti_su_residenti_fascia.csv", sep=";")
VAR = pd.read_csv(f"{PU}/scuole_variazione_2015_2024.csv", sep=";", dtype={"codice_comune": str})
T2 = pd.read_csv(f"{PU}/sec2_per_tipo_stranieri.csv", sep=";")
BN = pd.read_csv(f"{P}/nomi-bambini/pulito/nascite_milano_ds289.csv")
ana = pd.read_csv(f"{P}/censimenti/pulito/nil_2021_anagrafica.csv")
NILNAME = dict(zip(ana.nil, ana.nil_nome))
ORD = ["infanzia", "primaria", "sec1", "sec2"]
ORDNOME = ["Infanzia", "Primaria", "Secondaria di I grado", "Secondaria di II grado"]
BAND = {"infanzia": "3-5", "primaria": "6-10", "sec1": "11-13", "sec2": "14-18"}
GEST = ["statale", "comunale", "privata_paritaria", "privata_non_paritaria", "paritaria_mim"]
GESTNOME = ["Statale", "Comunale (infanzia)", "Privata paritaria", "Privata non paritaria", "Paritaria (MIM)"]
ANNI = list(range(2009, 2025))

# ------------------------------------------------------------------ nomi leggibili
ACR = {"ITIS", "IPSIA", "ITC", "ITCG", "ITI", "IPIA", "IPSSAR", "IPC", "IIS", "ICS", "CPIA", "CFP", "IPAA", "ITT", "ITE", "IISS", "SS", "IC", "ITG", "ITA", "ITF", "ITAS", "LSS", "CTP", "ITSOS", "IP", "IT", "ISIS", "IPSAR", "IPSCT", "ISS", "ITET", "ITS", "IPCT"}
ROM = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XX", "XXI", "XXII", "XXIII", "XXV", "XXVI", "XXVII"}
def bello(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    if s != s.upper(): return s
    def f(m):
        w = m.group(0)
        if w in ACR or w in ROM: return w
        return w[0] + w[1:].lower()
    out = re.sub(r"[A-ZÀ-Ý]+", f, s)
    out = re.sub(r"(?<=\w)'([a-zà-ÿ])", lambda m: "'" + m.group(1), out)
    return out
def via(s):
    s = re.sub(r"\s+", " ", str(s)).strip()
    if re.search(r"\(\s*ORD", s, re.I):
        s = re.split(r"\(\s*ORD", s, flags=re.I)[0].strip()  # sede ordinaria
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    if s == s.upper():
        return bello(s)
    return re.sub(r"\b[A-Z]{3,}\b", lambda m: m.group(0).capitalize(), s)

# ------------------------------------------------------------------ serie per ordine
iscr = C.groupby(["anno_inizio", "ordine"]).iscritti.sum().unstack()
non_it = C.groupby(["anno_inizio", "ordine"]).cittadinanza_non_italiana.sum().unstack()
sec2 = SL[SL.ordine == "sec2"].groupby("anno_inizio").alunni.sum()   # Comune ds105, fino al 2023/24
for a in ANNI:
    pass
RES = RN.groupby(["anno", "fascia_eta"])[["stranieri", "italiani"]].sum()
def res_band(o, a):
    f = BAND[o]
    return int(RES.loc[(a, f)].sum()) if (a, f) in RES.index else None
def res_band_stran(o, a):
    f = BAND[o]
    return int(RES.loc[(a, f), "stranieri"]) if (a, f) in RES.index else None
serie = {}
for o in ORD:
    s = {}
    for a in ANNI:
        if o == "sec2": v = sec2.get(a)
        else: v = iscr.loc[a, o] if a in iscr.index else None
        s[a] = None if v is None or pd.isna(v) else int(v)
    serie[o] = {"iscritti": [s[a] for a in ANNI], "residenti_fascia": [res_band(o, a) for a in ANNI], "residenti_fascia_nome": BAND[o]}
nascite = {int(r.anno): int(r.nati_avvenuti_a_milano) for r in BN.itertuples()}
check("infanzia 2024", serie["infanzia"]["iscritti"][-1], 26522)
check("primaria 2024", serie["primaria"]["iscritti"][-1], 54137)
check("sec1 2024", serie["sec1"]["iscritti"][-1], 35370)
check("sec2 2023 (ds105)", serie["sec2"]["iscritti"][-2], 74830)

# ------------------------------------------------------------------ gestione nel tempo
gest = {}
for o in ["infanzia", "primaria", "sec1"]:
    g = C[C.ordine == o].groupby(["anno_inizio", "gestione"]).iscritti.sum().unstack().fillna(0)
    gest[o] = {k: [int(g.loc[a, k]) if (a in g.index and k in g.columns) else 0 for a in ANNI] for k in ["statale", "comunale", "privata_paritaria", "privata_non_paritaria"]}
gm = M[M.ordine == "sec2"].groupby(["anno_inizio", "tipo"]).iscritti.sum().unstack().fillna(0)
gest["sec2"] = {"statale": [int(gm.loc[a, "statale"]) if a in gm.index else None for a in ANNI], "paritaria_mim": [int(gm.loc[a, "paritaria"]) if a in gm.index else None for a in ANNI]}

# ------------------------------------------------------------------ cittadinanza non italiana: serie e confronti
def row(df, a, o):
    x = df[(df.anno_inizio == a) & (df.ordine == o)]
    return x.iloc[0] if len(x) else None
stran = {}
for o in ORD:
    st = {"comune": [], "mim": [], "residenti": [], "nati_fuori": []}
    for a in ANNI:
        r = row(SS, a, o)
        st["comune"].append(r1(r.quota_non_italiana_comune_pct) if r is not None else None)
        st["mim"].append(r1(r.quota_non_italiana_mim_pct) if r is not None else None)
        st["residenti"].append(r1(r.quota_non_italiana_residenti_pct) if r is not None else None)
        st["nati_fuori"].append(r1(r.quota_nati_fuori_italia_pct) if r is not None else None)
    stran[o] = st
check("primaria 2024 Comune", stran["primaria"]["comune"][-1], 22.6, .05)
check("primaria 2024 MIM", stran["primaria"]["mim"][-1], 25.5, .05)
check("primaria 2024 residenti 6-10", stran["primaria"]["residenti"][-1], 25.7, .06)

# quota per gestione 2024 (Comune)
gg = C[C.anno_inizio == 2024].groupby(["ordine", "gestione"]).agg(scuole=("iscritti", "size"), iscritti=("iscritti", "sum"), non_it=("cittadinanza_non_italiana", "sum")).reset_index()
quota_gestione = [dict(ordine=r.ordine, gestione=r.gestione, scuole=int(r.scuole), iscritti=int(r.iscritti), quota=r1(100 * r.non_it / r.iscritti)) for r in gg.itertuples()]

# ------------------------------------------------------------------ Comune vs MIM (totali statali / paritarie)
cm = CQ[CQ.anno_inizio.isin([2018, 2024]) & CQ.tipo.isin(["statale", "paritaria"])].copy()
cm_out = [dict(anno=int(r.anno_inizio), ordine=r.ordine, tipo=r.tipo, comune=r1(r.quota_comune_pct), mim=r1(r.quota_mim_pct), differenza_pp=r1(r.differenza_pp_mim_meno_comune)) for r in cm.itertuples()]
cm.to_csv(f"{OUT}/confronto_MIM_Comune_quota_stranieri.csv", index=False, sep=";")
serie_cm = {}
for o in ["primaria", "sec1"]:
    s = CQ[(CQ.ordine == o) & (CQ.tipo == "statale")].sort_values("anno_inizio")
    serie_cm[o] = {"anni": [int(x) for x in s.anno_inizio], "comune": [r1(x) for x in s.quota_comune_pct], "mim": [r1(x) for x in s.quota_mim_pct]}

# ------------------------------------------------------------------ concentrazione
conc = CI.copy()
CI.to_csv(f"{OUT}/concentrazione_indici.csv", index=False, sep=";")
conc_out = {o: {str(int(r.anno_inizio)): dict(scuole=int(r.scuole), D_scuole=r.D_tra_scuole, D_scuole_pubbliche=r.D_tra_scuole_solo_pubbliche, D_gestioni=r.D_tra_gestioni, D_nil_sede=r.D_tra_NIL_per_sede_scuola, D_nil_residenti=r.D_tra_NIL_residenti_fascia,
                       oltre50=int(r.scuole_oltre_50pct), quota_in_oltre50=r.quota_stranieri_in_scuole_oltre_50pct, sotto10=int(r.scuole_sotto_10pct), it_in_sotto10=r.quota_italiani_in_scuole_sotto_10pct)
                for r in CI[CI.ordine == o].itertuples()} for o in ["infanzia", "primaria", "sec1"]}
check("D primaria 2024 scuole", conc_out["primaria"]["2024"]["D_scuole"], 0.415, .0005)
check("D primaria 2024 NIL residenti", conc_out["primaria"]["2024"]["D_nil_residenti"], 0.289, .0005)
check("D primaria 2012 scuole", conc_out["primaria"]["2012"]["D_scuole"], 0.416, .0005)

# ------------------------------------------------------------------ fuori dal NIL (ds1739-1741)
fuori = {}
for ds, o in [("ds1740", "infanzia"), ("ds1739", "primaria"), ("ds1741", "sec1")]:
    d = pd.read_csv(glob.glob(f"{S}/raw/comune_{ds}/*.csv")[0], sep=";", dtype=str)
    fuori[o] = {r[0]: float(r[2]) for r in d.itertuples(index=False)}
check("fuori NIL primaria 2023/24", fuori["primaria"]["2023/24"], 54.4, .05)

# ------------------------------------------------------------------ scuole: una riga per scuola
def serie_scuola(df, col, key, code):
    s = df[df[key] == code].set_index("anno_inizio")[col]
    return [int(s[a]) if a in s.index and not pd.isna(s[a]) else None for a in ANNI]
SQi = SQ.set_index(["ordine", "codice_comune"])
scuole = []
C24 = C[C.anno_inizio == 2024]
for o in ["infanzia", "primaria", "sec1"]:
    cc = C[C.ordine == o]
    for code in sorted(C24[C24.ordine == o].codice_comune.unique()):
        sub = cc[cc.codice_comune == code].sort_values("anno_inizio")
        last = sub.iloc[-1]
        if pd.isna(last.lon) or last.iscritti <= 0: continue
        isc = [None] * len(ANNI); st = [None] * len(ANNI)
        for r in sub.itertuples():
            if r.anno_inizio in ANNI:
                i = ANNI.index(r.anno_inizio); isc[i] = int(r.iscritti); st[i] = int(r.cittadinanza_non_italiana)
        key = (o, code)
        qs = SQi.loc[key] if key in SQi.index else None
        rr = RN[(RN.anno == 2024) & (RN.fascia_eta == BAND[o]) & (RN.id_nil == last.id_nil)]
        rq = None
        if len(rr): rq = 100 * rr.stranieri.sum() / (rr.stranieri.sum() + rr.italiani.sum())
        scuole.append(dict(id=f"C{code}", n=bello(last.denominazione), a=via(last.indirizzo), o=ORD.index(o), g=GEST.index(last.gestione), x=round(float(last.lon), 5), y=round(float(last.lat), 5),
                           nil=int(last.id_nil) if pd.notna(last.id_nil) else None, i=isc, s=st, r=r1(rq), z=r1(qs.quota_altre_scuole_nil_pct) if qs is not None else None, fonte="C"))
M2 = M[M.ordine == "sec2"]
for code in sorted(M2[M2.anno_inizio == 2024].codice_mecc.unique()):
    sub = M2[M2.codice_mecc == code].sort_values("anno_inizio"); last = sub.iloc[-1]
    if pd.isna(last.lon) or last.iscritti <= 0: continue
    isc = [None] * len(ANNI); st = [None] * len(ANNI)
    for r in sub.itertuples():
        i = ANNI.index(r.anno_inizio); isc[i] = int(r.iscritti); st[i] = int(r.cittadinanza_non_italiana)
    rr = RN[(RN.anno == 2024) & (RN.fascia_eta == "14-18") & (RN.id_nil == last.id_nil)]
    rq = 100 * rr.stranieri.sum() / (rr.stranieri.sum() + rr.italiani.sum()) if len(rr) else None
    scuole.append(dict(id=f"M{code}", n=bello(last.denominazione), a=via(last.indirizzo), o=3, g=0 if last.tipo == "statale" else 4, x=round(float(last.lon), 5), y=round(float(last.lat), 5),
                       nil=int(last.id_nil) if pd.notna(last.id_nil) else None, i=isc, s=st, r=r1(rq), z=None, fonte="M"))
print("scuole sulla mappa", len(scuole), {ORD[k]: sum(1 for s in scuole if s["o"] == k) for k in range(4)})
check("scuole mappa infanzia (con coordinate)", sum(1 for s in scuole if s["o"] == 0), 293, 5)

# ------------------------------------------------------------------ confronto scuola vs quartiere (tabella con nomi)
rows = []
for s in scuole:
    i24 = s["i"][-1]; n24 = s["s"][-1]
    q = 100 * n24 / i24 if i24 else None
    rows.append(dict(codice=s["id"], scuola=s["n"], indirizzo=s["a"], ordine=ORDNOME[s["o"]], gestione=GESTNOME[s["g"]], nil=NILNAME.get(s["nil"]) if s["nil"] else "", iscritti_2024=i24,
                     cittadinanza_non_italiana_2024=n24, quota_scuola_pct=r1(q, 2), quota_residenti_nil_stessa_fascia_pct=r1(s["r"], 2), differenza_punti=r1(q - s["r"], 2) if (q is not None and s["r"] is not None) else None,
                     quota_altre_scuole_stesso_ordine_nil_pct=s["z"], fonte="Comune ANASCO" if s["fonte"] == "C" else "MIM"))
pd.DataFrame(rows).to_csv(f"{OUT}/scuole_confronto_2024.csv", index=False, sep=";")
# scuole.json: per ogni scuola lo scarto lo calcola la pagina
# ------------------------------------------------------------------ variazione per scuola 2015-2024 (conteggi)
vv = VAR[VAR.situazione == "presente_in_entrambi"]
variazione = {o: vv[vv.ordine == o].classe_variazione.value_counts().to_dict() for o in ["infanzia", "primaria", "sec1"]}
chiuse = {o: dict(non_piu=int((VAR[VAR.ordine == o].situazione == "non_piu_presente_2024").sum()), nuove=int((VAR[VAR.ordine == o].situazione == "nuova_o_riaperta_2024").sum())) for o in ["infanzia", "primaria", "sec1"]}
var_gest = []
for o in ["infanzia", "primaria", "sec1"]:
    for g, d in vv[vv.ordine == o].groupby("gruppo_gestione"):
        var_gest.append(dict(ordine=o, gruppo=g, scuole=int(len(d)), v2015=int(d.iscritti_2015.sum()), v2024=int(d.iscritti_2024.sum()), var_pct=r1(100 * (d.iscritti_2024.sum() / d.iscritti_2015.sum() - 1))))

# ------------------------------------------------------------------ NIL: geometrie e valori
nilgeo = json.load(open(f"{P}/citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson", encoding="utf-8"))
def resids(nil, o, a):
    rr = RN[(RN.anno == a) & (RN.fascia_eta == BAND[o]) & (RN.id_nil == nil)]
    if not len(rr): return None, None
    return int((rr.stranieri + rr.italiani).sum()), int(rr.stranieri.sum())
c15 = C[C.anno_inizio == 2015]; c24 = C[C.anno_inizio == 2024]
feats = []; nilrows = []
for f in nilgeo["features"]:
    nid = int(f["properties"]["ID_NIL"])
    g = shape(f["geometry"]).simplify(0.0002, preserve_topology=True)
    p = dict(i=nid, n=NILNAME.get(nid) or f["properties"]["NIL"].title())
    for k, o in enumerate(["infanzia", "primaria", "sec1"]):
        a15 = c15[(c15.id_nil == nid) & (c15.ordine == o)]; a24 = c24[(c24.id_nil == nid) & (c24.ordine == o)]
        p[f"i15_{k}"] = int(a15.iscritti.sum()); p[f"i24_{k}"] = int(a24.iscritti.sum())
        p[f"n24_{k}"] = int(a24.cittadinanza_non_italiana.sum()); p[f"s24_{k}"] = int(len(a24))
        t15, _ = resids(nid, o, 2015); t24, st24 = resids(nid, o, 2024)
        p[f"r15_{k}"] = t15; p[f"r24_{k}"] = t24; p[f"rn24_{k}"] = st24
    t15 = sum(p[f"i15_{k}"] for k in range(3)); t24 = sum(p[f"i24_{k}"] for k in range(3))
    p["I15"] = t15; p["I24"] = t24; p["Iv"] = round(100 * (t24 / t15 - 1), 1) if t15 >= 200 else None
    r15 = sum(p[f"r15_{k}"] or 0 for k in range(3)); r24 = sum(p[f"r24_{k}"] or 0 for k in range(3))
    p["R15"] = r15; p["R24"] = r24; p["Rv"] = round(100 * (r24 / r15 - 1), 1) if r15 >= 200 else None
    feats.append({"type": "Feature", "properties": p, "geometry": json.loads(json.dumps(mapping(g), default=float))})
    nilrows.append(p)
def rnd_coords(c):
    if isinstance(c[0], (int, float)): return [round(c[0], 5), round(c[1], 5)]
    return [rnd_coords(x) for x in c]
for ft in feats: ft["geometry"]["coordinates"] = rnd_coords(ft["geometry"]["coordinates"])
json.dump({"type": "FeatureCollection", "features": feats}, open(f"{OUT}/nil.geojson", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(nilrows).rename(columns={"i": "id_nil", "n": "nil"}).to_csv(f"{OUT}/nil_scuole.csv", index=False, sep=";")
check("NIL con iscritti 2024", sum(1 for p in nilrows if p["I24"] > 0), 70, 3)
check("totale iscritti 3 ordini 2024 nei NIL", sum(p["I24"] for p in nilrows), 26522 + 54137 + 35370, 0)

# ------------------------------------------------------------------ tabelle di download
tid = pd.read_csv(f"{PU}/scuole_anno_tidy.csv", sep=";")
tid.to_csv(f"{OUT}/scuole_anno.csv", index=False, sep=";")
pd.DataFrame({"anno_scolastico_inizio": ANNI, **{f"iscritti_{o}": serie[o]["iscritti"] for o in ORD}, **{f"residenti_fascia_{o}_{BAND[o]}": serie[o]["residenti_fascia"] for o in ORD},
              "nati_avvenuti_a_milano": [nascite.get(a) for a in ANNI]}).to_csv(f"{OUT}/serie_per_ordine.csv", index=False, sep=";")

# ------------------------------------------------------------------ coorti (nascite -> prima primaria)
coorti = [dict(coorte=int(r.coorte), nati=int(r.nati_avvenuti_a_milano), prima=int(r.prima_primaria_a_s_coorte_piu_6) if pd.notna(r.prima_primaria_a_s_coorte_piu_6) else None,
               res5=int(r.residenti_eta5_a_fine_coorte_piu_5) if pd.notna(r.residenti_eta5_a_fine_coorte_piu_5) else None,
               rapp_res5=nn(r.prima_primaria_su_residenti_eta5), rapp_nati=nn(r.prima_primaria_su_nati)) for r in NB.itertuples()]
rr5 = [c["rapp_res5"] for c in coorti if c["rapp_res5"] is not None]
check("rapporto prima/res5 min", min(rr5), 0.915, .001); check("rapporto prima/res5 max", max(rr5), 0.947, .001)
# residenti 0 anni 2012 e 2025 (ds223) da riepilogo json
RJ0 = json.load(open(f"{PU}/riepilogo.json", encoding="utf-8"))
res_et = pd.read_csv(f"{PU}/residenti_per_eta_ds223.csv", sep=";")
r0 = res_et[res_et.eta == 0].groupby("anno").residenti.sum()
check("residenti 0 anni 2012", int(r0[2012]), 11818); check("residenti 0 anni 2025", int(r0[2025]), 8751)

sec2tipo = [dict(anno=int(r.anno_inizio), tipo=r.tipo_sec2, iscritti=int(r.iscritti), quota=r1(r.quota_non_italiana_pct), scuole=int(r.scuole)) for r in T2[T2.anno_inizio.isin([2015, 2024])].itertuples()]

riep = dict(
    anni=ANNI, ordini=ORD, ordini_nome=ORDNOME, gestioni=GEST, gestioni_nome=GESTNOME, ultimo_anno=2024,
    serie=serie, nascite={str(k): v for k, v in nascite.items()}, residenti_0_anni={"2012": int(r0[2012]), "2025": int(r0[2025])},
    gestione=gest, stranieri=stran, quota_gestione_2024=quota_gestione, confronto_mim_comune=cm_out, confronto_mim_comune_serie=serie_cm,
    concentrazione=conc_out, fuori_nil=fuori, coorti=coorti, variazione_scuole=variazione, scuole_chiuse_nuove=chiuse, variazione_gestione=var_gest, sec2_tipo=sec2tipo,
    residenti_fascia_2012_2025={o: {str(a): res_band(o, a) for a in (2012, 2025)} for o in ORD},
    iscritti_su_residenti_2024={r.ordine: r.rapporto for r in RI[RI.anno == 2024].itertuples()},
    picchi=dict(infanzia=[2011, 33007], primaria=[2017, 59909], sec1=[2019, 37109], sec2=[2021, 75098]),
    nati_fuori_italia_2024={o: stran[o]["nati_fuori"][-1] for o in ["infanzia", "primaria", "sec1"]},
    stranieri_nati_italia_comune_2023_24={"infanzia": 83.4, "primaria": 71.8, "sec1": 63.2, "sec2": 57.0},
    scaricato="2026-11-01",
)
json.dump(riep, open(f"{OUT}/riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(scuole, open(f"{OUT}/scuole.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for fn in ["riepilogo.json", "scuole.json", "nil.geojson", "scuole_anno.csv"]:
    print(fn, os.path.getsize(f"{OUT}/{fn}") // 1024, "KB")
print("AVVISI:", AVVISI if AVVISI else "nessuno")
