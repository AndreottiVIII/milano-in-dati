"""Scrive pulito/inventario.csv. Lanciare da bilancio-comune/ dopo build.py"""
import pandas as pd, json, glob, os, re, csv
d = json.load(open('raw/search_all.json'))
LIC = 'CC-BY 4.0 (CKAN: cc-by) - riuso libero citando la fonte (Comune di Milano)'
META = {
 # id: (titolo breve, anni_consuntivo, anni_previsione, fase, dettaglio, unita, note)
 'ds227': ('Bilancio trasparente: spesa corrente per missioni e programmi', '2012', '2013 (assestato); 2014 (al 27/02/2014)', 'consuntivo + assestato + previsione', 'missione / programma (solo spesa corrente, solo nomi, niente codici)', 'MILIONI di euro, virgola decimale', 'Righe TOTALE di missione e generale incluse. Codifica ASCII (apostrofi/accenti persi).'),
 'ds284': ('PEG spese correnti, consuntivo 2013', '2013', '', 'consuntivo (impegni)', 'titolo / macroaggregato / missione / programma / centro di costo / voce economica (solo Titolo 1 spese correnti)', 'euro, virgola decimale', 'Nomi senza codici; accenti persi (es. COMPETITIVIT+).'),
 'ds285': ('PEG entrate correnti, consuntivo 2013', '2013', '', 'consuntivo (accertamenti)', 'titolo / tipologia / centro di costo / voce economica (solo titoli 1-3)', 'euro, virgola decimale', 'Include multe (AMMENDE PER CONTRAVV. 410,5 M), trasporto pubblico (376,2 M).'),
}
PEG = {  # id: (edizione, ultimo rendiconto)
 'ds397': ('2015-2019', (2015, 2016)), 'ds396': ('2016-2020', (2016, 2017)), 'ds399': ('2017-2021', (2017, 2018)),
 'ds400': ('2018-2022', (2018, 2019)), 'ds401': ('2019-2023', (2019, 2020)), 'ds1936': ('2020-2024', (2020, 2021)),
 'ds2352': ('2021-2025', (2021, 2022)), 'ds2738': ('2022-2026', (2022, 2023)), 'ds2956': ('2023-2027', (2023, 2024)),
 'ds3013': ('2024-2028', (2024, 2025)),
}
ENC = {'ds397': 'cp1252', 'ds399': 'cp1252', 'ds400': 'cp1252'}
NUM = {'ds397': 'it (3.800.930,47)', 'ds396': 'it (3.850,00)', 'ds399': 'it + "-" per zero', 'ds400': 'it (3.850,00)', 'ds401': 'en (19,406.40)'}
rows = []
for n, p in sorted(d.items()):
    m = re.match(r'(ds\d+)', n); did = m.group(1)
    if did not in META and did not in PEG: continue
    for r in p['resources']:
        fn = os.path.join(f'raw/ckan_{did}', r['url'].split('/')[-1])
        size = os.path.getsize(fn) if os.path.exists(fn) else ''
        nrow = ''
        if r['format'] == 'CSV' and os.path.exists(fn):
            nrow = sum(1 for _ in open(fn, 'rb')) - 1
        if did in PEG:
            ed, (r1, r2) = PEG[did]
            rows.append(dict(id=did, titolo=p['title'], formato=r['format'], anni_consuntivo=f'{r1}, {r2}', anni_previsione=f'{r2+1}, {r2+2}, {r2+3} (stanziamento di competenza); {r2+1} (stanziamento di cassa)',
                fase='consuntivo (rendiconto) + previsione (stanziamento)', dettaglio='entrate e uscite per capitolo PEG; missione/programma (solo uscite); titolo/tipologia/categoria/IV livello PdC (entrate)',
                unita='euro', colonne='Tipo; PDC-Missione/Programma/Livello1-4 (+descrizioni); Centro di costo; Capitolo (+Articolo/Numero fino a ds2956); Centro di responsabilita; Rendiconto A1; Rendiconto A2; Stanziamento A3..A5; Stanziamento cassa; Direzione',
                codifica=ENC.get(did, 'utf-8') if r['format'] == 'CSV' else '', separatore_numeri=NUM.get(did, 'punto decimale, nessun separatore migliaia') if r['format'] == 'CSV' else '',
                righe_dati=nrow, licenza=LIC, file_locale=fn.replace('\\', '/') if size != '' else '', byte=size, ultimo_aggiornamento_ckan=r.get('last_modified', '')[:10],
                url=r['url'], note='Rendiconto dello stesso anno ripetuto in 2 edizioni consecutive: valori identici (controllo_coerenza.csv). Edizione 2024-2028: capitoli rinumerati (9 cifre), colonne Articolo/Numero assenti.' if did == 'ds3013' else 'Rendiconto dello stesso anno ripetuto in 2 edizioni consecutive: valori identici (controllo_coerenza.csv).'))
        else:
            t, ac, ap, fase, det, un, note = META[did]
            rows.append(dict(id=did, titolo=p['title'], formato=r['format'], anni_consuntivo=ac, anni_previsione=ap, fase=fase, dettaglio=det, unita=un,
                colonne='', codifica='cp1252/ASCII' if r['format'] == 'CSV' else '', separatore_numeri='virgola decimale' if r['format'] == 'CSV' else '', righe_dati=nrow,
                licenza=LIC, file_locale=fn.replace('\\', '/') if size != '' else '', byte=size, ultimo_aggiornamento_ckan=r.get('last_modified', '')[:10], url=r['url'], note=note))
# famiglie / altre fonti (non tutte scaricate per intero)
sio = sorted(glob.glob('raw/ckan_siope_spese/*.csv')) + sorted(glob.glob('raw/ckan_ds738/*.csv')) + sorted(glob.glob('raw/ckan_ds739/*.csv'))
rows.append(dict(id='siope_spese', titolo='SIOPE - Spese comune di Milano (2017, 2018 annuali; mensili da set 2019 a lug 2025)', formato='CSV', anni_consuntivo='pagamenti (cassa) 2017-2025', anni_previsione='', fase='cassa (pagamenti), non competenza',
    dettaglio='codice SIOPE (natura economica), NON missione', unita='euro', colonne='codice_siope; descrizione; importo', codifica='ASCII', separatore_numeri='virgola decimale / punto misto', righe_dati='',
    licenza=LIC, file_locale='raw/ckan_siope_spese/ (+ ckan_ds738, ckan_ds739)', byte=sum(os.path.getsize(f) for f in sio), ultimo_aggiornamento_ckan='', url='dati.comune.milano.it (package_search "siope"), %d file CSV scaricati' % len(sio),
    note='Elaborazione AgID su dati SIOPE. Utile solo come controllo (pagamenti per natura), non per missioni. Mesi assenti nel catalogo: 2019-11, 2020-02/03/04, 2020-09/10, 2023-06, 2023-08, 2023-12; nessun dato oltre luglio 2025. Verificato con ricerca mirata.'))
for did, t, note in [('ds478', 'Imposta di soggiorno: soggetti passivi ed esenti 2014-2024', 'Pernottamenti, non euro.'), ('ds312', 'Redditi: variabili IRPEF e addizionale comunale e regionale - serie storica', 'Addizionale comunale dovuta in euro per anno d imposta (riferimento per la voce entrate addizionale IRPEF).'),
    ('ds697', 'PagoPA transazioni ed incassi', 'Incassi PagoPA mensili dal 2017 (canale di pagamento, non una voce di bilancio).'), ('ds633', 'Bilancio partecipativo 2017/2018', 'Non e un bilancio del Comune: progetti e utenti di una consultazione. Scaricato per completezza, da ignorare.')]:
    fl = glob.glob(f'raw/ckan_{did}/*.csv')
    p = [v for k, v in d.items() if k.startswith(did + '-') or k.startswith(did + '_')][0]
    rows.append(dict(id=did, titolo=t, formato='CSV', anni_consuntivo='', anni_previsione='', fase='non e bilancio', dettaglio='', unita='', colonne='', codifica='ASCII', separatore_numeri='', righe_dati='',
        licenza=LIC, file_locale=';'.join(f.replace('\\', '/') for f in fl), byte=sum(os.path.getsize(f) for f in fl), ultimo_aggiornamento_ckan='', url=p['resources'][0]['url'], note=note))
rows.append(dict(id='ds73_ds71', titolo='Popolazione calcolata ISTAT del Comune di Milano 1880-2024 (fine anno)', formato='CSV', anni_consuntivo='', anni_previsione='', fase='denominatore pro capite', dettaglio='totale comune', unita='abitanti',
    colonne='Anni; ...; Popolazione calcolata', codifica='ASCII', separatore_numeri='', righe_dati='', licenza=LIC, file_locale='raw/ckan_pop/', byte=sum(os.path.getsize(f) for f in glob.glob('raw/ckan_pop/*')), ultimo_aggiornamento_ckan='',
    url='dati.comune.milano.it ds71, ds73', note='Manca il 2025. Rottura del 2012 (censimento): vedi NOTE.md.'))
rows.append(dict(id='FOI_strand12', titolo='Indice prezzi FOI senza tabacchi, medie annue raccordate 2025=100 (ISTAT) - copiato da prezzi-case/pulito/foi_annuale.csv', formato='CSV', anni_consuntivo='', anni_previsione='', fase='deflatore', dettaglio='Italia, indice generale', unita='indice 2025=100',
    colonne='', codifica='utf-8', separatore_numeri='', righe_dati='', licenza='ISTAT, CC-BY 4.0', file_locale='pulito/indice_prezzi_annuo_FOI_da_strand12.csv', byte=os.path.getsize('pulito/indice_prezzi_annuo_FOI_da_strand12.csv'), ultimo_aggiornamento_ckan='',
    url='esploradati.istat.it (scaricato da strand 12)', note='Nazionale, non di Milano. Il Comune pubblica anche NIC Milano per gruppi di spesa (raw/ckan_nic), senza riga indice generale.'))
rows.append(dict(id='BDAP_ent_2013', titolo='BDAP Open Data: 2013 - Lombardia - Gestione finanziaria Entrate Enti Locali (estratto Comune di Milano)', formato='CSV', anni_consuntivo='2013 (anche 2014, 2015 non scaricati)', anni_previsione='', fase='consuntivo (accertamenti/riscossioni)',
    dettaglio='titolo / categoria / risorsa / IV livello, vecchia classificazione DPR 194', unita='euro', colonne='Esercizio; ente; Codice/Descrizione Titolo, Categoria, Risorsa, IV livello; Popolazione ISTAT; Accertamento in CC; Riscossione in CC; Riscossione in CR',
    codifica='cp1252', separatore_numeri='punto decimale', righe_dati='96', licenza='CC-BY (BDAP CKAN: cc-by)', file_locale='raw/bdap_campione/entrate_2013_MILANO_estratto.csv', byte=os.path.getsize('raw/bdap_campione/entrate_2013_MILANO_estratto.csv'), ultimo_aggiornamento_ckan='2017-12-04',
    url='https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/dc1c560d-4e7b-4a2b-9048-b96027c60099.csv', note='Scaricato il file Lombardia intero (46 MB, in streaming) e conservate solo le 96 righe di Milano. Contiene righe di totale (TOTALE ENTRATE TRIBUTARIE, titolo 07) da non sommare. Spese Enti Locali per la Lombardia NON sono su BDAP CKAN.'))
rows.append(dict(id='MININT_certificati', titolo='Ministero dell Interno - Finanza locale - Certificati di conto consuntivo, Comune di Milano (campione)', formato='HTML (una pagina per anno e quadro)', anni_consuntivo='1998-2015 verificati (1996: assente)', anni_previsione='', fase='consuntivo (impegni, pagamenti)',
    dettaglio='Quadro 3 riepilogo spese per titolo; Quadro 4 spese correnti per funzione/servizio x intervento; Quadro 5 investimenti', unita='euro', colonne='', codifica='utf-8', separatore_numeri='it', righe_dati='', licenza='non dichiarata sulla pagina (dati pubblici del Ministero dell Interno)',
    file_locale='raw/ministero_interno_campione/ (5 pagine: 1998 q3, 2003 q3, 2008 q4 e q5, 2015 q3)', byte=sum(os.path.getsize(f) for f in glob.glob('raw/ministero_interno_campione/*')), ultimo_aggiornamento_ckan='',
    url='https://finanzalocale.interno.gov.it/apps/floc.php/certificati/index/codice_ente/1030491450/cod/4/anno/{anno}/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/{quadro}', note='Titolo I 2015 = 2.793.159.486,27: coincide con PEG ds397 (2.793,2 M).'))
rows.append(dict(id='OPENBILANCI', titolo='OpenBilanci (Openpolis / Depp srl): bilanci dei Comuni', formato='sito web + dataset per comune', anni_consuntivo='2005-2015 (vecchio sito), dal 2016 nuovo sito', anni_previsione='preventivi fino al 2022', fase='preventivo e consuntivo',
    dettaglio='classificazione originale dei certificati del Ministero dell Interno', unita='euro', colonne='', codifica='', separatore_numeri='', righe_dati='', licenza='CC BY-NC-SA 4.0 (non commerciale, condividi allo stesso modo)',
    file_locale='', byte='', ultimo_aggiornamento_ckan='', url='https://openbilanci.it/pages/licenze', note='Nessuna API pubblica trovata (/api/ = 404). Rimette in forma gli stessi certificati gia raggiungibili dal Ministero: non serve.'))
pd.DataFrame(rows).to_csv('pulito/inventario.csv', index=False, sep=';', encoding='utf-8-sig')
print(len(rows))
