"""Fase 2, passo 3 (Milano dal 1861): serie del comune ripulita, con le variazioni di confine marcate, e struttura per eta' 1881-2011.
Uso: python -I h6_storia.py <cartella censimenti>
Output (pulito/): serie_milano_1861_2023.csv, variazioni_confini_milano.csv, eta_storica_milano_1881_2011.csv, serie_annuale_milano_1880_2025_flag.csv
"""
import sys, re
import numpy as np
import pandas as pd

root = sys.argv[1]
P = root + "/pulito/"
C = root + "/raw/comune_ckan/"

# ---------------- variazioni di confine: fonti primarie in raw/storia_confini (Normattiva) ---------------------------
var = pd.DataFrame([
    dict(data_decreto="1873-06-08", in_vigore="1873-09-01", atto="Regio decreto 8 giugno 1873, n. 1413",
         effetto="Il Comune dei Corpi Santi e' unito al Comune di Milano (dal 1 settembre 1873)",
         comuni_annessi="Corpi Santi", n_comuni=1, anno_primo_censimento_dopo=1881,
         fonte="Normattiva (testo letto il 30/10/2026); GU n. 168 del 19-06-1873", file="raw/storia_confini/normattiva_regio.decreto_1873-06-08_1413.html"),
    dict(data_decreto="1918-01-31", in_vigore="1918-03-27", atto="Decreto luogotenenziale 31 gennaio 1918, n. 209",
         effetto="Il comune di Turro Milanese e' aggregato integralmente a Milano",
         comuni_annessi="Turro Milanese", n_comuni=1, anno_primo_censimento_dopo=1921,
         fonte="Normattiva; GU n. 60 del 12-03-1918", file="raw/storia_confini/normattiva_decreto.luogotenenziale_1918-01-31_209.html"),
    dict(data_decreto="1923-09-02", in_vigore="1923-10-14", atto="Regio decreto 2 settembre 1923, n. 1912",
         effetto="Undici comuni contermini riuniti nell'unico comune di Milano",
         comuni_annessi="Affori; Baggio; Chiaravalle Milanese; Crescenzago; Gorla-Precotto; Greco Milanese; Lambrate; Musocco; Niguarda; Trenno; Vigentino",
         n_comuni=11, anno_primo_censimento_dopo=1931,
         fonte="Normattiva art. 1 (testo letto il 30/10/2026); GU n. 229 del 29-09-1923. Nota: il decreto dice 'Gorla-Precotto' (Gorla Primo + Precotto, uniti nel 1920 con R.D. 1 luglio 1920 n. 1013 secondo Wikipedia).",
         file="raw/storia_confini/normattiva_RD_1923-09-02_n1912.html"),
    dict(data_decreto="1924-01-23", in_vigore="1924-01-23", atto="(non letto su fonte primaria)",
         effetto="Passano a Milano le frazioni Lorenteggio (da Corsico) e Ronchetto sul Naviglio (da Buccinasco); dal 1 gennaio 1925 Morsenchio (da Linate al Lambro) e parte di San Donato Milanese",
         comuni_annessi="porzioni di Corsico, Buccinasco, Linate al Lambro, San Donato Milanese", n_comuni=0, anno_primo_censimento_dopo=1931,
         fonte="Solo it.wikipedia 'Comuni aggregati a Milano' (estratto in raw/storia_confini): DA VERIFICARE con la Gazzetta Ufficiale", file="raw/storia_confini/wikipedia_it_Comuni_aggregati_a_Milano_estratto.txt"),
    dict(data_decreto="1932", in_vigore="1932", atto="(non letto su fonte primaria)",
         effetto="Milano cede Poasco e una porzione dell'antico comune di Chiaravalle a San Donato Milanese (compensazione)",
         comuni_annessi="(cessione)", n_comuni=0, anno_primo_censimento_dopo=1936,
         fonte="Solo it.wikipedia 'Comuni aggregati a Milano': DA VERIFICARE", file="raw/storia_confini/wikipedia_it_Comuni_aggregati_a_Milano_estratto.txt"),
])
var.to_csv(P + "variazioni_confini_milano.csv", index=False)

# ---------------- serie censuaria -------------------------------------------------------------------------------
old = pd.read_csv(P + "popolazione_comune_1861_2021.csv")
ep = old[old.confini == "confini_dell_epoca"].set_index("anno")
c91 = old[old.confini == "confini_al_20_ott_1991"].set_index("anno")
years = sorted(set(old.anno))
rows = []
for y in years:
    r = dict(anno=y)
    r["pop_confini_epoca"] = ep.popolazione_residente.get(y, np.nan)
    r["superficie_km2_epoca"] = ep.superficie_km2.get(y, np.nan)
    r["pop_confini_1991_ricostruita_ISTAT"] = c91.popolazione_residente.get(y, np.nan)
    cur = old[(old.anno == y) & (old.confini == "confini_attuali")]
    r["pop_confini_attuali_somma_sezioni"] = cur.popolazione_residente.iloc[0] if len(cur) else np.nan
    rows.append(r)
s = pd.DataFrame(rows)
# 2021 e 2023 usano i confini attuali (uguali a quelli 1991 per superficie: 181.8 km2) e sono conteggi di sezioni
s["pop_serie_continua_1991"] = s.pop_confini_1991_ricostruita_ISTAT.fillna(s.pop_confini_attuali_somma_sezioni)
s.loc[s.anno.isin([2001, 2011]), "pop_serie_continua_1991"] = s.loc[s.anno.isin([2001, 2011]), "pop_confini_epoca"]
s["indice_1861_100_conf1991"] = (100 * s.pop_serie_continua_1991 / s.loc[s.anno == 1861, "pop_serie_continua_1991"].iloc[0]).round(1)
s["var_pct_su_censimento_prec_conf1991"] = (100 * s.pop_serie_continua_1991.pct_change()).round(1)
s["nota_confini"] = ""
s.loc[s.anno == 1881, "nota_confini"] = "dopo annessione Corpi Santi (1873): superficie da 9,7 a 72,9 km2; serie 'epoca' NON confrontabile con 1871"
s.loc[s.anno == 1921, "nota_confini"] = "Turro Milanese annesso nel 1918 (dato 'epoca' 1921 lo include: da verificare)"
s.loc[s.anno == 1931, "nota_confini"] = "dopo annessione di 11 comuni (1923): superficie da 76,3 a 187,2 km2; serie 'epoca' NON confrontabile con 1921"
s.loc[s.anno == 1971, "nota_confini"] = "cifra tonda 1.732.000 nel volume ISTAT 1994 contro 1.728.686 in ds303"
s.loc[s.anno == 1981, "nota_confini"] = "superficie 171,7 km2 in ds303: probabile errore (nessuna variazione di confine nota 1971-1991)"
s.loc[s.anno == 2023, "nota_confini"] = "censimento permanente al 31.12.2023 (somma sezioni); include 10.038 persone senza fissa dimora in sezione fittizia"
s.to_csv(P + "serie_milano_1861_2023.csv", index=False)
print(s[["anno", "pop_confini_epoca", "superficie_km2_epoca", "pop_confini_1991_ricostruita_ISTAT", "pop_serie_continua_1991",
         "indice_1861_100_conf1991", "var_pct_su_censimento_prec_conf1991"]].to_string())

# ---------------- serie annuale calcolata con flag ---------------------------------------------------------------
a = pd.read_csv(P + "popolazione_milano_annuale_1880_calcolata.csv")
a["var_assoluta"] = a.popolazione_calcolata.diff()
a["var_pct"] = (100 * a.popolazione_calcolata.pct_change()).round(2)
a["flag_confini"] = ""
a.loc[a.anno == 1923, "flag_confini"] = "annessione 11 comuni (R.D. 1912/1923): salto non demografico"
a.loc[a.anno == 1918, "flag_confini"] = "Turro Milanese (D.L. 209/1918)"
a.to_csv(P + "serie_annuale_milano_1880_2025_flag.csv", index=False)
print(a[a.anno.between(1916, 1926)].to_string())
big = a.loc[a.var_pct.abs().sort_values(ascending=False).index[:6]]
print(big)

# ---------------- struttura per eta' 1881-2011 (ds300: eta' singola o a gruppi, Milano) ----------------------------------
d = pd.read_csv(C + "ds300_popolazione-censimenti-storici-popolazione-per-eta-188/00_ds300_popolazione_popolazione-storico-eta_1881-2011.csv",
                sep=";", dtype=str, encoding="cp1252")
d.columns = ["anno", "eta", "genere", "n"]
d["anno"] = d.anno.astype(int)
d["n"] = pd.to_numeric(d.n.str.replace(".", "", regex=False), errors="coerce").fillna(0)


def parse_age(s):
    s = s.replace(" ", " ").strip()
    if s.isdigit():
        a = int(s); return a, a, a
    m = re.match(r"^(\d+)-(\d+)$", s)
    if m:
        a, b = int(m.group(1)), int(m.group(2)); return a, b, (a + b) / 2 + 0.5
    m = re.match(r"^(\d+) e pi", s)
    if m:
        a = int(m.group(1)); return a, 120, a + 2.5
    return None, None, None      # 'Eta' ignota'


pa = d.eta.map(parse_age)
d["lo"] = [x[0] for x in pa]; d["hi"] = [x[1] for x in pa]; d["mid"] = [x[2] for x in pa]
print("eta' ignota (persone):", d[d.lo.isna()].groupby("anno").n.sum().to_dict())
out = []
for y, g in d.groupby("anno"):
    tot_all = g.n.sum()
    g = g.dropna(subset=["lo"])
    tot = g.n.sum()
    # classi di soglia: usabili solo se i gruppi non attraversano la soglia
    def below(th): return g[g.hi < th].n.sum()
    def atleast(th): return g[g.lo >= th].n.sum()
    ok = {th: not ((g.lo < th) & (g.hi >= th) & (g.lo != g.hi)).any() for th in (15, 65, 75, 80)}
    out.append(dict(anno=y, pop_ds300=int(tot_all), eta_ignota=int(tot_all - tot),
                    quota_0_14=round(100 * below(15) / tot, 2) if ok[15] else np.nan,
                    quota_65p=round(100 * atleast(65) / tot, 2) if ok[65] else np.nan,
                    quota_75p=round(100 * atleast(75) / tot, 2) if ok[75] else np.nan,
                    quota_80p=round(100 * atleast(80) / tot, 2) if ok[80] else np.nan,
                    eta_media=round((g.mid * g.n).sum() / tot, 2),
                    indice_vecchiaia=round(100 * atleast(65) / below(15), 1) if ok[15] and ok[65] else np.nan))
e = pd.DataFrame(out)
e.to_csv(P + "eta_storica_milano_1881_2011.csv", index=False)
print(e.to_string())
