"""Pulisce i dati grezzi sui musei -> pulito/ (CSV con ';' e punto decimale).
uso: python -I -X utf8 05_pulisci.py <cartella musei assoluta>
Legge raw/comune_milano (ds575, ds577, ds513, ds160), raw/mic (Tavole 1, 2, 7, 8 del 2024).
Scrive: civici_mensili.csv, civici_annuali.csv, civici_incassi.csv, statali_milano.csv, statali_italia.csv,
        mic_top30_2024.csv, mic_province_2024.csv, controlli.txt"""
import csv, os, sys, glob, collections, warnings
import openpyxl
warnings.simplefilter("ignore")
base = sys.argv[1]
raw = lambda *p: os.path.join(base, "raw", *p)
out = lambda n: os.path.join(base, "pulito", n)
os.makedirs(os.path.join(base, "pulito"), exist_ok=True)
log = []
MESI = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
NOMI = {"900": "Museo del Novecento", "ACQUARIO": "Acquario civico", "ANTIQUARIUM": "Antiquarium Alda Levi", "ARCHEOLOGICO": "Museo Archeologico",
        "CASA BOSCHI": "Casa Museo Boschi Di Stefano", "CASTELLO": "Musei del Castello Sforzesco", "GAM": "Galleria d'Arte Moderna",
        "MORANDO": "Museo di Milano / Palazzo Morando", "MUDEC": "Mudec", "MUSEO MESSINA": "Studio Museo Francesco Messina",
        "MUSEO STOR. NAT.": "Museo di Storia Naturale", "STORIA NATURALE": "Museo di Storia Naturale", "PLANETARIO": "Planetario",
        "RISORGIMENTO": "Museo del Risorgimento", "S.GIOV. IN CONCA": "Chiesa di San Giovanni in Conca", "SAN GIOV. IN CONCA": "Chiesa di San Giovanni in Conca"}


def w(path, head, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        c = csv.writer(f, delimiter=";", lineterminator="\n")
        c.writerow(head)
        c.writerows(rows)


def leggi(path):
    return list(csv.DictReader(open(path, encoding="utf-8-sig", newline=""), delimiter=";"))


def f1(pat):
    g = glob.glob(raw("comune_milano", pat))
    assert len(g) == 1, pat
    return g[0]


# ---- musei civici, mensili (ds575)
r = leggi(f1("ds575_*"))
mens = collections.OrderedDict()
tipo = {}
for x in r:
    nome = NOMI[x["Museo"].strip()]
    a = int(x["Anno"])
    m = MESI.index(x["Mese"].strip()) + 1
    mens[(nome, a, m)] = int(x["Visitatori"])
    tipo[(nome, a)] = x["Ingresso"].strip()
log.append(f"ds575: {len(r)} righe, {len(mens)} museo-anno-mese distinti (nessun doppione: {len(r) == len(mens)})")
w(out("civici_mensili.csv"), ["museo", "anno", "mese", "visitatori"], [(k[0], k[1], k[2], v) for k, v in sorted(mens.items())])
ann = collections.defaultdict(lambda: [0, 0])
for (n, a, m), v in mens.items():
    ann[(n, a)][0] += v
    ann[(n, a)][1] += 1
w(out("civici_annuali.csv"), ["museo", "anno", "visitatori", "mesi_con_dato", "ingresso"],
  [(n, a, v[0], v[1], tipo[(n, a)]) for (n, a), v in sorted(ann.items())])
# ---- incassi (ds577)
r = leggi(f1("ds577_*"))
inc = collections.defaultdict(float)
for x in r:
    inc[(NOMI[x["Museo"].strip()], int(x["Anno"]))] += float(x["Incasso"] or 0)
w(out("civici_incassi.csv"), ["museo", "anno", "incasso_euro"], [(n, a, round(v)) for (n, a), v in sorted(inc.items())])

# ---- musei statali a Milano (ds513, Comune di Milano da dati MiC)
r = leggi(f1("ds513_*"))
rows = []
for x in r:
    nome = x["museo nome"].strip()
    if nome.startswith("Parco dell'Anfiteatro"):
        nome = "Antiquarium Alda Levi e Anfiteatro romano"

    def fl(s):
        return float(s.replace(",", ".")) if s.strip() else None
    rows.append((nome, int(x["anno"]), int(x["visitatori paganti"]), int(x["visitatori non paganti"]), int(x["Totale visitatori"]),
                 fl(x["Introiti lordi in euro"]), fl(x["Introiti netti in euro"])))
rows.sort(key=lambda t: (t[0], t[1]))
w(out("statali_milano.csv"), ["museo", "anno", "paganti", "non_paganti", "totale", "introiti_lordi_euro", "introiti_netti_euro"], rows)
for t in rows:
    assert t[2] + t[3] == t[4], t
log.append(f"ds513: {len(rows)} righe museo-anno; paganti + non paganti = totale in tutte")

# ---- tavola 1 MiC: Italia
ws = openpyxl.load_workbook(raw("mic", "MUSEI_TAVOLA1_2024-1.xlsx"), data_only=True).active
sez = None
ita = {}
for r_ in ws.iter_rows(values_only=True):
    c = [v for v in r_ if v is not None]
    if not c:
        continue
    if isinstance(c[0], str):
        u = c[0].strip().upper()
        if u in ("MUSEI", "MONUMENTI E AREE ARCHEOLOGICHE", "CIRCUITI MUSEALI", "TOTALE"):
            sez = u
        continue
    if isinstance(c[0], int) and 1996 <= c[0] <= 2024 and len(c) >= 10 and sez:
        ita[(sez, c[0])] = c
# colonne: anno, istituti a pagamento, gratuiti, totale, paganti, non paganti (istituti a pagamento), totale istituti a pagamento,
#          visitatori degli istituti gratuiti, totale visitatori, introiti lordi
w(out("statali_italia.csv"), ["sezione", "anno", "istituti", "paganti", "non_paganti", "tot_istituti_a_pagamento", "visitatori_istituti_gratuiti", "totale_visitatori", "introiti_lordi_euro"],
  [(s, a, c[3], c[4], c[5], c[6], c[7], c[8], round(c[9], 2)) for (s, a), c in sorted(ita.items())])
for (s, a), c in ita.items():
    assert c[6] + c[7] == c[8], (s, a, c)
log.append("Tavola 1 (Italia): visitatori degli istituti a pagamento + gratuiti = totale visitatori, in tutte le righe")

# ---- tavola 8 top 30 e tavola 2 province
ws = openpyxl.load_workbook(raw("mic", "MUSEI_TAVOLA8_2024-1.xlsx"), data_only=True).active
rows = []
for r_ in ws.iter_rows(values_only=True):
    c = [v for v in r_ if v is not None]
    if c and isinstance(c[0], int):
        rows.append((c[0], c[1], c[2], c[3], c[4], round(c[5], 2)))
w(out("mic_top30_2024.csv"), ["posto", "istituto", "provincia", "comune", "visitatori", "introiti_lordi_euro"], rows)
ws = openpyxl.load_workbook(raw("mic", "MUSEI_TAVOLA2_2024-1.xlsx"), data_only=True).active
rows = []
for r_ in ws.iter_rows(values_only=True):
    c = [v for v in r_ if v is not None]
    if c and isinstance(c[0], str) and c[0] in ("MILANO", "LOMBARDIA", "ROMA", "FIRENZE", "NAPOLI", "VENEZIA", "TORINO"):
        rows.append(c[:10])
w(out("mic_province_2024.csv"), ["provincia", "istituti_a_pagamento", "istituti_gratuiti", "istituti", "paganti", "non_paganti_ist_pag", "tot_ist_pag", "visitatori_ist_gratuiti", "totale", "introiti_lordi_euro"], rows)

# controllo incrociato Tavola 7 (per istituto) con ds513, 2024
ws = openpyxl.load_workbook(raw("mic", "MUSEI_TAVOLA7_2024-1.xlsx"), data_only=True).active
t7 = {}
for r_ in ws.iter_rows(values_only=True):
    c = [v for v in r_ if v is not None]
    hit = [x for x in c if x in ("Cenacolo Vinciano", "Pinacoteca di Brera")]
    if hit:
        t7[hit[0]] = [x for x in c if isinstance(x, (int, float))][:3]
d24 = {t[0]: t for t in csv.reader(open(out("statali_milano.csv"), encoding="utf-8"), delimiter=";") if t[1] == "2024"}
for k, v in t7.items():
    ok = [int(d24[k][2]), int(d24[k][3]), int(d24[k][4])] == [int(x) for x in v]
    log.append(f"Tavola 7 (MiC 2024) {k}: {v} contro ds513 {d24[k][2:5]}: {'uguali' if ok else 'DIVERSI'}")
mi = [t for t in csv.reader(open(out("mic_province_2024.csv"), encoding="utf-8"), delimiter=";") if t[0] == "MILANO"][0]
s24 = sum(int(t[4]) for t in d24.values())
log.append(f"Tavola 2 (provincia di Milano 2024): {mi[8]} visitatori; somma ds513 2024: {s24}: {'uguali' if int(mi[8]) == s24 else 'DIVERSI'}")

# ---- ds160 (1996-2010): confronto con ds575 e ds513
r = leggi(f1("ds160_*"))
a160 = {}
for x in r:
    v = x["VISITATORI"].strip()
    if v.isdigit():
        a160[(x["DENOMINAZIONE"].strip(), int(x["ANNI"]))] = int(v)
conf = []
for (n, a), v in sorted(a160.items()):
    for k, nn in (("Acquario", "Acquario civico"), ("Castello Sforzesco", "Musei del Castello Sforzesco"), ("Museo di Storia Naturale", "Museo di Storia Naturale"), ("Museo Archeologico", "Museo Archeologico")):
        if n == k and a in range(2007, 2011) and (nn, a) in ann:
            conf.append(f"{n} {a}: ds160 {v} / ds575 {ann[(nn, a)][0]}")
log.append("Confronto ds160 / ds575 (2007-2010): " + "; ".join(conf))
sb = {(t[0], int(t[1])): int(t[4]) for t in csv.reader(open(out("statali_milano.csv"), encoding="utf-8"), delimiter=";") if t[1].isdigit()}
dd = []
for a in range(1996, 2011):
    for k in ("Cenacolo Vinciano", "Pinacoteca di Brera"):
        if (k, a) in a160 and (k, a) in sb and a160[(k, a)] != sb[(k, a)]:
            dd.append(f"{k} {a}: ds160 {a160[(k, a)]} / ds513 {sb[(k, a)]}")
log.append("Differenze ds160 / ds513 per Brera e Cenacolo (1996-2010): " + ("; ".join(dd) if dd else "nessuna"))
open(out("controlli.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
