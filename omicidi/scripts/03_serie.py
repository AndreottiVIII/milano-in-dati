"""Costruisce le serie pulite sugli omicidi. Nessun nome, nessun caso singolo: solo conteggi annuali.
Uso: python -I -X utf8 03_serie.py <cartella omicidi> <cartella milano-in-dati>
Scrive in pulito/ e stampa i controlli in out/controlli.txt
"""
import sys, os, csv, json, statistics as st, collections
import openpyxl, warnings
warnings.filterwarnings("ignore")
B, ROOT = sys.argv[1], sys.argv[2]
P = lambda *a: os.path.join(B, *a)
log = []
def say(*a):
    s = " ".join(str(x) for x in a); log.append(s); print(s)
def rcsv(path, **k):
    return list(csv.DictReader(open(path, encoding="utf-8"), **k))
def wcsv(name, rows, cols=None):
    cols = cols or list(rows[0].keys())
    with open(P("pulito", name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    say("scritto", name, len(rows), "righe")

# ---------- popolazione residente al 1 gennaio (ISTAT, ricostruzioni e POPRES)
pop = collections.defaultdict(dict)
for fn in ("pop_1982_1991.csv", "pop_1992_2001.csv", "pop_2002_2019.csv", "pop_2019_ult.csv"):
    for r in rcsv(P("raw/istat_popolazione", fn)):
        if r["DATA_TYPE"] == "JAN" and r["OBS_VALUE"]:
            pop[r["REF_AREA"]][int(r["TIME_PERIOD"])] = int(float(r["OBS_VALUE"]))  # i file successivi prevalgono sugli anni comuni
def popmedia(area, y):
    a, b = pop[area].get(y), pop[area].get(y + 1)
    if a and b: return (a + b) / 2
    return a or b
def somma_pop(aree, y):
    """Somma le aree al 1 gennaio e poi fa la media tra due gennaio: cosi' lo stacco di Monza (dal 2001 voce a parte) non crea salti."""
    jan = lambda k: sum(pop[a].get(k, 0) for a in aree) or None
    a, b = jan(y), jan(y + 1)
    if a and b: return (a + b) / 2
    return a or b

# ---------- conteggi di polizia
t83 = [r for r in rcsv(P("pulito/istat_1983_2003_omicidi_territori.csv")) if r["tavola"] == "totale"]
t00 = rcsv(P("pulito/istat_2000_2008_omicidi_territori.csv"))
sd = rcsv(P("raw/istat_delitti_province_ids/df1_CRIMEN_HOM_tutte_aree.csv"))
sdv = {(r["REF_AREA"], r["TYPE_CRIME"], int(r["TIME_PERIOD"])): int(float(r["OBS_VALUE"])) for r in sd if r["OBS_VALUE"]}
def get83(nome, y, campo="om_consumati"):
    for r in t83:
        if r["territorio"] == nome and int(r["anno"]) == y:
            return int(r[campo]) if r[campo] != "" else None
    return None
def get00(nome, y, campo="om_consumati"):
    for r in t00:
        if r["territorio"].strip() == nome and int(r["anno"]) == y:
            return int(r[campo]) if r[campo] != "" else None
    return None

TERR = {  # nome: (nome nei file 1983-2008, codici SDMX, codici popolazione per il tasso)
    "Italia": (["ITALIA"], ["IT"], ["IT"]),
    "Lombardia": (["LOMBARDIA"], ["ITC4"], ["ITC4"]),
    "Roma": (["Roma"], ["ITE43"], ["ITE43"]),
    "Torino": (["Torino"], ["ITC11"], ["ITC11"]),
    "Napoli": (["Napoli"], ["ITF33"], ["ITF33"]),
    "Genova": (["Genova"], ["ITC33"], ["ITC33"]),
    "Bologna": (["Bologna"], ["ITD55"], ["ITD55"]),
    "Firenze+Prato": (["Firenze", "Prato"], ["ITE14", "ITE15"], ["ITE14", "ITE15"]),
    "Palermo": (["Palermo"], ["ITG12"], ["ITG12"]),
    "Catania": (["Catania"], ["ITG17"], ["ITG17"]),
    "Venezia": (["Venezia"], ["ITD35"], ["ITD35"]),
    "Verona": (["Verona"], ["ITD31"], ["ITD31"]),
    "Area milanese (Milano+Monza+Lodi)": (["Milano", "Lodi"], ["ITC45", "IT108", "ITC49"], ["ITC45", "IT108", "ITC49"]),
}
def conta(nomi, codici, y, campo83, tipo):
    """2004-2005 solo dalla tavola 2000-2008; 1983-2003 dal file storico; dal 2006 SDMX."""
    if y <= 2003:
        vals = [get83(n if n != "ITALIA" else "ITALIA", y, campo83) for n in nomi]
    elif y <= 2005:
        vals = [get00({"ITALIA": "Italia", "LOMBARDIA": "Lombardia"}.get(n, n), y, "om_consumati" if tipo == "INTENHOM" else "tentati") for n in nomi]
    else:
        vals = [sdv.get((c, tipo, y)) for c in codici]
    vals = [v for v in vals if v is not None]
    return sum(vals) if vals else None

rows = []
for nome, (nomi, cod, cp) in TERR.items():
    for y in range(1983, 2025):
        c = conta(nomi, cod, y, "om_consumati", "INTENHOM")
        t = conta(nomi, cod, y, "tentati", "ATTEMPHOM")
        p = somma_pop(cp, y)
        # 1982-2001 la ricostruzione ITC45 comprende gia' Monza: IT108 non esiste, la somma resta corretta
        fonte = "ISTAT DELITTI_DENUNCIATI_1983_2003 (mod. 165)" if y <= 2003 else "ISTAT DELITTI_PERS_CONDAN_1985_2008 (SDI)" if y <= 2005 else "ISTAT DCCV_DELITTIPS_1 (SDI)"
        rows.append({"anno": y, "territorio": nome, "omicidi_consumati": c, "tentati_omicidi": t, "popolazione_media": round(p) if p else "",
                     "omicidi_per_100mila": round(c / p * 1e5, 3) if c is not None and p else "", "fonte_conteggi": fonte})
by = collections.defaultdict(dict)
for r in rows: by[r["territorio"]][r["anno"]] = r
for nome, d in by.items():
    for y, r in d.items():
        w = [d[k]["omicidi_consumati"] for k in range(y - 2, y + 3) if k in d and d[k]["omicidi_consumati"] is not None]
        wp = [d[k]["popolazione_media"] for k in range(y - 2, y + 3) if k in d and d[k]["popolazione_media"] != ""]
        r["tasso_media_5anni_centrata"] = round(sum(w) / sum(wp) * 1e5, 3) if len(w) == 5 and len(wp) == 5 else ""
wcsv("serie_lunga_polizia_1983_2024.csv", rows)

# ---------- Milano come pubblicata (confini che cambiano) e moventi 1983-2003
mil = []
for y in range(1983, 2004):
    r = {k: get83("Milano", y, k) for k in ("om_consumati", "om_mafia", "om_onore_passionali", "om_furto_rapina", "om_terrorismo", "om_altri_motivi", "tentati", "infanticidi", "preterintenzionali", "strage")}
    r["anno"] = y; r["lodi_consumati"] = get83("Lodi", y) if y >= 1996 else ""
    r["confini"] = "Milano+Monza+Lodi" if y <= 1995 else "Milano+Monza (Lodi a parte)"
    mil.append(r)
wcsv("milano_moventi_1983_2003.csv", mil, ["anno", "confini", "om_consumati", "om_mafia", "om_onore_passionali", "om_furto_rapina", "om_terrorismo", "om_altri_motivi", "tentati", "infanticidi", "preterintenzionali", "strage", "lodi_consumati"])

# ---------- comune di Milano (polizia) e confronto capoluoghi
com = rcsv(os.path.join(ROOT, "reati/pulito/milano_comune_ds564.csv"))
cc = {}
for r in com:
    if r["tipo_codice"] in ("INTENHOM", "ATTEMPHOM"):
        cc[(int(r["anno"]), r["tipo_codice"])] = (int(r["denunce_comune"]), int(r["residenti_comune_31dic"]))
rc = []
d337 = {}
import pandas as pd
x = pd.read_csv(P("raw/comune_ds337/ds337_decessi_causa_morte_2003-2011.csv"), sep=";", encoding="cp1252")
x = x[x["Tipologia morte violenta"] == "Omicidio"]
g = x.groupby(["Anno evento", "Genere"])["Numerosità"].sum().unstack(fill_value=0)
for y, row in g.iterrows(): d337[int(y)] = (int(row["Maschi"]), int(row["Femmine"]))
x = pd.read_csv(P("raw/comune_ds338/ds338_residenti_causa_morte_2012-2013.csv"), sep=";", encoding="cp1252")
x = x[x["tipo_morte_violenta"] == "Omicidio"]
g = x.groupby(["Anno_evento", "Genere"])["Numerosità"].sum().unstack(fill_value=0)
d338 = {int(y): (int(row["Maschi"]), int(row["Femmine"])) for y, row in g.iterrows()}
res = {y: v[1] for (y, t), v in cc.items() if t == "INTENHOM"}
for y in range(2003, 2025):
    c = cc.get((y, "INTENHOM"), (None,))[0]
    if c is None: c = sdv.get(("015146", "INTENHOM", y))
    t = cc.get((y, "ATTEMPHOM"), (None,))[0]
    if t is None: t = sdv.get(("015146", "ATTEMPHOM", y))
    p = res.get(y)
    if y == 2024: p = round(1 / (float(next(r["OBS_VALUE"] for r in rcsv(os.path.join(ROOT, "reati/raw/istat/df8_grandi_comuni_CRIMET.csv")) if r["REF_AREA"] == "015146" and r["TYPE_CRIME"] == "TOT" and r["TIME_PERIOD"] == "2024")) / float(next(r["OBS_VALUE"] for r in rcsv(os.path.join(ROOT, "reati/raw/istat/df1_CRIMEN_tutte_aree_TOT.csv")) if r["REF_AREA"] == "015146" and r["TIME_PERIOD"] == "2024")) / 1e5))  # implicita ISTAT, diversa da ds27
    m = d337.get(y); m2 = d338.get(y)
    rc.append({"anno": y, "omicidi_consumati_comune": c if c is not None else "", "tentati_comune": t if t is not None else "", "residenti_31dic_ds27": p or "",
               "per_100mila": round(c / p * 1e5, 2) if c is not None and p else "",
               "morti_omicidio_avvenuti_a_milano_M_ds337": m[0] if m else "", "morti_omicidio_avvenuti_a_milano_F_ds337": m[1] if m else "",
               "morti_omicidio_residenti_M_ds338": m2[0] if m2 else "", "morti_omicidio_residenti_F_ds338": m2[1] if m2 else ""})
wcsv("comune_milano_2003_2024.csv", rc)

# capoluoghi: popolazione implicita da totale delitti / tasso (come in reati/)
tot = rcsv(os.path.join(ROOT, "reati/raw/istat/df1_CRIMEN_tutte_aree_TOT.csv"))
totv = {(r["REF_AREA"], int(r["TIME_PERIOD"])): float(r["OBS_VALUE"]) for r in tot if r["OBS_VALUE"]}
tas = rcsv(os.path.join(ROOT, "reati/raw/istat/df8_grandi_comuni_CRIMET.csv"))
tasv = {(r["REF_AREA"], int(r["TIME_PERIOD"])): float(r["OBS_VALUE"]) for r in tas if r["TYPE_CRIME"] == "TOT" and r["OBS_VALUE"]}
CAP = {"015146": "Milano", "058091": "Roma", "001272": "Torino", "063049": "Napoli", "010025": "Genova", "037006": "Bologna", "048017": "Firenze", "082053": "Palermo", "087015": "Catania", "072006": "Bari", "027042": "Venezia", "023091": "Verona"}
rg = []
for code, nome in CAP.items():
    for y in range(2006, 2025):
        c = sdv.get((code, "INTENHOM", y)); t = sdv.get((code, "ATTEMPHOM", y))
        p = totv.get((code, y), 0) / tasv[(code, y)] * 1e5 if (code, y) in tasv and tasv[(code, y)] else None
        rg.append({"anno": y, "comune": nome, "omicidi_consumati": c, "tentati_omicidi": t, "popolazione_implicita": round(p) if p else "", "per_100mila": round(c / p * 1e5, 2) if c is not None and p else ""})
wcsv("grandi_comuni_2006_2024.csv", rg)
per = []
for nome in CAP.values():
    for a, b in ((2006, 2010), (2011, 2015), (2016, 2020), (2021, 2024)):
        s = [r for r in rg if r["comune"] == nome and a <= r["anno"] <= b]
        n = sum(r["omicidi_consumati"] or 0 for r in s); q = sum(r["popolazione_implicita"] or 0 for r in s)
        per.append({"comune": nome, "periodo": f"{a}-{b}", "omicidi": n, "media_annua": round(n / (b - a + 1), 1), "per_100mila": round(n / q * 1e5, 2) if q else ""})
wcsv("grandi_comuni_periodi.csv", per)

# ---------- decessi per causa (omicidio, aggressione), per sesso, provincia
cm = []
for f, tipo in (("cmorte_evento_omicidio_prov.csv", "luogo_evento"), ("cmorte_residenza_omicidio_prov.csv", "residenza")):
    for r in rcsv(P("raw/istat_cause_morte", f)):
        if r["OBS_VALUE"]:
            cm.append({"anno": int(r["TIME_PERIOD"]), "area": r["REF_AREA"], "base": tipo, "sesso": {"1": "M", "2": "F", "9": "T"}[r["SEX"]], "morti": int(float(r["OBS_VALUE"]))})
wcsv("decessi_causa_omicidio_province_2003_2023.csv", cm)
cmv = {(r["anno"], r["area"], r["base"], r["sesso"]): r["morti"] for r in cm}

# ---------- vittime per sesso (statistiche di polizia)
vit = []
for fn in ("vittime_omicidio_prov_2007_ult.csv", "vittime_tutte_aree.csv"):
    fp = P("raw/istat_vittime_prov", fn)
    if not os.path.exists(fp): continue
    for r in rcsv(fp):
        if r["OBS_VALUE"] and r["TYPE_CRIME"] == "INTENHOM":
            vit.append({"anno": int(r["TIME_PERIOD"]), "area": r["REF_AREA"], "sesso": {"1": "M", "2": "F", "9": "T"}[r["SEX"]], "vittime": int(float(r["OBS_VALUE"]))})
vit = list({(v["anno"], v["area"], v["sesso"]): v for v in vit}.values())
wcsv("vittime_polizia_sesso_aree.csv", sorted(vit, key=lambda v: (v["area"], v["anno"], v["sesso"])))

# ---------- Italia: relazione vittima-autore 2002-2024 (DCPC-ISTAT)
wb = openpyxl.load_workbook(P("raw/istat_relazione_autore/omicidi-relazione-autore-DCPC-anni-2002-2024.xlsx"), data_only=True)
rel = []
for sh, sesso in (("Vittime di omicidio - Totale", "T"), ("Vittime di omicidio - Maschi", "M"), ("Vittime di omicidio - Femmine", "F")):
    R = list(wb[sh].iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(R) if r[0] and "RELAZIONE" in str(r[0]))
    anni = [(j, int(str(c)[:4])) for j, c in enumerate(R[hi]) if c is not None and str(c)[:2] == "20"]
    visti = set()
    for r in R[hi + 1:]:
        lab = str(r[0] or "")
        voce = "partner" if lab.startswith("Partner") else "ex_partner" if lab.startswith("Ex") else "altro_parente" if lab.startswith("Altro parente") else "altro_conoscente" if lab.startswith("Altro con") else "sconosciuto" if lab.startswith("Autore scon") else "non_identificato" if lab.startswith("Autore non") else "totale" if lab.startswith("Totale") else None
        if voce is None or voce in visti: continue
        visti.add(voce)
        for j, y in anni:
            v = r[j]
            rel.append({"anno": y, "sesso": sesso, "relazione": voce, "vittime": int(round(v)) if isinstance(v, (int, float)) else ""})
wcsv("italia_relazione_2002_2024.csv", rel)

# ---------- Lombardia: relazione, tavole regionali ISTAT
lom = []
VOCI = ["partner_ex", "altro_parente", "altro_conoscente", "sconosciuto", "non_identificato", "totale"]
for path, sheet, anno in ((P("raw/istat_relazione_autore/omicidi-relazione-autore-DCPC-anni-2002-2024.xlsx"), "Vittime di omicidio-Regioni", 2024),
                          (P("raw/istat_tavole_2023/estratto/Apendice-statistica_regione.xlsx"), "A1", 2023),
                          (P("raw/istat_tavole_2019/Tavole-Fuori-testo-Omicidi.xlsx"), "TAV.A6-om.relaz-regioni (v.a.)", 2019)):
    R = list(openpyxl.load_workbook(path, data_only=True)[sheet].iter_rows(values_only=True))
    h = next(r for r in R if sum(1 for c in r if c and str(c).startswith("Partner")) == 3)
    cols = [j for j, c in enumerate(h) if c is not None and j > 0][:18]
    seen = set()
    for r in R:
        nm = str(r[0]).strip() if r[0] else ""
        nm2 = "Italia" if nm.upper() == "ITALIA" else nm
        if nm2 not in ("Lombardia", "Italia") or nm2 in seen: continue
        seen.add(nm2)  # la prima riga e' in valori assoluti, la seconda in quozienti
        v = [r[j] if isinstance(r[j], (int, float)) else 0 for j in cols]
        for k, sesso in enumerate("MFT"):
            parti = v[k * 6:k * 6 + 5]; tot = v[k * 6 + 5]
            if sum(parti) != tot: say("  ATTENZIONE somma relazione", anno, nm2, sesso, parti, tot)
            for i, voce in enumerate(VOCI):
                lom.append({"anno": anno, "area": nm2, "sesso": sesso, "relazione": voce, "vittime": int(round(v[k * 6 + i]))})
wcsv("lombardia_relazione_anni.csv", lom)

# ---------- Italia, serie lunghissima (tassi) dalla storia dati ISTAT
wb = openpyxl.load_workbook(P("raw/istat_storia_dati/storia-dati-criminalita-giustizia.xlsx"), data_only=True)
R = list(wb["1"].iter_rows(values_only=True))
ita = []
for r in R:
    if isinstance(r[0], int) and 1800 < r[0] < 2100:
        ita.append({"anno": r[0], "omicidi_volontari_azione_penale_per100mila": r[1] if r[1] is not None else "", "omicidi_volontari_polizia_per100mila": r[2] if r[2] is not None else "",
                    "consumati_tentati_infanticidi_azione_penale_per100mila": r[3] if r[3] is not None else "", "consumati_tentati_polizia_per100mila": r[4] if r[4] is not None else ""})
wcsv("italia_tassi_1880_2024.csv", ita)

# ========== CONTROLLI
say("\n=== CONTROLLI ===")
# A. file 1983-2003 contro tavole 2000-2008 sugli anni comuni, tutte le province
n = dif = 0
for y in range(2000, 2004):
    for r in t83:
        if int(r["anno"]) == y and r["livello"] == "provincia":
            v = get00(r["territorio"], y)
            if v is None: continue
            n += 1
            if v != int(r["om_consumati"]):
                dif += 1; say("  A diff", y, r["territorio"], r["om_consumati"], v)
say(f"A. 1983-2003 vs tavole 2000-2008, 2000-2003, province: {n} confronti, {dif} differenze")
# B. tavole 2000-2008 contro SDMX, 2006-2008
NAMES = {}
codes = {"Milano": "ITC45", "Lodi": "ITC49", "Roma": "ITE43", "Torino": "ITC11", "Napoli": "ITF33", "Genova": "ITC33", "Bologna": "ITD55", "Firenze": "ITE14", "Prato": "ITE15", "Palermo": "ITG12", "Catania": "ITG17", "Venezia": "ITD35", "Verona": "ITD31", "Italia": "IT", "Lombardia": "ITC4"}
n = dif = 0
for y in (2006, 2007, 2008):
    for nm, c in codes.items():
        a, b = get00(nm, y), sdv.get((c, "INTENHOM", y))
        if a is None or b is None: continue
        n += 1
        if a != b: dif += 1; say("  B diff", y, nm, a, b)
say(f"B. tavole 2000-2008 vs ISTAT DELITTIPS, 2006-2008, 15 aree: {n} confronti, {dif} differenze")
# C. comune ds564 vs ISTAT
n = dif = 0
for y in range(2006, 2024):
    a, b = cc[(y, "INTENHOM")][0], sdv.get(("015146", "INTENHOM", y))
    n += 1
    if a != b: dif += 1; say("  C diff", y, a, b)
say(f"C. comune ds564 vs ISTAT 015146, 2006-2023 (2019 gia' corretto in reati/): {n} confronti, {dif} differenze")
# D. polizia contro decessi per causa, provincia di Milano ai confini del tempo, 2006-2023
pl, dc = [], []
for y in range(2003, 2024):
    c = sdv.get(("ITC45", "INTENHOM", y)) or get83("Milano", y) or get00("Milano", y)
    d = cmv.get((y, "ITC45", "luogo_evento", "T"))
    pl.append(c); dc.append(d)
    say(f"  D {y}: polizia {c}, decessi per causa (luogo evento) {d}, decessi (residenza) {cmv.get((y,'ITC45','residenza','T'))}")
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** .5
say("D. correlazione polizia-decessi Milano 2003-2023:", round(corr(pl, dc), 3), "somma polizia", sum(pl), "somma decessi", sum(dc), "rapporto decessi/polizia", round(sum(dc) / sum(pl), 3))
pi = [sdv.get(("IT", "INTENHOM", y)) or get83("ITALIA", y) or get00("Italia", y) for y in range(2003, 2024)]
di = [cmv.get((y, "IT", "luogo_evento", "T")) for y in range(2003, 2024)]
say("D. Italia: correlazione", round(corr(pi, di), 3), "rapporto decessi/polizia", round(sum(di) / sum(pi), 3))
# E. comune polizia contro ds337 (morti avvenute a Milano)
a, b = [], []
for y in range(2004, 2012):
    a.append(cc[(y, "INTENHOM")][0]); b.append(sum(d337[y]))
    say(f"  E {y}: polizia comune {a[-1]}, ds337 morti per omicidio avvenute a Milano {b[-1]}")
say("E. correlazione", round(corr(a, b), 3), "somme", sum(a), sum(b))
# G. omicidi di mafia in Lombardia: somma province vs ISTAT Tavola 3 (quinquenni)
per = {"1983-1987": (1983, 1987, 10), "1988-1992": (1988, 1992, 61), "1993-1997": (1993, 1997, 10), "1998-2002": (1998, 2002, 4)}
for k, (a, b, atteso) in per.items():
    s = sum(get83("LOMBARDIA", y, "om_mafia") for y in range(a, b + 1)); m = sum(get83("Milano", y, "om_mafia") for y in range(a, b + 1))
    say(f"G. mafia Lombardia {k}: file {s}, tavola ISTAT {atteso}; di cui Milano {m}")
# H. popolazione
for y in (1983, 1991, 2001, 2002, 2011, 2019, 2024):
    say("H. popolazione area milanese", y, somma_pop(["ITC45", "IT108", "ITC49"], y), "Italia", popmedia("IT", y))
# riepilogo
say("\n=== RIEPILOGO AREA MILANESE ===")
am = by["Area milanese (Milano+Monza+Lodi)"]; it = by["Italia"]
for y in sorted(am):
    r = am[y]; say(y, r["omicidi_consumati"], r["tentati_omicidi"], r["popolazione_media"], r["omicidi_per_100mila"], r["tasso_media_5anni_centrata"], "| Italia", it[y]["omicidi_consumati"], it[y]["omicidi_per_100mila"])
def pooled(nome, a, b):
    d = by[nome]; c = sum(d[y]["omicidi_consumati"] or 0 for y in range(a, b + 1)); p = sum(d[y]["popolazione_media"] or 0 for y in range(a, b + 1))
    return c, round(c / (b - a + 1), 1), round(c / p * 1e5, 2)
periodi = [(1983, 1987), (1988, 1992), (1993, 1997), (1998, 2002), (2003, 2007), (2008, 2012), (2013, 2017), (2018, 2024)]
conf = []
for nome in TERR:
    for a, b in periodi:
        c, m, t = pooled(nome, a, b)
        conf.append({"territorio": nome, "periodo": f"{a}-{b}", "omicidi": c, "media_annua": m, "per_100mila": t})
wcsv("confronto_periodi_1983_2024.csv", conf)
say("\n=== TASSI PER PERIODO ===")
for nome in TERR:
    say(nome, [(f"{a}-{b}"[2:], pooled(nome, a, b)[2]) for a, b in periodi])
os.makedirs(P("out"), exist_ok=True)
open(P("out/controlli.txt"), "w", encoding="utf-8").write("\n".join(log))
