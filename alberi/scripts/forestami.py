"""Raccoglie dalle pagine pubbliche delle piantagioni Forestami: nome, anno, numero di piante. Uso: python -I -X utf8 forestami.py <raw_dir> <pulito_dir>"""
import sys, os, re, html, time, urllib.request, csv
raw, pul = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(raw, "forestami"), exist_ok=True)
sm = open(os.path.join(raw, "web_probe", "piant_sitemap.xml"), encoding="utf-8").read()
urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if "/piantagione/" in u and "/en/" not in u]
rows = []
for u in urls:
    fn = os.path.join(raw, "forestami", re.sub(r"[^a-z0-9]+", "_", u.lower()) + ".html")
    if not os.path.exists(fn):
        h = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=40).read().decode("utf-8", "replace")
        open(fn, "w", encoding="utf-8").write(h); time.sleep(0.7)
    h = open(fn, encoding="utf-8").read()
    x = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
    x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", x)))
    m = re.search(r"PIANTAGIONI (.+?) Anno di realizzazione (.+?) Numero di piante ([\d\.]+)", x)
    if m:
        rows.append({"url": u, "nome": m.group(1).strip(), "stagione_anno": m.group(2).strip(), "numero_piante": int(m.group(3).replace(".", ""))})
    else:
        rows.append({"url": u, "nome": "", "stagione_anno": "", "numero_piante": ""})
with open(os.path.join(pul, "forestami_piantagioni.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["url", "nome", "stagione_anno", "numero_piante"], delimiter=";"); w.writeheader(); w.writerows(rows)
tot = sum(r["numero_piante"] for r in rows if r["numero_piante"] != "")
mil = [r for r in rows if r["nome"].startswith("Milano")]
print(len(rows), "pagine; con numero:", sum(1 for r in rows if r["numero_piante"] != ""), "tot piante", tot)
print("Milano:", [(r["nome"], r["stagione_anno"], r["numero_piante"]) for r in mil], "somma", sum(r["numero_piante"] for r in mil if r["numero_piante"] != ""))
