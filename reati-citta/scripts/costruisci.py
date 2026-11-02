"""Pulizia e riepiloghi per reati-citta (rieseguibile, nessuna rete).

Uso:  python -I -X utf8 costruisci.py <cartella reati-citta assoluta> <cartella milano-in-dati assoluta>

Legge  raw/  (ISTAT altridelps2, percezione PPC_1_GC e PPC_6_GC; Comune ds516)
       e, della cartella reati/ gia' fatta, la popolazione implicita (pulito/province_totale_anno.csv,
       pulito/delitti_tipo_territorio_anno.csv) e il tasso 2024 dei 12 grandi comuni (docs/reati/data/grandi_comuni.json).
Scrive pulito/*.csv, pulito/riepilogo.json e out/riepilogo.txt (numeri citati nella pagina).
"""
import sys, os, csv, json, collections

BASE = sys.argv[1]
ROOT = sys.argv[2]
P = lambda *a: os.path.join(BASE, *a)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)


def wcsv(name, header, rows):
    with open(P("pulito", name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


os.makedirs(P("pulito"), exist_ok=True)
os.makedirs(P("out"), exist_ok=True)

# ---------------------------------------------------------------- A. famiglia, stalking, immagini
TIPI = {"CP572": "Maltrattamenti contro familiari e conviventi",
        "CP612BIS": "Atti persecutori (stalking)",
        "CP612TER": "Diffusione illecita di immagini o video sessualmente espliciti"}
MESI = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEPT", "OCT", "NOV", "DEC"]
rows = list(csv.DictReader(open(P("raw", "istat", "altridelps2.csv"), encoding="utf-8")))
cnt = {}  # (area,tipo,anno,mese)->n
for r in rows:
    if r["REF_AREA"] in ("ITC45", "IT") and r["TYPE_CRIME"] in TIPI and r["DATA_TYPE"] == "CRIMEN":
        cnt[(r["REF_AREA"], r["TYPE_CRIME"], int(r["TIME_PERIOD"]), r["MONTH_CRIME_COMMIT"])] = int(float(r["OBS_VALUE"]))

# popolazione implicita (denominatore costruito in reati/: denunce / tasso x 100.000)
pop = {}
for r in csv.DictReader(open(os.path.join(ROOT, "reati", "pulito", "province_totale_anno.csv"), encoding="utf-8")):
    if r["codice_istat"] == "ITC45":
        pop[("ITC45", int(r["anno"]))] = int(r["popolazione_istat_implicita"])
for r in csv.DictReader(open(os.path.join(ROOT, "reati", "pulito", "delitti_tipo_territorio_anno.csv"), encoding="utf-8")):
    if r["codice_istat"] == "IT" and r["tipo_codice"] == "TOT":
        pop[("IT", int(r["anno"]))] = int(r["popolazione_istat_implicita"])

NOME = {"ITC45": "Milano (provincia)", "IT": "Italia"}
annuale = []
for (a, t, y, m), n in sorted(cnt.items()):
    if m == "YEAR":
        p = pop.get((a, y))
        annuale.append([y, a, NOME[a], t, TIPI[t], n, p, round(n / p * 1e5, 2) if p else ""])
annuale.sort(key=lambda x: (x[3], x[1], x[0]))
wcsv("famiglia_stalking_annuale.csv", ["anno", "codice_istat", "territorio", "tipo_codice", "tipo_delitto", "denunce", "popolazione_implicita", "per_100mila"], annuale)

mensile = []
for (a, t, y, m), n in sorted(cnt.items()):
    if m != "YEAR":
        mensile.append([y, MESI.index(m) + 1, a, NOME[a], t, TIPI[t], n])
mensile.sort(key=lambda x: (x[4], x[2], x[0], x[1]))
wcsv("famiglia_stalking_mensile.csv", ["anno", "mese", "codice_istat", "territorio", "tipo_codice", "tipo_delitto", "denunce"], mensile)

# controllo: somma dei mesi = totale annuo dove i mesi ci sono
bad = 0
chk = 0
for (a, t, y, m), n in cnt.items():
    if m == "YEAR":
        s = [cnt.get((a, t, y, mm)) for mm in MESI]
        if all(v is not None for v in s):
            chk += 1
            if sum(s) != n:
                bad += 1
say("Controllo somma dei 12 mesi = totale annuo:", chk, "casi controllati,", bad, "differenze")

A = {"annuale": {}, "mesi": {}}
# tasso totale dei delitti 2024 (stessa fonte e stesso denominatore della pagina Reati), per il confronto
_tot = {}
for r in csv.DictReader(open(os.path.join(ROOT, "reati", "pulito", "delitti_tipo_territorio_anno.csv"), encoding="utf-8")):
    if r["tipo_codice"] == "TOT" and r["anno"] == "2024" and r["codice_istat"] in ("ITC45", "IT"):
        _tot[r["codice_istat"]] = [int(r["denunce"]), float(r["per_100mila"])]
A["tot2024"] = _tot
say("totale delitti 2024 (denunce, per 100.000):", _tot, "rapporto Milano/Italia:", round(_tot["ITC45"][1] / _tot["IT"][1], 2))
for t in TIPI:
    for a in ("ITC45", "IT"):
        A["annuale"].setdefault(t, {})[a] = {str(r[0]): [r[5], r[7]] for r in annuale if r[3] == t and r[1] == a}
        say(t, a, {r[0]: (r[5], r[7]) for r in annuale if r[3] == t and r[1] == a})
# quota di Milano sul totale italiano e quota della popolazione
for t in TIPI:
    q = {y: cnt[("ITC45", t, y, "YEAR")] / cnt[("IT", t, y, "YEAR")] * 100 for y in range(2018, 2025) if ("ITC45", t, y, "YEAR") in cnt and ("IT", t, y, "YEAR") in cnt}
    say("quota Milano su Italia", t, {y: round(v, 2) for y, v in q.items()})
say("quota popolazione implicita Milano su Italia", {y: round(pop[("ITC45", y)] / pop[("IT", y)] * 100, 2) for y in range(2018, 2025)})


def var(a, t, y0, y1, rate=False):
    k = 7 if rate else 5
    d = {r[0]: r[k] for r in annuale if r[3] == t and r[1] == a}
    return (d[y1] / d[y0] - 1) * 100


for t in TIPI:
    y0 = 2018 if t != "CP612TER" else 2019
    say("variazione %d-2024 denunce / tasso:" % y0, t, "Milano", round(var("ITC45", t, y0, 2024), 1), round(var("ITC45", t, y0, 2024, True), 1),
        "Italia", round(var("IT", t, y0, 2024), 1), round(var("IT", t, y0, 2024, True), 1))

# stagionalita': quota di ogni mese sul totale 2019-2024 (Milano e Italia)
stag = {}
for t in ("CP572", "CP612BIS"):  # per CP612TER i mesi 2019 non ci sono
    for a in ("ITC45", "IT"):
        tot = sum(cnt[(a, t, y, m)] for y in range(2019, 2025) for m in MESI)
        stag.setdefault(t, {})[a] = [round(sum(cnt[(a, t, y, m)] for y in range(2019, 2025)) / tot * 100, 2) for m in MESI]
        say("quota % per mese 2019-2024", t, a, "(totale %d)" % tot, stag[t][a])
A["stagionalita"] = stag
A["tot_2019_2024"] = {t: {a: sum(cnt[(a, t, y, m)] for y in range(2019, 2025) for m in MESI) for a in ("ITC45", "IT")} for t in ("CP572", "CP612BIS")}
say("mesi disponibili CP612TER Milano:", sorted({(y, m) for (a, t, y, m) in cnt if t == "CP612TER" and a == "ITC45" and m != "YEAR"})[:3], "...")

# ---------------------------------------------------------------- B. percezione della sicurezza
NOMI_COM = {}
b1 = list(csv.DictReader(open(P("raw", "istat", "DF_DCSS_BEST_PPC_1_GC.csv"), encoding="utf-8")))
b6 = list(csv.DictReader(open(P("raw", "istat", "DF_DCSS_BEST_PPC_6_GC.csv"), encoding="utf-8")))
NAMES = {"001272": "Torino", "010025": "Genova", "015146": "Milano", "017029": "Brescia", "023091": "Verona", "027042": "Venezia", "028060": "Padova",
         "032006": "Trieste", "034027": "Parma", "035033": "Reggio nell'Emilia", "036023": "Modena", "037006": "Bologna", "039014": "Ravenna",
         "048017": "Firenze", "049009": "Livorno", "054039": "Perugia", "058091": "Roma", "063049": "Napoli", "072006": "Bari", "073027": "Taranto",
         "080063": "Reggio di Calabria", "082053": "Palermo", "083048": "Messina", "087015": "Catania", "092009": "Cagliari", "099014": "Rimini", "100005": "Prato"}
# (nomi presi dal dizionario dei codici ISTAT scaricato con raw/istat/dsd_PPC.xml, verificati sui 27 codici a 6 cifre)
v1 = collections.defaultdict(dict)
for r in b1:
    if r["REF_AREA"] in NAMES and r["GENDER"] == "T":
        v1[(r["REF_AREA"], int(r["TIME_PERIOD"]))][r["PERC_CRIME_RISK"]] = float(r["OBS_VALUE"])
v6 = collections.defaultdict(dict)
for r in b6:
    if r["REF_AREA"] in NAMES and r["GENDER"] == "T":
        v6[(r["REF_AREA"], int(r["TIME_PERIOD"]))][r["PERC_SAF_WAD"]] = float(r["OBS_VALUE"])

perc = []
maxdiff1 = maxdiff6 = 0
for (a, y), d in sorted(v1.items()):
    tot = d["ALL"]
    somma = sum(v for k, v in d.items() if k not in ("ALL",))
    maxdiff1 = max(maxdiff1, abs(somma - tot) / tot)
    perc.append([y, a, NAMES[a], "rischio_criminalita_zona", "famiglie", round(tot),
                 round((d["CR_V_MUCH"] + d["CR_QUITE_BIT"]) / tot * 100, 1),  # molto + abbastanza
                 round(d["CR_V_MUCH"] / tot * 100, 1)])
perc_buio = []
for (a, y), d in sorted(v6.items()):
    tot = d["ALL"]
    somma = sum(v for k, v in d.items() if k != "ALL")
    maxdiff6 = max(maxdiff6, abs(somma - tot) / tot)
    perc_buio.append([y, a, NAMES[a], "sicurezza_camminando_al_buio", "persone 14+", round(tot),
                      round((d["SI_LITTLE_SAFE"] + d["SI_NATALL_SAFE"]) / tot * 100, 1),  # poco + per niente sicuro
                      round(d["SI_NATALL_SAFE"] / tot * 100, 1),
                      round((d["SI_NEVER_GO"] + d["SI_NEVER_GO_AL"]) / tot * 100, 1),     # non esce mai / mai da solo
                      round((d["SI_COMP_SAFE"] + d["SI_QUITE_SAFE"]) / tot * 100, 1)])
say("Percezione: scarto massimo tra somma delle categorie e totale: rischio criminalita'", round(maxdiff1 * 100, 3), "%; buio", round(maxdiff6 * 100, 3), "%")
wcsv("percezione_rischio_criminalita_zona.csv", ["anno", "codice_istat", "comune", "indicatore", "unita", "totale_stimato", "pct_molto_o_abbastanza", "pct_molto"], perc)
wcsv("percezione_sicurezza_buio.csv", ["anno", "codice_istat", "comune", "indicatore", "unita", "totale_stimato", "pct_poco_o_per_niente_sicuro", "pct_per_niente_sicuro", "pct_non_esce_mai_o_mai_da_solo", "pct_molto_o_abbastanza_sicuro"], perc_buio)


def ranking(tab, col, y):
    rr = sorted([r for r in tab if r[0] == y], key=lambda r: -r[col])
    return [(i + 1, r[2], r[col]) for i, r in enumerate(rr)]


B = {"rischio": {}, "buio": {}}
for y in (2022, 2023, 2024):
    rk = ranking(perc, 6, y)
    B["rischio"][str(y)] = [{"nome": n, "v": v, "rango": i} for i, n, v in rk]
    rm = [x for x in rk if x[1] == "Milano"][0]
    say("rischio criminalita' zona (molto+abbastanza)", y, "Milano", rm[2], "rango", rm[0], "su", len(rk), "| 1:", rk[0][1], rk[0][2], "| ultimo:", rk[-1][1], rk[-1][2],
        "| media semplice dei comuni:", round(sum(x[2] for x in rk) / len(rk), 1))
    rk = ranking(perc_buio, 6, y)
    B["buio"][str(y)] = [{"nome": n, "v": v, "rango": i} for i, n, v in rk]
    rm = [x for x in rk if x[1] == "Milano"][0]
    say("buio poco+per niente sicuro", y, "Milano", rm[2], "rango", rm[0], "su", len(rk), "| 1:", rk[0][1], rk[0][2], "| ultimo:", rk[-1][1], rk[-1][2],
        "| media semplice dei comuni:", round(sum(x[2] for x in rk) / len(rk), 1))
for r in perc_buio:
    if r[1] == "015146":
        say("Milano buio", r[0], "poco/per niente", r[6], "per niente", r[7], "non esce mai/mai da solo", r[8], "molto/abbastanza sicuro", r[9], "persone 14+ stimate", r[5])
for r in perc:
    if r[1] == "015146":
        say("Milano rischio", r[0], "molto+abbastanza", r[6], "molto", r[7], "famiglie stimate", r[5])

# confronto con le denunce 2024 (tasso del comune, 12 grandi comuni, da docs/reati/data/grandi_comuni.json)
gc = json.load(open(os.path.join(ROOT, "docs", "reati", "data", "grandi_comuni.json"), encoding="utf-8"))
den24 = {x["nome"]: x["tasso"] for x in gc["per_anno"]["2024"]}
conf = []
for nm, td in sorted(den24.items(), key=lambda kv: -kv[1]):
    r1 = [r for r in perc if r[2] == nm and r[0] == 2024][0]
    r6 = [r for r in perc_buio if r[2] == nm and r[0] == 2024][0]
    conf.append([nm, td, r1[6], r6[6]])
wcsv("confronto_denunce_percezione_2024.csv", ["comune", "denunce_per_100mila_2024", "pct_rischio_molto_o_abbastanza_2024", "pct_buio_poco_o_per_niente_sicuro_2024"], conf)
B["confronto"] = [{"nome": c[0], "den": c[1], "risk": c[2], "buio": c[3]} for c in conf]
for c in conf:
    say("confronto 2024", c)

# ---------------------------------------------------------------- C. 118
raw = list(csv.reader(open(P("raw", "comune_ds516", "ds516.csv"), encoding="cp1252"), delimiter=";"))
hdr = raw[0]
cod = ["bianco", "verde", "giallo", "rosso"]
c118 = []
for r in raw[1:]:
    tipo = r[1].replace("�", "à")
    for i, c in enumerate(cod):
        v = r[2 + i].strip()
        c118.append([int(r[0]), tipo, c, int(v) if v != "" else ""])
c118.sort(key=lambda x: (x[1], x[0], cod.index(x[2])))
wcsv("interventi_118_milano_2004_2015.csv", ["anno", "tipo_intervento", "codice_colore", "interventi"], c118)
tipi118 = sorted({r[1] for r in c118})
say("tipi 118:", tipi118)
agg = {}
tot = {}
for r in c118:
    if r[3] == "" or r[2] == "bianco":
        continue
    tot[r[0]] = tot.get(r[0], 0) + r[3]
    if r[1].startswith("Aggressioni"):
        agg[r[0]] = agg.get(r[0], 0) + r[3]
bianco = {r[0]: r[3] for r in c118 if r[1].startswith("Aggressioni") and r[2] == "bianco" and r[3] != ""}
rosso = {r[0]: r[3] for r in c118 if r[1].startswith("Aggressioni") and r[2] == "rosso" and r[3] != ""}
C = {"rosso": rosso, "anni": sorted(agg), "aggressioni_vgr": [agg[y] for y in sorted(agg)], "totale_vgr": [tot[y] for y in sorted(agg)],
     "quota_pct": [round(agg[y] / tot[y] * 100, 2) for y in sorted(agg)], "bianco": bianco}
say("118 aggressioni (verde+giallo+rosso):", agg)
say("118 totale interventi (verde+giallo+rosso):", tot)
say("118 quota aggressioni %:", C["quota_pct"])
say("118 aggressioni codice bianco (dal 2012):", bianco)
mn = min(agg, key=agg.get)
mx = max(agg, key=agg.get)
say("118 aggressioni minimo", mn, agg[mn], "massimo", mx, agg[mx], "2004->2015", round((agg[2015] / agg[2004] - 1) * 100, 1), "%")

json.dump({"A": A, "B": B, "C": C, "NOMI": NOME}, open(P("pulito", "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False)
open(P("out", "riepilogo.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")
print("fatto")
