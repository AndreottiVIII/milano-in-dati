"""Build pulito/derby.csv, pulito/marcatori.csv, pulito/differenze.md, pulito/differenze_marcatori.csv, pulito/non_ufficiali_riepilogo.csv
from the intermediate files made by scripts 01,02,05,08,09.
Usage: python -I 10_build.py <derby_dir>"""
import sys, re, csv, datetime, unicodedata, collections, os
base = sys.argv[1]
P = base + "/pulito/"
raw = base + "/raw/"

def rd(name):
    return list(csv.DictReader(open(P + name, encoding="utf-8")))

def D(s):
    return datetime.date.fromisoformat(s) if s else None

def noacc(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()

# ------------------------------------------------------------------ master (it.wikipedia list)
it = [x for x in rd("_itwiki_matches.csv") if x["home_goals"] != ""]      # played only
en = [x for x in rd("_enwiki_matches.csv") if x["home_goals"] != ""]
assert len(it) == 246, len(it)

def season_of(x):
    c = x["competition"]
    m = re.search(r"(\d{4})-(\d{4})$", c)
    if m: return "%s-%s" % (m.group(1), m.group(2)[2:])
    m = re.search(r"(\d{4})$", c)
    y = int(m.group(1))
    if c.startswith("Prima Categoria 1909") and not "-" in c: return "1909"          # Campionato Federale 1909 (Jan-Apr 1909)
    if c.startswith("Campionato Alta Italia"): return "1943-44"
    if c.startswith("Coppa Italia"): return "%d-%02d" % (y - 1, y % 100)               # Coppa Italia 1958 = 1957-58
    if c.startswith("Supercoppa"):
        d = D(x["date"]); y0 = d.year if d.month >= 7 else d.year - 1
        return "%d-%02d" % (y0, (y0 + 1) % 100)
    return str(y)

def group_of(c):
    for k, v in (("Prima Categoria", "Prima Categoria"), ("Divisione Nazionale", "Divisione Nazionale"), ("Serie A", "Serie A"),
                 ("Campionato Alta Italia", "Campionato Alta Italia 1944"), ("Coppa Italia", "Coppa Italia"),
                 ("Supercoppa", "Supercoppa italiana"), ("UEFA Champions League", "UEFA Champions League")):
        if c.startswith(k): return v
    raise ValueError(c)

ROUND_EN = {"QF": "Quarter-final", "SF": "Semi-final", "R16": "Round of 16", "R2": "Round 2", "GS": "Group stage",
            "Final Group": "Final group", "final": "Final", "Supercoppa Italiana final": "Final"}
def round_from_en(c):
    for g in ("Coppa Italia", "UEFA Champions League", "Supercoppa Italiana"):
        if c.startswith(g):
            r = c[len(g):].strip()
            if not r: return "Final" if g.startswith("Super") else ""
            return ROUND_EN.get(r, r)
    return ""

NEUTRAL = {"Stadio nazionale di Pechino", "Stadio internazionale Re Fahd", "Stadio dell'Università Re Sa'ud"}
INTER_NAMES = {"Inter": "Internazionale", "Ambrosiana": "Ambrosiana", "Ambrosiana-Inter": "Ambrosiana-Inter"}
MILAN_NAMES = {"Milan": "Milan", "Milano": "Milano"}

master = []
for i, x in enumerate(it, 1):
    g = group_of(x["competition"])
    status = "wartime_honorary" if g.startswith("Campionato Alta Italia") else "official"
    hn, an = x["home_name"], x["away_name"]
    master.append(dict(
        match_id="D%03d" % i, date=x["date"], season=season_of(x), competition_group=g, competition_detail=x["competition"],
        round="", round_it_box="", status=status, official=1 if status == "official" else 0,
        home=x["home"], away=x["away"],
        home_club_name=(INTER_NAMES.get(hn) or MILAN_NAMES.get(hn)), away_club_name=(INTER_NAMES.get(an) or MILAN_NAMES.get(an)),
        home_goals=int(x["home_goals"]), away_goals=int(x["away_goals"]), venue=x["venue"], neutral_venue=1 if x["venue"] in NEUTRAL else 0,
        referee=x["referee"], result_note="", derby_nr_it=x["nr"], nr_in_competition=x["nr_in_competition"], report_url=x["report_url"],
        _src={}, _diff=[]))
for m in master:
    m["winner"] = "draw" if m["home_goals"] == m["away_goals"] else (m["home"] if m["home_goals"] > m["away_goals"] else m["away"])
    if m["home_goals"] == m["away_goals"]: m["winner"] = "draw"
mid_by_nr = {m["derby_nr_it"]: m for m in master}
# the awarded match
for m in master:
    if m["date"] == "2005-04-12":
        m["result_note"] = "Result awarded 0-3 by UEFA; match abandoned at 73 minutes with Milan ahead 0-1 (Inter fans threw flares). Scorers list holds only the one real goal."

# ------------------------------------------------------------------ corrections to the it.wikipedia list
# Rule: a field is corrected only when >= 3 sources independent of Wikipedia (engsoccerdata, RSSSF, Inter almanac via archive.org) agree against it/en.wikipedia.
# Everything else is only reported in differenze.md.
corrections = []   # (match_id, field, it.wikipedia value, corrected value, evidence)
byid = {m["match_id"]: m for m in master}
def set_note(m, text):
    m["result_note"] = (m["result_note"] + " " if m["result_note"] else "") + text
for mid, newdate in (("D022", "1931-03-15"), ("D057", "1948-10-17")):
    m = byid[mid]
    corrections.append((mid, "date", m["date"], newdate, "engsoccerdata, RSSSF and interfc.it almanac all give " + newdate))
    set_note(m, "Date corrected from %s (it.wikipedia and en.wikipedia) to %s (engsoccerdata, RSSSF, interfc.it almanac)." % (m["date"], newdate))
    m["date"] = newdate
for mid, other in (("D071", "D072"), ("D072", "D071")):
    m = byid[mid]
    corrections.append((mid, "home/away", "%s %d-%d %s" % (m["home"], m["home_goals"], m["away_goals"], m["away"]), "%s %d-%d %s" % (m["away"], m["away_goals"], m["home_goals"], m["home"]),
                        "engsoccerdata, RSSSF and interfc.it almanac all give the mirrored home/away; scorers (minutes) match the mirrored version; it.wikipedia 'Referto' links of D071/D072 are also exchanged"))
    set_note(m, "Home/away label corrected: it.wikipedia and en.wikipedia list the two 1955-56 derbies with the home side reversed (engsoccerdata, RSSSF, interfc.it almanac agree on the corrected version).")
    m["home"], m["away"] = m["away"], m["home"]
    m["home_goals"], m["away_goals"] = m["away_goals"], m["home_goals"]
    m["home_club_name"], m["away_club_name"] = m["away_club_name"], m["home_club_name"]
byid["D071"]["report_url"], byid["D072"]["report_url"] = byid["D072"]["report_url"], byid["D071"]["report_url"]

# ------------------------------------------------------------------ matching helper
def match_source(rows, window=12, key_date=True):
    """greedy chronological match of source rows to master rows (same pair of clubs implied). returns {match_id: row}, unmatched rows"""
    used, out, unmatched = set(), {}, []
    rows = sorted(rows, key=lambda r: (r["date"] or "9999"))
    for r in rows:
        if not r["date"]:
            unmatched.append(r); continue
        best, bd = None, 10 ** 6
        for m in master:
            if m["match_id"] in used: continue
            dd = abs((D(m["date"]) - D(r["date"])).days)
            if dd <= window and dd < bd: best, bd = m, dd
        if best is None: unmatched.append(r)
        else: used.add(best["match_id"]); out[best["match_id"]] = r
    return out, unmatched

def compare(m, srcname, r, check_date=True, date_note=""):
    d = []
    if check_date and r.get("date") and r["date"] != m["date"]:
        d.append(("date", m["date"], r["date"] + date_note))
    if r.get("home") and r["home"] != m["home"]:
        d.append(("home", m["home"], r["home"]))
    if str(r["hg"]) != "" :
        if (int(r["hg"]), int(r["ag"])) != (m["home_goals"], m["away_goals"]):
            # same score with swapped home is reported under 'home'
            d.append(("score", "%d-%d" % (m["home_goals"], m["away_goals"]), "%s-%s" % (r["hg"], r["ag"])))
    m["_src"][srcname] = "agree" if not d else "differ"
    for k, a, b in d:
        m["_diff"].append((srcname, k, a, b))
    return d

all_diffs = []   # (match_id, date, source, field, master, other)
cover = collections.OrderedDict()   # source -> dict(compared, agree, differ, not_found, extra)

def run_source(name, rows, window=12, check_date=True, scope=None, date_note="", note_for_missing=None):
    """scope(m) -> True if master match m is expected to be covered by the source"""
    matched, unm = match_source(rows, window)
    c = dict(compared=0, agree=0, differ=0, not_found=[], extra=unm)
    for m in master:
        if m["match_id"] in matched:
            c["compared"] += 1
            d = compare(m, name, matched[m["match_id"]], check_date, date_note)
            c["agree" if not d else "differ"] += 1
            for k, a, b in d: all_diffs.append((m["match_id"], m["date"], name, k, a, b))
        elif scope and scope(m):
            c["not_found"].append(m["match_id"])
    cover[name] = c
    return matched

def sstart(m): return int(m["season"][:4])

# en.wikipedia (all)
en_rows = [dict(date=x["date"], home=x["home"], hg=x["home_goals"], ag=x["away_goals"], comp=x["competition"], season=x["season"], note=x["note"]) for x in en]
en_matched = run_source("en.wikipedia", en_rows, scope=lambda m: True)
for mid, r in en_matched.items():
    mm = next(m for m in master if m["match_id"] == mid)
    mm["round"] = round_from_en(r["comp"])
    if r["note"]: mm["result_note"] = (mm["result_note"] + " " if mm["result_note"] else "") + "en.wikipedia note: " + r["note"]
    en_group = r["comp"]
    # competition cross-check
    c0 = re.sub(r" (QF|SF|R16|R2|GS|Final Group|final)$", "", en_group)
    c0 = c0.replace("Supercoppa Italiana final", "Supercoppa Italiana")
    ok = {"Prima Categoria": "Prima Categoria", "Divisione Nazionale": "Divisione Nazionale", "Serie A": "Serie A", "Campionato Alta Italia": "Campionato Alta Italia 1944",
          "Coppa Italia": "Coppa Italia", "Supercoppa Italiana": "Supercoppa italiana", "UEFA Champions League": "UEFA Champions League"}.get(c0)
    if ok != mm["competition_group"]:
        all_diffs.append((mid, mm["date"], "en.wikipedia", "competition", mm["competition_group"], c0))

# engsoccerdata (Serie A 1929-30 .. 2024-25, only 'Serie A' group)
eng = [dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"]) for x in rd("_src_engsoccerdata.csv")]
run_source("engsoccerdata", eng, window=100, scope=lambda m: m["competition_group"] == "Serie A" and 1929 <= sstart(m) <= 2024)
# football-data (Serie A 1993-94 .. 2025-26)
fd = [dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"]) for x in rd("_src_footballdata.csv")]
run_source("football-data.co.uk", fd, scope=lambda m: m["competition_group"] == "Serie A" and 1993 <= sstart(m) <= 2025)
# openfootball
of = [dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"], src=x["src"]) for x in rd("_src_openfootball.csv") if x["hg"] != "" and x["date"] < "2026-10-30"]
run_source("openfootball", of, scope=lambda m: (m["competition_group"] == "Serie A" and 2013 <= sstart(m) <= 2025) or (m["competition_group"] == "Coppa Italia" and 2020 <= sstart(m) <= 2024))
# RSSSF (dated lists)
rs_all = rd("_src_rsssf.csv")
rs = [dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"], scorers=x["scorers"], kind=x["kind"], page=x["page"]) for x in rs_all if x["kind"] != "matrix" and x["date"]]
rs_undated = [x for x in rs_all if x["kind"] != "matrix" and not x["date"]]
rs_pages = {x["page"] for x in rs_all}
def rs_scope(m):
    if m["competition_group"] not in ("Serie A", "Divisione Nazionale", "Coppa Italia", "Campionato Alta Italia 1944"): return False
    return True
rs_matched = run_source("RSSSF", rs, window=16, scope=None, date_note=" (RSSSF uses round date)")
# RSSSF matrix (1926-28): season key by page name ital27 -> 1926-27
mx = [x for x in rs_all if x["kind"] == "matrix"]
for x in mx:
    sea = "19%02d-%02d" % (int(x["page"][4:]) - 1, int(x["page"][4:]))
    cands = [m for m in master if m["season"] == sea and m["home"] == x["home"] and m["competition_group"] == "Divisione Nazionale"]
    if len(cands) == 1:
        m = cands[0]
        d = compare(m, "RSSSF", dict(date="", home=x["home"], hg=x["hg"], ag=x["ag"]), check_date=False)
        for k, a, b in d: all_diffs.append((m["match_id"], m["date"], "RSSSF", k, a, b))
        cover["RSSSF"]["compared"] += 1; cover["RSSSF"]["agree" if not d else "differ"] += 1
# undated RSSSF rows: match by season/home
for x in rs_undated:
    ym = re.match(r"ital(\d{2,4})$", x["page"]); y = int(ym.group(1)); y = 2000 + y if len(ym.group(1)) == 2 and y < 26 else (1900 + y if len(ym.group(1)) == 2 else y)
    sea = "%d-%02d" % (y - 1, y % 100)
    cands = [m for m in master if m["season"] == sea and m["home"] == x["home"] and m["competition_group"] in ("Serie A", "Divisione Nazionale") and "RSSSF" not in m["_src"]]
    if len(cands) == 1:
        m = cands[0]
        d = compare(m, "RSSSF", dict(date="", home=x["home"], hg=x["hg"], ag=x["ag"]), check_date=False)
        for k, a, b in d: all_diffs.append((m["match_id"], m["date"], "RSSSF", k, a, b))
        cover["RSSSF"]["compared"] += 1; cover["RSSSF"]["agree" if not d else "differ"] += 1
        rs_matched[m["match_id"]] = dict(x, date=m["date"])
    else:
        cover["RSSSF"]["extra"].append(x)
# the RSSSF "not found" computed afterwards
cover["RSSSF"]["not_found"] = [m["match_id"] for m in master if "RSSSF" not in m["_src"] and m["competition_group"] in ("Serie A", "Divisione Nazionale", "Coppa Italia", "Campionato Alta Italia 1944") and m["season"] >= "1926"]

# Wikipedia edition pages (boxes)
wb = rd("_src_wikiseasons.csv")
wbrows = [dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"], venue=x["venue"], round=x["round"], referee=x["referee"], sh=x["scorers_home"], sa=x["scorers_away"], page=x["page"]) for x in wb if x["hg"] != ""]
wb_matched = run_source("it.wikipedia edition pages", wbrows, scope=lambda m: m["competition_group"] in ("Coppa Italia", "Supercoppa italiana") and (m["match_id"] in {"x"} or False))
cover["it.wikipedia edition pages"]["not_found"] = [m["match_id"] for m in master if m["match_id"] not in wb_matched and m["competition_group"] in ("Coppa Italia", "Supercoppa italiana") and m["season"] in
    {"1957-58", "1967-68", "1971-72", "1973-74", "1974-75", "1976-77", "1980-81", "1981-82", "1984-85", "1997-98", "1999-00", "2011-12", "2022-23", "2024-25"}]
for mid, r in wb_matched.items():
    mm = next(m for m in master if m["match_id"] == mid)
    mm["round_it_box"] = r["round"]

# venue cross-check against the edition boxes
def vnorm(v):
    v = noacc(v)
    if "san siro" in v or "meazza" in v: return "san siro"
    return v.replace("stadio ", "").replace("campo ", "")
for mid, r in wb_matched.items():
    mm = next(m for m in master if m["match_id"] == mid)
    if vnorm(mm["venue"]) != vnorm(r["venue"]):
        all_diffs.append((mid, mm["date"], "it.wikipedia edition pages", "venue", mm["venue"], r["venue"]))
    if mm["referee"] and r["referee"] and noacc(mm["referee"].split(" di ")[0]).split()[-1] not in noacc(r["referee"]):
        all_diffs.append((mid, mm["date"], "it.wikipedia edition pages", "referee", mm["referee"], r["referee"]))

# RSSSF European Cup pages: tie lines "Milan AC Ita Internazionale Ita 0-0 1-1 *1-1" (leg scores written from Milan's side)
cover["RSSSF (Champions League pages)"] = dict(compared=0, agree=0, differ=0, not_found=[], extra=[])
for fn, d1, d2 in (("ec200203", "2003-05-07", "2003-05-13"), ("ec200405", "2005-04-06", "2005-04-12"), ("ec202223", "2023-05-10", "2023-05-16")):
    txt = open(raw + "rsssf/%s.html" % fn, encoding="latin-1").read()
    mm = re.search(r"Milan(?: AC)?\s+Ita\s+Internazionale\s+Ita\s+(\d+)-(\d+)\s+(\d+)-(\d+)", txt)
    if not mm: continue
    legs = [(mm.group(1), mm.group(2)), (mm.group(3), mm.group(4))]    # Milan-goals, Inter-goals
    for dd, (mg, ig) in zip((d1, d2), legs):
        m = next(x for x in master if x["date"] == dd)
        hg_, ag_ = (mg, ig) if m["home"] == "Milan" else (ig, mg)
        d = compare(m, "RSSSF (Champions League pages)", dict(date="", home="", hg=hg_, ag=ag_), check_date=False)
        cv = cover["RSSSF (Champions League pages)"]; cv["compared"] += 1; cv["agree" if not d else "differ"] += 1
        for k, a, b in d: all_diffs.append((m["match_id"], m["date"], "RSSSF (Champions League pages)", k, a, b))

# Inter almanac pages (archive.org snapshot) - matched by id (the url comes from the it.wikipedia 'Referto' column)
ifc_rows = rd("_src_interfc.csv") if os.path.exists(P + "_src_interfc.csv") else []
ifc_by_id = {x["match_id"]: x for x in ifc_rows}
if "D071" in ifc_by_id and "D072" in ifc_by_id:
    ifc_by_id["D071"], ifc_by_id["D072"] = ifc_by_id["D072"], ifc_by_id["D071"]
cover["interfc.it almanac (archive.org)"] = dict(compared=0, agree=0, differ=0, not_found=[], extra=[])
for m in master:
    x = ifc_by_id.get(m["match_id"])
    if "interfc.it" not in m.get("report_url", ""): continue
    cv = cover["interfc.it almanac (archive.org)"]
    if not x or not x["title"]:
        cv["not_found"].append(m["match_id"]); continue
    d = compare(m, "interfc.it almanac (archive.org)", dict(date=x["date"], home=x["home"], hg=x["hg"], ag=x["ag"]))
    cv["compared"] += 1; cv["agree" if not d else "differ"] += 1
    for k, a, b in d: all_diffs.append((m["match_id"], m["date"], "interfc.it almanac (archive.org)", k, a, b))
    ifc_extra = x["extra"]
    if ifc_extra: m["result_note"] = (m["result_note"] + " " if m["result_note"] else "") + "interfc note: " + ifc_extra
    if x["referee"] and m["referee"]:
        if noacc(m["referee"].split(" di ")[0].replace(",", "")).split()[0] not in noacc(x["referee"]):
            all_diffs.append((m["match_id"], m["date"], "interfc.it almanac (archive.org)", "referee", m["referee"], x["referee"]))

# ------------------------------------------------------------------ scorers (it.wikipedia)
sc_it = rd("_itwiki_scorers.csv")
rows_sc = []
for s in sc_it:
    m = mid_by_nr.get(s["nr"])
    if not m: continue
    mins = [a for a in s["minutes"].split(";") if a]
    n = int(s["count"]) if s["count"] else None
    own = s["own_goal"] == "True"; pen = s["penalty"] == "True"
    credited = s["team"]
    scorer_team = ({"Milan": "Inter", "Inter": "Milan"}[credited] if own else credited)
    ngoals = max(len(mins), n or 1)
    club_then = None
    for k in range(ngoals):
        minute = mins[k] if k < len(mins) else ""
        pen_flag = "1" if pen and ngoals == 1 else ("some" if pen else "0")
        rows_sc.append(dict(match_id=m["match_id"], date=m["date"], team_credited=credited, player=s["player"], minute=minute,
                            own_goal=1 if own else 0, penalty=pen_flag, scorer_club=scorer_team,
                            minute_known=1 if minute else 0, note="goals in this entry: %d (minute list shorter than goals)" % ngoals if (len(mins) < ngoals and mins) else ""))
rows_sc.sort(key=lambda r: (r["date"], r["team_credited"], int(re.match(r"\d+", r["minute"]).group(0)) if r["minute"] else 999))

# ------------------------------------------------------------------ scorer cross-checks
def surname(name):
    n = noacc(name)
    n = re.sub(r"\(.*?\)", "", n).strip()
    toks = n.split()
    return toks[-1] if toks else n
sc_by_match = collections.defaultdict(list)
for r in rows_sc: sc_by_match[r["match_id"]].append(r)
sc_diffs = []   # (match_id, date, source, kind, detail)

def base_min(s): return int(re.match(r"\d+", s).group(0))

def check_text(m, srcname, text, minutes_style):
    t = noacc(text)
    mine = sc_by_match[m["match_id"]]
    for r in mine:
        sn = surname(r["player"])
        words = re.findall(r"[a-z]+", t)
        import difflib
        if not any(difflib.SequenceMatcher(None, sn, w).ratio() >= 0.7 for w in words):
            sc_diffs.append((m["match_id"], m["date"], srcname, "player not found in source", "%s (%s %s')" % (r["player"], r["team_credited"], r["minute"])))
    # minutes
    if minutes_style == "apos":
        mins = sorted(int(x) for x in re.findall(r"(\d+)'", text))
    else:
        mins = sorted(int(x) for x in re.findall(r"(?<![A-Za-z])(\d{1,3})(?:\+\d+)?(?:pen|og|\b)", re.sub(r"[A-Za-zÀ-ſ\"\.]+\d*", lambda g: "" if not g.group(0).isdigit() else g.group(0), text)))
    mymins = sorted(base_min(r["minute"]) for r in mine if r["minute"])
    if mymins and mins and mymins != mins and len(mymins) == len(mine):
        # tolerate stoppage-time typed as 45/90
        sc_diffs.append((m["match_id"], m["date"], srcname, "minutes differ", "it.wiki %s vs %s %s" % (mymins, srcname, mins)))

for mid, r in rs_matched.items():
    m = next(x for x in master if x["match_id"] == mid)
    if r.get("scorers"):
        check_text(m, "RSSSF", r["scorers"], "apos" if r.get("kind", "list") == "list" else "plain")
for mid, r in wb_matched.items():
    m = next(x for x in master if x["match_id"] == mid)
    txt = (r["sh"] + " " + r["sa"]).strip()
    if txt: check_text(m, "it.wikipedia edition pages", txt, "apos")

for mid, x in ifc_by_id.items():
    if not x["title"] or not x["scorers"]: continue
    m = next(y for y in master if y["match_id"] == mid)
    check_text(m, "interfc.it almanac (archive.org)", x["scorers"], "apos")

# openfootball 2025-26 full file (scorers with minutes, attendance)
full = open(raw + "openfootball/2025-26_1-seriea-full.txt", encoding="utf-8").read().split("\n")
for i, ln in enumerate(full):
    if re.match(r"\s+(FC Internazionale Milano v Milan|Milan v FC Internazionale Milano)\s+\d", ln):
        hdr = full[i - 1]; sc = full[i + 1]
        md = re.match(r"\w+ (\w+) (\d+) .*@ (.*?), Att: (\d+)", hdr)
        mon = {"Nov": 11, "Mar": 3}[md.group(1)]; year = 2025 if mon > 6 else 2026
        iso = "%d-%02d-%02d" % (year, mon, int(md.group(2)))
        m = next(x for x in master if x["date"] == iso)
        m["_src"]["openfootball (full, 2025-26)"] = "agree"
        sc_text = sc.strip().strip("()")
        check_text(m, "openfootball-full", sc_text, "apos")
        m["attendance_openfootball"] = md.group(4)
        # venue check
        if "Meazza" not in md.group(3): sc_diffs.append((m["match_id"], iso, "openfootball-full", "venue", md.group(3)))

# ------------------------------------------------------------------ write derby.csv
OTHER_SRC = ["en.wikipedia", "engsoccerdata", "football-data.co.uk", "openfootball", "RSSSF", "it.wikipedia edition pages", "interfc.it almanac (archive.org)", "RSSSF (Champions League pages)"]
for m in master:
    cov = [s for s in OTHER_SRC if s in m["_src"]]
    ag = [s for s in cov if m["_src"][s] == "agree"]
    dis = ["%s:%s" % (s, "/".join(sorted({d[1] for d in m["_diff"] if d[0] == s}))) for s in cov if m["_src"][s] == "differ"]
    m["sources_checked"] = len(cov) + 1       # +1: it.wikipedia main list
    m["sources_agree"] = len(ag) + 1
    m["sources_list"] = "it.wikipedia" + "".join("; " + s for s in cov)
    m["sources_disagree"] = " | ".join(dis)
    m["home_label_disputed"] = 1 if any(d[1] == "home" for d in m["_diff"]) else 0
cols = ["match_id", "date", "season", "competition_group", "competition_detail", "round", "round_it_box", "status", "official",
        "home", "away", "home_club_name", "away_club_name", "home_goals", "away_goals", "winner", "venue", "neutral_venue", "referee",
        "result_note", "home_label_disputed", "sources_checked", "sources_agree", "sources_list", "sources_disagree", "derby_nr_it", "nr_in_competition", "report_url"]
with open(P + "derby.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(master)
with open(P + "marcatori.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["match_id", "date", "team_credited", "player", "minute", "own_goal", "penalty", "scorer_club", "minute_known", "note"]); w.writeheader(); w.writerows(rows_sc)
with open(P + "differenze_marcatori.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["match_id", "date", "source", "kind", "detail"]); w.writerows(sc_diffs)

# ------------------------------------------------------------------ non-official summary (aggregates only, from it.wikipedia text)
nonuff = [("Coppa Firpi", 1, "1909", "national"), ("Scarpa Radice", 2, "1913", "national"), ("Coppa Gazzetta dello Sport", 2, "1915", "national"),
          ("Coppa Federale", 2, "1915-16", "national (wartime)"), ("Coppa Regionale Lombarda", 2, "1917", "national (wartime)"), ("Coppa Mauro", 5, "1917-19", "national (wartime)"),
          ("Coppa Giuriati", 1, "1918", "national (wartime)"), ("Coppa Biffi", 1, "1918", "national (wartime)"), ("Trofeo Lombardi e Macchi", 5, "1924-29", "national"),
          ("Trofeo Palla d'Oro", 1, "1931", "national"), ("Coppa Pozzani", 2, "1932", "national"), ("Coppa del Primato Cittadino", 8, "1934-1942", "national"),
          ("Coppa Monti", 3, "1944-45", "national (wartime)"), ("Torneo Benefico Lombardo", 2, "1945", "national (wartime)"), ("Coppa Pasinetti", 1, "1953", "national"),
          ("Coppa Citta di Milano", 2, "1963-69", "national"), ("Trofeo Luigi Berlusconi", 2, "1992-2015", "national"), ("Amichevoli varie", 22, "1908-2002", "friendly"),
          ("Coppa Chiasso", 1, "1908", "international"), ("Trofeo Citta di New York", 1, "1969", "international"), ("Mundialito per club", 3, "1981-87", "international"),
          ("World Football Challenge", 1, "2009", "international"), ("International Champions Cup", 1, "2015", "international"), ("Tournee a Perth", 2, "2026", "international")]
with open(P + "non_ufficiali_riepilogo.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f); w.writerow(["tournament", "matches", "years", "type", "note"])
    for t in nonuff: w.writerow(list(t) + ["count only (it.wikipedia 'Partite non ufficiali' legend); single matches NOT available in free sources found; excludes one-period games (Trofeo TIM 13, Memorial Ghezzi 2, Trofeo San Nicola 1)"])

# ------------------------------------------------------------------ differenze.md
L = []
L.append("# Differenze tra le fonti - derby di Milano (fase 1)\n")
L.append("Generato da `scripts/10_build.py` il %s. Le fonti sono confrontate partita per partita con la lista di it.wikipedia (246 derby giocati).\n" % datetime.date.today().isoformat())
L.append("## 1. Quadro per fonte\n")
L.append("| Fonte | Partite confrontate | Concordano (data, casa, punteggio) | Differiscono | Attese ma non trovate | Righe della fonte senza partita corrispondente |")
L.append("|---|---|---|---|---|---|")
for s, c in cover.items():
    L.append("| %s | %d | %d | %d | %d | %d |" % (s, c["compared"], c["agree"], c["differ"], len(c["not_found"]), len(c["extra"])))
L.append("")
L.append("Nota: per RSSSF la data e' quella della giornata (non sempre quella reale); per questo molte differenze di data RSSSF sono solo di calendario.\n")

def table(rows, hdr):
    out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    for r in rows: out.append("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |")
    return out

L.append("## 1b. Correzioni applicate alla lista di it.wikipedia (%d)" % len(corrections))
L.append("")
L.append("Regola: si corregge solo se almeno 3 fonti indipendenti da Wikipedia concordano contro it.wikipedia e en.wikipedia. Tutte le altre differenze restano come in it.wikipedia e sono solo elencate qui sotto.")
L.append("")
L += table([(a, b, c, d, e) for (a, b, c, d, e) in corrections], ["Partita", "Campo", "Valore in it.wikipedia (e en.wikipedia)", "Valore corretto", "Prova"])
L.append("")
L.append("Le tabelle seguenti confrontano le fonti con `derby.csv` DOPO le correzioni: dove it.wikipedia/en.wikipedia compaiono come 'differenti' per queste 4 partite, e' per via delle correzioni.")
L.append("")

for field, title in (("score", "2. Differenze di PUNTEGGIO"), ("home", "3. Differenze di SQUADRA DI CASA"), ("date", "4. Differenze di DATA"), ("competition", "5. Differenze di COMPETIZIONE"), ("venue", "6. Differenze di STADIO"), ("referee", "7. Differenze di ARBITRO")):
    rows = [(a, b, c, d, e, f) for (a, b, c, d, e, f) in all_diffs if d == field]
    L.append("## %s (%d)\n" % (title, len(rows)))
    if rows:
        if field == "date":
            main = [r for r in rows if r[2] != "RSSSF"]; rss = [r for r in rows if r[2] == "RSSSF"]
            L += table([(r[0], r[1], r[2], r[4], r[5]) for r in main], ["Partita", "Data in derby.csv", "Fonte", "derby.csv", "Fonte (data diversa)"])
            L.append("\nDate diverse nella sola RSSSF: %d (probabilmente data nominale della giornata). Elenco completo:\n" % len(rss))
            L += table([(r[0], r[1], r[4], r[5]) for r in rss], ["Partita", "Data in derby.csv", "derby.csv", "RSSSF"])
        else:
            L += table([(r[0], r[1], r[2], r[4], r[5]) for r in rows], ["Partita", "Data (derby.csv)", "Fonte", "derby.csv", "Fonte"])
    L.append("")

L.append("## 8. Differenze sui MARCATORI (%d segnalazioni)\n" % len(sc_diffs))
kinds = collections.Counter((s, k) for (_, _, s, k, _) in sc_diffs)
L += table([(s, k, n) for (s, k), n in sorted(kinds.items())], ["Fonte", "Tipo", "N."])
L.append("\nAvvertenza: il controllo sui giocatori cerca il cognome del marcatore di it.wikipedia nel testo della fonte (senza accenti): ortografie diverse (es. Sevcenko/Shevchenko) producono falsi allarmi. L'elenco completo e' in `differenze_marcatori.csv`; qui le prime righe per tipo.\n")
for (s, k), n in sorted(kinds.items()):
    L.append("### %s - %s\n" % (s, k))
    rr = [x for x in sc_diffs if x[2] == s and x[3] == k]
    L += table([(a, b, e) for (a, b, _, _, e) in rr], ["Partita", "Data", "Dettaglio"])
    L.append("")
L.append("## 9. Righe di una fonte senza partita corrispondente (o con data troppo lontana)\n")
for s_, c in cover.items():
    for r in c["extra"]:
        L.append("- **%s**: %s" % (s_, {k: v for k, v in r.items() if k in ("date", "home", "hg", "ag", "page", "src", "raw")}))
L.append("")
L.append("## 10. Partite attese ma non trovate in una fonte\n")
for s, c in cover.items():
    if c["not_found"]:
        L.append("- **%s** (%d): %s" % (s, len(c["not_found"]), ", ".join(c["not_found"][:60]) + (" ..." if len(c["not_found"]) > 60 else "")))
open(P + "differenze.md", "w", encoding="utf-8").write("\n".join(L) + "\n")

# console summary
print("derby.csv", len(master), "rows; marcatori.csv", len(rows_sc), "rows")
for s, c in cover.items(): print(s, {k: (len(v) if isinstance(v, list) else v) for k, v in c.items()})
print("diff counts", collections.Counter((a[2], a[3]) for a in all_diffs))
print("scorer diffs", kinds)
