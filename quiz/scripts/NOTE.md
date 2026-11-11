# Quante ne sai di Milano? — come è fatto il mazzo

Pagina: `docs/quiz/` (bozza in `bozze-grafici/quiz-v2/index.html`, anteprima con `python -I -X utf8 bozze-grafici/anteprima.py quiz`).

## Comando

    python -I -X utf8 quiz/scripts/genera.py                 # rigenera tutto e controlla
    python -I -X utf8 quiz/scripts/genera.py --solo fatti_a_clima   # controlla un modulo solo, non scrive

Scrive:
- `docs/quiz/data/mazzo.json` — le domande del gioco su Milano (sotto i 300 KB: il programma si ferma se no);
- `docs/quiz/data/quartieri.json` — i numeri del gioco per quartiere;
- `quiz/prove_mazzo.json` — per ogni domanda, file, percorso e valore di ogni dato letto (non pubblicato).

## File

| File | Cosa fa |
|---|---|
| `mazzo.py` | attrezzi: `Prove` (registra ogni lettura), lettore di JSON/CSV di `docs/`, i sei tipi di domanda |
| `genera.py` | raccoglie i moduli `fatti_*.py`, controlla, scrive |
| `fatti_00_esempio.py` | due domande modello |
| `fatti_a_clima.py` | clima, ambiente, muoversi (26 pagine) |
| `fatti_b_persone.py` | persone, casa, soldi (27 pagine) |
| `fatti_c_cultura.py` | servizi, sicurezza, cultura, politica (29 pagine) |
| `fatti_e_nuove.py` | 10 pagine nuove (56 domande): università, ospedali, catasto, economia, lavoro, aeroporti delle Olimpiadi, case e energia, negozi, proverbi, il tuo anno |
| `fatti_d_quartieri.py` | «quale quartiere?»: terne di quartieri dalle schede, seme fisso |
| `quartieri_gioco.py` | dati del gioco per quartiere (schede + età per quartiere) |

## Domande tolte
`escluse.txt`: 97 domande tolte l'11/11/2026 perché troppo tecniche o di nicchia (centraline, tariffe, catasto minuto, consiglio comunale…). Davide vuole fatti «grossi e succosi». `genera.py` le salta e avvisa se un id non esiste più. Nel mazzo restano 136 domande.

## Regole del mazzo
- Ogni numero viene da `p.v(file, percorso…)` sui file di `docs/<pagina>/data/`, o da `p.calc(...)` su quei valori. Mai numeri a mano.
- `genera.py` rilegge ogni file da capo e verifica: valori uguali, calcoli rifatti, ogni numero mostrato è una lettura o un calcolo, ogni numero scritto nel testo torna (arrotondato) con i dati, la pagina esiste, il tema viene da `temi.json`, la licenza è tra quelle della pagina in `docs/fonti/data/fonti.json`, niente parole vietate (nomi di file, «trappole»…). Deve finire con 0 errori e 0 avvisi.
- Numeri che nel testo fanno parte di un'unità («ogni 1.000 abitanti», «a 15 minuti», «over 65») e i decenni sono ammessi senza lettura.
- Si usa l'ultimo anno completo; gli anni parziali (2026 a metà) no. Ogni domanda dice l'anno.
- Le dieci pagine nuove (università, ospedali, catasto, economia, occupazione, Olimpiadi, case e energia, negozi, proverbi, il tuo anno) sono in `fatti_e_nuove.py`. Per `olimpiadi` le opere vengono da Simico, senza licenza dichiarata e fuori da `fonti.json` (c'è solo Eurostat per gli aeroporti): per questo ci sono solo domande sugli aeroporti, non sulle opere.

## Gioco per quartiere
Le domande si costruiscono nel browser dai numeri di `quartieri.json`: più bambini o over 65, più donne o uomini, sopra/sotto Milano, posizione in classifica, metà alta della classifica, classifica migliore tra tre, cittadinanza straniera più numerosa, residenti, ordine con due altri quartieri. Si usa una misura solo se il quartiere è nella sua classifica (r non vuoto). I quartieri quasi vuoti o sotto i 1.000 residenti non sono nell'elenco.
Controlli in `quartieri_gioco.py`: le età sommate danno i residenti della pagina Età; residenti, età media, over 65 e stranieri delle schede sono uguali a quelli delle pagine Età e Le comunità.

## Verifica a mano (10/11/2026)
30 domande estratte a caso (seme 30) rilette contro le pagine: tutte giuste. Corrette durante il controllo: il record di caldo a Brera (38,3 °C è condiviso da 1902 e 2003: la domanda ora è «dopo il 2010?», falso), il testo sulle pietre d'inciampo del 2024 (43, di cui 17 per Cibeno), «anni Venti» → «dal 2020 in poi», le etichette delle quote d'età.

## Punteggio
Più o meno, vero o falso, quale quartiere, cittadinanza: 10 o 0. Numero e posizione: 10 entro il 2,5% dell'intervallo, poi giù fino a 0 al 32,5%. Anno: 10, 8, 6, 5, 3, 3, 1, 1, 1 per 0…8 anni di scarto. Ordine: 10 tutto giusto, 3 se uno è al suo posto.
