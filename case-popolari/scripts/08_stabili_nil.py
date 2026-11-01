"""Assegna ai NIL i fabbricati ALER di Milano (elenco 2013/2015/2016, pulito/aler_stabili_canone_<anno>.csv) agganciando indirizzo+civico ai civici del Comune
(citta-15-minuti/out/civici_tempi.csv: civici con coordinate e NIL gia' calcolato col punto-in-poligono sui NIL vigenti).
Scrive pulito/aler_stabili_nil_<anno>.csv e pulito/aler_stabili_per_nil.csv.
Uso: python -I -X utf8 08_stabili_nil.py <case-popolari> <milano-in-dati>   (percorsi assoluti)
Metodo: nome via normalizzato (tolti tipo via, articoli, punteggiatura; parole ordinate) + civico normalizzato.
 'esatto' = stesso nome e stesso civico; 'via_civico_vicino' = stesso nome, civico numerico piu' vicino (stessa via); 'nome_approssimato' = nome con parole in comune >= 60%.
Nessun inquilino, nessun singolo alloggio: solo edifici."""
import sys, os, re, csv, unicodedata
import pandas as pd

base, root = sys.argv[1], sys.argv[2]
civ = pd.read_csv(os.path.join(root, "citta-15-minuti", "out", "civici_tempi.csv"),
                  usecols=["IDMASTER", "CODICE_VIA", "NUMEROCOMPLETO", "DENOMINAZIONE", "ID_NIL", "NIL", "lon", "lat"])
STOP = {"VIA", "VIALE", "PIAZZA", "PIAZZALE", "CORSO", "LARGO", "VICOLO", "STRADA", "DI", "DEL", "DELLA", "DELLE", "DEI", "DEGLI", "DELL", "DELLO", "DA", "D", "LA", "LE", "IL", "LO", "I", "GLI",
        "SAN", "S", "SANTA", "SANT", "SANTI", "ALZAIA", "BASTIONI", "CAVALCAVIA", "GALLERIA", "RIPA", "PIAZZETTA", "VICOLETTO", "CIRCONVALLAZIONE", "VIALETTO", "PASSAGGIO", "SALITA", "VIA-", "PARCO"}


def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def key(name):
    s = strip_acc(str(name).upper())
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [t for t in s.split() if t not in STOP]
    return " ".join(sorted(toks))


def civ_norm(c):
    return re.sub(r"[^A-Z0-9]", "", strip_acc(str(c).upper()))


civ["k"] = civ.DENOMINAZIONE.map(key)
civ["c"] = civ.NUMEROCOMPLETO.map(civ_norm)
civ["cn"] = civ.c.str.extract(r"^(\d+)")[0].astype(float)
exact = civ.drop_duplicates(["k", "c"]).set_index(["k", "c"])
by_k = {k: g for k, g in civ.groupby("k")}
keys = list(by_k.keys())


def split_addr(a):
    m = re.match(r"^(.*?)[\s,]+(\d+[A-Z0-9/\.\-]*(?:\s*[A-Z])?)\s*$", a.strip())
    if not m:
        return a, ""
    return m.group(1), m.group(2)


for anno in (2013, 2015, 2016):
    d = pd.read_csv(os.path.join(base, "pulito", f"aler_stabili_canone_{anno}.csv"))
    d = d[d.localita.fillna("").str.startswith("MILANO") & d.indirizzo.notna()].copy()
    res = []
    for _, r in d.iterrows():
        nome, num = split_addr(r.indirizzo)
        k, c = key(nome), civ_norm(num)
        out = dict(NIL=None, ID_NIL=None, lon=None, lat=None, metodo="non_trovato")
        if (k, c) in exact.index:
            e = exact.loc[(k, c)]
            out = dict(NIL=e.NIL, ID_NIL=e.ID_NIL, lon=e.lon, lat=e.lat, metodo="esatto")
        elif k in by_k and c:
            g = by_k[k]
            m = re.match(r"^(\d+)", c)
            if m:
                g = g.assign(dist=(g.cn - float(m.group(1))).abs()).sort_values("dist")
                e = g.iloc[0]
                if e.dist <= 20:
                    out = dict(NIL=e.NIL, ID_NIL=e.ID_NIL, lon=e.lon, lat=e.lat, metodo="via_civico_vicino")
        if out["metodo"] == "non_trovato" and k:
            tk = set(k.split())
            best, bs = None, 0
            for kk in keys:
                inter = len(tk & set(kk.split()))
                sc = inter / max(len(tk), len(kk.split()))
                if sc > bs:
                    best, bs = kk, sc
            if best and bs >= 0.6 and c:
                g = by_k[best]
                m = re.match(r"^(\d+)", c)
                if m:
                    g = g.assign(dist=(g.cn - float(m.group(1))).abs()).sort_values("dist")
                    e = g.iloc[0]
                    if e.dist <= 20:
                        out = dict(NIL=e.NIL, ID_NIL=e.ID_NIL, lon=e.lon, lat=e.lat, metodo="nome_approssimato")
        res.append(dict(anno=anno, indirizzo_aler=r.indirizzo, canone_fatturato=r.canone_fatturato, **out))
    R = pd.DataFrame(res)
    R.to_csv(os.path.join(base, "pulito", f"aler_stabili_nil_{anno}.csv"), index=False, encoding="utf-8")
    print(anno, "fabbricati Milano", len(R), R.metodo.value_counts().to_dict(), "quota canone agganciata %.1f%%" % (100 * R[R.metodo != "non_trovato"].canone_fatturato.clip(lower=0).sum() / R.canone_fatturato.clip(lower=0).sum()))

# tabella per NIL
parts = []
for anno in (2013, 2015, 2016):
    R = pd.read_csv(os.path.join(base, "pulito", f"aler_stabili_nil_{anno}.csv"))
    R = R[R.metodo != "non_trovato"]
    g = R.groupby(["ID_NIL", "NIL"]).agg(fabbricati=("indirizzo_aler", "count"), canone_fatturato=("canone_fatturato", "sum")).reset_index()
    g["anno"] = anno
    parts.append(g)
T = pd.concat(parts)
W = T.pivot_table(index=["ID_NIL", "NIL"], columns="anno", values=["fabbricati", "canone_fatturato"], aggfunc="sum").fillna(0)
W.columns = [f"{a}_{b}" for a, b in W.columns]
W = W.reset_index()
tot = W["canone_fatturato_2016"].sum()
W["quota_canone_2016_%"] = (100 * W["canone_fatturato_2016"] / tot).round(2)
W = W.sort_values("canone_fatturato_2016", ascending=False)
W.to_csv(os.path.join(base, "pulito", "aler_stabili_per_nil.csv"), index=False, encoding="utf-8")
print(W.head(12).to_string())
print(len(W), "NIL con almeno un fabbricato ALER (2016)")
