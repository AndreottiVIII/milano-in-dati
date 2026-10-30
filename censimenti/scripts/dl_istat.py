import sys, os, time, requests
root = sys.argv[1]
UA = {"User-Agent": "Mozilla/5.0 (research; davide.caniatti@gmail.com)"}
B = "https://www.istat.it/storage/cartografia/"
items = [
 ("istat_sezioni_1991","basi_territoriali/WGS_84_UTM/1991/R03_91_WGS84.zip"),
 ("istat_sezioni_2001","basi_territoriali/WGS_84_UTM/2001/R03_01_WGS84.zip"),
 ("istat_sezioni_2011","basi_territoriali/WGS_84_UTM/2011/R03_11_WGS84.zip"),
 ("istat_sezioni_2021","basi_territoriali/2021/R03_21.zip"),
 ("istat_variabili_cpa","variabili-censuarie/dati-cpa_1991.zip"),
 ("istat_variabili_cpa","variabili-censuarie/dati-cpa_2001.zip"),
 ("istat_variabili_cpa","variabili-censuarie/dati-cpa_2011.zip"),
 ("istat_variabili_cis","variabili-censuarie/dati-cis_1991.zip"),
 ("istat_variabili_cis","variabili-censuarie/dati-cis_2001.zip"),
 ("istat_variabili_cis","variabili-censuarie/dati-sce_2011.zip"),
 ("istat_aree_subcomunali","basi_territoriali/aree-subcomunali-xls-shp/ASC2011_WGS84.zip"),
 ("istat_aree_subcomunali","https://www.istat.it/wp-content/uploads/2025/04/ASC_21.zip"),
 ("istat_sezioni_kmz_43comuni","basi_territoriali/Sezioni-Censimento-kmz.zip"),
 ("istat_variabili_2021","https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip"),
 ("istat_documentazione","https://www.istat.it/wp-content/uploads/2024/07/Descrizione-dei-dati-Basi-territoriali.pdf"),
 ("istat_documentazione","https://www.istat.it/wp-content/uploads/2024/07/Nota-informativa-Basi-territoriali-2021-1.pdf"),
 ("istat_documentazione","https://www.istat.it/wp-content/uploads/2024/07/Nota-metodologica-RSBL.pdf"),
 ("istat_documentazione","https://www.istat.it/wp-content/uploads/2026/03/Nota-Informativa-sezioni-censimento-2023.pdf"),
 ("istat_documentazione","https://www.istat.it/it/files/2011/11/Descrizione-dati-Pubblicazionev2.pdf"),
 ("istat_documentazione","https://www.istat.it/it/files//2013/11/Descrizione-dati-Pubblicazione-2016.03.09.pdf"),
]
for d, u in items:
    url = u if u.startswith("http") else B+u
    out = os.path.join(root, "raw", d); os.makedirs(out, exist_ok=True)
    fn = os.path.join(out, url.rsplit("/",1)[1])
    if os.path.exists(fn) and os.path.getsize(fn)>0: print("skip", fn); continue
    for att in range(4):
        try:
            r = requests.get(url, headers=UA, stream=True, timeout=120)
            if r.status_code==429: time.sleep(60*(att+1)); continue
            r.raise_for_status()
            with open(fn+".part","wb") as f:
                for c in r.iter_content(1<<20): f.write(c)
            os.replace(fn+".part", fn); print("ok", fn, os.path.getsize(fn), flush=True); break
        except Exception as e:
            print("err", url, e, flush=True); time.sleep(10*(att+1))
    time.sleep(3)
print("DONE")
