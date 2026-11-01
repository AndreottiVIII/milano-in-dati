# Chi puo' permettersi di vivere dove: note (1 novembre 2026)

Idea: Mietenwatch (Berlino) e Furman Center (NYU). Regola: affitto <= 30% del reddito lordo. Confronti, non cause.

## Metodo
- Affitto: OMI abitazioni civili (e tipo economico), stato prevalente, valore centrale della forbice (loc_centro), euro/m2/mese, da `prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv`. Ogni civico residenziale (46.895, da `quartieri-che-cambiano/out/civici_collegamenti.csv`) riceve la zona OMI di OGNI semestre 2011-2024 (punto-in-poligono sui perimetri `prezzi-case/raw/geopoi/F205_*.json`); anno = media dei due semestri; NIL = media dei suoi civici. 40/60/80 m2 sono scelte nostre.
- Redditi: MEF per comune (`mef_comuni_2000_2024.csv`, Milano F205) per percentili di citta' 2011-2024; MEF per CAP (`mef_cap_2011_2024.csv`, solo 2011, 2015, 2019-2024) per i NIL: distribuzione del NIL = miscela delle distribuzioni dei CAP con pesi = quota di civici (`collegamento_cap_nil.csv`). Percentili da 7 classi con densita' lineare dentro la classe e media di classe = importo/contribuenti (classe <=0 unita alla prima; coda di Pareto oltre 120k per la quota "che ce la fa"). Classe oltre 120k mancante nei CAP 2023-24: contribuenti = reddito_complessivo_n - somma delle altre classi.
- Controllo: mediana di citta' vs `costo-vita/pulito/affitto_vs_reddito.csv` (interpolazione uniforme): differenza massima 1,9% su 14 anni.
- Quota = affitto mensile x 12 / reddito lordo annuo; "reddito per il 30%" = affitto x 12 / 0,30; "contribuenti che ce la fanno" = 1 - CDF di citta'.
- Conteggi: solo NIL con almeno 2.000 residenti 2024 (73 con quotazione; 69 senza i 5 del centro con CAP 20121/20122 >= 50% delle case).
- Airbnb: notti/mese per eguagliare l'affitto OMI di 60 m2 per zona (`affitti-brevi/pulito/confronto_affitto_notti_zone.csv`), media pesata sui NIL con `collegamento_omi_nil.csv` (zone 2026/1).

## Numeri principali (da `docs/permettersi/data/riepilogo.json`)
- Reddito mediano contribuente Milano: 19.944 (2011), 20.982 (2015), 22.050 (2019), 25.926 (2024) euro lordi; 25 percentile 9.640 / 10.020 / 10.443 / 12.493.
- 60 m2, reddito mediano: NIL dentro il 30% su 73: 42 (2011), 46 (2015), 52 (2019), 47 (2022), 18 (2024). 28 usciti dal 2015, 0 entrati. 40 m2: 66 (2015) -> 60 (2024); 80 m2: 21 -> 2.
- 25 percentile: 60 m2 mai sotto il 38% in nessun NIL e anno 2011-2024; 40 m2: 10 NIL (2015) -> 2 (2024).
- Reddito di quartiere (CAP), 60 m2: 50 su 69 (2015) -> 12 (2024); 38 usciti.
- Citta' intera, 60 m2, mediano: 34,5% (2011), 33,2% (2015), 33,8% (2022), 38,2% (2024).
- Affitto OMI medio civici: +13,5% 2015-2022, +25,0% 2022-2024 (+41,9% 2015-2024); reddito mediano +23,6%; FOI +19,7%.
- Reddito per stare nel 30% (60 m2, quartiere mediano): 18.936 (2015), 27.360 (2024); piu' caro Duomo 60.120; meno caro Gratosoglio 17.664. Contribuenti che raggiungono il reddito del quartiere mediano: 55% (2015), 47% (2024).

## La cosa piu' sorprendente
Fino al 2022 per il reddito mediano la situazione non era peggiorata (da 42 a 52 NIL dentro il 30% tra 2011 e 2019); in due anni (2022-2024) i NIL scendono da 47 a 18, ma e' soprattutto il salto delle quotazioni OMI 2023-24 (+25%), in parte aggiornamento delle stime dell'Agenzia.

## Limiti
OMI sono stime (non annunci, non contratti); salto 2023-24 e revisioni zone (55 -> 40 nel 2014, 42 nel 2024); zone != NIL; contribuenti != famiglie != inquilini; lordo, non netto; reddito di quartiere da CAP (CAP 20121/22 instabili: 5 NIL grigi); percentili da 7 classi (Q1 piu' incerto); Airbnb una fotografia 2026.

## Professioni (fonti ufficiali ARAN, scaricate e lette con un programma il 1/11/2026)
- Infermiere: CCNL Comparto Sanita' 2022-2024 (firmato 27/10/2025), Tabella 2a, pagina 106 del testo (107 del PDF): Area professionisti della salute e funzionari 24.918,93 euro x 12 + 13a = 26.995,51 dal 1/1/2024 (conferma il numero di LeggiOggi). Indennita' di specificita' infermieristica 80,73 euro/mese (Tabella 3), esclusa. PDF: https://www.aranagenzia.it/wp-content/uploads/2025/10/2025.10.27-CCNL-comparto-definitivo-3.pdf
- Docenti: CCNL Istruzione e Ricerca 2022-2024 (firmato 23/12/2025), Tabella A2 Scuola "segue", pagina 49 (51 del PDF), euro per 12 mensilita' + 13a: primaria 0-8 anni 22.420,48 (24.288,85 lordo), 15-20 anni 26.873,83 (29.113,32); laureato sec. II grado 0-8 24.268,28 (26.290,64), 15-20 30.341,15 (32.869,58). Valori letti con le coordinate delle celle (non solo il testo). PDF: https://www.aranagenzia.it/wp-content/uploads/2025/12/2025_12_23_COMP-IR_2022-2024.pdf
- NIL sotto il 30% nel 2024 (40/60/80 m2): infermiere 65/31/2, primaria inizio 56/9/1, primaria 15-20 69/44/2, sec. II inizio 64/20/2, sec. II 15-20 69/52/9.
- Autista: contratto privato, nessuna tabella ufficiale aperta trovata: non usato.
- I valori sono scritti in `scripts/pagina.py` (PROF_RAW) e finiscono in `dati.json`.

## Cosa non e' stato fatto
Nessun confronto con affitti da annunci; nessun reddito per nucleo familiare (solo "due redditi uguali" come moltiplicatore); nessun anno prima del 2011 (CAP) ne' dopo il 2024 (MEF).
