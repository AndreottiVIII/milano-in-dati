# Trappole dei dati: beni culturali di Milano (ICCD / ArCo 2.0)

Fonte: Catalogo generale dei beni culturali (ICCD), tramite il dump ArCo 2.0 del CNR-ISTC del 2023-12-01; scaricato il 2026-10-29.
File pulito: `beni_milano.csv` (30.721 righe, una per scheda, chiave `iri`). Programma: `scripts/06_pulisci.py`. I conteggi esatti sono in `problemi_conteggi.json`.
"Sede Milano" = 27.459 schede; "solo luogo collegato" = 3.262 schede (campo `ambito`/`sede_milano`). Se non scritto altrimenti, i numeri sotto sono sulle 27.459.

## 1. Righe doppie e chiavi

1. **Nessuna riga doppia nel file pulito.** `iri` e `codice_catalogo` sono unici su tutte le 30.721 righe (scartate: 0). Le righe doppie "vere" erano nel dump: 966.591.725 righe lette, 83.583.345 dopo avere tolto le ripetizioni (fase 1, `NOTE.md`).
2. **`id_catalogo` NON e' una chiave.** 4.707 schede di sede Milano condividono il numero con almeno un'altra (sono parti dello stesso bene: `0100127418-2`, `-21`, ...). Si usa sempre `iri`.
3. **Schede quasi identiche ma distinte.** 1.843 gruppi (5.900 schede, il piu' grande di 42) hanno uguali titolo, autore, data, materia, soggetto, detentore e coordinate (esempi: set di sedie, capitelli di una serie). Sono schede diverse nel catalogo (parti di un insieme): le abbiamo **tenute**, non sono doppioni. Contarle come "oggetti" gonfia i numeri; contiamo "schede".
4. **Valori ripetuti dentro un campo**: 6 titoli, 7 datazioni, 5 materie avevano lo stesso valore scritto due volte ("a | a"); tolti.

## 2. Che cosa e' "di Milano"

5. Le 3.262 schede `solo_luogo_collegato` sono beni di altre citta' (Caluso, Oderzo, Verona...) che hanno una localizzazione "altra" a Milano (luogo di fabbricazione, collocazione precedente, ripresa fotografica). Restano nel CSV ma **fuori da tutti i conteggi e dalla mappa**. Le coordinate di 1.664 di queste cadono fuori dal Comune (sono quelle dell'altra citta').
6. `tipo_scheda` e' la sigla ICCD (OA, D, RA, S, ...): disegni (D) e stampe (S) sono tipi a parte rispetto ai dipinti e alle sculture (OA). "Opere d'arte" in senso comune = OA + D + S + OAC. Nell'etichetta in italiano `VeAC` (1 scheda) e' una sigla di cui non e' scritto il significato nel dump: la etichetta e' una nostra lettura.

## 3. Titoli

7. **Il titolo e' spesso solo il tipo di oggetto.** Per 17.159 schede (62,5%) il titolo e' uguale al tipo di oggetto ("dipinto", "disegno", "reliquiario"). Il titolo vero, quando c'e', e' nel soggetto o nel titolo lungo. Per questo la ricerca guarda anche il soggetto.
8. **La forma della catalogazione e' scritta dentro il titolo**: "dipinto (opera isolata)", "disegno, elemento d'insieme"... Tolta dal titolo pulito se la stessa parentesi compare almeno 15 volte (71 forme diverse, elenco in `problemi_conteggi.json`, `forme_titolo`); 23.713 titoli modificati su 30.721. Il titolo originale e' nel file `../beni_culturali_milano.csv`.
9. **Architetture con coda vuota**: 522 titoli come `Casa Galimberti (casa)casa ( )`: tolta la coda (diventa `Casa Galimberti (casa)`); altri `casa ( )` ridotti a `casa`.
10. Titoli ripetuti due volte ("ritratto di X, ritratto di X"): ridotti a uno quando le due meta' sono identiche. Titoli molto lunghi (fino a 370 caratteri) restano.

## 4. Autori

11. **53,0% delle schede non ha autore** (14.565 su 27.459). Normale per reperti, architetture, stampe anonime, ma non e' un errore da riempire.
12. **I nomi sono scritti in due modi**: "Luigi Cagnola" e "Reni Guido". Abbiamo riunito le forme che hanno le stesse parole (indipendentemente dall'ordine, dagli accenti e da maiuscole/minuscole) e scelto la forma piu' frequente: 11 persone avevano piu' forme (es. "De Nittis Giuseppe" 8 volte e "Giuseppe De Nittis" 1 volta). Altre forme diverse della stessa persona restano separate (es. con o senza "Detto ..."). Il testo originale e' in `autore_originale`.
13. **Qualifiche dentro il nome**: "(attribuito)" 2.187, "(bottega)" 157, "(scuola)" 97, "(e aiuti)" 90, "(cerchia)" 84, "(maniera)" 82. Messe in `autore_qualifica`. Un "attribuito a X" conta come X nelle classifiche.
14. **Nomi abbreviati o tagliati**: "Uni", "Dien", "Cinc. A", "Hansen H" ... restano cosi' come sono (non sappiamo chi siano). 3.192 nomi distinti dopo la pulizia (sul totale delle sedi Milano).
15. **Piu' autori per scheda**: 1.498 schede (separati da `|`). Nelle classifiche la scheda conta una volta per ogni autore.

## 5. Datazioni

16. Il testo e' un intervallo con vari prefissi: `ca 1790-ca 1810`, `post 1520-ante 1560`, `(?) 1200-(?) 1299`, `ca 360 a.C-ca 340 a.C`, `1827/01/01-1827/12/31`. Abbiamo ricavato anno di inizio e fine del **primo** intervallo (581 schede ne hanno piu' d'uno: di solito opera + rifacimento) e il secolo del punto medio.
17. 1.543 schede (5,6%) non hanno data. Altre 152 hanno un testo che non siamo riusciti a leggere (`-`, `ca 1580-83-ca 1600`, secoli in numeri romani, `1227/00/00 post-`): restano senza anno, il testo e' conservato.
18. **Intervalli scritti al contrario**: 64 (es. `ca 1875-ca 1799`, `325 a.C-375 a.C`) invertiti da noi; altri 24 senza indicazione dell'era (`ca 299-ca 250`) lasciati senza anno perche' non si capisce se sono a.C. o d.C.
19. **Intervalli oltre 300 anni** (98, es. `1498/00/00-1932/00/00`): nessun secolo assegnato. Altre 80 schede hanno un solo estremo (`350 a.C-`): secolo preso da quell'unico anno. 12 schede a cavallo dell'anno 0 non hanno secolo.
20. Date a.C.: scritte `a.C`, `a.c`, `a. C`, `a C` e perfino `.360 a.C`: normalizzate. Anni a.C. salvati come numeri negativi.
21. Il secolo e' quello del punto medio: `1800-1899` -> XIX secolo; `1650-1750` cade sul confine e va al XVII o XVIII secondo il punto medio. Non e' un dato del catalogo.

## 6. Detentore (istituzione)

22. **68,6% delle schede non ha un detentore con nome** (18.849 su 27.459). Di queste 3.262 hanno solo un codice (`CulturalInstituteOrSite/...`) che nel dump non ha etichetta: cercato in tutte le 97 parti, nessun nome. Il piu' grosso, `DBunicoCG106788`, ha 3.195 schede (2.863 dipinti OA e 332 disegni D) e **tutte con le stesse coordinate** (45,472204 N, 9,188363 E, che e' dove sta Brera): e' probabile che sia una raccolta di Brera, ma e' una nostra deduzione e **non** l'abbiamo scritto nel dato. Valore nel file: `non indicata` (il codice e' in `istituzione_iri`).
23. Varianti dello stesso nome: apostrofo dritto/curvo ("d'Arte"/"d’Arte") unificato. Raccolte dello stesso museo con nomi diversi (es. le due raccolte del Castello Sforzesco) restano separate.

## 7. Luogo e indirizzo

24. **L'indirizzo e' quasi sempre solo "Milano"**: 10.799 schede (39,3%) hanno solo il comune, 10.715 (39,0%) nessun luogo; solo 4.156 (15,1%) hanno il nome di un sito (Accademia di Brera, Villa Necchi Campiglio, Palazzo Reale...) e 1.789 (6,5%) una via o piazza (1.139 sono "piazza Castello"). Totale con un luogo piu' preciso di "Milano": 5.945 (21,7%).
25. **Nomi di luogo con varianti**: "Palazzo Reala" (refuso di Palazzo Reale), "San Gottardo in Corte" e "Chiesa di San Gottardo in Corte", "S. Lorenzo Maggiore" e "Basilica di San Lorenzo Maggiore", sei grafie di Sant'Ambrogio. Unite con una tabella scritta a mano (`LUOGHI` in `06_pulisci.py`); tutte le altre grafie restano come sono.
26. **Valori inutili**: "Contenitore fisico" (165 + 423 "di: Collezione Grandi") e "non identificabile" (18): il primo senza nome e' trattato come luogo mancante; "Collezione Grandi" resta come nome.
27. **Un indirizzo che non c'e'**: 5 schede hanno come localita' "Castano Primo" (un altro comune) dentro l'indirizzo di Milano; le coordinate sono pero' a Milano (45,470 N). Lasciate come sono, segnalate qui.

## 8. Coordinate

28. 13.194 schede di sede Milano hanno coordinate; **2 avevano latitudine e longitudine scambiate** (es. Palazzo Gallarati Scotti: lat 9,19 long 45,47): riscambiate, colonna `coord_scambiate_corrette`.
29. **Controllo sul confine vero del Comune** (poligono del confine comunale, non un rettangolo): 13.193 dentro, **1 fuori** (`ArchitecturalOrLandscapeHeritage/0300101875`, Cascina Mirabello, 45,2948 N 9,1154 E: a circa 18 km a sud del centro di Milano, evidentemente sbagliata). Non viene disegnata sulla mappa; `coord_in_comune` = 0.
30. **Le coordinate sono quelle del detentore, non dell'oggetto**: 769 punti diversi per 13.193 schede; il punto piu' grande (Brera, 45,472204 N 9,188363 E) ne contiene 3.195 e altri quattro ne contengono ciascuno piu' di 1.000. Una chiesa o un palazzo possono avere coordinate proprie, un dipinto ha quelle del museo. La mappa mostra "dove sono conservate le schede", non "dove si trovano i monumenti".
31. 52,0% delle schede (14.265) non ha coordinate.

## 9. Link al catalogo

32. Il campo `url_catalogo` del dump punta a `www.catalogo.beniculturali.it/sigecSSU_FE/dettaglioScheda.action?keycode=ICCD...`, vecchio formato, ora dietro il controllo anti-bot (Anubis). Nel file pulito `url_catalogo` e' invece `https://catalogo.beniculturali.it/detail/<iri>` (es. `.../detail/HistoricOrArtisticProperty/0300211768`): il formato risulta dai risultati dei motori di ricerca per altre schede dello stesso catalogo; **non abbiamo potuto aprire le pagine** (anti-bot, non aggirato), quindi per le schede di Milano non e' verificato scheda per scheda. Il vecchio indirizzo e' conservato in `url_catalogo_dump`.

## 10. Aggiornamento

33. Il dump e' del 2023-12-01 ma le schede sono state aggiornate l'ultima volta nel 2022 (26.806) o nel 2023 (653). Il catalogo vivo oggi ha certamente piu' schede e non e' stato possibile leggerlo (anti-bot).
34. Proprieta' (`proprieta`, dal campo `dc:rights`): e' di chi e' il bene (Stato, ente religioso, privato...), non la licenza dei dati.
