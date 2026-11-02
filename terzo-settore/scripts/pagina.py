"""Scrive i file della pagina "Associazioni e terzo settore": docs/terzo-settore/data/* e docs/terzo-settore/index.html (dal modello pagina_template.html).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <terzo-settore_dir> <milano-in-dati_dir> <docs_dir>

Legge (fase 1, cartella pulito/): runts_milano.csv, runts_grandi_citta.csv, runts_province_metropolitane.csv, riepilogo_build.json,
registro_comune_associazioni.csv, regione_persone_giuridiche_milano.csv, nil_terzo_settore.csv, bes_nonprofit_per_10000_citta_metropolitane.csv,
istat_nonprofit_province_2023.csv, istat_N01GCOM_citta.csv; raw/comune/ds273 (censimento 2011); poligoni NIL di citta-15-minuti.
Scrive in <docs_dir>/terzo-settore/data/: riepilogo.json, nil.geojson, enti_milano.json, enti_milano.csv, citta.csv, nil.csv, bes_nonprofit.csv,
registro_comune_settori.csv, istat_2011_milano_settori.csv, istat_2011_citta.csv, runts_per_anno_milano.csv.
Nessun nome di persona: il nome del legale rappresentante del RUNTS non e' mai stato copiato in pulito/. Le email e i telefoni dei registri del Comune non sono ripubblicati.
Tutti i numeri della pagina nascono qui e sono controllati con check()."""
import sys, os, json, glob, shutil
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

T, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(T, "pulito")
OUT = os.path.join(DOCS, "terzo-settore", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []


def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


def rd(f, **k):
    return pd.read_csv(os.path.join(PU, f), keep_default_na=False, na_values=[""], **k)


B = json.load(open(os.path.join(PU, "riepilogo_build.json"), encoding="utf8"))
R = {}
R["date"] = {"runts": "2026-11-02", "comune": "2026-11-02", "istat": "2026-11-02", "popolazione": "2026-11-02"}

# ------------------------------------------------------------------ RUNTS Milano
m = rd("runts_milano.csv", sep=";", dtype=str)
N_MI = len(m)
check("enti RUNTS a Milano", N_MI, 3986)
ITA = B["runts_per_sezione_italia"]
N_ITA = B["runts_righe"]
check("enti RUNTS in Italia", N_ITA, 154244)
SEZ = [("ASSOCIAZIONI DI PROMOZIONE SOCIALE", "Associazioni di promozione sociale (APS)"),
       ("ORGANIZZAZIONI DI VOLONTARIATO", "Organizzazioni di volontariato (ODV)"),
       ("IMPRESE SOCIALI", "Imprese sociali (comprese le cooperative sociali)"),
       ("ALTRI ENTI DEL TERZO SETTORE", "Altri enti del Terzo settore"),
       ("ENTI FILANTROPICI", "Enti filantropici"),
       ("SOCIETA' DI MUTUO SOCCORSO", "Società di mutuo soccorso")]
sez_mi = m.sezione.value_counts().to_dict()
R["runts"] = {"italia": N_ITA, "milano": N_MI, "quota_milano_pct": round(100 * N_MI / N_ITA, 2),
              "quota_residenti_milano_pct": None, "sezioni": []}
pop_ita = B["pop_italia_2025"]
pop_mi = [g for g in B["grandi_citta"] if g["citta"] == "Milano"][0]["abitanti_2025"]
R["runts"]["quota_residenti_milano_pct"] = round(100 * pop_mi / pop_ita, 2)
for k, lab in SEZ:
    n, ni = int(sez_mi.get(k, 0)), int(ITA.get(k, 0))
    R["runts"]["sezioni"].append({"k": k, "t": lab, "n": n, "pct": round(100 * n / N_MI, 1), "ita": ni, "ita_pct": round(100 * ni / N_ITA, 1)})
nd = int(sez_mi.get("n.d.", 0))
R["runts"]["sezione_nd_milano"] = nd
check("somma sezioni Milano", sum(s["n"] for s in R["runts"]["sezioni"]) + nd, N_MI)
tipo = m.tipo.value_counts().to_dict()
R["runts"]["tipi"] = [{"t": k, "n": int(v), "pct": round(100 * v / N_MI, 1)} for k, v in tipo.items()]
check("cooperative sociali (dal nome) a Milano", tipo["cooperativa sociale"], 449)
R["runts"]["per_10000_milano"] = round(10000 * N_MI / pop_mi, 1)
R["runts"]["per_10000_italia"] = round(10000 * N_ITA / pop_ita, 1)
check("enti ogni 10.000 abitanti, Milano", R["runts"]["per_10000_milano"], 29.2, 0.05)
check("enti ogni 10.000 abitanti, Italia", R["runts"]["per_10000_italia"], 26.2, 0.05)
cinque_mi = int((m.cinque_per_mille == "Si").sum())
d_ita = rd(os.path.join("runts_enti_italia_senza_persone.csv"), sep=";", dtype=str)
cinque_ita = int((d_ita.cinque_per_mille == "Si").sum())
R["runts"]["cinque_per_mille"] = {"milano": cinque_mi, "milano_pct": round(100 * cinque_mi / N_MI, 1), "italia": cinque_ita, "italia_pct": round(100 * cinque_ita / N_ITA, 1)}
check("5x1000 Milano", cinque_mi, 2686)
# per anno di iscrizione
anno = m.anno_iscrizione.astype(int).value_counts().sort_index()
anno_ita = d_ita.anno_iscrizione.astype(int).value_counts().sort_index()
R["runts"]["anni"] = [{"a": int(a), "milano": int(anno.get(a, 0)), "italia": int(anno_ita.get(a, 0))} for a in sorted(set(anno.index) | set(anno_ita.index)) if a >= 2021]
check("somma anni Milano", int(anno[anno.index >= 2021].sum()), N_MI)
pd.DataFrame(R["runts"]["anni"]).to_csv(os.path.join(OUT, "runts_per_anno_milano.csv"), index=False)

# ------------------------------------------------------------------ grandi citta' e provincia
big = rd("runts_grandi_citta.csv")
cit = []
for _, r in big.iterrows():
    cit.append({"citta": r.citta, "enti": int(r.enti_runts), "ab": int(r.abitanti_2025), "p": float(r.per_10000), "odv": float(r.odv_per_10000),
                "aps": float(r.aps_per_10000), "imp": float(r.imprese_sociali_per_10000), "alt": float(r.altri_per_10000)})
R["citta"] = cit
pos = [c["citta"] for c in cit].index("Milano") + 1
R["milano_posizione"] = {"posto": pos, "su": len(cit)}
check("posizione di Milano tra le 18 grandi citta'", pos, 9)
check("numero di grandi citta'", len(cit), 18)
def rk(k):
    return sorted([c[k] for c in cit], reverse=True).index([c[k] for c in cit if c["citta"] == "Milano"][0]) + 1
R["milano_rank"] = {"odv": rk("odv"), "aps": rk("aps"), "imp": rk("imp"), "alt": rk("alt"), "su": len(cit)}
print("rank Milano per tipo:", R["milano_rank"])
big[["citta", "cod_istat", "abitanti_2025", "enti_runts", "per_10000", "odv_per_10000", "aps_per_10000", "imprese_sociali_per_10000", "altri_per_10000"]].to_csv(
    os.path.join(OUT, "citta.csv"), index=False)
pm = B["provincia_milano"]
resto_n = pm["enti_runts"] - N_MI
resto_ab = pm["abitanti_2025"] - pop_mi
R["provincia"] = {"enti": pm["enti_runts"], "ab": pm["abitanti_2025"], "p": pm["per_10000"], "resto_enti": resto_n, "resto_ab": resto_ab,
                  "resto_p": round(10000 * resto_n / resto_ab, 1), "comuni": B["provincia_mi_comuni_con_enti"]}
check("enti RUNTS nel resto della provincia di Milano ogni 10.000", R["provincia"]["resto_p"], 14.0, 0.05)

# ------------------------------------------------------------------ riconciliazione con il Bes e con l'ISTAT
bes = rd("bes_nonprofit_per_10000_citta_metropolitane.csv")
anni = [c for c in bes.columns if c != "territorio"]
R["bes"] = {"anni": [int(a) for a in anni], "serie": {r.territorio: [None if pd.isna(r[a]) else float(r[a]) for a in anni] for _, r in bes.iterrows()}}
bes.to_csv(os.path.join(OUT, "bes_nonprofit.csv"), index=False)
check("Bes Milano 2022", R["bes"]["serie"]["Milano"][-1], 53.9)
check("Bes Italia 2022", R["bes"]["serie"]["Italia"][-1], 61.0)
t22 = rd("istat_nonprofit_province_2023.csv")
mi22 = t22[t22.provincia == "Milano"].iloc[0]
ita_ist = float(t22.istituzioni.sum())
check("righe province nella tavola 22", len(t22), 107)
R["riconciliazione"] = {
    "bes_milano_2022": R["bes"]["serie"]["Milano"][-1], "bes_italia_2022": R["bes"]["serie"]["Italia"][-1],
    "istat_milano_2023": int(mi22.istituzioni), "istat_milano_dip_2023": int(mi22.dipendenti), "istat_italia_2023": int(ita_ist),
    "istat_milano_p10000": round(10000 * mi22.istituzioni / pm["abitanti_2025"], 1), "istat_italia_p10000": round(10000 * ita_ist / pop_ita, 1),
    "runts_su_istat_milano_pct": round(100 * pm["enti_runts"] / mi22.istituzioni, 1), "runts_su_istat_italia_pct": round(100 * N_ITA / ita_ist, 1)}
check("istituzioni ISTAT 2023 provincia di Milano", R["riconciliazione"]["istat_milano_2023"], 17900)
# ordine delle citta' metropolitane: Bes (tutto il non profit, 2022) contro RUNTS (solo ETS, provincia, 2026)
pr = rd("runts_province_metropolitane.csv")
sig2nome = {"TO": "Torino", "GE": "Genova", "MI": "Milano", "VE": "Venezia", "BO": "Bologna", "FI": "Firenze", "RM": "Roma", "NA": "Napoli", "BA": "Bari",
            "PA": "Palermo", "CT": "Catania", "ME": "Messina", "RC": "Reggio di Calabria", "CA": "Cagliari"}
pr["territorio"] = pr.provincia.map(sig2nome)
assert pr.territorio.notna().all()
conf = []
for _, r in pr.iterrows():
    conf.append({"t": r.territorio, "bes": R["bes"]["serie"][r.territorio][-1], "runts": float(r.per_10000)})
conf.sort(key=lambda x: -x["bes"])
for i, c in enumerate(conf):
    c["rk_bes"] = i + 1
for i, c in enumerate(sorted(conf, key=lambda x: -x["runts"])):
    c["rk_runts"] = i + 1
R["confronto_province"] = conf

# ------------------------------------------------------------------ Registri del Comune: per NIL
nil = rd("nil_terzo_settore.csv")
reg = rd("registro_comune_associazioni.csv", sep=";", dtype=str)
pj = rd("regione_persone_giuridiche_milano.csv", sep=";", dtype=str)
reg["ok"] = reg.id_nil.notna()
R["registro_comune"] = {"n": len(reg), "con_nil": int(reg.ok.sum()), "fuori_milano": int((reg.esito_geo == "fuori_milano").sum()),
                        "non_localizzate": int(len(reg) - reg.ok.sum() - (reg.esito_geo == "fuori_milano").sum()),
                        "natura": reg.natura.value_counts().to_dict(),
                        "settori": [{"t": k, "n": int(v), "pct": round(100 * v / len(reg), 1)} for k, v in reg.settore.value_counts().items()],
                        "municipi": [{"t": k, "n": int(v)} for k, v in reg.municipio_prevalente.value_counts().sort_index().items()]}
check("registro comunale: righe", len(reg), 795)
check("registro comunale: con NIL", R["registro_comune"]["con_nil"], 677)
pd.DataFrame(R["registro_comune"]["settori"]).to_csv(os.path.join(OUT, "registro_comune_settori.csv"), index=False)
R["albo_coop"] = {"n": B["ds562_righe"], "con_nil": B["ds562_righe"] - B["ds562_senza_nil"]}
R["persone_giuridiche"] = {"n": B["ds606_righe"], "con_nil": int(pj.id_nil.notna().sum()), "fondazioni_dal_nome": B["ds606_fondazioni"]}
R["ong"] = {"n": B["ds596_righe"]}
nil["in_classifica"] = nil.abitanti_2024 >= 5000
for c in ["associazioni_registro_comune", "cooperative_sociali_albo_comune", "persone_giuridiche_regione", "ong_regione"]:
    check("somma NIL " + c, int(nil[c].sum()), B["somma_nil"][c])
nil["tot_registri_nonsommabile"] = np.nan

# sezione NIL concentrata nel Duomo?
def share_top(c, k):
    s = nil.sort_values(c, ascending=False)[c]
    return round(100 * s.head(k).sum() / s.sum(), 1)


R["concentrazione"] = {c: {"top3_pct": share_top(c, 3), "top10_pct": share_top(c, 10), "totale": int(nil[c].sum())} for c in
                       ["associazioni_registro_comune", "cooperative_sociali_albo_comune", "persone_giuridiche_regione"]}
duomo = nil[nil.nil == "DUOMO"].iloc[0]
R["duomo"] = {"ab": int(duomo.abitanti_2024), "pg": int(duomo.persone_giuridiche_regione), "coop": int(duomo.cooperative_sociali_albo_comune),
              "ass": int(duomo.associazioni_registro_comune),
              "pg_pct": round(100 * duomo.persone_giuridiche_regione / nil.persone_giuridiche_regione.sum(), 1),
              "coop_pct": round(100 * duomo.cooperative_sociali_albo_comune / nil.cooperative_sociali_albo_comune.sum(), 1),
              "ab_pct": round(100 * duomo.abitanti_2024 / nil.abitanti_2024.sum(), 1)}
nil_out = nil.drop(columns=["tot_registri_nonsommabile"])
nil_out.to_csv(os.path.join(OUT, "nil.csv"), index=False)

# geojson NIL
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
anag = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(anag.nil, anag.nil_nome))
row = {int(r.id_nil): r for _, r in nil.iterrows()}
feats = []


def nn(x):
    return None if pd.isna(x) else float(x)


def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]


for f in nilgeo["features"]:
    i = int(f["properties"]["ID_NIL"])
    r = row[i]
    g = mapping(shape(f["geometry"]).simplify(0.00003, preserve_topology=True))
    feats.append({"type": "Feature", "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])},
                  "properties": {"i": i, "n": nomi.get(i) or str(r.nil).title(), "ab": int(r.abitanti_2024), "cl": int(r.abitanti_2024 >= 5000),
                                 "a": int(r.associazioni_registro_comune), "ap": nn(r.associazioni_registro_comune_per_10000),
                                 "c": int(r.cooperative_sociali_albo_comune), "cp": nn(r.cooperative_sociali_albo_comune_per_10000),
                                 "g": int(r.persone_giuridiche_regione), "gp": nn(r.persone_giuridiche_regione_per_10000),
                                 "o": int(r.ong_regione)}})
assert len(feats) == 88
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ ISTAT 2011 (censimento delle istituzioni non profit)
d = pd.read_csv(glob.glob(os.path.join(T, "raw", "comune", "ds273", "*.csv"))[0], sep=";", dtype=str)
d.columns = ["settore", "sotto", "forma", "ist", "addetti", "esterni", "temp", "vol"]
for c in ["settore", "sotto", "forma"]:
    d[c] = d[c].str.strip()
for c in ["ist", "addetti", "esterni", "temp", "vol"]:
    d[c] = pd.to_numeric(d[c])
check("2011: istituzioni a Milano", int(d.ist.sum()), 6662)
check("2011: volontari a Milano", int(d.vol.sum()), 142539)
sett = d.groupby("settore")[["ist", "addetti", "esterni", "vol"]].sum().sort_values("ist", ascending=False).reset_index()
sett["dip_est"] = sett.addetti + sett.esterni
sett.to_csv(os.path.join(OUT, "istat_2011_milano_settori.csv"), index=False)
forma = d.groupby("forma")[["ist", "addetti", "esterni", "vol"]].sum().sort_values("ist", ascending=False).reset_index()
R["istat2011"] = {"istituzioni": int(d.ist.sum()), "volontari": int(d.vol.sum()), "dipendenti_esterni": int(d.addetti.sum() + d.esterni.sum()),
                  "settori": [{"t": r.settore, "ist": int(r.ist), "dip": int(r.dip_est), "vol": int(r.vol)} for _, r in sett.iterrows()],
                  "forme": [{"t": r.forma, "ist": int(r.ist), "dip": int(r.addetti + r.esterni), "vol": int(r.vol)} for _, r in forma.iterrows()]}
g = rd("istat_N01GCOM_citta.csv", dtype=str)
a = g[(g.icnpo == "ALL") & (g.tipo_attivita == "ALL") & (g.finanziamento == "ALL") & (g.orientamento == "ALL")].copy()
a["valore"] = a.valore.astype(float)
pv = a.pivot_table(index="citta", columns="tipo_dato", values="valore", aggfunc="sum")
c11 = pd.DataFrame({"istituzioni": pv["ANPIN"], "volontari": pv["ANPIV"], "dipendenti_esterni": pv["ANPIEOW"]})
c11["volontari_per_istituzione"] = (c11.volontari / c11.istituzioni).round(1)
c11["dip_est_per_istituzione"] = (c11.dipendenti_esterni / c11.istituzioni).round(1)
c11 = c11.sort_values("volontari_per_istituzione", ascending=False).reset_index()
c11.to_csv(os.path.join(OUT, "istat_2011_citta.csv"), index=False)
check("2011 Milano: ISTAT bulk = Comune (istituzioni)", float(c11[c11.citta == "Milano"].istituzioni.iloc[0]), 6662)
check("2011 Milano: ISTAT bulk = Comune (dipendenti+esterni)", float(c11[c11.citta == "Milano"].dipendenti_esterni.iloc[0]), int(d.addetti.sum() + d.esterni.sum()))
R["istat2011"]["citta"] = [{"citta": r.citta, "ist": int(r.istituzioni), "vol": int(r.volontari), "dip": int(r.dipendenti_esterni),
                            "vol_per_ist": float(r.volontari_per_istituzione), "dip_per_ist": float(r.dip_est_per_istituzione)} for _, r in c11.iterrows()]
R["istat2011"]["milano_vol_rank"] = [c["citta"] for c in R["istat2011"]["citta"]].index("Milano") + 1
R["istat2011"]["milano_dip_rank"] = sorted([c["dip_per_ist"] for c in R["istat2011"]["citta"]], reverse=True).index(
    [c for c in R["istat2011"]["citta"] if c["citta"] == "Milano"][0]["dip_per_ist"]) + 1

# ------------------------------------------------------------------ elenco enti di Milano (per la tabella con ricerca)
SIG = {"ASSOCIAZIONI DI PROMOZIONE SOCIALE": "APS", "ORGANIZZAZIONI DI VOLONTARIATO": "ODV", "IMPRESE SOCIALI": "IS", "ALTRI ENTI DEL TERZO SETTORE": "AL",
       "ENTI FILANTROPICI": "EF", "SOCIETA' DI MUTUO SOCCORSO": "SMS", "n.d.": "nd"}
TIPI = {"APS": 0, "ODV": 1, "cooperativa sociale": 2, "altra impresa sociale": 3, "fondazione (dal nome)": 4, "cooperativa (dal nome)": 5, "altro ETS": 6}
m2 = m.sort_values("denominazione", key=lambda s: s.str.upper())
enti = [[r.denominazione, SIG[r.sezione], TIPI[r.tipo], int(r.anno_iscrizione), 1 if r.cinque_per_mille == "Si" else 0] for r in m2.itertuples()]
json.dump({"sezioni": SIG, "tipi": {str(v): k for k, v in TIPI.items()}, "colonne": ["denominazione", "sezione", "tipo_dal_nome", "anno_iscrizione", "cinque_per_mille"], "righe": enti},
          open(os.path.join(OUT, "enti_milano.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
m2.assign(sezione_runts=m2.sezione)[["denominazione", "sezione", "tipo", "anno_iscrizione", "cinque_per_mille"]].rename(
    columns={"tipo": "tipo_dal_nome", "sezione": "sezione_runts"}).to_csv(os.path.join(OUT, "enti_milano.csv"), index=False, encoding="utf8")

R["avvisi"] = AVVISI
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, allow_nan=False)

# ------------------------------------------------------------------ pagina
tpl = open(os.path.join(T, "scripts", "pagina_template.html"), encoding="utf8").read()
os.makedirs(os.path.join(DOCS, "terzo-settore"), exist_ok=True)
open(os.path.join(DOCS, "terzo-settore", "index.html"), "w", encoding="utf8").write(tpl)
print("\nAVVISI:", AVVISI if AVVISI else "nessuno")
print(json.dumps({k: R[k] for k in ["provincia", "riconciliazione", "milano_posizione", "concentrazione", "duomo"]}, ensure_ascii=False, indent=1))
print(json.dumps(R["confronto_province"], ensure_ascii=False))
print(json.dumps({"vol_rank": R["istat2011"]["milano_vol_rank"], "dip_rank": R["istat2011"]["milano_dip_rank"], "citta": R["istat2011"]["citta"]}, ensure_ascii=False))
