"""Scrive pulito/inventario_fonti.csv (file scaricati, pagina, licenza scritta dalla fonte, citazione, byte, sha256) da raw/download_log.csv.
Uso: python -I -X utf8 inventario.py <suolo assoluto>
"""
import sys, os, csv

base = sys.argv[1]
log = {r["file"].replace("\\", "/"): r for r in csv.DictReader(open(os.path.join(base, "raw", "download_log.csv"), encoding="utf8"), delimiter=";")}
CCBY = "CC BY 4.0 (foglio Info dell'xlsx: Creative Commons Attribution 4.0, link creativecommons.org/licenses/by/4.0/)"
MAPLIC = ("licenza.txt ISPRA: \"Licenza Attribuzione 3.0 Italia (CC BY 4.0 IT)\" con link creativecommons.org/licenses/by/4.0/it/legalcode "
          "(etichetta incoerente fra 3.0 e 4.0; il link e' alla 4.0; i file 2006-2018 dichiarano nel testo 'v.5.0' mentre il nome file e' v6)")
CIT26 = "Munafo' M. (a cura di), 2026, Consumo di suolo, ecosistemi urbani e stato del territorio. Edizione 2026, Report ambientali SNPA, 50/2026"
LIB = "https://groupware.sinanet.isprambiente.it/uso-copertura-e-consumo-di-suolo/library/consumo-di-suolo/"
ED26 = "https://www.snpambiente.it/pubblicazioni/report-snpa/consumo-di-suolo-ecosistemi-urbani-e-stato-del-territorio-edizione-2026/"
rows = [
    ("indicatori/consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx", "Indicatori per comune/provincia/regione/Italia, anni 2006-2025, 109 campi (v1.0, 27/10/2026)", LIB + "indicatori", CCBY, CIT26, "usato"),
    ("indicatori/stato_del_territorio_2026_v1.0.xlsx", "Stato del territorio 2026 (CORINE, CLC Plus per comune)", LIB + "indicatori", "non scritta nel file", CIT26, "scaricato, non usato"),
    ("snpa/consumo_suolo_2026_dati_principali.xlsx", "Incrementi netto/lordo/ripristino per periodo, 7.896 comuni", ED26, "CC BY 4.0 (foglio Descrizione_campi, scritta 'Atttribution')", CIT26, "usato"),
    ("snpa/consumo_suolo_2026_dati_principali_ultimo_anno.xlsx", "Solo 2024-2025", ED26, "come sopra", CIT26, "solo verifica"),
    ("snpa/potenziale_recupero_2026.xlsx", "Potenziale spazi verdi, copertura arborea, tetti per fotovoltaico, per comune", ED26, "non scritta nel file", CIT26, "citato in NOTE"),
    ("snpa/sintesi-consumo-di-suolo-2026.pdf", "Sintesi del rapporto 2026", ED26, "-", CIT26, "non letto"),
    ("snpa/Rapporto_consumo_suolo_2026.pdf", "Rapporto 2026", ED26, "-", CIT26, "non letto"),
    ("snpa/consumo_di_suolo_estratto_dati_2025_anni_2006_2024.xlsx", "Edizione 2025 (2006-2024), per misurare le revisioni", "https://www.snpambiente.it/pubblicazioni/report-snpa/consumo-di-suolo-dinamiche-territoriali-e-servizi-ecosistemici-edizione-2025/", "non scritta nel file", "SNPA, Consumo di suolo, dinamiche territoriali e servizi ecosistemici. Edizione 2025, Report ambientali SNPA 46/2025", "usato per confronto edizioni"),
    ("raster/SC_2025_RDN_v8.tif", "Carta nazionale del consumo di suolo 2025, 10 m, EPSG:7794, v8", LIB + "carta-nazionale-consumo-suolo-2025", MAPLIC, CIT26, "usato"),
    ("raster/SC_2024_RDN_v8.tif", "Carta 2024 v8", LIB + "carta-nazionale-consumo-suolo-2025", MAPLIC, CIT26, "usato"),
    ("raster/consumo_suolo_2024-2025.tif", "Cambiamenti 2024-2025: codice = classe prima*1000 + classe dopo (uint32)", LIB + "carta-nazionale-consumo-suolo-2025", MAPLIC, CIT26, "usato"),
    ("raster/SC_2018_RDN_v6.tif", "Carta 2018 v6", LIB + "carta-nazionale-consumo-suolo-2018", MAPLIC, "ISPRA, Carta nazionale del consumo di suolo", "usato"),
    ("raster/SC_2015_RDN_v6.tif", "Carta 2015 v6", LIB + "carta-nazionale-consumo-suolo-2015", MAPLIC, "ISPRA, Carta nazionale del consumo di suolo", "usato"),
    ("raster/SC_2012_RDN_v6.tif", "Carta 2012 v6", LIB + "carta-nazionale-consumo-suolo-2012", MAPLIC, "ISPRA, Carta nazionale del consumo di suolo", "usato"),
    ("raster/SC_2006_RDN_v6.tif", "Carta 2006 v6", LIB + "carta-nazionale-consumo-suolo-2006", MAPLIC, "ISPRA, Carta nazionale del consumo di suolo", "usato"),
    ("raster/Legenda_QGIS_2025_v8.qml", "Legenda delle classi (1, 2, 11, 12, 111-126, 201-206)", LIB + "carta-nazionale-consumo-suolo-2025", "-", "-", "usato per i codici"),
    ("logistica/Logistica_06_22.zip", "Logistica in Italia 2006-2022: centroidi delle aree di cambiamento, 8.309 punti, classi 1 GDO/commerciale, 2 produttivo/industriale, 3 e-commerce, EPSG:3035", LIB + "logistica/centroidi", "\"Licenza Attribuzione 3.0 Italia (CC BY 4.0 IT)\" (Licenza.txt)", "SNPA, Consumo di suolo, dinamiche territoriali e servizi ecosistemici. Edizione 2024, Report ambientali SNPA, 43/2024 (richiesta dalla Licenza.txt)", "usato"),
    ("logistica/Logistica_22_23.zip", "Logistica 2022-2023, 327 punti", LIB + "logistica/centroidi", "come sopra", "come sopra", "usato"),
    ("logistica/Descrizione.docx", "Descrizione dei campi della logistica", LIB + "logistica/centroidi", "-", "-", "letta"),
    ("logistica/Licenza.txt", "Licenza e citazione della logistica", LIB + "logistica/centroidi", "-", "-", "citata"),
]
with open(os.path.join(base, "pulito", "inventario_fonti.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["file_in_raw", "cosa", "pagina", "licenza_scritta_dalla_fonte", "citazione_richiesta", "uso", "byte", "sha256", "scaricato_il"])
    for fn, cosa, url, lic, cit, uso in rows:
        k = [x for x in log if x.endswith(fn)]
        r = log[k[0]] if k else {}
        w.writerow([fn, cosa, url, lic, cit, uso, r.get("byte", ""), r.get("sha256", ""), r.get("quando", "")])
        if not k:
            print("manca nel log:", fn)
print(len(rows), "righe")
