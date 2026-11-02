# Filone "Rifiuti e raccolta differenziata" (rifiuti/)

Fase 1 + pagina (`docs/rifiuti/index.html`). Dati scaricati il 1-2 novembre 2026. Tutto ripetibile con i programmi in `scripts/` (vedi STATO.md).

## 1. Fonti e licenze

| Cosa | Fonte | Anni | Licenza | File in raw/ |
|---|---|---|---|---|
| Rifiuti per comune (tonnellate per tipo, abitanti) | ISPRA, Catasto Rifiuti, "Download dei dati comunali" (`get/getDettaglioComunale.csv.php?aa=ANNO`), aggiornato 22/7/2026 | 2010-2024 | CC BY 4.0 (note legali ISPRA, isprambiente.gov.it/it/note-legali; sul sito del Catasto non c'e' una licenza scritta a parte) | `ispra_comuni/rifiuti_comuni_ANNO.csv` (15 file, ~2,7-3,0 MB) |
| Costi di gestione pro capite per comune | ISPRA, Catasto Rifiuti, "Costi gestione RU" (`costi/getCostiComunaleproc.csv.php`) | 2011-2024 | come sopra | `ispra_costi/costi_procapite_ANNO.csv` |
| Milano: serie del Comune (controllo) | Comune di Milano CKAN: ds857, ds858 (catasto ISPRA ripubblicato), ds859, ds860 (costi), ds572 (differenziata), ds524 (Milano e limitrofi 2000-2016), ds849-856 (rifiuti urbani per CER 2010-2020), ds693, ds615 | varie | CC BY / "Other (Attribution)" | `comune_milano/dsNNN.csv`, ricerca in `comune_milano_search_rifiuti.json` |
| TARI incassata | bilancio-comune (capitoli del rendiconto), `docs/bilancio-comune/data/capitoli_usati.csv`, voce `rifiuti` | 2015-2025 | CC BY | non copiato (sola lettura) |
| Notti dei turisti | filone turisti, `docs/turisti/data/serie_totale.csv` | 2000-2025 | CC BY | non copiato |
| Indicatore ISTAT BES rifiuti (controllo) | `benessere/pulito/milano_serie.csv`, codici 10AMB024P e 10AMB017, territorio "Milano" (= citta' metropolitana) | 2010-2023 | CC BY 4.0 | non copiato |
| Prezzi | indice FOI da `bilancio-comune/pulito/indice_prezzi_annuo_FOI_da_strand12.csv` | 1996-2025 | ISTAT | non copiato |

Non usati: Regione Lombardia / ARPA O.R.SO. (dati.lombardia.it): la ricerca col catalogo Socrata ha dato 404 sull'endpoint; ISPRA e Comune danno gia' tutto cio' che serve (rifiuti e costi per comune). Se serve la divisione per materiale dei comuni lombardi in modo piu' fine (O.R.SO. ha le frazioni merceologiche), e' da fare dopo, da ricercare a mano. Tentativi: solo `raw/probe/lomb_cat.json` (risposta 404).

Rate: un file ISPRA per volta, pausa 3 s, User-Agent che dichiara chi siamo. Nessuna registrazione, nessuna verifica superata. **Alla prima richiesta del file dei costi 2020 il sito ha risposto con una pagina di verifica JavaScript (cookie di sessione) invece del CSV**: non l'abbiamo eseguita ne' aggirata; la risposta e' in `raw/ispra_costi/costi_procapite_2020_prima_risposta_sfida_js.html` (non aprire); ripetuta la stessa richiesta dopo 20 secondi il CSV e' arrivato normalmente.

## 2. Come sono fatti i file ISPRA

- Rifiuti: una riga per comune (o "aggregazione": comuni uniti in un consorzio, con le righe dei singoli comuni "Vedi aggregazione" senza dati). 7.900-8.100 righe l'anno. Prime 2 righe: titolo e intestazione (25 colonne, uguali in tutti gli anni: controllato). Numeri all'italiana ("1.412,641", "-" = nessun dato), CRLF, righe che iniziano con 4 tabulazioni. Colonne: abitanti, tonnellate di umido, verde, carta, vetro, legno, metallo, plastica, RAEE, tessili, selettiva, C&D, pulizia stradale a recupero, ingombranti a recupero, altro, totale RD, ingombranti a smaltimento, indifferenziato, totale RU, % RD.
- Costi: righe per comune o aggregazione (`Numero di comuni` > 1), euro per abitante, voci CRT, CTS, (CAC, CGIND), CRD, CTR, (CGD), CSL, CC, CK, (Altri costi), CTOT. Dal 2020 spariscono CAC, CGIND, CGD e compare "Altri costi" (anche negativo).
- Copertura costi: il file e' un campione di comuni (65.553 righe in 14 anni; ~5.300 righe nel 2011, ~6.800 nel 2024; solo 2020-2021 con meno righe). Le sette grandi citta' ci sono quasi sempre (Napoli manca 2011-2014, 2016, 2022). Dei 131 comuni intorno a Milano ne hanno il costo da 104 (2020) a 130.

## 3. Controlli fatti

1. Per ogni riga di ogni anno: RD + ingombranti a smaltimento + indifferenziato = totale RU (entro l'1%): 0 eccezioni su 115.275 righe (`pulito/controlli.json`).
2. Le tonnellate di Milano (RU, RD) coincidono con il file ds858 del Comune (differenze < 1 t) per tutti gli anni 2010-2023.
3. Controllo indipendente su ISTAT BES (citta' metropolitana di Milano): kg per abitante della somma dei 132 comuni vs indicatore ISTAT 10AMB024P: differenza massima 4,4 kg (2013), di norma 1-2 kg, dal 2013 al 2023; quota RD vs 10AMB017: differenze <= 0,1 punti. Tabella completa in `docs/rifiuti/data/riepilogo.json` (`metro.controllo_bes`). Nel 2010-2012 il confronto per abitante non vale (vedi trappola 1).
4. Totali Italia (somma dei comuni senza le righe "Vedi aggregazione"): 29,9 Mt nel 2024, 67,7% di RD, 509 kg per abitante: ordine di grandezza coerente con i rapporti ISPRA (non confrontato riga per riga con il Rapporto Rifiuti Urbani).
5. TARI/costo: TARI incassata 301-322 milioni, costo ISPRA x abitanti 281-318 milioni: rapporto 93-112% (due fonti diverse, solo indicativo).

## 4. Limiti dei dati (spiegati anche nella pagina)

1. **Abitanti 2011 e 2012**: sono quelli del censimento 2011 (Milano 1.242.123 e 1.240.173; 1.324.110 nel 2010 e 1.324.169 nel 2013): il pro capite sbalza. Succede in tutte le citta' (Roma 2.761.477 / 2.614.263 / 2.863.322 nel 2010 / 2012 / 2013). Nella pagina i valori per abitante 2011-2012 non vengono calcolati (null, banda grigia). Anche 2019 (1.406.242) -> 2021 (1.371.498) e' un salto di abitanti, forse revisione dopo censimento permanente (ipotesi, non verificata); il pro capite 2019 e' un po' basso. Nota: la serie ds859/ds860 del Comune per i costi ha abitanti 2012 = 1.262.101, diversa da quella del file rifiuti (1.240.173): per i costi si usa quella del file dei costi.
2. **Quota RD non omogenea**: dal 2016 compaiono nel file "Rifiuti da C e D" e "Pulizia stradale a recupero" (vuote fino al 2015); a Milano 29 mila t nel 2016 (circa 4 punti: 57,6% -> 53,3% senza). Nella pagina serie tratteggiata `rd_pct_senza_cd_spazz` = (RD - C&D - spazzamento a recupero) / RU: calcolo nostro. Il metodo nazionale citato dal Comune per i suoi dati del 2017 e' il DM 26/5/2016 (causa del cambio: inferenza nostra). Lo scalino si vede anche in Italia e nei comuni intorno.
3. **Vetro/plastica/metalli cambiano classe**: plastica di Milano 31,2 mila t (2010), 19,9 (2018), 25,5 (2019), 45,0 (2020); vetro 83,0 mila t nel 2018; voce "Altro" 8,6 (2018) e 13,1 mila t (2019) contro 3,3 nel 2020. Si sommano in un gruppo; la somma vetro+plastica+metallo e' regolare (96-125 mila t).
4. **Costi**: dichiarati dai Comuni; voci diverse dal 2020 (vedi punto 2 sopra); Milano 2024: CTS 0,93 e CTR 37,5 euro (spostamento tra le due voci, totale 219,48 invariato nel senso che il totale non e' anomalo); Firenze 207 euro (2019) -> 356 (2024), Bologna 197 -> 269: possibili cambi di perimetro del costo. Il sito dice "dati 2023" per l'ultimo aggiornamento dei costi ma il file 2024 esiste (puo' essere provvisorio). Costo e TARI non sono la stessa cosa.
5. **Chili per abitante** dividono per i soli residenti, ma i rifiuti raccolti comprendono pendolari e turisti.
6. **Citta' di confronto scelte da noi** (Roma, Torino, Napoli, Bologna, Firenze, Genova).
7. **Raccolta differenziata non vuol dire riciclata**: nei dati non ci sono scarti di trattamento ne' destinazioni (discarica, termovalorizzatore).
8. **Area metropolitana = provincia di Milano** (codici 03015xxx) con dati in tutti i 15 anni: 132 comuni (133-134 comuni esistono in ciascun anno). Monza e Brianza (03108) esclusa. Per i costi dell'hinterland e' una media pesata sui comuni che hanno il dato.
9. Manca il 2025 (ISPRA arriva al 2024).

## 5. Numeri principali (Milano)

- Rifiuti urbani: 711.873 t (2010) -> 666.471 (2014) -> 707.507 (2019) -> 608.413 (2020, -14,0%) -> 657.674 (2024). Per abitante: 491 kg (2013), 503 (2019), 435 (2020), 481 (2024). Italia 2024: 509 kg.
- Raccolta differenziata: 33,8% (2010), 49,9% (2014), 57,6% (2016; 53,3% col calcolo vecchio), 62,7% (2020), 63,3% (2024; 60,2% col calcolo vecchio). Italia 67,7%; hinterland 73,4%; Milano 124 su 132 comuni per quota RD, 93 su 132 per pochi rifiuti a testa. Mediana 132 comuni: 78,8%.
- Umido: 34.506 t (2010), 40.783 (2012), 71.737 (2013), 118.188 (2014), 139.935 (2024). Indifferenziato: 471.263 t (2010) -> 241.157 (2024); kg a testa 356 (2010, abitanti 2010) -> 177 (2024).
- Costi (euro per abitante, anni correnti): 234,6 (2011), 225,1 (2019), 201,0 (2020), 219,5 (2024); euro 2025: 297 (2011) -> 223 (2024). Altre grandi citta' 2024: Bologna 269, Torino 270, Napoli 283, Roma 287, Genova 291, Firenze 356. Variazione 2019-2024: Milano -2,5%, Roma +11%, Torino +28%, Napoli +22%, Bologna +36%, Firenze +72%, Genova +8%.
- TARI incassata (milioni): 311 (2015), 301 (2019), 287 (2020), 322 (2024), 304 (2025).
- Turisti: notti 12,9 milioni (2019), 3,5 (2020), 16,5 (2024, +27% sul 2019): in media 45 mila presenti al giorno nel 2024 = 3,3% dei residenti (1,7% nel 2010). Rifiuti 2019->2024: -7,0%.

## 6. Cosa mostra la pagina e cosa e' la "sorpresa"

Quattro "sorprese" calcolate dal JSON: (1) indifferenziato dimezzato ma rifiuti totali per abitante fermi dal 2013 - il cambiamento e' l'umido; (2) costo per abitante piu' basso tra le sette grandi citta' e in calo dal 2019 mentre altre salgono (da leggere con cautela); (3) 123 comuni su 132 della citta' metropolitana hanno RD piu' alta di Milano; (4) Covid: -14,0%, il calo piu' forte tra le sette; turisti +27% sul 2019 e rifiuti -7%.

## 7. Da fare / dubbi per il coordinatore

- Regione Lombardia O.R.SO. (frazioni merceologiche e costi per comune): non scaricata (endpoint catalogo 404, non approfondito); aggiungerebbe poco.
- Verificare con un esperto o con la relazione del Comune/AMSA: quando e' partito l'umido quartiere per quartiere (il salto nei dati e' 2012-2014); la pagina non lo afferma.
- Verificare il motivo dei salti di costo di Firenze e Bologna e del cambio del 2020 (ARERA?).
- Non usate: ds849-856 (rifiuti urbani per codice CER, kg, 2010-2020, Comune), utili se serve il dettaglio CER.
