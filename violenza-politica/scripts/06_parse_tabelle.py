import sys, json, re
raw = sys.argv[1]
L = json.load(open(raw+"/liste_piombo.json", encoding="utf-8"))
def clean(s):
    s = re.sub(r"<ref[^>]*/>", "", s); s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", s); s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'''?", "", s); s = re.sub(r"<br\s*/?>", "; ", s)
    return re.sub(r"\s+", " ", s).strip()
def firstlink(s):
    m = re.search(r"\[\[([^\]|#]*)", s); return m.group(1) if m else ""
rows = []
for t, v in L.items():
    if not t.startswith("Persone uccise"): continue
    y = int(re.search(r"\((\d{4})\)", t).group(1))
    for blk in v["text"].split("\n|-")[1:]:
        cells = [c for c in re.split(r"\n\|(?!\|)", "\n" + blk.strip().lstrip("|").strip()) if c.strip()]
        txt = blk.strip().lstrip("|")
        parts = [p for p in re.split(r"\|\|", txt.replace("\n|", "||"))]
        parts = [p.strip() for p in parts if p.strip() != ""]
        if len(parts) < 5: continue
        data, nome, loc, resp, vitt = parts[:5]; note = parts[5] if len(parts) > 5 else ""
        rows.append({"anno_lista": y, "data": clean(data), "nome": clean(nome), "link_nome": firstlink(nome), "luogo_raw": clean(loc), "luogo_link": firstlink(loc),
            "responsabili": clean(resp), "vittime": clean(vitt), "note": clean(note)[:400], "fonte_lista": t, "revid": v["revid"], "ts": v["ts"]})
print(len(rows))
mil = [r for r in rows if re.search(r"Milano", r["luogo_raw"] + r["luogo_link"])]
print(len(mil))
json.dump(rows, open(raw+"/piombo_righe_tutte.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(mil, open(raw+"/piombo_righe_milano.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for r in mil: print(r["anno_lista"], r["data"], "|", r["nome"], "|", r["luogo_raw"], "|", r["responsabili"][:70], "|", r["vittime"][:90])
