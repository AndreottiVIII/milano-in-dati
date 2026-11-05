"""Scarica i dati aperti INVALSI (Servizio statistico, CC BY) che non sono microdati:
punteggi per territorio e per gestione (statale, paritaria) e dati sotto i rapporti.
Legge le pagine del catalogo salvate e poi la pagina di ogni dataset. Nessun login.
Uso: python -I -X utf8 invalsi_aperti_scarica.py <cartella catalogo> <cartella di uscita>
"""
import glob, hashlib, html, os, re, sys, time, urllib.request, urllib.parse

UA = {"User-Agent": "milano-in-dati/1.0"}
CAT, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)


def get(url, t=120):
    time.sleep(3)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
        return r.read(), r.geturl(), r.headers.get("Content-Type", ""), r.headers.get("Content-Disposition", "")


pagine = {}
for p in glob.glob(os.path.join(CAT, "open*.html")):
    t = open(p, encoding="utf-8", errors="replace").read()
    for m in re.finditer(r'href="(https://serviziostatistico\.invalsi\.it/invalsi_ss_data/[^"#?]+)"[^>]*>\s*([^<]{8,160})', t):
        if not m.group(2).strip().startswith("Microdati"):
            pagine[m.group(1)] = html.unescape(m.group(2)).strip()
TIENI = re.compile(r"(?i)sistemi-locali|punteggi-e-perce|dati-regionali|eccellenza|2024-2025|2025-2026|2023-2024")
sel = {u: n for u, n in pagine.items() if TIENI.search(u) or TIENI.search(n)}
print("pagine del catalogo", len(pagine), "scelte", len(sel), flush=True)
log = open(os.path.join(OUT, "_log.txt"), "a", encoding="utf-8")
for u, n in sorted(sel.items()):
    try:
        corpo, *_ = get(u, 60)
    except Exception as e:
        print("ERRORE pagina", u, e, flush=True)
        continue
    t = corpo.decode("utf-8", "replace")
    if os.path.basename(u.rstrip("/")):
        open(os.path.join(OUT, "_pag_" + os.path.basename(u.rstrip("/"))[:80] + ".html"), "w", encoding="utf-8").write(t)
    link = set(html.unescape(x) for x in re.findall(r'href="(https://serviziostatistico\.invalsi\.it/download/[^"]+)"', t))
    print(n[:70], "| file", len(link), flush=True)
    for l in sorted(link):
        nome = urllib.parse.unquote(l.rstrip("/").split("/")[-1])[:120] or "file"
        dest = os.path.join(OUT, nome)
        if os.path.exists(dest):
            continue
        try:
            d, fin, tipo, disp = get(l, 300)
        except Exception as e:
            print("  ERRORE", nome, e, flush=True)
            continue
        if "login" in fin.lower() or (b"<html" in d[:400].lower() and "html" in tipo):
            print("  salto, non e un file:", nome, tipo, flush=True)
            continue
        m = re.search(r'filename="?([^";]+)', disp or "")
        if m:
            dest = os.path.join(OUT, os.path.basename(m.group(1)))
        open(dest, "wb").write(d)
        print("  ", os.path.basename(dest), len(d), flush=True)
        log.write(f"{l}\t{os.path.basename(dest)}\t{len(d)}\t{hashlib.sha256(d).hexdigest()}\n")
        log.flush()
print("FINE", flush=True)
