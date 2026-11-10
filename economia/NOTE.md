# Milano in Italia e in Europa: note

Pagina nuova (bozza in bozze-grafici/economia-v2/, dati in docs/economia/data/). Non pubblicata, non nel menu.

## Fonti e licenze
- Eurostat, API di diffusione SDMX 2.1 (https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/<tabella>?format=TSV&compressed=true), tabelle intere, scaricate il 10/11/2026 in economia/raw/ (non nel sito):
  - `nama_10r_3gdp`: PIL per provincia (NUTS 3), 2000-2023, unità MIO_EUR (prezzi correnti), EUR_HAB (per abitante), PPS.
  - `nama_10r_3gva`: valore aggiunto per settore e provincia, 2000-2023, prezzi correnti (CP_MEUR). A prezzi dell'anno precedente (PYP_MEUR) c'è solo per l'Italia intera, non per le province.
  - `nama_10r_3empers`: occupati (dipendenti + indipendenti) per provincia e settore.
  - `nama_10r_3popgdp`: popolazione media annua per provincia.
  - `met_10r_3gdp`: PIL delle aree metropolitane europee, 2000-2022 (2021 ultimo anno per quasi tutte).
- Licenza: riuso libero con citazione della fonte (Decisione della Commissione 2011/833/UE, politica di riuso Eurostat, equivalente a CC BY 4.0). Nella pagina: «licenza: riuso libero con citazione».
- ISTAT conti territoriali ed esportazioni per provincia (Coeweb): NON usati. Il 10/11/2026 il portale esploradati.istat.it non ha risposto entro 60 s (richiesta dell'elenco dei dataflow), e Coeweb non ha un download diretto senza registrazione che abbiamo potuto verificare. I dati provinciali di Eurostat vengono comunque dall'ISTAT. Da ritentare.

## Passi (economia/scripts/)
01_scarica.py (scarica le tabelle), 02_elabora.py (scrive docs/economia/data/: riepilogo.json e 4 CSV), _lib.py (lettore dei TSV Eurostat). Python con -I -X utf8, lanciati dalla cartella del progetto.

## Scelte
- «Milano» = ITC4C, Città metropolitana di Milano (senza Monza e Brianza, ITC4D). Quota sul PIL italiano a prezzi correnti (Milano e Italia stessi prezzi dell'anno, quindi nessuna distorsione da inflazione).
- Il PIL è la voce `nama_10r_3gdp` (non il valore aggiunto): somma dei settori (valore aggiunto 207.049 milioni nel 2023) + imposte sui prodotti = 230.481. I settori usano il valore aggiunto.
- Valori nel tempo «in euro del 2023»: Milano nominale × (indice dei prezzi 2023 / indice dell'anno). Indice dei prezzi = deflatore implicito del valore aggiunto italiano, a catena dal 2000 (prezzi correnti / prezzi dell'anno prima). Prezzi 2023 su 2000: vedi riepilogo.json. È una stima: manca un deflatore provinciale.
- Classifica europea: aree metropolitane con codice più lungo di 4 caratteri, senza i totali «_NM» (non metropolitane) e senza i totali nazionali, valore dell'indice UE = 100 (PPS_HAB_EU27_2020). Posizione = 1 + numero di aree con indice maggiore di Milano. Risultato: 8ª su 238 nel 2000, 14ª su 248 nel 2021. Il rapporto IDEE_LIBERE (sez. 5) li dava uguali.
- Grafico a pendenza: 22 aree scelte (5 italiane, 17 europee note). Dublino (273 nel 2021) e Lussemburgo (266) escluse dal disegno per scala.

## Cosa è stato verificato prima della classifica
- Codici NUTS dell'area «IT002M» (Milano): Eurostat non pubblica l'elenco nel file scaricato. Confronti: PIL IT002M 2000 = 128.508 milioni, ITC4C + ITC4D = 127.110 (-1,1%), + ITC49 Lodi = 131.615 (+2,4%); 2021: 228.436 contro 228.018 (-0,2%) e 234.674 (+2,7%). Abitanti IT002M 2021 (met_pjangrp3): 4.339.269; ITC4C 3.228.300, ITC4D (con ITC4C) 4.098.600, con Lodi circa 4,33 milioni. Quindi l'area ha il PIL di Milano + Monza e abitanti da Milano + Monza + Lodi: non è fatta di province intere (anche per Roma e Torino i valori «metro» differiscono dal provinciale di 2-3%). Elenco esatto dei comuni non trovato. Dichiarato nella pagina.

## Limiti e difetti trovati
- **Salto 2008**: la quota di Milano sul PIL italiano passa da 8,81% (2007) a 9,56% (2008), +10,5% in un anno contro +1,4% dell'Italia. Il salto c'è in tutti i servizi (K-N da 11,5% a 13,0%, J da 19% a 21%, M_N da 14,6% a 16,7%), anche a Monza e Brianza (1,42% → 1,51%), mentre le altre province lombarde calano (Bergamo 10,5% → 9,8% del PIL lombardo, Varese, Brescia). Roma, Torino, Napoli e Bologna non hanno salti. Probabile discontinuità di metodo ISTAT/Eurostat; non verificata. Nella pagina la linea è spezzata e c'è una nota. Le variazioni 2000-2023 di Milano includono il salto; la crescita «pulita» è dal 2008.
- **Monza e Brianza**: la provincia è del 2009, ma Eurostat riporta ITC4D (e quindi ITC4C ridotta) per tutti gli anni dal 2000 con i confini di oggi. Nessuna rottura per questo motivo. Linea «Milano + Monza» nel grafico per confronto.
- Il PIL per abitante di Milano è gonfiato dai pendolari (il PIL si produce dove si lavora, gli abitanti sono residenti).
- Parità di potere d'acquisto: prezzi medi nazionali, gonfia Bucarest e Varsavia.
- Dati provinciali fino al 2023; metro fino al 2021 per quasi tutte (2022 solo per 58 aree, 2023 nessuna).
- Esportazioni e conti territoriali ISTAT: non inclusi (vedi sopra).
