"""Scarica i file ISPRA/SNPA necessari in raw/ (con ripresa se interrotto) e scrive raw/download_log.csv.
Uso: python -I -X utf8 scarica.py <cartella suolo assoluta> [gruppo ...]
Gruppi: indicatori, edizioni_snpa, raster_chiave, raster_altri
Solo pagine/file pubblici, nessun login. Un file alla volta.
"""
import sys, os, csv, time, hashlib, urllib.request, datetime

L = "https://groupware.sinanet.isprambiente.it/uso-copertura-e-consumo-di-suolo/library/consumo-di-suolo"
S = "https://www.snpambiente.it/wp-content/uploads"
UA = "milano-in-dati/1.0"

G = {
    "indicatori": [
        ("indicatori/consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx", f"{L}/indicatori/consumo_suolo_2026_com_prov_reg_naz_v1.0/download/en/1/consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx"),
        ("indicatori/stato_del_territorio_2026_v1.0.xlsx", f"{L}/indicatori/stato_del_territorio_2026_v1.0/download/en/1/stato_del_territorio_2026_v1.0.xlsx"),
        ("raster/licenza_2025.txt", f"{L}/carta-nazionale-consumo-suolo-2025/licenza/download/en/1/licenza.txt"),
    ],
    "edizioni_snpa": [
        ("snpa/consumo_suolo_2026_dati_principali.xlsx", f"{S}/2026/10/consumo_suolo_2026_dati_principali-1.xlsx"),
        ("snpa/consumo_suolo_2026_dati_principali_ultimo_anno.xlsx", f"{S}/2026/10/consumo_suolo_2026_dati_principali_ultimo_anno-1.xlsx"),
        ("snpa/potenziale_recupero_2026.xlsx", f"{S}/2026/10/potenziale_recupero_2026.xlsx"),
        ("snpa/sintesi-consumo-di-suolo-2026.pdf", f"{S}/2026/10/sintesi-consumo-di-suolo-2026.pdf"),
        ("snpa/Rapporto_consumo_suolo_2026.pdf", f"{S}/2026/10/Rapporto_consumo_suolo_2026.pdf"),
        ("snpa/consumo_di_suolo_estratto_dati_2025_anni_2006_2024.xlsx", f"{S}/2025/10/consumo_di_suolo_estratto_dati_2025_anni_2006_2024.xlsx"),
    ],
    "logistica": [
        ("logistica/Descrizione.docx", f"{L}/logistica/centroidi/descrizione/download/en/1/Descrizione.docx"),
        ("logistica/Licenza.txt", f"{L}/logistica/centroidi/licenza/download/en/1/Licenza.txt"),
        ("logistica/Logistica_06_22.zip", f"{L}/logistica/centroidi/logistica_06_22/download/en/1/Logistica_06_22.zip"),
        ("logistica/Logistica_22_23.zip", f"{L}/logistica/centroidi/logistica_22_23/download/en/1/Logistica_22_23.zip"),
    ],
    "raster_altri": [
        ("raster/SC_2015_RDN_v6.tif", f"{L}/carta-nazionale-consumo-suolo-2015/sc_2015_rdn_v6/download/en/1/SC_2015_RDN_v6.tif"),
        ("raster/SC_2018_RDN_v6.tif", f"{L}/carta-nazionale-consumo-suolo-2018/sc_2018_rdn_v6/download/en/1/SC_2018_RDN_v6.tif"),
        ("raster/SC_2024_RDN_v8.tif", f"{L}/carta-nazionale-consumo-suolo-2025/sc_2024_rdn_v8/download/en/1/SC_2024_RDN_v8.tif"),
    ],
    "raster_chiave": [
        ("raster/SC_2025_RDN_v8.tif", f"{L}/carta-nazionale-consumo-suolo-2025/sc_2025_rdn_v8/download/en/1/SC_2025_RDN_v8.tif"),
        ("raster/SC_2012_RDN_v6.tif", f"{L}/carta-nazionale-consumo-suolo-2012/sc_2012_rdn_v6/download/en/1/SC_2012_RDN_v6.tif"),
        ("raster/SC_2006_RDN_v6.tif", f"{L}/carta-nazionale-consumo-suolo-2006/sc_2006_rdn_v6-1/download/en/1/SC_2006_RDN_v6.tif"),
        ("raster/consumo_suolo_2024-2025.tif", f"{L}/carta-nazionale-consumo-suolo-2025/cambiamenti-2024-2025/consumo_suolo_2024-2025/download/en/1/consumo_suolo_2024-2025.tif"),
        ("raster/Legenda_QGIS_2025_v8.qml", f"{L}/carta-nazionale-consumo-suolo-2025/legenda_qgis_2025_v8/download/en/1/Legenda_QGIS_2025_v8.qml"),
    ],
}


def scarica(dest, url, log):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    if os.path.exists(dest):
        print("gia presente", dest)
        return
    pos = os.path.getsize(part) if os.path.exists(part) else 0
    h = {"User-Agent": UA}
    if pos:
        h["Range"] = f"bytes={pos}-"
    req = urllib.request.Request(url, headers=h)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=120) as r:
        mode = "ab" if (pos and r.status == 206) else "wb"
        with open(part, mode) as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
    os.replace(part, dest)
    sha = hashlib.sha256()
    with open(dest, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            sha.update(b)
    log.writerow([datetime.datetime.now().isoformat(timespec="seconds"), os.path.relpath(dest, base), os.path.getsize(dest), sha.hexdigest(), url])
    print("ok", dest, os.path.getsize(dest), f"{time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    base = sys.argv[1]
    gruppi = sys.argv[2:] or ["indicatori", "edizioni_snpa"]
    lp = os.path.join(base, "raw", "download_log.csv")
    new = not os.path.exists(lp)
    with open(lp, "a", newline="", encoding="utf8") as lf:
        log = csv.writer(lf, delimiter=";")
        if new:
            log.writerow(["quando", "file", "byte", "sha256", "url"])
        for g in gruppi:
            for rel, url in G[g]:
                for tent in range(5):
                    try:
                        scarica(os.path.join(base, "raw", rel), url, log)
                        lf.flush()
                        break
                    except Exception as e:
                        print("ERRORE", rel, e, "tentativo", tent, flush=True)
                        time.sleep(20 * (tent + 1))
                time.sleep(3)
