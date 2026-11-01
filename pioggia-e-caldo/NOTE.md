# Pioggia e caldo - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Due domande, stessa fonte: (A) piove più forte e più tutta insieme di prima? (B) quali parti di Milano sono più calde, soprattutto nelle notti d'estate?

## 1. In breve

1. **Fonte unica, buona e libera: ARPA Lombardia su dati.lombardia.it, licenza CC0.** Anagrafica di 1.462 sensori; temperatura e pioggia in 4 blocchi di date per grandezza. Scaricati 95 sensori entro 36 km dal Duomo (44 di temperatura, 51 di pioggia): 58,9 milioni di righe, 2,6 GB in `raw/`.
2. **Non esistono "zip annuali"**: ARPA pubblica ogni grandezza in 4 tabelle gigantesche (fino al 2010, 2011-2020, dal 2021, mese in corso). Ho scaricato in blocco con un filtro sui sensori scelti (una richiesta ogni 8 sensori), non riga per riga.
3. **Pioggia: nessuna tendenza visibile.** Nei 23 anni 2003-2025 dei pluviometri di Milano né il totale, né i giorni di pioggia, né l'ora più forte, né le ore sopra 20 mm/h hanno una pendenza distinguibile da zero (intervalli al 95% larghissimi). Nella serie lunga di Milano 1858-2008 (ECA&D) il totale annuo è piatto e i giorni di pioggia calano di 1,1 per decennio (intervallo -1,7/-0,6).
4. **Caldo: l'isola di calore è un fenomeno di notte.** Estati 2017-2025: le 4 stazioni del centro/nord/ovest sono 2,3-3,0 °C più calde della campagna tra le 22 e le 5, ma tra le 12 e le 16 sono uguali o più fresche (da -0,8 a +0,4). Le due stazioni dell'est (Feltre, Lambrate) sono 0,3-0,4 °C sopra la campagna anche di notte.
5. **Trappola grossa**: i pluviometri sbagliano e i termometri hanno salti (vedi punto 7). Prima di scrivere "record" bisogna controllare il giorno con le altre stazioni.

## 2. Fonti, una per una

Licenza (campo `licenseId` del catalogo e descrizione dei dataset): **"Creative Commons 1.0 Universal (Public Domain Dedication)" = CC0**, scritto nei dataset anche come "CC0_10"; attribuzione indicata dal portale: "ARPA Lombardia". Ripubblicabile. Orario dei dati: "ora solare" (CET fisso, niente ora legale); il valore si riferisce alle osservazioni "fino all'orario indicato" (descrizione ARPA di `pstb-pga6`).

| Cosa | Dataset | Periodo | Righe totali (tutta la Lombardia) | Passo |
|---|---|---|---|---|
| Anagrafica sensori | `nf78-nj6b` | aggiornato 21/10/2026 | 1.462 sensori (325 pioggia, 309 temperatura) | - |
| Pioggia fino al 2010 | `e7r2-7m84` | 1987-08-14 → 2011-01-01 | 52.180.472 | orario |
| Pioggia 2011-2020 | `2kar-pnuk` | 2011-01-01 → 2021-01-01 | 90.379.768 (232 sensori su 325) | orario fino al 2013, 10 min dal 2014 |
| Pioggia dal 2021 | `pstb-pga6` | 2021-01-01 → 2026-03-01 | 67.262.315 | 10 min |
| Temperatura fino al 2010 | `6eu4-4tja` | 1987-11-25 → 2011-01-01 | 36.682.214 | orario |
| Temperatura 2011-2020 | `d4kj-kbpj` | 2011 → 2021 | 104.930.618 | orario fino al 2013, 10 min dal 2014 |
| Temperatura dal 2021 | `w9wd-u6jh` | 2021-01-01 → 2026-03-01 | 64.440.191 | 10 min |
| Mese in corso (T e P) | `647i-nhxk` | da inizio aprile 2026 al 2026-11-01 | - | 10 min |
| Pioggia giornaliera lunga di Milano | ECA&D RR, stazione 173 "MILAN", sorgente Maugeri (Università di Milano) | 1858-01-01 → 2008-12 (151 anni, tutti "completi") | `raw/ecad_rr/blend_rr/RR_STAID000173.txt` | giorno, 0,1 mm |
| Pioggia giornaliera Linate | NOAA GSOD, già in `../neve-e-nebbia/pulito/giorni_neve_nebbia.csv` (campi `gsod_prcp_mm`, `gsod_prcp_flag`) | 1951-2025 con buchi | solo controllo incrociato | giorno UTC |

Indirizzi: `https://www.dati.lombardia.it/resource/<dataset>.csv` (SODA, filtro `idsensore in (...)`); cataloghi salvati in `raw/catalogo/`. ECA&D: `https://knmi-ecad-assets-prd.s3.amazonaws.com/download/ECA_blend_rr.zip` e `ECA_nonblend_rr.zip` (1,8 e 1,4 GB): letto solo l'indice e scaricati i file di Milano con HTTP Range (3 MB), come nel filone temperature. **Licenza ECA&D** (intestazione dei file): "THESE DATA CAN BE USED FOR NON-COMMERCIAL RESEARCH AND EDUCATION PROVIDED THAT THE FOLLOWING SOURCE IS ACKNOWLEDGED", cioè Klein Tank et al. 2002, Int. J. Climatol. 22, 1441-1453. Il grezzo non si ripubblica; valori aggregati sì, con citazione (stessa scelta del filone temperature, JOURNAL sez. 1, 29/10).

Nessun account, nessun token, nessuna registrazione. Il portale limita le richieste senza token (HTTP 429 dopo qualche raffica): il programma aspetta e riprova.

## 3. Sensori e completezza

Sensori scelti: tutti quelli di temperatura e pioggia entro 36 km dal Duomo (`pulito/sensori_selezionati.csv`); riepilogo per sensore con conteggi di qualità in `pulito/riepilogo_copertura_sensori.csv`, matrici anno x sensore in `pulito/pioggia_copertura_matrice.csv` e `pulito/caldo_copertura_matrice.csv`. "Anno completo" pioggia = almeno 90% delle ore dell'anno; "estate completa" = almeno 80 giorni validi su 92 (giugno-agosto).

**Pluviometri di Milano e dintorni** (`id sensore`, anni completi):
- Juvara 5908: 24 anni (1990-2010 con qualche buco, e 2021-2025), **buco 2011-2020** (vedi trappola 1)
- Zavattari 9341: 19 (2005-2025, mancano 2013, 2014)
- Lambrate 2006: 19 (2004-2025)
- Corsico 5902: 22 (2003-2025); Parco Nord 4065: 17 (2004-2025)
- Catena di Isola: Confalonieri 8149 (2006-06 → 2012-04, 5 anni completi) poi Rosellini 14121 (dal 2012-04, 13 anni): 450 m di distanza, uguale quartiere, li considero un unico pluviometro con un trasloco
- Brera 19373: solo dal 2016-07-11 (9 anni completi). Prima di quella data a Brera non c'è pioggia ARPA
- Segrate Milano Due 2065: 1994-2004, 3 anni completi, ore estreme non confermate dai vicini: escluso dai conteggi
- Rho 14741 (dal 2015), Cinisello, Rodano 5916 (14 anni, buco 2011-2020), Landriano 2195 (20 anni), ecc.

**Termometri** (estati complete): Brera 5897: 32 (1991-2026); Juvara 5909: 34 (1990-2026); Marche 5911: 37 (1990-2026, senza buchi); Zavattari 5920: 28 (1992-2026, 7 anni mancanti); Feltre 8162: 26 (2001-2026); Lambrate 2001: 22 (2002-2026); Corsico 5903: 30; Parco Nord 4058: 18; Rho 14742: 12 (dal 2015). Riferimenti rurali: Rodano 5917 (25 estati, dal 1999), Landriano 2187 (19), Lacchiarella 5910 (26), Arconate 4066 (20 estati, dal 2003), Sant'Angelo Lodigiano 2122 (31, dal 1993), Magenta Mainaga 17488 (8, dal 2019), Bereguardo 12716 (6, dal 2021). Linate non è ARPA (è NOAA: vedi `../neve-e-nebbia`).

Qualità (da `pulito/qualita_sensori.csv`, tutti i sensori): 548.897 righe con valore -999 su 58.897.406 (0,9%): nel file ARPA hanno `stato` vuoto, tutte le altre `stato` = `VA`; scarto le prime. Fuori soglia (T fuori -35/48 °C, pioggia oltre 100 mm in 10 minuti o 250 mm in un'ora): 78 righe in tutto. Pioggia oraria = somma delle 6 letture da 10 minuti (se ne manca una, l'ora non conta); i sensori hanno risoluzione 0,2 mm (tutti i valori sono multipli di 0,2, prima e dopo il 2011).

## 4. (A) Pioggia: numeri

Tutti da `pulito/pioggia_anno_sensore.csv` (sensore x anno, campi `tot_mm`, `giorni_piovosi_1mm`, `max_oraria_mm`, `max_giornaliera_mm`, `ore_ge20`, `ore_ge30`, `quota_top1pct_ore`, `quota_top1pct_ore_piovose`, `max_10min_mm`) salvo diversa indicazione. Le statistiche sono "validate": i giorni sopra 40 mm che nessun'altra stazione entro 15 km (né ECA&D né Linate per le stazioni di Milano) conferma almeno al 40% sono tolti (100 giorni su 3.283, elenco in `pioggia_giorni_ge40mm_verifica.csv`); il massimo grezzo resta nel campo `max_oraria_mm_grezza`.

- **Quanto piove**: 840-1.085 mm in media per anno sui pluviometri di Milano (Brera 842 su 9 anni; Lambrate 1.054 su 19; Zavattari 917 su 19). Serie lunga ECA&D Milano: 986 mm di media 1858-2008 (`pioggia_lungo_periodo.csv`); anno più secco 1921 (426,6 mm), più piovoso 1951 (1.586,5 mm).
- **Giorni di pioggia (≥ 1 mm)**: 76-88 per anno (ARPA). ECA&D: da 88-98 per anno (1858-1917) a 78 (1978-2008) (`pioggia_lungo_decenni.csv`); pendenza -1,14 giorni per decennio, intervallo 95% -1,70/-0,56 (`pioggia_lungo_tendenze.csv`, 1858-2008, 151 anni). Totali costanti: la pioggia per giorno piovoso sale da 11,3 mm (1858-1887) a 12,2 mm (1978-2008). Attenzione: il metodo di misura di Maugeri cambia nel tempo (campo `RR` ECA&D "intervallo non noto"), quindi è un'indicazione, non una misura precisa.
- **Ora più forte per anno**: da 11,8 a 78,0 mm/h sui pluviometri di Milano (media 31, mediana 29,2; 128 sensore-anni completi). **Ore sopra 20 mm/h**: in media 1,8-2,3 per sensore e anno; sopra 30 mm/h: 0,4-0,7 (`pioggia_periodi_milano.csv`, 1990-2003 solo 2 sensori, 2004-2012 cinque, 2013-2025 sei).
- **Quota della pioggia dell'anno che cade nell'1% delle ore più piovose** (circa 88 ore): in media 51-56% per periodo (0,54 su 128 sensore-anni completi), per sensore-anno da 39% a 71% (`quota_top1pct_ore`). Misurata sulle sole ore con pioggia (1% delle ore bagnate, circa 8): 12-19%. **Metà della pioggia annuale cade in meno di 90 ore.**
- **Tendenze, con onestà** (`pioggia_composito_tendenze.csv`: scarto di ogni pluviometro dalla propria media, media tra i sensori attivi, Theil-Sen con intervallo bootstrap al 95%, 23 anni 2003-2025): totale +8,8% per decennio (intervallo -17/+23%); giorni piovosi +7,1% (-8/+16%); ora massima +2,3 mm per decennio (-3,0/+6,1); ore ≥ 20 mm +0,57 per decennio (-0,34/+1,32); quota top 1% ore +2,4 punti (-2,2/+8,2). **Unica pendenza con intervallo che esclude lo zero: la quota nelle ore bagnate più forti (+1,1 punti per decennio, +0,13/+2,8)**; è una su otto misure, quindi è compatibile col caso e non va raccontata come scoperta. Per i singoli pluviometri (`pioggia_tendenze.csv`) quasi nessun intervallo esclude lo zero, e questo con 10-24 anni a testa.
- **Giorni più piovosi della città** (`pioggia_eventi_citta_giorni.csv`: mediana tra i pluviometri di Milano attivi, almeno 3 stazioni): 2009-07-07 (101,6 mm, 5 stazioni; Juvara 126,2), 2024-09-05 (99,8; Zavattari 128,4; Linate NOAA 120,9), 2014-11-15 (95,4; Lambrate 119,8), 2007-09-26 (94,4; Parco Nord 131,4, Confalonieri 105,0 a 6 km di distanza, ma ECA&D Brera 15,4: temporale piccolissimo), 2024-05-15 (80,0; Linate 102,1), 2025-09-22 (79,8; Rosellini 91,6).
- **Ora più forte confermata**: 78,0 mm tra le 05 e le 06 solare (ora indicata 06:00) del 2009-07-07, Juvara, `pioggia_eventi_top_ore.csv` (le altre 4 stazioni quel giorno: 71-121 mm nel giorno, 53,2 nella stessa ora). Seguono Zavattari 71,6 mm/h il 2019-07-03 (20:00; i vicini nella stessa ora al massimo 29,4) e 69,8 il 2015-08-10 (01:00).
- **Alluvioni del Seveso**: nessun filone ha le date, quindi non ho collegato nulla. Le date sopra (soprattutto 2014-11-15 e 2024-09-05) sono candidate da verificare con una fonte prima di scrivere "alluvione".
- **2022 contro 2024**: stessi pluviometri, Zavattari 450 mm nel 2022 e 1.523 nel 2024 (3,4 volte); Brera 386 → 1.490; Rosellini 441 → 1.593; Lambrate 447 → 1.631 (`tot_mm`).

## 5. (B) Caldo: numeri

Tutti da `pulito/caldo_estate_sensore.csv` (stazione x estate giugno-agosto) e `pulito/caldo_isola_stazione.csv` (finestre 2002-2010, 2011-2016, 2017-2025) e `pulito/caldo_isola_ora.csv` (per ora del giorno). Metodo: temperatura alle ore :00 (valori validi), minimo e massimo del giorno solare da quelle letture (giorno valido se almeno 20 ore su 24); l'estremo vero può essere un poco più alto o basso (stessa regola per tutte le stazioni e anni). **Isola di calore = temperatura della stazione meno la media dei termometri rurali nello stesso istante** (almeno 3 rurali disponibili; rurali: Rodano, Landriano, Lacchiarella, Arconate, Magenta, Sant'Angelo Lodigiano, Bereguardo: li ho scelti io per nome e distanza (> 12 km dal Duomo, paesi piccoli o cascine), non c'è una carta dell'uso del suolo nel progetto). I singoli rurali si discostano dalla media di -0,85/+0,68 °C la notte: **l'incertezza della differenza è circa ±0,5 °C**.

Estati 2017-2025, media sulle 9 estati (`caldo_isola_stazione.csv`, finestra 2017-2025):

| Stazione | NIL | minima media estate (°C) | notte 22-05 rispetto ai rurali (°C) | pomeriggio 12-16 (°C) | notti tropicali per estate (min ≥ 20 °C) |
|---|---|---|---|---|---|
| Juvara 5909 | Buenos Aires-Porta Venezia-Porta Monforte | 21,96 | +2,96 | -0,64 | 68,4 |
| Brera 5897 | Brera | 21,78 | +2,71 | -0,79 | 65,8 |
| Marche 5911 | Isola | 21,54 | +2,55 | -0,57 | 63,3 |
| Zavattari 5920 | San Siro | 21,37 | +2,30 | +0,39 | 62,3 |
| Corsico 5903 | (fuori comune) | 19,88 | +0,74 | -0,37 | 46,7 |
| Rho 14742 | (fuori comune) | 20,71 | +1,75 | -0,79 | 56,6 |
| Lambrate 2001 | Cimiano-Rottole-Q.re Feltre | 19,32 | +0,40 | +0,32 | 38,4 |
| Feltre 8162 | Cimiano-Rottole-Q.re Feltre | 19,28 | +0,33 | -0,36 | 37,9 |
| Parco Nord 4058 | (fuori comune) | 17,74 | -1,23 | +0,40 | 18,3 |
| Rurali (Rodano, Landriano, Lacchiarella, S.Angelo, Magenta) | - | 19,1-19,5 | circa 0 | circa 0 | 35-41 |

- **Curva per ora** (`caldo_isola_ora.csv`, riga `URBANE_MEDIA` = media delle 6 stazioni di Milano meno i rurali, 2017-2025): +1,9/+2,0 °C dalle 21 alle 5, massimo alle 22 (+2,01), poi cala all'alba (+0,8 alle 7, +0,08 alle 9), vale -0,1 a -0,36 °C tra le 12 e le 16, risale dalle 18. Uguale nelle altre due finestre (2002-2010 notte +2,3/+2,4; 2011-2016 +1,7/+2,0).
- **Notti tropicali 2026**: 79-80 notti su 92 a Brera, Juvara, Marche, Zavattari; 64-65 a Feltre e Lambrate; 63 a Rodano, 54 a Lacchiarella (estate 2026 completa; `caldo_notti_tropicali.csv`). Il 2026 e il 2022 sono i due anni peggiori: nel 2022 Brera 80, Juvara 82, Marche 72, Zavattari 79.
- **Stazione più calda**: di notte, nel 2017-2025, **Juvara** (+2,96 °C, minima media 21,96 °C, 68 notti tropicali per estate). Il primato cambia di anno in anno: la notte più calda dell'estate (`tmin_massima`) è a Zavattari nel 2022 (28,8 °C) e nel 2026 (29,8 °C), a Brera nel 2023 (28,9 °C); la giornata più calda del 2026 è ancora a Zavattari (39,5 °C).
- **Alberi, solo confronto** (`pulito/caldo_alberi_confronto.csv`; alberi del censimento 2025 entro 500 m dalla stazione, ds2484, e per NIL da `../alberi/pulito/nil_alberi.csv`): Brera 6,2 alberi per ettaro, Marche 18,2, Juvara 20,6, Zavattari 20,6, Lambrate 37,3, Feltre 43,0. Le due stazioni con più alberi (Lambrate e Feltre) sono quelle con la notte meno calda (+0,3/+0,4 °C), ma Brera, con meno alberi, sta nel mezzo: l'ordine non è proporzionale. Spearman tra alberi per km² del NIL e notte: -0,93, ma su 6 stazioni che stanno in soli 5 NIL e con due NIL che dominano; **non è una prova**. Il censimento copre solo gli alberi del Comune (non i giardini privati né i parchi di altri enti) e i parchi grandi (Forlanini vicino a Feltre/Lambrate) contano poco con un cerchio di 500 m.
- **Distanza dal Duomo**: minima media 2017-2025 scende da 21,4-22,0 °C (0,8-4 km) a 19,3 (6 km) a 18,1-19,5 (13-30 km; Arconate 18,1 e Bereguardo 18,8 sono i più freddi) (`minima media estate` nella tabella); è il confronto senza classi che non dipende dalla mia scelta dei rurali.

## 6. Le due cose più sorprendenti

**Pioggia**: l'ARPA di Milano, dove ci sono 9 stazioni, vede il solito: metà della pioggia dell'anno cade in 88 ore, ma niente cresce; la cosa più sorprendente è **quanto sia locale e quanto sbagli un pluviometro solo**. Il 26 settembre 2007 Parco Nord misura 131 mm, Confalonieri (a 6 km) 105 mm, Brera nella serie ECA&D 15 mm. Il 21 ottobre 1999 Juvara registra 212 mm in un giorno, quando ECA&D dice 68, Linate 72 e le stazioni intorno 67-85: un "record" che sparisce con un controllo. Altro dato forte: stessi pluviometri, 336-450 mm nel 2022 e 1.200-1.630 nel 2024.

**Caldo**: Milano di giorno non è più calda della campagna. Sui sei termometri della città il vantaggio è +2,0 °C di notte e **-0,1/-0,4 °C a metà pomeriggio** (-0,8 a Brera). E dentro la città, a 3-4 km di distanza, la notte cambia di 2,5 °C: Juvara +3,0, Lambrate +0,4, Feltre +0,3 (con 2-4 volte gli alberi nel raggio di 500 m). Ma attenzione: Feltre nel 2000-2007 era a +1,4/+2,6 e cala gradualmente fino a +0,1/+0,4 nel 2014-2018, quindi è possibile che sia cambiato il sensore o l'ambiente intorno.

## 7. Trappole dei dati (anche per la rubrica)

1. **Buco 2011-2020 nei pluviometri**: il dataset `2kar-pnuk` ha 232 sensori su 325. Di 47 pluviometri vicini a Milano attivi in quel periodo, **16 non hanno nessuna riga nel blocco 2011-2020** (compresi Juvara, l'unico di Milano che parte dal 1989, e Rodano); per i termometri solo 1 su 38 (Rivolta d'Adda). Non so perché; il registro non lo dice. Conseguenza: Juvara ha una serie spezzata (1990-2010 e 2021-2025).
2. **Brera, tre sensori diversi in tre luoghi per la pioggia**: Confalonieri (2006-2012), Rosellini (dal 2012, 450 m più in là) e Brera vera (dal luglio 2016). Il nome "Milano Brera" per la pioggia ha solo 9 anni.
3. **Pluviometri che inventano**: Segrate Milano Due 2000-03-21/22 (84,6 e 79,8 mm in un giorno, mentre Juvara, ECA&D e Linate dicono 0; `pioggia_ore_estreme_non_confermate.csv`); Juvara 1999-10-21 (212 mm contro 68-75 degli altri); Corsico 2018-05-16 (80,4 mm contro 20,8 intorno). Regola applicata: giorno ≥ 40 mm non confermato → tolto dalle statistiche validate.
4. **Un solo temporale può non vedersi altrove**: 2009-07-07 Juvara 78 mm in un'ora, Linate 0 (GSOD, flag E, periodo incompleto). Conferma: 4 altre stazioni di Milano da 71 a 121 mm nel giorno.
5. **GSOD (Linate)**: i flag A, B, C, E indicano somme di soli 6 o 12 ore (parziali), D, F, G coprono le 24 ore. Ho tenuto D, F, G, H, I. Giorno UTC, non solare (2014-11-15: ARPA 83-120 mm, Linate 5,6 mm: la pioggia di Linate sta nel giorno prima). Il massimo giornaliero di Linate 312,93 mm del 1975-07-11 (flag F) sembra un errore (4 volte il massimo di Milano): lasciato fuori.
6. **ECA&D RR**: intervalli di misura diversi nel tempo ("intervallo non noto", "mattina-mattina", ecc.); il giorno dei 0,1 mm non coincide col giorno solare ARPA.
7. **Termometri con salti propri** (`caldo_isola_anno.csv`): Parco Nord passa da +0,9 (2003-2007) a -1,3 dal 2011 (la notte); Lambrate da +1,5 (2007) a -1,8 (2011) e di nuovo +1,1 (2012); Zavattari sale di circa +1 °C di notte e +1,5 °C di giorno dal 2019; Feltre cala di circa 1,8 °C dal 2008 al 2014. Brera 2008-2016 ha già un problema noto (il sensore è circa 0,65 °C più caldo, filone temperature, JOURNAL sez. 1, 30/10): qui infatti dà +3,4/+4,4 nel 2011-2013 contro +2,2/+3,4 dopo il 2017. **Tendenze lunghe dell'isola di calore dalle singole stazioni non sono affidabili**; per i confronti tra stazioni uso solo 2017-2025 (sensori dopo il luglio 2016).
8. **Notti tropicali prima del 1996**: Brera, Juvara, Marche e Zavattari danno 39-69 notti tropicali per estate nel 1991-1994, contro 25-40 nel 1996-1997. Confrontando con Linate (NOAA) la differenza di minima delle stazioni milanesi passa da +4/+6 °C (1990-91) a +1 (1995-2005) a +2/+3 (dopo il 2006): non si capisce quanto sia clima e quanto sensore. **Non fare un grafico "notti tropicali dal 1990" senza questo avviso.**
9. **Il confronto "città contro campagna" dipende dai rurali scelti** (±0,5 °C) e dal fatto che le stazioni rurali ARPA stanno vicino a case e cortili (Rodano v.Turati, Lacchiarella v.Molise sono dentro paesi). Nessuna carta dell'uso del suolo (Copernicus Urban Atlas richiede login: saltato).
10. **Aprile 2026**: il blocco "dal 2021" finisce il 2026-03-01 e il "mese in corso" inizia il 2026-04-02 (Juvara 2026-04-09): manca marzo 2026 (e parte di aprile). Non tocca l'estate.
11. **Intestazioni sbagliate**: il dataset `647i-nhxk` ha 5 campi (`idoperatore` oltre ai 4 degli altri). Interrogato per più sensori restituisce righe a 5 campi con intestazione a 4: il programma le legge per numero di campi.
12. **Alberi**: il censimento comunale copre solo Milano, per cui fuori città il conteggio nel raggio dà zero (non vuol dire senza alberi).
13. Tre stazioni (Landriano, Rodano, Misinto) hanno 54, 3 e 3 letture di temperatura fuori soglia: scartate (`qualita_sensori.csv`).

## 8. Cosa può mostrare una pagina (o due)

**Pagina "Pioggia e nubifragi"**: (1) la striscia degli anni 1858-2008 (giorni di pioggia e totale) con la linea del 2003-2025 dei pluviometri di Milano: totale piatto, giorni di pioggia in calo lento; (2) "metà della pioggia in 88 ore": una barra annua per stazione con la quota dell'1% più bagnato; (3) la lista dei dieci giorni più piovosi della città con le stazioni a confronto (e il caso "Juvara 212 mm" come lezione sui dati sbagliati), con il rimando al Seveso solo se si trova una fonte per le date; (4) 2022 contro 2024 sulle stesse stazioni.

**Pagina "Il quartiere più caldo"**: (1) la curva per ora del giorno (città meno campagna): +2 °C di notte, 0 o meno a mezzogiorno; (2) la mappa dei NIL con i 6 punti e una barra: notti tropicali per estate 2017-2025 (62-68 al centro-nord-ovest, 38 a est, 35-41 nei paesi); (3) 2026 come anno record (79-80 notti tropicali); (4) alberi per ettaro vicino alla stazione come confronto con avviso "6 punti, non prova".

## 9. Da decidere / non fatto

- Verificare con fonti le date delle alluvioni del Seveso prima di collegarle (nessun filone le ha).
- Migliorare la classe urbano/rurale con un dato di copertura del suolo aperto senza login (per esempio GHSL del JRC: non provato qui).
- Omogeneizzare le serie di temperatura (salti dei punti 7-8) o limitarsi a 2017-2025.
- Capire con ARPA perché mancano i pluviometri nel blocco 2011-2020 (16 su 47) e se esistono altrove.
- `raw/` (2,6 GB) e `pulito/intermedi/` (circa 200 MB) non vanno nel repository pubblico; in GitHub solo programmi e tabelle di sintesi (CC0 per ARPA; i valori ECA&D e GSOD in forma aggregata con citazione).
