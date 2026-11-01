"""Scrive i file dati della pagina "Turisti per nazionalita'" (docs/turisti/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <turisti_dir> <docs_dir>

Legge (fase 1, tabelle pulite in <turisti_dir>/pulito/): annuale_paese.csv, annuale_paese_tipo.csv, mensile_paese.csv,
bdi_milano_paese_anno.csv.
Scrive in <docs_dir>/turisti/data/:
  dati.json            tutti i numeri della pagina (serie, paesi, mesi, Expo, Banca d'Italia, controlli)
  serie_totale.csv     anno, serie (vecchia 2000-2004 / nuova 2005-2025), arrivi e presenze: totale, italiani, stranieri
  paesi_anno.csv       anno, paese, arrivi, presenze, permanenza media (comune di Milano, 2005-2025)
  paesi_tipo.csv       anno, paese, tipo struttura (alberghiero / extra-alberghiero), arrivi e presenze (2008-2025)
  mensile_paese.csv    anno, mese, paese, arrivi, presenze (comune di Milano, 2015-2025)
  spesa_bdi.csv        anno, interviste, viaggiatori, notti, spesa (solo totale per il comune, Banca d'Italia)
Scelte (coordinatore): solo il comune di Milano (Comune di Milano, CC BY); niente provincia; serie nuova dal 2005, vecchia solo 2000-2004;
Banca d'Italia: solo il totale per la citta', mai la classifica tra paesi.
"""
import sys, os, json, csv
import pandas as pd

T, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(T, "pulito")
OUT = os.path.join(DOCS, "turisti", "data")
os.makedirs(OUT, exist_ok=True)

a = pd.read_csv(os.path.join(PU, "annuale_paese.csv"))
tipo = pd.read_csv(os.path.join(PU, "annuale_paese_tipo.csv"))
mens = pd.read_csv(os.path.join(PU, "mensile_paese.csv"))
bdi = pd.read_csv(os.path.join(PU, "bdi_milano_paese_anno.csv"))

AVVISI = []
def check(nome, calc, atteso, tol=0):
    if abs(calc - atteso) > tol:
        AVVISI.append(f"{nome}: calcolato {calc} atteso {atteso}")
def num(x):
    return None if pd.isna(x) else int(round(float(x)))

# ------------------------------------------------------------------ serie totale
tot = a.groupby("anno")[["arrivi", "presenze"]].sum()
it = a[a.paese == "Italia"].set_index("anno")[["arrivi", "presenze"]]
serie = []
for y in range(2000, 2026):
    ser = "vecchia" if y <= 2004 else "nuova"
    serie.append({"a": y, "s": ser, "pt": num(tot.loc[y, "presenze"]), "at": num(tot.loc[y, "arrivi"]),
                  "pi": num(it.loc[y, "presenze"]), "ai": num(it.loc[y, "arrivi"]),
                  "ps": num(tot.loc[y, "presenze"] - it.loc[y, "presenze"]), "as": num(tot.loc[y, "arrivi"] - it.loc[y, "arrivi"])})
S = {r["a"]: r for r in serie}
check("notti 2019", S[2019]["pt"], 12946065); check("notti 2025", S[2025]["pt"], 17748326)
check("notti italiani 2019", S[2019]["pi"], 4478745); check("notti italiani 2025", S[2025]["pi"], 3905864)
pd.DataFrame([{"anno": r["a"], "serie": r["s"], "arrivi_totale": r["at"], "presenze_totale": r["pt"], "arrivi_italiani": r["ai"], "presenze_italiani": r["pi"],
               "arrivi_stranieri": r["as"], "presenze_stranieri": r["ps"]} for r in serie]).to_csv(os.path.join(OUT, "serie_totale.csv"), index=False, encoding="utf-8")

# ------------------------------------------------------------------ paesi (serie nuova 2005-2025)
an = a[a.anno >= 2005].copy()
def gruppo(p):
    return p.startswith("Altri") or p.startswith("Paesi dell'")
anni = list(range(2005, 2026))
tp = tipo.pivot_table(index=["paese", "anno"], columns="tipo_struttura", values=["arrivi", "presenze"])
paesi = {}
for p, d in an.groupby("paese"):
    d = d.set_index("anno")
    if d.presenze.dropna().empty: continue
    if p == "Altri Paesi" or p == "Altri Paesi Extraeuropei" or p == "Altri Paesi Europei (Non Ue)": continue  # voci vuote o troppo piccole
    rec = {"g": 1 if gruppo(p) else 0,
           "ar": [num(d.arrivi.get(y)) for y in anni], "pr": [num(d.presenze.get(y)) for y in anni],
           "pa": [], "pe": []}
    for y in anni:
        k = (p, y)
        if y >= 2008 and k in tp.index:
            rec["pa"].append(num(tp.loc[k, ("presenze", "alberghiero")])); rec["pe"].append(num(tp.loc[k, ("presenze", "extra-alberghiero")]))
        else:
            rec["pa"].append(None); rec["pe"].append(None)
    paesi[p] = rec
# solo voci con dati nel 2025
paesi = {p: r for p, r in paesi.items() if r["pr"][-1]}
check("Italia in lista", 1 if "Italia" in paesi else 0, 1)
out = []
for p, r in paesi.items():
    for i, y in enumerate(anni):
        if r["pr"][i] is None: continue
        out.append({"anno": y, "paese": p, "gruppo_di_paesi": r["g"], "arrivi": r["ar"][i], "presenze": r["pr"][i],
                    "permanenza_media": round(r["pr"][i] / r["ar"][i], 2) if r["ar"][i] else None})
pd.DataFrame(out).to_csv(os.path.join(OUT, "paesi_anno.csv"), index=False, encoding="utf-8")
t2 = tipo[tipo.tipo_struttura != "totale"].copy()
t2 = t2[t2.paese.isin(paesi.keys())]
t2.to_csv(os.path.join(OUT, "paesi_tipo.csv"), index=False, encoding="utf-8")

# ------------------------------------------------------------------ albergo / extra totale
tt = tipo[tipo.paese.isin(paesi.keys())].pivot_table(index="anno", columns="tipo_struttura", values="presenze", aggfunc="sum")
# totale vero = somma su tutti i paesi della tabella tipo (anche quelli esclusi dalla lista)
tt_all = tipo.pivot_table(index="anno", columns="tipo_struttura", values="presenze", aggfunc="sum")
ti = tipo[tipo.paese == "Italia"].pivot_table(index="anno", columns="tipo_struttura", values="presenze")
tipo_tot = [{"a": int(y), "alb": num(tt_all.loc[y, "alberghiero"]), "ext": num(tt_all.loc[y, "extra-alberghiero"]),
             "ialb": num(ti.loc[y, "alberghiero"]), "iext": num(ti.loc[y, "extra-alberghiero"])} for y in tt_all.index]
check("extra 2025", tipo_tot[-1]["ext"], 8332433); check("extra 2019", [r for r in tipo_tot if r["a"] == 2019][0]["ext"], 2882369)

# ------------------------------------------------------------------ mensile
mens = mens[mens.paese.isin(paesi.keys())]
mn = {}
for p, d in mens.groupby("paese"):
    mn[p] = {}
    for y, dd in d.groupby("anno"):
        v = [None] * 12
        for _, r in dd.iterrows(): v[int(r.mese) - 1] = num(r.presenze)
        mn[p][int(y)] = v
mens.to_csv(os.path.join(OUT, "mensile_paese.csv"), index=False, encoding="utf-8")
# totale mensile (tutti i paesi della fonte, anche voci non in lista)
m_all = pd.read_csv(os.path.join(PU, "mensile_paese.csv"))
mt = m_all.groupby(["anno", "mese"]).presenze.sum()
mtot = {int(y): [num(mt.loc[(y, m)]) for m in range(1, 13)] for y in sorted(set(m_all.anno))}
check("somma mesi 2019", sum(mtot[2019]), 12946065); check("somma mesi 2025", sum(mtot[2025]), 17748326)

# ------------------------------------------------------------------ Expo
e15 = m_all[(m_all.anno == 2015) & m_all.mese.between(5, 10)].groupby("paese").presenze.sum()
e16 = m_all[(m_all.anno == 2016) & m_all.mese.between(5, 10)].groupby("paese").presenze.sum()
ex = pd.DataFrame({"a": e15, "b": e16}).dropna()
ex = ex[~ex.index.map(gruppo)]
ex["d"] = ex.a - ex.b; ex["p"] = 100 * ex.d / ex.b
exl = [{"paese": p, "m2015": num(r.a), "m2016": num(r.b), "pct": round(float(r.p), 1)} for p, r in ex.sort_values("d", ascending=False).head(8).iterrows()]
expo = {"mesi": {"2015": mtot[2015], "2016": mtot[2016], "2019": mtot[2019]},
        "mag_ott_2015": sum(mtot[2015][4:10]), "mag_ott_2016": sum(mtot[2016][4:10]),
        "altri_2015": sum(mtot[2015][:4]) + sum(mtot[2015][10:]), "altri_2016": sum(mtot[2016][:4]) + sum(mtot[2016][10:]),
        "annuo": {"2014": S[2014]["pt"] if 2014 in S else None, "2015": S[2015]["pt"], "2016": S[2016]["pt"]},
        "paesi": exl}
check("mag-ott 2015", expo["mag_ott_2015"], 6745341); check("mag-ott 2016", expo["mag_ott_2016"], 5753927)

# ------------------------------------------------------------------ Banca d'Italia: solo il totale della citta'
b = bdi[bdi.ambito == "comune_milano"].groupby("anno")[["interviste", "viaggiatori", "notti", "spesa_euro"]].sum()
bi = bdi[bdi.ambito == "italia"].groupby("anno").spesa_euro.sum()
spesa = [{"a": int(y), "n": int(r.interviste), "v": round(r.viaggiatori / 1e6, 2), "no": round(r.notti / 1e6, 1), "s": round(r.spesa_euro / 1e6),
          "q": round(100 * r.spesa_euro / bi.loc[y], 1)} for y, r in b.iterrows()]
Bd = {r["a"]: r for r in spesa}
check("spesa 2019", Bd[2019]["s"], 3858, 1); check("spesa 2025", Bd[2025]["s"], 5532, 1)
pd.DataFrame([{"anno": r["a"], "interviste": r["n"], "viaggiatori_milioni": r["v"], "notti_milioni": r["no"], "spesa_milioni_euro": r["s"],
               "quota_spesa_stranieri_in_Italia_pct": r["q"]} for r in spesa]).to_csv(os.path.join(OUT, "spesa_bdi.csv"), index=False, encoding="utf-8")

# ------------------------------------------------------------------ numeri chiave
def pct(x, y): return round(100 * (x / y - 1), 1)
k = {"tot_2019": S[2019]["pt"], "tot_2025": S[2025]["pt"], "tot_var": pct(S[2025]["pt"], S[2019]["pt"]),
     "it_2019": S[2019]["pi"], "it_2025": S[2025]["pi"], "it_var": pct(S[2025]["pi"], S[2019]["pi"]),
     "str_2019": S[2019]["ps"], "str_2025": S[2025]["ps"], "str_var": pct(S[2025]["ps"], S[2019]["ps"]),
     "it_quota_2019": round(100 * S[2019]["pi"] / S[2019]["pt"], 1), "it_quota_2025": round(100 * S[2025]["pi"] / S[2025]["pt"], 1)}
r19 = [r for r in tipo_tot if r["a"] == 2019][0]; r25 = tipo_tot[-1]
k.update({"it_alb_2019": r19["ialb"], "it_alb_2025": r25["ialb"], "it_alb_var": pct(r25["ialb"], r19["ialb"]),
          "it_ext_var": pct(r25["iext"], r19["iext"]),
          "extra_quota_2019": round(100 * r19["ext"] / (r19["alb"] + r19["ext"]), 1), "extra_quota_2025": round(100 * r25["ext"] / (r25["alb"] + r25["ext"]), 1)})
check("it_var", k["it_var"], -12.8, 0.05); check("str_var", k["str_var"], 63.5, 0.05); check("it_alb_var", k["it_alb_var"], -34.2, 0.05)
check("it_quota_2019", k["it_quota_2019"], 34.6, 0.05); check("it_quota_2025", k["it_quota_2025"], 22.0, 0.05)

dati = {"anni": anni, "serie": serie, "tipo_tot": tipo_tot, "paesi": paesi, "mensile": mn, "mensile_tot": mtot, "expo": expo, "spesa": spesa, "k": k}
json.dump(dati, open(os.path.join(OUT, "dati.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scritto in", OUT, "| paesi/gruppi:", len(paesi), "| avvisi:", len(AVVISI))
for v in AVVISI: print("AVVISO", v)
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
