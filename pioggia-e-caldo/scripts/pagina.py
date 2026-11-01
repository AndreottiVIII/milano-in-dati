"""Scrive i file dati delle pagine "Quanto piove a Milano" e "Il quartiere piu' caldo" (docs/pioggia/data/ e docs/caldo/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <pioggia-e-caldo_dir> <milano-in-dati_dir> <docs_dir>

Legge solo le tabelle gia' pulite in pioggia-e-caldo/pulito/ (e pulito/intermedi/P_orario.parquet per i dieci giorni piu' piovosi),
i poligoni dei NIL (citta-15-minuti) e i nomi dei NIL (censimenti/pulito/nil_2021_anagrafica.csv).
NON copia nulla da raw/. Dati ARPA Lombardia: CC0, ripubblicabili. ECA&D (Milano 1858-2008) e NOAA GSOD (Linate): solo
aggregati annuali e, per i dieci giorni piu' piovosi, il valore dello stesso giorno (10 valori), con citazione; nessuna serie giornaliera.
"""
import sys, os, json, math
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

B, R, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(B, "pulito")
OP = os.path.join(DOCS, "pioggia", "data")
OC = os.path.join(DOCS, "caldo", "data")
os.makedirs(OP, exist_ok=True)
os.makedirs(OC, exist_ok=True)
AVVISI = []


def check(nome, calcolato, atteso, tol=0.0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


def rd(n, **k):
    return pd.read_csv(os.path.join(PU, n), **k)


def js(path, obj):
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), default=lambda o: None if (isinstance(o, float) and math.isnan(o)) else (o.item() if hasattr(o, "item") else str(o)))


def clean(v, d=1):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return round(float(v), d)


sel = rd("sensori_selezionati.csv", dtype=str)
nome = dict(zip(sel.idsensore, sel.nomestazione))

# =============================================================== PIOGGIA
A = rd("pioggia_anno_sensore.csv", dtype={"idsensore": str})
MIL = {"9341": "Zavattari", "2006": "Lambrate", "5902": "Corsico", "4065": "Parco Nord", "5908": "Juvara", "14121": "Rosellini", "19373": "Brera", "8149": "Confalonieri"}
LUNGO = rd("pioggia_lungo_periodo.csv")
eca = LUNGO[(LUNGO.serie == "ECAD_Milano_RR_Maugeri") & LUNGO.anno_completo]
check("ECA anni completi", len(eca), 151)

# ---- serie lunga ECA&D: solo aggregati annuali
lungo = [dict(a=int(r.anno), tot=clean(r.tot_mm, 1), g1=int(r.giorni_piovosi_1mm), mx=clean(r.max_giornaliera_mm, 1), g30=int(r.giorni_ge30mm))
         for r in eca.itertuples()]
secco = eca.loc[eca.tot_mm.idxmin()]
umido = eca.loc[eca.tot_mm.idxmax()]
dec = rd("pioggia_lungo_decenni.csv")
dec = dec[dec.serie == "ECAD_Milano_RR_Maugeri"]
eca_dec = [dict(d=int(r.decennio), anni=int(r.anni), tot=clean(r.tot_mm, 0), g1=clean(r.giorni_piovosi_1mm, 1), g30=clean(r.giorni_ge30mm, 1)) for r in dec.itertuples()]

# ---- ARPA: sensore x anno (solo anni completi, pluviometri di Milano)
Ac = A[A.idsensore.isin(MIL) & A.anno_completo].copy()
arpa = []
for r in Ac.itertuples():
    arpa.append(dict(s=r.idsensore, a=int(r.anno), tot=clean(r.tot_mm, 1), g1=int(r.giorni_piovosi_1mm), mxh=clean(r.max_oraria_mm, 1), mxg=clean(r.max_giornaliera_mm, 1),
                     h20=int(r.ore_ge20), h30=int(r.ore_ge30), q=clean(r.quota_top1pct_ore, 3), qw=clean(r.quota_top1pct_ore_piovose, 3), nc=int(r.giorni_non_confermati)))
arpa_sens = []
for sid, nm in MIL.items():
    g = Ac[Ac.idsensore == sid]
    if len(g) == 0:
        continue
    arpa_sens.append(dict(id=sid, nome=nm, ufficiale=nome[sid], da=int(g.anno.min()), a=int(g.anno.max()), anni=len(g),
                          tot=clean(g.tot_mm.mean(), 0), g1=clean(g.giorni_piovosi_1mm.mean(), 0), q=clean(g.quota_top1pct_ore.mean(), 3),
                          qmin=clean(g.quota_top1pct_ore.min(), 3), qmax=clean(g.quota_top1pct_ore.max(), 3), mxh=clean(g.max_oraria_mm.max(), 1)))
# media annuale tra i pluviometri di Milano attivi (solo anni completi, senza Segrate)
mean_year = Ac.groupby("anno").agg(n=("idsensore", "size"), tot=("tot_mm", "mean"), g1=("giorni_piovosi_1mm", "mean")).reset_index()
arpa_media = [dict(a=int(r.anno), n=int(r.n), tot=clean(r.tot, 0), g1=clean(r.g1, 0)) for r in mean_year.itertuples()]
q_tutti = Ac.quota_top1pct_ore

# ---- 2022 contro 2024
def tot(sid, y):
    x = A[(A.idsensore == sid) & (A.anno == y)]
    return None if len(x) == 0 or not bool(x.anno_completo.iloc[0]) else float(x.tot_mm.iloc[0])
dd = []
for sid in ["9341", "2006", "14121", "19373", "5902", "4065", "5908"]:
    a, b = tot(sid, 2022), tot(sid, 2024)
    if a and b:
        dd.append(dict(nome=MIL[sid], t22=clean(a, 0), t24=clean(b, 0), rapporto=clean(b / a, 1)))
zav = [d for d in dd if d["nome"] == "Zavattari"][0]
check("Zavattari 2022", zav["t22"], 450, 1)
check("Zavattari 2024", zav["t24"], 1523, 1)

# ---- tendenze
tc = rd("pioggia_composito_tendenze.csv")
tc_rows = []
ETI = {"tot_mm": "Totale annuo", "giorni_piovosi_1mm": "Giorni di pioggia (almeno 1 mm)", "max_oraria_mm": "Ora più forte dell'anno",
       "max_giornaliera_mm": "Giorno più piovoso dell'anno", "ore_ge10": "Ore con almeno 10 mm", "ore_ge20": "Ore con almeno 20 mm",
       "quota_top1pct_ore": "Quota della pioggia nell'1% delle ore più piovose dell'anno", "quota_top1pct_ore_piovose": "Quota della pioggia nell'1% delle ore bagnate più forti"}
for r in tc.itertuples():
    pct = r.variabile in ("tot_mm", "giorni_piovosi_1mm")
    q = r.variabile.startswith("quota")
    f = 100.0 if (pct or q) else 1.0
    tc_rows.append(dict(v=r.variabile, nome=ETI[r.variabile], anni=int(r.anni), da=int(r.da), a=int(r.a), unita=("% della media del sensore" if pct else ("punti percentuali" if q else ("mm" if "max" in r.variabile else "ore"))),
                        pend=clean(r.pendenza_per_decennio * f, 2), lo=clean(r.ic95_lo * f, 2), hi=clean(r.ic95_hi * f, 2), esclude0=bool(r.ic_esclude_zero)))
tl = rd("pioggia_lungo_tendenze.csv")
tl = tl[(tl.serie == "ECAD_Milano_RR_Maugeri") & (tl.da == 1858)]
tl_rows = [dict(v=r.variabile, anni=int(r.anni), media=clean(r.media, 1), pend=clean(r.pendenza_per_decennio, 2), lo=clean(r.ic95_lo, 2), hi=clean(r.ic95_hi, 2), esclude0=bool(r.ic_esclude_zero)) for r in tl.itertuples()]
gp = [x for x in tl_rows if x["v"] == "giorni_piovosi_1mm"][0]
check("ECA giorni piovosi pendenza", gp["pend"], -1.14, 0.02)
# per periodo
per = rd("pioggia_periodi_milano.csv")
periodi = [dict(p=str(r.periodo), sa=int(r.sensore_anni), sensori=int(r.sensori), tot=clean(r.tot_mm, 0), g1=clean(r.giorni_piovosi_1mm, 0), mxh=clean(r.max_oraria_mm, 1),
                h20=clean(r.ore_ge20, 2), h30=clean(r.ore_ge30, 2), g50=clean(r.giorni_ge50mm, 2), q=clean(r.quota_top1pct_ore, 3)) for r in per.itertuples()]

# ---- dieci giorni piu' piovosi della citta', stazioni affiancate
cit = rd("pioggia_eventi_citta_giorni.csv").head(10)
P = pd.read_parquet(os.path.join(PU, "intermedi", "P_orario.parquet"))
P["giorno"] = (P.ora - pd.Timedelta(minutes=10)).dt.floor("D")
ver = rd("pioggia_giorni_ge40mm_verifica.csv", dtype={"idsensore": str})
ver["giorno"] = pd.to_datetime(ver.giorno)
nonconf = set(zip(ver[ver.stato == "NON_CONFERMATO"].idsensore, ver[ver.stato == "NON_CONFERMATO"].giorno))
ids_mil = ["19373", "5908", "8149", "14121", "9341", "2006", "5902", "4065"]
giorni = []
for r in cit.itertuples():
    g = pd.Timestamp(r.giorno)
    x = P[P.giorno == g]
    st = {}
    for sid in ids_mil:
        y = x[x.idsensore == sid]
        if len(y) >= 20:
            st[sid] = clean(y.mm.sum(), 1)
    # ora piu' forte del giorno tra le stazioni di Milano
    best = None
    for sid in ids_mil:
        y = x[x.idsensore == sid]
        if len(y) >= 20:
            k = y.loc[y.mm.idxmax()]
            if best is None or k.mm > best[0]:
                best = (float(k.mm), sid, int(k.ora.hour))
    giorni.append(dict(g=str(g.date()), mediana=clean(r.mediana, 1), n=int(r.n), stazioni=st, eca=clean(r.eca_milano_mm, 1), linate=clean(r.gsod_linate_mm, 1),
                       ora_mm=clean(best[0], 1) if best else None, ora_st=MIL[best[1]] if best else None, ora_h=best[2] if best else None))
check("giorno 1 = 2009-07-07", 1 if giorni[0]["g"] == "2009-07-07" else 0, 1)

# ---- casi che sorprendono: stesso giorno, stazioni vicine e lontane
def caso(g, ids_extra=None):
    g = pd.Timestamp(g)
    x = P[(P.giorno == g)]
    out = []
    for sid in ["4065", "8149", "9341", "5908", "2006", "5902", "14121", "2065", "5916", "5872", "5894", "5900", "5933"]:
        y = x[x.idsensore == sid]
        if len(y) >= 20:
            s = sel[sel.idsensore == sid].iloc[0]
            out.append(dict(nome=s.nomestazione, km=clean(float(s.dist_duomo_km), 1), mm=clean(y.mm.sum(), 1), nc=(sid, g) in nonconf))
    return out
ec = pd.read_csv(os.path.join(B, "raw/ecad_rr/blend_rr/RR_STAID000173.txt"), skiprows=20, skipinitialspace=True)
ec.columns = [c.strip() for c in ec.columns]
ec["data"] = pd.to_datetime(ec.DATE.astype(str), format="%Y%m%d")
ec = ec[(ec.RR != -9999) & (ec.Q_RR == 0)].set_index("data")
gs = pd.read_csv(os.path.join(R, "neve-e-nebbia/pulito/giorni_neve_nebbia.csv"), usecols=["date", "station", "gsod_prcp_mm", "gsod_prcp_flag"])
gs = gs[(gs.station == "LINATE") & gs.gsod_prcp_flag.isin(list("DFGHI")) & gs.gsod_prcp_mm.notna()]
gs["data"] = pd.to_datetime(gs.date)
gs = gs.set_index("data")
casi = {}
for g in ["2007-09-26", "1999-10-21"]:
    t = pd.Timestamp(g)
    casi[g] = dict(stazioni=caso(g), eca=clean(ec.RR.get(t) / 10.0, 1) if t in ec.index else None, linate=clean(gs.gsod_prcp_mm.get(t), 1) if t in gs.index else None)
c07 = {s["nome"]: s["mm"] for s in casi["2007-09-26"]["stazioni"]}
check("2007-09-26 Parco Nord", c07["Cinisello Balsamo Parco Nord"], 131.4, 0.1)
check("2007-09-26 ECA Brera", casi["2007-09-26"]["eca"], 15.4, 0.05)
c99 = {s["nome"]: s["mm"] for s in casi["1999-10-21"]["stazioni"]}
check("1999-10-21 Juvara", c99["Milano v.Juvara"], 212.0, 0.1)

# ---- giorni non confermati (elenco, ARPA CC0)
nc = ver[ver.stato == "NON_CONFERMATO"].sort_values("mm_giorno", ascending=False)
nc_rows = [dict(g=str(r.giorno.date()), nome=r.nomestazione, mm=clean(r.mm_giorno, 1), rif=clean(r.max_riferimenti, 1), nrif=int(r.n_riferimenti)) for r in nc.itertuples()]
check("giorni non confermati", len(nc_rows), 100)
tot40 = len(ver)

# ---- qualita' e copertura
qs = rd("riepilogo_copertura_sensori.csv", dtype={"idsensore": str})
pre = qs[qs.tipologia == "Precipitazione"]
cop_p = [dict(nome=MIL[r.idsensore], ufficiale=r.nomestazione, dist=clean(r.dist_duomo_km, 1), anni=int(r.anni_completi), da=int(r.primo_anno), a=int(r.ultimo_anno), buchi=int(r.anni_mancanti_tra_primo_e_ultimo))
         for r in pre.itertuples() if r.idsensore in MIL]
tot_righe = int(qs.righe.sum())
meno999 = int(qs.meno999.sum())

riep_p = dict(
    note="Tutti i numeri della pagina 'Quanto piove a Milano'. Campo origine = file in pioggia-e-caldo/pulito/ da cui viene il numero.",
    scaricato="2026-11-01",
    quota_media=clean(q_tutti.mean(), 3), quota_min=clean(q_tutti.min(), 3), quota_max=clean(q_tutti.max(), 3), sensore_anni=int(len(Ac)),
    ore_anno=8760, ore_1pct=88,
    secco=dict(a=int(secco.anno), mm=clean(secco.tot_mm, 1)), umido=dict(a=int(umido.anno), mm=clean(umido.tot_mm, 1)), eca_media=clean(eca.tot_mm.mean(), 0),
    eca_anni=len(eca), eca_da=int(eca.anno.min()), eca_a=int(eca.anno.max()),
    giorni_ge40=int(tot40), giorni_non_confermati=len(nc_rows),
    righe_scaricate=tot_righe, righe_meno999=meno999,
    origine=dict(eca="pulito/pioggia_lungo_periodo.csv (serie ECAD_Milano_RR_Maugeri)", arpa="pulito/pioggia_anno_sensore.csv", tendenze="pulito/pioggia_composito_tendenze.csv, pioggia_lungo_tendenze.csv",
                 giorni="pulito/pioggia_eventi_citta_giorni.csv + intermedi/P_orario.parquet", verifica="pulito/pioggia_giorni_ge40mm_verifica.csv",
                 copertura="pulito/riepilogo_copertura_sensori.csv"))
js(os.path.join(OP, "riepilogo.json"), dict(riep=riep_p, eca_decenni=eca_dec, arpa_sensori=arpa_sens, arpa_media=arpa_media, arpa_2022_2024=dd, tendenze=tc_rows,
                                          tendenze_eca=tl_rows, periodi=periodi, giorni=giorni, casi=casi, copertura=cop_p))
js(os.path.join(OP, "eca_annuale.json"), dict(nota="Aggregati annuali da ECA&D (Milano, serie Maugeri, STAID 173), 1858-2008. Solo ricerca e istruzione non commerciali; citare Klein Tank et al. 2002, Int. J. Climatol. 22, 1441-1453. giorni_1mm = giorni con almeno 1 mm; max = giorno piu' piovoso dell'anno (mm); g30 = giorni con almeno 30 mm.", anni=lungo))
js(os.path.join(OP, "arpa_sensore_anno.json"), dict(nota="ARPA Lombardia (CC0). Solo anni con almeno il 90% delle ore; giorni >= 40 mm non confermati dai vicini tolti. s = id sensore.", sensori=arpa_sens, righe=arpa))
nc_df = pd.DataFrame(nc_rows).rename(columns={"g": "giorno", "nome": "stazione", "mm": "mm_giorno", "rif": "max_altri_riferimenti_mm", "nrif": "n_riferimenti"})
nc_df.to_csv(os.path.join(OP, "giorni_non_confermati.csv"), index=False)

# =============================================================== CALDO
est = rd("caldo_estate_sensore.csv", dtype={"idsensore": str})
stz = rd("caldo_isola_stazione.csv", dtype={"idsensore": str})
cls = rd("stazioni_classi.csv", dtype={"idsensore": str})
sna = rd("stazioni_nil_alberi.csv", dtype={"idstazione": str})
ora = rd("caldo_isola_ora.csv", dtype={"idsensore": str})
ann = rd("caldo_isola_anno.csv", dtype={"idsensore": str})
tsel = sel[sel.tipologia == "Temperatura"][["idsensore", "idstazione"]]
s17 = stz[stz.finestra == "2017-2025"].merge(cls[["idsensore", "classe"]], on="idsensore").merge(tsel, on="idsensore").merge(
    sna[["idstazione", "lat", "lng", "id_nil", "nil", "alberi_500m", "alberi_ha_500m"]], on="idstazione")
CORTI = {"5897": "Brera", "5909": "Juvara", "5911": "Marche", "5920": "Zavattari", "8162": "Feltre", "2001": "Lambrate", "5903": "Corsico", "4058": "Parco Nord", "14742": "Rho",
         "5917": "Rodano", "2187": "Landriano", "5910": "Lacchiarella", "4066": "Arconate", "17488": "Magenta", "2122": "Sant'Angelo Lodigiano", "12716": "Bereguardo"}
e26 = est[est.anno == 2026].set_index("idsensore")
stazioni = []
for r in s17.itertuples():
    e = e26.loc[r.idsensore] if r.idsensore in e26.index else None
    stazioni.append(dict(id=r.idsensore, nome=CORTI[r.idsensore], ufficiale=r.nomestazione, classe=r.classe, lat=clean(r.lat, 5), lng=clean(r.lng, 5), km=clean(r.dist_duomo_km, 1),
                         nil=(None if pd.isna(r.nil) else r.nil), alberi_500m=(int(r.alberi_500m) if r.classe == "urbana" else None), alberi_ha=(clean(r.alberi_ha_500m, 1) if r.classe == "urbana" else None),
                         notte=clean(r.diff_notte_22_05, 2), pom=clean(r.diff_pomeriggio_12_16, 2), tmin=clean(r.tmin_jja_media, 2), tmax=clean(r.tmax_jja_media, 2),
                         tropicali=clean(r.notti_tropicali_per_estate, 1), estati=int(r.estati),
                         trop26=(int(e.notti_tropicali) if e is not None else None), tmin26=(clean(e.tmin_media, 2) if e is not None else None), tmax26_max=(clean(e.tmax_massima, 1) if e is not None else None)))
order = {"urbana": 0, "cintura": 1, "rurale": 2}
stazioni.sort(key=lambda s: (order[s["classe"]], -(s["notte"] or 0)))
check("Juvara notte", [s for s in stazioni if s["id"] == "5909"][0]["notte"], 2.96, 0.01)
check("Brera trop 2026", [s for s in stazioni if s["id"] == "5897"][0]["trop26"], 80)

# curva per ora
curve = {}
for fin in ["2002-2010", "2011-2016", "2017-2025"]:
    x = ora[(ora.finestra == fin) & (ora.idsensore == "URBANE_MEDIA")].sort_values("ora")
    curve[fin] = [clean(v, 2) for v in x.differenza_vs_rurali]
per_st = {}
for sid in CORTI:
    x = ora[(ora.finestra == "2017-2025") & (ora.idsensore == sid)].sort_values("ora")
    if len(x) == 24:
        per_st[CORTI[sid]] = [clean(v, 2) for v in x.differenza_vs_rurali]
check("curva 22:00", curve["2017-2025"][22], 2.007, 0.01)
check("curva 14:00", curve["2017-2025"][14], -0.358, 0.01)

# notti tropicali per anno (estati complete), rurali = media delle 5 lunghe
core = ["5897", "5909", "5911", "5920", "8162", "2001"]
rur = ["5917", "2187", "5910", "2122", "4066"]
ec_ = est[est.estate_completa]
anni_nt = []
for y in range(2003, 2027):
    row = {"a": y}
    for sid in core:
        v = ec_[(ec_.idsensore == sid) & (ec_.anno == y)]
        row[CORTI[sid]] = int(v.notti_tropicali.iloc[0]) if len(v) else None
    v = ec_[(ec_.idsensore.isin(rur)) & (ec_.anno == y)]
    row["Campagna (media)"] = clean(v.notti_tropicali.mean(), 0) if len(v) >= 2 else None
    row["n_rurali"] = int(len(v))
    anni_nt.append(row)
# differenza di minima per anno (si vedono i salti)
diff_anno = {}
for sid in ["5897", "5909", "5911", "5920", "8162", "2001", "4058", "5903"]:
    x = ann[ann.idsensore == sid]
    diff_anno[CORTI[sid]] = [dict(a=int(r.anno), n=clean(r.tmin_meno_rurali, 1), g=clean(r.tmax_meno_rurali, 1)) for r in x.itertuples()]

# NIL semplificati (solo confini e nome, per la mappa)
nilgeo = json.load(open(os.path.join(R, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf8"))
ana = pd.read_csv(os.path.join(R, "censimenti/pulito/nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
feats = []
for f in nilgeo["features"]:
    i = int(f["properties"]["ID_NIL"])
    g = shape(f["geometry"]).simplify(0.00004, preserve_topology=True)
    gm = mapping(g)
    gm["coordinates"] = json.loads(json.dumps(gm["coordinates"]))
    def rnd(c):
        return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
    gm["coordinates"] = rnd(gm["coordinates"])
    feats.append(dict(type="Feature", properties=dict(i=i, n=nomi.get(i) or str(f["properties"]["NIL"]).title()), geometry=gm))
js(os.path.join(OC, "nil.geojson"), dict(type="FeatureCollection", features=feats))

e17 = est[(est.anno >= 2017) & (est.anno <= 2025) & (est.idsensore.isin(core))]
riep_c = dict(
    note="Tutti i numeri della pagina 'Il quartiere piu' caldo'. Campo origine = file in pioggia-e-caldo/pulito/.",
    scaricato="2026-11-01", finestra="2017-2025 (estati giugno-agosto, 9 estati)",
    curva_notte_max=clean(max(curve["2017-2025"]), 2), curva_ora_max=int(np.argmax(curve["2017-2025"])), curva_pom_min=clean(min(curve["2017-2025"][12:17]), 2),
    rurali_scelti=[CORTI[s] for s in ["5917", "2187", "5910", "4066", "17488", "2122", "12716"]],
    origine=dict(stazioni="pulito/caldo_isola_stazione.csv, caldo_estate_sensore.csv, stazioni_nil_alberi.csv", curva="pulito/caldo_isola_ora.csv", anni="pulito/caldo_estate_sensore.csv, caldo_isola_anno.csv"))
js(os.path.join(OC, "riepilogo.json"), dict(riep=riep_c, stazioni=stazioni, curva=curve, curva_stazioni=per_st, notti_per_anno=anni_nt, differenza_per_anno=diff_anno))
pd.DataFrame(stazioni).to_csv(os.path.join(OC, "stazioni.csv"), index=False)

print("\nAVVISI:", AVVISI if AVVISI else "nessuno")
