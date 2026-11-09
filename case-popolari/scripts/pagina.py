"""Scrive i file dati della pagina "Case popolari vuote" (docs/case-popolari/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <case_popolari_dir> <milano_in_dati_dir> <docs_dir>

Legge solo le tabelle pulite della fase 1 (case-popolari/pulito/*.csv), i poligoni dei NIL di citta-15-minuti
(raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson) e censimenti/pulito/{nil_2021_anagrafica,indicatori_NIL}.csv.
Scrive in <docs_dir>/case-popolari/data/: riepilogo.json, nil.geojson, nil.csv e i csv delle serie.
Per i NIL: solo la QUOTA del canone fatturato ALER (2016) e il numero di edifici per quartiere: nessun indirizzo di edificio,
nessun inquilino o occupante, nessun alloggio singolo. I PDF non sono ripubblicati: sono citati (titolo, link, pagina).
Ogni numero importante e' confrontato con il valore atteso (controlli stampati; se uno e' diverso lo script si ferma)."""
import sys, os, json
import pandas as pd
from shapely.geometry import shape, mapping

A, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(A, "pulito")
OUT = os.path.join(DOCS, "case-popolari", "data")
os.makedirs(OUT, exist_ok=True)
AVV = []


def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")
    if not ok:
        AVV.append(nome)


def rd(f, **k):
    return pd.read_csv(os.path.join(PU, f), **k)


def N(x):
    return None if pd.isna(x) else (int(x) if float(x) == int(x) else float(x))


# ------------------------------------------------------------------ fonti (titolo, link, pagine): i PDF non vengono ripubblicati
RB = "https://www.regione.lombardia.it/content/dam/rl/canali-tematici-servizi/08-politiche-sociali/01-abitare-in-lombardia/red-osservatorio-condizione-abitativa/accordion/allegati/"
FONTI = {
    "R25": {"titolo": "Regione Lombardia, Rapporto annuale al Consiglio regionale - anno 2025 (DGR XII/6666 del 3/8/2026)", "url": RB + "DGR%206666%20del%2003%20agosto%202026%20Rapporto%20al%20Consiglio%202025.pdf", "pagine": "p.8 e 10 (patrimonio SAP), p.12 e 17 (avvisi 2025), p.43 (occupazioni abusive 2021-2025)"},
    "R24": {"titolo": "Regione Lombardia, Rapporto annuale al Consiglio regionale - anno 2024", "url": RB + "All_1%20Rapporto-annuale-consiglio-regionale-2024.pdf", "pagine": "p.7 (patrimonio), p.11 (avvisi 2024)"},
    "RZ": {"titolo": "Regione Lombardia, Rapporti al Consiglio regionale 2014-2022 (archivio zip, un PDF per anno)", "url": RB + "Rapporti%20al%20Consiglio%20regionale%202014_2022.zip", "pagine": "tabella 'Milano Città': Rapporto 2017 p.12, 2017_2 p.10, 2018 p.10, 2019 p.38, 2020 p.25, 2021 p.20, 2022 p.10; avvisi: Rapporto 2020 p.33 e 36, 2022 p.15; domande ERP: Rapporti 2017 p.19, 2017_2 p.16, 2018 p.17, 2019 p.45, 2020 p.42"},
    "AP": {"titolo": "ALER Milano, Amministrazione trasparente, canoni incassati: Prospetto n.5 'Entrate da canoni di locazione per titolo giuridico' (uno per anno, 2018-2025)", "url": "https://aler.mi.it/amministrazione-trasparente/canoni-incassati/", "pagine": "p.1 (alloggi con/senza contratto, sfitti e motivi), p.2 (occupazioni senza titolo)"},
    "AB": {"titolo": "ALER Milano, Bilanci consuntivi - relazione sulla gestione 2021 e 2023", "url": "https://aler.mi.it/amministrazione-trasparente/bilancio-preventivo-e-consuntivo/", "pagine": "consuntivo 2021 p.75 e consuntivo 2023 p.72 (andamento delle occupazioni abusive)"},
    "AE": {"titolo": "ALER Milano, Amministrazione trasparente, canoni incassati: elenco degli edifici con il canone fatturato (2013, 2015, 2016)", "url": "https://aler.mi.it/amministrazione-trasparente/canoni-incassati/", "pagine": "elenco per indirizzo (qui usato solo sommato per quartiere)"},
    "CP": {"titolo": "Comune di Milano, Piano annuale dell'offerta dei servizi abitativi pubblici e sociali 2026 (slide, delibera di Giunta 30/2026)", "url": "https://www2.comune.milano.it/documents/20126/464282611/04022604+Delib+30-26+Slide+Piano+annuale+dell'offerta+dei+servizi+abitativi.pdf/e14c34fd-7a3c-7d9e-eeee-8647bc7a2f52?t=1770911344724", "pagine": "p.3 (consistenza), p.3-7 (alloggi assegnabili per Municipio)"},
    "CS": {"titolo": "Comune di Milano, 'Una nuova strategia per la casa' (20/3/2023)", "url": "https://web.archive.org/web/20230320170612/https://www.comune.milano.it/documents/20126/409775564/20230320+Una+nuova+strategia+per+la+casa.pdf/cf53af81-c775-7b9e-0480-d8d0ba0be74e", "pagine": "p.34 (patrimonio, 273 complessi), p.38 (tabella 'analisi unità per stato di utilizzo'), p.57 (27.075 unità comunali). Copia letta: Wayback Machine, 20/3/2023, perché il sito del Comune non risponde"},
    "CE": {"titolo": "Comune di Milano / ISTAT, abitazioni per NIL e per Comune (censimenti 2011, registri 2021 e 2023)", "url": "https://dati.comune.milano.it/", "pagine": "indicatori_comune.csv e indicatori_NIL.csv della pagina Censimenti, campo abit_tot"},
}

# ------------------------------------------------------------------ stock
pat = rd("patrimonio_sap_milano_serie.csv")
ult = pat.iloc[-1]
check("SAP Comune", int(ult.unita_proprieta_Comune_di_Milano), 26010)
check("SAP ALER", int(ult.unita_proprieta_ALER_Milano), 33044)
check("SAP totale", int(ult.totale_Milano_citta), 59054)
ind = rd_ = pd.read_csv(os.path.join(P, "censimenti", "pulito", "indicatori_comune.csv")).set_index("anno")
ab23, ab21, abo23, ab11 = (int(ind.loc[a, c]) for a, c in ((2023, "abit_tot"), (2021, "abit_tot"), (2023, "abit_occ"), (2011, "abit_tot")))
quota = {"2023": round(100 * ult.totale_Milano_citta / ab23, 1), "2021": round(100 * ult.totale_Milano_citta / ab21, 1),
         "occupate_2023": round(100 * ult.totale_Milano_citta / abo23, 1), "2011": round(100 * ult.totale_Milano_citta / ab11, 1)}
check("quota SAP su abitazioni 2023 (%)", quota["2023"], 7.1)
serie_pat = [{"rapporto": r.rapporto, "data": r.data_riferimento, "comune": int(r.unita_proprieta_Comune_di_Milano), "aler": int(r.unita_proprieta_ALER_Milano),
              "tot": int(r.totale_Milano_citta), "pagina": int(r.pagina), "nota": (r.nota if isinstance(r.nota, str) else "")} for r in pat.itertuples()]
cons = rd("piano_annuale_2026_consistenza.csv").set_index("categoria")
STOCK = {"data": str(ult.data_riferimento), "comune": int(ult.unita_proprieta_Comune_di_Milano), "aler": int(ult.unita_proprieta_ALER_Milano), "tot": int(ult.totale_Milano_citta),
         "abitazioni": {"2023": ab23, "2021": ab21, "occupate_2023": abo23, "2011": ab11}, "quota_pct": quota, "serie": serie_pat,
         "piano2026": {"sap_comune": int(cons.loc["SAP", "alloggi_Comune_di_Milano"]), "sap_aler": int(cons.loc["SAP", "alloggi_ALER_Milano"]),
                       "sas_comune": int(cons.loc["SAS", "alloggi_Comune_di_Milano"]), "sas_aler": int(cons.loc["SAS", "alloggi_ALER_Milano"]),
                       "altri_usi_comune": int(cons.loc["ALTRI USI RESIDENZIALI", "alloggi_Comune_di_Milano"]), "altri_usi_aler": int(cons.loc["ALTRI USI RESIDENZIALI", "alloggi_ALER_Milano"])},
         "altri_usi_comune_2018": 5974, "altri_usi_comune_2026": 1261, "complessi_comunali_2023": 273, "complessi_cielo_terra_2023": 200,
         "unita_cielo_terra_2023": 22876, "edifici_cielo_terra_2023": 682,
         "casi": [{"nome": "Lorenteggio", "testo": "circa 2.600 alloggi ALER nell'area del programma di rigenerazione", "fonte": "Rapporto regionale 2025, p.24"},
                  {"nome": "Gratosoglio", "testo": "12 fabbricati e 782 alloggi in efficientamento energetico; 120 alloggi sfitti da recuperare", "fonte": "Rapporto regionale 2025, p.47"},
                  {"nome": "Via Bolla 26/42", "testo": "circa 250 alloggi SAP in due complessi", "fonte": "Rapporto regionale 2025, p.48"},
                  {"nome": "San Siro", "testo": "3 stabili ALER (viale Mar Jonio 9, piazza Selinunte 6, via Morgantini 5) con 195 alloggi SAP in riqualificazione", "fonte": "Rapporto regionale 2025, p.50"}]}

# ------------------------------------------------------------------ fotografia di marzo 2023
su = rd("stato_utilizzo_marzo_2023.csv")
sap = su[(su.servizio == "SAP") & su.ente.isin(["Comune di Milano (MM)", "Aler Milano"])].set_index("ente")
snap = []
for ente, tot in (("Comune di Milano (MM)", 26489), ("Aler Milano", 32017)):
    r = sap.loc[ente]
    ass, lib, sfi = int(r.assegnati), int(r.liberi), int(r.sfitti_per_carenze_manutentive)
    snap.append({"ente": "Comune di Milano (gestito da MM)" if ente.startswith("Comune") else "ALER Milano", "totale": tot, "assegnati": ass, "liberi": lib, "sfitti_carenze": sfi,
                 "non_classificati": tot - ass - lib - sfi, "vuoti": lib + sfi})
check("Comune: assegnati+liberi+sfitti = 26.489", snap[0]["assegnati"] + snap[0]["vuoti"], 26489)
check("ALER: non classificati nella tabella", snap[1]["non_classificati"], 4016)
tv = sum(s["vuoti"] for s in snap)
tt = sum(s["totale"] for s in snap)
check("vuote totali marzo 2023", tv, 8420)
SNAP = {"data": "marzo 2023", "righe": snap, "vuoti": tv, "totale": tt, "vuoti_pct": round(100 * tv / tt, 1),
        "comune_pct": round(100 * snap[0]["vuoti"] / snap[0]["totale"], 1), "aler_pct": round(100 * snap[1]["vuoti"] / snap[1]["totale"], 1),
        "fonte": "CS", "tot_dichiarato_sap": 58506, "comune_27075": {"unita": 27075, "assegnate": 22113, "sfitte_e_da_ristrutturare": 4962}}
check("vuote su SAP (%)", SNAP["vuoti_pct"], 14.4)

# ------------------------------------------------------------------ ALER 2018-2025
ar = rd("aler_vuoti_serie_armonizzata.csv")
check("ALER sfitti 2021", int(ar[ar.anno == 2021].sfitti_come_scritti_da_ALER.iloc[0]), 8350)
check("ALER sfitti 2025", int(ar[ar.anno == 2025].sfitti_come_scritti_da_ALER.iloc[0]), 5175)
check("ALER vuoti armonizzati 2025", int(ar[ar.anno == 2025].vuoti_totali_armonizzati.iloc[0]), 7735)
check("scarto massimo della somma", int(ar.scarto_su_totale.abs().max()), 0)
aler = [{"anno": int(r.anno), "totale": int(r.totale_ALER_canone_sociale), "sfitti": int(r.sfitti_come_scritti_da_ALER), "vuoti": int(r.vuoti_totali_armonizzati),
         "ristrutturazione": int(r.in_ristrutturazione), "riassegnazione": int(r.in_riassegnazione), "demolizione": int(r.extra_fuori_da_sfitti_demolizione),
         "vendita_fuori": int(r.extra_fuori_da_sfitti_vendita), "valorizzazione_fuori": int(r.extra_fuori_da_sfitti_valorizzazione),
         "senza_titolo": int(r.occupati_senza_titolo), "con_contratto": int(r.con_contratto), "vuoti_pct": float(r["vuoti_%_del_totale"])} for _, r in ar.iterrows()]
# vendita e valorizzazione dentro "sfitti" fino al 2021: dal Prospetto (aler_sfitti_serie.csv)
sr = rd("aler_sfitti_serie.csv").pivot_table(index="anno", columns="voce", values="n_alloggi", aggfunc="first")
for a in aler:
    y = a["anno"]
    a["vendita"] = int(sr.loc[y].get("sfitti: destinati a piani di vendita", 0) or 0)
    a["valorizzazione"] = int(sr.loc[y].get("sfitti: destinati a piani di valorizzazione", 0) or 0) if y >= 2021 else 0
for a in aler:
    check(f"{a['anno']}: motivi sommano ai vuoti", a["ristrutturazione"] + a["riassegnazione"] + a["demolizione"] + a["vendita"] + a["valorizzazione"], a["vuoti"])
a21, a25 = [x for x in aler if x["anno"] == 2021][0], [x for x in aler if x["anno"] == 2025][0]
ALER = {"serie": aler, "var_sfitti_pct": round(100 * (a25["sfitti"] / a21["sfitti"] - 1), 1), "var_vuoti_pct": round(100 * (a25["vuoti"] / a21["vuoti"] - 1), 1),
        "fonte": "AP", "perimetro": "tutto il territorio ALER Milano: 53.143 alloggi a canone sociale nel 2025 (la città ne ha 33.044)"}
check("var. sfitti 2021-2025 (%)", ALER["var_sfitti_pct"], -38.0)
check("var. vuoti 2021-2025 (%)", ALER["var_vuoti_pct"], -7.4)

# ------------------------------------------------------------------ domande / assegnati
av = rd("avvisi_milano.csv")
righe = []
for y, g in av.groupby("anno_avvisi"):
    righe.append({"anno": int(y), "avvisi": int(len(g)), "alloggi": int(g.alloggi_pubblicati_in_avviso.sum()), "domande": int(g.domande.sum()), "assegnati": int(g.alloggi_assegnati.sum()),
                  "pagine": sorted(set(int(p) for p in g.pagina)), "file": sorted(set(str(f).split("/")[-1] for f in g.file))})
for r in righe:
    r["dom_per_alloggio"] = round(r["domande"] / r["alloggi"], 1)
    r["assegnati_pct"] = round(100 * r["assegnati"] / r["alloggi"], 1)
check("2025: alloggi in avviso", [r for r in righe if r["anno"] == 2025][0]["alloggi"], 723)
check("2025: domande", [r for r in righe if r["anno"] == 2025][0]["domande"], 17754)
check("2022: assegnati", [r for r in righe if r["anno"] == 2022][0]["assegnati"], 1297)
gr = rd("domande_assegnazioni_erp_milano_2016_2020.csv")
grad = [{"anno": int(r.anno), "domande": int(r.domande_in_graduatoria), "assegnazioni": int(r.assegnazioni_totale), "nota": (r.nota if isinstance(r.nota, str) else "")} for r in gr.itertuples()]
DOM = {"anni": righe, "mancanti": [2021, 2023], "graduatoria_2016_2020": grad,
       "regione_2025": {"avvisi": 92, "alloggi": 3090, "domande": 46060, "nuclei_stima": 43700, "assegnati_2025": 3076, "assegnati_comuni": 935, "assegnati_aler": 2141, "quota_milano_domande_pct": 38.5},
       "fonte": "RZ, R24, R25"}

# ------------------------------------------------------------------ piano 2026 per Municipio
pm = rd("piano_annuale_2026_per_municipio.csv")
VOCI = {"b": "in carenza manutentiva, assegnabili com'è", "c": "dopo ristrutturazione già programmata", "d": "nuova costruzione", "e": "liberi o che si liberano (turn-over)", "g": "totale"}
mun = []
for m in range(1, 10):
    row = {"municipio": m}
    for k in VOCI:
        s = pm[(pm.voce.str.startswith(k + ")")) & (pm.municipio == f"Municipio {m}")].iloc[0]
        row[k + "_c"], row[k + "_a"] = int(s.alloggi_Comune_MM), int(s.alloggi_ALER)
    mun.append(row)
tot_c = sum(r["g_c"] for r in mun)
tot_a = sum(r["g_a"] for r in mun)
check("assegnabili 2026 Comune", tot_c, 897)
check("assegnabili 2026 ALER", tot_a, 1150)
for r in mun:
    check(f"M{r['municipio']}: b+c+d+e = g", sum(r[k + s] for k in "bcde" for s in "_c _a".split()), r["g_c"] + r["g_a"])
PIANO = {"municipi": mun, "voci": VOCI, "tot_comune": tot_c, "tot_aler": tot_a, "tot": tot_c + tot_a, "sat_comune": 224, "sat_aler": 50, "fonte": "CP",
         "totali_voce": {k: [sum(r[k + "_c"] for r in mun), sum(r[k + "_a"] for r in mun)] for k in VOCI}}
check("voce c (ristrutturazione) Comune+ALER", sum(PIANO["totali_voce"]["c"]), 1268)

# ------------------------------------------------------------------ occupazioni senza titolo (non sono alloggi vuoti)
oc = rd("occupazioni_abusive_serie.csv")
def ser(nome):
    return [[int(r.anno), int(r.occupazioni_consolidate)] for r in oc[oc.ente == nome].itertuples()]
OCC = {"aler_bilanci": ser("ALER Milano (bilanci ALER)"), "aler_regione": ser("ALER Milano (Rapporto regionale 2025)"), "comune": ser("Comune di Milano / MM (Rapporto regionale 2025)"),
       "aler_senza_contratto": [[a["anno"], a["senza_titolo"]] for a in aler], "fonte": "AB, R25, AP"}
check("ALER 2025 consolidate", dict(OCC["aler_regione"])[2025], 2324)
check("Comune/MM 2025", dict(OCC["comune"])[2025], 459)

# ------------------------------------------------------------------ NIL (solo quota ALER 2016 sul totale cittadino; nessun indirizzo)
nn = rd("nil_aler_stabili_abitazioni.csv")
anag = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
ab_nil = pd.read_csv(os.path.join(P, "censimenti", "pulito", "indicatori_NIL.csv"))
ab_nil = ab_nil[ab_nil.anno == 2023].set_index("nil")
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
nn = nn.set_index("ID_NIL")
tot16 = float(nn.canone_fatturato_2016.sum())
tot13 = float(nn.canone_fatturato_2013.sum())
feats, rows = [], []
for _, a in anag.sort_values("nil_nome").iterrows():
    i = int(a.nil)
    has = i in nn.index
    r = nn.loc[i] if has else None
    q16 = round(100 * float(r.canone_fatturato_2016) / tot16, 2) if has else 0.0
    q13 = round(100 * float(r.canone_fatturato_2013) / tot13, 2) if has else 0.0
    abit = int(ab_nil.loc[i, "abit_tot"]) if i in ab_nil.index else None
    p = {"i": i, "n": a.nil_nome, "m": int(a.municipio_prevalente), "q16": q16, "q13": q13, "ed16": int(r.fabbricati_2016) if has else 0, "ed13": int(r.fabbricati_2013) if has else 0,
         "m16": round(float(r.canone_fatturato_2016) / 1e6, 2) if has else 0.0, "abit": abit,
         "pa": round(float(r.canone_fatturato_2016) / abit) if has and abit else 0}
    g = geom[i].simplify(0.00003, preserve_topology=True)
    gj = mapping(g)

    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    rows.append({"id_nil": i, "nil": a.nil_nome, "municipio_prevalente": p["m"], "quota_canone_ALER_2013_pct": q13, "quota_canone_ALER_2016_pct": q16, "edifici_ALER_2013": p["ed13"], "edifici_ALER_2016": p["ed16"],
                 "canone_fatturato_ALER_2016_milioni_euro": p["m16"], "abitazioni_2023": abit, "canone_ALER_2016_per_abitazione_euro": p["pa"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";")
check("somma quote 2016", round(sum(f["properties"]["q16"] for f in feats), 0), 100, 1)
top = sorted(feats, key=lambda f: -f["properties"]["q16"])[:5]
check("quota dei primi 5 NIL (%)", round(sum(f["properties"]["q16"] for f in top), 1), 33.9, 0.1)
NILS = {"anno": 2016, "n_nil_con_edifici": int(sum(1 for f in feats if f["properties"]["ed16"] > 0)), "edifici_totali_2016": int(sum(f["properties"]["ed16"] for f in feats)),
        "top5": [[f["properties"]["n"], f["properties"]["q16"]] for f in top], "quota_agganciata_pct": 96.5, "canone_totale_milioni_2016": round(tot16 / 1e6, 1), "fonte": "AE"}
check("NIL con almeno un edificio ALER", NILS["n_nil_con_edifici"], 50)

# ------------------------------------------------------------------ altre fonti (secondarie): riquadro separato
alt = rd("numeri_fonti_secondarie.csv")
ALTRE = [{"cosa": r.descrizione, "valore": r.valore, "data": r.data_riferimento, "fonte": r.fonte, "tipo": r.tipo_fonte, "avvertenza": r.avvertenza} for r in alt.itertuples()]

R = {"scaricato": "2026-11-01", "fonti": FONTI, "stock": STOCK, "snapshot": SNAP, "aler": ALER, "domande": DOM, "piano": PIANO, "occupazioni": OCC, "nil": NILS, "altre_fonti": ALTRE}
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------------ csv scaricabili (serie aggregate; nessun dato personale)
pat.drop(columns=["file"]).to_csv(os.path.join(OUT, "patrimonio_sap_milano_serie.csv"), index=False, sep=";")
su[["ente", "servizio", "assegnati", "liberi", "sfitti_per_carenze_manutentive", "data_riferimento", "nota"]].to_csv(os.path.join(OUT, "stato_utilizzo_marzo_2023.csv"), index=False, sep=";")
ar.to_csv(os.path.join(OUT, "aler_vuoti_serie_2018_2025.csv"), index=False, sep=";")
av.drop(columns=["file"]).to_csv(os.path.join(OUT, "avvisi_milano.csv"), index=False, sep=";")
gr.drop(columns=["file"]).to_csv(os.path.join(OUT, "domande_assegnazioni_2016_2020.csv"), index=False, sep=";")
pm.drop(columns=["fonte"]).to_csv(os.path.join(OUT, "piano_2026_per_municipio.csv"), index=False, sep=";")
oc.drop(columns=["fonte"]).to_csv(os.path.join(OUT, "occupazioni_abusive.csv"), index=False, sep=";")
alt.to_csv(os.path.join(OUT, "altre_fonti.csv"), index=False, sep=";")
print("scritti:", sorted(os.listdir(OUT)))
if AVV:
    print("CONTROLLI FALLITI:", AVV)
    sys.exit(1)
