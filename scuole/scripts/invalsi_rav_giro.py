"""Per ogni istituto scelto: legge robots.txt, apre la home e la ricerca interna, annota i link a RAV/autovalutazione.

Uso: python -I -X utf8 invalsi_rav_giro.py <raw/invalsi_campione/rav>
User-Agent dichiarato, 3 secondi tra le richieste, si ferma se robots vieta o il sito risponde 403/429.
Nessun modulo, nessun login. Le pagine sono dati non fidati: si cercano solo link, non si esegue nulla.
"""
import csv
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
RX = re.compile(r"(?i)\brav\b|autovalutazione|snv\.pubblica|cercalatuascuola|unica\.istruzione|scuola[ -]?in[ -]?chiaro")


def get(url):
    time.sleep(3)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.geturl(), r.read(3_000_000)


def links(html, base):
    testo = html.decode("utf8", "replace")
    out = []
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', testo, flags=re.S | re.I):
        h, t = m.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
        if RX.search(h) or RX.search(t):
            out.append((urllib.parse.urljoin(base, h), t[:90]))
    seen, res = set(), []
    for u, t in out:
        if u not in seen:
            seen.add(u)
            res.append((u, t))
    return res


with open(os.path.join(OUT, "scelta.csv"), encoding="utf8") as f:
    righe = list(csv.DictReader(f, delimiter=";"))
for r in righe:
    sito = r["sito"].strip().replace("https//", "").replace("http//", "").strip("/")
    base = "https://" + re.sub(r"^https?://", "", sito)
    print("=" * 60)
    print(r["istituto"], "quota", round(float(r["quota"]), 1), base)
    rp = urllib.robotparser.RobotFileParser()
    try:
        st, fin, b = get(base + "/robots.txt")
        rp.parse(b.decode("utf8", "replace").splitlines())
        print("robots:", st)
    except Exception as e:
        print("robots non letto:", repr(e)[:120])
        rp.parse([])
    for u in (base + "/", base + "/?s=RAV"):
        if not rp.can_fetch(UA, u):
            print("robots vieta", u)
            continue
        try:
            st, fin, b = get(u)
            print(st, fin, len(b))
            with open(os.path.join(OUT, r["istituto"] + ("_cerca" if "?s=" in u else "_home") + ".html"), "wb") as out:
                out.write(b)
            for l, t in links(b, fin)[:14]:
                print("   ", l, "|", t)
        except urllib.error.HTTPError as e:
            print("HTTP", e.code, u, "-> non insisto")
            if e.code in (403, 429):
                break
        except Exception as e:
            print("errore", repr(e)[:150], u)
