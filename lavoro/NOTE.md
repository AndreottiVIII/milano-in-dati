# Il lavoro quartiere per quartiere (lavoro/)

Fase 1 (analisi) e pagina `docs/lavoro/` fatte il 1-2 novembre 2026. Niente git, JOURNAL.md, docs/index.html, docs/menu.js non toccati. Tutti i numeri qui sotto escono da `out/analisi.txt` / `out/analisi.json` / `out/controlli.txt` (rifacibili).

## Fonti (nessun nuovo download: tutto riusato da censimenti/, quartieri-che-cambiano/)
- ISTAT, censimenti 1991, 2001, 2011 e censimento permanente 2021, 2023, dati per sezione di censimento (`censimenti/pulito/sezioni_<anno>.csv`; CC BY 4.0 secondo le note legali ISTAT; scaricati il 30/10/2026). Sezione -> NIL: `censimenti/pulito/sezioni_armonizzate.csv`. Quartieri "robusti" (66): campo `robusto` di `variazioni_NIL_1991_2023.csv`.
- Comune di Milano, record individuali 1991 (ds1636) e 2001 (ds1518), CC BY, scaricati il 30/10/2026: usati solo per due controlli sull'intera citta' (`out/micro_condizione_1991_2001.csv`).
- Reddito medio per contribuente 2024 per NIL: `quartieri-che-cambiano/out/indicatori_nil.csv` campo `reddito_2024` (MEF, CC BY 3.0, scaricato 1/11/2026, CAP -> NIL).

## Come si rifa
```
python -I -X utf8 scripts/01_micro_controllo.py <milano-in-dati>
python -I -X utf8 scripts/02_indicatori.py <milano-in-dati>
python -I -X utf8 scripts/03_analisi.py <milano-in-dati>
python -I -X utf8 scripts/pagina.py <milano-in-dati> <milano-in-dati>/docs/lavoro
```
(percorsi assoluti). `pagina.py` copia anche `scripts/pagina_template.html` in `docs/lavoro/index.html`: il testo legge i numeri da `docs/lavoro/data/*.json`.

## Definizioni (campo per campo)
| Indicatore | 1991 | 2001 | 2011 | 2021, 2023 |
|---|---|---|---|---|
| occupati | P61 (uomini P67) | P61 (P65) | P61 (P65) | P101 (P102, P103), solo 15-64 anni |
| forze di lavoro | P60 (uomini P69+P70) | P60 (P64) | P60 (P64) | non c'e' |
| in cerca di lavoro | P60-P61 (comprende prima occupazione) | idem | idem | non c'e' |
| studenti | P149 (P150) | P131 (P132) | P131 (P132) | non c'e' |
| pensionati | P151 "ritirati" (P152) | P133 (P134) | **P139** (P140) | non c'e' |
| casalinghe/i | P148 | P130 | P130 | non c'e' |
Residenti 15-64: somma P17-P26 (uomini P33-P42), donne per differenza.
Indicatore principale: **occupati ogni 100 residenti di 15-64 anni** (occupati di ogni eta' fino al 2011, solo 15-64 dal 2021). Disoccupazione = (forze di lavoro - occupati) / forze di lavoro. Studenti/pensionati/casalinghe ogni 100 residenti (casalinghe ogni 100 donne).

Verifiche aritmetiche (`out/controlli.txt`): nessun valore mancante o negativo; forze di lavoro >= occupati in ogni sezione; nel 2011 P139 coincide al numero con i ritirati ottenuti per differenza (P128-P130-P131-P135 = 289.498), quindi nonostante l'etichetta del tracciato ("percettori di reddito da lavoro o capitale") e' la voce "pensionati"; nel 1991 le colonne P65/P66 del tracciato sono etichettate male (sono "non attivi", non "attivi maschi"), non usate; nel 2001 P63 non esiste nel tracciato e P60 > P61+P62: uso P60-P61.

## Numeri principali (Milano, somma di tutte le sezioni)
- Occupati: 553.978 (1991), 544.229 (2001), 550.946 (2011), 613.520 (2021), 642.475 (2023). 1991->2011: totale -3.032; uomini -38.795 (330.899 -> 292.104), donne +35.763 (223.079 -> 258.842); residenti -127.108.
- Occupati ogni 100 residenti 15-64: 56,6 / 65,2 / 71,2 / 70,1 / 71,1. Uomini 69,5 / 74,7 / 77,7 / 75,2 / 75,7. Donne 44,4 / 56,2 / 65,0 / 64,9 / 66,3. Divario 25,2 / 18,5 / 12,7 / 10,3 / 9,3 punti.
- Disoccupazione: 9,5% (1991), 5,5% (2001), 6,9% (2011); donne 10,5 / 6,0 / 7,1, uomini 8,8 / 5,1 / 6,8.
- Casalinghe/i 227.501 -> 151.992 -> 81.743 (da 31,2 a 12,4 ogni 100 donne). Pensionati 233.342 -> 270.963 -> 289.498 (17,0 -> 23,3 ogni 100 residenti). Studenti 120.512 -> 69.746 -> 68.432 (nel 1991 il 9,4% sono 14enni).
- Donne 1991->2011, 66 NIL robusti: aumento in tutti, da +8,9 (Quinto Romano) a +26,6 punti (Rogoredo - Santa Giulia), mediana +20,5.
- Reddito 2024 (Spearman, 72 NIL con CAP stabili) con occupati 15-64: +0,56 (1991), +0,56 (2001), +0,63 (2011), +0,40 (2021), +0,33 (2023); con disoccupazione 2011 -0,63. Terzo piu' ricco / piu' povero nel 2011: 73,7 contro 67,5 occupati, disoccupazione 5,9% contro 8,5%; casalinghe ogni 100 donne praticamente uguali (12,0 e 12,8; 1991: 31,8 e 30,6).

## La cosa piu' sorprendente
**Milano ha quasi lo stesso numero di occupati residenti nel 1991 e nel 2011 (553.978 e 550.946) con 127.108 abitanti in meno, ma e' uno scambio: -38.795 uomini, +35.763 donne.** Dietro: le casalinghe scendono di 145.758 e in tutti i 66 quartieri confrontabili le donne occupate guadagnano almeno 8,9 punti.

## Limiti dei dati (quello che conta)
1. **Rottura 2011 -> 2021.** Tra i 66 NIL robusti la variazione 2011-2021 del tasso di occupazione e' fortemente legata alla quota di laureati 2011 (Spearman -0,79: terzo con piu' laureati -3,9 punti, terzo con meno +1,3), mentre 1991->2011 no (+0,33). Il Spearman tra le graduatorie e' 0,51 (2011-2023) contro 0,97 (2021-2023). Conclusione: **2021 e 2023 sono una serie a parte; nessun confronto NIL per NIL con il 2011**; a livello di citta' il tasso sembra quasi continuo (71,2 -> 70,1) ma non lo si interpreta. Non ho trovato nei documenti scaricati la definizione di "occupato" del 2021 (la nota ISTAT sul censimento permanente dice che le variabili tematiche sono stimate con modelli su indagini + registri, tra cui il Registro tematico del lavoro; `censimenti/raw/istat_documentazione` e nota censipop 2021 letta il 2/11/2026). Non spiego la causa.
2. 2021 e 2023: solo occupati 15-64 per sesso; mancano disoccupati, studenti, pensionati, casalinghe.
3. Fino al 2011 gli occupati includono i 65+: nei record del Comune sono il 2,1% (1991) e il 2,65% (2001) degli occupati; tasso "stretto" 15-64: 55,4 (1991) e 62,5 (2001) contro 56,6 e 65,2 delle tabelle ISTAT (2001: 0,9 punti per classificazioni diverse, oltre ai 65+). 2011 non misurabile.
4. 2001: occupati per sezione 544.229, condizione dichiarata nei record del Comune 536.332 (+1,5%); studenti 69.746 contro 74.013. 1991 coincide al numero. Il calo della disoccupazione 1991->2001 puo' essere in parte di definizione (non misurato).
5. Studenti 1991: contati dai 14 anni (11.286 14enni su 120.512).
6. Casalinghi uomini: 0 nel 1991 (record) e nel 2001 (per differenza); 3.236 nel 2011 (per differenza): sfalsamento lieve.
7. Piccoli NIL: 22 NIL non robusti sono grigi e fuori da confronti e graduatorie; tassi non calcolati con meno di 500 residenti 15-64 (disoccupazione: meno di 300 forze di lavoro). Quintosole 2011 (28,5% occupati) e' un valore chiaramente anomalo di un NIL piccolo.
8. Sezioni dei senza fissa dimora (2001: 1.225 persone, 2011: 266, 2021: 8.545, 2023: 10.038) fuori dai NIL, dentro il totale della citta'.
9. Residenti, non posti di lavoro. Reddito: del contribuente, per CAP, 2024; 4 NIL del centro senza reddito affidabile (CAP 20121/20122).
10. Niente dati prima del 1991 per NIL; nessuna validazione esterna del 2021 (non ho confrontato con altre fonti ISTAT).

## File
`out/`: `sezioni_lavoro.csv`, `lavoro_NIL.csv`, `lavoro_comune.csv`, `micro_condizione_1991_2001.csv`, `analisi.json`, `analisi.txt`, `controlli.txt`. Pagina: `docs/lavoro/index.html` + `data/` (dati.json, nil.geojson, riepilogo.json, nil_lavoro.csv, comune_lavoro.csv; 200 KB circa).
