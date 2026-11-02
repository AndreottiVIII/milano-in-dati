"""Estrae le tabelle del Ministero dell'Interno (INT 00004, sfratti) e le famiglie ISTAT in sfratti/pulito/.

Uso (percorsi assoluti, rilanciabile):
  python -I -X utf8 estrai.py <sfratti_dir>

Legge: raw/ministero_interno/*.xlsx|xls (province 2013-2025), raw/ministero_interno/sfratti_anno_2012.pdf (serie 2001-2012 delle
province dei grandi comuni e dell'Italia), raw/istat_probe/*.zip (famiglie ISTAT: censimenti 1971-2011 e censimento permanente 2018-2024).
Scrive: pulito/province_2013_2025.csv, pulito/grandi_province_2001_2012.csv, pulito/italia_2001_2025.csv,
        pulito/famiglie_territori.csv, pulito/controlli_estrazione.txt
Ogni riga dice file e foglio/pagina di origine. Nessun numero e' corretto a mano: i controlli di somma sono stampati.
"""
import sys, os, re, csv, glob, io, zipfile, json, collections
import openpyxl, xlrd
import pymupdf as fitz

BASE = sys.argv[1]
RAW = os.path.join(BASE, "raw")
MI = os.path.join(RAW, "ministero_interno")
PU = os.path.join(BASE, "pulito")
os.makedirs(PU, exist_ok=True)
LOG = []
def say(s):
    print(s); LOG.append(s)

REGIONI = {"Piemonte", "Valle d'Aosta", "Lombardia", "Trentino Alto Adige", "Trentino A. A.", "Trentino-Alto Adige", "Veneto", "Friuli V. G.",
           "Friuli Venezia Giulia", "Liguria", "Emilia Romagna", "Emilia-Romagna", "Toscana", "Umbria", "Marche", "Lazio", "Abruzzo", "Molise",
           "Campania", "Puglia", "Basilicata", "Calabria", "Sicilia", "Sardegna", "ITALIA", "Italia", "TOTALE", "Totale", "Totale Italia"}

def num(x):
    if x is None or x == "":
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def righe(f):
    if f.endswith(".xlsx"):
        wb = openpyxl.load_workbook(f, data_only=True)
        for ws in wb:
            for i, r in enumerate(ws.iter_rows(values_only=True), 1):
                yield ws.title, i, list(r)
    else:
        wb = xlrd.open_workbook(f)
        for ws in wb.sheets():
            for i in range(ws.nrows):
                yield ws.name, i + 1, ws.row_values(i)

# ------------------------------------------------------------------ A. province 2013-2025 dai file xlsx/xls
FILE_ANNO = {
    "SFRATTI Anno 2013.xlsx": 2013, "SFRATTI Anno 2014.xlsx": 2014, "SFRATTI Anno 2015.xlsx": 2015, "Sfratti Anno 2016.xls": 2016,
    "Sfratti Anno 2017.xls": 2017, "SFRATTI Anno 2018.xlsx": 2018, "Dati_Sfratti__al_31-12-2019_-_Provinciali.xlsx": 2019,
    "2021_Dati_Sfratti_al_31-12-2020-Provinciali.xlsx": 2020,
    "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2021 (1).xlsx": 2021, "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2022.xlsx": 2022,
    "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2023.xlsx": 2023, "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2024.xlsx": 2024,
    "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2025.xlsx": 2025,
}
CAMPI = ["nec_cap", "nec_resto", "fin_cap", "fin_resto", "mor_cap", "mor_resto", "totale", "var_tot_pct", "richieste", "var_rich_pct", "eseguiti", "var_eseg_pct"]
PROV = []
for fn, anno in FILE_ANNO.items():
    f = os.path.join(MI, fn)
    if not os.path.exists(f):
        say(f"MANCA {fn} (anno {anno})")
        continue
    nb = ""
    visti = set()
    for sh, i, r in righe(f):
        if "provincial" in sh.lower() or sh in ("tabella", "Foglio1", "Province", "Regioni-Province"):
            pass
        else:
            continue
        nome0 = r[0] if r else None
        if isinstance(nome0, str) and nome0.strip().startswith("N.B."):
            nb = nome0.strip()
        if not isinstance(nome0, str):
            continue
        nome = re.sub(r"\s*\(.*$", "", nome0.strip()) if not nome0.strip().startswith("(") else nome0.strip()
        flag = re.findall(r"\((\w)\)", nome0.strip()) if not nome0.strip().startswith("(") else []
        vals = [num(c) for c in r[1:13]]  # per posizione: le variazioni % possono mancare (None)
        vals += [None] * (12 - len(vals))
        if any(v is None for v in vals[:7]) or vals[8] is None or vals[10] is None or nome in REGIONI or nome.startswith("(") or nome.startswith("N.B"):
            continue
        # evitare le righe di totale regionale dentro il foglio provinciale (stesso nome della regione)
        if nome in ("Lombardia",):
            continue
        key = (anno, nome)
        if key in visti:
            continue
        visti.add(key)
        d = dict(zip(CAMPI, vals[:12]))
        chk = sum(d[k] for k in ("nec_cap", "nec_resto", "fin_cap", "fin_resto", "mor_cap", "mor_resto"))
        d.update(anno=anno, provincia=nome, flag_riga=",".join(flag), somma_ok=int(abs(chk - d["totale"]) < 0.5),
                 nota_foglio=nb[:300], fonte=f"{fn} | {sh} | riga {i}")
        PROV.append(d)
say(f"province 2013-2025 estratte: {len(PROV)} righe; anni: {sorted(set(p['anno'] for p in PROV))}")
bad = [p for p in PROV if not p["somma_ok"]]
say(f"righe in cui la somma dei motivi non torna col totale: {len(bad)}")
for p in bad[:20]:
    say(f"  {p['anno']} {p['provincia']}: motivi={sum(p[k] for k in CAMPI[:6])} totale={p['totale']}")

# provincia incompleta: nota del foglio dice quali province hanno dati incompleti
def incompleta(p):
    nb = p["nota_foglio"]
    if not nb:
        return 0
    return int(re.search(r"\b" + re.escape(p["provincia"]) + r"\b", nb) is not None)
for p in PROV:
    p["incompleta_secondo_nota"] = incompleta(p)

# 2020: il file originale non e' scaricabile (il server non risponde); si ricava dalle variazioni % dei dati 2021 (derivato, 2 decimali)
if not any(p["anno"] == 2020 for p in PROV):
    der = []
    for p in PROV:
        if p["anno"] != 2021:
            continue
        def inv(v, pct):
            if v is None or pct is None:
                return None
            return v / (1 + pct / 100.0) if pct > -100 else None
        d = dict(anno=2020, provincia=p["provincia"], totale=inv(p["totale"], None), richieste=inv(p["richieste"], p["var_rich_pct"]),
                 eseguiti=inv(p["eseguiti"], p["var_eseg_pct"]))
        # il totale 2021 ha la variazione sul 2020 (var_tot_pct)
        d["totale"] = inv(p["totale"], p["var_tot_pct"])
        for k in CAMPI:
            d.setdefault(k, None)
        for k in ("totale", "richieste", "eseguiti"):
            if d[k] is not None:
                d[k] = round(d[k])
        d.update(flag_riga="", somma_ok=0, nota_foglio="", incompleta_secondo_nota=0,
                 fonte="DERIVATO: valore 2021 diviso (1+variazione % rispetto al 2020) dal file dati_2021; il file 2020 non era scaricabile")
        der.append(d)
    PROV += der
    say(f"2020 derivato dalle variazioni % del file 2021: {len(der)} province (solo totale, richieste, eseguiti; niente motivi)")

cols = ["anno", "provincia"] + CAMPI + ["flag_riga", "somma_ok", "incompleta_secondo_nota", "nota_foglio", "fonte"]
PROV.sort(key=lambda p: (p["anno"], p["provincia"]))
with open(os.path.join(PU, "province_2013_2025.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(PROV)

# controllo: somma province lombarde = riga Lombardia (solo anni con regione nel foglio)
for fn, anno in FILE_ANNO.items():
    f = os.path.join(MI, fn)
    if not os.path.exists(f):
        continue
    reg = None
    for sh, i, r in righe(f):
        if r and isinstance(r[0], str) and r[0].strip() == "Lombardia":
            vals = [num(c) for c in r[1:]]
            vals = [v for v in vals if v is not None]
            if len(vals) >= 12:
                reg = vals[6]  # totale emessi; l'ultima riga trovata e' il subtotale in provincia, o la riga regionale
    LOMB = {"Bergamo", "Brescia", "Como", "Cremona", "Lecco", "Lodi", "Mantova", "Milano", "Monza e della Brianza", "Monza e Brianza", "Pavia", "Sondrio", "Varese"}
    s = sum(p["totale"] for p in PROV if p["anno"] == anno and (p["provincia"] in LOMB or p["provincia"].startswith("Milano") or p["provincia"].startswith("Monza")))
    if reg is not None:
        say(f"controllo Lombardia {anno}: somma province={s:.0f} riga regione={reg:.0f} {'ok' if abs(s-reg) < 1 else 'DIVERSO'}")

# ------------------------------------------------------------------ B. serie nazionale 2004-2025 (xlsx 2025) + 2001-2003 (pdf 2012)
IT = {}
f25 = os.path.join(MI, "INT00004-PROCEDURE_RILASCIO_IMMOBILI_USO_ABITATIVO_dati_2025.xlsx")
for sh, i, r in righe(f25):
    if sh.startswith("Serie storica") and isinstance(r[0], int) and 2004 <= r[0] <= 2025:
        v = [c for c in r[1:] if c is not None]
        IT[r[0]] = dict(anno=r[0], nec=v[0], fin=v[1], mor=v[2], totale=v[3], richieste=v[5], eseguiti=v[7],
                        fonte=f"{os.path.basename(f25)} | {sh} | riga {i}")
pdf12 = fitz.open(os.path.join(MI, "sfratti_anno_2012.pdf"))
txt = "\n".join(p.get_text() for p in pdf12)
# righe 2001-2003 della tabella nazionale (pdf 2012, pag. 27 della numerazione del documento)
tl = pdftxt = None
import subprocess
pl = subprocess.run(["pdftotext", "-layout", os.path.join(MI, "sfratti_anno_2012.pdf"), "-"], capture_output=True, text=True, encoding="utf8", errors="replace").stdout
for m in re.finditer(r"^(200[123])\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d,]+)\s+([\d.]+)\s+(-?[\d,]+)\s+([\d.]+)\s+(-?[\d,]+)\s*$", pl, re.M):
    a = int(m.group(1))
    n = lambda s: int(s.replace(".", ""))
    if n(m.group(2)) + n(m.group(3)) + n(m.group(4)) != n(m.group(5)):
        continue  # altra tabella del rapporto con una riga 2001 simile
    IT[a] = dict(anno=a, nec=n(m.group(2)), fin=n(m.group(3)), mor=n(m.group(4)), totale=n(m.group(5)), richieste=n(m.group(7)), eseguiti=n(m.group(9)),
                 fonte="sfratti_anno_2012.pdf | Tab. serie nazionale 2001-2012 (pag. 25-26 del rapporto)")
say("Italia anni estratti: " + str(sorted(IT)))
for a, d in sorted(IT.items()):
    if d["nec"] is not None and d["fin"] is not None and abs(d["nec"] + d["fin"] + d["mor"] - d["totale"]) > 1:
        say(f"  Italia {a}: motivi {d['nec']+d['fin']+d['mor']} totale {d['totale']} (differenza)")
with open(os.path.join(PU, "italia_2001_2025.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.DictWriter(fh, fieldnames=["anno", "nec", "fin", "mor", "totale", "richieste", "eseguiti", "fonte"], delimiter=";")
    w.writeheader()
    for a in sorted(IT):
        w.writerow(IT[a])

# ------------------------------------------------------------------ C. 2001-2012 per le province dei grandi comuni (pdf 2012, pag. 63-71)
CITTA = {"T O R I N O": "Torino", "M I L A N O": "Milano (con Monza e Brianza)", "B O L O G N A": "Bologna", "F I R E N Z E": "Firenze", "R O M A": "Roma", "N A P O L I": "Napoli"}
GR = []
for pi in range(len(pdf12)):
    t = pdf12[pi].get_text()
    nome = [v for k, v in CITTA.items() if k in t]
    if not nome or not re.search(r"Tab\. (2[3-9]|3[0-5])", t):
        continue
    toks = [x.strip() for x in t.split("\n")]
    # sequenza: anno, [flag], nec, fin, mor, totale, richieste, eseguiti
    s = " | ".join(toks)
    for m in re.finditer(r"(20(?:0[1-9]|1[0-2]))(?: \((\w)\))? \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+)", s):
        n = lambda x: int(x.replace(".", ""))
        a = int(m.group(1))
        if any(g["anno"] == a and g["provincia"] == nome[0] for g in GR):
            continue
        GR.append(dict(anno=a, provincia=nome[0], flag=m.group(2) or "", nec=n(m.group(3)), fin=n(m.group(4)), mor=n(m.group(5)), totale=n(m.group(6)),
                       richieste=n(m.group(7)), eseguiti=n(m.group(8)), fonte=f"sfratti_anno_2012.pdf | pag. {pi+1} del file | Tab. province dei grandi comuni"))
say(f"grandi province 2001-2012: {len(GR)} righe; per citta': " + str(collections.Counter(g['provincia'] for g in GR)))
for g in GR:
    if g["nec"] + g["fin"] + g["mor"] != g["totale"]:
        say(f"  somma diversa: {g['provincia']} {g['anno']}: {g['nec']+g['fin']+g['mor']} vs {g['totale']}")
GR.sort(key=lambda g: (g["provincia"], g["anno"]))
with open(os.path.join(PU, "grandi_province_2001_2012.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.DictWriter(fh, fieldnames=["anno", "provincia", "flag", "nec", "fin", "mor", "totale", "richieste", "eseguiti", "fonte"], delimiter=";")
    w.writeheader()
    w.writerows(GR)

# ------------------------------------------------------------------ D. famiglie ISTAT
CODICI = {  # codice ISTAT: (etichetta, tipo)
    "IT": ("Italia", "paese"),
    "ITC11": ("Torino", "provincia"), "ITC45": ("Milano", "provincia"), "IT108": ("Monza e della Brianza", "provincia"), "ITD55": ("Bologna", "provincia"),
    "ITE14": ("Firenze", "provincia"), "ITE43": ("Roma", "provincia"), "ITF33": ("Napoli", "provincia"),
    "001272": ("Torino", "comune"), "015146": ("Milano", "comune"), "037006": ("Bologna", "comune"), "048017": ("Firenze", "comune"),
    "058091": ("Roma", "comune"), "063049": ("Napoli", "comune"),
}
FAM = []
zc = zipfile.ZipFile(os.path.join(RAW, "istat_probe", "DICA_FAM_CARATT-data.zip"))
nome = "CSV - DATI CODICI E DESCRIZIONI - DATA AND DESCRIPTION/DICA_FAM_CARATT-data-it.csv"
rd = csv.DictReader(io.TextIOWrapper(zc.open(nome), encoding="utf-8-sig"), delimiter="|")
for r in rd:
    if r["ITTER107"] in CODICI and r["TIPO_DATO_CENS_POP"] == "NPHH_AV" and r["TIP_FAM"] == "HH" and r["NUMEROSITA"] == "TOT" and r["TIME"] in ("2001", "2011"):
        eti, tipo = CODICI[r["ITTER107"]]
        if r["COND_ABIT"] == "ALL" and r["ABITAZ_FAM"] == "ALL" and r["TIT_POSSESSO"] == "ALL" and r["CONTESTO_ABIT"] == "ALL":
            FAM.append(dict(codice=r["ITTER107"], territorio=eti, tipo=tipo, anno=int(r["TIME"]), famiglie=int(float(r["Value"])), tipo_dato="famiglie_censimento",
                            fonte="ISTAT DCSS/censtatv5db DICA_FAM_CARATT-data.zip (Censimento popolazione e abitazioni)"))
        elif r["COND_ABIT"] == "ALL" and r["ABITAZ_FAM"] == "PH_IN_CDW" and r["CONTESTO_ABIT"] == "ALL" and r["TIT_POSSESSO"] in ("RENT", "OWN", "OTH_OR") and r["TIME"] == "2011":
            FAM.append(dict(codice=r["ITTER107"], territorio=eti, tipo=tipo, anno=2011, famiglie=int(float(r["Value"])), tipo_dato={"RENT": "famiglie_in_affitto", "OWN": "famiglie_proprieta", "OTH_OR": "famiglie_altro_titolo"}[r["TIT_POSSESSO"]],
                            fonte="ISTAT DICA_FAM_CARATT-data.zip (Censimento 2011, famiglie in abitazione per titolo di godimento)"))
zp = zipfile.ZipFile(os.path.join(RAW, "istat_probe", "fam_pop.zip"))
rd = csv.DictReader(io.TextIOWrapper(zp.open(zp.namelist()[0]), encoding="utf-8-sig"), delimiter="|")
for r in rd:
    if r["ITTER107"] in CODICI and r["TIPO_DATO_CENS_POP"] == "NPHH_AV":
        eti, tipo = CODICI[r["ITTER107"]]
        FAM.append(dict(codice=r["ITTER107"], territorio=eti, tipo=tipo, anno=int(r["TIME"]), famiglie=round(float(r["Value"])), tipo_dato="famiglie_31dic_censimento_permanente",
                        fonte="ISTAT esploradati DCSS_FAM_POP (censimento permanente, famiglie al 31 dicembre)"))
FAM.sort(key=lambda d: (d["tipo"], d["territorio"], d["tipo_dato"], d["anno"]))
with open(os.path.join(PU, "famiglie_territori.csv"), "w", newline="", encoding="utf8") as fh:
    w = csv.DictWriter(fh, fieldnames=["codice", "territorio", "tipo", "anno", "tipo_dato", "famiglie", "fonte"], delimiter=";")
    w.writeheader()
    w.writerows(FAM)
say(f"famiglie ISTAT: {len(FAM)} righe")
for d in FAM:
    if d["tipo_dato"] == "famiglie_censimento":
        say(f"  {d['tipo']:9s} {d['territorio']:22s} {d['anno']}: {d['famiglie']:>10,}")

open(os.path.join(PU, "controlli_estrazione.txt"), "w", encoding="utf8").write("\n".join(LOG))
