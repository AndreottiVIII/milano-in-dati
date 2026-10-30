"""Load derby matches from the secondary sources into small normalised CSVs (pulito/_src_*.csv).
Usage: python -I 05_load_sources.py <derby_dir>"""
import sys, os, re, csv, glob, datetime
import pandas as pd
base = sys.argv[1]
raw, out = base + "/raw", base + "/pulito"

def w(name, rows, cols):
    with open(f"{out}/{name}", "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols); wr.writeheader(); wr.writerows(rows)
    print(name, len(rows))

# --- engsoccerdata
d = pd.read_csv(raw + "/engsoccerdata/italy.csv")
rows = []
for r in d.itertuples():
    if {r.home, r.visitor} == {"AC Milan", "Inter"}:
        rows.append(dict(date=r.Date, season=r.Season, home="Milan" if r.home == "AC Milan" else "Inter",
                         away="Milan" if r.visitor == "AC Milan" else "Inter", hg=r.hgoal, ag=r.vgoal, src="engsoccerdata"))
w("_src_engsoccerdata.csv", rows, ["date", "season", "home", "away", "hg", "ag", "src"])

# --- football-data (cache + direct)
rows = []
def nm(t):
    t = t.strip()
    if t in ("Inter", "Internazionale"): return "Inter"
    if t in ("Milan", "AC Milan"): return "Milan"
    return None
for f in sorted(glob.glob(raw + "/footballdata/cache_*")):
    df = pd.read_csv(f)
    for r in df.itertuples():
        a, b = nm(r._2), nm(r._5)
        if a and b:
            dt = datetime.datetime.strptime(r.Date, "%a %b %d %Y").strftime("%Y-%m-%d")
            hg, ag = [int(x) for x in str(r.FT).split("-")]
            rows.append(dict(date=dt, season=os.path.basename(f)[6:13], home=a, away=b, hg=hg, ag=ag, src="footballdata"))
for f in sorted(glob.glob(raw + "/footballdata/fd_*")):
    df = pd.read_csv(f)
    for r in df.itertuples():
        a, b = nm(r.HomeTeam), nm(r.AwayTeam)
        if a and b and not pd.isna(r.FTHG):
            dt = datetime.datetime.strptime(r.Date, "%d/%m/%Y").strftime("%Y-%m-%d")
            rows.append(dict(date=dt, season=os.path.basename(f)[3:7], home=a, away=b, hg=int(r.FTHG), ag=int(r.FTAG), src="footballdata"))
w("_src_footballdata.csv", rows, ["date", "season", "home", "away", "hg", "ag", "src"])

# --- openfootball (scores only; the 2025-26 '-full' file with scorers is parsed in 06)
MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
TM = r"(FC Internazionale Milano|Internazionale|Inter|AC Milan|Milan)(?![A-Za-z])"
rows = []
for f in sorted(glob.glob(raw + "/openfootball/*_1-seriea.txt") + glob.glob(raw + "/openfootball/*_cup.txt")):
    season = os.path.basename(f)[:7]
    y0 = int(season[:4])
    cur = None
    for line in open(f, encoding="utf-8"):
        m = re.match(r"\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Z][a-z]{2})\s+(\d+)(?:\s+(\d{4}))?\s*$", line)
        if m:
            mo, dd = MON[m.group(1)], int(m.group(2))
            yy = int(m.group(3)) if m.group(3) else (y0 if mo >= 7 else y0 + 1)
            cur = datetime.date(yy, mo, dd).isoformat()
            continue
        ts = list(re.finditer(TM, line))
        names = [("Milan" if t.group(1) in ("AC Milan", "Milan") else "Inter") for t in ts]
        if len(ts) == 2 and set(names) == {"Milan", "Inter"}:
            rest = re.sub(r"\([^)]*\)", " ", line)
            rest = re.sub(TM, " ", rest)
            sc = re.findall(r"(\d+)-(\d+)", rest)
            extra = ("pen." in line) or ("a.e.t." in line)
            hg, ag = (int(sc[0][0]), int(sc[0][1])) if sc else ("", "")
            rows.append(dict(date=cur, season=season, home=names[0], away=names[1], hg=hg, ag=ag,
                             src="openfootball:" + os.path.basename(f) + (" | " + line.strip() if extra or not sc else "")))
w("_src_openfootball.csv", rows, ["date", "season", "home", "away", "hg", "ag", "src"])
