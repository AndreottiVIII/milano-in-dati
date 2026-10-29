import sys, json, re
raw = sys.argv[1]
KW = re.compile(r"attentat|strage|omicid|assassin|ucciso|uccis|bomba|bombe|ordigno|esplosi|terror|agguato|eccidio|vittim|scontri|morto|morti|ferit|sparat|rapina|gambizz|esplos|dinamit", re.I)
CATKW = re.compile(r"Attentat|Strag|Omicid|Vittime|piombo|Terror|assassinat|Eccid|Brigate|Prima Linea|Esplosion", re.I)
MI = re.compile(r"\bMilan[oi]|milanes", re.I)
rows = []
for l in open(raw+"/info_pagine.jsonl", encoding="utf-8"):
    d = json.loads(l)
    if d["disamb"]: continue
    t = d["title"]; ex = d["extract"]
    inb = any(9.04 <= c["lon"] <= 9.28 and 45.38 <= c["lat"] <= 45.54 for c in d["coords"])
    mi = bool(MI.search(ex[:600])) or "Milano" in t or inb
    kw = bool(KW.search(ex[:600])) or any(CATKW.search(c) for c in d["cats"])
    cat = any(CATKW.search(c) for c in d["cats"])
    if mi and kw:
        yrs = [int(y) for y in re.findall(r"\b(1[89]\d\d|20[0-2]\d)\b", ex[:600])]
        rows.append((t, d["qid"], cat, inb, yrs[:3], ex[:170].replace("\n", " ")))
print(len(rows))
rows.sort(key=lambda r: (r[4][0] if r[4] else 0))
json.dump(rows, open(raw+"/candidati.json", "w", encoding="utf-8"), ensure_ascii=False)
for r in rows:
    if not r[4] or max(r[4]) >= 1900:
        print(r[0], "|", r[4], "|C" if r[2] else "|", "|", r[5][:120])
