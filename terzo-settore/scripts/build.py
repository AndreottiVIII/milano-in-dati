"""Fase 1 - pulizia e riepiloghi del filone "Associazioni e terzo settore".
Uso: python -I -X utf8 build.py <terzo-settore_dir assoluto> <milano-in-dati_dir assoluto>
Legge: raw/runts/*.xlsx (RUNTS, lista enti iscritti 2/11/2026), raw/comune/ds1332 ds562 ds606 ds596 (CKAN Comune, 2/11/2026),
       raw/istat/*.xlsx (Tavole non profit 2023), raw/istat_pop/estratto_2025 (POSAS 1/1/2025),
       citta-15-minuti (civici ds634), alberi/pulito/nil_alberi.csv (abitanti per NIL 2024), benessere/pulito/bes_lungo.csv.
Scrive in pulito/. La colonna con il nome del legale rappresentante del RUNTS NON viene mai copiata."""
import sys, os, re, json, glob, unicodedata
import pandas as pd, numpy as np
T, P = sys.argv[1], sys.argv[2]
PU = os.path.join(T, "pulito"); os.makedirs(PU, exist_ok=True)
sys.path.insert(0, os.path.join(T, "scripts"))
from lib_geocode import Geocoder
LOG = {}


def sa(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).upper().strip()


# ------------------------------------------------------------------ RUNTS
x = glob.glob(os.path.join(T, "raw", "runts", "*iscritti*.xlsx"))[0]
df = pd.read_excel(x, dtype=str, keep_default_na=False, na_values=[""]).iloc[:, :10]   # "NA" = provincia di Napoli: non va letta come dato mancante
df.columns = ["cf", "repertorio", "denominazione", "sezione", "legale_rapp", "rete", "comune", "provincia", "cinque_per_mille", "data_iscrizione"]
df = df.drop(columns=["legale_rapp"])           # dati di persone: mai usati
df["denominazione"] = df.denominazione.str.strip()
df["sezione"] = df.sezione.replace({"-": "n.d."})
df["anno_iscrizione"] = df.data_iscrizione.str[-4:].astype(int)
LOG["runts_righe"] = len(df)
assert df.provincia.notna().all() and df.comune.notna().all()
assert df.cf.is_unique and df.repertorio.is_unique
assert df.cf.str.fullmatch(r"\d{11}").all()      # nessun codice fiscale di persona fisica (16 caratteri)
LOG["runts_per_sezione_italia"] = df.sezione.value_counts().to_dict()
LOG["runts_per_anno_iscrizione"] = df.anno_iscrizione.value_counts().sort_index().to_dict()


def tipo_nome(r):
    n = sa(r.denominazione)
    if r.sezione == "IMPRESE SOCIALI":
        return "cooperativa sociale" if re.search(r"\bCOOP", n) else "altra impresa sociale"
    if re.search(r"\bFONDAZIONE\b|\bFOUNDATION\b", n):
        return "fondazione (dal nome)"
    if re.search(r"\bCOOP", n):
        return "cooperativa (dal nome)"
    return {"ORGANIZZAZIONI DI VOLONTARIATO": "ODV", "ASSOCIAZIONI DI PROMOZIONE SOCIALE": "APS"}.get(r.sezione, "altro ETS")


df["tipo"] = df.apply(tipo_nome, axis=1)
df["comune_n"] = df.comune.map(sa)
df.drop(columns=["comune_n"]).to_csv(os.path.join(PU, "runts_enti_italia_senza_persone.csv"), sep=";", index=False, encoding="utf8")

# ------------------------------------------------------------------ popolazione 1/1/2025 (ISTAT POSAS) per comune
pf = glob.glob(os.path.join(T, "raw", "istat_pop", "estratto_2025", "*.csv"))[0]
pop = pd.read_csv(pf, sep=";", skiprows=1, encoding="utf-8-sig", dtype={"Codice comune": str})
tot = pop[pop["Età"] == 999].copy()
if tot.empty:
    tot = pop.groupby(["Codice comune", "Comune"], as_index=False)["Totale"].sum()
tot = tot.rename(columns={"Codice comune": "cod", "Comune": "nome", "Totale": "ab"})[["cod", "nome", "ab"]]
tot["prov3"] = tot.cod.str[:3]
LOG["pop_italia_2025"] = int(tot.ab.sum()); LOG["pop_comuni"] = len(tot)
BIG = {"058091": ("Roma", "RM"), "015146": ("Milano", "MI"), "063049": ("Napoli", "NA"), "001272": ("Torino", "TO"), "082053": ("Palermo", "PA"),
       "010025": ("Genova", "GE"), "037006": ("Bologna", "BO"), "048017": ("Firenze", "FI"), "072006": ("Bari", "BA"), "087015": ("Catania", "CT"),
       "027042": ("Venezia", "VE"), "023091": ("Verona", "VR"), "083048": ("Messina", "ME"), "028060": ("Padova", "PD"), "032006": ("Trieste", "TS"),
       "017029": ("Brescia", "BS"), "034027": ("Parma", "PR"), "100005": ("Prato", "PO")}   # i 18 comuni con almeno 197.000 residenti (1/1/2025)
for c in BIG:
    assert c in set(tot.cod), c
bigrows = []
for cod, (nome, sig) in BIG.items():
    ab = int(tot[tot.cod == cod].ab.iloc[0])
    r = df[(df.comune_n == sa(nome)) & (df.provincia == sig)]
    row = {"citta": nome, "cod_istat": cod, "abitanti_2025": ab, "enti_runts": len(r)}
    for k, v in r.sezione.value_counts().items():
        row["sez_" + k] = int(v)
    for k, v in r.tipo.value_counts().items():
        row["tipo_" + k] = int(v)
    row["per_10000"] = round(10000 * len(r) / ab, 1)
    bigrows.append(row)
big = pd.DataFrame(bigrows).fillna(0)
for c in big.columns:
    if c.startswith(("sez_", "tipo_")):
        big[c] = big[c].astype(int)
big["odv_per_10000"] = (10000 * big["sez_ORGANIZZAZIONI DI VOLONTARIATO"] / big.abitanti_2025).round(1)
big["aps_per_10000"] = (10000 * big["sez_ASSOCIAZIONI DI PROMOZIONE SOCIALE"] / big.abitanti_2025).round(1)
big["imprese_sociali_per_10000"] = (10000 * big["sez_IMPRESE SOCIALI"] / big.abitanti_2025).round(1)
big["altri_per_10000"] = (10000 * big["sez_ALTRI ENTI DEL TERZO SETTORE"] / big.abitanti_2025).round(1)
big = big.sort_values("per_10000", ascending=False)
big.to_csv(os.path.join(PU, "runts_grandi_citta.csv"), index=False, encoding="utf8")
LOG["grandi_citta"] = big[["citta", "enti_runts", "abitanti_2025", "per_10000"]].to_dict("records")
LOG["runts_italia_per_10000"] = round(10000 * len(df) / LOG["pop_italia_2025"], 1)

# provincia di Milano (133 comuni) - per il confronto con ISTAT/Bes (provincia)
ab_mi = int(tot[tot.prov3 == "015"].ab.sum()); mi_prov = int((df.provincia == "MI").sum())
LOG["provincia_milano"] = {"abitanti_2025": ab_mi, "enti_runts": mi_prov, "per_10000": round(10000 * mi_prov / ab_mi, 1)}
SIG = {"001": "TO", "010": "GE", "015": "MI", "027": "VE", "037": "BO", "048": "FI", "058": "RM", "063": "NA", "072": "BA", "082": "PA", "087": "CT", "083": "ME", "080": "RC", "092": "CA"}
rows = []
for p3, sig in SIG.items():
    ab = int(tot[tot.prov3 == p3].ab.sum()); n = int((df.provincia == sig).sum())
    rows.append({"provincia": sig, "abitanti_2025": ab, "enti_runts": n, "per_10000": round(10000 * n / ab, 1)})
pd.DataFrame(rows).to_csv(os.path.join(PU, "runts_province_metropolitane.csv"), index=False)

# ------------------------------------------------------------------ RUNTS - Milano comune
m = df[(df.comune_n == "MILANO") & (df.provincia == "MI")].copy()
LOG["runts_milano"] = len(m)
LOG["runts_milano_per_sezione"] = m.sezione.value_counts().to_dict()
LOG["runts_milano_per_tipo"] = m.tipo.value_counts().to_dict()
LOG["runts_milano_per_anno"] = m.anno_iscrizione.value_counts().sort_index().to_dict()
LOG["runts_milano_5x1000"] = int((m.cinque_per_mille == "Si").sum())
LOG["runts_milano_rete"] = int((m.rete == "Si").sum())
m[["cf", "repertorio", "denominazione", "sezione", "tipo", "rete", "cinque_per_mille", "data_iscrizione", "anno_iscrizione"]].to_csv(
    os.path.join(PU, "runts_milano.csv"), sep=";", index=False, encoding="utf8")
LOG["provincia_mi_comuni_con_enti"] = int(df[df.provincia == "MI"].comune_n.nunique())

# ------------------------------------------------------------------ Registri del Comune (CKAN) con indirizzo -> NIL
civ = os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "civici", "estratto", "ds634_civici_coordinategeografiche_20261001_final.csv")
G = Geocoder(civ)
c1332 = pd.read_csv(glob.glob(os.path.join(T, "raw", "comune", "ds1332", "*.csv"))[0], sep=";", dtype=str, encoding="utf8").fillna("")
LOG["ds1332_righe"] = len(c1332)
sede = (c1332["Indirizzo sede legale"] + " " + c1332["Civico sede legale"]).str.strip()
res = [G.geocodifica(a) if c.strip().lower() == "milano" else dict(esito="fuori_milano") for a, c in zip(sede, c1332["Comune sede legale"])]
c1332["esito_geo"] = [r["esito"] for r in res]
c1332["lon"] = [r.get("lon") for r in res]
c1332["lat"] = [r.get("lat") for r in res]
c1332["id_nil"] = [r.get("idnil") for r in res]
c1332["nil"] = [r.get("nil") for r in res]
LOG["ds1332_geocodifica"] = c1332.esito_geo.value_counts().to_dict()
LOG["ds1332_con_nil"] = int((c1332.id_nil.fillna("") != "").sum())
c1332_out = c1332.rename(columns={"Denominazione": "denominazione", "Natura giuridica": "natura", "Settore di intervento": "settore",
                                  "Municipio prevalente": "municipio_prevalente", "Municipi di interesse": "municipi_interesse"})
c1332_out[["denominazione", "natura", "settore", "municipio_prevalente", "municipi_interesse", "esito_geo", "lon", "lat", "id_nil", "nil"]].to_csv(
    os.path.join(PU, "registro_comune_associazioni.csv"), sep=";", index=False, encoding="utf8")

c562 = pd.read_csv(glob.glob(os.path.join(T, "raw", "comune", "ds562", "*.csv"))[0], sep=";", dtype=str, encoding="utf8").fillna("")
c606 = pd.read_csv(glob.glob(os.path.join(T, "raw", "comune", "ds606", "*.csv"))[0], sep=";", dtype=str, encoding="utf8").fillna("")
c596 = pd.read_csv(glob.glob(os.path.join(T, "raw", "comune", "ds596", "*.csv"))[0], sep=";", dtype=str, encoding="utf8").fillna("")
LOG["ds562_righe"] = len(c562)
LOG["ds562_comune"] = c562.COMUNE.value_counts().head(5).to_dict()
LOG["ds562_senza_nil"] = int((c562.ID_NIL == "").sum())
LOG["ds596_righe"] = len(c596)
LOG["ds596_senza_nil"] = int((c596.ID_NIL == "").sum())


def ind606(r):
    v, n = r.VIA.strip(), r.NRO_CIVICO.strip()
    if n.lower() in ("null", ""):
        return v.replace(",", " ")
    return v + " " + n


r606 = [G.geocodifica(ind606(r)) for r in c606.itertuples()]
c606["esito_geo"] = [r["esito"] for r in r606]
c606["id_nil"] = [r.get("idnil") for r in r606]
c606["nil"] = [r.get("nil") for r in r606]
c606["lon"] = [r.get("lon") for r in r606]
c606["lat"] = [r.get("lat") for r in r606]
LOG["ds606_righe"] = len(c606)
LOG["ds606_geocodifica"] = c606.esito_geo.value_counts().to_dict()
c606["tipo"] = np.where(c606.DENOMINAZIONE.map(sa).str.contains(r"\bFONDAZIONE\b"), "fondazione", "altro")
LOG["ds606_fondazioni"] = int((c606.tipo == "fondazione").sum())
c606.to_csv(os.path.join(PU, "regione_persone_giuridiche_milano.csv"), sep=";", index=False, encoding="utf8")

# ------------------------------------------------------------------ per NIL
nil = pd.read_csv(os.path.join(P, "alberi", "pulito", "nil_alberi.csv"), sep=";")[["id_nil", "nil", "abitanti_2024", "area_km2"]]


def cnt(s):
    s = pd.to_numeric(s, errors="coerce").dropna().astype(int).value_counts()
    return nil.id_nil.map(s).fillna(0).astype(int)


out = nil.copy()
out["associazioni_registro_comune"] = cnt(c1332.id_nil)
out["cooperative_sociali_albo_comune"] = cnt(c562.ID_NIL)
out["persone_giuridiche_regione"] = cnt(c606.id_nil)
out["ong_regione"] = cnt(c596.ID_NIL)
COLS = ["associazioni_registro_comune", "cooperative_sociali_albo_comune", "persone_giuridiche_regione", "ong_regione"]
for c in COLS:
    out[c + "_per_10000"] = (10000 * out[c] / out.abitanti_2024).round(2)
out.to_csv(os.path.join(PU, "nil_terzo_settore.csv"), index=False, encoding="utf8")
LOG["somma_nil"] = {c: int(out[c].sum()) for c in COLS}
LOG["abitanti_nil_2024"] = int(out.abitanti_2024.sum())

# ------------------------------------------------------------------ Bes (provincia) + ISTAT tavola 22 (provincia, 2023)
bes = pd.read_csv(os.path.join(P, "benessere", "pulito", "bes_lungo.csv"), dtype=str)
b = bes[(bes.codice == "05REL008") & (bes.edizione == "2025") & ((bes.citta_metropolitana == "True") | (bes.territorio == "Italia"))]
bp = b.pivot_table(index="territorio", columns="anno", values="valore", aggfunc="first").astype(float)
bp.to_csv(os.path.join(PU, "bes_nonprofit_per_10000_citta_metropolitane.csv"), encoding="utf8")
LOG["bes_milano_2022"] = float(bp.loc["Milano", "2022"])
LOG["bes_italia_2022"] = float(bp.loc["Italia", "2022"])
t22 = pd.read_excel(os.path.join(T, "raw", "istat", "2026-11-02_Tavole_nonprofit_2023.xlsx"), sheet_name=22, header=None, dtype=object).iloc[:, :4]
t22.columns = ["cod", "provincia", "istituzioni", "dipendenti"]
t22 = t22[pd.to_numeric(t22.istituzioni, errors="coerce").notna()].copy()
t22["istituzioni"] = t22.istituzioni.astype(float)
t22["dipendenti"] = t22.dipendenti.astype(float)
t22.to_csv(os.path.join(PU, "istat_nonprofit_province_2023.csv"), index=False, encoding="utf8")
LOG["istat2023_milano_prov"] = t22[t22.provincia == "Milano"][["istituzioni", "dipendenti"]].iloc[0].to_dict()
LOG["istat2023_somma_province"] = {"istituzioni": float(t22.istituzioni.sum()), "dipendenti": float(t22.dipendenti.sum()), "righe": len(t22)}
json.dump(LOG, open(os.path.join(PU, "riepilogo_build.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(LOG, ensure_ascii=False, indent=1, default=str)[:7000])
