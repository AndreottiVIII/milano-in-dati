"""Scrive (o riscrive) la sezione 'Fase 3 - taratura' in fondo a NOTE.md. Uso: python -I f3_note.py <ABS strand>"""
import sys, json, re
import pandas as pd
S = sys.argv[1]
J = json.load(open(S + '/out/f3_taratura.json', encoding='utf-8'))
p, q = J['parametri'], J['prima']; E = J['errori']
f = lambda x: ('%g' % x).replace('.', ',')
bk, bq = p['bike_kmh'], q['bike_kmh']
L = []
L.append('<!-- FASE3 -->')
L.append('## Fase 3 - taratura con Google Maps e risultati (29 ottobre 2026; riscritta da `scripts\\f3_note.py`)')
L.append('')
L.append("Taratura fatta con i tragitti di prova che hanno i tempi di Google Maps letti il 29/10/2026 per martedi 3/11/2026 (file: %s). Tragitti usati: **%d** (con valore Google: bici %d, auto %d, mezzi %d); ore 08:00 = %d, 12:00 = %d, 21:00 = %d. Divisione 70/30 per ora e distanza: **%d di taratura** (scelta dei parametri) e **%d di controllo** (solo per misurare l'errore, non toccati dalla taratura). Google e' un riferimento, non la verita': i suoi tempi di auto sono intervalli (\"tipicamente X-Y min\", usato il valore di mezzo), la bici e' un percorso consigliato, i mezzi sono il primo percorso proposto. I tempi di Google non sono pubblicati, solo i nostri errori in percentuale." % (', '.join('`%s`' % x for x in J['file']), J['n_tragitti'], J['n_con_google']['bici'], J['n_con_google']['auto'], J['n_con_google']['mezzi'], J['n_per_ora']['08'], J['n_per_ora']['12'], J['n_per_ora']['21'], J['n_taratura'], J['n_controllo']))
L.append('')
L.append("### Cosa e' cambiato (valore vecchio -> valore nuovo, perche)")
L.append('| Parametro | Prima | Dopo | Perche |')
L.append('|---|---|---|---|')
L.append("| Bici su strada normale (km/h) | %s | %s | la nostra bici era sempre piu lenta di Google (rapporto mediano %s). Velocita su strada cercata tra 14 e 18 km/h: la prima per cui il rapporto mediano sui tragitti di taratura sta tra 0,95 e 1,05 (regola in `f3_calibra.py`) |" % (f(bq[1]), f(bk[1]), f(E['prima']['bici']['tutti']['rapporto_mediano'])))
L.append('| Bici su ciclabile o corsia (km/h) | %s | %s | strada + 2 km/h |' % (f(bq[0]), f(bk[0])))
L.append('| Bici su strada di servizio (km/h) | %s | %s | strada - 1 km/h |' % (f(bq[2]), f(bk[2])))
L.append('| Attesa media a un semaforo, bici (s) | %s | %s | la bici supera spesso le code e prende scorciatoie; si prova prima 6 s, poi 4 s, poi 2 s se la velocita da sola non basta |' % (f(q['bike_signal_s']), f(p['bike_signal_s'])))
L.append("| Attraversamento senza semaforo di strada grande, bici (s) | %s | %s | meta dell'attesa al semaforo |" % (f(q['bike_major_cross_s']), f(p['bike_major_cross_s'])))
L.append('| Bici: pedonale pedalabile, a mano, sterrato (km/h) | 10, 5, 10 | 10, 5, 10 | invariati (pochi tratti) |')
L.append("| Bici: lucchetto | 60 s | 60 s | invariato (Google non lo conta, il confronto con Google e' sulla sola pedalata) |")
L.append('| Auto: fattore di velocita ore 08:00 | %s | %s | invariato: ancorato a TomTom (38 min 43 s ogni 10 km) |' % (f(q['car_scale'][0]), f(p['car_scale'][0])))
L.append("| Auto: fattore di velocita ore 12:00 | %s | %s | prima era un'ipotesi (27 min ogni 10 km). Un moltiplicatore comune alle ore 12 e 21 portato a rapporto mediano 1 sui tragitti di taratura (esclusi quelli con meta a meno di 1 km, dove Google gira largo per le zone chiuse) |" % (f(q['car_scale'][1]), f(p['car_scale'][1])))
L.append('| Auto: fattore di velocita ore 21:00 | %s | %s | idem |' % (f(q['car_scale'][2]), f(p['car_scale'][2])))
L.append('| Mezzi: margine per cambiare mezzo (s) | %s | %s | i nostri mezzi erano ottimisti (Google propone il primo percorso, non il piu veloce in assoluto) |' % (f(q['transit_slack_s']), f(p['transit_slack_s'])))
L.append("| Mezzi: tempo per scendere/salire al binario di metro e treno (s, all'inizio e alla fine) | %s | %s | la fermata del GTFS e' il binario, ma si parte dalla strada. Scelto con una griglia (margine 45-180 s x accesso 0-120 s) minimizzando errore medio + distorsione |" % (f(q['station_access_s']), f(p['station_access_s'])))
L.append('| Mezzi: velocita a piedi, distanza massima a piedi | 4,5 km/h; 800 m / 300 m (400 m tra due stazioni, vedi correzioni mezzi) | invariati | non modificati: cambiano poco il risultato e sono scelte di principio |')
L.append('')
L.append('### Errori prima e dopo (nostra stima / Google: 1,00 = uguale; errore in % del tempo Google)')
L.append('| Mezzo | Gruppo | N | Rapporto mediano prima | dopo | Errore mediano prima | dopo | Errore medio prima | dopo |')
L.append('|---|---|---|---|---|---|---|---|---|')
for mod, nm in [('bici', 'Bici'), ('auto', 'Auto (solo guida)'), ('mezzi', 'Mezzi')]:
    for gr in ('taratura', 'controllo', 'tutti'):
        a, b = E['prima'][mod][gr], E['dopo'][mod][gr]
        L.append('| %s | %s | %d | %s | %s | %s%% | %s%% | %s%% | %s%% |' % (nm, gr, b['n'], f(a['rapporto_mediano']), f(b['rapporto_mediano']), f(a['errore_mediano_pct']), f(b['errore_mediano_pct']), f(a['errore_medio_pct']), f(b['errore_medio_pct'])))
L.append('')
L.append('Auto per ora di partenza (tutti i tragitti), rapporto mediano prima -> dopo: ' + '; '.join('%s:00 = %s -> %s (N=%d)' % (b, f(E['prima']['auto']['ore_' + b]['rapporto_mediano']), f(E['dopo']['auto']['ore_' + b]['rapporto_mediano']), E['dopo']['auto']['ore_' + b]['n']) for b in ('08', '12', '21')) + '.')
L.append('')
L.append("Attenzione: con pochi tragitti per ora (vedi N) l'errore sul gruppo di controllo e' molto incerto. Nella taratura 12:00 e 21:00 l'auto diventa lenta quasi quanto alle 08:00 sulle strade principali: probabilmente il valore di mezzo dell'intervallo di Google e' pessimista per le ore tranquille; con il valore basso l'auto vincerebbe di piu.")
L.append('')
try:
    q_ = pd.read_csv(S + '/out/quote_vittorie.csv', sep=';', encoding='utf-8-sig')
    L.append('### Risultati generali dopo la taratura (tutte le coppie cella-cella: 2.915 x 2.915 celle da 250 m, martedi 3/11/2026)')
    L.append("Chi arriva prima porta a porta (bici con 1 min di lucchetto; auto con 2+2 min a piedi e ricerca del parcheggio; mezzi con attesa vera). Non conta il costo. Le celle senza fermate entro 800 m non danno vittorie ai mezzi.")
    for fa in q_.fascia_oraria.unique():
        L.append('')
        L.append('**Ore %s**' % fa)
        L.append('| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | a piedi batte tutti % | mezzi non raggiungibili % |')
        L.append('|---|---|---|---|---|---|---|---|')
        for r in q_[q_.fascia_oraria == fa].itertuples():
            L.append('| %s | %d | %s | %s | %s | %s | %s | %s |' % (r.distanza_in_linea_retta, r.coppie, f(r.bici_pct), f(r.auto_pct), f(r.mezzi_pct), f(r.netta_10pct_pct), f(r.a_piedi_batte_tutti_pct), f(r.mezzi_non_raggiungibili_pct)))
except Exception as e:
    L.append('(tabelle generali non ancora calcolate: %s)' % e)
try:
    QJ = json.load(open(S + '/../docs/bici-auto-mezzi/data/quote.json', encoding='utf-8'))
    L.append('')
    L.append("### Sensibilita alla velocita della bici (tutte le coppie; auto e mezzi invariati)")
    L.append("Il risultato dipende molto dalla velocita della bici: la taratura su Google porta a circa 17-18 km/h su strada (veloce per una bici normale). Quote di vittoria su tutte le coppie:")
    L.append('| Bici | ore | bici % | auto % | mezzi % |')
    L.append('|---|---|---|---|---|')
    for nm, rows_ in [('come tarata (%s km/h su strada, semaforo %s s)' % (f(bk[1]), f(p['bike_signal_s'])), QJ['quote']), (QJ['sens_param']['media'], QJ['sens']['media']), (QJ['sens_param']['lenta'], QJ['sens']['lenta'])]:
        for r in rows_:
            if r['distanza_in_linea_retta'] == 'tutte':
                L.append('| %s | %s | %s | %s | %s |' % (nm, r['fascia_oraria'], f(r['bici_pct']), f(r['auto_pct']), f(r['mezzi_pct'])))
except Exception as e:
    L.append('(sensibilita non disponibile: %s)' % e)
L.append('')
L.append('I risultati della "Fase 2" in questo file (sezione 4) sono i primi, prima della taratura: valgono questi.')
L.append('')
L.append('Come rifare tutto: `STATO.md` (una riga: `scripts\\f3_rifai.py`). Dati della pagina: `docs\\bici-auto-mezzi\\data\\`.')
L.append('<!-- /FASE3 -->')
txt = '\n'.join(L) + '\n'
n = open(S + '/NOTE.md', encoding='utf-8').read()
if '<!-- FASE3 -->' in n:
    n = re.sub(r'<!-- FASE3 -->.*<!-- /FASE3 -->\n?', lambda m: txt, n, flags=re.S)
else:
    n = n.rstrip('\n') + '\n\n---\n\n' + txt
open(S + '/NOTE.md', 'w', encoding='utf-8').write(n)
print('NOTE.md aggiornato')
