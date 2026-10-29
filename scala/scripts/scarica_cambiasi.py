"""Scarica da Internet Archive i file di Cambiasi (1872, 1881) e il testo OCR di Marangoni-Vanbianchi 1906-1920.
Uso: python -I scarica_cambiasi.py <cartella_raw_cambiasi>   (salta i file gia' presenti)"""
import sys, os, time, requests
UA = {"User-Agent": "Mozilla/5.0 (research; milano-in-dati)"}
out = sys.argv[1]
items = {
 "teatroallascala100camb": ["teatroallascala100camb.pdf","teatroallascala100camb_djvu.txt","teatroallascala100camb_hocr.html","teatroallascala100camb_jp2.zip"],
 "teatroallascala00cambgoog": ["teatroallascala00cambgoog.pdf","teatroallascala00cambgoog_djvu.txt"],
 "bub_gb_e864LY_9qOUC": ["bub_gb_e864LY_9qOUC.pdf","bub_gb_e864LY_9qOUC_djvu.txt"],
 "pdf24_merged-16": ["pdf24_merged-16_djvu.txt"],
}
for ident, files in items.items():
    d = os.path.join(out, ident); os.makedirs(d, exist_ok=True)
    for f in files:
        p = os.path.join(d, f)
        if os.path.exists(p): print("gia' presente", p); continue
        for t in range(4):
            try:
                r = requests.get(f"https://archive.org/download/{ident}/{f}", headers=UA, timeout=120, stream=True)
                if r.status_code == 429: time.sleep(60*(t+1)); continue
                r.raise_for_status()
                with open(p+".part","wb") as fh:
                    for c in r.iter_content(1<<20): fh.write(c)
                os.replace(p+".part", p); print("ok", p, os.path.getsize(p)); break
            except Exception as e:
                print("errore", f, e); time.sleep(10*(t+1))
        time.sleep(5)
