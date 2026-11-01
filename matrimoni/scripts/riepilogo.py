"""Riepiloghi dalle tabelle pulite. Uso: python -I -X utf8 riepilogo.py <assoluto matrimoni> <assoluto milano-in-dati>
Scrive in pulito/: tassi_per_mille_milano.csv, confronto_comune_istat_2004_2024.csv, eta_sposi_milano_2021_2024.csv,
coppie_miste_milano_2003_2024.csv, covid_2020.csv, riepilogo.json, riepilogo_log.txt"""
import sys, os, json
import pandas as pd, numpy as np

M, P = sys.argv[1], sys.argv[2]
PU = os.path.join(M, "pulito")
R = {}
L = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)
def rd(n): return pd.read_csv(os.path.join(PU, n), sep=";")
def save(df, n): df.to_csv(os.path.join(PU, n), index=False, sep=";", encoding="utf-8")

# ------------------------------------------------------------------ popolazione (denominatori)
pop_a = pd.read_csv(os.path.join(P, "censimenti/pulito/popolazione_milano_annuale_1880_calcolata.csv")).set_index("anno")["popolazione_calcolata"]
pop_b = pd.read_csv(os.path.join(P, "bilancio-comune/pulito/popolazione_milano.csv"), sep=";", encoding="utf-8-sig").set_index("anno")["pop_calcolata_istat_fine_anno"]

# ------------------------------------------------------------------ 1. tassi per mille e sorpasso civile/religioso
r48 = rd("rito_milano_1948_2024.csv")
w = r48.pivot(index="anno", columns="rito", values="n_usato")
w["totale"] = w["civile"] + w["religioso"]
w["quota_civili_pct"] = (100 * w["civile"] / w["totale"]).round(1)
w["pop_comune_ds1494"] = pop_a.reindex(w.index)
w["pop_istat_calcolata"] = pop_b.reindex(w.index)
w["per1000_ab_ds1494"] = (1000 * w["totale"] / w["pop_comune_ds1494"]).round(2)
w["per1000_ab_istat_pop"] = (1000 * w["totale"] / w["pop_istat_calcolata"]).round(2)
w["civili_per1000"] = (1000 * w["civile"] / w["pop_comune_ds1494"]).round(2)
w["religiosi_per1000"] = (1000 * w["religioso"] / w["pop_comune_ds1494"]).round(2)
w = w.reset_index()
w["fonte"] = "rito_milano_1948_2024.csv (ds1496; 2024 civili = 2018) / popolazione ds1494 (censimenti/pulito) e ISTAT calcolata (bilancio-comune/pulito)"
save(w, "tassi_per_mille_milano.csv")
S = w.set_index("anno")
cross = int(S.index[(S["civile"] > S["religioso"])].min())
say("Sorpasso Milano (civili > religiosi, ds1496):", cross, S.loc[cross - 1, ["civile", "religioso"]].to_dict(), S.loc[cross, ["civile", "religioso"]].to_dict())
it = rd("istat_italia_rito_1930_2024.csv").set_index("anno")
cross_it = int(it.index[it["civili"] > it["religiosi"]].min())
say("Sorpasso Italia (ISTAT MA4):", cross_it, it.loc[cross_it - 1, ["civili", "religiosi"]].to_dict(), it.loc[cross_it, ["civili", "religiosi"]].to_dict())
# prima volta in cui i civili superano 1/4, 1/2, 3/4
for th in (25, 50, 75):
    a = S.index[S["quota_civili_pct"] >= th]; b = it.index[it["quota_civili_pct"] >= th]
    say(f"Quota civili >= {th}%: Milano {int(a.min()) if len(a) else None}, Italia {int(b.min()) if len(b) else None}")
for y in (1948, 1960, 1971, 1972, 1990, 2002, 2010, 2019, 2020, 2024):
    r = S.loc[y]
    say(f"Milano {y}: civili {int(r.civile)} religiosi {int(r.religioso)} tot {int(r.totale)} quota civili {r.quota_civili_pct}% tasso {r.per1000_ab_ds1494}/1000 (ISTAT pop: {r.per1000_ab_istat_pop})")
say("Italia 2024 quota civili", it.loc[2024, "quota_civili_pct"], " 1972:", it.loc[1972, "quota_civili_pct"], "2019:", it.loc[2019, "quota_civili_pct"])
mx = S["per1000_ab_ds1494"].idxmax(); say("Massimo del tasso Milano:", mx, S.loc[mx, "per1000_ab_ds1494"], " minimo:", S["per1000_ab_ds1494"].idxmin(), S["per1000_ab_ds1494"].min())
R["sorpasso"] = dict(milano=cross, italia=cross_it, anni_di_anticipo=cross_it - cross)
R["tasso_per_mille"] = {str(y): float(S.loc[y, "per1000_ab_ds1494"]) for y in (1948, 1964, 1990, 2002, 2008, 2019, 2020, 2024)}

# ------------------------------------------------------------------ 2. confronto Comune - ISTAT 2004-2024 (comune di Milano)
im = rd("istat_milano_comune_rito_2004_2024.csv").set_index("anno")
cmp = pd.DataFrame({"comune_religiosi": S["religioso"], "comune_civili": S["civile"], "istat_religiosi": im["religiosi"], "istat_civili": im["civili"]}).loc[2004:2024]
cmp["diff_religiosi"] = cmp["istat_religiosi"] - cmp["comune_religiosi"]; cmp["diff_civili"] = cmp["istat_civili"] - cmp["comune_civili"]
cmp["diff_totale"] = cmp["diff_religiosi"] + cmp["diff_civili"]
cmp = cmp.reset_index(); cmp["fonte"] = "rito_milano_1948_2024.csv (n_usato) vs istat_milano_comune_rito_2004_2024.csv"
save(cmp, "confronto_comune_istat_2004_2024.csv")
say("Differenze ISTAT - Comune (totale) per anno:", cmp.set_index("anno")["diff_totale"].to_dict())

# ------------------------------------------------------------------ 3. coppie miste (cittadinanza) 2003-2024
rc = rd("matrimoni_rito_cittadinanza_milano.csv")
def mixed(df):
    g = df[df.cit_marito != "n.d."][df.cit_moglie != "n.d."]
    # esclusi i casi con cittadinanza ignota: la quota e' calcolata sui noti
    tot = g.groupby("anno")["n"].sum()
    alm1 = g[(g.cit_marito == "straniera") | (g.cit_moglie == "straniera")].groupby("anno")["n"].sum()
    misti = g[g.cit_marito != g.cit_moglie].groupby("anno")["n"].sum()
    ent = g[(g.cit_marito == "straniera") & (g.cit_moglie == "straniera")].groupby("anno")["n"].sum()
    return pd.DataFrame({"n_noti": tot, "almeno_uno_straniero": alm1, "misti_it_str": misti, "entrambi_stranieri": ent}).fillna(0)
out = []
for per in ("celebrati_a_milano", "almeno_un_coniuge_residente"):
    for rito_f in ("tutti", "civile", "religiosi"):
        d = rc[rc.perimetro == per]
        if rito_f == "civile": d = d[d.rito == "civile"]
        elif rito_f == "religiosi": d = d[d.rito != "civile"]
        m = mixed(d); m["quota_almeno_uno_straniero_pct"] = (100 * m["almeno_uno_straniero"] / m["n_noti"]).round(1)
        m["quota_misti_pct"] = (100 * m["misti_it_str"] / m["n_noti"]).round(1); m["quota_entrambi_stranieri_pct"] = (100 * m["entrambi_stranieri"] / m["n_noti"]).round(1)
        m.insert(0, "rito", rito_f); m.insert(0, "perimetro", per); out.append(m.reset_index())
cm = pd.concat(out); cm["fonte"] = "matrimoni_rito_cittadinanza_milano.csv (ds138/ds1947 celebrati; ds132/ds1949 residenti); esclusi i pochi casi con cittadinanza non indicata"
save(cm, "coppie_miste_milano_2003_2024.csv")
c = cm[(cm.perimetro == "celebrati_a_milano") & (cm.rito == "tutti")].set_index("anno")
for y in (2003, 2008, 2012, 2019, 2020, 2024):
    r = c.loc[y]; say(f"Celebrati a Milano {y}: almeno uno straniero {r.quota_almeno_uno_straniero_pct}% (misti {r.quota_misti_pct}%, entrambi stranieri {r.quota_entrambi_stranieri_pct}%), n={int(r.n_noti)}")
for rito_f in ("civile", "religiosi"):
    c2 = cm[(cm.perimetro == "celebrati_a_milano") & (cm.rito == rito_f)].set_index("anno")
    say(rito_f, "2003:", c2.loc[2003, "quota_almeno_uno_straniero_pct"], "2012:", c2.loc[2012, "quota_almeno_uno_straniero_pct"], "2024:", c2.loc[2024, "quota_almeno_uno_straniero_pct"])
cr = cm[(cm.perimetro == "almeno_un_coniuge_residente") & (cm.rito == "tutti")].set_index("anno")
say("Residenti 2011/2019/2024: almeno uno straniero", cr.loc[2011, "quota_almeno_uno_straniero_pct"], cr.loc[2019, "quota_almeno_uno_straniero_pct"], cr.loc[2024, "quota_almeno_uno_straniero_pct"])
tc = rd("istat_matrimoni_tipologia_coppia_2004_2024.csv")
for terr in ("provincia_milano", "italia"):
    t = tc[tc.territorio == terr].set_index("anno")
    say(f"ISTAT {terr}: almeno uno straniero % 2004/2012/2019/2024:", [round(100 * t.loc[y, "almeno_uno_straniero"] / t.loc[y, "totale"], 1) for y in (2004, 2012, 2019, 2024)])
R["coppie_miste_celebrati_milano_pct"] = {str(y): float(c.loc[y, "quota_almeno_uno_straniero_pct"]) for y in (2003, 2012, 2019, 2024)}

# ------------------------------------------------------------------ 4. residenti vs celebrati
tot = rd("matrimoni_rito_per_anno_milano.csv")
tt = tot.assign(gruppo=np.where(tot.rito == "civile", "civile", "religioso")).groupby(["perimetro", "anno", "gruppo"], as_index=False)["n"].sum()
cel = tt[tt.perimetro == "celebrati_a_milano"].pivot(index="anno", columns="gruppo", values="n")
res = tt[tt.perimetro == "almeno_un_coniuge_residente"].pivot(index="anno", columns="gruppo", values="n")
rv = pd.DataFrame({"celebrati_civili": cel["civile"], "celebrati_religiosi": cel["religioso"], "residenti_civili": res["civile"], "residenti_religiosi": res["religioso"]}).loc[2011:2024]
rv["residenti_totale"] = rv["residenti_civili"] + rv["residenti_religiosi"]; rv["celebrati_totale"] = rv["celebrati_civili"] + rv["celebrati_religiosi"]
rv["rapporto_religiosi_residenti_su_celebrati"] = (rv["residenti_religiosi"] / rv["celebrati_religiosi"]).round(2)
rv["rapporto_civili_residenti_su_celebrati"] = (rv["residenti_civili"] / rv["celebrati_civili"]).round(2)
rv["residenti_per1000_ab"] = (1000 * rv["residenti_totale"] / pop_a.reindex(rv.index)).round(2)
rv = rv.reset_index(); rv["fonte"] = "matrimoni_rito_per_anno_milano.csv: ds138/ds1947 (celebrati) vs ds132/ds1949 (almeno un coniuge residente); popolazione ds1494"
save(rv, "residenti_vs_celebrati_2011_2024.csv")
say(rv.set_index("anno")[["celebrati_totale", "residenti_totale", "rapporto_religiosi_residenti_su_celebrati", "rapporto_civili_residenti_su_celebrati", "residenti_per1000_ab"]].to_string())

# ------------------------------------------------------------------ 5. eta' (classi quinquennali, 2021-2024)
ea = rd("matrimoni_eta_milano_2021_2024.csv")
def mid(c):
    if c.startswith("n.d"): return np.nan
    if "e più" in c: return 87.5
    a, b = c.split(" ")[0].split("-"); return (int(a) + int(b) + 1) / 2
ea["m_mar"] = ea.classe_eta_marito.map(mid); ea["m_mog"] = ea.classe_eta_moglie.map(mid)
res_e = []
for (per, y), g in ea.groupby(["perimetro", "anno"]):
    g = g.dropna(subset=["m_mar", "m_mog"]); n = g.n.sum()
    def wmed(col):
        s = g.groupby(col)["n"].sum().sort_index().cumsum(); return float(s.index[(s >= n / 2).values][0])
    both = lambda lo: float(g[(g.m_mar >= lo) & (g.m_mog >= lo)].n.sum() / n * 100)
    res_e.append(dict(perimetro=per, anno=y, n_con_eta_nota=int(n), eta_media_sposi_stima=round((g.m_mar * g.n).sum() / n, 1), eta_media_spose_stima=round((g.m_mog * g.n).sum() / n, 1),
                      classe_mediana_sposi=wmed("m_mar"), classe_mediana_spose=wmed("m_mog"),
                      sposa_piu_grande_pct=round(100 * g[g.m_mog > g.m_mar].n.sum() / n, 1), stessa_classe_pct=round(100 * g[g.m_mog == g.m_mar].n.sum() / n, 1),
                      sposo_piu_grande_di_almeno_10_anni_pct=round(100 * g[g.m_mar - g.m_mog >= 10].n.sum() / n, 1),
                      sposi_sotto_30_pct=round(100 * g[g.m_mar < 30].n.sum() / n, 1), spose_sotto_30_pct=round(100 * g[g.m_mog < 30].n.sum() / n, 1),
                      entrambi_40_piu_pct=round(both(40), 1), sposi_40_piu_pct=round(100 * g[g.m_mar >= 40].n.sum() / n, 1)))
re_ = pd.DataFrame(res_e); re_["fonte"] = "matrimoni_eta_milano_2021_2024.csv (ds1950, ds1952); eta' media stimata col centro della classe (85+ = 87,5), esclusi i n.d."
save(re_, "eta_sposi_milano_2021_2024.csv")
say(re_.drop(columns="fonte").to_string())
ie = rd("istat_eta_media_al_matrimonio_2004_2024.csv")
say("ISTAT eta media al matrimonio, provincia Milano (tutti gli stati civili) sposi/spose 2004, 2012, 2019, 2024:")
for sx in ("sposi", "spose"):
    t = ie[(ie.territorio == "provincia_milano") & (ie.sesso == sx)].set_index("anno")
    say(" ", sx, [t.loc[y, "eta_media_totale"] for y in (2004, 2012, 2019, 2024)], "celibi/nubili:", [t.loc[y, "eta_media_celibe_nubile"] for y in (2004, 2012, 2019, 2024)])
pm = rd("istat_primo_matrimonio_lombardia_italia_1990_2024.csv")
for ind in ("eta_media_sposi_primo_matrimonio", "eta_media_spose_primo_matrimonio"):
    for terr in ("Lombardia", "Italia"):
        t = pm[(pm.indicatore == ind) & (pm.territorio == terr)].set_index("anno")["valore"]
        say(" ", ind, terr, {y: t.get(y) for y in (1990, 2000, 2010, 2019, 2024)})
ind = rd("istat_indicatori_nuzialita_2004_2024.csv")
for terr in ("provincia_milano", "italia"):
    t = ind[ind.territorio == terr].set_index("anno")
    say(f"ISTAT {terr} quoziente nuzialita' ‰ 2004/2012/2019/2020/2024:", [t.loc[y, "quoziente_nuzialita_per1000"] for y in (2004, 2012, 2019, 2020, 2024)],
        "civili %:", [t.loc[y, "matrimoni_civili_pct"] for y in (2004, 2012, 2019, 2024)], "secondo matr. sposi %:", [t.loc[y, "sposi_secondo_o_succ_pct"] for y in (2004, 2024)])

# ------------------------------------------------------------------ 6. unioni civili
uc = rd("unioni_civili_per_anno_sesso_milano.csv").pivot(index="anno", columns="sesso_coppia", values="n"); uc["totale"] = uc.sum(axis=1)
uc["quota_uomini_pct"] = (100 * uc["uomini"] / uc["totale"]).round(1)
uc["matrimoni_celebrati"] = S["totale"].reindex(uc.index)
uc["unioni_ogni_100_matrimoni"] = (100 * uc["totale"] / uc["matrimoni_celebrati"]).round(1)
ui = rd("istat_unioni_civili_2018_2024.csv")
uc["istat_comune_milano"] = ui[ui.territorio == "comune_milano"].set_index("anno")["totale"].reindex(uc.index)
uc["istat_italia"] = ui[ui.territorio == "italia"].set_index("anno")["totale"].reindex(uc.index)
uc["quota_milano_su_italia_pct_istat"] = (100 * uc["istat_comune_milano"] / uc["istat_italia"]).round(1)
uc["istat_italia_quota_uomini_pct"] = (100 * ui[ui.territorio == "italia"].set_index("anno")["uomini"] / ui[ui.territorio == "italia"].set_index("anno")["totale"]).reindex(uc.index).round(1)
uc = uc.reset_index(); uc["fonte"] = "unioni_civili_per_anno_sesso_milano.csv (ds398) + istat_unioni_civili_2018_2024.csv (ISTAT UC4/UC2) + matrimoni (rito_milano_1948_2024.csv)"
save(uc, "unioni_civili_riepilogo.csv")
say(uc.drop(columns="fonte").to_string())
uu = rd("unioni_civili_milano_2016_2024.csv")
mix = uu[(uu.cit_partner1 != uu.cit_partner2)].n.sum() / uu.n.sum() * 100; fo = uu[(uu.cit_partner1 == "straniera") | (uu.cit_partner2 == "straniera")].n.sum() / uu.n.sum() * 100
say(f"Unioni civili 2016-2024: almeno un partner straniero {fo:.1f}%, coppie miste (uno it uno str) {mix:.1f}%")
def midc(c):
    if "e più" in c: return 90.0
    a, b = c.split(" ")[0].split("-"); return (int(a) + int(b) + 1) / 2
uu["m1"] = uu.classe_eta_partner1.map(midc); uu["m2"] = uu.classe_eta_partner2.map(midc)
say("Unioni civili: eta' media stimata (centro classe) dei due partner (media) 2016-2024:", round(((uu.m1 + uu.m2) / 2 * uu.n).sum() / uu.n.sum(), 1), "; classi 25-44 entrambi:", round(100 * uu[(uu.m1 >= 25) & (uu.m1 < 45) & (uu.m2 >= 25) & (uu.m2 < 45)].n.sum() / uu.n.sum(), 1), "%")
R["unioni_civili"] = {str(int(r.anno)): int(r.totale) for r in uc.itertuples()}

# ------------------------------------------------------------------ 7. separazioni e divorzi
sd = rd("separazioni_divorzi_milano_piu_monza_2007_2024.csv")
sp = sd.pivot(index="anno", columns="tipo", values="milano_piu_monza").rename(columns={"separazioni": "separazioni_milano_piu_monza", "divorzi": "divorzi_milano_piu_monza"})
sp["separazioni_milano_provincia_istat"] = sd[sd.tipo == "separazioni"].set_index("anno")["milano_provincia"]
sp["divorzi_milano_provincia_istat"] = sd[sd.tipo == "divorzi"].set_index("anno")["milano_provincia"]
sp["separazioni_italia"] = sd[sd.tipo == "separazioni"].set_index("anno")["italia"]; sp["divorzi_italia"] = sd[sd.tipo == "divorzi"].set_index("anno")["italia"]
mt = tc[tc.territorio.isin(["provincia_milano", "provincia_monza_brianza"])].pivot_table(index="anno", columns="territorio", values="totale", aggfunc="first")
sp["matrimoni_milano_piu_monza_istat"] = (mt["provincia_milano"] + mt["provincia_monza_brianza"]).reindex(sp.index)
sp["matrimoni_italia_istat"] = it["totale"].reindex(sp.index)
sp["sep_su_100_matrimoni_milano"] = (100 * sp["separazioni_milano_piu_monza"] / sp["matrimoni_milano_piu_monza_istat"]).round(1)
sp["div_su_100_matrimoni_milano"] = (100 * sp["divorzi_milano_piu_monza"] / sp["matrimoni_milano_piu_monza_istat"]).round(1)
sp["sep_su_100_matrimoni_italia"] = (100 * sp["separazioni_italia"] / sp["matrimoni_italia_istat"]).round(1)
sp["div_su_100_matrimoni_italia"] = (100 * sp["divorzi_italia"] / sp["matrimoni_italia_istat"]).round(1)
sp = sp.reset_index(); sp["fonte"] = "separazioni_divorzi_milano_piu_monza_2007_2024.csv (ISTAT sepdiv tavole 1.5/2.5; area = province Milano + Monza e Brianza) / matrimoni ISTAT MA3 (stessa area). Rapporti grezzi: eventi dell'anno su matrimoni dell'anno, NON probabilita' di rottura"
save(sp, "separazioni_divorzi_riepilogo.csv")
say(sp.drop(columns="fonte").to_string())
sdi = sd.set_index(["tipo", "anno"])
for tipo in ("separazioni", "divorzi"):
    s = sd[sd.tipo == tipo].set_index("anno")["milano_piu_monza"]
    say(tipo, "Milano+Monza 2007/2014/2015/2016/2019/2020/2024:", [s[y] for y in (2007, 2014, 2015, 2016, 2019, 2020, 2024)], " variazione 2019->2020: %.1f%%" % (100 * (s[2020] / s[2019] - 1)), " 2014->2016: %.0f%%" % (100 * (s[2016] / s[2014] - 1)))
R["separazioni_milano_piu_monza"] = {str(int(r.anno)): int(r.separazioni_milano_piu_monza) for r in sp.itertuples()}
R["divorzi_milano_piu_monza"] = {str(int(r.anno)): int(r.divorzi_milano_piu_monza) for r in sp.itertuples()}
sc = rd("scioglimenti_2018_comune_milano_aggregati.csv"); say(sc.drop(columns="fonte").to_string())

# ------------------------------------------------------------------ 8. Covid 2020
cv = []
def add(nome, a19, a20, a21=None, a23=None, a24=None):
    cv.append(dict(serie=nome, v2019=a19, v2020=a20, var_2020_su_2019_pct=round(100 * (a20 / a19 - 1), 1), v2021=a21, v2023=a23, v2024=a24,
                   v2024_su_2019_pct=None if a24 is None else round(100 * (a24 / a19 - 1), 1)))
g = lambda col: (S.loc[2019, col], S.loc[2020, col], S.loc[2021, col], S.loc[2023, col], S.loc[2024, col])
add("Milano matrimoni celebrati - totale", *g("totale")); add("Milano matrimoni civili", *g("civile")); add("Milano matrimoni religiosi", *g("religioso"))
gi = lambda col: (it.loc[2019, col], it.loc[2020, col], it.loc[2021, col], it.loc[2023, col], it.loc[2024, col])
add("Italia matrimoni - totale", *gi("totale")); add("Italia matrimoni civili", *gi("civili")); add("Italia matrimoni religiosi", *gi("religiosi"))
u = uc.set_index("anno")["totale"]; add("Milano unioni civili (Comune)", u[2019], u[2020], u[2021], u[2023], u[2024])
r_ = rv.set_index("anno")["residenti_totale"]; cv.append(dict(serie="Milano matrimoni di residenti (ds132/ds1949)", v2019=r_[2019], v2020=r_[2020], var_2020_su_2019_pct=round(100 * (r_[2020] / r_[2019] - 1), 1), v2021=r_[2021], v2023=r_[2023], v2024=r_[2024], v2024_su_2019_pct=round(100 * (r_[2024] / r_[2019] - 1), 1)))
s_ = sp.set_index("anno")
for nome, col in (("Milano+Monza separazioni (ISTAT)", "separazioni_milano_piu_monza"), ("Milano+Monza divorzi (ISTAT)", "divorzi_milano_piu_monza")):
    add(nome, s_.loc[2019, col], s_.loc[2020, col], s_.loc[2021, col], s_.loc[2023, col], s_.loc[2024, col])
cvd = pd.DataFrame(cv); cvd["fonte"] = "tabelle pulite indicate nelle righe sopra"
save(cvd, "covid_2020.csv"); say(cvd.drop(columns="fonte").to_string())
# mese: ISTAT MA1 q2 non scaricato; vedi NOTE

json.dump(R, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(PU, "riepilogo_log.txt"), "w", encoding="utf-8").write("\n".join(L) + "\n")
