"""Prepara i dati della pagina docs/ristoranti/ (sola lettura su pulito/, scrive solo in docs/ristoranti/data/).
Uso: python -I -X utf8 pagina.py <ristoranti_abs> <docs_ristoranti_data_abs>
Pubblica: punti OSM (nome, tipo, cucina, lon/lat: ODbL, share-alike) e punti delle pratiche ds58 SENZA insegna ne' indirizzo (CC BY).
Non pubblica: insegne del registro (potrebbero contenere nomi di persona), indirizzi, uid/changeset OSM."""
import sys, os, json, re
import numpy as np, pandas as pd

R, OUT = sys.argv[1], sys.argv[2]
PUL = os.path.join(R, "pulito")
os.makedirs(OUT, exist_ok=True)


def rd(fn, **k):
    return pd.read_csv(os.path.join(PUL, fn), sep=";", encoding="utf-8-sig", low_memory=False, **k)


def wj(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


FJ = json.load(open(os.path.join(PUL, "freschezza.json"), encoding="utf-8"))
CJ = json.load(open(os.path.join(PUL, "controlli.json"), encoding="utf-8"))
BJ = json.load(open(os.path.join(PUL, "build_log.json"), encoding="utf-8"))
loc = rd("locali.csv")
nilc = rd("nil_locali_per_1000ab.csv")
cuc = rd("nil_cucine.csv")
chg = rd("registro_2019_2026_nil.csv")
conf = rd("confronto_nil.csv")
osmp = rd("osm_poi.csv")

SOGLIA_PICCOLO = 3000
MIN_CUCINA = 20
TIPI = [("restaurant", "Ristorante"), ("fast_food", "Fast food e asporto"), ("cafe", "Caffè"), ("bar", "Bar"), ("pub", "Pub"), ("ice_cream", "Gelateria")]
GRUPPI = [("pizza", "Pizza"), ("italiana", "Italiana"), ("giapponese_sushi", "Giapponese e sushi"), ("cinese", "Cinese"), ("altro_asiatico", "Altra asiatica"), ("indiana_sudasiatica", "Indiana e sud-asiatica"),
          ("kebab_medio_oriente", "Kebab e Medio Oriente"), ("latinoamericana", "Latinoamericana"), ("africana", "Africana"), ("hamburger_panini", "Hamburger e panini"), ("pesce", "Pesce"),
          ("carne_griglia", "Carne e griglia"), ("altre_europee", "Altre europee"), ("dolci_caffe", "Dolci e caffetteria"), ("veg_insalate_poke", "Vegetariana, insalate, poke"), ("fusion_internazionale", "Fusion e internazionale")]
ETNICHE = ["giapponese_sushi", "cinese", "altro_asiatico", "indiana_sudasiatica", "kebab_medio_oriente", "latinoamericana", "africana"]
tk = [t for t, _ in TIPI]; gk = [g for g, _ in GRUPPI]

# ---------- mappa OSM
o = loc[(loc.fonte == "osm") & loc.tipo.isin(tk)].copy()
o["cucina_gruppi"] = o.cucina_gruppi.fillna("")
pts = []
for r in o.itertuples():
    gs = [gk.index(g) for g in r.cucina_gruppi.split("|") if g in gk]
    pts.append([round(r.lon, 5), round(r.lat, 5), tk.index(r.tipo), gs, r.nome if isinstance(r.nome, str) else "", r.cucina if isinstance(r.cucina, str) else ""])
wj("locali_osm.json", {"tipi": [x for _, x in TIPI], "gruppi": [x for _, x in GRUPPI], "p": pts})
pub = o[["id", "nome", "tipo", "cucina", "lon", "lat", "nil", "ultima_modifica"]].rename(columns={"id": "osm_id"})
pub.to_csv(os.path.join(OUT, "locali_osm.csv"), sep=";", index=False, encoding="utf-8-sig")

# ---------- pratiche del registro (solo punti e tipo)
TREG = [("ristorante_trattoria", "Ristorante, trattoria"), ("ristorante_tipico", "Ristorante, cucina tipica"), ("pizzeria", "Pizzeria"), ("tavola_calda_fastfood", "Tavola calda, fast food"),
        ("bar_caffe", "Bar caffè"), ("bar_gastronomico", "Bar gastronomico"), ("bar_pasticceria_gelateria", "Bar pasticceria, gelateria"), ("wine_bar_pub", "Wine bar, pub, birreria"),
        ("disco_bar_serale", "Disco bar, locale serale"), ("non_classificato", "Tipo non indicato")]
trk = [t for t, _ in TREG]
r58 = loc[loc.fonte == "comune_ds58"]
wj("pratiche_ds58.json", {"tipi": [x for _, x in TREG], "p": [[round(r.lon, 5), round(r.lat, 5), trk.index(r.tipo)] for r in r58.itertuples()]})

# ---------- NIL: locali per 1000 abitanti
n = nilc.copy()
n["piccolo"] = (n.abitanti_2024 < SOGLIA_PICCOLO).astype(int)
n = n.rename(columns={"registro_in_piano_ds58": "pratiche_in_piano", "registro_fuori_piano_ds59": "pratiche_fuori_piano", "registro_artigianato_ds250": "pratiche_artigianato_alim",
                      "osm_6tipi": "locali_osm", "ds58_per_1000ab": "in_piano_per_1000ab", "osm_per_1000ab": "osm_per_1000ab", "ds58_per_km2": "in_piano_per_km2", "rapporto_osm_su_ds58": "osm_su_registro"})
n = n[["id_nil", "nil", "abitanti_2024", "area_km2", "pratiche_in_piano", "pratiche_fuori_piano", "pratiche_artigianato_alim", "locali_osm", "in_piano_per_1000ab", "osm_per_1000ab", "in_piano_per_km2", "osm_su_registro", "piccolo"]]
n.to_csv(os.path.join(OUT, "nil.csv"), sep=";", index=False, encoding="utf-8-sig")
nil_rows = [[int(r.id_nil), r.nil, int(r.abitanti_2024), int(r.pratiche_in_piano), None if pd.isna(r.in_piano_per_1000ab) else float(r.in_piano_per_1000ab), int(r.locali_osm),
             None if pd.isna(r.osm_per_1000ab) else float(r.osm_per_1000ab), int(r.piccolo)] for r in n.itertuples()]

# ---------- cucine: citta' e per NIL
rf = loc[(loc.fonte == "osm") & loc.tipo.isin(["restaurant", "fast_food"])].copy()
rf["cucina_gruppi"] = rf.cucina_gruppi.fillna("")
rfc = rf[rf.cucina_gruppi != ""].copy()
for g in gk:
    rfc[g] = rfc.cucina_gruppi.str.split("|").map(lambda x: g in x)
rfc["etnica"] = rfc[ETNICHE].any(axis=1)
N_C = len(rfc)
citta_mix = [[GRUPPI[i][1], int(rfc[g].sum()), round(100 * rfc[g].mean(), 1)] for i, g in enumerate(gk)]
etn_citta = round(100 * rfc.etnica.mean(), 1)
nil_names = dict(zip(nilc.id_nil, nilc.nil))
c20 = cuc[cuc.n_con_cucina >= MIN_CUCINA].copy()
mix_nil = []
for r in c20.itertuples():
    sub = rfc[rfc.id_nil == r.id_nil]
    mix_nil.append({"id": int(r.id_nil), "nil": r.nil, "n": int(len(sub)), "n_rf": int(r.n_rist_fast_osm), "etn": round(100 * sub.etnica.mean(), 1), "g": [int(sub[g].sum()) for g in gk]})
mix_nil.sort(key=lambda x: x["nil"])
cuc[["id_nil", "nil", "n_rist_fast_osm", "n_con_cucina", "pct_con_cucina"] + [f"{g}_pct" for g in gk]].to_csv(os.path.join(OUT, "nil_cucine.csv"), sep=";", index=False, encoding="utf-8-sig")

# ---------- concentrazione (indice di localizzazione), solo NIL con 15+ locali con cucina e almeno 3 locali del gruppo
LQ = []
for g in ["cinese", "giapponese_sushi", "indiana_sudasiatica", "kebab_medio_oriente", "latinoamericana", "altro_asiatico", "pizza", "pesce"]:
    ng = int(rfc[g].sum()); sh = ng / N_C
    by = rfc.groupby("id_nil")[g].agg(["sum", "size"])
    by = by[(by["size"] >= 15) & (by["sum"] >= 3)]
    by["lq"] = (by["sum"] / by["size"]) / sh
    top = by.sort_values("lq", ascending=False).head(4)
    top5n = rfc.groupby("id_nil")[g].sum().sort_values(ascending=False).head(5)
    LQ.append({"g": GRUPPI[gk.index(g)][1], "n": ng, "quota": round(100 * sh, 1), "quota_primi5": round(100 * top5n.sum() / ng, 1),
               "top": [{"nil": nil_names[i], "lq": round(float(r.lq), 1), "k": int(r["sum"]), "n": int(r["size"])} for i, r in top.iterrows()]})

# ---------- cambiamento registro 2019-2026
ch = chg.copy()
ch = ch[ch.registro_2019 >= 40].copy()
ch_rows = [[int(r.id_nil), r.nil, int(r.registro_2019), int(r.registro_2026), float(r.variazione_pct)] for r in ch.sort_values("variazione_pct", ascending=False).itertuples()]
chg.to_csv(os.path.join(OUT, "pratiche_2019_2026_nil.csv"), sep=";", index=False, encoding="utf-8-sig")
RG = BJ["registro_2019_2026"]

# ---------- la cucina milanese
mil = rd("locali_milanesi.csv")
mil_rows = [[r.nome if isinstance(r.nome, str) else "", r.tipo, r.cucina if isinstance(r.cucina, str) else "", r.nil, bool(r.milanese_cucina)] for r in mil.itertuples()]
mil[["id", "nome", "tipo", "cucina", "nil", "ultima_modifica"]].to_csv(os.path.join(OUT, "locali_milanesi.csv"), sep=";", index=False, encoding="utf-8-sig")

# ---------- sorpresa: NoLo e Sarpi
def nil_info(name):
    r = cuc[cuc.nil == name].iloc[0]
    sub = rfc[rfc.nil == name]
    return {"nil": name, "n": int(r.n_con_cucina), "etn": int(sub.etnica.sum()), "etn_pct": round(100 * sub.etnica.mean(), 1),
            "gruppi_ge3": [GRUPPI[i][1] for i, g in enumerate(gk) if g in ETNICHE and sub[g].sum() >= 3],
            "dett": {GRUPPI[i][1]: int(sub[g].sum()) for i, g in enumerate(gk) if g in ETNICHE and sub[g].sum() >= 3}}
nolo = nil_info("LORETO - CASORETTO - NOLO"); sarpi = nil_info("SARPI")
sarpi_est = int(rfc[rfc.nil == "SARPI"][["cinese", "giapponese_sushi", "altro_asiatico"]].any(axis=1).sum())
nolo_est = int(rfc[rfc.nil == "LORETO - CASORETTO - NOLO"][["cinese", "giapponese_sushi", "altro_asiatico"]].any(axis=1).sum())

# ---------- freschezza
F6 = FJ["freschezza_osm"]["SEI_tipi_(rist,fast,cafe,bar,pub,gelato)"]
rec = osmp[pd.to_datetime(osmp.timestamp, utc=True) >= "2025-01-01"]
top5 = rec.uid.value_counts().head(5).index
osm6 = osmp[osmp.amenity.isin(tk)]
senza_top5 = round(100 * ((osm6.eta_anni <= 3) & ~osm6.uid.isin(top5)).sum() / len(osm6), 1)
fresh = {
    "osm_n": int(F6["n"]), "osm_1a": F6["modificati_ultimi_1_anni_pct"], "osm_2a": F6["modificati_ultimi_2_anni_pct"], "osm_3a": F6["modificati_ultimi_3_anni_pct"], "osm_5a": F6["modificati_ultimi_5_anni_pct"],
    "osm_mediana_eta": F6["mediana_eta_anni"], "osm_cd_pct": F6["con_check_date_pct"], "osm_cd_3a_pct": F6["check_date_ultimi_3_anni_pct"], "osm_cd_12m_n": CJ["check_date_ultimi_12_mesi_n"],
    "osm_cucina_pct": F6["con_cuisine_pct"], "osm_orari_pct": F6["con_opening_hours_pct"], "osm_indirizzo_pct": F6["con_indirizzo_pct"],
    "rist_fast_cucina_pct": BJ["rist_fast_osm"]["con_cuisine_pct"],
    "reg_ds58": int(BJ["citta"]["ds58"]), "reg_ds58_file": 9269, "reg_ds59_file": 3799, "reg_ds250_file": 1471, "osm_su_registro_pct": round(100 * FJ["rapporto_osm6_su_ds58"], 1),
    "nil_tot": FJ["NIL_reg_ds58"]["totali"], "nil_20": FJ["NIL_reg_ds58"]["entro_20pct"], "nil_30": FJ["NIL_reg_ds58"]["entro_30pct"], "nil_50": FJ["NIL_reg_ds58"]["entro_50pct"],
    "nil_mediana_diff": FJ["NIL_reg_ds58"]["mediana_diff_pct"], "nil_correlazione": FJ["NIL_reg_ds58"]["correlazione"],
    "nil_rel_20": CJ["NIL_rapporto_relativo_reg_ds58"]["entro_20pct_dal_rapporto_di_citta"], "nil_rel_tot": CJ["NIL_rapporto_relativo_reg_ds58"]["NIL_con_almeno_20_nel_registro"],
    "mod_2526_n": CJ["modifiche_2025_26"]["n"], "mod_2526_utenti": CJ["modifiche_2025_26"]["utenti_distinti"], "mod_top1": CJ["modifiche_2025_26"]["top1_pct"], "mod_top5": CJ["modifiche_2025_26"]["top5_pct"],
    "osm_3a_senza_top5": senza_top5,
    "campione_100": FJ["campione100_restaurant"]["match_50m"], "campione_100_25m": 88, "indirizzo_ritrovato_pct": CJ["osm6_con_indirizzo"]["indirizzo_trovato_nel_registro_pct"], "indirizzo_n": CJ["osm6_con_indirizzo"]["n"],
    "match_25m_pct": CJ["match_osm6_entro_25m_pct"], "match_50m_pct": CJ["match_osm6_entro_50m_pct"], "nullo_25m_pct": CJ["controllo_nullo_spostati_150_400m_entro_25m_pct"], "nullo_50m_pct": CJ["controllo_nullo_spostati_150_400m_entro_50m_pct"],
    "chiusi_n": CJ["osm_chiusi"]["senza_altro_food_attivo_entro_20m"], "chiusi_nel_registro": CJ["osm_chiusi"]["di_cui_ancora_nel_registro_entro_25m"],
    "nuovi_2026_n": CJ["osm6_nuovi_2026_(versione_1)"]["n"], "nuovi_2026_senza": CJ["osm6_nuovi_2026_(versione_1)"]["senza_registro_entro_50m"],
    "reg_codici_2019": RG["2019_righe"], "reg_codici_comuni": RG["codici_in_comune"], "reg_codici_spariti": RG["codici_scomparsi"], "reg_codici_nuovi": RG["codici_nuovi"],
    "reg_nuovi_stesso_indirizzo_pct": RG["codici_nuovi_con_indirizzo_gia_presente_2019_pct"], "reg_spariti_stesso_indirizzo_pct": RG["codici_scomparsi_con_indirizzo_ancora_presente_pct"],
    "reg_indirizzi_spariti": RG["indirizzi_scomparsi"], "reg_indirizzi_nuovi": RG["indirizzi_nuovi"],
    "anno_modifica": FJ["osm_anno_ultima_modifica"],
}
tipo_cnt = {x: int((o.tipo == x).sum()) for x in tk}
reg_tipi = {TREG[trk.index(k)][1]: int(v) for k, v in r58.tipo.value_counts().items()}
cit = BJ["citta"]
RI = {
    "generato": "2026-11-01", "osm_base": FJ["osm_timestamp_base"],
    "fresh": fresh, "citta": {"abitanti": cit["abitanti_2024"], "osm_per_1000": cit["osm_per_1000ab"], "in_piano_per_1000": cit["ds58_per_1000ab"], "piano_e_fuori_per_1000": cit["ds58_59_per_1000ab"],
                              "osm_6tipi": cit["osm_6tipi"], "in_piano": cit["ds58"]},
    "tipi_osm": {TIPI[tk.index(k)][1]: v for k, v in tipo_cnt.items()}, "tipi_registro": reg_tipi,
    "cucine": {"n": N_C, "n_rist_fast": int(len(rf)), "mix": citta_mix, "etniche_pct": etn_citta, "min_cucina_nil": MIN_CUCINA, "nil_ammessi": len(mix_nil)},
    "sorpresa": {"nolo": nolo, "sarpi": sarpi, "sarpi_asia_orientale": sarpi_est, "nolo_asia_orientale": nolo_est},
    "lq": LQ, "mix_nil": mix_nil, "nil": nil_rows, "soglia_piccolo": SOGLIA_PICCOLO,
    "cambi": {"rows": ch_rows, "n_2019": RG["2019_righe"], "n_2026": RG["2026_righe"]},
    "milanesi": {"rows": mil_rows, "con_tag": BJ["milanesi"]["con_tag_cuisine_milanese_lombard_risotto_cotoletta"], "regional_n": BJ["cucina_regional_n"], "tot": len(mil_rows),
                 "trattoria_osteria_nel_nome": BJ["ristoranti_OSM_con_Trattoria_o_Osteria_nel_nome"]["n"]},
    "origine": {"osm_*": "ristoranti/pulito/freschezza.json, controlli.json, osm_poi.csv (Overpass 1/11/2026)", "reg_*": "ristoranti/pulito/build_log.json, registro.csv (ds58, ds59, ds250 scaricati 1/11/2026)",
                "nil": "ristoranti/pulito/nil_locali_per_1000ab.csv (abitanti ds205 2024)", "cucine": "ristoranti/pulito/locali.csv (cucina_gruppi) - ristoranti e fast food OSM con cucina nota",
                "lq": "indice di localizzazione = quota del gruppo nel NIL / quota nella citta'; solo NIL con 15+ locali con cucina e almeno 3 del gruppo", "cambi": "ristoranti/pulito/registro_2019_2026_nil.csv"},
}
wj("riepilogo.json", RI)
sz = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("file:", sorted(os.listdir(OUT)), "totale byte", sz)
print("mix_nil ammessi:", len(mix_nil), "| NoLo", nolo, "| Sarpi", sarpi, sarpi_est, nolo_est, "| senza top5", senza_top5)
