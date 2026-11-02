# Quanto sono vecchi i palazzi - fase 1 + pagina (2 novembre 2026)

Niente git. Pagina: `docs\palazzi\index.html` + `docs\palazzi\data\`. Programma: `scripts\pagina.py` (ripetibile). Nessuno scaricamento: tutto da file gia' sul disco (strand censimenti, costruzioni, prezzi-case).

## Dati e dove sono

| Cosa | Fonte (file) | Note |
|---|---|---|
| Edifici residenziali per epoca, per sezione 2011 | `censimenti\pulito\sezioni_2011.csv`, variabili E3 e E8-E16 (ISTAT) | E8..E16 sommano a E3 in tutte le 6.017 sezioni; totale 42.980 |
| Sezione -> NIL | `censimenti\pulito\raccordo_sezioni_2011.csv` | area massima; in 5.718 sezioni con edifici la purezza minima e' 0,68 |
| Abitazioni occupate per epoca, per municipio, 2011 | `censimenti\raw\comune_ckan\ds1456*` (Comune) | 604.044 + 468 in edifici non residenziali = 604.512, contro A2 delle sezioni 604.507 |
| Abitazioni occupate 1991 per epoca, per NIL | `sezioni_1991.csv` A11-A16 + `raccordo_sezioni_1991.csv` | A11..A16 = A2 = 576.777; usate solo come controllo e in scheda |
| Edifici 2001 (E9-E15) e 2021 (E3) | `sezioni_2001.csv`, `sezioni_2021.csv` | solo controlli sul totale citta'; il 2021 per sezione non ha l'epoca |
| Prezzi | `docs\prezzi-case\data\zone.geojson` + `zone_ultimo_semestre.csv` (OMI 2026/1, abitazioni civili, `compr_centro`) | sovrapposizione con le sezioni 2011 |
| Nuove abitazioni 2014-2024 | `costruzioni\pulito\nil_costruzioni.csv` | 25.005 su 26.174 assegnate a un NIL |
| Geometrie NIL | `docs\censimenti\data\nil.geojson` | semplificate (circa 4 m) |

## Risultati (tutti in `docs\palazzi\data\riepilogo.json`, con campo `origine`)

- Citta' 2011: edifici per epoca 12,4 / 23,5 / 27,7 / 19,9 / 8,6 / 2,9 / 2,0 / 1,5 / 1,5 % (prima 1919 ... dopo 2005); abitazioni 8,5 / 16,0 / 25,2 / 28,4 / 11,4 / 4,3 / 2,4 / 2,0 / 1,7 %.
- **Sorpresa**: 53,6% delle abitazioni occupate e' in palazzi del 1946-1970 (25 anni); 89,5% e' di prima del 1981; dopo il 1990 solo 6,2%. Il 1961-70 e' il 19,9% degli edifici ma il 28,4% delle abitazioni.
- NIL piu' antichi (>= 200 edifici): Magenta-S.Vittore 67,7% prima del 1946, Buenos Aires-Porta Venezia 66,9%, XXII Marzo 61,7%. Piu' recenti: Barona 32,9% dopo il 1980, Rogoredo-Santa Giulia 30,2%, Gratosoglio 29,2%. Boom 1946-70: Lorenteggio 83,2%, Bande Nere 82,2%, Taliedo 79,4%.
- Prezzi (72 NIL con >= 100 edifici e prezzo >= 80% coperto): Spearman quota prima del 1946 vs prezzo +0,59 (IC95 +0,40/+0,75); dopo il 1980 -0,63; 1946-70 -0,28. Confronto, non causa (centralita').
- Controllo: Spearman edifici 2011 prima del 1946 contro abitazioni 1991 prima del 1946: +0,76 (69 NIL).
- Prova di sensibilita' (ripartizione per quote di area): differenza massima 0,3 punti, nessun NIL cambia epoca dominante.

## Scelte

- Soglie: quote per NIL colorate solo con >= 100 edifici (72 NIL); classifiche con >= 200 (62 NIL).
- "Palazzo" = edificio ad uso residenziale ISTAT (anche villetta: 21% ha 1-2 interni). Interni != abitazioni (includono negozi e uffici).
- Prezzo del NIL = media dei prezzi OMI delle zone sovrapposte alla sezione (pesata per area), poi media delle sezioni pesata sulle abitazioni occupate. 4 NIL con copertura < 80% (Chiaravalle, Quintosole, Ronchetto delle Rane senza zone; Parco delle Abbazie 40%) esclusi dal confronto.
- Classe energetica: nessun dato in questo strand (CENED ds604/ds623 esistono sul portale ma non sono stati scaricati): la pagina lo dice.
- DBT (costruzioni\): non ha l'anno di costruzione, quindi non misura l'eta'; non usato per le epoche (detto nei limiti).

## Comando

```
python -I -X utf8 palazzi\scripts\pagina.py C:\Users\davide\Desktop\ClaudeTower\milano-in-dati C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\docs
```
Il programma si ferma (exit 1) se un totale non torna.

## Aperto

- Voce nel menu (`docs\menu.js`), nell'elenco di `docs\index.html` e nel `JOURNAL.md`: da fare al coordinatore (non toccati).
- Epoca dichiarata nel censimento, non verificata con altre fonti. Gli edifici costruiti dopo il 2011 non hanno dati per NIL sulla loro epoca (solo abitazioni dei permessi).
- Provato: server locale porta 8863 (fermato), nessun errore in console, nessuno scorrimento orizzontale a 375 px (la scheda del quartiere va in colonna sotto i 600 px).
