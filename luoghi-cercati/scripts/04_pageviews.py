"""Passo 4: visualizzazioni mensili da Wikimedia REST API (per-article, all-access, agent=user) per ogni (qid, lingua).
Da luglio 2015 (inizio dell'API) all'ultimo mese completo. Ogni risposta e' salvata in raw/pageviews_mensili/<lingua>/<qid>.json
(riprendibile: i file esistenti non si riscaricano). Limite proprio: 4 richieste/s in totale (10/s ricevevano 429), 8 thread, pausa globale su 429 (Retry-After).
Uso: python -I -X utf8 04_pageviews.py <luoghi-cercati assoluto> [fine AAAAMMGG00]
Fonte: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ (dati CC0)."""
import sys, os, json, csv, time, threading, urllib.parse, collections
import requests
from concurrent.futures import ThreadPoolExecutor

UA = "MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)"
base = sys.argv[1]
END = sys.argv[2] if len(sys.argv) > 2 else "2026103100"
START = "2015070100"
RATE = 4.0
lock = threading.Lock()
nxt = [time.time()]


def wait():
    with lock:
        t = max(time.time(), nxt[0])
        nxt[0] = t + 1.0 / RATE
    d = t - time.time()
    if d > 0:
        time.sleep(d)


tit = list(csv.DictReader(open(os.path.join(base, "pulito", "titoli_wikipedia.csv"), encoding="utf8"), delimiter=";"))
luoghi = {r["qid"]: r for r in csv.DictReader(open(os.path.join(base, "pulito", "luoghi.csv"), encoding="utf8"), delimiter=";")}
# priorita: lingue principali e luoghi con piu' edizioni per primi
main = ["it", "en", "de", "fr", "es", "zh", "ja", "ru", "pt", "ar"]
tit.sort(key=lambda r: (0 if r["lingua"] in main else 1, -int(luoghi[r["qid"]]["n_wikipedia"])))
sess = requests.Session()
sess.headers["User-Agent"] = UA
stats = collections.Counter()


def job(r):
    d = os.path.join(base, "raw", "pageviews_mensili", r["lingua"])
    f = os.path.join(d, r["qid"] + ".json")
    if os.path.exists(f):
        stats["cache"] += 1
        return
    os.makedirs(d, exist_ok=True)
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/%s.wikipedia/all-access/user/%s/monthly/%s/%s" % (
        r["lingua"], urllib.parse.quote(r["titolo"], safe=""), START, END)
    for k in range(40):
        wait()
        try:
            resp = sess.get(url, timeout=60)
        except Exception as e:
            time.sleep(5 * (k + 1))
            continue
        if resp.status_code in (200, 404):
            out = {"qid": r["qid"], "progetto": r["lingua"] + ".wikipedia", "titolo": r["titolo"], "http": resp.status_code,
                   "scaricato": time.strftime("%Y-%m-%d"), "inizio": START, "fine": END,
                   "items": resp.json().get("items", []) if resp.status_code == 200 else []}
            with open(f + ".tmp", "w", encoding="utf8") as fo:
                json.dump(out, fo, ensure_ascii=False)
            os.replace(f + ".tmp", f)
            stats[resp.status_code] += 1
            return
        stats["retry_%d" % resp.status_code] += 1
        if resp.status_code == 429:
            ra = float(resp.headers.get("retry-after", 15)) + 2
            with lock:
                nxt[0] = max(nxt[0], time.time() + ra)
        else:
            time.sleep(3 * (k + 1))
    stats["fallita"] += 1


t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    for i, _ in enumerate(ex.map(job, tit)):
        if i % 500 == 0:
            print(i, "/", len(tit), dict(stats), "%.0fs" % (time.time() - t0), flush=True)
print("fine", dict(stats), "%.0fs" % (time.time() - t0), flush=True)



