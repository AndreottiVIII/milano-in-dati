"""Scrive i file dati della pagina "Povertà educativa" (docs/poverta-educativa/data/).

Uso (percorsi assoluti, si può rilanciare):
  python -I -X utf8 pagina.py <poverta-educativa_dir> <milano-in-dati_dir> <docs_dir>

Legge: poverta-educativa/pulito/*.csv (scritti da build.py), controlli_build.json, il file dei poligoni NIL di citta-15-minuti.
Scrive in <docs_dir>/poverta-educativa/data/: dati.json (tutte le tabelle della pagina), riepilogo.json (numeri citati nel testo, con origine),
nil.geojson (88 quartieri semplificati, con i valori), e copie dei CSV aggregati.
Solo valori aggregati (per città, per quartiere, per CAP): nessuna scuola o sede di nido singola.
"""
import sys, os, json, shutil
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

PE, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(PE, "pulito")
OUT = os.path.join(DOCS, "poverta-educativa", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []

def check(nome, calcolato, atteso, tol=0.0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

def rd(f): return pd.read_csv(os.path.join(PU, f), sep=";")
def nn(x, d=1):
    if x is None or (isinstance(x, float) and np.isnan(x)): return None
    return round(float(x), d)
def rec(df, cols, d=1):
    return [[nn(v, d) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (np.integer,)) else v) for v in row] for row in df[cols].itertuples(index=False, name=None)]

CTR = json.load(open(os.path.join(PU, "controlli_build.json"), encoding="utf8"))["controlli"]
RIEP = {"origine": {}}
def put(k, v, origine):
    RIEP[k] = v; RIEP["origine"][k] = origine

# ---------------------------------------------------------------- nidi
n6 = rd("nidi_6citta_serie.csv"); n14 = rd("nidi_14citta_italia_serie.csv")
SEI = ["Milano", "Roma", "Torino", "Napoli", "Bologna", "Firenze"]
nid = {c: rec(n6[n6.area == c].sort_values("anno"), ["anno", "p100_tot", "p100_pub", "p100_priv", "posti_tot", "posti_pub", "posti_priv", "servizi_tot", "servizi_priv", "utenti_servizi_comuni", "utenti_servizi_comuni_per100"]) for c in SEI}
r24 = n14[n14.anno == 2024].sort_values("p100_tot", ascending=False)
rank24 = rec(r24, ["area", "p100_tot", "posti_tot"])
ser14 = {a: rec(g.sort_values("anno"), ["anno", "p100_tot"]) for a, g in n14.groupby("area")}
m24 = n6[(n6.area == "Milano") & (n6.anno == 2024)].iloc[0]
put("nidi_milano_p100_2024", nn(m24.p100_tot), "ISTAT IstatData 47_850_DF_DCIS_SERVSOCEDU1_6, DATA_TYPE P_100CH_Y0_2, titolare 9 (totale), anno 2024")
put("nidi_milano_posti_2024", int(m24.posti_tot), "stesso flusso, DATA_TYPE AUTP")
put("nidi_milano_p100_pub_2024", nn(m24.p100_pub), "stesso flusso, titolare 2 (pubblico)")
put("nidi_milano_p100_priv_2024", nn(m24.p100_priv), "stesso flusso, titolare 1 (privato)")
put("nidi_milano_quota_privati_2024", nn(m24.quota_posti_privati_pct), "posti privati / posti totali, stesso flusso")
put("nidi_italia_p100_2024", nn(r24[r24.area == "Italia"].p100_tot.iloc[0]), "stesso flusso, REF_AREA IT")
put("nidi_lombardia_p100_2024", nn(r24[r24.area == "Lombardia"].p100_tot.iloc[0]), "stesso flusso, REF_AREA ITC4")
put("nidi_milano_bambini_0_2_istat_2024", int(m24.bambini_0_2_impliciti), "posti AUTP / posti per 100 bambini x 100 (denominatore implicito ISTAT)")
put("milano_0_2_ds27_2024", CTR["milano_0_2"]["comune_ds27_2024"], "Comune di Milano ds27, residenti 0-2 anni, anno 2024 (via scuole/pulito/residenti_nil_fascia_cittadinanza_ds27.csv)")
put("milano_0_2_ds27_2013", int(0), "")  # riempito sotto
mil_users = n6[n6.area == "Milano"].set_index("anno")
r27 = pd.read_csv(os.path.join(P, "scuole", "pulito", "residenti_nil_fascia_cittadinanza_ds27.csv"), sep=";")
r02 = r27[r27.fascia_eta == "0-2"].assign(t=lambda x: x.stranieri + x.italiani).groupby("anno").t.sum()
RIEP["milano_0_2_ds27_2013"] = int(r02[2013]); RIEP["origine"]["milano_0_2_ds27_2013"] = "Comune di Milano ds27, residenti 0-2 anni, 2013"
put("milano_0_2_calo_2013_2024_pct", nn(100 * (r02[2024] / r02[2013] - 1)), "ds27: (0-2 anni 2024 / 2013 - 1)")
put("milano_utenti_servizi_comune_2013", int(mil_users.loc[2013, "utenti_servizi_comuni"]), "ISTAT DF_DCIS_SERVSOCEDU1_3, DATA_TYPE USSSPM (utenti dei servizi offerti dai comuni), 2013")
put("milano_utenti_servizi_comune_2024", int(mil_users.loc[2024, "utenti_servizi_comuni"]), "stesso, 2024")
ut_per100 = {int(a): nn(100 * mil_users.loc[a, "utenti_servizi_comuni"] / r02[a]) for a in mil_users.index}
put("milano_utenti_per100_0_2_ds27", ut_per100, "utenti dei servizi del Comune / residenti 0-2 (ds27) x 100, per anno")

# jump di Milano
mm = n6[n6.area == "Milano"].set_index("anno")
put("milano_salti_serie", {"posti_pubblici_2019": int(mm.loc[2019, "posti_pub"]), "posti_pubblici_2020": int(mm.loc[2020, "posti_pub"]),
                           "posti_privati_2021": int(mm.loc[2021, "posti_priv"]), "posti_privati_2022": int(mm.loc[2022, "posti_priv"]),
                           "servizi_privati_2021": int(mm.loc[2021, "servizi_priv"]), "servizi_privati_2022": int(mm.loc[2022, "servizi_priv"]),
                           "p100_2019": nn(mm.loc[2019, "p100_tot"]), "p100_2021": nn(mm.loc[2021, "p100_tot"]), "p100_2022": nn(mm.loc[2022, "p100_tot"])},
    "ISTAT DF_DCIS_SERVSOCEDU1_6, Milano, anni indicati")

# sedi per municipio (Comune ds47, 2018/19)
mun = rd("nidi_milano_municipi_2018_19.csv")
sedi_tot = int(mun.sedi.sum())
put("ds47_sedi_2018_19", sedi_tot, "Comune di Milano ds47, sedi distinte 2018/19 (una riga per fascia d'età, sedi contate una volta)")
put("ds47_sedi_comunali_2018_19", int(mun.comunali.sum()), "ds47, TIPO_STRUTTURA che comincia con 'Comunale'")
put("ds47_senza_posizione_2018_19", CTR["ds47_sedi_senza_posizione_2018_19"], "ds47, righe senza LONG/LAT")
put("ds47_municipio_max", [int(mun.loc[mun.sedi_per_1000_0_2.idxmax(), "municipio"]), nn(mun.sedi_per_1000_0_2.max(), 1)], "ds47 / residenti 0-2 2018 (ds27, NIL per municipio prevalente)")
put("ds47_municipio_min", [int(mun.loc[mun.sedi_per_1000_0_2.idxmin(), "municipio"]), nn(mun.sedi_per_1000_0_2.min(), 1)], "idem")
mun_rec = rec(mun, ["municipio", "sedi", "comunali", "private", "res_0_2_2018", "sedi_per_1000_0_2"], 2)
put("spearman_nil_sedi_nido_reddito", CTR["spearman_nil_sedi_nido_reddito"], "build.py: sedi di nido per 1.000 bambini 0-2 (NIL con almeno 150 bambini) contro reddito stimato del NIL; [rho, p, n NIL, [IC95 basso, alto]]")

# ---------------------------------------------------------------- tempo pieno
tp = rd("tempo_pieno_primaria_citta_serie.csv")
tps = {}
for c in SEI + ["Italia"]:
    tps[c] = {g: rec(tp[(tp.citta == c) & (tp.gestione == g)].sort_values("anno"), ["anno", "alunni", "tempo_pieno_pct"]) for g in ("totale", "statale", "paritaria")}
t24 = tp[(tp.anno == 2024)].pivot_table(index="citta", columns="gestione", values="tempo_pieno_pct")
t15 = tp[(tp.anno == 2015) & (tp.gestione == "totale")].set_index("citta").tempo_pieno_pct
a24 = tp[(tp.anno == 2024)].pivot_table(index="citta", columns="gestione", values="alunni")
tp14 = [[c, nn(t24.loc[c, "totale"]), nn(t24.loc[c, "statale"]), nn(t24.loc[c, "paritaria"]), nn(t15[c]), int(a24.loc[c, "totale"])] for c in t24.sort_values("totale", ascending=False).index if c != "Italia, altri comuni"]
put("tp_milano_2024_tot", nn(t24.loc["Milano", "totale"], 1), "MIM DS0090+DS0100, primaria, tempo pieno / alunni, statale + paritaria, a.s. 2024/25, scuole nel comune di Milano")
put("tp_milano_2015_tot", nn(t15["Milano"], 1), "idem, a.s. 2015/16")
put("tp_milano_2024_statale", nn(t24.loc["Milano", "statale"], 1), "idem, solo statali")
put("tp_milano_2024_paritaria", nn(t24.loc["Milano", "paritaria"], 1), "idem, solo paritarie")
put("tp_italia_2024_tot", nn(t24.loc["Italia", "totale"], 1), "idem, tutta Italia")
put("tp_italia_2015_tot", nn(t15["Italia"], 1), "idem, a.s. 2015/16")
put("tp_alunni_milano_2024", int(a24.loc["Milano", "totale"]), "idem, alunni primaria (statale+paritaria)")
put("tp_alunni_milano_2024_statale", int(a24.loc["Milano", "statale"]), "idem")
put("tp_alunni_milano_2024_paritaria", int(a24.loc["Milano", "paritaria"]), "idem")
tpst = t24.statale.drop(["Italia", "Italia, altri comuni"]).sort_values(ascending=False)
put("tp_statale_milano_primo", bool(tpst.index[0] == "Milano"), "Milano ha la quota di tempo pieno nelle statali più alta tra le 14 città")
put("tp_statale_seconda", [tpst.index[1], nn(tpst.iloc[1])], "idem")
put("tp_nil_statali_unita_sotto_50", [CTR["milano_statali_unita_sotto_50pct_tp"], CTR["milano_statali_unita"]], "build.py: unità statali di Milano con meno del 50% di alunni a tempo pieno, su tutte le unità statali di primaria (a.s. 2024/25)")

# ---------------------------------------------------------------- mensa
me = rd("mensa_primaria_statale_2024_25_citta.csv")
mensa = rec(me.sort_values("pct_alunni_in_scuole_con_mensa", ascending=False), ["citta", "pct_alunni_in_scuole_con_mensa", "alunni", "pct_alunni_scuole_non_nel_file_edilizia"])
mi = me.set_index("citta")
put("mensa_milano_pct", nn(mi.loc["Milano", "pct_alunni_in_scuole_con_mensa"]), "MIM edilizia scolastica statale (ambienti funzionali), a.s. 2024/25: alunni di primaria statale in scuole con almeno un edificio con spazio mensa / alunni; alunni da DS0090")
put("mensa_napoli_pct", nn(mi.loc["Napoli", "pct_alunni_in_scuole_con_mensa"]), "idem")
put("mensa_roma_pct", nn(mi.loc["Roma", "pct_alunni_in_scuole_con_mensa"]), "idem")
put("mensa_italia_pct", nn(mi.loc["Italia", "pct_alunni_in_scuole_con_mensa"]), "idem")
put("mensa_milano_non_nel_file_pct", nn(mi.loc["Milano", "pct_alunni_scuole_non_nel_file_edilizia"]), "idem: scuole di Milano che non compaiono nel file edilizia")

# ---------------------------------------------------------------- INVALSI
iv = rd("invalsi_dispersione_citta_serie.csv")
IV = {}
for g in (8, 13):
    IV[str(g)] = {c: rec(iv[(iv.citta == c) & (iv.grado == g)].sort_values("anno"), ["anno", "disp", "ecc"]) for c in SEI + ["Italia", "Lombardia"]}
ivl = iv[iv.anno == "2024-25"].pivot_table(index="citta", columns="grado", values="disp")
iv_rank = [[c, nn(ivl.loc[c, 8]), nn(ivl.loc[c, 13])] for c in ivl.sort_values(8).index]
put("invalsi8_milano_2024", nn(ivl.loc["Milano", 8]), "INVALSI open data (dispersione e eccellenza), aggregato 'Comune plesso', Totale, grado 8, anno 2024-25: % studenti a rischio dispersione implicita")
put("invalsi8_napoli_2024", nn(ivl.loc["Napoli", 8]), "idem")
put("invalsi8_italia_2024", nn(ivl.loc["Italia", 8]), "idem, Italia")
put("invalsi13_milano_2024", nn(ivl.loc["Milano", 13]), "idem, grado 13: % studenti in dispersione implicita")
put("invalsi13_italia_2024", nn(ivl.loc["Italia", 13]), "idem")
put("invalsi8_posizione_milano", [int(list(ivl.drop(["Italia", "Lombardia"]).sort_values(8).index).index("Milano")) + 1, ivl.drop(["Italia", "Lombardia"]).sort_values(8).index[0]], "posizione di Milano (1 = valore più basso) tra le 14 città, grado 8, 2024-25, e la città con il valore più basso")
og = rd("invalsi_dispersione_per_origine.csv")
ogm = og[og.anno == "2024-25"]
ORI = {c: {str(g): {s: nn(ogm[(ogm.citta == c) & (ogm.grado == g) & (ogm["sub"] == s)].disp.iloc[0]) if len(ogm[(ogm.citta == c) & (ogm.grado == g) & (ogm["sub"] == s)]) else None for s in ("Nativo", "Straniero I generazione", "Straniero II generazione", "Totale")} for g in (8, 13)} for c in ("Italia", "Provincia di Milano")}
put("invalsi_per_origine_2024", ORI, "INVALSI open data, aggregati 'Italia' e 'Provincia' (Milano), 2024-25, per origine: i singoli comuni non hanno la divisione")
cop = iv[(iv.citta == "Milano") & (iv.anno == "2024-25") & (iv.grado == 8)].cop
put("invalsi8_milano_copertura_pct", nn(cop.iloc[0]), "INVALSI: % alunni che hanno fatto tutte le prove sugli attesi")

# ---------------------------------------------------------------- Bes (città metropolitane)
bes = rd("bes_istruzione_citta_metropolitane.csv")
def bes_ult(cod, terr=None):
    d = bes[(bes.codice == cod)]
    out = {}
    for t, g in d.groupby("territorio"):
        g = g.dropna(subset=["valore"]).sort_values("anno")
        if len(g): out[t] = (int(g.anno.iloc[-1]), float(g.valore.iloc[-1]))
    return out
BES = {}
for cod in ("02IST006-N22", "02IST001", "12SER002", "02IST010P", "02IST011P"):
    BES[cod] = {t: [a, nn(v)] for t, (a, v) in bes_ult(cod).items()}
neet_m = bes[(bes.codice == "02IST006-N22") & (bes.territorio == "Milano")].dropna(subset=["valore"]).sort_values("anno")
put("neet_milano", [int(neet_m.anno.iloc[-1]), nn(neet_m.valore.iloc[-1])], "ISTAT Bes dei territori 2025, 02IST006-N22, Città metropolitana di Milano, ultimo anno")
neet_ser = rec(neet_m, ["anno", "valore"])

# ---------------------------------------------------------------- redditi e riepilogo 14 città
rc = rd("reddito_citta_2024.csv")
red = dict(zip(rc.citta, rc.reddito_medio_contribuente_eur))
cap = rd("milano_cap_tempo_pieno_reddito_2024_25.csv")
cap_rec = rec(cap, ["cap", "alunni", "tempo_pieno_pct_tot", "tempo_pieno_pct_statali", "quota_paritaria_pct", "reddito_medio_euro2025", "alunni_statali"], 1)
put("spearman_cap", CTR["spearman_cap"], "build.py, 38 CAP (n con reddito = %d): tempo pieno tutte le scuole / solo statali / quota paritarie contro reddito medio per contribuente (a.i. 2024, euro 2025). [rho, p, [IC95]]" % CTR["cap_n"])
put("paritarie_milano_quota_2024", nn(100 * a24.loc["Milano", "paritaria"] / a24.loc["Milano", "totale"]), "alunni paritarie / alunni totali, primaria Milano 2024/25 (MIM DS0090/DS0100)")

# tabella 14 città
tab = []
n24 = n14[n14.anno == 2024].set_index("area").p100_tot
n6_24 = n6[n6.anno == 2024].set_index("area")
for c in red:
    tab.append(dict(citta=c, reddito=int(red[c]), nidi_p100=nn(n24.get(c)), nidi_quota_priv=nn(n6_24.quota_posti_privati_pct.get(c)) if c in n6_24.index else None,
                    tp_tot=nn(t24.loc[c, "totale"]), tp_stat=nn(t24.loc[c, "statale"]), mensa=nn(mi.loc[c, "pct_alunni_in_scuole_con_mensa"]),
                    disp8=nn(ivl.loc[c, 8]), disp13=nn(ivl.loc[c, 13])))
tab.sort(key=lambda r: -r["reddito"])


# correlazione tra le 14 città (Spearman) tra reddito medio per contribuente e ogni indicatore
from scipy.stats import spearmanr
def ic14(x, y, n=5000, seed=11):
    rng = np.random.default_rng(seed); x = np.asarray(x); y = np.asarray(y); r = []
    for _ in range(n):
        i = rng.integers(0, len(x), len(x)); r.append(spearmanr(x[i], y[i])[0])
    return [round(float(np.nanpercentile(r, 2.5)), 2), round(float(np.nanpercentile(r, 97.5)), 2)]
td = pd.DataFrame(tab)
S14 = {}
for k in ("nidi_p100", "tp_tot", "tp_stat", "mensa", "disp8", "disp13"):
    x = td.dropna(subset=[k]); r = spearmanr(x.reddito, x[k])
    S14[k] = [round(float(r[0]), 2), round(float(r[1]), 4), ic14(x.reddito, x[k]), len(x)]
put("spearman_14_citta_reddito", S14, "Spearman tra reddito medio per contribuente (MEF 2024) e ogni indicatore, 14 città; [rho, p, [IC95], n]")
put("nidi_rango_milano_2024", [int(list(r24[~r24.area.isin(["Italia", "Lombardia"])].area).index("Milano")) + 1, 14], "posizione di Milano per posti ogni 100 bambini 0-2 nel 2024 tra le 14 città (1 = più alto)")

# ---------------------------------------------------------------- NIL: geojson
nil = rd("milano_nil_poverta_educativa.csv")
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
byid = nil.set_index("id_nil")
feats = []
def r5(c):
    if isinstance(c[0], (int, float)): return [round(c[0], 5), round(c[1], 5)]
    return [r5(x) for x in c]
for f in nilgeo["features"]:
    i = int(f["properties"]["ID_NIL"]); r = byid.loc[i]
    g = shape(f["geometry"]).simplify(0.00003, preserve_topology=True)
    gm = mapping(g); gm = {"type": gm["type"], "coordinates": r5(gm["coordinates"])}
    def v(k, d=1):
        x = r[k]
        return None if pd.isna(x) else (round(float(x), d) if d else int(x))
    feats.append({"type": "Feature", "geometry": gm, "properties": {
        "i": i, "n": r["nil"], "m": int(r["municipio"]), "r02": v("res_0_2_2018", 0), "sd": v("sedi_nido_2018_19", 0), "sp": v("sedi_nido_per_1000_0_2"),
        "al": v("alunni_primaria", 0), "tp": v("tp_pct_tot"), "ts": v("tp_pct_statali"), "as": v("alunni_statali", 0), "par": v("quota_paritaria_pct"),
        "me": v("mensa_pct_statali"), "rd": v("reddito_stimato_euro2025", 0), "cc": v("quota_civici_nel_cap_principale_pct", 0)}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
put("nil_con_scuole_primarie", CTR["nil_con_scuole_primarie"], "build.py: NIL con almeno una scuola primaria (MIM) assegnata")
put("milano_alunni_primaria_senza_nil", CTR["milano_2024_alunni_senza_nil"], "alunni di scuole primarie di Milano (MIM) senza NIL (indirizzo non agganciato alle localizzazioni del Comune)")
put("nil_tp_tot_sotto_55", int(((nil.alunni_primaria > 0) & (nil.tp_pct_tot < 55)).sum()), "NIL con scuole primarie e tempo pieno (tutte le scuole) sotto il 55%")
put("nil_tp_statali_sotto_70", [[r.nil, nn(r.tp_pct_statali)] for r in nil[nil.tp_pct_statali < 70].sort_values("tp_pct_statali").itertuples()], "NIL con tempo pieno nelle statali sotto il 70% (a.s. 2024/25)")
put("nil_mensa_sotto_50", [[r.nil, nn(r.mensa_pct_statali)] for r in nil[nil.mensa_pct_statali < 50].sort_values("mensa_pct_statali").itertuples()], "NIL con meno del 50% di alunni statali in scuole con spazio mensa")
_es = mun[~mun.municipio.isin([int(mun.loc[mun.sedi_per_1000_0_2.idxmax(), "municipio"]), int(mun.loc[mun.sedi_per_1000_0_2.idxmin(), "municipio"])])]
put("ds47_municipi_altri_min_max", [nn(_es.sedi_per_1000_0_2.min(), 1), nn(_es.sedi_per_1000_0_2.max(), 1)], "sedi per 1.000 bambini 0-2, municipi esclusi il più alto e il più basso")
put("nil_tp_tot_sotto_55_quota_paritaria_min", nn(nil[(nil.alunni_primaria > 0) & (nil.tp_pct_tot < 55)].quota_paritaria_pct.min()), "quota minima di alunni in paritarie tra i NIL con tempo pieno (tutte le scuole) sotto il 55%")
_cs = cap[cap.tempo_pieno_pct_statali < 90]
put("cap_statali_sotto_90", [len(_cs), int(cap.tempo_pieno_pct_statali.notna().sum()), [[str(r.cap), nn(r.tempo_pieno_pct_statali), int(r.reddito_medio_euro2025)] for r in _cs.itertuples()]], "CAP con tempo pieno nelle statali sotto il 90%: [n, su n CAP con statali, elenco CAP/tempo pieno/reddito]")
put("nil_sedi_nido_n_calcolabili", int(nil.sedi_nido_per_1000_0_2.notna().sum()), "NIL con almeno 150 bambini 0-2 (2018)")

# liste NIL
low_tp = nil[(nil.alunni_primaria > 0)].sort_values("tp_pct_tot").head(8)
nil_eccez = rec(low_tp, ["nil", "municipio", "alunni_primaria", "tp_pct_tot", "tp_pct_statali", "quota_paritaria_pct"])
low_me = nil[(nil.alunni_statali > 0)].sort_values("mensa_pct_statali").head(6)
nil_mensa = rec(low_me, ["nil", "alunni_statali", "mensa_pct_statali"])

# ---------------------------------------------------------------- scrittura
D = {"nidi": nid, "nidi_rank_2024": rank24, "nidi_serie14": ser14, "nidi_municipi": mun_rec, "tp": tps, "tp14": tp14, "mensa": mensa,
     "inv": IV, "inv_rank": iv_rank, "inv_origine": ORI, "bes": BES, "neet_milano": neet_ser, "tab14": tab, "cap": cap_rec, "nil_eccez_tp": nil_eccez, "nil_mensa": nil_mensa}
json.dump(D, open(os.path.join(OUT, "dati.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
RIEP["controlli"] = CTR
RIEP["avvisi_pagina"] = AVVISI
json.dump(RIEP, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=str)
for f in ["nidi_6citta_serie.csv", "nidi_14citta_italia_serie.csv", "nidi_milano_municipi_2018_19.csv", "tempo_pieno_primaria_citta_serie.csv",
          "mensa_primaria_statale_2024_25_citta.csv", "invalsi_dispersione_citta_serie.csv", "invalsi_dispersione_per_origine.csv",
          "bes_istruzione_citta_metropolitane.csv", "reddito_citta_2024.csv", "milano_cap_tempo_pieno_reddito_2024_25.csv", "milano_nil_poverta_educativa.csv"]:
    shutil.copyfile(os.path.join(PU, f), os.path.join(OUT, f))

# controlli finali: i numeri della pagina contro le tabelle pulite
check("riepilogo: nidi Milano 2024 = 49,3", RIEP["nidi_milano_p100_2024"], 49.3, 0.05)
check("riepilogo: posti pubblici + privati Milano 2024 = totale", float(m24.posti_pub + m24.posti_priv), float(m24.posti_tot), 0)
check("tab14: 14 città", len(tab), 14, 0)
check("mensa: 16 righe (14 città, altri comuni, Italia)", len(me), 16, 0)
print("AVVISI:", AVVISI if AVVISI else "nessuno")
