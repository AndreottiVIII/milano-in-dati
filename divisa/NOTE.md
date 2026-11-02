# Quanto è divisa Milano - analisi e pagina (divisa/)

Fatto il 1 novembre 2026, solo con dati già su disco. Nessun git; `JOURNAL.md`, `docs/index.html`, `docs/menu.js`, `docs/MENU_README.md` e le altre pagine non toccati. Pagina: `docs/divisa/index.html` (dati in `docs/divisa/data/`). Idea di partenza: City Observatory (separazione residenziale nel tempo).

Parole: **NIL** = i 88 Nuclei di Identità Locale. **CAP** = indirizzo fiscale del contribuente (non dove vive). **Cittadinanza** = quella scritta in anagrafe: non origine né luogo di nascita. Tutti i numeri sotto escono da `out/*.csv` e `docs/divisa/data/riepilogo.json` (campo `numeri`).

## 1. Le misure (spiegate in una frase)

| Misura | Cosa dice | Dove si usa |
|---|---|---|
| **D (dissimilarità)** | quanti dei due gruppi dovrebbero cambiare zona perché siano distribuiti uguale (0-100%) | cittadinanza (italiani/stranieri e comunità), età (65+ contro under 35), laureati, reddito (quarto ricco/quarto povero) |
| **Isolamento** | tra i residenti della zona di una persona del gruppo, quanti sono del gruppo (media), da leggere contro la quota in città | stranieri, 65+, laureati, quarto ricco |
| **H di Theil (entropia)** | quanta parte della varietà di cittadinanze della città si spiega col quartiere | cittadinanza (tutte; e solo tra stranieri) |
| **Entropia a ordine di rango** (Reardon et al. 2006) | come H per categorie in ordine (fasce di reddito, età): quanta parte delle differenze si spiega con la zona; guarda posizioni, non euro: l'inflazione non la muove | reddito (7 fasce), età (101 età singole) |
| **Valore «a caso»** | media di 30-100 riallocazioni casuali (stesse zone, stesse quote): sotto non si può scendere | tutti i grafici |
| **Intervallo** | ricampionamento multinomiale dentro ogni zona (100-300 volte), 2,5-97,5 percentile | tutti i grafici |

`scripts/misure.py` contiene le funzioni; verificato che D delle comunità 1999 coincide con `popolazione/pulito/cittadinanze_concentrazione.csv` (Cina 0,391, Egitto 0,265). L'entropia a ordine di rango con 7 gruppi invece di 101 età singole dà lo stesso valore a meno dell'1% (0,00376 contro 0,00376, 0,00378 con 10 gruppi): la stima con poche fasce non è distorta almeno sull'età; per il reddito non si può verificare.

## 2. Numeri principali

**Reddito per CAP** (`out/reddito_serie.csv`; MEF, anni d'imposta 2011, 2015, 2019-2024; 7 fasce, 38 CAP, circa 26.500 contribuenti per CAP):
- Quanta parte delle differenze di reddito si spiega col CAP, Milano: **2,08% (2011), 2,25% (2015), 2,34% (2019), 2,34% (2024)**. Dal 2015 praticamente ferma (+4%). Napoli 3,84% → 4,17%; Roma 2,61% → 3,15%; Torino 2,23% → 2,88%; Bologna 1,50% → 1,56%. Intervalli di ricampionamento strettissimi (±0,0005 punti): il caso dei conteggi non conta, contano le definizioni dei dati.
- D tra quarto più ricco e quarto più povero: 15,1% (2011), 16,0% (2015), 15,4% (2024). Isolamento del quarto più ricco: 27,4% (2011), 27,6% (2024) (25% se mescolati).
- Quota di contribuenti oltre 55.000 euro (fasce nominali): 11,5% → 17,5% (in parte inflazione).
- **Milano contro 41 città** (`out/reddito_41_citta.csv`, anno 2024): 8ª su 22 città con almeno 10 CAP; in testa Napoli (4,2%), poi Roma (3,2%), Palermo, Catania, Genova, Torino; in fondo La Spezia (0,7%). Il confronto tra città dipende dal numero e dalla grandezza dei CAP (Genova ne ha 43 da 10.000 contribuenti, Roma 72 da 26.000).
- **Variante CAP 20121/20122** (`out/reddito_varianti_milano.csv`): tutti i CAP 2,08% → 2,34%; i due CAP uniti 2,08% → 2,34%; senza i due 1,79% → 2,28%. La crescita 2011-2015 dipende da come si trattano i due CAP; dal 2015 no.
- **Laureati** (`out/laureati_serie.csv`; censimenti 1991, 2001, 2011, 2021, 2023, 88 NIL): D 31,4% → 28,1% → 25,2% → 20,6% → 19,8%; laureati 9,3% → 31,9%; isolamento 13,6% → 34,9%. Con i 66 NIL a confini stabili: 31,2% → 19,5%.

**Cittadinanza** (`out/cittadinanza_serie.csv`, `cittadinanza_comunita.csv`; ds27 1999-2025, 88 NIL, 87 dal 2020):
- D italiani/stranieri: **17,1% (1999) → 22,1% (2015, picco) → 18,8% (2025)**; valore a caso 0,7-1,0%. Stranieri 7,9% → 21,1% dei residenti. Isolamento: lo straniero medio ha il 24,2% di stranieri nel quartiere (21,1% in città); 1999: 9,2% contro 7,9%: rapporto 1,14 contro 1,17.
- H di Theil tra tutte le cittadinanze: 3,7% (1999), 4,9% (2018), 4,3% (2025); solo tra stranieri: 5,8% (1999), 4,7% (2013), 5,2% (2025).
- Comunità, D 2025 (contro tutti gli altri residenti): Bangladesh 37,5%, Cina 36,9%, Egitto 33,6%, Marocco 30,5%, Perù 21,1%, Filippine 20,9%, Ecuador 20,9%, Sri Lanka 18,3%, Romania 17,4%, Ucraina 10,2%. Cina: massimo 47% nel 2008, poi in discesa; Bangladesh 50% (1999) → 37,5%; Egitto 27% (1999) → 34%.
- Salti del registro: D 16,3% (2002) → 16,1% (2003); 19,9% (2011) → 20,4% (2012): piccoli.

**Età** (`out/eta_serie.csv`; ds27): D over 65 contro under 35: **8,0% (1999) → 9,2% (2012, picco) → 6,8% (2025)**, minimo della serie; entropia a ordine di rango su tutte le età: 0,36% → 0,53% (2012-13) → 0,38%; la quota di 65+ è 21,7% → 22,4%. Intervallo e valore a caso (0,8%) nei CSV.

## 3. La cosa più sorprendente

**Milano non si sta dividendo di più: dal 2015-2016 tutte e tre le separazioni sono ferme (reddito) o scendono (cittadinanza ed età).** Mentre gli stranieri sono passati dall'8% al 21% dei residenti e i contribuenti sopra 55.000 euro dall'11,5% al 17,5%, i quartieri non si sono polarizzati: italiani/stranieri è tornato dal 22,1% al 18,8% (livello del 2007), over 65/under 35 è al minimo dal 1999, il reddito per CAP è fermo. Anche indietro nel tempo (laureati 1991-2023) la separazione è scesa. I due gruppi più concentrati tra le comunità (Cina, Bangladesh) si stanno disperdendo da anni. Secondo punto: a Milano il CAP spiega poco (2,3%), meno che a Napoli (4,2%) e Roma (3,2%), nonostante la città sia la più disuguale per reddito (`redditi/NOTE.md`: Gini 0,54).

## 4. Come ho deciso (scelte con il motivo)

- **Entropia a ordine di rango e non D con soglie fisse in euro.** D tra «sotto 15.000» e «sopra 55.000» scendeva da 29% a 23% solo perché la fascia alta si allargava con l'inflazione (`d_soglie` nei CSV, non usato). Le posizioni (percentili) non dipendono dall'inflazione. Il D del quarto ricco/povero usa i quarti della città, con la fascia di confine divisa in proporzione.
- **Fascia «≤0» unita a «0-10.000».** Con 8 fasce l'indice a rango saltava da 0,023 (2015) a 0,028 (2019) in tutte e cinque le città: era un artefatto (dal 2019 il MEF svuota la classe ≤0: 3.257 contribuenti a Milano nel 2015, 283 nel 2019; a p quasi 0 il rumore di poche decine di persone pesava come un taglio vero). Verificato togliendo la fascia: 0,0235 nel 2019 e 0,0235 nel 2024.
- **Celle mancanti del MEF.** Classe >120.000 nascosta in 11-18 CAP di Milano nel 2023-24: ricostruita per differenza (reddito_complessivo_n = somma delle 8 fasce, differenza 0 su 591 righe complete): 527 celle in 41 città. Per altre celle nascoste (CAP piccoli): quota mediana del CAP negli altri anni (194 righe). Tolti i CAP con meno di 500 contribuenti (47 righe) e 60 righe di CAP che non hanno mai un anno completo.
- **Intervalli.** Ricampionamento multinomiale (stesse quote osservate per zona): misura solo il caso dei conteggi. A Milano per il reddito è ±0,0005 punti: l'incertezza vera sta nei CAP 20121/20122, nelle fasce e nel significato di «CAP». Per questo c'è la tabella delle varianti.
- **Valore a caso.** Indispensabile per cittadinanza ed età (D a caso 0,7-1% per i quartieri; 3-39% per comunità piccole come Ucraina 1999: 68 residenti). Le comunità si disegnano solo da 300 residenti.
- **Reddito sui quartieri.** Per la mappa il CAP è portato ai NIL con i civici (`quartieri-che-cambiano/out/collegamento_cap_nil.csv`, quote che sommano a 1 per NIL). È una stima: i dati sono per CAP.

## 5. Limiti dei dati (anche sulla pagina)

1. CAP = indirizzo fiscale; CAP grandi (26.500 contribuenti): non si vede la separazione tra vie.
2. CAP 20121/20122 riassegnati (20122: 20.361 → 32.776 tra 2015 e 2019; 20121: 16.612 → 22.090 tra 2022 e 2023): il 2011 dipende da loro.
3. Solo 8 anni d'imposta e 7 fasce; fasce nominali (la quota di «alti» sale con l'inflazione).
4. Cittadinanza ≠ origine (naturalizzazioni 7.660-9.021 l'anno nel 2022-24).
5. Salti del registro (-53.857 tra 2002 e 2003, +24.579 tra 2011 e 2012); il registro supera ISTAT dal 2020 (stranieri +10,4% nel 2025).
6. NIL prima del 2012: assegnazione non documentata dal Comune; 87 NIL con residenti dal 2020 (Parco Sempione senza residenti).
7. Zone diverse (38 CAP contro 88 NIL): i tre temi non si confrontano; il confronto tra città dipende dal numero di CAP.
8. Laureati: confini che cambiano, base 6+ poi 9+; 66 NIL a confini stabili come controllo.
9. Quartieri e comunità piccoli: grigio sotto 500 residenti; comunità da 300 residenti.
10. Descrizione, non cause.

## 6. Come rifare

`python -I -X utf8 scripts/<nome>.py <percorso assoluto di milano-in-dati> <percorso assoluto di divisa>` nell'ordine `01_reddito`, `02_cittadinanza`, `03_eta`, `04_laureati`; poi `pagina.py <milano-in-dati> <divisa> <docs>/divisa`. Tutto è deterministico (semi fissi). Tempo: circa 40 secondi in tutto.
