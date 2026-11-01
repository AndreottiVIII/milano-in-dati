"""Scrive i dati della pagina docs/pietre-inciampo/data/ (solo fatti: nome, anni di nascita e morte, categoria, campo, anno di posa, indirizzo,
coordinate, link alla scheda del Comitato) e i riepiloghi aggregati. Rieseguibile.
Uso: python -I -X utf8 pagina.py <pietre-inciampo_abs> <milano-in-dati_abs>
Legge: pulito/pietre.csv, alberi/pulito/nil_alberi.csv (residenti ds205 2024), NIL ds964 in citta-15-minuti.
Non pubblica: biografie, foto, eta' o sesso delle singole persone (solo conteggi), dati CDEC (usati solo per controllo)."""
import sys, os, json, csv, datetime
import pandas as pd
import shapely
from shapely.geometry import shape, mapping

A, P = sys.argv[1], sys.argv[2]
OUT = os.path.join(P, "docs", "pietre-inciampo", "data")
os.makedirs(OUT, exist_ok=True)
C = pd.read_csv(os.path.join(A, "pulito", "pietre.csv"), sep=";", dtype=str, keep_default_na=False)
for c in ["anno_posa", "id_nil", "eta_arresto", "lon", "lat"]:
    C[c] = pd.to_numeric(C[c], errors="coerce")
D = C[C.solo_wikipedia == "0"].copy()   # persone con scheda del Comitato
LINK = "https://www.pietredinciampomilano.it/?page_id=451&ricerca="
CAT = {"razziale": "razziale", "politica": "politica", "IMI": "IMI"}
CAMP_UNITI = {"Bolzano": "Bolzano e Fossoli", "Fossoli": "Bolzano e Fossoli", "altro": "Altri luoghi o non indicato", "non indicato": "Altri luoghi o non indicato"}

# ---------- elenco delle pietre (fatti)
rec = []
for _, r in C.sort_values(["anno_posa", "nome"]).iterrows():
    sol = r.solo_wikipedia == "1"
    anno_m = r.data_morte[:4] if r.data_morte else ""
    luogo = "" if sol else (r.luogo_morte if r.luogo_morte and r.campo_gruppo in ("altro", "non indicato") else r.campo_gruppo)
    if not sol and r.campo_gruppo in ("altro", "non indicato") and not r.luogo_morte:
        luogo = ""
    rec.append({"id": (int(r.id_scheda) if not sol else None), "nome": r.nome, "nato": (r.anno_nascita or ""), "morto": anno_m,
                "cat": ("altro" if sol else r.categoria), "campo": luogo, "anno": int(r.anno_posa),
                "stato": r.anno_posa_stato, "via": r.indirizzo, "lon": round(float(r.lon), 6), "lat": round(float(r.lat), 6),
                "nil": r.nil, "sg": r.sottogruppo,
                "link": (LINK + str(int(r.id_scheda))) if not sol else ""})
json.dump(rec, open(os.path.join(OUT, "pietre.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(OUT, "pietre.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter=";")
    w.writerow(["nome", "anno_nascita", "anno_morte", "categoria", "luogo_o_campo_di_morte", "anno_posa", "stato_anno_posa", "indirizzo", "lon", "lat", "quartiere_NIL", "scheda_del_Comitato"])
    for x in rec:
        w.writerow([x["nome"], x["nato"], x["morto"], x["cat"], x["campo"], x["anno"], x["stato"], x["via"], x["lon"], x["lat"], x["nil"], x["link"]])

# ---------- riepiloghi aggregati
R = {"aggiornato": datetime.date.today().isoformat(), "scaricato": "2026-11-01"}
R["n_pietre"] = int(len(C)); R["n_schede"] = int(len(D)); R["n_solo_wikipedia"] = int((C.solo_wikipedia == "1").sum())
R["categorie"] = D.categoria.value_counts().to_dict()
# per anno di posa x categoria
yy = C.assign(cat=C.categoria.where(C.solo_wikipedia == "0", "altro")).groupby(["anno_posa", "cat"]).size().unstack(fill_value=0)
R["anni"] = [{"anno": int(a), "razziale": int(r.get("razziale", 0)), "politica": int(r.get("politica", 0)), "IMI": int(r.get("IMI", 0)), "altro": int(r.get("altro", 0))} for a, r in yy.iterrows()]
R["cibeno_2024"] = int(((D.anno_posa == 2024) & D.sottogruppo.str.startswith("strage di Cibeno") & (D.anno_posa_conflitto == "1")).sum())
R["anni_da_verificare"] = D[D.anno_posa_stato.isin(["da verificare"])][["nome", "anno_posa"]].assign(anno_posa=lambda d: d.anno_posa.astype(int)).to_dict("records")
R["anni_risolti"] = int(D.anno_posa_stato.isin(["verificato", "annunciato"]).sum())
# arresti per mese
m = D[D.data_arresto != ""].copy(); m["mese"] = m.data_arresto.str[:7]
mm = m.groupby(["mese", "categoria"]).size().unstack(fill_value=0)
R["mesi"] = [{"mese": k, "razziale": int(r.get("razziale", 0)), "politica": int(r.get("politica", 0)), "IMI": int(r.get("IMI", 0))} for k, r in mm.iterrows()]
R["arresti_noti"] = int(len(m)); R["arresti_ignoti"] = int((D.data_arresto == "").sum())
due = m.mese.isin(["1943-12", "1944-03"])
R["arresti_dic43"] = int((m.mese == "1943-12").sum()); R["arresti_mar44"] = int((m.mese == "1944-03").sum())
R["arresti_due_mesi"] = int(due.sum()); R["arresti_due_mesi_pct"] = round(100 * float(due.mean()), 1)
R["arresti_mar44_politici"] = int(((m.mese == "1944-03") & (m.categoria == "politica")).sum())
R["mar44_sg"] = int(D.sottogruppo.str.startswith("arrestato a marzo 1944").sum())
R["mar44_cita_sciopero"] = int(D.sottogruppo.str.contains("cita lo sciopero").sum())
R["mar44_cibeno"] = int(((m.mese == "1944-03") & (m.categoria == "politica")).sum()) - R["mar44_sg"]
R["anni_diversi_comitato_wikipedia"] = int((D.anno_posa_conflitto == "1").sum())
R["senza"] = {"luogo_nascita": int((D.luogo_nascita == "").sum()), "data_morte": int((D.data_morte == "").sum()), "luogo_arresto": int((D.luogo_arresto == "").sum()), "data_arresto": int((D.data_arresto == "").sum())}
R["schede_con_testo_mancante"] = int(D.note_scheda.str.contains("luogo mancante").sum())
R["arresti_dic43_razziali"] = int(((m.mese == "1943-12") & (m.categoria == "razziale")).sum())
# campi x categoria
D["campo2"] = D.campo_gruppo.map(lambda x: CAMP_UNITI.get(x, x))
cc = D.groupby(["campo2", "categoria"]).size().unstack(fill_value=0)
cc["tot"] = cc.sum(axis=1); cc = cc.sort_values("tot", ascending=False)
altri = "Altri luoghi o non indicato"
order = [i for i in cc.index if i != altri] + ([altri] if altri in cc.index else [])
R["campi"] = [{"campo": k, "razziale": int(cc.loc[k].get("razziale", 0)), "politica": int(cc.loc[k].get("politica", 0)), "IMI": int(cc.loc[k].get("IMI", 0))} for k in order]
# eta' all'arresto (fasce), sesso, nascita: solo conteggi
bins = [0, 18, 30, 40, 50, 60, 70, 120]; lab = ["meno di 18", "18-29", "30-39", "40-49", "50-59", "60-69", "70 e oltre"]
D["fascia"] = pd.cut(D.eta_arresto, bins=bins, labels=lab, right=False)
fa = pd.crosstab(D.fascia, D.categoria)
R["eta"] = [{"fascia": f, "razziale": int(fa.loc[f].get("razziale", 0)), "politica": int(fa.loc[f].get("politica", 0)), "IMI": int(fa.loc[f].get("IMI", 0))} for f in lab]
R["eta_note"] = int(D.eta_arresto.notna().sum()); R["eta_mediana"] = float(D.eta_arresto.median()); R["eta_sotto18"] = int((D.eta_arresto < 18).sum())
sx = pd.crosstab(D.categoria, D.sesso)
R["sesso"] = {k: {"donne": int(sx.loc[k].get("F", 0)), "uomini": int(sx.loc[k].get("M", 0))} for k in sx.index}
R["donne"] = int((D.sesso == "F").sum()); R["uomini"] = int((D.sesso == "M").sum())
nl = D.luogo_nascita.str.lower()
ESTERO = r"siria|egitto|ungheria|bulgaria|cipro|grecia|turchia|ucraina|croazia|francia|crimea|austria|slovacchia|malta|impero austro"
R["nati_noti"] = int((D.luogo_nascita != "").sum()); R["nati_milano"] = int(nl.str.startswith("milano").sum()); R["nati_estero"] = int(nl.str.contains(ESTERO).sum())
R["nati_milano_pct"] = round(100 * R["nati_milano"] / R["nati_noti"])
R["morti_tutte"] = bool((D.esito != "non indicato nella scheda").all())
# indirizzi con piu' pietre
R["indirizzi"] = int(D.indirizzo.nunique())
vc = D.groupby("indirizzo").size()
R["indirizzi_1"] = int((vc == 1).sum()); R["indirizzi_2piu"] = int((vc >= 2).sum())

# ---------- NIL
pop = pd.read_csv(os.path.join(P, "alberi", "pulito", "nil_alberi.csv"), sep=";", dtype=str)
pop["id_nil"] = pd.to_numeric(pop.id_nil); pop["ab"] = pd.to_numeric(pop.abitanti_2024.str.replace(",", "."), errors="coerce")
g = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
cnt = D.groupby(["id_nil", "categoria"]).size().unstack(fill_value=0)
feats = []; tab = []
for f in g["features"]:
    i = int(f["properties"]["ID_NIL"]); nm = f["properties"]["NIL"]
    r = cnt.loc[i] if i in cnt.index else None
    razz = int(r.get("razziale", 0)) if r is not None else 0
    pol = int(r.get("politica", 0)) if r is not None else 0
    imi = int(r.get("IMI", 0)) if r is not None else 0
    n = razz + pol + imi
    ab = pop.loc[pop.id_nil == i, "ab"]; ab = float(ab.iloc[0]) if len(ab) and pd.notna(ab.iloc[0]) else None
    p10 = round(n / ab * 10000, 2) if ab and ab >= 5000 else None
    tab.append({"id": i, "nil": nm, "pietre": n, "razziale": razz, "politica": pol, "IMI": imi, "abitanti": int(ab) if ab else None, "per10mila": p10})
    geom = shapely.simplify(shape(f["geometry"]), 0.00015)
    geom = shapely.set_precision(geom, 0.00001)
    feats.append({"type": "Feature", "properties": tab[-1], "geometry": mapping(geom)})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
T = pd.DataFrame(tab)
R["nil_totale"] = int(len(T)); R["nil_con"] = int((T.pietre > 0).sum()); R["nil_senza"] = int((T.pietre == 0).sum())
R["nil_senza_elenco"] = sorted(T[T.pietre == 0].nil.tolist())
R["nil_poche_ab"] = [{"nil": x["nil"], "pietre": x["pietre"], "abitanti": (None if pd.isna(x["abitanti"]) else int(x["abitanti"]))} for x in T[(T.abitanti.isna()) | (T.abitanti < 5000)].to_dict("records")]
big = T[T.per10mila.notna()].sort_values("per10mila", ascending=False)
R["nil_per10mila_media_citta"] = round(float(D.shape[0] / pop.ab.sum() * 10000), 2)
R["nil_top"] = big.head(5)[["nil", "pietre", "abitanti", "per10mila"]].to_dict("records")
R["nil_assoluto_top"] = T.sort_values("pietre", ascending=False).head(5)[["nil", "pietre"]].to_dict("records")
T.sort_values("pietre", ascending=False).to_csv(os.path.join(OUT, "nil.csv"), sep=";", index=False, encoding="utf-8")
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, allow_nan=False)
print(json.dumps({k: R[k] for k in R if k not in ("nil_senza_elenco", "mesi", "campi", "eta")}, ensure_ascii=False, indent=1))
print(os.listdir(OUT), [os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT)])
