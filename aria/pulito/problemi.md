# Aria: trappole dei dati (per la rubrica "trappole dei dati")

Elenco dei difetti trovati scaricando e pulendo i dati dell'aria di Milano. Ogni punto dice dove si vede.
Quelli del download (fase 1) sono dettagliati in `aria\NOTE.md`, sezione 6; qui sono quelli che contano per leggere le serie, più quelli trovati nella pulizia (fase 2).

## A. Cambi di stazione e di strumento (non sono cambiamenti dell'aria)

1. **Juvara e Pascal non sono la stessa stazione.** Juvara (ARPA 502, Comune 9) chiude l'11/06/2007 (NO2, polveri; SO2 e ozono arrivano a metà luglio 2007). Pascal (ARPA 705, Comune 2) apre il 16/06/2007 per NO2 e ozono, ma misura il PM10 già dal 21/04/2007. Distanza tra i due punti: circa 925 m (coordinate ARPA, `stazioni_storia.csv`). Nei 48 giorni in cui misurano insieme il PM10 (21/04-10/06/2007) le medie sono vicine (Juvara 33,1, Pascal 34,7 µg/m³, correlazione 0,82), ma il NO2 cambia livello: media annua Juvara 2006 = 68,8, Pascal 2008 = 49,5 (`riepilogo_annuale.csv`). Una linea unica Juvara+Pascal mescola due posti. Nel file pulito entrambe le stazioni hanno la bandiera `cambio_stazione` in ogni riga e nei grafici sono tratteggiate/separate.
2. **Le coordinate di Pascal divergono di 531 m** tra Comune (`qaria_stazione.csv`) e ARPA (registro `ib47-atvt`). Per la mappa si usa ARPA. Le altre otto stazioni differiscono di meno di 150 m (`stazioni_storia.csv`, campo `distanza_coordinate_m`).
3. **Chiusure nel 2017**: Abbiategrasso, Parco Lambro, Zavattari. Il Comune scrive 31/08/2017, il registro ARPA 30/07/2018, i dati ARPA finiscono con il 2016. Il 2017 esiste solo nel Comune: per NO2 solo come massimo orario (non come media), per CO e benzene (Zavattari) come valore giornaliero. Perciò le medie annue del NO2 di queste tre stazioni finiscono nel 2016.
4. **Il codice del sensore cambia con lo strumento.** Per gli inquinanti del file pulito c'è un solo sensore per stazione, quindi la serie non si spezza (controllo in `pulito\stazioni_sensori.csv`). I cambi di strumento ci sono per Black Carbon e ammoniaca (29001→20455, 20005→20465, 20004→20581, 20020→20484), che stanno fuori dal file principale.
5. **Polveri totali (PTS) e PM10 non sono la stessa cosa**: a Juvara le PTS finiscono il 12/02/1998 e il PM10 comincia il giorno dopo. Il nome dello strumento per il PM10 è "SM2005" in tutte le stazioni, ma i dati non dicono se il metodo è cambiato nel tempo.
6. **Gli inquinanti si spengono da soli**: CO a Liguria dal 03/10/2023, CO a Verziere dal 04/07/2011, benzene e SO2 in varie stazioni. L'assenza di un anno non significa che l'aria è pulita.
7. **Il PM10 a Marche parte solo nel 2018, il PM2.5 nel 2021**: i confronti "prima/dopo" 2012 e 2019 per queste due serie non esistono.

## B. Date, orari, unità

8. **La data del Comune è il giorno dopo la misura.** Spostando di -1 giorno il PM10 del Comune coincide con quello ARPA nel 99% dei giorni (`pulito\confronto_fonti.csv`: PM10 99,0%, PM2.5 99,1%, CO 96,2%, NO2 massimo orario 97,6% entro il 5%). Senza spostamento coincide solo nel 10%. Chi usa i dati del Comune senza spostarli sbaglia di un giorno.
9. **Il "valore giornaliero" del Comune non è la stessa statistica per tutti gli inquinanti** (non è scritto nei metadati, l'ho dedotto dal confronto): NO2 e ozono = massimo orario; CO = massimo su 8 ore; PM10 e PM2.5 = media; benzene = media (coincide entro 1 µg/m³ nell'89,7% dei giorni, meno degli altri). Per questo dal Comune si riempiono solo le statistiche corrispondenti: l'ozono non si può riempire (il Comune dà il massimo orario, l'indicatore ufficiale è il massimo su 8 ore).
10. **Ore "a fine ora"** nei dati orari ARPA: la riga delle 00:00 appartiene al giorno prima (il giorno "24:00"). Se si raggruppa per data senza spostare si sbagliano tutti i giorni. In 22 righe l'ora non è tonda (es. 16:00:03): arrotondate all'ora.
11. **Dato mancante = `-9999`** nei file ARPA (380.679 righe) e campo `stato` vuoto; il Comune lascia la cella vuota. Il dataset in tempo quasi reale (`ykhg-b8rs`) non ha nemmeno il campo `stato`: non l'ho usato (è un doppione non validato degli ultimi giorni).
12. **Unità**: µg/m³ per tutto tranne CO in mg/m³. I file del Comune non scrivono le unità. Nel registro ARPA gli apici/le lettere accentate sono rotte (`µg/m�`, `Citt�`): le unità nel file pulito sono scritte a mano.

## C. Buchi

13. **Dal 2016 il Comune pubblica solo i giorni feriali** (229-242 giorni per anno; 2019 completo). Chi calcola una media annua dal Comune per il 2016-2025 usa solo lunedì-venerdì. Nel file pulito i giorni presi dal Comune sono 4.836 su 337.417 e portano la bandiera `da_comune_data_spostata_-1g`; sono usati solo dove ARPA manca.
14. **Il dataset ARPA 2018-2025 (`g2hp-ar79`) non ha i dati di benzene a Marche e Pascal** (nemmeno chiedendoli direttamente). Il Comune li ha, ma solo nei giorni feriali: le medie annue 2018-2025 risultano sotto il 75% di giorni e non vengono mostrate. Stesso problema per Marche PM10 e PM2.5 2025 (Marche PM10 2025: 99 giorni, tutti dal Comune).
15. **Pascal NO2 2012**: 191 giorni di NO2 non sono in ARPA; il Comune li ha solo come massimo orario, non come media. Risultato: nel file pulito il 2012 di Pascal ha il massimo orario ma non la media giornaliera completa (completezza 45%). Il confronto Area C (gennaio 2012) perde così una stazione.
16. **L'anno in corso (2026) è parziale** (fino al 28/10): le medie di PM10 e NO2 sono più basse perché mancano novembre-dicembre, quelle dell'ozono più alte perché c'è l'estate. Nei grafici l'anno 2026 non c'è; è nel CSV con `anno_parziale = 1`.
17. **Regola del 75%**: un giorno vale se ha almeno 18 ore valide su 24 (per le medie mobili su 8 ore: almeno 6 ore su 8 per ogni media e 18 medie su 24 nel giorno). Un anno è "mostrato" se ha almeno il 75% di giorni validi. Il limite europeo per le medie annue chiede il 90% dei dati: qui è più largo, dichiarato. I conteggi dei giorni sopra soglia sono quindi **minimi** (i giorni mancanti non si contano).
18. **Buchi interni**: NO2 Marche ha un buco di 130 giorni; CO Senato 29 giorni; benzene Senato 2009 ha solo il 62% dei giorni (`riepilogo_annuale.csv`, campo `completezza_pct`).

## D. Doppioni e righe fantasma

19. **Doppioni** tra i dataset ARPA dove si sovrappongono (17 righe per sensore): tolti. **Righe vuote duplicate** nel Comune (56 coppie nei file 2021, 2022, 2025) e **segnaposto** (stazione-inquinante che non esiste, una sola riga vuota): tolti.
20. **Zeri nel Comune**: 24 per il benzene, 20 per il CO, 1 per il PM10. Gli zeri di PM10 (e PM2.5) sono scartati perché impossibili; benzene e CO a zero sono tenuti (possono essere sotto la soglia di rilevazione, non verificato).

## E. Cosa non si può dire

21. **Il tempo atmosferico pesa più di qualunque misura.** Le medie del PM10 in inverno dipendono dai giorni senza vento e senza pioggia. Non ho scaricato dati meteo: nessun confronto "prima/dopo" è una stima dell'effetto di una misura. Il "caso del Covid" e delle zone a traffico limitato mostra solo che i numeri sono cambiati.
22. **Le stazioni non sono un campione della città**: sono nove, con tipi di sito diversi (traffico, fondo urbano) che i dati scaricati non dichiarano. Il confronto "stazione peggiore" è un confronto tra punti, non tra quartieri.
23. **Il perimetro di Area C** (Senato e Verziere sembrano dentro, le altre fuori) è una mia lettura delle posizioni, non verificata sulla mappa ufficiale. Tutte le stazioni di Milano sono dentro Area B: per questo i "controlli" sono stazioni ARPA fuori Milano (Pioltello, Magenta, Sesto S. Giovanni, Rho, Cinisello), scaricate in fase 2 (`raw\arpa_controllo\`).
