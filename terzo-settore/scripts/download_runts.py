"""Scarica le liste pubbliche del RUNTS (servizi.lavoro.gov.it/runts/it-it/Lista-enti).

La pagina e' pubblica, senza login: ogni riga ha un pulsante "Scarica" (modulo ASP.NET, invio del modulo).
Qui si fa la stessa cosa che fa il pulsante: GET della pagina, poi POST del modulo con il pulsante scelto.
Nessun trucco: stesso indirizzo, user-agent dichiarato, nessun aggiramento di blocchi.
Uso: python -I -X utf8 download_runts.py <cartella_raw_runts_assoluta> [indici separati da virgola, default 1,6]
 indici: 0 iscritti senza provvedimento, 1 iscritti, 2 cancellati, 3 cancellati xls, 4 diniegati, 5 iscritti trasmigrazione, 6 iscritti xls
"""
import sys, os, re, hashlib, datetime, csv
import requests
from html import unescape

OUT = sys.argv[1]
IDX = [int(x) for x in (sys.argv[2] if len(sys.argv) > 2 else "1,6").split(",")]
URL = "https://servizi.lavoro.gov.it/runts/it-it/Lista-enti"
UA = "milano-in-dati-research/1.0 (dati pubblici; lettura unica)"
os.makedirs(OUT, exist_ok=True)
s = requests.Session(); s.headers["User-Agent"] = UA
r = s.get(URL, timeout=60); r.raise_for_status()
h = r.text
campi = dict(re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', h))
bottoni = re.findall(r'<input type="submit" name="([^"]+btnScaricaDoc)" value="Scarica"', h)
titoli = [unescape(t) for t in re.findall(r"<tr>\s*<td>([^<]+)</td><td>", h)]
print(len(bottoni), "pulsanti:", titoli)
log = []
for i in IDX:
    dati = {k: unescape(v) for k, v in campi.items()}
    dati[bottoni[i]] = "Scarica"
    rr = s.post(URL, data=dati, timeout=600)
    cd = rr.headers.get("Content-Disposition", ""); ct = rr.headers.get("Content-Type", "")
    nome = re.findall(r'filename="?([^";]+)', cd)
    nome = nome[0] if nome else f"lista_{i}.bin"
    quando = datetime.date.today().isoformat()
    p = os.path.join(OUT, f"{quando}_{nome}")
    open(p, "wb").write(rr.content)
    sha = hashlib.sha256(rr.content).hexdigest()
    print(i, titoli[i], rr.status_code, ct, len(rr.content), p)
    log.append([quando, titoli[i], i, rr.status_code, ct, cd, len(rr.content), sha, p])
with open(os.path.join(OUT, "download_log.csv"), "a", newline="", encoding="utf8") as f:
    csv.writer(f).writerows(log)
