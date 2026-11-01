"""Scrive i dati aggregati della pagina docs/matrimoni/ (riepilogo.json + CSV scaricabili).
Uso: python -I -X utf8 pagina.py <assoluto matrimoni> <assoluto milano-in-dati>
Legge solo le tabelle di matrimoni/pulito/ (gia' aggregate). Si puo' rilanciare.
Dati: Comune di Milano (CC-BY) e ISTAT (CC BY 4.0), scaricati il 2026-11-01."""
import sys, os, json, shutil
import pandas as pd

M, P = sys.argv[1], sys.argv[2]
PU = os.path.join(M, "pulito")
OUT = os.path.join(P, "docs", "matrimoni", "data")
os.makedirs(OUT, exist_ok=True)

def rd(n): return pd.read_csv(os.path.join(PU, n), sep=";")
def nn(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return None
    return float(x) if not float(x).is_integer() else int(x)
def ser(df, xc, yc): return [[int(a), nn(b)] for a, b in zip(df[xc], df[yc])]

R = {"meta": {"scaricato": "2026-11-01", "pagina_generata_da": "matrimoni/scripts/pagina.py",
              "licenze": "Comune di Milano: CC-BY (portale CKAN, versione non indicata); ISTAT: CC BY 4.0 (istat.it/it/note-legali)"}}
N = {}  # numeri citati nel testo, ciascuno con l'origine
def num(k, v, origine): N[k] = {"v": nn(v) if not isinstance(v, str) else v, "origine": origine}

# ---------------------------------------------------------------- rito, tassi
t = rd("tassi_per_mille_milano.csv").set_index("anno")
R["rito"] = [dict(a=int(a), civ=int(r.civile), rel=int(r.religioso), tot=int(r.totale), q=nn(r.quota_civili_pct), pm=nn(r.per1000_ab_ds1494),
                  cpm=nn(r.civili_per1000), rpm=nn(r.religiosi_per1000), pop=int(r.pop_comune_ds1494)) for a, r in t.iterrows()]
src_t = "pulito/tassi_per_mille_milano.csv (ds1496 con civili 2024 = 2018; popolazione ds1494)"
for y in (1948, 1961, 1963, 1971, 1972, 2002, 2019, 2020, 2024):
    r = t.loc[y]
    num(f"civ_{y}", r.civile, src_t + f", anno {y}, civile"); num(f"rel_{y}", r.religioso, src_t + f", anno {y}, religioso")
    num(f"tot_{y}", r.totale, src_t); num(f"pm_{y}", r.per1000_ab_ds1494, src_t + ", per1000_ab_ds1494")
    num(f"cpm_{y}", r.civili_per1000, src_t + ", civili_per1000"); num(f"rpm_{y}", r.religiosi_per1000, src_t + ", religiosi_per1000")
    num(f"q_{y}", r.quota_civili_pct, src_t + ", quota_civili_pct")
num("civ_mediana_1972_2024", t.loc[1972:, "civile"].median(), src_t)
num("civ_max_dal_1972", t.loc[1972:, "civile"].max(), src_t); num("pm_max", t["per1000_ab_ds1494"].max(), src_t); num("pm_max_anno", t["per1000_ab_ds1494"].idxmax(), src_t)
c81 = t.loc[1981:, "civile"].drop(2020)
num("civ_max_dal_1981", t.loc[1981:, "civile"].max(), src_t); num("civ_min_dal_1981_senza_2020", c81.min(), src_t + " (2020 escluso)")
num("rel_1961_su_2024_pct", 100 * t.loc[2024, "religioso"] / t.loc[1961, "religioso"], src_t)

it = rd("istat_italia_rito_1930_2024.csv").set_index("anno")
R["italia"] = [dict(a=int(a), civ=int(r.civili), rel=int(r.religiosi), q=nn(r.quota_civili_pct)) for a, r in it.loc[1948:].iterrows()]
src_i = "pulito/istat_italia_rito_1930_2024.csv (ISTAT demo MA4 q1)"
cross_m = int(t.index[t.civile > t.religioso].min()); cross_i = int(it.index[it.civili > it.religiosi].min())
num("sorpasso_milano", cross_m, "pulito/tassi_per_mille_milano.csv: primo anno con civile > religioso"); num("sorpasso_italia", cross_i, src_i + ": primo anno con civili > religiosi")
num("q25_milano", int(t.index[t.quota_civili_pct >= 25].min()), src_t); num("q25_italia", int(it.index[it.quota_civili_pct >= 25].min()), src_i)
num("q_italia_2024", it.loc[2024, "quota_civili_pct"], src_i); num("civ_it_2024", it.loc[2024, "civili"], src_i); num("tot_it_2024", it.loc[2024, "totale"], src_i)
num("civ_it_1971", it.loc[1971, "civili"], src_i); num("civ_it_1972", it.loc[1972, "civili"], src_i)
ind = rd("istat_indicatori_nuzialita_2004_2024.csv")
for terr, k in (("provincia_milano", "prov"), ("italia", "it")):
    s = ind[ind.territorio == terr].set_index("anno")
    for y in (2004, 2019, 2020, 2024):
        num(f"quoz_{k}_{y}", s.loc[y, "quoziente_nuzialita_per1000"], f"pulito/istat_indicatori_nuzialita_2004_2024.csv, {terr}, quoziente_nuzialita_per1000")
num("civ_prov_2024", ind[(ind.territorio == "provincia_milano") & (ind.anno == 2024)].matrimoni_civili_pct.iloc[0], "pulito/istat_indicatori_nuzialita_2004_2024.csv, matrimoni_civili_pct")

# ---------------------------------------------------------------- eta'
em = rd("istat_eta_media_al_matrimonio_2004_2024.csv")
def emv(sex, col):
    s = em[(em.territorio == "provincia_milano") & (em.sesso == sex)]; return ser(s, "anno", col)
R["eta_prov"] = dict(sposi=emv("sposi", "eta_media_totale"), spose=emv("spose", "eta_media_totale"), sposi_cel=emv("sposi", "eta_media_celibe_nubile"), spose_cel=emv("spose", "eta_media_celibe_nubile"))
pm = rd("istat_primo_matrimonio_lombardia_italia_1990_2024.csv")
def pmv(ind_, terr): s = pm[(pm.indicatore == ind_) & (pm.territorio == terr)].sort_values("anno"); return ser(s, "anno", "valore")
R["primo"] = dict(lomb_sposi=pmv("eta_media_sposi_primo_matrimonio", "Lombardia"), lomb_spose=pmv("eta_media_spose_primo_matrimonio", "Lombardia"),
                  it_sposi=pmv("eta_media_sposi_primo_matrimonio", "Italia"), it_spose=pmv("eta_media_spose_primo_matrimonio", "Italia"))
def last(lst, y): return [v for a, v in lst if a == y][0]
for k, lst in (("sposi_prov", R["eta_prov"]["sposi"]), ("spose_prov", R["eta_prov"]["spose"])):
    for y in (2004, 2024): num(f"eta_{k}_{y}", last(lst, y), "pulito/istat_eta_media_al_matrimonio_2004_2024.csv, provincia_milano, eta_media_totale")
for k in ("lomb_sposi", "lomb_spose", "it_sposi", "it_spose"):
    for y in (1990, 2024): num(f"primo_{k}_{y}", last(R["primo"][k], y), "pulito/istat_primo_matrimonio_lombardia_italia_1990_2024.csv (ISTAT NU1)")
ec = rd("eta_sposi_milano_2021_2024.csv"); ec = ec[ec.perimetro == "celebrati_a_milano"].sort_values("anno")
R["eta_comune"] = [dict(a=int(r.anno), n=int(r.n_con_eta_nota), sposi=nn(r.eta_media_sposi_stima), spose=nn(r.eta_media_spose_stima), spose_piu_grandi=nn(r.sposa_piu_grande_pct),
                        stessa_classe=nn(r.stessa_classe_pct), sposo_10=nn(r.sposo_piu_grande_di_almeno_10_anni_pct), entrambi_40=nn(r.entrambi_40_piu_pct)) for r in ec.itertuples()]
num("spose_piu_grandi_2024", ec[ec.anno == 2024].sposa_piu_grande_pct.iloc[0], "pulito/eta_sposi_milano_2021_2024.csv, celebrati_a_milano 2024, sposa_piu_grande_pct (ds1950)")
num("stessa_classe_2024", ec[ec.anno == 2024].stessa_classe_pct.iloc[0], "idem, stessa_classe_pct")
num("sposo_10_2024", ec[ec.anno == 2024].sposo_piu_grande_di_almeno_10_anni_pct.iloc[0], "idem")

# ---------------------------------------------------------------- coppie miste
cm = rd("coppie_miste_milano_2003_2024.csv"); cc = cm[(cm.perimetro == "celebrati_a_milano") & (cm.rito == "tutti")].sort_values("anno")
tc = rd("istat_matrimoni_tipologia_coppia_2004_2024.csv")
def tcs(terr): s = tc[tc.territorio == terr].sort_values("anno"); return [[int(a), round(100 * x / y, 1)] for a, x, y in zip(s.anno, s.almeno_uno_straniero, s.totale)]
R["miste"] = dict(comune=ser(cc, "anno", "quota_almeno_uno_straniero_pct"), prov=tcs("provincia_milano"), italia=tcs("italia"),
                  civile={str(y): nn(cm[(cm.perimetro == "celebrati_a_milano") & (cm.rito == "civile") & (cm.anno == y)].quota_almeno_uno_straniero_pct.iloc[0]) for y in (2003, 2012, 2024)},
                  religiosi={str(y): nn(cm[(cm.perimetro == "celebrati_a_milano") & (cm.rito == "religiosi") & (cm.anno == y)].quota_almeno_uno_straniero_pct.iloc[0]) for y in (2003, 2012, 2024)})
for y in (2003, 2019, 2024): num(f"miste_com_{y}", last(R["miste"]["comune"], y), "pulito/coppie_miste_milano_2003_2024.csv, celebrati_a_milano, tutti, quota_almeno_uno_straniero_pct")
for y in (2004, 2024):
    num(f"miste_prov_{y}", last(R["miste"]["prov"], y), "pulito/istat_matrimoni_tipologia_coppia_2004_2024.csv (almeno_uno_straniero / totale), provincia_milano")
    num(f"miste_it_{y}", last(R["miste"]["italia"], y), "idem, italia")
num("miste_prov_2019", last(R["miste"]["prov"], 2019), "idem, provincia_milano"); num("miste_it_2019", last(R["miste"]["italia"], 2019), "idem, italia")

# ---------------------------------------------------------------- unioni civili
u = rd("unioni_civili_riepilogo.csv")
R["unioni"] = [dict(a=int(r.anno), m=int(r.uomini), f=int(r.donne), t=int(r.totale), per100=nn(r.unioni_ogni_100_matrimoni), istat_mi=nn(r.istat_comune_milano), istat_it=nn(r.istat_italia),
                    quota=nn(r.quota_milano_su_italia_pct_istat), it_uomini=nn(r.istat_italia_quota_uomini_pct)) for r in u.itertuples()]
num("uc_totale", u.totale.sum(), "pulito/unioni_civili_riepilogo.csv, somma di totale 2016-2024 (ds398)"); num("uc_uomini_pct", 100 * u.uomini.sum() / u.totale.sum(), "idem, uomini / totale")
num("uc_2017", u[u.anno == 2017].totale.iloc[0], "idem"); num("uc_2024", u[u.anno == 2024].totale.iloc[0], "idem"); num("uc_2020", u[u.anno == 2020].totale.iloc[0], "idem")
num("uc_quota_min", u.quota_milano_su_italia_pct_istat.min(), "idem, quota_milano_su_italia_pct_istat"); num("uc_quota_max", u.quota_milano_su_italia_pct_istat.max(), "idem")
num("uc_quota_2024", u[u.anno == 2024].quota_milano_su_italia_pct_istat.iloc[0], "idem")
num("mi_su_it_matrimoni_2024_pct", 100 * t.loc[2024, "totale"] / it.loc[2024, "totale"], "tot Milano ds1496 (civili 2024 = 2018) / totale Italia ISTAT MA4")
num("uc_uomini_it_2024", u[u.anno == 2024].istat_italia_quota_uomini_pct.iloc[0], "pulito/unioni_civili_riepilogo.csv, istat_italia_quota_uomini_pct")
num("uc_uomini_mi_2024", 100 * u[u.anno == 2024].uomini.iloc[0] / u[u.anno == 2024].totale.iloc[0], "idem, uomini/totale Comune 2024")
uu = rd("unioni_civili_milano_2016_2024.csv")
num("uc_straniero_pct", 100 * uu[(uu.cit_partner1 == "straniera") | (uu.cit_partner2 == "straniera")].n.sum() / uu.n.sum(), "pulito/unioni_civili_milano_2016_2024.csv: coppie con almeno un partner straniero / totale")

# ---------------------------------------------------------------- separazioni e divorzi
sp = rd("separazioni_divorzi_riepilogo.csv")
R["sepdiv"] = [dict(a=int(r.anno), sep=int(r.separazioni_milano_piu_monza), div=int(r.divorzi_milano_piu_monza), sep_mi=nn(r.separazioni_milano_provincia_istat), div_mi=nn(r.divorzi_milano_provincia_istat),
                    sep_it=int(r.separazioni_italia), div_it=int(r.divorzi_italia)) for r in sp.itertuples()]
s = sp.set_index("anno"); src_s = "pulito/separazioni_divorzi_riepilogo.csv (ISTAT tavole 1.5 e 2.5; Milano + Monza e Brianza)"
for y in (2007, 2014, 2015, 2016, 2019, 2020, 2022, 2024):
    num(f"sep_{y}", s.loc[y, "separazioni_milano_piu_monza"], src_s); num(f"div_{y}", s.loc[y, "divorzi_milano_piu_monza"], src_s)
num("div_var_2014_2016_pct", 100 * (s.loc[2016, "divorzi_milano_piu_monza"] / s.loc[2014, "divorzi_milano_piu_monza"] - 1), src_s)
num("div_it_var_2014_2016_pct", 100 * (s.loc[2016, "divorzi_italia"] / s.loc[2014, "divorzi_italia"] - 1), src_s)
num("sep_mi_2009", s.loc[2009, "separazioni_milano_provincia_istat"], src_s + ", separazioni_milano_provincia_istat (Monza inclusa)"); num("sep_mi_2010", s.loc[2010, "separazioni_milano_provincia_istat"], src_s + ", separazioni_milano_provincia_istat (senza Monza)")
num("sep_var_2019_2020_pct", 100 * (s.loc[2020, "separazioni_milano_piu_monza"] / s.loc[2019, "separazioni_milano_piu_monza"] - 1), src_s)
num("div_var_2019_2020_pct", 100 * (s.loc[2020, "divorzi_milano_piu_monza"] / s.loc[2019, "divorzi_milano_piu_monza"] - 1), src_s)
sc = rd("scioglimenti_2018_comune_milano_aggregati.csv").iloc[0]
num("scioglimenti_2018_comune", sc.scioglimenti, "pulito/scioglimenti_2018_comune_milano_aggregati.csv (ds705)"); num("div_2018_prov", s.loc[2018, "divorzi_milano_provincia_istat"], src_s + ", divorzi_milano_provincia_istat")

# ---------------------------------------------------------------- Covid
cv = rd("covid_2020.csv")
R["covid"] = [dict(serie=r.serie, v2019=nn(r.v2019), v2020=nn(r.v2020), var=nn(r.var_2020_su_2019_pct), v2024=nn(r.v2024), var24=nn(r.v2024_su_2019_pct)) for r in cv.itertuples()]

# ---------------------------------------------------------------- residenti contro celebrati
rv = rd("residenti_vs_celebrati_2011_2024.csv")
R["residenti"] = [dict(a=int(r.anno), cel=int(r.celebrati_totale), res=int(r.residenti_totale), cel_rel=int(r.celebrati_religiosi), res_rel=int(r.residenti_religiosi),
                       cel_civ=int(r.celebrati_civili), res_civ=int(r.residenti_civili), ratio_rel=nn(r.rapporto_religiosi_residenti_su_celebrati)) for r in rv.itertuples()]
r_ = rv.set_index("anno"); src_r = "pulito/residenti_vs_celebrati_2011_2024.csv (ds138/ds1947 contro ds132/ds1949)"
for y in (2011, 2018, 2023, 2024):
    num(f"res_rel_{y}", r_.loc[y, "residenti_religiosi"], src_r); num(f"cel_rel_{y}", r_.loc[y, "celebrati_religiosi"], src_r)
    num(f"res_tot_{y}", r_.loc[y, "residenti_totale"], src_r); num(f"cel_tot_{y}", r_.loc[y, "celebrati_totale"], src_r)
num("altrove_pct_2011", 100 * (r_.loc[2011, "residenti_religiosi"] - r_.loc[2011, "celebrati_religiosi"]) / r_.loc[2011, "residenti_religiosi"], src_r + ": (residenti - celebrati) / residenti, religiosi 2011, minimo perche' i celebrati includono non residenti")
num("altrove_pct_2018", 100 * (r_.loc[2018, "residenti_religiosi"] - r_.loc[2018, "celebrati_religiosi"]) / r_.loc[2018, "residenti_religiosi"], src_r + ", 2018")
num("res_rel_var_2024_pct", 100 * (r_.loc[2024, "residenti_religiosi"] / r_.loc[2023, "residenti_religiosi"] - 1), src_r)
num("cel_rel_var_2024_pct", 100 * (r_.loc[2024, "celebrati_religiosi"] / r_.loc[2023, "celebrati_religiosi"] - 1), src_r)

# ---------------------------------------------------------------- confronto Comune/ISTAT
cf = rd("confronto_comune_istat_2004_2024.csv")
R["confronto"] = [dict(a=int(r.anno), com=int(r.comune_religiosi + r.comune_civili), ist=int(r.istat_religiosi + r.istat_civili), d=int(r.diff_totale)) for r in cf.itertuples()]
c10 = cf[cf.anno == 2010].iloc[0]
num("istat_2010", c10.istat_religiosi + c10.istat_civili, "pulito/confronto_comune_istat_2004_2024.csv"); num("comune_2010", c10.comune_religiosi + c10.comune_civili, "idem")
num("istat_2010_rel", c10.istat_religiosi, "idem"); num("comune_2010_rel", c10.comune_religiosi, "idem")

R["numeri"] = N

# ---------------------------------------------------------------- file scaricabili (tabelle aggregate)
FILES = [("rito_milano_1948_2024.csv", "Matrimoni civili e religiosi per anno a Milano, 1948-2024, con il valore usato e quello del file (civili 2024)"),
         ("tassi_per_mille_milano.csv", "Matrimoni per 1.000 abitanti, quota di civili, popolazione usata"),
         ("istat_italia_rito_1930_2024.csv", "Matrimoni per rito in Italia, 1930-2024 (ISTAT)"),
         ("istat_milano_comune_rito_2004_2024.csv", "Matrimoni per rito, comune di Milano, 2004-2024 (ISTAT)"),
         ("confronto_comune_istat_2004_2024.csv", "Confronto Comune - ISTAT, comune di Milano"),
         ("eta_sposi_milano_2021_2024.csv", "Eta' degli sposi, stime dalle classi di 5 anni, 2021-2024"),
         ("istat_eta_media_al_matrimonio_2004_2024.csv", "Eta' media al matrimonio, provincia di Milano e Italia (ISTAT)"),
         ("istat_primo_matrimonio_lombardia_italia_1990_2024.csv", "Eta' media al primo matrimonio, Lombardia, Italia (ISTAT)"),
         ("coppie_miste_milano_2003_2024.csv", "Quota di matrimoni con uno straniero, per anno, rito e perimetro"),
         ("istat_matrimoni_tipologia_coppia_2004_2024.csv", "Matrimoni per cittadinanza degli sposi, province e Italia (ISTAT)"),
         ("unioni_civili_riepilogo.csv", "Unioni civili a Milano 2016-2024 e confronto con l'Italia"),
         ("separazioni_divorzi_riepilogo.csv", "Separazioni e divorzi 2007-2024, Milano + Monza e Brianza e Italia (ISTAT)"),
         ("covid_2020.csv", "Il 2020 rispetto al 2019"),
         ("residenti_vs_celebrati_2011_2024.csv", "Nozze di residenti e nozze celebrate a Milano"),
         ("inventario.csv", "Elenco delle fonti: contenuto, anni, righe, licenza, cosa manca")]
for f, _ in FILES: shutil.copyfile(os.path.join(PU, f), os.path.join(OUT, f))
R["file"] = [dict(nome=f, descr=d) for f, d in FILES]
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# controlli interni: i numeri chiave coincidono con la fase di raccolta
assert N["civ_2024"]["v"] == 2018 and N["civ_1972"]["v"] == 3308 and N["rel_1961"]["v"] == 10525 and N["rel_2024"]["v"] == 474
assert N["sorpasso_milano"]["v"] == 2002 and N["sorpasso_italia"]["v"] == 2018
assert N["uc_totale"]["v"] == 1879 and N["res_rel_2011"]["v"] == 2780 and N["cel_rel_2011"]["v"] == 1080
print("OK", len(N), "numeri,", os.path.getsize(os.path.join(OUT, "riepilogo.json")), "byte")
for k in ("altrove_pct_2011", "altrove_pct_2018", "div_var_2014_2016_pct", "uc_quota_min", "uc_quota_max", "mi_su_it_matrimoni_2024_pct", "pm_max", "pm_max_anno", "q25_milano", "q25_italia", "civ_mediana_1972_2024"):
    print(k, N[k]["v"])
