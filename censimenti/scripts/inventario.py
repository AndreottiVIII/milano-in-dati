import csv, os, sys
root = sys.argv[1]
RAW = os.path.join(root, "raw")


def mb(p):
    p = os.path.join(root, p)
    if os.path.isfile(p):
        return round(os.path.getsize(p) / 1e6, 1)
    return round(sum(os.path.getsize(os.path.join(a, f)) for a, _, fs in os.walk(p) for f in fs) / 1e6, 1)


def mbp(prefix, must=""):
    d = os.path.join(RAW, "comune_ckan")
    return round(sum(mb("raw/comune_ckan/" + x) for x in os.listdir(d) if x.startswith(prefix) and must in x and os.path.isdir(os.path.join(d, x))), 1)


I = "https://www.istat.it/storage/cartografia/"
C = "https://dati.comune.milano.it/dataset/"
H = ["id", "fonte", "anno", "geografia", "contenuto_e_variabili", "url", "file_in_raw", "dimensione_mb", "righe_milano", "licenza", "note"]
R = [
    ["istat_pop_storica_1861_1991", "ISTAT volume Popolazione residente dei comuni, censimenti 1861-1991 (1994)", "1861-1991 (13 censimenti)", "comune",
     "popolazione residente ai confini del 20.10.1991 (tutti i comuni) e ai confini dell'epoca",
     "https://ebiblio.istat.it/digibib/Censimenti%20popolazione/Censimentipopolazioneresidentedal1861/RML0050288Pop_res_cens_1861_1991.pdf (oggi 403; copia da Internet Archive del 2026-10-06)",
     "raw/istat_volumi_storici/Pop_res_cens_1861_1991_ISTAT_via_wayback.pdf", mb("raw/istat_volumi_storici/Pop_res_cens_1861_1991_ISTAT_via_wayback.pdf"),
     "13 valori (riga 146 Milano, Tavola 3, pdf p.293)", "ISTAT: riproduzione autorizzata; sito ISTAT CC BY 4.0", "PDF con OCR, non una tabella; letta solo la riga di Milano"],
    ["istat_popolazione_legale_2011", "ISTAT volume popolazione legale XV censimento", "2011 (+ prospetti 1861-2011 per ripartizione)", "comune (2011)",
     "popolazione legale 2011 per comune", "https://www.istat.it/it/files/2012/12/volume_popolazione-legale_XV_censimento_popolazione.pdf",
     "raw/istat_volumi_storici/volume_popolazione-legale_XV_censimento_2011.pdf", mb("raw/istat_volumi_storici/volume_popolazione-legale_XV_censimento_2011.pdf"),
     "1 (1.242.123)", "CC BY 4.0", "la serie 1861-2011 nel volume e' solo per ripartizioni, non per comune"],
    ["comune_ds303", "Comune di Milano ds303 Censimenti storici 1861-2011: popolazione e superficie ai confini dell'epoca", "1861-2011 (14 censimenti; mancano 1891 e 1941)",
     "comune, confini dell'epoca", "popolazione e superficie km2", C + "ds303-popolazione-popolazione-superficie-storico-1861-2011",
     "raw/comune_ckan/ds303-popolazione-popolazione-superficie-storico-1861-2011/", mbp("ds303"), 14, "CC BY", "da qui pulito/popolazione_comune_1861_2021.csv"],
    ["comune_ds300_302", "Comune di Milano ds300/ds301/ds302 censimenti storici", "1881-2011", "comune",
     "popolazione per eta' singola e genere (1881-2011), per stato civile (1886-2011), famiglie per numero di componenti (1881-2011)",
     C + "ds300_popolazione-censimenti-storici-popolazione-per-eta-1881-2011 (e ds301, ds302)", "raw/comune_ckan/ds300*, ds301*, ds302*",
     round(mbp("ds300") + mbp("ds301") + mbp("ds302"), 1), "", "CC BY", "da verificare in fase 2 quali confini usano"],
    ["comune_ds1494_serie_calcolata", "Comune di Milano ds1494 popolazione calcolata dal 1880 (+ ds1495 nati vivi, ds2918 natalita e mortalita, ds73 per genere 1936-2024)",
     "1880-2025 annuale", "comune", "popolazione calcolata (non e' un censimento) annuale", C + "ds1494-popolazione-calcolata-nel-comune-di-milano-dal-1880",
     "raw/comune_ckan/ds1494*, ds1495*, ds2918*, ds73*", mbp("ds1494") + mbp("ds1495") + mbp("ds2918") + mbp("ds73"), "146 anni", "CC BY",
     "salto 1922->1923 (697.368 -> 826.469) = annessioni; copia in pulito/popolazione_milano_annuale_1880_calcolata.csv"],
    ["istat_sezioni_1991", "ISTAT basi territoriali + variabili CPA 1991 (Lombardia R03)", "1991", "sezione di censimento (5.583 con dati; 5.831 poligoni)",
     "207 colonne popolazione/famiglie/abitazioni/edifici (P1..), metadati nel file", I + "basi_territoriali/WGS_84_UTM/1991/R03_91_WGS84.zip ; " + I + "variabili-censuarie/dati-cpa_1991.zip",
     "raw/istat_sezioni_1991, raw/istat_variabili_cpa/dati-cpa_1991.zip", mb("raw/istat_sezioni_1991") + mb("raw/istat_variabili_cpa/dati-cpa_1991.zip"), 5583, "CC BY 4.0",
     "pulito/sezioni_1991.csv, variabili_1991.csv, geometrie/sezioni_1991_Milano.geojson (EPSG:32632)"],
    ["istat_sezioni_2001", "ISTAT basi territoriali + variabili CPA 2001", "2001", "sezione di censimento (5.983 con dati; 6.083 poligoni)", "204 colonne (P1..)",
     I + "basi_territoriali/WGS_84_UTM/2001/R03_01_WGS84.zip ; " + I + "variabili-censuarie/dati-cpa_2001.zip", "raw/istat_sezioni_2001, raw/istat_variabili_cpa/dati-cpa_2001.zip",
     mb("raw/istat_sezioni_2001") + mb("raw/istat_variabili_cpa/dati-cpa_2001.zip"), 5983, "CC BY 4.0",
     "pulito/sezioni_2001.csv, variabili_2001.csv, geometrie/sezioni_2001_Milano.geojson"],
    ["istat_sezioni_2011", "ISTAT basi territoriali + variabili CPA 2011 (sezioni, ACE, aree subcomunali, localita)", "2011", "sezione (6.017; 6.085 poligoni), ACE (86), municipi (9)",
     "circa 140 variabili: popolazione, eta', stato civile, cittadinanza, istruzione, occupazione, famiglie, abitazioni, edifici (P, ST, A, PF, E)",
     I + "basi_territoriali/WGS_84_UTM/2011/R03_11_WGS84.zip ; " + I + "variabili-censuarie/dati-cpa_2011.zip", "raw/istat_sezioni_2011, raw/istat_variabili_cpa/dati-cpa_2011.zip",
     mb("raw/istat_sezioni_2011") + mb("raw/istat_variabili_cpa/dati-cpa_2011.zip"), 6017, "CC BY 4.0",
     "pulito/sezioni_2011.csv, ace_2011.csv, aree_subcomunali_2011.csv, variabili_2011_*.csv, geometrie/sezioni_2011_Milano.geojson"],
    ["istat_sezioni_2021", "ISTAT basi territoriali 2021 + censimento permanente 2021 (indicatori per sezione)", "2021",
     "sezione 2021 (6.055 con indicatori; 7.095 in geometria), con municipio (COM_ASC1) e NIL (COM_ASC2)",
     "circa 120 variabili (P, ST, A, PF, E): popolazione, eta', cittadinanza, istruzione, occupazione, famiglie, abitazioni, edifici",
     I + "basi_territoriali/2021/R03_21.zip ; https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2021.zip (e Comuni_2021.zip)",
     "raw/istat_sezioni_2021, raw/istat_variabili_2021, raw/istat_variabili_2021_comuni",
     mb("raw/istat_sezioni_2021") + mb("raw/istat_variabili_2021") + mb("raw/istat_variabili_2021_comuni"), 6055, "CC BY 4.0",
     "pulito/sezioni_2021.csv (indicatori), sezioni_2021_base.csv (POP21, FAM21, ABI21, EDI21 su 7.095), variabili_2021.csv, aree_subcomunali_2021_*.csv, geometrie/sezioni_2021_Milano.geojson"],
    ["istat_cens_perm_2023", "ISTAT censimento permanente 2023, dati per sezione (Comuni_2023.zip, capoluoghi di Citta' Metropolitane)", "31.12.2023", "sezione 2021 (6.059)",
     "148 colonne: popolazione, eta', cittadinanza, istruzione, occupazione, famiglie, auto, abitazioni",
     "https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Comuni_2023.zip (regionale: Dati_regionali_2023.zip)", "raw/istat_variabili_2023", mb("raw/istat_variabili_2023"), 6059, "CC BY 4.0",
     "pulito/sezioni_2023.csv, variabili_2023.csv; totale 1.371.499 residenti. Il file regionale 2023 (261 MB) e' scaricato ma non estratto (Milano e' gia' in Comuni_2023)"],
    ["istat_attivita_economiche", "ISTAT Censimento industria e servizi per sezione: 1991 (cis), 2001 (cis i/u), 2011 (sce)", "1991, 2001, 2011", "sezione",
     "imprese/unita' locali/addetti per gruppo ATECO a 3 cifre", I + "variabili-censuarie/dati-cis_1991.zip, dati-cis_2001.zip, dati-sce_2011.zip", "raw/istat_variabili_cis",
     mb("raw/istat_variabili_cis"), "63.703 / 160.786 / 104.673", "CC BY 4.0", "pulito/sezioni_<anno>_attivita.csv; tracciati originali nei file estratti (1991 .txt, 2001 .rtf, 2011 .xls)"],
    ["istat_aree_subcomunali", "ISTAT aree subcomunali 2011 (ASC2011_WGS84) e 2021 (ASC_21)", "2011, 2021", "municipi, NIL, ACE (Milano)", "poligoni + tabelle",
     I + "basi_territoriali/aree-subcomunali-xls-shp/ASC2011_WGS84.zip ; https://www.istat.it/wp-content/uploads/2025/04/ASC_21.zip", "raw/istat_aree_subcomunali",
     mb("raw/istat_aree_subcomunali"), "9 municipi, 88 NIL (2021)", "CC BY 4.0", ""],
    ["istat_sezioni_kmz_43comuni", "ISTAT sezioni di censimento in kmz per 43 comuni (incl. Milano)", "non verificato", "sezione", "solo geometria kmz",
     I + "basi_territoriali/Sezioni-Censimento-kmz.zip", "raw/istat_sezioni_kmz_43comuni", mb("raw/istat_sezioni_kmz_43comuni"), "", "CC BY 4.0",
     "non aperto: gli shapefile bastano; tenuto per controllo"],
    ["istat_documentazione", "ISTAT note informative e metodologiche basi territoriali, RSBL, descrizione dati 2011", "1991-2023", "-", "tracciati, metodo",
     "www.istat.it/wp-content/uploads/... (vedi scripts/dl_istat.py)", "raw/istat_documentazione", mb("raw/istat_documentazione"), "", "CC BY 4.0", "manca Descrizione-dati-Pubblicazione-2016 (404)"],
    ["comune_microdati_1991", "Comune di Milano ds1636/1637/1638/1639 Censimento 1991 (residenti, non residenti, famiglie, abitazioni) + ds1635 collegamento sezioni", "1991",
     "un record per persona/famiglia/abitazione, con CodSez",
     "residenti: sesso, eta', stato civile, cittadinanza, istruzione, condizione e posizione professionale, settore, pendolarismo; 1.369.231 record = totale ISTAT",
     C + "ds1636-censimento-1991-popolazione-residente (e ds1635, ds1637-1639)", "raw/comune_ckan/ds163*", mbp("ds163"),
     "1.369.231 persone; 583.889 famiglie; 640.641 abitazioni", "CC BY", "zip con csv separato da ';'; CodSez coincide con il codice ISTAT per il 97% delle sezioni; non estratti"],
    ["comune_microdati_2001", "Comune di Milano ds1518-ds1526 Censimento 2001 (residenti, famiglie, abitazioni, edifici, dimoranti, pendolari) + ds1529 sezioni", "2001",
     "un record per persona/famiglia/abitazione, con CodSez", "come 1991 + spostamenti studio/lavoro; 1.256.211 record = totale ISTAT",
     C + "ds1518-censimento-2001-popolazione-residente (e ds1519-ds1529)", "raw/comune_ckan/ds15*", mbp("ds15", "censimento-2001"),
     "1.256.211 persone; 588.197 famiglie; 633.673 abitazioni", "CC BY", "CodSez coincide con ISTAT per il 99% delle sezioni; ds1529 collega sezione -> zone 9/20 e NIL"],
    ["comune_censimento_2011", "Comune di Milano: censimento 2011 per sezione (ds382-385), ACE (ds364), NIL e municipi (ds1447-1457, ds319-329), stranieri (ds386-389), pendolari (ds390-395), indicatori 1991-2001-2011 (ds361-366), popolazione legale (ds152)",
     "2011 (+ confronti 1991-2001)", "sezione, ACE, NIL, municipio, comune", "popolazione, famiglie, abitazioni, edifici, istruzione, lavoro, stranieri, pendolarismo",
     C + "ds382-... (elenco in raw/comune_ckan/pacchetti_censimento.json)", "raw/comune_ckan/ds3*, ds1447-1457, ds152", "(incluso nel totale comune_ckan)", "",
     "CC BY", "80 pacchetti, 353 file in tutto"],
    ["comune_geometrie_sezioni", "Comune di Milano ds98 (sezioni 2011), ds2845 (sezioni 2021), ds95 (ACE 2011)", "2011, 2021", "sezione, ACE", "geojson/shp/csv con centroidi",
     C + "ds98_infogeo_sezioni_censimento_localizzazione_2011c ; ds2845-territorio-localizzazione-delle-sezioni-di-censimento-anno-2021 ; ds95_infogeo_aree_censimento_localizzazione_2011c",
     "raw/comune_ckan/ds98_*, ds2845*, ds95_*", "", "", "CC BY", ""],
    ["strand9_nil", "Popolazione per NIL (strand 9, sola lettura)", "2000-2025", "NIL / quartiere", "caratteristiche e cittadinanza",
     "..\\citta-15-minuti\\raw\\comune_milano\\pop_caratteristiche_quartiere e pop_cittadinanza_quartiere", "(non copiato)", "", "", "CC BY", "solo riferimento"],
    ["BLOCCATI", "ebiblio.istat.it (volumi digitalizzati dei censimenti), 8milaCensus (serie 1951-2011 per comune ai confini 2011), esploradati SDMX API (popolazione per comune, censimento permanente annuale 2018-2024)",
     "-", "-", "-", "-", "-", "", "", "", "ebiblio e 8milaCensus rimandano a avvisi.istat.it (403); API SDMX senza risposta (timeout 120 s); Internet Archive CDX offline. Non aggirato."],
]
with open(os.path.join(root, "pulito", "inventario.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(H)
    w.writerows(R)
print(len(R))
