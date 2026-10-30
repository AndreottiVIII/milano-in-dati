"""Fase 2, passo 2: indicatori armonizzati per NIL 2021 (88), municipio (9) e comune, anni 1991, 2001, 2011, 2021, 2023.
Uso: python -I h5_indicatori.py <cartella censimenti>
Input: pulito/sezioni_<anno>.csv, pulito/raccordo_sezioni_<anno>.csv (h1), ds1635 e ds1529 (Comune), pulito/nil_2021_anagrafica.csv
Output (in pulito/):
  sezioni_armonizzate.csv        una riga per sezione e anno con NIL/municipio assegnati e la fonte dell'assegnazione
  indicatori_NIL.csv             una riga per NIL e anno (conteggi e indicatori)
  indicatori_municipi.csv        idem per i 9 municipi
  indicatori_comune.csv          idem per tutto il comune (comprese le sezioni speciali)
  copertura_raccordo.csv         quanta popolazione e' stata collocata e con quale qualita', per anno
  sensibilita_ripartizione_area.csv  differenza tra assegnazione 'sezione intera' e 'ripartizione per area' (1991, 2001, 2011)
"""
import sys
import numpy as np
import pandas as pd

root = sys.argv[1]
P = root + "/pulito/"
C = root + "/raw/comune_ckan/"
YEARS = [1991, 2001, 2011, 2021, 2023]
AGE_COLS = [f"P{i}" for i in range(14, 30)]          # <5, 5-9, ..., 70-74, 75+  (stessa definizione in tutti gli anni)
MID = np.array([2.5 + 5 * i for i in range(15)] + [82.0])   # punti medi; 75+ fissato a 82 anni (vedi NOTE)

z91 = pd.read_csv(C + "ds1635-censimento-1991-sezioni-di-censimento-collegamento-tr/00_ds1635-censimento-1991-sezioni.csv", sep=";")
z01 = pd.read_csv(C + "ds1529-censimento-2001-sezioni/00_ds1529-censimento-2001-sezioni.csv", sep=";")
nilana = pd.read_csv(P + "nil_2021_anagrafica.csv")
SPECIAL_MIN = 8000000   # sezioni 888888x / 8888902 = senza fissa dimora, non collocabili in un NIL


def standard(y):
    """Restituisce un DataFrame con colonne standard per anno + chiave 'sez' + eventuali NIL/municipio ufficiali."""
    if y == 1991:
        d = pd.read_csv(P + "sezioni_1991.csv", low_memory=False); key = "SEZIONE"
        o = pd.DataFrame({"sez": d[key], "stran": d["ST16"], "grad": d["P47"], "edu_base": d["P46"], "occ": d["P61"],
                          "forze_lavoro": d["P60"], "fam": d["PF1"], "fam_comp_exact": d["PF2"], "fam1": d["PF3"],
                          "fam_big": d["PF8"] + d["PF9"] + d["PF10"], "abit_tot": d["A1"], "abit_occ": d["A2"]})
        o["fam_members_approx"] = d["PF3"] + 2 * d["PF4"] + 3 * d["PF5"] + 4 * d["PF6"] + 5 * d["PF7"] + 6 * o["fam_big"]
    elif y == 2001:
        d = pd.read_csv(P + "sezioni_2001.csv", low_memory=False); key = "SEZIONE"
        o = pd.DataFrame({"sez": d[key], "stran": d["ST07"], "grad": d["P47"], "edu_base": d["P46"], "occ": d["P61"],
                          "forze_lavoro": d["P60"], "fam": d["PF1"], "fam_comp_exact": d["PF2"], "fam1": d["PF3"],
                          "fam_big": d["PF8"], "abit_tot": d["A1"], "abit_occ": d["A2"]})
        o["fam_members_approx"] = d["PF3"] + 2 * d["PF4"] + 3 * d["PF5"] + 4 * d["PF6"] + 5 * d["PF7"] + 6 * d["PF8"]
    elif y == 2011:
        d = pd.read_csv(P + "sezioni_2011.csv", low_memory=False); key = "NSEZ"
        o = pd.DataFrame({"sez": d[key], "stran": d["ST1"], "grad": d["P47"], "edu_base": d["P46"], "occ": d["P61"],
                          "forze_lavoro": d["P60"], "fam": d["PF1"], "fam_comp_exact": d["PF2"], "fam1": d["PF3"],
                          "fam_big": d["PF8"], "abit_tot": d["A2"] + d["A3"], "abit_occ": d["A2"]})
        o["fam_members_approx"] = d["PF3"] + 2 * d["PF4"] + 3 * d["PF5"] + 4 * d["PF6"] + 5 * d["PF7"] + 6 * d["PF8"]
        o["mun_ufficiale"] = d["CODASC"]
    else:
        d = pd.read_csv(P + f"sezioni_{y}.csv", low_memory=False); key = "SEZ21_ID"
        o = pd.DataFrame({"sez": d[key].astype(str).str[-7:].astype(int), "stran": d["ST1"], "grad": d["P90"], "edu_base": d["P83"],
                          "occ": d["P101"], "forze_lavoro": np.nan, "fam": d["PF1"], "fam_comp_exact": np.nan, "fam1": d["PF3"],
                          "fam_big": d["PF8"], "abit_tot": d["A8"], "abit_occ": d["A2"]})
        o["fam_members_approx"] = d["PF3"] + 2 * d["PF4"] + 3 * d["PF5"] + 4 * d["PF6"] + 5 * d["PF7"] + 6 * d["PF8"]
        o["nil_ufficiale"] = d["COM_ASC2"] % 1000
        o["mun_ufficiale"] = d["COM_ASC1"] % 1000
        if y == 2023:
            for c in [c for c in d.columns if c.startswith("CIT_")]:
                o[c] = d[c]
    o["pop"] = d["P1"]
    o["pop_m"] = d["P2"] if "P2" in d else np.nan
    for c in AGE_COLS:
        o[c] = d[c]
    o["a0_14"] = d["P14"] + d["P15"] + d["P16"]
    o["a65p"] = d["P27"] + d["P28"] + d["P29"]
    o["a75p"] = d["P29"]
    o["eta_somma_classi"] = (d[AGE_COLS].values * MID).sum(axis=1)
    o["anno"] = y
    return o


rows, cover = [], []
for y in YEARS:
    s = standard(y)
    s["speciale"] = s.sez >= SPECIAL_MIN
    if y in (1991, 2001, 2011):
        r = pd.read_csv(P + f"raccordo_sezioni_{y}.csv")[["sezione", "nil", "municipio", "purezza_nil", "copertura", "purezza_mun"]]
        r = r.rename(columns={"nil": "nil_geom", "municipio": "mun_geom"})
        s = s.merge(r, left_on="sez", right_on="sezione", how="left").drop(columns="sezione")
        s["nil"] = s.nil_geom; s["nil_fonte"] = "sovrapposizione geometrica (area massima)"
        s["mun"] = s.mun_geom; s["mun_fonte"] = "sovrapposizione geometrica"
        if y == 1991:
            m = s.merge(z91, left_on="sez", right_on="CodSez", how="left")
            ok = m.Zona9.notna() & (m.Zona9 > 0)
            s.loc[ok.values, "mun"] = m.loc[ok, "Zona9"].values; s.loc[ok.values, "mun_fonte"] = "Comune ds1635 Zona9"
        if y == 2001:
            m = s.merge(z01, left_on="sez", right_on="CodSez", how="left")
            ok = m.CodNIL.between(1, 88)
            s.loc[ok.values, "nil"] = m.loc[ok, "CodNIL"].values; s.loc[ok.values, "nil_fonte"] = "Comune ds1529 CodNIL"
            ok = m.Zona9.notna() & (m.Zona9 > 0)
            s.loc[ok.values, "mun"] = m.loc[ok, "Zona9"].values; s.loc[ok.values, "mun_fonte"] = "Comune ds1529 Zona9"
        if y == 2011:
            ok = s.mun_ufficiale.between(1, 9)
            s.loc[ok, "mun"] = s.loc[ok, "mun_ufficiale"]; s.loc[ok, "mun_fonte"] = "ISTAT 2011 CODASC"
    else:
        s["nil"] = s.nil_ufficiale; s["nil_fonte"] = "ISTAT 2021 COM_ASC2"
        s["mun"] = s.mun_ufficiale; s["mun_fonte"] = "ISTAT 2021 COM_ASC1"
        s["purezza_nil"] = 1.0; s["copertura"] = 1.0; s["purezza_mun"] = 1.0
    s.loc[s.speciale, ["nil", "mun"]] = np.nan
    s.loc[s.speciale, ["nil_fonte", "mun_fonte"]] = "sezione speciale (senza fissa dimora): non collocata"
    rows.append(s)
    tot = s["pop"].sum()
    placed = s[s.nil.notna()]
    cover.append(dict(anno=y, sezioni=len(s), popolazione_totale=int(tot),
                      sezioni_speciali=int(s.speciale.sum()), pop_sezioni_speciali=int(s[s.speciale]["pop"].sum()),
                      pop_collocata_in_NIL=int(placed["pop"].sum()), quota_collocata=round(placed["pop"].sum() / tot, 5),
                      pop_con_assegnazione_ufficiale_Comune_o_ISTAT=int(placed[~placed.nil_fonte.str.startswith("sovrapp")]["pop"].sum()),
                      pop_in_sezioni_purezza_lt_90=int(placed[placed.purezza_nil < 0.9]["pop"].sum()),
                      quota_pop_purezza_lt_90=round(placed[placed.purezza_nil < 0.9]["pop"].sum() / tot, 4),
                      quota_pop_purezza_lt_99=round(placed[placed.purezza_nil < 0.99]["pop"].sum() / tot, 4),
                      nil_con_dati=int(placed.nil.nunique())))
S = pd.concat(rows, ignore_index=True)
S.to_csv(P + "sezioni_armonizzate.csv", index=False)
pd.DataFrame(cover).to_csv(P + "copertura_raccordo.csv", index=False)
pd.set_option("display.width",250); pd.set_option("display.max_columns",30)
print(pd.DataFrame(cover).T)

# ------------------------------------------------------------------ aggregazione
SUMC = ["pop", "a0_14", "a65p", "a75p", "eta_somma_classi", "stran", "grad", "edu_base", "occ", "fam", "fam_comp_exact",
        "fam1", "fam_members_approx", "abit_tot", "abit_occ", "forze_lavoro"] + AGE_COLS + [c for c in S.columns if c.startswith("CIT_")]


def indicators(g):
    g = g.copy()
    pop = g["pop"]
    g["pop_15_64"] = pop - g.a0_14 - g.a65p
    g["quota_0_14"] = 100 * g.a0_14 / pop
    g["quota_65p"] = 100 * g.a65p / pop
    g["quota_75p"] = 100 * g.a75p / pop
    g["indice_vecchiaia"] = 100 * g.a65p / g.a0_14
    g["eta_media_classi"] = g.eta_somma_classi / pop
    g["quota_stranieri"] = 100 * g.stran / pop
    g["quota_laureati_su_base"] = 100 * g.grad / g.edu_base
    g["quota_laureati_su_residenti"] = 100 * g.grad / pop
    g["famiglie_comp_medio_approx"] = g.fam_members_approx / g.fam
    g["famiglie_comp_medio_esatto"] = g.fam_comp_exact / g.fam
    g["quota_famiglie_1_comp"] = 100 * g.fam1 / g.fam
    g["abit_non_occ_da_residenti"] = g.abit_tot - g.abit_occ
    g["quota_abit_non_occ_da_residenti"] = 100 * g.abit_non_occ_da_residenti / g.abit_tot
    g["tasso_occupazione_15_64_approx"] = 100 * g.occ / g.pop_15_64
    g["tasso_occupazione_15piu"] = 100 * g.occ / (pop - g.a0_14)
    g.loc[g.anno >= 2021, "tasso_occupazione_15piu"] = np.nan   # 2021/2023: occupati solo 15-64 anni, non confrontabile
    return g


def agg(by):
    out = []
    for y in YEARS:
        s = S[S.anno == y]
        s = s[s[by].notna()] if by else s
        grp = s.groupby(by)[SUMC].sum(min_count=1).reset_index() if by else s[SUMC].sum(min_count=1).to_frame().T
        grp.insert(0, "anno", y)
        out.append(grp)
    return indicators(pd.concat(out, ignore_index=True))


nil = agg("nil"); nil["nil"] = nil.nil.astype(int)
nil = nil.merge(nilana[["nil", "nil_nome", "municipio_prevalente", "area_km2"]], on="nil", how="left")
nil["densita_ab_km2"] = nil["pop"] / nil.area_km2
nil.to_csv(P + "indicatori_NIL.csv", index=False)
mun = agg("mun"); mun["mun"] = mun.mun.astype(int); mun.to_csv(P + "indicatori_municipi.csv", index=False)
com = agg(None); com.to_csv(P + "indicatori_comune.csv", index=False)
print(com[["anno", "pop", "quota_0_14", "quota_65p", "quota_75p", "indice_vecchiaia", "eta_media_classi", "stran", "quota_stranieri",
           "quota_laureati_su_base", "quota_laureati_su_residenti", "famiglie_comp_medio_approx", "famiglie_comp_medio_esatto",
           "quota_famiglie_1_comp", "quota_abit_non_occ_da_residenti", "tasso_occupazione_15_64_approx"]].round(2).T)

# ------------------------------------------------------------------ sensibilita': ripartizione per area
sens = []
for y in (1991, 2001, 2011):
    q = pd.read_csv(P + f"raccordo_quote_area_{y}.csv")
    q["w"] = q.quota_area / q.groupby("sezione").quota_area.transform("sum")
    s = S[(S.anno == y) & S.nil.notna()][["sez", "pop", "a65p", "stran", "nil"]]
    m = q.merge(s, left_on="sezione", right_on="sez")
    m["pop_a"] = m.w * m["pop"]; m["a65_a"] = m.w * m.a65p; m["str_a"] = m.w * m.stran
    ar = m.groupby("nil_x")[["pop_a", "a65_a", "str_a"]].sum().rename_axis("nil").reset_index()
    ai = S[(S.anno == y) & S.nil.notna()].groupby("nil")[["pop", "a65p", "stran"]].sum().reset_index()
    ai["nil"] = ai.nil.astype(int)
    c = ai.merge(ar, on="nil", how="outer").fillna(0)
    c["anno"] = y
    c["diff_pop_pct"] = 100 * (c.pop_a - c["pop"]) / c["pop"]
    c["quota65_intera"] = 100 * c.a65p / c["pop"]; c["quota65_area"] = 100 * c.a65_a / c.pop_a
    c["quota_str_intera"] = 100 * c.stran / c["pop"]; c["quota_str_area"] = 100 * c.str_a / c.pop_a
    sens.append(c)
sens = pd.concat(sens)
sens.round(3).to_csv(P + "sensibilita_ripartizione_area.csv", index=False)
for y, g in sens.groupby("anno"):
    print(y, "NIL: diff pop %% assoluta mediana %.2f, max %.2f | diff quota65 (punti) max %.2f | diff quota stranieri (punti) max %.2f" % (
        g.diff_pop_pct.abs().median(), g.diff_pop_pct.abs().max(), (g.quota65_intera - g.quota65_area).abs().max(),
        (g.quota_str_intera - g.quota_str_area).abs().max()))
