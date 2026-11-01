"""Scrive i file dati della pagina "Le antenne dei cellulari" (docs/antenne/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <antenne_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): antenne/pulito/impianti.csv, snapshot_impianti.csv, nil_antenne.csv, gestori.csv, serie_snapshot.csv,
serie_snapshot_gestori_mobile.csv, riepilogo.json, scuole_vicinanza_antenne.csv; i poligoni NIL di citta-15-minuti e
censimenti/pulito/nil_2021_anagrafica.csv (nomi dei NIL).
Scrive in <docs_dir>/antenne/data/: riepilogo.json, siti.json, siti.csv, nil.geojson, nil.csv, gestori.csv, serie_snapshot.csv,
serie_gestori_mobile.csv, scuole_per_ordine.csv.
ds718 e' CC BY: si ripubblicano i siti (posizione + conteggi per categoria), non l'elenco impianto per impianto.
Nessuna misura di campo e nessun dato ARPA a licenza riservata (solo numeri citati nel testo della pagina).
"""
import sys, os, json, csv, math
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping

A, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(A, "pulito")
OUT = os.path.join(DOCS, "antenne", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []


def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
t = pd.read_csv(os.path.join(PU, "impianti.csv"), sep=";", dtype={"cap": str, "id_nil_file": str}, keep_default_na=True)
for c in ("acceso", "previsto", "procedura_scia"):
    t[c] = t[c].astype(bool)
nil = pd.read_csv(os.path.join(PU, "nil_antenne.csv"), sep=";")
ger = pd.read_csv(os.path.join(PU, "gestori.csv"), sep=";")
ser = pd.read_csv(os.path.join(PU, "serie_snapshot.csv"), sep=";")
serg = pd.read_csv(os.path.join(PU, "serie_snapshot_gestori_mobile.csv"), sep=";", index_col=0)
sc = pd.read_csv(os.path.join(PU, "scuole_vicinanza_antenne.csv"), sep=";")

# ---------------------------------------------------------------- categorie
CAT = {"operatore mobile": 0, "societa infrastrutture": 1, "radio e TV": 2}
def cat_idx(c):
    return CAT.get(c, 3)
TIPI = ["Telefonia", "Microcella", "Ponte", "Radiofonia", "Televisione", "Altro"]
def tipo_idx(x):
    return TIPI.index(x) if x in TIPI else 5  # Wireless -> Altro

a = t[t.acceso].copy()
a["ci"] = a.categoria.map(cat_idx)
a["ti"] = a.tipo.map(tipo_idx)

# ---------------------------------------------------------------- nomi NIL
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
nil["nome"] = [nomi.get(int(i)) or str(n).title() for i, n in zip(nil.id_nil, nil.nil)]
NOME = dict(zip(nil.id_nil.astype(int), nil.nome))

# ---------------------------------------------------------------- siti (posizione + conteggi per categoria e tipo)
sit = []
for sid, g in a.dropna(subset=["sito_id"]).groupby("sito_id"):
    k = g.groupby(["ci", "ti"]).size()
    flat = []
    for (c, ti), n in k.items():
        flat += [int(c), int(ti), int(n)]
    gest = g.gruppo_gestore.value_counts()
    gtxt = ", ".join((f"{x} ×{n}" if n > 1 else x) for x, n in gest.head(4).items()) + (f" e altri {len(gest) - 4}" if len(gest) > 4 else "")
    lon, lat = sid.split(",")
    nid = g.id_nil.dropna()
    sit.append({"x": round(float(lon), 5), "y": round(float(lat), 5), "a": str(g.indirizzo.iloc[0]).title().replace(" Di ", " di ").replace(" Del ", " del "),
                "n": int(nid.iloc[0]) if len(nid) else None, "k": flat, "g": gtxt, "t": int(len(g))})
sit.sort(key=lambda s: -s["t"])
json.dump({"categorie": ["Operatori mobili", "Società di infrastrutture", "Radio e TV", "Altro"], "tipi": TIPI, "siti": sit},
          open(os.path.join(OUT, "siti.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
with open(os.path.join(OUT, "siti.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["lon", "lat", "indirizzo", "id_nil", "nil", "impianti_accesi", "operatori_mobili", "societa_infrastrutture", "radio_tv", "altro", "gestori"])
    for s in sit:
        cc = [0, 0, 0, 0]
        for i in range(0, len(s["k"]), 3):
            cc[s["k"][i]] += s["k"][i + 2]
        w.writerow([s["x"], s["y"], s["a"], s["n"] or "", NOME.get(s["n"], ""), s["t"]] + cc + [s["g"]])
check("siti con almeno un impianto acceso", len(sit), RIEP["siti_unici_coordinate_accesi"])
check("impianti accesi con coordinate nei siti", sum(s["t"] for s in sit), int(a.sito_id.notna().sum()))

# ---------------------------------------------------------------- NIL: geometrie e valori
g_ = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in g_["features"]}
def rnd(x):
    return [round(x[0], 5), round(x[1], 5)]
def rcoords(c):
    if isinstance(c[0], (int, float)):
        return rnd(c)
    return [rcoords(i) for i in c]
nil["cl"] = (nil.abitanti_2024 >= 1000).astype(int)
feats = []
for _, r in nil.iterrows():
    i = int(r.id_nil)
    gg = geom[i].simplify(0.00018, preserve_topology=True)
    m = mapping(gg)
    props = {"i": i, "n": r.nome, "ar": round(float(r.area_km2), 3), "ab": int(r.abitanti_2024), "m": int(r.mobile_impianti), "mk": float(r.mobile_per_km2),
             "m1": None if pd.isna(r.mobile_per_1000_ab) or r.cl == 0 else float(r.mobile_per_1000_ab), "ms": int(r.mobile_macro_siti), "mc": int(r.microcelle),
             "rt": int(r.radio_tv_impianti), "ia": int(r.impianti_accesi), "pr": int(r.previsti), "cl": int(r.cl)}
    feats.append({"type": "Feature", "properties": props, "geometry": {"type": m["type"], "coordinates": rcoords(m["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
n2 = nil[["id_nil", "nome", "area_km2", "abitanti_2024", "impianti_accesi", "siti_accesi", "mobile_impianti", "mobile_macro_siti", "microcelle", "radio_tv_impianti", "previsti",
          "mobile_per_km2", "mobile_per_1000_ab", "macro_siti_per_km2", "macro_siti_per_1000_ab", "abitanti_sotto_1000"]].copy()
n2.to_csv(os.path.join(OUT, "nil.csv"), sep=";", index=False, encoding="utf-8")
ger.to_csv(os.path.join(OUT, "gestori.csv"), sep=";", index=False, encoding="utf-8")
ser.to_csv(os.path.join(OUT, "serie_snapshot.csv"), sep=";", index=False, encoding="utf-8")
serg.to_csv(os.path.join(OUT, "serie_gestori_mobile.csv"), sep=";", encoding="utf-8")

# ---------------------------------------------------------------- numeri della pagina
mob = a[(a.categoria.isin(["operatore mobile", "societa infrastrutture"])) & (a.tipo.isin(["Telefonia", "Microcella"]))]
big = nil[nil.abitanti_2024 >= 1000]
def nrow(r, k):
    return {"n": r.nome, "v": float(r[k]), "m": int(r.mobile_impianti), "ab": int(r.abitanti_2024)}
top_km = [nrow(r, "mobile_per_km2") for _, r in nil.sort_values("mobile_per_km2", ascending=False).head(8).iterrows()]
bot_km = [nrow(r, "mobile_per_km2") for _, r in nil[nil.mobile_impianti > 0].sort_values("mobile_per_km2").head(8).iterrows()]
top_ab = [nrow(r, "mobile_per_1000_ab") for _, r in big.sort_values("mobile_per_1000_ab", ascending=False).head(8).iterrows()]
bot_ab = [nrow(r, "mobile_per_1000_ab") for _, r in big.sort_values("mobile_per_1000_ab").head(8).iterrows()]

gru = a.groupby("gruppo_gestore").agg(imp=("id_impianto", "size"), cg=("categoria", "first"), micro=("tipo", lambda s: int((s == "Microcella").sum())),
                                       tel=("tipo", lambda s: int((s == "Telefonia").sum()))).sort_values("imp", ascending=False)
gtab = [{"n": k, "c": cat_idx(r.cg), "imp": int(r.imp), "micro": int(r.micro), "tel": int(r.tel)} for k, r in gru.head(14).iterrows()]
cc = a[a.gruppo_gestore == "CommsCon"]
duomo = a[(a.nil == "DUOMO") & a.categoria.isin(["operatore mobile", "societa infrastrutture"]) & a.tipo.isin(["Telefonia", "Microcella"])]
semp = a[a.sito_id == "9.165719,45.47847"]
potcc = cc.potenza_classe_W.fillna("n.d.").value_counts().to_dict()

# scuole
def share(x, d):
    return round(100 * float((x <= d).mean()), 1)
sv = RIEP["scuole_vs_civici_residenziali_telefonia_mobile"]
svm = RIEP["scuole_vs_civici_residenziali_solo_macro"]
per_ord = []
for o, nm in [("infanzia", "Infanzia"), ("primaria", "Primaria"), ("sec1", "Secondaria di I grado"), ("sec2", "Secondaria di II grado")]:
    x = sc[sc.ordine == o]
    per_ord.append({"o": nm, "n": int(len(x)), "e100": share(x.dist_min_m_telefonia_mobile, 100), "e50": share(x.dist_min_m_telefonia_mobile, 50), "e200": share(x.dist_min_m_telefonia_mobile, 200)})
pd.DataFrame(per_ord).to_csv(os.path.join(OUT, "scuole_per_ordine.csv"), sep=";", index=False, encoding="utf-8")
check("scuole entro 100 m (%)", share(sc.dist_min_m_telefonia_mobile, 100), sv["scuole"]["entro_100m_pct"])
check("scuole totali", len(sc), RIEP["scuole_con_coordinate"])

# flussi e serie
fl = RIEP["flussi_con_id"]
tot_new = None
S = pd.read_csv(os.path.join(PU, "snapshot_impianti.csv"), sep=";", dtype=str, keep_default_na=False)
x23 = set(S[S.snapshot == "2023-01"].id_impianto); x25 = set(S[S.snapshot == "2025-06"].id_impianto)
serie_date = {"2020-21": "2021-01-22", "2023-01": "2023-01-24", "2024-05": "2024-05-15", "2024-06": "2024-06-15", "2025-06": "2025-06-08"}
serie = []
for _, r in ser.iterrows():
    serie.append({"s": r.snapshot, "d": serie_date[r.snapshot], "righe": int(r.righe), "accesi": int(r.accesi), "mob": int(r.telefonia_mobile_accesi), "macro": int(r.macro_Telefonia),
                  "micro": int(r.Microcella), "scia": float(r.scia_su_accesi_pct)})
sg = {k: {s: int(v) for s, v in serg[k].items()} for k in serg.columns}
mob_gest = {k: int(v) for k, v in mob.gruppo_gestore.value_counts().items()}

R = {
    "scaricato": "2026-11-01",
    "citta": {"impianti": int(len(t)), "accesi": int(t.acceso.sum()), "previsti": int(t.previsto.sum()), "siti_accesi": len(sit), "senza_coordinate": int(t.lon.isna().sum()),
              "mobile": int(len(mob)), "macro": int((mob.tipo == "Telefonia").sum()), "micro": int((mob.tipo == "Microcella").sum()), "macro_siti": RIEP["telefonia_mobile_macro_siti_unici"],
              "mobile_siti": RIEP["telefonia_mobile_siti_unici"], "area_km2": RIEP["nil_area_totale_km2"], "abitanti": RIEP["abitanti_2024"],
              "per_km2": RIEP["citta_mobile_per_km2"], "per_1000": RIEP["citta_mobile_per_1000_ab"], "macro_per_km2": RIEP["citta_macro_siti_per_km2"], "macro_per_1000": RIEP["citta_macro_siti_per_1000_ab"],
              "mediana_km2": RIEP["nil_mediana_mobile_per_km2"], "mediana_1000": RIEP["nil_mediana_mobile_per_1000_ab"], "rapporto_1000": RIEP["nil_ratio_max_min_per_1000_ab_(>=1000 ab, esclusi_zero)"],
              "nil_con_impianti": int((nil.impianti_accesi > 0).sum()), "nil_senza": [NOME[int(i)] for i in nil[nil.impianti_accesi == 0].id_nil],
              "categorie_accesi": {k: int(v) for k, v in a.categoria.value_counts().items()}, "tipi_accesi": {k: int(v) for k, v in a.tipo.value_counts().items()},
              "microcelle_infra_pct": RIEP["quota_microcelle_gestite_da_societa_infrastrutture_pct"], "colocazione": RIEP["colocazione_distribuzione_impianti_per_sito"],
              "macro_n_operatori": RIEP["siti_macro_telefonia_con_n_operatori"], "corr_spearman_densita": RIEP["nil_correlazione_mobile_vs_densita_abitanti_spearman"]},
    "gestori": gtab, "mobile_per_gestore": mob_gest,
    "commscon": {"impianti_accesi": int(len(cc)), "micro": int((cc.tipo == "Microcella").sum()), "previsti": int(t[(t.gruppo_gestore == "CommsCon")].previsto.sum()),
                 "scia": int(cc.procedura_scia.sum()), "potenza": potcc, "nil_top": cc.nil.value_counts().head(4).to_dict(),
                 "duomo_micro": int((duomo.tipo == "Microcella").sum()), "duomo_mobile": int(len(duomo)), "windtre_tutti": int(ger[ger.gruppo_gestore == "WindTre"].impianti.iloc[0]),
                 "iliad_tutti": int(ger[ger.gruppo_gestore == "Iliad"].impianti.iloc[0]), "commscon_tutti": int(ger[ger.gruppo_gestore == "CommsCon"].impianti.iloc[0])},
    "sempione": {"impianti": int(len(semp)), "radio_tv": int((semp.categoria == "radio e TV").sum()), "indirizzo": "Corso Sempione 27", "nil": NOME[int(semp.id_nil.iloc[0])]},
    "top_km2": top_km, "bot_km2": bot_km, "top_1000": top_ab, "bot_1000": bot_ab,
    "nil_sotto_1000": [{"n": NOME[int(r.id_nil)], "ab": int(r.abitanti_2024), "m": int(r.mobile_impianti)} for _, r in nil[nil.abitanti_2024 < 1000].iterrows()],
    "serie": serie, "serie_gestori": sg,
    "tra_2023_2025": {"mob_2023": serie[1]["mob"], "mob_2025": serie[-1]["mob"], "macro_2023": serie[1]["macro"], "macro_2025": serie[-1]["macro"], "micro_2023": serie[1]["micro"], "micro_2025": serie[-1]["micro"],
                      "codici_nuovi": len(x25 - x23), "codici_spariti": len(x23 - x25), "codici_2023": len(x23), "cambi_stato_giu24_giu25": fl[2]["cambi_di_stato"],
                      "nuovi_gen23_mag24": fl[0]["nuovi_per_gestore"], "nuovi_giu24_giu25": fl[2]["nuovi_per_gestore"]},
    "approx_2020_2023": RIEP["approx_2020_2023"],
    "scuole": {"n": RIEP["scuole_con_coordinate"], "per_ordine": per_ord, "scuole": sv["scuole"], "civici": sv["civici_residenziali"], "scuole_macro": svm["scuole"], "civici_macro": svm["civici_residenziali"],
               "entro_20m_n": RIEP["scuole_entro_20m_n"], "entro_50m_n": RIEP["scuole_entro_50m_n"], "entro_100m_n": RIEP["scuole_entro_100m_n"],
               "casuali_100m": RIEP["campioni_casuali_di_civici_entro_100m_pct"]},
    "stati": {"scia_pct_accesi": [s["scia"] for s in serie], "incoerenza_grave": int((t.segnalazione_parere == "incoerenza grave").sum()),
              "parere_non_rispetto": int((t.segnalazione_parere == "ultimo parere: non rispetto limiti").sum()), "parere_negativo": int((t.segnalazione_parere == "ultimo parere negativo").sum())},
    "legge": {"esposizione_3MHz_3GHz": 20, "attenzione_dal_2024": 15, "attenzione_prima": 6, "fonte": "L. 30/12/2023 n. 214, art. 10, comma 2 (Normattiva); MIMIT, La Comunicazione n. 71/2026"},
    "arpa_regionale_2018": {"misure": 887, "sotto3": 92, "da3a6": 7, "da6a20": 1},
}
check("mobile accesi", R["citta"]["mobile"], RIEP["telefonia_mobile_accesi_impianti"])
check("CommsCon tutti", R["commscon"]["commscon_tutti"], 373)
check("Sempione impianti", R["sempione"]["impianti"], 84)
check("Sempione radio TV", R["sempione"]["radio_tv"], 82)
check("serie 2025 mob", serie[-1]["mob"], 2097)
check("serie 2023 mob", serie[1]["mob"], 1964)
check("codici nuovi 2023->2025", R["tra_2023_2025"]["codici_nuovi"], 257)
check("codici spariti 2023->2025", R["tra_2023_2025"]["codici_spariti"], 120)
json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
print("AVVISI:", AVVISI or "nessuno")
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
sys.exit(1 if AVVISI else 0)
