"""Scarica da POLLnet (ISPRA, servizio WFS aperto, CC-BY 4.0) le concentrazioni giornaliere
di pollini/spore per alcune stazioni vicine a Milano.

Uso: python -I -X utf8 scarica_pollnet.py <cartella raw/ispra assoluta> [id stazione ...]
Il server restituisce al massimo 3000 righe per richiesta: si pagina con startIndex,
un anno alla volta. File non fidati: restano in raw/, mai eseguiti.
Scrive: <raw>/concentrazioni/STAT<id>_<codice>.csv  e  <raw>/download_log.csv
"""
import csv, io, sys, time, urllib.parse, urllib.request, datetime, os

BASE = "https://sdi.isprambiente.it/geoserver/om/ows"
UA = "Mozilla/5.0 (research; milano-in-dati; dati aperti CC-BY)"
PAGE = 3000
STAZIONI = {113: "NO1", 143: "VC1", 124: "PC1", 114: "VB1", 152: "VR1", 148: "AL6"}


def get(params, tries=4):
    url = BASE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read().decode("utf8")
        except Exception as e:  # noqa
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))


def anno(stat, y):
    rows, hdr, start = [], None, 0
    flt = f"STAT_ID={stat} and REMA_DATE between '{y}-01-01' and '{y}-12-31'"
    while True:
        txt = get(dict(service="WFS", version="2.0.0", request="GetFeature",
                       typeName="om:Concentrazione_pollini_spore", outputFormat="csv",
                       sortBy="PART_SEQ,PART_ID", count=PAGE, startIndex=start, cql_filter=flt))
        rd = list(csv.reader(io.StringIO(txt)))
        if not rd:
            break
        hdr = rd[0]
        body = rd[1:]
        rows += body
        if len(body) < PAGE:
            break
        start += PAGE
        time.sleep(0.3)
    return hdr, rows


def main():
    raw = sys.argv[1]
    ids = [int(x) for x in sys.argv[2:]] or list(STAZIONI)
    os.makedirs(os.path.join(raw, "concentrazioni"), exist_ok=True)
    log = []
    ora = datetime.datetime.now().isoformat(timespec="seconds")
    for st in ids:
        out, hdr_all = [], None
        for y in range(2005, 2027):
            hdr, rows = anno(st, y)
            if hdr:
                hdr_all = hdr
            out += rows
            print(st, y, len(rows), flush=True)
        if hdr_all is None:
            continue
        fn = os.path.join(raw, "concentrazioni", f"STAT{st}_{STAZIONI.get(st, 'x')}.csv")
        with open(fn, "w", encoding="utf8", newline="") as f:
            w = csv.writer(f)
            w.writerow(hdr_all)
            w.writerows(out)
        log.append((st, STAZIONI.get(st, ""), len(out), os.path.getsize(fn), ora))
    lf = os.path.join(raw, "download_log.csv")
    new = not os.path.exists(lf)
    with open(lf, "a", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["stat_id", "codice", "righe", "byte", "scaricato_il"])
        w.writerows(log)


if __name__ == "__main__":
    main()
