"""Analisi "BikeMi e bici in citta'" (fase 1). Si puo' rilanciare.

Uso: python -I -X utf8 analisi.py <bici_dir> <progetto_milano_in_dati_dir>
Legge:  bici/raw/comune/{ds574,ds65,ds60}, bici/raw/gbfs/*, bici/raw/zenodo_bikemi/{11,12,13}.csv,
        pioggia-e-caldo/pulito/intermedi/P_orario.parquet, pioggia-e-caldo/pulito/sensori_selezionati.csv,
        temperature/serie/serie_unica.csv   (solo confronto con il tempo, nessuna correzione)
Scrive: bici/pulito/*.csv e bici/pulito/riepilogo.json (ogni numero della pagina viene da qui).
"""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import zenodo_lettura as Z

B, P = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(B, "raw"), os.path.join(B, "pulito")
os.makedirs(PU, exist_ok=True)
R = {}
AVV = []

def chk(nome, val, atteso, tol=0):
    ok = abs(val - atteso) <= tol
    print(("ok  " if ok else "!!  ") + f"{nome}: {val} (atteso {atteso})")
    if not ok: AVV.append(nome)

# ================================================================ 1. ds574: bike sharing, serie annuale
s = pd.read_csv(os.path.join(RAW, "comune", "ds574_1.csv"), sep=";", dtype=str, keep_default_na=False)
b = s[s.sharing_veicoli == "bike sharing"].copy()
b["v"] = pd.to_numeric(b.sharing_veicoli_valore)
b["anno"] = b.anno.astype(int)
def pv(tip, ind):
    x = b[(b.sharing_veicoli_tipologia == tip) & (b.sharing_veicoli_indicatori == ind)]
    return x.set_index("anno").v
SB, FF, FS = "Station Based", "Free Floating", "Free Floating+Station Based"
ser = pd.DataFrame({
    "stazioni": pv(SB, "Numero stazioni"), "bici_sb": pv(SB, "biciclette totale"), "ebike_sb": pv(SB, "biciclette elettriche"),
    "abbonati_sb": pv(SB, "Abbonati annuali"), "noleggi_giorno_sb": pv(SB, "Noleggi medi giornalieri totale"),
    "noleggi_giorno_sb_bici": pv(SB, "Noleggi medi giornalieri bike"), "noleggi_giorno_sb_ebike": pv(SB, "Noleggi medi giornalieri ebike"),
    "noleggi_giorno_sb_ebike_seggiolino": pv(SB, "Noleggi medi giornalieri ebike with child seat"),
    "bici_ff": pv(FF, "biciclette totale"), "ebike_ff": pv(FF, "biciclette elettriche"), "noleggi_giorno_ff": pv(FF, "Noleggi medi giornalieri totale"),
    "km_annui_sb_ff": pv(FS, "Percorrenze annue"),
}).sort_index()
ser.index.name = "anno"
giorni = {a: (366 if (a % 4 == 0) else 365) for a in ser.index}
ser["noleggi_anno_sb_stima"] = [round(v * giorni[a]) if pd.notna(v) else np.nan for a, v in ser.noleggi_giorno_sb.items()]
ser["noleggi_anno_ff_stima"] = [round(v * giorni[a]) if pd.notna(v) else np.nan for a, v in ser.noleggi_giorno_ff.items()]
ser["noleggi_giorno_totale"] = ser.noleggi_giorno_sb + ser.noleggi_giorno_ff.fillna(0)
ser["noleggi_per_bici_giorno_sb"] = (ser.noleggi_giorno_sb / ser.bici_sb).round(2)
q = ser.noleggi_giorno_sb_ebike + ser.noleggi_giorno_sb_ebike_seggiolino
ser["quota_ebike_noleggi_sb_pct"] = (100 * q / (ser.noleggi_giorno_sb_bici + q)).round(1)
ser.to_csv(os.path.join(PU, "bikemi_serie.csv"), sep=";", encoding="utf8")
# controlli interni: le tre voci 2022-2025 sommano al totale
for a in (2022, 2023, 2024, 2025):
    r = ser.loc[a]
    chk(f"somma noleggi {a}", r.noleggi_giorno_sb_bici + r.noleggi_giorno_sb_ebike + r.noleggi_giorno_sb_ebike_seggiolino, r.noleggi_giorno_sb, 1)
pk = ser.noleggi_giorno_sb.idxmax()
R["sharing"] = {
    "picco_anno_sb": int(pk), "picco_noleggi_giorno_sb": int(ser.noleggi_giorno_sb.max()),
    "noleggi_giorno_sb": {int(a): int(v) for a, v in ser.noleggi_giorno_sb.items()},
    "abbonati": {int(a): int(v) for a, v in ser.abbonati_sb.items()},
    "stazioni": {int(a): int(v) for a, v in ser.stazioni.items()},
    "bici_sb": {int(a): int(v) for a, v in ser.bici_sb.items()},
    "noleggi_anno_sb_stima": {int(a): int(v) for a, v in ser.noleggi_anno_sb_stima.items()},
    "var_2020_su_2019_pct": round(100 * (ser.noleggi_giorno_sb[2020] / ser.noleggi_giorno_sb[2019] - 1), 1),
    "var_2025_su_2019_pct": round(100 * (ser.noleggi_giorno_sb[2025] / ser.noleggi_giorno_sb[2019] - 1), 1),
    "var_2025_su_picco_pct": round(100 * (ser.noleggi_giorno_sb[2025] / ser.noleggi_giorno_sb.max() - 1), 1),
    "abbonati_var_2025_su_2017_pct": round(100 * (ser.abbonati_sb[2025] / ser.abbonati_sb[2017] - 1), 1),
    "abbonati_var_2025_su_2024_pct": round(100 * (ser.abbonati_sb[2025] / ser.abbonati_sb[2024] - 1), 1),
    "noleggi_per_bici_2017": float(ser.noleggi_per_bici_giorno_sb[2017]), "noleggi_per_bici_2025": float(ser.noleggi_per_bici_giorno_sb[2025]),
    "quota_ebike_2022": float(ser.quota_ebike_noleggi_sb_pct[2022]), "quota_ebike_2025": float(ser.quota_ebike_noleggi_sb_pct[2025]),
    "ff_noleggi_giorno_2025": int(ser.noleggi_giorno_ff[2025]), "ff_noleggi_giorno_2017": int(ser.noleggi_giorno_ff[2017]),
    "ff_bici_2025": int(ser.bici_ff[2025]), "ff_bici_2017": int(ser.bici_ff[2017]),
    "ff_ebike_2025": int(ser.ebike_ff[2025]), "ff_ebike_2020": int(ser.ebike_ff[2020]),
    "totale_noleggi_giorno_2025": int(ser.noleggi_giorno_totale[2025]),
    "km_annui_2025": int(ser.km_annui_sb_ff[2025]), "km_annui_2020": int(ser.km_annui_sb_ff[2020]), "km_annui_2018": int(ser.km_annui_sb_ff[2018]),
    "ebike_sb_2025": int(ser.ebike_sb[2025]),
}
# uso per bici: e-bike contro bici muscolari (stazioni, 2025: la flotta e-bike e' una voce a parte in ds574)
r25 = ser.loc[2025]
eb_noleggi = r25.noleggi_giorno_sb_ebike + r25.noleggi_giorno_sb_ebike_seggiolino
mu_bici = r25.bici_sb - r25.ebike_sb
R["sharing"].update({
    "ebike_quota_flotta_2025_pct": round(100 * r25.ebike_sb / r25.bici_sb, 1),
    "ebike_noleggi_per_bici_giorno_2025": round(float(eb_noleggi / r25.ebike_sb), 2),
    "muscolari_noleggi_per_bici_giorno_2025": round(float(r25.noleggi_giorno_sb_bici / mu_bici), 2),
    "ebike_rapporto_uso_2025": round(float((eb_noleggi / r25.ebike_sb) / (r25.noleggi_giorno_sb_bici / mu_bici)), 1),
    "ff_noleggi_per_bici_giorno_2025": round(float(r25.noleggi_giorno_ff / r25.bici_ff), 2),
})
# altri servizi di sharing (solo per contesto, stessi dati ds574)
oth = s[s.sharing_veicoli.isin(["monopattini", "scooter sharing", "car sharing"]) & (s.sharing_veicoli_indicatori == "Noleggi medi giornalieri totale")].copy()
oth["v"] = pd.to_numeric(oth.sharing_veicoli_valore, errors="coerce")
oth = oth.groupby(["anno", "sharing_veicoli"]).v.sum().unstack()
oth.to_csv(os.path.join(PU, "altri_sharing_noleggi_giorno.csv"), sep=";")

# ================================================================ 2. ds65 stazioni + GBFS (fotografia)
st = pd.read_csv(os.path.join(RAW, "comune", "ds65_1.csv"), sep=";", dtype={"numero": str})
assert len(st) == 325 and (st.stato == "attiva").all()
st["anno"] = st.anno.astype("Int64")
inst = st.groupby("anno").agg(stazioni=("id_amat", "count"), stalli=("stalli", "sum")).cumsum()
inst.to_csv(os.path.join(PU, "stazioni_cumulate_per_anno_installazione.csv"), sep=";")
munic = st.groupby("zd_attuale").agg(stazioni=("id_amat", "count"), stalli=("stalli", "sum")).reset_index()
munic.to_csv(os.path.join(PU, "stazioni_per_municipio.csv"), sep=";", index=False)
chk("stazioni ds65 = ds574 2021", len(st), int(ser.stazioni[2021]))
R["stazioni"] = {
    "n": int(len(st)), "stalli": int(st.stalli.sum()), "tipo": st.tipo.value_counts().to_dict(),
    "per_municipio": {int(r.zd_attuale): {"stazioni": int(r.stazioni), "stalli": int(r.stalli)} for r in munic.itertuples()},
    "quota_municipio1_pct": round(100 * int(munic[munic.zd_attuale == 1].stazioni.iloc[0]) / len(st), 1),
    "per_anno_installazione": {int(a): int(v) for a, v in st.groupby("anno").size().items()},
    "anno_max": int(st.anno.max()), "senza_anno": int(st.anno.isna().sum()),
}
# GBFS: fotografia del 2 novembre 2026 (un solo scaricamento)
gi = json.load(open(os.path.join(RAW, "gbfs", "station_information.json"), encoding="utf8"))
gs = json.load(open(os.path.join(RAW, "gbfs", "station_status.json"), encoding="utf8"))
gts = gi["last_updated"]
g = pd.DataFrame(gi["data"]["stations"])[["station_id", "name", "lat", "lon", "capacity", "is_virtual_station"]]
gst = pd.DataFrame(gs["data"]["stations"])
gst["ebike"] = gst.vehicle_types_available.map(lambda L: sum(x["count"] for x in L if x["vehicle_type_id"] in ("ebike", "ebike_with_childseat")))
g = g.merge(gst[["station_id", "is_installed", "is_renting", "num_bikes_available", "num_docks_available", "ebike"]], on="station_id", how="left")
g["numero"] = g.name.str.extract(r"^(\w+)\s*-")[0].map(lambda x: x.zfill(3) if isinstance(x, str) and x.isdigit() else x)
ds65n = set(st.numero)
g["in_ds65"] = g.numero.isin(ds65n)
g.to_csv(os.path.join(PU, "gbfs_fotografia_2026-11-02.csv"), sep=";", index=False)
real = g[~g.is_virtual_station]
nuove = g[~g.in_ds65]
R["gbfs"] = {
    "istante_unix": int(gts), "istante": pd.Timestamp(gts, unit="s", tz="UTC").tz_convert("Europe/Rome").strftime("%Y-%m-%d %H:%M"),
    "stazioni": int(len(g)), "virtuali": int(g.is_virtual_station.sum()), "capacita_totale": int(g.capacity.sum()),
    "stazioni_in_ds65": int(g.in_ds65.sum()), "stazioni_non_in_ds65": int(len(nuove)),
    "ds65_non_in_gbfs": int(len(ds65n - set(g.numero))),
    "bici_disponibili": int(g.num_bikes_available.sum()), "ebike_disponibili": int(g.ebike.sum()),
    "stazioni_installate_non_attive": int((~g.is_renting.fillna(False)).sum()),
    "stazioni_vuote": int((g.num_bikes_available == 0).sum()), "stazioni_piene": int((g.num_docks_available == 0).sum()),
    "ebike_su_bici_pct": round(100 * g.ebike.sum() / g.num_bikes_available.sum(), 1),
}
chk("stazioni GBFS", len(g), 321)

# ================================================================ 3. ds60: chilometri di itinerari per anno
c = pd.read_csv(os.path.join(RAW, "comune", "ds60_itinerari_ciclabili.csv"), sep=";")
c["km"] = c.lunghezza / 1000
chk("segmenti ds60", len(c), 4411)
ded = c[c.tipologia.isin(["ciclabile sede propria", "ciclabile segnaletica"])].copy()
ded["anno"] = ded.fine_lavor
def cum(df, nome):
    y = df[df.anno > 0].groupby("anno").km.sum()
    idx = range(int(y.index.min()), int(y.index.max()) + 1)
    y = y.reindex(idx, fill_value=0)
    return y
tab = pd.DataFrame({"sede_propria_km": cum(ded[ded.tipologia == "ciclabile sede propria"], "sp"),
                    "corsia_segnaletica_km": cum(ded[ded.tipologia == "ciclabile segnaletica"], "sg")}).fillna(0)
tab["nuovi_km"] = tab.sum(axis=1)
tab["cumulati_km"] = tab.nuovi_km.cumsum()
tab["di_cui_ordinanza_lavori_km"] = ded[(ded.anno > 0) & (ded.norma == "ordinanza lavori stradali")].groupby("anno").km.sum().reindex(tab.index, fill_value=0)
tab = tab.round(3); tab.index.name = "anno_fine_lavori"
tab.to_csv(os.path.join(PU, "ciclabili_km_per_anno.csv"), sep=";")
tot_ded = ded.km.sum()
senza_anno = ded[ded.anno == 0].km.sum()
R["ciclabili"] = {
    "segmenti_totali": int(len(c)), "km_tutti_itinerari": round(c.km.sum(), 1),
    "km_per_tipologia": {k: round(v, 1) for k, v in c.groupby("tipologia").km.sum().items()},
    "km_piste_e_corsie": round(tot_ded, 1),
    "km_sede_propria": round(ded[ded.tipologia == "ciclabile sede propria"].km.sum(), 1),
    "km_corsie_segnaletica": round(ded[ded.tipologia == "ciclabile segnaletica"].km.sum(), 1),
    "km_piste_e_corsie_senza_attraversamenti": round(ded[ded.sede != "attraversamento"].km.sum(), 1),
    "km_senza_anno": round(senza_anno, 1), "segmenti_senza_anno": int((ded.anno == 0).sum()),
    "km_ordinanza_lavori": round(ded[ded.norma == "ordinanza lavori stradali"].km.sum(), 1),
    "quota_ordinanza_pct": round(100 * ded[ded.norma == "ordinanza lavori stradali"].km.sum() / tot_ded, 1),
    "km_2020": round(float(tab.nuovi_km.get(2020, 0)), 1), "km_2020_ordinanza": round(float(tab.di_cui_ordinanza_lavori_km.get(2020, 0)), 1),
    "km_2019": round(float(tab.nuovi_km.get(2019, 0)), 1), "km_2021": round(float(tab.nuovi_km.get(2021, 0)), 1),
    "km_2026": round(float(tab.nuovi_km.get(2026, 0)), 1),
    "km_cumulati_fine_2010": round(float(tab.cumulati_km.get(2010, 0)), 1), "km_cumulati_fine_2019": round(float(tab.cumulati_km.get(2019, 0)), 1),
    "km_cumulati_fine_2020": round(float(tab.cumulati_km.get(2020, 0)), 1), "km_cumulati_fine_2025": round(float(tab.cumulati_km.get(2025, 0)), 1),
    "anno_min": int(tab.index.min()),
    "quota_2020_su_totale_datato_pct": round(100 * float(tab.nuovi_km.get(2020, 0)) / float(tab.nuovi_km.sum()), 1),
    "per_gerarchia_km": {k: round(v, 1) for k, v in ded.groupby("gerarchia").km.sum().items()},
}
chk("km piste e corsie senza attraversamenti (~194 di parcheggi)", R["ciclabili"]["km_piste_e_corsie_senza_attraversamenti"], 194.3, 1.0)
# km per anno di BikeMi / piste: confronto semplice (solo accostamento)

# ================================================================ 4. Zenodo 2011-2013: indice di movimento orario
def prepara(anno2):
    t, scart = Z.leggi(os.path.join(RAW, "zenodo_bikemi", anno2 + ".csv"))
    t = t[(t.b >= 0) & (t.f >= 0) & (t.b + t.f <= 60)].copy()
    mp = {n: Z.chiave(n) for n in t.nome.drop_duplicates()}
    t["num"] = t.nome.map(lambda n: mp[n][0]); t["norm"] = t.nome.map(lambda n: mp[n][1])
    t["k"] = t.num.fillna(t.norm)
    t = t.sort_values(["k", "t"]).drop_duplicates(["k", "t"])
    dt = t.groupby("k").t.diff(); db = t.groupby("k").b.diff()
    t["mov"] = np.where(dt == pd.Timedelta(hours=1), db.abs(), np.nan)
    t["dia"] = t.t.dt.normalize()
    return t, scart
DICH = {"2011": 2957, "2012": 3899, "2013": 5190}
prof_rows = []; daily = {}
Zres = {}
T13 = None
for a2, anno in (("11", "2011"), ("12", "2012"), ("13", "2013")):
    t, scart = prepara(a2)
    d = t.groupby("dia").agg(mov=("mov", "sum"), n=("mov", "count"))
    full = d[d.n >= 0.9 * d.n.median()].copy()          # solo giorni con quasi tutte le misure
    full["idx"] = full.mov / 2
    daily[anno] = full
    ratio = full.idx.mean() / DICH[anno]
    Zres[anno] = {"righe_valide": int(len(t)), "righe_scartate_lettura": int(scart), "stazioni_chiave": int(t.k.nunique()),
                  "giorni_completi": int(len(full)), "indice_medio_giorno": round(float(full.idx.mean())),
                  "noleggi_medi_giorno_ds574": DICH[anno], "rapporto_indice_su_ds574": round(float(ratio), 2),
                  "da": str(t.t.min().date()), "a": str(t.t.max().date()),
                  "righe_senza_numero_stazione_pct": round(100 * float(t.num.isna().mean()), 1)}
    h = t.dropna(subset=["mov"]).copy()
    h["wd"] = np.where(h.t.dt.day_of_week < 5, "feriale", "festivo")
    h["ora"] = h.t.dt.hour
    h = h[h.dia.isin(full.index)]
    pr = h.groupby(["wd", "ora"]).mov.sum().div(h.groupby(["wd"]).mov.sum(), level="wd").mul(100).reset_index(name="quota_pct")
    pr["anno"] = int(anno)
    prof_rows.append(pr)
    if anno == "2013": T13 = t
chk("rapporto indice/ds574 2012 e 2013 (0.4-0.7)", Zres["2013"]["rapporto_indice_su_ds574"], 0.55, 0.15)
prof = pd.concat(prof_rows); prof.to_csv(os.path.join(PU, "profilo_orario_2011_2013.csv"), sep=";", index=False)
R["zenodo"] = Zres

# profilo orario (ora in cui finisce la misura: 8 = movimento tra le 7 e le 8)
def pr_(anno, wd):
    x = prof[(prof.anno == anno) & (prof.wd == wd)].set_index("ora").quota_pct
    return x.reindex(range(24), fill_value=0)
R["profilo_orario"] = {
    "feriale_2013": [round(float(v), 2) for v in pr_(2013, "feriale")], "festivo_2013": [round(float(v), 2) for v in pr_(2013, "festivo")],
    "feriale_2012": [round(float(v), 2) for v in pr_(2012, "feriale")], "festivo_2012": [round(float(v), 2) for v in pr_(2012, "festivo")],
}
f13 = pr_(2013, "feriale")
R["profilo_orario"]["picchi_feriali_2013"] = {"mattina_ora": int(f13.loc[6:11].idxmax()), "mattina_quota": round(float(f13.loc[6:11].max()), 1),
                                              "sera_ora": int(f13.loc[16:21].idxmax()), "sera_quota": round(float(f13.loc[16:21].max()), 1),
                                              "notte_0_5_pct": round(float(f13.loc[0:5].sum()), 1)}

# giorno della settimana e mese (2013, giorni completi)
d13 = daily["2013"].copy(); d13["dow"] = d13.index.day_of_week; d13["mese"] = d13.index.month
dow = d13.groupby("dow").idx.mean(); mean13 = d13.idx.mean()
mes = d13[d13.mese <= 11].groupby("mese").idx.agg(["mean", "count"])
pd.DataFrame({"indice_medio_giorno": dow.round(0), "relativo_alla_media": (dow / mean13).round(3)}).to_csv(os.path.join(PU, "giorno_settimana_2013.csv"), sep=";")
mes_out = pd.DataFrame({"indice_medio_giorno": mes["mean"].round(0), "giorni_completi": mes["count"], "relativo_alla_media": (mes["mean"] / mean13).round(3)})
mes_out.to_csv(os.path.join(PU, "mese_2013.csv"), sep=";")
R["stagioni_2013"] = {"dow_rel": [round(float(v), 3) for v in (dow / mean13)], "mese_rel": {int(m): round(float(v), 3) for m, v in (mes["mean"] / mean13).items()},
                      "mese_giorni": {int(m): int(v) for m, v in mes["count"].items()}, "media_2013": round(float(mean13))}

# ---- stazioni piu' movimentate (2013)
t = T13.copy()
t = t[t.dia.isin(daily["2013"].index)]
sj = t.groupby("k").agg(mov=("mov", "sum"), n=("mov", "count"), nome=("nome", lambda s: s.mode().iloc[0]), num=("num", "first")).reset_index()
ngiorni = len(daily["2013"])
sj["indice_per_giorno"] = sj.mov / 2 / ngiorni      # come per la citta': meta' delle variazioni in valore assoluto
sj = sj[sj.n > 0.5 * sj.n.max()].copy()                 # esclude stazioni attive solo per una parte dell'anno
sj["nome_pulito"] = sj.nome.str.replace(r"\s+0$", "", regex=True).str.strip()
sj["numero_ds65"] = sj.num
sj = sj.merge(st[["numero", "nome", "indirizzo", "stalli", "zd_attuale", "LONG_X_4326", "LAT_Y_4326"]].rename(columns={"numero": "numero_ds65", "nome": "nome_ds65"}), on="numero_ds65", how="left")
sj = sj.sort_values("indice_per_giorno", ascending=False)
sj.drop(columns=["k", "num", "nome"]).round(3).to_csv(os.path.join(PU, "stazioni_movimento_2013.csv"), sep=";", index=False)
top = sj.head(15)
R["stazioni_top_2013"] = [{"nome": r.nome_pulito, "nome_ds65": (None if pd.isna(r.nome_ds65) else r.nome_ds65), "num": (None if pd.isna(r.numero_ds65) else r.numero_ds65),
                           "indice_giorno": round(float(r.indice_per_giorno), 1), "lon": (None if pd.isna(r.LONG_X_4326) else round(float(r.LONG_X_4326), 5)),
                           "lat": (None if pd.isna(r.LAT_Y_4326) else round(float(r.LAT_Y_4326), 5))} for r in top.itertuples()]
R["stazioni_top_2013_meta"] = {"stazioni_valutate": int(len(sj)), "giorni": int(ngiorni), "quota_top15_pct": round(100 * float(top.mov.sum() / sj.mov.sum()), 1),
                               "senza_corrispondenza_ds65": int(sj.nome_ds65.isna().sum())}
# quota del movimento nelle stazioni del centro (Municipio 1) dove abbinabili
mm = sj.dropna(subset=["zd_attuale"])
R["stazioni_top_2013_meta"]["quota_municipio1_movimento_pct"] = round(100 * float(mm[mm.zd_attuale == 1].mov.sum() / mm.mov.sum()), 1)
R["stazioni_top_2013_meta"]["quota_municipio1_stazioni_abbinate_pct"] = round(100 * float((mm.zd_attuale == 1).mean()), 1)

# ================================================================ 5. confronto con il tempo (2013)
rain_path = os.path.join(P, "pioggia-e-caldo", "pulito", "intermedi", "P_orario.parquet")
p = pd.read_parquet(rain_path)
p = p[p.idsensore.isin(["14121", "9341", "2006"]) & (p.ora >= "2013-01-01") & (p.ora < "2014-01-01")]
ph = p.groupby("ora").mm.mean()                    # media dei tre pluviometri (Rosellini, Zavattari, Lambrate)
cop = p.groupby("ora").idsensore.nunique()
ph = ph[cop >= 2]
R["tempo_2013"] = {"pluviometri": ["Rosellini 14121", "Zavattari 9341", "Lambrate 2006"], "ore_con_pioggia_dato": int(len(ph))}
t13 = T13.dropna(subset=["mov"]).copy()
t13 = t13[t13.dia.isin(daily["2013"].index)]
hh = t13.groupby("t").mov.sum().rename("mov")
H = pd.DataFrame(hh).join(ph.rename("mm"), how="inner")
H["ora"] = H.index.hour; H["dow"] = H.index.day_of_week; H["mese"] = H.index.month
# pioggia nell'ora della misura o in quella prima (le etichette orarie dei pluviometri non sono certe)
prev = ph.shift(1, freq="h").reindex(H.index)
H["mm2"] = np.nan_to_num(H.mm) + np.nan_to_num(prev)
w = H[(H.dow < 5) & (H.ora.between(7, 20)) & (H.mese.between(3, 11))]
wet = w[w.mm2 >= 0.4]; dry = w[w.mm2 < 0.05]
# confronto a parita' di ora del giorno e di mese: media per (mese, ora) all'asciutto, poi rapporto
base = dry.groupby(["mese", "ora"]).mov.mean().rename("base")
wj = wet.join(base, on=["mese", "ora"]).dropna(subset=["base"])
rapp_ora = float(wj.mov.sum() / wj.base.sum())
R["tempo_2013"]["pioggia_ora"] = {"ore_bagnate": int(len(wj)), "ore_asciutte": int(len(dry)), "rapporto_movimento_bagnato_su_asciutto": round(rapp_ora, 2),
                                  "soglia_bagnato_mm_2ore": 0.4, "soglia_asciutto_mm_2ore": 0.05, "ore_giorno": "7-20", "giorni": "feriali, marzo-novembre"}
bu = []
for lo, hi, lab in ((0.4, 1.0, "0,4-1 mm"), (1.0, 3.0, "1-3 mm"), (3.0, 1e9, "3 mm o piu'")):
    x = wj[(wj.mm2 >= lo) & (wj.mm2 < hi)]
    if len(x): bu.append({"classe": lab, "ore": int(len(x)), "rapporto": round(float(x.mov.sum() / x.base.sum()), 2)})
R["tempo_2013"]["pioggia_classi"] = bu
# giornaliero: temperatura media e pioggia del giorno
ts = pd.read_csv(os.path.join(P, "temperature", "serie", "serie_unica.csv"), usecols=["date", "tmean", "tmax"], parse_dates=["date"]).set_index("date")
D = daily["2013"].join(ts, how="left")
D["pioggia"] = ph.resample("D").sum().reindex(D.index)
D["ore_pioggia_dato"] = ph.resample("D").count().reindex(D.index)
D = D[(D.index.day_of_week < 5) & (D.index.month.isin(range(3, 12)))].copy()
D = D[D.ore_pioggia_dato >= 20]
D["mese"] = D.index.month
D["rel_mese"] = D.idx / D.groupby("mese").idx.transform("mean")      # relativo alla media del suo mese (toglie la stagione)
D["classe_t"] = pd.cut(D.tmean, [-50, 8, 14, 20, 26, 60], labels=["sotto 8", "8-14", "14-20", "20-26", "sopra 26"])
tt = D.groupby("classe_t", observed=True).agg(giorni=("idx", "count"), indice_medio=("idx", "mean"), rel_mese=("rel_mese", "mean")).round(2)
tt.to_csv(os.path.join(PU, "temperatura_2013_feriali.csv"), sep=";")
D["piove"] = D.pioggia >= 1.0
pp = D.groupby("piove").agg(giorni=("idx", "count"), indice_medio=("idx", "mean"), rel_mese=("rel_mese", "mean")).round(3)
pp.to_csv(os.path.join(PU, "pioggia_giorno_2013_feriali.csv"), sep=";")
R["tempo_2013"]["temperatura_classi"] = [{"classe": str(k), "giorni": int(r.giorni), "indice_medio": round(float(r.indice_medio)), "rel_mese": round(float(r.rel_mese), 2)} for k, r in tt.iterrows()]
R["tempo_2013"]["giorno_piovoso"] = {"giorni_pioggia_ge1mm": int(pp.loc[True, "giorni"]), "giorni_asciutti": int(pp.loc[False, "giorni"]),
                                     "indice_pioggia": round(float(pp.loc[True, "indice_medio"])), "indice_asciutto": round(float(pp.loc[False, "indice_medio"])),
                                     "rel_mese_pioggia": round(float(pp.loc[True, "rel_mese"]), 2), "rel_mese_asciutto": round(float(pp.loc[False, "rel_mese"]), 2)}
# giorni singoli estremi (per sanita')
best = D.sort_values("idx", ascending=False).head(3)
R["tempo_2013"]["giorni_top"] = [{"data": str(i.date()), "indice": round(float(r.idx)), "tmean": round(float(r.tmean), 1), "pioggia_mm": round(float(r.pioggia), 1)} for i, r in best.iterrows()]

# ================================================================ 6. ricerca contatori: esito
R["contatori"] = {"dataset_comune_trovati": 0, "parole_cercate": ["contabici", "conteggio bici", "conta bici", "contatori", "rilevatori", "spire", "postazioni di conteggio", "passaggi", "transiti", "ciclisti", "flussi", "traffico"],
                  "schede_catalogo_comune": 2611, "esito": "nessuna scheda con conteggi di biciclette (le schede 'transiti/accessi giornalieri' sono dell'Area C)",
                  "stampa": [{"fonte": "Moto.it, 27/2/2023", "dato": "Corso Buenos Aires, dati AMAT 2022: media 6.792 bici al giorno, punte vicine a 10.000"}]}

json.dump(R, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("\nAVVISI:", AVV or "nessuno")
