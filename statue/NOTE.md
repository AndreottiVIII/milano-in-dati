# Statue e monumenti di Milano - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Ogni numero dice file e campo. Programmi in `scripts/` (numerati 01-08, si lanciano con `python -I -X utf8 <programma> <percorso assoluto di statue> [<percorso assoluto di milano-in-dati>]`, vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 0. AGGIORNAMENTO della sera del 1 novembre 2026 (vale al posto dei numeri delle sezioni 1, 4.1-4.3, 7 dove sono diversi)

Dopo il controllo a mano e la lettura delle iscrizioni delle lapidi (programma `scripts/06b_soggetti_da_iscrizioni.py`) e dopo aver letto anche i tag OSM `memorial:subject:wikidata`, `commemorates:wikidata`, `buried:wikidata`:
- **Controllo a mano delle coppie opera-persona trovate per nome: tolte 8** (`scripts/soggetti_esclusi.csv`, con il motivo): Luigi Riccardi (omonimo dubbio), Gian Giacomo Trivulzio (trovato un omonimo nato nel 1839, il mausoleo e' del 1518), Pompeo Litta Biumi (l'iscrizione dice storico morto nel 1852, trovato un pittore), Rachele Bianchi, Cesare Poli, Giorgio de Santi (solo il nome su OSM, omonimo non escludibile), Guido Ucelli (la targa e' per due persone, Guido e Carla), Mario Bobbio (trovato un omonimo nato nel 1960).
- **Iscrizioni:** 50 opere con un'iscrizione leggibile (non tutta in maiuscolo) e senza soggetto; il nome per esteso nel testo ha dato **31 persone** (accettata solo una corrispondenza esatta con una persona di Wikidata, e solo se il testo ne nomina una sola). Esempi: Ornella Vanoni, Giulio Natta, Alessandro Manzoni, Giuseppe Verdi, Gio Ponti, Fanny Mangili. Le iscrizioni tutte in maiuscolo (molte lapidi ai partigiani) non si leggono; le persone senza voce Wikidata (molti partigiani) restano senza sesso.
- **Soggetto riconosciuto per 215 opere su 777 (27.7%)**, non piu' 189 (24%). Persone distinte: 196. Coppie opera-persona: 225 (164 da collegamenti, 31 da iscrizioni, 30 da titoli).
- **Donne (persone distinte di sesso noto):** tutte le opere 9 su 194 (4.6%, 2.5-8.6%); statue, monumenti, sculture 4 su 99 (4.0%, 1.6-9.9%); solo statue e busti 3 su 41 (7.3%); **lapidi e targhe 3 su 80 (3.8%, 1.3-10.5%)** (prima 1 su 61: le iscrizioni hanno aggiunto Ornella Vanoni e Fanny Mangili); vie 6,6%. Le 9 donne: Belgiojoso (2021), Hack (2022), Vanoni (targa 2026), Callas (ex abitazione), Fanny Mangili (targa), Lina Merlin (targa), Valentina Doria (tomba), due busti antichi (Agrippina minore, Teodora). Lettura onesta: **poche, nello stesso ordine di grandezza delle vie**.
- **Piu' rappresentati:** il massimo e' **4 opere** (Alessandro Manzoni: monumento, tomba, due lapidi); poi 3 (Stoppani, Porta, Garibaldi, Verdi, Sant'Ambrogio). Vittorio Emanuele II: 1 opera.
- **Sorpresa invariata:** nessuna donna reale in un monumento o statua con anno di posa prima del 2021 (0 su 57 persone celebrate fino al 2020; poi Belgiojoso 2021, Hack 2022, su 59 persone datate in tutto). **La Madonna ha 7 opere, poco meno delle 9 donne reali dell'elenco** (non piu' "tante quante": le donne reali sono salite a 9).
- Correzioni di programma: il gruppo di mestiere non confonde piu' "benefattrice" con "attrice"; `wdlib.py`.
- Pagina: `docs/statue/index.html`, dati in `docs/statue/data/` (programma `scripts/pagina.py`).

## 1. In breve

1. **Il Comune di Milano non pubblica un elenco di statue, monumenti, lapidi o arte pubblica.** Ricerca CKAN con 24 parole chiave, 315 dataset trovati (`raw/search_all.json`): nessuno è l'elenco cercato. I due più vicini (ds599, ds617) sono capolavori dentro i musei.
2. **Le fonti utili sono tre, e si completano poco: Wikidata (CC0), OpenStreetMap (ODbL) e il catalogo ICCD (già in `../beni-culturali`).** Messe insieme e senza doppioni: **777 opere** (`pulito/opere.csv`): 431 solo in OSM, 238 solo in Wikidata, 97 in Wikidata e OSM insieme (2 di queste anche in ICCD), 1 in OSM e ICCD, 10 solo in ICCD.
3. **Cosa sono:** 218 lapidi e targhe, 172 sculture e installazioni, 96 monumenti, 86 statue, 53 murali e opere decorative, 45 monumenti funebri o tombe, 35 monumenti ai caduti, 24 altri memoriali, 21 cippi e stele, 19 busti, 8 fontane. Quelle che si possono chiamare statue e monumenti (senza lapidi, tombe, murali): **437**; di queste 344 senza indizi che stiano dentro una chiesa, un museo o un cimitero.
4. **Il soggetto (chi è raffigurato) si conosce solo per 189 opere su 777 (24%).** Per le altre manca: OSM ha 230 oggetti senza nome e quasi nessun `subject:wikidata`; il titolo "La Danza" o "Colonna" non dice chi. Questo limita tutto il resto: sono numeri su un campione piccolo.
5. **Donne: 7 su 177 persone di sesso noto (4,0%); nelle statue e monumenti 5 su 99 (5,1%); nelle lapidi 1 su 61 (1,6%).** Per le vie la stessa misura è 6,6% (140 su 2.110, `../donne-nelle-vie/out/percentuali.json`). Con così poche donne le differenze non sono nette: l'intervallo di incertezza (Wilson 95%) per le statue e i monumenti va da 2,2% a 11,3%, quello delle vie da 5,7% a 7,8%. Si può dire "poche, dello stesso ordine di grandezza delle vie", non "meno delle vie".
6. **Più rappresentati:** nessuno domina. Il massimo è 3 opere: Antonio Stoppani (busto, monumento, statua), Carlo Porta (busto, monumento, statua), Giuseppe Garibaldi (statua e due targhe) e Sant'Ambrogio. Vittorio Emanuele II compare in 1 opera (il monumento in piazza Duomo).
7. **La cosa più sorprendente:** vedi la sezione 8.

## 2. Fonti, una per una (anche in `pulito/inventario_fonti.csv`)

### 2.1 Comune di Milano (dati.comune.milano.it, CKAN)
- Ricerca: parole chiave monumenti, monumento, statue, statua, opere d'arte, arte pubblica, lapidi, lapide, targhe, patrimonio artistico, sculture, scultura, memoriale, fontane, busto, cippi, arredo urbano, street art, murales, patrimonio culturale, beni culturali, ricordo, caduti. Programma `scripts/01_search_ckan.py`, risultato `raw/search_all.json` (315 dataset, quasi tutti rumore: "caduti" e "opere pubbliche d'arte" ricercano per parola singola e trovano di tutto).
- **ds599** "Schede catalografiche di beni culturali siti nel Comune di Milano" (SIRBeC, Regione Lombardia): CSV scaricato il 1/11/2026 con curl da `https://dati.comune.milano.it/dataset/364a67d3-0734-49d3-b4b7-2c704eeadd24/resource/2c87c7c1-b007-4d9c-8d15-f252fd7328db/download/ds599_beni_culturali_siti_nel__c23i-gtvh_final.csv` in `raw/comune_ds599/ds599.csv`, **322 righe**, licenza **CC0** (`license_id = cc-zero`). Contenuto: 206 "capolavori" (dipinti, ceramiche...), 23 collezioni, 22 chiese, 22 palazzi, 19 musei, 18 apparati decorativi, 9 piazze e borghi. Solo 9 "statua", 10 "scultura", 5 "busto" e 2 "monumento funebre", tutti schede di musei, palazzi e chiese. **Non è arte pubblica: non usato nei conteggi.**
- **ds617** (opere nei musei) e **ds585** (architetture): CC0, individuati ma **non scaricati** (fuori tema).
- Confini dei NIL: riuso di `../citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson` (88 NIL, CC-BY), come in `../alberi`.

### 2.2 Wikidata (CC0)
- Due ricerche SPARQL (`scripts/03_wikidata_items.py`, risultati `raw/wikidata/A_p131.json`, `B_box.json`): elementi che sono statua (Q179700), monumento (Q4989906), memoriale (Q5003624), scultura (Q860861), targa commemorativa (Q721747) o arte pubblica (Q557141), anche tramite sottoclassi, (A) con luogo amministrativo (P131) dentro Milano, (B) con coordinate nel rettangolo 9,04-9,29 E / 45,38-45,55 N. Trovati **438** elementi.
- Poi `scripts/04_wikidata_entities.py` scarica con `wbgetentities` (lingua it/en) 2.357 entità: gli elementi, le persone raffigurate (P180), commemorate (P547), soggetto principale (P921), i creatori (P170), le classi, i luoghi, le professioni (P106). Cache `raw/wikidata/entities_cache.json` (92 MB, non per il repo). Il programma 06 aggiunge altre entità (candidati per nome) e `search_cache.json`, `sitelinks_cache.json`.
- **Tenuti 335 su 438.** Scartati: 57 senza una classe ammessa (palazzi, porte, sale di museo...), 28 che sono anche edificio (es. palazzo + "monumento"), 16 con coordinate fuori dal confine comunale (Sesto San Giovanni, Cormano, Cusano...), 2 senza coordinate e senza P131 milanese (conteggi in `pulito/_lavoro/stage1_log.json`).
- Cosa manca: 140 opere senza coordinate (lapidi e opere dentro chiese e musei); anno di posa per 103 delle 335; il soggetto (P180/P547/P921) c'è solo per una parte.

### 2.3 OpenStreetMap (ODbL)
- Una richiesta Overpass (`scripts/02_overpass.py`) sul Comune di Milano (relazione admin_level 8, wikidata=Q490): `historic=memorial|monument`, qualsiasi `memorial=*`, `tourism=artwork`, `historic=wayside_cross`. File `raw/osm/overpass_statue.json`, **561 elementi** (513 punti, 45 linee/aree, 3 relazioni), momento dei dati OSM **2026-11-01T19:52:06Z**.
- Tenuti 534: tolte 21 pietre d'inciampo (hanno un filone a parte in `../pietre-inciampo`) e 6 "biciclette bianche" (ghost bike).
- Tag usati: `name`, `memorial`, `artwork_type`, `start_date`, `artist_name`, `artist:wikidata`, `subject:wikidata`, `wikidata`, `inscription`. Il 57% ha un nome (318 su 561); `subject:wikidata` in 30; `start_date` in 69; l'`inscription` (testo della lapide) in 129 ma non è stata letta con un programma per ricavare i nomi.
- Licenza: ODbL. Si può ripubblicare citando "© OpenStreetMap contributors" e con la stessa licenza per i dati derivati (obbligo share-alike). Regola del JOURNAL: nel repo meglio solo risultati e programmi, non il JSON grezzo.

### 2.4 ICCD (già scaricato in `../beni-culturali`, nessun nuovo scarico)
- `../beni-culturali/pulito/beni_milano.csv`, 27.459 schede con sede a Milano (dump ArCo 2.0 del 1/12/2023). Licenza: metadati CC BY 4.0 secondo il catalogo, CC BY-SA 4.0 secondo ArCo/Zenodo (non risolto, vedi la NOTE di beni-culturali).
- Cercate le schede con `tipo_oggetto` statua (465), lapide commemorativa/celebrativa/documentaria (107+4+32), gruppo scultoreo (38), busto (37), monumento ai caduti (11), targa (7), cippo (7), stele (4), monumento (3): **715 schede**. Solo **13 utili**: senza istituzione detentrice, con coordinate proprie (non quelle di un museo: tolti i punti con 10 schede o più) e dentro il Comune. 470 non hanno coordinate, 228 hanno quelle di un museo o deposito. Tre si fondono con opere di OSM/Wikidata, 10 restano solo ICCD (8 monumenti ai caduti, 2 schede "statua" senza titolo né soggetto: da guardare).
- L'ICCD aggiunge quasi niente di arte pubblica: le sue statue sono per lo più in Duomo e chiese, senza ubicazione precisa.

### 2.5 Fonti viste e non usate
- Regione Lombardia (Lombardia Beni Culturali, SIRBeC): è la fonte da cui il Comune ha estratto ds599; non cercata a parte.
- Wikimedia Commons (categorie "statue di Milano"): ricche ma senza dati strutturati sul soggetto; non scaricate in questa fase.
- Elenchi di Wikipedia sui monumenti di Milano: testo CC BY-SA, non strutturato; non usato.

## 3. File prodotti (cartella `pulito/`)

| File | Contenuto |
|---|---|
| `opere.csv` | **777 righe, una per opera.** Colonne richieste: `id, nome, tipo, soggetto, soggetto_qid, genere soggetto, professione, anno posa, autore, lon, lat, NIL, fonte`; poi colonne in più: `id_nil, soggetto_tipo, soggetto_come_trovato, professioni_wikidata, nascita_soggetto, morte_soggetto, epoca_posa, collocazione_dedotta, qid_opera, osm_id, iccd_iri, anno_fonte, anno_nota, tipo_wikidata, flag`. Più persone: valori separati da ` \| `. |
| `soggetti.csv` | **199 righe, una per coppia opera-persona**: persona, QID, genere, nascita, morte, gruppo di professione, come è stata trovata. È la tabella per tutte le percentuali. |
| `per_nil.csv` | opere, statue/monumenti, lapidi, murali, persone, donne e opere per km² per ciascuno degli 88 NIL |
| `piu_rappresentati_tutte/monumenti/lapidi.csv`, `donne_rappresentate.csv` | classifiche delle persone |
| `professioni_tutte/monumenti/lapidi.csv`, `epoca_per_professione_monumenti.csv` | gruppi di professione |
| `per_decennio.csv` | opere datate per decennio |
| `riepilogo.json`, `controlli.json`, `tipo_per_fonte.csv`, `inventario_fonti.csv` | tutti i conteggi di questa nota |
| `_lavoro/` | passaggi intermedi: `stage1.json`, `stage2.json`, `ricerche_soggetti.csv` (ogni soggetto cercato per nome: esito e motivo), log |

### Come ho costruito `opere.csv`
1. **Wikidata:** ogni elemento ha una classe (P31) che decide il `tipo`; scartati edifici e porte. Il `soggetto` viene da P180 (raffigura), P547 (commemora), P921 (soggetto principale).
2. **OpenStreetMap:** `tipo` dai tag (`memorial=plaque` = lapide o targa, `memorial=statue`/`artwork_type=statue` = statua, ecc.). Unione con Wikidata: 85 oggetti per QID (il tag `wikidata`), altri 17 per vicinanza (entro 60 m) più una parola significativa del nome in comune.
3. **ICCD:** come in 2.4; unione per vicinanza (entro 150 m e nome simile, o 60 m per i monumenti ai caduti).
4. **NIL:** punto in poligono sui 88 NIL; entro 100 m dal confine si assegna il NIL più vicino (flag `NIL_per_vicinanza`, nessun caso). 637 opere hanno NIL, 140 no (senza coordinate).
5. **Soggetto non collegato:** per 128 opere senza persona collegata ma con un titolo del tipo "Monumento a X" o "Targa a X" (o un nome proprio come titolo) cerco X su Wikidata (`wbsearchentities`) e accetto solo una corrispondenza **esatta** del nome con una **persona** (P31 = umano): 33 accettati per nome unico, 3 per "unico italiano tra omonimi", 2 per "omonimo molto più noto" (più di 15 pagine Wikipedia e almeno 5 volte il secondo). 87 non risolti: nessuna corrispondenza (59), corrispondenza ma non persona (24, es. "Colonna del Leone"), omonimi non risolvibili (9, es. Giovanni Ardizzone: due persone). Ogni esito è in `pulito/_lavoro/ricerche_soggetti.csv`.
6. **Genere:** **solo** il campo P21 (sesso o genere) di Wikidata della persona raffigurata. Mai dal nome. Come per le vie.
7. **Persona reale:** umano (Q5) ma non una figura biblica, mitologica, leggendaria o di fantasia (che Wikidata a volte marca "umano"): la Madonna e gli apostoli sono "figura religiosa", non persona. I santi storici (Sant'Ambrogio, Carlo Borromeo) sono persone reali e nel gruppo "religioso o santo" (flag P411).
8. **Collocazione dedotta:** dai contenitori di Wikidata (P131, P276, P361) guardando di che tipo sono (chiesa, museo, cimitero; piazze e vie contano come spazio aperto). Per OSM e ICCD non c'è nulla e si assume "non indicata". È una **ipotesi grezza**.
9. **Gruppo di professione:** il primo gruppo corrispondente tra le professioni (P106) di Wikidata, nell'ordine scritto; se non ce ne sono, la descrizione breve (es. "vittima di Mauthausen" = "vittima o caduto"). Gruppi: sovrano o nobile, religioso o santo, militare o forze dell'ordine, patriota o resistente, artista, scienziato o medico, scrittore o giornalista, politico o giurista, imprenditore o benefattore, sportivo, vittima o caduto. Regole in `scripts/wdlib.py`.

## 4. Numeri principali (tutti da `pulito/riepilogo.json` e `pulito/controlli.json`)

### 4.1 Quante opere con una persona reale
- **189 opere su 777** hanno una persona reale riconosciuta (184 con una persona, 5 con più persone). 34 sono monumenti ai caduti o a un evento (soggetto collettivo), 20 raffigurano una figura religiosa, mitologica o di fantasia, 534 non hanno soggetto determinato.
- **Statue, monumenti e sculture con persone reali: 107 opere** (75 se si tolgono quelle con collocazione dedotta in chiesa, museo o cimitero; `opere_con_persone` in `riepilogo.json`, sezione `genere`); lapidi e targhe con persone: 60; monumenti funebri: 19.
- Persone distinte: 179 in tutto; 99 nelle statue/monumenti/sculture; 63 nelle lapidi e targhe.
- Come sono state trovate le 199 coppie opera-persona: 161 collegate in Wikidata/OSM, 38 cercate per nome.

### 4.2 Donne (confronto con le vie 6,6%)
| Insieme | Persone distinte di sesso noto | Donne | Quota | Intervallo 95% |
|---|---|---|---|---|
| Tutte le opere | 177 | 7 | 4,0% | 1,9% - 7,9% |
| Statue, monumenti, sculture | 99 | 5 | 5,1% | 2,2% - 11,3% |
| ... solo con collocazione non in chiesa/museo/cimitero | 74 | 4 | 5,4% | 2,1% - 13,1% |
| Solo statue e busti | 41 | 3 | 7,3% | 2,5% - 19,4% |
| Lapidi e targhe | 61 | 1 | 1,6% | 0,3% - 8,7% |
| Vie (donne-nelle-vie, santi compresi) | 2.110 | 140 | 6,6% | 5,7% - 7,8% |

Senza i santi le quote salgono poco (statue e monumenti 5,7%; vie 5,1%). Solo con le persone collegate in modo strutturato (senza la ricerca per nome) 3,5% per le statue/monumenti. Le 7 donne: Cristina Trivulzio di Belgiojoso (monumento 2021), Margherita Hack (statua 2022), la scultrice Rachele Bianchi (monumento, senza anno), due busti antichi (Agrippina minore, imperatrice Teodora), una tomba (Valentina Doria), una targa (Lina Merlin).
- Autori: tra le 174 attribuzioni d'autore che hanno un elemento Wikidata, 168 sono a uomini, 2 a donne (Sissi, Nina Akamu), 4 senza sesso noto.

### 4.3 Chi è più rappresentato
Per numero di opere distinte (`pulito/piu_rappresentati_tutte.csv`): Antonio Stoppani 3, Carlo Porta 3, Giuseppe Garibaldi 3 (statua + 2 targhe), Sant'Ambrogio 3, poi con 2: Alessandro Manzoni, Carlo Borromeo, Carlo Cattaneo, Francesco d'Assisi, Giuseppe Mazzini, Giuseppe Parini. Napoleone Bonaparte 2 (statue/sculture). Vittorio Emanuele II: 1 (monumento di piazza Duomo, con altre figure). Con questi numeri una differenza di una sola opera non conta. La figura più rappresentata in assoluto è la **Madonna**: 7 opere (poi Gesù 3, san Bartolomeo 3).

### 4.4 Epoche di posa (solo le 143 opere con un anno, il 18% del totale)
| Epoca | Tutte | Statue/monumenti | di cui con collocazione non in chiesa/museo/cimitero |
|---|---|---|---|
| prima del 1861 | 31 | 25 | 15 |
| 1861-1921 (Italia liberale) | 41 | 38 | 35 |
| 1922-1943 (fascismo) | 14 | 13 | 10 |
| 1944-1969 (dopoguerra) | 9 | 7 | 6 |
| 1970-1999 | 18 | 16 | 16 |
| dal 2000 | 30 | 22 | 20 |
Il decennio con più opere datate sono gli anni 2010 (15) e gli anni Dieci del Novecento (13), poi i Venti (11). I monumenti ai caduti datati (17 su 35) hanno mediana 1923. Le opere datate dopo il 2000 sono sovrarappresentate perché Wikidata e OSM registrano meglio il recente (vedi limiti). Per 58 persone con anno di morte e di posa, mediana **13 anni tra la morte e il monumento**; il 55% entro 30 anni dalla morte; il 28% oltre 100 anni (santi e personaggi antichi); solo 2 persone erano ancora in vita (Bernabò Visconti 1363, Napoleone 1807).

### 4.5 Professioni (`pulito/professioni_monumenti.csv`, incidenze nelle statue/monumenti/sculture)
Religiosi e santi 23, politici e giuristi 21, artisti 19, scrittori e giornalisti 19, scienziati e medici 16, sovrani e nobili 4, militari e forze dell'ordine 3, vittime 2. **Pochi militari** (3): i monumenti ai caduti sono collettivi (34 senza una persona). Nelle lapidi: politici e giuristi 19, artisti 8, scienziati 7, scrittori 7, vittime 6. Le professioni sono quelle scritte da Wikidata e il gruppo è una euristica (esempi di errore: Garibaldi e Napoleone finiscono in "politico o giurista", Costantino I in "religioso o santo").

### 4.6 Mappa per NIL (`pulito/per_nil.csv`)
Su 637 opere con coordinate: **DUOMO 148, BRERA 52, PARCO SEMPIONE 25, GUASTALLA 23, LAMBRATE-ORTICA 21, CITTA' STUDI 19, PORTA GARIBALDI-PORTA NUOVA 18, STAZIONE CENTRALE-PONTE SEVESO 17, GIARDINI PORTA VENEZIA 16, XXII MARZO 16.** Duomo e Brera da soli: 200 su 637 (31%). Per km²: Giardini Porta Venezia 64, Duomo 63, Parco Sempione 53, Brera 32. **16 NIL su 88 non hanno nessuna opera.** (La concentrazione al centro dipende anche da dove Wikidata e OSM guardano di più: vedi limiti.)

### 4.7 Lapidi e targhe
218 in tutto: 157 solo in OSM (il 38% delle lapidi OSM ha un nome), 56 solo in Wikidata (molte create da un progetto locale), **solo 5 in entrambe**. Ne esistono certamente migliaia in città: questa è la parte meno completa. La stima grezza di sovrapposizione dà ~1.800 (vedi 5). Soggetto riconosciuto per 60 lapidi: 19 politici e giuristi, 8 artisti, 7 scienziati, 7 scrittori, 6 vittime.

## 5. Quanto è completo
Sovrapposizione Wikidata/OSM (`controlli.json`, `sovrapposizione_wikidata_osm`; stima "cattura-ricattura" grezza che assume fonti indipendenti, quindi **solo un indizio**):
- **statue, busti, monumenti** (146 non in chiese/musei/cimiteri): 70 in Wikidata, 132 in OSM, 58 in entrambe: stima totale ~159. Le grandi opere sono ben coperte dalle due fonti insieme.
- **sculture e installazioni**: 114 trovate, 19 / 105 / 10: stima ~200.
- **lapidi e targhe**: 212 trovate, 55 / 162 / 5: stima ~1.800. Qui la copertura è bassissima.

## 6. Limiti dei dati
1. **Non esiste un registro ufficiale**. Il numero 777 è quello che Wikidata, OSM e ICCD riescono a vedere, non il numero di opere di Milano.
2. **Il soggetto manca per tre opere su quattro** (534 su 777 "non determinato"). I risultati su donne, professioni ed epoche si basano su 189 opere, spesso su meno (es. 99 persone per le statue e i monumenti).
3. **Poche donne = intervalli larghi.** 5 donne su 99; passare da 5 a 7 donne sposta la quota da 5% a 7%.
4. **Gli anni di posa ci sono per il 18% delle opere**, e sono più frequenti per le opere recenti e per quelle in Wikidata. Gli anni di Wikidata (P571, "inizio") sono spesso la data di inaugurazione, non sempre. Le epoche vanno lette come ordine di grandezza. Date imprecise (decennio o secolo) lasciate vuote, campo `anno_nota`.
5. **Doppioni e fusioni:** l'unione per vicinanza e nome può mancare doppioni o unire due opere vicine con nomi simili. Un solo gruppo di opere con stessa posizione e stesso tipo (2 opere) nel controllo (`controlli.json`).
6. **Collocazione dedotta** (chiesa, museo, cimitero): solo da Wikidata e solo se c'è un contenitore. Esempi sbagliati noti: il monumento a Costantino (davanti a San Lorenzo) risulta "chiesa"; "Legge Nuova" risulta Duomo. Per OSM e ICCD non si sa. 77 opere "museo o edificio", 33 "chiesa o interno", 23 "cimitero".
7. **Soggetto per nome = omonimi possibili.** "Nome unico" vuol dire una sola persona con quel nome su Wikidata, non che sia verificata. Esempi da controllare a mano: Giorgio De Santi (lapide), Stefano Cerri, Cesare Poli, Francesco Rigoldi (`ricerche_soggetti.csv`). Tutte le 38 coppie trovate per nome sono marcate in `soggetto_come_trovato`; i totali senza di esse sono nelle righe `__solo_collegate_in_wikidata_osm` di `riepilogo.json`.
8. **Gruppo di professione = euristica** sulla prima professione di Wikidata, con errori.
9. **Wikidata ha elementi senza etichetta** (es. Q133658673, un lapide a Enrico Pedenovi) e descrizioni mancanti: 17 persone senza professione e 2 senza sesso.
10. **OSM è volontariato**: nomi in forme diverse, tag mancanti; 230 oggetti senza nome. Dati OSM del 1/11/2026: cambieranno.
11. **Distorsione verso il centro e verso le opere note**: Duomo e Brera hanno il 31% delle opere con coordinate; le periferie sono coperte soprattutto da OSM.
12. **Le due schede ICCD "statua" senza titolo** (MI0776, MI0777) restano nell'elenco ma non hanno soggetto.
13. **Le fontane, i murali e le opere decorative** sono contati a parte (8 fontane, 53 murali): non sono né statue né monumenti a persone.
14. **Console Windows**: il terminale mostra "?" per alcune lettere accentate; i file sono UTF-8 e giusti.

## 7. La cosa più sorprendente
**Tra i monumenti e le statue con un anno di posa nessuno è dedicato a una donna reale prima del 2021.** Sono 54 le persone celebrate da monumenti datati fino al 1999 (11 prima del 1861, 30 nell'Italia liberale, 8 sotto il fascismo, 1 dopoguerra, 4 tra 1970 e 1999) e zero donne; poi arrivano due: Cristina Trivulzio di Belgiojoso (2021) e Margherita Hack (2022), su 5 persone celebrate dal 2000. La donna più rappresentata in tutta la scultura pubblica milanese è invece la Madonna (7 opere), tante quante le sette donne reali di tutto l'elenco messe insieme. Il campione è piccolo (le sole 54 persone con anno): il fatto è solido sui dati che abbiamo, non su tutti i monumenti di Milano.
Altri spunti: nessun re o generale in cima (il più ripetuto ha 3 opere); la mediana tra la morte e il monumento è 13 anni; 16 NIL su 88 non hanno nessun monumento; le lapidi sono la parte meno coperta dai dati aperti (5 su 218 in entrambe le fonti).

## 8. Cosa può mostrare una pagina
- Una mappa dei punti (637 con coordinate) filtrabile per tipo e collocazione; un cartogramma per NIL (opere o opere per km²).
- "Chi c'è": le persone più rappresentate, per gruppo di professione; confronto con le vie (6,6% donne) con la dicitura "limiti dei dati" e gli intervalli.
- Una linea del tempo per decennio (con la nota che sono il 18% delle opere) e le epoche: Italia liberale, fascismo, dopoguerra, recente.
- Il grafico del gap tra morte e monumento.
- Le sette donne con le loro opere; il confronto Madonna / donne reali.
- Le lapidi come caso di dati aperti ancora vuoti: l'invito a completare OSM e Wikidata.
- Licenze da citare: Wikidata CC0, OSM © contributors ODbL (share-alike sui derivati), ICCD (CC BY 4.0 o CC BY-SA 4.0: da chiarire), Comune di Milano per i NIL (CC-BY).

## 9. Da decidere / non fatto
- Leggere le `inscription` di OSM (129) per ricavare i nomi delle lapidi senza titolo (un programma con regole molto prudenti).
- Rivedere a mano le 38 coppie per nome e gli omonimi non risolti (es. Giovanni Ardizzone).
- Estendere a Wikimedia Commons / Wikipedia per le date di posa.
- Chiarire la licenza ICCD (CC BY o CC BY-SA) prima di ripubblicare righe ICCD.
- Cercare una fonte per la collocazione (aperto/chiuso) delle opere OSM e ICCD.
