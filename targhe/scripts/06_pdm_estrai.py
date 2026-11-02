"""Estrae i CAMPI FATTUALI dalle schede di Pietre della Memoria (ANMIG, dati usati con autorizzazione dichiarata da Davide il 2/11/2026).
Si tengono: titolo, tipo, indirizzo, coordinate, luogo e data di collocazione, materiali (generico), ente preposto, testo dell'iscrizione (e' il testo inciso sulla targa), data della scheda.
NON si tengono: foto, biografie e testi di contestualizzazione scritti dai volontari, osservazioni personali.
Uso: python -I -X utf8 06_pdm_estrai.py <raw/pdm assoluto> <uscita csv assoluta>"""
import sys, re, csv, glob, html, os
raw, outp = sys.argv[1:3]
def clean(s):
    s = re.sub(r"<br\s*/?>", " / ", s); s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s); s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"( / )+", " / ", s).strip(" /")
    return s
rows = []
for f in sorted(glob.glob(os.path.join(raw, "schede", "*.html"))):
    t = open(f, encoding="utf8").read()
    h = re.findall(r"<h1[^>]*>(.*?)</h1>", t, flags=re.S)
    if len(h) < 2: continue
    tit = clean(h[1])
    m = re.match(r"(\d+) - (.*)", tit)
    pid, titolo = (m.group(1), m.group(2)) if m else ("", tit)
    d = {}
    for dt, dd in re.findall(r"<dt>([^<]*)</dt>\s*<dd[^>]*>(.*?)</dd>", t, flags=re.S): d.setdefault(dt.strip(" :"), clean(dd))
    tags = re.findall(r'rel="tag">([^<]+)</a>', re.search(r'post_tags">(.*?)</p>', t, flags=re.S).group(1)) if re.search(r'post_tags">', t) else []
    ds = re.search(r'<time datetime="([^"]+)"', t)
    data = d.get("Data di collocazione", "")
    ym = re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", data)
    def fl(x):
        try: return float(x.replace(",", "."))
        except: return None
    url = re.search(r'rel="canonical" href="([^"]+)"', t)
    rows.append(dict(id_pdm=pid, url=url.group(1) if url else "", titolo=titolo, tags=" | ".join(tags), indirizzo=d.get("Indirizzo", ""), cap=d.get("CAP", ""), lat=fl(d.get("Latitudine", "")), lon=fl(d.get("Longitudine", "")),
                     luogo_collocazione=d.get("Luogo di collocazione", ""), data_collocazione=data, anno_collocazione=ym[0] if ym else "", materiali=d.get("Materiali (Generico)", ""),
                     ente=d.get("Ente preposto alla conservazione", ""), iscrizione=d.get("Iscrizioni", ""), data_scheda=ds.group(1)[:10] if ds else ""))
with open(outp, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "schede;", sum(1 for r in rows if r["lat"]), "con coordinate;", sum(1 for r in rows if r["anno_collocazione"]), "con anno di collocazione;", sum(1 for r in rows if r["iscrizione"]), "con iscrizione;", sum(1 for r in rows if r["ente"]), "con ente")
