"""Stampa e salva in pulito/riepilogo.txt i numeri citati in NOTE.md (tutti ricavati dalle tabelle di pulito/).
Uso: python -I -X utf8 riepilogo.py <percorso assoluto redditi>"""
import sys, os, io
import numpy as np, pandas as pd

P = os.path.join(sys.argv[1], "pulito")
buf = io.StringIO()


def p(*a):
    print(*a, file=buf)


S = pd.read_csv(os.path.join(P, "serie_unita_anno.csv"))
F = pd.read_csv(os.path.join(P, "italia_lombardia_serie_definitiva.csv"))
T = pd.read_csv(os.path.join(P, "tipi_reddito.csv"))
SR = pd.read_csv(os.path.join(P, "soglie_reali.csv"))
G = pd.read_csv(os.path.join(P, "cap_divario_per_citta.csv"))
C = pd.read_csv(os.path.join(P, "cap_redditi_tutte_le_citta.csv"), dtype={"cap": str})
CITTA = ["Milano", "Roma", "Torino", "Napoli", "Bologna"]
# serie unica per confronto: citta' da serie_unita_anno, Italia/Lombardia dalla serie definitiva
U = pd.concat([S[S.unita.isin(CITTA)][["unita", "anno_imposta", "media_nominale", "media_euro2025", "gini_classi", "quota_reddito_sopra_120k", "quota_contr_sopra_120k", "quota_contr_sotto_15k", "quota_contr_sotto_10k"]].rename(columns={"gini_classi": "gini"}),
               F.rename(columns={"gini_classi_grandi": "gini"})[["unita", "anno_imposta", "media_nominale", "media_euro2025", "gini", "quota_reddito_sopra_120k", "quota_contr_sopra_120k", "quota_contr_sotto_15k", "quota_contr_sotto_10k"]]])
U.to_csv(os.path.join(P, "confronto_citta_serie_unica.csv"), index=False, float_format="%.6g")
ANNI = [2000, 2006, 2010, 2015, 2019, 2022, 2024]
for col, nome in [("media_nominale", "MEDIA PER CONTRIBUENTE, euro correnti"), ("media_euro2025", "MEDIA PER CONTRIBUENTE, euro 2025"), ("gini", "GINI da classi (classi >0)"),
                  ("quota_reddito_sopra_120k", "QUOTA DEL REDDITO in mano a chi dichiara >120.000 euro"), ("quota_contr_sopra_120k", "QUOTA DEI CONTRIBUENTI con >120.000 euro"),
                  ("quota_contr_sotto_15k", "QUOTA DEI CONTRIBUENTI con <15.000 euro"), ("quota_contr_sotto_10k", "QUOTA DEI CONTRIBUENTI con <10.000 euro")]:
    p("##", nome); p(U[U.anno_imposta.isin(ANNI)].pivot(index="anno_imposta", columns="unita", values=col).round(3 if col not in ("media_nominale", "media_euro2025") else 0).to_string()); p()
m = U[U.unita == "Milano"].set_index("anno_imposta"); i_ = U[U.unita == "Italia"].set_index("anno_imposta")
p("## MILANO / ITALIA (media nominale)"); p((m.media_nominale / i_.media_nominale).loc[ANNI].round(3).to_string()); p()
p("## VARIAZIONE REALE media 2000->2024 e 2006->2024 (euro 2025)")
for u in CITTA + ["Lombardia", "Italia"]:
    x = U[U.unita == u].set_index("anno_imposta").media_euro2025
    p(f"{u:10s} 2000->2024 {x[2024] / x[2000] * 100 - 100:+.1f}%   2006->2024 {x[2024] / x[2006] * 100 - 100:+.1f}%   max {x.idxmax()} ({x.max():.0f})")
p()
Sm = S[S.unita == "Milano"].set_index("anno_imposta")
p("## MILANO dettaglio"); p(Sm.loc[ANNI, ["contribuenti", "senza_classe", "popolazione", "contribuenti_per_100_abitanti", "mediana_stimata_euro2025", "rapporto_media_oltre120k_su_media_generale", "media_classe_oltre120k_nominale"]].round(2).to_string()); p()
p("## SOGLIE REALI (euro del 2000): quota di contribuenti sopra 26k e 55k (euro 2000)")
for col in ["quota_sopra_26k_euro2000", "quota_sopra_55k_euro2000"]:
    p(col); p(SR[SR.anno_imposta.isin(ANNI)].pivot(index="anno_imposta", columns="unita", values=col).round(4).to_string())
p()
p("## TIPI DI REDDITO - Milano (quota dei contribuenti che li ricevono; quota del reddito complessivo; media per percettore in euro 2025)")
Tm = T[T.unita == "Milano"].set_index("anno_imposta")
for k in ["dipendente", "pensione", "autonomo", "impresa"]:
    p(k); p(Tm.loc[[2002, 2008, 2010, 2018, 2019, 2024], [k + "_quota_contribuenti", k + "_quota_del_reddito_complessivo", k + "_per_percettore_euro2025"]].round(3).to_string())
p("confronto Italia, pensione per percettore e quota contribuenti:")
Ti = T[T.unita == "Italia"].set_index("anno_imposta"); p(Ti.loc[[2002, 2010, 2024], ["pensione_quota_contribuenti", "pensione_per_percettore_euro2025", "dipendente_quota_contribuenti", "dipendente_per_percettore_euro2025", "autonomo_per_percettore_euro2025"]].round(3).to_string()); p()
# pensionati vs dipendenti: media per percettore Milano/Italia
p("Rapporto Milano/Italia media per percettore 2024: dipendente %.2f, pensione %.2f, autonomo %.2f, impresa %.2f" % tuple(
    Tm.loc[2024, k + "_per_percettore_euro2025"] / Ti.loc[2024, k + "_per_percettore_euro2025"] for k in ["dipendente", "pensione", "autonomo", "impresa"])); p()
# CAP
mil = C[C.comune.str.upper() == "MILANO"]
p("## CAP - divario nelle citta' (rapporto p90/p10 delle medie per CAP, pesato; Gini tra CAP)")
g = G[G.comune.isin(["MILANO", "ROMA", "TORINO", "NAPOLI", "BOLOGNA", "GENOVA", "FIRENZE"])]
p(g.pivot(index="anno_imposta", columns="comune", values="p90_su_p10").round(2).to_string()); p(g.pivot(index="anno_imposta", columns="comune", values="gini_tra_cap").round(3).to_string()); p()
for t in (2011, 2024):
    x = mil[mil.anno == t].sort_values("media_euro2025")
    p(f"Milano CAP {t}: 5 piu' poveri (media euro 2025):", [(r.cap, round(r.media_euro2025), int(r.contribuenti)) for r in x.head(5).itertuples()])
    p(f"Milano CAP {t}: 5 piu' ricchi:", [(r.cap, round(r.media_euro2025), int(r.contribuenti)) for r in x.tail(5).itertuples()])
# quartili pesati dei CAP per reddito 2011 e variazione reale
a = mil[mil.anno == 2011].set_index("cap"); b = mil[mil.anno == 2024].set_index("cap")
a = a.assign(q=pd.qcut(a.media_euro2025, 4, labels=["Q1 piu' poveri", "Q2", "Q3", "Q4 piu' ricchi"]))
rows = []
for q, g_ in a.groupby("q", observed=True):
    caps = g_.index
    r11 = a.loc[caps, "reddito_eur"].sum() * 1.0; n11 = a.loc[caps, "contribuenti"].sum()
    r24 = b.loc[caps, "reddito_eur"].sum(); n24 = b.loc[caps, "contribuenti"].sum()
    m11 = r11 / n11 * 1.266; m24 = r24 / n24 * 1.014
    rows.append((q, len(caps), n11, round(m11), round(m24), round((m24 / m11 - 1) * 100, 1)))
p("Quartili di CAP (per reddito 2011): [quartile, n CAP, contribuenti 2011, media 2011 euro2025, media 2024 euro2025, var reale %]")
for r in rows: p(r)
p("(fattore euro2025 2011 = 1.266, 2024 = 1.014, da foi_annuale)")
p()
p("## CAP dove cambia il numero di contribuenti in un anno (>15%) = possibili cambi di assegnazione CAP")
pv = mil.pivot(index="cap", columns="anno", values="contribuenti"); yrs = list(pv.columns)
for i in range(1, len(yrs)):
    ch = (pv[yrs[i]] / pv[yrs[i - 1]] - 1)
    for cap, v in ch[ch.abs() > 0.15].items(): p(f"  {cap}: {yrs[i - 1]}->{yrs[i]} contribuenti {pv.loc[cap, yrs[i - 1]]:.0f} -> {pv.loc[cap, yrs[i]]:.0f} ({v * 100:+.0f}%)")
p()
# quota >120k per CAP
p("Quota di contribuenti >120k nei CAP 2011 vs 2024 (primi 6 CAP 2024)")
q = mil.pivot(index="cap", columns="anno", values="quota_sopra_120k"); p((q[[2011, 2024]].sort_values(2024, ascending=False).head(6) * 100).round(1).to_string())
txt = buf.getvalue()
open(os.path.join(P, "riepilogo.txt"), "w", encoding="utf8").write(txt)
print(txt)
