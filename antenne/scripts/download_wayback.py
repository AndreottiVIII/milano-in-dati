"""Scarica da Wayback Machine (id_ = file originale) le versioni storiche del dataset ds718 CASTEL del Comune di Milano.
Uso: python -I -X utf8 download_wayback.py <out_dir>
Pausa tra le richieste per non sovraccaricare archive.org."""
import sys, os, time, urllib.request, hashlib, csv
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
B = "https://dati.comune.milano.it/dataset/6be404a9-0c3c-46d0-b805-9c004b26dd19/resource/"
R_CSV = "9f5b3cb1-b2b7-47df-b9d1-c5207613ff05"; R_JSON = "5bf13308-f611-4f66-ac89-49b41ec554be"; R_GEO = "1145e629-271e-478c-a1cf-47c62cd0fb86"
items = [
 ("20200927204945", R_JSON, "ds718_ags_castel_30_layer_2_impianti___final.json"),
 ("20210122072959", R_JSON, "ds718_ags_castel_30_layer_2_impianti___final_.json"),
 ("20240502220135", R_CSV, "ags_castel_30_layer_2_impianti_20230124__final_-no_filter.csv"),
 ("20240515201511", R_CSV, "ags_castel_30_layer_2_impianti_-015146_4326_final.csv"),
 ("20240615072509", R_CSV, "ags_castel_30_layer_2_impianti_-015146_4326_final.csv"),
 ("20260224210805", R_CSV, "ags_castel_30_layer_1_impianti_-015146_4326_final.csv"),
]
log = []
for ts, rid, fn in items:
    url = f"https://web.archive.org/web/{ts}id_/{B}{rid}/download/{fn}"
    dest = os.path.join(out, f"wayback_{ts}_{fn}")
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/antenne (ricerca open data)"})
            data = urllib.request.urlopen(req, timeout=120).read()
            open(dest, "wb").write(data)
            log.append([ts, url, len(data), hashlib.sha256(data).hexdigest()[:16], "ok"]); print(ts, len(data)); break
        except Exception as e:
            print(ts, "tentativo", attempt, e); time.sleep(30 * (attempt + 1))
    else:
        log.append([ts, url, 0, "", "fallito"])
    time.sleep(15)
with open(os.path.join(out, "download_log.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["timestamp_wayback", "url", "byte", "sha256_16", "esito"]); w.writerows(log)
