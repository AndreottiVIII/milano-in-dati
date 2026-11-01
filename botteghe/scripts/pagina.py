"""Prepara i dati della pagina docs/botteghe/data/ a partire da botteghe/pulito/.
Pubblica solo insegne (mai ragione sociale), niente id/nomi/date OSM (solo un si/no "trovata su OpenStreetMap", derivato da OSM, ODbL).
Le 18 attività la cui posizione è incerta (unione per nome e anno con fonti a più di 1 km) non hanno scheda né punto: sono contate.
Uso: python -I -X utf8 pagina.py <botteghe abs> <docs/botteghe abs>   (rilanciabile)"""
import sys, os, json, csv, collections, math
import pandas as pd
B, OUT = sys.argv[1:3]
D = OUT + "/data"
os.makedirs(D, exist_ok=True)
b = pd.read_csv(B + "/pulito/botteghe.csv", dtype=str, keep_default_na=False)
rec = pd.read_csv(B + "/pulito/entita_record.csv", dtype=str, keep_default_na=False)
ed = pd.read_csv(B + "/pulito/edizioni_conteggi.csv", dtype=str)
b["anno"] = pd.to_numeric(b.anno_fondazione, errors="coerce")
b["disc"] = pd.to_numeric(b.discordanza_albo2024_m, errors="coerce")
b["incerta"] = b.disc > 1000
mun = rec[rec.municipio != ""].groupby("ent_id").municipio.agg(lambda s: s.iloc[-1])
b["mun"] = b.id.map(mun).fillna("")
STAT = {"si": "A", "probabile": "P", "cessata": "C", "contraddittoria": "D", "non_verificabile": "D", "cessata_probabile": "D"}
b["st"] = b.ancora_attiva.map(STAT)
TIPO = {"farmacia": "Farmacie", "ristorante": "Ristoranti, trattorie, osterie", "bar_caffe": "Bar e caffè", "pasticceria_gelateria": "Pasticcerie e gelaterie", "panificio": "Panifici",
        "alimentari": "Alimentari (salumerie, macellerie...)", "gioielleria_orologeria": "Gioiellerie e orologerie", "ottica_foto": "Ottica e foto", "cura_persona": "Parrucchieri e profumerie",
        "tabaccheria": "Tabaccherie", "libreria_cartoleria": "Librerie, cartolerie, edicole", "sartoria_riparazioni": "Sartorie e riparazioni", "calzature_pelletteria": "Calzature e pelletterie",
        "abbigliamento": "Abbigliamento", "sport_tempo_libero": "Sport e giocattoli", "auto_moto": "Auto e moto", "casa_ferramenta": "Casa e ferramenta", "laboratori_produzione": "Laboratori",
        "stampa_incisioni": "Stampa e incisioni", "servizi_spettacolo": "Servizi e spettacolo", "fiori_piante": "Fiori e piante", "salute_benessere": "Salute e benessere", "altro": "Altro"}
R = {}
R["tot"] = len(b)
R["in_albo17"] = int((b.in_albo_2017 == "sì").sum())
R["in_albo24"] = int((b.in_albo_2024 == "sì").sum())
R["in_reg26"] = int((b.in_regione_2026 == "sì").sum())
R["in_entrambi"] = int(((b.in_albo_2024 == "sì") & (b.in_regione_2026 == "sì")).sum())
R["solo_albo"] = int(((b.in_albo_2024 == "sì") & (b.in_regione_2026 != "sì")).sum())
R["solo_reg"] = int(((b.in_albo_2024 != "sì") & (b.in_regione_2026 == "sì")).sum())
R["in_nessuna_lista_recente"] = int(((b.in_albo_2024 != "sì") & (b.in_regione_2026 != "sì")).sum())
R["stato"] = b.st.value_counts().to_dict()
R["stato_dettaglio"] = b.ancora_attiva.value_counts().to_dict()
R["incerte_escluse"] = int(b.incerta.sum())
R["righe_edizioni"] = int(ed.righe.astype(int).sum())
# --- Albo
a24 = b[b.in_albo_2024 == "sì"].copy()
a24["c"] = a24.stato_albo_2024 == "cessata"
R["albo24_cessata"] = int(a24.c.sum()); R["albo24_attiva"] = int((~a24.c).sum()); R["albo24_cessata_pct"] = round(a24.c.mean() * 100, 1)
a17 = b[b.in_albo_2017 == "sì"]
R["albo17_n"] = len(a17)
R["albo17_cessata_2024"] = int((a17.stato_albo_2024 == "cessata").sum())
R["albo17_assenti_2024"] = int((a17.in_albo_2024 != "sì").sum())
R["albo17_attiva_2024"] = int((a17.stato_albo_2024 == "attiva").sum())
nuove = a24[a24.in_albo_2017 != "sì"]
R["albo24_nuove"] = len(nuove); R["albo24_nuove_cessate"] = int(nuove.c.sum())
# --- per tipo
pt = a24.groupby("settore").agg(n=("id", "size"), cessate=("c", "sum")).reset_index()
pt["pct"] = (pt.cessate / pt.n * 100).round(1)
pt["tipo"] = pt.settore.map(TIPO)
pt = pt.sort_values("n", ascending=False)
pt[["settore", "tipo", "n", "cessate", "pct"]].to_csv(D + "/chi_chiude_per_tipo.csv", index=False)
R["per_tipo"] = pt[["settore", "tipo", "n", "cessate", "pct"]].to_dict("records")
try:
    from scipy.stats import fisher_exact
    def pv(mask):
        x, y = a24[mask], a24[~mask]
        return float(fisher_exact([[x.c.sum(), len(x) - x.c.sum()], [y.c.sum(), len(y) - y.c.sum()]])[1])
    R["p_bar"] = round(pv(a24.settore == "bar_caffe"), 4)
    R["p_pan_past"] = round(pv(a24.settore.isin(["panificio", "pasticceria_gelateria"])), 4)
    R["p_45_59"] = round(pv((a24.anno >= 1945) & (a24.anno <= 1959)), 4)
    R["p_farmacie"] = round(pv(a24.settore == "farmacia"), 4)
    R["p_centro"] = round(pv(a24.mun == "1"), 4)
except Exception as e:
    print("scipy non disponibile:", e)
pp = a24[a24.settore.isin(["panificio", "pasticceria_gelateria"])]
R["pan_past_n"] = len(pp); R["pan_past_cess"] = int(pp.c.sum())
bar = a24[a24.settore == "bar_caffe"]; R["bar_n"] = len(bar); R["bar_cess"] = int(bar.c.sum())
farm = a24[a24.settore == "farmacia"]; R["farm_n"] = len(farm); R["farm_cess"] = int(farm.c.sum())
# --- per epoca
a24["epoca"] = pd.cut(a24.anno, [0, 1919, 1944, 1959, 1969, 2100], labels=["fino al 1919", "1920-44", "1945-59", "1960-69", "dal 1970"])
ep = a24.groupby("epoca", observed=True).agg(n=("id", "size"), cessate=("c", "sum")).reset_index()
ep["pct"] = (ep.cessate / ep.n * 100).round(1); ep["epoca"] = ep.epoca.astype(str)
R["per_epoca"] = ep.to_dict("records")
ep.to_csv(D + "/chi_chiude_per_epoca.csv", index=False)
cm = a24.groupby(a24.mun == "1").agg(n=("id", "size"), cessate=("c", "sum"))
R["centro"] = {"n": int(cm.loc[True, "n"]), "cessate": int(cm.loc[True, "cessate"])}
R["resto"] = {"n": int(cm.loc[False, "n"]), "cessate": int(cm.loc[False, "cessate"])}
# --- anni
dec = b.dropna(subset=["anno"]).copy()
dec["dec"] = (dec.anno // 10 * 10).astype(int)
dec.loc[dec.anno < 1900, "dec"] = 1800
hist = dec.groupby("dec").size().reset_index(name="n")
R["decenni"] = hist.to_dict("records")
R["anno_mediano"] = float(b.anno.median())
R["prima_1900"] = int((b.anno < 1900).sum())
R["dal_1945_al_1975"] = int(((b.anno >= 1945) & (b.anno <= 1975)).sum())
R["cento_anni"] = int((2026 - b.anno >= 100).sum())
aperte = b[b.st.isin(["A", "P"])].sort_values("anno").head(12)
R["piu_antiche_aperte"] = [{"n": r.nome_insegna, "a": int(r.anno), "ind": r.indirizzo, "nil": r.nil, "st": r.st, "tipo": TIPO[r.settore]} for r in aperte.itertuples() if not r.incerta]
chiuse = b[b.st == "C"].sort_values("anno").head(5)
R["piu_antiche_cessate"] = [{"n": r.nome_insegna, "a": int(r.anno), "tipo": TIPO[r.settore]} for r in chiuse.itertuples() if not r.incerta]
# --- NIL
pop = pd.read_csv(B + "/pulito/per_nil.csv")
pop["per10000"] = pop.per_10000_abitanti
top = pop.sort_values("n_attivita", ascending=False).head(10)
R["nil_top"] = [{"nil": r.nil, "n": int(r.n_attivita), "ab": int(r.abitanti_2024), "p10": round(float(r.per_10000_abitanti), 1)} for r in top.itertuples()]
R["nil_duomo"] = int(pop[pop.nil == "DUOMO"].n_attivita.iloc[0])
R["nil_zero"] = int((pop.n_attivita == 0).sum()); R["nil_tot"] = len(pop)
R["per_10000_citta"] = round(float(pop.n_attivita.sum() / pop.abitanti_2024.sum() * 1e4), 1)
R["mun1"] = int((b.mun == "1").sum())
R["top5_quota"] = round(float(pop.sort_values("n_attivita", ascending=False).head(5).n_attivita.sum() / pop.n_attivita.sum() * 100), 1)
# --- edizioni Regione
e = ed[ed.elenco == "B_regione"][["data_edizione", "righe"]].copy(); e["righe"] = e.righe.astype(int)
R["edizioni_regione"] = e.to_dict("records")
e.to_csv(D + "/elenco_regione_per_edizione.csv", index=False)
R["edizioni_albo"] = ed[ed.elenco == "A_albo"][["data_edizione", "righe"]].assign(righe=lambda d: d.righe.astype(int)).to_dict("records")
u = pd.read_csv(B + "/pulito/regione_uscite_entrate.csv"); u.to_csv(D + "/elenco_regione_uscite_entrate.csv", index=False)
rj = json.load(open(B + "/pulito/riepilogo.json", encoding="utf-8"))
R["regione_uscite_2026"] = rj["regione_uscite_dal_2019_non_piu_nel_2026"]
R["regione_uscite_2019"] = rj["regione_uscite_luglio_agosto_2019"]
R["regione_uscite_stato_albo24"] = rj["regione_uscite_stato_albo24"]
R["regione26_cessata_albo"] = rj["regione26_con_stato_cessata_albo"]
R["osm_attive_pct"] = rj["osm_trova_%_delle_attive_albo24"]; R["osm_cessate_pct"] = rj["osm_trova_%_delle_cessate_albo24"]
R["coord_ok50"] = int(b.coord_verifica.str.startswith("ok").sum())
R["albo2024_indirizzo_discordante"] = int((b.indirizzo_discordante != "").sum())
rl = json.load(open(B + "/pulito/regione_lombardia_riepilogo.json", encoding="utf-8"))
R["lombardia"] = {"righe": rl["lombardia_righe"], "comuni": rl["lombardia_comuni"], "milano": rl["milano_citta"], "quota": rl["milano_quota_%"], "artigiane_mi": rl["tipo_milano"].get("Bottega artigiana storica"), "artigiane_lomb": rl["tipo_lombardia"].get("Bottega artigiana storica")}
# --- campione di controllo (giudizio dato leggendo le prove di ciascuna scheda; vedi NOTE)
GIUD = {}
for i in "E0012 E0073 E0740 E0174 E0538 E0335 E0186 E0310 E0482 E0212 E0450 E0504 E0011 E0207 E0574 E0573 E0009".split(): GIUD[i] = ("regge", "prova indipendente credibile (nome e luogo coincidono)")
GIUD["E0609"] = ("dubbio", "punto OSM con lo stesso nome ma ultima modifica 2022: potrebbe essere vecchio")
for i in "E0653 E0297 E0309 E0622 E0217 E0338 E0748".split(): GIUD[i] = ("regge", "cessata per l'Albo, nessuna prova contraria in OSM o nel registro")
GIUD["E0749"] = ("ambigua", "cessata per l'Albo ma il registro 2026 ha la stessa insegna sul posto")
for i in "E0030 E0446 E0001 E0436 E0123 E0662 E0267 E0655 E0210 E0271 E0372 E0513 E0461 E0363".split(): GIUD[i] = ("non confermabile", "solo negli elenchi, nessuna prova indipendente")
s40 = b.sample(40, random_state=20261101)
camp = []
for r in s40.itertuples():
    g = GIUD[r.id]
    camp.append(dict(id=r.id, insegna=r.nome_insegna, indirizzo=r.indirizzo, stato=r.ancora_attiva, giudizio=g[0], motivo=g[1], coordinate=r.coord_verifica))
pd.DataFrame(camp).to_csv(D + "/campione_controllo_40.csv", index=False)
cg = collections.Counter(c["giudizio"] for c in camp)
R["campione"] = {"n": 40, "regge": cg["regge"], "dubbio": cg["dubbio"], "ambigua": cg["ambigua"], "non_confermabile": cg["non confermabile"],
                 "decise": sum(1 for c in camp if c["stato"] in ("si", "cessata")), "coord_ok": sum(1 for c in camp if c["coordinate"].startswith("ok")),
                 "coord_non_trovato": sum(1 for c in camp if c["coordinate"].startswith("civico non")), "coord_scarto": sum(1 for c in camp if c["coordinate"].startswith("scarto"))}
assert all(c["id"] in GIUD for c in camp)
# --- mappa: file compatto (solo insegna, indirizzo, anno, tipo, stato, prove sotto forma di codici)
pts = []
for r in b.itertuples():
    if r.incerta or not r.lon: continue
    pts.append({"i": r.id, "n": r.nome_insegna, "ind": r.indirizzo, "a": int(r.anno), "t": r.settore, "s": r.st, "x": round(float(r.lon), 5), "y": round(float(r.lat), 5), "q": r.nil,
                "al": ("c" if r.stato_albo_2024 == "cessata" else "a") if r.in_albo_2024 == "sì" else ("v" if r.in_albo_2017 == "sì" else ""),
                "r": 1 if r.in_regione_2026 == "sì" else 0, "o": 1 if r.osm_trovata == "sì" else 0, "oc": 1 if r.osm_chiusa == "sì" else 0, "g": {"forte": "f", "debole": "d"}.get(r.registro_2026, "n"),
                "k": 1 if r.coord_verifica.startswith("ok") else 0})
json.dump({"tipi": TIPO, "punti": pts}, open(D + "/botteghe.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# --- csv scaricabile
def prove(r):
    p = []
    if r.in_albo_2024 == "sì": p.append("Albo comunale 12/2024: " + r.stato_albo_2024)
    elif r.in_albo_2017 == "sì": p.append("Albo comunale 2017: sì; assente dall'Albo 2024")
    p.append("elenco Regione 19/10/2026: " + ("presente" if r.in_regione_2026 == "sì" else "assente"))
    p.append("registro commerciale Comune 2026: " + {"forte": "pratica con insegna simile sul posto", "debole": "pratica dello stesso settore sul posto", "no": "nessuna pratica compatibile"}.get(r.registro_2026, ""))
    p.append("OpenStreetMap: " + ("punto segnato chiuso" if r.osm_chiusa == "sì" else ("punto con nome simile" if r.osm_trovata == "sì" else "nessun punto con nome simile")))
    return "; ".join(p)
STATO_TXT = {"A": "attiva (con prova indipendente)", "P": "probabile (solo negli elenchi)", "C": "cessata secondo l'Albo del Comune (data non indicata)", "D": "dubbia"}
rows = []
for r in b.itertuples():
    inc = bool(r.incerta)
    rows.append(dict(id=r.id, insegna=r.nome_insegna, tipo=TIPO[r.settore], categoria_regione=r.categoria, anno_fondazione_dichiarato=int(r.anno), anno_riconoscimento_regione=r.anno_riconoscimento_regione,
                     riconoscimento_albo=r.albo_riconoscimento, indirizzo="" if inc else r.indirizzo, lon="" if inc else r.lon, lat="" if inc else r.lat, nil="" if inc else r.nil,
                     in_albo_2017=r.in_albo_2017, in_albo_2024=r.in_albo_2024, stato_albo_2024=r.stato_albo_2024, in_regione_2026=r.in_regione_2026,
                     stato=STATO_TXT[r.st], trovata_su_openstreetmap_ODbL=r.osm_trovata, registro_2026=r.registro_2026, prove=prove(r),
                     posizione_incerta_non_pubblicata="sì" if inc else ""))
pd.DataFrame(rows).to_csv(D + "/botteghe.csv", index=False, encoding="utf-8")
json.dump(R, open(D + "/riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ["tot", "stato", "incerte_escluse", "campione", "centro", "resto", "p_bar", "p_pan_past", "p_45_59", "nil_duomo", "mun1"]}, ensure_ascii=False))
print(len(pts), "punti")
