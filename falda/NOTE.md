# La falda che risale: note (15/11/2026)

Pagina: bozza in `bozze-grafici/falda-v2/index.html`, anteprima in `docs/anteprima/falda/`. Non pubblicata.

## Dati (verificati in rete il 15/11/2026)
Tutti su Open Data Lombardia, Città metropolitana di Milano, formato GeoJSON/CSV via API Socrata.
- Piezometria settembre 2022: `9j8c-7map` (CC0). Controllo: `krur-6ms9` (stessa carta, 80 linee).
- Piezometria marzo 2022: `wp7j-awzt` (CC0). Esistono anche `dfha-eywp` (solo città, 48 linee) e `8xba-rphy` (senza geometria).
- Soggiacenza indicativa marzo 2022: `u3wq-chcr` (CC0), 31 poligoni a fasce (< 2,5 ... > 35 m).
- Isopieze 2007-2013, CC BY 4.0: marzo 2007 `t34c-5qeq`, settembre 2007 `vxmx-t3zq`, marzo 2009 `dmse-82se`, settembre 2009 `875x-wqng`, marzo 2010 `72vq-8vpk`, settembre 2010 `253s-q2hp`, marzo 2011 `sb4i-gr6d`, settembre 2011 `354f-iu45`, marzo 2012 `2xpi-jryy`, settembre 2012 `qs2b-225i`, settembre 2013 `832x-mcv2`. Mancano 2008, marzo 2013 e tutto 2014-2021.
- Comune di Milano ds587 (CC0): solo 8 punti, campionamenti chimici 2016, 7 con coordinate. Nessun livello di falda: serve solo come mappa dei punti di controllo.
- Confini quartieri: `docs/negozi/data/nil.geojson` (88 NIL, copiato). Stazioni: `docs/metro/data/stazioni_metro.csv`.

## Quota e soggiacenza
Le carte 2007-2013 e le piezometrie 2022 danno la QUOTA (m sul livello del mare). La soggiacenza (m sotto il suolo) esiste solo per marzo 2022, a fasce. Non si sono mescolate: mappa e stazioni usano la soggiacenza, serie, mappa della variazione, pallini e sezione usano la quota.

## Metodo
`scripts/scarica.py` scarica in `dati_grezzi/` (non pubblicato). `scripts/calcola.py` campiona le isolinee ogni 150 m (UTM 32N), interpola in modo lineare (Delaunay), valuta ogni carta su celle da 100 m dentro i quartieri (18.186 celle) e media per quartiere. `scripts/verifica.py` rifà i numeri con un secondo metodo (campionamento 75 m, `griddata`, celle da 80 m sfalsate, aree invece di punti): coincidono tutti, tranne il conteggio «quartieri con variazione negativa» (60 contro 61) perché un quartiere ha variazione di 0,00 m: per questo la pagina non usa quel conteggio ma soglie (oltre 1,5 m: 23; oltre 0,5 m: 45 e 17).

## Risultati principali
- Quota media sotto Milano: marzo 2007 108,8 m; settembre 2013 111,4 m (+2,6); marzo 2010 110,7; marzo 2022 110,1 (-0,6 dal 2010, +1,3 dal 2007); settembre 2022 109,7.
- Marzo contro settembre dà lo stesso quadro (-0,5 m, 58 quartieri su 88 più bassi).
- Calo nel centro e nel sud (fino a -3,5 m a Muggiano), salita a nord (fino a +1,9 a Figino).
- Fasce di soggiacenza: Duomo 15-20 m; 4 quartieri (Chiaravalle, Monluè, Quintosole, Triulzo Superiore) con la falda sotto i 5 m su metà territorio; 18 stazioni su 125 con falda sotto i 10 m, 3 sotto 5 m (Assago Milanofiori Forum, Linate Aeroporto, San Donato).

## Limiti da ricordare
- Un quartiere preso da solo balla di circa 0,7 m (mediana) da una carta alla successiva rispetto alla media di Milano, fino a 2 m nel 10% dei casi: valgono i quadri d'insieme, non le differenze piccole di un quartiere.
- Linee «stimate»: 24 su 32 nella carta di marzo 2010; 53 su 99 marzo 2011; 62 su 104 settembre 2009.
- Errore dell'interpolazione provato sulla carta 2022 (tolte le linee a 2,5 m e ricostruite): medio 0,2 m, massimo 1,3 m. Sulle carte vecchie è probabilmente maggiore.
- Profondità di scavo delle stazioni non nei dati: si dice solo dove sta l'acqua, mai quali stazioni sono a rischio.
- Colori: blu = falda alta, arancio = falda bassa (non verde/rosso, perché la falda alta non è né bene né male).

## Dove sta ora (15/11/2026, dopo la decisione di Davide)
La falda non è più una pagina a sé: è il capitolo «La falda sotto i piedi» (id `falda`) della pagina «Acqua e fogne», bozza `bozze-grafici/fogne-v2/index.html`. Link dall'«Acqua del sindaco» (bozza `bozze-grafici/acqua-del-sindaco-v2/`) verso `../fogne/#falda`.
Dati pubblici in `docs/fogne/data/`: `falda_confini.geojson`, `falda_quartieri.json` e `.csv`, `falda_serie_quartieri.json`, `falda_stazioni.json`, `falda_riepilogo.json` (tutti sotto 100 KB).
Per rigenerarli: `python -I -X utf8 falda/scripts/scarica.py` (se servono i dati grezzi), poi `calcola.py` (scrive in `docs/fogne/data/falda_*`; sezione nord-sud, punti di controllo e serie della città vanno in `falda/dati_extra/`, non pubblicati) e `verifica.py`.
`docs/falda/` e la bozza `falda-v2` non servono più al capitolo.
