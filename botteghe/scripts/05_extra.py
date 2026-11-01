"""Extra: quadro regionale (elenco Regione Lombardia 19/10/2026, tutti i comuni), locali da ballo storici e mercati storici di Milano.
Scrive pulito/regione_lombardia_per_provincia.csv, regione_lombardia_per_tipo_milano_vs_resto.csv, locali_da_ballo_storici_milano.csv, mercati_storici_milano.csv.
Uso: python -I -X utf8 05_extra.py <botteghe abs>"""
import sys, csv, collections, json
import pandas as pd
B = sys.argv[1]
c = pd.read_csv(B + "/raw/lombardia/czq5-nkk7/czq5-nkk7.csv", dtype=str, keep_default_na=False)
prov = c.groupby("PR").size().reset_index(name="attivita").sort_values("attivita", ascending=False)
prov["quota_%"] = (prov.attivita / len(c) * 100).round(1)
prov.to_csv(B + "/pulito/regione_lombardia_per_provincia.csv", index=False)
c["milano_citta"] = c.COMUNE == "MILANO"
t = c.groupby(["milano_citta", "TIPO"]).size().reset_index(name="n")
t.to_csv(B + "/pulito/regione_lombardia_per_tipo_milano_vs_resto.csv", index=False)
top = c.groupby("COMUNE").size().sort_values(ascending=False).head(15)
c["inizio"] = pd.to_numeric(c.INIZIO_ATT, errors="coerce")
R = {"lombardia_righe": len(c), "lombardia_comuni": int(c.COMUNE.nunique()), "milano_citta": int(c.milano_citta.sum()), "milano_quota_%": round(c.milano_citta.mean() * 100, 1),
     "provincia_MI": int((c.PR == "MI").sum()), "top_comuni": top.to_dict(),
     "anno_inizio_mediano_lombardia": float(c.inizio.median()), "anno_inizio_mediano_milano": float(c[c.milano_citta].inizio.median()),
     "quota_prima_del_1900_lombardia_%": round((c.inizio < 1900).mean() * 100, 1), "quota_prima_del_1900_milano_%": round((c[c.milano_citta].inizio < 1900).mean() * 100, 1),
     "tipo_milano": c[c.milano_citta].TIPO.value_counts().to_dict(), "tipo_lombardia": c.TIPO.value_counts().to_dict()}
b = list(csv.DictReader(open(B + "/raw/lombardia/xguy-ssff/xguy-ssff.csv", encoding="utf-8-sig")))
m = [x for x in b if x["LOCALE_DA_BALLO_COMUNE"].upper() == "MILANO"]
with open(B + "/pulito/locali_da_ballo_storici_milano.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nome_locale", "indirizzo", "data_decreto", "fonte"])
    for x in m:
        w.writerow([x["LOCALE_DA_BALLO_DENOM"], x["LOCALE_DA_BALLO_INDIRIZZO"], x["DATA_DECRETO"], "Regione Lombardia xguy-ssff (CC0), scaricato 2026-11-01"])
mm = list(csv.DictReader(open(B + "/raw/lombardia/z47y-7rbf/z47y-7rbf.csv", encoding="utf-8-sig")))
mm = [x for x in mm if x["COMUNE"].upper() == "MILANO"]
with open(B + "/pulito/mercati_storici_milano.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ubicazione", "giorno", "anno_istituzione", "riconoscimento", "data_riconoscimento", "posti", "fonte"])
    for x in mm:
        w.writerow([x["UBICAZIONE"], x["GIORNO"], x["ANNOIST"], x["ESITOISTRU"], x["DRICON"][:8], x["TOTPOST"], "Regione Lombardia z47y-7rbf (CC0), dati 2012, scaricato 2026-11-01"])
R["locali_da_ballo_storici_milano"] = len(m)
R["mercati_storici_milano"] = len(mm)
R["mercati_storici_esiti"] = collections.Counter(x["ESITOISTRU"] for x in mm)
json.dump(R, open(B + "/pulito/regione_lombardia_riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
