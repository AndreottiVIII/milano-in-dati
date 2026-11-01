"""Scarica i file grezzi dei beni confiscati. Uso: python -I -X utf8 scarica.py <cartella_raw_assoluta>
Solo link pubblici di download (nessun login, nessun aggiramento). Pausa tra una richiesta e l'altra. User-Agent onesto.
Scrive anche download_log.csv (url, file, data, dimensione, sha256)."""
import sys, os, time, csv, hashlib, datetime, urllib.request, zipfile

RAW = sys.argv[1]
UA = {"User-Agent": "milano-in-dati-research/1.0"}
COM = "https://dati.comune.milano.it/dataset/2c48e7c0-6e86-4a0a-95de-b9ea0564efcd/resource/"
OR = "https://openregio.anbsc.it/statistiche/export/"
AZ = "https://aziendeconfiscate.camcom.gov.it/odacWeb/opendata/download/"
WB = "https://web.archive.org/web/"
CB = "confiscatibene.it/sites/default/files/"
FILES = [
    # Comune di Milano, CKAN ds147 (CC-BY)
    ("ds147/ds147_elenco-beni-immobili-confiscati-06_2026.csv", COM + "f0db7ac6-d29a-4cc7-ae97-c05b7908c99e/download/ds147_elenco-beni-immobili-confiscati-06_2026.csv"),
    ("ds147/ds147_elenco-beni-immobili-confiscati-06_2026.json", COM + "03a7adcd-ace2-43d7-a448-d2bb9000bcd8/download/ds147_elenco-beni-immobili-confiscati-06_2026.json"),
    ("ds147/package_show.json", "https://dati.comune.milano.it/api/3/action/package_show?id=ds147-sociale-beni-immobili-confiscati-criminalita-organizzata"),
    # ANBSC OpenRe.G.I.O. (Infoweb), export nazionale CSV: iter 1 = in gestione, 5 = destinati
    ("anbsc_openregio/nazionale_gestione_immobili.csv", OR + "1/immobili/0/0/0/csv"),
    ("anbsc_openregio/nazionale_gestione_aziende.csv", OR + "1/aziende/0/0/0/csv"),
    ("anbsc_openregio/nazionale_destinati_immobili.csv", OR + "5/immobili/0/0/0/csv"),
    ("anbsc_openregio/nazionale_destinati_aziende.csv", OR + "5/aziende/0/0/0/csv"),
    # Aziende Confiscate (Unioncamere + ANBSC), JSON-LD, CC BY 4.0
    ("aziende_confiscate_unioncamere/opendata-aziendeconfiscate-catalog.json", AZ + "opendata-aziendeconfiscate-catalog.json"),
    ("aziende_confiscate_unioncamere/aziende-confiscate-anbsc.json", AZ + "aziende-confiscate-anbsc.json"),
    ("aziende_confiscate_unioncamere/aziende-confiscate-unioncamere.json", AZ + "aziende-confiscate-unioncamere.json"),
    # Regione Lombardia, Open Data (Socrata)
    ("regione_lombardia/krpf-yure_meta.json", "https://www.dati.lombardia.it/api/views/krpf-yure.json"),
    ("regione_lombardia/krpf-yure.csv", "https://www.dati.lombardia.it/resource/krpf-yure.csv?$limit=100000"),
    # ISTAT popolazione residente 1/1/2025
    ("istat_pop/POSAS_2025_it_Comuni.zip", "https://demo.istat.it/data/posas/POSAS_2025_it_Comuni.zip"),
    # confiscatibene.it (spento): copie nella Wayback Machine (id_ = file originale)
    ("confiscatibene_wayback/latest_big_2024-08-07.csv", WB + "20240807182618id_/https://www." + CB + "latest_big.csv"),
    ("confiscatibene_wayback/latest_bid_2024-08-06.csv", WB + "20240806133326id_/https://www." + CB + "latest_bid_0.csv"),
    ("confiscatibene_wayback/latest_ad_2024-08-06.csv", WB + "20240806182621id_/https://www." + CB + "latest_ad.csv"),
    ("confiscatibene_wayback/latest_aig_2024-08-08.csv", WB + "20240808070518id_/https://www." + CB + "latest_aig.csv"),
    ("confiscatibene_wayback/immobili_anbsc_2014-09-20.csv", WB + "20140920182231id_/http://www." + CB + "20140721_confiscatibene-immobili_anbsc_0.csv"),
    ("confiscatibene_wayback/aziende_anbsc_2014-09-20.csv", WB + "20140920182600id_/http://www." + CB + "20140721_confiscatibene-aziende_anbsc.csv"),
    ("confiscatibene_wayback/openregio_comuni_2018-02-26.csv", WB + "20180226025107id_/http://www." + CB + "anbsc_openregio_comuni.csv"),
    ("confiscatibene_wayback/dataset_openregiomap_page_2019.html", WB + "20190822202410id_/https://www.confiscatibene.it/dataset/openregiomap"),
    ("confiscatibene_wayback/dataset_openregio_page_2019.html", WB + "20190723221237id_/https://www.confiscatibene.it/dataset/openregio"),
]
log = []
for rel, url in FILES:
    path = os.path.join(RAW, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        data = open(path, "rb").read(); note = "gia' presente"
    else:
        for t in range(3):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
                open(path, "wb").write(data); note = "scaricato"; break
            except Exception as e:
                note = f"errore {e}"; data = b""; time.sleep(20)
        time.sleep(4)
    log.append(dict(file=rel, url=url, data=datetime.date.today().isoformat(), byte=len(data), sha256=hashlib.sha256(data).hexdigest(), esito=note))
    print(rel, len(data), note)
if os.path.exists(os.path.join(RAW, "istat_pop", "POSAS_2025_it_Comuni.zip")):
    zipfile.ZipFile(os.path.join(RAW, "istat_pop", "POSAS_2025_it_Comuni.zip")).extractall(os.path.join(RAW, "istat_pop", "estratto"))
with open(os.path.join(RAW, "download_log.csv"), "w", encoding="utf8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["file", "url", "data", "byte", "sha256", "esito"]); w.writeheader(); w.writerows(log)
