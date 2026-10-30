"""Extract Milan-Inter 'Incontro di club' boxes (and simple table lines for early seasons) from fetched it.wiki season pages.
Usage: python -I 08_season_boxes.py <derby_dir>"""
import sys, re, csv, glob, os
base = sys.argv[1]
MESI = {m: i for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}
def clean(s):
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\{\{Goal\|([^}]*)\}\}", lambda m: " ".join(x + "'" for x in m.group(1).split("|") if x), s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    return re.sub(r"\s+", " ", s).strip()
def team(s):
    s = clean(s).lower()
    if "milanese" in s: return None
    if re.fullmatch(r"(ac |us )?milan(o)?( .*)?", s) and "internaz" not in s: return "Milan"
    if "inter" in s or "ambrosiana" in s: return "Inter"
    return None
rows = []
for f in sorted(glob.glob(base + "/raw/wikipedia/seasons/*.wiki")):
    t = open(f, encoding="utf-8").read()
    # split blocks of {{Incontro di club ... }} by brace counting
    i = 0
    while True:
        i = t.find("{{Incontro di", i)
        if i < 0: break
        depth, j = 0, i
        while j < len(t):
            if t.startswith("{{", j): depth += 1; j += 2
            elif t.startswith("}}", j): depth -= 1; j += 2; 
            else: j += 1
            if depth == 0: break
        blk = t[i:j]; i = j
        p = {}
        for m in re.finditer(r"^\s*\|\s*([^=|\n]+?)\s*=\s*(.*?)(?=^\s*\|\s*[^=|\n]+?\s*=|\Z)", blk, re.S | re.M):
            p[m.group(1).strip()] = m.group(2).strip()
        t1, t2 = team(p.get("Squadra 1", "")), team(p.get("Squadra 2", ""))
        if {t1, t2} != {"Milan", "Inter"}: continue
        gm = clean(p.get("Giornomese", "")).split()
        date = ""
        if len(gm) >= 2 and gm[1] in MESI and p.get("Anno", "").strip().isdigit():
            date = "%s-%02d-%02d" % (p["Anno"].strip(), MESI[gm[1]], int(re.sub(r"\D", "", gm[0])))
        rows.append(dict(page=os.path.basename(f)[:-5], date=date, round=clean(p.get("Turno", "")), venue=clean(p.get("Stadio", "")), city=clean(p.get("Città", "")),
                         home=t1, away=t2, hg=clean(p.get("Punteggio 1", "")), ag=clean(p.get("Punteggio 2", "")),
                         scorers_home=clean(p.get("Marcatori 1", "")), scorers_away=clean(p.get("Marcatori 2", "")), referee=clean(p.get("Arbitro", "")),
                         extra=clean(p.get("Note", "") or p.get("Rigori 1", "")), raw=re.sub(r"\s+", " ", blk)[:0]))
with open(base + "/pulito/_src_wikiseasons.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
