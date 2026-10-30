"""Parse the 'Official match results' tables of en.wikipedia 'Derby della Madonnina'.
Usage: python -I 02_parse_enwiki.py <wikitext> <out.csv>"""
import sys, re, csv, datetime

def clean(s):
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s.replace("&nbsp;", " ")).strip()

def main(src, out):
    lines = open(src, encoding="utf-8").read().split("\n")
    a = next(i for i, l in enumerate(lines) if l.startswith("== Official match results"))
    b = next(i for i, l in enumerate(lines) if l.startswith("== Statistics"))
    seg = "\n".join(lines[a:b])
    rows = seg.split("\n|-")
    active = {}
    res = []
    for r in rows[1:]:
        cells = [l[1:] for l in r.strip().split("\n") if l.startswith("|") and not l.startswith("|}") and not l.startswith("|-")]
        cells = [x for c in cells for x in c.split("||")]
        if len(cells) < 3:
            continue
        if len(cells) >= 6 and not cells[0].lstrip().startswith("rowspan") is False or len(cells) >= 6:
            active.clear()
        vals, ci = [], 0
        for col in range(6):
            if col in active and active[col][0] > 0:
                active[col][0] -= 1; vals.append(active[col][1]); continue
            if ci >= len(cells):
                vals.append(""); continue
            c = cells[ci]; ci += 1
            m = re.match(r"\s*rowspan\s*=\s*(\d+)\s*\|(.*)", c, re.S)
            if m:
                c = m.group(2); active[col] = [int(m.group(1)) - 1, c]
            vals.append(c)
        season, comp, date, home, score, away = vals
        d = clean(date)
        iso = ""
        for fmt in ("%d %B %Y", "%B %d, %Y"):
            try:
                iso = datetime.datetime.strptime(d, fmt).strftime("%Y-%m-%d"); break
            except ValueError:
                pass
        notes = re.findall(r"\{\{efn\|(.*?)(?:<ref|\}\})", " ".join(cells), re.S)
        note = " / ".join(clean(n) for n in notes)
        sc = re.search(r"(\d+)\s*[–-]\s*(\d+)", re.sub(r"style=\"[^\"]*\"", "", score).replace("&ndash;","–"))
        res.append(dict(season=clean(season), competition=clean(comp), date_text=d, date=iso, home=clean(home), away=clean(away),
                        home_goals=sc.group(1) if sc else "", away_goals=sc.group(2) if sc else "", score_raw=clean(score), note=note, raw_row=" | ".join(cells)[:300]))
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
    print(len(res), "rows")

main(*sys.argv[1:3])
