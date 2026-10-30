"""Parse archived interfc.it match pages -> pulito/_src_interfc.csv. Usage: python -I 12_parse_interfc.py <derby_dir>"""
import sys, re, csv, glob, os, html
base = sys.argv[1]
rows = []
for f in sorted(glob.glob(base + "/raw/interfc_archive/D*.html")):
    mid = os.path.basename(f)[:-5]
    t = open(f, encoding="latin-1").read()
    t = re.sub(r"<script.*?</script>", " ", t, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t)).replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t)
    i = t.find("PARTITE UFFICIALI")
    seg = t[i:i + 900] if i >= 0 else t[:900]
    d = re.search(r"Data: (\d\d)\.(\d\d)\.(\d{4})", seg)
    m = re.search(r"vs (.+?) (\d+)-(\d+)(?: \((.*?)\))? Reti:|vs (.+?) (\d+)-(\d+)(?: \((.*?)\))? (?:Arbitro|Allenatore)", seg)
    title = None
    if m:
        g = [x for x in m.groups()]
        title, hg, ag, extra = (g[0], g[1], g[2], g[3]) if g[0] else (g[4], g[5], g[6], g[7])
    if not title:
        m2 = re.search(r"((?:Milano?|Inter|Ambrosiana(?:-Inter)?)-(?:Milano?|Inter|Ambrosiana(?:-Inter)?)) (\d+)-(\d+)(?: \((.*?)\))? (?:Reti|Arbitro|Allenatore)", seg)
        if m2: title, hg, ag, extra = m2.group(1), m2.group(2), m2.group(3), m2.group(4)
    reti = re.search(r"Reti: (.*?) (?:Arbitro|Allenatore|Presidente)", seg)
    arb = re.search(r"Arbitro: (.*?) (?:Allenatore|Presidente|I risultati)", seg)
    home = ""
    if title:
        tl = title.strip().lower()
        home = "Milan" if tl.startswith("milan") else ("Inter" if (tl.startswith("inter") or tl.startswith("ambrosiana")) else "?")
    rows.append(dict(match_id=mid, date="%s-%s-%s" % (d.group(3), d.group(2), d.group(1)) if d else "", title=title or "", home=home, hg=hg if title else "", ag=ag if title else "",
                     scorers=reti.group(1).strip() if reti else "", referee=arb.group(1).strip() if arb else "", extra=extra if title and extra else "", seg=seg[:300] if not title else ""))
with open(base + "/pulito/_src_interfc.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "pages;", sum(1 for r in rows if not r["title"]), "unparsed")
