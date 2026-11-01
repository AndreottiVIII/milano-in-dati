"""Legge gli zip MEF (comunale 2000-2024, sub-comunale 2011/2015/2019-2024) in raw/mef e scrive
tabelle pulite con nomi di colonna uniformi in pulito/.
Uso: python -I -X utf8 pulisci_mef.py <percorso assoluto redditi>
Le etichette delle colonne cambiano da un anno all'altro: si riconoscono con parole chiave (funzione canon).
Nessun numero e' modificato; _n = frequenza (numero contribuenti), _eur = ammontare in euro."""
import sys, os, re, csv, io, zipfile, glob, json
base = sys.argv[1]
RAW = os.path.join(base, "raw", "mef"); OUT = os.path.join(base, "pulito")
os.makedirs(OUT, exist_ok=True)

def canon(h):
    h = re.sub(r"\s+", " ", h.strip().lower()).replace("\u2019", "'").replace("\ufffd", "'").replace("à", "a")
    h = h.replace("contabilita'", "contabilita").replace("contabilità", "contabilita")
    if not h: return None
    if h.startswith("anno di imposta"): return "anno"
    if h == "cap": return "cap"
    if h == "codice catastale": return "catastale"
    if h in ("codice istat comune", "codice istat"): return "istat"
    if h == "denominazione comune": return "comune"
    if h == "sigla provincia": return "prov"
    if h == "regione": return "regione"
    if h == "codice istat regione": return "istat_reg"
    if h == "numero contribuenti": return "contribuenti"
    suf = "_n" if "frequenza" in h else "_eur"
    b = re.split(r" - ", h)[0]
    if b.startswith("reddito da fabbricati"): k = "fabbricati"
    elif b.startswith("reddito da lavoro dipendente e pensione"): k = "dip_e_pens"
    elif b.startswith("reddito da lavoro dipendente"): k = "dipendente"
    elif b.startswith("reddito da pensione"): k = "pensione"
    elif b.startswith("reddito da lavoro autonomo sez.e-ia"): k = "autonomo_eia"
    elif b.startswith("reddito da lavoro autonomo sez.e-ib"): k = "autonomo_eib"
    elif b.startswith("reddito da lavoro autonomo sez.e-ii"): k = "autonomo_eii"
    elif b.startswith("reddito da lavoro autonomo"): k = "autonomo"
    elif "imprenditore" in b and "ordinaria" in b: k = "imp_ordinaria"
    elif "imprenditore" in b and "semplificata" in b: k = "imp_semplificata"
    elif b.startswith("reddito da partecipazione"): k = "partecipazione"
    elif b.startswith("reddito imponibile addizionale"): k = "imponibile_addiz"
    elif b.startswith("reddito imponibile"): k = "imponibile"
    elif b.startswith("imposta netta"): k = "imposta_netta"
    elif b.startswith("addizionale regionale"): k = "addiz_reg"
    elif b.startswith("addizionale comunale"): k = "addiz_com"
    elif b.startswith("bonus spettante") or b.startswith("trattamento spettante"): k = "bonus_trattamento"
    elif b.startswith("reddito complessivo"):
        if "minore" in b: k = "cl0_le0"
        elif "da 0 a 10000" in b: k = "cl1_0_10k"
        elif "da 10000 a 15000" in b: k = "cl2_10_15k"
        elif "da 15000 a 26000" in b: k = "cl3_15_26k"
        elif "da 26000 a 55000" in b: k = "cl4_26_55k"
        elif "da 55000 a 75000" in b: k = "cl5_55_75k"
        elif "da 75000 a 120000" in b: k = "cl6_75_120k"
        elif "oltre 120000" in b: k = "cl7_oltre120k"
        else: k = "reddito_complessivo"
    else:
        raise ValueError("colonna non riconosciuta: " + h)
    return k + suf

def num(s):
    s = s.strip()
    if s == "": return None
    s = s.replace(" ", "")
    try: return int(s)
    except ValueError:
        try: return float(s.replace(",", "."))
        except ValueError: return None

def leggi(path):
    z = zipfile.ZipFile(path); n = z.namelist()
    assert len(n) == 1, n
    b = z.read(n[0])
    try: s = b.decode("utf8")
    except UnicodeDecodeError: s = b.decode("latin1")
    if s.startswith("\ufeff"): s = s[1:]
    r = csv.reader(io.StringIO(s), delimiter=";")
    hdr = next(r)
    cols = [canon(h) for h in hdr]
    dup = [c for c in cols if c and cols.count(c) > 1]
    assert not dup, (path, set(dup))
    rows = []
    for row in r:
        if not any(x.strip() for x in row): continue
        d = {}
        for c, v in zip(cols, row):
            if c is None: continue
            d[c] = v.strip() if c in ("catastale", "istat", "comune", "prov", "regione", "cap", "istat_reg", "anno") else num(v)
        rows.append(d)
    return rows, hdr, n[0]

STR = ["anno", "catastale", "istat", "comune", "prov", "regione", "istat_reg", "cap"]
def scrivi(nome, rows, extra_first):
    allk = []
    for d in rows:
        for k in d:
            if k not in allk: allk.append(k)
    first = [k for k in extra_first if k in allk]
    rest = sorted([k for k in allk if k not in first], key=lambda k: (k.endswith("_eur"), k))
    # ordine: contribuenti, poi per tipo n/eur affiancati
    tipi = []
    for k in allk:
        t = re.sub(r"_(n|eur)$", "", k)
        if k not in first and t not in tipi: tipi.append(t)
    cols = first + [t + s for t in tipi for s in ("_n", "_eur") if (t + s) in allk] + [k for k in allk if k not in first and not k.endswith(("_n", "_eur"))]
    cols = list(dict.fromkeys(cols))
    with open(os.path.join(OUT, nome), "w", newline="", encoding="utf8") as f:
        w = csv.writer(f); w.writerow(cols)
        for d in rows: w.writerow([d.get(c, "") if d.get(c) is not None else "" for c in cols])
    return cols

log = []
for kind, tag, years in (("comunale", "comuni", range(2000, 2025)), ("subcomunale", "cap", (2011, 2015, 2019, 2020, 2021, 2022, 2023, 2024))):
    allrows = []
    for y in years:
        p = os.path.join(RAW, f"Redditi_e_principali_variabili_IRPEF_su_base_{kind}_CSV_{y}.zip")
        rows, hdr, inner = leggi(p)
        for d in rows:
            d["anno"] = str(y) if not d.get("anno") else d["anno"]
        bad = [d for d in rows if d["anno"] != str(y)]
        log.append({"tipo": kind, "anno": y, "file_zip": os.path.basename(p), "file_interno": inner, "righe": len(rows), "colonne": len(hdr), "righe_con_anno_diverso": len(bad)})
        allrows += rows
    cols = scrivi(f"mef_{tag}_{min(years)}_{max(years)}.csv", allrows, STR + ["contribuenti"] if False else ["anno", "catastale", "istat", "comune", "prov", "regione", "istat_reg", "cap", "contribuenti"])
    print(kind, len(allrows), "righe;", len(cols), "colonne")
with open(os.path.join(OUT, "mef_lettura_log.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.DictWriter(f, fieldnames=list(log[0])); w.writeheader(); w.writerows(log)
print(json.dumps(log[:3]))
