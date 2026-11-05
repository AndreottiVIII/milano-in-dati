"""Scarica un URL in un file (solo standard library). Uso: python -I -X utf8 scarica.py <url> <file_assoluto> [accept] [timeout_s]
Scrive anche una riga in raw/download_log.csv (nella stessa radice costo-vita/raw)."""
import sys, os, urllib.request, time, datetime, hashlib
url, out = sys.argv[1], sys.argv[2]
acc = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "*/*"
to = int(sys.argv[4]) if len(sys.argv) > 4 else 600
os.makedirs(os.path.dirname(out), exist_ok=True)
req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0", "Accept": acc})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=to)
    data = r.read()
    open(out, "wb").write(data)
    msg = "%s;%s;%s;%d;%s;%s" % (datetime.date.today(), r.status, url, len(data), hashlib.sha256(data).hexdigest()[:16], out)
    print(msg, round(time.time() - t, 1), "s", r.headers.get("Content-Type"))
except Exception as e:
    msg = "%s;ERR %s;%s;0;;%s" % (datetime.date.today(), str(e)[:80], url, out)
    print(msg, round(time.time() - t, 1), "s")
raw = out.split("costo-vita")[0] + "costo-vita/raw"
with open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8") as f:
    f.write(msg + "\n")
