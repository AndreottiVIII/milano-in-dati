"""Scrive i file dati della pagina "Gli sfratti" (docs/sfratti/data/).

Uso (percorsi assoluti, rilanciabile):
  python -I -X utf8 pagina.py <sfratti_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge: sfratti/pulito/{serie_unita,famiglie_per_anno,famiglie_territori,province_2013_2025,grandi_province_2001_2012,italia_2001_2025}.csv,
       costo-vita/pulito/affitto_vs_reddito.csv e nic_milano_voci_base2015.csv (solo per il confronto con gli affitti).
Scrive in <docs_dir>/sfratti/data/: riepilogo.json (serie e numeri della pagina), serie_unita.csv, province_2013_2025.csv,
       grandi_province_2001_2012.csv, italia_2001_2025.csv, famiglie_per_anno.csv.
Dati aggregati ufficiali (Ministero dell'Interno, ISTAT): nessun dato personale.
"""
import sys, os, csv, json, shutil, datetime, collections

S, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(S, "pulito")
OUT = os.path.join(DOCS, "sfratti", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0.0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

def leggi(path):
    return list(csv.DictReader(open(path, encoding="utf8"), delimiter=";"))
def fl(x):
    return None if x in (None, "") else float(x)

serie = leggi(os.path.join(PU, "serie_unita.csv"))
by = {(r["unita"], int(r["anno"])): r for r in serie}
UN = ["Italia", "Milano (provincia con Monza e Brianza)", "Milano (provincia senza Monza)", "Comune di Milano", "Torino", "Roma", "Napoli", "Bologna", "Firenze",
      "Comune di Torino", "Comune di Roma", "Comune di Napoli", "Comune di Bologna", "Comune di Firenze"]
SIGLA = {u: u for u in UN}

# ----------------------------------------------------------------------- serie per la pagina
out_serie = {}
for u in UN:
    righe = []
    for a in range(2001, 2026):
        r = by.get((u, a))
        if not r:
            continue
        righe.append(dict(
            a=a, em=fl(r["emessi"]), ric=fl(r["richieste"]), ese=fl(r["eseguiti"]), nec=fl(r["nec"]), fin=fl(r["fin"]), mor=fl(r["mor"]),
            fam=fl(r["famiglie"]), r_em=fl(r["emessi_per_1000_fam"]), r_ric=fl(r["richieste_per_1000_fam"]), r_ese=fl(r["eseguiti_per_1000_fam"]),
            mor_pct=fl(r["quota_morosita_pct"]), nota=r["note"], orig_fam=r["origine_famiglie"]))
    out_serie[u] = righe

# ----------------------------------------------------------------------- controlli sui dati di partenza (valori letti a mano nei file del Ministero)
MIL = "Milano (provincia con Monza e Brianza)"
def v(u, a, k):
    return fl(by[(u, a)][k])
# 2010: Milano 6.466 (PDF 2012, Tab. 24), 2025: Milano 1.834 + Monza 634 (file dati_2025)
check("Milano 2010 emessi", v(MIL, 2010, "emessi"), 6466)
check("Milano+Monza 2025 emessi", v(MIL, 2025, "emessi"), 1834 + 634)
check("Milano senza Monza 2025 emessi", v("Milano (provincia senza Monza)", 2025, "emessi"), 1834)
check("Comune di Milano 2025 emessi (343+0+764)", v("Comune di Milano", 2025, "emessi"), 343 + 764)
check("Italia 2019 emessi", v("Italia", 2019, "emessi"), 49459)
check("Italia 2020 eseguiti", v("Italia", 2020, "eseguiti"), 5270)
check("Italia 2025 richieste", v("Italia", 2025, "richieste"), 61856)
# i tassi sono ricalcolati qui con un calcolo indipendente
fam = {(r["unita"], int(r["anno"])): float(r["famiglie"]) for r in leggi(os.path.join(PU, "famiglie_per_anno.csv"))}
check("tasso Milano 2025 ricalcolato", round(1000 * 2468 / fam[(MIL, 2025)], 3), v(MIL, 2025, "emessi_per_1000_fam"), 0.001)

# ----------------------------------------------------------------------- numeri principali
def ser(u, k):
    return {a: r[k] for a, r in ((a, by[(u, a)]) for a in range(2001, 2026) if (u, a) in by)}
rm = {a: v(MIL, a, "emessi_per_1000_fam") for a in range(2001, 2026)}
ri = {a: v("Italia", a, "emessi_per_1000_fam") for a in range(2001, 2026)}
sopra = [a for a in range(2001, 2026) if rm[a] > ri[a]]
sotto_dal = None
for a in range(2025, 2000, -1):
    if rm[a] < ri[a]:
        sotto_dal = a
    else:
        break
picco_a = max(range(2010, 2026), key=lambda a: rm[a])
picco_2013_2019 = max(range(2013, 2020), key=lambda a: rm[a])
N = {}
N["tasso_milano_2025"] = rm[2025]; N["tasso_italia_2025"] = ri[2025]
N["tasso_milano_picco_anno"] = picco_a; N["tasso_milano_picco"] = rm[picco_a]
N["tasso_milano_2014"] = rm[2014]; N["tasso_italia_2014"] = ri[2014]
N["tasso_milano_2019"] = rm[2019]; N["tasso_milano_2020"] = rm[2020]
N["anni_milano_sopra_italia"] = sopra
N["milano_sotto_italia_di_seguito_dal"] = sotto_dal
N["calo_tasso_milano_2014_2025_pct"] = round(100 * (rm[2025] / rm[2014] - 1), 1)
N["calo_tasso_italia_2014_2025_pct"] = round(100 * (ri[2025] / ri[2014] - 1), 1)
N["emessi_milano_2014"] = v(MIL, 2014, "emessi"); N["emessi_milano_2025"] = v(MIL, 2025, "emessi")
N["emessi_milano_senza_monza_2025"] = v("Milano (provincia senza Monza)", 2025, "emessi")
N["emessi_comune_milano_2013"] = v("Comune di Milano", 2013, "emessi"); N["emessi_comune_milano_2025"] = v("Comune di Milano", 2025, "emessi")
N["tasso_comune_milano_2013"] = v("Comune di Milano", 2013, "emessi_per_1000_fam"); N["tasso_comune_milano_2025"] = v("Comune di Milano", 2025, "emessi_per_1000_fam")
N["emessi_milano_2001"] = v(MIL, 2001, "emessi"); N["emessi_milano_2009"] = v(MIL, 2009, "emessi"); N["emessi_milano_2010"] = v(MIL, 2010, "emessi")
N["italia_emessi_2009"] = v("Italia", 2009, "emessi"); N["italia_emessi_2010"] = v("Italia", 2010, "emessi")
N["salto_milano_2009_2010_pct"] = round(100 * (v(MIL, 2010, "emessi") / v(MIL, 2009, "emessi") - 1), 1)
N["salto_italia_2009_2010_pct"] = round(100 * (v("Italia", 2010, "emessi") / v("Italia", 2009, "emessi") - 1), 1)
# Covid, Italia (serie del Ministero)
for k, nm in (("emessi", "emessi"), ("richieste", "richieste"), ("eseguiti", "eseguiti")):
    N[f"italia_{nm}_2019"] = v("Italia", 2019, k); N[f"italia_{nm}_2020"] = v("Italia", 2020, k)
    N[f"italia_{nm}_2021"] = v("Italia", 2021, k); N[f"italia_{nm}_2022"] = v("Italia", 2022, k)
    N[f"italia_var_{nm}_2020_pct"] = round(100 * (v("Italia", 2020, k) / v("Italia", 2019, k) - 1), 1)
N["italia_richieste_2022_su_2021"] = round(v("Italia", 2022, "richieste") / v("Italia", 2021, "richieste"), 2)
N["milano_emessi_2019"] = v(MIL, 2019, "emessi"); N["milano_emessi_2020_derivato"] = v(MIL, 2020, "emessi")
N["milano_var_emessi_2020_pct_derivata"] = round(100 * (v(MIL, 2020, "emessi") / v(MIL, 2019, "emessi") - 1), 1)
# motivi
N["mor_pct_comune_milano_2013"] = v("Comune di Milano", 2013, "quota_morosita_pct"); N["mor_pct_comune_milano_2025"] = v("Comune di Milano", 2025, "quota_morosita_pct")
N["fin_comune_milano_2013"] = v("Comune di Milano", 2013, "fin"); N["fin_comune_milano_2025"] = v("Comune di Milano", 2025, "fin")
N["mor_pct_italia_2012"] = v("Italia", 2012, "quota_morosita_pct"); N["mor_pct_italia_2019"] = v("Italia", 2019, "quota_morosita_pct")
N["mor_pct_italia_2025"] = v("Italia", 2025, "quota_morosita_pct")
N["fin_italia_2019"] = v("Italia", 2019, "fin"); N["fin_italia_2025"] = v("Italia", 2025, "fin")
N["fin_italia_var_2019_2025_pct"] = round(100 * (N["fin_italia_2025"] / N["fin_italia_2019"] - 1), 1)
N["nec_italia_2025"] = v("Italia", 2025, "nec")
N["mor_italia_2019"] = v("Italia", 2019, "mor"); N["mor_italia_2025"] = v("Italia", 2025, "mor")
N["mor_italia_var_2019_2025_pct"] = round(100 * (N["mor_italia_2025"] / N["mor_italia_2019"] - 1), 1)
# richieste ed esecuzioni Milano
rr = {a: v(MIL, a, "richieste") for a in range(2001, 2026)}
N["richieste_milano_min"] = [min(rr, key=rr.get), min(rr.values())]
N["richieste_milano_max"] = [max(rr, key=rr.get), max(rr.values())]
N["richieste_milano_2015"] = rr[2015]; N["richieste_milano_2020"] = rr[2020]; N["richieste_milano_2023"] = rr[2023]; N["richieste_milano_2024"] = rr[2024]; N["richieste_milano_2025"] = rr[2025]
N["eseguiti_milano_2019"] = v(MIL, 2019, "eseguiti"); N["eseguiti_milano_2025"] = v(MIL, 2025, "eseguiti")
N["richieste_su_emessi_milano_2019"] = round(v(MIL, 2019, "richieste") / v(MIL, 2019, "emessi"), 1)
N["richieste_su_emessi_italia_2019"] = round(v("Italia", 2019, "richieste") / v("Italia", 2019, "emessi"), 1)
N["quota_milano_richieste_italia_2019_pct"] = round(100 * v(MIL, 2019, "richieste") / v("Italia", 2019, "richieste"), 1)
N["quota_milano_emessi_italia_2019_pct"] = round(100 * v(MIL, 2019, "emessi") / v("Italia", 2019, "emessi"), 1)
N["quota_milano_richieste_italia_2023_pct"] = round(100 * v(MIL, 2023, "richieste") / v("Italia", 2023, "richieste"), 1)
N["quota_milano_richieste_italia_2024_pct"] = round(100 * v(MIL, 2024, "richieste") / v("Italia", 2024, "richieste"), 1)
N["eseguiti_su_emessi_italia"] = {a: round(v("Italia", a, "eseguiti") / v("Italia", a, "emessi"), 2) for a in (2004, 2010, 2019, 2022, 2025)}
# confronto fra citta': ultimo anno, 2019 e 2014
cit = ["Milano (provincia con Monza e Brianza)", "Torino", "Roma", "Napoli", "Bologna", "Firenze", "Italia"]
N["tassi_2025"] = {u: v(u, 2025, "emessi_per_1000_fam") for u in cit}
N["tassi_2019"] = {u: v(u, 2019, "emessi_per_1000_fam") for u in cit}
N["tassi_2014"] = {u: v(u, 2014, "emessi_per_1000_fam") for u in cit}
N["tassi_media_2022_2025"] = {u: round(sum(v(u, a, "emessi_per_1000_fam") for a in range(2022, 2026)) / 4, 3) for u in cit}
ordine25 = sorted(cit[:-1], key=lambda u: -N["tassi_2025"][u])
N["ordine_2025"] = ordine25
# per 1.000 famiglie in affitto (affittuari al censimento 2011)
fam_t = leggi(os.path.join(PU, "famiglie_territori.csv"))
aff = collections.defaultdict(float)
for r in fam_t:
    if r["tipo_dato"] == "famiglie_in_affitto" and r["tipo"] == "provincia":
        aff[r["territorio"]] += float(r["famiglie"])
tot11 = collections.defaultdict(float)
for r in fam_t:
    if r["tipo_dato"] == "famiglie_censimento" and r["anno"] == "2011" and r["tipo"] in ("provincia", "paese"):
        tot11[r["territorio"]] += float(r["famiglie"])
N["affittuari_2011"] = {"Milano (provincia con Monza e Brianza)": aff["Milano"] + aff["Monza e della Brianza"], "Torino": aff["Torino"], "Roma": aff["Roma"], "Napoli": aff["Napoli"],
                        "Bologna": aff["Bologna"], "Firenze": aff["Firenze"]}
N["quota_affitto_2011_pct"] = {"Milano (provincia con Monza e Brianza)": round(100 * (aff["Milano"] + aff["Monza e della Brianza"]) / (tot11["Milano"] + tot11["Monza e della Brianza"]), 1),
                               "Torino": round(100 * aff["Torino"] / tot11["Torino"], 1), "Roma": round(100 * aff["Roma"] / tot11["Roma"], 1), "Napoli": round(100 * aff["Napoli"] / tot11["Napoli"], 1),
                               "Bologna": round(100 * aff["Bologna"] / tot11["Bologna"], 1), "Firenze": round(100 * aff["Firenze"] / tot11["Firenze"], 1)}
N["tassi_2025_su_affittuari_2011"] = {u: round(1000 * v(u, 2025, "emessi") / N["affittuari_2011"][u], 2) for u in N["affittuari_2011"]}
# comuni capoluogo, 2025 (solo emessi nel capoluogo)
N["tassi_comuni_2025"] = {u: v(u, 2025, "emessi_per_1000_fam") for u in ("Comune di Milano", "Comune di Torino", "Comune di Roma", "Comune di Napoli", "Comune di Bologna", "Comune di Firenze")}
N["emessi_comuni_2025"] = {u: v(u, 2025, "emessi") for u in N["tassi_comuni_2025"]}
N["tassi_comuni_2019"] = {u: v(u, 2019, "emessi_per_1000_fam") for u in N["tassi_comuni_2025"]}
# affitti (confronto)
omi = {int(r["anno"]): fl(r["affitto_civ_eur_m2_mese"]) for r in leggi(os.path.join(P, "costo-vita", "pulito", "affitto_vs_reddito.csv"))}
istat = collections.defaultdict(list)
for r in leggi(os.path.join(P, "costo-vita", "pulito", "nic_milano_voci_base2015.csv")):
    if r["voce"] == "affitti":
        istat[int(r["periodo"][:4])].append(float(r["indice_base2015_100"]))
affitti = []
for a in range(2013, 2026):
    if a in istat:
        affitti.append(dict(a=a, omi=omi.get(a), istat=round(sum(istat[a]) / len(istat[a]), 2), mesi=len(istat[a])))
N["omi_2013"] = omi[2013]; N["omi_2024"] = omi[2024]; N["omi_var_2013_2024_pct"] = round(100 * (omi[2024] / omi[2013] - 1), 1)
i13 = [x for x in affitti if x["a"] == 2013][0]["istat"]; i25 = [x for x in affitti if x["a"] == 2025][0]["istat"]
N["istat_affitti_2013"] = i13; N["istat_affitti_2025"] = i25; N["istat_affitti_var_2013_2025_pct"] = round(100 * (i25 / i13 - 1), 1)
N["calo_tasso_milano_2013_2025_pct"] = round(100 * (rm[2025] / rm[2013] - 1), 1)
N["tasso_milano_2013"] = rm[2013]
N["nota_incompleti_milano"] = [a for a in range(2001, 2026) if "incompleti" in by[(MIL, a)]["note"]]

# ----------------------------------------------------------------------- scrittura
json.dump(dict(
    generato=datetime.date.today().isoformat(),
    serie=out_serie, numeri=N, affitti=affitti,
    unita=UN,
    famiglie_note="censimenti 2001 e 2011, censimento permanente 2018-2024, interpolazione lineare negli anni in mezzo, 2025 = 2024",
), open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
for fn in ("serie_unita.csv", "province_2013_2025.csv", "grandi_province_2001_2012.csv", "italia_2001_2025.csv", "famiglie_per_anno.csv"):
    shutil.copyfile(os.path.join(PU, fn), os.path.join(OUT, fn))
print("\nAVVISI:", AVVISI or "nessuno")
print(json.dumps({k: N[k] for k in ("tasso_milano_2025", "tasso_italia_2025", "tasso_milano_picco_anno", "tasso_milano_picco", "milano_sotto_italia_di_seguito_dal", "calo_tasso_milano_2014_2025_pct", "calo_tasso_italia_2014_2025_pct", "salto_milano_2009_2010_pct", "salto_italia_2009_2010_pct", "ordine_2025", "tassi_2025", "quota_affitto_2011_pct", "tassi_2025_su_affittuari_2011", "omi_var_2013_2024_pct", "istat_affitti_var_2013_2025_pct", "calo_tasso_milano_2013_2025_pct", "richieste_milano_min", "richieste_milano_max", "quota_milano_richieste_italia_2019_pct", "quota_milano_emessi_italia_2019_pct", "tassi_comuni_2025", "tassi_comuni_2019", "anni_milano_sopra_italia", "mor_pct_comune_milano_2013", "mor_pct_comune_milano_2025", "mor_pct_italia_2012", "mor_pct_italia_2025", "fin_italia_var_2019_2025_pct", "mor_italia_var_2019_2025_pct", "italia_var_emessi_2020_pct", "italia_var_richieste_2020_pct", "italia_var_eseguiti_2020_pct", "italia_richieste_2022_su_2021", "milano_var_emessi_2020_pct_derivata", "eseguiti_su_emessi_italia", "richieste_su_emessi_milano_2019", "richieste_su_emessi_italia_2019")}, ensure_ascii=False, indent=1))
