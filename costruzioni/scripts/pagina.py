"""Scrive i file dati della pagina "Dove si costruisce" (docs/costruzioni/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <costruzioni_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): costruzioni/pulito/{titoli_edilizi,serie_annuale,nuovi_per_tipo_titolo_anno,nuovi_per_trimestre_2021_2024,nil_costruzioni,dbt_nil}.csv,
riepilogo.json, dbt_controlli.json, inventario.csv; i confini NIL di citta-15-minuti; i nomi dei NIL di censimenti.
Scrive in <docs_dir>/costruzioni/data/: riepilogo.json, nil.geojson, nil.csv, serie_annuale.csv, titoli_per_anno.csv, trimestri_2021_2024.csv,
grandi_interventi.csv.

Regole: nessun record singolo di titolo edilizio viene ripubblicato, tranne i "grandi interventi" (indirizzo + categoria del titolare + dimensioni)
e solo se il titolare e' impresa/societa', cooperativa o ente pubblico (mai persona fisica, mai "Altro") e il record non e' un piccolo ampliamento.
Nessun nome di progetto: l'indirizzo e' quello scritto nel file. Nessun nome di persona.
"""
import sys, os, json
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping

K, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(K, "pulito")
OUT = os.path.join(DOCS, "costruzioni", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")
def R(x, d=1):
    return None if pd.isna(x) else round(float(x), d)
def I(x):
    return None if pd.isna(x) else int(round(float(x)))

ser = pd.read_csv(os.path.join(PU, "serie_annuale.csv"), sep=";")
tit = pd.read_csv(os.path.join(PU, "nuovi_per_tipo_titolo_anno.csv"), sep=";")
trim = pd.read_csv(os.path.join(PU, "nuovi_per_trimestre_2021_2024.csv"), sep=";")
nilc = pd.read_csv(os.path.join(PU, "nil_costruzioni.csv"), sep=";")
RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))
DBTC = json.load(open(os.path.join(PU, "dbt_controlli.json"), encoding="utf8"))
t = pd.read_csv(os.path.join(PU, "titoli_edilizi.csv"), sep=";", dtype={"civico": str})
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))

# ------------------------------------------------------------ serie annuale
ser["nuovi_tot"] = ser.nuovi_fabbricati_res + ser.nuovi_fabbricati_nonres + ser.nuovi_fabbricati_collettivita
tot_ab = int(ser.nuove_abitazioni_in_nuovi_fabbricati.sum())
pop0, pop1 = float(ser.popolazione.iloc[0]), float(ser.popolazione.iloc[-1])
check("nuovi residenziali 2014-2024", int(ser.nuovi_fabbricati_res.sum()), 725)
check("nuovi non residenziali", int(ser.nuovi_fabbricati_nonres.sum()), 210)
check("abitazioni in nuovi fabbricati", tot_ab, 26174)
check("variazione popolazione 2014-2024", pop1 - pop0, 56364)
anni = []
for _, r in ser.iterrows():
    anni.append({"anno": int(r.anno), "res": I(r.nuovi_fabbricati_res), "nonres": I(r.nuovi_fabbricati_nonres), "coll": I(r.nuovi_fabbricati_collettivita), "tot": I(r.nuovi_tot),
                 "abitazioni": I(r.nuove_abitazioni_in_nuovi_fabbricati), "ampl": I(r.ampliamenti_res + r.ampliamenti_nonres + r.ampliamenti_collettivita),
                 "volume_nuovi_m3": I(r.volume_nuovi_fabbricati_m3), "popolazione": I(r.popolazione), "var_pop": I(r.var_popolazione),
                 "istat_prov_abitazioni": I(r.istat_prov_MI_abitazioni_nuovi_res), "istat_prov_fabbricati_res": I(r.istat_prov_MI_nuovi_fabbricati_res)})
pd.DataFrame(anni).to_csv(os.path.join(OUT, "serie_annuale.csv"), index=False, sep=";")

# ------------------------------------------------------------ titolo per anno (SCIA + SCIA alternativa sommate)
tit["scia_tutte"] = tit["SCIA"] + tit["SCIA alternativa"]
tit["tot"] = tit["Permesso di costruire"] + tit.scia_tutte
tit["quota_scia_tutte_pct"] = (100 * tit.scia_tutte / tit.tot).round(1)
ti = [{"anno": int(r.anno), "pdc": int(r["Permesso di costruire"]), "scia": int(r["SCIA"]), "scia_alt": int(r["SCIA alternativa"]), "scia_tutte": int(r.scia_tutte),
       "tot": int(r.tot), "quota_scia_pct": R(r.quota_scia_tutte_pct)} for _, r in tit.iterrows()]
pd.DataFrame(ti).to_csv(os.path.join(OUT, "titoli_per_anno.csv"), index=False, sep=";")
q22 = [x for x in ti if x["anno"] == 2022][0]; check("quota SCIA 2022", q22["quota_scia_pct"], 72.4, .05)

# ------------------------------------------------------------ ricostruzioni dopo demolizione (2022-2024)
rc = RIEP["ricostruzioni_nuovi_res_2022_2024"]
check("ricostruzioni 2022-24", rc["ricostruzioni"], 92); check("edifici 2022-24", rc["edifici"], 185)
check("SCIA alt tra ricostruzioni", rc["scia_alt_tra_ricostruzioni"], 61); check("SCIA alt tra non sostitutivi", rc["scia_alt_tra_non_sostitutivi"], 40)
nres = 185 - 92
ricostr = {"edifici": rc["edifici"], "ricostruzioni": rc["ricostruzioni"], "quota_pct": rc["quota_pct"],
           "abitazioni_ricostruzioni": int(rc["abitazioni_ricostruzioni"]), "volume_ricostruzioni_m3": int(rc["volume_ricostruzioni_m3"]),
           "non_sostitutivi": nres, "abitazioni_non_sostitutivi": int(rc["abitazioni_non_sostitutivi"]), "volume_non_sostitutivi_m3": int(rc["volume_non_sostitutivi_m3"]),
           "scia_alt_ricostruzioni": rc["scia_alt_tra_ricostruzioni"], "scia_alt_non_sostitutivi": rc["scia_alt_tra_non_sostitutivi"],
           "quota_scia_alt_ricostruzioni_pct": round(100 * rc["scia_alt_tra_ricostruzioni"] / rc["ricostruzioni"]),
           "quota_scia_alt_non_sostitutivi_pct": round(100 * rc["scia_alt_tra_non_sostitutivi"] / nres),
           "per_anno": [{"anno": 2022, "si": 45, "tot": 103}, {"anno": 2023, "si": 38, "tot": 58}, {"anno": 2024, "si": 9, "tot": 24}],
           "campo_2021": RIEP["campo_abbattimento_2021"]}
# controllo dei per_anno
x = t[(t.intervento == "nuovo_fabbricato") & (t.uso == "residenziale") & (t.anno >= 2022) & (t.anno <= 2024)]
for e in ricostr["per_anno"]:
    s = x[x.anno == e["anno"]]; check(f"ricostruzioni {e['anno']}", int((s.abbattimento_ricostruzione == "si").sum()), e["si"]); check(f"edifici res {e['anno']}", len(s), e["tot"])

# ------------------------------------------------------------ trimestri 2021-2024 e confronto con ISTAT
tr = [{"t": r.trim, "nuovi": int(r.nuovi_fabbricati), "abitazioni": I(r.abitazioni)} for _, r in trim.iterrows()]
pd.DataFrame(tr).to_csv(os.path.join(OUT, "trimestri_2021_2024.csv"), index=False, sep=";")
cmp_ = RIEP["confronto_2024_comune_vs_istat"]
y = ser.set_index("anno")
confronto = {
    "comune_fabbricati_res": {"2022": I(y.loc[2022, "nuovi_fabbricati_res"]), "2023": I(y.loc[2023, "nuovi_fabbricati_res"]), "2024": I(y.loc[2024, "nuovi_fabbricati_res"])},
    "comune_abitazioni": {"2022": I(y.loc[2022, "nuove_abitazioni_in_nuovi_fabbricati"]), "2023": I(y.loc[2023, "nuove_abitazioni_in_nuovi_fabbricati"]), "2024": I(y.loc[2024, "nuove_abitazioni_in_nuovi_fabbricati"])},
    "istat_prov_fabbricati_res": {a: I(y.loc[int(a), "istat_prov_MI_nuovi_fabbricati_res"]) for a in ("2022", "2023", "2024")},
    "istat_prov_abitazioni": {a: I(y.loc[int(a), "istat_prov_MI_abitazioni_nuovi_res"]) for a in ("2022", "2023", "2024")},
    "var_pct": cmp_,
    "istat_2025_provincia": {"abitazioni": 3241, "fabbricati_res": 344}}
check("ISTAT prov abitazioni 2025", RIEP["istat_2025_provincia_MI"]["abitazioni_nuovi_res"], 3241)

# ------------------------------------------------------------ NIL
nilgeo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
feats, rows = [], []
nilc = nilc.set_index("id_nil")
ARTEFATTO = {60}   # Stadio-Ippodromi: le tribune dello stadio risultano "sparite" per un cambio di codifica (verificato)
assert len(nilc) == 88
for i in sorted(nilc.index, key=lambda k: nomi.get(int(k), "")):
    r = nilc.loc[i]; nome = nomi.get(int(i)) or str(r.nil).title()
    ab = I(r.pop_2024)
    p = {"i": int(i), "n": nome, "ab": ab, "nd": I(r.nuove_abitazioni_2014_2024), "nd1": I(r.nuove_abitazioni_2014_2019), "nd2": I(r.nuove_abitazioni_2020_2024),
         "nfr": I(r.nuovi_fabbricati_res), "nfn": I(r.nuovi_fabbricati_nonres),
         "p1000": R(1000 * r.nuove_abitazioni_2014_2024 / r.pop_2024, 1) if r.pop_2024 and r.pop_2024 > 0 else None,
         "vol": I(r.volume_nuovi_m3), "dp": I(r.var_pop_2014_2024), "dpp": R(r.var_pop_pct, 1), "q": R(r.quota_abitazioni_nuove_pct, 1),
         "cl": 1 if (r.pop_2024 or 0) >= 5000 else 0,
         "dn": I(r.dbt_volume_nuove_m3), "dso": I(r.dbt_volume_sopraelevazioni_m3), "ds": I(r.dbt_volume_sparite_m3), "dnet": I(r.dbt_volume_netto_m3),
         "art": 1 if int(i) in ARTEFATTO else 0}
    g = geom[int(i)].simplify(0.00003, preserve_topology=True); gj = mapping(g)
    def rnd(c): return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
    rows.append({"id_nil": int(i), "nil": nome, "abitanti_2024": ab, "abitanti_2014": I(r.pop_2014), "variazione_abitanti_2014_2024": p["dp"],
                 "nuovi_fabbricati_residenziali_2014_2024": p["nfr"], "nuovi_fabbricati_non_residenziali_2014_2024": p["nfn"],
                 "nuove_abitazioni_2014_2024": p["nd"], "nuove_abitazioni_2014_2019": p["nd1"], "nuove_abitazioni_2020_2024": p["nd2"],
                 "nuove_abitazioni_ogni_1000_abitanti_2024": p["p1000"], "quota_abitazioni_nuove_della_citta_pct": p["q"], "volume_nuovi_fabbricati_m3": p["vol"],
                 "dbt_volume_unita_nuove_m3": p["dn"], "dbt_volume_sopraelevazioni_m3": p["dso"], "dbt_volume_unita_sparite_m3": p["ds"], "dbt_volume_netto_m3": p["dnet"],
                 "dbt_dato_non_affidabile": p["art"], "in_classifica_almeno_5000_abitanti": p["cl"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";")
check("abitazioni assegnate a NIL", sum(f["properties"]["nd"] for f in feats), 25005)
nilc2 = nilc.copy(); nilc2["nome"] = [nomi.get(int(i)) or str(n).title() for i, n in zip(nilc2.index, nilc2.nil)]
top = nilc2.sort_values("nuove_abitazioni_2014_2024", ascending=False)
top10 = [{"n": r.nome, "nd": I(r.nuove_abitazioni_2014_2024), "p1000": R(1000 * r.nuove_abitazioni_2014_2024 / r.pop_2024, 1), "quota": R(r.quota_abitazioni_nuove_pct, 1)} for _, r in top.head(10).iterrows()]
check("quota top 5 NIL", round(float(top.head(5).quota_abitazioni_nuove_pct.sum()), 1), 28.8, .15)

# ------------------------------------------------------------ grandi interventi (solo campi ammessi)
tt = t[(t.flag_anno_fuori_serie == 0) & (t.intervento == "nuovo_fabbricato")].copy()
tt["cl"] = tt.indirizzo.str.lower().str.replace(r"[^a-z0-9 ]", " ", regex=True).str.split().str.join(" ")
OK_CAT = {"Impresa / Società": "impresa o società", "Cooperativa edilizia": "cooperativa edilizia", "Ente pubblico": "ente pubblico"}
def cap(s):
    s = str(s).strip()
    return s if not s.isupper() else s.title()
g = tt.groupby(["cl", "anno"]).agg(indirizzo=("indirizzo", "first"), civico=("civico", "first"), nil=("nil", "first"), edifici=("id_modello", "size"),
        abitazioni=("abitazioni", "sum"), volume_m3=("volume_m3", "sum"), uso=("uso", "first"), titoli=("tipo_titolo", lambda s: ", ".join(sorted(set(s.dropna())))),
        cat=("titolare_categoria", lambda s: "|".join(sorted(set(s)))), pub=("indirizzo_pubblicabile", "min")).reset_index()
g = g[(g.pub == 1) & g.cat.isin(OK_CAT.keys())].copy()      # un solo tipo di titolare per gruppo e tra quelli ammessi
def civ(c):
    c = "" if pd.isna(c) else str(c).strip()
    return "" if c in ("", "0", "-", "nan") else c
g["indirizzo"] = [(cap(a) + (", " + civ(c) if civ(c) else "")) for a, c in zip(g.indirizzo, g.civico)]
g["categoria_titolare"] = g.cat.map(OK_CAT)
g["quartiere"] = [nomi.get(int(nilc.index[nilc.nil == n][0]), n.title()) if isinstance(n, str) and n and (nilc.nil == n).any() else "" for n in g.nil]
g["uso"] = g.uso.map({"residenziale": "residenziale", "non_residenziale": "non residenziale", "collettivita": "collettività"})
g["abitazioni"] = g.abitazioni.fillna(0).astype(int); g["volume_m3"] = g.volume_m3.fillna(0).astype(int)
cols = ["anno", "indirizzo", "quartiere", "uso", "edifici", "abitazioni", "volume_m3", "titoli", "categoria_titolare"]
gv = g.sort_values("volume_m3", ascending=False).head(15)[cols]
ga = g[g.uso == "residenziale"].sort_values("abitazioni", ascending=False).head(10)[cols]
pd.concat([gv.assign(classifica="per volume"), ga.assign(classifica="per abitazioni")]).to_csv(os.path.join(OUT, "grandi_interventi.csv"), index=False, sep=";")
# controllo: nessuna persona fisica e nessun "Altro"
assert not g.cat.str.contains("Persona|Altro").any()
vol_tot = tt.volume_m3.sum()
check("volume totale nuovi fabbricati (m3)", int(vol_tot), 19879914, 1)
ok_ = nilc2[~nilc2.index.isin(ARTEFATTO)].sort_values("dbt_volume_netto_m3", ascending=False)
dbt_top = [{"n": r.nome, "net": I(r.dbt_volume_netto_m3), "nuove": I(r.dbt_volume_nuove_m3), "sparite": I(r.dbt_volume_sparite_m3)} for _, r in ok_.head(5).iterrows()]
dbt_bot = [{"n": r.nome, "net": I(r.dbt_volume_netto_m3)} for _, r in ok_.tail(3).iterrows()]
st = nilc2.loc[list(ARTEFATTO)[0]]
dbt_art = {"n": st.nome, "net": I(st.dbt_volume_netto_m3)}
grandi = {"per_volume": gv.to_dict("records"), "per_abitazioni": ga.to_dict("records"),
          "esclusi": "titolari persona fisica (87 nuovi fabbricati), categoria «Altro» (369) e piccoli ampliamenti residenziali; indirizzi dei record esclusi non pubblicati",
          "quota_abitazioni_in_edifici_da_100_in_su_pct": 28.3}

# ------------------------------------------------------------ riepilogo.json
dbt_tot = DBTC["totali"]; dbt_gr = DBTC["unita_grandi_oltre_300m2"]
zr = DBTC["origine_unita_2012_per_ID_ZRIL"]
riep = {
  "generato_da": "costruzioni/scripts/pagina.py", "download": "2026-11-01",
  "totali": {"nuovi_res": int(ser.nuovi_fabbricati_res.sum()), "nuovi_nonres": int(ser.nuovi_fabbricati_nonres.sum()), "nuovi_coll": int(ser.nuovi_fabbricati_collettivita.sum()),
            "ampliamenti": int(ser.ampliamenti_res.sum() + ser.ampliamenti_nonres.sum() + ser.ampliamenti_collettivita.sum()),
            "abitazioni_nuovi": tot_ab, "abitazioni_ampliamenti": int(ser.abitazioni_da_ampliamenti.sum()),
            "volume_nuovi_m3": int(ser.volume_nuovi_fabbricati_m3.sum()), "volume_ampliamenti_m3": int(ser.volume_ampliamenti_m3.sum()),
            "pop_2014": int(pop0), "pop_2024": int(pop1), "var_pop": int(pop1 - pop0), "abitazioni_per_100_residenti": round(100 * tot_ab / (pop1 - pop0)),
            "senza_nil_abitazioni": 1169, "senza_nil_record": 54, "record_totali": 1315, "record_serie": 1306},
  "anni": anni, "titoli": ti, "ricostruzioni": ricostr, "trimestri": tr, "confronto_2024": confronto,
  "nil_top10": top10, "nil_quota_top5_pct": 28.8, "nil_quota_top10_pct": 43.2, "nil_senza_abitazioni": 14,
  "spearman": {"abitazioni_vs_variazione_popolazione": RIEP["spearman_abitazioni_nuove_vs_var_popolazione_per_NIL"],
               "abitazioni_vs_volume_nuovo_dbt": RIEP["spearman_abitazioni_permessi_vs_volume_nuovo_DBT_per_NIL"]},
  "dbt": {"unita_2012_tipi": DBTC["unita_2012_tutti_i_tipi"], "unita_2020_tipi": DBTC["unita_2020_tutti_i_tipi"], "origine_2012": zr,
          "quota_2006_pct": round(100 * zr["MI_2006"] / (zr["MI_2006"] + zr["MI_2012"])), "soglia_m2": DBTC["soglia_area_m2"],
          "nuove_n": dbt_tot["nuove_n"], "nuove_milioni_m3": dbt_tot["nuove_volume_milioni_m3"], "sopraelevate_n": dbt_tot["sopraelevate_n"],
          "sopraelevate_milioni_m3": dbt_tot["sopraelevate_volume_aggiunto_milioni_m3"], "sparite_n": dbt_tot["sparite_n"], "sparite_milioni_m3": dbt_tot["sparite_volume_milioni_m3"],
          "grandi_nuove_n": dbt_gr["nuove_n"], "grandi_nuove_milioni_m3": dbt_gr["nuove_volume_milioni_m3"], "grandi_sparite_n": dbt_gr["sparite_n"], "grandi_sparite_milioni_m3": dbt_gr["sparite_volume_milioni_m3"],
          "volume_totale_milioni_m3": DBTC["volume_totale_milioni_m3"], "impronta_km2": DBTC["area_impronta_totale_km2"],
          "delta_altezza_percentili": DBTC["delta_altezza_unita_presenti_percentili_1_10_25_50_75_90_99"]},
  "grandi": grandi, "dbt_top5_netto": dbt_top, "dbt_ultimi3_netto": dbt_bot, "dbt_artefatto": dbt_art,
  "cronologia": [
    {"quando": "25 luglio 2024", "cosa": "Gli emendamenti «Salva Milano» vengono ritirati dal decreto «Salva-casa»; l'inchiesta riguarda lavori fatti con la SCIA invece del permesso di costruire.", "fonte": "https://ediltecnico.it/salva-milano-bocciato-ritirati-gli-emendamenti/", "fonte_nome": "Ediltecnico, 25/7/2024"},
    {"quando": "marzo 2025", "cosa": "Arresto di un ex funzionario comunale; la norma «Salva Milano», approvata dalla Camera, non viene mai votata al Senato.", "fonte": "https://www.ilpost.it/2025/07/17/inchieste-edilizia-milano-beppe-sala-indagato/", "fonte_nome": "Il Post, 17/7/2025"},
    {"quando": "maggio 2025", "cosa": "Il consiglio comunale adotta regole più severe: per gli edifici oltre 25 metri non basta più la SCIA, serve un progetto completo.", "fonte": "https://www.ilpost.it/2025/07/17/inchieste-edilizia-milano-beppe-sala-indagato/", "fonte_nome": "Il Post, 17/7/2025"}],
  "fonti": [
    {"nome": "Comune di Milano, «Edilizia» (ds270, ds2984, ds271, ds2985, ds2983)", "licenza": "CC BY (versione non indicata dal portale)", "scaricato": "2026-11-01", "url": "https://dati.comune.milano.it/"},
    {"nome": "Comune di Milano, Database Topografico 2012 e 2020 (ds2892, ds2889)", "licenza": "CC BY", "scaricato": "2026-11-01", "url": "https://dati.comune.milano.it/"},
    {"nome": "Comune di Milano, residenti per quartiere (ds205) e confini dei NIL (ds964)", "licenza": "CC BY", "scaricato": "2026-11-01", "url": "https://dati.comune.milano.it/"},
    {"nome": "ISTAT, permessi di costruire (IstatData)", "licenza": "CC BY 4.0 dichiarata da ISTAT", "scaricato": "2026-11-01", "url": "https://www.istat.it/tavole-di-dati/statistiche-sui-permessi-di-costruire-anno-2025/"},
    {"nome": "Agenzia delle Entrate, OMI (compravendite)", "licenza": "CC BY 4.0", "scaricato": "2026-10-30 (filone prezzi-case)", "url": "https://www.agenziaentrate.gov.it/"}],
  "avvisi_controlli": AVVISI,
  "origine": {"anni": "costruzioni/pulito/serie_annuale.csv (da titoli_edilizi.csv e ds205)", "titoli": "pulito/nuovi_per_tipo_titolo_anno.csv", "ricostruzioni": "pulito/riepilogo.json e titoli_edilizi.csv (campo abbattimento_ricostruzione)",
              "trimestri": "pulito/nuovi_per_trimestre_2021_2024.csv", "nil": "pulito/nil_costruzioni.csv", "dbt": "pulito/dbt_controlli.json e dbt_nil.csv", "grandi": "pulito/titoli_edilizi.csv (solo campi ammessi)"}}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print("file scritti in", OUT, os.listdir(OUT))
if AVVISI: print("AVVISI:", AVVISI); sys.exit(1)
