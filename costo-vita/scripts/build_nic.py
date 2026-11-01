"""Indici dei prezzi al consumo (NIC) di Milano e dell'Italia: lettura, raccordo tra le basi, riepiloghi.
Uso: python -I -X utf8 build_nic.py <costo-vita assoluto>
Scrive in pulito/: nic_milano_voci_base2015.csv, nic_milano_divisioni_base2015.csv, nic_milano_generale_annuo_2000_2025.csv,
nic_italia_divisioni_base2015.csv, riepilogo_indici_voci.csv, controlli_nic.txt

RACCORDO (stessa idea dell'ISTAT): ogni segmento ha una base diversa (1998=100 per 2005-2010; 2010=100 per 2011-2015; 2015=100 per 2016-2025;
2025=100 per 2026). Si porta tutto a base 2015=100 usando la MEDIA DEL 2010, del 2015 e del 2025 come anni di aggancio.
Gli indici sono pubblicati con 1 decimale: errore di raccordo atteso dell'ordine di +-0,2-0,5 punti percentuali."""
import sys, os, csv, glob, re, unicodedata, collections, statistics
C = sys.argv[1]
RAW = os.path.join(C, "raw"); OUT = os.path.join(C, "pulito"); os.makedirs(OUT, exist_ok=True)
log = []
def say(s):
    print(s); log.append(s)

def nk(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-z]", "", s)

def readtext(p):
    b = open(p, "rb").read()
    try: return b.decode("utf-8-sig")
    except UnicodeDecodeError: return b.decode("cp1252", errors="replace")

def num(x):
    x = (x or "").strip().replace(",", ".")
    try: v = float(x)
    except ValueError: return None
    return v if v > 0 else None   # 0,0 = segnaposto di dato mancante nei file del Comune

MESI = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
MESI_LUNGHI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}

def wide(ds):
    """ds244 / ds245: righe = voci, colonne = gen-05 ... -> {nome: {YYYY-MM: val}}"""
    p = glob.glob(os.path.join(RAW, "comune", ds, "*.csv"))[0]
    rows = list(csv.reader(readtext(p).splitlines(), delimiter=";"))
    hdr = rows[0]; out = {}
    cols = []
    for h in hdr[1:]:
        m, y = h.strip().lower().split("-")
        cols.append("%04d-%02d" % (2000 + int(y), MESI[m]))
    for r in rows[1:]:
        if not r or not r[0].strip(): continue
        out[r[0].strip()] = {cols[i]: num(r[i + 1]) for i in range(len(cols)) if i + 1 < len(r) and num(r[i + 1]) is not None}
    return out

def longf(ds, namecol=1):
    """ds1433 / ds2979: Periodo;Sottoclasse;Numeri indice;Nota"""
    p = glob.glob(os.path.join(RAW, "comune", ds, "*.csv"))[0]
    out = collections.defaultdict(dict)
    for r in csv.reader(readtext(p).splitlines(), delimiter=";"):
        if not r or r[0] == "Periodo": continue
        v = num(r[2])
        if v is not None: out[r[namecol].strip()][r[0]] = v
    return out

def merge_by_nk(d):
    """unisce i nomi che differiscono solo per l'accento rotto (Caff / Caffè)"""
    out = collections.defaultdict(dict)
    for n, s in d.items():
        out[nk(n)].update(s)
    return out

E1 = merge_by_nk(wide("ds244"))      # 2005-2010, base 1998
E2 = merge_by_nk(wide("ds245"))      # 2011-2015, base 2010
E3 = merge_by_nk(longf("ds1433"))    # 2016-2025, base 2015
E4 = merge_by_nk(longf("ds2979"))    # 2026, base 2025
say("voci per segmento: ds244=%d ds245=%d ds1433=%d ds2979=%d" % (len(E1), len(E2), len(E3), len(E4)))

# ---------------------------------------------------------------- voci (sottoclassi / voci di prodotto) di Milano
# (id, etichetta, nome ds244 [2005-10, base 1998], ds245 [2011-15, base 2010], ds1433 [2016-25, base 2015], ds2979 [2026, base 2025], nota)
# un nome che finisce con * = prefisso (per i nomi con accento rotto: Caff, Caffe', "citt")
ITEMS = [
 ("pane", "Pane", "Pane", "Pane", "Pane", "Pane e prodotti da forno", "dal 2026 'Pane e prodotti da forno'"),
 ("pasta", "Pasta", "Pasta", "Pasta secca, pasta fresca e preparati di pasta", "Pasta secca, pasta fresca e preparati di pasta", None, "nel 2026 non c'e' una voce equivalente"),
 ("pizza_confezionata", "Pizza e quiche (da supermercato, NON pizzeria)", None, "Pizza e quiche", "Pizza e quiche", None, "serie 2011-2025"),
 ("latte", "Latte", "Latte", "Latte fresco", "Latte intero", "Latte crudo e intero", "definizioni leggermente diverse tra segmenti"),
 ("uova", "Uova", "Uova", "Uova", "Uova", "Uova", ""),
 ("caffe_prodotto", "Caffe' (pacco da casa)", "Caff*", "Caff*", "Caff*", "Caff*", ""),
 ("bar", "Consumazioni al bar", "Consumazioni al bar", "Consumazioni al bar e simili", None, None, "serie 2005-2015: dal 2016 il bar e' dentro 'Ristoranti, pizzerie, bar e simili'"),
 ("ristoranti", "Ristoranti e pizzerie (dal 2016 anche bar)", "Ristoranti, pizzerie e simili", "Ristoranti, pizzerie e simili", "Ristoranti, pizzerie, bar e simili", "Ristoranti, bar e simili - con servizio completo", "ROTTURA nel 2016: la voce incorpora il bar; 2026 solo 'servizio completo'"),
 ("affitti", "Affitti (canoni pagati da chi e' in affitto)", "Affitti reali", "Affitti reali per abitazioni di privati", "Affitti reali per l'abitazione principale", "Canoni di affitto effettivamente pagati dagli inquilini per la prima casa", "ISTAT: canoni dei contratti in corso, NON i prezzi OMI dei nuovi contratti"),
 ("acqua", "Acqua (fornitura)", "Acqua potabile", "Fornitura acqua", "Fornitura acqua", "Distribuzione d'acqua attraverso sistemi di reti", ""),
 ("rifiuti", "Rifiuti (tariffa)", "Tariffa rifiuti solidi", "Raccolta rifiuti", "Raccolta rifiuti", "Raccolta dei rifiuti", ""),
 ("spese_condominiali", "Spese condominiali", "Spese condominiali", "Spese condominiali", "Spese condominiali", "Spese condominiali", ""),
 ("elettricita", "Energia elettrica", "Energia elettrica", "Energia elettrica", "Energia elettrica", "Elettricit*", ""),
 ("gas", "Gas di rete", "Gas", "Gas di citt*", "Gas di citt*", "Gas naturale distribuito tramite rete", ""),
 ("benzina", "Benzina", "Benzine", "Benzina", "Benzina", "Benzina", ""),
 ("gasolio_auto", "Gasolio per auto", None, "Gasolio per mezzi di trasporto", "Gasolio per mezzi di trasporto", "Carburante diesel", "serie dal 2011"),
 ("bus_tram_metro", "Trasporto urbano / autobus", "Trasporti urbani", "Trasporto passeggeri su autobus e pulman", "Trasporto passeggeri su autobus e pullman", "Trasporto di passeggeri su autobus e pullman", "2005-2010 'Trasporti urbani'; dal 2011 'autobus e pullman' (include extraurbano): definizione NON identica"),
 ("taxi", "Taxi", "Taxi", "Trasporto passeggeri su taxi", "Trasporto passeggeri su taxi", "Trasporto di passeggeri su taxi e veicoli noleggiati con autista", ""),
 ("treno", "Treno", "Trasporti ferroviari", "Trasporto ferroviario passeggeri", "Trasporto ferroviario passeggeri", "Trasporto ferroviario di passeggeri", ""),
 ("cinema_teatri", "Cinema e teatri", "Cinema, teatri e musei", "Cinema, teatri e concerti", "Cinema, teatri e concerti", "Servizi forniti da cinema, teatri e sale da concerto", "2005-2010 include i musei"),
 ("parrucchiere_uomo", "Parrucchiere uomo", None, "Servizi di parrucchiere per uomo e bambino", "Servizi di parrucchiere per uomo e bambino", "Servizi di parrucchiere", "serie dal 2011; nel 2026 un'unica voce uomo+donna"),
 ("alberghi", "Alberghi", "Alberghi", "Alberghi, motel, pensioni e simili", "Alberghi, motel, pensioni e simili", "Alberghi, motel, pensioni e simili", ""),
 ("giornali", "Giornali", "Giornali", "Giornali", "Giornali", "Giornali", ""),
 ("libri_scolastici", "Libri scolastici", "Libri scolastici", "Libri scolastici", "Libri scolastici", "Libri didattici e libri di testo", ""),
 ("telefonia_mobile", "Telefonia", "Servizi di telefonia", "Servizi di telefonia mobile", "Servizi di telefonia mobile", None, "2005-2010 fissa+mobile insieme; 2026 non raccordata"),
 ("medicinali", "Medicinali", "Medicinali", "Prodotti farmaceutici", "Prodotti farmaceutici", "Medicinali, vaccini e altri preparati farmaceutici", ""),
 ("sigarette", "Sigarette", "Sigarette", "Sigarette", "Sigarette", "Sigarette", ""),
 ("univ", "Istruzione universitaria", "Istruzione universitaria", "Istruzione universitaria, escluso dottorato di ricerca (ISCED 5)", "Istruzione universitaria, escluso dottorato di ricerca (ISCED 5)", "Istruzione universitaria", ""),
 ("assic_auto", "Assicurazione auto", "Assicurazioni sui mezzi di trasporto", "Assicurazioni sui mezzi di trasporto", "Assicurazioni sui mezzi di trasporto", "Servizi assicurativi connessi ai mezzi personali di trasporto", ""),
]

def pick(E, name):
    if name is None: return None
    if name.endswith("*"):
        pre = nk(name[:-1]); out = {}
        for k, s in E.items():
            if k.startswith(pre): out.update(s)
        return out or None
    return E.get(nk(name))

def avg(s, y):
    v = [s.get("%04d-%02d" % (y, m)) for m in range(1, 13)]
    v = [x for x in v if x is not None]
    return statistics.mean(v) if len(v) == 12 else None

def chain(s1, s2, s3, s4):
    """porta tutto a base 2015=100 con le medie annue 2010 (s1->s2), 2015 (s2->s3), 2025 (s3->s4)"""
    out = {}; warn = []
    if not s3:
        if s2:   # serie che finisce nel 2015: base 2010=100
            out.update(s2)
            if s1:
                a10 = avg(s1, 2010)
                if a10:
                    for k, v in s1.items(): out[k] = v * 100.0 / a10
            return out, ["serie 2005-2015 in base 2010=100 (finisce nel 2015)"]
        return out, ["manca il segmento 2016-2025: non raccordabile"]
    out.update(s3)
    a25 = avg(s3, 2025)
    if s4:
        if a25 is None: warn.append("manca la media 2025")
        else:
            for k, v in s4.items(): out[k] = v * a25 / 100.0
    if s2:
        a15 = avg(s2, 2015)
        if a15 is None: warn.append("manca la media 2015 nel segmento 2011-15")
        else:
            for k, v in s2.items(): out[k] = v * 100.0 / a15
            if s1:
                a10 = avg(s1, 2010)
                if a10 is None: warn.append("manca la media 2010 nel segmento 2005-10")
                else:
                    for k, v in s1.items(): out[k] = v * 100.0 / a10 * 100.0 / a15
    return out, warn

def seg_of(p):
    y = int(p[:4]); return 1 if y <= 2010 else 2 if y <= 2015 else 3 if y <= 2025 else 4

voci = {}; vrows = []
for iid, label, n1, n2, n3, n4, note in ITEMS:
    s = [pick(E1, n1), pick(E2, n2), pick(E3, n3), pick(E4, n4)]
    ser, warn = chain(*s)
    if not ser:
        say("VOCE SALTATA %s: %s" % (iid, warn)); continue
    voci[iid] = (label, ser, note, warn, [x is not None for x in s])
    for p in sorted(ser):
        vrows.append([iid, label, p, round(ser[p], 3), seg_of(p), ["ds244", "ds245", "ds1433", "ds2979"][seg_of(p) - 1]])
    if warn: say("AVVISO %s: %s" % (iid, warn))
    if not all(x is not None for x in s): say("  nota: %s manca in alcuni segmenti %s" % (iid, [x is not None for x in s]))
with open(os.path.join(OUT, "nic_milano_voci_base2015.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["voce", "etichetta", "periodo", "indice_base2015_100", "segmento", "dataset_comune"]); w.writerows(vrows)
say("voci raccordate: %d, righe %d" % (len(voci), len(vrows)))

# ---------------------------------------------------------------- divisioni di spesa e indice generale di Milano (2011-2026)
def divs_ds91():
    p = glob.glob(os.path.join(RAW, "comune", "ds91", "*.csv"))[0]
    out = collections.defaultdict(dict)
    for r in csv.reader(readtext(p).splitlines(), delimiter=";"):
        if not r or r[0] == "Periodo": continue
        m, y = r[0].lower().split("-")
        mm = re.search(r"(\d\d)\s*:", r[1])
        if not mm: continue
        out[int(mm.group(1))]["%04d-%02d" % (int(y), MESI[m[:3]])] = num(r[2])
    return out
def divs_long(ds):
    p = glob.glob(os.path.join(RAW, "comune", ds, "*.csv"))[0]
    out = collections.defaultdict(dict); names = {}
    for r in csv.reader(readtext(p).splitlines(), delimiter=";"):
        if not r or r[0] == "Periodo": continue
        c = int(r[1]); out[c][r[0]] = num(r[3]); names[c] = r[2]
    return out, names
D2 = divs_ds91(); D3, NAMES3 = divs_long("ds1436"); D4, NAMES4 = divs_long("ds2976")
DIV_OK = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11]   # divisioni con stesso contenuto prima e dopo il 2026 (la 08, 09, 12 cambiano con ECOICOP 2)
drows = []; div = {}
for c in DIV_OK:
    ser, warn = chain(None, D2.get(c), D3.get(c), D4.get(c))
    div[c] = ser
    for p in sorted(ser): drows.append([c, NAMES3[c], p, round(ser[p], 3), seg_of(p)])
    if warn: say("AVVISO divisione %d: %s" % (c, warn))
with open(os.path.join(OUT, "nic_milano_divisioni_base2015.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["divisione", "nome", "periodo", "indice_base2015_100", "segmento"]); w.writerows(drows)
gen = div[0]

# controllo con ISTAT SDMX (Milano ITC45, divisione 00)
def sdmx(fn):
    out = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(RAW, "istat_sdmx", fn), encoding="utf-8")):
        k = [x for x in r if x in ("COICOP_REV_ISTAT", "E_COICOP_REV_ISTAT", "ECOICOP_2")][0]
        if r["MEASURE"] != "4" or not r["OBS_VALUE"]: continue
        out[(r["REF_AREA"], r[k])][r["TIME_PERIOD"]] = float(r["OBS_VALUE"])
    return out
S2 = sdmx("nic_2011_2015_ITC45_IT_coicop3.csv"); S3 = sdmx("nic_2016_2025_ITC45_IT_principali.csv"); S4 = sdmx("nic_2026_ITC45_IT_principali.csv")
def istat_chain(area, code):
    ser, w = chain(None, S2.get((area, code)), S3.get((area, code)), S4.get((area, code)))
    return ser
gm = istat_chain("ITC45", "00")
dif = [(p, gen[p], gm[p]) for p in sorted(gen) if p in gm]
mx = max(abs(a - b) for _, a, b in dif)
say("CONTROLLO indice generale Milano: Comune (ds91/ds1436/ds2976) contro ISTAT SDMX ITC45: %d mesi, differenza massima %.2f punti; media %.3f" % (len(dif), mx, statistics.mean(a - b for _, a, b in dif)))

# ---------------------------------------------------------------- Italia: divisioni 1996-2026 base 2015
def sdmx_it_long():
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in csv.DictReader(open(os.path.join(RAW, "istat_sdmx", "nic_1996_2025_IT_ecoicop2_tuttebasi.csv"), encoding="utf-8")):
        if r["MEASURE"] != "4" or not r["OBS_VALUE"]: continue
        out[r["ECOICOP_2"]][r["DATA_TYPE"]][r["TIME_PERIOD"]] = float(r["OBS_VALUE"])
    return out
IT = sdmx_it_long()
def it_series(code):
    t = IT[code]; s95, s10, s15 = t.get("1", {}), t.get("9", {}), t.get("39", {})
    out = {}
    out.update(s15)
    a15 = avg(s10, 2015); a10 = avg(s95, 2010)
    for k, v in s10.items(): out[k] = v * 100.0 / a15
    for k, v in s95.items(): out[k] = v * 100.0 / a10 * 100.0 / a15
    s26 = S4.get(("IT", code))
    if s26:
        a25 = avg(s15, 2025)
        for k, v in s26.items(): out[k] = v * a25 / 100.0
    return out
it_rows = []; it = {}
for c in ["%02d" % d for d in DIV_OK]:
    if c not in IT: continue
    it[c] = it_series(c)
    for p in sorted(it[c]): it_rows.append(["IT", c, p, round(it[c][p], 3)])
with open(os.path.join(OUT, "nic_italia_divisioni_base2015.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["area", "codice_ecoicop", "periodo", "indice_base2015_100"]); w.writerows(it_rows)
say("Italia: divisioni %s, periodo %s - %s" % (sorted(it), min(it["00"]), max(it["00"])))
for a, b in [("2010-12", "2011-01"), ("2015-12", "2016-01"), ("2025-12", "2026-01")]:
    say("  continuita' raccordo Italia indice generale %s=%.2f -> %s=%.2f" % (a, it["00"][a], b, it["00"][b]))
    if a in gen: say("  continuita' raccordo Milano indice generale %s=%.2f -> %s=%.2f" % (a, gen[a], b, gen[b]))

# controllo: salto mensile ai punti di raccordo (dic->gen) confrontato con il salto tipico dei mesi vicini
say("SALTI AI RACCORDI (variazione % dic->gen; per confronto: variazione % media assoluta degli altri mesi della stessa voce)")
for iid, (label, ser, note, warn, pres) in voci.items():
    typ = statistics.mean(abs(ser[k] / ser[j] - 1) * 100 for j, k in zip(sorted(ser)[:-1], sorted(ser)[1:]) if j[5:] != "12" and ser[j])
    out = []
    for a, b in [("2010-12", "2011-01"), ("2015-12", "2016-01"), ("2025-12", "2026-01")]:
        if a in ser and b in ser: out.append("%s->%s %+.1f%%" % (a[:4], b[:4], (ser[b] / ser[a] - 1) * 100))
    say("  %-20s tipico %.1f%% | %s" % (iid, typ, "; ".join(out)))
# ---------------------------------------------------------------- inflazione annua 2000-2025: Milano (ds1821) e Italia
ann_m = {}
for r in csv.reader(readtext(glob.glob(os.path.join(RAW, "comune", "ds1821", "*.csv"))[0]).splitlines(), delimiter=";"):
    if r and r[0].isdigit(): ann_m[int(r[0])] = float(r[1])
L = {1999: 100.0}
for y in range(2000, 2026): L[y] = L[y - 1] * (1 + ann_m[y] / 100.0)
f25 = 100.0 / L[2025]; Lm = {y: L[y] * f25 for y in L}
Li = {}
for y in range(1996, 2026):
    a = avg(it["00"], y)
    if a: Li[y] = a
fi = 100.0 / Li[2025]
chk = []
for y in range(2011, 2026):
    real = avg(gen, y); chk.append((y, real / avg(gen, 2025) * 100, Lm[y]))
say("CONTROLLO ricostruzione annua Milano (da tassi ds1821) contro medie annue dell'indice vero: errore max %.2f punti (2025=100)" % max(abs(a - b) for _, a, b in chk))
with open(os.path.join(OUT, "nic_milano_generale_annuo_2000_2025.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["anno", "tasso_annuo_milano_ds1821_pct", "livello_milano_2025_100_da_tassi", "livello_milano_2025_100_da_indice_vero", "livello_italia_2025_100_NIC", "tasso_italia_NIC_pct_calcolato"])
    for y in range(2000, 2026):
        real = avg(gen, y)
        w.writerow([y, ann_m[y], round(Lm[y], 3), round(real / avg(gen, 2025) * 100, 3) if real else "", round(Li[y] * fi, 3), round((Li[y] / Li[y - 1] - 1) * 100, 2) if y - 1 in Li else ""])

# ---------------------------------------------------------------- riepilogo per voce
def last12(ser, end="2026-09"):
    ks = sorted(k for k in ser if k <= end)[-12:]
    return statistics.mean(ser[k] for k in ks) if len(ks) == 12 else None
def pct(a, b): return round((b / a - 1) * 100, 1) if a and b else ""
rows = []
def addrow(kind, key, label, ser, note=""):
    a05, a10, a15, a20, a25 = [avg(ser, y) for y in (2005, 2010, 2015, 2020, 2025)]
    a21, a22, a23 = avg(ser, 2021), avg(ser, 2022), avg(ser, 2023)
    l26 = ser.get("2026-09")
    if a25 is None and a15 and a05:
        note = (note + " | serie corta: variazione 2005->2015 = %+.1f%%" % ((a15 / a05 - 1) * 100)).strip(" |")
    rows.append([kind, key, label, min(ser), pct(a05, a25), pct(a10, a25), pct(a15, a25), pct(a20, a25), pct(a21, a22), pct(a22, a23),
                 round(a25, 1) if a25 else "", round(l26, 1) if l26 else "", pct(a25, l26), note])
for iid, (label, ser, note, warn, pres) in voci.items():
    addrow("voce Milano", iid, label, ser, note + (" | AVVISO: " + "; ".join(warn) if warn else ""))
for c in DIV_OK:
    addrow("divisione Milano", "%02d" % c, NAMES3[c], div[c])
for c in sorted(it):
    addrow("divisione Italia", c, "ECOICOP %s" % c, it[c], "Italia" if c != "00" else "Italia, indice generale")
with open(os.path.join(OUT, "riepilogo_indici_voci.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["tipo", "chiave", "etichetta", "primo_mese", "var_pct_2005_2025", "var_pct_2010_2025", "var_pct_2015_2025", "var_pct_2020_2025", "var_pct_2021_2022", "var_pct_2022_2023", "indice_media_2025_base2015", "indice_2026_09_base2015", "var_pct_media2025_a_2026_09", "note"])
    w.writerows(rows)
say("INFLAZIONE CUMULATA indice generale (medie annue): Milano 2000->2025 = %.1f%% ; Italia NIC 2000->2025 = %.1f%%" % ((Lm[2025] / Lm[2000] - 1) * 100, (Li[2025] / Li[2000] - 1) * 100))
say("   Milano 2010->2025 = %.1f%% ; Italia = %.1f%%  | Milano 2020->2025 = %.1f%% ; Italia = %.1f%%" % ((Lm[2025] / Lm[2010] - 1) * 100, (Li[2025] / Li[2010] - 1) * 100, (Lm[2025] / Lm[2020] - 1) * 100, (Li[2025] / Li[2020] - 1) * 100))
open(os.path.join(OUT, "controlli_nic.txt"), "w", encoding="utf-8").write("\n".join(log) + "\n")
