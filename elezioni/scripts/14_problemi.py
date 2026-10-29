"""Compone pulito/problemi.md dal log automatico di 13_pulizia.py + note manuali.
uso: python -I 14_problemi.py <cartella elezioni> <cartella lavoro con problemi_auto.json>
"""
import sys, os, json, collections

base, work = sys.argv[1], sys.argv[2]
P = json.load(open(os.path.join(work, 'problemi_auto.json'), encoding='utf-8'))
by = collections.defaultdict(list)
for p in P:
    by[p['codice']].append(p)

L = []
w = L.append
w('# Problemi dei dati e correzioni (fase 2)\n')
w('Ogni voce e una "trappola dei dati". Le righe marcate (auto) sono prodotte dallo script `scripts\\13_pulizia.py` mentre pulisce; le altre sono note scritte a mano dopo il controllo. I dataset sono indicati con il numero `dsNNNN` del portale del Comune di Milano.\n')
w('## Cosa contiene il dataset pulito\n')
w('- `elezioni.csv`: una riga per consultazione (157: 138 usate nel sito + 19 tenute ma non usate perche senza famiglie, vedi colonna `nota_sito`). Campi: id, gruppo, data corretta, sistema territoriale, dataset di origine.')
w('- `risultati_sezione.csv`: una riga per sezione e consultazione (elettori, votanti, validi, non validi, Si/No per i referendum, territorio, flag).')
w('- `voti_sezione.csv`: una riga per sezione, consultazione e lista (o candidato, o Si/No). Il territorio e quello del file risultati (controllo: coincide con quello del file voti in tutte le righe).\n')

w('## 1. Date sbagliate o non-date\n')
w('**Ballottaggi (auto).** Il campo `Sessione` porta la data del primo turno. Date messe: 1993-06-20, 1997-05-11, 2011-05-29, 2016-06-19, e 2009-06-21 per il ballottaggio provinciale. Le date 2011 e 2016 sono confermate dai titoli dei dataset di sedi (ds1111: "Ballottaggio del 29-30/5/2011", ds1117: "19/6/2016"); **1993, 1997 e 2009 vengono dal calendario elettorale e non da un campo del portale: da verificare** (non ho trovato nei dati una conferma).\n')
for p in by['DATA_REFERENDUM']:
    w('- (auto) %s: %s' % (p['dove'], p['cosa']))
w('')
w('Nota: il campo `Sessione` del 2021 e `03/10/2021` (primo giorno), mentre il campo `date_start` dell\'inventario di fase 1 dava 2021-10-04. Uso `Sessione`. Per le votazioni su due giorni (referendum 2020, 2025, 2026) la data e il primo giorno.\n')

w('## 2. Territorio: tre sistemi con lo stesso nome di colonna\n')
w('- Fino al 1997 la colonna e `Circoscrizione` (1-20). Dal 1999 `Zona` (1-9). Dal 2016 `Municipio` (1-9). Il numero 5 del 1997 non e il numero 5 del 1999.')
w('- (auto) Nei referendum 1985-1997 la colonna si chiama `Zona` ma contiene valori fino a 20: sono le circoscrizioni (%d file). Nel pulito il campo `sistema_territorio` dice quale dei tre sistemi vale.' % len(by['ZONA_E_CIRCOSCRIZIONE']))
w('- (auto) Nei 5 referendum del 1981 (ds1372-ds1376) la colonna `Zona` e vuota. Ho ripreso la circoscrizione dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); campo `territorio_derivato = 1`. **2 sezioni su 2.162 non si ritrovano** (restano senza territorio, contano solo nel totale della citta).')
w('- Le 9 zone 1999-2011 hanno gli stessi numeri dei municipi 2016 (2011 -> 2016: stesso numero in 1.245 sezioni su 1.245) e anche gli stessi confini: le superfici di ds153 (9 zone) e ds379 (municipi) coincidono entro lo 0,005% (`pulito\\confini_verifiche.json`).')
w('- Le 20 ex zone di decentramento (ds378, campo `ZONADEC20` 1-20) sono usate come confini delle circoscrizioni 1-20: **ipotesi** che il numero coincida (la numero 1 contiene il Duomo; la somma delle superfici e uguale a quella dei municipi). Non ho una tabella ufficiale di corrispondenza.\n')

w('## 3. Numeri che non tornano\n')
for code, title in [('ELETTORI_ZERO', 'Elettori a zero in tutto il file'), ('VOTANTI_ZERO', 'Votanti a zero o vuoto in tutto il file')]:
    w('**%s (auto).** %s: %s.' % (title, 'dataset', ', '.join(p['dove'] for p in by[code])))
    w('Nel pulito il campo e vuoto (non zero), cosi l\'affluenza risulta "non disponibile" invece di 0%.')
    w('')
w('Dove Votanti manca, Non validi e comunque 0, quindi non si puo ricostruire (Votanti = Validi + Non validi darebbe i soli validi): nel sito l\'affluenza e "n.d." per Senato 1996, Senato 2001, Provinciali 2009, Circoscrizionali 2011.\n')
tot_gt = sum(p['righe'] or 0 for p in by['VOTANTI_SOPRA_ELETTORI'])
w('**Votanti > Elettori o Elettori = 0 con Votanti > 0 (auto).** %d casi in %d dataset (elenco nel log completo). Tenuti: sono probabilmente sezioni ospedaliere o speciali. Con la somma dei file la distorsione sull\'affluenza di territorio e piccola, ma sulla singola sezione puo superare il 100%%.\n' % (tot_gt, len(by['VOTANTI_SOPRA_ELETTORI'])))
w('**Sezioni 9001-9011 (2025, auto).** Tenute, flag `sezione_speciale` nel pulito (%d file referendum 2025). Contano nei totali.\n' % len(by['SEZIONI_9001_9011']))
for p in by['LISTE_OLTRE_VALIDI']:
    w('- (auto) %s: %s' % (p['dove'], p['cosa']))
w('')

w('## 4. Voti vuoti\n')
for p in by['VOTI_VUOTI']:
    w('- (auto) %s' % p['cosa'])
w('  Sono le righe dei file ds1139, ds1144, ds1145, ds1153, ds1154 (maggioritario 1994/1996/2001, Senato 1996/2001): una riga per ogni candidato o lista in ogni sezione, vuota dove il candidato non si presentava nel collegio della sezione. Vuoto = non applicabile, non zero: le ho tolte.\n')

w('## 5. Nomi delle liste\n')
w('- Troncati a 30 caratteri (es. `Partito Comunista dei Lavorato`, `FORZA ITALIA BERLUSCONI PER BE`), abbreviati in modo diverso da un anno all\'altro (`PD`, `Part. Democratico`, `Partito Democratico`), a volte tutto maiuscolo (dal 2021 e Politiche 2022) o con refusi (`Popolo delle Liberta` nelle Comunali 2011, `Soc. Italianii`, `Io amo l\'Iitalia`). Per questo la tabella delle famiglie parte dal nome cosi com\'e nel dato.')
w('- Nelle Comunali 2016 e 2021 molte liste hanno il nome del candidato sindaco dentro (`Per Parisi Forza Italia Berl.`, `PARTITO DEMOCRATICO BEPPE SALA`): ho usato queste parole per assegnare la famiglia.')
w('- Il carattere accentato nei titoli dei dataset e gia rovinato sul portale (`Unit�`, `Indennit�`): nel sito ho corretto a mano i titoli dei quesiti.')
w('- Le Comunali, i ballottaggi e i Municipali hanno il nome del candidato nel campo `Lista` quando il file e "Sindaco" o "Presidente".\n')

w('## 6. Cosa tengo e cosa lascio fuori dal sito (ma resta nel pulito)\n')
w('Nel sito: Consiglio comunale, Sindaco (primo turno), ballottaggio, Municipali (consiglio), Circoscrizionali 2011 (liste), Camera (proporzionale per 1994-2001; "liste nel collegio uninominale" per 2018 e 2022), Senato (liste), Europee, Regionali (liste provinciali o circoscrizionali), Provinciali 2009 (consiglio), tutti i referendum (Si/No).')
w('Nel pulito ma non nel sito: Camera maggioritario 1994/1996/2001, candidati uninominali 2018/2022, Presidenti di municipio (59 nomi nel 2016), candidati presidente di regione (listini), Circoscrizionali 2011 coalizioni, Provinciali presidente e ballottaggio. Mancano di famiglia perche sono nomi di persone o coalizioni locali.')
w('Nei Comunali (Consiglio) e Municipali (Consiglio) la quota per famiglia e calcolata sui soli voti alle liste: i voti dati solo al sindaco non entrano. Nelle Politiche 2018 e 2022 i voti "solo al candidato uninominale" non sono ripartiti tra le liste (il dato del Comune non lo fa).\n')
w('## 7. Prima del 1979\n')
w('Sul portale non ci sono dati di sezione prima del 1979. Vedi `NOTE_fase2.md` per quanto offre l\'archivio storico del Ministero dell\'Interno.\n')
w('## 8. Elenco completo del log automatico\n')
w('Codice | Dove | Cosa')
w('---|---|---')
for p in P:
    w('%s | %s | %s' % (p['codice'], p['dove'], p['cosa'].replace('|', '/')))
open(os.path.join(base, 'pulito', 'problemi.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('ok', len(L))
