"""Estrae i campi strutturati dalle schede del Comitato (raw/biografie/N.html) e le coordinate dalla mappa (raw/web/la-mappa-delle-pietre.html).
Si tengono solo i campi (fatti), NON i testi biografici. Uso: python -I -X utf8 parse_biografie.py <raw_dir> <pulito_dir>"""
import sys, os, re, html, csv, json
raw, pul = sys.argv[1], sys.argv[2]
mp = open(os.path.join(raw, "web", "la-mappa-delle-pietre.html"), encoding="utf-8").read()
pts = {int(i): (float(lon), float(lat), html.unescape(n)) for lon, lat, i, n in re.findall(r"fromLonLat\(\[([\d.]+), ([\d.]+)\]\)\),\s*html: \"<a href='[^']*ricerca=(\d+)'[^>]*>([^<]*)</a>", mp)}
def text(fn):
    t = open(fn, encoding="utf-8").read()
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", t, flags=re.S)
    t = t[t.find('id="main-content"'):]
    t = re.sub(r"<[^>]+>", "\n", t); t = html.unescape(re.sub(r"[ \t\xa0]+", " ", t))
    return [l.strip() for l in t.split("\n") if l.strip()]
rows = []; vocab = {}
for i in sorted(pts):
    fn = os.path.join(raw, "biografie", f"{i}.html")
    L = text(fn)
    try: k = next(j for j, l in enumerate(L) if l.startswith("Pietra in") or l.startswith("Pietra a") or l.startswith("Pietra di"))
    except StopIteration: k = 30
    H = L[1:k + 3]
    r = {"id_scheda": i, "titolo": L[0], "lon": pts[i][0], "lat": pts[i][1], "nome_mappa": pts[i][2], "campi_raw": " | ".join(H)}
    for l in H:
        m = re.match(r"(Nat[oa]|Arrestat[oa]|Mort[oa]|Ucciso|Uccisa|Deportat[oa]|Liberat[oa]|Sopravvissut[oa]|Fucilat[oa]|Fuggit[oa]|Rilasciat[oa]|Rientrat[oa]|Motivo dell'arresto|Anno di posa della pietra|Detenzione|Deportazione|Trasporto|Pietra in|Pietra a|Pietra di|Richiesta da|Richiesta dal|Richiesta dalla|Richiesta dai)\b\s*:?\s*(.*)", l)
        if m:
            key = m.group(1); vocab[key] = vocab.get(key, 0) + 1
            r.setdefault("f_" + key, m.group(2))
    corpo = " ".join(L[k + 1:]).split(" x Home Chi siamo")[0].lower()
    r["bio_scioper"] = int("scioper" in corpo)
    r["bio_cibeno"] = int("cibeno" in corpo)
    r["bio_lunghezza"] = len(corpo)
    r["bio_gusen"] = int("gusen" in corpo)
    rows.append(r)
keys = sorted({k for r in rows for k in r})
with open(os.path.join(pul, "comitato_schede.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys, delimiter=";"); w.writeheader(); w.writerows(rows)
print(len(rows), "schede"); print(vocab)
