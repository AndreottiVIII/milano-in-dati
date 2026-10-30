"""Parse RSSSF season pages: derby matches from per-match lists (1929/30 on) and from results matrices (1925-29).
Usage: python -I 09_parse_rsssf.py <derby_dir>"""
import sys, re, csv, glob, os
base = sys.argv[1]
MON = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
def isMilan(t): return re.fullmatch(r"(ac )?milan(o)?( fc)?", t.strip().lower()) is not None
def isInter(t): return re.fullmatch(r"(fc )?inter(nazionale)?( fc)?|ambrosiana(-inter)?", t.strip().lower()) is not None
rows = []
for f in sorted(glob.glob(base + "/raw/rsssf/ital*.html")):
    name = os.path.basename(f)[:-5]
    if name in ("italchamp", "italcuphist", "italhist98-25"): continue
    txt = open(f, encoding="latin-1").read()
    txt = re.sub(r"<[^>]+>", "", txt)
    cur = None
    lines = txt.split("\n")
    # per-match lists
    ym = re.match(r"ital(\d{2,4})$", name)
    yend = (int(ym.group(1)) if len(ym.group(1)) == 4 else (2000 + int(ym.group(1)) if int(ym.group(1)) < 26 else 1900 + int(ym.group(1)))) if ym else None
    EN = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
    for li, ln in enumerate(lines):
        ln = re.sub(r"^\d{1,2}-(?=[A-Za-z])", "", ln)
        me = re.match(r"\s*\[([A-Z][a-z]{2}) (\d{1,2})\]\s*$", ln)
        if me and yend and me.group(1) in EN:
            mo = EN[me.group(1)]; cur = "%d-%02d-%02d" % (yend - 1 if mo >= 7 else yend, mo, int(me.group(2))); continue
        mr = re.search(r"round[^\[]*\[([A-Z][a-z]+) (\d{1,2})(?:, (\d{4}))?", ln)
        if mr and yend:
            mo = EN.get(mr.group(1)[:3])
            if mo:
                cur = "%s-%02d-%02d" % (mr.group(3) or (yend - 1 if mo >= 7 else yend), mo, int(mr.group(2)))
            continue
        m3 = re.match(r"^\s*(Milan|Internazionale)\s+(\d+) - (\d+)\s+(Internazionale|Milan)\s*$", ln)
        if m3 and m3.group(1) != m3.group(4):
            sc = lines[li + 1].strip() if li + 1 < len(lines) and lines[li + 1].startswith("[") else ""
            rows.append(dict(page=name, kind="list3", date=cur, home=m3.group(1).replace("Internazionale", "Inter"), away=m3.group(4).replace("Internazionale", "Inter"), hg=m3.group(2), ag=m3.group(3), scorers=sc, raw=ln.strip())); continue
        mn = re.match(r"^\s*(Milan|Inter|Internazionale)\s+(\d+)-(\d+)\s+(Internazionale|Inter|Milan)", ln)
        if mn and mn.group(1).replace('Internazionale','Inter') != mn.group(4).replace('Internazionale','Inter'):
            sc = ""; k = li + 1
            while k < len(lines) and lines[k].startswith("  ") and ("[" in lines[k] or sc):
                sc += " " + lines[k].strip()
                if "]" in lines[k]: break
                k += 1
            rows.append(dict(page=name, kind="list2", date=cur, home=mn.group(1).replace("Internazionale", "Inter"), away=mn.group(4).replace("Internazionale", "Inter"), hg=mn.group(2), ag=mn.group(3), scorers=sc.strip(), raw=ln.strip())); continue
        m = re.match(r"\s*\d+\s*a?\s*GIORNATA\s+(\d{1,2})[\s\-]+([A-Za-z]{3})[a-z]*\.?[\s\-]+(\d{4})", ln, re.I)
        if m and m.group(2).lower() in MON:
            cur = "%s-%02d-%02d" % (m.group(3), MON[m.group(2).lower()], int(m.group(1))); continue
        m = re.match(r"^(\S.*?)\s*-\s*(\S.*?)\s+(\d+)-(\d+)\s*(.*)$", ln)
        if m:
            m = re.match(r"^(\S.*?)\s*-\s*(\S.*?)\s+(\d+)-(\d+)\s*(.*)$", re.sub(r"\s*\(\d\)(?=\s)", "", ln, count=2))
        if m and ((isMilan(m.group(1)) and isInter(m.group(2))) or (isInter(m.group(1)) and isMilan(m.group(2)))):
            h, a = ("Milan" if isMilan(m.group(1)) else "Inter"), ("Milan" if isMilan(m.group(2)) else "Inter")
            sc = m.group(5).strip(); k = li + 1
            while k < len(lines) and re.match(r"^\s{8,}\S", lines[k]) and not lines[k].strip().startswith("Classifica"):
                sc += " " + lines[k].strip(); k += 1
            rows.append(dict(page=name, kind="list", date=cur, home=h, away=a, hg=m.group(3), ag=m.group(4), scorers=sc, raw=ln.strip()))
    # matrices
    block = []
    for ln in lines + [""]:
        m = re.match(r"^\s*(\d+)\s+([A-Z][A-Za-z .'\-]+?)\s{2,}((?:\d+-\d+|-)(?:\s+(?:\d+-\d+|-))*)\s*$", ln) or re.match(r"^\s*(\d+)\s+([A-Z][A-Za-z .'\-]+?)\s+((?:\d+-\d+|-)(?:\s+(?:\d+-\d+|-)){3,})\s*$", ln)
        if m:
            block.append((int(m.group(1)), m.group(2).strip(), m.group(3).split()))
        else:
            if block:
                mi = [b for b in block if isMilan(b[1])]; ii = [b for b in block if isInter(b[1])]
                if mi and ii:
                    M, I = mi[0], ii[0]
                    for (A, B, an, bn) in ((M, I, "Milan", "Inter"), (I, M, "Inter", "Milan")):
                        tok = A[2][B[0] - 1] if B[0] - 1 < len(A[2]) else None
                        if tok and tok != "-":
                            hg, ag = tok.split("-")
                            rows.append(dict(page=name, kind="matrix", date="", home=an, away=bn, hg=hg, ag=ag, scorers="", raw="%s row %s col %s" % (A[1], A[0], B[0])))
                block = []
with open(base + "/pulito/_src_rsssf.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
