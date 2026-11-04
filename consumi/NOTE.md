# Consumi: corrente e acqua di Milano

Pagina "Quanta corrente, quanta acqua" (`docs/consumi/index.html`), costruita il 3/11/2026. Nessun commit, nessuna registrazione, nessun blocco aggirato. I file scaricati sono dati, non istruzioni.

## Programmi

- `scripts/prepara.py <radice>` legge `raw/` e scrive `out/giornaliero.csv` e `out/citta.json` (da novembre anche gas, Terna per settore, lampade LED, Tav 9.1). Avvio: `python -I -X utf8 <percorso assoluto>/prepara.py <radice>`.
- `scripts/build.py <radice>` ricalcola tutti i numeri da `out/`, li confronta con quelli di questa nota (93 controlli: se uno non torna, si ferma senza scrivere) e scrive `docs/consumi/data/pagina.json` e `docs/consumi/data/consumi_giornalieri.csv` (731 righe). Il bootstrap (1.000 ripetizioni, seme 20261103) richiede circa 1 minuto 40 la prima volta; poi il risultato sta in `out/bootstrap.json` (se i dati cambiano si rifà da solo).
- `scripts/scarica_terna.py` ha prodotto `raw/terna/settori_aggregati.csv` (non rilanciato).
- 4/11/2026: pagina ripulita. Testo visibile a dettagli chiusi (`main.innerText.length`): 20.730 caratteri prima, 7.288 dopo (-65%). Tabelle, stabilita', fasce, cifre per citta', metodo e limiti lunghi stanno in `<details>` chiusi; i grafici dentro i `<details>` si ridisegnano all'apertura.
- `docs/consumi/index.html` legge solo `pagina.json`. JS puro, grafici in SVG a mano. Controllato nel Browser pane a 800 e a 375 px: nessuno scorrimento orizzontale (anche con le sezioni a scomparsa aperte), nessun errore in console. I tooltip di quattro grafici (giorni, caldo, città elettricità, acqua) sono stati provati con eventi mouse simulati: funzionano; non provati con il dito.

## Fonti, licenze, date di scarico (tutte scaricate il 3/11/2026, senza iscrizione)

Comune di Milano, dati.comune.milano.it, licenza `cc-by` nei metadati CKAN (versione non indicata; nel progetto la riga del Comune è CC BY 4.0). Metadati salvati in `raw/comune/meta_*.json`.

| File | Contenuto | Note |
|---|---|---|
| ds1574 (bdfc8120-...) | elettricità erogata da A2A al giorno, GWh, 2019-2020 | 731 righe, date tutte presenti, nessun doppione; i nomi dei giorni coincidono con le date; ultima modifica CKAN del file 14/4/2021 |
| ds1537 (ccf1f52e-...) | elettricità annua 2014-2018, GWh | "estrapolato dalla tavola 9.1 energia Istat", "dati 2018 provvisori"; il 2018 è scritto `6750.1.` (punto in più, letto come 6750,1) |
| ds523 (be9028dd-...) | pro capite 2000-2011: elettricità domestica (kWh), gas (m³), acqua fatturata domestica (m³) | unità dai metadati; solo citato nei limiti |
| ds1571 (6f2c8cc0-...) | acqua 2018 | "estrapolato dalla tavola 17 - GMA 2021 Istat": è lo stesso dato ISTAT del 2018, controllato uguale |

ISTAT, licenza CC BY 4.0 (come registrato nel progetto):

- `ENERGIA_serie_storiche-1.xlsx` (comunicato "Trasformazioni e innovazioni nei consumi elettrici delle città capoluogo, anno 2024", 2026/07) e il testo con nota metodologica (`raw/istat_pdf/`). Tav. 1.1, 1.3, 2.2, 3.2, 4.1, 4.2, 5.2, 6.x.
- `TAVOLE_AMBURB_2024.zip` (comunicato "Ambiente urbano, anno 2024", 9/9/2026): `ENERGIA_2024.xlsx` (Tav 6.3 elettricità in GWh, Tav 6.4 gas in milioni di m³) e `ACQUA_2024.xlsx` (Tav 1.1 e 1.2, fonte "Censimento delle acque per uso civile (dati provvisori)").
- Acqua degli anni intermedi, trovata senza iscrizione: `Tavole_GMA2021.xlsx` (Tav. 17, dati 2018), `Istat_Tavole_Censimento_acque_2020-21122022.xlsx` (Tav. 15 e 16, dati 2020; pubblicata il 29/12/2022; con la nota metodologica) e `Istat-GMA2024-Tavole.xlsx` (Tav. 5 e 6, dati 2022). Scaricato anche `Tavole_GMA2023.xlsx` (dati 2020-2021): non contiene volumi per città, non usato.

Temperature: `temperature/serie/serie_unica.csv` (stazione ARPA Lombardia Milano v.Brera, sensore 5897, CC0). Per il 2019-2020 la fonte è `BRERA_H` per 708 giorni e `VICINE_ARPA` (media delle stazioni ARPA vicine, per i giorni con meno di 20 ore valide) per 23 giorni. Le fonti ECA&D/Maugeri (licenza non commerciale) non entrano: servono solo giorni dal 2019. Massima e minima sono calcolate dalle letture orarie (la massima vera è un po' più alta). Nessun altro dato di temperatura usato.

Nuove fonti scaricate il 4/11/2026, senza iscrizione:

- Comune di Milano, `cc-by` nei metadati CKAN: ds1573 (376d8b11-434d-4d21-adcd-25aaab08f331), gas erogato da A2A al giorno, Smc, 2019-2020, 731 righe, ultima modifica del file 14/4/2021 (`raw/comune/ds1573.csv`, `meta_ds1573.json`); ds1576 (e07b64f8-5bb8-46e4-8b2a-ab87050a1238), "Transizione illuminazione: da tradizionale a led", numero di lampade (non lampioni) per anno 2002-2020 (`raw/comune/ds1576.csv`, `meta_ds1576.json`).
- Terna, centro download (https://dati.terna.it/download-center), Consumi, "Energia elettrica per settore", 2000-2024. **Licenza non indicata: nella pagina e in `docs/consumi/data/` solo somme annue per settore, con citazione; il file grezzo `raw/terna/` non si pubblica.** Comunicato del 5/1/2021 sulla riclassificazione, letto su MarketScreener (https://in.marketscreener.com/quote/stock/TERNA-S-P-A-135034/news/Terna-italian-electricity-consumption-data-increasingly-accurate-up-to-date-and-detailed-32122049/): "necessary interruption in the historical data"; il confronto con gli anni prima e' possibile solo per i macrosettori (Agricoltura, Industria, Servizi, Domestico) e "not completely"; non dice da che anno.
- ISTAT, `ENERGIA_2024.xlsx`, Tav 9.1 (consumo totale per provincia, 2017-2024), gia' nel pacchetto scaricato.

## Fattori di conversione (dal glossario del testo ISTAT 2024)

1 GWh = 86 tep. 1.000 m³ di gas = 0,819 tep. Controllo: GWh da tep/86 uguale alla Tav 6.3 (2018-2024) e al dataset del Comune ds1537 (2015-2018) a meno di 0,05; gas da tep/0,819 uguale alla Tav 6.4 (2018-2024). kWh per abitante = tep per 100 abitanti × 1.000.000 / 86 / 100.

## Risultati: dati giornalieri A2A 2019-2020

- Somme annue: 2019 7.116,7 GWh; 2020 6.399,3 GWh.
- Massimo 27/6/2019: 30,9 GWh. Quel giorno la massima a Brera è 36,9 °C: secondo giorno più caldo dei 731 (il primo è il 28/6/2019, 37,9 °C, con 30,8 GWh). Il massimo cade quindi in un giorno caldissimo. I dieci giorni di maggior consumo sono tutti feriali tra 26/6 e 25/7/2019, massime 34,8-37,9 °C.
- Minimo 16/4/2020: 12,3 GWh, ma isolato (il 15/4 14,2; il 17/4 14,1). Non spiegato: potrebbe essere un errore del dato. Nel lockdown i feriali stanno a circa 14-16 GWh (mediane settimanali).
- Mediane dei feriali: marzo 2019 18,7 (21 giorni); 1-21 febbraio 2020 19,8 (15 giorni); 23-27 marzo 2020 15,0: -20% su marzo 2019, -24% su febbraio 2020. Domeniche: marzo 2019 15,5 (5), 29/3/2020 13,1 (-15%). Luglio 2019 25,2; gennaio 2019 (dal 7) 21,7 (+16%). Luglio 2020 20,7; gennaio 2020 (dal 7) 20,5: il sorpasso dell'estate vale nel 2019, non si può generalizzare. Settimane più basse fuori dal lockdown: Pasqua 2019 16,1; agosto 2019 e Natale 2019 16,9: la buca di agosto non è la più larga.
- Ferragosto 11-19/8/2019: 18,0 19,3 17,7 16,9 15,5 16,2 15,8 16,0 18,5 (il 15/8: 15,5, il minimo della settimana, uguale alle domeniche di marzo 2019). Massima media in quei giorni 30,1 °C. Feriali 12-16 agosto (con il 15): mediana 16,9, -10% su marzo 2019.
- Festivi usati: 26 date nei due anni (1/1, 6/1, Pasqua e lunedì dell'Angelo, 25/4, 1/5, 2/6, 15/8, 1/11, 7/12, 8/12, 25/12, 26/12; Pasqua 21/4/2019 e 12/4/2020). Il 7 dicembre è Sant'Ambrogio.

## Risultati: il caldo (cuore della pagina)

Metodo. Giorni feriali non festivi: 507. Esclusi: 89 di lockdown e riaperture (24/2-30/6/2020), 29 della pausa di agosto (5-25 agosto, dove la corrente cala per le ferie, visibile nei dati settimanali), 14 delle feste di fine anno (24/12-6/1). Restano 375 giorni (232 del 2019, 143 del 2020); 17 hanno la temperatura da stazioni ARPA vicine.
Modello: GWh = a + giorno della settimana (lun-ven) + 2020 + b_caldo × max(0, T − T0) + b_freddo × max(0, T1 − T), con T0 e T1 scelte su una griglia (T0 ogni 0,5 °C, T1 ogni 1 °C, con T1 almeno 3 °C sotto T0) dove l'errore quadratico è minimo. Intervalli: bootstrap per settimane intere (1.000 ripetizioni, percentili 2,5 e 97,5; nel bootstrap la griglia di T0 è a passo 1 °C).

Risultati con la temperatura massima (tmax):

- Soglia del caldo T0 = 26,0 °C (bootstrap 24-28); soglia del freddo T1 = 18,0 °C (bootstrap 13-19). Nella fascia 18-26 °C la curva è piatta.
- Caldo: **+0,78 GWh per grado sopra 26 °C** (bootstrap 0,50-1,10), circa il 4% di un feriale mite (mediana 18,5 con massima 20-25 °C). Se si cerca la sola soglia del caldo (senza lato freddo): T0 = 28 °C, 0,93 GWh/°C.
- Freddo: +0,20 GWh per grado sotto 18 °C (bootstrap 0,16-0,33): più debole, e confuso con il buio invernale.
- R² 0,78 con la temperatura; 0,07 senza (solo giorno della settimana e anno). Correlazione di Pearson tmax-GWh: 0,40 su tutti i 375 giorni, 0,83 sui giorni sopra la soglia. Effetto 2020: -1,19 GWh a parità di tutto il resto. Giorno della settimana rispetto al lunedì: mar +0,18, mer +0,25, gio +0,20, ven +0,04.
- Con la temperatura media (tmean): T0 = 21,0 °C, T1 = 14,0 °C; +0,88 GWh per grado sopra 21 °C (bootstrap 0,53-1,11); freddo +0,26. R² più alto della tmax (0,82 contro 0,78).
- Fasce di tmax (mediana GWh, giorni): <5 °C 21,6 (10); 5-10 20,6 (54); 10-15 19,9 (70); 15-20 18,6 (83); 20-25 18,5 (53); 25-30 20,0 (50); 30-35 22,1 (44); ≥35 28,4 (11, di cui 9 del 2019). Con ≥35 °C: +54% rispetto alla fascia 20-25.
- Domeniche (72, senza feste, lockdown, agosto, fine anno): mediana 16,4 con tmax <20 °C (44), 16,0 tra 20 e 28 (13), 17,9 da 28 in su (15): differenza piccola, campione piccolo.
- Stabilità (tmax, GWh per grado): 0,78 (principale), 0,86 solo 2019, 0,85 2019 più 2020 prima del 24/2, 0,83 2019 più 2020 da settembre, 0,83 lockdown fino al 31/5, 0,89 lockdown fino al 31/7, 0,78 con le feste di fine anno, 0,81 senza tutto agosto, 0,71 senza i giorni con temperatura dalle stazioni vicine, **1,06 con la pausa di agosto dentro (e soglia 29 °C)**. Intervallo 0,71-1,06. Con la tmean: 0,79-0,96.
- Ferragosto contro il modello (adattato fuori da agosto): nei giorni di lavoro 12, 13, 14, 16/8/2019 il modello, con le loro temperature, prevede in mediana 21,6 GWh; misurati 17,3 (-20%). È una stima, non una misura dell'effetto delle ferie.
- Ipotesi di lavoro (non provata): i condizionatori. La pagina scrive che il legame è misurato, la causa no, e che i dati non dicono dove si usa l'elettricità. Non sono stati usati articoli per i numeri.

## Risultati: gas e freddo (ds1573, 4/11/2026)

Dati: 731 giorni, nessun buco, nomi dei giorni coerenti con le date, anno coerente con la data. Quattro righe (16-19 aprile 2020) hanno ".5" di Smc, le altre sono intere: non spiegato (il 16/4/2020 e' anche il minimo della corrente, pure non spiegato). Giorno piu' basso 15/8/2020, piu' alto 1/2/2019. Gas in milioni di Smc al giorno; mediane mensili da circa 7,3 (gennaio 2019) a 0,58 (agosto 2019).

Metodo: giorni feriali non festivi (507, lockdown compreso: il gas non ha l'esclusione del caldo), temperatura media del giorno (tmean) di Brera, gas = base + pendenza x max(0, T1 - T), T1 cercata su griglia 8-26 °C ogni 0,5, intervallo bootstrap per settimane intere (1.000 ripetizioni, seme 20261104, griglia 0,5). Non e' usato nessun periodo di accensione dei riscaldamenti.

- Soglia T1 = 19,0 °C (bootstrap 18,5-20,0); **+0,443 milioni di Smc per grado in meno** (bootstrap 0,407-0,474); base estiva 0,80 milioni di Smc; R2 0,92. Con la massima invece della media: soglia 25,5, 0,341 (altra grandezza, non confrontabile).
- Stabilita' (Smc per grado, tmean): solo feriali 2019 0,448; solo feriali 2020 0,439; senza lockdown e riaperture (24/2-30/6/2020; soglia 19,5) 0,432; senza i 17 giorni con temperatura da stazioni vicine 0,443 (490 giorni); sabati 0,433 (100); domeniche e feste 0,410 (124); tutti i 731 giorni con base per tipo di giorno 0,436. Il livello cambia con il tipo di giorno (base 0,80 feriali, 0,76 sabati, 0,70 domeniche e feste), la pendenza poco: per questo la tabella li tiene separati.
- Fasce di tmean (feriali, n, mediana milioni di Smc): <5 46, 7,47; 5-10 98, 6,07; 10-15 117, 3,99; 15-20 88, 1,12; >=20 158, 0,77. Con tmean <8 le mediane: feriali 6,71, sabati 6,32, domeniche e feste 6,30.
- Somme annue A2A: 1.150,4 (2019) e 1.146,7 (2020) milioni di Smc. ISTAT (Tav 6.4): 1.007,5 e 996,9 milioni di m3. Scarto +14,2% e +15,0%. Calo 2020: -0,3% (A2A), -1,1% (ISTAT). La causa dello scarto non e' stata cercata e non e' scritta.
- Ipotesi non provata: il gas serve in gran parte al riscaldamento; la pagina scrive solo "legame misurato, non spiegazione".

## Risultati: settori Terna dal 2000 (provincia di Milano + Monza e Brianza)

- Si somma sempre Milano + Monza: Terna separa Monza dal 2010 (2009 Milano 21.132; 2010 Milano 17.257 + Monza 4.259). Totale: 19.448 GWh (2000), massimo 21.977 (2008), 19.644 (2020), 20.182 (2024). Il totale (con agricoltura, 50-87 GWh) non dipende dalle categorie.
- La sola provincia di Milano coincide con ISTAT Tav 9.1 per 2017-2024: entro 0,05 GWh dal 2018, 0,4 nel 2017 (16.686,8 contro 16.687,2). 2024: 15.971,3 (controllo in build.py).
- Rottura delle categorie tra 2018 e 2019, dedotta dai dati (Terna non dice l'anno): servizi 9.818 -> 9.091 (-7%), industria 6.478 -> 6.961 (+7%), case 4.786 -> 4.848 (+1%), totale -1%. Controllo mio sul numero di voci per anno nel file (4/11/2026): 2017 11.849, 2018 11.899, 2019 100.468, 2020 105.774, 2021 428, 2024 428. Il grafico interrompe industria e servizi tra 2018 e 2019; confronti di lungo periodo solo fino al 2018: industria 8.782 -> 6.478, servizi 6.202 -> 9.818, case 4.414 -> 4.786. Nessuna causa data.
- Coincidenza osservata, non spiegazione: la nascita di Monza nei dati Terna cade nel 2010, lo stesso anno del salto ISTAT non spiegato del comune di Milano (vedi sotto). Gli usi domestici ISTAT non cambiano e il comune non perde territorio, quindi non e' una spiegazione. Non nella pagina.

## Risultati: lampade (ds1576)

2002-2020 senza buchi (19 anni). Tradizionali + LED: 2002 113.277 + 0; 2013 141.963 + 0; 2014 65.503 + 77.774; 2020 1.557 + 151.409. Totale 113.277 -> 143.277 (2014) -> 152.966 (2020), non scende mai; i LED non scendono mai; salto maggiore del totale +4.460 (2003). Quota LED 54,3% (2014), 99,0% (2020). Cosa strana: i LED passano da 0 a 77.774 in un solo anno (2013-2014): potrebbe essere l'anno in cui il Comune comincia a contarli. Il dato conta lampade, non energia: non si dice quanta se ne e' risparmiata.

## Risultati: negli anni (ISTAT)

- Elettricità, GWh: 2015 6.824,3; 2016 6.643,5; 2017 6.732,4; 2018 6.750,1; 2019 6.677,7; 2020 6.105,6; 2021 6.253,0; 2022 6.416,1; 2023 6.271,4; 2024 6.396,1 (il 2023 per Milano è dato "stimato" in alcune tavole).
- Per abitante (kWh): 5.070, 4.892, 4.906, 4.862, 4.766, 4.391, 4.590, 4.738, 4.595, 4.673. 2015-2024: -7,8%. 2020 su 2019: -8,6% (GWh).
- Quota non domestica 2022: 74%. Quota domestica 2023-2024 stimata da ISTAT.
- Gas (milioni di m³): 1.030, 1.030, 1.025, 1.036, 1.008, 997, 1.063, 922, 838, 882.
- Tra i 14 capoluoghi di città metropolitana, Milano è 3ª nel 2024 per kWh per abitante (Venezia 5.966, Catania 5.288, Milano 4.673, Bologna 4.304, Firenze 4.134...). Variazione 2015-2024 per abitante: da -9,9% (Roma, Cagliari) a +14,0% (Catania); Milano -7,8%.

### Il salto 2009-2010: non si spiega

- Tav 1.3: Milano 658.090 tep (2009) → 574.412 (2010), -13%. Gas (Tav 4.2) 704.919 → 994.317, +41%. Gli usi domestici (Tav 2.2) non cambiano (148.040 → 147.721), cioè tutto il salto sta negli altri usi (non domestico 510.050 → 426.691, -16%). Elettricità + gas insieme: 1.363.009 → 1.568.730 tep (+15%).
- Note in fondo alle tavole: solo le note (a) (utenze escluse), (b) (dato stimato), (*) (Cesena). Il comunicato/testo ISTAT 2024 e la nota metodologica parlano solo di una rottura nel 2014: "fino all'anno 2014 consumi fatturati, dal 2015 consumi effettivi (archivi Arera)", e per la serie dell'uso domestico di una rottura 2014 per riclassificazione delle tipologie di uso. Nulla sul 2010.
- Tra i 103 comuni capoluogo con elettricità e gas positivi in entrambi gli anni, solo Milano ha insieme calo dell'elettricità ≥10% e gas ≥+20% (Alessandria -19% elettricità, Venezia -16%, Taranto -11%; gas ≥+30%: Lodi +69%, Trapani, Sondrio, Rieti +31-36%, Milano +41%). Mediana delle variazioni 2009-2010 sui capoluoghi: circa +0,5% elettricità, +5,5% gas (calcolo fatto una volta fuori da build.py).
- Una ricerca web (una sola, senza trovare la tavola del 2010) non ha trovato spiegazioni. Non ho provato a leggere le vecchie edizioni ISTAT 2010-2011 (Dati ambientali nelle città): potrebbero spiegarlo.
- Scelta: la serie annua parte dal 2015 (non dal 2014): il 2014 è ancora "fatturato" e ISTAT lo ha rivisto (6.522,2 GWh nella serie attuale, 6.500,8 nel dataset del Comune). Mai una tendenza che attraversa 2009-2010 o 2014-2015.

### A2A e ISTAT non coincidono

Somme giornaliere A2A 7.116,7 (2019) e 6.399,3 (2020) contro ISTAT 6.677,7 e 6.105,6: +6,6% e +4,8%. Il calo 2020 su 2019: -10,1% (A2A), -8,6% (ISTAT). Il Comune dice solo "energia elettrica erogata da A2A ... nel Comune di Milano". ISTAT: consumi prelevati dalle reti di distribuzione, esclusi i punti collegati alla rete di trasporto nazionale ed escluso RFI (Tav 6.3). Le definizioni sono diverse, le note non dicono quale parte spieghi la differenza. Non è stata cercata una spiegazione fuori dalle note. Nella pagina non si mescolano mai le due serie in un grafico.

## Risultati: acqua (ISTAT, Censimento delle acque per uso civile)

Milano, l/ab/giorno (immessa, erogata), perdite, fatturata domestica:

| Anno | Immessa | Erogata | Perdite | Domestica | Note |
|---|---|---|---|---|---|
| 2018 | 426 | 365 | 14,3% | – | volumi 213.352 e 182.776 migliaia di m³; popolazione pre-revisione 2021 |
| 2020 | 399 | 346 | 13,5% | 265 | |
| 2022 | 413 | 358 | 13,4% | 274 | |
| 2024 | 403 | 358 | 11,1% | 272 | provvisorio; 201.950 immessa, 179.603 erogata, 179.185 fatturata, 136.157 domestica (migliaia di m³) |

- Le perdite ricalcolate da immessa ed erogata coincidono con quelle pubblicate in tutti e quattro gli anni.
- Dal 2018 al 2024: immessa -5% (213 → 202 milioni di m³), erogata -1,7% (183 → 180), per abitante l'erogata 365 → 358.
- Domestica 272 l/ab/g = 76% dell'erogata/fatturata; il resto, 86 l, per altri usi.
- 14 capoluoghi di città metropolitana: perdite 2024 di Milano 11,1% contro mediana delle altre 13 al 38,0% (la più bassa del gruppo, anche nel 2018). Erogata 2024 di Milano 358 (la più alta; mediana delle altre 210); domestica 272 (la più alta; mediana delle altre 143, intervallo 115-176). In 11 città su 14 la perdita è più bassa nel 2024 che nel 2018; salgono Reggio di Calabria, Palermo, Cagliari. Alcuni salti tra un anno e l'altro nelle altre città (Catania, 2022: immessa 402 contro 527-570 negli altri anni) non sono stati indagati.
- I litri per abitante dividono per i residenti: comprendono uffici, negozi, servizi, chi viene da fuori. Nel testo si distingue erogata da domestica.

## Altro controllato

- ds523 (2011): elettricità domestica 1.196,1 kWh per abitante; acqua fatturata domestica 83,1 m³ = 228 litri al giorno. Per confronto, l'elettricità domestica 2022 di ISTAT (1.674 GWh sui residenti impliciti) è 1.236 kWh per abitante: stesso ordine di grandezza, fonti diverse. Non unite nei grafici. L'acqua del 2024 (272 l) è più alta dei 228 del 2011: non confrontabile (fonte e definizioni diverse).
- Vibrazioni: la pagina legge `docs/vibrazioni/data/pagina.json` (lockdown -27%, Ferragosto feriali -19% su marzo 2019) e le mette in una tabella accanto alla corrente (-20% e -10% sugli stessi riferimenti), con l'avviso che sono due misure diverse.

## Limiti, cosa non torna, cosa non ho fatto

- Terna, dati a 15 minuti: non usati. Verificato il 4/11/2026 (dal proprietario) su https://dati.terna.it/download-center: Fabbisogno Italia ogni 15 minuti per zona di offerta (Nord, Centro-Nord ecc.), anni 2021-2026, senza iscrizione. Un dato per ora di Milano non e' stato trovato; la zona Nord e' molto piu' grande di Milano. (Corretto l'errore precedente sull'iscrizione.) Solo i settori annui 2000-2024 sono usati (vedi sopra).
- Niente consumi per quartiere, niente dato giornaliero dell'acqua, giornaliero della corrente solo 2019-2020.
- Il salto 2009-2010 resta senza spiegazione (vedi sopra).
- La differenza A2A-ISTAT resta senza spiegazione.
- Il 16/4/2020 resta senza spiegazione (corrente minima; stesse date delle 4 righe del gas con mezzi Smc).
- Gas: A2A contro ISTAT +14,2% e +15,0%, senza spiegazione; soglia 19 °C cercata dai dati (non e' un calendario di accensione).
- Terna per settore: momento della rottura dedotto, non dichiarato; non ho cercato il comunicato su altre fonti oltre MarketScreener; non ho verificato altre serie provinciali.
- Sono due anni; il 2020 è atipico anche fuori dal lockdown (l'effetto 2020 nel modello è -1,2 GWh). Non c'è un controllo sul clima degli anni (nessun confronto con altri anni).
- Il modello a due soglie ha soglie scelte dai dati: l'intervallo bootstrap le include, ma non è una verifica esterna. La soglia del freddo è molto incerta (13-19 °C).
- La pausa di agosto (5-25) è stata scelta guardando le mediane settimanali; non c'è un calendario ufficiale delle ferie.
- Non ho letto i vecchi comunicati ISTAT (2010-2011) né le note metodologiche del Censimento acque 2018/2022 (solo la nota 2020 è stata scaricata, non letta con attenzione). Non ho controllato se le definizioni dell'acqua sono identiche tra 2018, 2020, 2022 e 2024: ISTAT usa gli stessi nomi di colonna e lo stesso censimento, ma è un'assunzione.
- ISTAT 2023 "stimato" per alcune tavole; usi domestici 2023-2024 stimati.
- La pagina non è stata aperta su un telefono vero, solo con la dimensione 375 px del Browser pane. Non ho provato Safari.
- `docs/temi.json`, `JOURNAL.md`, `STATO_PROGETTO.md`, `docs/menu.js`, `docs/elenco/` e la pagina delle fonti non sono stati toccati: restano da fare (menu, tessera in home, riga in fonti.csv).
