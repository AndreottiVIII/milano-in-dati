"""Scarica un URL in un file. Uso: python -I -X utf8 scarica_url.py <url> <out> [accept] [timeout_s]"""
import sys, urllib.request, time, hashlib
url, out = sys.argv[1], sys.argv[2]
acc = sys.argv[3] if len(sys.argv) > 3 else "*/*"; to = int(sys.argv[4]) if len(sys.argv) > 4 else 300
req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati research (milano-in-dati)", "Accept": acc})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=to); d = r.read(); open(out, "wb").write(d)
    print(r.status, len(d), round(time.time()-t, 1), r.headers.get("Content-Type"), hashlib.sha256(d).hexdigest()[:16], url)
except Exception as e:
    print("ERR", e, round(time.time()-t, 1), url)
