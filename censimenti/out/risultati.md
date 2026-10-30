# Risultati principali - filone 19, I censimenti (fase 2)

Tutti i numeri vengono da file in `pulito\` (ripetibili con gli script `h1`-`h9` in `scripts\`). "NIL" = i 88 Nuclei di Identità Locale del 2021; "NIL robusti" = 66 NIL con almeno 2.000 residenti nel 1991 e nel 2023 e con meno del 5% di differenza tra i due modi di assegnare le sezioni del 1991 e del 2001 (campo `robusto` in `variazioni_NIL_1991_2023.csv`); i 22 esclusi (parchi, cascine, Ortomercato, Farini, Tre Torri...) hanno 22.680 abitanti nel 1991 e 29.411 nel 2023 e le loro graduatorie non sono affidabili.

## Quanto è affidabile il raccordo sezioni -> NIL (`copertura_raccordo.csv`)

| Anno | Sezioni | Popolazione collocata in un NIL | Non collocata | Assegnazione ufficiale (Comune/ISTAT) | Pop. in sezioni dubbie (<90% dentro un solo NIL) |
|---|---|---|---|---|---|
| 1991 | 5.583 | 100% (1.369.231) | 0 | nessuna (solo municipio, ds1635) | 5,8% |
| 2001 | 5.983 | 99,90% | 1.225 (24 sezioni speciali) | 99,8% (ds1529 CodNIL) | 0,4% |
| 2011 | 6.017 | 99,98% | 266 (6 sezioni speciali) | no (sovrapposizione) | 0,1% |
| 2021 | 6.055 | 99,37% | 8.545 (1 sezione fittizia) | 100% (COM_ASC2) | 0 |
| 2023 | 6.059 | 99,27% | 10.038 (1 sezione fittizia) | 100% (COM_ASC2) | 0 |

Convalida: il municipio ottenuto per sovrapposizione coincide con la Zona9 del Comune per il 99,97% degli abitanti nel 1991 e il 100% nel 2001; il NIL per sovrapposizione coincide con il CodNIL del Comune per il 99,91% degli abitanti nel 2001. I nostri indicatori di comune coincidono con quelli pubblicati dal Comune (ds361, ds363, ds365, ds366) entro 0,1 punti, tranne il tasso di occupazione 2001 (+0,7) e l'età media (vedi sotto) (`convalida_indicatori_Comune.csv`).

## 1. Come è cambiata Milano quartiere per quartiere, 1991-2023 (NIL robusti)

- **Popolazione del comune:** 1.369.231 (1991) -> 1.256.211 (2001) -> 1.242.123 (2011) -> 1.349.930 (2021) -> 1.371.499 (2023). Il 2023 è +0,17% sul 1991. Fonte: somma di P1 in `sezioni_<anno>.csv`.
- **Quartieri cresciuti di più (%):** Rogoredo - Santa Giulia 4.208 -> 11.443 (+171,9%); Maggiore - Musocco - Certosa 4.755 -> 9.279 (+95,1%); Bicocca 4.492 -> 8.682 (+93,3%); Adriano 9.262 -> 17.267 (+86,4%); Lambrate - Ortica 6.972 -> 12.228 (+75,4%). In numeri assoluti: Adriano +8.005, Rogoredo - Santa Giulia +7.235, Lambrate - Ortica +5.256.
- **Quartieri calati di più (%):** Barona 21.157 -> 16.408 (-22,4%); Gallaratese - San Leonardo - Lampugnano 39.292 -> 31.336 (-20,2%); Forze Armate -18,7%; Porta Ticinese - Conca del Naviglio -16,2%; Duomo 19.100 -> 16.231 (-15,0%). In assoluto: Gallaratese -7.956, Bande Nere -7.552 (-14,9%), Forze Armate -5.262. 35 NIL robusti su 66 hanno meno abitanti che nel 1991.
- **Municipi (9) 1991 -> 2023:** crescono M2 (+10,0%), M9 (+6,9%), M8 (+1,7%); calano M1 (-8,3%), M6 (-7,1%), M7 (-5,0%), M3 (-4,2%). Fonte: `variazioni_municipi_1991_2023.csv`.
- **Famiglie:** 583.889 -> 743.276; famiglie di una persona dal 32,0% al 55,6%; componenti medi 2,32 -> 1,82 (2023 stimato). Fonte: `indicatori_comune.csv`.
- **Cautele:** (a) il NIL Duomo nel file ISTAT 2023 contiene 10.038 persone senza fissa dimora (sezione fittizia 151468888888, anche nel 2021: 8.545): le ho tolte da tutti i NIL; se non le togli Duomo "cresce" del 37,5% (26.269) invece di calare del 15%. (b) Le sezioni 1991 hanno confini digitalizzati peggio: per il 1991 la scelta di assegnare la sezione intera al NIL che la copre di più, invece di ripartirla per area, cambia la popolazione di un NIL di una mediana dell'1,4% (media pesata 1,4%), con picchi sui parchi (`sensibilita_ripartizione_area.csv`). (c) Il 2021 e il 2023 sono stime del censimento permanente (registri + campione), il 1991-2011 conteggi: il confronto è tra metodi diversi.

## 2. Milano dal 1861 (`serie_milano_1861_2023.csv`, `variazioni_confini_milano.csv`, `eta_storica_milano_1881_2011.csv`)

- **Annessioni (fonti primarie lette su Normattiva il 30/10/2026):** Regio decreto 8 giugno 1873 n. 1413: i Corpi Santi uniti a Milano dal 1 settembre 1873. Decreto luogotenenziale 31 gennaio 1918 n. 209: Turro Milanese. **Regio decreto 2 settembre 1923 n. 1912 (in vigore dal 14/10/1923): undici comuni, cioè Affori, Baggio, Chiaravalle Milanese, Crescenzago, Gorla-Precotto, Greco Milanese, Lambrate, Musocco, Niguarda, Trenno e Vigentino.** Correzione alla mia memoria della fase 1: non "Gorla Primo" ma "Gorla-Precotto". Dopo il 1923 ci sono ritocchi (1924 Lorenteggio e Ronchetto; 1925 Morsenchio; 1932 cessione di Poasco e di parte di Chiaravalle a San Donato) che ho solo da Wikipedia italiana e restano da verificare.
- **Popolazione ai confini del 1991 (ricostruzione ISTAT):** 267.618 (1861) -> 1.732.000 (1971, massimo) -> 1.369.231 (1991) -> 1.242.123 (2011, minimo tra i censimenti; confini dell'epoca uguali) -> 1.371.499 (2023). Indice 1861 = 100: 647 nel 1971, 512 nel 2023. Dal massimo del 1971 (1.728.686 ai confini dell'epoca) al minimo del 2011 Milano perde 486.563 abitanti (-28,1%); dal 2011 al 2023 ne recupera 129.376 (+10,4%).
- **Salti dovuti ai confini, non alla demografia:** nella serie "dell'epoca" la superficie passa da 9,7 a 72,9 km2 tra 1871 e 1881 (popolazione 199.009 -> 321.839) e da 76,3 a 187,2 km2 tra 1921 e 1931 (718.800 -> 992.036). Nella serie annuale del Comune (ds1494) il 1923 sale di 129.101 persone in un anno (+18,5%, da 697.368 a 826.469) mentre negli anni vicini cresce dell'1-2%: è l'annessione.
- **L'età media a Milano, censimento per censimento (da età singola, ds300):** 29,5 anni (1881), 35,9 (1951), 42,5 (1991), 45,0 (2001), 45,7 (2011). Indice di vecchiaia (over 65 ogni 100 under 15): 19 (1881), 47 (1951), 176 (1991), 212 (2001, massimo), 196 (2011).
- **Cautele:** la superficie 1981 di ds303 (171,7 km2) è quasi certamente un errore (non risulta nessuna variazione di confine 1971-1991); il 1971 nel volume ISTAT 1994 è una cifra tonda; il 1861-1871 "ai confini 1991" è una ricostruzione ISTAT con proporzioni, non un conteggio; la ricostruzione 1921 ai confini 1991 (818.148) contro i 718.800 dell'epoca dice che il territorio poi annesso ospitava circa 99.000 persone nel 1921 (stima nostra: differenza tra le due serie). Il totale per età di ds300 nel 1881 (320.292) differisce di 1.547 da ds303 (321.839).

## 3. Dove la città invecchia e dove ringiovanisce (età media da classi quinquennali; 75+ messo a 82 anni)

- **Comune:** età media 43,1 (1991), 45,5 (2001), 46,1 (2011), 45,6 (2021), 45,6 (2023); quota over 65: 18,2% -> 22,8% -> 25,0% -> 22,7% -> 22,3%; indice di vecchiaia 176 -> 212 -> 196 -> 182 -> 188. L'invecchiamento si è fermato tra il 2001 e il 2021 (arrivo di stranieri giovani) e dal 2023 riparte: 193,7 nel 2025 e 197,9 al 1 gennaio 2026 (`annuale_milano_2018_2025.csv`).
- **NIL che invecchiano di più 1991 -> 2023 (anni di età media):** Trenno 36,6 -> 50,6 (+14,0; over 65 dall'8,4% al 32,7%; indice di vecchiaia da 49,5 a 349,5); Quinto Romano +12,1; Quarto Cagnino +9,3; Barona 39,7 -> 48,9 (+9,2; indice da 93,5 a 269,7). Ipotesi, non verificata: sono quartieri riempiti da famiglie giovani nei decenni precedenti, che sono rimaste sul posto.
- **NIL che ringiovaniscono (età media in calo, solo 6 dei 66 NIL robusti):** San Siro 46,7 -> 44,4 (-2,2; indice di vecchiaia da 283 a 154; stranieri dal 2,4% al 34,5%); Maggiore - Musocco - Certosa 41,6 -> 40,6 (-1,0; +95% di abitanti); Rogoredo - Santa Giulia -0,7; QT 8 -0,7; Comasina -0,5.
- **Nel 2023** il NIL più vecchio è Trenno (età media 50,6) e il più giovane Maggiore - Musocco - Certosa (40,6; indice di vecchiaia 94 contro 350).
- **Cautele:** le età medie qui sono calcolate dalle classi di 5 anni (come fa anche il Comune: 43,0/45,5/46,1) e sono di circa 0,5 anni più alte dell'età media esatta dei record individuali (42,5/45,0/45,7; 45,3 secondo ISTAT POSAS al 1.1.2024). L'80+ non è nelle sezioni di nessun anno: per i NIL c'è solo il 75+. Il confronto tra NIL è tra sezioni assegnate per sovrapposizione geometrica nel 1991.

## 4. Chi è arrivato (stranieri e nuovi residenti)

- **Stranieri residenti (comune):** 26.568 (1,9%) nel 1991; 87.590 (7,0%) nel 2001; 176.303 (14,2%) nel 2011; 253.531 (18,8%) nel 2021; 269.397 (19,6%) nel 2023. Fonti: campi ST16 (1991), ST07 (2001), ST1 (2011, 2021, 2023). Dal 1 gennaio 2026 (ISTAT STRASA): 267.986 (19,7%).
- **Quartieri con più stranieri nel 2023:** Comasina 38,0% (nel 1991 0,5%: +37,4 punti, il maggiore aumento), San Siro 34,5%, Bovisa 30,7%, Quarto Oggiaro - Vialba - Musocco 30,6%, Padova - Turro - Crescenzago 30,5%; 11 NIL robusti su 66 sono sopra il 25%, 2 sotto il 10%. Tra i NIL robusti nessuno superava il 4,0% nel 1991. Aumento minore: Pagano +7,1 punti. Per municipio 2023: M2 24,7%, M9 22,7%, M8 20,1%, M1 15,2%, M3 15,2%.
- **Cittadinanze principali (`cittadinanze_comune.csv`):** 1991 Egitto 2.934 (11,0% degli stranieri), Filippine 2.474, Francia 1.419; 2001 Filippine 14.673 (16,8%), Egitto 9.537, Perù 7.337; 2011 Filippine 32.594, Cina 19.258, Egitto 19.254; 2023 Egitto 42.023 (15,6%), Filippine 35.906, Cina 33.465, Perù 15.884, Sri Lanka 15.076. Gli egiziani sono 14 volte quelli del 1991; i filippini, primi nel 2001 e nel 2011, nel 2023 sono quasi fermi (+10% sul 2011). Per il 2011 e il 2023 solo le dieci cittadinanze principali (circa il 75% e il 71% degli stranieri).
- **Laureati (titolo terziario su popolazione di 6 anni e più nel 1991-2011, di 9 e più nel 2021-2023):** 9,3% (1991), 16,9% (2001), 22,9% (2011), 30,3% (2021), 31,7% (2023); sul totale dei residenti 8,9% -> 29,6%. Per NIL robusti 2023: massimo Porta Vigentina - Porta Lodovica 48,8%, Magenta - San Vittore 48,3%, Pagano 48,2%; minimo Quarto Oggiaro - Vialba - Musocco 11,8%, Quinto Romano 14,9%, Gratosoglio 15,9%. Aumento maggiore: Porta Romana 11,5% -> 43,9% (+32,4 punti), Bicocca +31,4; minore Quarto Oggiaro (1,2% -> 11,8%, +10,6). Il divario tra il NIL con più e quello con meno laureati cresce da 23,7 a 37,0 punti. Per municipio: M1 22,4% -> 46,3%, M9 4,8% -> 27,3%.
- **Nuovi residenti, flussi annuali 2019-2024 (ISTAT D7B, `annuale_milano_2018_2025.csv`):** ogni anno il saldo naturale è negativo (da -3.300 a -8.261: 2024 nati 9.364, morti 13.782). Il saldo migratorio è positivo e dipende dall'estero: iscritti dall'estero 26.563 e saldo migratorio totale +19.494 nel 2023, solo +2.562 nel 2024. Verso altri comuni Milano perde ogni anno persone (2024: 27.305 arrivi, 37.527 partenze).
- **Cautele:** "straniero" = cittadinanza, non origine (i naturalizzati contano come italiani). Il 2023 ha 10.038 senza fissa dimora in una sezione fittizia (cittadinanze miste); i NIL non robusti (parchi, cascine) hanno percentuali instabili.

## Altre sorprese e trappole trovate

1. **Il crollo del 2020-2021 è in gran parte statistico.** La popolazione di Milano passa da 1.406.242 (31.12.2019) a 1.349.930 (31.12.2021), -56.312; i flussi reali (nati, morti, trasferimenti) sommano -5.754; il resto, -50.558, sono "aggiustamenti statistici" del censimento permanente (-27.193 nel 2020, -23.365 nel 2021; D7B mese 13). Le cifre prima del 2021 non sono confrontabili con quelle dopo. Fonte: `annuale_milano_2018_2025.csv`, campi `aggiustamento_statistico`, `saldo_totale_flussi`.
2. **Il registro anagrafico del Comune (ds205) sovrastima rispetto al censimento:** nel 2011 1.341.830 contro 1.242.123 del censimento (+8,0%); nel 2023 1.417.597 contro 1.371.499 (+3,4%). Anche la serie annuale calcolata del Comune (ds1494) ha un salto di -55.682 (-4,3%) nel 2002, l'anno dopo il censimento 2001, tipico di un riallineamento tra anagrafe e censimento (spiegazione non verificata). Quindi la "ripresa" 2011-2023 è +10,4% con i censimenti ma solo +5,6% con l'anagrafe: il 2011 era sottostimato, o il registro troppo gonfio.
3. **Le abitazioni "non occupate da residenti" salgono dal 6,0% (2011) al 13,5% (2021)**, ma è un cambio di definizione e di metodo (nel 2021 le abitazioni totali sono 809.990 contro 643.053 del 2011, +26% in dieci anni mentre le famiglie crescono del 16%): non va letto come un aumento delle case vuote.
4. **ISTAT POSAS al 1 gennaio 2022 e al 1 gennaio 2024 coincidono esattamente** con i totali del censimento permanente (1.349.930 e 1.371.499) e con gli stranieri (253.531 e 269.397): sono la stessa popolazione.

## Definizioni cambiate tra gli anni (da tenere nei confronti)

| Indicatore | 1991 | 2001 | 2011 | 2021-2023 |
|---|---|---|---|---|
| Classi di età nelle sezioni | <5, 5-9 ... 70-74, 75+ (uguali in tutti gli anni; 80+ non disponibile) | = | = | = |
| Laureati: base | 6 anni e più (il metadato dice 5+ ma il totale P46 è 6+) | 6+ | 6+ | 9+ ("titoli terziari", compresi i dottori di ricerca) |
| Stranieri | ST16 stranieri residenti | ST07 (anche apolidi) | ST1 (stranieri e apolidi) | ST1 |
| Occupati | P61, popolazione attiva | P61 | P61 (15+) | P101 solo 15-64 anni: tasso 15+ non calcolabile, uso 15-64 approssimato in tutti gli anni (occupati di ogni età su residenti 15-64, sovrastima 1991-2011 di poco) |
| Abitazioni | A1 totale, A2 occupate | A1, A2 | A2+A3, A2 | A8, A2 (conteggio da registri: salto di metodo) |
| Componenti per famiglia | PF2/PF1 (esatto) | esatto | esatto | stima (6+ contato 6) |
| Metodo di rilevazione | porta a porta | porta a porta | porta a porta | permanente: registri + campione, sezioni 2021 (stime) |

## Non verificato

- Laureati nel 1991 a Quarto Oggiaro (346 su 28.675, 1,2%): coerente con 2001 (4,5%) ma non controllato con un'altra fonte.
- Nel 1991 ho usato il codice di sezione dei record del Comune (CodSez) uguale a quello ISTAT (SEZIONE): coincide per circa il 97% delle sezioni; per NIL e municipi uso sempre le sezioni ISTAT, i record individuali servono solo per età media esatta, 80+ e cittadinanze del comune.
- Le variazioni di confine dopo il 1923 (solo Wikipedia).
