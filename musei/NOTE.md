# Filone "Musei" (musei/)

Fase 1 + pagina (`docs/musei/index.html`). Dati scaricati il 2 novembre 2026. Tutto ripetibile con i programmi in `scripts/` (vedi STATO.md).

## 1. Fonti e licenze

| Cosa | Fonte | Anni | Licenza | File |
|---|---|---|---|---|
| Visitatori mensili dei musei civici | Comune di Milano CKAN, ds575 "Musei: visitatori mensili per museo nel corso dell'anno" | 2007-2017 | CC BY | `raw/comune_milano/ds575_*.csv` |
| Incassi dei musei civici | Comune CKAN, ds577 | 2007-2017 | CC BY | `raw/comune_milano/ds577_*.csv` |
| Visitatori per museo e sede espositiva | Comune CKAN, ds160 | 1996-2010 | CC BY | usato solo per controllo (vedi sez. 3) |
| Musei statali a Milano (Brera, Cenacolo, Anfiteatro) | Comune CKAN, ds513 "Musei statali: visitatori ed introiti 1996-2024" (dati MiC) | 1996-2024 | CC BY | `raw/comune_milano/ds513_*.csv` |
| Milano Musei Card, Osservatorio Milano (ds650) | Comune CKAN, ds2727, ds650 | - | CC BY | scaricati, non usati (ds2727 = elenco musei della card, niente visitatori; ds650 = confronto con 4 citta', anni diversi) |
| Italia: visitatori e introiti siti statali | MiC, Ufficio di Statistica, statistica.cultura.gov.it, "Visitatori e introiti di musei, monumenti e aree archeologiche statali - Anno 2024", Tavole 1 (1996-2024), 2 (province), 3 (non usata), 7 (per sito), 8 (top 30) in xlsx | 1996-2024 | nessuna licenza scritta sulla pagina; statistica ufficiale pubblica, le stesse cifre sono ripubblicate dal Comune in CC BY | `raw/mic/MUSEI_TAVOLA*_2024-1.xlsx` |
| Musei riconosciuti della Lombardia | Regione Lombardia, pagina "I visitatori dei musei riconosciuti" (musei.regione.lombardia.it / regione.lombardia.it/.../red-visitatori-musei-riconosciuti) e PDF "Rilevazione visitatori 2024" | 2015-2025 | (c) Regione Lombardia, tutti i diritti riservati | `raw/regione_lombardia/Rilevazione_visitatori_2024.pdf` (NON pubblicare); in pagina solo totali e un estratto di 10 righe con fonte |
| Cifre dichiarate dal Comune | Italpress 19/1/2024, ANSA 18/12/2024, Finestre sull'Arte 29/6/2026 (primo Annual Report della Direzione Cultura) | 2023-2025 | stampa, solo cifre con fonte | nessun file |
| Regola della prima domenica gratuita | MiC, comunicato 23/12/2025 (cultura.gov.it/comunicato/28500) | - | - | - |

Rate: una richiesta per volta con pausa 3-5 s, User-Agent che dichiara chi siamo, nessuna registrazione, nessuna verifica superata. Log in `raw/download_log.csv`. Ricerche: `raw/ricerche/` (CKAN Comune: 9 parole chiave; catalogo Socrata Regione Lombardia: nessun dataset di visitatori dei musei per Milano; "Comune Bergamo - Visitatori ai musei civici" non e' Milano).

Non trovato: dati aperti dei musei civici dopo il 2017; visitatori per giorno (niente domeniche gratuite isolabili); Palazzo Reale/PAC come serie; MiC dati.cultura.gov.it senza CSV.

## 2. Controlli fatti (`pulito/controlli.txt`)

1. ds575: 1.616 righe, nessun doppione museo-anno-mese; nomi unificati (Storia Naturale / Museo Stor. Nat., S. Giov. / San Giov. in Conca).
2. ds513: in tutte le 79 righe paganti + non paganti = totale.
3. Tavola 7 MiC 2024: Brera (328.181 + 218.336 = 546.517) e Cenacolo (439.718 + 89.704 = 529.422) uguali a ds513; Tavola 2: provincia di Milano 1.081.661 = Brera + Cenacolo + Anfiteatro (5.722) del ds513.
4. Tavola 1: in tutte le righe visitatori degli istituti a pagamento + gratuiti = totale. Italia 2024: 60.850.091 visitatori (in linea con le circa 60,85 milioni dichiarate dal Ministero, citate dalla stampa).
5. ds160 vs ds575 (2007-2010): Acquario, Archeologico, Storia Naturale coincidono (poche differenze di poche migliaia); il Castello Sforzesco NO (ds160 mette nella riga "Castello" valori di sedi espositive, es. 42.331 nel 2008).
6. ds160 vs ds513: Brera e Cenacolo differiscono di poche migliaia in alcuni anni (1999, 2003, 2004, 2007) e nel 2009 sono scambiati.
7. Somma dei primi 10 musei lombardi a Milano (PDF regionale 2024): 4.060.275, coerente con "oltre 4 milioni" del testo.

## 3. Limiti dei dati (anche nella pagina)

1. I dati aperti del Comune sui musei civici finiscono nel 2017. Dopo: solo cifre di stampa (2023: 3.197.477 tra musei e mostre; 2024: circa 3 milioni; 2025: 1.774.510 musei + 949.812 mostre = 2.724.322), non confrontabili.
2. Perimetro 2007-2017: solo i musei elencati; senza Palazzo Reale, PAC, sedi di mostre, ne' musei di fondazioni e privati (Triennale, Pinacoteca Ambrosiana, Poldi Pezzoli, Museo Scienza, Duomo...).
3. Mesi mancanti: 29 museo-anno con meno di 12 mesi (Novecento 2010 = 1 mese, Mudec 2015 = 3 mesi, Museo di Milano 2009 = 8, ecc.).
4. ds160 non usato: mescola civici/statali/privati e sedi di mostre; zeri = dato mancante; nomi che cambiano.
5. "Gratuito/a pagamento" = etichetta per museo e anno; Planetario "non pervenuto" dal 2011. Quota di visitatori nei musei gratuiti 31% (2007) -> 12% (2017): effetto del passaggio a pagamento nel 2014 di Acquario, GAM e Museo di Milano (visitatori dei tre: 256.267 nel 2013 -> 225.055 nel 2014; non si dimostra una causa).
6. Siti statali: biglietti emessi; metodi di conteggio cambiati per alcuni (Pantheon 2010-2015 campione, Capodimonte dal 2018, Colosseo dal 2022, Gallerie nazionali dal 2024); numero siti 333 (1996), 479 (2019), 490 (2017), 453 (2024): totale Italia non omogeneo.
7. Introiti per visitatore pagante: calcolo nostro (introiti lordi / paganti), approssimato, prezzi correnti. Cenacolo 6,39 euro (2010) -> 14,32 (2024).
8. Regione Lombardia: numero di musei diverso ogni anno, alcuni contano le mostre ospitate; per la citta' di Milano cifre isolate che non tornano (2019: "poco piu' di 3.700.000" in 31 istituti; 2020: 1.092.995 = -77% sul 2019, cioe' circa 4.740.000): nessuna serie di Milano.
9. Visitatori = ingressi, non persone.
10. Brera 2009: salto isolato (203.843 -> 336.981), poi 250-290 mila fino al 2014; non spiegato nei dati.

## 4. Numeri principali

- Musei civici: 775.092 (2007) -> 1.546.212 (2017), +99,5%; senza Novecento e Mudec 1.210.158 (+56,1%); i due musei nuovi valgono il 44% della crescita. Castello Sforzesco 320.177 -> 485.979 (532.689 nel 2015). Incassi 0,63 -> 1,87 milioni di euro. Stagionalita': aprile 11,2%, marzo 10,7%, maggio 10,0%; luglio 6,3%, giugno 6,5%.
- Brera: 417.976 (2019), 111.727 (2020, -73%), 546.517 (2024, +31%). Cenacolo: 445.728, 132.223 (-70%), 529.422 (+19%). Italia siti statali: 54,8 milioni (2019), 13,3 (2020, -76%), 60,9 (2024, +11%); soli musei +32%.
- Brera 14a e Cenacolo 16o tra i siti statali a pagamento (Tavola 8). Milano (3 siti statali): 1.081.661 visitatori contro Roma 28,6 milioni, Napoli 8,6, Firenze 8,6, Torino 2,4. Quota di Milano sul totale statale: 1,6% (2019), 1,8% (2024).
- Non paganti: Brera 31,6% (1996), 42,2% (2019), 70,0% (2020), 40,0% (2024); Cenacolo 16,9% (2024); Italia (siti a pagamento) 32,2% (2019), 38,4% (2024).
- Regione Lombardia musei riconosciuti: 7.893.785 (2019), 1.962.253 (2020), 9.539.212 (2024), 10.083.017 (2025). Top 10 non statali 2024: Duomo 785.992, Triennale 683.069, Polo musei scientifici 606.065; 8 su 10 a Milano, 4.060.275 insieme.

## 5. La "sorpresa"

Nel 2024 Brera e il Cenacolo hanno piu' visitatori del 2019 (+31% e +19%) e il Cenacolo incassa molto piu' di Brera con meno visitatori (6,3 contro 3,7 milioni lordi); al Cenacolo gli introiti salgono del 272% dal 2010 contro +57% dei visitatori. I musei civici raddoppiano in dieci anni, ma il 44% della crescita viene da due musei nuovi.

## 6. Da fare / dubbi per il coordinatore

- Richiedere (o cercare) i dati 2018-2025 dei musei civici per museo: il Comune ha pubblicato solo il totale nel Report Cultura 2025; l'Annual Report della Direzione Cultura (PDF) non e' stato trovato; se Davide lo ottiene, si estende la serie.
- Il PDF e il testo della Regione hanno "tutti i diritti riservati": verificare se si vuole tenere il top 10 2024 in pagina (10 righe con fonte) o toglierlo.
- La pagina MiC non dichiara la licenza; se serve certezza, scrivere a statistica@cultura.gov.it.
- Domeniche gratuite non isolabili; eventuale confronto con i dati di Brera sul mese della prima domenica non esiste.
