"""Tabella finale delle opere e riepiloghi. Uso: python -I -X utf8 07_opere.py <statue> <milano-in-dati>
Legge pulito/_lavoro/stage3.json (da 06). Scrive pulito/opere.csv, soggetti.csv, riepilogo.json, e i riepiloghi csv."""
import sys, os, re, json, csv, collections, statistics
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape
from pyproj import Transformer
S, P = sys.argv[1:3]
sys.path.insert(0, os.path.join(S, "scripts"))
from wdlib import WD, norm, G, group_of
wd = WD(os.path.join(S, "raw/wikidata/entities_cache.json"))
W = json.load(open(os.path.join(S, "pulito/_lavoro/stage3.json"), encoding="utf8"))
OUT = os.path.join(S, "pulito")
R = {}

# ---------- persone
def person(q):
    labs = [wd.lab(o) for o in wd.ids(q, "P106")]
    g = wd.ids(q, "P21")
    gen = G.get(g[0], "altro") if g else "n.d."
    b = [y for y, p in wd.times(q, "P569")]; d = [y for y, p in wd.times(q, "P570")]
    saint = bool(wd.ids(q, "P411"))
    grp = "religioso o santo" if saint else group_of(labs, wd.desc(q))
    return dict(qid=q, nome=(wd.lab(q) if wd.lab(q) != q or q not in FALLBACK else FALLBACK[q]), genere=gen, nascita=min(b) if b else None, morte=min(d) if d else None, occ=labs, gruppo=grp, santo=saint, desc=wd.desc(q))

FALLBACK = {}  # voci Wikidata senza etichetta: si usa il nome cercato
ESCL = set()
for r_ in csv.DictReader(open(os.path.join(S, "scripts/soggetti_esclusi.csv"), encoding="utf8")):
    ESCL.add((r_["chiave_opera"], r_["qid_persona"]))
rows_s = []; rows = []
for w in W:
    pers = []
    for q in w["subj_persone_struct"]:
        pers.append((q, "collegamento in Wikidata/OSM"))
    nm = w.get("subj_persone_nome")
    if nm and nm["qid"] not in [p[0] for p in pers]:
        pers.append((nm["qid"], "ricerca per nome (" + nm["metodo"] + ")")); FALLBACK[nm["qid"]] = nm["query"]
    isc = w.get("subj_persone_iscrizione")
    if isc and isc["qid"] not in [p[0] for p in pers]:
        pers.append((isc["qid"], "nome scritto nell'iscrizione (" + isc["metodo"] + ")")); FALLBACK[isc["qid"]] = isc["testo"]
    # controllo a mano: coppie opera-persona escluse (omonimi dubbi)
    keys = {w.get("qid")} | set(w.get("osm", []))
    pers = [(q, v) for q, v in pers if not (v.startswith(("ricerca", "nome scritto")) and any((k, q) in ESCL for k in keys if k))]
    w["persone"] = [dict(person(q), via=v) for q, v in pers]
    nonreal = [q for q in w["subj_struct"] if q not in w["subj_persone_struct"] and (wd.nonreal(q) and wd.is_human(q) or "Q4271324" in wd.ids(q, "P31") or "Q178885" in wd.ids(q, "P31") or "Q22988604" in wd.ids(q, "P31")
               or set(wd.ids(q, "P31")) & {"Q20643955", "Q15632617", "Q13002315", "Q95074", "Q146083", "Q2064732"})]
    w["figure"] = [wd.lab(q) for q in nonreal]
    if w["persone"]: st = "persona reale" if len(w["persone"]) == 1 else "piu' persone reali"
    elif w["figure"]: st = "figura religiosa, mitologica o di fantasia"
    elif w["tipo"] == "monumento ai caduti": st = "caduti o evento (collettivo)"
    else: st = "non determinato"
    w["soggetto_tipo"] = st

# ---------- anno / epoca
def epoca(y):
    if y is None: return ""
    if y < 1861: return "1. prima del 1861"
    if y < 1922: return "2. 1861-1921 (Italia liberale)"
    if y < 1944: return "3. 1922-1943 (fascismo)"
    if y < 1970: return "4. 1944-1969 (dopoguerra)"
    if y < 2000: return "5. 1970-1999"
    return "6. dal 2000"
def collocazione_lab(c): return c or "non indicata (probabile spazio aperto)"

for w in W:
    ps = w["persone"]
    w["genere_opera"] = ""
    if ps:
        gs = {p["genere"] for p in ps}
        w["genere_opera"] = "solo donne" if gs == {"donna"} else "solo uomini" if gs == {"uomo"} else "miste o n.d."
    w["epoca"] = epoca(w["anno"])
    fl = []
    if w["anno"] and any(p["nascita"] and w["anno"] < p["nascita"] for p in ps): fl.append("anno_posa_prima_della_nascita")
    if w["anno"] and w["anno"] < 1200: fl.append("anno_posa_molto_antico")
    if w["lon"] is None: fl.append("senza_coordinate")
    if w["nil_stato"] == "entro100m": fl.append("NIL_per_vicinanza")
    if not w["nome"]: fl.append("senza_nome")
    w["flag"] = ";".join(fl)

def nome_opera(w):
    return w["nome"] or (w["qid"] or "") or ""
for w in W:
    ps = w["persone"]
    rows.append({
        "id": w["id"], "nome": nome_opera(w), "tipo": w["tipo"],
        "soggetto": " | ".join(p["nome"] for p in ps) if ps else " | ".join(w["figure"]),
        "soggetto_qid": " | ".join(p["qid"] for p in ps),
        "genere soggetto": " | ".join(p["genere"] for p in ps),
        "professione": " | ".join(p["gruppo"] for p in ps),
        "anno posa": w["anno"] if w["anno"] is not None else "",
        "autore": " | ".join(w["autori"]),
        "lon": round(w["lon"], 6) if w["lon"] is not None else "", "lat": round(w["lat"], 6) if w["lat"] is not None else "",
        "NIL": w["nil"], "fonte": "+".join(w["src"]),
        # colonne in piu'
        "id_nil": w["nil_id"] if w["nil_id"] is not None else "",
        "soggetto_tipo": w["soggetto_tipo"], "soggetto_come_trovato": " | ".join(p["via"] for p in ps),
        "professioni_wikidata": " | ".join(", ".join(p["occ"][:3]) for p in ps),
        "nascita_soggetto": " | ".join(str(p["nascita"] or "") for p in ps), "morte_soggetto": " | ".join(str(p["morte"] or "") for p in ps),
        "epoca_posa": w["epoca"], "collocazione_dedotta": collocazione_lab(w["contesto"]),
        "qid_opera": w["qid"] or "", "osm_id": " ".join(w["osm"]), "iccd_iri": " ".join(w["iccd"]), "anno_fonte": w["anno_fonte"], "anno_nota": w["anno_nota"],
        "tipo_wikidata": " | ".join(w["tipo_wd"]), "flag": w["flag"]})
    for p in ps:
        rows_s.append({"id_opera": w["id"], "opera": nome_opera(w), "tipo_opera": w["tipo"], "qid": p["qid"], "persona": p["nome"], "genere": p["genere"], "nascita": p["nascita"] or "", "morte": p["morte"] or "",
                       "gruppo_professione": p["gruppo"], "professioni_wikidata": ", ".join(p["occ"][:4]), "santo": int(p["santo"]), "come_trovato": p["via"], "anno_posa": w["anno"] or "", "epoca_posa": w["epoca"],
                       "NIL": w["nil"], "collocazione_dedotta": collocazione_lab(w["contesto"]), "descrizione_wikidata": p["desc"]})
df = pd.DataFrame(rows); ds = pd.DataFrame(rows_s)
df.to_csv(os.path.join(OUT, "opere.csv"), index=False, encoding="utf-8-sig")
ds.to_csv(os.path.join(OUT, "soggetti.csv"), index=False, encoding="utf-8-sig")

# ---------- riepiloghi
R["opere_totali"] = len(df)
R["per_fonte"] = df.fonte.value_counts().to_dict()
R["per_tipo"] = df.tipo.value_counts().to_dict()
R["con_coordinate"] = int((df.lon != "").sum()); R["con_NIL"] = int((df.NIL != "").sum())
R["con_anno_posa"] = int((df["anno posa"] != "").sum())
R["con_autore"] = int((df.autore != "").sum())
R["con_persona_reale"] = int(df.soggetto_tipo.isin(["persona reale", "piu' persone reali"]).sum())
R["per_soggetto_tipo"] = df.soggetto_tipo.value_counts().to_dict()
R["collocazione"] = df.collocazione_dedotta.value_counts().to_dict()
fonti_pers = collections.Counter(p["via"] for w in W for p in w["persone"])
R["persone_come_trovate"] = dict(fonti_pers)

# insiemi di lavoro
FUN = "monumento funebre o tomba"
PLAQ = "lapide o targa"
open_ = df.collocazione_dedotta.str.startswith("non indicata")
mon = df[~df.tipo.isin([PLAQ, FUN, "murale o opera decorativa", "altro memoriale"])]           # statue, busti, monumenti, sculture, cippi, fontane, caduti
mon_open = mon[mon.collocazione_dedotta.str.startswith("non indicata")]
pl = df[df.tipo == PLAQ]
R["monumenti_e_statue_totali"] = len(mon); R["monumenti_e_statue_spazio_aperto_probabile"] = len(mon_open)
R["lapidi_e_targhe_totali"] = len(pl)
R["funebri_totali"] = int((df.tipo == FUN).sum())
R["murali_e_opere_decorative"] = int((df.tipo == "murale o opera decorativa").sum())
R["altro_memoriale"] = int((df.tipo == "altro memoriale").sum())

sub = ds.merge(df[["id", "tipo"]], left_on="id_opera", right_on="id")
def gender_stats(d, label):
    """d: righe di soggetti.csv (una per opera-persona). quote su incidenze e su persone uniche"""
    out = {}
    n = len(d); out["incidenze"] = n
    c = d.genere.value_counts().to_dict(); out["per_genere"] = c
    known = d[d.genere.isin(["uomo", "donna"])]
    out["quota_donne_su_incidenze_note"] = round((known.genere == "donna").mean(), 4) if len(known) else None
    u = d.drop_duplicates("qid"); ku = u[u.genere.isin(["uomo", "donna"])]
    out["persone_uniche"] = len(u); out["donne_uniche"] = int((u.genere == "donna").sum()); out["uomini_unici"] = int((u.genere == "uomo").sum())
    out["quota_donne_su_persone_uniche"] = round((ku.genere == "donna").mean(), 4) if len(ku) else None
    ws = d.groupby("id_opera").genere.apply(lambda s: "donna" if (s == "donna").any() else "uomo" if (s == "uomo").any() else "nd")
    out["opere_con_persone"] = len(ws); out["opere_con_almeno_una_donna"] = int((ws == "donna").sum())
    out["quota_opere_con_donna"] = round((ws == "donna").mean(), 4) if len(ws) else None
    return out
G_all = {}
sets = {
    "tutte_le_opere": sub,
    "statue_monumenti_sculture": sub[sub.tipo.isin(mon.tipo.unique())],
    "statue_monumenti_sculture_spazio_aperto": sub[sub.tipo.isin(mon.tipo.unique()) & sub.collocazione_dedotta.str.startswith("non indicata")],
    "solo_statue_e_busti": sub[sub.tipo.isin(["statua", "busto"])],
    "lapidi_e_targhe": sub[sub.tipo == PLAQ],
    "funebri": sub[sub.tipo == FUN],
}
for k, v in sets.items():
    G_all[k] = gender_stats(v, k)
    G_all[k + "__senza_santi"] = gender_stats(v[v.santo == 0], k)
    G_all[k + "__solo_collegate_in_wikidata_osm"] = gender_stats(v[v.come_trovato.str.startswith("collegamento")], k)
R["genere"] = G_all
# confronto con le vie
pct = json.load(open(os.path.join(P, "donne-nelle-vie/out/percentuali.json"), encoding="utf8"))
R["confronto_vie"] = {"fonte": "donne-nelle-vie/out/percentuali.json, scope 'con santi', quota_donne_su_persone_ferma", "quota_donne_vie_su_persone": pct["percentuali"][0]["quota_donne_su_persone_ferma"],
                      "donne_sicure": pct["percentuali"][0]["donne_sicure"], "persone_sicure": pct["percentuali"][0]["persone_sicure"],
                      "senza_santi": pct["percentuali"][1]["quota_donne_su_persone_ferma"]}

# piu' rappresentati
def top(d, n=20):
    g = d.groupby(["qid", "persona", "genere", "gruppo_professione"]).agg(opere=("id_opera", "nunique"), tipi=("tipo_opera", lambda s: ", ".join(sorted(set(s))))).reset_index().sort_values(["opere", "persona"], ascending=[False, True])
    return g.head(n)
top(sub, 40).to_csv(os.path.join(OUT, "piu_rappresentati_tutte.csv"), index=False, encoding="utf-8-sig")
top(sets["statue_monumenti_sculture"], 40).to_csv(os.path.join(OUT, "piu_rappresentati_monumenti.csv"), index=False, encoding="utf-8-sig")
top(sets["lapidi_e_targhe"], 40).to_csv(os.path.join(OUT, "piu_rappresentati_lapidi.csv"), index=False, encoding="utf-8-sig")
top(sub[sub.genere == "donna"], 40).to_csv(os.path.join(OUT, "donne_rappresentate.csv"), index=False, encoding="utf-8-sig")
R["top10_monumenti"] = top(sets["statue_monumenti_sculture"], 10)[["persona", "opere"]].values.tolist()
R["top10_tutte"] = top(sub, 10)[["persona", "opere"]].values.tolist()
R["top10_lapidi"] = top(sets["lapidi_e_targhe"], 10)[["persona", "opere"]].values.tolist()

# professioni
def prof(d):
    return d.groupby("gruppo_professione").agg(incidenze=("id_opera", "size"), persone_uniche=("qid", "nunique"), donne=("genere", lambda s: int((s == "donna").sum()))).sort_values("incidenze", ascending=False).reset_index()
prof(sets["statue_monumenti_sculture"]).to_csv(os.path.join(OUT, "professioni_monumenti.csv"), index=False, encoding="utf-8-sig")
prof(sets["lapidi_e_targhe"]).to_csv(os.path.join(OUT, "professioni_lapidi.csv"), index=False, encoding="utf-8-sig")
prof(sub).to_csv(os.path.join(OUT, "professioni_tutte.csv"), index=False, encoding="utf-8-sig")
R["professioni_monumenti"] = prof(sets["statue_monumenti_sculture"]).values.tolist()
R["professioni_lapidi"] = prof(sets["lapidi_e_targhe"]).values.tolist()

# epoche
dfa = df[df["anno posa"] != ""].copy(); dfa["anno"] = dfa["anno posa"].astype(int)
R["opere_con_anno"] = len(dfa)
ep = dfa.groupby("epoca_posa").size().to_dict(); R["opere_per_epoca"] = ep
dm = dfa[dfa.tipo.isin(mon.tipo.unique())]
R["monumenti_per_epoca"] = dm.groupby("epoca_posa").size().to_dict()
dec = dfa.assign(decennio=(dfa.anno // 10 * 10)).groupby("decennio").agg(opere=("id", "size")).reset_index()
dec_m = dm.assign(decennio=(dm.anno // 10 * 10)).groupby("decennio").size().rename("statue_monumenti_sculture").reset_index()
dec_p = dfa[dfa.tipo == PLAQ].assign(decennio=lambda d: d.anno // 10 * 10).groupby("decennio").size().rename("lapidi_targhe").reset_index()
dec = dec.merge(dec_m, how="left").merge(dec_p, how="left").fillna(0)
dec.to_csv(os.path.join(OUT, "per_decennio.csv"), index=False, encoding="utf-8-sig")
# epoca x genere/professione sui soggetti
sa = sub[sub.anno_posa != ""].copy(); sa["anno_posa"] = sa.anno_posa.astype(int)
sa_m = sa[sa.tipo.isin(mon.tipo.unique())]
R["donne_per_epoca_monumenti"] = sa_m.groupby("epoca_posa").genere.apply(lambda s: [int((s == "donna").sum()), int(len(s))]).to_dict()
R["donne_per_epoca_tutte"] = sa.groupby("epoca_posa").genere.apply(lambda s: [int((s == "donna").sum()), int(len(s))]).to_dict()
R["professioni_per_epoca_monumenti"] = sa_m.groupby(["epoca_posa", "gruppo_professione"]).size().unstack(fill_value=0).to_dict("index")
sa_m.groupby(["epoca_posa", "gruppo_professione"]).size().unstack(fill_value=0).to_csv(os.path.join(OUT, "epoca_per_professione_monumenti.csv"), encoding="utf-8-sig")
dmo = dfa[dfa.tipo.isin(mon.tipo.unique()) & dfa.collocazione_dedotta.str.startswith("non indicata")]
R["monumenti_spazio_aperto_per_epoca"] = dmo.groupby("epoca_posa").size().to_dict()
R["monumenti_spazio_aperto_con_anno"] = len(dmo); R["monumenti_spazio_aperto_totale"] = len(mon_open)
smo = sa[sa.tipo.isin(mon.tipo.unique()) & sa.collocazione_dedotta.str.startswith("non indicata")]
R["donne_per_epoca_monumenti_spazio_aperto"] = smo.groupby("epoca_posa").genere.apply(lambda s: [int((s == "donna").sum()), int(len(s))]).to_dict()
R["donne_nei_monumenti_con_anno"] = sa_m[sa_m.genere == "donna"][["persona", "opera", "anno_posa", "tipo", "collocazione_dedotta"]].values.tolist()
fig = collections.Counter(f for w in W for f in w["figure"])
R["figure_religiose_mitologiche"] = fig.most_common(20)
R["opere_con_figura_religiosa_o_mitologica"] = int((df.soggetto_tipo.str.startswith("figura")).sum())
# distanza posa - morte
sd = sa[(sa.morte != "")].copy(); sd["lag"] = sd.anno_posa - sd.morte.astype(int)
smon = sd[sd.tipo.isin(mon.tipo.unique()) & (sd.lag > -200)]
R["lag_posa_meno_morte_monumenti"] = dict(n=len(smon), mediana=float(smon.lag.median()) if len(smon) else None, quota_in_vita=round(float((smon.lag < 0).mean()), 3) if len(smon) else None,
                                         entro_30_anni_dalla_morte=round(float(((smon.lag >= 0) & (smon.lag <= 30)).mean()), 3) if len(smon) else None, piu_di_100_anni=round(float((smon.lag > 100).mean()), 3) if len(smon) else None)
R["lag_per_epoca_mediana"] = smon.groupby("epoca_posa").lag.median().to_dict()
R["persone_ancora_in_vita_alla_posa_esempi"] = smon[smon.lag < 0][["persona", "opera", "anno_posa", "morte"]].head(10).values.tolist()
# autori
aut = df[df.autore != ""].assign(a=lambda d: d.autore.str.split(" \\| ")).explode("a")
R["top_autori"] = aut.groupby("a").size().sort_values(ascending=False).head(15).to_dict()
R["autori_donne"] = []
auth_q = collections.Counter()
for w in W:
    for q in w["autori_qid"]:
        auth_q[(q, wd.lab(q))] += 1
ga = [(wd.lab(q), n, G.get((wd.ids(q, "P21") or [""])[0], "n.d.")) for (q, _), n in auth_q.items()]
R["autori_con_qid_per_genere"] = dict(collections.Counter(g for _, n, g in ga for _ in range(n)))
R["autori_donne"] = [(a, n) for a, n, g in ga if g == "donna"]

# ---------- NIL
g = json.load(open(os.path.join(P, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf-8"))
tr = Transformer.from_crs(4326, 32632, always_xy=True)
nilinfo = {}
for f in g["features"]:
    pg = shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
    nilinfo[int(f["properties"]["ID_NIL"])] = (f["properties"]["NIL"], pg.area / 1e6)
dn = df[df.id_nil != ""].copy(); dn["id_nil"] = dn.id_nil.astype(int)
dn["_mon"] = dn.tipo.isin(mon.tipo.unique()); dn["_pl"] = dn.tipo == PLAQ; dn["_aperto"] = dn.collocazione_dedotta.str.startswith("non indicata")
sn = sub[sub.NIL != ""]
nil_rows = []
for i, (nm, ar) in sorted(nilinfo.items()):
    d = dn[dn.id_nil == i]
    s_ = sn[(sn.NIL == nm)]
    nil_rows.append(dict(id_nil=i, NIL=nm, area_kmq=round(ar, 2), opere=len(d), statue_monumenti_sculture=int(d._mon.sum()), lapidi_targhe=int(d._pl.sum()), murali=int((d.tipo == "murale o opera decorativa").sum()),
                         persone_reali=int(len(s_)), donne=int((s_.genere == "donna").sum()), opere_per_kmq=round(len(d) / ar, 2)))
pd.DataFrame(nil_rows).sort_values("opere", ascending=False).to_csv(os.path.join(OUT, "per_nil.csv"), index=False, encoding="utf-8-sig")
R["nil_top10"] = [(r["NIL"], r["opere"]) for r in sorted(nil_rows, key=lambda r: -r["opere"])[:10]]
R["nil_senza_opere"] = sum(1 for r in nil_rows if r["opere"] == 0)
R["nil_con_opere"] = sum(1 for r in nil_rows if r["opere"] > 0)
R["nil_totale"] = len(nil_rows)
R["opere_in_NIL_Duomo"] = next((r["opere"] for r in nil_rows if r["NIL"] == "DUOMO"), None)

# ---------- per tipo x fonte
pd.crosstab(df.tipo, df.fonte).to_csv(os.path.join(OUT, "tipo_per_fonte.csv"), encoding="utf-8-sig")
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
