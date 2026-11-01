"""Riepiloghi sulle pietre d'inciampo di Milano (solo luoghi, anni, categorie: mai classifiche di persone).
Uso: python -I -X utf8 analisi.py <pietre-inciampo_abs> <milano-in-dati_abs>"""
import sys, os, re, json, unicodedata
import numpy as np, pandas as pd

A, P = sys.argv[1], sys.argv[2]
pul = os.path.join(A, "pulito")
C = pd.read_csv(os.path.join(pul, "pietre.csv"), sep=";", keep_default_na=False, dtype=str)
for c in ["anno_posa", "anno_posa_comitato", "id_nil", "eta_arresto", "eta_morte", "lon", "lat"]:
    C[c] = pd.to_numeric(C[c], errors="coerce")
R = {}
D = C[C.solo_wikipedia == "0"].copy()          # le 262 persone con scheda del Comitato
R["pietre_totali"] = int(len(C)); R["pietre_con_scheda_comitato"] = int(len(D)); R["pietre_solo_wikipedia"] = int((C.solo_wikipedia == "1").sum())


def save(df, name):
    df.to_csv(os.path.join(pul, name), sep=";", index=False, encoding="utf-8")


# 1. per anno di posa (tutte le 265) e per categoria
y = C.groupby("anno_posa").size().rename("pietre").reset_index()
y["cumulato"] = y.pietre.cumsum(); save(y, "riep_anno_posa.csv"); R["per_anno_posa"] = dict(zip(y.anno_posa.astype(int).astype(str), y.pietre.astype(int)))
R["per_anno_posa_solo_comitato"] = D.groupby("anno_posa").size().astype(int).rename(index=str).to_dict()
yc = D.pivot_table(index="anno_posa", columns="categoria", values="nome", aggfunc="count", fill_value=0).reset_index(); save(yc, "riep_anno_categoria.csv")
R["anno_x_categoria"] = yc.astype(int).to_dict("records")
# 2. categoria / sottogruppo
R["categoria"] = D.categoria.value_counts().to_dict()
D["sg"] = D.sottogruppo.str.replace(" - la scheda cita lo sciopero", "", regex=False)
R["sottogruppo"] = D.sg.replace("", "(nessuno)").value_counts().to_dict()
R["marzo1944_scheda_cita_sciopero"] = int(D.sottogruppo.str.contains("cita lo sciopero").sum())
R["categoria_x_sottogruppo"] = D.groupby(["categoria", D.sg.replace("", "(nessuno)")]).size().rename("n").reset_index().to_dict("records")
# 3. esito / campo
R["esito"] = D.esito.value_counts().to_dict()
R["campo_gruppo"] = D.campo_gruppo.value_counts().to_dict()
save(pd.crosstab(D.campo_gruppo, D.categoria).reset_index(), "riep_campo_categoria.csv")
R["campo_x_categoria"] = pd.crosstab(D.campo_gruppo, D.categoria).to_dict("index")
D["anno_morte"] = D.data_morte.str[:4]
R["anno_morte"] = D[D.anno_morte != ""].anno_morte.value_counts().sort_index().to_dict(); R["senza_data_morte"] = int((D.data_morte == "").sum())
D["anno_arresto"] = D.data_arresto.str[:7]
R["mese_arresto_top"] = D[D.anno_arresto != ""].anno_arresto.value_counts().head(8).to_dict(); R["senza_data_arresto"] = int((D.data_arresto == "").sum())
# luogo di arresto: Milano o no (per categoria)
D["arresto_milano"] = D.luogo_arresto.str.lower().str.contains("milano")
R["arresto_a_milano"] = {"si": int(D.arresto_milano.sum()), "no_o_ignoto": int((~D.arresto_milano).sum())}
R["arresto_milano_per_categoria"] = D.groupby("categoria").arresto_milano.agg(["sum", "count"]).astype(int).to_dict("index")
ma = D[(D.categoria == "politica") & D.data_arresto.between("1944-03-01", "1944-03-31")]
R["politica_arrestati_marzo_1944_(data)"] = int(len(ma))
R["politica_arrestati_marzo_1944_e_mauthausen"] = int(ma.campo_gruppo.str.startswith("Mauthausen").sum())
R["arresti_dic43_mar44_su_noti"] = {"dic1943+mar1944": int(D.data_arresto.str[:7].isin(["1943-12", "1944-03"]).sum()), "noti": int((D.data_arresto != "").sum())}
# 4. età
for col, nm in [("eta_arresto", "eta_arresto"), ("eta_morte", "eta_morte")]:
    s = D[col].dropna()
    R[nm] = {"n": int(len(s)), "mediana": float(s.median()), "media": round(float(s.mean()), 1), "sotto_18": int((s < 18).sum()), "sotto_30": int((s < 30).sum()), "da_60": int((s >= 60).sum()),
             "per_categoria_mediana": D.groupby("categoria")[col].median().to_dict()}
bins = [0, 18, 30, 40, 50, 60, 70, 120]; lab = ["0-17", "18-29", "30-39", "40-49", "50-59", "60-69", "70+"]
D["fascia_arresto"] = pd.cut(D.eta_arresto, bins=bins, labels=lab, right=False)
fa = pd.crosstab(D.fascia_arresto, D.categoria); save(fa.reset_index(), "riep_eta_arresto.csv"); R["fasce_eta_arresto"] = fa.to_dict("index")
# 5. genere
R["sesso"] = D.sesso.value_counts().to_dict(); R["sesso_per_categoria"] = pd.crosstab(D.categoria, D.sesso).to_dict("index")
R["sesso_per_anno"] = pd.crosstab(D.anno_posa, D.sesso).astype(int).rename(index=lambda x: str(int(x))).to_dict("index")
# 6. luogo di nascita
D["nato_milano"] = D.luogo_nascita.str.lower().str.startswith("milano")
R["nati_a_milano"] = {"si": int(D.nato_milano.sum()), "no": int((~D.nato_milano & (D.luogo_nascita != "")).sum()), "ignoto": int((D.luogo_nascita == "").sum())}
R["nati_a_milano_per_categoria"] = D[D.luogo_nascita != ""].groupby("categoria").nato_milano.agg(["sum", "count"]).astype(int).to_dict("index")
ESTERO = r"siria|egitto|ungheria|bulgaria|cipro|grecia|turchia|ucraina|croazia|francia|crimea|austria|slovacchia|malta|impero austro"
D["nato_estero"] = D.luogo_nascita.str.lower().str.contains(ESTERO)
R["nati_estero"] = {"n": int(D.nato_estero.sum()), "su_luogo_noto": int((D.luogo_nascita != "").sum()), "per_categoria": D.groupby("categoria").nato_estero.sum().astype(int).to_dict()}
R["luoghi_nascita_top"] = D.luogo_nascita.value_counts().head(12).to_dict()
# 7. NIL
pop = pd.read_csv(os.path.join(P, "alberi", "pulito", "nil_alberi.csv"), sep=";", dtype=str)
R["nil_alberi_colonne"] = pop.columns.tolist()
nil = D.groupby(["id_nil", "nil"]).size().rename("pietre").reset_index()
pc = [c for c in pop.columns if "abitanti" in c.lower() or "popolazione" in c.lower()]
if pc:
    pop["abitanti"] = pd.to_numeric(pop[pc[0]].str.replace(",", "."), errors="coerce")
    idc = [c for c in pop.columns if c.lower() in ("id_nil", "idnil")][0]
    pop["id_nil"] = pd.to_numeric(pop[idc], errors="coerce")
    nil = nil.merge(pop[["id_nil", "abitanti"]].drop_duplicates("id_nil"), on="id_nil", how="outer")
    nil["pietre"] = nil.pietre.fillna(0).astype(int)
    nil["per_10mila_ab"] = (nil.pietre / nil.abitanti * 10000).round(2)
bc = pd.crosstab(D.nil, D.categoria)
nil = nil.merge(bc.reset_index().rename(columns={"index": "nil"}), on="nil", how="left").fillna({"politica": 0, "razziale": 0, "IMI": 0})
nil = nil.sort_values("pietre", ascending=False); save(nil, "riep_nil.csv")
R["nil_con_pietre"] = int((nil.pietre > 0).sum()); R["nil_senza_pietre"] = int((nil.pietre == 0).sum())
R["nil_top10_per_numero_assoluto"] = nil.head(10)[["nil", "pietre"]].to_dict("records")
if "per_10mila_ab" in nil:
    big = nil[nil.abitanti > 3000].sort_values("per_10mila_ab", ascending=False)
    R["nil_top10_per_10mila_ab_(abitanti>3000)"] = big.head(10)[["nil", "pietre", "abitanti", "per_10mila_ab"]].to_dict("records")
cat_nil = {}
for cat in ["razziale", "politica"]:
    s = D[D.categoria == cat].groupby("nil").size().sort_values(ascending=False)
    cat_nil[cat] = {"nil_con_pietre": int(len(s)), "top5": s.head(5).to_dict(), "quota_nei_primi_5": round(float(s.head(5).sum() / s.sum()), 3)}
R["nil_per_categoria"] = cat_nil
# distanza dal Duomo per categoria (mediana, km): dove abitavano i deportati
dl = (D.lon - 9.1900) * 111.32 * np.cos(np.radians(45.464)); dla = (D.lat - 45.4642) * 110.57
D["km_duomo"] = np.sqrt(dl ** 2 + dla ** 2)
R["km_dal_duomo_mediana_per_categoria"] = D.groupby("categoria").km_duomo.median().round(2).to_dict()
R["km_dal_duomo_mediana"] = round(float(D.km_duomo.median()), 2)
R["entro_2km_dal_duomo"] = int((D.km_duomo <= 2).sum())
# 8. vie
def via_key(a):
    a = re.sub(r"\s+", " ", a.strip().strip(".").lower().replace("’", "'"))
    a = re.sub(r"\s*(angolo|ang\.).*$", "", a)
    a = re.sub(r"[,\s]+\d+\s*[a-z]?(/\s*[a-z0-9]+)?\s*$", "", a)
    return a


D["via"] = D.indirizzo.map(via_key)
v = D.groupby("via").size().sort_values(ascending=False)
R["vie_con_pietre"] = int(len(v)); R["vie_con_piu_pietre_top10"] = v.head(10).to_dict()
ind = D.groupby("indirizzo").size().sort_values(ascending=False); R["indirizzi_con_piu_pietre_top8"] = ind.head(8).to_dict()
R["indirizzi_distinti"] = int(D.indirizzo.nunique())
save(v.rename("pietre").reset_index(), "riep_vie.csv")
# 9. richiedenti
R["richiesta_da_top"] = D[D.richiesta_da != ""].richiesta_da.value_counts().head(8).to_dict(); R["richiesta_da_compilata"] = int((D.richiesta_da != "").sum())
# 10. qualita'
R["qualita"] = {"senza_data_nascita": int((D.data_nascita == "").sum()), "senza_luogo_nascita": int((D.luogo_nascita == "").sum()), "senza_luogo_arresto": int((D.luogo_arresto == "").sum()),
                "senza_data_arresto": int((D.data_arresto == "").sum()), "senza_data_morte": int((D.data_morte == "").sum()), "senza_luogo_morte": int((D.luogo_morte == "").sum()),
                "con_note_scheda": int((D.note_scheda != "").sum()), "civico_non_abbinato": int((D.civico_stato.str.startswith(("via non", "civico non", "indirizzo non"))).sum()),
                "dist_comitato_civico_oltre_100m": int((pd.to_numeric(D.dist_civico_m, errors="coerce") > 100).sum())}
json.dump(R, open(os.path.join(pul, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
