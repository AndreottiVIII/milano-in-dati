"""Scarica dataset scelti dal Comune. Uso: python -I -X utf8 02_download_comune.py <search_all.json> <raw_dir>"""
import sys, json, os, urllib.request, datetime, hashlib, csv
sj, raw = sys.argv[1], sys.argv[2]
d = json.load(open(sj, encoding="utf-8"))
WANT = ["ds2952-trasporto-pubblico-locale-dati-sul-servizio","ds1547-domanda-di-tpl-passeggeri-annui-per-abitante-serie-storica",
"ds528_trasporto-pubblico-locale-entro-i-confini-comunali-2008-2013","ds1551-estensione-rete-metropolitana-serie-storica",
"ds1550-densita-rete-metropolitana-serie-storica","ds1566-disponibilita-convogli-metropolitana-serie-storica",
"ds1567-convogli-della-metropolitana-utilizzati-serie-storica","ds535_atm-fermate-linee-metropolitane",
"ds537_atm-orari-linee-metropolitane","ds539_atm-percorsi-linee-metropolitane","ds533_atm-composizione-percorsi-linee-metropolitane"]
log = []
today = datetime.date.today().isoformat()
for k in WANT:
    v = d[k]
    ds = k.split("_")[0].split("-")[0]
    od = os.path.join(raw, "comune_" + ds); os.makedirs(od, exist_ok=True)
    for fmt, size, url in v["res"]:
        if fmt not in ("CSV", "GeoJSON"): continue
        fn = url.rsplit("/", 1)[-1]
        p = os.path.join(od, fn)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati research"})
            data = urllib.request.urlopen(req, timeout=120).read()
            open(p, "wb").write(data)
            log.append([k, fmt, url, fn, len(data), hashlib.sha256(data).hexdigest()[:16], today, "ok"])
        except Exception as e:
            log.append([k, fmt, url, fn, 0, "", today, "ERR " + str(e)[:80]])
        print(log[-1][3], log[-1][4], log[-1][-1])
w = csv.writer(open(os.path.join(raw, "download_log_comune.csv"), "w", newline="", encoding="utf-8"))
w.writerow(["dataset","formato","url","file","byte","sha256_16","data_download","esito"]); w.writerows(log)
