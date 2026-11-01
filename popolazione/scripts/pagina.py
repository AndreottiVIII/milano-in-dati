"""Scrive i file dati delle TRE pagine del filone popolazione:
  docs/arrivi-partenze/data/, docs/comunita/data/, docs/eta/data/
Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <popolazione_dir> <milano-in-dati_dir> <docs_dir>
Legge solo file gia' puliti dalla fase 1 (popolazione/pulito/*) e i poligoni NIL di citta-15-minuti (ds964).
Scrive dati aggregati (per NIL, per anno); nessun dato individuale esiste nei file di partenza.
Gli HTML delle pagine sono file a mano (docs/<pagina>/index.html) e leggono questi dati con fetch."""
import sys, os, json, csv
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

POP, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(POP, "pulito")
AVVISI = []
def check(nome, calc, atteso, tol=0):
    ok = abs(calc - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: {calc} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calc} (atteso {atteso})")

def rd(name, **kw): return pd.read_csv(os.path.join(PU, name), **kw)
def out(page): d = os.path.join(DOCS, page, "data"); os.makedirs(d, exist_ok=True); return d
def dump(obj, path): json.dump(obj, open(path, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
def R(x, d=1): return None if pd.isna(x) else round(float(x), d)

# ------------------------------------------------------------------ NIL: nomi e poligoni
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
NOME = dict(zip(ana.nil.astype(int), ana.nil_nome))
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
GEOM = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
assert set(GEOM) == set(NOME) and len(NOME) == 88
def rnd(c): return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
def geom_json(i):
    g = mapping(GEOM[i].simplify(0.00003, preserve_topology=True))
    return {"type": g["type"], "coordinates": rnd(g["coordinates"])}
def fc(props_by_id):
    return {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": props_by_id[i], "geometry": geom_json(i)} for i in sorted(props_by_id)]}

ANNI = list(range(1999, 2026))
ind = rd("eta_nil_anno_indicatori.csv")
RES = ind.pivot(index="id_nil", columns="anno", values="residenti").reindex(index=sorted(NOME), columns=ANNI).fillna(0)

# =================================================================== PAGINA 1: arrivi e partenze
O1 = out("arrivi-partenze")
f = rd("flussi_citta_anno.csv").set_index("anno")
rA = json.load(open(os.path.join(PU, "riepilogo_A.json"), encoding="utf8"))

serie = []
for y in range(2002, 2026):
    r = f.loc[y]
    d = {"a": y, "isc_i": int(r.istat_isc_interno), "canc_i": int(r.istat_canc_interno), "isc_e": int(r.istat_isc_estero), "canc_e": int(r.istat_canc_estero)}
    if 2004 <= y <= 2024:
        d.update({"ev_isc_i": int(r.ev_isc_italia), "ev_canc_i": int(r.ev_canc_italia), "ev_isc_e": int(r.ev_isc_estero), "ev_canc_e": int(r.ev_canc_estero),
                  "ev_isc_alt": int(r.ev_isc_altro), "ev_canc_alt": int(r.ev_canc_altro)})
    serie.append(d)
check("ISTAT saldo interno 2002-2025", sum(d["isc_i"] - d["canc_i"] for d in serie), -73618)
check("ISTAT saldo estero 2002-2025", sum(d["isc_e"] - d["canc_e"] for d in serie), 300487)
check("ISTAT saldo interno 2012-2019", sum(d["isc_i"] - d["canc_i"] for d in serie if 2012 <= d["a"] <= 2019), 64579)
check("ISTAT saldo interno 2020-2025", sum(d["isc_i"] - d["canc_i"] for d in serie if 2020 <= d["a"] <= 2025), -34195)

lz = rA["luogo_zone_totale_2020_2024"]
check("provincia MI saldo 2020-24", lz["Provincia di Milano (hinterland)"]["saldo"], -39473)
check("estero saldo 2020-24", lz["Estero"]["saldo"], 65783)
check("Sud saldo 2020-24", lz["Sud e isole (+Abruzzo, Molise)"]["saldo"], 24788)
lug = rd("flussi_luogo_2020_2024.csv")
destinazioni = {"zone": rA["luogo_zone"], "zone_tot": lz, "regioni_saldo": rA["luogo_regioni_saldo_2020_2024"],
                "quota_cancellazioni_italia": rA["quota_cancellazioni_italia_per_destinazione_2020_2024"]}
eta = rd("flussi_eta_2020_2024.csv")
etaj = {"classi": list(dict.fromkeys(eta.eta)), "anni": [2020, 2021, 2022, 2023, 2024],
        "saldo": {str(a): [int(v) for v in eta[eta.anno == a].saldo] for a in range(2020, 2025)},
        "isc": {str(a): [int(v) for v in eta[eta.anno == a].n_isc] for a in range(2020, 2025)},
        "canc": {str(a): [int(v) for v in eta[eta.anno == a].n_canc] for a in range(2020, 2025)},
        "gruppi": rA["eta_gruppi_totale_2020_2024"]}
check("eta 20-34 saldo 2020-24", etaj["gruppi"]["20-34"]["saldo"], 52168)
# covid: mensile 2019-2022 (ISTAT D7B, riga Totale)
m = rd("istat_bilancio_milano_2019_2024_mensile.csv", dtype={"Codice comune": str})
m = m[(m.Sesso == "Totale") & (m.Anno <= 2022) & (m.Mese <= 12)].sort_values(["Anno", "Mese"])
covid = [{"a": int(r.Anno), "m": int(r.Mese), "isc_i": int(r["Immigrati da altro comune"]), "canc_i": int(r["Emigrati per altro comune"]),
          "isc_e": int(r["Immigrati dall'estero"]), "canc_e": int(r["Emigrati per l'estero"]), "morti": int(r["Morti"])} for _, r in m.iterrows()]
check("estero iscritti 2020 (somma mesi)", sum(c["isc_e"] for c in covid if c["a"] == 2020), 11599)
dsl = rd("flussi_nil_riepilogo.csv")
props = {}
for i in sorted(NOME):
    p = {"i": i, "n": NOME[i]}
    for per, k in (("2012-2019", "a"), ("2020-2024", "b")):
        qq = dsl[(dsl.id_nil == i) & (dsl.periodo == per)]
        if len(qq) == 0:
            p[k] = [None, None, None, 0, 0, 0]; continue
        q = qq.iloc[0]
        p[k] = [R(q.saldo_italia_x1000_anno, 1), R(q.saldo_estero_x1000_anno, 1), R(q.saldo_tot_x1000_anno, 1), int(round(q.res)), int(q.si), int(q.se)]
    p["cl"] = 1 if p["b"][3] >= 3000 else 0
    props[i] = p
nilcsv = pd.DataFrame([{"id_nil": i, "nil": props[i]["n"], "residenti_medi_2020_2024": props[i]["b"][3],
                        "saldo_italia_x1000_anno_2012_2019": props[i]["a"][0], "saldo_estero_x1000_anno_2012_2019": props[i]["a"][1], "saldo_totale_x1000_anno_2012_2019": props[i]["a"][2],
                        "saldo_italia_x1000_anno_2020_2024": props[i]["b"][0], "saldo_estero_x1000_anno_2020_2024": props[i]["b"][1], "saldo_totale_x1000_anno_2020_2024": props[i]["b"][2]} for i in sorted(props)])
nilcsv.to_csv(os.path.join(O1, "nil_saldi.csv"), index=False, sep=";")
dump(fc(props), os.path.join(O1, "nil.geojson"))
dump({"serie": serie, "destinazioni": destinazioni, "eta": etaj, "covid": covid,
      "nil_conteggi": {"periodo_2020_2024": {"nil_70": rA["nil_2020-2024"]["n_nil"], "saldo_italia_negativo": rA["nil_2020-2024"]["saldo_italia_negativo"], "saldo_estero_positivo": rA["nil_2020-2024"]["saldo_estero_positivo"]},
                       "periodo_2012_2019": {"nil_70": rA["nil_2012-2019"]["n_nil"], "saldo_tot_negativo": rA["nil_2012-2019"]["saldo_tot_negativo"]}},
      "naturalizzazioni_note": "vedi pagina comunita",
      "origine": {"serie": "pulito/flussi_citta_anno.csv (ISTAT RBD 2001-2018, D7B 2019-2024, P2 2025; Comune ds1596/1600/1954/1956)", "destinazioni": "pulito/flussi_luogo_2020_2024.csv (ds1959/ds1960)",
                  "eta": "pulito/flussi_eta_2020_2024.csv (ds1957/ds1958)", "covid": "pulito/istat_bilancio_milano_2019_2024_mensile.csv (ISTAT D7B, riga Totale)", "nil": "pulito/flussi_nil_riepilogo.csv (ds1596/1600/1954/1956)"}},
     os.path.join(O1, "riepilogo.json"))
pd.DataFrame(serie).to_csv(os.path.join(O1, "saldi_anno.csv"), index=False, sep=";")
lug.to_csv(os.path.join(O1, "destinazioni_2020_2024.csv"), index=False, sep=";")
eta.to_csv(os.path.join(O1, "eta_saldi_2020_2024.csv"), index=False, sep=";")

# =================================================================== PAGINA 2: comunita'
O2 = out("comunita")
cn = rd("residenti_nil_anno_cittadinanza.csv")
cc = rd("residenti_comune_anno_cittadinanza.csv")
LAB = {"Cinese, Rep. Popolare": "Cina", "Sri Lanka (ex Ceylon)": "Sri Lanka", "Russa, Federazione": "Russia", "Congo Rep. Dem (ex Zaire)": "Congo (Rep. Dem.)",
       "Dominicana, Rep.": "Rep. Dominicana", "Corea del Sud, Rep.": "Corea del Sud", "Macedonia, ex Rep. Jugoslava": "Macedonia del Nord", "Ceca, Rep.": "Rep. Ceca",
       "Regno Unito": "Regno Unito", "Stati Uniti d'America": "Stati Uniti"}
def lab(k): return LAB.get(k, k)
tot_ct = cc[cc.cittadinanza != "Italia"].pivot(index="cittadinanza", columns="anno", values="residenti").fillna(0)
top = list(tot_ct[2025].sort_values(ascending=False).head(30).index)
for must in ("Ucraina", "Ecuador", "Francia"):
    assert must in top, must
pn = cn.pivot_table(index=["cittadinanza", "id_nil"], columns="anno", values="residenti", fill_value=0)
cit = []
for k in top:
    sub = pn.loc[k]
    nn = {str(int(i)): [int(sub.loc[i].get(y, 0)) for y in ANNI] for i in sub.index if sub.loc[i].sum() > 0}
    cit.append({"k": k, "l": lab(k), "c": [int(tot_ct.loc[k, y]) for y in ANNI], "n": nn})
str_nil = cn[cn.cittadinanza != "Italia"].groupby(["id_nil", "anno"]).residenti.sum().unstack(fill_value=0)
tot_city = cc.groupby("anno").residenti.sum()
str_city = cc[cc.cittadinanza != "Italia"].groupby("anno").residenti.sum()
ita_city = cc[cc.cittadinanza == "Italia"].groupby("anno").residenti.sum()
check("stranieri 2025", int(str_city[2025]), 295805); check("stranieri 1999", int(str_city[1999]), 105082)
check("Egitto 2025", int(tot_ct.loc["Egitto", 2025]), 41957)
com = [c for c in cit if c["k"] == "Cinese, Rep. Popolare"][0]
check("Cina Comasina 2025", com["n"]["82"][-1], 2390); check("Cina Comasina 1999", com["n"]["82"][0], 38)
check("Cina Sarpi 2025", com["n"]["69"][-1], 2437); check("Cina Villapizzone 2025", com["n"]["71"][-1], 3134)
ukr = [c for c in cit if c["k"] == "Ucraina"][0]; check("Ucraina 2022-2021", ukr["c"][-4] - ukr["c"][-5], 287)
# naturalizzazioni
ds221 = pd.read_csv(os.path.join(POP, "raw", "comune_ds221", "ds221-popolazione-stranieri-acquisizioni-cittadinanza.csv"), sep=";").groupby("Anno").Numerosita.sum()
ds1964 = pd.read_csv(os.path.join(POP, "raw", "comune_ds1964", "ds1964_acquisizioni-cittadinanza_motivo.csv"), sep=";").groupby("Anno")["Numerosità"].sum()
nat = {int(a): int(v) for a, v in list(ds221.items()) + list(ds1964.items())}
d63 = pd.read_csv(os.path.join(POP, "raw", "comune_ds1963", "ds1963_acquisizioni-cittadinanza_cit_prec.csv"), sep=";")
n63 = d63.groupby("Cittadinanza precedente")["Numerosità"].sum().sort_values(ascending=False).head(10)
check("naturalizzazioni 2024", nat[2024], 9021); check("naturalizzazioni Egitto 2021-24", int(n63["Egitto"]), 7082)
# diversita'
ci = rd("cittadinanze_nil_indicatori.csv")
div = {}
for y in (1999, 2011, 2025):
    q = ci[(ci.anno == y) & (ci.residenti >= 3000) & (ci.stranieri >= 500)].copy()
    div[str(y)] = [{"n": NOME[int(r.id_nil)], "ne": R(r.n_effettivo, 1), "qs": R(100 * r.quota_stranieri, 1), "top": lab(r.cit_top1), "tq": R(100 * r.top1_quota_su_stranieri, 1), "res": int(r.residenti), "str": int(r.stranieri)}
                    for r in q.sort_values("n_effettivo").itertuples()]
check("diversita 2025 minima Comasina", div["2025"][0]["ne"], 3.2, 0.05)
conc = rd("cittadinanze_concentrazione.csv")
conc = conc[conc.anno == 2025][["cittadinanza", "residenti", "dissimilarita", "quota_nei_5_nil_top"]]
conc["l"] = conc.cittadinanza.map(lab)
concj = [{"l": r.l, "n": int(r.residenti), "d": R(r.dissimilarita, 2), "t5": R(100 * r.quota_nei_5_nil_top, 0)} for r in conc.sort_values("residenti", ascending=False).head(15).itertuples()]
# nil
props2 = {}
for i in sorted(NOME):
    props2[i] = {"i": i, "n": NOME[i], "r": [int(RES.loc[i, y]) for y in ANNI], "s": [int(str_nil.loc[i, y]) if i in str_nil.index else 0 for y in ANNI]}
dump(fc({i: {"i": p["i"], "n": p["n"]} for i, p in props2.items()}), os.path.join(O2, "nil.geojson"))
dump({"anni": ANNI, "nil": {str(i): {"n": p["n"], "r": p["r"], "s": p["s"]} for i, p in props2.items()}, "cit": cit,
      "citta": {"totale": [int(tot_city[y]) for y in ANNI], "stranieri": [int(str_city[y]) for y in ANNI], "italia": [int(ita_city[y]) for y in ANNI]}},
     os.path.join(O2, "cittadinanze.json"))
dump({"naturalizzazioni": nat, "naturalizzazioni_per_cittadinanza_2021_2024": {lab(k): int(v) for k, v in n63.items()}, "diversita": div, "concentrazione_2025": concj,
      "origine": {"cittadinanze": "pulito/residenti_nil_anno_cittadinanza.csv (ds27, campo Cittadinanza, residenti al 31/12)", "diversita": "pulito/cittadinanze_nil_indicatori.csv", "concentrazione": "pulito/cittadinanze_concentrazione.csv",
                  "naturalizzazioni": "raw/comune_ds221 (2003-2020), ds1964 (2021-2024), ds1963 (cittadinanza precedente 2021-2024)"}},
     os.path.join(O2, "riepilogo.json"))
rows = []
for c in cit:
    for i, v in c["n"].items():
        for y, n in zip(ANNI, v):
            if n: rows.append((c["k"], int(i), NOME[int(i)], y, n))
pd.DataFrame(rows, columns=["cittadinanza", "id_nil", "nil", "anno", "residenti"]).to_csv(os.path.join(O2, "residenti_per_cittadinanza_nil.csv"), index=False, sep=";")
pd.DataFrame([{"anno": y, "cittadinanza": c["k"], "residenti": c["c"][j]} for c in cit for j, y in enumerate(ANNI)]).to_csv(os.path.join(O2, "residenti_per_cittadinanza_citta.csv"), index=False, sep=";")
pd.DataFrame([{"anno": y, **{k: v for k, v in d.items()}} for y in (1999, 2011, 2025) for d in div[str(y)]]).rename(columns={"n": "nil", "ne": "numero_effettivo_cittadinanze", "qs": "quota_stranieri_pct", "top": "prima_cittadinanza", "tq": "quota_prima_su_stranieri_pct", "res": "residenti", "str": "stranieri"}).to_csv(os.path.join(O2, "diversita_nil.csv"), index=False, sep=";")

# =================================================================== PAGINA 3: eta' e centenari
O3 = out("eta")
cen_n = rd("centenari_nil_anno.csv").pivot(index="id_nil", columns="anno", values="centenari").reindex(index=sorted(NOME), columns=ANNI).fillna(0).astype(int)
def piv(col): return ind.pivot(index="id_nil", columns="anno", values=col)
EM, Q65, Q80, Q14, MED = piv("eta_media"), piv("q_65p"), piv("q_80p"), piv("q_0_14"), piv("eta_mediana")
props3 = {}
for i in sorted(NOME):
    props3[i] = {"i": i, "n": NOME[i], "r": [int(RES.loc[i, y]) for y in ANNI], "em": [R(EM.loc[i, y], 2) for y in ANNI], "md": [R(MED.loc[i, y], 1) for y in ANNI],
                 "q65": [R(100 * Q65.loc[i, y], 1) for y in ANNI], "q80": [R(100 * Q80.loc[i, y], 1) for y in ANNI], "q14": [R(100 * Q14.loc[i, y], 1) for y in ANNI],
                 "c": [int(cen_n.loc[i, y]) for y in ANNI]}
dump(fc({i: {"i": i, "n": p["n"]} for i, p in props3.items()}), os.path.join(O3, "nil.geojson"))
cy = rd("eta_comune_anno_indicatori.csv").set_index("anno")
cenc = rd("centenari_comune_anno_genere.csv").set_index("anno")
conf = rd("confronto_istat_comune.csv").set_index("anno_comune_31dic")
city = {"em": [R(cy.loc[y, "eta_media"], 2) for y in ANNI], "md": [R(cy.loc[y, "eta_mediana"], 2) for y in ANNI], "q14": [R(100 * cy.loc[y, "q_0_14"], 2) for y in ANNI],
        "q65": [R(100 * cy.loc[y, "q_65p"], 2) for y in ANNI], "q80": [R(100 * cy.loc[y, "q_80p"], 2) for y in ANNI], "q90": [R(100 * cy.loc[y, "q_90p"], 2) for y in ANNI],
        "r": [int(round(cy.loc[y, "residenti"])) for y in ANNI], "cF": [int(cenc.loc[y, "Femmine"]) for y in ANNI], "cM": [int(cenc.loc[y, "Maschi"]) for y in ANNI],
        "istat100": {str(int(k)): int(v) for k, v in conf.istat_100.items()}, "registro100": {str(int(k)): int(v) for k, v in conf.comune_100p.items()}}
check("centenari 2025", city["cF"][-1] + city["cM"][-1], 835); check("centenari 1999", city["cF"][0] + city["cM"][0], 249)
check("q65 2008", city["q65"][ANNI.index(2008)], 24.05, 0.01); check("q65 2023", city["q65"][ANNI.index(2023)], 22.01, 0.01)
check("eta media 2025", city["em"][-1], 45.65, 0.01)
# piramidi: classi di 5 anni (0-4 ... 95-99, 100+) per genere, anni 1999/2011/2025, tutti i NIL
g = rd("residenti_nil_anno_eta_genere.csv")
g = g[g.anno.isin([1999, 2011, 2025])].copy()
g["cl"] = np.minimum(g.eta // 5, 20)
pir = {}
for (a, i, ge), s in g.groupby(["anno", "id_nil", "genere"]):
    v = s.groupby("cl").residenti.sum().reindex(range(21), fill_value=0)
    pir.setdefault(str(a), {}).setdefault(str(i), {})["F" if ge == "Femmine" else "M"] = [int(x) for x in v.values]
# centenari per NIL 2025 e 2011
cl = []
for i in sorted(NOME):
    cl.append({"id_nil": i, "nil": NOME[i], "residenti_2025": props3[i]["r"][-1], "centenari_2025": props3[i]["c"][-1], "centenari_2011": props3[i]["c"][ANNI.index(2011)],
               "eta_media_2025": props3[i]["em"][-1], "eta_media_1999": props3[i]["em"][0], "quota_65_2025": props3[i]["q65"][-1], "quota_80_2025": props3[i]["q80"][-1]})
pd.DataFrame(cl).to_csv(os.path.join(O3, "nil_eta_centenari.csv"), index=False, sep=";")
dump({"anni": ANNI, "nil": {str(i): {k: v for k, v in p.items() if k != "i"} for i, p in props3.items()}, "citta": city}, os.path.join(O3, "eta.json"))
dump(pir, os.path.join(O3, "piramidi.json"))
pd.DataFrame({"anno": ANNI, "eta_media": city["em"], "eta_mediana": city["md"], "quota_0_14_pct": city["q14"], "quota_65_pct": city["q65"], "quota_80_pct": city["q80"], "quota_90_pct": city["q90"],
              "residenti": city["r"], "centenari_donne": city["cF"], "centenari_uomini": city["cM"]}).to_csv(os.path.join(O3, "citta_eta_centenari.csv"), index=False, sep=";")
dump({"origine": {"eta": "pulito/eta_nil_anno_indicatori.csv (ds27, residenti al 31/12; eta' in anni compiuti)", "centenari": "pulito/centenari_*.csv (eta' '100 e piu')",
                  "confronto_istat": "pulito/confronto_istat_comune.csv (ISTAT POSAS al 1 gennaio dell'anno dopo)"}}, os.path.join(O3, "riepilogo.json"))
print("AVVISI:", AVVISI or "nessuno")
if AVVISI: sys.exit(1)
