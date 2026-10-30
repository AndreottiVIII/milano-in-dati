# Fase 2: dati piccoli + pagina per docs/acqua-del-sindaco/
# uso: python -I scripts\pagina_dati.py <cartella acqua-del-sindaco> <cartella docs\acqua-del-sindaco>
# Rifacibile: legge solo pulito\*, scrive docs\acqua-del-sindaco\data\* e index.html (da pagina_template.html).
import csv, json, os, re, sys, shutil, itertools, statistics
import numpy as np
import pandas as pd

base, out = sys.argv[1:3]
pul = os.path.join(base, "pulito")
here = os.path.dirname(os.path.abspath(__file__))
dat = os.path.join(out, "data")
os.makedirs(dat, exist_ok=True)

ZONE = [("NO", "Nord-Ovest", 6), ("NE", "Nord-Est", 18), ("SE", "Sud-Est", 16), ("SO", "Sud-Ovest", 15)]
ZC = [z[0] for z in ZONE]

# ------------------------------------------------------------------ analisi mensile
A = pd.read_csv(os.path.join(pul, "analisi.csv"), sep=";", dtype=str, keep_default_na=False)
M = A[A.periodo_tipo == "mese"].copy()
M["v"] = pd.to_numeric(M.valore, errors="coerce")
M["thr"] = pd.to_numeric(M.soglia, errors="coerce")
# 4 valori "0" di manganese: probabile sotto soglia non marcato (NOTE.md, sez. 3): non sono mai uno zero misurato
zero_ss = M.nota_valore.str.contains('probabile "sotto soglia"', regex=False)
M.loc[zero_ss, "qualita_dato"] = "zero_probabile_sotto_soglia"
M.loc[zero_ss, "v"] = np.nan
M["a"] = M.anno.astype(int)
M["mm"] = M.mese.astype(int)
mesi = sorted(M.periodo.unique())
# calendario completo (anche i mesi che il Comune non ha pubblicato)
y0, m0 = map(int, mesi[0].split("-")); y1, m1 = map(int, mesi[-1].split("-"))
cal = []
y, m = y0, m0
while (y, m) <= (y1, m1):
    cal.append("%04d-%02d" % (y, m)); m += 1
    if m == 13: y += 1; m = 1
mancanti = [p for p in cal if p not in mesi]
ultimo = mesi[-1]
# finestra "ultimi 12 mesi" = 12 mesi di calendario che finiscono nell'ultimo mese pubblicato
fin = cal[-12:]
mese_file = {p: g.file_origine.iloc[0] for p, g in M.groupby("periodo")}
mese_ds = {p: g.dataset.iloc[0] for p, g in M.groupby("periodo")}
file_ds = {}
for p in mesi: file_ds.setdefault(mese_file[p], mese_ds[p].split("_")[0])
file_periodi = {}
for p in mesi: file_periodi.setdefault(mese_file[p], []).append(p)

# ------------------------------------------------------------------ parametri
NOMI = {
    "residuo_fisso_180": "Residuo fisso a 180 °C", "durezza": "Durezza", "ph": "pH", "calcio": "Calcio",
    "magnesio": "Magnesio", "sodio": "Sodio", "potassio": "Potassio", "bicarbonati": "Bicarbonati",
    "solfati": "Solfati", "cloruri": "Cloruri", "nitrati": "Nitrati", "fluoruri": "Fluoruri",
    "conducibilita": "Conducibilità a 20 °C", "ammonio": "Ammonio", "nitriti": "Nitriti",
    "arsenico": "Arsenico", "manganese": "Manganese", "cloro_residuo": "Cloro residuo"}
BREVI = {"conducibilita": "Conducibilità", "residuo_fisso_180": "Residuo fisso"}
info = {r["parametro"]: r["testo_info"] for r in csv.DictReader(open(os.path.join(pul, "parametri_info.csv"), encoding="utf-8"), delimiter=";")}
par = []
for k in NOMI:
    g = M[M.parametro == k]
    r0 = g.iloc[0]
    dec = 0
    for t in g.valore_testo:
        mm_ = re.fullmatch(r"\d+[.,](\d+)", t.strip())
        if mm_: dec = max(dec, len(mm_.group(1)))
    par.append(dict(k=k, n=NOMI[k], nb=BREVI.get(k, NOMI[k]), u=r0.unita, dec=dec,
                    tipo=r0.limite_tipo, lt=r0.limite_testo.replace("*", "").strip(),
                    lmin=float(r0.limite_min) if r0.limite_min else None,
                    lmax=float(r0.limite_max) if r0.limite_max else None,
                    info=re.sub(r"\s+", " ", info.get(k, "")).strip()))

# ------------------------------------------------------------------ serie mensili (69 mesi x 4 zone x 18 parametri)
serie = {}
for k in NOMI:
    serie[k] = {}
    for z in ZC:
        g = M[(M.parametro == k) & (M.zona_codice == z)].set_index("periodo")
        arr = []
        for p in cal:
            if p not in g.index: arr.append(None); continue
            r = g.loc[p]
            q = r.qualita_dato
            if q == "ok" and not np.isnan(r.v): arr.append(float(r.v) if r.v != int(r.v) else int(r.v))
            elif q == "sotto_soglia": arr.append("<" + r.soglia)
            elif q == "anomalo": arr.append("!" + r.valore_testo)
            elif q == "zero_probabile_sotto_soglia": arr.append("?0")
            else: arr.append(None)
        serie[k][z] = arr

# ------------------------------------------------------------------ schede: ultimi 12 mesi
def num(x): return int(x) if float(x) == int(x) else round(float(x), 4)
sched = {}
for z in ZC:
    sched[z] = {}
    for k in NOMI:
        g = M[(M.parametro == k) & (M.zona_codice == z) & (M.periodo.isin(fin))]
        ok = g[(g.qualita_dato == "ok") & g.v.notna()]
        ss = g[g.qualita_dato == "sotto_soglia"]
        d = dict(n=int(len(ok)), ns=int(len(ss)), nn=int((g.qualita_dato == "non_misurato").sum()),
                 na=int((g.qualita_dato == "anomalo").sum()), pub=int(len(g)))
        if len(ok):
            vals = sorted(ok.v)
            d["med"] = num(statistics.median(vals)); d["min"] = num(vals[0]); d["max"] = num(vals[-1])
            d["pmin"] = ok.loc[ok.v.idxmin(), "periodo"]; d["pmax"] = ok.loc[ok.v.idxmax(), "periodo"]
        if len(ss):
            d["sg"] = [num(ss.thr.min()), num(ss.thr.max())]
        d["mesi"] = sorted(list(ok.periodo) + list(ss.periodo))
        d["files"] = sorted(set(g.file_origine))
        sched[z][k] = d

# ------------------------------------------------------------------ stagionalita': correlazione media tra anni (2022-2025, senza dic 2024)
stag = {}
for k in NOMI:
    cs = []
    for z in ZC:
        g = M[(M.parametro == k) & (M.zona_codice == z) & M.v.notna() & M.a.between(2022, 2025) & (M.periodo != "2024-12")]
        piv = g.pivot_table(index="mm", columns="a", values="v")
        piv = piv - piv.mean()
        for a_, b_ in itertools.combinations(piv.columns, 2):
            x = piv[[a_, b_]].dropna()
            if len(x) >= 6 and x[a_].std() > 0 and x[b_].std() > 0:
                cs.append(float(np.corrcoef(x[a_], x[b_])[0, 1]))
    stag[k] = dict(r=round(float(np.mean(cs)), 2) if cs else None, n=len(cs))

# ------------------------------------------------------------------ fonti per anno
anni_file = []
for f in sorted(file_periodi):
    ps = file_periodi[f]
    anni_file.append(dict(file=f, ds=file_ds[f], da=ps[0], a=ps[-1], mesi=len(ps)))

# ------------------------------------------------------------------ perdite
pr = list(csv.DictReader(open(os.path.join(pul, "perdite.csv"), encoding="utf-8"), delimiter=";"))[0]
perdite = {k: pr[k] for k in pr}

# ------------------------------------------------------------------ indirizzi (compatti)
C = pd.read_csv(os.path.join(pul, "civici_zone.csv"), sep=";", dtype=str, keep_default_na=False)
n_civici = len(C); n_stimati = int((C.fonte_zona != "ds1827 (MM, ufficiale)").sum())
SMALL = {"di", "del", "della", "dei", "delle", "dello", "degli", "da", "de", "al", "alla", "e", "ai", "in", "la", "le", "lo", "il", "dal", "dalla", "sul", "sulla", "sui", "nel", "nella", "per", "a"}
ROMAN = {"II", "III", "IV", "V", "VI", "XI", "XIV"}
APOS_LOW = {"dell", "d", "all", "nell", "dall", "sull", "un"}
ACC = {"A": "à", "E": "è", "I": "ì", "O": "ò", "U": "ù"}
def cap(w): return w[:1].upper() + w[1:].lower()
def bella(via):
    out_ = []
    for i, w in enumerate(via.split(), start=1):  # il tipo (Via, Piazza...) e' sempre prima
        if w in ROMAN: out_.append(w); continue
        if w.endswith("'") and len(w) > 2 and w not in ("DE'",):
            body = w[:-1]
            out_.append(cap(body[:-1] + ACC.get(body[-1], body[-1] + "'")) if body[-1] in ACC else cap(w)); continue
        if "'" in w and not w.endswith("'"):
            pre, post = w.split("'", 1)
            pre = pre.lower() if (pre.lower() in APOS_LOW and i > 0) else cap(pre)
            out_.append(pre + "'" + cap(post)); continue
        if w.lower() in SMALL and i > 0: out_.append(w.lower()); continue
        if "-" in w: out_.append("-".join(cap(x) for x in w.split("-"))); continue
        out_.append(cap(w))
    return " ".join(out_)
zi = {z: i for i, z in enumerate(ZC)}
def b36(n):
    s = ""; n = int(n)
    if n == 0: return "0"
    while n: s = "0123456789abcdefghijklmnopqrstuvwxyz"[n % 36] + s; n //= 36
    return s
C["est"] = (C.fonte_zona != "ds1827 (MM, ufficiale)").astype(int)
C["lonf"] = pd.to_numeric(C.lon, errors="coerce"); C["latf"] = pd.to_numeric(C.lat, errors="coerce")
strade = []
n_voci = 0; n_conflitti = 0
for kv, g in C.groupby("chiave_via", sort=True):
    tipo = g.tipo_via.iloc[0]; via = g.via.iloc[0]
    voci = []
    for ck, h in g.groupby("chiave_civico", sort=False):
        # zona prevalente: prima i civici ufficiali, poi la zona piu' frequente
        hh = h[h.est == 0] if (h.est == 0).any() else h
        vc = hh.zona_codice.value_counts()
        zona = vc.index[0]
        conf = 1 if len(set(h.zona_codice)) > 1 else 0
        n_conflitti += conf
        r = hh[hh.zona_codice == zona].iloc[0]
        code = zi[zona] + 4 * int(r.est) + 8 * conf
        lo = "" if np.isnan(r.lonf) else b36(round((r.lonf - 9.0) * 1e4))
        la = "" if np.isnan(r.latf) else b36(round((r.latf - 45.3) * 1e4))
        voci.append((ck, code, lo, la))
    def ordkey(t):
        mm_ = re.match(r"(\d+)(.*)", t[0]); return (int(mm_.group(1)), mm_.group(2)) if mm_ else (10**9, t[0])
    voci.sort(key=ordkey)
    n_voci += len(voci)
    strade.append([tipo + " " + bella(via), kv, ",".join("%s:%x:%s:%s" % v for v in voci)])
json.dump(dict(v=1, s=strade), open(os.path.join(dat, "indirizzi.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ zone approssimate
gj = json.load(open(os.path.join(pul, "zone_approx.geojson"), encoding="utf-8"))
def rnd(c):
    return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], float) else [rnd(x) for x in c]
feats = []
for f in gj["features"]:
    p = f["properties"]
    feats.append(dict(type="Feature", properties=dict(c=p["zona_codice"], n=p["zona_nome"], km2=p["area_km2"]),
                      geometry=dict(type=f["geometry"]["type"], coordinates=rnd(f["geometry"]["coordinates"]))))
json.dump(dict(type="FeatureCollection", features=feats), open(os.path.join(dat, "zone_approx.geojson"), "w", encoding="utf-8"), separators=(",", ":"))

# ------------------------------------------------------------------ riepilogo zone (civici)
zr = {r["zona_codice"]: r for r in csv.DictReader(open(os.path.join(pul, "zone_riepilogo.csv"), encoding="utf-8"), delimiter=";")}
zone = [dict(c=c, n=n, id=i, km2=float(zr[c]["area_km2"]), q_area=float(zr[c]["quota_area"]), q_civici=float(zr[c]["quota_civici"])) for c, n, i in ZONE]

# ------------------------------------------------------------------ PFAS (fase 3): solo riepiloghi, mai le righe
# Le tabelle MM (PDF senza licenza dichiarata) sono trascritte in raw\pfas\*.csv (trascrizione controllata riga per riga col PDF).
# Alla pagina vanno soltanto conteggi, massimo, minimo, mediana e il numero di analisi per fascia.
pf_dir = os.path.join(base, "raw", "pfas")
pf = []   # (origine, data, punto, valore o None se "NQ")
for fn, orig in (("MM_rete_distribuzione_2025.csv", "rete"), ("MM_rubinetto_controllo_qualita_2025.csv", "cq")):
    for r in csv.DictReader(open(os.path.join(pf_dir, fn), encoding="utf-8"), delimiter=";"):
        v = r["somma_pfas_ug_l"].strip()
        pf.append((orig, r["data_prelievo"], r["punto_prelievo"], None if v == "NQ" else float(v.replace(",", "."))))
pf_val = sorted(x[3] for x in pf if x[3] is not None)
pf_nq = sum(1 for x in pf if x[3] is None)
pf_tutti = [0.0] * pf_nq + pf_val          # NQ = sotto il limite di quantificazione, messi in fondo alla scala solo per la mediana
pf_med = statistics.median(pf_tutti)
pf_date = sorted(x[1][6:] + x[1][3:5] + x[1][:2] for x in pf)   # aaaammgg
def pf_d(s):   # aaaammgg -> "8 gennaio 2025"
    mesi_ = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    return "%d %s %s" % (int(s[6:]), mesi_[int(s[4:6]) - 1], s[:4])
pf_fasce = [sum(1 for v in pf_val if int(round(v * 1000)) // 10 == i) for i in range(10)]   # 0,00x ... 0,09x
pf_sopra = sum(1 for v in pf_val if v > 0.10)
assert sum(pf_fasce) + pf_sopra == len(pf_val)
pf_sotto005 = pf_nq + sum(1 for v in pf_val if v < 0.05)
pfas = dict(n=len(pf), n_rete=sum(1 for x in pf if x[0] == "rete"), n_cq=sum(1 for x in pf if x[0] == "cq"),
            punti_rete=len(set(x[2] for x in pf if x[0] == "rete")), punti_cq=len(set(x[2] for x in pf if x[0] == "cq")),
            nq=pf_nq, max=max(pf_val), min=min(pf_val), mediana=pf_med, limite=0.10, sopra_limite=pf_sopra,
            sotto_005=pf_sotto005, dal=pf_d(pf_date[0]), al=pf_d(pf_date[-1]), n_2026=sum(1 for x in pf if x[1].endswith("/2026")),
            fasce=pf_fasce, fonte="MM SpA, tabelle PDF 'Dati 2025 PFAS' (riepilogo calcolato qui)")
json.dump(pfas, open(os.path.join(dat, "pfas.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
def f3(x): return ("%.3f" % x).replace(".", ",")
def pct(a, b): return ("%.1f" % (100.0 * a / b)).replace(".", ",")

# ------------------------------------------------------------------ acqua.json
meta = dict(ultimo=ultimo, fin=[fin[0], fin[-1]], fin_mesi=fin, mancanti=mancanti, sospetto=["2024-12"],
            n_civici=n_civici, n_stimati=n_stimati, n_strade=len(strade), n_voci=n_voci,
            scaricato="2026-10-30")
acqua = dict(meta=meta, cal=cal, mese_file={p: mese_file[p] for p in mesi}, zone=zone, par=par, serie=serie, sched=sched,
             stag=stag, anni_file=anni_file, perdite=perdite)
json.dump(acqua, open(os.path.join(dat, "acqua.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ csv scaricabili
cols = ["periodo", "zona_codice", "zona_nome", "parametro", "valore", "unita", "sotto_soglia", "soglia", "qualita_dato",
        "valore_testo", "nota_valore", "limite_testo", "limite_tipo", "file_origine", "riga_origine"]
M[cols].to_csv(os.path.join(dat, "analisi_mensile_zone.csv"), sep=";", index=False, encoding="utf-8")
shutil.copy(os.path.join(pul, "perdite.csv"), os.path.join(dat, "perdite_2018.csv"))

# ------------------------------------------------------------------ pagina
tpl = open(os.path.join(here, "pagina_template.html"), encoding="utf-8").read()
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
def mname(p): return MESI[int(p[5:7]) - 1] + " " + p[:4]
def it(n): return "{:,}".format(n).replace(",", ".")
sost = {"N_CIVICI": it(n_civici), "N_STIMATI": it(n_stimati), "N_STRADE": it(len(strade)),
        "ULTIMO_MESE": mname(ultimo), "SCARICATO": "30 ottobre 2026", "FIN_DA": mname(fin[0]), "FIN_A": mname(fin[-1]),
        "PF_N": it(pfas["n"]), "PF_N_RETE": it(pfas["n_rete"]), "PF_N_CQ": it(pfas["n_cq"]), "PF_PT_RETE": pfas["punti_rete"], "PF_PT_CQ": pfas["punti_cq"],
        "PF_NQ": pfas["nq"], "PF_NQ_PCT": pct(pfas["nq"], pfas["n"]), "PF_MAX": f3(pfas["max"]), "PF_MIN": f3(pfas["min"]), "PF_MED": f3(pfas["mediana"]),
        "PF_SOTTO005": it(pfas["sotto_005"]), "PF_SOTTO005_PCT": pct(pfas["sotto_005"], pfas["n"]), "PF_DAL": pfas["dal"], "PF_AL": pfas["al"],
        "PF_N2026": pfas["n_2026"], "PF_SOPRA": pfas["sopra_limite"]}
for k, v in sost.items(): tpl = tpl.replace("{{" + k + "}}", str(v))
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl)

# ------------------------------------------------------------------ riepilogo a schermo
for fn in sorted(os.listdir(dat)):
    print("%-30s %9d byte" % (fn, os.path.getsize(os.path.join(dat, fn))))
print("strade", len(strade), "voci", n_voci, "conflitti", n_conflitti, "stimati", n_stimati)
print("stag", {k: v["r"] for k, v in stag.items()})
print("mancanti", mancanti, "finestra", fin[0], fin[-1])
