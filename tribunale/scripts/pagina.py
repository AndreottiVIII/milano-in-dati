"""Scrive i file dati della pagina "Il tribunale di Milano" (docs/tribunale/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <tribunale_dir> <docs_dir>

Legge tribunale/pulito/*.csv (fatti da build.py) e scrive in <docs_dir>/tribunale/data/:
  serie.json                       serie storiche per indicatore: Milano, Italia, banda tra 25o e 75o percentile degli uffici, ogni ufficio
  riepilogo.json                   i numeri citati nel testo (valore, testo formattato, fonte), la tabella PNRR e la tabella dei grandi tribunali
  grandi_tribunali.csv             i 12 tribunali con piu' cause civili aperte
  tribunali_2025.csv               tutti i 140 tribunali, civile e penale, 2019 e 2025
  corti_appello_2025.csv           tutte le corti di appello
  serie_milano_italia.csv          le serie di Milano e dell'Italia in formato "lungo"
  pnrr_obiettivi.csv               gli obiettivi PNRR e dove sono Italia, Tribunale e Corte d'appello di Milano
  pendenti_milano_protezione_internazionale.csv
  verifiche.csv                    i controlli incrociati di build.py
Sono solo tabelle ricalcolate da noi (aggregati per ufficio): i file originali del Ministero non vengono ripubblicati.
"""
import sys, os, json, math, shutil
import numpy as np, pandas as pd

T, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(T, "pulito")
OUT = os.path.join(DOCS, "tribunale", "data")
os.makedirs(OUT, exist_ok=True)

uff = pd.read_csv(os.path.join(PU, "uffici_dt.csv"))
fl = pd.read_csv(os.path.join(PU, "flussi_civili.csv"))
fp = pd.read_csv(os.path.join(PU, "flussi_penali.csv"))
du = pd.read_csv(os.path.join(PU, "durata_effettiva.csv"))
ver = pd.read_csv(os.path.join(PU, "verifiche.csv"))
assert (ver.esito == "ok").all(), "ci sono controlli di build.py non riusciti"


def chiave(s):
    return " ".join(str(s).strip().lower().replace("/bozen", "").split())


for d in (uff, fl, fp, du):
    d["chiave"] = d["sede"].map(chiave)

# nomi da mostrare: quelli del file PNRR (stesso nome per civile e penale)
NOME = {}
for tipo in ("tribunale", "corte_appello"):
    for s in uff[(uff.tipo == tipo)].sede.unique():
        NOME[(tipo, chiave(s))] = s
assert sum(1 for k in NOME if k[0] == "tribunale") == 140 and sum(1 for k in NOME if k[0] == "corte_appello") == 29

MI = "milano"
# ------------------------------------------------------------------ utilita'
def cl(v, d=None):
    if v is None:
        return None
    try:
        if isinstance(v, (float, np.floating)) and (math.isnan(v) or math.isinf(v)):
            return None
    except TypeError:
        return None
    if d is None:
        return int(v) if float(v).is_integer() else float(v)
    return round(float(v), d)


def it_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


def it_dec(x, d=1):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def it_pct(x, d=1, segno=False):
    s = it_dec(100 * x, d)
    if segno and x > 0:
        s = "+" + s
    return s.replace("-", "−")


def it_var(x, d=0):
    """variazione relativa con segno (x = 0.042 -> '+4%')"""
    s = it_dec(100 * x, d)
    if x > 0 and not s.startswith("+"):
        s = "+" + s
    return s.replace("-", "−")


X_P = ["2019", "2020", "2021", "2022", "2023", "2024", "2025", "2026*"]
PER_P = [(2019, "Intero anno"), (2020, "Intero anno"), (2021, "Intero anno"), (2022, "Intero anno"), (2023, "Intero anno"), (2024, "Intero anno"),
         (2025, "Intero anno"), (2026, "Primo semestre")]
X_F = [str(a) for a in range(2014, 2026)]
ANNI_F = list(range(2014, 2026))
NUM = {}


def num(chiave_, valore, testo, fonte):
    NUM[chiave_] = {"v": cl(valore, 6), "t": testo, "f": fonte}


# ------------------------------------------------------------------ serie per ufficio
SERIE = {}  # chiave indicatore -> dict


def pct_band(vals_by_office, n):
    out = {"p25": [], "p50": [], "p75": []}
    for i in range(n):
        v = np.array([s[i] for s in vals_by_office.values() if s[i] is not None], dtype=float)
        if len(v) >= 10:
            out["p25"].append(cl(np.percentile(v, 25), 3)); out["p50"].append(cl(np.percentile(v, 50), 3)); out["p75"].append(cl(np.percentile(v, 75), 3))
        else:
            for k in out:
                out[k].append(None)
    return out


def costruisci(key, meta, x, per_ufficio, italia, dec, banda=True, tipo="tribunale"):
    """per_ufficio: {chiave_ufficio: lista di valori}, italia: lista"""
    uffici = {}
    for k, vals in per_ufficio.items():
        uffici[NOME[(tipo, k)]] = [cl(v, dec) for v in vals]
    mil = uffici[NOME[(tipo, MI)]]
    d = dict(meta)
    d.update({"x": x, "milano": mil, "italia": [cl(v, dec) for v in italia], "uffici": uffici})
    if banda:
        d.update(pct_band(uffici, len(x)))
    SERIE[key] = d
    return d


def serie_pnrr(settore, tipo, colonna, tipo_calc):
    """valori per ufficio (e Italia) dal file PNRR, sui periodi X_P. tipo_calc: 'dt' (giorni*pend/def), 'somma' (somma di una colonna)"""
    q = uff[(uff.settore == settore) & (uff.tipo == tipo)]
    per = {}
    ita = []
    for (a, p) in PER_P:
        qq = q[(q.anno == a) & (q.periodo == p)]
        for _, r in qq.iterrows():
            per.setdefault(r.chiave, {})[(a, p)] = r
        if tipo_calc == "dt":
            ita.append(qq.giorni_periodo.iloc[0] * qq.pendenti.sum() / qq.definiti.sum())
        else:
            ita.append(qq[colonna].sum())
    res = {}
    for k, dd in per.items():
        if tipo_calc == "dt":
            res[k] = [dd[(a, p)].dt_giorni if (a, p) in dd else None for (a, p) in PER_P]
        else:
            res[k] = [dd[(a, p)][colonna] if (a, p) in dd else None for (a, p) in PER_P]
    return res, ita


def pivot_flussi(df, valore, tipo, anni):
    q = df[df.tipo == tipo]
    p = q.pivot_table(index="chiave", columns="anno", values=valore, aggfunc="sum", dropna=False)
    return {k: [p.loc[k, a] if a in p.columns and not pd.isna(p.loc[k, a]) else None for a in anni] for k in p.index}


# ---- CIVILE: tempo di smaltimento, pendenti, cause vecchie
M_DT = {"unit": "giorni", "dir": "meno", "dec": 0}
for tipo, tnome in (("tribunale", "Tribunale"), ("corte_appello", "Corte d'appello")):
    soglia = "3" if tipo == "tribunale" else "2"
    per, ita = serie_pnrr("civile", tipo, None, "dt")
    costruisci(f"civile_{tipo}_dt", {**M_DT, "label": "Tempo di smaltimento (giorni)", "dir": "meno",
               "desc": "Quanti giorni servirebbero per chiudere tutte le cause civili aperte, al ritmo dell'anno (cause aperte a fine anno diviso cause chiuse nell'anno, per 365). Solo le cause contenziose scelte dall'Unione europea. Meno è meglio.",
               "fonte": "Monitoraggio_PNRR.xlsx, fogli Civile e Indicatori (ricalcolato e verificato)", "ult": 6, "zero": True, "stima": True}, X_P, per, ita, 1, tipo=tipo)
    per, ita = serie_pnrr("civile", tipo, "pendenti", "somma")
    costruisci(f"civile_{tipo}_pend", {"unit": "cause", "dir": None, "label": "Cause civili aperte a fine anno",
               "desc": "Cause civili contenziose ancora aperte a fine anno (stesso elenco del tempo di smaltimento).",
               "fonte": "Monitoraggio_PNRR.xlsx, foglio Civile", "ult": 6, "zero": True}, X_P, per, ita, 0, banda=False, tipo=tipo)
    per, ita = serie_pnrr("civile", tipo, "arretrato_oltre_soglia", "somma")
    costruisci(f"civile_{tipo}_vecchie_n", {"unit": "cause", "dir": "meno", "label": f"Cause vecchie: aperte da più di {soglia} anni (numero)",
               "desc": f"Cause civili ancora aperte a fine periodo e iscritte da più di {soglia} anni (arretrato 'legge Pinto'). Meno è meglio.",
               "fonte": "Monitoraggio_PNRR.xlsx, foglio Civile, colonna Arretrato", "ult": 6, "zero": True}, X_P, per, ita, 0, banda=False, tipo=tipo)

# quota di cause vecchie sul totale delle aperte (stesso registro SICID)
for tipo in ("tribunale", "corte_appello"):
    soglia = "3" if tipo == "tribunale" else "2"
    q = uff[(uff.settore == "civile") & (uff.tipo == tipo) & (uff.periodo == "Intero anno") & (uff.anno <= 2025)][["chiave", "anno", "arretrato_oltre_soglia"]]
    f_ = fl[fl.tipo == tipo][["chiave", "anno", "pendenti"]].rename(columns={"pendenti": "pend_sicid"})
    m = q.merge(f_, on=["chiave", "anno"], how="left")
    m["q"] = m.arretrato_oltre_soglia / m.pend_sicid
    p = m.pivot_table(index="chiave", columns="anno", values="q")
    per = {k: [cl(p.loc[k, a]) if a in p.columns else None for a in range(2019, 2026)] + [None] for k in p.index}
    s = m.groupby("anno")[["arretrato_oltre_soglia", "pend_sicid"]].sum()
    ita = [s.loc[a, "arretrato_oltre_soglia"] / s.loc[a, "pend_sicid"] for a in range(2019, 2026)] + [None]
    costruisci(f"civile_{tipo}_vecchie_q", {"unit": "%", "dir": "meno", "mult": 100, "label": f"Cause vecchie: quota sulle cause aperte (oltre {soglia} anni)",
               "desc": f"Su 100 cause civili aperte a fine anno, quante sono aperte da più di {soglia} anni. Le cause vecchie sono contate dal Ministero sul registro SICID, senza giudice tutelare e simili: per questo il totale a cui sono riferite è più grande di quello del tempo di smaltimento. Meno è meglio.",
               "fonte": "Monitoraggio_PNRR.xlsx (arretrato) e CivileFlussi20142025.xlsx (cause aperte SICID)", "ult": 6, "zero": True}, X_P, per, ita, 4, tipo=tipo)

# tempo di smaltimento senza protezione internazionale (nostro calcolo)
q = uff[(uff.settore == "civile") & (uff.tipo == "tribunale") & (uff.periodo == "Intero anno") & (uff.anno <= 2025)][["chiave", "anno", "definiti", "pendenti", "giorni_periodo"]]
pi = fl[fl.tipo == "tribunale"][["chiave", "anno", "pi_definiti", "pi_pendenti"]]
m = q.merge(pi, on=["chiave", "anno"], how="left")
m[["pi_definiti", "pi_pendenti"]] = m[["pi_definiti", "pi_pendenti"]].fillna(0)  # nessuna riga di protezione internazionale = nessuna causa
m["dts"] = m.giorni_periodo * (m.pendenti - m.pi_pendenti) / (m.definiti - m.pi_definiti)
p = m.pivot_table(index="chiave", columns="anno", values="dts")
per = {k: [cl(p.loc[k, a]) for a in range(2019, 2026)] + [None] for k in p.index}
s = m.groupby("anno")[["definiti", "pendenti", "pi_definiti", "pi_pendenti", "giorni_periodo"]].agg(
    {"definiti": "sum", "pendenti": "sum", "pi_definiti": "sum", "pi_pendenti": "sum", "giorni_periodo": "max"})
ita = [s.loc[a, "giorni_periodo"] * (s.loc[a, "pendenti"] - s.loc[a, "pi_pendenti"]) / (s.loc[a, "definiti"] - s.loc[a, "pi_definiti"]) for a in range(2019, 2026)] + [None]
costruisci("civile_tribunale_dt_spi", {"unit": "giorni", "dir": "meno", "label": "Tempo di smaltimento senza le cause di protezione internazionale (giorni)",
           "desc": "Come il tempo di smaltimento, ma togliendo le cause di protezione internazionale (asilo e simili), concentrate in pochi tribunali. Calcolo nostro, non del Ministero. Meno è meglio.",
           "fonte": "Monitoraggio_PNRR.xlsx e CivileFlussi20142025.xlsx (voce Protezione internazionale), calcolo nostro", "ult": 6, "zero": True, "stima": True}, X_P, per, ita, 1)
PIM = m[m.chiave == MI].set_index("anno")

# indice di ricambio (flussi) civile e penale
for settore, df in (("civile", fl), ("penale", fp)):
    for tipo in ("tribunale", "corte_appello"):
        di = pivot_flussi(df, "definiti", tipo, ANNI_F)
        isc = pivot_flussi(df, "iscritti", tipo, ANNI_F)
        per = {k: [(100 * di[k][i] / isc[k][i]) if (di[k][i] is not None and isc[k][i]) else None for i in range(len(ANNI_F))] for k in di}
        sd = np.array([sum(v[i] or 0 for v in di.values()) for i in range(len(ANNI_F))], dtype=float)
        si = np.array([sum(v[i] or 0 for v in isc.values()) for i in range(len(ANNI_F))], dtype=float)
        costruisci(f"{settore}_{tipo}_cr", {"unit": "su 100", "dir": "piu", "label": "Indice di ricambio (cause chiuse ogni 100 nuove)",
                   "desc": "Quante cause l'ufficio chiude ogni 100 che ne arrivano nell'anno. 100 = pareggio; sopra 100 le cause aperte diminuiscono, sotto 100 aumentano. Più è alto, meglio è (ma sopra 100 non può durare per sempre).",
                   "fonte": ("CivileFlussi20142025.xlsx, registro SICID senza giudice tutelare, ATP e simili (ricalcolato)" if settore == "civile" else
                             "PenaleFlussi20142025.xlsx, sezioni GIP/GUP, dibattimento e assise (tribunali) o ordinaria, assise, minorenni (corti di appello)"),
                   "ult": len(ANNI_F) - 1, "zero": False, "ref": 100}, X_F, per, 100 * sd / si, 1, tipo=tipo)

# penale: tempo di smaltimento (Ministero), pendenti, solo dibattimento monocratico (nostro)
for tipo in ("tribunale", "corte_appello"):
    per, ita = serie_pnrr("penale", tipo, None, "dt")
    costruisci(f"penale_{tipo}_dt", {"unit": "giorni", "dir": "meno", "label": "Tempo di smaltimento (giorni)",
               "desc": ("Quanti giorni servirebbero per chiudere tutti i procedimenti penali aperti, al ritmo dell'anno. Nei tribunali comprende anche la fase delle indagini davanti al giudice (GIP/GUP), dove molti procedimenti finiscono con l'archiviazione: non è la durata dei processi. Meno è meglio." if tipo == "tribunale" else
                        "Quanti giorni servirebbero per chiudere tutti i procedimenti penali aperti in corte d'appello, al ritmo dell'anno. Meno è meglio."),
               "fonte": "Monitoraggio_PNRR.xlsx, fogli Penale e Indicatori (ricalcolato e verificato)", "ult": 6, "zero": True, "stima": True}, X_P, per, ita, 1, tipo=tipo)
    per, ita = serie_pnrr("penale", tipo, "pendenti", "somma")
    costruisci(f"penale_{tipo}_pend", {"unit": "procedimenti", "dir": None, "label": "Procedimenti penali aperti a fine anno",
               "desc": "Procedimenti penali ancora aperti a fine anno.", "fonte": "Monitoraggio_PNRR.xlsx, foglio Penale", "ult": 6, "zero": True},
               X_P, per, ita, 0, banda=False, tipo=tipo)
dp = pivot_flussi(fp, "dibm_definiti", "tribunale", ANNI_F)
pp_ = pivot_flussi(fp, "dibm_pendenti", "tribunale", ANNI_F)
per = {k: [(366 if a % 4 == 0 else 365) * pp_[k][i] / dp[k][i] if (dp[k][i] and pp_[k][i] is not None) else None for i, a in enumerate(ANNI_F)] for k in dp}
ita = [(366 if a % 4 == 0 else 365) * sum(v[i] or 0 for v in pp_.values()) / sum(v[i] or 0 for v in dp.values()) for i, a in enumerate(ANNI_F)]
costruisci("penale_tribunale_dt_dib", {"unit": "giorni", "dir": "meno", "label": "Tempo di smaltimento solo del dibattimento con giudice singolo (giorni)",
           "desc": "Come il tempo di smaltimento, ma solo per i processi davanti al giudice singolo (la parte più numerosa dei processi penali di primo grado), senza la fase delle indagini. Calcolo nostro. Meno è meglio.",
           "fonte": "PenaleFlussi20142025.xlsx, sezione Dibattimento monocratico, calcolo nostro", "ult": len(ANNI_F) - 1, "zero": True, "stima": True}, X_F, per, ita, 1)

# durata effettiva (solo civile)
for tipo in ("tribunale", "corte_appello"):
    for mat, nome, chv in (("Civile ordinario", "cause civili ordinarie", "co"), ("Lavoro", "cause di lavoro", "lav")):
        q = du[(du.tipo == tipo) & (du.livello == ("ufficio" if tipo == "tribunale" else "distretto")) & (du.materia == mat)]
        p = q.pivot_table(index="chiave", columns="anno", values="durata_giorni")
        per = {k: [cl(p.loc[k, a]) if a in p.columns else None for a in ANNI_F] for k in p.index if (tipo, k) in NOME}
        n = du[(du.tipo == tipo) & (du.livello == "nazionale") & (du.materia == mat)].set_index("anno").durata_giorni
        costruisci(f"civile_{tipo}_dur_{chv}", {"unit": "giorni", "dir": "meno", "label": f"Durata media effettiva delle {nome} chiuse (giorni)",
                   "desc": f"Giorni passati in media, dall'iscrizione alla chiusura, dalle {nome} chiuse in quell'anno. È la durata vera, ma guarda solo le cause già finite: le più lunghe, ancora aperte, non ci sono. Meno è meglio.",
                   "fonte": "Durata_SICID_20142025.xlsx", "ult": len(ANNI_F) - 1, "zero": True}, X_F, per, [n.get(a) for a in ANNI_F], 0, tipo=tipo)

# ------------------------------------------------------------------ posizioni e numeri citati nel testo
def val(key, lab, off=MI, tipo="tribunale"):
    s = SERIE[key]
    i = s["x"].index(lab)
    if off == "italia":
        return s["italia"][i]
    return s["uffici"][NOME[(tipo, off)]][i]


def posizione(key, lab, tipo="tribunale"):
    """posizione di Milano (1 = migliore) tra gli uffici con un valore, mediana e numero di uffici"""
    s = SERIE[key]
    i = s["x"].index(lab)
    v = {k: x[i] for k, x in s["uffici"].items() if x[i] is not None}
    mil = v[NOME[(tipo, MI)]]
    asc = s["dir"] == "meno"
    ordine = sorted(v.values(), reverse=not asc)
    pos = 1 + sum(1 for x in ordine if (x < mil if asc else x > mil))
    return pos, len(v), float(np.median(list(v.values()))), mil


FT_PNRR = "Monitoraggio_PNRR.xlsx"
a = lambda k, l, o=MI, t="tribunale": val(k, l, o, t)

for tipo, pre, tn in (("tribunale", "t", "Tribunale"), ("corte_appello", "c", "Corte d'appello")):
    k = f"civile_{tipo}_dt"
    num(f"{pre}_civ_dt_mi_2019", a(k, "2019", MI, tipo), it_int(a(k, "2019", MI, tipo)), FT_PNRR + ", foglio Civile: pendenti e definiti 2019 (ricalcolato)")
    num(f"{pre}_civ_dt_mi_2025", a(k, "2025", MI, tipo), it_int(a(k, "2025", MI, tipo)), FT_PNRR + ", foglio Civile: pendenti e definiti 2025 (ricalcolato)")
    num(f"{pre}_civ_dt_mi_2026", a(k, "2026*", MI, tipo), it_int(a(k, "2026*", MI, tipo)), FT_PNRR + ", foglio Civile: primo semestre 2026 (ricalcolato)")
    num(f"{pre}_civ_dt_it_2019", a(k, "2019", "italia", tipo), it_int(a(k, "2019", "italia", tipo)), FT_PNRR + ", foglio Civile: somma degli uffici 2019 (ricalcolato)")
    num(f"{pre}_civ_dt_it_2025", a(k, "2025", "italia", tipo), it_int(a(k, "2025", "italia", tipo)), FT_PNRR + ", foglio Civile: somma degli uffici 2025 (ricalcolato)")
    num(f"{pre}_civ_dt_it_2026", a(k, "2026*", "italia", tipo), it_int(a(k, "2026*", "italia", tipo)), FT_PNRR + ", foglio Civile: somma degli uffici, primo semestre 2026")
    v19, v25, i19, i25 = a(k, "2019", MI, tipo), a(k, "2025", MI, tipo), a(k, "2019", "italia", tipo), a(k, "2025", "italia", tipo)
    num(f"{pre}_civ_dt_mi_var", v25 / v19 - 1, it_var(v25 / v19 - 1), "calcolato: DT 2025 su DT 2019")
    num(f"{pre}_civ_dt_it_var", i25 / i19 - 1, it_var(i25 / i19 - 1), "calcolato: DT 2025 su DT 2019, Italia")
    num(f"{pre}_civ_dt_mi_var26", a(k, "2026*", MI, tipo) / v19 - 1, it_var(a(k, "2026*", MI, tipo) / v19 - 1), "calcolato: DT primo semestre 2026 su DT 2019")
    num(f"{pre}_civ_dt_it_var26", a(k, "2026*", "italia", tipo) / i19 - 1, it_var(a(k, "2026*", "italia", tipo) / i19 - 1), "calcolato: DT primo semestre 2026 su DT 2019, Italia")
    num(f"{pre}_civ_dt_mi_var_vs_it_2019", 1 - v19 / i19, it_pct(1 - v19 / i19, 0), "calcolato: quanto Milano era sotto la media italiana nel 2019")
    pos, n, med, mil = posizione(k, "2025", tipo)
    num(f"{pre}_civ_dt_pos", pos, str(pos), "calcolato sul DT 2025 di tutti gli uffici (1 = il più veloce)")
    num(f"{pre}_civ_dt_n", n, str(n), "uffici con dato")
    num(f"{pre}_civ_dt_med", med, it_int(med), "mediana del DT 2025 degli uffici")
    k = f"civile_{tipo}_pend"
    num(f"{pre}_civ_pend_mi_2019", a(k, "2019", MI, tipo), it_int(a(k, "2019", MI, tipo)), FT_PNRR + ", foglio Civile")
    num(f"{pre}_civ_pend_mi_2023", a(k, "2023", MI, tipo), it_int(a(k, "2023", MI, tipo)), FT_PNRR + ", foglio Civile")
    num(f"{pre}_civ_pend_mi_2025", a(k, "2025", MI, tipo), it_int(a(k, "2025", MI, tipo)), FT_PNRR + ", foglio Civile")
    num(f"{pre}_civ_pend_mi_2026", a(k, "2026*", MI, tipo), it_int(a(k, "2026*", MI, tipo)), FT_PNRR + ", foglio Civile, primo semestre 2026")
    num(f"{pre}_civ_pend_it_2025", a(k, "2025", "italia", tipo), it_int(a(k, "2025", "italia", tipo)), FT_PNRR + ", foglio Civile, somma degli uffici")
    num(f"{pre}_civ_pend_mi_var2325", a(k, "2025", MI, tipo) / a(k, "2023", MI, tipo) - 1, it_var(a(k, "2025", MI, tipo) / a(k, "2023", MI, tipo) - 1), "calcolato")
    num(f"{pre}_civ_pend_mi_var1925", a(k, "2025", MI, tipo) / a(k, "2019", MI, tipo) - 1, it_var(a(k, "2025", MI, tipo) / a(k, "2019", MI, tipo) - 1), "calcolato")
    k = f"civile_{tipo}_vecchie_n"
    for lab, y in (("2019", "2019"), ("2022", "2022"), ("2025", "2025"), ("2026*", "2026")):
        num(f"{pre}_civ_vec_mi_{y}", a(k, lab, MI, tipo), it_int(a(k, lab, MI, tipo)), FT_PNRR + ", foglio Civile, colonna Arretrato")
    num(f"{pre}_civ_vec_it_2019", a(k, "2019", "italia", tipo), it_int(a(k, "2019", "italia", tipo)), FT_PNRR + ", foglio Civile, colonna Arretrato, somma degli uffici")
    num(f"{pre}_civ_vec_it_2025", a(k, "2025", "italia", tipo), it_int(a(k, "2025", "italia", tipo)), FT_PNRR + ", foglio Civile, colonna Arretrato, somma degli uffici")
    num(f"{pre}_civ_vec_it_var", a(k, "2025", "italia", tipo) / a(k, "2019", "italia", tipo) - 1, it_var(a(k, "2025", "italia", tipo) / a(k, "2019", "italia", tipo) - 1), "calcolato")
    k = f"civile_{tipo}_vecchie_q"
    qm, qi = a(k, "2025", MI, tipo), a(k, "2025", "italia", tipo)
    num(f"{pre}_civ_vq_mi_2025", qm, it_pct(qm), "Arretrato (Monitoraggio_PNRR.xlsx) su cause aperte SICID 2025 (CivileFlussi20142025.xlsx)")
    num(f"{pre}_civ_vq_it_2025", qi, it_pct(qi), "idem, somma degli uffici")
    num(f"{pre}_civ_vq_mi_2019", a(k, "2019", MI, tipo), it_pct(a(k, "2019", MI, tipo)), "idem, 2019")
    num(f"{pre}_civ_vq_mi_2022", a(k, "2022", MI, tipo), it_pct(a(k, "2022", MI, tipo)), "idem, 2022")
    pos, n, med, mil = posizione(k, "2025", tipo)
    num(f"{pre}_civ_vq_pos", pos, str(pos), "posizione di Milano (1 = meno cause vecchie)")
    num(f"{pre}_civ_vq_n", n, str(n), "uffici con dato")
    num(f"{pre}_civ_vq_med", med, it_pct(med), "mediana della quota degli uffici")
    ps = fl[(fl.tipo == tipo) & (fl.chiave == MI) & (fl.anno == 2025)].pendenti.iloc[0]
    num(f"{pre}_civ_pends_mi_2025", ps, it_int(ps), "cause aperte nel registro SICID (senza giudice tutelare e simili) al 31/12/2025, CivileFlussi20142025.xlsx")
    k = f"civile_{tipo}_cr"
    for lab in ("2019", "2023", "2024", "2025"):
        num(f"{pre}_civ_cr_mi_{lab}", a(k, lab, MI, tipo), it_dec(a(k, lab, MI, tipo), 0), "CivileFlussi20142025.xlsx: definiti su iscritti (ricalcolato)")
        num(f"{pre}_civ_cr_it_{lab}", a(k, lab, "italia", tipo), it_dec(a(k, lab, "italia", tipo), 0), "idem, somma degli uffici")
    k = f"civile_{tipo}_dur_co"
    for lab in ("2019", "2022", "2025"):
        num(f"{pre}_dur_co_mi_{lab}", a(k, lab, MI, tipo), it_int(a(k, lab, MI, tipo)), "Durata_SICID_20142025.xlsx, civile ordinario")
        num(f"{pre}_dur_co_it_{lab}", a(k, lab, "italia", tipo), it_int(a(k, lab, "italia", tipo)), "Durata_SICID_20142025.xlsx, civile ordinario, livello nazionale")
    pos, n, med, mil = posizione(k, "2025", tipo)
    num(f"{pre}_dur_co_pos", pos, str(pos), "posizione di Milano (1 = durata più breve)")
    num(f"{pre}_dur_co_n", n, str(n), "uffici con dato")
    k = f"civile_{tipo}_dur_lav"
    for lab in ("2019", "2022", "2025"):
        num(f"{pre}_dur_lav_mi_{lab}", a(k, lab, MI, tipo), it_int(a(k, lab, MI, tipo)), "Durata_SICID_20142025.xlsx, lavoro")
        num(f"{pre}_dur_lav_it_{lab}", a(k, lab, "italia", tipo), it_int(a(k, lab, "italia", tipo)), "Durata_SICID_20142025.xlsx, lavoro, livello nazionale")

# protezione internazionale
pm = PIM
num("pi_mi_2025", pm.loc[2025, "pi_pendenti"], it_int(pm.loc[2025, "pi_pendenti"]), "CivileFlussi20142025.xlsx, voci 'Protezione internazionale', pendenti 2025, Tribunale di Milano")
num("pi_mi_2019", pm.loc[2019, "pi_pendenti"], it_int(pm.loc[2019, "pi_pendenti"]), "idem, 2019")
num("pi_mi_quota_2025", pm.loc[2025, "pi_pendenti"] / pm.loc[2025, "pendenti"], it_pct(pm.loc[2025, "pi_pendenti"] / pm.loc[2025, "pendenti"], 0),
    "protezione internazionale su cause aperte del tempo di smaltimento, 2025")
num("pi_mi_quota_2019", pm.loc[2019, "pi_pendenti"] / pm.loc[2019, "pendenti"], it_pct(pm.loc[2019, "pi_pendenti"] / pm.loc[2019, "pendenti"], 0), "idem, 2019")
sI = m.groupby("anno")[["pi_pendenti", "pendenti"]].sum()
num("pi_it_2025", sI.loc[2025, "pi_pendenti"], it_int(sI.loc[2025, "pi_pendenti"]), "idem, somma dei 140 tribunali (coincide con la tab. 8 della relazione del Ministero)")
num("pi_it_quota_2025", sI.loc[2025, "pi_pendenti"] / sI.loc[2025, "pendenti"], it_pct(sI.loc[2025, "pi_pendenti"] / sI.loc[2025, "pendenti"], 0), "idem")
m25 = m[m.anno == 2025].sort_values("pi_pendenti", ascending=False)
num("pi_mi_pos", int(list(m25.chiave).index(MI)) + 1, str(int(list(m25.chiave).index(MI)) + 1), "posizione di Milano per cause di protezione internazionale aperte (1 = più cause)")
num("pi_mi_su_it", pm.loc[2025, "pi_pendenti"] / sI.loc[2025, "pi_pendenti"], it_pct(pm.loc[2025, "pi_pendenti"] / sI.loc[2025, "pi_pendenti"], 0), "Milano su Italia")
k = "civile_tribunale_dt_spi"
for lab in ("2019", "2025"):
    num(f"spi_mi_{lab}", a(k, lab), it_int(a(k, lab)), "calcolo nostro: DT senza protezione internazionale")
    num(f"spi_it_{lab}", a(k, lab, "italia"), it_int(a(k, lab, "italia")), "calcolo nostro: DT senza protezione internazionale, Italia")
pos, n, med, mil = posizione(k, "2025")
num("spi_pos", pos, str(pos), "posizione di Milano (1 = più veloce)")
num("spi_med", med, it_int(med), "mediana degli uffici")
num("spi_mi_var", a(k, "2025") / a(k, "2019") - 1, it_var(a(k, "2025") / a(k, "2019") - 1), "calcolato")

atp = pd.read_csv(os.path.join(PU, "atp_previdenza.csv"))
atp["chiave"] = atp.sede.map(chiave)
for a_ in (2019, 2024, 2025):
    num(f"atp_it_{a_}", atp[atp.anno == a_].pendenti.sum(), it_int(atp[atp.anno == a_].pendenti.sum()), "CivileFlussi20142025.xlsx, ATP in materia di previdenza, pendenti nei tribunali (coincide con la tab. 8 della relazione del Ministero)")
num("atp_mi_2025", atp[(atp.anno == 2025) & (atp.chiave == MI)].pendenti.sum(), it_int(atp[(atp.anno == 2025) & (atp.chiave == MI)].pendenti.sum()), "CivileFlussi20142025.xlsx, ATP in materia di previdenza, Tribunale di Milano")

ripart = uff[(uff.settore == "civile") & (uff.tipo == "tribunale")][["chiave", "ripartizione"]].drop_duplicates()
a25 = atp[atp.anno == 2025].merge(ripart, on="chiave", how="left")
assert a25.ripartizione.notna().all(), a25[a25.ripartizione.isna()].sede.tolist()
num("atp_sud_quota", a25[a25.ripartizione == "Sud"].pendenti.sum() / a25.pendenti.sum(), it_pct(a25[a25.ripartizione == "Sud"].pendenti.sum() / a25.pendenti.sum(), 0),
    "CivileFlussi20142025.xlsx (ATP previdenza 2025) e ripartizione geografica del file Monitoraggio_PNRR.xlsx")
sps = pd.read_csv(os.path.join(PU, "stato_persona_sedi.csv"))
sps["chiave"] = sps.sede.map(chiave)
for a_ in (2019, 2025):
    num(f"ve_stato_{a_}", sps[(sps.chiave == "venezia") & (sps.anno == a_)].pendenti.sum(), it_int(sps[(sps.chiave == "venezia") & (sps.anno == a_)].pendenti.sum()),
        "CivileFlussi20142025.xlsx, materia 'Stato della persona e diritti della personalita', Tribunale di Venezia")
    num(f"ve_pend_{a_}", a("civile_tribunale_pend", str(a_), "venezia"), it_int(a("civile_tribunale_pend", str(a_), "venezia")), FT_PNRR + ", foglio Civile, Tribunale di Venezia")
dc = pd.read_csv(os.path.join(PU, "controllo_monitoraggio_distrettuale_civile.csv")).scarto_pct.abs()
num("scarto_civ_min", dc.min(), it_dec(dc.min(), 1), "confronto flussi/monitoraggio distrettuale di Milano, controllo_monitoraggio_distrettuale_civile.csv")
num("scarto_civ_max", dc.max(), it_dec(dc.max(), 1), "idem")
nc = ver[ver.controllo.str.startswith("numero di confronti")].calcolato.iloc[0]
num("n_confronti_dt", nc, it_int(nc), "verifiche.csv")

# penale
for tipo, pre in (("tribunale", "t"), ("corte_appello", "c")):
    k = f"penale_{tipo}_dt"
    for lab in ("2019", "2025", "2026*"):
        y = lab.replace("*", "")
        num(f"{pre}_pen_dt_mi_{y}" if lab != "2026*" else f"{pre}_pen_dt_mi_2026", a(k, lab, MI, tipo), it_int(a(k, lab, MI, tipo)), FT_PNRR + ", foglio Penale (ricalcolato)")
        num(f"{pre}_pen_dt_it_{y}" if lab != "2026*" else f"{pre}_pen_dt_it_2026", a(k, lab, "italia", tipo), it_int(a(k, lab, "italia", tipo)), FT_PNRR + ", foglio Penale, somma degli uffici")
    pos, n, med, mil = posizione(k, "2025", tipo)
    num(f"{pre}_pen_dt_pos", pos, str(pos), "posizione di Milano sul DT penale 2025 (1 = più veloce)")
    num(f"{pre}_pen_dt_n", n, str(n), "uffici")
    num(f"{pre}_pen_dt_med", med, it_int(med), "mediana degli uffici")
    num(f"{pre}_pen_dt_mi_var26", a(k, "2026*", MI, tipo) / a(k, "2019", MI, tipo) - 1, it_var(a(k, "2026*", MI, tipo) / a(k, "2019", MI, tipo) - 1), "calcolato")
    num(f"{pre}_pen_dt_it_var26", a(k, "2026*", "italia", tipo) / a(k, "2019", "italia", tipo) - 1, it_var(a(k, "2026*", "italia", tipo) / a(k, "2019", "italia", tipo) - 1), "calcolato")
    k = f"penale_{tipo}_pend"
    num(f"{pre}_pen_pend_mi_2019", a(k, "2019", MI, tipo), it_int(a(k, "2019", MI, tipo)), FT_PNRR + ", foglio Penale")
    num(f"{pre}_pen_pend_mi_2025", a(k, "2025", MI, tipo), it_int(a(k, "2025", MI, tipo)), FT_PNRR + ", foglio Penale")
    num(f"{pre}_pen_pend_mi_var", a(k, "2025", MI, tipo) / a(k, "2019", MI, tipo) - 1, it_var(a(k, "2025", MI, tipo) / a(k, "2019", MI, tipo) - 1), "calcolato")
    k = f"penale_{tipo}_cr"
    for lab in ("2019", "2025"):
        num(f"{pre}_pen_cr_mi_{lab}", a(k, lab, MI, tipo), it_dec(a(k, lab, MI, tipo), 0), "PenaleFlussi20142025.xlsx: definiti su iscritti (ricalcolato)")
        num(f"{pre}_pen_cr_it_{lab}", a(k, lab, "italia", tipo), it_dec(a(k, lab, "italia", tipo), 0), "idem, somma degli uffici")
k = "penale_tribunale_dt_dib"
num("dib_mi_2019", a(k, "2019"), it_int(a(k, "2019")), "PenaleFlussi20142025.xlsx, dibattimento monocratico, calcolo nostro")
num("dib_mi_2025", a(k, "2025"), it_int(a(k, "2025")), "idem, 2025")
num("dib_it_2025", a(k, "2025", "italia"), it_int(a(k, "2025", "italia")), "idem, somma dei tribunali")
pos, n, med, mil = posizione(k, "2025")
num("dib_pos", pos, str(pos), "posizione di Milano (1 = più veloce)")
num("dib_n", n, str(n), "tribunali")
num("dib_med", med, it_int(med), "mediana dei tribunali")

# indice di ricambio / pendenti penali: gia' sopra. Numero di uffici
num("n_tribunali", 140, "140", "elenco dei tribunali nel file PNRR")
num("n_corti", 29, "29", "elenco delle corti di appello nel file PNRR (comprende 3 sezioni distaccate)")

# ------------------------------------------------------------------ obiettivi PNRR (tabella)
def tot3(settore, anno, periodo):
    q = uff[(uff.settore == settore) & (uff.anno == anno) & (uff.periodo == periodo)].groupby("tipo")[["definiti", "pendenti", "giorni_periodo"]].agg(
        {"definiti": "sum", "pendenti": "sum", "giorni_periodo": "max"})
    dts = {t_: q.loc[t_, "giorni_periodo"] * q.loc[t_, "pendenti"] / q.loc[t_, "definiti"] for t_ in ("tribunale", "corte_appello", "cassazione")}
    return dts, sum(dts.values())


R = {}
for settore in ("civile", "penale"):
    b, bt = tot3(settore, 2019, "Intero anno")
    c25, ct25 = tot3(settore, 2025, "Intero anno")
    c26, ct26 = tot3(settore, 2026, "Primo semestre")
    R[settore] = {"base": bt, "v25": ct25, "v26": ct26, "var25": ct25 / bt - 1, "var26": ct26 / bt - 1}
    num(f"pnrr_{settore}_base", bt, it_int(bt), FT_PNRR + ": somma dei DT di tribunali, corti di appello e Cassazione, 2019")
    num(f"pnrr_{settore}_v25", ct25, it_int(ct25), FT_PNRR + ": somma dei tre DT, 2025")
    num(f"pnrr_{settore}_v26", ct26, it_int(ct26), FT_PNRR + ": somma dei tre DT, primo semestre 2026")
    num(f"pnrr_{settore}_var25", ct25 / bt - 1, it_var(ct25 / bt - 1, 1), "calcolato (coincide con la relazione del Ministero)")
    num(f"pnrr_{settore}_var26", ct26 / bt - 1, it_var(ct26 / bt - 1, 1), "calcolato (coincide con la relazione del Ministero)")


def smaltimento(tipo, sede_chiave, colbase, colpend, anno, periodo):
    q = uff[(uff.settore == "civile") & (uff.tipo == tipo) & (uff.chiave == sede_chiave)]
    base = q[(q.anno == anno) & (q.periodo == periodo)][colbase].iloc[0]
    pe = q[(q.anno == anno) & (q.periodo == periodo)][colpend].iloc[0]
    return base, pe, pe / base - 1


b24t, p24t, v24t = smaltimento("tribunale", MI, "baseline_obiettivo_2024", "pendenti_obiettivo_2024", 2024, "Intero anno")
b24c, p24c, v24c = smaltimento("corte_appello", MI, "baseline_obiettivo_2024", "pendenti_obiettivo_2024", 2024, "Intero anno")
b26t, p26t, v26t = smaltimento("tribunale", MI, "baseline_obiettivo_2026", "pendenti_obiettivo_2026", 2026, "Primo semestre")
b26c, p26c, v26c = smaltimento("corte_appello", MI, "baseline_obiettivo_2026", "pendenti_obiettivo_2026", 2026, "Primo semestre")
q = uff[(uff.settore == "civile") & (uff.anno == 2026) & (uff.periodo == "Primo semestre")].groupby("tipo")[["baseline_obiettivo_2026", "pendenti_obiettivo_2026"]].sum()
it26t = q.loc["tribunale", "pendenti_obiettivo_2026"] / q.loc["tribunale", "baseline_obiettivo_2026"] - 1
it26c = q.loc["corte_appello", "pendenti_obiettivo_2026"] / q.loc["corte_appello", "baseline_obiettivo_2026"] - 1
for k_, v_, t_ in (("sm24_t_base", b24t, it_int(b24t)), ("sm24_t_fine", p24t, it_int(p24t)), ("sm24_t_var", v24t, it_pct(v24t, 1)),
                   ("sm24_c_base", b24c, it_int(b24c)), ("sm24_c_fine", p24c, it_int(p24c)), ("sm24_c_var", v24c, it_pct(v24c, 1)),
                   ("sm26_t_base", b26t, it_int(b26t)), ("sm26_t_fine", p26t, it_int(p26t)), ("sm26_t_var", v26t, it_pct(v26t, 1)),
                   ("sm26_c_base", b26c, it_int(b26c)), ("sm26_c_fine", p26c, it_int(p26c)), ("sm26_c_var", v26c, it_pct(v26c, 1)),
                   ("sm26_it_t_var", it26t, it_pct(it26t, 1)), ("sm26_it_c_var", it26c, it_pct(it26c, 1))):
    num(k_, v_, t_, FT_PNRR + ", foglio Civile, colonne 'Baseline/Pendenti per obiettivo' (Milano; Italia = somma degli uffici)")

PNRR = [
    {"obiettivo": "Ridurre del 40% il tempo di smaltimento civile (somma dei tre gradi) entro giugno 2026, rispetto al 2019",
     "italia": f"{NUM['pnrr_civile_var26']['t']}% (primo semestre 2026; {NUM['pnrr_civile_var25']['t']}% nel 2025)",
     "mi_trib": f"{NUM['t_civ_dt_mi_var26']['t']}% ({NUM['t_civ_dt_mi_2019']['t']} giorni nel 2019, {NUM['t_civ_dt_mi_2026']['t']} nel primo semestre 2026)",
     "mi_corte": f"{it_var(a('civile_corte_appello_dt','2026*')/a('civile_corte_appello_dt','2019')-1)}% ({NUM['c_civ_dt_mi_2019']['t']} giorni, poi {NUM['c_civ_dt_mi_2026']['t']})",
     "esito": "Italia: raggiunto"},
    {"obiettivo": "Ridurre del 25% il tempo di smaltimento penale (somma dei tre gradi) entro giugno 2026, rispetto al 2019",
     "italia": f"{NUM['pnrr_penale_var26']['t']}% (primo semestre 2026; {NUM['pnrr_penale_var25']['t']}% nel 2025)",
     "mi_trib": f"{NUM['t_pen_dt_mi_var26']['t']}% ({NUM['t_pen_dt_mi_2019']['t']} giorni nel 2019, {NUM['t_pen_dt_mi_2026']['t']} nel primo semestre 2026)",
     "mi_corte": f"{NUM['c_pen_dt_mi_var26']['t']}% ({NUM['c_pen_dt_mi_2019']['t']} giorni, poi {NUM['c_pen_dt_mi_2026']['t']})",
     "esito": "Italia: raggiunto"},
    {"obiettivo": "Ridurre del 95% entro il 31/12/2024 le cause civili già vecchie nel 2019 (iscritte fino al 2016 in tribunale, fino al 2017 in corte d'appello)",
     "italia": "raggiunto, secondo il Ministero (relazione I semestre 2026, pag. 2)",
     "mi_trib": f"{NUM['sm24_t_var']['t']}% ({NUM['sm24_t_base']['t']} cause nel 2019, {NUM['sm24_t_fine']['t']} a fine 2024)",
     "mi_corte": f"{NUM['sm24_c_var']['t']}% ({NUM['sm24_c_base']['t']} cause, poi {NUM['sm24_c_fine']['t']})",
     "esito": "Italia: raggiunto"},
    {"obiettivo": "Ridurre del 90% entro il 30/06/2026 le cause civili aperte a fine 2022 e iscritte dal 2017 (tribunali) o dal 2018 (corti di appello) al 2022",
     "italia": f"tribunali {NUM['sm26_it_t_var']['t']}%, corti di appello {NUM['sm26_it_c_var']['t']}% (primo semestre 2026)",
     "mi_trib": f"{NUM['sm26_t_var']['t']}% ({NUM['sm26_t_base']['t']} cause a fine 2022, {NUM['sm26_t_fine']['t']} a giugno 2026)",
     "mi_corte": f"{NUM['sm26_c_var']['t']}% ({NUM['sm26_c_base']['t']} cause, poi {NUM['sm26_c_fine']['t']})",
     "esito": "Italia: raggiunto"},
]
pd.DataFrame(PNRR).rename(columns={"obiettivo": "obiettivo", "italia": "italia_variazione", "mi_trib": "tribunale_di_milano", "mi_corte": "corte_appello_di_milano",
                                   "esito": "esito_italia"}).to_csv(os.path.join(OUT, "pnrr_obiettivi.csv"), index=False, sep=";")

# ------------------------------------------------------------------ tabella dei grandi tribunali + file per ufficio
def riga(tipo, chv):
    nm = NOME[(tipo, chv)]
    g = lambda key, lab: SERIE[key]["uffici"][nm][SERIE[key]["x"].index(lab)]
    pre = f"civile_{tipo}_"
    r = {"ufficio": nm,
         "civile_cause_aperte_2025": g(pre + "pend", "2025"),
         "civile_tempo_smaltimento_2019": g(pre + "dt", "2019"), "civile_tempo_smaltimento_2025": g(pre + "dt", "2025"),
         "civile_indice_ricambio_2025": g(pre + "cr", "2025"),
         "civile_quota_cause_vecchie_2025": g(pre + "vecchie_q", "2025"),
         "civile_cause_vecchie_2025": g(pre + "vecchie_n", "2025"),
         "civile_durata_media_cause_ordinarie_2025": g(pre + "dur_co", "2025"),
         "penale_tempo_smaltimento_2019": g(f"penale_{tipo}_dt", "2019"), "penale_tempo_smaltimento_2025": g(f"penale_{tipo}_dt", "2025"),
         "penale_indice_ricambio_2025": g(f"penale_{tipo}_cr", "2025")}
    if tipo == "tribunale":
        r["civile_tempo_smaltimento_senza_prot_internaz_2025"] = g("civile_tribunale_dt_spi", "2025")
        r["penale_tempo_smaltimento_solo_dibattimento_2025"] = g("penale_tribunale_dt_dib", "2025")
    r["distretto"] = uff[(uff.tipo == tipo) & (uff.chiave == chv)].distretto.iloc[0]
    return r


trib = pd.DataFrame([riga("tribunale", k[1]) for k in NOME if k[0] == "tribunale"]).sort_values("civile_cause_aperte_2025", ascending=False)
corti = pd.DataFrame([riga("corte_appello", k[1]) for k in NOME if k[0] == "corte_appello"]).sort_values("civile_cause_aperte_2025", ascending=False)
trib.to_csv(os.path.join(OUT, "tribunali_2025.csv"), index=False, sep=";", decimal=",")
corti.to_csv(os.path.join(OUT, "corti_appello_2025.csv"), index=False, sep=";", decimal=",")
grandi = trib.head(12)
assert "Milano" in set(grandi.ufficio)
grandi.to_csv(os.path.join(OUT, "grandi_tribunali.csv"), index=False, sep=";", decimal=",")
GRANDI = [{k: (cl(v) if not isinstance(v, str) else v) for k, v in r.items()} for r in grandi.to_dict("records")]

# ------------------------------------------------------------------ protezione internazionale a Milano
pit = pd.DataFrame({"anno": list(range(2019, 2026)), "cause_civili_aperte_tempo_smaltimento": [int(pm.loc[a_, "pendenti"]) for a_ in range(2019, 2026)],
                    "di_cui_protezione_internazionale": [int(pm.loc[a_, "pi_pendenti"]) for a_ in range(2019, 2026)]})
pit["altre_cause"] = pit.cause_civili_aperte_tempo_smaltimento - pit.di_cui_protezione_internazionale
pit.to_csv(os.path.join(OUT, "pendenti_milano_protezione_internazionale.csv"), index=False, sep=";")
PI_TAB = pit.to_dict("records")

# ------------------------------------------------------------------ serie in formato lungo
righe = []
for key, s in SERIE.items():
    sett, tipo, ind = key.split("_", 2)
    for i, xl in enumerate(s["x"]):
        for chi, vals in (("Milano", s["milano"]), ("Italia", s["italia"]), ("Mediana degli uffici", s.get("p50")), ("25o percentile degli uffici", s.get("p25")),
                          ("75o percentile degli uffici", s.get("p75"))):
            if vals is None or vals[i] is None:
                continue
            righe.append({"settore": sett, "ufficio_tipo": tipo, "indicatore": ind, "descrizione": s["label"], "periodo": xl.replace("*", " (primo semestre, provvisorio)"),
                          "chi": chi, "valore": vals[i], "unita": s["unit"]})
pd.DataFrame(righe).to_csv(os.path.join(OUT, "serie_milano_italia.csv"), index=False, sep=";", decimal=",")

# ------------------------------------------------------------------ scrittura JSON
def default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if math.isnan(o) else float(o)
    raise TypeError(type(o))


json.dump(SERIE, open(os.path.join(OUT, "serie.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"), default=default)
json.dump({"n": NUM, "pnrr": PNRR, "grandi": GRANDI, "pi": PI_TAB, "scaricato": "2 novembre 2026"},
          open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"), default=default)
shutil.copyfile(os.path.join(PU, "verifiche.csv"), os.path.join(OUT, "verifiche.csv"))
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
print("numeri nel testo:", len(NUM), "indicatori:", len(SERIE))
