"""Scrive i file dati della pagina "Il consiglio comunale: presenze e voti" (docs/consiglio/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <consiglio_dir> <docs_dir>

Legge consiglio/pulito/{consiglieri.csv, serie_cumulata.csv, gruppi.csv, per_periodo.csv, per_sesso.csv, per_sesso_gruppo.csv, surroghe.csv,
  controlli.json} e consiglio/raw/download_log.csv (prodotti da build.py e scarica.py).
Scrive in <docs_dir>/consiglio/data/: riepilogo.json (tutti i numeri della pagina, con i controlli), consiglieri.json (tabella della pagina),
  e copie CSV: consiglieri.csv, serie_cumulata.csv, gruppi.csv, per_periodo.csv, per_sesso.csv, per_sesso_gruppo.csv, surroghe.csv.
Dati pubblicati: nome, gruppo, sesso (dal Ministero dell'Interno), presenze e votazioni dei consiglieri comunali nel loro ruolo pubblico, come
nei file del Comune. Nessun altro dato personale.
"""
import sys, os, json, csv, shutil
import pandas as pd, numpy as np

C, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(C, "pulito"); OUT = os.path.join(DOCS, "consiglio", "data"); os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso}, tolleranza {tol})")
def num(x, d=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)

cons = pd.read_csv(os.path.join(PU, "consiglieri.csv"))
ser = pd.read_csv(os.path.join(PU, "serie_cumulata.csv"))
grp = pd.read_csv(os.path.join(PU, "gruppi.csv"))
per = pd.read_csv(os.path.join(PU, "per_periodo.csv"))
sess = pd.read_csv(os.path.join(PU, "per_sesso.csv"))
sg = pd.read_csv(os.path.join(PU, "per_sesso_gruppo.csv"))
sur = pd.read_csv(os.path.join(PU, "surroghe.csv"))
ctl = json.load(open(os.path.join(PU, "controlli.json"), encoding="utf8"))
test = json.load(open(os.path.join(PU, "per_sesso_test.json"), encoding="utf8"))
dl = pd.read_csv(os.path.join(C, "raw", "download_log.csv"), sep=";")
MAND = ["2016-2021", "2021-2026"]

# ------------------------------------------------------------ per mandato
RES = {}
for m in MAND:
    x = cons[cons.mandato == m]
    s = x[x.sindaco == 0]
    sind = x[x.sindaco == 1].iloc[0]
    pp = per[per.mandato == m]
    ult = ser[ser.mandato == m].periodo.max(); pri = ser[ser.mandato == m].periodo.min()
    ses_tot = int(pp.sedute_del_consiglio.sum()); vot_tot = int(pp.votazioni_del_consiglio.sum())
    # sedute e votazioni del consiglio = massimo cumulato nel file dell'ultimo mese
    ul = ser[(ser.mandato == m) & (ser.periodo == ult)]
    check(f"{m}: sedute del consiglio (somma dei periodi = ultimo cumulato)", ses_tot, int(ul.sedute.max()))
    check(f"{m}: votazioni del consiglio (somma dei periodi = ultimo cumulato)", vot_tot, int(ul.votazioni_totali.max()))
    sedute_p = int(s.sedute.sum()); pres = int(s.presenze.sum()); vt = int(s.votazioni_totali.sum()); ve = int(s.votazioni_effettuate.sum())
    # partecipanti medi a ogni votazione e presenti medi a ogni seduta (tutti i consiglieri, sindaco compreso)
    ppl_vot = x.votazioni_effettuate.sum() / vot_tot
    ppl_sed = x.presenze.sum() / ses_tot
    RES[m] = {
        "primo_mese": pri, "ultimo_mese": ult, "sedute": ses_tot, "votazioni": vot_tot,
        "persone": int(len(x)), "persone_senza_sindaco": int(len(s)),
        "donne": int((s.sesso == "F").sum()), "uomini": int((s.sesso == "M").sum()), "sesso_non_noto": int((~s.sesso.isin(["F", "M"])).sum()),
        "pct_presenze": num(100 * pres / sedute_p, 2), "pct_votazioni": num(100 * ve / vt, 2),
        "mediana_presenze": num(s.pct_presenze.median(), 1), "mediana_votazioni": num(s.pct_votazioni.median(), 1),
        "presenti_medi_per_seduta": num(ppl_sed, 1), "partecipanti_medi_per_votazione": num(ppl_vot, 1),
        "presenze_ge90": int((s.pct_presenze >= 90).sum()), "presenze_lt70": int((s.pct_presenze < 70).sum()),
        "sindaco": {"nome": sind.consigliere, "sedute": int(sind.sedute), "presenze": int(sind.presenze), "pct_presenze": num(sind.pct_presenze, 1),
                    "pct_votazioni": num(sind.pct_votazioni, 1)},
        "cambi_gruppo": int((s.cambi_gruppo > 0).sum()),
        "ingressi_dopo_inizio": int((s.primo_periodo > ("2016-12" if m == "2016-2021" else "2021-10")).sum()),
    }
    check(f"{m}: Σ presenze dei consiglieri = presenze in gruppi.csv (± effetto dei 3 cumulati che scendono nella fonte)",
          pres, int(grp[(grp.mandato == m)].presenze.sum()), 3)

# ------------------------------------------------------------ gruppi
G = {}
for m in MAND:
    g = grp[grp.mandato == m].copy().sort_values("sedute_persona", ascending=False)
    G[m] = [{"gruppo": r.gruppo, "persone": int(r.persone_che_ne_hanno_fatto_parte), "sedute_persona": int(r.sedute_persona), "pct_presenze": num(r.pct_presenze, 1),
             "pct_votazioni": num(r.pct_votazioni, 1), "differenza": num(r.differenza_punti, 1)} for r in g.itertuples()]

# ------------------------------------------------------------ nel tempo
P = []
for r in per.itertuples():
    lab = {("2016-2021", 2016): "2016 (lug-dic)", ("2016-2021", 2021): "2021 (gen-set)", ("2021-2026", 2021): "2021 (ott-dic)", ("2021-2026", 2026): "2026 (gen-mag)"}.get((r.mandato, r.periodo), str(r.periodo))
    P.append({"mandato": r.mandato, "periodo": int(r.periodo), "etichetta": lab, "sedute": int(r.sedute_del_consiglio), "votazioni": int(r.votazioni_del_consiglio),
              "pct_presenze": num(r.pct_presenze_senza_sindaco, 1), "pct_votazioni": num(r.pct_votazioni_senza_sindaco, 1),
              "presenti_medi": num(r.presenti_medi_per_seduta, 1), "partecipanti_medi": num(r.partecipanti_medi_per_votazione, 1)})

# ------------------------------------------------------------ donne e uomini
SX = {}
for m in MAND:
    SX[m] = {}
    s = cons[(cons.mandato == m) & (cons.sindaco == 0) & cons.sesso.isin(["F", "M"])]
    for k in ("F", "M"):
        r = sess[(sess.mandato == m) & (sess.sesso == k)].iloc[0]
        a = sg[(sg.mandato == m) & (sg.sesso == k)].iloc[0]
        x = s[s.sesso == k].sort_values("pct_presenze")
        senza3 = x.iloc[3:]
        SX[m][k] = {"persone": int(r.persone), "pct_presenze": num(r.pct_presenze, 1), "pct_votazioni": num(r.pct_votazioni, 1),
                    "mediana_presenze": num(r.mediana_pct_presenze_per_persona, 1), "mediana_votazioni": num(r.mediana_pct_votazioni_per_persona, 1),
                    "pct_presenze_attesa_dal_gruppo": num(a.pct_attesa_dal_gruppo, 1), "differenza_dal_gruppo": num(a.differenza_punti, 1),
                    "differenza_dal_gruppo_votazioni": num(a.differenza_punti_vot, 1),
                    "pct_presenze_senza_le_3_piu_basse": num(100 * senza3.presenze.sum() / senza3.sedute.sum(), 1),
                    "presenze_ge90": int((x.pct_presenze >= 90).sum()),
                    "test_casualita": test[m]}
        check(f"{m} {k}: persone in per_sesso.csv = persone con sesso noto senza sindaco", int(r.persone), len(x))

# ------------------------------------------------------------ surroghe / ingressi e uscite 2021-26
sur_rows = [{"consigliere": r.consigliere, "primo_mese": r.primo_mese, "ultimo_mese": r.ultimo_mese,
             "nota": r.nota_nel_file_presenze if isinstance(r.nota_nel_file_presenze, str) else "", "in_ds1914": r.in_ds1914} for r in sur.itertuples()]
ingressi = [r for r in sur_rows if r["primo_mese"] > "2021-10"]
uscite = [r for r in sur_rows if r["ultimo_mese"] < "2026-05"]
SUR = {"ingressi_nei_file_presenze": len(ingressi), "uscite_nei_file_presenze": len(uscite),
       "ingressi_in_ds1914": sum(1 for r in ingressi if r["in_ds1914"] == "si"), "uscite_in_ds1914": sum(1 for r in uscite if r["in_ds1914"] == "si"),
       "righe_ds1914": 4, "righe": sur_rows}
check("ingressi + uscite: persone nei file di presenze (ds1643) con ingresso o uscita", len({r['consigliere'] for r in ingressi + uscite}), 20)

# ------------------------------------------------------------ tabella consiglieri (per la pagina)
T = []
for r in cons.sort_values(["mandato", "pct_presenze"], ascending=[True, False]).itertuples():
    T.append({"m": r.mandato, "n": r.consigliere, "s": r.sesso if isinstance(r.sesso, str) else "", "g": r.gruppo_finale, "gg": r.gruppi,
              "se": int(r.sedute), "pr": int(r.presenze), "p": num(r.pct_presenze, 1), "vt": int(r.votazioni_totali), "ve": int(r.votazioni_effettuate),
              "v": num(r.pct_votazioni, 1), "a": r.primo_periodo, "z": r.ultimo_periodo, "k": int(r.sindaco)})
json.dump(T, open(os.path.join(OUT, "consiglieri.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------ sorgenti
FONTI = [{"dataset": d, "file": int(n), "scaricato": str(dl[dl.dataset == d].data.iloc[0]), "licenza": str(dl[dl.dataset == d].licenza.iloc[0])}
         for d, n in dl.groupby("dataset").size().items()]

R = {
    "scaricato": str(dl.data.max()),
    "mandati": RES, "gruppi": G, "per_periodo": P, "sesso": SX, "surroghe": SUR, "fonti": FONTI,
    "controlli_build": {k: v for k, v in ctl.items()},
    "n_cumulati_che_scendono": int(ctl["cumulati_che_scendono"]["dettaglio"].split(" ")[0]),
}
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# copie CSV da scaricare (nomi di colonna invariati)
cons.drop(columns=["chiave", "sesso_fonte"]).to_csv(os.path.join(OUT, "consiglieri.csv"), index=False)
for f in ("serie_cumulata.csv", "gruppi.csv", "per_periodo.csv", "per_sesso.csv", "per_sesso_gruppo.csv", "surroghe.csv"):
    shutil.copyfile(os.path.join(PU, f), os.path.join(OUT, f))

# controlli finali
for k, v in ctl.items():
    if not v["ok"]: AVVISI.append(f"controllo di build non superato: {k}: {v['dettaglio']}")
print("AVVISI:", AVVISI if AVVISI else "nessuno")
if AVVISI: sys.exit(1)
