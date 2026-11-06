"""Scrive docs/scuole/data/invalsi_milano.json: i tre blocchi INVALSI della pagina scuole (quartieri, licei, statali e paritarie).

Uso: python -I -X utf8 invalsi_milano_pagina.py <cartella scuole> <cartella docs>
Legge dal pulito (invalsi_istituti.csv, invalsi_superiori.csv, invalsi_paritarie.csv, invalsi_istituti_quota_stranieri.csv,
miur_scuole_anno.csv) e dall'anagrafe del Ministero in raw/miur (nome e codice dell'istituto di riferimento, plesso con piu' iscritti).
Solo righe di istituto: mai plessi, sezioni o classi. Un solo anno scolastico: 2024/25.

Regole (stesse di invalsi_analisi_milano.py e invalsi_paritarie_confronto.py, piu' i punti segnati):
- Quartiere di un istituto = quello del plesso con piu' iscritti (i plessi sono nell'anagrafe del Ministero).
- Zone: 5a primaria e 3a media, italiano e matematica; scarto dalla Lombardia (punteggio - media lombarda della stessa prova),
  poi standardizzato dentro ogni prova (meno la media, diviso la deviazione standard degli istituti di Milano); lo stesso per la
  differenza da scuole con contesto simile. Media per quartiere sulle prove disponibili (come nell'analisi originale).
- Licei e tecnici: tipo secondo la tabella del portale. In matematica il portale separa i licei scientifici da tutti gli altri
  licei (classici e linguistici compresi), in italiano separa scientifici+classici+linguistici dagli altri licei.
- Paritarie, superiori: le pagine riportano anche righe di altre scuole dello stesso gestore. Si tengono solo le scuole il cui nome
  e' coerente con il tipo: per i licei nome con LICEO o SAN RAFFAELE (e il tipo giusto: scientifico/classico/linguistico oppure
  artistico/scienze umane/musicale/coreutico); per tecnici e professionali nome senza LICEO ne' SAN RAFFAELE (professionali:
  nome con PROFESSIONALE; tecnici: senza). Media se lo stesso istituto ha piu' righe. Gli istituti tecnici con nome di liceo
  vanno fuori dai tecnici, e viceversa.
- Primo ciclo paritarie: si tolgono le righe doppie con stesso punteggio e stessa differenza (pagine dello stesso gestore).
"""
import glob
import json
import os
import sys
import unicodedata

import numpy as np
import pandas as pd

BASE, DOCS = sys.argv[1], sys.argv[2]
P = os.path.join(BASE, "pulito")
ANNO = "2024/2025"
ITA_MAT = ["Italiano", "Matematica"]


def rd(f):
    return pd.read_csv(os.path.join(P, f), sep=";", encoding="utf-8-sig", dtype={"istituto": str})


def num(d):
    d = d.copy()
    for c in ("punteggio", "lombardia", "diff_escs", "partecipazione"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["scarto"] = d.punteggio - d.lombardia
    return d


def fixtxt(s):
    return str(s).replace("Â°", "°").strip()


def r1(x):
    return None if pd.isna(x) else round(float(x), 1)


def r2(x):
    return None if pd.isna(x) else round(float(x), 2)


# ---- anagrafe: nome, quartiere (plesso con piu' iscritti) ----
ms = pd.read_csv(os.path.join(P, "miur_scuole_anno.csv"), sep=";", encoding="utf-8-sig", dtype=str)
ms = ms[ms.anno_scolastico == ms.anno_scolastico.max()]
g = pd.read_csv(sorted(glob.glob(os.path.join(BASE, "raw", "miur", "SCUANAGRAFESTAT*.csv")))[-1], dtype=str, keep_default_na=False)
g = g[g.CODICECOMUNESCUOLA == "F205"]
NOME = g.drop_duplicates("CODICEISTITUTORIFERIMENTO").set_index("CODICEISTITUTORIFERIMENTO").DENOMINAZIONEISTITUTORIFERIMENTO.to_dict()
pl = g[["CODICEISTITUTORIFERIMENTO", "CODICESCUOLA"]].merge(ms[["codice_mecc", "nil", "iscritti"]], left_on="CODICESCUOLA", right_on="codice_mecc", how="left")
pl["iscritti"] = pd.to_numeric(pl["iscritti"], errors="coerce")


def zona(x):
    x = x.dropna(subset=["nil", "iscritti"])
    if x.empty:
        return None
    return x.groupby("nil").iscritti.sum().idxmax()


NIL = pl.groupby("CODICEISTITUTORIFERIMENTO").apply(zona).to_dict()


def chiave(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(c for c in s if c.isalnum())


gj = json.load(open(os.path.join(DOCS, "scuole", "data", "nil.geojson"), encoding="utf-8"))
BELLI = {chiave(f["properties"]["n"]): f["properties"]["n"] for f in gj["features"]}


def bello(n):
    return BELLI.get(chiave(n)) or str(n).title()


QS = rd("invalsi_istituti_quota_stranieri.csv").set_index("istituto")

# ---- primo ciclo statali ----
pc = num(rd("invalsi_istituti.csv"))
pc = pc[(pc.anni == ANNO) & pc.materia.isin(ITA_MAT)]
GR5, GR3 = "Scuola primaria - classi quinte", "Scuola secondaria di primo grado - classi terze"

# ---- 1. quartieri ----
z = pc[pc.grado.isin([GR5, GR3])].dropna(subset=["scarto"]).copy()
z["zs"] = z.groupby(["grado", "materia"]).scarto.transform(lambda s: (s - s.mean()) / s.std())
z["ze"] = z.groupby(["grado", "materia"]).diff_escs.transform(lambda s: (s - s.mean()) / s.std())
z["nil"] = z.istituto.map(NIL)
senza = z[z.nil.isna()].istituto.nunique()
zq = z.dropna(subset=["nil"]).groupby("nil").agg(i=("istituto", "nunique"), prove=("zs", "size"), p=("zs", "mean"), c=("ze", "mean")).reset_index()
zq = zq.sort_values("p", ascending=False)
zone = [dict(q=bello(r.nil), i=int(r.i), p=r2(r.p), c=r2(r.c)) for r in zq.itertuples()]
print("QUARTIERI", len(zone), "istituti", int(zq.i.sum()), "senza quartiere", senza)

# ---- superiori statali ----
su = num(rd("invalsi_superiori.csv"))
su_pagina = su.istituto.nunique()
su = su[(su.anni == ANNO) & su.materia.isin(ITA_MAT)].dropna(subset=["scarto"]).copy()
su["nome"] = su.istituto.map(NOME).map(fixtxt)


def classifica(grado, materia):
    """(tipo, classe, sotto) secondo la tabella del portale; tipo t1/t2/t3."""
    cl = "quinta" if "quinte" in grado else "seconda"
    if grado.startswith("Licei scientifici, classici"):
        return ("t1", cl, None) if materia == "Italiano" else (None, cl, None)
    if grado.startswith("Licei scientifici -"):
        return ("t1", cl, None) if materia == "Matematica" else (None, cl, None)
    if grado.startswith("Altri Licei"):
        return ("t2", cl, None)
    if grado.startswith("Istituti Tecnici"):
        return ("t3", cl, "tecnico")
    if grado.startswith("Istituti Professionali"):
        return ("t3", cl, "professionale")
    return (None, cl, None)


cls = [classifica(a, b) for a, b in zip(su.grado, su.materia)]
su["tipo"], su["classe"], su["sotto"] = [c[0] for c in cls], [c[1] for c in cls], [c[2] for c in cls]
su = su.dropna(subset=["tipo"])
# una sola riga per istituto, prova e tipo (media se doppie)
chi = ["istituto", "nome", "tipo", "classe", "materia", "sotto"]
su["sotto_k"] = su.sotto.fillna("")
su = su.drop(columns="sotto").rename(columns={"sotto_k": "sotto"})
su = su.groupby(chi, as_index=False)[["punteggio", "lombardia", "diff_escs", "scarto"]].mean()
su["gest"] = "S"
su["q"] = su.istituto.map(lambda c: QS.quota_sec2.get(c, np.nan))
print("SUPERIORI statali con pagina", su_pagina, "con punteggi 2024/25", su.istituto.nunique())

# ---- paritarie ----
par_all = num(rd("invalsi_paritarie.csv"))
par_all["nome"] = par_all.nome.map(fixtxt)
tot = []
for f in glob.glob(os.path.join(BASE, "raw", "invalsi_rav_par", "*.json")):
    d = json.load(open(f, encoding="utf8"))
    tot.append(dict(ist=d["istituto"], punt=sum(r.get("punteggio") is not None for r in d["righe"]), a2425=any(r.get("punteggio") is not None and r.get("anno") == ANNO for r in d["righe"])))
par_cod = len(tot)
par_con = sum(1 for t in tot if t["punt"] > 0)
par_2425 = par_all[(par_all.anni == ANNO) & par_all.punteggio.notna()].istituto.nunique()
print("PARITARIE codici", par_cod, "con punteggi", par_con, "con 2024/25", par_2425)
par = par_all[(par_all.anni == ANNO) & par_all.materia.isin(ITA_MAT)].dropna(subset=["scarto"]).copy()


def coerente(nome, tipo, sotto, materia):
    n = nome.upper()
    liceo = ("LICEO" in n) or ("SAN RAFFAELE" in n)
    if tipo == "t3":
        if liceo:
            return False
        return ("PROFESSIONALE" in n) if sotto == "professionale" else ("PROFESSIONALE" not in n)
    if not liceo:
        return False
    altri = any(k in n for k in ("ARTISTIC", "SCIENZE UMANE", "MUSICAL", "COREUT"))
    scient = "SCIENTIFIC" in n or "SAN RAFFAELE" in n
    if tipo == "t1":
        if altri:
            return False
        if materia == "Matematica":
            return scient          # in matematica il tipo e' solo "licei scientifici"
        return True                # italiano: scientifici, classici, linguistici (tutti i licei non "altri")
    if tipo == "t2":
        if materia == "Matematica":
            return not scient      # classici, linguistici e altri licei
        return altri
    return False


cp = [classifica(a, b) for a, b in zip(par.grado, par.materia)]
par["tipo"], par["classe"], par["sotto"] = [c[0] for c in cp], [c[1] for c in cp], [c[2] or "" for c in cp]
parp = par.dropna(subset=["tipo"]).copy()
ok = [coerente(n, t, s, m) for n, t, s, m in zip(parp.nome, parp.tipo, parp.sotto, parp.materia)]
print("PARITARIE superiori: righe", len(parp), "tenute", int(sum(ok)))
parp = parp[ok]
parp = parp.groupby(["istituto", "nome", "tipo", "classe", "materia", "sotto"], as_index=False)[["punteggio", "lombardia", "diff_escs", "scarto"]].mean()
parp["gest"] = "P"
parp["q"] = np.nan
dup = parp.duplicated(["tipo", "classe", "materia", "punteggio", "diff_escs"], keep=False).sum()
print("paritarie superiori con punteggio e differenza uguali ad altre righe:", int(dup))

# ---- 2. licei ----
TIPI = [("t1", "Licei scientifici, classici e linguistici"), ("t2", "Altri licei"), ("t3", "Tecnici e professionali")]
PROVE = [("ita5", "Italiano", "quinta", "Italiano, quinta"), ("ita2", "Italiano", "seconda", "Italiano, seconda"),
         ("mat5", "Matematica", "quinta", "Matematica, quinta"), ("mat2", "Matematica", "seconda", "Matematica, seconda")]
tutti = pd.concat([su, parp], ignore_index=True)
licei = {"tipi": []}
for tid, tnome in TIPI:
    blocco = {"id": tid, "nome": tnome, "prove": {}}
    for pid, mat, cl, _ in PROVE:
        x = tutti[(tutti.tipo == tid) & (tutti.materia == mat) & (tutti.classe == cl)].sort_values("scarto", ascending=False)
        righe = []
        for r in x.itertuples():
            d = dict(n=r.nome, g=r.gest, p=r1(r.punteggio), l=r1(r.lombardia), s=r1(r.punteggio - r.lombardia), e=r1(r.diff_escs), q=r1(r.q))
            if tid == "t3":
                d["t"] = r.sotto
            righe.append(d)
        blocco["prove"][pid] = righe
    licei["tipi"].append(blocco)
    print("LICEI", tid, {k: (sum(1 for r in v if r["g"] == "S"), sum(1 for r in v if r["g"] == "P")) for k, v in blocco["prove"].items()})

# ---- 3. statali e paritarie ----
def conf(sa, pa, titolo, pid):
    if sa.istituto.nunique() < 3 or pa.istituto.nunique() < 3:
        return None
    return dict(id=pid, t=titolo, ns=int(sa.istituto.nunique()), np=int(pa.istituto.nunique()),
                ss=r1(sa.scarto.mean()), sp=r1(pa.scarto.mean()), es=r1(sa.diff_escs.mean()), ep=r1(pa.diff_escs.mean()))


primo = []
pcs = pc.dropna(subset=["scarto"])
pp = par_all[(par_all.anni == ANNO) & par_all.materia.isin(ITA_MAT)].copy()
pp["scarto"] = pp.punteggio - pp.lombardia
pp = pp.dropna(subset=["scarto"])
for gr, glab in ((GR5, "5ª primaria"), (GR3, "3ª media")):
    for mat in ITA_MAT:
        a = pcs[(pcs.grado == gr) & (pcs.materia == mat)]
        b0 = pp[(pp.grado == gr) & (pp.materia == mat)]
        b = b0.drop_duplicates(["punteggio", "diff_escs"])
        print("PRIMO CICLO", glab, mat, "righe paritarie", len(b0), "dopo righe doppie", len(b))
        c = conf(a, b, "%s, %s" % (glab, mat.lower()), "%s-%s" % (glab[:2], mat[:3]))
        if c:
            primo.append(c)
sup_c = []
for tid, tnome in TIPI:
    for pid, mat, cl, plab in PROVE:
        x = tutti[(tutti.tipo == tid) & (tutti.materia == mat) & (tutti.classe == cl)]
        c = conf(x[x.gest == "S"], x[x.gest == "P"], "%s, %s" % (tnome, plab.lower()), "%s-%s" % (tid, pid))
        if c:
            sup_c.append(c)

out = dict(anno="2024/25",
           conti=dict(sup_statali_pagina=int(su_pagina), sup_statali_2425=int(su.istituto.nunique()), par_codici=int(par_cod), par_con_punteggi=int(par_con), par_2425=int(par_2425),
                      zone_quartieri=len(zone), zone_istituti=int(zq.i.sum())),
           zone=zone, licei=licei, confronto=dict(primo=primo, sup=sup_c))
p = os.path.join(DOCS, "scuole", "data", "invalsi_milano.json")
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scritto", p, os.path.getsize(p), "byte")
for c in primo + sup_c:
    print(c)
