"""Fase 2, passo 3: aggrega per sezione i record individuali del Comune (1991, 2001).
Uso: python -I h3_micro.py <cartella censimenti>
Legge lo zip in streaming (non estrae nulla). Residenti: 1991 TR=2 (componenti famiglia) + TR=4 (convivenze);
2001 TR in (1,2) (abitualmente dimoranti in alloggi e convivenze).
Output: pulito/micro_sezioni_<anno>.csv (una riga per CodSez: persone, somma eta', 65+, 75+, 80+, 85+, 90+, stranieri, laureati)
        pulito/micro_cittadinanza_<anno>.csv (CodSez, Nazione, persone) solo non italiani
        pulito/micro_codici_nazione.csv (Nazione, nome, anno)
"""
import sys, zipfile, io
import pandas as pd

root = sys.argv[1]
C = root + "/raw/comune_ckan/"
cfg = {
    1991: dict(zip=C + "ds1636-censimento-1991-popolazione-residente/00_ds1636-censimento-1991-residenti.zip",
               dec=C + "ds1636-censimento-1991-popolazione-residente/02_ds1636-censimento-1991-residenti-decodifiche.csv",
               tr=[2, 4], cit="Cittad2Mod", cit_it=1, extra=["TitStudioRicl", "LaureaRicl"]),
    2001: dict(zip=C + "ds1518-censimento-2001-popolazione-residente/00_ds1518-censimento-2001-popolazione-residente.zip",
               dec=C + "ds1518-censimento-2001-popolazione-residente/02_ds1518-censimento-2001-popolazione-residente-decodifiche.csv",
               tr=[1, 2], cit="Cittad3Mod", cit_it=1, extra=["LaureaRicl"]),
}
names = []
for y, c in cfg.items():
    dec = pd.read_csv(c["dec"], sep=";")
    for col in ["Nazione"]:
        d = dec[dec.Colonna == col][["Valore", "Decodifica"]].copy(); d["anno"] = y; names.append(d)
    z = zipfile.ZipFile(c["zip"]); fn = z.namelist()[0]
    head = pd.read_csv(z.open(fn), sep=";", nrows=1).columns.tolist()
    use = ["TR", "CodSez", "Eta", c["cit"], "Nazione"] + [e for e in c["extra"] if e in head]
    agg, cits, trs = [], [], {}
    for ch in pd.read_csv(z.open(fn), sep=";", usecols=use, chunksize=300000, low_memory=False):
        for k, v in ch.TR.value_counts().items(): trs[k] = trs.get(k, 0) + v
        ch = ch[ch.TR.isin(c["tr"])].copy()
        ch["Eta"] = pd.to_numeric(ch.Eta, errors="coerce")
        ch["n"] = 1
        ch["eta_ok"] = ch.Eta.notna().astype(int)
        ch["eta_sum"] = ch.Eta.fillna(0)
        for t in (65, 75, 80, 85, 90):
            ch[f"p{t}"] = (ch.Eta >= t).astype(int)
        ch["stran"] = (ch[c["cit"]] != c["cit_it"]).astype(int)
        cols = ["n", "eta_ok", "eta_sum", "p65", "p75", "p80", "p85", "p90", "stran"]
        agg.append(ch.groupby("CodSez")[cols].sum())
        s = ch[ch.stran == 1]
        cits.append(s.groupby(["CodSez", "Nazione"]).size().rename("persone").reset_index())
    print(y, "righe per TR (tutto il file):", trs)
    a = pd.concat(agg).groupby(level=0).sum().reset_index()
    a.insert(0, "anno", y)
    a.to_csv(root + f"/pulito/micro_sezioni_{y}.csv", index=False)
    ci = pd.concat(cits).groupby(["CodSez", "Nazione"]).persone.sum().reset_index()
    ci.insert(0, "anno", y)
    ci.to_csv(root + f"/pulito/micro_cittadinanza_{y}.csv", index=False)
    print(y, "residenti nei record:", int(a.n.sum()), "sezioni:", len(a), "stranieri:", int(a.stran.sum()),
          "eta' media esatta:", round(a.eta_sum.sum() / a.eta_ok.sum(), 3), "80+:", int(a.p80.sum()))
pd.concat(names).rename(columns={"Valore": "nazione_cod", "Decodifica": "nome"}).to_csv(root + "/pulito/micro_codici_nazione.csv", index=False)
