"""Riepiloghi: stagioni polliniche per taxon, stazione e anno; tendenze; legame con le temperature.

Uso: python -I -X utf8 analisi.py <P = cartella pollini assoluta> <M = cartella milano-in-dati assoluta>
Legge:  P/pulito/concentrazioni_giornaliere.csv, P/raw/ispra/pollini_spore.csv (classi di riferimento POLLnet),
        M/temperature/serie/serie_unica.csv (Brera, serie pubblicata dal sito), M/alberi/pulito/alberi.csv
Scrive in P/pulito/: stagioni_taxon_anno.csv, tendenze_stazione.csv, indicatore_regionale_anno.csv,
        tendenze_regionali.csv, legame_temperature.csv, alberi_contesto.csv, riepilogo.json

DEFINIZIONI (tutte qui, nessun numero a mano)
 - dato: media giornaliera in granuli/m3 (POLLnet). Un "giorno campionato" e' un giorno in cui la stazione ha
   almeno una riga di dati (qualunque taxon). Per alcune stazioni/anni gli zeri non sono registrati (le righe
   esistono solo per i valori > 0): per somme, inizi, fini e picchi non cambia nulla.
 - integrale annuo = somma dei valori giornalieri dell'anno solare, in granuli*giorno/m3 (e' un MINIMO se mancano giorni).
 - inizio / fine della stagione = primo giorno in cui la somma cumulata dell'anno raggiunge il 5% / il 95% dell'integrale.
 - durata = fine - inizio (giorni). Picco = giorno col valore giornaliero massimo.
 - giorni sopra "medio" = giorni campionati con valore >= limite MEDIO POLLnet per quel taxon (pollini_spore.csv).
 - anno VALIDO per (stazione, taxon): taxon con integrale >= 30; copertura >= 75% (giorni campionati / giorni di calendario)
   dentro la finestra inizio-fine; copertura >= 80% dentro la FINESTRA ATTESA del taxon (mesi fissi, vedi FINESTRA_ATTESA:
   serve a scoprire i buchi che la finestra inizio-fine, calcolata dai dati stessi, non vede); almeno 200 giorni campionati.
 - tendenza: pendenza di Theil-Sen (mediana delle pendenze a coppie) con intervallo al 95% di scipy.stats.theilslopes,
   e test di Mann-Kendall (Kendall tau contro l'anno). Servono >= 10 anni validi.
 - indicatore regionale: per ogni taxon e anno, mediana su stazioni delle anomalie (valore - media della stazione
   sugli anni validi comuni) dall'anno 2011; serve >= 3 stazioni.
"""
import json, math, os, sys, datetime
import numpy as np
import pandas as pd
from scipy import stats

TAXA = {  # nome in POLLnet : (etichetta, mesi della temperatura "di avvicinamento" alla stagione)
    "Corylus": ("Nocciolo (Corylus)", (1, 2)),
    "Alnus": ("Ontano (Alnus)", (1, 2)),
    "Cupressaceae/Taxaceae": ("Cipressi e affini (Cupressaceae/Taxaceae)", (1, 2)),
    "Betula": ("Betulla (Betula)", (2, 3)),
    "Platanaceae": ("Platano (Platanaceae)", (2, 3)),
    "Fraxinus": ("Frassino (Fraxinus)", (2, 3)),
    "Quercus": ("Quercia (Quercus)", (3, 4)),
    "Gramineae": ("Graminacee (Gramineae)", (3, 4)),
    "Urticaceae": ("Urticacee, parietaria (Urticaceae)", (3, 4)),
    "Artemisia": ("Artemisia", (6, 7)),
    "Ambrosia": ("Ambrosia", (6, 7)),
}
FINESTRA_ATTESA = {  # mesi (da, a) in cui la stagione del taxon cade quasi sempre; serve per controllare i buchi
    "Corylus": (1, 3), "Alnus": (1, 3), "Cupressaceae/Taxaceae": (1, 4), "Betula": (3, 5), "Platanaceae": (3, 5),
    "Fraxinus": (2, 5), "Quercus": (3, 6), "Gramineae": (4, 8), "Urticaceae": (3, 10), "Artemisia": (7, 10),
    "Ambrosia": (7, 10),
}
MIN_COP_ATTESA = 0.80
MIN_INTEGRALE = 30
MIN_COPERTURA = 0.75
MIN_GIORNI_ANNO = 200
MIN_ANNI_TREND = 10


def serie_trend(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < MIN_ANNI_TREND or np.ptp(x) == 0:
        return None
    sl, ic, lo, hi = stats.theilslopes(y, x, alpha=0.95)
    tau, p = stats.kendalltau(x, y)
    return dict(n=len(x), pendenza=sl, ic95_basso=lo, ic95_alto=hi, tau=tau, p_mk=p,
                anni=f"{int(x.min())}-{int(x.max())}")


def main():
    P, M = sys.argv[1], sys.argv[2]
    out = os.path.join(P, "pulito")
    d = pd.read_csv(os.path.join(out, "concentrazioni_giornaliere.csv"), sep=";")
    d["data"] = pd.to_datetime(d.data)
    d["anno"] = d.data.dt.year
    ref = pd.read_csv(os.path.join(P, "raw", "ispra", "pollini_spore.csv"))
    medio = {r.PART_NAME_I: r.PART_MIDDLE for r in ref.itertuples()}
    medio.setdefault("Betula", 16)

    campionati = d.groupby("codice_stazione").data.apply(lambda s: np.array(sorted(s.unique()), dtype="datetime64[D]"))
    camp_anno = d.groupby(["codice_stazione", "anno"]).data.nunique()

    rows = []
    for (stz, tx, anno), g in d[d.taxon.isin(TAXA)].groupby(["codice_stazione", "taxon", "anno"]):
        g = g.sort_values("data")
        tot = g.granuli_m3.sum()
        r = dict(stazione=stz, taxon=tx, anno=anno, giorni_campionati_anno=int(camp_anno[(stz, anno)]),
                 righe_taxon=len(g), righe_zero=int((g.granuli_m3 == 0).sum()), integrale=float(tot))
        if tot <= 0:
            r.update(valida=False, nota="taxon mai > 0 (non contato o assente)")
            rows.append(r)
            continue
        cum = g.granuli_m3.cumsum().values / tot
        i5 = int(np.argmax(cum >= 0.05))
        i95 = int(np.argmax(cum >= 0.95))
        ini, fin = g.data.iloc[i5], g.data.iloc[i95]
        camp = campionati[stz]
        n_in = int(((camp >= np.datetime64(ini.date())) & (camp <= np.datetime64(fin.date()))).sum())
        dur = (fin - ini).days
        cop = n_in / (dur + 1)
        ip = int(g.granuli_m3.values.argmax())
        sogl = medio.get(tx, None)
        r.update(inizio=ini.date().isoformat(), fine=fin.date().isoformat(), inizio_doy=ini.day_of_year,
                 fine_doy=fin.day_of_year, durata_giorni=dur, picco_data=g.data.iloc[ip].date().isoformat(),
                 picco_doy=g.data.iloc[ip].day_of_year, picco_valore=float(g.granuli_m3.iloc[ip]),
                 giorni_ge_medio=int((g.granuli_m3 >= sogl).sum()) if sogl is not None else None,
                 copertura_finestra=round(cop, 3))
        m0, m1 = FINESTRA_ATTESA[tx]
        a0 = np.datetime64(f"{anno}-{m0:02d}-01")
        a1 = np.datetime64(f"{anno}-{m1:02d}-01") + np.timedelta64(int(pd.Timestamp(anno, m1, 1).days_in_month) - 1, "D")
        att = float(((camp >= a0) & (camp <= a1)).sum()) / float((a1 - a0).astype(int) + 1)
        r["copertura_finestra_attesa"] = round(att, 3)
        ok = (tot >= MIN_INTEGRALE and cop >= MIN_COPERTURA and att >= MIN_COP_ATTESA
              and r["giorni_campionati_anno"] >= MIN_GIORNI_ANNO)
        r["valida"] = bool(ok)
        r["nota"] = "" if ok else ("integrale < %d" % MIN_INTEGRALE if tot < MIN_INTEGRALE else
                                    "copertura finestra inizio-fine < 75%" if cop < MIN_COPERTURA else
                                    "buchi nella finestra attesa (< 80%)" if att < MIN_COP_ATTESA else "meno di 200 giorni campionati")
        rows.append(r)
    S = pd.DataFrame(rows).sort_values(["taxon", "stazione", "anno"])
    S.to_csv(os.path.join(out, "stagioni_taxon_anno.csv"), sep=";", index=False)
    V = S[S.valida].copy()

    # ---- tendenze per stazione
    metr = {"inizio_doy": "giorni/anno", "fine_doy": "giorni/anno", "durata_giorni": "giorni/anno",
            "log10_integrale": "log10/anno", "picco_valore": "granuli/m3 per anno", "giorni_ge_medio": "giorni/anno"}
    V["log10_integrale"] = np.log10(V.integrale)
    T = []
    for (stz, tx), g in V.groupby(["stazione", "taxon"]):
        for m in metr:
            gg = g.dropna(subset=[m])
            t = serie_trend(gg.anno, gg[m])
            if t:
                T.append(dict(stazione=stz, taxon=tx, metrica=m, unita=metr[m], **t))
    T = pd.DataFrame(T)
    T["pendenza_per_decennio"] = T.pendenza * 10
    T["ic95_basso_dec"] = T.ic95_basso * 10
    T["ic95_alto_dec"] = T.ic95_alto * 10
    lg = T.metrica == "log10_integrale"
    T["fattore_integrale_per_decennio"] = np.where(lg, 10 ** T.pendenza_per_decennio, np.nan)
    T["fattore_ic95_basso"] = np.where(lg, 10 ** T.ic95_basso_dec, np.nan)
    T["fattore_ic95_alto"] = np.where(lg, 10 ** T.ic95_alto_dec, np.nan)
    T.to_csv(os.path.join(out, "tendenze_stazione.csv"), sep=";", index=False)

    # ---- indicatore regionale (anomalie rispetto alla media della stazione)
    reg = []
    V11 = V[V.anno >= 2011]
    for m in ["inizio_doy", "fine_doy", "durata_giorni", "log10_integrale", "giorni_ge_medio"]:
        for tx, g in V11.groupby("taxon"):
            gg = g.dropna(subset=[m]).copy()
            # solo stazioni con >= 8 anni validi dal 2011
            ok = gg.groupby("stazione").anno.nunique()
            gg = gg[gg.stazione.isin(ok[ok >= 8].index)]
            gg["anom"] = gg[m] - gg.groupby("stazione")[m].transform("mean")
            for a, h in gg.groupby("anno"):
                if h.stazione.nunique() >= 3:
                    reg.append(dict(taxon=tx, metrica=m, anno=a, anomalia_mediana=float(h.anom.median()),
                                    n_stazioni=int(h.stazione.nunique()),
                                    stazioni=",".join(sorted(h.stazione.unique()))))
    R = pd.DataFrame(reg)
    R.to_csv(os.path.join(out, "indicatore_regionale_anno.csv"), sep=";", index=False)
    TR = []
    for (tx, m), g in R.groupby(["taxon", "metrica"]):
        t = serie_trend(g.anno, g.anomalia_mediana)
        if t:
            TR.append(dict(taxon=tx, metrica=m, **t))
    TR = pd.DataFrame(TR)
    for c in ["pendenza", "ic95_basso", "ic95_alto"]:
        TR[c + "_dec"] = TR[c] * 10
    lg = TR.metrica == "log10_integrale"
    TR["fattore_integrale_per_decennio"] = np.where(lg, 10 ** TR.pendenza_dec, np.nan)
    TR["fattore_ic95_basso"] = np.where(lg, 10 ** TR.ic95_basso_dec, np.nan)
    TR["fattore_ic95_alto"] = np.where(lg, 10 ** TR.ic95_alto_dec, np.nan)
    TR.to_csv(os.path.join(out, "tendenze_regionali.csv"), sep=";", index=False)

    # ---- anni peggiori (indicatore regionale: anomalia mediana del log10 dell'integrale)
    W = []
    for tx, g in R[R.metrica == "log10_integrale"].groupby("taxon"):
        for rk, (_, h) in enumerate(g.sort_values("anomalia_mediana", ascending=False).head(3).iterrows(), 1):
            q = V[(V.taxon == tx) & (V.anno == h.anno)]
            W.append(dict(taxon=tx, posizione=rk, anno=int(h.anno), fattore_sulla_media=round(10 ** h.anomalia_mediana, 2),
                          n_stazioni=int(h.n_stazioni), integrale_per_stazione="; ".join(
                              f"{r.stazione}={r.integrale:.0f}" for r in q.itertuples())))
    pd.DataFrame(W).to_csv(os.path.join(out, "anni_peggiori.csv"), sep=";", index=False)

    # ---- Ambrosia e il coleottero Ophraella communa (arrivato in Lombardia nel 2013 secondo Regione Lombardia)
    AM = []
    for stz, g in V[V.taxon == "Ambrosia"].groupby("stazione"):
        prima = g[(g.anno >= 2007) & (g.anno <= 2012)]
        dopo = g[(g.anno >= 2013) & (g.anno <= 2025)]
        a12 = g[g.anno == 2012].integrale
        a13 = g[g.anno == 2013].integrale
        if (len(prima) >= 2 and len(dopo) >= 5) or (len(a12) and len(a13)):
            AM.append(dict(stazione=stz, anni_prima=(f"{int(prima.anno.min())}-{int(prima.anno.max())}" if len(prima) else ""), n_prima=len(prima),
                           mediana_prima=float(prima.integrale.median()) if len(prima) else None, n_dopo=len(dopo),
                           mediana_dopo_2013_2025=float(dopo.integrale.median()) if len(dopo) else None,
                           rapporto_dopo_su_prima=float(dopo.integrale.median() / prima.integrale.median()) if len(prima) and len(dopo) else None,
                           integrale_2012=float(a12.iloc[0]) if len(a12) else None,
                           integrale_2013=float(a13.iloc[0]) if len(a13) else None,
                           rapporto_2013_su_2012=float(a13.iloc[0] / a12.iloc[0]) if len(a12) and len(a13) else None))
    pd.DataFrame(AM).to_csv(os.path.join(out, "ambrosia_prima_dopo_2013.csv"), sep=";", index=False)

    # ---- temperature di Brera (serie pubblicata, 'serie_unica.csv', non la 'corretta')
    tt = pd.read_csv(os.path.join(M, "temperature", "serie", "serie_unica.csv"), parse_dates=["date"])
    tt["anno"] = tt.date.dt.year
    tt["mese"] = tt.date.dt.month
    LT = []
    for tx, (_, mesi) in TAXA.items():
        sel = tt[tt.mese.isin(mesi)]
        gm = sel.groupby("anno").agg(t=("tmean", "mean"), n=("tmean", "count"))
        gm = gm[gm.n >= 0.8 * 28 * len(mesi)]["t"]
        for nome, serie in [("regionale", R[(R.taxon == tx) & (R.metrica == "inizio_doy")].set_index("anno").anomalia_mediana),
                            ("Novara", V[(V.taxon == tx) & (V.stazione == "NO1")].set_index("anno").inizio_doy)]:
            j = pd.concat([serie.rename("inizio"), gm.rename("t")], axis=1, join="inner").dropna()
            j = j[j.index <= 2026]
            if len(j) < 8:
                continue
            rho, p = stats.spearmanr(j.t, j.inizio)
            lr = stats.linregress(j.t, j.inizio)
            # versione senza tendenza: residui di ciascuna serie rispetto all'anno
            ry = j.inizio - np.polyval(np.polyfit(j.index, j.inizio, 1), j.index)
            rt = j.t - np.polyval(np.polyfit(j.index, j.t, 1), j.index)
            rho_d, p_d = stats.spearmanr(rt, ry)
            tr_t = stats.theilslopes(j.t, j.index)[0] * 10
            LT.append(dict(taxon=tx, serie=nome, mesi_temperatura=f"{mesi[0]}-{mesi[1]}", n_anni=len(j),
                           anni=f"{j.index.min()}-{j.index.max()}",
                           spearman_rho=rho, p=p, giorni_per_grado=lr.slope, errore_std=lr.stderr,
                           rho_senza_tendenza=rho_d, p_senza_tendenza=p_d,
                           tendenza_temp_C_per_decennio=tr_t))
    LT = pd.DataFrame(LT)
    LT.to_csv(os.path.join(out, "legame_temperature.csv"), sep=";", index=False)

    # ---- alberi del censimento comunale, ed. 2025
    al = pd.read_csv(os.path.join(M, "alberi", "pulito", "alberi.csv"), sep=";",
                     usecols=["edizione", "genere", "famiglia"], low_memory=False)
    al = al[al.edizione.astype(str).str.startswith("2025")]
    tot = len(al)
    gruppi = {"Betula (betulla)": al.genere == "Betula", "Platanus (platano)": al.genere == "Platanus",
              "Cupressaceae (cipressi, tuie, calocedri, ginepri...)": al.famiglia == "Cupressaceae",
              "Taxaceae (tasso)": al.famiglia == "Taxaceae",
              "Corylus (nocciolo)": al.genere == "Corylus", "Alnus (ontano)": al.genere == "Alnus",
              "Fraxinus (frassino)": al.genere == "Fraxinus", "Quercus (quercia)": al.genere == "Quercus",
              "Carpinus (carpino)": al.genere == "Carpinus", "Ulmus (olmo)": al.genere == "Ulmus",
              "Populus (pioppo)": al.genere == "Populus", "Celtis (bagolaro; famiglia Cannabaceae)": al.genere == "Celtis",
              "Ostrya": al.genere == "Ostrya"}
    A = pd.DataFrame([dict(gruppo=k, alberi_2025=int(v.sum()), quota_pct=round(100 * v.sum() / tot, 2))
                      for k, v in gruppi.items()])
    A.loc[len(A)] = dict(gruppo="TOTALE censimento comunale 2025", alberi_2025=tot, quota_pct=100.0)
    A.to_csv(os.path.join(out, "alberi_contesto.csv"), sep=";", index=False)

    # ---- riepilogo tipico per taxon e stazione (mediane sugli anni validi; date in giorno dell'anno e come data 2001)
    def d2(x):
        return (datetime.date(2001, 1, 1) + datetime.timedelta(days=int(round(x)) - 1)).strftime("%d/%m")
    RS = V.groupby(["taxon", "stazione"]).agg(anni_validi=("anno", "count"), primo=("anno", "min"), ultimo=("anno", "max"),
                                             inizio_doy=("inizio_doy", "median"), picco_doy=("picco_doy", "median"),
                                             fine_doy=("fine_doy", "median"), durata_mediana=("durata_giorni", "median"),
                                             integrale_mediano=("integrale", "median"),
                                             picco_valore_mediano=("picco_valore", "median"),
                                             giorni_ge_medio_mediani=("giorni_ge_medio", "median")).reset_index()
    for c in ["inizio", "picco", "fine"]:
        RS[c + "_tipico"] = RS[c + "_doy"].map(d2)
    RS.to_csv(os.path.join(out, "riepilogo_taxon_stazione.csv"), sep=";", index=False)

    # ---- riepilogo
    ri = {"anni_validi_per_taxon_stazione": V.groupby(["taxon", "stazione"]).anno.agg(["count", "min", "max"]).reset_index().to_dict("records"),
          "righe_stagioni": len(S), "valide": int(S.valida.sum())}
    json.dump(ri, open(os.path.join(out, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
    print("stagioni", len(S), "valide", int(S.valida.sum()))
    print(T[T.stazione == "NO1"].round(3).to_string())


if __name__ == "__main__":
    main()
