"""Scarica da web.archive.org copie archiviate dei file dell'elenco attività storiche (dati CC0 del Comune/Regione).
Uso: python -I -X utf8 scarica_wayback.py <raw assoluta>. Pausa tra le richieste, 4 tentativi."""
import sys, os, time, urllib.request, hashlib, csv, datetime
raw = sys.argv[1] + "/wayback"; os.makedirs(raw, exist_ok=True)
B = "https://dati.comune.milano.it/dataset/624e5fff-9e40-4adc-9b82-a5d06fa95a26/resource/"
J = B + "6fb23e90-eddc-4303-8522-d0563f4bd1b4/download/"
C = B + "d5391f43-4186-43b7-8b68-d3b2c2b5fb28/download/"
L = "https://www.dati.lombardia.it/api/views/czq5-nkk7/"
voci = [
 ("mi_20190723.csv", "20190723194023", C + "ds612_negozi-e-locali-storici-georeferenziati-nel-comune_puf6-2m2d.csv"),
 ("mi_20190823.json", "20190823052555", J + "ds612_negozi-e-locali-storici-georeferenziati-nel-comune_puf6-2m2d.json"),
 ("mi_20191024.json", "20191024052435", J + "ds612_negozi-e-locali-storici-georeferenziati-nel-comune_puf6-2m2d.json"),
 ("mi_20200810.json", "20200810105802", J + "ds612_negozi-e-locali-storici-georeferenziati-nel-comune_puf6-2m2d.json"),
 ("mi_20240502.csv", "20240502161336", C + "ds612_elenco-attivita-storiche-e-di-tradizione-nel-comune-di-milano_d5uj-xwht_final.csv"),
 ("mi_20241130.json", "20241130074808", J + "ds612_elenco_attivita_storiche_d5uj-xwht_final.json"),
 ("mi_20250421.csv", "20250421092119", C + "ds612_elenco_attivita_storiche_d5uj-xwht_final.csv"),
 ("mi_20260207.json", "20260207044646", J + "ds612_elenco_attivita_storiche_g4x3-hs9b_final.json"),
 ("reg_20240502.csv", "20240502164953", L + "rows.csv?accessType=DOWNLOAD"),
 ("reg_20240618.csv", "20240618180011", L + "rows.csv?accessType=DOWNLOAD"),
 ("reg_20250212.tsv", "20250212002458", L + "rows.tsv?accessType=DOWNLOAD"),
 ("reg_20251207.tsv", "20251207032115", L + "rows.tsv?accessType=DOWNLOAD"),
]
log = []
for nome, ts, url in voci:
    if os.path.exists(f"{raw}/{nome}") and os.path.getsize(f"{raw}/{nome}") > 100:
        continue
    u = f"https://web.archive.org/web/{ts}id_/{url}"
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=120).read()
            if b[:5].lower() == b"<html": raise RuntimeError("html/offline")
            open(f"{raw}/{nome}", "wb").write(b)
            print(nome, len(b)); break
        except Exception as e:
            print(nome, "tentativo", t, e); time.sleep(10)
    time.sleep(3)
with open(raw + "/download_log.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["file", "timestamp_wayback", "url_originale", "byte", "sha256_16", "scaricato"])
    for nome, ts, url in voci:
        p = f"{raw}/{nome}"
        if os.path.exists(p):
            b = open(p, "rb").read(); w.writerow([nome, ts, url, len(b), hashlib.sha256(b).hexdigest()[:16], datetime.date.today().isoformat()])
