# -*- coding: utf-8 -*-
"""Scarica dal portale del Comune i file del dataset ds2914 (vie e mappe storiche) in vie-storiche/raw/.
Uso: python -I -X utf8 scarica.py"""
import json, os, urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(QUI), "raw")
UA = {"User-Agent": "milano-in-dati/1.0"}
API = "https://dati.comune.milano.it/api/3/action/package_show?id=ds2914-vie-di-milano-e-corrispondenza-toponomastica-nelle-mappe-storiche-dal-1884"


def prendi(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read()


os.makedirs(RAW, exist_ok=True)
meta = json.loads(prendi(API))["result"]
with open(os.path.join(RAW, "metadati.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
for r in meta["resources"]:
    nome = r["url"].rsplit("/", 1)[-1]
    dati = prendi(r["url"])
    with open(os.path.join(RAW, nome), "wb") as f:
        f.write(dati)
    print(nome, len(dati))
print("licenza:", meta.get("license_title"), "| ultima modifica:", meta.get("metadata_modified"))
