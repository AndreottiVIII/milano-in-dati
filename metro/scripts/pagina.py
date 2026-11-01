"""Dati aggregati per la pagina docs/metro/ (solo aggregati; niente PDF, niente grafici copiati).
Legge metro/pulito/*.csv e scrive docs/metro/data/*.json|csv. Si puo' rilanciare senza effetti collaterali.
Uso: python -I -X utf8 pagina.py <metro_dir_assoluta> <docs_dir_assoluta>"""
import sys, os, csv, json, collections, statistics, datetime
M, DOCS = sys.argv[1], sys.argv[2]
P = os.path.join(M, "pulito")
OUT = os.path.join(DOCS, "metro", "data")
os.makedirs(OUT, exist_ok=True)
rd = lambda f: list(csv.DictReader(open(os.path.join(P, f), encoding="utf-8")))
LINEE = ["M1", "M2", "M3", "M4", "M5"]
R = {"generato": datetime.date.today().isoformat(), "origine": {}}

# ---------- passeggeri per linea e anno
lin = rd("metro_passeggeri_linea_anno.csv")
v = {(r["linea"], int(r["anno"])): float(r["passeggeri_mln"]) for r in lin}
anni = list(range(2016, 2026))
righe = []
for a in anni:
    row = {"anno": a}
    for l in LINEE: row[l] = round(v.get((l, a), 0.0), 1)
    row["totale"] = round(sum(v.get((l, a), 0.0) for l in LINEE), 1)
    row["fonte"] = "wikipedia_non_verificato" if a == 2025 else "grafico_amat_report_2024"
    righe.append(row)
with open(os.path.join(OUT, "passeggeri_linea_anno.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["anno"] + LINEE + ["totale", "fonte"]); w.writeheader(); w.writerows(righe)
R["linee_anno"] = righe

# ---------- rete: km e stazioni-linea (Carte ATM), passeggeri per km
carta = {int(r["anno_dati"]): r for r in rd("atm_carta_mobilita_numeri.csv")}
km = {a: float(carta[a]["lunghezza_metro_km"].replace(",", ".")) for a in anni}
stz = {a: int(carta[a]["stazioni_metro"]) for a in anni}
tot = {r["anno"]: r["totale"] for r in righe}
rete = [{"anno": a, "km": km[a], "stazioni_linea": stz[a], "linee": int(carta[a]["linee_metro"]), "passeggeri_mln": tot[a],
         "mln_per_km": round(tot[a] / km[a], 2)} for a in anni]
R["rete"] = rete
with open(os.path.join(OUT, "rete_km_passeggeri.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rete[0])); w.writeheader(); w.writerows(rete)
a19, a25 = rete[3], rete[9]
R["sorpresa"] = {
    "km_2019": a19["km"], "km_2025": a25["km"], "km_var_pct": round(100 * (a25["km"] / a19["km"] - 1), 1),
    "linee_2019": a19["linee"], "linee_2025": a25["linee"], "stazioni_linea_2019": a19["stazioni_linea"], "stazioni_linea_2025": a25["stazioni_linea"],
    "pass_2019": a19["passeggeri_mln"], "pass_2025": a25["passeggeri_mln"], "pass_var_pct": round(100 * (a25["passeggeri_mln"] / a19["passeggeri_mln"] - 1), 1),
    "perkm_2019": a19["mln_per_km"], "perkm_2025": a25["mln_per_km"], "perkm_var_pct": round(100 * (a25["mln_per_km"] / a19["mln_per_km"] - 1), 1),
    "m4_2024": v[("M4", 2024)], "m4_2025": round(v[("M4", 2025)], 1), "m4_delta": round(v[("M4", 2025)] - v[("M4", 2024)], 1),
    "m123_2024": round(sum(v[(l, 2024)] for l in ("M1", "M2", "M3")), 1), "m123_2025": round(sum(v[(l, 2025)] for l in ("M1", "M2", "M3")), 1),
    "delta_linea_2024_2025": {l: round(v[(l, 2025)] - v[(l, 2024)], 1) for l in LINEE},
}
R["sorpresa"]["m123_delta"] = round(R["sorpresa"]["m123_2025"] - R["sorpresa"]["m123_2024"], 1)
R["sorpresa"]["totale_delta"] = round(a25["passeggeri_mln"] - rete[8]["passeggeri_mln"], 1)
# covid per linea (solo le 4 linee che c'erano nel 2019)
cov = {}
for l in ("M1", "M2", "M3", "M5"):
    cov[l] = {str(a): round(100 * (v[(l, a)] / v[(l, 2019)] - 1), 1) for a in (2020, 2021, 2022, 2023, 2024, 2025)}
somma4 = lambda a: sum(v[(l, a)] for l in ("M1", "M2", "M3", "M5"))
cov["M1+M2+M3+M5"] = {str(a): round(100 * (somma4(a) / somma4(2019) - 1), 1) for a in (2020, 2024, 2025)}
R["covid"] = cov
R["origine"]["linee_anno"] = ("2016-2024: AMAT, Report della Mobilità 2024, pdf p. 48 (stampata 94), grafico 'Passeggeri rete metropolitana' letto dal vettoriale, ±0,5 mln, somma controllata sui totali "
                              "pubblicati (scarto sotto l'1%); 2025: it.wikipedia 'Metropolitana di Milano' che cita il Report AMAT 2025, non verificato.")
R["origine"]["rete"] = "ATM, Carte della Mobilità 2017-2026 (tabella 'ATM in numeri': lunghezza rete e stazioni-linea metro; anno dei dati = anno della Carta meno 1)."

# ---------- stazioni (mappa per anno di apertura)
st = rd("stazioni_metro.csv")
colonne = []
for r in st:
    ap = {}
    for p in r["apertura_per_linea_wikipedia"].split(";"):
        if ":" in p:
            l, d = p.split(":", 1); ap[l] = d
    first = min(ap.items(), key=lambda kv: kv[1]) if ap else ("", "")
    colonne.append({"n": r["stazione"], "lat": float(r["lat_gtfs"]), "lon": float(r["lon_gtfs"]), "l": sorted(ap), "ap": ap,
                    "y": int(first[1][:4]) if first[1] else None, "c": first[0],
                    "corse": int(r["corse_giorno_feriale_gtfs_rif_2026-11-11"])})
R["stazioni"] = colonne
anni_ap = collections.Counter(s["y"] for s in colonne)
R["stazioni_per_anno_prima_apertura"] = {str(k): n for k, n in sorted(anni_ap.items())}
with open(os.path.join(OUT, "stazioni_metro.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["stazione", "linee", "apertura_per_linea (da it.wikipedia, CC BY-SA 4.0)", "lat", "lon", "corse_giorno_feriale_orario_2026"])
    for s, r in zip(colonne, st): w.writerow([s["n"], r["linee"], r["apertura_per_linea_wikipedia"], s["lat"], s["lon"], s["corse"]])
R["origine"]["stazioni"] = "Elenco: filone nomi-fermate (GTFS ATM/AMAT, feed 425, CC-BY); date di apertura: it.wikipedia 'Stazioni della metropolitana di Milano' (CC BY-SA 4.0), scaricato 1/11/2026."

# ---------- Linate M4 mensile
lm = rd("report24_m4_linate_mese.csv")
R["linate"] = [{"mese": r["mese"], "migliaia": round(float(r["passeggeri_migliaia_letto_da_grafico"]))} for r in lm]
with open(os.path.join(OUT, "linate_m4_mese.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["mese", "passeggeri_migliaia_(letto_da_grafico,_+-3)"]); w.writerows([[x["mese"], x["migliaia"]] for x in R["linate"]])
R["origine"]["linate"] = "AMAT, Report della Mobilità 2024, pdf p. 81 (stampata 161), grafico 'n° passeggeri ingresso/uscita Linate M4', migliaia, letto dal vettoriale, ±3 mila."

# ---------- treni
tr = rd("stazioni_treno_covid_ripresa.csv")
treni = []
for r in tr:
    if not r["saliti_2019"] or not r["saliti_2025"]: continue
    treni.append({"n": r["stazione"], "s2019": int(float(r["saliti_2019"])), "s2020": int(float(r["saliti_2020"])), "s2025": int(float(r["saliti_2025"])),
                  "p20": float(r["pct_2020_su_2019"]), "p25": float(r["pct_2025_su_2019"]),
                  "arr": float(r["rapporto_discesi_su_saliti_7_9_2019"]) if r["rapporto_discesi_su_saliti_7_9_2019"] else None})
treni.sort(key=lambda t: t["p25"])
R["treni"] = treni
xs = [t["arr"] for t in treni if t["arr"]]; ys = [t["p25"] for t in treni if t["arr"]]
mx, my = statistics.mean(xs), statistics.mean(ys)
R["treni_corr"] = round(sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (sum((a - mx) ** 2 for a in xs) ** .5 * sum((b - my) ** 2 for b in ys) ** .5), 2)
R["treni_n"] = len(treni)
s19 = sum(t["s2019"] for t in treni)
R["treni_somma"] = {"2019": s19, "2020": sum(t["s2020"] for t in treni), "2025": sum(t["s2025"] for t in treni)}
R["treni_somma"]["p20"] = round(100 * R["treni_somma"]["2020"] / s19); R["treni_somma"]["p25"] = round(100 * R["treni_somma"]["2025"] / s19)
fr = rd("stazioni_treno_milano_frequentazione.csv")
wk = collections.defaultdict(int)
for r in fr:
    if r["anno"] == "2025" and r["mese_rilevazione"] == "11": wk[r["tipo_giorno"]] += int(float(r["saliti_24h"]))
R["treni_giorno_tipo_2025_nov"] = {"feriale": wk["Feriale"], "sabato": wk["Sabato"], "festivo": wk["Festivo"],
                                   "sabato_pct": round(100 * wk["Sabato"] / wk["Feriale"]), "festivo_pct": round(100 * wk["Festivo"] / wk["Feriale"])}
with open(os.path.join(OUT, "treni_stazioni_milano_2019_2020_2025.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["stazione_ferroviaria", "saliti_nov_feriale_2019", "saliti_nov_feriale_2020", "saliti_nov_feriale_2025", "pct_2020_su_2019", "pct_2025_su_2019", "discesi_su_saliti_7_9_2019"])
    for t in treni: w.writerow([t["n"], t["s2019"], t["s2020"], t["s2025"], t["p20"], t["p25"], t["arr"]])
R["origine"]["treni"] = "Regione Lombardia/Trenord, dati.lombardia.it 'Flussi Stazioni Ferroviarie' (m2u2-frtq) e 'Frequentazione delle stazioni del servizio ferroviario regionale' (ut63-s688), CC0, scaricati 1/11/2026. Treni, non metropolitana."

# ---------- corse GTFS
sv = rd("gtfs_metro_servizio_giorno.csv")
ag = collections.defaultdict(set)
for r in sv:
    k = "feriale" if r["giorno_settimana"] in ("Mon", "Tue", "Wed", "Thu", "Fri") else ("sabato" if r["giorno_settimana"] == "Sat" else "domenica")
    ag[(r["linea"], k)].add(int(r["corse"]))
corse = []
for l in LINEE:
    corse.append({"linea": l, **{k: [min(ag[(l, k)]), max(ag[(l, k)])] for k in ("feriale", "sabato", "domenica")}})
R["corse"] = corse
R["corse_totale"] = {k: [sum(c[k][0] for c in corse), sum(c[k][1] for c in corse)] for k in ("feriale", "sabato", "domenica")}
with open(os.path.join(OUT, "corse_giorno_per_linea.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["linea", "feriale_min", "feriale_max", "sabato_min", "sabato_max", "domenica_min", "domenica_max"])
    for c in corse: w.writerow([c["linea"]] + [x for k in ("feriale", "sabato", "domenica") for x in c[k]])
R["origine"]["corse"] = "GTFS ATM/AMAT, feed_version 425, valido 26/10-30/11/2026 (dati.comune.milano.it/gtfs.zip, CC-BY). Solo l'orario attuale."
R["rete_attuale"] = {"stazioni_distinte": len(colonne), "stazioni_linea": 134, "interscambio": sum(1 for s in colonne if len(s["l"]) > 1), "corse_media_2025_carta": 3261}

json.dump(R, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scritti:", sorted(os.listdir(OUT)))
print(R["sorpresa"])
