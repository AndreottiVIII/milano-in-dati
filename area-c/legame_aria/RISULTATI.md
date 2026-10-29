# Area C e aria: gli ingressi cambiano l'aria vicino ai varchi? (29/10/2026)

Domanda di Davide: gli ingressi in Area C cambiano l'aria nelle stazioni vicine? Dentro Area C: via Senato e Verziere. Fuori: le altre stazioni di Milano (tutte dentro Area B) e cinque stazioni ARPA fuori Milano.
Tutti i file sono in `area-c\legame_aria\`. Ogni numero dice da quale file e campo viene. La pagina del sito è `docs\area-c\index.html`, sezione "Area C e l'aria".

## Risposta in breve
Con questi dati **non si vede un legame stabile** tra quanti veicoli entrano in Area C in un giorno e quanto l'aria delle stazioni dentro è più (o meno) sporca di quella fuori. Non è una prova che Area C non conti: gli intervalli sono troppo larghi per escludere effetti piccoli o medi, e le stazioni sono poche.

- **Giorno per giorno** (feriali normali, tolti giorno della settimana, mese, anno e meteo): per 10.000 ingressi in più, la differenza di NO2 dentro − resto di Milano cambia di **−0,08 µg/m³ [−0,71 ; +0,54]** (`regressioni.csv`, campione "feriali normali", specifica "4 + meteo", variabile `D_NO2m_B`, campo `effetto_per_10mila_ingressi`, intervallo in `ci95_basso/alto`; 1.119 giorni, 285 settimane). Da un giorno all'altro quella differenza varia di ±6,55 µg/m³ (`dev_std_differenza`).
- **Esperimenti naturali** (`esperimenti_naturali.csv`): non vanno tutti nello stesso senso (vedi sotto).
- **Tendenza 2016-2024** (`tendenza_annuale.csv`, `tendenza_correlazioni.csv`): gli ingressi calano di un quarto, dentro − resto di Milano non si muove; dentro − fuori Milano scende ma è la città che scende più dell'hinterland.
- **Prima/dopo 16/1/2012** (`prima_dopo_2012.csv`, `prima_dopo_2012_placebo.csv`): il NO2 dentro scende più che fuori, ma negli altri anni lo stesso confronto varia di altrettanto.

## 1. Come si è fatto (in parole semplici)
1. **Perché le differenze.** Il meteo muove l'aria di tutta la città insieme. Si guarda quindi la differenza nello stesso giorno tra stazioni dentro e stazioni fuori: il meteo comune sparisce in gran parte.
2. **Gruppi** (`01_panel.py`): *dentro* = media di Senato e Verziere; *resto di Milano* = media di viale Marche, viale Liguria, via Pascal; *fuori Milano* = media di Pioltello, Magenta, Sesto San Giovanni, Rho, Cinisello (almeno 4 su 5). Un giorno vale solo se ci sono tutte le stazioni del gruppo (così il gruppo non cambia). Dati d'aria: `aria\pulito\aria_giornaliera.csv` e `controlli_giornaliera.csv`; il Black Carbon viene dai dati orari grezzi `aria\raw\arpa\*\sensore_*.csv` (sensori 20005/20465 Senato, 20004/20581 Pascal, 29001/20455 Marche), media giornaliera con almeno 18 ore valide.
3. **Giorni:** feriali non festivi (campo `lavorativo` di `area-c\pulito\calendario.csv`) dal 1/9/2016 al 30/11/2024 con ingressi presenti: 2.070 giorni (`copertura.csv`). Gli ingressi sono il campo `totale` di `ingressi_giornalieri.csv` (moto comprese). La serie 2012-2015 non è usata (altro conteggio).
4. **Giorni "normali":** senza agosto, 24/12-6/1 e il periodo Covid 9/3/2020-8/6/2021: 1.554 giorni (1.170 con la differenza di NO2).
5. **Meteo** (ARPA Lombardia, dati.lombardia.it, CC0, `00_scarica_meteo.py`, `00b_meteo_giornaliero.py`): Milano Brera sensori 19007 (vento), 19373 (pioggia), 5897 (temperatura); Milano Lambrate 2003, 2006, 2001 (solo per il 2011-2013). Medie giornaliere con almeno 116 intervalli da 10 minuti su 144. Variabili usate: vento, vento al quadrato, pioggia sì/no (≥1 mm), temperatura, vento e pioggia del giorno prima (`meteo_giornaliero.csv`, 3.000 giorni circa).
6. **Stime** (`lib.py`): minimi quadrati con errori standard "a grappoli" per settimana (giorni vicini si assomigliano); Spearman con intervallo ricampionando settimane intere. Intervalli al 95%.

## 2. Giorno per giorno: ingressi e differenza dentro − fuori (`02_regressioni.py` → `regressioni.csv`)
Effetto per +10.000 ingressi. Ingressi nei giorni normali: media 149.578, scarto tipico 16.500 (campi `ingressi_media`, `ingressi_dev_std`). Specifica 4 = con giorno della settimana, mese, anno e meteo.

| Cosa | giorni | effetto per +10.000 ingressi [intervallo] | campione `feriali normali` |
|---|---|---|---|
| NO2 medio, dentro − resto di Milano (`D_NO2m_B`) | 1.119 | −0,08 [−0,71 ; +0,54] | |
| NO2 medio, dentro − fuori Milano (`D_NO2m_C`) | 1.297 | −0,02 [−0,46 ; +0,41] | |
| NO2 massimo orario, dentro − resto di Milano (`D_NO2x_B`) | 1.128 | −0,28 [−1,35 ; +0,80] | |
| PM10 dentro − Pascal (`D_PM10_B`) | 1.230 | −0,20 [−0,53 ; +0,14] | |
| PM10 dentro − fuori Milano (`D_PM10_C`) | 1.236 | −0,24 [−0,57 ; +0,08] | |
| PM2,5 Senato − Pascal (`D_PM25_B`) | 1.290 | −0,06 [−0,43 ; +0,31] | |
| Black Carbon Senato − viale Marche (`D_BC_Marche`, 11/2020-11/2024) | 559 | −0,034 [−0,073 ; +0,005] | |
| Black Carbon Senato − Pascal (`D_BC_Pascal`, 9/2016-12/2017) | 206 | −0,036 [−0,159 ; +0,087] | |

- **Specifiche più semplici** (solo giorno della settimana e mese, specifica "2"): sul NO2 massimo orario −1,39 [−2,20 ; −0,59] e sul PM10 dentro − Pascal −0,33 [−0,62 ; −0,04]; per dentro − fuori Milano +1,08 [+0,67 ; +1,50]. Appena si aggiunge l'anno (specifica "3") spariscono tutte: erano la tendenza di fondo (anche gli ingressi di 7 giorni dopo, "placebo", danno stime simili, ma sono tutte vicine a zero).
- **Con tutti i feriali, compresi agosto, Natale e Covid** (campione "tutti i feriali", specifica 4): PM10 dentro − fuori Milano +0,29 [+0,11 ; +0,47], PM2,5 +0,21 [+0,07 ; +0,36], rapporto NO2 dentro/resto di Milano +0,90% [+0,24 ; +1,56], NO2 in µg/m³ +0,20 [−0,09 ; +0,48]. Vengono dai periodi di calo di tutto il traffico; anche il placebo dei 7 giorni dopo dà +0,22 [+0,07 ; +0,38] per PM10 dentro − fuori Milano.
- **Spearman** (campo `spearman_grezzo`, `spearman_dopo_aver_tolto_anche_meteo`): per dentro − resto di Milano −0,09 e +0,01.
- **Black Carbon:** il segno è opposto a quello atteso (più ingressi → Senato relativamente meno BC di viale Marche) e il placebo dà zero (+0,0035 [−0,027 ; +0,034]). Lettura possibile, non verificata: viale Marche segue il traffico di tutta la città più di via Senato.
- **Per coppie di stazioni** (`07_robustezza.py` → `robustezza_coppie.csv`, specifica 4): 6 coppie su 8 danno zero (intervallo con lo zero); contro via Pascal +0,62 [+0,03 ; +1,21] (Senato) e +0,72 [+0,20 ; +1,25] (Verziere). Pascal ha salti di livello (vedi trappole).
- **Cosa non si può escludere:** l'intervallo di NO2 dentro − resto di Milano arriva a +0,54 per 10.000 ingressi, cioè circa 8 µg/m³ su tutti i circa 150.000 ingressi al giorno: un effetto di quella grandezza è compatibile coi dati e non si vedrebbe.

## 3. Esperimenti naturali (`03_esperimenti.py` → `esperimenti_naturali.csv`, versione con meteo `esperimenti_naturali_meteo.csv`)
Differenza media tra i giorni del periodo e i giorni di confronto, tolto il giorno della settimana (e l'anno). Campo `differenza`, intervallo `ci95_basso/alto`. Ingressi in migliaia al giorno (campo `ingressi10k` × 10).

| Periodo (confronto) | ingressi | NO2 dentro − resto di Milano | in % | NO2 dentro − fuori Milano | con meteo (D_NO2m_B) |
|---|---|---|---|---|---|
| Agosto 8-23 (27/6-25/7 e 6/9-4/10 stesso anno; 80 / 261 giorni) | −92 | −2,25 [−3,90 ; −0,60] | −12,8% | −1,86 [−2,98 ; −0,73] | −3,24 [−4,94 ; −1,54] |
| Natale 27/12-5/1 (15/11-13/12 e 12/1-9/2; 39 / 232) | −57 | +1,50 [−0,67 ; +3,67] | +3,8% | +2,50 [+0,76 ; +4,25] | +1,04 |
| Ponti (11 / 51) | −50 | +0,63 [−4,11 ; +5,36] | −3,0% | −1,12 [−3,28 ; +1,05] | +1,43 |
| Covid, lockdown stretto 12/3-3/5/2020 (stesse date 2018-19; 35 / 60) | −115 | −8,16 [−11,61 ; −4,70] | −22,0% | −7,92 [−11,06 ; −4,78] | −7,17 |
| Covid, riaperture, Area C sospesa 4/5-14/6/2020 (27 / 22) | −59 | −3,09 [−8,00 ; +1,82] | −9,8% | −5,74 [−8,88 ; −2,60] | −1,64 |
| Covid, seconda sospensione 5/11/2020-23/2/2021 (49 / 121) | −32 | **+6,00** [+3,20 ; +8,81] | +10,3% | +1,65 [−1,02 ; +4,32] | +5,98 |
| Covid, orario ridotto 24/2-8/6/2021 (46 / 98) | −31 | −6,25 [−9,19 ; −3,31] | −14,1% | −8,07 [−10,68 ; −5,46] | −6,08 |

- Agosto e lockdown stretto: la differenza si abbassa, come atteso se i veicoli di Area C pesassero. Natale e seconda sospensione: sale. Con soli −31.000 ingressi l'orario ridotto fa −6,25. Nessuna relazione ordinata col numero di ingressi.
- Agosto anno per anno (righe "Agosto ... anno" di `esperimenti_naturali.csv`, `D_NO2m_B`): 2017 −0,72; 2018 −12,12; 2019 −5,79; 2020 −1,56; 2021 +0,17; 2022 −0,68; 2023 +2,45; 2024 −2,88: negativo in 6 anni su 8.
- **Cosa confonde:** in agosto e nel lockdown cala il traffico di tutta la città e tutti i valori di NO2 si abbassano; la differenza in µg/m³ si accorcia solo per questo (per questo c'è la colonna in %). Le date delle sospensioni di Area C sono da fonti pubbliche, "da verificare" (`area-c\pulito\eventi.csv`); il campo `areac` dei dati non dice se Area C era sospesa.

## 4. Tendenza 2016-2024 (`04_tendenza.py` → `tendenza_mensile.csv`, `tendenza_annuale.csv`, `tendenza_correlazioni.csv`)
Feriali senza il periodo Covid (3/2020-6/2021); mesi con meno di 8 giorni validi non usati.
- Ingressi: 166.832 (2016) → 127.124 (2024) al giorno, feriali dell'anno (`tendenza_annuale.csv`, campione "feriali dell'anno", campo `ingressi`); pendenza −4.059 al giorno ogni anno.
- **Dentro − resto di Milano** (`D_NO2m_B`): da −4,6 (sett.-nov. 2016) a −0,1 (2024), senza tendenza (pendenza +0,005 µg/m³ l'anno, p = 0,98). Correlazione mensile con gli ingressi −0,07 [Spearman; 82 mesi], tolta la stagione −0,03.
- **Dentro − fuori Milano** (`D_NO2m_C`): da +11,9 (sett.-nov. 2016) a +1,1 (2024), pendenza −0,97 µg/m³ l'anno; correlazione con gli ingressi +0,34 (mensile), +0,43 (tolta la stagione), +0,81 (8 medie annuali). Ma NO2 dentro scende di 3,35 µg/m³ l'anno, il resto di Milano di 3,33, le 5 stazioni fuori Milano di 2,36: la città scende più dell'hinterland. Due linee che scendono insieme sono correlate comunque: non prova nulla. Appena si toglie l'anno nelle stime giornaliere (sezione 2) la relazione sparisce.

## 5. Prima e dopo l'avvio di Area C, 16/1/2012 (`05_prima_dopo_2012.py` → `prima_dopo_2012.csv`, `_placebo.csv`, `_mensile.csv`, `_con_meteo.csv`)
12 mesi prima (16/1/2011-15/1/2012) contro 12 mesi dopo (16/1/2012-15/1/2013), feriali non festivi. Fuori Milano = 5 stazioni; resto di Milano = Marche e Liguria (Pascal non ha la media del NO2 nel 2012). Le stesse stime sono rifatte per le altre 13 coppie di anni (prima dal 16/1/2005 al 16/1/2018): "placebo".
- NO2 dentro 66,63 → 54,99 µg/m³ (−17,5%); resto di Milano 79,93 → 76,58 (−4,2%); fuori Milano 59,36 → 55,41 (−6,6%) (campi `media_prima`, `media_dopo`, `differenza_percento`).
- Dentro − resto di Milano: −5,78 [−9,28 ; −2,27]; dentro − fuori Milano: −8,14 [−10,27 ; −6,01]. Negli altri anni (`prima_dopo_2012_placebo.csv`): dentro − resto di Milano da −11,44 a +17,41 (dev. std 7,88), in 5 casi su 13 il cambio è uguale o più grande in valore assoluto; dentro − fuori Milano da −8,95 a +10,49, 4 casi su 13. L'intervallo del cambio (errori a grappoli per settimana) è molto più stretto della variazione da un anno all'altro: il confronto con gli altri anni è quello onesto.
- PM10 dentro − Pascal: −5,17 [−8,21 ; −2,13] (altri anni da −0,87 a +4,57, nessuno così grande). Ma `prima_dopo_2012_mensile.csv` (campo `P_B`) mostra che nasce dall'inverno 2010-2011 (dicembre 2010 +10,6; gennaio 2011 +24,0; febbraio 2011 +18,2), con la differenza tornata vicino a zero da aprile 2011, prima di Area C. Non c'è un gradino a gennaio 2012.
- Con il meteo di Lambrate (il vento, la pioggia e la temperatura ci sono solo in 265-297 giorni su circa 450): dentro − fuori Milano da −5,36 a −6,60; dentro − resto di Milano da −7,10 a −9,16 (`prima_dopo_2012_con_meteo.csv`, campi `senza_meteo`, `con_meteo`, stessi giorni). I livelli assoluti cambiano troppo su quel sottoinsieme per essere usati.
- **Ecopass:** dal 2008 al 2011 nello stesso centro c'era già Ecopass: si confronta Area C con Ecopass, non con il nulla.

## 6. Cosa i dati non possono dire
- Non misurano l'effetto di Area C: mostrano solo se la differenza dentro − fuori si muove con gli ingressi o con le date di eventi. Non sappiamo cosa sarebbe successo senza Area C.
- Solo due stazioni dentro e tre fuori in città; il tipo di sito (traffico o fondo) non è nei dati scaricati. Un solo strumento spostato o cambiato sposta il risultato.
- Il traffico dentro Area C e quello fuori si muovono insieme (festivi, estate, Covid): gli esperimenti naturali non isolano Area C.
- Con la variabilità giornaliera di ±6,5 µg/m³ non si vedrebbe un effetto fino a circa 0,5 µg/m³ ogni 10.000 ingressi.
- Il perimetro (Senato e Verziere dentro) è una nostra lettura, non controllata sulla mappa ufficiale; le date Covid e delle regole vengono da fonti non ufficiali.
- Correlazione non è causalità.

## 7. Trappole dei dati trovate in questo lavoro
1. **Il Black Carbon di via Pascal manca dal 2018 al 2025** nei dati scaricati: il sensore 20004 ha dati dal 30/9/2013 al 1/1/2018 (dataset `nr8w-tj77`) e dal 1/1/2026 (dataset `nicp-bhqi`); il dataset 2018-2025 (`g2hp-ar79`) non ha righe per 20004 né per 20581. Il confronto Senato − Pascal esiste quindi solo 9/2016-12/2017 (255 giorni feriali). Senato − viale Marche solo da 11/2020 (il BC di Marche ricomincia il 25/11/2020).
2. **Il NO2 di via Pascal ha un salto nell'aprile 2011** (da 65 a 34 µg/m³ in un mese, mentre le altre stazioni scendono di meno: `aria_giornaliera.csv`, medie mensili) e scarti dal gruppo di controllo che oscillano di ±10 µg/m³ da un trimestre all'altro negli anni successivi: probabile cambio di strumento o di taratura, non verificato. Per questo il 2012 è stato fatto senza Pascal.
3. **Meteo ARPA: i dataset "Dati sensori meteo NNNN" sono tutti filtri della stessa tabella, che contiene solo il periodo recente** (da marzo 2026): lo storico è in dataset separati per grandezza (vento `x9gp-z9xx` 2011-2020 e `hu5q-68e3` dal 2021; pioggia `2kar-pnuk` e `pstb-pga6`; temperatura `d4kj-kbpj` e `w9wd-u6jh`). Dopo una scansione troppo veloce di circa 130 dataset il server ha risposto "Too many requests" per circa 40 minuti: errore mio, rimediato con pause e ripetizioni (`00_scarica_meteo.py`).
4. **Il vento di Brera ha un buco dal 1 al 23 settembre 2016**; la pioggia di Brera parte l'11/7/2016 (prima di allora non c'è nessun pluviometro a Brera nel registro): per questo il 2011-2013 usa Lambrate. Lambrate ha vento in 1.198 giorni su 1.461 (2011-2014), quindi la versione "con meteo" del 2012 usa solo giorni con tutto.
5. **Le stazioni di controllo hanno solo la media giornaliera del NO2**, non il massimo orario: per il massimo orario il confronto c'è solo dentro − resto di Milano.
6. **Le tre stazioni "fuori" in Milano devono esserci tutte** nello stesso giorno: dei 2.070 feriali, 1.574 hanno la differenza dentro − resto di Milano (`copertura.csv`).
7. **Il campo `areac` degli ingressi non dice se Area C era sospesa** (vedi `area-c\pulito\problemi.md`): le sospensioni Covid sono da fonti pubbliche.

## 8. Programmi e file
In ordine di esecuzione (da `area-c\legame_aria\`, `python -I`; `lib.py` è importato dagli altri):
- `00_scarica_meteo.py raw_meteo` (ripetibile; scarica 85 MB di dati a 10 minuti: `raw_meteo\`, non pubblicati) → `00b_meteo_giornaliero.py raw_meteo meteo_giornaliero.csv`
- `01_panel.py <milano-in-dati> .` → `pannello_giornaliero.csv`, `copertura.csv`
- `02_regressioni.py .` → `regressioni.csv`, `scatter_NO2_B.csv`
- `03_esperimenti.py .` e `03_esperimenti.py . meteo` → `esperimenti_naturali.csv`, `esperimenti_naturali_meteo.csv`
- `04_tendenza.py .` → `tendenza_mensile.csv`, `tendenza_annuale.csv`, `tendenza_correlazioni.csv`
- `05_prima_dopo_2012.py <milano-in-dati> .` → `prima_dopo_2012*.csv`, `pannello_2005_2019.csv`
- `07_robustezza.py .` → `robustezza_coppie.csv`
- `06_sito_json.py . ..\..\docs\area-c\data\legame_aria.json` → dati della pagina (119 KB)

Licenze: meteo ARPA Lombardia CC0; aria ARPA CC0 e Comune di Milano; ingressi Comune di Milano / AMAT CC BY. Il pannello giornaliero (1,4 MB) mescola le tre fonti: va citato così se pubblicato. Nessun git.
