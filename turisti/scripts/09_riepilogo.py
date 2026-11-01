"""Riepiloghi sul turismo a Milano per paese di provenienza. Stampa e salva out/riepilogo.txt; scrive tabelle in pulito/riepilogo_*.csv.
uso: python -I -X utf8 09_riepilogo.py <cartella turisti assoluta>
Legge solo le tabelle pulite create da 07 e 08. Confronti, non cause."""
import sys, os, io
import pandas as pd
base = sys.argv[1]
PUL = os.path.join(base, "pulito"); OUT = os.path.join(base, "out"); os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
buf = io.StringIO()
def P(*a):
    s = " ".join(str(x) for x in a); print(s); buf.write(s + "\n")
def T(df, **k): P(df.to_string(**k))
def save(df, nome): df.to_csv(os.path.join(PUL, nome), index=False, encoding="utf-8")

a = pd.read_csv(os.path.join(PUL, "annuale_paese.csv"))
a["permanenza"] = a.presenze / a.arrivi
tipo = pd.read_csv(os.path.join(PUL, "annuale_paese_tipo.csv"))
mens = pd.read_csv(os.path.join(PUL, "mensile_paese.csv"))
prov = pd.read_csv(os.path.join(PUL, "provincia_mensile.csv"))
bdi = pd.read_csv(os.path.join(PUL, "bdi_milano_paese_anno.csv"))
bmes = pd.read_csv(os.path.join(PUL, "bdi_milano_mese.csv"))
vy = pd.read_csv(os.path.join(PUL, "milano_italiani_stranieri.csv"))

# ---------- 1. Italiani e stranieri
P("== 1. ITALIANI E STRANIERI (comune di Milano, tutte le strutture; ds211+ds213; 2000-2004 da ds210+ds212)")
tot = a.groupby("anno")[["arrivi", "presenze"]].sum()
it = a[a.paese == "Italia"].set_index("anno")[["arrivi", "presenze"]]
t = pd.DataFrame({"arrivi_tot": tot.arrivi, "pres_tot": tot.presenze, "arrivi_it": it.arrivi, "pres_it": it.presenze})
t["arrivi_str"] = t.arrivi_tot - t.arrivi_it; t["pres_str"] = t.pres_tot - t.pres_it
t["quota_str_pres_%"] = (100 * t.pres_str / t.pres_tot).round(1); t["quota_str_arr_%"] = (100 * t.arrivi_str / t.arrivi_tot).round(1)
t["indice_pres_it_2019=100"] = (100 * t.pres_it / t.loc[2019, "pres_it"]).round(1)
t["indice_pres_str_2019=100"] = (100 * t.pres_str / t.loc[2019, "pres_str"]).round(1)
t = t.reset_index(); save(t, "riepilogo_italiani_stranieri.csv"); T(t.astype({c: "int64" for c in ["arrivi_tot", "pres_tot", "arrivi_it", "pres_it", "arrivi_str", "pres_str"]}), index=False)

# ---------- 2. classifica dei paesi
P("\n== 2. PRIMI PAESI STRANIERI PER NOTTI (presenze) - solo voci che sono un paese (non 'Altri ...')")
paesi = a[(a.paese != "Italia") & (~a.paese.str.startswith("Altri"))]
rk = {}
for y in (2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025):
    d = paesi[paesi.anno == y].sort_values("presenze", ascending=False).reset_index(drop=True)
    rk[y] = d
    P(f"-- {y}: " + "; ".join(f"{i + 1}. {r.paese} {int(r.presenze):,}" for i, r in d.head(12).iterrows()))
voci_altri = a[(a.anno == 2025) & (a.paese.str.startswith("Altri") | a.paese.str.startswith("Paesi dell"))][["paese", "arrivi", "presenze"]]
P("(voci 'Altri ...' 2025, non confrontabili come singoli paesi:)"); T(voci_altri.astype({"arrivi": "int64", "presenze": "int64"}), index=False)

# ---------- 3. paesi scelti nel tempo
P("\n== 3. PAESI SCELTI: presenze per anno e indice sul 2019 (=100). Tutte le strutture, comune di Milano")
sel = ["Cina", "Stati Uniti d'America", "Regno Unito", "Russia", "Giappone", "Germania", "Francia", "Spagna", "Brasile", "India", "Corea del Sud", "Svizzera e Liechtenstein", "Altri Paesi del Medio Oriente", "Polonia", "Romania", "Turchia", "Ucraina", "Israele"]
pv = a[a.paese.isin(sel)].pivot(index="anno", columns="paese", values="presenze")
pv.to_csv(os.path.join(PUL, "riepilogo_paesi_scelti_presenze.csv"), encoding="utf-8")
T((pv.loc[[2005, 2010, 2014, 2015, 2016, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]] / 1000).round(0).astype("Int64").T)
idx = (100 * pv / pv.loc[2019]).round(0)
P("indice presenze, 2019 = 100:"); T(idx.loc[[2015, 2016, 2019, 2020, 2021, 2022, 2023, 2024, 2025]].astype("Int64").T)
pa = a[a.paese.isin(sel)].pivot(index="anno", columns="paese", values="arrivi")
P("arrivi (migliaia), anni scelti:"); T((pa.loc[[2005, 2010, 2015, 2019, 2020, 2022, 2025]] / 1000).round(0).astype("Int64").T)
P("\nPicco storico delle presenze per paese (anno e valore), e valore 2025 / picco:")
for c in sel:
    s = pv[c].dropna(); y = s.idxmax()
    P(f"  {c}: picco {y} ({int(s.max()):,}); 2019 {int(pv.loc[2019, c]):,}; 2025 {int(pv.loc[2025, c]):,} = {100 * pv.loc[2025, c] / s.max():.0f}% del picco, {100 * pv.loc[2025, c] / pv.loc[2019, c]:.0f}% del 2019")

# ---------- 4. permanenza media
P("\n== 4. PERMANENZA MEDIA (notti per arrivo) per paese, anni 2019 e 2025 (paesi con almeno 100.000 arrivi nell'anno; ds211/ds213)")
for y in (2019, 2025):
    d = paesi[(paesi.anno == y) & (paesi.arrivi >= 100000)].sort_values("permanenza", ascending=False)
    P(f"-- {y}: " + "; ".join(f"{r.paese} {r.permanenza:.2f}" for _, r in d.iterrows()))
    P(f"   totale Milano {a[a.anno == y].presenze.sum() / a[a.anno == y].arrivi.sum():.2f}; Italia {a[(a.anno == y) & (a.paese == 'Italia')].presenze.iloc[0] / a[(a.anno == y) & (a.paese == 'Italia')].arrivi.iloc[0]:.2f}")
perm = a[a.paese.isin(sel + ["Italia"])].pivot(index="anno", columns="paese", values="permanenza").round(2)
perm.to_csv(os.path.join(PUL, "riepilogo_permanenza_paesi_scelti.csv"), encoding="utf-8")

# ---------- 5. alberghi / extra-alberghiero
P("\n== 5. ALBERGHI E STRUTTURE EXTRA-ALBERGHIERE per paese (ds217-ds220, 2008-2025). Quota delle notti in strutture extra-alberghiere")
p = tipo.pivot_table(index=["anno", "paese"], columns="tipo_struttura", values="presenze").reset_index()
p["quota_extra_%"] = (100 * p["extra-alberghiero"] / p["totale"]).round(1)
q = tipo.pivot_table(index=["anno", "paese"], columns="tipo_struttura", values="arrivi").reset_index()
p["perm_alb"] = None
save(p, "riepilogo_alberghi_extra_per_paese.csv")
tt = p.groupby("anno")[["alberghiero", "extra-alberghiero", "totale"]].sum()
tt["quota_extra_%"] = (100 * tt["extra-alberghiero"] / tt.totale).round(1)
P("Totale Milano, presenze:"); T(tt.astype("int64", errors="ignore") if False else tt.round(1))
for y in (2019, 2025):
    d = p[(p.anno == y) & (p.totale >= 250000)].sort_values("quota_extra_%", ascending=False)
    P(f"-- {y}, paesi con almeno 250.000 notti, in ordine di quota extra-alberghiera: " + "; ".join(f"{r.paese} {r['quota_extra_%']:.0f}% ({int(r.totale):,})" for _, r in d.iterrows()))
# permanenza hotel vs extra per italiani/stranieri totali
ar = tipo.pivot_table(index=["anno", "paese"], columns="tipo_struttura", values="arrivi").reset_index()
m = p.merge(ar, on=["anno", "paese"], suffixes=("_p", "_a"))
m["perm_alb"] = m["alberghiero_p"] / m["alberghiero_a"]; m["perm_extra"] = m["extra-alberghiero_p"] / m["extra-alberghiero_a"]
P("Permanenza media in albergo e in extra-alberghiero, 2025 (paesi con almeno 250.000 notti):")
d = m[(m.anno == 2025) & (m.totale_p >= 250000)][["paese", "perm_alb", "perm_extra"]].round(2); T(d, index=False)
save(m[["anno", "paese", "alberghiero_p", "extra-alberghiero_p", "totale_p", "alberghiero_a", "extra-alberghiero_a", "totale_a", "perm_alb", "perm_extra"]], "riepilogo_alberghi_extra_perm.csv")
P("Dove sta la crescita 2019-2025 per paese (notti, extra-alberghiero e albergo, variazione assoluta)")
w19 = p[p.anno == 2019].set_index("paese"); w25 = p[p.anno == 2025].set_index("paese")
dd = pd.DataFrame({"alb_19": w19.alberghiero, "alb_25": w25.alberghiero, "extra_19": w19["extra-alberghiero"], "extra_25": w25["extra-alberghiero"]})
dd["d_alb"] = dd.alb_25 - dd.alb_19; dd["d_extra"] = dd.extra_25 - dd.extra_19; dd = dd.sort_values("d_alb")
P("  paesi che hanno perso piu' notti negli alberghi:"); T(dd.head(6).astype("int64"))
P("  paesi che ne hanno guadagnate di piu' negli alberghi:"); T(dd.tail(6).astype("int64"))
dd.to_csv(os.path.join(PUL, "riepilogo_crescita_2019_2025_tipo.csv"), encoding="utf-8")

# ---------- 6. Expo 2015
P("\n== 6. EXPO 2015 (1 maggio - 31 ottobre 2015). Mensile per paese disponibile dal 2015 (ds214/ds215), comune di Milano")
mt = mens.groupby(["anno", "mese"])[["arrivi", "presenze"]].sum().reset_index()
pz = mt.pivot(index="mese", columns="anno", values="presenze")
P("presenze mensili totali (migliaia):"); T((pz[[2015, 2016, 2017, 2018, 2019]] / 1000).round(0).astype("Int64"))
ex = pz.loc[5:10]
P(f"somma maggio-ottobre: 2015 {ex[2015].sum():,.0f}; 2016 {ex[2016].sum():,.0f} ({100 * ex[2016].sum() / ex[2015].sum() - 100:+.1f}%); 2017 {ex[2017].sum():,.0f}; 2019 {ex[2019].sum():,.0f}")
nex = pz.loc[[1, 2, 3, 4, 11, 12]]
P(f"somma gen-apr + nov-dic: 2015 {nex[2015].sum():,.0f}; 2016 {nex[2016].sum():,.0f} ({100 * nex[2016].sum() / nex[2015].sum() - 100:+.1f}%)")
P("annuale (ds211/213): 2014 %s, 2015 %s, 2016 %s presenze" % tuple(f"{a[a.anno == y].presenze.sum():,.0f}" for y in (2014, 2015, 2016)))
e15 = mens[(mens.anno == 2015) & mens.mese.between(5, 10)].groupby("paese").presenze.sum()
e16 = mens[(mens.anno == 2016) & mens.mese.between(5, 10)].groupby("paese").presenze.sum()
c = pd.DataFrame({"mag_ott_2015": e15, "mag_ott_2016": e16}).dropna()
c["diff"] = c.mag_ott_2015 - c.mag_ott_2016; c["pct_%"] = (100 * c["diff"] / c.mag_ott_2016).round(1)
c = c[~c.index.str.startswith("Altri")]
P("Paesi con piu' notti in maggio-ottobre 2015 che nello stesso periodo del 2016 (differenza assoluta, primi 10):"); T(c.sort_values("diff", ascending=False).head(10).astype("float").round(1))
P("Paesi con la differenza percentuale piu' alta (almeno 20.000 notti nel 2016):"); T(c[c.mag_ott_2016 >= 20000].sort_values("pct_%", ascending=False).head(8).round(1))
save(c.reset_index(), "riepilogo_expo_2015_vs_2016.csv")

# ---------- 7. Olimpiadi 2026 e ultimi mesi
P("\n== 7. OLIMPIADI INVERNALI (6-22 febbraio 2026): i dati arrivano a dicembre 2025")
P("Ultimo mese disponibile nel comune: " + f"{int(mens.anno.max())}-{int(mens[mens.anno == mens.anno.max()].mese.max()):02d}")
P("Ultimo mese nel dataset provinciale: " + f"{int(prov.anno.max())}-{int(prov[prov.anno == prov.anno.max()].mese.max()):02d}")
P("Quindi i mesi olimpici non si vedono. Per confronto, presenze di febbraio e dicembre nel comune (migliaia):")
T((pz.loc[[2, 12], [2019, 2022, 2023, 2024, 2025]] / 1000).round(0).astype("Int64"))

# ---------- 8. mesi forti per paese (stagionalita' 2019 e 2025)
P("\n== 8. STAGIONALITA': mese con piu' notti per paese, 2019 e 2025 (comune di Milano, ds215)")
for y in (2019, 2025):
    d = mens[(mens.anno == y) & (~mens.paese.str.startswith("Altri"))]
    top = d.groupby("paese").presenze.sum().sort_values(ascending=False).head(14).index
    pk = d[d.paese.isin(top)].sort_values("presenze").groupby("paese").tail(1).set_index("paese")["mese"]
    P(f"-- {y}: " + "; ".join(f"{c} mese {int(pk[c])}" for c in top))

# ---------- 9. Covid
P("\n== 9. COVID: presenze 2019 -> 2020 -> 2021 -> 2022 (stranieri per area; comune di Milano)")
area = a.copy()
def grp(r):
    if r.paese == "Italia": return "Italia"
    if r.paese.startswith("Altri") or r.paese.startswith("Paesi dell"): return "Altri/residuo"
    return r.paese
cv = pv.loc[[2019, 2020, 2021, 2022]].T
cv["2020/2019_%"] = (100 * cv[2020] / cv[2019]).round(0); cv["2022/2019_%"] = (100 * cv[2022] / cv[2019]).round(0); T(cv.astype("float").round(0))

# ---------- 10. provincia di Milano mensile (PoliS)
P("\n== 10. PROVINCIA DI MILANO, mensile 2019-2025 (PoliS xzck-giqt): primi 12 paesi esteri per notti 2025 e andamento")
pr = prov[(prov.tipo_struttura == "totale") & (prov.tipo_provenienza == "estero")]
y = pr.groupby(["anno", "provenienza"]).presenze.sum().reset_index().pivot(index="provenienza", columns="anno", values="presenze")
y = y.sort_values(2025, ascending=False)
T((y.head(14) / 1000).round(0))
tp = prov[(prov.tipo_struttura == "totale")].groupby(["anno", "tipo_provenienza"]).presenze.sum().unstack()
P("Presenze provincia di Milano per tipo di provenienza:"); T(tp.astype("int64"))
cm = a.groupby("anno").presenze.sum()
P("Comune di Milano / provincia (presenze totali): " + "; ".join(f"{yy} {100 * cm[yy] / tp.loc[yy].sum():.0f}%" for yy in range(2019, 2026)))

# ---------- 11. Banca d'Italia
P("\n== 11. BANCA D'ITALIA - indagine alle frontiere: spesa dei viaggiatori stranieri con destinazione il comune di Milano (stime da campione)")
b = bdi[bdi.ambito == "comune_milano"].copy()
tb = b.groupby("anno")[["interviste", "viaggiatori", "notti", "spesa_euro"]].sum()
ti = bdi[bdi.ambito == "italia"].groupby("anno")[["spesa_euro", "viaggiatori"]].sum()
tb["quota_spesa_Italia_%"] = (100 * tb.spesa_euro / ti.spesa_euro).round(1)
tb["spesa_mln"] = (tb.spesa_euro / 1e6).round(0); tb["viagg_mln"] = (tb.viaggiatori / 1e6).round(2); tb["notti_mln"] = (tb.notti / 1e6).round(1)
T(tb[["interviste", "viagg_mln", "notti_mln", "spesa_mln", "quota_spesa_Italia_%"]])
save(tb.reset_index(), "riepilogo_bdi_totali_comune_milano.csv")
for yv in (2019, 2025):
    d = b[b.anno == yv].sort_values("spesa_euro", ascending=False).head(12)
    P(f"-- {yv}: primi 12 paesi per spesa (milioni di euro; interviste; spesa per viaggiatore): " + "; ".join(f"{r.stato.title()} {r.spesa_euro / 1e6:.0f} (n={r.interviste}, {r.spesa_euro / r.viaggiatori:.0f} euro/viagg.)" for _, r in d.iterrows()))
b["spesa_viagg"] = b.spesa_euro / b.viaggiatori
sel_b = ["STATI UNITI D'AMERICA", "CINA REP.POP.", "REGNO UNITO", "RUSSIA, FEDERAZIONE DI", "GIAPPONE", "GERMANIA", "FRANCIA", "SPAGNA", "SVIZZERA", "BRASILE", "ARABIA SAUDITA", "INDIA", "COREA DEL SUD", "EMIRATI ARABI UNITI"]
pb = b[b.stato.isin(sel_b)].pivot(index="anno", columns="stato", values="spesa_euro") / 1e6
P("Spesa in milioni di euro, paesi scelti (ATTENZIONE: n. di interviste piccolo per alcuni paesi, vedi bdi_milano_paese_anno.csv):"); T(pb.loc[[2007, 2010, 2015, 2018, 2019, 2021, 2022, 2023, 2024, 2025]].round(0).T)
pn = b[b.stato.isin(sel_b)].pivot(index="anno", columns="stato", values="interviste")
P("Numero di interviste (campione):"); T(pn.loc[[2007, 2010, 2015, 2018, 2019, 2021, 2022, 2023, 2024, 2025]].T)
save(b, "riepilogo_bdi_comune_milano_paese.csv")
bm = bmes[(bmes.ambito == "comune_milano") & (bmes.anno.isin([2015, 2019, 2022, 2023, 2024, 2025]))].pivot(index="mese", columns="anno", values="spesa_euro") / 1e6
P("Spesa mensile (milioni di euro) comune di Milano, anni scelti:"); T(bm.round(0))
# ---------- 12. italiani/stranieri da PoliS
P("\n== 12. PoliS vyxt-7jdx: italiani e stranieri per tipo di struttura (comune di Milano, notti)")
v = vy[vy.cittadinanza.isin(["italiani", "stranieri"])].pivot_table(index="anno", columns=["tipo_struttura", "cittadinanza"], values="presenze")
T(v.astype("int64"))
open(os.path.join(OUT, "riepilogo.txt"), "w", encoding="utf-8").write(buf.getvalue())
