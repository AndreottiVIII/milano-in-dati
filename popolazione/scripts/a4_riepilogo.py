"""a4: riepilogo storia A (chi arriva e chi lascia Milano). Legge pulito/flussi_citta_anno.csv, flussi_nil_riepilogo.csv e i dataset per eta' e luogo (ds1957-1960).
Uso: python -I -X utf8 a4_riepilogo.py <popolazione assoluto>   Scrive pulito/riepilogo_A.json, pulito/flussi_eta_2020_2024.csv, pulito/flussi_luogo_2020_2024.csv"""
import sys, os, json
import numpy as np, pandas as pd
P = sys.argv[1]; out = os.path.join(P, "pulito"); raw = os.path.join(P, "raw")
f = pd.read_csv(os.path.join(out, "flussi_citta_anno.csv")).set_index("anno")
res = {}
ist = f.loc[2002:2025, ["istat_isc_interno", "istat_canc_interno", "istat_saldo_interno", "istat_isc_estero", "istat_canc_estero", "istat_saldo_estero"]].astype(int)
ist["saldo_totale"] = ist.istat_saldo_interno + ist.istat_saldo_estero
res["istat_per_anno"] = {int(y): r.to_dict() for y, r in ist.iterrows()}
res["istat_totali_2002_2025"] = ist.sum().to_dict()
res["istat_totali_2020_2025"] = ist.loc[2020:2025].sum().to_dict()
res["istat_totali_2012_2019"] = ist.loc[2012:2019].sum().to_dict()
res["istat_totali_2002_2010"] = ist.loc[2002:2010].sum().to_dict()
res["anni_saldo_interno_positivo"] = [int(y) for y in ist.index[ist.istat_saldo_interno > 0]]
# cittadinanza (ISTAT 2002-2018): saldo estero per cittadinanza
c = f.loc[2002:2018]
res["istat_estero_per_cittadinanza_2002_2018"] = dict(
    italiani_iscritti=int(c.istat_isc_estero_ita.sum()), italiani_cancellati=int(c.istat_canc_estero_ita.sum()),
    stranieri_iscritti=int(c.istat_isc_estero_str.sum()), stranieri_cancellati=int(c.istat_canc_estero_str.sum()))
# per evento, per cittadinanza 2004-2024
e = f.loc[2004:2024]
res["evento_estero_cittadinanza"] = {int(y): dict(isc_ita=int(r.ev_isc_estero_ita), isc_str=int(r.ev_isc_estero_str), canc_ita=int(r.ev_canc_estero_ita), canc_str=int(r.ev_canc_estero_str)) for y, r in e.iterrows()}
res["evento_saldi"] = {int(y): dict(italia=int(r.ev_saldo_italia), estero=int(r.ev_saldo_estero), altro=int(r.ev_isc_altro - r.ev_canc_altro)) for y, r in e.iterrows()}
# eta' 2020-2024
i = pd.read_csv(f"{raw}/comune_ds1957/ds1957_popolazione_iscrizioni_evento_eta.csv", sep=";"); c_ = pd.read_csv(f"{raw}/comune_ds1958/ds1958_popolazione_cancellazioni_evento_eta.csv", sep=";")
i.columns = c_.columns = ["anno", "eta", "n"]
m = i.merge(c_, on=["anno", "eta"], suffixes=("_isc", "_canc")); m["saldo"] = m.n_isc - m.n_canc
m.to_csv(os.path.join(out, "flussi_eta_2020_2024.csv"), index=False)
def grp(e):
    k = int(e.split("-")[0].split(" ")[0])
    if k < 15: return "0-14"
    if k < 20: return "15-19"
    if k < 35: return "20-34"
    if k < 50: return "35-49"
    if k < 65: return "50-64"
    return "65+"
m["gruppo"] = m.eta.map(grp)
gg = m.groupby(["gruppo", "anno"])[["n_isc", "n_canc", "saldo"]].sum().reset_index()
res["eta_gruppi"] = {g: {int(r.anno): dict(isc=int(r.n_isc), canc=int(r.n_canc), saldo=int(r.saldo)) for r in x.itertuples()} for g, x in gg.groupby("gruppo")}
tt = m.groupby("gruppo")[["n_isc", "n_canc", "saldo"]].sum()
res["eta_gruppi_totale_2020_2024"] = tt.astype(int).to_dict("index")
res["eta_classe_max_saldo"] = m.groupby("eta").saldo.sum().sort_values(ascending=False).head(3).to_dict()
# luogo 2020-2024
p = pd.read_csv(f"{raw}/comune_ds1959/ds1959_popolazione_iscrizioni_evento_prov.csv", sep=";"); d = pd.read_csv(f"{raw}/comune_ds1960/ds1960_popolazione_cancellazioni_evento_dest.csv", sep=";")
p.columns = ["anno", "luogo", "isc"]; d.columns = ["anno", "luogo", "canc"]
x = p.merge(d, on=["anno", "luogo"]); x["saldo"] = x.isc - x.canc
x.to_csv(os.path.join(out, "flussi_luogo_2020_2024.csv"), index=False)
reg_sud = ["Abruzzo", "Basilicata", "Calabria", "Campania", "Molise", "Puglia", "Sardegna", "Sicilia"]
def zona(l):
    if l == "Prov. MI": return "Provincia di Milano (hinterland)"
    if l == "Altre prov. Lombardia": return "Resto della Lombardia"
    if l == "Estero": return "Estero"
    if l == "n.d.": return "Luogo non indicato"
    if l in reg_sud: return "Sud e isole (+Abruzzo, Molise)"
    if l in ("Piemonte", "Valle d'Aosta", "Liguria", "Emilia Romagna", "Veneto", "Friuli Venezia Giulia", "Trentino Alto Adige"): return "Nord (fuori Lombardia)"
    return "Centro (Lazio, Toscana, Umbria, Marche)"
x["zona"] = x.luogo.map(zona)
z = x.groupby(["zona", "anno"])[["isc", "canc", "saldo"]].sum().reset_index()
res["luogo_zone"] = {g: {int(r.anno): dict(isc=int(r.isc), canc=int(r.canc), saldo=int(r.saldo)) for r in y.itertuples()} for g, y in z.groupby("zona")}
res["luogo_zone_totale_2020_2024"] = z.groupby("zona")[["isc", "canc", "saldo"]].sum().astype(int).to_dict("index")
res["luogo_regioni_saldo_2020_2024"] = x.groupby("luogo").saldo.sum().sort_values().astype(int).to_dict()
tot = x.groupby("anno")[["isc", "canc"]].sum()
res["luogo_tot"] = tot.to_dict("index")
# destinazioni: quota delle cancellazioni verso altri comuni italiani (esclusi estero e n.d.)
ita = x[~x.luogo.isin(["Estero", "n.d."])].groupby("luogo").canc.sum()
res["quota_cancellazioni_italia_per_destinazione_2020_2024"] = (ita / ita.sum()).sort_values(ascending=False).head(8).round(4).to_dict()
# nil
rs = pd.read_csv(os.path.join(out, "flussi_nil_riepilogo.csv"))
for per in ("2012-2019", "2020-2024"):
    q = rs[(rs.periodo == per) & (rs.res >= 3000)]
    res[f"nil_{per}"] = dict(n_nil=int(len(q)), saldo_tot_negativo=int((q.saldo_tot_x1000_anno < 0).sum()), saldo_italia_negativo=int((q.saldo_italia_x1000_anno < 0).sum()), saldo_estero_positivo=int((q.saldo_estero_x1000_anno > 0).sum()),
                            peggiori=q.sort_values("saldo_tot_x1000_anno").head(6)[["nil", "res", "saldo_italia_x1000_anno", "saldo_estero_x1000_anno", "saldo_tot_x1000_anno"]].round(1).to_dict("records"),
                            migliori=q.sort_values("saldo_tot_x1000_anno").tail(6)[["nil", "res", "saldo_italia_x1000_anno", "saldo_estero_x1000_anno", "saldo_tot_x1000_anno"]].round(1).to_dict("records"))
json.dump(res, open(os.path.join(out, "riepilogo_A.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k in ("istat_totali_2002_2025", "istat_totali_2002_2010", "istat_totali_2012_2019", "istat_totali_2020_2025", "anni_saldo_interno_positivo", "istat_estero_per_cittadinanza_2002_2018", "eta_gruppi_totale_2020_2024", "luogo_zone_totale_2020_2024", "quota_cancellazioni_italia_per_destinazione_2020_2024"):
    print(k, json.dumps(res[k], ensure_ascii=False))
print(json.dumps(res["eta_gruppi"]["20-34"])); print(json.dumps(res["eta_gruppi"]["0-14"])); print(json.dumps(res["eta_gruppi"]["35-49"]))
print(json.dumps(res["luogo_zone"]["Provincia di Milano (hinterland)"])); print(json.dumps(res["luogo_zone"]["Sud e isole (+Abruzzo, Molise)"]))
print(json.dumps(res["evento_saldi"])); print(json.dumps(res["evento_estero_cittadinanza"]))
