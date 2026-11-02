"""Scarica i file "Procedure di rilascio di immobili ad uso abitativo" (INT 00004) dal sito dell'Ufficio centrale di statistica
del Ministero dell'Interno (ucs.interno.gov.it) in sfratti/raw/ministero_interno/.

Uso: python -I -X utf8 scarica.py <sfratti_dir>
Rilanciabile: salta i file gia' scaricati. Un file alla volta, pausa di 2 secondi, user agent onesto (nessuna imitazione di browser),
nessun aggiramento. I file scaricati sono dati non fidati: vengono solo letti come tabelle/testo, mai eseguiti.
Scrive anche raw/download_log.csv (data, url, byte, sha256).
"""
import sys, os, re, time, hashlib, csv, datetime, subprocess, urllib.request, urllib.parse

BASE = sys.argv[1]
OUT = os.path.join(BASE, "raw", "ministero_interno")
os.makedirs(OUT, exist_ok=True)
UA = "milano-in-dati/1.0 (ricerca open data; contatto: davide.caniatti@gmail.com)"
ROOT = "https://ucs.interno.gov.it"
PAGINA = ROOT + "/it/le-statistiche/le-indagini/territorio/procedure-di-rilascio-di-immobili-ad-uso-abitativo"

def get(url):
    rq = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(rq, timeout=90) as r:
        return r.read()

pag = get(PAGINA).decode("utf8", "replace").replace("\\/", "/")
open(os.path.join(BASE, "raw", "pagina_indagine_INT00004.html"), "w", encoding="utf8").write(pag)
links = sorted(set(re.findall(r"""["'(]([^"'()\s]*sites/default/files/[^"'()\s]*\.(?:xlsx|xls|csv|pdf))""", pag)))
print(len(links), "file elencati nella pagina")

logp = os.path.join(BASE, "raw", "download_log.csv")
nuovo = not os.path.exists(logp)
log = open(logp, "a", newline="", encoding="utf8")
w = csv.writer(log)
if nuovo:
    w.writerow(["data", "url", "file", "byte", "sha256"])
for l in links:
    nome = urllib.parse.unquote(l.split("/")[-1])
    dest = os.path.join(OUT, nome)
    if os.path.exists(dest):
        continue
    url = ROOT + l
    # curl con tetto di tempo (urllib poteva restare appeso); il file va in un nome temporaneo e si controlla la dimensione
    tmp = dest + ".part"
    rc = subprocess.run(["curl", "-sS", "-L", "--max-time", "120", "-A", UA, "-o", tmp, "-w", "%{http_code} %{size_download}", url],
                        capture_output=True, text=True)
    info = rc.stdout.strip().split()
    if rc.returncode != 0 or not info or info[0] != "200":
        print("ERRORE", url, rc.returncode, rc.stdout, rc.stderr[:200])
        if os.path.exists(tmp):
            os.remove(tmp)
        continue
    b = open(tmp, "rb").read()
    os.replace(tmp, dest)
    w.writerow([datetime.date.today().isoformat(), url, nome, len(b), hashlib.sha256(b).hexdigest()])
    log.flush()
    print("ok", nome, len(b))
    time.sleep(2)
log.close()
