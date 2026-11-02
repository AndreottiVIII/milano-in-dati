"""Scarica i CSV del Comune di Milano (CKAN) sui musei. Pausa 3 s. Registra data in raw/download_log.csv.
uso: python -I -X utf8 02_scarica.py <cartella musei assoluta>"""
import sys, os, time, json, urllib.request, datetime
base = sys.argv[1]
raw = os.path.join(base, "raw", "comune_milano"); os.makedirs(raw, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (musei fase 1)"}
ric = json.load(open(os.path.join(base, "raw", "ricerche", "ckan_milano_musei.json"), encoding="utf-8"))
voci = [("ds160", "ds160-cultura-museo-visitatori-1996-2010"), ("ds513", "ds513_musei-statali-visitatori-ed-introiti-1996-avanti"),
        ("ds575", "ds575_musei-visitatori-per-museo-nel-corso-dell-anno"), ("ds577", "ds577_musei_incassi_per_museo_nel_corso_dellanno"),
        ("ds2727", "ds2727-cultura-milano-musei-card"), ("ds650", "ds650_osservatorio_milano__vocazioni_arte_cultura_e_design")]
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
for sig, name in voci:
    for fmt, url in ric[name]["res"]:
        if fmt != "CSV": continue
        fn = os.path.join(raw, sig + "_" + url.rsplit("/", 1)[1])
        if os.path.exists(fn): continue
        r = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(r, timeout=120) as f: data = f.read()
        open(fn, "wb").write(data)
        log.write(f"{datetime.date.today()};{url};{fn};{len(data)};{ric[name]['license']}\n"); log.flush()
        print(fn, len(data)); time.sleep(3)
