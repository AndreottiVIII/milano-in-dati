# Come votano i quartieri ricchi e poveri: voto per sezione contro reddito del CAP (fase 1, analisi)

Data: 2026-11-01. Nessuna pagina, nessun git, JOURNAL.md e docs/ non toccati. Per il JOURNAL: questo file va unito a mano dal coordinatore.
Dove non è scritto altro, "file X, campo Y" si riferisce ai file in `voto-reddito\out\`.

## 1. Domanda e come leggere i risultati

Come cambia il voto (e l'affluenza) passando dai CAP con redditi più bassi a quelli con redditi più alti, e come è cambiato dal 2016 al 2026.
**Avvertenza ecologica (da ripetere in pagina):** di nessuno si conosce il voto individuale. Si sa il voto di una sezione (circa 800 elettori) e il reddito medio del CAP in cui stanno i suoi civici. Una sezione "ricca" non vota in un modo perché ha il reddito alto: dentro lo stesso CAP vivono persone con redditi diversi, e il reddito del CAP è quello dei contribuenti con domicilio fiscale lì, non degli elettori. Sono confronti tra zone, non cause e non comportamenti di persone.

## 2. Fonti e legami (ogni passaggio ha il suo script)

| Cosa | File | Campi |
|---|---|---|
| Voti e affluenza per sezione, 2016-2026 | `elezioni\pulito\risultati_sezione.csv`, `voti_sezione.csv`, `elezioni.csv` (portale open data del Comune di Milano, CC BY) | `elettori`, `votanti`, `si`, `no`, `lista`, `voti` |
| Lista -> famiglia politica | `elezioni\famiglie_partiti.csv` (stessa regola di `elezioni\scripts\16_aggrega.py`, con intervalli di anni) | `lista`, `famiglia`, `anno_da`, `anno_a` |
| Sezione -> CAP e NIL | `elezioni\raw\ds939-...\ds939_Stradario_referendum_2020.csv` (una riga per civico) | `SEZIONE`, `CAP`, `ID_NIL` |
| Reddito per CAP | `redditi\pulito\cap_milano_media_euro2025.csv`, `cap_milano_media_nominale.csv`, `cap_milano_contribuenti.csv` (da `mef_cap_2011_2024.csv`, MEF Dipartimento delle Finanze, CC BY 3.0) | reddito complessivo medio per contribuente, 38 CAP |
| Popolazione per NIL | `popolazione\pulito\cittadinanze_nil_indicatori.csv` (`quota_stranieri`), `eta_nil_anno_indicatori.csv` (`q_65p`), anno 2023. **Provvisori:** il filone popolazione è ancora in costruzione | |
| NIL con dati fragili | `elezioni\pulito\nil_controllo_popolazione.csv` (`fragile`, `rapporto` elettori/adulti) | |

**Sezione -> CAP: il CAP è ufficiale, non stimato.** Nel filone 9 il CAP dei civici è stimato dal punto più vicino con CAP noto. Qui no: lo stradario ds939 dà a ogni civico la sua sezione **e** il suo CAP (campo `CAP`, tre cifre: 121 = 20121). Non c'è nessun file con i confini delle sezioni (NOTE.md di `elezioni`, punto 4), e non serve: si va per civici.
- 51.323 civici in ds939; 81 esclusi perché hanno CAP 100 (cioè 20100, generico, 80 civici) o 54 (1 civico) e il MEF non ha reddito per quel CAP (`out\controllo_cap_filone9.json`, campo `civici_senza_reddito_cap100_cap54`).
- 1.238 sezioni col legame (`out\sezione_cap.csv`). Una sezione può avere civici di più CAP: 871 sezioni su 1 CAP, 318 su 2, 41 su 3, 8 su 4; `peso` = quota dei civici della sezione in quel CAP. Per 1.042 sezioni su 1.238 (84%) il CAP prevalente ha almeno l'80% dei civici (`out\sezione_cap_qualita.csv`, campo `peso_max`).
- Controllo con il filone 9: sui 46.255 civici confrontabili (via + numero, `citta-15-minuti\out\civici_tempi.csv`, campo `CAP`), il CAP ufficiale di ds939 coincide con quello stimato nel 96,68% dei casi (`out\controllo_cap_filone9.json`, campo `stesso_cap_pct`). Cioè la stima del filone 9 era buona (il filone dichiarava 96,6%).
- Il legame è quello del 2020. Per le altre elezioni vale quanto già verificato per i NIL: stessa sezione nel 98,8-100% dei civici per gli stradari 2016-2026 (`elezioni\pulito\sezione_nil_stabilita.csv`). Le sezioni senza legame (10-23 per elezione, 11 speciali 9001-9011 nel 2025) valgono lo 0,03-2,7% dei votanti: **copertura 99,9% dei votanti per quasi tutte le elezioni, 97,3% per i 5 referendum 2025** (`gradiente_per_voce.csv`, campo `copertura_votanti_pct`, minimo 97,26, massimo 99,97).

**Reddito.** Misura principale: reddito complessivo medio per contribuente del CAP, media dei 4 anni d'imposta 2019-2022, in euro 2025 (`cap_reddito.csv`, campo `reddito_2019_22_euro2025`): da 21.507 (20157) a 113.459 euro (20121; 20145: 93.691, 20123: 87.894, 20122: 71.451). Scelta: per il 2023-24 il MEF ha cambiato l'assegnazione dei contribuenti di alcuni CAP (`redditi\NOTE.md`, trappola 5) e per prima del 2019 non c'è dato; la media 2019-22 è l'unica finestra stabile. L'ordine dei CAP cambia pochissimo con l'anno: correlazione di Spearman tra la misura principale e il 2015 = 0,990, e il 2024 = 0,991 (`cap_reddito.csv`). Il reddito di una sezione = media dei redditi dei suoi CAP pesata per i civici (`sezioni_reddito_decile.csv`, campo `inc`).

**Decili.** Tagli fissi sul reddito di sezione, pesati per gli elettori delle Comunali 2021 (`decili_definizione.csv`); stessi tagli per tutte le elezioni. Ogni decile ha 108-137 sezioni, il 9-11% degli elettori, da 7 a 19 CAP prevalenti. D1: 21,5-27,5 mila euro; D10: 64,5-113,5 mila. **D10 è fatto di 4 CAP**: 20123 (33% degli elettori del decile), 20122 (24%), 20145 (19%), 20121 (19%) (`composizione_decili_per_cap.csv`). D9: 20129, 20149, 20124, 20144.

**Elezioni usate (28):** referendum 2016 (2), 2017, 2020, 2022 (5), 2025 (5), 2026; Comunali Consiglio e Sindaco 2016 e 2021, ballottaggio 2016; Politiche Camera e Senato 2018 e 2022; Regionali 2018 e 2023; Europee 2019 e 2024. **Le Comunali 2026 non esistono** (si voterà nel 2027): l'ultimo voto è il referendum del 22-23 marzo 2026. Politiche 2018 e 2022 e Regionali 2023 sono "dati ufficiosi" nel portale (trappola 15 di `elezioni\NOTE.md`). Le Municipali 2016 e 2021 non sono usate (stessi elettori delle Comunali).

**Famiglie e blocchi.** Famiglie come nel sito `docs\elezioni` (Sinistra, Centrosinistra, M5S, Centro, Centrodestra, Lega, Destra, Altri; `famiglie_partiti.csv`, ancora con 69 righe "da rivedere"). Blocchi usati qui per semplicità, **non sono coalizioni elettorali**: Sx = Sinistra + Centrosinistra; Dx = Centrodestra + Lega + Destra; Sx+Centro = Sx + Centro. La famiglia Centro cambia contenuto: nel 2018 è +Europa (alleata del PD), nel 2022 è Azione-Italia Viva + +Europa, nel 2024 Azione + Stati Uniti d'Europa. Per ogni lista con almeno il 2,5% (3% per i candidati sindaco) c'è anche la riga della singola lista in `gradiente_per_voce.csv` (campo `voce`, `tipo` = lista).

## 3. Metodo (in due livelli, per non fidarsi di uno solo)

1. **Sezione** (`20_analisi.py`): quota di una voce per decile di reddito di sezione; "gap" = quota in D10 meno quota in D1 (punti percentuali). Incertezza: bootstrap a grappoli (2.000 ripetizioni, seme fisso, ricampionando i 38 CAP interi, ogni sezione al suo CAP prevalente), intervallo 2,5-97,5 percentile.
2. **CAP** (38 punti): voti e elettori delle sezioni divisi tra i CAP in proporzione ai civici (come i NIL nel filone elezioni); quota per CAP; correlazione di Spearman con il reddito e pendenza (punti per +10.000 euro, minimi quadrati pesati con i voti), stesso bootstrap sui CAP.
3. **Affluenza** = votanti / elettori, **solo sulle sezioni regolari** (elettori > 0 e votanti <= elettori; tra le sezioni con legame, 12 sono escluse nel 2021 e 5 di queste sono in D10, `30_diagnostiche.py`). Il denominatore è il registro elettorale, non i residenti.
4. **Robustezza** (`robustezza.csv`, per 8 voci chiave): reddito dell'anno più vicino all'elezione, reddito 2024, reddito 2015, senza i 3 CAP instabili (20121, 20122, 20145), solo sezioni con CAP prevalente >= 80%, livello NIL (reddito del NIL = media dei CAP pesata per civici, `nil_reddito.csv`) con e senza controllo per quota di stranieri e di over 65.

## 4. Numeri principali

### 4.1 Il gradiente di reddito nel tempo (Comunali = Sindaco primo turno; Camera; Regionali/Europee: voti di lista)
Quota nel decile più povero (D1), nel penultimo (D9), nel più ricco (D10); gap D10-D1 con intervallo di confidenza 95%; Spearman sui 38 CAP (`sintesi_nel_tempo.csv`, `gradiente_per_voce.csv`).

| Elezione | Voce | Città | D1 | D9 | D10 | Gap D10-D1 (IC 95%) | Spearman CAP |
|---|---|---|---|---|---|---|---|
| Comunali 2016 | Sala (Centrosinistra) | 41,7 | 36,3 | 45,8 | 45,8 | +9,5 (+7,9/+11,3) | 0,89 |
| Politiche 2018 | PD e affini | 28,0 | 23,6 | 31,7 | 33,8 | +10,3 (+8,8/+12,3) | 0,95 |
| Europee 2019 | PD | 36,0 | 28,3 | 42,1 | 41,8 | +13,5 (+11,0/+16,3) | 0,89 |
| Comunali 2021 | Sala | 57,7 | 49,2 | 63,9 | 63,9 | +14,7 (+11,4/+17,7) | 0,88 |
| Politiche 2022 | PD e affini | 26,0 | 23,9 | 26,7 | 23,0 | -0,9 (-2,3/+0,5) | 0,23 |
| Regionali 2023 | PD e affini | 35,2 | 32,5 | 36,5 | 30,6 | -1,9 (-3,8/+0,5) | 0,22 |
| Europee 2024 | PD | 31,4 | 28,7 | 32,7 | 27,8 | -0,9 (-2,9/+1,2) | 0,29 |
| Politiche 2018 | Centro (+Europa) | 8,0 | 3,9 | 11,9 | 12,9 | +9,0 (+7,9/+10,1) | 0,91 |
| Politiche 2022 | Centro (Azione-IV, +Europa) | 21,2 | 13,1 | 28,7 | 36,7 | +23,6 (+21,4/+25,4) | 0,94 |
| Regionali 2023 | Centro (Moratti, Azione-IV) | 13,8 | 8,8 | 18,4 | 26,4 | +17,6 (+16,0/+18,9) | 0,92 |
| Europee 2024 | Centro (Azione, SUE) | 12,8 | 8,0 | 17,1 | 22,0 | +14,0 (+12,7/+15,2) | 0,93 |
| Politiche 2022 | Sx+Centro | 55,1 | 44,3 | 62,3 | 64,3 | +20,0 (+16,0/+23,9) | 0,90 |
| Europee 2024 | Sx+Centro | 57,2 | 50,1 | 61,1 | 57,9 | +7,8 (+3,7/+11,6) | 0,65 |
| Europee 2019 | Dx | 43,0 | 49,6 | 39,2 | 40,7 | -8,9 (-11,9/-6,3) | -0,78 |
| Comunali 2021 | Dx (Bernardo) | 32,0 | 38,3 | 28,2 | 29,6 | -8,7 (-11,1/-5,9) | -0,77 |
| Politiche 2022 | Dx | 34,0 | 40,9 | 30,5 | 30,8 | -10,2 (-13,1/-6,9) | -0,76 |
| Europee 2024 | Dx | 36,7 | 41,2 | 35,0 | 39,5 | -1,7 (-5,0/+1,7) | -0,35 |
| Politiche 2018 | M5S | 18,2 | 24,3 | 12,8 | 8,4 | -15,9 (-17,5/-13,8) | -0,93 |
| Politiche 2022 | M5S | 7,7 | 10,9 | 4,7 | 3,1 | -7,8 (-8,6/-7,0) | -0,94 |
| Europee 2024 | M5S | 5,3 | 7,7 | 3,3 | 2,1 | -5,5 (-6,5/-4,8) | -0,93 |

Liste singole (stesso file): Lega Europee 2019 D1 35,2 -> D10 19,8 (-15,3; -18,1/-13,0); Lega Politiche 2022 9,4 -> 3,4 (-6,0). Fratelli d'Italia Politiche 2022 23,8 -> 19,5 (-4,2; -5,9/-1,8), Europee 2024 25,0 -> 22,8 (-2,2; -4,2/+0,5); nel 2018 4,1 -> 4,7 (piatta). Forza Italia Politiche 2018 14,6 -> 21,2 (+6,6), Europee 2024 8,2 -> 12,4 (+4,2; +3,0/+5,3). Azione-Italia Viva Politiche 2022 8,8 -> 31,4 (+22,5; +20,6/+24,1). Alleanza Verdi e Sinistra Europee 2024 10,8 -> 6,4 (-4,4; -5,7/-3,4).

### 4.2 Affluenza per reddito
| Elezione | D1 | D9 | D10 | Gap D10-D1 (IC 95%) |
|---|---|---|---|---|
| Comunali 2016 | 54,8 | 54,1 | 50,8 | -4,0 (-6,8/-0,4) |
| Politiche 2018 | 70,4 | 75,8 | 76,2 | +5,8 (+3,1/+9,3) |
| Europee 2019 | 55,5 | 61,2 | 59,8 | +4,3 (+0,6/+8,0) |
| Comunali 2021 | 45,3 | 49,1 | 45,3 | -0,1 (-4,1/+3,8) |
| Politiche 2022 | 62,7 | 73,3 | 74,0 | +11,3 (+7,5/+15,9) |
| Regionali 2023 | 39,8 | 43,8 | 40,9 | +1,1 (-2,6/+5,2) |
| Europee 2024 | 46,3 | 54,1 | 51,4 | +5,1 (+0,4/+10,0) |
| Referendum 2025 (lavoro, quesito 1) | 34,2 | 35,5 | 29,0 | -5,2 (-8,7/-0,9) |
| Referendum 2026 (giustizia) | 58,8 | 69,8 | 69,9 | +11,2 (+6,8/+17,1) |

Nelle Politiche l'affluenza sale con il reddito (D1 62,7% contro D10 74,0% nel 2022; Spearman 0,90). Nelle amministrative il quadro è piatto o rovesciato (Comunali 2016: più alta nel decile povero). **Nelle elezioni "minori" l'ultimo decile vota meno del penultimo**: D10 meno D9 = -3,3 punti (Comunali 2016), -3,8 (Comunali 2021), -4,3 (Regionali 2018), -2,9 (Regionali 2023), -1,5 (Europee 2019), -2,7 (Europee 2024), -6,5 (Referendum 2025, primo quesito), -5,3 (trivellazioni 2016); nelle Politiche 2018 e 2022 e nel referendum 2016-12 e 2026 D10 e D9 sono pari (differenza tra -0,2 e +0,8; `decili_per_voce.csv`, voce `AFFLUENZA`). Vedi i limiti dei dati (registro elettorale).

### 4.3 Referendum (quota di Sì, D1 -> D10; direzione del Sì indicata)
Costituzionale 2016 (Sì = riforma Renzi-Boschi): 43,1 -> 65,4 (+22,3; +19,8/+25,4; Spearman 0,97). Taglio dei parlamentari 2020 (Sì = taglio): 66,8 -> 43,4 (-23,4; -26,1/-20,4; -0,89). Lavoro 2025 (Sì = abrogare), quattro quesiti: licenziamenti 89,3 -> 73,4 (-15,9); indennità 88,0 -> 72,3 (-15,7); contratti a termine 89,6 -> 75,6 (-14,0); sicurezza appalti 88,3 -> 79,1 (-9,2). Cittadinanza 2025 (Sì = cinque anni invece di dieci): 67,5 -> 79,8 (+12,3; +9,4/+14,8). Giustizia 2022: separazione delle funzioni 76,6 -> 84,6 (+8,1), consigli giudiziari 74,7 -> 84,8 (+10,1), incandidabilità 56,0 -> 57,5 (+1,4; -0,6/+3,5). Giustizia 2026 (Sì = separazione delle carriere): 42,3 -> 52,6 (+10,4; +7,1/+13,6). Referendum senza gradiente: trivellazioni 2016 (-0,1; -2,0/+1,5), autonomia Lombardia 2017 (+0,2; -0,4/+0,9). Fonte: `gradiente_per_voce.csv`, voce `Si`.

### 4.4 Quanto spiega il reddito (sezione per sezione)
Quota della varianza tra sezioni che sta tra CAP (eta quadro) e quota spiegata da una retta sul reddito (R quadro), pesi = voti (`robustezza.csv`, campi `eta2_tra_cap`, `r2_reddito`): Sx Comunali 2021 0,50 / 0,24; Sx Politiche 2022 0,32 / 0,05; Sx Europee 2024 0,35 / 0,08; Centro Politiche 2022 0,71 / 0,65; M5S Politiche 2022 0,52 / 0,43; Dx Politiche 2022 0,46 / 0,16; Dx Comunali 2016 0,19 / 0,00; affluenza Politiche 2022 0,29 / 0,17, Comunali 2021 0,10 / 0,00. **Il reddito del CAP descrive bene Centro e M5S, poco la distinzione destra/sinistra, quasi niente l'affluenza nelle amministrative.** Anche dove il legame tra CAP è forte (Spearman 0,9), dentro lo stesso CAP le sezioni variano molto: a livello di sezione la correlazione con il reddito è più bassa (0,15-0,64 per le voci chiave, es. Sx Comunali 2021 0,64, Sx Politiche 2018 0,55; campo `spearman`, variante "sezioni con CAP prevalente >= 80%").

### 4.5 Robustezza (`robustezza.csv`)
- Anno del reddito e variante a 36 CAP: nei 115 confronti (elezione x voce, livello CAP) l'ampiezza del Spearman tra le varianti ha mediana 0,05. I tre casi più sensibili (0,33-0,35) sono tutti il Centrosinistra nel 2022-2024: Spearman 0,22-0,30 con le misure di reddito alternative, **0,55-0,62 togliendo 20121, 20122 e 20145** (pendenza +0,3 / +0,5 punti per +10.000 euro). Quindi: dal 2022 il PD sale con il reddito molto meno che nel 2016-2021 (pendenza +2,2 nelle Comunali 2021), e quel poco che resta dipende da come si trattano i 3 CAP più ricchi. Per tutte le altre voci il segno e l'ordine non cambiano.
- **La pendenza in punti per +10.000 euro è fragile, il Spearman e i decili no.** Togliendo 20121, 20122 e 20145 la pendenza delle Comunali 2021 passa da +2,1 a +3,2 punti, quella del Centro nel 2022 da +3,5 a +4,0, ma il Spearman resta 0,87 e 0,92. Per questo la tabella principale usa decili e Spearman.
- Livello NIL (70-74 quartieri con più di 1.000 votanti): stesso segno quasi ovunque (Sx Comunali 2021 Spearman 0,83; Centro 2022 pendenza +3,7). **Controllando per quota di stranieri e di over 65 il legame con il reddito si riduce:** Sx Comunali 2021 da +2,3 a +1,4 punti per +10.000 euro (IC 0,9/2,7); Sx Politiche 2018 da +1,3 a +0,7 (0,4/1,3). I tre indicatori sono intrecciati (Spearman reddito-quota stranieri -0,50, `correlazioni_nil_reddito_stranieri_eta.csv`): il reddito non si separa dalla composizione dei residenti. M5S e Centro tengono il segno anche con i controlli (M5S 2018: -2,5 -> -2,2).
- Le stime a livello di CAP usano 38 punti; gli intervalli sono larghi per le pendenze (es. Comunali 2021, Sx: +2,0 punti, IC +1,4/+3,3).

## 5. La cosa più sorprendente

**La distinzione tra quartieri ricchi e poveri non è sparita dal 2022: ha cambiato partito.** Fino al 2021 il Centrosinistra (PD e affini) prendeva in media 10-15 punti in più nei CAP ricchi che nei poveri (2016 +9,5; 2018 +10,3; 2019 +13,5; 2021 +14,7). Dal 2022 quel divario scompare: -0,9 (Politiche 2022), -1,9 (Regionali 2023), -0,9 (Europee 2024), con intervalli che comprendono lo zero. Ma il divario non si è chiuso, si è spostato: nelle stesse elezioni le liste di Centro (Azione-Italia Viva, Moratti, Stati Uniti d'Europa) passano dal 13% al 37% (Politiche 2022), dal 9% al 26% (Regionali 2023), dall'8% al 22% (Europee 2024) tra il decile più povero e il più ricco. Sommando Sinistra, Centrosinistra e Centro, il divario D10-D1 è +17,4 (Politiche 2018), +17,5 (Europee 2019), +20,0 (Politiche 2022), +12,9 (Regionali 2023), +7,8 (Europee 2024, Spearman 0,65): resta alto fino al 2023 e scende nel 2024. Il PD nelle Politiche 2022 prende il 24% nel decile povero e il 23% nel più ricco. **Cautela:** tolti i 3 CAP più ricchi il PD sale ancora debolmente (Spearman 0,55-0,62, vedi 4.5): la frase giusta è "il PD non ha più la forte salita con il reddito del 2016-2021", non "il PD non ha alcun legame col reddito".
Due contorni, entrambi nei dati: (a) il M5S ha lo stesso segno in tutte le 11 elezioni con una lista o un candidato M5S (Spearman tra -0,90 e -0,94, `gradiente_per_voce.csv`) mentre scende dal 18% (Politiche 2018) a meno del 5%: è il gradiente più stabile; (b) il decile più ricco non è il "più a sinistra": in D10 il PD cala (Europee 2024: 32,7% in D9, 27,8% in D10) e la destra risale (Dx 2024: 35,0% in D9, 39,5% in D10, Forza Italia +4,2 punti rispetto a D1). Ma il decile è fatto di soli 4 CAP centrali (20121, 20122, 20123, 20145), quindi può essere un effetto di quelle zone più che del reddito.

## 6. Limiti dei dati (per la pagina)

1. **Ecologico.** Sono confronti tra zone. Nessuna frase del tipo "i ricchi votano X".
2. **Il reddito è dei contribuenti con domicilio fiscale nel CAP**, non degli elettori; copre chi presenta dichiarazione (a Milano 77 contribuenti ogni 100 residenti, `redditi\NOTE.md`, trappola 1). Gli stranieri e i giovani senza dichiarazione contano poco o niente nel reddito, e gli stranieri non votano.
3. **Solo 38 CAP.** Il decile più ricco è fatto di 4 CAP (20121, 20122, 20123, 20145); 20145 ha solo 13.855 contribuenti e 20121/20122 hanno cambi di assegnazione (`redditi\NOTE.md`, trappola 5). Il reddito di un singolo CAP non è affidabile come la media del gruppo.
4. **Legame fermo al 2020**, sezioni miste (16% delle sezioni ha meno dell'80% dei civici nel CAP prevalente; i voti sono divisi in proporzione ai civici, non agli elettori).
5. **Affluenza e registro elettorale.** Nel quinto più ricco dei NIL gli elettori sono 1,02 volte gli adulti residenti (mediana), negli altri quattro quinti 0,80-0,88 (`nil_rapporto_elettori_adulti_reddito.csv`, campo `rapporto`: elettori Comunali 2021 / adulti 2021 del filone citta-15-minuti; correlazione di Spearman con il reddito 0,55). Nei NIL ricchi il registro sembra più grande della popolazione che vive lì: l'affluenza dell'ultimo decile può essere più bassa per questo e non per un'astensione maggiore. È un'ipotesi coerente coi dati, non provata. Gli elettori dei NIL con reddito basso sono invece pochi rispetto agli adulti (gli stranieri non votano).
6. **Famiglie politiche e blocchi non sono coalizioni** (vedi sopra). Il Centro non è la stessa cosa nei tre anni. La tabella delle famiglie ha ancora 69 righe "da rivedere".
7. **Dati ufficiosi**: Politiche 2018 e 2022, Regionali 2023. Le Politiche 2018 e 2022 sono "liste nel collegio uninominale", cioè la lista scelta insieme al candidato: si usano come voto di lista (651.345 voti nel 2018, contro 694.898 votanti, `elezioni\pulito\voti_sezione.csv`).
8. **Politiche e referendum con un solo quesito per volta**: la "quota di Sì" dipende dal quesito, non c'è una direzione sinistra/destra fissa.
9. **Redditi non contemporanei**: reddito 2019-22 contro voti 2016-2026. L'ordine dei CAP è stabile (Spearman 0,99 tra le misure) ma i livelli no.
10. **Popolazione per NIL (stranieri, over 65, anno 2023)** viene da `popolazione\pulito`, filone ancora in costruzione: i controlli dei punti 4.5 e 6 vanno riconfermati quando sarà chiuso.

## 7. Cosa potrebbe mostrare una pagina

1. Un grafico a 10 barre (i decili) per elezione con un selettore di famiglia: Centrosinistra 2016-2021 in salita, 2022-2024 piatto con il calo in D10; Centro sempre in salita; M5S sempre in discesa. Ogni barra con l'intervallo.
2. Una striscia "il divario D10-D1 per elezione" per Centrosinistra, Centro, Destra, M5S, affluenza (tabella 4.1), con il punto di rottura 2021/2022.
3. Un dispersivo dei 38 CAP (reddito sull'asse x, quota sull'asse y) con le sezioni in grigio per far vedere quanto variano dentro lo stesso CAP; un tasto "togli i 3 CAP instabili".
4. I referendum a coppie: Sì costituzionale 2016 (+22 punti nei ricchi) contro Sì taglio parlamentari 2020 (-23), e il lavoro 2025.
5. Un riquadro fisso "limiti dei dati": ecologico, 38 CAP, decile ricco fatto di 4 CAP, registro elettorale.
6. Sempre vietato: parole che suggeriscono causa ("i ricchi votano", "voto di classe"), mappe di sezioni con colori che sembrano giudizi.

## 8. File prodotti (cartella `voto-reddito\`)

- `scripts\10_sezione_cap.py` (legami e redditi), `20_analisi.py` (gradienti, bootstrap, robustezza, ~2 minuti), `30_diagnostiche.py` (composizione dei decili, elettori su adulti), `31_sintesi.py` (tabella nel tempo). Ordine: 10 -> 20 -> 30 -> 31, tutti con `python -I -X utf8 <script> <milano-in-dati> <voto-reddito>` (31 vuole solo `<voto-reddito>`).
- `out\sezione_cap.csv`, `sezione_cap_qualita.csv`, `cap_reddito.csv`, `nil_reddito.csv`, `controllo_cap_filone9.json`, `sezioni_reddito_decile.csv`, `decili_definizione.csv`, `composizione_decili_per_cap.csv`, `gradiente_per_voce.csv` (276 righe), `decili_per_voce.csv`, `cap_per_voce.csv` (quote per CAP, per la pagina), `robustezza.csv`, `sintesi_nel_tempo.csv`, `correlazioni_nil_reddito_stranieri_eta.csv`, `nil_rapporto_elettori_adulti_reddito.csv`, `parametri.json`.
- Il grezzo non è copiato: si legge da `elezioni\` e `redditi\` in sola lettura.
