"""Fase 1 - pulizia: legge gli amministratori comunali a fine anno 2007-2025 (DAIT, Ministero dell'Interno) e l'elenco "in carica" al 24/8/2026.
Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 build.py <amministratori_dir>
Legge: raw/dait/comuni_31dic<anno>.csv, raw/dait/in_carica_ammcom.csv
Scrive in pulito/:
  comuni_ruoli.csv.gz        tutta Italia, una riga per persona-carica-fotografia: SENZA cognome, nome, luogo di nascita
                             (solo hash della persona, sesso, anno di nascita, eta')
  milano_amministratori.csv  Milano (cod. ISTAT 015146), con nome e cognome (persone pubbliche, ruolo pubblico)
  milano_in_carica.csv       Milano al 24/8/2026 (elenco "in carica")
  grandi_citta_in_carica.csv sindaci e giunte delle 10 maggiori citta' al 24/8/2026
  controlli_build.json
Nessun file in pulito/ ha date o luoghi di nascita completi: solo anno di nascita e eta'.
"""
import sys, os, json, hashlib
import pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comune_lib as L

A = sys.argv[1]
RAW = os.path.join(A, "raw", "dait"); PU = os.path.join(A, "pulito"); os.makedirs(PU, exist_ok=True)
CTRL = {}


def hid(c, n, d):
    return hashlib.sha1(f"{c}|{n}|{d}".encode("utf8")).hexdigest()[:12]


def prep(d, snap_date):
    """d: DataFrame di stringhe (schema vecchio o nuovo). Restituisce tabella normalizzata."""
    pop = d["POPOLAZIONE_CENSITA_ALLA_DATA_ELEZIONE"] if "POPOLAZIONE_CENSITA_ALLA_DATA_ELEZIONE" in d else d["POPOLAZIONE_CENSITA"]
    ini = d["DATA_INIZIO_CARICA"] if "DATA_INIZIO_CARICA" in d else d["DATA_NOMINA"]
    lis = d["LISTA_APPARTENENZA/COLLEGAMENTO"] if "LISTA_APPARTENENZA/COLLEGAMENTO" in d else d["PARTITO_LISTA_COALIZIONE"]
    dn = pd.to_datetime(d["DATA_NASCITA"], format="%d/%m/%Y", errors="coerce")
    eta = (snap_date - dn).dt.days / 365.2425
    out = pd.DataFrame({
        "istat": d["ISTAT_CODICE_COMUNE"].str.zfill(6),
        "comune": d["DESCRIZIONE_COMUNE"].str.strip().str.title(),
        "provincia": d["SIGLA_PROVINCIA"],
        "regione": d["DESCRIZIONE_REGIONE"].str.title(),
        "pop": pd.to_numeric(pop, errors="coerce"),
        "elezione": d["DATA_ELEZIONE"],
        "carica": d["DESCRIZIONE_CARICA"].str.strip(),
        "inizio": pd.to_datetime(ini, format="%d/%m/%Y", errors="coerce"),
        "fine": pd.to_datetime(d["DATA_CESSAZIONE"], format="%d/%m/%Y", errors="coerce"),
        "sesso": d["SESSO"].str.strip().str.upper(),
        "anno_nascita": dn.dt.year,
        "eta": eta.round(1),
        "titolo_orig": d["TITOLO_DI_STUDIO"].str.strip(),
        "professione_orig": d["PROFESSIONE"].str.strip(),
        "lista": lis.str.strip(),
        "persona": [hid(c, n, x) for c, n, x in zip(d["COGNOME"], d["NOME"], d["DATA_NASCITA"])],
        "cognome": d["COGNOME"].str.strip().str.title(),
        "nome": d["NOME"].str.strip().str.title(),
    })
    out["ruolo"] = out["carica"].map(L.ruolo)
    out["esterno"] = out["carica"].map(L.esterno)
    out["titolo"] = out["titolo_orig"].map(L.titolo)
    out["prof_cat"] = out["professione_orig"].map(L.prof_cat)
    return out


parti = []; ctrl_anni = {}
for y in range(2007, 2026):
    snap = pd.Timestamp(y, 12, 31)
    enc = "utf8" if y >= 2023 else "cp1252"
    d = pd.read_csv(os.path.join(RAW, f"comuni_31dic{y}.csv"), sep=";", dtype=str, encoding=enc, keep_default_na=False)
    o = prep(d, snap)
    o.insert(0, "anno", y)
    ctrl_anni[y] = {"righe": len(o), "righe_ruolo_valido": int(o.ruolo.notna().sum()),
                    "inizio_dopo_31dic": int((o.inizio > snap).sum()), "cessazione_entro_31dic": int((o.fine <= snap).sum()),
                    "eta_fuori_18_100": int(((o.eta < 18) | (o.eta > 100)).sum()), "eta_mancante": int(o.eta.isna().sum()),
                    "sesso_mancante": int((~o.sesso.isin(["M", "F"])).sum()),
                    "doppioni_persona_comune": int(o[o.ruolo.notna()].duplicated(["istat", "persona"]).sum())}
    o.loc[(o.eta < 18) | (o.eta > 100), ["eta", "anno_nascita"]] = np.nan
    o = o[o.ruolo.notna()]
    parti.append(o)
    print(y, len(o), flush=True)
CTRL["per_anno"] = ctrl_anni

tutto = pd.concat(parti, ignore_index=True)
tutto.drop(columns=["titolo_orig", "professione_orig", "lista", "cognome", "nome"]).to_csv(
    os.path.join(PU, "comuni_ruoli.csv.gz"), index=False, compression="gzip")
mi = tutto[tutto.istat == "015146"].drop(columns=["istat", "comune", "provincia", "regione"])
mi.to_csv(os.path.join(PU, "milano_amministratori.csv"), index=False)
CTRL["milano_righe"] = len(mi)

# ---------------- in carica al 24/8/2026
ic = pd.read_csv(os.path.join(RAW, "in_carica_ammcom.csv"), sep=";", dtype=str, encoding="utf8", keep_default_na=False, skiprows=2)
CTRL["in_carica_righe"] = len(ic)
snap = pd.Timestamp(2026, 8, 24)
dn = pd.to_datetime(ic["data_nascita"], format="%d/%m/%Y", errors="coerce")
x = pd.DataFrame({
    "codice_regione": ic["codice_regione"], "codice_provincia": ic["codice_provincia"], "codice_comune": ic["codice_comune"],
    "comune": ic["denominazione_comune"].str.title(), "provincia": ic["sigla_provincia"],
    "pop": pd.to_numeric(ic["popolazione_censita_alla_data_elezione"], errors="coerce"),
    "cognome": ic["cognome"].str.strip().str.title(), "nome": ic["nome"].str.strip().str.title(),
    "sesso": ic["sesso"].str.upper(), "anno_nascita": dn.dt.year, "eta": ((snap - dn).dt.days / 365.2425).round(1),
    "carica": ic["descrizione_carica"].str.strip(), "incarico": ic["incarico"].str.strip(),
    "elezione": ic["data_elezione"], "inizio": pd.to_datetime(ic["data_entrata_in_carica"], format="%d/%m/%Y", errors="coerce"),
    "lista": ic["lista_appartenenza/collegamento"].str.strip(), "titolo_orig": ic["titolo_studio"].str.strip(),
    "professione_orig": ic["professione"].str.strip()})
x["ruolo"] = x.carica.map(L.ruolo); x["titolo"] = x.titolo_orig.map(L.titolo); x["prof_cat"] = x.professione_orig.map(L.prof_cat)
mil = x[(x.codice_regione == "03") & (x.codice_provincia == "049") & (x.codice_comune == "1450")]
assert len(mil) > 50, len(mil)
mil.drop(columns=["codice_regione", "codice_provincia", "codice_comune"]).to_csv(os.path.join(PU, "milano_in_carica.csv"), index=False)
CTRL["milano_in_carica_righe"] = len(mil)
nomi_g = {"Roma": "RM", "Milano": "MI", "Napoli": "NA", "Torino": "TO", "Palermo": "PA", "Genova": "GE", "Bologna": "BO",
          "Firenze": "FI", "Bari": "BA", "Catania": "CT"}
sel = pd.concat([x[(x.comune == c) & (x.provincia == sg)] for c, sg in nomi_g.items()])
sel = sel[sel.ruolo.isin(["sindaco", "giunta"])]
sel.drop(columns=["codice_regione", "codice_provincia", "codice_comune", "titolo_orig", "professione_orig"]).to_csv(
    os.path.join(PU, "grandi_citta_in_carica.csv"), index=False)
CTRL["grandi_citta_in_carica_righe"] = len(sel)
CTRL["grandi_citta_trovate"] = sorted(sel.comune.unique())
json.dump(CTRL, open(os.path.join(PU, "controlli_build.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False, default=str)
print("fatto")
