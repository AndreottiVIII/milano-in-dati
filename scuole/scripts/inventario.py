"""Inventario delle fonti scaricate. Uso: python -I -X utf8 inventario.py <abs scuole>"""
import sys, glob, json, os, re, csv
import pandas as pd
S = sys.argv[1]; RAW = f"{S}/raw"; OUT = f"{S}/pulito"
rows = []
# MIM: per prefisso
log = pd.read_csv(f"{RAW}/miur/download_log.csv")
log["prefisso"] = log.file.str.extract(r"^([A-Z]+)\d")[0]
log["anno_inizio"] = log.file.str.extract(r"^[A-Z]+(\d{4})\d{2}\d{8}\.csv")[0].astype(float)
NOMI = {"ALUCORSOETASTA": "Studenti per anno di corso e fascia di eta - statale (DS0010)", "ALUCORSOETAPAR": "Studenti per anno di corso e fascia di eta - paritaria (DS0020)",
        "ALUCORSOINDCLASTA": "Studenti per anno di corso, classe e genere - statale (DS0030)", "ALUCORSOINDCLAPAR": "idem - paritaria (DS0040)",
        "ALUITASTRACITSTA": "Studenti primaria e secondaria per cittadinanza - statale (DS0050)", "ALUITASTRACITPAR": "idem - paritaria (DS0060)",
        "INFANZIAETASTA": "Infanzia per fascia di eta - statale (DS1116)", "INFANZIAETAPAR": "Infanzia per fascia di eta - paritaria (DS1117)",
        "INFANZIACLASTA": "Infanzia classi e bambini per genere - statale (DS1114)", "INFANZIACLAPAR": "Infanzia classi e bambini per genere - paritaria (DS1115)",
        "INFANZIASTRACITSTA": "Infanzia per cittadinanza - statale (DS1118)", "INFANZIASTRACITPAR": "Infanzia per cittadinanza - paritaria (DS1119)",
        "SCUANAGRAFESTAT": "Anagrafe scuole statali (DS0400)", "SCUANAGRAFEPAR": "Anagrafe scuole paritarie (DS0410)", "EDIANAGRAFESTA": "Edilizia scolastica: elenco e localizzazione edifici (DS0200)"}
for pref, g in log.groupby("prefisso"):
    nrows = 0; mil = None
    for f in g.file:
        with open(f"{RAW}/miur/{f}", "rb") as fh: nrows += sum(1 for _ in fh) - 1
    rows.append(dict(fonte="MIM dati.istruzione.it/opendata", dataset=NOMI.get(pref, pref), file_prefisso=pref, file=len(g), anni=f"{int(g.anno_inizio.min())}/{str(int(g.anno_inizio.min())+1)[2:]} - {int(g.anno_inizio.max())}/{str(int(g.anno_inizio.max())+1)[2:]}" if g.anno_inizio.notna().any() else "vari",
                     righe_nazionali_totali=nrows, byte=int(g.bytes.sum()), licenza="IODL 2.0 (Italian Open Data License v2.0), http://www.dati.gov.it/iodl/2.0/", scaricato=g.downloaded.max()))
# Comune
cl = pd.read_csv(f"{RAW}/comune_download_log.csv")
for ds, g in cl.groupby("dataset", sort=False):
    meta = json.load(open(f"{RAW}/comune_{ds}/_metadati.json", encoding="utf-8"))
    nrows = 0
    for f in g.file:
        if f.endswith(".csv"):
            with open(f"{RAW}/comune_{ds}/{f}", "rb") as fh: nrows += sum(1 for _ in fh) - 1
    rows.append(dict(fonte="Comune di Milano dati.comune.milano.it", dataset=f"{ds}: {meta['title']}", file_prefisso=ds, file=len(g), anni=(lambda tc: (tc[0]["temporal_start"] + " .. " + tc[0]["temporal_end"]) if tc else "vedi titolo")(json.loads(meta["temporal_coverage"]) if meta.get("temporal_coverage") else None),
                     righe_nazionali_totali=nrows, byte=int(g.bytes.sum()), licenza=f"{meta.get('license_title')} (license_id {meta.get('license_id')}); frequenza {meta.get('frequency')}; metadata_modified {meta.get('metadata_modified','')[:10]}", scaricato=g.downloaded.max()))
DF = pd.DataFrame(rows)
DF.loc[DF.file_prefisso == "EDIANAGRAFESTA", "anni"] = "2015/16 (data 2016), 2017/18, 2018/19, 2020/21-2024/25 (8 file)"
DF.to_csv(f"{OUT}/inventario_fonti.csv", index=False, sep=";")
print(pd.DataFrame(rows)[["dataset", "file", "anni", "righe_nazionali_totali", "byte", "licenza"]].to_string())
