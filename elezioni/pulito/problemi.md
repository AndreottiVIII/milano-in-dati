# Problemi dei dati e correzioni (fase 2)

Ogni voce e una "trappola dei dati". Le righe marcate (auto) sono prodotte dallo script `scripts\13_pulizia.py` mentre pulisce; le altre sono note scritte a mano dopo il controllo. I dataset sono indicati con il numero `dsNNNN` del portale del Comune di Milano.

## Cosa contiene il dataset pulito

- `elezioni.csv`: una riga per consultazione (157: 138 usate nel sito + 19 tenute ma non usate perche senza famiglie, vedi colonna `nota_sito`). Campi: id, gruppo, data corretta, sistema territoriale, dataset di origine.
- `risultati_sezione.csv`: una riga per sezione e consultazione (elettori, votanti, validi, non validi, Si/No per i referendum, territorio, flag).
- `voti_sezione.csv`: una riga per sezione, consultazione e lista (o candidato, o Si/No). Il territorio e quello del file risultati (controllo: coincide con quello del file voti in tutte le righe).

## 1. Date sbagliate o non-date

**Ballottaggi (auto).** Il campo `Sessione` porta la data del primo turno. Date messe: 1993-06-20, 1997-05-11, 2011-05-29, 2016-06-19, e 2009-06-21 per il ballottaggio provinciale. Le date 2011 e 2016 sono confermate dai titoli dei dataset di sedi (ds1111: "Ballottaggio del 29-30/5/2011", ds1117: "19/6/2016"); **1993, 1997 e 2009 vengono dal calendario elettorale e non da un campo del portale: da verificare** (non ho trovato nei dati una conferma).

- (auto) ds1369: campo Sessione = '114' non coincide con la data nel titolo (2016-04-17): uso quella del titolo
- (auto) ds1371: campo Sessione = '117' non coincide con la data nel titolo (2017-10-22): uso quella del titolo
- (auto) ds2931: campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
- (auto) ds2932: campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
- (auto) ds2933: campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
- (auto) ds2934: campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo

Nota: il campo `Sessione` del 2021 e `03/10/2021` (primo giorno), mentre il campo `date_start` dell'inventario di fase 1 dava 2021-10-04. Uso `Sessione`. Per le votazioni su due giorni (referendum 2020, 2025, 2026) la data e il primo giorno.

## 2. Territorio: tre sistemi con lo stesso nome di colonna

- Fino al 1997 la colonna e `Circoscrizione` (1-20). Dal 1999 `Zona` (1-9). Dal 2016 `Municipio` (1-9). Il numero 5 del 1997 non e il numero 5 del 1999.
- (auto) Nei referendum 1985-1997 la colonna si chiama `Zona` ma contiene valori fino a 20: sono le circoscrizioni (26 file). Nel pulito il campo `sistema_territorio` dice quale dei tre sistemi vale.
- (auto) Nei 5 referendum del 1981 (ds1372-ds1376) la colonna `Zona` e vuota. Ho ripreso la circoscrizione dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); campo `territorio_derivato = 1`. **2 sezioni su 2.162 non si ritrovano** (restano senza territorio, contano solo nel totale della citta).
- Le 9 zone 1999-2011 hanno gli stessi numeri dei municipi 2016 (2011 -> 2016: stesso numero in 1.245 sezioni su 1.245) e anche gli stessi confini: le superfici di ds153 (9 zone) e ds379 (municipi) coincidono entro lo 0,005% (`pulito\confini_verifiche.json`).
- Le 20 ex zone di decentramento (ds378, campo `ZONADEC20` 1-20) sono usate come confini delle circoscrizioni 1-20: **ipotesi** che il numero coincida (la numero 1 contiene il Duomo; la somma delle superfici e uguale a quella dei municipi). Non ho una tabella ufficiale di corrispondenza.

## 3. Numeri che non tornano

**Elettori a zero in tutto il file (auto).** dataset: ds1195, ds1196, ds1197, ds1198, ds1199, ds1200, ds1203, ds1204, ds1207.
Nel pulito il campo e vuoto (non zero), cosi l'affluenza risulta "non disponibile" invece di 0%.

**Votanti a zero o vuoto in tutto il file (auto).** dataset: ds1216, ds1225, ds1240, ds1241, ds1242, ds1248, ds1249.
Nel pulito il campo e vuoto (non zero), cosi l'affluenza risulta "non disponibile" invece di 0%.

Dove Votanti manca, Non validi e comunque 0, quindi non si puo ricostruire (Votanti = Validi + Non validi darebbe i soli validi): nel sito l'affluenza e "n.d." per Senato 1996, Senato 2001, Provinciali 2009, Circoscrizionali 2011.

**Votanti > Elettori o Elettori = 0 con Votanti > 0 (auto).** 3483 casi in 126 dataset (elenco nel log completo). Tenuti: sono probabilmente sezioni ospedaliere o speciali. Con la somma dei file la distorsione sull'affluenza di territorio e piccola, ma sulla singola sezione puo superare il 100%.

**Sezioni 9001-9011 (2025, auto).** Tenute, flag `sezione_speciale` nel pulito (5 file referendum 2025). Contano nei totali.

- (auto) municipali_consiglio_2021-10-03: 3 sezioni con somma voti di lista > Validi del file risultati (campo Validi non e la somma delle liste)
- (auto) municipali_presidente_2021-10-03: 1 sezioni con somma voti di lista > Validi del file risultati (campo Validi non e la somma delle liste)

## 4. Voti vuoti

- (auto) 8811 righe con voti vuoti: tolte
  Sono le righe dei file ds1139, ds1144, ds1145, ds1153, ds1154 (maggioritario 1994/1996/2001, Senato 1996/2001): una riga per ogni candidato o lista in ogni sezione, vuota dove il candidato non si presentava nel collegio della sezione. Vuoto = non applicabile, non zero: le ho tolte.

## 5. Nomi delle liste

- Troncati a 30 caratteri (es. `Partito Comunista dei Lavorato`, `FORZA ITALIA BERLUSCONI PER BE`), abbreviati in modo diverso da un anno all'altro (`PD`, `Part. Democratico`, `Partito Democratico`), a volte tutto maiuscolo (dal 2021 e Politiche 2022) o con refusi (`Popolo delle Liberta` nelle Comunali 2011, `Soc. Italianii`, `Io amo l'Iitalia`). Per questo la tabella delle famiglie parte dal nome cosi com'e nel dato.
- Nelle Comunali 2016 e 2021 molte liste hanno il nome del candidato sindaco dentro (`Per Parisi Forza Italia Berl.`, `PARTITO DEMOCRATICO BEPPE SALA`): ho usato queste parole per assegnare la famiglia.
- Il carattere accentato nei titoli dei dataset e gia rovinato sul portale (`Unit�`, `Indennit�`): nel sito ho corretto a mano i titoli dei quesiti.
- Le Comunali, i ballottaggi e i Municipali hanno il nome del candidato nel campo `Lista` quando il file e "Sindaco" o "Presidente".

## 6. Cosa tengo e cosa lascio fuori dal sito (ma resta nel pulito)

Nel sito: Consiglio comunale, Sindaco (primo turno), ballottaggio, Municipali (consiglio), Circoscrizionali 2011 (liste), Camera (proporzionale per 1994-2001; "liste nel collegio uninominale" per 2018 e 2022), Senato (liste), Europee, Regionali (liste provinciali o circoscrizionali), Provinciali 2009 (consiglio), tutti i referendum (Si/No).
Nel pulito ma non nel sito: Camera maggioritario 1994/1996/2001, candidati uninominali 2018/2022, Presidenti di municipio (59 nomi nel 2016), candidati presidente di regione (listini), Circoscrizionali 2011 coalizioni, Provinciali presidente e ballottaggio. Mancano di famiglia perche sono nomi di persone o coalizioni locali.
Nei Comunali (Consiglio) e Municipali (Consiglio) la quota per famiglia e calcolata sui soli voti alle liste: i voti dati solo al sindaco non entrano. Nelle Politiche 2018 e 2022 i voti "solo al candidato uninominale" non sono ripartiti tra le liste (il dato del Comune non lo fa).

## 7. Prima del 1979

Sul portale non ci sono dati di sezione prima del 1979. Vedi `NOTE_fase2.md` per quanto offre l'archivio storico del Ministero dell'Interno.

## 8. Elenco completo del log automatico

Codice | Dove | Cosa
---|---|---
ELETTORI_ZERO | ds1195 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1196 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1197 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1198 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1199 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1200 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
VOTANTI_SOPRA_ELETTORI | ds1201 | 15 sezioni con votanti > elettori e 24 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1202 | 13 sezioni con votanti > elettori e 24 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ELETTORI_ZERO | ds1203 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
ELETTORI_ZERO | ds1204 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
VOTANTI_SOPRA_ELETTORI | ds1205 | 10 sezioni con votanti > elettori e 23 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1206 | 7 sezioni con votanti > elettori e 23 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ELETTORI_ZERO | ds1207 | campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)
VOTANTI_SOPRA_ELETTORI | ds1208 | 7 sezioni con votanti > elettori e 22 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1209 | 7 sezioni con votanti > elettori e 22 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_BALLOTTAGGIO | ds1210 | Sessione = 06/06/1993 (primo turno), ballottaggio corretto a 1993-06-20 (calendario ufficiale)
VOTANTI_SOPRA_ELETTORI | ds1210 | 7 sezioni con votanti > elettori e 22 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1211 | 806 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1212 | 15 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1213 | 7 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1214 | 7 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1215 | 8 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_ZERO | ds1216 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_SOPRA_ELETTORI | ds1217 | 10 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1218 | 10 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1219 | 6 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1220 | 6 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_BALLOTTAGGIO | ds1221 | Sessione = 27/04/1997 (primo turno), ballottaggio corretto a 1997-05-11 (calendario ufficiale)
VOTANTI_SOPRA_ELETTORI | ds1221 | 7 sezioni con votanti > elettori e 21 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1222 | 6 sezioni con votanti > elettori e 22 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1223 | 6 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1224 | 6 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_ZERO | ds1225 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_SOPRA_ELETTORI | ds1226 | 5 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1227 | 5 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1228 | 7 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1229 | 7 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1230 | 11 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1231 | 12 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1232 | 12 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1233 | 10 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1234 | 11 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1235 | 11 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1236 | 11 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1237 | 11 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1238 | 11 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1239 | 12 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_ZERO | ds1240 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_ZERO | ds1241 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
DATA_BALLOTTAGGIO | ds1242 | Sessione = 06/06/2009 (primo turno), ballottaggio corretto a 2009-06-21 (calendario ufficiale)
VOTANTI_ZERO | ds1242 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_SOPRA_ELETTORI | ds1243 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1244 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1245 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1246 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_BALLOTTAGGIO | ds1247 | Sessione = 15/05/2011 (primo turno), ballottaggio corretto a 2011-05-29 (calendario ufficiale)
VOTANTI_SOPRA_ELETTORI | ds1247 | 12 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_ZERO | ds1248 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_ZERO | ds1249 | campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto
VOTANTI_SOPRA_ELETTORI | ds1250 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1251 | 14 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1252 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1253 | 13 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1254 | 10 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1255 | 8 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1256 | 8 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_BALLOTTAGGIO | ds1257 | Sessione = 05/06/2016 (primo turno), ballottaggio corretto a 2016-06-19 (calendario ufficiale)
VOTANTI_SOPRA_ELETTORI | ds1257 | 8 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1258 | 8 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1259 | 8 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1260 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1261 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1262 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1263 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1264 | 8 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1265 | 8 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1266 | 8 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_REFERENDUM | ds1369 | campo Sessione = '114' non coincide con la data nel titolo (2016-04-17): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds1369 | 4 sezioni con votanti > elettori e 4 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1370 | 8 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
DATA_REFERENDUM | ds1371 | campo Sessione = '117' non coincide con la data nel titolo (2017-10-22): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds1372 | 16 sezioni con votanti > elettori e 0 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1373 | 15 sezioni con votanti > elettori e 0 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1374 | 15 sezioni con votanti > elettori e 0 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1375 | 15 sezioni con votanti > elettori e 0 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1376 | 16 sezioni con votanti > elettori e 0 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1377 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1378 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1379 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1380 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1381 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1382 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1383 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1384 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1384 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1385 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1385 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1386 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1386 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1387 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1387 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1388 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1388 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1389 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1389 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1390 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1390 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1391 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1391 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1392 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1392 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1393 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1393 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1394 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1394 | 3 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1395 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1395 | 2 sezioni con votanti > elettori e 2 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
ZONA_E_CIRCOSCRIZIONE | ds1396 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1397 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1398 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1399 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1400 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1401 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
ZONA_E_CIRCOSCRIZIONE | ds1402 | colonna 'Zona' con valori fino a 20: sono le 20 circoscrizioni
VOTANTI_SOPRA_ELETTORI | ds1403 | 5 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1404 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1405 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1406 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1407 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1408 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1409 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1410 | 4 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1411 | 12 sezioni con votanti > elettori e 20 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1412 | 7 sezioni con votanti > elettori e 7 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1413 | 7 sezioni con votanti > elettori e 7 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1414 | 4 sezioni con votanti > elettori e 6 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1415 | 4 sezioni con votanti > elettori e 6 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1416 | 4 sezioni con votanti > elettori e 6 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1417 | 4 sezioni con votanti > elettori e 6 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1418 | 10 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1419 | 2 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1420 | 2 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1421 | 2 sezioni con votanti > elettori e 13 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1422 | 12 sezioni con votanti > elettori e 9 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1423 | 12 sezioni con votanti > elettori e 9 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1424 | 12 sezioni con votanti > elettori e 9 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1425 | 12 sezioni con votanti > elettori e 9 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1426 | 11 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1427 | 11 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1428 | 11 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1429 | 11 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1430 | 11 sezioni con votanti > elettori e 12 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1461 | 8 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1624 | 7 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1625 | 7 sezioni con votanti > elettori e 15 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1626 | 6 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1627 | 6 sezioni con votanti > elettori e 14 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1889 | 6 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1890 | 6 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1891 | 6 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1892 | 6 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1893 | 6 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1983 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1984 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1985 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds1986 | 7 sezioni con votanti > elettori e 16 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds2204 | 5 sezioni con votanti > elettori e 17 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds2205 | 5 sezioni con votanti > elettori e 17 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds2746 | 6 sezioni con votanti > elettori e 17 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
VOTANTI_SOPRA_ELETTORI | ds2930 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
SEZIONI_9001_9011 | ds2930 | 11 sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale
DATA_REFERENDUM | ds2931 | campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds2931 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
SEZIONI_9001_9011 | ds2931 | 11 sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale
DATA_REFERENDUM | ds2932 | campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds2932 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
SEZIONI_9001_9011 | ds2932 | 11 sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale
DATA_REFERENDUM | ds2933 | campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds2933 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
SEZIONI_9001_9011 | ds2933 | 11 sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale
DATA_REFERENDUM | ds2934 | campo Sessione = '2022-06-12' non coincide con la data nel titolo (2025-06-08): uso quella del titolo
VOTANTI_SOPRA_ELETTORI | ds2934 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
SEZIONI_9001_9011 | ds2934 | 11 sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale
VOTANTI_SOPRA_ELETTORI | ds2975 | 5 sezioni con votanti > elettori e 18 con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)
TERRITORIO_MANCANTE | referendum_1981-05-17_ds1372 | colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); 2 sezioni su 2162 non ritrovate
TERRITORIO_MANCANTE | referendum_1981-05-17_ds1373 | colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); 2 sezioni su 2162 non ritrovate
TERRITORIO_MANCANTE | referendum_1981-05-17_ds1374 | colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); 2 sezioni su 2162 non ritrovate
TERRITORIO_MANCANTE | referendum_1981-05-17_ds1375 | colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); 2 sezioni su 2162 non ritrovate
TERRITORIO_MANCANTE | referendum_1981-05-17_ds1376 | colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); 2 sezioni su 2162 non ritrovate
VOTI_SENZA_RISULTATI | voti | 20 righe voti di sezioni senza territorio nei risultati (le 2 sezioni dei referendum 1981 non ritrovate): restano senza territorio
LISTE_OLTRE_VALIDI | municipali_consiglio_2021-10-03 | 3 sezioni con somma voti di lista > Validi del file risultati (campo Validi non e la somma delle liste)
LISTE_OLTRE_VALIDI | municipali_presidente_2021-10-03 | 1 sezioni con somma voti di lista > Validi del file risultati (campo Validi non e la somma delle liste)
VOTI_VUOTI | voti | 8811 righe con voti vuoti: tolte
