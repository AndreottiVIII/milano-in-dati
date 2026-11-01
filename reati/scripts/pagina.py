"""Scrive i dati della pagina (docs/reati/data/) a partire da reati/pulito/.
Uso: python -I -X utf8 pagina.py <percorso assoluto di reati> <percorso assoluto di docs>
Rieseguibile: riscrive sempre tutti i file. L'index.html e' scritto a mano e legge questi file.
Fonti: ISTAT esploradati (CC BY 4.0), Comune di Milano ds564/ds395/ds345 (CC BY); aggregati, nessun dato personale.
"""
import sys, os, csv, json, shutil, collections
R, DOCS = sys.argv[1], sys.argv[2]
PUL = f"{R}/pulito"
OUT = f"{DOCS}/reati/data"
os.makedirs(OUT, exist_ok=True)

def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))
def dump(name, obj):
    with open(f"{OUT}/{name}", "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    print(("OK   " if ok else "ERRORE ") + nome, calcolato, atteso)
    if not ok:
        raise SystemExit(1)

long_ = rd(f"{PUL}/delitti_tipo_territorio_anno.csv")
D = {}
for r in long_:
    if r["denunce"] != "":
        D[(r["codice_istat"], int(r["anno"]), r["tipo_codice"])] = {
            "n": int(r["denunce"]), "r": float(r["per_100mila"]) if r["per_100mila"] else None,
            "p": int(r["popolazione_istat_implicita"]) if r["popolazione_istat_implicita"] else None,
            "nome": r["tipo_delitto"], "gruppo": r["gruppo"]}
YEARS = list(range(2006, 2025))
def rate(c, y, t="TOT"):
    x = D.get((c, y, t)); return x["r"] if x else None
def cnt(c, y, t="TOT"):
    x = D.get((c, y, t)); return x["n"] if x else None
def r1(x):
    return None if x is None else round(x, 1)

# --- controlli sui numeri-chiave (devono coincidere con NOTE.md)
check("tasso totale Milano prov 2024", round(rate("ITC45", 2024)), 6989)
check("tasso totale Italia 2024", round(rate("IT", 2024)), 4070)
check("denunce comune Milano 2024", cnt("015146", 2024), 140974)
check("tasso comune Milano 2006", round(rate("015146", 2006)), 13025)

# --- 1. serie del tasso totale
KEYS = [("milano_monza", "ITC45+IT108"), ("milano_prov", "ITC45"), ("milano_comune", "015146"), ("roma", "ITE43"), ("torino", "ITC11"),
        ("napoli", "ITF33"), ("bologna", "ITD55"), ("firenze", "ITE14"), ("italia", "IT")]
serie = {"anni": YEARS, "tasso": {}, "denunce": {}}
for k, c in KEYS:
    serie["tasso"][k] = [r1(rate(c, y)) for y in YEARS]
    serie["denunce"][k] = [cnt(c, y) for y in YEARS]
dump("serie_totale.json", serie)

# --- 2. denunce assolute nel comune di Milano, 2004-2024
ds = {}
for r in rd(f"{PUL}/milano_comune_ds564.csv"):
    if r["tipo_codice"] == "TOT":
        ds[int(r["anno"])] = {"n": int(r["denunce_comune"]), "res": int(r["residenti_comune_31dic"]) if r["residenti_comune_31dic"] else None, "fonte": "Comune di Milano ds564"}
ds[2024] = {"n": cnt("015146", 2024), "res": None, "fonte": "ISTAT"}
check("ds564 2004", ds[2004]["n"], 141636)
check("ds564 2007 (picco)", ds[2007]["n"], 174040)
anni_c = sorted(ds)
picco = max(anni_c, key=lambda y: ds[y]["n"]); minimo = min(anni_c, key=lambda y: ds[y]["n"])
den = {"anni": anni_c, "denunce": [ds[y]["n"] for y in anni_c], "residenti_anagrafe": [ds[y]["res"] for y in anni_c],
       "picco": {"anno": picco, "n": ds[picco]["n"]}, "minimo": {"anno": minimo, "n": ds[minimo]["n"]},
       "var_2024_su_2004_pc": round((ds[2024]["n"] / ds[2004]["n"] - 1) * 100, 1), "var_2024_su_picco_pc": round((ds[2024]["n"] / ds[picco]["n"] - 1) * 100, 1)}
dump("denunce_comune.json", den)
check("var 2024 su picco", den["var_2024_su_picco_pc"], -19.0, 0.05)

# --- 3. rango delle province
pt = rd(f"{PUL}/province_totale_anno.csv")
byy = collections.defaultdict(list)
for r in pt:
    byy[int(r["anno"])].append((float(r["per_100mila"]), r["provincia"], int(r["rango"])))
rk = {r["anno"]: r for r in rd(f"{PUL}/riepilogo_rango_milano.csv")}
top5 = {y: [n for _, n, k in sorted(byy[y], reverse=True)[:5]] for y in YEARS}
ever = []
for y in YEARS:
    for n in top5[y]:
        if n not in ever:
            ever.append(n)
bump = []
for n in ever:
    bump.append({"nome": n, "rango": {y: next(k for _, p, k in byy[y] if p == n) for y in YEARS}, "tasso": {y: round(next(v for v, p, k in byy[y] if p == n), 0) for y in YEARS}})
dump("rango_province.json", {"anni": YEARS, "n_province": {y: len(byy[y]) for y in YEARS}, "serie": bump, "top5": top5,
                             "milano_con_monza": {y: int(rk[str(y)]["rango_milano_con_monza"]) for y in YEARS if rk[str(y)]["rango_milano_con_monza"]}})
check("rango Milano 2006", next(k for _, p, k in byy[2006] if p == "Milano"), 4)
check("rango Milano 2010", next(k for _, p, k in byy[2010] if p == "Milano"), 1)
check("rango Milano 2024", next(k for _, p, k in byy[2024] if p == "Milano"), 1)

# --- 4. grandi comuni
gc = rd(f"{PUL}/riepilogo_rango_grandi_comuni.csv")
AREAN = json.load(open(f"{R}/raw/probe/codelists.json", encoding="utf8"))["CL_ITTER107"]
big = collections.defaultdict(dict)
for r in rd(f"{R}/raw/istat/df8_grandi_comuni_CRIMET.csv"):
    if r["TYPE_CRIME"] == "TOT" and r["OBS_VALUE"]:
        big[int(r["TIME_PERIOD"])][AREAN[r["REF_AREA"]]] = round(float(r["OBS_VALUE"]), 1)
gcj = {}
for y in YEARS:
    s = sorted(big[y].items(), key=lambda kv: -kv[1])
    gcj[y] = [{"nome": n, "tasso": v, "rango": i + 1} for i, (n, v) in enumerate(s)]
dump("grandi_comuni.json", {"anni": YEARS, "per_anno": gcj, "rango_milano": {y: next(x["rango"] for x in gcj[y] if x["nome"] == "Milano") for y in YEARS}})
check("grandi comuni: Milano 2024 rango", next(x["rango"] for x in gcj[2024] if x["nome"] == "Milano"), 2)
check("grandi comuni: anni con Milano primo", sum(1 for y in YEARS if gcj[y][0]["nome"] == "Milano"), 13)

# --- 5. tipi per il comune di Milano
KEYT = ["THEFT", "PICKTHEF", "BAGTHEF", "BURGTHEF", "VEHITHEF", "SHOPTHEF", "CARTHEF", "MOTORTHEF", "MOPETHEF", "ROBBER", "STREETROB",
        "INTENHOM", "ATTEMPHOM", "CULPINJU", "BLOWS", "MENACE", "RAPE", "RAPEUN18", "SWINCYB", "CYBERCRIM", "DRUG", "DAMAGE", "EXTORT", "ARSON",
        "COUNTER", "RECEIV", "MONEYLAU", "OTHCRIM"]
def pc(a, b):
    return None if (a is None or b is None or a == 0) else round((b / a - 1) * 100, 1)
tipi = []
for t in KEYT:
    row = {"codice": t, "nome": D[("015146", 2024, t)]["nome"] if ("015146", 2024, t) in D else D[("015146", 2019, t)]["nome"],
           "gruppo": D[("015146", 2024, t)]["gruppo"] if ("015146", 2024, t) in D else ""}
    for y in (2006, 2019, 2020, 2024):
        row[f"den_{y}"] = cnt("015146", y, t); row[f"tasso_{y}"] = r1(rate("015146", y, t))
        row[f"it_tasso_{y}"] = r1(rate("IT", y, t)); row[f"prov_tasso_{y}"] = r1(rate("ITC45", y, t))
    for a, b in [(2006, 2024), (2019, 2024), (2019, 2020)]:
        row[f"var_{a}_{b}"] = pc(rate("015146", a, t), rate("015146", b, t))
        row[f"it_var_{a}_{b}"] = pc(rate("IT", a, t), rate("IT", b, t))
    row["quota_2024"] = round(cnt("015146", 2024, t) / cnt("015146", 2024) * 100, 1) if cnt("015146", 2024, t) else None
    tipi.append(row)
dump("tipi_comune.json", tipi)
def tp(c):
    return next(r for r in tipi if r["codice"] == c)
check("violenze sessuali var 19-24", tp("RAPE")["var_2019_2024"], 70.1, 0.05)
check("frodi var 06-24", tp("SWINCYB")["var_2006_2024"], 145.7, 0.05)
check("borseggi covid", tp("PICKTHEF")["var_2019_2020"], -49.2, 0.05)

# --- 6. covid per territorio
cov = rd(f"{PUL}/riepilogo_covid.csv")
dump("covid.json", [{"territorio": r["territorio"], "t2019": float(r["per100k_2019"]), "t2020": float(r["per100k_2020"]), "t2021": float(r["per100k_2021"]),
                     "t2022": float(r["per100k_2022"]), "t2024": float(r["per100k_2024"]), "v20": float(r["var_2020_su_2019_%"]), "v21": float(r["var_2021_su_2019_%"]),
                     "v24": float(r["var_2024_su_2019_%"])} for r in cov])

# --- 7. divario con l'Italia
dec = rd(f"{PUL}/riepilogo_scomposizione_divario.csv")
div = {}
for r in dec:
    d = div.setdefault(r["anno"], {}).setdefault(r["territorio"], {"divario": float(r["divario_totale"]), "gruppi": []})
    d["gruppi"].append({"nome": r["tipo_delitto"], "diff": float(r["diff_per100k_vs_italia"]), "quota": float(r["quota_del_divario_%"])})
for a in div.values():
    for t in a.values():
        t["gruppi"].sort(key=lambda g: -g["diff"])
dump("divario.json", div)
check("divario comune 2024", div["2024"]["Milano comune"]["divario"], 6273.1, 0.05)

# --- 8. presenti (solo Milano)
pr = rd(f"{PUL}/riepilogo_presenti_milano.csv")
tur = rd(f"{PUL}/riepilogo_turisti_per_residente.csv")
pend = {"entrata": 474680, "uscita": 90063, "saldo": 384617, "anno": 2011}
rows = [{"anno": int(r["anno"]), "denunce": int(r["denunce_comune"]), "residenti": int(r["residenti_istat_implicito"]), "turisti_giorno": int(r["turisti_medi_al_giorno"]) if r["turisti_medi_al_giorno"] else None,
         "solo_residenti": float(r["per100k_residenti"]), "con_turisti": float(r["per100k_residenti_piu_turisti"]) if r["per100k_residenti_piu_turisti"] else None,
         "con_turisti_e_saldo": float(r["per100k_residenti_turisti_e_saldo_pendolari2011"]) if r["per100k_residenti_turisti_e_saldo_pendolari2011"] else None,
         "con_turisti_e_entrata": float(r["per100k_residenti_turisti_e_pendolari_in_entrata2011"]) if r["per100k_residenti_turisti_e_pendolari_in_entrata2011"] else None} for r in pr]
tur_n = {int(r["anno"]): {k: v for k, v in r.items() if k != "anno" and v != ""} for r in tur}
dump("presenti_milano.json", {"pendolari_2011": pend, "righe": rows, "turisti_per_100_residenti": tur_n})
check("presenti 2024 con saldo", next(r["con_turisti_e_saldo"] for r in rows if r["anno"] == 2024), 7863.2, 0.05)
check("pendolari: saldo", pend["entrata"] - pend["uscita"], pend["saldo"])

# --- 9. omicidi
hom = {"anni": list(range(2004, 2025)), "comune": {}, "italia": {}}
for r in rd(f"{PUL}/milano_comune_ds564.csv"):
    if r["tipo_codice"] == "INTENHOM":
        hom["comune"][int(r["anno"])] = int(r["denunce_comune"])
hom["comune"][2024] = cnt("015146", 2024, "INTENHOM")
for y in YEARS:
    hom["italia"][y] = cnt("IT", y, "INTENHOM")
hom["tasso_comune_2024"] = r1(rate("015146", 2024, "INTENHOM")); hom["tasso_italia_2024"] = r1(rate("IT", 2024, "INTENHOM"))
hom["tasso_prov_2024"] = r1(rate("ITC45", 2024, "INTENHOM"))
hom["rapporto_comune_italia_2024"] = round(rate("015146", 2024, "INTENHOM") / rate("IT", 2024, "INTENHOM"), 2)
dump("omicidi.json", hom)
check("omicidi 2024 comune", hom["comune"][2024], 6)
check("omicidi 2019 comune (riattribuita)", hom["comune"][2019], 8)

# --- 10. numeri della scheda
dump("riepilogo.json", {
    "scaricato": "2026-11-01", "ultimo_anno": 2024,
    "popolazione_comune_su_provincia_2024": round(D[("015146", 2024, "TOT")]["p"] / D[("ITC45", 2024, "TOT")]["p"] * 100, 1),
    "denunce_comune_su_provincia_2024": round(cnt("015146", 2024) / cnt("ITC45", 2024) * 100, 1),
    "monza_salto": {"pop_2010": D[("ITC45", 2010, "TOT")]["p"], "pop_2011": D[("ITC45", 2011, "TOT")]["p"], "monza_pop_2011": D[("IT108", 2011, "TOT")]["p"],
                    "tasso_2010": r1(rate("ITC45", 2010)), "tasso_2011": r1(rate("ITC45", 2011)), "monza_2011": r1(rate("ITC45+IT108", 2011)), "monza_2024": r1(rate("ITC45+IT108", 2024))},
    "borseggi_comune_2024": cnt("015146", 2024, "PICKTHEF"), "borseggi_al_giorno_2024": round(cnt("015146", 2024, "PICKTHEF") / 366, 0),
    "quota_frodi_2006": round(cnt("015146", 2006, "SWINCYB") / cnt("015146", 2006) * 100, 1), "quota_frodi_2024": round(cnt("015146", 2024, "SWINCYB") / cnt("015146", 2024) * 100, 1),
    "quota_furti_2024": round(cnt("015146", 2024, "THEFT") / cnt("015146", 2024) * 100, 1),
    "sole24ore_2025": {"milano_oltre": 7000, "var_pc": 0.6, "fonte": "LaPresse 12/10/2026, dati Dipartimento Pubblica sicurezza forniti in esclusiva al Sole 24 Ore", "coerenza": round(rate("ITC45", 2024) * 1.006)},
})

# --- 11. file scaricabili
with open(f"{OUT}/delitti_tipo_territorio_anno.csv", "w", encoding="utf-8", newline="") as f:
    cols = ["anno", "codice_istat", "territorio", "livello", "tipo_codice", "tipo_delitto", "gruppo", "denunce", "per_100mila", "per_100mila_pubblicato_istat", "popolazione_istat_implicita"]
    w = csv.DictWriter(f, cols); w.writeheader()
    for r in long_:
        w.writerow({k: r[k] for k in cols})
for fn in ["province_totale_anno.csv", "milano_comune_ds564.csv", "riepilogo_variazioni.csv", "riepilogo_scomposizione_divario.csv", "riepilogo_presenti_milano.csv"]:
    shutil.copyfile(f"{PUL}/{fn}", f"{OUT}/{fn}")
print("scritti:", sorted(os.listdir(OUT)))
for fn in sorted(os.listdir(OUT)):
    print(f"  {fn}: {os.path.getsize(os.path.join(OUT, fn)) // 1024} KB")
