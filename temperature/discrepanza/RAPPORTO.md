# Perché la serie storica di Milano e il sensore ARPA di Brera non vanno d'accordo dopo il 2000

Data: 2026-10-29. Cartella: `temperature/discrepanza/`. I programmi sono in `scripts/`, i risultati in `out/`.
Tutti i numeri qui sotto sono medie di differenze giornaliere, in °C. Accanto a ogni numero c'è il file e la colonna da cui viene.

## In una riga

**A sbagliare è la serie lunga (Maugeri, quella di ECA&D/GHCN-D), non il sensore ARPA.** Da giugno 2001 la serie lunga diventa all'improvviso più calda di circa 2,5 °C, nel 2006 sale ancora di circa 1 °C, e già dal 1995 aveva cominciato a scaldarsi d'estate. Il sensore ARPA di Brera invece resta allineato con le altre stazioni di Milano. Per una serie unica: **Maugeri fino al 1994, ARPA Brera dal 1995**, con una piccola correzione (tabella in fondo).

## Come l'ho capito

Due serie che si allontanano non dicono, da sole, quale delle due si muove. Serve un terzo termometro. Ne ho usati due tipi:

1. **Tre altre centraline ARPA di Milano**: via Juvara (sensore 5909), via Marche (5911), piazza Zavattari (5920). Tutte dal 1989. Ho fatto la media delle tre ogni giorno e confrontato tutte le serie con questa media ("le vicine"). Programma `scripts/vs_vicine.py`.
2. **Linate** (aeroporto). Il file GHCN-D `ITM00016080` indicato **non esiste** (il server risponde "non trovato" e non è nell'elenco `raw/ghcnd/ghcnd-stations.txt`). Ho usato al suo posto NOAA GSOD, stazione 16080099999 "LINATE", 1975-2025, in `raw/gsod_linate/`. Ma Linate si è rivelato **poco affidabile** come metro: tutte le stazioni di città si spostano insieme di circa 2 °C rispetto a Linate tra il 1993 e il 1996 (`out/diff_annue_vs_LINATE.csv`, colonne `ARPA_5909_TX`, `ARPA_5911_TX`, `ARPA_5920_TX`, `BRERA_TX`: da circa 0 nel 1992 a circa -2 nel 1996). Quindi Linate l'ho usato solo per gli anni '80, quando non c'è altro.

### Prova 1 — Rispetto alle vicine, Brera sta ferma e Maugeri sale

File `out/diff_annue_vs_VICINE.csv` (media annua di "serie meno vicine"):

| anno | Maugeri, massime (`MAUGERI_TX`) | Brera ARPA, massime (`BRERA_TX`) | Maugeri, minime (`MAUGERI_TN`) | Brera ARPA, minime (`BRERA_TN`) |
|---|---|---|---|---|
| 1992 | -0,08 | -0,10 | -0,74 | 0,16 |
| 1994 | 0,10 | -0,21 | -1,00 | 0,19 |
| 1998 | 0,98 | 0,27 | -0,44 | 0,65 |
| 2000 | 0,60 | 0,00 | -0,26 | 0,37 |
| 2002 | 2,58 | -0,28 | 1,07 | 0,22 |
| 2004 | 2,72 | -0,09 | 1,75 | 0,41 |
| 2006 | 3,59 | 0,07 | 2,67 | 0,34 |
| 2007 | 3,33 | -0,04 | 2,53 | 0,30 |

Brera dal 1995 al 2007 resta tra -0,28 e +0,32 per le massime. Maugeri sale di 3,5 °C.

### Prova 2 — Il salto ha un giorno preciso: 21 giugno 2001

- La serie Maugeri ha giorni mancanti dal 7 all'11 giugno 2001 e il 20 giugno 2001; subito dopo cambia livello.
- `out/salto_2001_finestre.csv`: Maugeri meno Brera, massime, **+1,06** nei 30 giorni prima (21 maggio-19 giugno) e **+3,54** nei 30 giorni dopo (21 giugno-20 luglio). Minime: da **-0,80** a **+1,25**. Salto di circa +2,5 °C sulle massime e +2,0 sulle minime da un giorno all'altro. Il clima non fa questo: è un cambio di strumento o di fonte dei dati.
- Altri salti, da `out/diff_mensili_vs_VICINE.csv` colonna `MAUGERI_TX`: marzo-aprile 2006 (aprile 2005 +2,4, aprile 2006 +4,7); settembre 2007 **-2,0** (un mese "troppo freddo", poi ottobre 2007 manca del tutto).
- Prima ancora: dalla primavera 1995 Maugeri si scalda d'estate (giugno-agosto 1995-1999 tra +0,9 e +1,8 sulle massime, inverni attorno a 0). Una differenza solo estiva e solo diurna è il segno tipico di un termometro che prende troppo sole (schermo che invecchia o strumento nuovo).
- Non è un errore di "giorno sbagliato": le variazioni da un giorno all'altro coincidono al giorno 0, non a ±1 (correlazione 0,95-0,97 a giorno 0, -0,16/-0,18 a ±1; calcolo annotato in `STATO.md`).

### Prova 3 — Il sensore ARPA è calcolato bene

- Le righe con -999 hanno sempre `stato` vuoto: scartandole (tenere solo `stato` = `VA`) non resta nessun valore strano. Nessun -999 "scappa" nei calcoli.
- Massime e minime giornaliere ricalcolate in tre modi (giorni con almeno 20 ore; solo giorni con tutte le 24 ore; i valori già calcolati da ECA&D per Brera, fonte 180713/180712) danno lo stesso risultato: `out/diff_annue_vs_LINATE.csv`, colonne `BRERA_TX`, `BRERA24_TX`, `ECAD_BRERA_TX` (es. 2006: -1,01, -1,01, -1,00).
- Nessuna stazione ARPA ha valori copiati da un'altra (ore identiche sotto il 6% in tutti gli anni).

### Prova 4 — La serie "omogeneizzata" ECA&D ha preso per buono il pezzo sbagliato

`out/hom_meno_maugeri_periodi.csv` (omogeneizzata meno Maugeri): la serie omogeneizzata coincide con Maugeri dal **1° ottobre 2001** in poi (0,00), e **prima è più alta in tutti i periodi**: massime +1,82 (1835-1899), +2,20 (1900-1949), +2,73 (1950-1986), +2,35 (1995-2000); minime da +1,5 a +2,5.
Cosa vuol dire: il metodo di Squintu et al. prende il pezzo più recente come "giusto" e ci allinea tutto il resto. Qui il pezzo recente è proprio quello rovinato, quindi **tutta la storia dal 1781 al 2001 è stata alzata di circa 2-2,5 °C**. In più il salto è messo al 1° ottobre invece che al 21 giugno 2001, e il salto del 2006 non è corretto. **La serie omogeneizzata ECA&D di Milano non va usata.**

### Prova 5 — Anche il 1986-87 è sospetto (trasloco dell'osservatorio)

Prima del 1989 c'è solo Linate. `out/maugeri_meno_linate_mensile.csv`, colonna `MAUGERI_meno_LINATE_TX`: di solito tra 0 e +1,5; da **dicembre 1986 ad agosto 1987** tra **+2,8 e +4,7**, poi torna a +0,4 a settembre 1987. Nello stesso periodo la differenza tra massima e minima della serie Maugeri sale a 10-12 °C contro gli 8-10 abituali (`out/maugeri_escursione_mensile.csv`, marzo-agosto 1987). Coincide con il 1987, anno in cui l'osservatorio si sposta in piazza Duomo e a Brera parte la stazione automatica (Nimbus 49-50, già in `NOTE.md`). Da trattare a parte (riga 2 della tabella).

### Cosa dice la letteratura (cercato una volta)

- Gli articoli di Maugeri e colleghi (Climatic Change 53, 2002) completano e omogeneizzano la serie **solo fino al 1998** (è nel titolo: "Daily Milan temperature and pressure series (1763-1998)", https://air.unimi.it/handle/2434/16986). Il pezzo 1999-2008 dentro ECA&D è quindi un'aggiunta successiva, e **non ho trovato nessun documento** che dica da quale strumento o luogo venga.
- Frustaci e altri, EMS 2013 (abstract EMS2013-180, copia in `raw/letteratura_discrepanza/EMS2013-180.pdf`): la serie di Brera "è purtroppo colpita negli ultimi tempi da dati mancanti" e propongono di ricostruirla con stazioni vicine. Conferma che il pezzo recente è fragile.
- AGI, 10/9/2022 (https://www.agi.it/cronaca/news/2022-09-10/osservatorio-brera-sentinella-cielo-18004788/): dal 1987 a Brera c'è una stazione automatica, poi entrata nella rete ARPA Lombardia (senza data).
- Squintu et al. (Int. J. Climatol. 39, 1243-1261): correzione "a quantili" usando come riferimento i pezzi omogenei vicini (https://boris.unibe.ch/120719/).
- Ipotesi NON verificata: che dopo giugno 2001 i dati vengano da un altro punto di misura (per esempio un tetto come quello di piazza Duomo). Un tetto spiegherebbe massime più alte d'estate e notti più calde, ma non ho un documento che lo dica.

## Raccomandazione per la serie unica

Programma che la applica: `scripts/giunzione.py` → serie pronta in `out/serie_continua_1763_oggi.csv` (colonne `TX`, `TN`, `TG`, `fonte_usata`, `nota`), regole in `out/regole_giunzione.csv`, correzioni mese per mese in `out/giunzione_scarti.csv`.

| da | a | fonte | correzione da AGGIUNGERE |
|---|---|---|---|
| 1763-01-01 | 1986-11-14 | Maugeri (ECA&D 105248 / 105247 / 105249) | nessuna |
| 1986-11-15 | 1987-09-15 | Linate GSOD 16080099999 | riga "C" di `giunzione_scarti.csv`, mese per mese (in media TX +0,59, TN +2,13, TG +1,61) |
| 1987-09-16 | 1994-12-31 | Maugeri | nessuna |
| 1995-01-01 | oggi | ARPA Brera 5897, **solo i valori all'ora esatta (:00)** | riga "B" di `giunzione_scarti.csv`, mese per mese (in media TX -0,08, TN -1,43, TG -0,55) |

Note sulla tabella:
- Perché Maugeri fino al 1994 e non fino al 2001: dal 1995 Maugeri ha già il riscaldamento estivo (Prova 2). Fino al 1994 sta con le vicine.
- Perché la correzione per ARPA: la serie lunga e il sensore ARPA non sono lo stesso termometro. Le minime ARPA sono più alte di circa 1,4 °C, le massime quasi uguali. La correzione porta ARPA al livello della serie lunga, così la storia resta confrontabile. Calcolo (metodo B): (Maugeri meno vicine, 1992-1994) meno (Brera meno vicine, 1995-2007). Il confronto diretto Maugeri-Brera 1992-1994 (metodo A) dà TX +0,14, TN -1,07: la differenza tra i due metodi (0,2-0,4 °C) è il margine di incertezza della giunzione. Il metodo A è disturbato da estati 1992-1993 anomale di Brera.
- Controllo: la serie unita, confrontata con le vicine, resta piatta prima e dopo il 1995 (`out/verifica_giunzione.csv`, colonna `continua_meno_vicine_TX`: 1992-1994 tra -0,29 e +0,10; 1995-2007 tra -0,37 e +0,24).
- Giorni senza Brera dopo il 1995: riempiti con la media delle vicine più la differenza media dello stesso anno (358 giorni, `nota` = "riempito"). Restano 68 giorni vuoti.
- Se si vuole una versione senza correzioni mese per mese: TX -0,1, TN -1,4, TG -0,5 tutto l'anno.

## Cose non risolte

- **Brera dal 2008 al 2016 è più calda delle vicine** di 0,5-1,7 °C (massime) e poi torna come prima verso il 2017 (`out/brera_meno_singole_annue.csv`, colonna `BRERA_meno_ARPA_5909_H_TX`: 2005 +0,06, 2009 +1,19, 2012 +1,74, 2017 -0,17; simile con le altre). Rispetto a Linate invece resta più calda anche dopo (`BRERA_meno_LINATE_TG`: 2005 -0,07, 2009 +1,38, 2025 +1,06). Anche le vicine cambiano (Zavattari +1 °C dal 2020, `out/diff_annue_vs_VICINE_H_1989-2026.csv`, colonna `ARPA_5920_TX`). Non l'ho corretto: serve un'omogeneizzazione vera del periodo recente con più stazioni. Incertezza sul periodo recente: circa ±0,5 °C. **Aggiornamento**: analizzato con 10 stazioni in `RAPPORTO_2008_2016.md` (salto di Brera 11/12/2007-29/9/2016, circa +0,65 °C; correzione proposta, spenta).
- Il 1986-87 si appoggia solo a Linate (unica stazione disponibile).
- Prima del 1986 non ho controllato nulla: la serie è quella di Maugeri.

## Trappole dei dati trovate qui

1. **Il pezzo 2001-2008 della serie lunga ECA&D/GHCN-D di Milano è rotto**: +2,5 °C dal 21 giugno 2001, altro +1 °C dal 2006, settembre 2007 troppo freddo, ottobre 2007 mancante. Chi lo usa vede a Milano un riscaldamento finto di circa 3 °C in sei anni.
2. **La serie omogeneizzata ECA&D (STAID 173) alza di 2-2,5 °C tutta la storia di Milano dal 1781 al 2001**, perché si è allineata al pezzo rotto.
3. **ARPA cambia passo il 2014-03-19** (non nel 2021 come scritto in `NOTE.md`): da un valore all'ora a uno ogni 10 minuti, dentro il dataset `d4kj-kbpj`. Con i valori ogni 10 minuti le massime vengono più alte di 0,28 °C e le minime più basse di 0,10 °C (`out/campionamento_orario_vs_10min.csv`, colonne `dTX_mean`, `dTN_mean`, media 2014-2026). È un salto finto: per una serie lunga usare solo i valori all'ora esatta.
4. **Il codice Linate `ITM00016080` in GHCN-D non esiste.** Linate è in NOAA GSOD (16080099999), ma le sue massime e minime non sono stabili negli anni '90: non usarlo come metro.
5. **I dati ARPA fino al 1999 hanno meno cifre** (scalini di 0,08 °C nel 1995, 0,01 °C dal 2000). Non sposta le medie, ma i valori ripetuti di ora in ora sono il 5-7% fino al 1999 e meno dell'1% dopo.
6. **I primi anni ARPA (1990-1991) sono instabili**: Brera nel 1991 è +0,9 °C rispetto alle vicine tutto l'anno e torna normale nel 1992; nel 1990 Marche e Zavattari sono fuori di +1,8 e -1,6 °C. Non usarli per tarare.
