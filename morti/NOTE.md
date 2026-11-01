# Morti giorno per giorno - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Nessuna pagina web, nessun giudizio sulle cause: solo confronti. Programmi in `scripts/` (si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>`, vedi STATO.md). File grezzi in `raw/` (non fidati, mai eseguiti), tabelle pulite in `pulito/`. Ogni numero qui sotto sta in un file di `pulito/` (indicato tra parentesi).

## 1. In breve

1. **Fonte**: ISTAT, "Decessi e cause di morte: dati giornalieri comunali" (pagina https://www.istat.it/it/archivio/240401), release del **25 agosto 2026**: decessi per giorno, comune di **residenza** del defunto, sesso, classe di età (22 classi, da 0 a 100+), **1/1/2011 - 30/6/2026**. 7.894 comuni, tutti con dati in tutti gli anni.
2. **Licenza**: ISTAT, note legali (https://www.istat.it/note-legali/): "Salvo diversa indicazione, tutti i contenuti pubblicati su questo sito sono soggetti alla licenza ... Creative Commons - Attribuzione - versione 4.0"; "Devi riconoscere una menzione di paternità adeguata ... fornire un link alla licenza e indicare se sono state effettuate delle modifiche". Quindi CC BY 4.0: si può ripubblicare citando ISTAT e dicendo che i dati sono stati elaborati. La pagina del dataset non ha una licenza propria; vale quella generale del sito.
3. **Milano 2011-2025: tra 14.043 (2019) e 14.573 (2017) morti l'anno, tranne il 2020: 18.487.** Nel 2024 sono 13.735 e nel 2025 13.639: i più bassi di tutta la serie (`annuale_confronto.csv`, scope Milano; il 2025 è già stabile tra due release, vedi 6).
4. **Picco Covid**: il giorno con più morti a Milano è il **3 aprile 2020: 137 decessi, 3,5 volte il normale** (normale = 38,9; `picco_2020.csv`). Settimana più alta: 30 marzo - 5 aprile 2020, 839 morti contro 274 attesi (3,06 volte; `milano_settimana.csv`). In Lombardia il giorno massimo è il 21 marzo (1.178, 4,3 volte), in Italia il 27 marzo (3.470, 1,9 volte).
5. **Eccesso marzo-maggio 2020**: Milano +2.934 morti (+83%), Lombardia +27.407 (+112%), Lombardia senza Milano +24.473 (+117%), Italia +51.045 (+32%), Italia senza Lombardia +23.638 (+17%) (`finestre_covid.csv`, rispetto al baseline B, vedi 3).
6. **Sorpresa**: vedi 8.

## 2. Il file ISTAT

- Zip 51.592.163 byte (SHA-256 372696e568983c995a372740125ea2dab9a50d0e8a3787a6d8bdd7080cfa0d1e, in `raw/istat_20260825/`); contiene `comuni_giornaliero_30giugno26.csv` (827 MB, 5.332.982 righe di dati + intestazione, encoding latin-1) e il PDF "Descrizione e tracciato record dati comunali giornalieri" (datato 25 agosto 2026; fonti: rilevazione Istat P.5 sui cancellati dall'anagrafe per decesso, ANPR, Anagrafe Tributaria).
- Una riga = comune x classe di età (`CL_ETA`, 0..21) x giorno dell'anno (`GE` = MMGG). Colonne `M_11..M_26`, `F_11..F_26`, `T_11..T_26` = decessi di quel giorno nei 16 anni (2011-2026). Non c'è un anno per riga: sono 16 colonne.
- **Le righe a zero non ci sono** (NOTA 1 del PDF): se manca un giorno per un comune e classe, non è morto nessuno. Per le medie bisogna riempire gli zeri. Milano ha 6.238 righe su 22 x 366 possibili.
- `n.d.` = non disponibile: solo per il 2026 dopo il 30 giugno (2.570.867 righe), mai per gli anni precedenti. Il 29 febbraio compare con 0 negli anni non bisestili (non è un dato).
- `COD_PROVCOM` = codice ISTAT del comune al 31/3/2026 (Milano 015146). `TIPO_COMUNE` = 1 per tutti i 7.894 comuni (1 = dati fino al 30/6/2026; 2 = dati assenti nel 2026: nessun comune di tipo 2).
- URL scaricato: https://www.istat.it/storage/dati_mortalita/giugno-2026/decessi-comunali-giornalieri-provvisori-4.zip (header `Last-Modified` 25/8/2026, in `raw/istat_20260825/headers.txt`).
- Ho scaricato anche le due release precedenti per misurare le revisioni (6): 31/3/2026 (dati fino al 31/12/2025; https://www.istat.it/storage/dati_mortalita/marzo-2026/decessi-comunali-giornalieri-provvisori-4.zip, 39,5 MB) e 5/8/2025 (fino al 30/6/2025; https://www.istat.it/storage/dati_mortalita/giugno-2025/Dataset%20decessi%20comunali%20giornalieri%20e%20tracciato%20record_dati%20provvisori_4.zip, 43,0 MB). SHA-256 marzo 2026: 3de435f136b43fd91b4d208994adc472de9901369f42d0f77ef4a73dd3a035af; agosto 2025: dd37a5b056a04ef237038b991d70f1f8177611886e8e27a6e726f98e26a0cd7e.

## 3. Cosa ho calcolato (`scripts/build.py`, `scripts/analisi.py`, `scripts/revisioni.py`)

- `pulito/decessi_giorno_eta_sesso.csv`: scope (Milano / Lombardia / Italia), data, classe d'età, M, F, T. Righe a zero omesse. Controlli (`decessi_giorno_eta_sesso_controlli.json`): M+F=T in tutte le righe; totale Italia 10.142.521 nel periodo; i totali annuali Italia coincidono con quelli noti (746.146 nel 2020).
- **Attesi (due varianti, giorno per giorno, lisciati con media mobile centrata a 15 giorni)**:
  - **A, "ultimi 5 anni"**: media dello stesso giorno dei 5 anni precedenti (3 anni per il 2014, 4 per il 2015; non calcolabile prima del 2014).
  - **B, "ultimi 5 anni senza 2020 e 2021"**: come A ma salta 2020 e 2021 (2020: 2015-2019; 2022: 2015-2019; 2024: 2023, 2022, 2019, 2018, 2017). Scelta mia, da confermare: in A dal 2021 il 2020 gonfia la base e gli eccessi diventano negativi (Milano 2023-2025: -8%, -10%, -10% in A contro -3%, -5%, -5% in B).
  - **Età (solo Milano, 2019-2026)**: tassi di morte per classe d'età e sesso del 2019 (morti 2019 / popolazione media 2019; popolazione `POSAS` al 1 gennaio da `censimenti/raw/istat_demo/`, ISTAT demo.istat.it) applicati alla popolazione per età di ogni anno, con la forma stagionale di B (`riepilogo.json`). Fattore di invecchiamento rispetto al 2019: 0,989 (2020), 0,972 (2021), 0,978 (2022), 0,985 (2023), 1,000 (2024), 1,022 (2025), 1,035 (2026). I numeri 2020-2021 sono incerti: la popolazione di Milano scende per l'"aggiustamento statistico" del bilancio demografico (-27.193 nel 2020, -23.365 nel 2021, vedi `censimenti/NOTE.md`), non per i morti. **Prima del 2019 non ho la popolazione per età**: demo.istat.it ha i file POSAS di Milano solo dal 2019 (2011-2018: HTTP 404, provati con curl).
- Settimane: ISO (lunedì-domenica), somma dei giorni; `completa` = 7 giorni nel periodo (la prima del 2014 e l'ultima del 2026 no).
- Temperature: serie giornaliera cucita di Brera `temperature/discrepanza/out/serie_continua_1763_oggi.csv` (TX, TN, TG; fino al 28/10/2026), la stessa del filone temperature. Vale la nota del JOURNAL: nel 2008-2016 Brera ARPA è più calda di circa 0,65 °C (correzione non applicata, decisione di Davide).

## 4. Numeri principali, Milano (tutti da `pulito/`)

**Anni** (`annuale_confronto.csv`): 2020 morti 18.487, attesi B 14.360, eccesso +4.127 (+28,7%); con attesi per età +4.603 (+33,2%). 2021: 14.578 (+262, +1,8% in B; +925, +6,8% con età). 2022: 15.417 (+1.102, +7,7%; con età +12,3%). 2023: 14.075 (-411, -2,8%). 2024: 13.735 (-768, -5,3%). 2025: 13.639 (-650, -4,6%). Primi sei mesi 2026: 6.736 (-263, -3,8%).

**Ondate Covid** (`finestre_covid.csv`, `mensile_confronto.csv`, `milano_settimana.csv`):
- Primavera 2020 (1/3-31/5): 6.449 morti, 3.515 attesi, +2.934 (+83%). Per mese: marzo +102% (Lombardia +193%, Italia +49%), aprile +128% (Lombardia +119%, Italia +41%), maggio +19%. Per settimana: dal 9 marzo (1,75 volte il normale) al 4-10 maggio (1,45); dalla settimana dell'11 maggio si torna a 1,04.
- Autunno 2020 (1/10-31/12): +1.427 (+40%); novembre da solo +920 (+80%). Settimana più alta 9-15 novembre: 531 morti, 2,0 volte. Lombardia +37%, Italia +32% nel trimestre.
- Primavera 2021 (marzo-aprile): +254 (+11%) in B (in A, che contiene il 2020, risulterebbe -10%). Inverno 2021-22 (1/12-31/3): +27 (+0,5%).

**Età e sesso** (`milano_eta_sesso_finestre.csv`, `milano_tassi_eta_sesso.csv`, `milano_composizione_per_anno.csv`):
- Primavera 2020: 85+ anni +1.826 (+108%, cioè 62% dell'eccesso totale), 75-84 +774 (+74%), 65-74 +227 (+52%), 0-64 +107 (+31%). Uomini +1.314 (+82%), donne +1.620 (+85%): in valore assoluto più donne perché sono più numerose tra gli anziani. Per fascia: 65-74 uomini +65%, donne +36%; 0-64 uomini +48%, donne +7%.
- Autunno 2020: uomini +53%, donne +29%.
- Quota di morti con 85+ anni: 43,1% nel 2011, 51,1% nel 2019, 55,5% nel 2025. Sotto i 65 anni: 10,9% nel 2011, 9,0% nel 2025.
- Tassi per 100.000 (popolazione media POSAS): uomini 85+ 13.082 (2019), 13.111 (2025); donne 85+ 11.396 (2019), 10.864 (2025); donne 75-84 2.527 → 2.590; uomini 75-84 4.179 → 3.943.
- Morti 2025: maschi 6.159, femmine 7.480.

**Caldo** (`ondate_caldo.csv`, `estati_confronto.csv`, `estati_pct_per_area.csv`, `estate_rapporto_per_tmax3.csv`). Definizione mia: ondata = almeno 3 giorni di fila con TX >= 33 °C a Brera; finestra = giorni dell'ondata + 3 giorni dopo; eccesso rispetto a B. 39 ondate nel 2014-2025.
- Le più alte per eccesso: **14-26 luglio 2022** (13 giorni, TX max 37,3): +260 morti (+44%), di cui 85+ +179. **12-24 luglio 2015** (TX max 37,5): +164 (+29%); **2-8 luglio 2015** (TX max 36,4): +133 (+38%). 3-6 agosto 2022 +89 (+34%); 12-25 agosto 2023 (TX max 37,9) +82 (+13%); 3-8 agosto 2018 +76 (+23%).
- Mesi: luglio 2015 +299 (+27%); luglio 2022 +285 (+25%), agosto 2022 +236 (+21%); luglio 2023 -137 (-12%).
- Estati (giugno-agosto) rispetto a B: 2015 +10,4% (35 giorni con TX >= 33), 2022 +15,2% (33 giorni), ma 2023 -7,7% (27 giorni), 2024 -4,1% (34 giorni), 2025 -4,7% (30 giorni). Con gli attesi per età: 2022 +654 morti, 2023 -110, 2024 -33, 2025 -173.
- Stessa estate, altre aree: 2022 Lombardia senza Milano +18,1%, Italia +15,5%; 2015 Lombardia senza Milano +13,2%, Italia +9,1%; 2019 Lombardia senza Milano +6,9% ma Milano -4,8%; 2023 Lombardia senza Milano -1,4%, Italia -0,3% (Milano -7,7%).
- Tutti i giorni di giugno-agosto 2014-2025 divisi per la massima media dei 3 giorni (d-2..d): rapporto morti/attesi 0,93 (sotto 27 °C), 0,96 (27-30), 0,98 (30-32), 1,02 (32-34), 1,14 (34-36), 1,22 (sopra 36; 31 giorni).
- Estate 2026: i morti arrivano al 30 giugno, le temperature a fine ottobre, quindi **l'estate 2026 non è coperta** (giugno 2026 +1,1%). Agosto 2003 è prima del 2011.

**Freddo e influenza** (`ondate_freddo.csv`, `inverni_confronto.csv`): a Brera dal 2014 una sola sequenza di almeno 3 giorni con temperatura media <= 0 °C (26/2-1/3/2018: +21 morti, +4,6% nella finestra con 7 giorni dopo). Con soglia <= 3 °C: 6-13 gennaio 2017 (TG medio 0,4): +230 (+34%), di cui 85+ +176, l'episodio più alto (la settimana 2-8 gennaio 2017 è tra le 25 più alte, 1,41 volte). Altri episodi con soglia 3 °C sono entro +/-13%, anche negativi (gennaio 2016 -12%). Inverni (1/12-31/3) rispetto a B: 2016/17 +7,9%, 2014/15 +3,8%, 2015/16 -7,0%, 2023/24 -7,5%, 2024/25 -6,3%; 2019/20 +18,2% ma contiene febbraio-marzo 2020 (non confrontabile). Nei dati non c'è un'influenza separabile dal resto.

## 5. Coperture e cambi nel file

- Nessun comune assente in nessun anno (7.894 comuni, tutti `TIPO_COMUNE` 1). Milano ha tutte le 22 classi d'età.
- La classificazione dei comuni è quella al 31/3/2026: i comuni fusi sono già riportati ai codici nuovi. Milano non ha subito variazioni.
- Nelle release vecchie il numero di comuni cambiava (pagina ISTAT: 7.357 comuni per il 2020 nella release di agosto 2020, 7.903 in ottobre 2020): la release 2026 non ha il problema.
- **È per comune di residenza**, non di luogo di morte: i milanesi morti altrove contano, i non residenti morti negli ospedali di Milano no. I numeri non sono "morti avvenuti a Milano".

## 6. Dati provvisori e revisioni (`revisioni_release.csv`)

Il file si chiama "provvisori", ma i totali annuali 2011-2024 sono **identici** nelle tre release (5/8/2025, 31/3/2026, 25/8/2026; Milano, Lombardia, Italia). Il 2025 completo è identico tra la release di marzo e quella di agosto 2026: è già stabile. Il rischio è sugli ultimi mesi: la release di agosto 2025 (5 settimane dopo la fine del semestre) aveva contato meno morti di quelli oggi noti per i primi sei mesi del 2025. Milano: gennaio -0,7%, febbraio -1,0%, marzo -0,4%, aprile -0,8%, maggio -1,9%, **giugno -3,5%** (1.032 contro 1.069); Italia giugno -2,3% (49.294 contro 50.455). La release attuale ha il 2026 con 8 settimane di ritardo, non 5, quindi **maggio-giugno 2026 sono forse sottostimati di qualche punto**. Per affermazioni sul 2026 usare gennaio-aprile o aspettare la release successiva.

## 7. Trappole

1. **Residenza, non luogo del decesso** (vedi 5).
2. **Righe a zero mancanti**: le somme vengono giuste, ma medie e conteggi di giorni sbagliano se non si riempie.
3. **Il baseline "ultimi 5 anni" dopo il Covid è sporco**: dal 2021 contiene il 2020 (Milano 2023: -8,2% in A, -2,8% in B). Qualunque scelta è convenzionale: dire quale.
4. **Il baseline B non segue l'invecchiamento**: per la Lombardia il 2015-2019 ha +1% / +7% di eccesso "normale" (popolazione che invecchia, 2014 anno basso). Per Milano il livello è piatto (14.0-14.6 mila) e B funziona; per Lombardia e Italia i confronti in percentuale 2021-2025 sono approssimativi.
5. **Popolazione per età 2019-2021**: l'"aggiustamento statistico" di Milano abbassa i denominatori; il confronto con gli attesi per età è un controllo, non un secondo risultato.
6. **Giorno di decesso, non di registrazione**, ma gli ultimi mesi si riempiono con ritardo (6).
7. **Temperatura di Brera 2008-2016 troppo calda (circa 0,65 °C)**: con soglia fissa a 33 °C le ondate 2014-2016 sono leggermente sovrastimate.
8. **Soglie e finestre di caldo/freddo sono mie** (TX >= 33 °C per 3 giorni, +3 giorni dopo; TG <= 0 o 3 °C, +7 giorni): cambiandole cambiano gli elenchi. `z_poisson` = eccesso / radice degli attesi: ignora l'incertezza del baseline, solo ordine di grandezza.
9. **Rumore giornaliero**: a Milano un giorno ha circa 39 morti attese (deviazione circa 6): sotto 10-15 di scarto non c'è segnale.
10. **File in latin-1**: i nomi dei comuni si rompono se letti come UTF-8 (il codice `COD_PROVCOM` no).

## 8. La cosa più sorprendente

**Stesse estati calde, risultati opposti.** A Brera i giorni con almeno 33 °C sono 35 nel 2015, 33 nel 2022, 34 nel 2024: eppure l'estate (giugno-agosto) ha avuto +10% di morti nel 2015, +15% nel 2022 e **-4% nel 2024**; il 2023 (27 giorni, massima 37,9 °C in agosto) -8%, con luglio 2023 a -12%. Nelle ondate più forti l'eccesso è quasi tutto tra gli 85+ (179 su 260 a luglio 2022). Solo confronto, nessuna causa.
Seconde sorprese: **Milano nel 2025 ha 13.639 morti, il minimo dal 2011**, nonostante più anziani (quota di morti con 85+ anni dal 43% al 55%): i tassi delle donne 85+ scendono da 11.396 a 10.864 per 100.000 dal 2019 al 2025, gli uomini sono fermi. E **a marzo 2020 Milano ha +102% contro +193% della Lombardia**, ma ad aprile il rapporto si inverte (+128% contro +119%): il picco di Milano è più tardivo (3 aprile contro 21 marzo).

## 9. Cosa potrebbe mostrare una pagina

- Un anno a barre (circa 14.000 morti) con la riga "normale" e il 2020 che esce dalla pagina; poi lo zoom marzo-aprile 2020 giorno per giorno (137 il 3 aprile contro 39).
- Milano - Lombardia - Italia in percentuale (marzo 2020: 102 / 193 / 49) e il ritardo del picco di Milano.
- Ondate di caldo (luglio 2015, luglio 2022, agosto 2023) contro la temperatura di Brera con la linea degli attesi, e le estati in cui con lo stesso caldo non c'è eccesso.
- Chi muore: fascia d'età, uomini/donne, e la quota 85+ (43% → 55%).
- Sempre come confronto con "il normale", mai con una causa. Citazione: ISTAT, CC BY 4.0, dati provvisori, elaborazione Milano in dati; dichiarare il baseline.

## 10. File

`raw/istat_20260825/` (zip; `x/` = csv estratto e PDF), `raw/istat_20260331/` e `raw/istat_20250805/` (solo zip, csv estraibili). `pulito/`: `decessi_giorno_eta_sesso.csv`, `{milano,lombardia,italia}_{giorno,settimana}.csv`, `annuale_confronto.csv`, `mensile_confronto.csv`, `finestre_covid.csv`, `picco_2020.csv`, `milano_eta_sesso_finestre.csv`, `milano_tassi_eta_sesso.csv`, `milano_composizione_per_anno.csv`, `ondate_caldo.csv`, `ondate_freddo.csv`, `estati_confronto.csv`, `estati_pct_per_area.csv`, `estate_rapporto_per_tmax3.csv`, `inverni_confronto.csv`, `milano_settimane_top_eccesso.csv`, `milano_settimane_piu_basse.csv`, `milano_giorni_top.csv`, `revisioni_release.csv`, `riepilogo.json`, `rev_*_decessi.csv` (stessa tabella per le release vecchie), log.
