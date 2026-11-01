"""Prepara i dati della pagina docs/statue/ (nessun file di cache, nessun dato grezzo).
Uso: python -I -X utf8 pagina.py <statue> <milano-in-dati>
Legge statue/pulito/*, scrive milano-in-dati/docs/statue/data/ (pagina.json, opere_mappa.json e le copie dei file pubblicabili).
Rilanciabile: sovrascrive tutto in docs/statue/data/. Il file docs/statue/index.html e' scritto a mano e legge pagina.json."""
import sys, os, json, math, shutil, collections
import pandas as pd
S, P = sys.argv[1:3]
O = os.path.join(S, "pulito")
D = os.path.join(P, "docs", "statue", "data")
os.makedirs(D, exist_ok=True)

d = pd.read_csv(os.path.join(O, "opere.csv"), dtype=str).fillna("")
s = pd.read_csv(os.path.join(O, "soggetti.csv"), dtype=str).fillna("")
ctl = json.load(open(os.path.join(O, "controlli.json"), encoding="utf8"))
riep = json.load(open(os.path.join(O, "riepilogo.json"), encoding="utf8"))
st1 = json.load(open(os.path.join(O, "_lavoro/stage1_log.json"), encoding="utf8"))
vie = json.load(open(os.path.join(P, "donne-nelle-vie/out/percentuali.json"), encoding="utf8"))["percentuali"][0]

def wilson(k, n, z=1.96):
    if n == 0: return [None, None]
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]

MON = ["statua", "busto", "monumento", "scultura o installazione", "cippo, stele o pietra", "fontana", "monumento ai caduti"]
PL = "lapide o targa"
d["anno"] = pd.to_numeric(d["anno posa"], errors="coerce")
d["aperto"] = d.collocazione_dedotta.str.startswith("non indicata")
d["persona"] = d.soggetto_tipo.isin(["persona reale", "piu' persone reali"])
n = len(d)
out = {}
out["generato"] = pd.Timestamp.now().strftime("%Y-%m-%d")
out["osm_timestamp"] = st1["osm_timestamp"]
out["n"] = n
out["tipi"] = [[k, int(v)] for k, v in d.tipo.value_counts().items()]
out["mon"] = int(d.tipo.isin(MON).sum()); out["mon_aperto"] = int((d.tipo.isin(MON) & d.aperto).sum())
out["statue_monumenti"] = int(d.tipo.isin(["statua", "busto", "monumento"]).sum())
out["lapidi"] = int((d.tipo == PL).sum())
out["fonti"] = [[k, int(v)] for k, v in d.fonte.value_counts().items()]
out["in_wd"] = int(d.fonte.str.contains("wikidata").sum()); out["in_osm"] = int(d.fonte.str.contains("osm").sum()); out["in_iccd"] = int(d.fonte.str.contains("iccd").sum())
out["in_wd_e_osm"] = int((d.fonte.str.contains("wikidata") & d.fonte.str.contains("osm")).sum())
cov = dict(coord=int((d.lon != "").sum()), anno=int(d.anno.notna().sum()), autore=int((d.autore != "").sum()), persona=int(d.persona.sum()), nome=int((d.nome != "").sum()))
out["copertura"] = {k: [v, round(100 * v / n, 1)] for k, v in cov.items()}
out["soggetto_tipi"] = [[k, int(v)] for k, v in d.soggetto_tipo.value_counts().items()]
out["collocazione"] = [[k, int(v)] for k, v in d.collocazione_dedotta.value_counts().items()]

# ---- persone
sm = s.merge(d[["id", "tipo", "aperto"]], left_on="id_opera", right_on="id")
sm["anno"] = pd.to_numeric(sm.anno_posa, errors="coerce")
sm["morte_n"] = pd.to_numeric(sm.morte, errors="coerce")
def gstat(x, nome):
    u = x.drop_duplicates("qid"); k = u[u.genere.isin(["uomo", "donna"])]
    nd = int((k.genere == "donna").sum()); nn = len(k)
    lo, hi = wilson(nd, nn)
    return dict(nome=nome, donne=nd, persone=nn, quota=round(100 * nd / nn, 1) if nn else None, lo=lo, hi=hi)
G = [gstat(sm, "Tutte le opere"), gstat(sm[sm.tipo.isin(MON)], "Statue, monumenti, sculture"), gstat(sm[sm.tipo.isin(["statua", "busto"])], "Solo statue e busti"), gstat(sm[sm.tipo == PL], "Lapidi e targhe")]
vq = vie["donne_sicure"] / vie["persone_sicure"]
G.append(dict(nome="Vie intitolate a persone", donne=vie["donne_sicure"], persone=vie["persone_sicure"], quota=round(100 * vq, 1), lo=wilson(vie["donne_sicure"], vie["persone_sicure"])[0], hi=wilson(vie["donne_sicure"], vie["persone_sicure"])[1]))
out["genere"] = G
out["quota_vie"] = round(100 * vq, 1)
out["persone_uniche"] = int(sm.qid.nunique())
out["coppie_opera_persona"] = len(sm)
out["come_trovato"] = [[k, int(v)] for k, v in sm.come_trovato.str.replace(r"\s*\(.*\)", "", regex=True).value_counts().items()]
out["opere_persona"] = int(d.persona.sum())
out["persone_mon_aperto"] = gstat(sm[sm.tipo.isin(MON) & sm.aperto], "")

# ---- piu' rappresentati
top = sm.groupby(["qid", "persona", "genere"]).agg(n=("id_opera", "nunique"), tipi=("tipo_opera", lambda x: ", ".join(sorted(set(x))))).reset_index().sort_values(["n", "persona"], ascending=[False, True])
out["top"] = top.head(14)[["persona", "n", "tipi", "genere"]].values.tolist()
out["top_max"] = int(top.n.max()); out["top_con_max"] = top[top.n == top.n.max()].persona.tolist()
vit = sm[sm.persona == "Vittorio Emanuele II di Savoia"]
out["ve2"] = [int(vit.id_opera.nunique()), vit.persona.iloc[0] if len(vit) else "", vit.opera.drop_duplicates().tolist()]
gar = sm[sm.persona == "Giuseppe Garibaldi"]
out["garibaldi"] = [int(gar.id_opera.nunique()), gar.tipo_opera.tolist()]
# figure religiose
mar = d[d.soggetto_tipo.str.startswith("figura")]
out["figure_n"] = int(len(mar))
fig = collections.Counter()
for t in mar.soggetto:
    for x in t.split(" | "): fig[x] += 1
out["figure_top"] = fig.most_common(6)
out["maria_n"] = int(mar.soggetto.str.contains(r"(?:^|\| )Maria(?: \||$)", regex=True).sum())

# ---- professioni
def prof(x):
    g = x.groupby("gruppo_professione").agg(inc=("id_opera", "size"), donne=("genere", lambda z: int((z == "donna").sum()))).sort_values("inc", ascending=False).reset_index()
    return g.values.tolist()
out["prof_mon"] = prof(sm[sm.tipo.isin(MON)]); out["prof_lap"] = prof(sm[sm.tipo == PL])

# ---- tempo
dd = d[d.anno.notna()].copy()
dd["dec"] = (dd.anno // 10 * 10).astype(int)
dec = []
for k in range(int(dd.dec.min()), int(dd.dec.max()) + 1, 10):
    x = dd[dd.dec == k]
    dec.append([k, int(len(x)), int(x.tipo.isin(MON).sum()), int((x.tipo == PL).sum())])
out["decenni"] = dec
out["n_datate"] = int(len(dd))
EP = [("prima del 1861", 0, 1860), ("1861-1921", 1861, 1921), ("1922-1943", 1922, 1943), ("1944-1969", 1944, 1969), ("1970-1999", 1970, 1999), ("dal 2000", 2000, 3000)]
out["epoche"] = [[nm, int(((dd.anno >= a) & (dd.anno <= b)).sum()), int(((dd.anno >= a) & (dd.anno <= b) & dd.tipo.isin(MON)).sum())] for nm, a, b in EP]
# sorpresa: persone nei monumenti datati
sd = sm[sm.tipo.isin(MON) & sm.anno.notna() & sm.genere.isin(["uomo", "donna"])]
pre = sd[sd.anno < 2021]
out["sorpresa"] = dict(persone_datate=int(len(sd)), persone_datate_prima_2021=int(len(pre)), donne_prima_2021=int((pre.genere == "donna").sum()),
                       donne_datate=sd[sd.genere == "donna"][["persona", "opera", "anno"]].assign(anno=lambda z: z.anno.astype(int)).values.tolist())
# anche con statue e monumenti non datati: donne senza anno
undated_w = sm[sm.tipo.isin(MON) & sm.anno.isna() & (sm.genere == "donna")]
out["sorpresa"]["donne_monumenti_senza_anno"] = undated_w[["persona", "opera"]].values.tolist()

# ---- distanza morte-monumento
lg = sm[sm.tipo.isin(MON) & sm.anno.notna() & sm.morte_n.notna()].copy()
lg["lag"] = lg.anno - lg.morte_n
lg = lg[lg.lag > -200]
bins = [("ancora in vita", lg.lag < 0), ("0-10 anni", (lg.lag >= 0) & (lg.lag <= 10)), ("11-30 anni", (lg.lag > 10) & (lg.lag <= 30)), ("31-100 anni", (lg.lag > 30) & (lg.lag <= 100)), ("oltre 100 anni", lg.lag > 100)]
out["lag"] = dict(n=int(len(lg)), mediana=float(lg.lag.median()) if len(lg) else None, bins=[[nm, int(m.sum())] for nm, m in bins],
                  esempi_in_vita=lg[lg.lag < 0][["persona", "opera", "anno"]].assign(anno=lambda z: z.anno.astype(int)).values.tolist())

# ---- donne
w = sm[sm.genere == "donna"].copy()
out["donne_elenco"] = [[r.persona, r.opera, r.tipo_opera, int(r.anno) if not math.isnan(r.anno) else None, r.gruppo_professione, r.NIL, r.collocazione_dedotta, r.come_trovato] for r in w.sort_values("anno").itertuples()]

# ---- lapidi
pl = d[d.tipo == PL]
out["lapidi_info"] = dict(n=int(len(pl)), solo_osm=int((pl.fonte == "osm").sum()), solo_wd=int((pl.fonte == "wikidata").sum()), entrambe=int(pl.fonte.str.contains("osm").mul(pl.fonte.str.contains("wikidata")).sum()),
                          con_persona=int(pl.persona.sum()), senza_nome=int((pl.nome == "").sum()), stima=ctl["sovrapposizione_wikidata_osm"]["lapidi_e_targhe"])
out["overlap"] = ctl["sovrapposizione_wikidata_osm"]

# ---- NIL
nl = pd.read_csv(os.path.join(O, "per_nil.csv"))
out["nil_top"] = nl.sort_values("opere", ascending=False).head(10)[["NIL", "opere", "statue_monumenti_sculture", "lapidi_targhe"]].values.tolist()
out["nil_senza"] = int((nl.opere == 0).sum()); out["nil_tot"] = int(len(nl))
out["nil_duomo_brera"] = int(nl[nl.NIL.isin(["DUOMO", "BRERA"])].opere.sum()); out["nil_opere_tot"] = int(nl.opere.sum())
out["inventario"] = pd.read_csv(os.path.join(O, "inventario_fonti.csv"), dtype=str).fillna("").to_dict("records")
out["conteggi_pulizia"] = dict(wd_trovati=st1["wd_qid_trovati_da_sparql"], wd_tenuti=st1["wd_tenuti"], osm_elementi=st1["osm_elementi"], osm_tenuti=st1["osm_tenuti"],
                              iccd_schede=st1["iccd_schede_milano"], iccd_tipi=st1["iccd_schede_dei_tipi_cercati"], iccd_tenute=st1["iccd_candidati_tenuti"])
out["controlli"] = dict(soggetti_per_nome=ctl["soggetti_trovati_per_nome_da_controllare"], esclusi=int(len(pd.read_csv(os.path.join(S, "scripts/soggetti_esclusi.csv")))))
json.dump(out, open(os.path.join(D, "pagina.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)

# ---- punti della mappa (compatti)
cols = ["id", "nome", "tipo", "lon", "lat", "soggetto", "genere", "gruppo", "anno", "NIL", "fonte", "coll", "stipo"]
pts = [[r["id"], r["nome"], r["tipo"], float(r["lon"]), float(r["lat"]), r["soggetto"], r["genere soggetto"], r["professione"], int(r["anno posa"]) if r["anno posa"] else None, r["NIL"], r["fonte"],
        "" if r["collocazione_dedotta"].startswith("non indicata") else r["collocazione_dedotta"], r["soggetto_tipo"]] for _, r in d[d.lon != ""].iterrows()]
json.dump({"colonne": cols, "punti": pts}, open(os.path.join(D, "opere_mappa.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ---- copie dei file pubblicabili
for f in ["opere.csv", "soggetti.csv", "per_nil.csv", "inventario_fonti.csv", "piu_rappresentati_tutte.csv", "per_decennio.csv"]:
    shutil.copy(os.path.join(O, f), os.path.join(D, f))
shutil.copy(os.path.join(O, "_lavoro/ricerche_soggetti.csv"), os.path.join(D, "controllo_soggetti_per_titolo.csv"))
shutil.copy(os.path.join(O, "_lavoro/iscrizioni_soggetti.csv"), os.path.join(D, "controllo_soggetti_da_iscrizione.csv"))
shutil.copy(os.path.join(S, "scripts/soggetti_esclusi.csv"), os.path.join(D, "soggetti_esclusi_a_mano.csv"))
open(os.path.join(D, "LICENZE.txt"), "w", encoding="utf8").write("""Milano in dati - Statue e monumenti: licenze dei file in questa cartella
Dati scaricati il 1 novembre 2026.

- Dati derivati da OpenStreetMap (nomi, tipi, posizioni, iscrizioni delle lapidi, anni): (c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0.
  Chi riusa o ripubblica questi file deve citare la fonte e distribuire i dati derivati con la stessa licenza (share-alike). https://www.openstreetmap.org/copyright
- Dati derivati dal Catalogo generale dei beni culturali (ICCD, ArCo, schede di Milano): CC BY-SA 4.0 (stessa scelta del filone Beni culturali del progetto). Citare ICCD - Catalogo generale dei beni culturali.
- Dati ricavati da Wikidata: CC0 (pubblico dominio).
- Confini dei NIL e nomi dei quartieri: Comune di Milano, CC BY (dati.comune.milano.it, ds964).
- Il file opere.csv unisce le tre fonti: ha la colonna "fonte" che dice da dove viene ogni riga. Trattatelo come ODbL + CC BY-SA 4.0 (riga per riga, secondo la colonna fonte).
- I programmi e le note sono nel repository del progetto.
""")
print("ok", D, len(pts), "punti")
print(json.dumps({k: out[k] for k in ["n", "mon", "mon_aperto", "copertura", "genere", "top", "sorpresa", "lag", "figure_top", "maria_n", "lapidi_info", "come_trovato"]}, ensure_ascii=False, indent=1, default=str))
