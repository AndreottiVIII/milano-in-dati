# Povertà educativa - FASE 1 + pagina (nidi, tempo pieno, mense, INVALSI, NEET)

Scaricato il 1-2 novembre 2026. Programmi in `scripts/`, tabelle pulite in `pulito/`, grezzi (non fidati, mai eseguiti) in `raw/` (elenco con sha256 in `raw/fonti.csv`). Pagina: `docs/poverta-educativa/index.html` + `data/` (scritti da `scripts/pagina.py`). Ogni numero del testo ha l'origine in `docs/poverta-educativa/data/riepilogo.json`. Idea di partenza: Osservatorio povertà educativa #conibambini (Con i Bambini + Openpolis). **Nessun file di Openpolis usato**: non ho trovato un loro dato aperto comunale con licenza scaricabile; i loro numeri sui nidi sono elaborazioni di dati ISTAT, che qui sono scaricati alla fonte.

## 1. In breve
1. **Il confronto tra città è solido**; dentro Milano i dati sono scarsi (nidi: solo l'elenco delle sedi, fermo al 2018/19).
2. **Tempo pieno primaria (MIM, a.s. 2024/25)**: Milano 82,1% (statali 96,8%, paritarie 26,9%), invariato dal 2015 (82,2%); Italia 34,1% -> 42,5%. Milano ha il valore più alto delle 14 città nelle statali (Firenze 91,8%). Tra i CAP il tempo pieno (tutte le scuole) è negativamente legato al reddito (Spearman -0,39, IC95 -0,65/-0,07) perché i CAP ricchi hanno più alunni nelle paritarie (+0,41, +0,08/+0,66). Nelle sole statali -0,54, ma solo 4 CAP su 38 sono sotto il 90% (tre con reddito oltre 70.000 euro).
3. **Nidi (ISTAT 2024)**: Milano 49,3 posti ogni 100 bambini 0-2 (14.024 posti; Italia 33,2; Lombardia 39,4); è 4ª tra le 14 città (Firenze 58,6, Bologna 57,4, Roma 53,8). Metà dei posti è privata (24,7 pubblici + 24,6 privati per 100 bambini; Bologna 40,5 + 16,9).
4. **Mense (MIM edilizia, solo statali)**: alunni di primaria statale in scuole con uno spazio mensa: Milano 94,2%, Torino 99,2%, Roma 46,4%, Napoli 2,5%, Catania 2,9%, Italia 56,3%. Misura lo spazio, non il servizio.
5. **INVALSI, dispersione implicita (3ª media, 2024-25)**: Milano 6,9% (2ª tra le 14 dopo Bologna 6,4%; Italia 12,3%; Napoli 21,9%, Palermo 25,9%). Per origine, provincia di Milano: nativi 5,7%, stranieri di 1ª generazione 24,6%, di 2ª 9,2% (Italia 11,6 / 22,5 / 10,4).
6. **Tra le 14 città il reddito medio per contribuente (MEF 2024) segue gli indicatori**: Spearman +0,93 con i posti nido, +0,85 con il tempo pieno nelle statali, -0,91 con la dispersione in 3ª media (n=14; riassume la distanza Nord-Sud, non è una causa). Milano ha il reddito più alto ma è quarta per i nidi.
7. **La cosa più sorprendente** (scelta per la pagina): a Milano il tempo pieno nelle statali è già al 96,8% (il più alto tra le grandi città) e il divario è soprattutto tra statale e paritaria, più che tra quartieri; i CAP più ricchi hanno meno tempo pieno perché vanno di più alle paritarie. In seconda battuta: Milano è ferma da 10 anni mentre le altre salgono.

## 2. Fonti (file, licenza, note) - dettaglio e sha256 in `raw/fonti.csv`
| Fonte | Cosa | Licenza | Note |
|---|---|---|---|
| ISTAT IstatData (SDMX) flusso `47_850_DF_DCIS_SERVSOCEDU1_6` "Servizi sul territorio - prov. e com." | posti autorizzati (AUTP), posti per 100 bambini 0-2 (P_100CH_Y0_2), servizi (SERV), per titolare 1 privato / 2 pubblico / 9 totale, 2013-2024; 6 città, e (scarico a parte) 14 città, Italia (IT), Lombardia (ITC4) | CC BY 4.0 (note legali ISTAT: "salvo diversa indicazione") | richiesta `data/IT1,<flusso>,1.0/A.<aree>...` con `Accept: application/vnd.sdmx.data+csv`; poche chiamate in tutto |
| ISTAT stesso, flusso `..._3` "Servizi offerti dai comuni" | utenti (USSSPM), spesa (TOTEXP) | idem | per Milano usato per gli utenti dei servizi comunali |
| ISTAT comunicato 2023/24: tavole e report; report 2022/23 | solo regioni, nessun comune | - | consultati, non usati |
| ISTAT DF_DCSS_LCAS_FRISC_4 (Censimento permanente, frequenza del nido, grandi comuni) | tutte le celle vuote (flag J) | - | scaricato, **non usabile** |
| MIM, dati.istruzione.it/opendata: DS0090 / DS0100 (alunni per tempo scuola, statale/paritaria), 2015/16-2024/25 | 20 file nazionali (6,5 MB statali, 0,5 MB paritarie), filtrati per comune con l'anagrafe delle scuole (filone `scuole/raw/miur`) | IODL 2.0 | 0 alunni senza comune in tutti i 20 file |
| MIM edilizia scolastica statale, `EDIAMBFUNZSTA` 2024/25 | campo MENSA per scuola e edificio | IODL 2.0 | dati caricati dagli enti locali |
| INVALSI Servizio statistico, open data "Eccellenza accademica e dispersione scolastica implicita" (agg. 3/12/2025) | % studenti a rischio dispersione implicita (grado 8) / in dispersione implicita (grado 13), per Italia, regione, provincia, comune istituto principale, comune plesso, SLL; 2017-18...2024-25 | Creative Commons ("anche a scopi commerciali, citando la fonte"; versione non scritta nella pagina di questo dataset; CC BY 4.0 IT nella sezione open data) | **nessuna registrazione** per la sezione Open data; "Popolazione" e "Campione" la richiedono (non usati). Scaricato anche "info territoriali classi" (metadati di classe, nessun risultato): cancellato |
| Comune di Milano ds47 (nidi, sedi 2016/17-2018/19), ds27 (residenti per NIL), ds964 (NIL) | già su disco (filoni scuole, citta-15-minuti) | CC BY | |
| ISTAT Bes dei territori 2025 (filone benessere), MEF IRPEF comuni e CAP (filone redditi) | NEET, 4-5 anni, utenti servizi comunali, competenze 3ª media (Città metropolitane); reddito per comune | CC BY 4.0 / CC BY 3.0 | |

Cercato e **non trovato / non aperto**: posti e liste d'attesa dei nidi del Comune di Milano (CKAN: 30 parole chiave, 468 dataset, solo ds47 e gli elenchi ds709/678); iscritti per nido; refezione scolastica (solo tariffe ds2427/2428); abbandono scolastico (ELET) per comune; INVALSI per scuola o quartiere (riservati alle scuole). I dataset "other-at" del MIM ripubblicati dal Comune non sono stati usati (i dati si prendono dal MIM).

## 3. Controlli (in `pulito/controlli_build.json` e `docs/poverta-educativa/data/riepilogo.json`)
- ISTAT: posti pubblici + privati = totale in tutte le 72 celle (6 città x 12 anni); i due scarichi coincidono sui valori comuni.
- Milano: denominatore ISTAT implicito 28.446 bambini 0-2 (2024) contro 27.539 del Comune (ds27): 3% in più.
- ds47: 371 / 373 / 378 sedi distinte nei tre anni; 66 sedi 2018/19 senza coordinate (17%); tutte hanno il municipio.
- MIM: totale alunni primaria Milano (st.+par.) 2024/25 = 52.353; 14 città + altri comuni = Italia; reddito Milano 40.316 euro = valore del filone redditi.
- NIL: 65 con scuole primarie; 3.815 alunni (7,3%) di scuole non agganciate a un NIL.

## 4. Limiti (visibili anche sulla pagina)
1. **Serie nidi di Milano con salti**: posti pubblici 9.757 (2019) -> 6.535 (2020), privati 1.836 (2021) -> 6.848 (2022), servizi privati 97 -> 278. Gli utenti dei servizi del Comune restano 25-29 ogni 100 bambini (denominatore ds27) e le sedi del ds47 non cambiano: non sembra un fatto reale. Non spiegato (ipotesi: cambio di fonte per il privato). Rapporto 2013: 46,5, 2021: 27,8, 2022: 48,0. Le altre 5 città non hanno salti.
2. Posti autorizzati, non occupati; nessuna retta; "privato" comprende convenzionati col Comune.
3. Dentro Milano, nidi: sedi, non posti; 2018/19; classificazione comunale/privato cambiata tra anni (174 comunali nel 2016/17, 27 nel 2018/19); legame sedi/reddito per NIL nullo (rho +0,01, n=63) ma l'indicatore è debole.
4. Tempo pieno: classificazione MIM, alunni per scuola e non per residenza; paritarie = private riconosciute; private non paritarie assenti.
5. Mensa = spazio nell'edificio, non servizio; 2,4% degli alunni di Milano in scuole assenti dal file edilizia (Palermo 22,7%).
6. INVALSI: dispersione implicita non è abbandono; per origine solo Italia e provincia; copertura 93,2% a Milano (grado 8).
7. Bes: Città metropolitana (133 comuni).
8. Reddito: per CAP e per contribuente; il CAP della scuola non è quello degli alunni; reddito per NIL stimato (media dei CAP pesata con i civici stimati, filone citta-15-minuti).
9. Spearman su 14 città: indicativo, e il reddito riassume il divario Nord-Sud.

## 5. Come ripetere (percorsi assoluti; PE = .../milano-in-dati/poverta-educativa, P = .../milano-in-dati)
```
python -I -X utf8 PE/scripts/search_comune.py PE/raw/comune/search_comune.json
python -I -X utf8 PE/scripts/download_miur_tempo.py PE/raw/miur
(ISTAT: tre richieste SDMX documentate in raw/fonti.csv; INVALSI: link dalla pagina della sezione Open data, vedi raw/fonti.csv; EDIAMBFUNZSTA 2024/25 da dati.istruzione.it)
python -I -X utf8 PE/scripts/fonti.py PE
python -I -X utf8 PE/scripts/build.py PE P
python -I -X utf8 PE/scripts/pagina.py PE P P/docs
```
