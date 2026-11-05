"""Apre poche pagine indicate a mano e annota i link a documenti (pdf e simili). Controlla robots prima.

Uso: python -I -X utf8 invalsi_rav_pagine.py <cartella> <url1> [url2 ...]
"""
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = "milano-in-dati/1.0"
OUT = sys.argv[1]
CACHE = {}


def get(url):
    time.sleep(3)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.geturl(), r.headers.get("Content-Type"), r.read(40_000_000)


def permesso(url):
    p = urllib.parse.urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in CACHE:
        rp = urllib.robotparser.RobotFileParser()
        try:
            _, _, _, b = get(base + "/robots.txt")
            rp.parse(b.decode("utf8", "replace").splitlines())
            CACHE[base] = rp
            print("  [robots letto]", base)
        except urllib.error.HTTPError as e:
            print("  [robots HTTP", e.code, "]", base)
            CACHE[base] = None
        except Exception as e:
            print("  [robots non letto", repr(e)[:80], "]", base)
            CACHE[base] = None
    r = CACHE[base]
    return True if r is None else r.can_fetch(UA, url)


for u in sys.argv[2:]:
    print("=" * 60)
    print(u)
    if not permesso(u):
        print("  ROBOTS VIETA: non apro")
        continue
    try:
        st, fin, tipo, b = get(u)
    except urllib.error.HTTPError as e:
        print("  HTTP", e.code)
        continue
    except Exception as e:
        print("  errore", repr(e)[:150])
        continue
    print(" ", st, fin, tipo, len(b))
    nome = re.sub(r"[^A-Za-z0-9._-]", "_", urllib.parse.urlsplit(fin).netloc + urllib.parse.urlsplit(fin).path)[-120:]
    if tipo and "pdf" in tipo.lower():
        if not nome.lower().endswith(".pdf"):
            nome += ".pdf"
        open(os.path.join(OUT, nome), "wb").write(b)
        print("  salvato pdf", nome)
        continue
    open(os.path.join(OUT, nome + ".html"), "wb").write(b)
    t = b.decode("utf8", "replace")
    pagina = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    testo = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", pagina))
    i = testo.lower().find("autovalutazione")
    print("  testo:", testo[max(0, i - 200):i + 500] if i >= 0 else testo[:300])
    seen = set()
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', t, flags=re.S | re.I):
        h = urllib.parse.urljoin(fin, m.group(1))
        tx = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()[:90]
        if h in seen:
            continue
        if re.search(r"(?i)\.pdf|\brav\b|autovaluta|snv\.|valutazione|documenti/", h + " " + tx):
            seen.add(h)
            print("   ", h, "|", tx)
