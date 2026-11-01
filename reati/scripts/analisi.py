"""Riepiloghi dai file puliti. Uso: python -I -X utf8 analisi.py <reati> <milano-in-dati>
Scrive in pulito/: riepilogo_totale_100k.csv, riepilogo_rango_milano.csv, riepilogo_tipi_*.csv, riepilogo_covid.csv,
riepilogo_presenti_milano.csv, riepilogo.json ; stampa i numeri citati in NOTE.md in out/riepilogo.txt
"""
import sys, csv, json, os, collections
R, M = sys.argv[1], sys.argv[2]
OUT = f"{R}/pulito"
os.makedirs(f"{R}/out", exist_ok=True)
lines = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)
def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def wr(name, rows):
    with open(f"{OUT}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(rows[0].keys())); w.writeheader(); w.writerows(rows)

long_ = rd(f"{OUT}/delitti_tipo_territorio_anno.csv")
D = {}      # (codice, anno, tipo) -> (denunce, per100k calcolato, pop)
for r in long_:
    if r["denunce"] == "":
        continue
    D[(r["codice_istat"], int(r["anno"]), r["tipo_codice"])] = (int(r["denunce"]), float(r["per_100mila"]) if r["per_100mila"] else None,
                                                               int(r["popolazione_istat_implicita"]) if r["popolazione_istat_implicita"] else None)
NAME = {"IT": "Italia", "ITC45": "Milano prov.", "ITE43": "Roma prov.", "ITC11": "Torino prov.", "ITF33": "Napoli prov.",
        "ITD55": "Bologna prov.", "ITE14": "Firenze prov.", "015146": "Milano comune", "058091": "Roma comune",
        "001272": "Torino comune", "063049": "Napoli comune", "037006": "Bologna comune", "048017": "Firenze comune",
        "ITC45+IT108": "Milano+Monza"}
PROVS = ["ITC45", "ITE43", "ITC11", "ITF33", "ITD55", "ITE14", "IT"]
COMS = ["015146", "058091", "001272", "063049", "037006", "048017"]
YEARS = list(range(2006, 2025))
def v(c, y, t="TOT"):
    return D.get((c, y, t), (None, None, None))[1]
def n(c, y, t="TOT"):
    return D.get((c, y, t), (None, None, None))[0]

# 1. totale per 100.000: province, comuni, Milano+Monza
rows = []
for y in YEARS:
    r = {"anno": y}
    for c in PROVS + ["ITC45+IT108"] + COMS:
        r[NAME[c]] = round(v(c, y), 1) if v(c, y) is not None else ""
    rows.append(r)
wr("riepilogo_totale_100k.csv", rows)
P("== Totale delitti per 100.000 abitanti (provincia; ISTAT, denominatore implicito)")
P("anno | " + " | ".join(NAME[c] for c in PROVS + ["ITC45+IT108"]))
for y in YEARS:
    P(y, "|", " | ".join(f"{v(c, y):.0f}" if v(c, y) else "-" for c in PROVS + ["ITC45+IT108"]))
P("== Totale denunce assolute")
for y in (2006, 2010, 2011, 2019, 2020, 2021, 2024):
    P(y, {NAME[c]: n(c, y) for c in PROVS + ["ITC45+IT108", "015146"]})

# 2. rango di Milano tra le province (anno per anno), pubblicato e ricostruito
pt = rd(f"{OUT}/province_totale_anno.csv")
by = collections.defaultdict(list)
for r in pt:
    by[int(r["anno"])].append((float(r["per_100mila"]), r["codice_istat"], r["provincia"]))
rk = []
P("== Rango di Milano (provincia) per tasso totale tra le province ISTAT")
for y in YEARS:
    lst = sorted(by[y], reverse=True)
    pos = {c: i + 1 for i, (_, c, _) in enumerate(lst)}
    top = [f"{nm}({val:.0f})" for val, c, nm in lst[:5]]
    # ricostruzione: Milano+Monza unite (dal 2011)
    rec = ""
    if y >= 2011 and ("ITC45+IT108", y, "TOT") in D:
        comb = D[("ITC45+IT108", y, "TOT")][1]
        l2 = [(val, c) for val, c, _ in lst if c not in ("ITC45", "IT108")] + [(comb, "COMB")]
        l2.sort(reverse=True)
        rec = [c for _, c in l2].index("COMB") + 1
    rk.append({"anno": y, "rango_milano_pubblicato": pos["ITC45"], "n_province": len(lst), "rango_milano_con_monza": rec,
               "prime_cinque": "; ".join(top)})
    P(y, "rango", pos["ITC45"], "su", len(lst), "| con Monza:", rec, "| prime 5:", ", ".join(top))
wr("riepilogo_rango_milano.csv", rk)
# rango Milano comune tra 12 grandi comuni (ISTAT)
P("== Rango Milano tra i grandi comuni (12 comuni ISTAT, tasso totale CRIMET)")
big = collections.defaultdict(dict)
for r in rd(f"{R}/raw/istat/df8_grandi_comuni_CRIMET.csv"):
    if r["TYPE_CRIME"] == "TOT" and r["OBS_VALUE"]:
        big[int(r["TIME_PERIOD"])][r["REF_AREA"]] = float(r["OBS_VALUE"])
AREAN = json.load(open(f"{R}/raw/probe/codelists.json", encoding="utf8"))["CL_ITTER107"]
rows = []
for y in YEARS:
    s = sorted(big[y].items(), key=lambda kv: -kv[1])
    rows.append({"anno": y, "rango_milano": [k for k, _ in s].index("015146") + 1, "primo": AREAN[s[0][0]], "tasso_primo": s[0][1],
                 "tasso_milano": big[y]["015146"], "tasso_secondo": s[1][1], "secondo": AREAN[s[1][0]]})
    P(y, "Milano rango", rows[-1]["rango_milano"], "| primo", rows[-1]["primo"], s[0][1], "| Milano", big[y]["015146"])
wr("riepilogo_rango_grandi_comuni.csv", rows)

# 3. per tipo: Milano comune (confini stabili) vs altri; tassi per 100k in anni chiave
KEY = ["THEFT", "PICKTHEF", "BAGTHEF", "BURGTHEF", "VEHITHEF", "SHOPTHEF", "CARTHEF", "MOTORTHEF", "MOPETHEF", "ROBBER", "STREETROB",
       "INTENHOM", "ATTEMPHOM", "CULPINJU", "BLOWS", "MENACE", "OFFENCE", "RAPE", "RAPEUN18", "SWINCYB", "CYBERCRIM", "DRUG", "DAMAGE",
       "EXTORT", "ARSON", "COUNTER", "RECEIV", "MONEYLAU", "OTHCRIM", "TOT"]
LABEL = {r["tipo_codice"]: r["tipo_delitto"] for r in long_}
def tab(code, years, name):
    rows = []
    for t in KEY:
        r = {"tipo_codice": t, "tipo_delitto": LABEL[t]}
        for y in years:
            r[f"denunce_{y}"] = n(code, y, t) if n(code, y, t) is not None else ""
            r[f"per100k_{y}"] = round(v(code, y, t), 1) if v(code, y, t) is not None else ""
        rows.append(r)
    wr(name, rows)
    return rows
YK = [2006, 2010, 2011, 2019, 2020, 2021, 2024]
for code, nm in [("015146", "milano_comune"), ("ITC45", "milano_provincia"), ("ITE43", "roma_provincia"), ("ITC11", "torino_provincia"),
                 ("ITF33", "napoli_provincia"), ("ITD55", "bologna_provincia"), ("ITE14", "firenze_provincia"), ("IT", "italia"),
                 ("058091", "roma_comune"), ("001272", "torino_comune"), ("063049", "napoli_comune"), ("037006", "bologna_comune"), ("048017", "firenze_comune")]:
    tab(code, YK, f"riepilogo_tipi_{nm}.csv")
P("== Per tipo, per 100.000: Milano comune vs Milano provincia vs Roma, Torino, Napoli, Bologna, Firenze (province), Italia - anno 2024 e 2019")
for y in (2019, 2024):
    P("-- anno", y)
    P("tipo | MI com | MI prov | Roma | Torino | Napoli | Bologna | Firenze | Italia")
    for t in KEY:
        P(LABEL[t][:48], "|", " | ".join(f"{v(c, y, t):.1f}" if v(c, y, t) is not None else "-" for c in ["015146", "ITC45", "ITE43", "ITC11", "ITF33", "ITD55", "ITE14", "IT"]))

# 4. variazioni nel tempo: Milano comune e provincia (2011->2024 confini coerenti per la provincia; 2006->2024 per il comune), Italia
P("== Variazione del tasso per 100.000, Milano comune: 2006->2024, 2011->2024, 2019->2024; Italia stessi intervalli (tipi con >=150 denunce nel 2019)")
chg = []
for t in KEY:
    row = {"tipo_codice": t, "tipo_delitto": LABEL[t]}
    for (a, b) in [(2006, 2024), (2011, 2024), (2019, 2024), (2019, 2020), (2019, 2021)]:
        for c, nm in [("015146", "mi_comune"), ("ITC45", "mi_prov"), ("IT", "italia")]:
            x, z = v(c, a, t), v(c, b, t)
            row[f"{nm}_{a}_{b}_%"] = round((z / x - 1) * 100, 1) if x and z is not None else ""
    row["denunce_mi_comune_2019"] = n("015146", 2019, t)
    row["denunce_mi_comune_2024"] = n("015146", 2024, t)
    chg.append(row)
wr("riepilogo_variazioni.csv", chg)
for r in sorted([r for r in chg if (r["denunce_mi_comune_2019"] or 0) >= 150 and r["mi_comune_2019_2024_%"] != ""], key=lambda r: r["mi_comune_2019_2024_%"]):
    P(f"{r['tipo_delitto'][:46]:46s} den2019 {r['denunce_mi_comune_2019']:>7} den2024 {r['denunce_mi_comune_2024']:>7} | MI 06-24 {r['mi_comune_2006_2024_%']} 11-24 {r['mi_comune_2011_2024_%']} 19-24 {r['mi_comune_2019_2024_%']} | covid 19-20 {r['mi_comune_2019_2020_%']} (Italia {r['italia_2019_2020_%']}) 19-21 {r['mi_comune_2019_2021_%']} | Italia 19-24 {r['italia_2019_2024_%']}")

# 5. Covid, totali
P("== Covid, totale denunce e tasso: 2019, 2020, 2021, 2022, 2024")
cov = []
for c in ["015146", "ITC45", "ITE43", "ITC11", "ITF33", "ITD55", "ITE14", "IT"]:
    x = {y: v(c, y) for y in (2019, 2020, 2021, 2022, 2023, 2024)}
    cov.append({"territorio": NAME[c], **{f"per100k_{y}": round(x[y], 1) for y in x},
                "var_2020_su_2019_%": round((x[2020] / x[2019] - 1) * 100, 1), "var_2021_su_2019_%": round((x[2021] / x[2019] - 1) * 100, 1),
                "var_2024_su_2019_%": round((x[2024] / x[2019] - 1) * 100, 1)})
    P(cov[-1])
wr("riepilogo_covid.csv", cov)

# 6. presenti: turisti + pendolari (Milano comune)
tur = {int(r["anno"]): float(r["pres_tot"]) for r in rd(f"{M}/turisti/pulito/riepilogo_italiani_stranieri.csv")}
def readsc(p, enc, delim, col):
    rows = list(csv.reader(open(p, encoding=enc), delimiter=delim))
    return sum(float(r[col].replace(",", ".")) for r in rows[1:])
inflow = readsc(f"{R}/raw/comune_ds395/x/395_14_Pendolarismo_perMI_caratteristiche.csv", "latin-1", ";", 8)
outflow = readsc(f"{R}/raw/comune_ds345/ds345.csv", "utf-8-sig", ";", 7)
P("== Milano comune: pendolari 2011 (censimento) entrata", round(inflow), "uscita", round(outflow), "saldo", round(inflow - outflow))
rows = []
for y in YEARS:
    nn, rate_, pop_ = D.get(("015146", y, "TOT"), (None, None, None))
    if not nn:
        continue
    t_avg = tur.get(y, 0) / 365 if y in tur else None
    r = {"anno": y, "denunce_comune": nn, "residenti_istat_implicito": pop_, "per100k_residenti": round(nn / pop_ * 1e5, 1),
         "presenze_turistiche_notti": int(tur[y]) if y in tur else "", "turisti_medi_al_giorno": round(t_avg) if t_avg is not None else ""}
    if t_avg is not None:
        r["per100k_residenti_piu_turisti"] = round(nn / (pop_ + t_avg) * 1e5, 1)
        r["per100k_residenti_turisti_e_saldo_pendolari2011"] = round(nn / (pop_ + t_avg + (inflow - outflow)) * 1e5, 1)
        r["per100k_residenti_turisti_e_pendolari_in_entrata2011"] = round(nn / (pop_ + t_avg + inflow) * 1e5, 1)
    rows.append(r)
wr("riepilogo_presenti_milano.csv", rows)
P("== Milano comune: tasso su residenti / +turisti / +turisti+saldo pendolari / +turisti+tutti i pendolari in entrata")
for r in rows:
    P(r["anno"], r["denunce_comune"], r["residenti_istat_implicito"], r["per100k_residenti"], r.get("turisti_medi_al_giorno"), r.get("per100k_residenti_piu_turisti"),
      r.get("per100k_residenti_turisti_e_saldo_pendolari2011"), r.get("per100k_residenti_turisti_e_pendolari_in_entrata2011"))

# 7. serie del comune ds564 2004-2023 (per 100k su residenti del Comune)
c564 = rd(f"{OUT}/milano_comune_ds564.csv")
P("== Comune di Milano ds564, totale e per 100.000 residenti (ds27), 2004-2023")
for r in c564:
    if r["tipo_codice"] == "TOT":
        P(r["anno"], r["denunce_comune"], r["residenti_comune_31dic"], r["per_100mila_residenti"])
# 8. quota dei tipi sul totale Milano comune 2024 e 2006
P("== Composizione 2024 e 2006: quota % sul totale (Milano comune)")
for t in ["THEFT", "DAMAGE", "SWINCYB", "ROBBER", "CULPINJU", "MENACE", "DRUG", "RAPE", "OTHCRIM", "RECEIV", "EXTORT", "BLOWS"]:
    P(LABEL[t][:40], f"2024: {n('015146', 2024, t) / n('015146', 2024) * 100:.1f}%", f"2006: {n('015146', 2006, t) / n('015146', 2006) * 100:.1f}%")
P("Furti, di cui destrezza+scippo+abitazione+auto in sosta+negozio, 2024 e 2006, quota di furti Milano comune")
for t in ["PICKTHEF", "BAGTHEF", "BURGTHEF", "VEHITHEF", "SHOPTHEF", "CARTHEF"]:
    P(LABEL[t][:30], f"2024: {n('015146', 2024, t) / n('015146', 2024, 'THEFT') * 100:.1f}%", f"2006: {n('015146', 2006, t) / n('015146', 2006, 'THEFT') * 100:.1f}%")
open(f"{R}/out/riepilogo.txt", "w", encoding="utf8").write("\n".join(lines))
# 9. scomposizione del divario con l'Italia (tasso per 100.000), per grandi gruppi
TOPS = ["THEFT", "DAMAGE", "SWINCYB", "CYBERCRIM", "ROBBER", "DRUG", "CULPINJU", "BLOWS", "MENACE", "RAPE", "INTENHOM", "ATTEMPHOM", "EXTORT", "RECEIV", "OTHCRIM"]
P("== Scomposizione: tasso Milano - tasso Italia, per gruppo di delitti (per 100.000); quota del divario")
dec = []
for y in (2019, 2024):
    for c in ("015146", "ITC45", "ITE43"):
        gap = v(c, y) - v("IT", y)
        used = 0
        for t in TOPS:
            d = v(c, y, t) - v("IT", y, t); used += d
            dec.append({"anno": y, "territorio": NAME[c], "tipo_codice": t, "tipo_delitto": LABEL[t], "diff_per100k_vs_italia": round(d, 1),
                        "quota_del_divario_%": round(d / gap * 100, 1), "divario_totale": round(gap, 1)})
        dec.append({"anno": y, "territorio": NAME[c], "tipo_codice": "ALTRI", "tipo_delitto": "Tutti gli altri tipi", "diff_per100k_vs_italia": round(gap - used, 1),
                    "quota_del_divario_%": round((gap - used) / gap * 100, 1), "divario_totale": round(gap, 1)})
wr("riepilogo_scomposizione_divario.csv", dec)
for r in dec:
    if r["anno"] == 2024 and r["territorio"] in ("Milano comune", "Milano prov.", "Roma prov.") and abs(r["quota_del_divario_%"]) >= 2:
        P(r["anno"], r["territorio"], r["tipo_delitto"][:40], r["diff_per100k_vs_italia"], f"{r['quota_del_divario_%']}% di {r['divario_totale']}")

# 10. notti turistiche per residente (ISTAT movimento clienti, provincia; Milano = comune dal Comune)
tr = rd(f"{R}/raw/istat/tur7_6aree.csv")
nights = {}
for r in tr:
    if r["DATA_TYPE"] == "NI" and r["TYPE_ACCOMMODATION"] == "ALL" and r["COUNTRY_RES_GUESTS"] == "WORLD" and r["OBS_VALUE"]:
        nights[(r["REF_AREA"], int(r["TIME_PERIOD"]))] = float(r["OBS_VALUE"])
P("== Turisti medi al giorno (notti/365) ogni 100 residenti; ISTAT TUR_7 (province) e Comune di Milano (comune)")
rows = []
for y in YEARS:
    r = {"anno": y}
    for c in ["ITE43", "ITC11", "ITF33", "ITD55", "ITE14", "IT"]:
        if (c, y) in nights and (c, y, "TOT") in D:
            r[NAME[c]] = round(nights[(c, y)] / 365 / D[(c, y, "TOT")][2] * 100, 1)
    if y in tur and ("015146", y, "TOT") in D:
        r["Milano comune"] = round(tur[y] / 365 / D[("015146", y, "TOT")][2] * 100, 1)
    rows.append(r)
    P(r)
allk = sorted({k for r in rows for k in r})
for r in rows:
    for k in allk:
        r.setdefault(k, "")
wr("riepilogo_turisti_per_residente.csv", rows)
open(f"{R}/out/riepilogo.txt", "w", encoding="utf8").write(chr(10).join(lines))
