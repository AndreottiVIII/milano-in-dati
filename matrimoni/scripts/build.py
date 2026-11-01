"""Pulizia: dai file grezzi in raw/ alle tabelle ordinate (tidy) in pulito/.
Uso: python -I -X utf8 build.py <percorso assoluto di matrimoni> <percorso assoluto di milano-in-dati>
Nulla viene eseguito dai file scaricati: sono solo letti come dati."""
import sys, os, json, csv, re
import pandas as pd

M, P = sys.argv[1], sys.argv[2]
RAW, OUT = os.path.join(M, "raw"), os.path.join(M, "pulito")
os.makedirs(OUT, exist_ok=True)
log = []

def save(df, name):
    df.to_csv(os.path.join(OUT, name), index=False, encoding="utf-8", sep=";")
    log.append(f"{name};{len(df)} righe")
    print(name, len(df))

def rc(path, **k):
    return pd.read_csv(os.path.join(RAW, path), sep=";", encoding="utf-8-sig", **k)

# ---------------------------------------------------------------- Comune di Milano
# 1. Serie storica civile/religioso dal 1948 (ds1496)
h = rc("comune_ds1496/ds1496_matrimoni_dal_1948.csv")
rows = []
for _, r in h.iterrows():
    for col, rito in (("Rito civile", "civile"), ("Rito religioso", "religioso")):
        n = int(r[col]); usato = n; nota = ""
        if int(r["Anno"]) == 2024 and rito == "civile":
            usato = 2018
            nota = "Il file ds1496 dice 2218; ds1947 e ds1950 (Comune, stesso anno) e ISTAT (demo.istat.it MA1) dicono 2018: sembra un refuso di 200; uso 2018"
        if int(r["Anno"]) == 1972 and rito == "civile":
            nota = "Raddoppio dal 1971 (1460 -> 3308); in tutta Italia i civili raddoppiano nel 1972 (ISTAT MA4: 15.591 -> 30.674): coerente col divorzio (L. 898/1970), la causa e' una mia deduzione"
        rows.append(dict(anno=int(r["Anno"]), rito=rito, n_fonte=n, n_usato=usato, nota=nota,
                         fonte="comune_ds1496/ds1496_matrimoni_dal_1948.csv campi Rito civile / Rito religioso"))
rito48 = pd.DataFrame(rows); save(rito48, "rito_milano_1948_2024.csv")

# 2. Dettaglio per rito e cittadinanza: celebrati a Milano (ds138 2003-2020 + ds1947 2021-2024)
#    e con almeno un coniuge residente (ds132 2011-2020 + ds1949 2021-2024)
def tidy(path, perimetro, fonte):
    d = rc(path)
    d.columns = ["anno", "rito", "cit_marito", "cit_moglie", "n"]
    d["rito"] = d["rito"].str.strip()
    for c in ("cit_marito", "cit_moglie"):
        d[c] = d[c].fillna("n.d.").str.lower().replace({"italiana": "italiana", "straniera": "straniera"})
    d["perimetro"] = perimetro; d["fonte"] = fonte
    return d
parts = [tidy("comune_ds138/ds138-popolazione-matrimoni-celebrati.csv", "celebrati_a_milano", "comune_ds138"),
         tidy("comune_ds1947/ds1947-popolazione-matrimoni-celebrati-rito.csv", "celebrati_a_milano", "comune_ds1947"),
         tidy("comune_ds132/ds132-popolazione-matrimoni-coniuge-residente.csv", "almeno_un_coniuge_residente", "comune_ds132"),
         tidy("comune_ds1949/ds1949-popolazione-matrimoni-residenti-rito.csv", "almeno_un_coniuge_residente", "comune_ds1949")]
rc_all = pd.concat(parts, ignore_index=True)
rc_all["rito"] = rc_all["rito"].str.lower().replace({"altri riti": "altri_riti"})
save(rc_all[["perimetro", "anno", "rito", "cit_marito", "cit_moglie", "n", "fonte"]], "matrimoni_rito_cittadinanza_milano.csv")

# totale per anno e rito (tutti i riti) nei due perimetri
tot = rc_all.groupby(["perimetro", "anno", "rito"], as_index=False)["n"].sum()
save(tot, "matrimoni_rito_per_anno_milano.csv")

# 3. Eta' degli sposi (ds1950, ds1952): classi quinquennali marito x moglie, 2021-2024
def eta(path, perimetro, fonte):
    d = rc(path)
    d.columns = ["anno", "classe_eta_marito", "classe_eta_moglie", "n"]
    d["perimetro"] = perimetro; d["fonte"] = fonte
    return d
ea = pd.concat([eta("comune_ds1950/ds1950-popolazione-matrimoni-celebrati-eta.csv", "celebrati_a_milano", "comune_ds1950"),
                eta("comune_ds1952/ds1952-popolazione-matrimoni-residenti-eta.csv", "almeno_un_coniuge_residente", "comune_ds1952")], ignore_index=True)
save(ea[["perimetro", "anno", "classe_eta_marito", "classe_eta_moglie", "n", "fonte"]], "matrimoni_eta_milano_2021_2024.csv")

# 4. Unioni civili (ds398)
u = rc("comune_ds398/ds398_unioni_civili_celebrate_2016_2024.csv")
u.columns = ["anno", "luogo", "sesso_coppia", "classe_eta_partner1", "cit_partner1", "classe_eta_partner2", "cit_partner2", "n"]
u["sesso_coppia"] = u["sesso_coppia"].map({"Maschi": "uomini", "Femmine": "donne"})
u["cit_partner1"] = u["cit_partner1"].str.lower(); u["cit_partner2"] = u["cit_partner2"].str.lower()
u["fonte"] = "comune_ds398"
save(u, "unioni_civili_milano_2016_2024.csv")
uc = u.groupby(["anno", "sesso_coppia"], as_index=False)["n"].sum()
save(uc, "unioni_civili_per_anno_sesso_milano.csv")

# 5. Scioglimenti 2018 (ds705): record individuali anonimi -> solo aggregati
s = rc("comune_ds705/ds705_scioglimenti-di-matrimonio-2018_.csv")
s.columns = ["anno", "comune", "sesso1", "nasc1", "cit1", "sesso2", "nasc2", "cit2"]
s["eta1"] = s["anno"] - s["nasc1"]; s["eta2"] = s["anno"] - s["nasc2"]
s["entrambi_italiani"] = (s["cit1"].str.upper() == "ITALIA") & (s["cit2"].str.upper() == "ITALIA")
s["uno_italiano"] = (s["cit1"].str.upper() == "ITALIA") ^ (s["cit2"].str.upper() == "ITALIA")
sc = pd.DataFrame([dict(
    anno=2018, scioglimenti=len(s), eta_media_marito=round(s["eta1"].mean(), 1), eta_media_moglie=round(s["eta2"].mean(), 1),
    mediana_marito=float(s["eta1"].median()), mediana_moglie=float(s["eta2"].median()),
    entrambi_italiani=int(s["entrambi_italiani"].sum()), uno_solo_italiano=int(s["uno_italiano"].sum()),
    nessuno_italiano=int((~s["entrambi_italiani"] & ~s["uno_italiano"]).sum()),
    moglie_piu_grande=int((s["eta2"] > s["eta1"]).sum()),
    nasc_mancanti=int(s["nasc1"].isna().sum() + s["nasc2"].isna().sum()),
    fonte="comune_ds705 (sesso/nascita/cittadinanza dei due coniugi; niente anno di matrimonio ne' tipo di scioglimento)")])
save(sc, "scioglimenti_2018_comune_milano_aggregati.csv")

# 6. Indicatori famiglie/coppie dei censimenti (ds361), solo Milano
f = pd.read_csv(os.path.join(RAW, "comune_ds361/ds361_popolazione_indicatori_caratteristiche_famiglie_coppie_2011c.csv"), sep=";", encoding="cp1252")
f = f[f["Territorio"] == "Milano"][["Anno", "Indicatore", "Valore indicatore"]].copy()
f.columns = ["anno", "indicatore", "valore"]
f["valore"] = pd.to_numeric(f["valore"].astype(str).str.replace(",", ".").replace({"-": None}), errors="coerce").round(1)
f = f[f["indicatore"].str.contains("Coppie miste|Coppie non coniugate")]
f["fonte"] = "comune_ds361 (censimenti 1991/2001/2011; '-' = non disponibile nel 1991)"
save(f, "coppie_miste_non_coniugate_censimenti_milano.csv")

# ---------------------------------------------------------------- ISTAT demo.istat.it (JSON grezzi)
def jl(name):
    return json.load(open(os.path.join(RAW, "istat_demo", name + ".json"), encoding="utf-8"))["datatable"]
def num(x, sep):  # sep = separatore delle migliaia nel testo ISTAT
    if x is None or x == "": return None
    if isinstance(x, (int, float)): return x
    x = str(x)
    if sep == ".": return float(x.replace(".", "").replace(",", "."))
    return float(x.replace(",", ""))
def dec(x):  # decimale con virgola
    return None if x in (None, "") else float(str(x).replace(",", "."))

# 6a. Comune di Milano per rito 2004-2024
d = pd.DataFrame(jl("ma1_q1_comune_milano_rito")["data"])[["anno", "rel", "civil", "tot"]]
d.columns = ["anno", "religiosi", "civili", "totale"]; d["fonte"] = "istat_demo MA1 query1 comune 015146"
save(d, "istat_milano_comune_rito_2004_2024.csv")
istat_mi = d
# 6b. Italia per rito 1930-2024 (serie storica MA4)
d = pd.DataFrame(jl("ma4_q1_rito_serie_storica")["data"])
d = pd.DataFrame(dict(anno=d["anno"], religiosi=d["rel"].map(lambda x: num(x, ",")), civili=d["civil"].map(lambda x: num(x, ",")), totale=d["tot"].map(lambda x: num(x, ","))))
d["quota_civili_pct"] = (100 * d["civili"] / d["totale"]).round(1); d["fonte"] = "istat_demo MA4 query1 (Italia)"
save(d, "istat_italia_rito_1930_2024.csv")
# 6c. Italia 2004-2024 MA1 (per controllo)
d2 = pd.DataFrame(jl("ma1_q1_italia_rito")["data"])[["anno", "rel", "civil", "tot"]]
d2.columns = ["anno", "religiosi", "civili", "totale"]; d2["fonte"] = "istat_demo MA1 query1 Italia"
save(d2, "istat_italia_rito_2004_2024_ma1.csv")
# 6d. Indicatori di nuzialita' provincia Milano, Monza e Brianza, Lombardia (riga regione), Italia
cols = {"fmrbrgrall_110": "primonuzialita_sposi_per1000", "fmrbrall_110": "primonuzialita_spose_per1000", "cmarrgp_110": "matrimoni_civili_pct",
        "jownpp_110": "comunione_beni_pct", "maralfsp_110": "almeno_uno_straniero_pct", "brgrasm_110": "sposi_secondo_o_succ_pct",
        "brasm_110": "spose_secondo_o_succ_pct", "nupt_totm_tage": "tasso_nuzialita_totale_sposi_per1000", "nupt_totw_tage": "tasso_nuzialita_totale_spose_per1000",
        "nuptrate_110": "quoziente_nuzialita_per1000"}
ind = []
for nome, terr in (("ma1_q3_indicatori_provincia_milano", "provincia_milano"), ("ma1_q3_indicatori_provincia_monza", "provincia_monza_brianza"), ("ma1_q3_indicatori_italia", "italia")):
    for r in jl(nome)["data"]:
        o = {"territorio": terr, "anno": r["anno"]}
        for k, v in cols.items(): o[v] = dec(r.get(k))
        ind.append(o)
ind = pd.DataFrame(ind); ind["fonte"] = "istat_demo MA1 query3"
save(ind, "istat_indicatori_nuzialita_2004_2024.csv")
# 6e. Eta' media al matrimonio per stato civile precedente
em = []
for sx, sesso in (("sposi", "sposi"), ("spose", "spose")):
    for nome, terr in ((f"ma1_q4_eta_media_{sx}_provincia_milano", "provincia_milano"), (f"ma1_q4_eta_media_{sx}_italia", "italia")):
        for r in jl(nome)["data"]:
            em.append(dict(territorio=terr, sesso=sesso, anno=r["anno"], eta_media_celibe_nubile=dec(r["statociv_1"]), eta_media_divorziato=dec(r["statociv_3"]),
                           eta_media_vedovo=dec(r["statociv_4"]), eta_media_totale=dec(r["statociv_99"])))
em = pd.DataFrame(em); em["fonte"] = "istat_demo MA1 query4"
save(em, "istat_eta_media_al_matrimonio_2004_2024.csv")
# 6f. Primo matrimonio: eta' media, Lombardia e Italia (NU1, dal 1990)
npm = []
for nome, ind_n in (("nu1_q1_eta_media_sposi_primo_matrimonio_regioni", "eta_media_sposi_primo_matrimonio"), ("nu1_q1_eta_media_spose_primo_matrimonio_regioni", "eta_media_spose_primo_matrimonio"),
                    ("nu1_q1_eta_media_sposi_primo_matrimonio_ripartizioni", "eta_media_sposi_primo_matrimonio"), ("nu1_q1_eta_media_spose_primo_matrimonio_ripartizioni", "eta_media_spose_primo_matrimonio"),
                    ("nu1_q1_primonuzialita_sposi_regioni", "tasso_primonuzialita_totale_sposi"), ("nu1_q1_primonuzialita_spose_regioni", "tasso_primonuzialita_totale_spose")):
    for r in jl(nome)["data"]:
        for c, v in r.items():
            m = re.fullmatch(r"a(\d{4})", c)
            if m and 1990 <= int(m.group(1)) <= 2024:
                npm.append(dict(indicatore=ind_n, anno=int(m.group(1)), territorio=r["denominazione"], valore=dec(v)))
npm = pd.DataFrame(npm).drop_duplicates(); npm["fonte"] = "istat_demo NU1 query1 (territorio REG / RIP)"
save(npm[npm["territorio"].str.contains("Lombardia|Italia|Nord-ovest")], "istat_primo_matrimonio_lombardia_italia_1990_2024.csv")
# 6g. Tipologia di coppia (cittadinanza) provincia Milano, Monza, Lombardia, Italia
tc = []
lab = {"tipcoppia_4": "entrambi_italiani", "tipcoppia_1": "sposo_italiano_sposa_straniera", "tipcoppia_2": "sposo_straniero_sposa_italiana", "tipcoppia_3": "entrambi_stranieri",
       "tipcoppia_8": "almeno_uno_straniero", "tipcoppia_9": "totale"}
for nome, terr in (("ma3_q1_tipologia_coppia_provincia_milano", "provincia_milano"), ("ma3_q1_tipologia_coppia_provincia_monza", "provincia_monza_brianza"),
                   ("ma3_q1_tipologia_coppia_lombardia", "lombardia"), ("ma3_q1_tipologia_coppia_italia", "italia")):
    for r in jl(nome)["data"]:
        o = {"territorio": terr, "anno": r["anno"]}
        for k, v in lab.items(): o[v] = num(r.get(k), ".")
        tc.append(o)
tc = pd.DataFrame(tc); tc["fonte"] = "istat_demo MA3 query1 (valori assoluti)"
save(tc, "istat_matrimoni_tipologia_coppia_2004_2024.csv")
# 6h. Rito x tipologia di coppia, provincia Milano
rt = []
for nome, terr in (("ma3_q3_rito_tipologia_provincia_milano", "provincia_milano"), ("ma3_q3_rito_tipologia_italia", "italia")):
    for r in jl(nome)["data"]:
        o = {"territorio": terr, "anno": r["anno"], "rito": r["descrizione"].lower()}
        for k, v in lab.items(): o[v] = num(r.get(k), ".")
        rt.append(o)
rt = pd.DataFrame(rt); rt["fonte"] = "istat_demo MA3 query3 (valori assoluti)"
save(rt, "istat_matrimoni_rito_tipologia_2004_2024.csv")
# 6i. Unioni civili: Milano comune (grandi comuni, UC4), provincia/Italia per sesso e mese (UC2)
a = pd.DataFrame(jl("uc4_q4_unioni_grandi_comuni_milano")["data"])
a = pd.DataFrame(dict(territorio="comune_milano", anno=a["anno"], uomini=a["sesso_1"].map(lambda x: num(x, ".")), donne=a["sesso_2"].map(lambda x: num(x, ".")), totale=a["sesso_9"].map(lambda x: num(x, "."))))
b = pd.DataFrame(jl("uc4_q4_unioni_grandi_comuni_totale")["data"])
print("UC4 totale grandi comuni colonne:", list(b.columns))
b = pd.DataFrame(dict(territorio="totale_grandi_comuni", anno=b["anno"], uomini=b["sesso_1"].map(lambda x: num(x, ".")), donne=b["sesso_2"].map(lambda x: num(x, ".")), totale=b["sesso_9"].map(lambda x: num(x, "."))))
mm = []
for nome, terr in (("uc2_q1_unioni_sesso_mese_provincia_milano", "provincia_milano"), ("uc2_q1_unioni_sesso_mese_italia", "italia")):
    x = pd.DataFrame(jl(nome)["data"])
    x = x[x["mese"] == 13].copy()  # riga 'Tutti i mesi' (le righe 1-12 sono i mesi): niente somma, per non contare due volte
    x = x.groupby("anno", as_index=False)[["maschi", "femmine", "totale"]].sum()
    mm.append(pd.DataFrame(dict(territorio=terr, anno=x["anno"], uomini=x["maschi"], donne=x["femmine"], totale=x["totale"])))
uc2 = pd.concat([a, b] + mm, ignore_index=True); uc2["fonte"] = "istat_demo UC4 query4 (grandi comuni) / UC2 query1 (sesso e mese, riga 'Tutti i mesi')"
save(uc2, "istat_unioni_civili_2018_2024.csv")

# ---------------------------------------------------------------- ISTAT separazioni e divorzi (xls/xlsx)
def prov_table(fn, tipo):
    d = pd.read_excel(os.path.join(RAW, "istat_sepdiv", fn), header=None)
    hdr = d.index[d[0].astype(str).str.strip() == "Codice"][0]
    years = [int(re.match(r"\d{4}", str(v)).group()) for v in d.iloc[hdr, 2:]]
    out = []
    for _, r in d.iloc[hdr + 1:].iterrows():
        name = str(r[1]).strip()
        if name in ("nan", ""): continue
        if str(r[0]).strip() in ("nan", "Codice") and name != "ITALIA": continue
        for y, v in zip(years, r[2:]):
            v = None if str(v).strip() in ("-", "nan") else float(v)
            out.append(dict(tipo=tipo, anno=y, provincia=name, n=v))
    return pd.DataFrame(out)
sd = pd.concat([prov_table("seriestoriche__tavola_1.5.xlsx", "separazioni"), prov_table("seriestoriche__tavola_2.5.xlsx", "divorzi")], ignore_index=True)
sd["fonte"] = "istat_sepdiv seriestoriche tavola 1.5 / 2.5 (valori assoluti stimati; provincia del tribunale o dell'ufficio di stato civile; divorzi 2024 includono scioglimenti di unioni civili)"
sel = sd[sd["provincia"].isin(["Milano", "Monza e della Brianza", "ITALIA", "Lodi", "Como", "Varese", "Pavia"])]
save(sel, "istat_separazioni_divorzi_province_2007_2024.csv")
# serie omogenea: Milano + Monza e Brianza (prima del 2010 Monza e' dentro Milano)
pv = sel.pivot_table(index=["tipo", "anno"], columns="provincia", values="n", aggfunc="first").reset_index()
pv["milano_piu_monza"] = pv["Milano"] + pv["Monza e della Brianza"].fillna(0)
pv = pv.rename(columns={"Milano": "milano_provincia", "Monza e della Brianza": "monza_brianza", "ITALIA": "italia"})
save(pv[["tipo", "anno", "milano_provincia", "monza_brianza", "milano_piu_monza", "italia"]], "separazioni_divorzi_milano_piu_monza_2007_2024.csv")

open(os.path.join(OUT, "build_log.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
