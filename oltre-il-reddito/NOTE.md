# Oltre il reddito: fonti, scelte, limiti

Pagina: `docs/oltre-il-reddito/index.html`. Dati: `docs/oltre-il-reddito/data/` (`riepilogo.json`, `quartieri.csv`). Programma: `scripts/build.py` (`python -I -X utf8 C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\oltre-il-reddito\scripts\build.py`, pochi secondi, seme 20261102, solo file locali). Il log dei controlli contro il rapporto sta in `out/controlli.txt` (solo sul PC).

Domanda: il reddito per CAP basta a descrivere un quartiere? Unità: i 70 NIL con almeno 3.000 residenti (registro al 31/12/2024). Tutti i confronti sono tra zone.

## Da dove vengono i numeri (file originali dei filoni)

| Cosa | File | Note |
|---|---|---|
| Residenti, età media, densità | `popolazione/pulito/eta_nil_anno_indicatori.csv` (2024) | Comune di Milano ds27, CC BY |
| Distanza dal Duomo | `docs/elezioni/data/nil.geojson` | baricentro dei confini, km |
| Morti osservate e attese 2022-2024 | `speranza-vita/pulito/nil_smr_e0.csv` (`osservati`, `attesi`, finestra 2022-2024, sesso T) | Comune di Milano ds137/ds1940 (CC BY); tassi per età ISTAT (CC BY 4.0) |
| Affluenza Camera 2022 (e Comunali 2021, Europee 2024, le otto elezioni per il controllo prudente) | `docs/elezioni/data/nil/<elezione>.json` (`vt`/`e`) | Comune di Milano, CC BY 4.0 |
| Reddito per CAP 2024, prezzo OMI 2026/1 | `quartieri-che-cambiano/out/indicatori_nil.csv` (`reddito_2024`, `prezzo_2026_reale`) | MEF CC BY 3.0; Agenzia delle Entrate OMI CC BY 4.0 |
| Laureati | `censimenti/pulito/indicatori_NIL.csv` (`quota_laureati_su_residenti`, media 2021 e 2023) | ISTAT CC BY 4.0; il 2023 è una stima da registri |
| Occupazione e disoccupazione 2011 | `docs/lavoro/data/nil_lavoro.csv` | ISTAT censimento 2011 |
| Metri quadri a persona e quota proprietà 2011 | `censimenti/pulito/sezioni_2011.csv` + `sezioni_armonizzate.csv` (A44/P1; A47/(A46+A47+A48)) | ISTAT censimento 2011 |
| Canone medio ALER 2016 per abitazione | `docs/case-popolari/data/nil.csv` | Regione Lombardia: nessuna licenza dichiarata, si citano i numeri |
| CAP dominante di ogni quartiere | `quartieri-che-cambiano/out/collegamento_cap_nil.csv` | per il confronto "dentro lo stesso CAP" |

Il calcolo dell'indice, le correlazioni parziali e l'affluenza ripetono `incroci-esplorativi/verifica/scripts/` (`vc.py`, `v06_D.py`, `v05_C.py`) ma partono dai file originali. Non sono usate le colonne con difetti noti elencate in testa a `incroci-esplorativi/RAPPORTO.md`. Come controllo, il programma ricalcola l'indice anche con gli SMR del ricontrollo (`verifica/out/smr_propri.csv`, che non è un input): stessi risultati (differenza massima tra i due SMR 0,0026).

## Scelte

- **Terzi per affluenza**: `pd.qcut(affluenza, 3)` sui 70 quartieri, quindi 24 / 23 / 23. Rapporti = somma morti osservate / somma attese del gruppo.
- **Fasce di reddito**: `qcut` in tre terzi, dentro ognuno due metà per affluenza (12+12, 12+11, 12+11). Sulla pagina il rapporto di ogni cella è osservate/attese sommate (pesa i quartieri per le attese). Il rapporto del primo studio (1,15 e 0,98) è invece la media semplice dei rapporti dei singoli quartieri: la pagina riporta anche questa nella nota del grafico.
- **Indice senza reddito**: sette misure (laureati, occupazione 2011, disoccupazione 2011 e canone ALER con segno rovesciato, prezzo OMI, metri quadri a persona, quota proprietà); per ogni misura le posizioni tra i 70, standardizzate, media semplice. Non contiene né mortalità né affluenza. Posizione sulla pagina = 71 - rango (1 = valore più alto). Nelle posizioni con pari merito (reddito uguale perché stesso CAP) compare un mezzo punto: Rogoredo-Santa Giulia è "circa 58°" (57,5).
- **Prova dei pesi**: 5.000 vettori di pesi da una Dirichlet(1,...,1) a 7 componenti. "Stabile" = tra i 10 quartieri con lo scarto maggiore tra posizione per indice e per reddito in almeno l'80% delle prove. Risultato: Giambellino 100%, Rogoredo-Santa Giulia 100%, San Siro 98,3%. Tra gli altri il massimo è Affori 76%. Per gli altri quartieri l'intervallo tra il 5° e il 95° percentile della posizione sull'indice è largo 15 posti in mediana. Solo i tre stabili sono nominati sulla pagina.
- **"A parità di"**: correlazione di Spearman parziale (regressione sui ranghi) con controlli distanza dal Duomo, età media, densità, più reddito (o indice).
- **Morivione**: segnato "cautela" (possibile residenza per anziani, ipotesi non verificata, come in `speranza-vita`). Resta nei grafici, nel grafico a punti ha il rapporto più alto (1,45).
- **Tono**: nessun ordinamento della tabella per rapporto o per posizione (alfabetica), nessun colore buono/cattivo, nessuna cittadinanza.

## Controlli contro il rapporto (RAPPORTO.md)

Confermati: terzo con meno affluenza 16.913 morti contro 15.661 attese (+8%); terzo con più affluenza 13.445 contro 14.665 (-8%); grezza -0,80; affluenza a parità -0,69 (il rapporto dice -0,68: il valore qui è -0,688, con l'affluenza vt/e dei file `docs/elezioni`; il ricontrollo, con le sole sezioni regolari, dà -0,683: differenza di arrotondamento); indice a parità di reddito -0,61 e reddito a parità di indice -0,03 (con 2022-2024); tre quartieri stabili San Siro, Giambellino, Rogoredo-Santa Giulia.

Diversi (tenuto il calcolo di questo programma):

- **Fascia di reddito più basso**: pooled (osservate/attese sommate) 1,11 con affluenza bassa e 1,02 con affluenza alta; il rapporto 1,15 / 0,98 corrisponde alla **media semplice dei rapporti dei quartieri** (1,145 e 0,976). Sulla pagina il grafico usa i rapporti sommati; la nota riporta anche la media semplice.
- **A parità di laureati**: Camera 2022 e morti 2022-2024: -0,57 (non -0,45). La cifra -0,45 del rapporto non corrisponde a nessun calcolo con i laureati: con la misura prudente (media di otto elezioni, morti 2012-2019) il legame a parità dei quattro controlli è -0,47, con i laureati -0,30.
- **Dentro lo stesso CAP**: Camera 2022 e morti 2022-2024: Spearman -0,55 (Pearson -0,64), 58 quartieri; con la media di otto elezioni e morti 2012-2019: Spearman -0,42, Pearson -0,42. Il -0,42 del rapporto è quest'ultimo.
- Sulla pagina sono riportati sia i valori della Camera 2022 sia quelli prudenti, con la loro definizione.
- **Residenti all'estero al denominatore**: con le Comunali 2021 e le Europee 2024 il legame a parità è -0,41 e -0,49; usando come denominatore gli elettori della Camera 2022 (senza iscritti all'estero) sale a -0,56 e -0,61. La Camera 2022 ha già solo gli elettori in Italia.

## Limiti dei dati (elenco completo sulla pagina)

Confronto tra zone e non tra persone; correlazione non è causa; l'affluenza è una misura di svantaggio; il legame cala con i laureati e dentro lo stesso CAP ma non sparisce; reddito per CAP (38 CAP) e del contribuente; l'indice è una costruzione nostra, in parte con dati 2011, pesi uguali; case ALER senza quelle del Comune; OMI stimate; residenze per anziani non note (Morivione); residenti solo sulla carta possibili; quartieri piccoli con pochi morti in tre anni; nessuna affluenza per età; i residenti all'estero indeboliscono il legame e non lo creano.

## Cosa non è stato fatto

Nessuna mappa; nessun intervallo di incertezza sui rapporti per quartiere; nessuna analisi per cause né per sesso; non è stato letto l'indice del primo studio (contiene mortalità e affluenza); nessuna modifica a `menu.js`, `temi.json`, elenco, `JOURNAL.md`, `STATO_PROGETTO.md`; nessun commit.
