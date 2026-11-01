"""Costruisce le tabelle pulite (tidy) dei delitti denunciati.
Uso: python -I -X utf8 build.py <reati> <milano-in-dati>
Entrate (tutte in raw/): istat/df1_*, istat/df9_*, comune_ds564/*.csv ; da probe/codelists.json i nomi.
Uscite in pulito/: delitti_tipo_territorio_anno.csv, province_totale_anno.csv, milano_comune_ds564.csv, controlli_build.txt
"""
import sys, csv, json, collections, os
R, M = sys.argv[1], sys.argv[2]
RAW, OUT = f"{R}/raw", f"{R}/pulito"
os.makedirs(OUT, exist_ok=True)
log = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); log.append(s)

cl = json.load(open(f"{RAW}/probe/codelists.json", encoding="utf8"))
AREA = cl["CL_ITTER107"]
TIPO = cl["CL_REATI_PS"]

# gruppi per la lettura (miei, dichiarati nel NOTE)
GRUPPO = {
 "TOT": "totale",
 "THEFT": "furti", "PICKTHEF": "furti", "BAGTHEF": "furti", "BURGTHEF": "furti", "SHOPTHEF": "furti", "VEHITHEF": "furti",
 "CARTHEF": "furti", "MOPETHEF": "furti", "MOTORTHEF": "furti", "TRUCKTHEF": "furti", "ARTTHEF": "furti",
 "ROBBER": "rapine", "HOUSEROB": "rapine", "BANKROB": "rapine", "POSTROB": "rapine", "SHOPROB": "rapine", "STREETROB": "rapine",
 "INTENHOM": "contro la persona", "ATTEMPHOM": "contro la persona", "CULPINJU": "contro la persona", "BLOWS": "contro la persona",
 "MENACE": "contro la persona", "OFFENCE": "contro la persona", "KIDNAPP": "contro la persona",
 "RAPE": "sessuali", "RAPEUN18": "sessuali", "CORRUPUN18": "sessuali", "PROSTI": "sessuali", "PORNO": "sessuali",
 "SWINCYB": "frodi e informatici", "CYBERCRIM": "frodi e informatici",
 "DRUG": "stupefacenti",
}
def tipo_label(c):
    return TIPO[c][0].upper() + TIPO[c][1:]

# territori usati nel dettaglio per tipo
PROV7 = {"IT": "Italia", "ITC45": "Milano (provincia)", "IT108": "Monza e della Brianza (provincia)", "ITE43": "Roma (provincia)",
         "ITC11": "Torino (provincia)", "ITF33": "Napoli (provincia)", "ITD55": "Bologna (provincia)", "ITE14": "Firenze (provincia)"}
COM6 = {"015146": "Milano (comune)", "058091": "Roma (comune)", "001272": "Torino (comune)", "063049": "Napoli (comune)",
        "037006": "Bologna (comune)", "048017": "Firenze (comune)"}

def readcsv(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig")))

# --- conteggi ISTAT (CRIMEN): 7 aree tutti i tipi + 6 comuni tutti i tipi + Monza (solo TOT dal file tutte-aree)
cnt = {}  # (area, anno, tipo) -> valore
for fn in ["df1_CRIMEN_7aree_tutti_tipi.csv", "df1_CRIMEN_6comuni_tutti_tipi.csv"]:
    for r in readcsv(f"{RAW}/istat/{fn}"):
        assert r["DATA_TYPE"] == "CRIMEN" and r["Y_KNOWN_OFFENDER_IDEN"] == "9" and r["REFERENCE_PERIOD_CRIME"] == "YRDUR"
        cnt[(r["REF_AREA"], int(r["TIME_PERIOD"]), r["TYPE_CRIME"])] = float(r["OBS_VALUE"])
tot_all = {}  # (area, anno) -> totale, tutte le aree (province+comuni+nuts)
for r in readcsv(f"{RAW}/istat/df1_CRIMEN_tutte_aree_TOT.csv"):
    tot_all[(r["REF_AREA"], int(r["TIME_PERIOD"]))] = float(r["OBS_VALUE"])
# --- tassi ISTAT (CRIMET) tutte le aree e tutti i tipi
rate = {}
flag = {}
for r in readcsv(f"{RAW}/istat/df9_CRIMET_tutte_aree.csv"):
    k = (r["REF_AREA"], int(r["TIME_PERIOD"]), r["TYPE_CRIME"])
    if r["OBS_VALUE"] == "":
        continue
    rate[k] = float(r["OBS_VALUE"]); flag[k] = r["OBS_STATUS"]
for r in readcsv(f"{RAW}/istat/df8_grandi_comuni_CRIMET.csv"):
    k = (r["REF_AREA"], int(r["TIME_PERIOD"]), r["TYPE_CRIME"])
    if r["OBS_VALUE"] == "":
        continue
    rate[k] = float(r["OBS_VALUE"]); flag[k] = r["OBS_STATUS"]

# controllo: i conteggi del file "tutte le aree TOT" coincidono con quelli dei file per tipo
bad = 0
for (a, y, t), v in cnt.items():
    if t == "TOT" and (a, y) in tot_all and tot_all[(a, y)] != v:
        bad += 1
P("controllo TOT file-tutte-aree vs file-per-tipo: discordanze =", bad)

# popolazione implicita (denominatore ISTAT) = delitti / tasso * 100000, dal totale
pop = {}
for (a, y), n in tot_all.items():
    t = rate.get((a, y, "TOT"))
    if t:
        pop[(a, y)] = n / t * 100000
# coerenza: stesso denominatore per un altro tipo (furti)
dev = []
for (a, y, t), v in cnt.items():
    if t == "THEFT" and (a, y, t) in rate and rate[(a, y, t)] > 0:
        dev.append(abs(v / rate[(a, y, t)] * 100000 / pop[(a, y)] - 1))
P("denominatore implicito: scarto massimo relativo tra totale e furti =", f"{max(dev):.5f}", "su", len(dev), "casi")
P("Milano provincia popolazione implicita:", {y: round(pop[("ITC45", y)]) for y in (2006, 2009, 2010, 2011, 2012, 2020, 2024) if ("ITC45", y) in pop})
P("Monza popolazione implicita:", {y: round(pop[("IT108", y)]) for y in (2010, 2011, 2012, 2024) if ("IT108", y) in pop})
P("anni Monza presenti:", sorted({y for (a, y) in tot_all if a == "IT108"}))

# serie combinata Milano + Monza (stessi confini 2006-2010 e 2011+)
comb_name = "Milano + Monza e Brianza (confini fino al 2010)"
def combined(y, t):
    if y <= 2010:
        return cnt.get(("ITC45", y, t)), pop.get(("ITC45", y))
    a, b = cnt.get(("ITC45", y, t)), tot_all.get(("IT108", y))
    pa, pb = pop.get(("ITC45", y)), pop.get(("IT108", y))
    return (a + b if a is not None and b is not None else None), (pa + pb if pa and pb else None)

# --- Tabella lunga
rows = []
def add(code, name, livello, y, t, n, pr):
    p = pop.get((code, y))
    rows.append({"anno": y, "codice_istat": code, "territorio": name, "livello": livello, "tipo_codice": t,
                 "tipo_delitto": tipo_label(t), "gruppo": GRUPPO.get(t, "altro"), "denunce": int(n) if n is not None else "",
                 "per_100mila": f"{n / p * 100000:.2f}" if (n is not None and p) else "",
                 "per_100mila_pubblicato_istat": pr if pr is not None else "",
                 "popolazione_istat_implicita": int(round(p)) if p else "",
                 "fonte": "ISTAT esploradati, dataflow 73_67_DF_DCCV_DELITTIPS_1 (conteggi) e _9/_8 (tassi), CC BY 4.0"})
for code, name in PROV7.items():
    for (a, y, t), n in sorted(cnt.items()):
        if a == code and t in TIPO:
            if code == "IT108":
                continue  # Monza: solo totale, vedi sotto
            add(code, name, "Italia" if code == "IT" else "provincia", y, t, n, rate.get((a, y, t)))
for code, name in COM6.items():
    for (a, y, t), n in sorted(cnt.items()):
        if a == code and t in TIPO:
            add(code, name, "comune", y, t, n, rate.get((a, y, t)))
# Monza solo totale
for (a, y), n in sorted(tot_all.items()):
    if a == "IT108":
        add("IT108", PROV7["IT108"], "provincia", y, "TOT", n, rate.get((a, y, "TOT")))
# combinata Milano+Monza tutti i tipi dove Monza ha il totale solo -> solo TOT (per i tipi non c'e' Monza)
for y in range(2006, 2025):
    n, p = combined(y, "TOT")
    if n is not None and p:
        rows.append({"anno": y, "codice_istat": "ITC45+IT108", "territorio": comb_name, "livello": "provincia (ricostruita)", "tipo_codice": "TOT",
                     "tipo_delitto": tipo_label("TOT"), "gruppo": "totale", "denunce": int(n), "per_100mila": f"{n / p * 100000:.2f}",
                     "per_100mila_pubblicato_istat": "", "popolazione_istat_implicita": int(round(p)),
                     "fonte": "somma mia di ISTAT ITC45 e IT108 (dal 2011); fino al 2010 e' ITC45 che include gia' Monza"})
fields = list(rows[0].keys())
with open(f"{OUT}/delitti_tipo_territorio_anno.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
P("scritto delitti_tipo_territorio_anno.csv", len(rows), "righe")

# --- Tutte le province: totale e rango
PROVCODES = {a for a in AREA if a.startswith("IT") and len(a) == 5 and a[2] in "CDEFG"} | {"IT108", "IT109", "IT110"}
byyear = collections.defaultdict(list)
for (a, y, t), v in rate.items():
    if t == "TOT" and a in PROVCODES:
        byyear[y].append((v, a))
prow = []
for y, lst in byyear.items():
    lst.sort(reverse=True)
    for i, (v, a) in enumerate(lst, 1):
        prow.append({"anno": y, "codice_istat": a, "provincia": AREA[a], "denunce": int(tot_all.get((a, y), 0)) or "",
                     "per_100mila": v, "rango": i, "n_province": len(lst),
                     "popolazione_istat_implicita": int(round(pop[(a, y)])) if (a, y) in pop else ""})
prow.sort(key=lambda r: (r["anno"], r["rango"]))
with open(f"{OUT}/province_totale_anno.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, list(prow[0].keys())); w.writeheader(); w.writerows(prow)
P("scritto province_totale_anno.csv", len(prow), "righe; province per anno:", {y: len(l) for y, l in sorted(byyear.items())})

# --- Comune di Milano ds564 (2004-2023)
LAB = {  # il file ha un '?' al posto delle lettere accentate
    "Violazione della propriet? intellettuale": "Violazione della proprietà intellettuale",
    "Riciclaggio e impiego di denaro, beni o utilit? di provenienza illecita": "Riciclaggio e impiego di denaro, beni o utilità di provenienza illecita"}
NAME2CODE = {  # ds564 -> codice ISTAT (stessa classificazione)
 "Strage": "MASSMURD", "Omicidi volontari totale": "INTENHOM", "Omicidi a scopo di furto o rapina": "ROBBHOM", "Omicidi di tipo mafioso": "MAFIAHOM",
 "Omicidi a scopo terroristico": "TERRORHOM", "Tentati omicidi": "ATTEMPHOM", "Infanticidi": "INFANTHOM", "Omicidi preterintenzionali": "MANSHOM",
 "Omicidi colposi totale": "UNINTHOM", "Omicidi colposi da incidente stradale": "ROADHOM", "Percosse": "BLOWS", "Lesioni dolose": "CULPINJU",
 "Minacce": "MENACE", "Sequestri di persona": "KIDNAPP", "Ingiurie": "OFFENCE", "Violenze sessuali": "RAPE", "Atti sessuali con minorenne": "RAPEUN18",
 "Corruzione di minorenne": "CORRUPUN18", "Sfruttamento e favoreggiamento della prostituzione": "PROSTI",
 "Pornografia minorile e detenzione di materiale pedopornografico": "PORNO", "Furti": "THEFT", "furti con strappo": "BAGTHEF",
 "Furti con destrezza": "PICKTHEF", "Furti in abitazioni": "BURGTHEF", "Furti in esercizi commerciali": "SHOPTHEF", "Furti in auto in sosta": "VEHITHEF",
 "Furti di opere d'arte e materiale archeologico": "ARTTHEF", "Furti di automezzi pesanti trasportanti merci": "TRUCKTHEF",
 "Furti di ciclomotori": "MOPETHEF", "Furti di motocicli": "MOTORTHEF", "Furti di autovetture": "CARTHEF", "Rapine totale": "ROBBER",
 "Rapine in abitazione": "HOUSEROB", "Rapine in banca": "BANKROB", "Rapine in uffici postali": "POSTROB", "Rapine in esercizi commerciali": "SHOPROB",
 "Rapine in pubblica via": "STREETROB", "Estorsioni": "EXTORT", "Truffe e frodi informatiche": "SWINCYB", "Delitti informatici": "CYBERCRIM",
 "Contraffazione di marchi e prodotti industriali": "COUNTER", "Violazione della proprietà intellettuale": "INTPROP", "Ricettazione": "RECEIV",
 "Riciclaggio e impiego di denaro, beni o utilità di provenienza illecita": "MONEYLAU", "Usura": "USURY", "Danneggiamenti": "DAMAGE",
 "Incendi totale": "ARSON", "Incendi boschivi": "FOREARS", "Danneggiamento seguito da incendio": "DAMARS", "Normativa sugli stupefacenti": "DRUG",
 "Attentati": "ATTACK", "Associazione per delinquere": "CRIMASS", "Associazione di tipo mafioso": "MAFIASS", "Contrabbando": "SMUGGL",
 "Altri delitti": "OTHCRIM", "Reati totale": "TOT"}
resid = collections.defaultdict(int)
for r in readcsv(f"{M}/popolazione/pulito/residenti_comune_anno_eta_genere.csv"):
    resid[int(r["anno"])] += int(r["residenti"])
c564 = readcsv(f"{RAW}/comune_ds564/ds564_reati_denunciati_2004_2023.csv")
out564 = []
unmatched = set()
# DIFETTO NEL FILE DEL COMUNE: la riga "2009, Omicidi volontari totale, 8" compare due volte con anno 2009 (22 e 8) e manca il 2019.
# La riga con 8 sta nel blocco 2020-2018 del file (riga 227) e ISTAT per il comune da' 8 nel 2019 e 22 nel 2009: la riattribuisco al 2019.
seen = collections.Counter((r["anno_rilevamento_reato"], " ".join(r["Reati_denunciati_tipologia"].split())) for r in c564)
dups = [k for k, c in seen.items() if c > 1]
miss = [(y, t) for t in {k[1] for k in seen} for y in map(str, range(2004, 2024)) if (y, t) not in seen]
P("ds564: chiavi (anno,tipo) duplicate:", dups, "| mancanti (anno,tipo):", sorted(miss)[:12], "... tot", len(miss))
for i, r in enumerate(c564):
    if (r["anno_rilevamento_reato"], " ".join(r["Reati_denunciati_tipologia"].split()), r["reati_denunciati"]) == ("2009", "Omicidi volontari totale", "8"):
        assert ("2019", "Omicidi volontari totale") not in seen
        r["anno_rilevamento_reato"] = "2019"
        P("ds564: riga", i + 2, "riattribuita da 2009 a 2019 (omicidi volontari = 8)")
for r in c564:
    nm = " ".join(r["Reati_denunciati_tipologia"].split())
    nm = LAB.get(nm, nm)
    code = NAME2CODE.get(nm)
    if code is None:
        unmatched.add(nm); continue
    if not r["reati_denunciati"].strip().isdigit():
        continue  # valore mancante (vuoto o "non disponibile") nel file del Comune
    y = int(r["anno_rilevamento_reato"]); n = int(r["reati_denunciati"])
    ist = cnt.get(("015146", y, code))
    out564.append({"anno": y, "tipo_codice": code, "tipo_delitto": tipo_label(code), "gruppo": GRUPPO.get(code, "altro"), "denunce_comune": n,
                   "residenti_comune_31dic": resid.get(y, ""), "per_100mila_residenti": f"{n / resid[y] * 100000:.2f}" if resid.get(y) else "",
                   "denunce_istat_comune_015146": int(ist) if ist is not None else "",
                   "fonte": "Comune di Milano ds564 (CC-BY); residenti: popolazione/pulito (ds27) sommando le eta'"})
P("tipi ds564 non agganciati:", unmatched)
with open(f"{OUT}/milano_comune_ds564.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, list(out564[0].keys())); w.writeheader(); w.writerows(out564)
# confronto ds564 vs ISTAT per il comune
diff = collections.Counter(); tot = 0
for r in out564:
    if r["denunce_istat_comune_015146"] != "":
        tot += 1
        if r["denunce_istat_comune_015146"] != r["denunce_comune"]:
            diff[r["anno"]] += 1
P("confronto ds564 vs ISTAT comune di Milano: righe confrontabili", tot, "; righe diverse per anno:", dict(sorted(diff.items())))
tot564 = {r["anno"]: r["denunce_comune"] for r in out564 if r["tipo_codice"] == "TOT"}
P("ds564 totale per anno:", tot564)
P("ISTAT comune Milano totale per anno:", {y: int(v) for (a, y, t), v in sorted(cnt.items()) if a == "015146" and t == "TOT"})
P("residenti comune (somma ds27):", {y: resid[y] for y in (2004, 2010, 2015, 2020, 2023)})
P("popolazione implicita ISTAT comune di Milano:", {y: round(pop[("015146", y)]) for y in (2006, 2010, 2015, 2020, 2023) if ("015146", y) in pop})
open(f"{OUT}/controlli_build.txt", "w", encoding="utf8").write("\n".join(log))
