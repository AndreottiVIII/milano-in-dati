"""MIMIT Osservatorio Prezzi e Tariffe - beni e servizi di largo consumo, provincia di Milano, archivio mensile 2021-2026.
Pagina pubblica, modulo GET (robots.txt non vieta il percorso). Una richiesta ogni 2 s. Salva l'HTML grezzo.
Uso: python -I -X utf8 osservaprezzi_milano.py <costo-vita assoluto> [tipi separati da virgola]   (riprendibile; tipi: altri_alim,orto,ittici,servizi,energia,groc)"""
import sys, os, time, urllib.request, urllib.parse, datetime, hashlib
base = sys.argv[1]
out = os.path.join(base, "raw", "mimit_osservaprezzi"); os.makedirs(out, exist_ok=True)
H = {"User-Agent": "milano-in-dati/1.0"}
U = "https://osservaprezzi.mise.gov.it/prezzi/livelli/beni-e-servizi-di-largo-consumo/archivio-rilevazioni-beni-e-servizi-di-largo-consumo"
TIPI = sys.argv[2].split(",") if len(sys.argv) > 2 else ["altri_alim", "orto", "ittici", "servizi", "energia", "groc"]
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
n = 0
for anno in range(2021, 2027):
    for mese in range(1, 13):
        if (anno, mese) > (2026, 9): continue
        for tipo in TIPI:
            fn = os.path.join(out, "%d_%02d_%s.html" % (anno, mese, tipo))
            if os.path.exists(fn): continue
            q = urllib.parse.urlencode({"ANNO": anno, "MESE": mese, "f[PROVINCIA]": "Milano", "f[TIPO_RECORD_MISE]": tipo, "submit": "Applica"})
            try:
                data = urllib.request.urlopen(urllib.request.Request(U + "?" + q, headers=H), timeout=90).read()
            except Exception as e:
                print("ERR", anno, mese, tipo, e, flush=True); time.sleep(5); continue
            open(fn, "wb").write(data); n += 1
            log.write("%s;200;%s;%d;%s;%s\n" % (datetime.date.today(), U + "?" + q, len(data), hashlib.sha256(data).hexdigest()[:16], fn)); log.flush()
            time.sleep(2)
        print(anno, mese, flush=True)
print("FINE", n, flush=True)
