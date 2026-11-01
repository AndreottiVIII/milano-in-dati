"""Pagina web: scrive i dati aggregati in docs/luoghi-cercati/data/ (la pagina index.html e' scritta a mano).
Uso: python -I -X utf8 pagina.py <luoghi-cercati assoluto> <milano-in-dati assoluto>
Legge: pulito/*.csv, raw/pageviews_giornalieri/, raw/aggregato_wikipedia/, citta-15-minuti (poligoni NIL).
Scrive: data/riepilogo.json, data/serie.json, data/luoghi.csv, data/nil.geojson, data/non_luoghi.csv.
Scelte di Davide (1/11/2026): istituzioni, opere, marchi, eventi, la voce "Milano" restano fuori dalla classifica dei luoghi
(riquadro a parte); la voce Unesco di Santa Maria delle Grazie e' unita alla chiesa; i Navigli restano separati
con una riga "Navigli insieme"."""
import sys, os, json, glob, csv, time
import numpy as np
import pandas as pd
from shapely.geometry import shape, mapping

base, mid = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito")
OUT = os.path.join(mid, "docs", "luoghi-cercati", "data")
os.makedirs(OUT, exist_ok=True)
LANGS = ["it", "en", "de", "fr", "es", "ru", "zh", "ja", "pt", "ar"]
MERGE = {"Q11349456": "Q244952"}  # voce Unesco "Chiesa di S. Maria delle Grazie e Convento..." -> chiesa
NAVIGLI = ["Q1416580", "Q1416575", "Q362331", "Q3665046", "Q41868039"]

vm = pd.read_csv(os.path.join(P, "views_mensili.csv"), sep=";")
lu = pd.read_csv(os.path.join(P, "luoghi.csv"), sep=";", dtype={"id_nil": "Int64"})
vm["qid"] = vm.qid.replace(MERGE)
lu = lu[~lu.qid.isin(MERGE)].copy()
months = sorted(vm.mese.unique())
MI = {m: i for i, m in enumerate(months)}
luogo = lu[lu.tipo == "luogo"].set_index("qid")
fin = vm[vm.qid.isin(luogo.index)].copy()
fin["lg"] = fin.lingua.where(fin.lingua.isin(LANGS), "altre")
tot = fin.groupby("qid").views.sum().sort_values(ascending=False)
byl = fin.groupby(["qid", "lg"]).views.sum().unstack(fill_value=0)
R = {"scaricato": "2026-11-01", "mese_primo": months[0], "mese_ultimo": months[-1], "n_mesi": len(months)}
R["n_luoghi"] = int(len(luogo))
R["views_totali_luoghi"] = int(tot.sum())
lang_tot = fin.groupby("lingua").views.sum().sort_values(ascending=False)
R["quota_lingua"] = {k: round(100 * float(v) / float(lang_tot.sum()), 2) for k, v in lang_tot.head(12).items()}
R["quota_it"] = round(100 * float(lang_tot["it"]) / float(lang_tot.sum()), 1)
R["n_lingue"] = int(vm.lingua.nunique())
# ---- classifiche
def row(q, lg=None):
    r = luogo.loc[q]
    t = int(tot[q])
    it = int(byl.loc[q].get("it", 0))
    v = t if lg is None or lg == "all" else int(byl.loc[q].get(lg, 0))
    return {"q": q, "n": r.nome, "c": r.categoria, "nil": r.nil if isinstance(r.nil, str) else "", "v": v, "t": t,
            "it": round(100 * it / t, 1)}
# serie mensili per luogo (tutte le lingue e per lingua)
def series_of(qids, lg):
    d = fin[fin.qid.isin(qids)]
    if lg != "all":
        d = d[d.lingua == lg]
    a = np.zeros(len(months), dtype=int)
    for m, v in d.groupby("mese").views.sum().items():
        a[MI[m]] = int(v)
    return a.tolist()
nav_t = int(sum(tot.get(q, 0) for q in NAVIGLI))
nav_lang = {lg: int(sum(byl.loc[q].get(lg, 0) for q in NAVIGLI if q in byl.index)) for lg in LANGS}
nav = {"voci": [{"n": luogo.loc[q].nome, "t": int(tot[q])} for q in NAVIGLI], "t": nav_t,
       "it": round(100 * nav_lang["it"] / nav_t, 1)}
R["navigli_insieme"] = nav
tops = {}
need = set()
for lg in ["all"] + LANGS:
    s = (tot if lg == "all" else byl[lg]).sort_values(ascending=False).head(20)
    rows = [row(q, lg) for q in s.index]
    nv = nav_t if lg == "all" else nav_lang[lg]
    rows.append({"q": "navigli", "n": "Navigli insieme (somma di 5 voci)", "c": "somma", "nil": "", "v": nv, "t": nav_t, "it": nav["it"], "somma": True})
    rows.sort(key=lambda r: -r["v"])
    # la riga "somma" resta, ma al massimo 20 luoghi veri
    out, k = [], 0
    for r in rows:
        if not r.get("somma"):
            k += 1
            if k > 20:
                break
        out.append(r)
    tops[lg] = out
    need |= {r["q"] for r in out if r["q"] != "navigli"}
R["top"] = tops
# serie per i luoghi che servono (top20 di ogni lingua + top 60 generale)
need |= set(tot.head(60).index)
S = {"mesi": months, "luoghi": {}}
for q in sorted(need):
    S["luoghi"][q] = {lg: series_of([q], lg) for lg in ["all"] + LANGS}
S["luoghi"]["navigli"] = {lg: series_of(NAVIGLI, lg) for lg in ["all"] + LANGS}
# ---- sorpresa
rk = {q: i + 1 for i, q in enumerate(tot.index)}
R["sorpresa"] = {"stadio_t": int(tot["Q133566"]), "duomo_t": int(tot["Q18068"]), "stadio_estero": round(100 - row("Q133566")["it"], 1),
                 "duomo_estero": round(100 - row("Q18068")["it"], 1), "bosco_rango": rk["Q2501413"], "bosco_t": int(tot["Q2501413"]),
                 "stadio_maggio2023": int(S["luoghi"]["Q133566"]["all"][MI["2023-05"]]),
                 "duomo_mese_medio": round(float(tot["Q18068"]) / len(months)),
                 "top10_quota": round(100 * float(tot.head(10).sum()) / float(tot.sum()), 1),
                 "grazie_unite": int(tot["Q244952"]), "n_100k": int((tot >= 100000).sum()), "n_1m": int((tot >= 1000000).sum())}
# lingua preferita per luogo: chi vince il Duomo e chi lo stadio
win = {}
for lg in LANGS:
    s = byl[lg].sort_values(ascending=False)
    win[lg] = s.index[0]
R["primo_per_lingua"] = {lg: luogo.loc[q].nome for lg, q in win.items()}
# ---- non luoghi
nl = lu[lu.tipo != "luogo"].set_index("qid")
vv = vm[vm.qid.isin(nl.index)].groupby("qid").views.sum().sort_values(ascending=False)
ETI = {"citta_intera": "articolo sulla città", "opera_arte": "opera d'arte", "evento": "evento", "marchio": "marchio",
       "rete_trasporti": "rete di trasporti", "istruzione": "università/scuola", "stato_storico": "stato storico",
       "ente_territoriale": "ente territoriale", "citta_antica": "città antica", "ospedale": "ospedale",
       "biblioteca_archivio": "biblioteca/archivio", "istituzione_sanitaria": "ospedale/RSA"}
rows = [{"n": nl.loc[q].nome, "t": int(v), "tipo": ETI.get(nl.loc[q].categoria, nl.loc[q].categoria), "q": q} for q, v in vv.head(16).items()]
R["non_luoghi"] = rows
R["views_non_luoghi"] = int(vv.sum())
pd.DataFrame([{"qid": q, "nome": nl.loc[q].nome, "tipo": nl.loc[q].tipo, "categoria": nl.loc[q].categoria, "views_totali": int(v)}
              for q, v in vv.items()]).to_csv(os.path.join(OUT, "non_luoghi.csv"), sep=";", index=False)
# ---- piu stranieri / piu italiani (almeno 200.000 letture)
t2 = pd.DataFrame({"q": tot.index, "t": tot.values})
t2["it"] = [100 * byl.loc[q].get("it", 0) / t for q, t in zip(t2.q, t2.t)]
t2 = t2[t2.t >= 200000].copy()
t2["n"] = t2.q.map(luogo.nome)
t2 = t2.sort_values("it")
fm = lambda d: [{"n": r.n, "t": int(r.t), "it": round(float(r.it), 1)} for r in d.itertuples()]
R["piu_stranieri"] = fm(t2.head(12))
R["piu_italiani"] = fm(t2.tail(12).iloc[::-1])
R["n_200k"] = int(len(t2))
# ---- andamento nel tempo
it_m = [0] * len(months); es_m = [0] * len(months)
for (m, lgg), v in fin.assign(f=np.where(fin.lingua == "it", "it", "es")).groupby(["mese", "f"]).views.sum().items():
    (it_m if lgg == "it" else es_m)[MI[m]] = int(v)
R["tempo"] = {"mesi": months, "it": it_m, "estero": es_m}
years = sorted({m[:4] for m in months})
yt = {}
for y in years:
    idx = [i for i, m in enumerate(months) if m[:4] == y]
    yt[y] = {"it": int(sum(it_m[i] for i in idx)), "estero": int(sum(es_m[i] for i in idx)), "mesi": len(idx)}
R["annuale"] = yt
agg = {}
for f in glob.glob(os.path.join(base, "raw", "aggregato_wikipedia", "*.json")):
    d = json.load(open(f))
    agg[d["progetto"].split(".")[0]] = {i["timestamp"][:4] + "-" + i["timestamp"][4:6]: i["views"] for i in d["items"]}
pm = {}
for lg in ["it", "en", "de", "fr", "es"]:
    mm = fin[fin.lingua == lg].groupby("mese").views.sum()
    pm[lg] = {}
    for y in years:
        ms_ = [m for m in months if m[:4] == y]
        w = sum(agg[lg][m] for m in ms_)
        pm[lg][y] = {"wiki": int(w), "luoghi": int(sum(mm.get(m, 0) for m in ms_)), "per_milione": round(1e6 * sum(mm.get(m, 0) for m in ms_) / w, 2)}
R["per_milione"] = pm
# ---- picchi verificati e non spiegati
SRC = {
    "notre": ("Incendio di Notre-Dame de Paris (15 aprile 2019)", "https://en.wikipedia.org/wiki/Notre-Dame_de_Paris_fire", "Wikipedia, Notre-Dame de Paris fire"),
    "ucl16": ("Finale di Champions League a San Siro (28 maggio 2016)", "https://en.wikipedia.org/wiki/2016_UEFA_Champions_League_final", "Wikipedia, 2016 UEFA Champions League final"),
    "ucl23": ("Semifinali di Champions League Milan-Inter (10 maggio 2023) e Inter-Milan (16 maggio 2023)", "https://en.wikipedia.org/wiki/2022%E2%80%9323_UEFA_Champions_League_knockout_phase", "Wikipedia, 2022-23 UEFA Champions League knockout phase (rapporti UEFA)"),
    "ucl25": ("Semifinale di ritorno Inter-Barcellona (6 maggio 2025)", "https://en.wikipedia.org/wiki/2024%E2%80%9325_UEFA_Champions_League_knockout_phase", "Wikipedia, 2024-25 UEFA Champions League knockout phase (rapporto UEFA)"),
    "olim19": ("Assegnazione a Milano e Cortina dei Giochi invernali 2026 (24 giugno 2019, sessione CIO a Losanna)", "https://en.wikipedia.org/wiki/2026_Winter_Olympics", "Wikipedia, 2026 Winter Olympics"),
    "olim26": ("Cerimonia di apertura dei Giochi olimpici invernali a San Siro (6 febbraio 2026)", "https://en.wikipedia.org/wiki/2026_Winter_Olympics_opening_ceremony", "Wikipedia, 2026 Winter Olympics opening ceremony"),
    "boc": ("Concerto di Pasqua di Andrea Bocelli nel Duomo vuoto (12 aprile 2020)", "https://en.wikipedia.org/wiki/Andrea_Bocelli", "Wikipedia, Andrea Bocelli"),
    "leo": ("Sgombero del centro sociale Leoncavallo (21 agosto 2025)", "https://it.wikipedia.org/wiki/Centro_sociale_Leoncavallo", "Wikipedia, Centro sociale Leoncavallo"),
    "dome": ("Giochi olimpici invernali (6-22 febbraio 2026): la voce dell'impianto dice che vi si giocano parte dei tornei di hockey su ghiaccio", "https://it.wikipedia.org/wiki/Unipol_Dome", "Wikipedia, Unipol Dome"),
}
def daily(q, lg):
    d = json.load(open(os.path.join(base, "raw", "pageviews_giornalieri", lg, q + ".json"), encoding="utf8"))
    s = pd.Series({i["timestamp"][:8]: i["views"] for i in d["items"]})
    s.index = pd.to_datetime(s.index, format="%Y%m%d")
    return s.asfreq("D", fill_value=0)
EV = [("Q18068", "it", ["2019-04-15", "2019-04-16"], "notre"), ("Q133566", "en", ["2016-05-28"], "ucl16"),
      ("Q133566", "en", ["2023-05-10", "2023-05-16"], "ucl23"), ("Q133566", "en", ["2025-05-06"], "ucl25"),
      ("Q133566", "en", ["2019-06-24"], "olim19"), ("Q133566", "en", ["2026-02-06"], "olim26"),
      ("Q18068", "en", ["2020-04-12"], "boc"), ("Q3830487", "it", ["2025-08-21"], "leo")]
picchi = []
for q, lg, dates, key in EV:
    s = daily(q, lg)
    vals, meds = [], []
    for dt in dates:
        t = pd.Timestamp(dt)
        vals.append(int(s[t]))
        meds.append(float(s[t - pd.Timedelta(days=28):t - pd.Timedelta(days=1)].median()))
    picchi.append({"luogo": luogo.loc[q].nome, "quando": ", ".join(dates), "lingua": lg, "valori": vals, "normale": round(float(np.mean(meds))),
                   "evento": SRC[key][0], "fonte": SRC[key][1], "fonte_n": SRC[key][2]})
# Unipol Dome: mese
mpk = pd.read_csv(os.path.join(P, "picchi_mensili.csv"), sep=";")
r = mpk[(mpk.qid == "Q64825395") & (mpk.mese == "2026-02")].iloc[0]
picchi.append({"luogo": r.nome, "quando": "febbraio 2026 (mese)", "lingua": "tutte", "valori": [int(r.views)], "normale": round(float(r["mediana_6+6_mesi"])),
               "evento": SRC["dome"][0], "fonte": SRC["dome"][1], "fonte_n": SRC["dome"][2]})
coperti = {("Q133566", m) for m in ["2016-05", "2019-06", "2023-05", "2025-05", "2026-02"]} | {("Q18068", "2019-04"), ("Q18068", "2020-04"),
          ("Q3830487", "2025-08"), ("Q3830487", "2025-09"), ("Q64825395", "2026-01"), ("Q64825395", "2026-02")}
seen = set()
nonsp = []
for r in mpk.sort_values("eccesso", ascending=False).itertuples():
    if (r.qid, r.mese) in coperti or r.qid in seen or r.qid not in luogo.index:
        continue
    seen.add(r.qid)
    nonsp.append({"luogo": r.nome, "quando": r.mese + " (mese)", "valori": [int(r.views)], "normale": round(float(r._4))})
    if len(nonsp) >= 10:
        break
R["picchi_verificati"] = picchi
R["picchi_non_spiegati"] = nonsp
R["eventi_grafico"] = [
    {"m": "2016-05", "s": "stadio", "t": "28 maggio 2016: finale di Champions League a San Siro"},
    {"m": "2019-04", "s": "duomo", "t": "15-16 aprile 2019: incendio di Notre-Dame"},
    {"m": "2019-06", "s": "stadio", "t": "24 giugno 2019: assegnazione dei Giochi invernali 2026 a Milano e Cortina"},
    {"m": "2020-04", "s": "duomo", "t": "12 aprile 2020: concerto di Pasqua di Bocelli nel Duomo vuoto"},
    {"m": "2023-05", "s": "stadio", "t": "10 e 16 maggio 2023: semifinali di Champions League Milan-Inter"},
    {"m": "2025-05", "s": "stadio", "t": "6 maggio 2025: semifinale Inter-Barcellona a San Siro"},
    {"m": "2026-02", "s": "stadio", "t": "6 febbraio 2026: apertura dei Giochi olimpici invernali a San Siro"}]
R["lockdown"] = {"da": "2020-03", "a": "2020-04", "t": "Primo lockdown nazionale in Italia (dal 9 marzo 2020; riaperture graduali dal 4 maggio)",
                 "fonte": "https://en.wikipedia.org/wiki/COVID-19_lockdowns_in_Italy", "fonte_n": "Wikipedia, COVID-19 lockdowns in Italy"}
# redirect
rd = pd.read_csv(os.path.join(P, "redirect_it_riepilogo.csv"), sep=";")
R["redirect"] = {"controllati": int(len(rd)), "totale_%": round(100 * rd.views_it_redirect.sum() / rd.views_it_titolo_attuale.sum(), 1),
                 "mediana_%": round(float(rd["redirect_su_titolo_%"].median()), 1),
                 "casi": [{"n": r.nome, "titolo": r.redirect_principale.replace("_", " "), "redirect": int(r.views_redirect_principale), "voce": int(r.views_it_titolo_attuale)}
                          for r in rd.head(4).itertuples()]}
# ---- NIL
fin2 = fin.merge(luogo[["id_nil"]], left_on="qid", right_index=True, suffixes=("_x", ""))
nv = fin2.groupby("id_nil").views.sum()
nn = luogo[luogo.id_nil.notna()].groupby("id_nil").size()
topq = {}
for q in tot.index:
    i = luogo.loc[q].id_nil
    if pd.notna(i) and int(i) not in topq:
        topq[int(i)] = q
g = json.load(open(os.path.join(mid, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
feats = []
tv = float(nv.sum())
def rnd(c):
    return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
for f in g["features"]:
    i = int(f["properties"]["ID_NIL"])
    geom = shape(f["geometry"]).simplify(0.00004, preserve_topology=True)
    q = topq.get(i)
    feats.append({"type": "Feature", "properties": {"i": i, "n": f["properties"]["NIL"].title().replace(" - ", " - "), "v": int(nv.get(i, 0)),
                  "q": round(100 * float(nv.get(i, 0)) / tv, 2), "np": int(nn.get(i, 0)), "top": luogo.loc[q].nome if q else "", "topv": int(tot[q]) if q else 0},
                  "geometry": {"type": geom.geom_type, "coordinates": rnd(mapping(geom)["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
R["nil_top"] = [{"n": f["properties"]["n"], "v": f["properties"]["v"], "q": f["properties"]["q"], "np": f["properties"]["np"], "top": f["properties"]["top"]}
                for f in sorted(feats, key=lambda f: -f["properties"]["v"])[:8]]
R["nil_top3_quota"] = round(sum(x["q"] for x in R["nil_top"][:3]), 1)
R["nil_fuori"] = int((luogo.id_nil.isna()).sum())
# ---- tabella di tutti i luoghi
rows = []
for q in tot.index:
    r = luogo.loc[q]
    t = int(tot[q])
    rows.append({"qid": q, "nome": r.nome, "categoria": r.categoria, "nil": r.nil if isinstance(r.nil, str) else "", "lat": r.lat, "lon": r.lon, "views_totali": t,
                 **{"views_" + lg: int(byl.loc[q].get(lg, 0)) for lg in LANGS}, "views_altre_lingue": int(byl.loc[q].get("altre", 0)),
                 "quota_italiano_%": round(100 * int(byl.loc[q].get("it", 0)) / t, 1)})
pd.DataFrame(rows).to_csv(os.path.join(OUT, "luoghi.csv"), sep=";", index=False)
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(S, open(os.path.join(OUT, "serie.json"), "w", encoding="utf8"), separators=(",", ":"))
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
print(json.dumps(R["sorpresa"], ensure_ascii=False))
print(json.dumps(R["picchi_non_spiegati"][:4], ensure_ascii=False))
