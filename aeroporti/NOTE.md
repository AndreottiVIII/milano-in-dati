# Filone "Aeroporti" (aeroporti/)

Fase 1 + pagina (`docs/aeroporti/index.html`). Dati scaricati il 2 novembre 2026. Tutto ripetibile con i programmi in `scripts/` (vedi STATO.md).

## 1. Fonti e licenze

| Cosa | Fonte | Anni | Licenza | File |
|---|---|---|---|---|
| Passeggeri per aeroporto (totale, nazionali, internazionali, UE, extra UE), annuali e mensili | Eurostat, tabella `avia_paoa` (API di diffusione, JSON-stat), tutti gli aeroporti europei; si tengono quelli IT_* | 1993-2025 (annuale), 1993-2026-05 per i tre aeroporti (mensile); affidabile dal 2004 | CC BY 4.0 | `raw/eurostat/avia_paoa_*.json` |
| Voli commerciali con passeggeri per aeroporto | Eurostat `avia_paoa`, misura CAF_PAS | come sopra | CC BY 4.0 | `raw/eurostat/avia_paoa_*_voli*.json` |
| Merci e posta per aeroporto (tonnellate) | Eurostat `avia_gooa`, misura FRM_LD_NLD | come sopra | CC BY 4.0 | `raw/eurostat/avia_gooa_*.json` |
| Passeggeri per paese (solo controllo) | Eurostat `avia_paoc` | 1993-2025 | CC BY 4.0 | `raw/eurostat/avia_paoc_A_pax_it.json` |
| Serie 1994-2003 dei tre aeroporti e dell'Italia (movimenti, passeggeri, cargo) | ENAC, Annuario statistico 2003, pagine PDF 150 (Italia), 152 (Malpensa), 153 (Linate), 156 (Bergamo) | 1994-2003 | nessuna licenza scritta sulla pagina; statistica ufficiale di un ente pubblico | `raw/enac/Dati-di-traffico-2003.pdf` |
| Controllo | ENAC, Dati di traffico 2007 (p. 9), 2010 (p. 13), 2024 (p. 76), 2025 (p. 74); Annuari 2000-2002 scaricati e guardati (Tavola APT 1 2001 p. 12, 2002 p. 10) | - | come sopra | `raw/enac/*.pdf` |
| Assaeroporti, Dati di traffico (xlsx mensili dal 2000) | assaeroporti.com/statistiche (link `data-upload.assaeroporti.com/download-export/AAAA/M`) | 2000-2026 | **Note legali: "La riproduzione e' vietata ... senza il preventivo consenso scritto"; copia solo per uso personale; ristampa in pubblicazioni solo non elettroniche** | scaricato UN solo file (dicembre 2025) per vedere la struttura, NON conservato ne' usato; nessun numero pubblicato |

Rate: una richiesta per volta con pausa 3-5 s, User-Agent che dichiara chi siamo, nessuna registrazione, nessuna verifica superata. robots.txt di Assaeroporti non vieta i file. Log in `raw/download_log.csv`.

**Decisione sulle condizioni d'uso**: dato che Assaeroporti vieta la riproduzione elettronica, la pagina e' costruita su Eurostat (CC BY) + ENAC (ente pubblico) e cita Assaeroporti solo come fonte da consultare. Se Davide vuole i dati Assaeroporti (che includono l'aviazione generale e i mesi dopo maggio 2026), serve il consenso scritto di Assaeroporti.

## 2. Come sono fatti i dati

- Eurostat: `PAS_CRD` = passeggeri trasportati (arrivi + partenze dello stesso aeroporto; il totale "Italia" e' la somma degli aeroporti, 34-36 per anno dal 2004). Prima del 2004 i valori sono segnati "u" (poco affidabili) e per il 1999-2000 sono zero. Il totale per paese di Eurostat e' piu' basso della somma degli aeroporti (160,7 milioni contro 192,6 nel 2019): probabilmente conta i voli nazionali una volta sola (ipotesi, non verificata nei metadati).
- ENAC: traffico commerciale (servizi di linea e non di linea) arrivi + partenze, movimenti, passeggeri, tonnellate. Nell'Annuario 2003 per Linate c'e' la nota "variazione dall'anno 1998 dovuta all'apertura il 05/10/1998 di Malpensa 2000".
- La pagina 156 dell'Annuario 2003 (Bergamo) non ha il nome nel testo: e' stata identificata dall'ordine alfabetico (Bari 155, Bologna 157) e controllata con i valori 2001 e 2002 dei rapporti 2001 e 2002 (1.046.454 e 1.287.059).

## 3. Controlli fatti (`pulito/controlli.txt`, `pulito/controllo_eurostat_enac.csv`)

1. Nazionali + internazionali = totale, e UE + extra UE = internazionali, 2004-2025, tre aeroporti: 0 eccezioni.
2. Somma dei 12 mesi = totale annuo, 2004-2025, tre aeroporti: 0 differenze.
3. Passeggeri Eurostat contro ENAC (2001-2003, 2007, 2010, 2024, 2025): differenza entro 0,5% per Linate, Malpensa, Bergamo e Italia, tranne Bergamo 2002 (-4,2%, anno segnato "u" da Eurostat, si usa ENAC) e Linate 2001 (+0,8%). Es.: Malpensa 2025 31.226.087 (Eurostat) / 31.220.874 (ENAC p. 74); Italia 2025 229.083.370 / 229.389.513.
4. Merci: entro 1% per Bergamo e Malpensa; Linate 2007 -3,2% (numero piccolo); Italia entro 1,6%.
5. Classifica 2025 (Eurostat): Fiumicino, Malpensa, Bergamo, Napoli, Catania, Venezia, Bologna, Linate (8o), Palermo: coincide con ENAC 2025 p. 82.
6. Movimenti: ENAC contro "voli" Eurostat NON coincidono (2025: Malpensa 216.430 / 195.407; Linate 92.823 / 106.069; Bergamo 100.263 / 99.518): definizioni diverse, la serie dei voli e' solo Eurostat dal 2004, ENAC e' un controllo.

## 4. Limiti dei dati (anche nella pagina)

1. Raccordo ENAC-Eurostat nel 2004 (passeggeri entro 1%; per i voli no).
2. Nazionali/internazionali solo dal 2004.
3. Voli = voli commerciali con passeggeri (Eurostat), senza voli di sola merce e aviazione generale; prima del 2004 movimenti commerciali ENAC.
4. Passeggeri contati all'arrivo e alla partenza (voli nazionali due volte nel totale Italia).
5. Merci = merci + posta caricate e scaricate.
6. Date della chiusura di Linate (27/7-27/10/2019) dalla stampa (Il Post 9/7/2019, Teleborsa 27/7/2019), non dal gestore; i dati mensili le confermano (agosto e settembre 2019 a zero).
7. 2026 incompleto: mensile Eurostat fino a maggio 2026.
8. Assaeroporti non usato (condizioni d'uso).
9. Nessuna informazione sull'origine dei passeggeri (milanesi, turisti, pendolari).

## 5. Numeri principali

- Linate: 13,6 milioni (1998), 6,7 (1999, apertura Malpensa 2000 il 5/10/1998), 6,0 (2000), 8-10 (2004-2018), 9,2 (2018), 6,5 (2019, -29,1%), 2,3 (2020), 10,6 (2024), 11,1 (2025). Quota internazionali 27,4% (2004) -> 57,1% (2025): nazionali 6,50 -> 4,77 milioni, internazionali 2,45 -> 6,35.
- Malpensa: 16,9 (1999), 20,5 (2000), 23,6 (2007), 17,3 (2009), 24,1 (2018), 28,7 (2019, +18,9%), 7,2 (2020), 28,7 (2024), 31,2 (2025, +8,7%).
- Bergamo: 1,17 (2000), 7,7 (2010), 13,8 (2019), 3,8 (2020), 17,35 (2024), 16,9 (2025, -2,4%). Supera Linate dal 2015.
- Tre aeroporti: 46,3 milioni (2018), 49,1 (2019, +6,0%), 13,3 (2020, -72,9%), 59,3 (2025). Quota sull'Italia (somma aeroporti): 29,3% (2004), 25,5% (2019), 25,9% (2025). Italia: 192,6 milioni (2019), 52,9 (2020, -72,6%), 229,1 (2025).
- Chiusura di Linate agosto-ottobre: Linate 2,41 milioni (2018) -> 125.842 (2019); i tre aeroporti insieme 13,06 -> 13,41 milioni (+2,7%).
- Merci: Malpensa 763.090 t nel 2025, 62% dell'Italia (1,24 milioni di t); Linate 63.115 t (1998) -> 1.747 (2025); Bergamo 127.953 (2003) -> 24.467 (2025).
- Passeggeri per volo (voli con passeggeri Eurostat): Malpensa 90 (2004) -> 160 (2025), Bergamo 103 -> 170, Linate 97 -> 105.
- Classifica 2025: Fiumicino 50,9; Malpensa 31,2 (2o); Bergamo 16,9 (3o); Linate 11,1 (8o).

## 6. La "sorpresa"

Quando un aeroporto chiude i passeggeri si spostano: nel 2019 Linate -29% ma i tre aeroporti +6%; tra agosto e ottobre 2019 Linate quasi azzerato (125.842 contro 2,41 milioni) e i tre aeroporti insieme +2,7%. Inoltre Linate e' passato dal 27% al 57% di passeggeri internazionali (2004-2025) e Bergamo e' cresciuto 15 volte dal 2000.

## 7. Da fare / dubbi per il coordinatore

- Se si vuole Assaeroporti (aviazione generale, mesi fino a settembre 2026 e la serie mensile dal 2000): chiedere il consenso scritto; altrimenti la pagina resta su Eurostat + ENAC.
- Eurostat 1999-2000: nessun dato; ENAC ha il 2000 nell'Annuario 2003 (usato). Il rapporto ENAC "Annuario 2000" si riferisce al 1999.
- Serie ENAC completa 2004-2023 dei movimenti: non estratta (formati diversi per anno); estrarre da `raw/enac` solo se serve il numero esatto di movimenti per anno.
- Possibile estensione: divisione per compagnia/low cost (ENAC 2025 pp. 125-129) e per destinazione (ENAC tavole OD), non fatta.
- Il testo sulla chiusura di Linate cita solo stampa; un documento SEA/ENAC darebbe la fonte primaria.
