"""Scarica un URL in un file, con User-Agent dichiarato e pausa di cortesia.

Uso: python -I -X utf8 invalsi_get.py <url> <file di destinazione assoluto>
Non segue login, non invia dati. Stampa stato, tipo, dimensione e sha256.
Rifiuta di salvare se il server risponde con una pagina di login (segnala soltanto).
"""
import hashlib
import sys
import time
import urllib.request

UA = "milano-in-dati/1.0"


def main():
    url, dest = sys.argv[1], sys.argv[2]
    time.sleep(2)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = r.read()
        print("status", r.status, "| finale", r.geturl())
        print("tipo", r.headers.get("Content-Type"), "| disposition", r.headers.get("Content-Disposition"))
    with open(dest, "wb") as f:
        f.write(data)
    print("byte", len(data), "| sha256", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
