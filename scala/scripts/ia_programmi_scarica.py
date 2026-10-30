"""Internet Archive: scarica i programmi di sala Teatro alla Scala 2002-2011 APERTI (testo OCR sempre; PDF solo se <= 12 MB). 3 s tra richieste, riprendibile.
Uso (dalla cartella scala/): python -I -X utf8 scripts/ia_programmi_scarica.py"""
import sys, os, json, re, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "raw", "ia_programmi"); os.makedirs(OUT, exist_ok=True)
UA = "milano-in-dati research project (davide.caniatti@gmail.com; programmi di sala aperti, 1 richiesta ogni 3 s)"
last = [0.0]
def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0: return False
    w = 3 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as f: data = f.read()
    open(dest, "wb").write(data); return True
tutti = json.load(open(os.path.join(OUT, "tutti.json"), encoding="utf8"))
ids = sorted(k for k, x in tutti.items() if k.startswith("teatro-alla-scala-") and not x.get("access-restricted-item"))
print("elementi:", len(ids), flush=True)
for ident in ids:
    d = os.path.join(OUT, ident); os.makedirs(d, exist_ok=True)
    try:
        fetch("https://archive.org/metadata/" + ident, os.path.join(d, "metadata.json"))
        m = json.load(open(os.path.join(d, "metadata.json"), encoding="utf8"))
        files = m.get("files", [])
        txt = [f for f in files if f["name"].endswith("_djvu.txt")]
        pdf = [f for f in files if f["name"].lower().endswith(".pdf") and f.get("source") == "original"] or [f for f in files if f["name"].lower().endswith(".pdf")]
        if txt: fetch("https://archive.org/download/%s/%s" % (ident, urllib.request.quote(txt[0]["name"])), os.path.join(d, "testo.txt"))
        if pdf and int(pdf[0].get("size", 0)) <= 12 * 1048576:
            fetch("https://archive.org/download/%s/%s" % (ident, urllib.request.quote(pdf[0]["name"])), os.path.join(d, "programma.pdf"))
        print("ok", ident[:70], "testo" if txt else "NO TESTO", "pdf %.1f MB" % (int(pdf[0]["size"]) / 1048576) if pdf else "", flush=True)
    except Exception as e:
        print("ERR", ident, e, flush=True)
print("FINE", flush=True)
