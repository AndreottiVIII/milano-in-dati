"""Scarica da infocamere.it/movimprese i file dati ANNUALI "Totale imprese" (tipo 2d) e le note.

Uso (percorsi assoluti, si puo' rilanciare: salta i file gia' presenti):
  python -I -X utf8 scarica_movimprese.py <imprese_dir> [anno_da anno_a]

Usa solo la pagina pubblica "Archivio Documenti" (form GET senza captcha) e i file .zip linkati.
NON usa il modulo "Scarica CSV" (protetto da reCAPTCHA): non si aggira.
Condizioni di utilizzo InfoCamere: uso e diffusione consentiti previa citazione della fonte.
Pause di 1,5 s tra le richieste, User-Agent dichiarato.
Scrive: raw/movimprese/<anno>_<periodo>_<tipo>.zip e raw/movimprese/download_log.csv
"""
import sys, os, re, time, csv, hashlib, datetime
import requests

BASE = "https://www.infocamere.it"
PAGE = BASE + "/principali-soluzioni/movimprese.html"
UA = "milano-in-dati research (dati aperti, uso divulgativo)"
D = sys.argv[1]
A0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1995
A1 = int(sys.argv[3]) if len(sys.argv) > 3 else 2025
OUT = os.path.join(D, "raw", "movimprese")
os.makedirs(OUT, exist_ok=True)
LOG = os.path.join(OUT, "download_log.csv")
s = requests.Session()
s.headers["User-Agent"] = UA

def get(url, **kw):
    for k in range(4):
        try:
            r = s.get(url, timeout=120, **kw)
            if r.status_code == 200:
                return r
            print("HTTP", r.status_code, url)
        except requests.RequestException as e:
            print("errore", e)
        time.sleep(5 * (k + 1))
    return None

done = {}
if os.path.exists(LOG):
    for r in csv.DictReader(open(LOG, encoding="utf8")):
        done[r["file"]] = r
logf = open(LOG, "a", newline="", encoding="utf8")
w = csv.writer(logf)
if not done:
    w.writerow(["file", "anno", "periodo", "tipo", "url", "bytes", "sha256", "data_download"])

jobs = [(a, "a", t) for a in range(A0, A1 + 1) for t in ("2d", "1n*")]
for anno, per, tipo in jobs:
    r = get(PAGE, params={"searchForDownload_anno": anno, "searchForDownload_periodo": per, "searchForDownload_tipo": tipo})
    time.sleep(1.5)
    if r is None:
        continue
    links = sorted(set(re.findall(r'href="(/dam/[^"]+\.(?:zip|pdf|xlsx?|docx?))"', r.text)))
    links = [l for l in links if re.search(r"/(\d{4})_[a1-4]_", l) or re.search(r"\d{4}", os.path.basename(l)) and "accessibilita" not in l and "Condizioni" not in l and "Glossario" not in l and "social" not in l]
    for l in links:
        name = os.path.basename(l)
        name = re.sub(r"\.\d{4}-\d\d-\d\d-\d\d-\d\d-\d\d(?=\.)", "", name)
        if name in done and os.path.exists(os.path.join(OUT, name)):
            continue
        rr = get(BASE + l)
        time.sleep(1.5)
        if rr is None:
            continue
        open(os.path.join(OUT, name), "wb").write(rr.content)
        w.writerow([name, anno, per, tipo, BASE + l, len(rr.content), hashlib.sha256(rr.content).hexdigest(),
                    datetime.date.today().isoformat()])
        logf.flush()
        print("scaricato", name, len(rr.content))
