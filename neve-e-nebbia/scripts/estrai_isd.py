"""Legge i file ISD (gz, formato a larghezza fissa) e produce:
 1) un file giornaliero (giorno UTC) per stazione con segnali neve/nebbia/visibilita'
 2) un file di diagnostica per stazione-anno (n. osservazioni, tipi di rapporto, copertura tempo presente)
Uso: python -I estrai_isd.py <raw/noaa/isd> <cartella_uscita>
Definizioni (vedi NOTE.md):
 MW = tempo presente manuale (tab. WMO 4677), AW = automatico (tab. 4680), AU = automatico METAR-like, AT = sintesi giornaliera
"""
import sys, os, re, gzip, csv, collections, glob

root, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)

# codici WMO 4677 (MW)
MW_SNOW_STRICT = {70,71,72,73,74,75,77,78,85,86}          # neve in atto all'osservazione (no 76 diamond dust, 79 ice pellets)
MW_SNOW_WIDE = MW_SNOW_STRICT | {68,69,83,84,22,23,26}     # + pioggia e neve, e neve nell'ora precedente
MW_FOG_STRICT = {41,42,43,44,45,46,47,48,49}              # nebbia sulla stazione
MW_FOG_WIDE = MW_FOG_STRICT | {28,40,11,12}                # + nebbia ora precedente / lontana / strati bassi
# codici WMO 4680 (AW)
AW_SNOW_STRICT = {70,71,72,73,85,86,87}   # neve (nel testo ISD: 70-73 neve, 85-87 rovesci di neve)
AW_SNOW_WIDE = AW_SNOW_STRICT | {45,46,67,68,24}  # + precipitazione solida, pioggia e neve, neve ora prec.
AW_FOG_STRICT = {30,31,32,33,34,35}
AW_FOG_WIDE = AW_FOG_STRICT | {20}
GOOD_Q = set("014 5 9AIMPRU".replace(" ", ""))  # esclude 2,3,6,7 (sospetto/errato)

re_mw = re.compile(r"MW(\d)(\d{2})(\w)")
re_aw = re.compile(r"AW(\d)(\d{2})(\w)")
re_au = re.compile(r"AU\d(\d)(\d)(\d{2})(\d)(\d)(\d)(\w)")
re_aj = re.compile(r"AJ1(\d{4})(\w)(\w)")
re_at = re.compile(r"AT\d(AU|AW|MW)(\d{2}).{4}(\w)")
re_at_strip = re.compile(r"AT\d(?:AU|AW|MW)\d{2}.{4}\w")

re_tok = re.compile(r"^([-+]|VC)?(MI|PR|BC|DR|BL|SH|TS|FZ)*(DZ|RA|SN|SG|IC|PL|GR|GS|UP|BR|FG|FU|VA|DU|SA|HZ|PY|PO|SQ|FC|SS|DS)+$")
def metar_text(rem):
    """Se REM contiene un METAR/SPECI completo ritorna (completo, auto, neve, nebbia_qualsiasi, nebbia_densa, vv); altrimenti None"""
    m = re.search(r"(METAR|SPECI)\s+(COR\s+)?[A-Z]{4}\s+\d{6}Z\s*(AUTO|COR)?", rem)
    if not m: return None
    body = rem[m.start():].split("=")[0]
    auto = bool(re.search(r"\sAUTO\s", body))
    for kw in (" BECMG", " TEMPO", " NOSIG", " RMK"):
        k = body.find(kw)
        if k >= 0: body = body[:k]
    toks = body.split()
    snow = fog = dense = vv = False
    for t in toks[3:]:
        if t.startswith("VV"): vv = True
        if re_tok.match(t):
            core = t.lstrip("+-")
            if ("SN" in core or "SG" in core) and not core.startswith(("BL", "DR")): snow = True
            if "FG" in core and not core.startswith("VC"):
                fog = True
                if core in ("FG", "FZFG", "PRFG") or t == "FG": dense = True
    return True, auto, snow, fog, dense, vv

def newday():
    return dict(n_obs=0, horas=set(), n_pw=0, types=collections.Counter(), snow_strict=0, snow_wide=0, fog_strict=0, fog_wide=0,
                fogvis=0, syn_n=0, syn_hours=set(), syn_snow=0, syn_fog=0, syn_fogvis=0, syn_minvis=None, m_full=0, m_auto=0, m_snow=0, m_fog=0, m_fogd=0, m_vv=0, snow_heavy=0, minvis=None, depth=None, snowdepth_n=0, at_snow=0, at_fog=0, src_manual=0, src_auto=0, pw_codes=collections.Counter())

for st_dir in sorted(glob.glob(os.path.join(root, "*"))):
    st = os.path.basename(st_dir)
    days = {}
    diag = {}
    for fn in sorted(glob.glob(os.path.join(st_dir, "*.gz"))):
        year = int(os.path.basename(fn).split("-")[-1][:4])
        d = diag.setdefault(year, collections.Counter())
        with gzip.open(fn, "rt", encoding="latin-1") as f:
            for line in f:
                line = line.rstrip("\n")
                if len(line) < 105: continue
                date = line[15:19] + "-" + line[19:21] + "-" + line[21:23]
                hhmm = line[23:27]
                rtype = line[41:46].strip()
                add = line[105:]
                rem = ""
                i = add.find("REM")
                if i >= 0:
                    rem = add[i+3:]
                    j = rem.find("EQD")
                    if j >= 0: rem = rem[:j]
                for cut in ("REM", "EQD"):
                    i = add.find(cut)
                    if i >= 0: add = add[:i]
                vis_raw = line[78:84]; vis_q = line[84]; cavok = line[77]
                vis = None
                if vis_raw != "999999" and vis_q in GOOD_Q:
                    try: vis = int(vis_raw)
                    except: pass
                dd = days.setdefault(date, newday())
                dd["n_obs"] += 1
                dd["horas"].add(hhmm[:2])
                dd["types"][rtype] += 1
                d["obs"] += 1; d["type_" + rtype] += 1
                mt = metar_text(rem)
                if mt:
                    d["metar_full"] += 1; dd["m_full"] += 1
                    if mt[1]: d["metar_auto"] += 1; dd["m_auto"] += 1
                    if mt[2]: dd["m_snow"] += 1
                    if mt[3]: dd["m_fog"] += 1
                    if mt[4]: dd["m_fogd"] += 1
                    if mt[5]: dd["m_vv"] += 1
                if rtype == "AUTO": d["type_AUTO_flag"] += 1
                if vis is not None:
                    d["vis_ok"] += 1
                    if dd["minvis"] is None or vis < dd["minvis"]: dd["minvis"] = vis
                if cavok == "Y": d["cavok"] += 1
                at_all = re_at.findall(add)
                add = re_at_strip.sub("", add)
                mw = [(int(c), q) for _, c, q in re_mw.findall(add) if q in GOOD_Q]
                aw = [(int(c), q) for _, c, q in re_aw.findall(add) if q in GOOD_Q]
                au = [m for m in re_au.findall(add) if m[6] in GOOD_Q]
                has_pw = bool(mw or aw or au)
                if has_pw:
                    dd["n_pw"] += 1; d["pw_obs"] += 1
                if mw: d["mw_obs"] += 1; dd["src_manual"] += 1
                if aw: d["aw_obs"] += 1; dd["src_auto"] += 1
                if au: d["au_obs"] += 1; dd["src_auto"] += 1
                codes_mw = {c for c, q in mw}; codes_aw = {c for c, q in aw}
                snow_s = bool(codes_mw & MW_SNOW_STRICT or codes_aw & AW_SNOW_STRICT or any(m[2] in ("03", "04") and m[0] != "4" for m in au))
                snow_w = snow_s or bool(codes_mw & MW_SNOW_WIDE or codes_aw & AW_SNOW_WIDE)
                fog_s = bool(codes_mw & MW_FOG_STRICT or codes_aw & AW_FOG_STRICT or any(m[3] == "2" and m[1] == "0" and m[0] != "4" for m in au))  # FG senza descrittore
                fog_w = fog_s or bool(codes_mw & MW_FOG_WIDE or codes_aw & AW_FOG_WIDE or any(m[3] == "2" and m[0] != "4" for m in au))
                for c in codes_mw: dd["pw_codes"]["MW%02d" % c] += 1
                for c in codes_aw: dd["pw_codes"]["AW%02d" % c] += 1
                if (codes_mw & {74,75}) or (codes_aw & {73,87}) or any(m[2] in ("03","04") and m[0] == "3" for m in au): dd["snow_heavy"] += 1
                if snow_s: dd["snow_strict"] += 1
                if snow_w: dd["snow_wide"] += 1
                if fog_s: dd["fog_strict"] += 1
                if fog_w: dd["fog_wide"] += 1
                if fog_w and vis is not None and vis < 1000: dd["fogvis"] += 1
                # osservazioni "a ore sinottiche": ore 00,03,..,21 UTC e minuto < 30 (campione omogeneo, 8 al giorno al massimo)
                if int(hhmm[:2]) % 3 == 0 and int(hhmm[2:]) < 30:
                    dd["syn_n"] += 1; dd["syn_hours"].add(hhmm[:2])
                    if snow_s: dd["syn_snow"] += 1
                    if fog_s: dd["syn_fog"] += 1
                    if fog_w and vis is not None and vis < 1000: dd["syn_fogvis"] += 1
                    if vis is not None and (dd["syn_minvis"] is None or vis < dd["syn_minvis"]): dd["syn_minvis"] = vis
                for m in at_all:
                    if m[1] == "18": dd["at_snow"] = 1
                    if m[1] in ("01", "02"): dd["at_fog"] = 1
                    d["at_obs"] += 1
                for m in re_aj.finditer(add):
                    dep, cond, q = m.groups()
                    if q in GOOD_Q and dep != "9999":
                        dd["snowdepth_n"] += 1
                        v = int(dep)
                        if cond == "3": v = 0.5  # traccia
                        if dd["depth"] is None or v > dd["depth"]: dd["depth"] = v
                        d["aj_obs"] += 1
    # scrittura
    with open(os.path.join(out, "isd_giorni_%s.csv" % st), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo)
        w.writerow(["date", "station", "n_obs", "n_hours", "n_obs_presentweather", "n_obs_manual_pw", "n_obs_auto_pw", "snow_strict_n", "snow_wide_n", "snow_heavy_n",
                    "fog_code_strict_n", "fog_code_wide_n", "fog_code_vis_lt1km_n", "min_vis_m", "snow_depth_cm", "n_snowdepth_reports", "metar_text_n", "metar_auto_n", "metar_text_snow_n", "metar_text_fog_n", "metar_text_fogdense_n", "metar_text_vv_n", "syn_n_hours", "syn_snow_strict_n", "syn_fog_code_strict_n", "syn_fog_code_vis_lt1km_n", "syn_min_vis_m", "at_snow", "at_fog", "report_types"])
        for date in sorted(days):
            x = days[date]
            w.writerow([date, st, x["n_obs"], len(x["horas"]), x["n_pw"], x["src_manual"], x["src_auto"], x["snow_strict"], x["snow_wide"], x["snow_heavy"], x["fog_strict"], x["fog_wide"], x["fogvis"],
                        "" if x["minvis"] is None else x["minvis"], "" if x["depth"] is None else x["depth"], x["snowdepth_n"], x["m_full"], x["m_auto"], x["m_snow"], x["m_fog"], x["m_fogd"], x["m_vv"], len(x["syn_hours"]), x["syn_snow"], x["syn_fog"], x["syn_fogvis"], "" if x["syn_minvis"] is None else x["syn_minvis"], x["at_snow"], x["at_fog"],
                        ";".join("%s:%d" % kv for kv in sorted(x["types"].items()))])
    allkeys = sorted({k for dd in diag.values() for k in dd})
    with open(os.path.join(out, "isd_diagnostica_%s.csv" % st), "w", newline="", encoding="utf-8") as fo:
        w = csv.writer(fo); w.writerow(["year"] + allkeys)
        for y in sorted(diag): w.writerow([y] + [diag[y].get(k, 0) for k in allkeys])
    print(st, len(days), "giorni")
