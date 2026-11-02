# Esito del ricontrollo (da leggere prima del resto)

Il 2 novembre 2026 un secondo agente ha rifatto i calcoli da zero, senza leggere le conclusioni del primo. **Dove i due giudizi non coincidono, vale questa tabella**, non il testo più sotto. Script in `verifica/scripts/`. Numeri in `verifica/out/`, solo sul PC.

| Risultato | Primo studio | Dopo il ricontrollo | Motivo |
|---|---|---|---|
| Affluenza e mortalità | FORTE | **FORTE** | -0,68 per entrambi; 84 prove su 84 negative; nessun meccanismo lo crea. Tenendo pari anche i laureati va da -0,57 (Camera 2022, morti 2022-24) a -0,30 (media di otto elezioni, morti 2012-19); nello stesso CAP da -0,55 a -0,42. Nella fascia di reddito più bassa 1,11 contro 1,02 sommando le morti: 1,15 e 0,98 sono la media semplice dei quartieri |
| Reddito per CAP e quartieri | FORTE | **FORTE per 3 quartieri** | San Siro, Giambellino, Rogoredo-Santa Giulia. Il resto della lista cambia con i pesi |
| Pioggia e moto in Area C | FORTE | **FORTE, misura da -22% a -33%** | Dipende da come si definisce la giornata di pioggia. Auto da +1% a +3% |
| Olimpiadi e Wikipedia | FORTE | **FORTE, ma solo su poche voci** | Meazza e Unipol Dome fanno il 57% del salto, 10 voci il 94%; senza le prime 20 resta +7% |
| I municipi spiegano poco | FORTE | **FORTE** | Non battono gruppi casuali di quartieri confinanti (salvo l'affluenza alle Comunali 2021) |
| Eccesso di morti 2020 per quartiere | morto | **Confermato** | Città +28%; differenze tra quartieri non distinguibili dal caso (non si esclude una dispersione vera fino a circa 7 punti) |
| Voto e laureati | FORTE | **MEDIO** | Dentro lo stesso CAP i laureati ordinano il voto. "Il reddito non conta" non si può dire: alla stessa grana la differenza non è significativa (0 casi su 20). Il -0,79 contro +0,13 del primo studio è un coefficiente di regressione con altri controlli e senza la sua incertezza |
| Laureati del 1991 | FORTE | **MEDIO** | Regge, ma il 2001 dà quasi lo stesso e pesano quartieri ricostruiti: non è per forza memoria |
| Denunce da fine 2023 | MEDIO | **MEDIO, solo maltrattamenti** | Milano +35%, Italia +20%, con la salita da fine estate 2023. Lo stalking non regge |
| Airbnb e aree gioco | MEDIO | **MEDIO, correzione** | -0,50. **Il primo studio sbagliava sulla vicinanza**: l'area più vicina è più lontana (+0,47). Airbnb e distanza dal Duomo sono troppo legati (-0,87) per separarli |
| Beni confiscati e locali | MEDIO | **DEBOLE** | +0,51 sulle unità, ma contando solo i negozi +0,25 |
| Airbnb e bambini | morto | **Riaperto, solo un indizio** | Vedi sotto |
| Famiglie piccole e sinistra | MEDIO | **Morto** | Il salto del 2022 viene da come è classificato il Centro: con Sinistra+Centro -0,12 |
| Divario di lavoro e affluenza | MEDIO | **Morto** | -0,21 con laureati e stranieri; col divario 2011 il segno si inverte |
| Notti in albergo e Linate | MEDIO | **Morto come classifica** | Il file comprende anche l'extra-alberghiero, con una rottura ISTAT nel 2025; sui soli alberghi di provincia 0,36, 0,13 e 0,17, con pochi mesi |

**Airbnb e bambini: perché è riaperto.** Il primo studio guardava il 2014-2025 e la quota di bambini. Il secondo ha guardato il numero di bambini e ha separato i periodi. Dal 2019 al 2024 i bambini 0-14 calano del 12,8% nel terzo di quartieri con più Airbnb e del 5,4% in quello con meno (città -10,2%). A parità: -0,38 [-0,62; -0,09], senza i 5 più influenti -0,54, con stranieri e laureati -0,29. Nel 2014-2019 non c'è niente (-0,03). Gli altri residenti non seguono lo stesso andamento (-0,07). La quota di bambini non è significativa (-0,21 [-0,53; +0,10]), gli Airbnb sono una fotografia recente, e il periodo coincide con il Covid. Sono state provate più finestre, quindi va letto come indizio. Prova: `verifica/scripts/v13_airbnb_bambini_o_tutti.py`.

**Errori di codice trovati, non ancora corretti.** Nessun join sbagliato, nessun codice NIL disallineato, nessun segno invertito. Da correggere prima di riusare queste colonne:

- `01_tabella_nil.py:170-178`: le colonne `saldo_*_12_19` e `saldo_*_20_24` coprono in realtà il 2004-2019 e il 2022-2024.
- `01_tabella_nil.py:304-307`: `wiki_views_x_kmq` e `wiki_quota_estero` contano anche voci che non sono luoghi; tocca il segnale minore antenne e letture dall'estero.
- `robusta.py:134-135`: il valore assoluto nasconde i cambi di segno "togliendo un municipio" nelle coppie deboli.
- `07_approfondimenti_nil.py:218-222`: "Pta Romana" non abbina, persa 1 unità nei soli conteggi degli indirizzi dei beni confiscati.
- `07_approfondimenti_nil.py:41,123,177-178`: un quartiere senza voti diventerebbe 0 invece di vuoto; oggi nessun effetto.
- `07_approfondimenti_nil.py:241`: l'indice del primo studio contiene mortalità e affluenza, quindi è circolare contro di esse. Quello del ricontrollo li esclude: a parità di reddito con l'SMR 2022-24 dà -0,61, e il reddito a parità di indice -0,03.

---

# Milano in dati: cosa esce incrociando tutto

Lavoro esplorativo del 2 novembre 2026. Nessuna pagina, nessun dato nuovo scaricato, nessuna modifica a `docs/`, `JOURNAL.md` o altri filoni. Sono confronti tra zone e tra mesi, **non cause**. Tutti i numeri si rifanno con `scripts/lancia_tutto.py`.

## In breve

- Dei 12 risultati che restano, **6 sono forti e nuovi**. Il più interessante: **a Milano il voto segue il titolo di studio, non il reddito**, e l'affluenza è il miglior specchio della mortalità del quartiere.
- La grande maggioranza delle correlazioni trovate **è morta ai controlli**, e l'elenco dei morti conta quanto quello dei vivi: per esempio Airbnb non si vede nel calo dei bambini, il verde non si vede nella mortalità, la M4 non si vede a Linate.
- Sui mesi e sugli anni quasi non resta niente: togliendo stagioni, tendenza e Covid, le serie della città si muovono ognuna per conto suo.

**Come si leggono i numeri.** `rho` va da -1 a +1: 0 vuol dire nessun legame, 1 ordine perfetto. "A parità" vuol dire che ho tolto distanza dal Duomo, reddito, età media e densità (i "4 controlli"). "Controlli forti" aggiunge laureati, prezzi, quota di cittadini stranieri e numero di residenti. `q` è la probabilità di falso allarme tenendo conto di quante prove ho fatto. Le classifiche sono: **FORTE** regge a tutti i controlli, **MEDIO** regge ma con un punto debole dichiarato, **DEBOLE** è solo un indizio.

### Quanto è stretto il setaccio (70 quartieri con almeno 3.000 residenti)

| Passo | Coppie rimaste |
|---|---|
| Coppie provate (152 variabili) | 11.439 |
| Tolte perché meccaniche, stessa fonte o stesso concetto | 900 |
| Grezze con legame forte (rho oltre 0,5) | 1.706 |
| Grezze "significative" dopo la correzione per le prove multiple | 4.390 |
| Dopo i 4 controlli (q sotto 0,05) | 257 |
| Con le etichette dei quartieri mescolate, per caso | 0 |
| Dopo le permutazioni spaziali | 257 |
| Dopo i controlli forti e dentro il municipio | 197 |
| Oltre i 6 assi generali della città | 77 |
| Dopo la lettura una per una (meccanismo, punti deboli) | i 12 qui sotto, più i segnali minori |

Due cose imparate dal setaccio: il caso non è il problema (zero falsi con etichette mescolate) e nemmeno la vicinanza geografica (i residui hanno poca autocorrelazione: Moran quasi sempre sotto 0,2, massimo 0,32). **Il vero problema è che un solo asse riassume il 35% di tutto**: centro, reddito, laureati, prezzi, locali e voto a sinistra sono quasi la stessa cosa. Molte coppie sono solo due termometri della stessa febbre.

---

## 1. I risultati che restano

### 1. Il voto segue i laureati, non il reddito — FORTE, nuovo

- **Numeri.** Destra e centrodestra alla Camera 2022 contro laureati: rho -0,87. Contro reddito: -0,79. Messi in gara insieme: **laureati -0,72 (t -5,5), reddito 0,00 (t 0,0)**. In punti: 10 punti di laureati in più valgono **-4,4 punti** di destra; 10.000 euro di reddito in più valgono +1,05 (non distinguibile da zero). Quarto Oggiaro: 12% laureati, 46% destra. Pagano: 48% laureati, 30% destra.
- **Stabile nel tempo.** In tutte le 8 elezioni 2016-2024, per sinistra e destra, il reddito non va oltre |t| = 1 quando ci sono i laureati. I laureati arrivano almeno a |t| 2,3 per la destra in 6 elezioni su 8 (fanno eccezione Comunali 2016 ed Europee 2024) e per la sinistra fino al 2021. Dal 2022 la sinistra non è più ordinata né dall'una né dall'altra cosa: vedi risultato 2.
- **Fonti.** `censimenti/pulito/indicatori_NIL.csv` (`quota_laureati_su_base`), `quartieri-che-cambiano/out/indicatori_nil.csv` (`reddito_2024`), `docs/elezioni/data/nil/*.json`. Tabella: `out/app_voto_laureati_reddito.csv`.
- **Controlli.** Il dubbio più serio era la grana: i laureati vengono dalle sezioni, il reddito da 38 CAP. Ho quindi sfocato i laureati sui CAP, come il reddito: **il risultato resta (-0,79 contro +0,13)**. Regge senza il centro (57 quartieri: -0,74 contro -0,04), senza i 4 quartieri con CAP instabili, con i prezzi al posto del reddito (-0,75 contro +0,04). Lega alle Europee 2019: rho -0,94, a parità -0,74, togliendo i 5 quartieri più influenti -0,58. Eccezione onesta: per il M5S 2018 contano entrambi (-0,49 e -0,25) e per il Centro 2022 entrambi (+0,71 e +0,17).
- **Spiegazione innocente.** Confronto tra zone, non tra persone: non dice che i laureati votano a sinistra. Il reddito è del contribuente, non del residente. Reddito e laureati sono molto legati (rho 0,8), quindi la gara è sensibile. Le famiglie politiche sono raggruppamenti del progetto.
- **Sul sito.** `voto-reddito` confronta il voto con il reddito e non usa mai i laureati: questo risultato ne cambia la lettura.

### 2. Laureati di ieri e laureati di oggi votano diverso — FORTE, nuovo

- **Numeri.** A parità di laureati di oggi (e dei 4 controlli), i quartieri che **ne avevano già molti nel 1991** votano meno a sinistra e più a destra: da -0,37 a -0,57 per la sinistra e da +0,36 a +0,61 per la destra, **in tutte le 7 elezioni provate**. Esempio: Porta Romana e Brera hanno oggi gli stessi laureati (44%); nel 1991 erano 11,5% e 21,6%; alla Camera 2022 la sinistra fa 37,1% contro 26,6%.
- **In punti.** Passare da 18 a 24,5 punti di nuovi laureati in 30 anni vale **+4,5 punti** di sinistra alla Camera 2022.
- **Fonti.** `censimenti/pulito/indicatori_NIL.csv` (`quota_laureati_su_residenti` 1991 e 2023), `out/app_laureati_vecchi_nuovi.csv`.
- **Controlli.** Rho a parità 0,69 (intervallo 0,52-0,80), q sotto 0,0001, permutazioni spaziali p 0,0001, senza i 5 più influenti 0,60, togliendo un municipio alla volta 0,64-0,73, controlli forti 0,74, oltre gli assi generali 0,70. Stesso risultato sui 66 quartieri a confini stabili (0,66) e con i sotto-periodi 1991-2011 e 2011-2023 (0,49 e 0,49). Non cambia con età 20-34, dimensione delle famiglie o ricambio di residenti.
- **Spiegazione innocente.** Il 1991 è ricostruito con la sovrapposizione delle sezioni, e il 2023 è una stima da registri. "Vecchi laureati" può essere il nome di una ricchezza di famiglia che il reddito per CAP non vede, anche se regge coi prezzi tra i controlli.
- **Curiosità collegata.** La mappa dei laureati del 1991 prevede il M5S del 2018 un po' meglio di quella di oggi: rho -0,93 contro -0,91. In 32 anni la geografia sociale di Milano si è mossa poco (rho 1991-2023: 0,93).

### 3. Dove si vota meno si muore di più, anche a parità di reddito ed età — FORTE, nuovo

- **Numeri.** Affluenza Camera 2022 contro morti osservate su attese (SMR) 2022-2024: rho -0,80, **a parità -0,68**. Diviso in tre gruppi: nel terzo con meno affluenza 16.913 morti contro 15.661 attese (**+8%**); nel terzo con più affluenza 13.445 contro 14.665 (**-8%**). Anche dentro ogni fascia di reddito: reddito basso, SMR 1,15 con affluenza bassa e 0,98 con affluenza alta. L'affluenza da sola spiega il 64% dell'ordine dei quartieri; il reddito il 32%, la disoccupazione 2011 il 51%, i laureati il 43%.
- **Fonti.** `docs/elezioni/data/nil/*.json` (`vt`, `e`), `speranza-vita/pulito/nil_smr_e0.csv` (`smr`; non uso la speranza di vita, che è un modello). Tabella: `out/app_affluenza_smr_tutte_elezioni.csv`.
- **Controlli.** Provate **15 elezioni per 3 periodi: 45 legami su 45 sono negativi**, anche con le morti del 2012-2015, prima di tutte queste elezioni. Uomini e donne simili (-0,57 e -0,54). Permutazioni spaziali p 0,0001, Moran 0, senza i 5 più influenti -0,54, togliendo un municipio -0,60/-0,72, controlli forti -0,66, sezioni poco condivise -0,73, oltre gli assi generali -0,60. Senza Morivione -0,69.
- **Punto debole dichiarato.** Sfocando l'affluenza sui CAP il legame scende a -0,38 (SMR 2022-24) e -0,23 (2012-19): buona parte del vantaggio sul reddito viene dalla grana più fine. In gara con la disoccupazione 2011, che ha la stessa grana, l'affluenza vince alle politiche e ai referendum grandi (Camera 2022: -0,86 contro -0,03), ma non alle Comunali 2021 o alle Europee (-0,12/-0,30 contro +0,40/+0,33).
- **Spiegazione innocente.** Nessuno vive di più perché vota. L'affluenza è una misura fine, gratuita e per sezione dello svantaggio che il reddito per CAP non vede. Le residenze per anziani alzano l'SMR e non ho il loro elenco; il registro può contenere residenti solo sulla carta. Confronto tra zone, non tra persone.
- **Sul sito.** `speranza-vita` confronta con il reddito, non con il voto.

### 4. Il reddito per CAP racconta male alcuni quartieri — FORTE come limite, nuovo

- **Numeri.** Con 7 indicatori diversi dal reddito (laureati, occupati, disoccupazione 2011, affluenza, case ALER, mortalità 2012-19, prezzi; correlazione media tra loro 0,58) ho messo in fila i quartieri e li ho confrontati con il reddito. Accordo generale buono (rho 0,81), ma **San Siro è 27° per reddito e 60° sul resto**. Così anche Giambellino (22° e 54°), Gallaratese (33° e 58°), Moncucco (28° e 52°). Al contrario Rogoredo-Santa Giulia (57° e 27°), Muggiano (68° e 38°), Affori (65° e 42°).
- **Fonti.** `out/app_reddito_cap_vs_indice.csv`.
- **Controllo.** San Siro e Ortomercato sono "anomali" se predico con il reddito (p 0,006 e 0,000), e smettono di esserlo se predico con i laureati (p 0,96 e 0,66; `out/nil_anomali_due_versioni.csv`): l'anomalia era nel reddito, non nel quartiere.
- **Spiegazione innocente.** La media può essere giusta e nascondere due mondi nello stesso CAP. Il mio indice è una costruzione, con pesi uguali, e contiene affluenza e mortalità (quindi non va usato per ridimostrare il risultato 3).
- **Conseguenza pratica.** Tocca le pagine che usano il reddito per quartiere come misura sociale: `speranza-vita` (quintili), `lavoro`, `voto-reddito`, `quartiere`.

### 5. Quando piove spariscono le moto, le auto no — FORTE, nuovo

- **Numeri.** Giorni feriali normali in Area C (1.386 giorni, senza agosto, Natale e Covid): con almeno 1 mm di pioggia le moto calano del **22%** (z -14), oltre i 10 mm di un altro 21%. Le auto salgono appena dell'1% (z 2). In numeri medi: da 29.325 a 22.785 moto (-6.540), da 121.388 a 123.493 auto (+2.105): **solo un terzo delle moto mancanti si ritrova in auto**. Il totale cala del 2,9%.
- **Fonti.** `docs/area-c/data/ingressi_giornalieri.csv` (`tipo_moto`, `tipo_auto`), `pioggia-e-caldo/pulito/intermedi/P_orario.parquet`. Tabella: `out/app_pioggia_areac.csv`.
- **Controlli.** La pioggia di ieri non conta (+0,3%); quella di domani poco (-5,7%: previsioni, o pioggia che dura). Vale nel 2016-2019 (-19%) e nel 2022-2024 (-15%), con stagioni diverse (inverno -22%, estate -11%).
- **Spiegazione innocente.** È solo Area C. Non so dove finiscano quei viaggi: mezzi, giorni diversi, percorsi fuori dalla cerchia. Le telecamere potrebbero leggere peggio le targhe piccole con la pioggia, anche se non si vede sulle auto.

### 6. Le Olimpiadi hanno raddoppiato le letture dall'estero, per un mese — FORTE, nuovo

- **Numeri.** A febbraio 2026 le letture dei luoghi di Milano nelle Wikipedia non italiane valgono **80,6 per milione** di letture totali, contro 36-37 nei febbraio 2023-2025 (2,2 volte). Solo 1 mese su 85 ha un rapporto più alto. **In italiano 1,05 volte: niente.** A marzo si torna a 32,5. Salgono San Siro (da 123 a 295 mila), Unipol Dome (da 11 a 111 mila), Villaggio Olimpico (da 1 a 35 mila). L'Ultima Cena scende.
- **Fonti.** `luoghi-cercati/pulito/luoghi_vs_wikipedia_mensile.csv`, `views_mensili.csv`.
- **Spiegazione innocente.** Leggere non è venire: i passeggeri di febbraio (Malpensa +18%, Linate +20%) restano dentro le oscillazioni normali, e i turisti del 2026 non ci sono ancora nei dati.

### 7. Più sono piccole le famiglie, più si vota a sinistra, e sempre di più — MEDIO, nuovo

- **Numeri.** Europee 2024: a parità rho -0,53, con i controlli forti **-0,67**. Da 1,77 a 1,96 persone per famiglia: **-4,5 punti** di sinistra. Il legame cresce: con i controlli forti -0,23 nel 2016, -0,44 nel 2019, da -0,63 a -0,67 nel 2022-2024.
- **Fonti.** `censimenti/pulito/indicatori_NIL.csv` (`famiglie_comp_medio_*`, `quota_famiglie_1_comp`), `docs/elezioni/data/nil/*.json`.
- **Controlli.** q 0,001, spaziale p 0,0001, senza i 5 più influenti -0,40, togliendo un municipio -0,47/-0,61, oltre gli assi generali -0,57.
- **Punto debole.** Il salto tra 2021 e 2022 coincide con il Centro che corre da solo: parte della crescita può essere il cambio di offerta politica. Le famiglie 2023 sono stime del censimento permanente; anche chi non vota (cittadini stranieri, minori) entra nella dimensione della famiglia.

### 8. Dove donne e uomini lavorano in modo più diverso si vota meno — MEDIO, nuovo

- **Numeri.** Divario di occupazione uomini-donne contro affluenza: a parità -0,58 sia alle Comunali 2021 sia alle Europee 2024, -0,59 al referendum 2025. Da 8,4 a 11 punti di divario: **-3 punti** di affluenza. In gara con occupazione, disoccupazione, laureati, reddito, età e cittadinanza resta il segno: t da -2,3 a -3,7 in 4 elezioni su 4.
- **Fonti.** `docs/lavoro/data/nil_lavoro.csv` (`gap_occ_mf`), `docs/elezioni/data/nil/*.json`.
- **Controlli.** q 0,0001, spaziale p 0,0002 o meno, senza i 5 più influenti -0,44/-0,51, togliendo un municipio -0,51/-0,64, controlli forti -0,46, con il registro elettorale tra i controlli -0,55.
- **Punto debole.** I dati 2021-2023 per quartiere sono stime da registri e modelli (`lavoro/NOTE.md`): non si confrontano col 2011. Può essere un altro termometro dello svantaggio, come il risultato 3, più che un fenomeno a sé. Il divario non dice chi lo vive.

### 9. Da novembre 2023 le denunce salgono, e a Milano più che in Italia — MEDIO, già nei dati ma non commentato

- **Numeri.** Il programma trova, senza che gliela indichi, una rottura a **novembre 2023** sia nei maltrattamenti in famiglia sia nello stalking. I 12 mesi dopo contro i 12 prima: maltrattamenti **+31,7%** a Milano e +19,8% in Italia (l'anno prima -1,4% e 0,0%); stalking **+24,9%** e +13,4% (l'anno prima +5,6% e +2,8%). Ottobre 2023: 116 maltrattamenti; novembre: 152.
- **Fonti.** `docs/reati-citta/data/famiglia_stalking_mensile.csv`.
- **Spiegazione innocente.** Denunciato non è commesso: è molto più facile che sia aumentata la denuncia che il fatto. A novembre 2023 ci sono stati un femminicidio molto seguito e una legge nuova (contesto mio, da verificare; non è nei dati). Anche le chiamate al 1522 salgono (`violenza-donne/NOTE.md`). È provincia, non comune, e il dato finisce a dicembre 2024. Sul lungo periodo (dal 2018) l'Italia cresce più di Milano.

### 10. Le notti in albergo si muovono con Linate, non con Malpensa — MEDIO, nuovo

- **Numeri.** Tolte stagione e tendenza, senza Covid: Linate e presenze rho 0,67 (n 60), q 0,03 anche dopo aver tolto la memoria di ogni serie. Prova diversa (variazione sull'anno prima, poi differenza mese su mese, dal 2023): **Linate 0,57, Malpensa 0,38, Bergamo 0,16**.
- **Fonti.** `docs/aeroporti/data/mensile_tre_aeroporti.csv`, `turisti/pulito/milano_mensile_totale.csv`.
- **Spiegazione innocente.** Lo stesso calendario di fiere e Pasqua mobile può spingere entrambi. Le presenze sono solo 2019 e 2022-2025, quindi poche. Nessuna informazione su chi viaggia.

### 11. I beni confiscati stanno dove ci sono più bar e ristoranti — MEDIO, nuovo

- **Numeri.** A parità rho 0,52 con i locali per residente; terzo con meno locali 0,88 unità ogni 10.000 abitanti, terzo con più locali 3,17. I più alti per indirizzi distinti: Farini, Bovisa, Loreto-NoLo, Dergano.
- **Fonti.** `docs/beni-confiscati/data/nil.geojson` (`cu`), `beni-confiscati/pulito/per_nil.csv`, `docs/beni-confiscati/data/unita_comune.csv`, `docs/ristoranti/data/nil.csv`.
- **Controlli.** Regge con altre definizioni, importanti perché tre palazzi pesano tanto: elenco ANBSC 0,40, indirizzi distinti 0,47, per km² 0,45; conteggi puri, togliendo il denominatore comune, 0,50. Controlli forti 0,47, senza i 5 più influenti 0,36. **Punto debole:** oltre gli assi generali scende a 0,30.
- **Spiegazione innocente.** Le vie con molti negozi hanno più unità di ogni tipo, confiscate comprese: si contano unità, anche box e cantine. Non c'è data di confisca. **Non dice** che i locali abbiano a che fare con la criminalità: dice dove stanno i muri.

### 12. Dove ci sono più Airbnb ci sono meno aree gioco per abitante — MEDIO, nuovo

- **Numeri.** A parità rho -0,52. Terzo con meno Airbnb 10 aree ogni 10.000 abitanti, terzo con più Airbnb 4,4. Regge togliendo palazzi vecchi, verde, ALER, suolo e bambini (da -0,43 a -0,53), e per km² (-0,39) o per bambino (-0,44).
- **Fonti.** `affitti-brevi/pulito/nil_riepilogo.csv`, `docs/verde/data/nil_verde.csv` (`gioco_n`).
- **Punto debole.** Togliendo i 5 quartieri più influenti scende a -0,28. La **vicinanza** non c'entra: quota di residenti con un'area gioco entro 15 minuti +0,03. C'è meno quantità, non meno accesso.
- **Spiegazione innocente.** Tessuti storici senza spazio, con i turisti che arrivano lì per altri motivi. Non è l'Airbnb a togliere i giochi.

---

## 2. Tipi di quartiere e anomali

**I municipi spiegano poco — FORTE, nuovo.** Sui 140 indicatori il municipio spiega in mediana il 18% delle differenze, contro l'11% atteso col caso con 9 gruppi mescolati. Quattro semplici fasce di distanza dal Duomo fanno meglio (24%). Il 58% dei confini tra quartieri vicini separa tipi diversi. È anche una conseguenza del disegno: i municipi sono spicchi, ognuno va dal centro alla periferia.

**Quattro tipi** (`out/nil_tipi.csv`). Stabili al ricampionamento (accordo 0,67; tra due metodi 0,88), ma con confini sfumati: Milano è un continuo, non quattro isole. Il 37% spiegato dai tipi è un po' gonfiato, perché i tipi nascono dagli stessi dati.

| Tipo | Quartieri | Reddito | Laureati | Affluenza 2022 | SMR 2022-24 | Esempi |
|---|---|---|---|---|---|---|
| Centro storico | 9 | 70.000 | 46% | 73% | 0,9 | Brera, Duomo, Pagano, Magenta |
| Semicentro denso | 18 | 44.000 | 40% | 71% | 1,0 | Isola, Sarpi, Città Studi, NoLo |
| Città in movimento | 24 | 31.000 | 28% | 67% | 1,0 | Bovisa, Bicocca, Lambrate, Corvetto, San Siro |
| Periferia esterna | 19 | 28.000 | 21% | 65% | 1,1 | Baggio, Gallaratese, Quarto Oggiaro, Comasina |

La "città in movimento" è il tipo più interessante: più giovane (44,6 anni), con molta costruzione recente; 11 dei suoi 24 quartieri sono "in salita rapida" per `quartieri-che-cambiano`. L'accordo con quelle tipologie è solo parziale (0,23): misurano cose diverse.

**Quartieri fuori da ciò che reddito, centralità, età e densità prevedono** (`out/nil_anomali.csv`, `out/nil_anomali_due_versioni.csv`). Si contano gli indicatori con scarto forte, confrontandoli col caso. Tengo chi resta anomalo sia con il reddito sia con i laureati come predittori (Maggiore-Musocco-Certosa è al limite: p 0,06 con il reddito):

| Quartiere | Cosa ha di strano | Possibile lettura |
|---|---|---|
| **Rogoredo-Santa Giulia** | Reddito basso ma poca disoccupazione, pochi incidenti, niente BikeMi vicino, quasi nessun laureato nel 1991 | Quartiere nuovo, di arrivo recente: il CAP non lo vede ancora |
| **Vigentino-Fatima** | Popolazione anziana, mortalità bassa, senza metro né BikeMi, voto a destra sopra l'atteso | Un paese dentro la città |
| **Morivione** | Mortalità molto alta (SMR 1,45), niente cinema né artigiani | Probabile residenza per anziani, già segnalata dal filone |
| **Maggiore-Musocco-Certosa** | Saldo di arrivi +16 per mille, età che scende | Grande cantiere |

Più piccoli e quindi più rumorosi (sotto 5.000 residenti): QT8, Muggiano, Farini. Spariscono togliendo il reddito: **San Siro, Ortomercato, Bovisa**. Bovisa resta comunque notevole per pochi alberi (47 per 1.000 abitanti, mediana 143).

---

## 3. Segnali minori

| Legame | Numeri | Perché è solo minore | Voto |
|---|---|---|---|
| Inflazione di quest'anno, compravendite l'anno dopo | r -0,86 (n 15, q 0,03); ogni punto di inflazione: -4,3% di compravendite. Stessa cosa per le immatricolazioni (-0,89). Regge senza crisi e Covid | È tutto il paese, passa dai tassi; 15 anni soli | MEDIO, nuovo |
| Impianti di telefonia e locali | Per km²: in gara locali +0,65 (t 5,1), densità di abitanti +0,10 (t 1,2). A parità gli impianti per abitante seguono le letture dall'estero (0,49) | Plausibile: la rete segue chi c'è di giorno. La pagina dice già 0,79 con gli abitanti, ma su tutti gli 88 quartieri | MEDIO, in parte noto |
| Case ALER e mortalità | A parità 0,47, controlli forti 0,36 | Un altro termometro dello svantaggio; dati 2016, senza case del Comune | MEDIO, proxy |
| Domenica si muore meno | -2,8% (z -3,5), sotto la media in 10 anni su 12 | Effetto piccolo. Vedi idee | DEBOLE, nuovo |
| Nidi e divario di lavoro | -0,37, q 0,047 nell'elenco chiuso, senza 5 -0,21 | Sedi del 2018, non posti; nello screening largo q 0,11 | DEBOLE |
| Palazzi antichi e opere pubbliche | 0,47, regge | Quasi ovvio: statue e lapidi vanno dove la città è vecchia | Non interessante |

---

## 4. Cosa sembrava interessante ed è morto (con il perché)

**Domande che ci si aspetta, in elenco chiuso** (`out/nil_ipotesi.csv`: 50 domande scritte prima, correzione solo su queste).

| Domanda | Risultato | Perché è morta |
|---|---|---|
| Più Airbnb, meno bambini, alunni, residenti? | A parità -0,08 / -0,12 / -0,20 / -0,27, q oltre 0,17 | La caduta grezza (-0,41 sui residenti in età scolare) è tutta centralità e reddito |
| Airbnb cresciuti, affitti più alti? | -0,12; col livello +0,03 | Niente a questa scala. Non prova che non ci sia effetto: gli affitti OMI sono per zona |
| Più case nuove, prezzi meno alti? | +0,28, q 0,17 | Se mai il contrario, ma non si distingue |
| Metro vicina, prezzi saliti? | -0,13 | Niente: `prezzi-case` lo tratta con il confronto M4 |
| Più alberi o verde, meno morti? Più calore, più morti? | +0,03, +0,08, -0,05 | Il grezzo col calore (-0,44) è la ricchezza del centro. Non si dice che il verde non faccia bene: a questa scala non si vede |
| Più antenne, più morti? | Grezzo -0,58, a parità -0,26, q 0,17 | Niente, e se mai segno opposto |
| Più medici o farmacie, meno morti? | +0,12, +0,11 | Niente. Il grezzo con le farmacie (-0,33) è il centro |
| Più associazioni, più affluenza? | 0,00 | La sede legale non dice dove lavora un'associazione |
| Targhe della Resistenza o pietre, più sinistra? | +0,24 (q 0,21), -0,03 | Il grezzo (0,36 e 0,50) è il centro storico |
| Metro vicina, meno incidenti per residente? | +0,45, q 0,003: **al contrario** | È il denominatore: gli incidenti sono di chi passa, non di chi abita |

**Passati allo screening, morti alla lettura.**

| Coppia | Numeri | Perché è morta |
|---|---|---|
| Crescita antenne e spostamento a sinistra | +0,53 → senza 5 +0,28 | Nessun meccanismo: due cose che crescono nei quartieri in cambiamento |
| Quota incidenti moto e calo bambini | -0,44 | Nessun meccanismo; entrambe seguono l'anello semicentrale |
| Bambini e medici entro 15 minuti | -0,49 → senza 5 -0,27 | Tetto: il valore è quasi sempre 100%. Con i medici per abitante -0,09 |
| Sport per abitante ed elettori per adulto | +0,56 | La seconda misura il registro elettorale (cittadini stranieri, residenti all'estero): tolta dalla ricerca |
| Airbnb cresciuti e voto | -0,61, n 42 → senza 5 -0,32 | Pochi quartieri; è solo l'allargamento verso la periferia |
| Occupati e arrivi da altri comuni | +0,57 | Quasi una tautologia: chi arriva lavora, e i dati vengono dagli stessi registri |
| Palazzi antichi e 80enni | -0,43 | Nasce dal controllo sull'età; grezzo -0,10. Case del dopoguerra e 80enni: +0,20, niente |
| Cucine (pizza e artigiani, poke e BikeMi, italiana e letture estere) | -0,63, +0,54, -0,58, n circa 39 → senza 5 -0,37, +0,24, -0,36 | OSM volontario, tag più frequenti in centro |
| Reddito e destra | A parità -0,42 → controlli forti +0,02 | Era il titolo di studio: risultato 1 |
| Eccesso di morti nel 2020 con densità, famiglie, reddito, ospedali | q minima 0,14 | **Il dato è quasi tutto rumore**: il 98% delle differenze tra quartieri è ciò che il caso produrrebbe da solo. Si può dire solo che l'SMR 2020 ricalca quello di prima (0,71) |

**Sulle serie della città.**

| Cosa | Numeri | Perché è morta |
|---|---|---|
| Quasi tutto il mensile | 5.738 prove, ne restano 7, di cui 6 sono meteo-aria già noti | Le serie della città non si parlano |
| Quasi tutto l'annuale | 2.485 prove, ne restano 3 | Una è prestiti-affitti con rho 1,00 su 8 anni: artefatto. Nati e presenze, musei e pioggia ecc.: q oltre 0,3 |
| PM10 e NO2, morti dello stesso giorno | +0,15% per 10 µg (z 0,9) | Non si vede nel giornaliero. **Non vuol dire che l'aria non faccia male**: il danno è cumulato e i dati non hanno la forza per vederlo così |
| Benzina cara, meno ingressi; shock energia 2022 | Mensile -0,13. Area C -10% nel 2022 rispetto al 2017-19, ma -13% nel 2023 e -16% nel 2024 | Il calo c'è ma non è dell'energia: continua dopo |
| M4 e Linate | Linate sul 2017-18: +1% (2023), +14% (2024), +19% (2025). Malpensa +13, +25, +36 | Linate cresce meno degli altri: non si vede un effetto M4 |
| M4 e Area C | -11% prima di M4, -14% dopo | Era già giù |
| Chiusura di Linate e aria | NO2 -20% (z -1,9) | Il NO2 resta basso anche dopo la riapertura: è Area B e tendenza |
| Expo e musei civici | +23% nel 2015, +13% nel 2016, +18% nel 2017 | Non torna giù: Mudec, biglietti, tendenza. Prestiti -7% |
| Presenze e prestiti | 0,49, q 0,002 | Entrambe in ripresa dopo il Covid: con la differenza mese su mese -0,21 |
| Inflazione e prestiti | 0,46 | Stessa cosa: dal 2024 +0,11 |
| Rotture che coincidono | 101 coppie contro 63 attese (p 0,001) | 83 su 101 sono tutte dal 2022 in poi: uscita dal Covid |
| Pioggia e prestiti, pioggia e musei | +0,20 (q 0,09), -0,05 | Troppo poco |

---

## 5. Già noti sul sito (ritrovati: confermano che il metodo funziona)

Caldo e morti (+3,6% per grado oltre 24 °C, z 12), freddo e morti, Linate chiusa con Malpensa che assorbe (-2,28 milioni contro +2,34), Area B e NO2 (-14%, ma -7,5% l'anno prima, quindi l'effetto netto è circa la metà), reddito e mortalità, Airbnb e reddito, alberi e reddito, prezzi e centralità, servizi e reddito, pioggia e aria. Non li conto come scoperte.

---

## 6. Idee che i dati suggeriscono

**Pagine o approfondimenti**

1. **"Chi vota cosa: laureati o ricchi?"**: unisce `voto-reddito` e `censimenti`, con i laureati del 1991 (risultati 1, 2, 7).
2. **Il quartiere dentro il quartiere**: l'affluenza esiste per sezione (circa 1.250). Mostrerebbe i due mondi dentro San Siro o Giambellino, che il CAP non vede.
3. **Un indice sociale per quartiere** come alternativa al reddito per CAP, da mettere accanto al reddito dove la pagina lo usa come misura sociale. Va costruito con più cura del mio.
4. **Dove spariscono le moto quando piove**: `area-c/pulito/ingressi_varco_giorno.csv` ha il dettaglio per varco.
5. **Cosa c'è ora al posto dei cinema spariti**: `cinema-spariti/pulito/cinema.csv` (`cosa_c_ora`) unito a Airbnb, locali, botteghe.
6. **A chi vanno i beni confiscati**: unire `beni-confiscati` e `terzo-settore` per assegnatari e quartiere.

**Stranezze da guardare**

7. **La domenica si muore meno**: giorno vero, o effetto di come vengono registrati i decessi? Da capire.
8. **Nei quartieri ricchi gli elettori sono più degli adulti residenti** (già in `voto-reddito/NOTE.md`). Rifare l'affluenza sugli adulti cambierebbe alcune classifiche: il legame con la mortalità regge (-0,40 alle Comunali 2021).
9. **Il segno di Area C si inverte tra le due serie**: nella serie 2012-2015 la pioggia dà +3%, in quella dal 2016 -3%. Forse la vecchia non conta le moto allo stesso modo (ipotesi non verificata): da chiarire prima di unirle.

**Assenze che pesano**

10. **Elenco delle residenze per anziani con i posti letto**: risolverebbe Morivione e pulirebbe tutto l'SMR. Sarebbe l'unico file nuovo davvero utile (non l'ho cercato).
11. **Età e cause di morte per quartiere** non esistono; l'età alla morte per NIL si potrebbe chiedere al Comune.
12. **Incidenti con il giorno**: dal 2012 c'è solo il mese, quindi niente pioggia-incidenti, che sarebbe la domanda naturale dopo il risultato 5.
13. **Serie che si fermano**: Area C a novembre 2024, musei civici al 2017, presenze mensili solo dal 2019, metro solo annuale. Per questo la M4 e le Olimpiadi non si misurano bene.

---

## 7. Metodo, scelte e limiti

**Scelte dichiarate**

- **Cittadinanza.** Non è origine. Quota stranieri, diversità e divario scuola-residenti restano solo come **controlli**, e non entrano nella ricerca di scoperte. Non produco nessun risultato che leghi una comunità a un quartiere o a un fenomeno. Unica prova neutra: se le cucine seguono i residenti di quella cittadinanza; il legame è debole e irregolare (a parità da 0,11 a 0,37, n 39) e lo lascio fuori.
- **Speranza di vita** e **verde stima B**: non usate come scoperte. La prima è un modello con età non osservata per quartiere (uso l'SMR), la seconda è collocata con gli alberi.
- **Elettori per adulto**: tolta dalla ricerca perché misura il registro.
- **Laureati, reddito, prezzo, età, densità** sono controlli e non entrano nello screening largo. Il risultato 1 è arrivato da laureati 1991 e variazione dei laureati, che ci sono entrati, ed è stato poi provato a parte.
- **Prestiti per quartiere**: solo 22 quartieri con biblioteca, fuori dallo screening.

**Un errore trovato e corretto.** Al rilancio completo è uscito un difetto del lettore dei CSV: le colonne con separatore `;` e celle vuote restavano testo, e questo lasciava vuota `medici_65piu`. Corretto: è l'unica colonna delle tabelle che cambia e non ha legami che sopravvivono (q minima 0,08). Le tabelle dei risultati sono identiche; cambiano di poco solo i conteggi del setaccio.

**Tabelle**

- `out/nil_tabella.csv`: 70 quartieri (`nil_tabella_tutti.csv`: 88), 168 variabili descritte.
- `out/tempo_giorno.csv`, `tempo_mese.csv`, `tempo_anno.csv`: serie di città.
- `out/dizionario.csv`, `dizionario_tempo.csv`: per ogni colonna fonte, anno e limite; per i quartieri anche costruzione, denominatore e affidabilità. Il dizionario delle serie non copre tutte le colonne di `tempo_*`.
- `out/limiti_note.txt`: le sezioni sui limiti di tutti i `NOTE.md`, lette prima di usare le variabili.

**Quartieri, in ordine**

1. Rho grezzo per tutte le coppie.
2. Rho parziale sui ranghi con distanza (e quadrato), reddito, età media, densità.
3. Correzione di Benjamini-Hochberg sulle sole coppie non meccaniche (`out/nil_coppie_tutte.csv`, colonna `meccanica`).
4. Permutazioni spaziali (Moran spectral randomization, 9.999 prove) e Moran sui residui.
5. Controlli forti e municipio come effetto fisso.
6. Assi latenti: analisi parallela, 6 assi, ricalcolati senza le variabili della stessa fonte o concetto.
7. Sui candidati: 5 più influenti tolti, un municipio tolto alla volta, intervallo bootstrap, filtro spaziale MEM, definizioni alternative.

**Serie, in ordine**

1. Tolte stagione e tendenza a tratti, stimate senza il Covid.
2. Tolta la memoria di ogni serie (AR1).
3. Anticipi e ritardi da -6 a +6 mesi, correzione per prove multiple, con e senza marzo 2020-dicembre 2021.
4. Annuale su differenze, senza 2020-2022.
5. Rotture con segmentazione e test di coincidenza.
6. Esperimenti naturali contro gli stessi mesi degli anni prima, con anni finti come riprova.
7. Modelli giornalieri con errori robusti.

**Limiti generali**

- 70 quartieri e tanti confronti: i numeri sono ordini di grandezza.
- Reddito e prezzi sono condivisi tra quartieri vicini.
- Il censimento 2021-2023 è in parte stima.
- Tutti i confronti sono tra zone, mai tra persone: la **fallacia ecologica** è sempre in agguato.
- Le permutazioni spaziali mantengono l'autocorrelazione di una variabile; non possono togliere un fattore comune non misurato.
- Il giudizio finale, FORTE o MEDIO, è una lettura mia dei controlli, non un calcolo.

**Rifarlo**: `python -I -X utf8 scripts/lancia_tutto.py` (circa 3 minuti, semi fissi, scrive i log in `out/log_*.txt`).
