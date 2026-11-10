# Quanto consumano le case: note

Bozza della pagina: `bozze-grafici/case-energia-v2/index.html`. Dati per il sito: `docs/case-energia/data/` (tutti sotto i 100 KB, il più grande è `nil.geojson` con 91 KB). Fatto il 10/11/2026. Niente git, niente pubblicazione.

## Fonti e licenze

| Dato | Fonte | Licenza | Come |
|---|---|---|---|
| Attestati fino al 2016 (235.106, Milano) | Regione Lombardia - ARIA, "CENED - Certificazione ENergetica degli EDifici" (dati.lombardia.it, rsg3-xhvk) | CC0 (dichiarata nei metadati) | già scaricato in `_esplorazione/aree/energia/lombardia_rsg3-xhvk/milano.csv` |
| Attestati dal 2016 (400.384 per Milano, 342.479 di abitazioni) | Regione Lombardia - ARIA, "Database CENED+2" (bbky-sde5) | CC0 (dichiarata nei metadati) | `scripts/01_scarica_cened2.py`, solo le colonne utili, in `raw/cened2_milano.csv` (con gli indirizzi: NON va online) |
| Sezioni di censimento 2011 -> quartiere | ISTAT, sezioni 2011, raccordo già fatto in `censimenti/pulito/raccordo_sezioni_2011.csv` | CC BY 4.0 | riuso |
| Confini dei quartieri (NIL) | Comune di Milano, copia di `docs/ospedali/data/nil_quartieri.geojson` (proprietà ridotte a id e nome, coordinate a 5 decimali) | CC BY | riuso |
| Colonnine di ricarica (ds540), punti di fornitura teleriscaldamento (ds1575), abitanti serviti (ds1536), volumetria (ds1535) | Comune di Milano | CC BY (dichiarata nel catalogo del Comune per ds540, ds1575, ds1536; ds1535 non riletta ma stessa serie del Comune) | già scaricati in `_esplorazione/aree/energia/` |

Tutte le fonti dichiarano la licenza. Nessun avviso da fare su questo.

Scarico: User-Agent `milano-in-dati/1.0`, nessun login, nessuna email, 1 secondo tra una richiesta e l'altra (il robots.txt di dati.lombardia.it chiede Crawl-delay 1; 9 richieste da 50.000 righe). Il sito del Comune risponde "accesso non consentito" alla pagina robots.txt letta da browser; non ho scaricato nulla di nuovo da lì, solo tre letture del catalogo (API pubblica) per vedere la licenza.

## Passi

1. `scripts/01_scarica_cened2.py <cartella case-energia>`: scarica i 400.384 attestati di Milano di CENED+2 (29 colonne) in `raw/`.
2. `scripts/02_calcola.py <cartella milano-in-dati>`: calcola tutto in aggregato e scrive i file in `docs/case-energia/data/`. Passi principali:
   - classe unica: A+ e A (vecchio), A1-A4 (nuovo) diventano A;
   - epoca in 7 fasce (prima del 1930, 1930-1945, 1946-1960, 1961-1976, 1977-1992, 1993-2006, dopo il 2006); gli anni singoli (per esempio "1960", "2014") sono messi nella fascia che li contiene;
   - emissioni: valore di mezzo (mediana); scartati i valori nulli o sopra 1.000 kg/m² (nei dati ci sono errori di milioni);
   - quartiere: ultime 7 cifre di `sez_censimento` -> sezione 2011 -> NIL con il raccordo. 341.023 attestati su 342.479 (99,6%) hanno un quartiere;
   - mappa: quartieri con almeno 150 attestati (75 su 88; 13 grigi); cinque classi di colore con lo stesso numero di quartieri;
   - "la tua casa": per ogni quartiere ed epoca i conteggi per classe e la CO2 tipica; con meno di 30 attestati si mostra Milano;
   - anni: vecchio per anno di chiusura della pratica (2010-2015), nuovo per anno di inserimento (2017-2025); 2009, 2016 e 2026 esclusi perché pochi o a metà.
3. Pagina: legge solo i file in `docs/case-energia/data/`.

## Numeri e differenze rispetto al brief

- 235.106 attestati, 158.923 in F o G = **67,6%**: confermato (tutti gli usi).
- Emissioni tipiche delle abitazioni (uso E.1(1)): **36,5** prima del 1930, **8,7** dopo il 2006. Il brief diceva circa 36 e circa 10: il 10,2 si ottiene contando solo gli attestati con la fascia già scritta; includendo anche gli anni singoli (per esempio 2014) la mediana scende a 8,7. Ho usato il calcolo completo. Se Davide preferisce il 10, basta cambiare `banda()`.
- Con il nuovo sistema (dal 2016) la quota in F o G delle abitazioni è **42,7%** (la pagina Età dei palazzi dice 43%, stesso dato). Non è confrontabile con il 67,6%: cambiano le regole di calcolo e le classi.

## Limiti

- Gli attestati si fanno a vendita, affitto, nuova costruzione, ristrutturazione. Dal 2016: 49,8% vendite, 24,0% affitti, 5,0% case nuove (99,2% in A o B), 4,4% ristrutturazioni importanti (62,8% in A o B). Sono scritti nella pagina, con come possono distorcere (case mai vendute mancano, case nuove sovrarappresentate, più attestati per la stessa casa, quartieri con più compravendite).
- Un attestato non è una casa: la stessa casa può avere più attestati; nei dati aperti c'è l'indirizzo ma non un codice unico dell'abitazione, e non lo pubblico.
- Le sezioni di censimento sono assunte del 2011 (i codici arrivano fino a circa 6.000, in linea con il 2011); non ho una prova diretta della versione. Il 99,6% di abbinamento fa pensare che sia giusta.
- Il vecchio sistema non ha né indirizzo né sezione: la mappa e "la tua casa" usano solo il nuovo (2016-2026).
- Le emissioni sono calcolate dal tecnico, non misurate.
- Nei due periodi le definizioni di pompa di calore, teleriscaldamento e gasolio non sono identiche (vecchio: tipo di generatore e combustibile; nuovo: impianto e vettore principale): per questo i piccoli grafici hanno uno stacco nel 2016.
- Colonnine: l'anno è quello dell'ordinanza, non della messa in funzione; solo suolo pubblico. Teleriscaldamento: serie ferma al 2018.
- Il calo di F e G dal 2017 al 2025 non ha causa dimostrata (incentivi, nuovi attestati dopo i lavori, composizione): la pagina lo dice.
- Fotovoltaico del Comune (fermo al 2018) lasciato fuori.

## File prodotti (docs/case-energia/data/)

`riepilogo.json`, `tuacasa.json`, `nil.geojson`, `classi_per_epoca.csv`, `classi_per_anno.csv`, `quartieri.csv`, `riscaldamento.csv`, `riscaldamento_per_anno.csv`, `colonnine_per_anno.csv`, `teleriscaldamento_abitanti.csv`. Nessun indirizzo, nessun attestato singolo.
