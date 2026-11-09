# Una città di studenti: note

Pagina nuova (bozza in bozze-grafici/universita-v2/, dati in docs/universita/data/). Non pubblicata, non nel menu.

## Fonti e licenze
- MUR, Ufficio di statistica, dati-ustat.mur.gov.it, dataset "Iscritti" (dati ANS, ago-ott 2026), IODL 2.0. File usati (in dati_grezzi/): 01 iscritti per anno, 02 per ateneo (dal 2000/01), 10 internazionali per ateneo (diploma estero, dal 2010/11), 14a residenza x sede corso x gruppo (dal 2010/11, senza telematiche, occorrenze <5 escluse), 18 ateneo x gruppo disciplinare, 14c (scaricato, non usato), 00 info (definizioni). robots.txt MUR: Crawl-Delay 10 s e /api/ vietato: scaricato solo /download/ con pausa 11 s (una sola chiamata iniziale all'API per leggere i nomi dei file, poi mai più).
- Comune di Milano, DS752 "Iscritti nelle università milanesi" 2017/18-2024/25, IODL 2.0 (la scheda CKAN dice "other-at" ma il testo cita IODL 2.0). Usato per i corsi 2024/25 e come controllo dei totali. robots.txt del portale restituisce una pagina di manutenzione, senza regole.
- ISTAT, limiti amministrativi 2021 generalizzati (regioni), CC BY 4.0, già in pendolari/raw.
- Residenti Milano 2024: docs/eta/data/eta.json (Comune, CC BY).

## Passi (universita/scripts/)
01_scarica.py, 02_elabora.py (scrive docs/universita/data/), 03_mappa.py (regioni semplificate). Python con -I -X utf8.

## Limiti e difetti trovati
- Serie MUR: scalino 2009/10-2010/11 (da indagine ad ANS), 2009/10 mancante per ateneo; in MUR 01 il 2000/01 e il 2001/02 hanno lo stesso valore (non usato: serie da file 02).
- Salti: Cattolica 2017→2018 -2.8k e 2020→2021 +6.8k, San Raffaele 2020→2021 raddoppia. Comune 2018/19 incompleto (Cattolica 27.7k): per le serie solo MUR.
- Nel CSV del Comune accenti e apostrofi sono U+FFFD; ricostruiti (davanti a lettera = apostrofo, altrimenti à). Nomi corso con maiuscole diverse sommati ignorando le maiuscole.
- Telematiche: 323k iscritti nel 2024, quasi tutte a Roma/Napoli: escluse dai confronti con l'Italia e tra città.
- 14a: 184.341 iscritti con corso in provincia di Milano (codice sede 215); Comune dice 186.099 con corso nel comune di Milano: definizioni diverse.
- Humanitas (Rozzano) fuori dai sette (2.193). Residenze universitarie e affitti studenti: nessun dato aperto trovato.
