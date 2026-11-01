"""Inventario delle fonti scaricate (contenuto, anni, righe, dimensione, licenza, data).
Uso: python -I -X utf8 inventario.py <assoluto matrimoni>"""
import sys, os, json, csv, glob
M = sys.argv[1]; RAW = os.path.join(M, "raw")
MANCA = {
 "ds1496": "Solo rito civile/religioso per anno: niente cittadinanza, eta', residenza. Civili 2024 = 2218 (refuso: altre fonti dicono 2018).",
 "ds138": "Solo rito e cittadinanza (nessuna eta', nessuno stato civile precedente, nonostante la descrizione). 2003-2020. Cittadinanza mancante in 69 matrimoni (2005-2010).",
 "ds132": "Solo rito e cittadinanza, 2011-2020. La descrizione dice 'celebrati a Milano' ma i numeri sono molto piu' alti dei celebrati: comprende nozze di residenti celebrate altrove.",
 "ds1947": "Solo rito e cittadinanza, 2021-2024; stessa struttura di ds138.",
 "ds1949": "Solo rito e cittadinanza, 2021-2024; stessa struttura di ds132. Il 2024 (3.655) sembra incompleto.",
 "ds1950": "Eta' in classi di 5 anni, marito x moglie, solo 2021-2024; niente rito, niente cittadinanza, niente stato civile precedente.",
 "ds1952": "Eta' in classi di 5 anni, solo 2021-2024, residenti; ha righe con eta' 'n.d'.",
 "ds398": "Solo unioni celebrate a Milano, classi di eta' di 10 anni; niente regime patrimoniale ne' stato civile prima dell'unione; nessuna informazione su scioglimenti di unioni.",
 "ds705": "Solo il 2018; record individuali anonimi (sesso, anno di nascita, cittadinanza). Niente anno di matrimonio, durata, figli, tipo di scioglimento. Solo coppie M+F.",
 "ds361": "Censimenti 1991/2001/2011; coppie miste e non coniugate solo per 2001 e 2011.",
}
rows = []
for f in sorted(glob.glob(os.path.join(RAW, "comune_ds*", "_metadati.json"))):
    d = json.load(open(f, encoding="utf-8")); folder = os.path.dirname(f); sid = os.path.basename(folder).replace("comune_", "")
    csvs = glob.glob(os.path.join(folder, "*.csv"))
    nrows = sum(sum(1 for l in open(c, "rb") if l.strip()) - 1 for c in csvs)
    rows.append(dict(id=sid, fonte="Comune di Milano, dati.comune.milano.it (CKAN package_show %s)" % d["name"], titolo=d["title"],
                     anni=(d.get("notes") or "").split("\n")[0][:160], righe=nrows, byte=sum(os.path.getsize(c) for c in csvs),
                     licenza="%s (%s)" % (d.get("license_id"), d.get("license_title")),
                     aggiornamento=d.get("frequency") or [e["value"] for e in d.get("extras", []) if "frequ" in e["key"].lower()],
                     modificato_catalogo=d.get("metadata_modified"), scaricato="2026-11-01", cosa_manca=MANCA.get(sid, "")))
I = {"ma1_q1_comune_milano_rito": ("MA1 q1", "Matrimoni per comune e rito 2004-2024, Comune di Milano", "Solo religiosi/civili. Niente eta' ne' cittadinanza per comune (le altre tavole ISTAT arrivano solo alla provincia). 2010: religiosi 1808, molto sopra la fonte del Comune (1139)."),
     "ma1_q1_italia_rito": ("MA1 q1", "Matrimoni per rito, Italia 2004-2024", ""),
     "ma1_q1_comuni_provincia_milano_rito": ("MA1 q1", "Matrimoni per rito di tutti i comuni della provincia di Milano 2004-2024 (non usato nelle tabelle pulite)", ""),
     "ma1_q3_indicatori_provincia_milano": ("MA1 q3", "Indicatori di nuzialita' provincia di Milano 2004-2024 (quozienti, % civili, % almeno uno straniero, secondi matrimoni)", "Provincia, non comune."),
     "ma1_q3_indicatori_provincia_monza": ("MA1 q3", "Idem Monza e Brianza", ""),
     "ma1_q3_indicatori_italia": ("MA1 q3", "Idem Italia", ""),
     "ma1_q3_indicatori_lombardia": ("MA1 q3", "Idem tutte le province lombarde (non usato)", ""),
     "ma1_q4_eta_media_sposi_provincia_milano": ("MA1 q4", "Eta' media degli sposi per stato civile precedente, provincia di Milano 2004-2024", "Provincia."),
     "ma1_q4_eta_media_spose_provincia_milano": ("MA1 q4", "Idem spose", ""),
     "ma1_q4_eta_media_sposi_italia": ("MA1 q4", "Idem Italia sposi", ""), "ma1_q4_eta_media_spose_italia": ("MA1 q4", "Idem Italia spose", ""),
     "ma3_q1_tipologia_coppia_provincia_milano": ("MA3 q1", "Matrimoni per cittadinanza degli sposi (tipologia di coppia), provincia di Milano 2004-2024", "Provincia."),
     "ma3_q1_tipologia_coppia_provincia_monza": ("MA3 q1", "Idem Monza e Brianza", ""), "ma3_q1_tipologia_coppia_lombardia": ("MA3 q1", "Idem Lombardia", ""), "ma3_q1_tipologia_coppia_italia": ("MA3 q1", "Idem Italia", ""),
     "ma3_q3_rito_tipologia_provincia_milano": ("MA3 q3", "Rito x tipologia di coppia, provincia di Milano", ""), "ma3_q3_rito_tipologia_italia": ("MA3 q3", "Rito x tipologia di coppia, Italia", ""),
     "ma4_q1_rito_serie_storica": ("MA4 q1", "Matrimoni per rito, Italia, serie storica 1930-2024", "Solo Italia."),
     "ma4_q3_tipologia_coppia_serie_storica": ("MA4 q3", "Matrimoni per tipologia di coppia, Italia 1996-2024", ""),
     "ma4_q4_sposi_classe_eta_serie_storica": ("MA4 q4", "Sposi per classe di eta', Italia dal 1865", ""), "ma4_q4_spose_classe_eta_serie_storica": ("MA4 q4", "Spose per classe di eta', Italia dal 1865", ""),
     "nu1_q1_primonuzialita_sposi_regioni": ("NU1 q1", "Tasso di primo-nuzialita' sposi, regioni 1981-2024", "Solo regioni."),
     "nu1_q1_primonuzialita_spose_regioni": ("NU1 q1", "Idem spose", ""),
     "nu1_q1_eta_media_sposi_primo_matrimonio_regioni": ("NU1 q1", "Eta' media al primo matrimonio, sposi, regioni", "Il 1983 del Piemonte e' 48,84 (impossibile): errore ISTAT, fuori dal periodo usato."),
     "nu1_q1_eta_media_spose_primo_matrimonio_regioni": ("NU1 q1", "Idem spose", ""),
     "nu1_q1_eta_media_sposi_primo_matrimonio_ripartizioni": ("NU1 q1", "Idem ripartizioni e Italia, sposi", ""), "nu1_q1_eta_media_spose_primo_matrimonio_ripartizioni": ("NU1 q1", "Idem ripartizioni e Italia, spose", ""),
     "uc4_q1_unioni_ripartizione": ("UC4 q1", "Unioni civili per ripartizione 2018-2024", ""), "uc4_q4_unioni_grandi_comuni_milano": ("UC4 q4", "Unioni civili nei grandi comuni: Milano, per sesso, 2018-2024", "Parte dal 2018 (2016-2017 solo dal Comune)."),
     "uc4_q4_unioni_grandi_comuni_totale": ("UC4 q4", "Unioni civili nei 12 grandi comuni, totale", ""),
     "uc2_q1_unioni_sesso_mese_provincia_milano": ("UC2 q1", "Unioni civili per sesso e mese, provincia di Milano 2018-2024", "Ogni anno ha 12 righe mensili piu' la riga 'Tutti i mesi' (non sommare tutte)."),
     "uc2_q1_unioni_sesso_mese_italia": ("UC2 q1", "Idem Italia", "Come sopra.")}
for f in sorted(glob.glob(os.path.join(RAW, "istat_demo", "*.json"))):
    n = os.path.basename(f)[:-5]; j = json.load(open(f, encoding="utf-8"))
    app, tit, manca = I.get(n, ("?", n, ""))
    rows.append(dict(id="istat_demo/" + n, fonte="ISTAT demo.istat.it, tavola %s (POST https://demo.istat.it/app/RPCCerca.php, pubblica, nessun login)" % app, titolo=tit,
                     anni=(j.get("caption") or "")[:120], righe=len(j["datatable"]["data"]), byte=os.path.getsize(f),
                     licenza="CC BY 4.0 (https://www.istat.it/it/note-legali, letta il 2026-11-01)", aggiornamento="annuale", modificato_catalogo="", scaricato="2026-11-01", cosa_manca=manca))
TIT = {"seriestoriche__tavola_1.5.xlsx": "Separazioni personali per provincia 2007-2024", "seriestoriche__tavola_2.5.xlsx": "Divorzi per provincia 2007-2024",
       "seriestoriche__tavola_1.1.xls": "Separazioni per regione 2007-2024", "seriestoriche__tavola_2.1.xls": "Divorzi per regione 2007-2024",
       "seriestoriche__tavola_1.2.xlsx": "Separazioni per 1.000 abitanti, regioni", "seriestoriche__tavola_2.2.xls": "Divorzi per 1.000 abitanti, regioni",
       "seriestoriche__tavola_1.3.xlsx": "Indicatori sulle separazioni 2015-2021 (durata procedimento, durata matrimonio, % coppie miste)", "seriestoriche__tavola_2.3.xlsx": "Indicatori sui divorzi",
       "seriestoriche__tavola_1.4.xls": "Separazioni per classe di eta' e regione", "seriestoriche__tavola_2.4.xls": "Divorzi per classe di eta' e regione"}
for f in sorted(glob.glob(os.path.join(RAW, "istat_sepdiv", "*"))):
    n = os.path.basename(f)
    prov = n.endswith(("1.5.xlsx", "2.5.xlsx"))
    rows.append(dict(id="istat_sepdiv/" + n, fonte="ISTAT demo.istat.it/data/sepdiv/ (file Excel pubblici)", titolo=TIT.get(n, "Tavola per distretto di Corte d'Appello / regione, anno " + n[:4]),
                     anni="2007-2024" if "seriestoriche" in n else n[:4], righe="", byte=os.path.getsize(f), licenza="CC BY 4.0 (https://www.istat.it/it/note-legali)",
                     aggiornamento="annuale", modificato_catalogo="", scaricato="2026-11-01",
                     cosa_manca="Provincia = provincia del tribunale o dell'ufficio di stato civile; 'valori assoluti stimati'; Monza e Brianza dentro Milano fino al 2009; niente comune; niente anni prima del 2007." if prov else ""))
with open(os.path.join(M, "pulito", "inventario.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter=";"); w.writeheader(); w.writerows(rows)
print(len(rows), "fonti")
for r in rows:
    if r["id"].startswith("ds"): print(r["id"], r["righe"], r["byte"], r["anni"][:100], "|", r["aggiornamento"], "|", r["modificato_catalogo"][:10])
