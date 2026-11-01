"""Fase 1 - riepiloghi: Milano contro le grandi citta' e contro l'Italia, fotografie di fine anno 2007-2025.
Uso: python -I -X utf8 analisi.py <amministratori_dir>
Legge pulito/comuni_ruoli.csv.gz, milano_amministratori.csv, milano_in_carica.csv, grandi_citta_in_carica.csv, sindaci_milano.csv
Scrive in pulito/: serie_temporali.csv, titoli_professioni.csv, milano_mandati.csv, ricambio.csv, milano_liste.csv,
                   milano_attuale_riepilogo.json, riepilogo.json, analisi_log.txt
"""
import sys, os, json
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comune_lib as L

A = sys.argv[1]; PU = os.path.join(A, "pulito")
GRANDI = {"058091": "Roma", "015146": "Milano", "063049": "Napoli", "001272": "Torino", "082053": "Palermo",
          "010025": "Genova", "037006": "Bologna", "048017": "Firenze", "072006": "Bari", "087015": "Catania"}
t = pd.read_csv(os.path.join(PU, "comuni_ruoli.csv.gz"), dtype={"istat": str}, parse_dates=["inizio", "fine"], low_memory=False)
t["istat"] = t.istat.str.zfill(6)
t["donna"] = np.where(t.sesso == "F", 1.0, np.where(t.sesso == "M", 0.0, np.nan))
LOG = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)

# ---------- quante persone per citta'/anno/corpo: citta'-anno incomplete (es. Roma 2015, 2021) si scartano
cnt = t[t.istat.isin(GRANDI)].groupby(["istat", "anno", "ruolo"]).size().unstack(fill_value=0)
incomplete = cnt[(cnt.get("consiglio", 0) < 20)].index.tolist()
log("citta'-anno incomplete (consiglio < 20 persone):", [(GRANDI[i], a) for i, a in incomplete])
t["completo"] = True
for i, a in incomplete: t.loc[(t.istat == i) & (t.anno == a), "completo"] = False
# anche per tutti i comuni: un comune-anno con 0 consiglieri ma amministratori (es. in attesa di caricamento) non entra nei confronti del consiglio
nc = t[t.ruolo == "consiglio"].groupby(["istat", "anno"]).size()
t = t.join(nc.rename("n_cons_com"), on=["istat", "anno"])
t["n_cons_com"] = t.n_cons_com.fillna(0)

# ---------- gruppi
def gruppi(df):
    """Genera (nome_gruppo, sottoinsieme)."""
    d = df[df.completo]
    for i, n in GRANDI.items():
        yield n, d[d.istat == i]
    yield "Grandi città (10)", d[d.istat.isin(GRANDI)]
    big = d[(d["pop"] >= 100000)]
    yield "Comuni sopra 100.000 abitanti", big
    yield "Tutta Italia (tutti i comuni)", d
    yield "Comuni sotto 5.000 abitanti", d[(d["pop"] < 5000)]

def riga(g, corpo, anno, s):
    r = {"gruppo": g, "corpo": corpo, "anno": anno, "n": len(s)}
    if len(s) == 0: return r
    r["n_donne"] = int(s.donna.sum()); n_sex = s.donna.notna().sum()
    r["donne_pct"] = round(100 * s.donna.sum() / n_sex, 1) if n_sex else np.nan
    r["eta_media"] = round(s.eta.mean(), 1); r["eta_mediana"] = round(s.eta.median(), 1)
    r["under40_pct"] = round(100 * (s.eta < 40).sum() / s.eta.notna().sum(), 1) if s.eta.notna().sum() else np.nan
    r["over60_pct"] = round(100 * (s.eta >= 60).sum() / s.eta.notna().sum(), 1) if s.eta.notna().sum() else np.nan
    tit = s.titolo.dropna()
    r["titolo_dichiarato_pct"] = round(100 * len(tit) / len(s), 1)
    r["laurea_pct_dei_dichiarati"] = round(100 * (tit == "Laurea o più").sum() / len(tit), 1) if len(tit) else np.nan
    pr = s.prof_cat.dropna()
    r["prof_dichiarata_pct"] = round(100 * len(pr) / len(s), 1)
    if corpo == "giunta": r["esterni_pct"] = round(100 * s.esterno.mean(), 1)
    return r

rows = []
for anno, d in t.groupby("anno"):
    for g, s in gruppi(d):
        for corpo, rr in (("consiglio", "consiglio"), ("giunta", "giunta"), ("sindaco", "sindaco")):
            x = s[s.ruolo == rr]
            if len(x) == 0: continue
            rows.append(riga(g, corpo, anno, x))
ser = pd.DataFrame(rows)
# n minimo per mostrare un dato: un solo sindaco o poche persone => i percentuali non hanno senso per citta' singole nel sindaco
ser.to_csv(os.path.join(PU, "serie_temporali.csv"), index=False)
log("serie_temporali righe", len(ser))

# ---------- titoli di studio e professioni (distribuzioni) per gruppo-corpo-periodo
def periodo(a):
    return "2007-2012" if a <= 2012 else ("2013-2018" if a <= 2018 else "2019-2025")
t["periodo"] = t.anno.map(periodo)
dist = []
for p, d in t.groupby("periodo"):
    for g, s in gruppi(d):
        for corpo in ("consiglio", "giunta"):
            x = s[s.ruolo == corpo]
            # una persona conta una volta per periodo e corpo (tenuta l'ultima fotografia): evita di contare 6 volte chi resta in carica
            x = x.sort_values("anno").drop_duplicates(["istat", "persona"], keep="last")
            for col, nome in (("titolo", "titolo di studio"), ("prof_cat", "professione")):
                v = x[col].dropna()
                for k, n in v.value_counts().items():
                    dist.append({"periodo": p, "gruppo": g, "corpo": corpo, "tipo": nome, "categoria": k, "n": int(n),
                                 "pct_dei_dichiarati": round(100 * n / len(v), 1), "dichiarati": len(v), "persone": len(x)})
dist = pd.DataFrame(dist); dist.to_csv(os.path.join(PU, "titoli_professioni.csv"), index=False)

# ---------- Milano: per mandato
mi = pd.read_csv(os.path.join(PU, "milano_amministratori.csv"), parse_dates=["inizio", "fine"])
mi["donna"] = np.where(mi.sesso == "F", 1.0, np.where(mi.sesso == "M", 0.0, np.nan))
mi["mandato"] = mi.elezione.str[-4:].astype(int)  # anno di elezione
MAND = sorted(mi.mandato.unique())
log("mandati in Milano:", MAND)
# prima fotografia del mandato
prima = mi.groupby("mandato").anno.min()
rost = {m: mi[mi.mandato == m] for m in MAND}
ric_rows = []; mand_rows = []
for m in MAND:
    r = rost[m]
    for corpo in ("consiglio", "giunta", "sindaco"):
        x = r[r.ruolo == corpo]
        pers = x.drop_duplicates("persona")
        mand_rows.append({"mandato": m, "corpo": corpo, "persone_nel_mandato": len(pers), "prima_fotografia": int(prima[m]),
                          "donne_pct_persone": round(100 * pers.donna.mean(), 1), "eta_media_persone": round(pers.eta.mean(), 1)})
    # ricambio: chi e' nella prima fotografia del mandato m e gia' c'era (in qualunque ruolo) nel mandato precedente
    i = MAND.index(m)
    if i > 0:
        prev = set(rost[MAND[i - 1]].persona)
        first = r[(r.anno == prima[m]) & r.ruolo.isin(["consiglio", "giunta", "sindaco"])]
        for corpo in ("consiglio", "giunta"):
            x = first[first.ruolo == corpo].drop_duplicates("persona")
            ric_rows.append({"gruppo": "Milano", "mandato": m, "precedente": MAND[i - 1], "corpo": corpo, "persone": len(x),
                             "riconfermati": int(x.persona.isin(prev).sum()), "riconfermati_pct": round(100 * x.persona.isin(prev).mean(), 1),
                             "precedente_completo": bool(i - 1 > 0)})
mand = pd.DataFrame(mand_rows); mand.to_csv(os.path.join(PU, "milano_mandati.csv"), index=False)

# ---------- ricambio per grandi citta' e Italia (stessa definizione), con le persone di tutte le fotografie
def ricambio(df, nome):
    out = []
    for ist, c in df.groupby("istat"):
        el = c.groupby("elezione").agg(a=("anno", "min")).sort_values("a")
        el["y"] = pd.to_datetime(el.index, format="%d/%m/%Y", errors="coerce").year
        el = el.dropna().sort_values("y")
        ys = list(el.y.astype(int)); keys = list(el.index)
        for j in range(2, len(keys)) if False else range(1, len(keys)):
            # il mandato precedente deve essere osservato dall'inizio: il primo mandato del comune e' parziale e non fa da riferimento "completo"
            prev = set(c[c.elezione == keys[j - 1]].persona)
            a0 = el.a.iloc[j]
            cur = c[(c.elezione == keys[j]) & (c.anno == a0) & (c.ruolo == "consiglio")].drop_duplicates("persona")
            if len(cur) < 5: continue
            out.append({"gruppo": nome, "istat": ist, "anno_elezione": ys[j], "persone": len(cur),
                        "riconfermati": int(cur.persona.isin(prev).sum()), "precedente_completo": j >= 2})
    return pd.DataFrame(out)
rc = []
for i, n in GRANDI.items():
    rc.append(ricambio(t[(t.istat == i) & t.completo], n))
big = ricambio(t[(t["pop"] >= 100000) & t.completo], "Comuni sopra 100.000 abitanti")
alli = ricambio(t[t.completo], "Tutta Italia (tutti i comuni)")
rc_all = pd.concat(rc + [big, alli])
rc_ok = rc_all[rc_all.precedente_completo]
def aggr(df):
    return df.groupby(["gruppo", "anno_elezione"]).agg(persone=("persone", "sum"), riconfermati=("riconfermati", "sum"), comuni=("istat", "nunique")).reset_index()
rca = aggr(rc_ok); rca["riconfermati_pct"] = (100 * rca.riconfermati / rca.persone).round(1)
rca.to_csv(os.path.join(PU, "ricambio.csv"), index=False)
pd.DataFrame(ric_rows).to_csv(os.path.join(PU, "milano_ricambio_dettaglio.csv"), index=False)

# ---------- Milano: liste del consiglio (prima fotografia di ogni mandato) e oggi
ic = pd.read_csv(os.path.join(PU, "milano_in_carica.csv"), parse_dates=["inizio"])
def lista_corta(s):
    if not isinstance(s, str) or not s.strip(): return "(non indicata)"
    return s.strip().title().replace("'", "'")
liste = []
for m in MAND:
    r = rost[m]; x = r[(r.anno == prima[m]) & (r.ruolo == "consiglio")]
    for k, n in x.lista.map(lista_corta).value_counts().items(): liste.append({"quando": f"inizio mandato {m} (fotografia {prima[m]})", "lista": k, "consiglieri": int(n)})
x = ic[ic.ruolo == "consiglio"]
for k, n in x.lista.map(lista_corta).value_counts().items(): liste.append({"quando": "24/8/2026", "lista": k, "consiglieri": int(n)})
pd.DataFrame(liste).to_csv(os.path.join(PU, "milano_liste.csv"), index=False)

# ---------- riepilogo numeri chiave
R = {}
def get(g, c, a, col):
    x = ser[(ser.gruppo == g) & (ser.corpo == c) & (ser.anno == a)]
    return None if x.empty else (None if pd.isna(x.iloc[0].get(col)) else float(x.iloc[0][col]))
for c in ("consiglio", "giunta"):
    for col in ("donne_pct", "eta_media", "laurea_pct_dei_dichiarati", "titolo_dichiarato_pct", "prof_dichiarata_pct"):
        R[f"{c}_{col}"] = {g: {a: get(g, c, a, col) for a in (2007, 2012, 2016, 2019, 2022, 2025)}
                           for g in ("Milano", "Roma", "Torino", "Napoli", "Grandi città (10)", "Comuni sopra 100.000 abitanti", "Tutta Italia (tutti i comuni)")}
R["sindaci_donne_pct_italia"] = {a: get("Tutta Italia (tutti i comuni)", "sindaco", a, "donne_pct") for a in range(2007, 2026)}
R["milano_mandati"] = mand.to_dict("records")
R["ricambio_milano"] = pd.DataFrame(ric_rows).to_dict("records")
R["ricambio_aggregati"] = rca.to_dict("records")
R["citta_anno_incomplete"] = [(GRANDI[i], int(a)) for i, a in incomplete]
# Milano oggi
cons = ic[ic.ruolo == "consiglio"]; gi = ic[ic.ruolo == "giunta"]; sin = ic[ic.ruolo == "sindaco"]
def sintesi(x):
    return {"n": len(x), "donne": int((x.sesso == "F").sum()), "donne_pct": round(100 * (x.sesso == "F").mean(), 1),
            "eta_media": round(x.eta.mean(), 1), "eta_mediana": round(x.eta.median(), 1),
            "titolo_dichiarato": int(x.titolo.notna().sum()), "laurea_su_dichiarati": int((x.titolo == "Laurea o più").sum()),
            "prof_dichiarata": int(x.prof_cat.notna().sum())}
R["milano_oggi"] = {"consiglio": sintesi(cons), "giunta": sintesi(gi), "sindaco": sintesi(sin), "data": "2026-08-24",
                    "inizio_mandato_min": str(ic.inizio.min().date())}
# professioni Milano: tutte le persone di tutti i mandati osservati (una volta per mandato e corpo)
pm = mi[mi.ruolo.isin(["consiglio", "giunta"])].sort_values("anno").drop_duplicates(["mandato", "ruolo", "persona"], keep="last")
R["milano_prof_totale"] = {c: pm[pm.ruolo == c].prof_cat.dropna().value_counts().to_dict() for c in ("consiglio", "giunta")}
R["milano_prof_dichiarata_pct_per_mandato"] = {int(m): round(100 * x.prof_cat.notna().mean(), 1) for m, x in pm[pm.ruolo == "consiglio"].groupby("mandato")}
R["milano_titolo_dichiarato_pct_per_mandato"] = {int(m): round(100 * x.titolo.notna().mean(), 1) for m, x in pm[pm.ruolo == "consiglio"].groupby("mandato")}
json.dump(R, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
open(os.path.join(PU, "analisi_log.txt"), "w", encoding="utf8").write("\n".join(LOG))
log("fatto")
