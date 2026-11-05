"""Scarica una lista di URL, uno alla volta, con User-Agent dichiarato e pausa.
Uso: python -I -X utf8 scarica.py <cartella raw> <lista.tsv> [pausa_secondi]
lista.tsv: sottocartella<TAB>file<TAB>url[<TAB>accept]. Salta i file gia' presenti. Registra in raw/download_log.csv."""
import sys, os, time, hashlib, urllib.request, urllib.parse
raw, lista = sys.argv[1], sys.argv[2]
pausa = int(sys.argv[3]) if len(sys.argv) > 3 else 20
UA = "milano-in-dati/1.0"
log = open(os.path.join(raw, "download_log.csv"), "a", encoding="utf-8")
for riga in open(lista, encoding="utf-8"):
    riga = riga.rstrip("\n")
    if not riga or riga.startswith("#"):
        continue
    p = riga.split("\t")
    sub, fn, url = p[0], p[1], p[2]
    acc = p[3] if len(p) > 3 else "*/*"
    d = os.path.join(raw, sub); os.makedirs(d, exist_ok=True)
    path = os.path.join(d, fn)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        print("gia' presente", sub, fn, flush=True); continue
    u = urllib.parse.quote(url, safe=":/?&=%,+.-_~")
    req = urllib.request.Request(u, headers={"User-Agent": UA, "Accept": acc})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=500)
        data = r.read()
        open(path, "wb").write(data)
        msg = f"OK,{sub}/{fn},{len(data)},{r.status},{r.headers.get('Content-Type')},{hashlib.sha256(data).hexdigest()},{time.strftime('%Y-%m-%d %H:%M:%S')},{url}"
    except Exception as e:
        msg = f"ERR,{sub}/{fn},0,{e!r},,,{time.strftime('%Y-%m-%d %H:%M:%S')},{url}"
    print(msg[:220], round(time.time() - t, 1), "s", flush=True)
    log.write(msg + "\n"); log.flush()
    time.sleep(pausa)
