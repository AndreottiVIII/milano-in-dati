"""MIMIT carburanti: archivio trimestrale (tar.gz) -> estratto dei soli impianti del comune di Milano.
Uso: python -I -X utf8 carburanti_milano.py <costo-vita assoluto>
Per ogni trimestre 2015-1 ... 2026-3:
  1. scarica anagrafica (tar.gz), estrae primo e ultimo file giornaliero, tiene gli impianti con Comune = MILANO e Provincia = MI
  2. (poi) scarica prezzo_alle_8 (tar.gz), tiene le righe di quegli impianti (unione di tutti i trimestri), aggiunge la data del file
I tar.gz originali si cancellano dopo l'estrazione; si registrano dimensione e sha256 in raw/download_log.csv.
Riprendibile: salta cio' che c'e'."""
import sys, os, tarfile, io, csv, hashlib, urllib.request, datetime, time, re, glob
base = sys.argv[1]
R = os.path.join(base, "raw", "mimit"); A = os.path.join(R, "archivio"); M = os.path.join(R, "archivio_milano")
os.makedirs(A, exist_ok=True); os.makedirs(M, exist_ok=True)
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
H = {"User-Agent": "milano-in-dati/1.0"}
quarters = [(y, q) for y in range(2015, 2027) for q in range(1, 5) if (y, q) <= (2026, 3)]
def fetch(url, dst):
    if os.path.exists(dst): return
    t = time.time()
    data = None
    for tentativo in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120).read(); break
        except Exception as e:
            print("riprovo", url, e, flush=True); time.sleep(10)
    if data is None: raise SystemExit("scaricamento fallito " + url)
    open(dst, "wb").write(data)
    log.write("%s;200;%s;%d;%s;%s (cancellato dopo estrazione)\n" % (datetime.date.today(), url, len(data), hashlib.sha256(data).hexdigest()[:16], dst)); log.flush()
    print("scaricato", url, len(data), round(time.time() - t), "s", flush=True)
def dec(b):
    try: return b.decode("utf-8")
    except UnicodeDecodeError: return b.decode("cp1252")
# fase 1: anagrafica
ids = set()
for y, q in quarters:
    out = os.path.join(M, "anagrafica_milano_%d_%d.csv" % (y, q))
    if not os.path.exists(out) and (y, q) > (2021, 2) and not (q == 1 or (y, q) == (2026, 3)):
        continue   # dopo il 2021 si usano solo le anagrafiche del 1o trimestre di ogni anno e del 3o 2026 (file da 100 MB l'uno)
    if not os.path.exists(out):
        tgz = os.path.join(A, "anagrafica_%d_%d.tar.gz" % (y, q))
        fetch("https://opendatacarburanti.mise.gov.it/categorized/anagrafica_impianti_attivi/%d/%d_%d_tr.tar.gz" % (y, y, q), tgz)
        t = tarfile.open(tgz)
        mem = sorted([m for m in t.getmembers() if m.isfile()], key=lambda m: m.name)
        sel = [mem[0], mem[-1]] if len(mem) > 1 else mem
        rows = {}; hdr = None
        for m in sel:
            txt = dec(t.extractfile(m).read()).splitlines()
            # prima riga puo' essere "Estrazione del ..."
            k = 0
            while "impianto" not in txt[k].lower(): k += 1
            sep = "|" if txt[k].count("|") > 3 else ";"
            rd = csv.reader(txt[k:], delimiter=sep)
            h = next(rd); hdr = h
            hl = [x.strip().lower() for x in h]; ci, cp = hl.index("comune"), hl.index("provincia")
            for r in rd:
                if len(r) == len(h) and r[ci].strip().upper() == "MILANO" and r[cp].strip().upper() == "MI":
                    rows[r[0]] = [m.name.rsplit("-", 1)[-1][:8]] + r
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";"); w.writerow(["file_data"] + hdr)
            for r in rows.values(): w.writerow(r)
        t.close(); os.remove(tgz)
        print("anagrafica", y, q, len(rows), flush=True)
    for r in csv.reader(open(out, encoding="utf-8"), delimiter=";"):
        if r[1].strip().isdigit(): ids.add(r[1].strip())
print("impianti Milano (unione):", len(ids), flush=True)
# fase 2: prezzi
Y0, Y1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (2015, 2026)   # opzionale: intervallo di anni per la fase 2 (per lavorare in parallelo)
for y, q in quarters:
    if not (Y0 <= y <= Y1): continue
    out = os.path.join(M, "prezzi_milano_%d_%d.csv" % (y, q))
    if os.path.exists(out): continue
    tgz = os.path.join(A, "prezzo_%d_%d.tar.gz" % (y, q))
    fetch("https://opendatacarburanti.mise.gov.it/categorized/prezzo_alle_8/%d/%d_%d_tr.tar.gz" % (y, y, q), tgz)
    t = tarfile.open(tgz); n = 0
    with open(out + ".tmp", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";"); w.writerow(["file_data", "idImpianto", "descCarburante", "prezzo", "isSelf", "dtComu"])
        for m in sorted([m for m in t.getmembers() if m.isfile()], key=lambda m: m.name):
            d = re.search(r"(\d{8})", m.name).group(1)
            txt = dec(t.extractfile(m).read()).splitlines()
            k = 0
            while k < len(txt) and "impianto" not in txt[k].lower(): k += 1
            if k >= len(txt): print("file vuoto o senza intestazione:", m.name, flush=True); continue
            sep = "|" if txt[k].count("|") > 2 else ";"
            for r in csv.reader(txt[k + 1:], delimiter=sep):
                if len(r) >= 5 and r[0] in ids: w.writerow([d] + r[:5]); n += 1
    t.close(); os.remove(tgz); os.replace(out + ".tmp", out)
    print("prezzi", y, q, n, flush=True)
print("FINE", flush=True)
