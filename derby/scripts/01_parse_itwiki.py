"""Parse the big results table of it.wikipedia 'Derby di Milano' (saved wikitext).
Usage: python -I 01_parse_itwiki.py <wikitext> <out_matches.csv> <out_scorers.csv>
"""
import sys, re, csv

MESI = {m: i for i, m in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split(), 1)}


def strip_markup(s):
    s = re.sub(r"\{\{TA\|(.*)\}\}", r"\1", s.strip())          # no-wrap template
    return s.strip()


def link_text(s):
    """[[a|b]] -> b ; [[a]] -> a ; remove other markup"""
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    s = s.replace("'''", "").replace("''", "")
    return re.sub(r"\s+", " ", s).strip()


def parse_date(s):
    s = link_text(strip_markup(s))
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    m = re.match(r"(\d+)(?:º|°)?\s+([a-zà]+)\s+(\d{4})", s)
    if not m:
        return None
    return "%s-%02d-%02d" % (m.group(3), MESI[m.group(2)], int(m.group(1)))


def parse_scorers(cell):
    """returns list of dict(player, minute, extra, own_goal, penalty, n_goals, raw)"""
    cell = strip_markup(cell)
    out = []
    for part in re.split(r"<br\s*/?>", cell):
        raw = part.strip()
        if not raw:
            continue
        p = strip_markup(raw)
        own = "(aut.)" in p
        pen = "(rig.)" in p
        # explicit count e.g. (2) / (3)
        mcount = re.search(r"\((\d)\)", p)
        ncount = int(mcount.group(1)) if mcount else None
        mins = re.findall(r"(\d+)'(?:\s*\+\s*(\d+)'?)?", re.sub(r"\[\[.*?\]\]", "", p))
        # player name(s): first wikilink or plain text
        names = re.findall(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", p)
        if names:
            name = names[0]
        else:
            name = link_text(re.sub(r"\(\w+\.\)|\(\d\)|\d+'(\+\d+')?,?", "", p))
        out.append(dict(player=name.strip(), minutes=[("%s+%s" % (a, b) if b else a) for a, b in mins],
                        own_goal=own, penalty=pen, count=ncount, raw=raw))
    return out


def main(src, outm, outs):
    lines = open(src, encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("== Risultati =="))
    end = next(i for i, l in enumerate(lines) if l.startswith("== Statistiche =="))
    seg = "\n".join(lines[start:end])
    rows = seg.split("\n|-")[1:]
    active = {}
    matches, scorers = [], []
    for r in rows:
        cells = [l[1:] for l in r.strip().split("\n") if l.startswith("|") and not l.startswith("|}")]
        if len(cells) < 6:
            continue
        vals, ci = [], 0
        for col in range(11):
            if col in active and active[col][0] > 0:
                active[col][0] -= 1
                vals.append(active[col][1])
                continue
            if ci >= len(cells):
                vals.append("")
                continue
            c = cells[ci]
            ci += 1
            m = re.match(r"\s*rowspan=(\d+)\s*\|(.*)", c)
            if m:
                n = int(m.group(1))
                c = m.group(2)
                active[col] = [n - 1, c]
            vals.append(c)
        n_, data, stadio, comp, inc, ris, scM, scI, nt, ref, arb = vals
        iso = parse_date(data)
        inc_clean = strip_markup(inc)
        t = re.findall(r"\{\{Calcio ([A-Za-z\-]+)", inc_clean)
        home_name = t[0] if t else ""
        away_name = t[1] if len(t) > 1 else ""
        norm = lambda n: "Milan" if n.startswith("Milan") else ("Inter" if n in ("Inter", "Ambrosiana", "Ambrosiana-Inter") else n)
        home, away = norm(home_name), norm(away_name)
        mr = re.search(r"(\d+)\s*[-–]\s*(\d+)", ris)
        hg, ag = (int(mr.group(1)), int(mr.group(2))) if mr else (None, None)
        mref = re.search(r"https?://[^\s\]]+?(?=''|\s|\])", ref) if ref else None
        matches.append(dict(
            nr=link_text(n_), date_text=link_text(data), date=iso, venue=link_text(stadio),
            competition=link_text(comp), competition_raw=comp.strip(), home=home, away=away, home_name=home_name, away_name=away_name,
            home_goals=hg, away_goals=ag, result_raw=link_text(ris),
            scorers_milan_raw=scM.strip(), scorers_inter_raw=scI.strip(),
            nr_in_competition=link_text(nt), referee=link_text(arb), report_url=mref.group(0) if mref else ""))
        for team, cellx in (("Milan", scM), ("Inter", scI)):
            for s in parse_scorers(cellx):
                scorers.append(dict(nr=link_text(n_), date=iso, team=team, **{k: v for k, v in s.items()}))
    with open(outm, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(matches[0].keys()))
        w.writeheader(); w.writerows(matches)
    with open(outs, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["nr", "date", "team", "player", "minutes", "own_goal", "penalty", "count", "raw"])
        w.writeheader()
        for s in scorers:
            s = dict(s); s["minutes"] = ";".join(s["minutes"]); w.writerow(s)
    print(len(matches), "matches", len(scorers), "scorer entries")


if __name__ == "__main__":
    main(*sys.argv[1:4])
