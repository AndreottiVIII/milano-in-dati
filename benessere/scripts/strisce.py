"""Scrive docs/benessere/data/strisce.json: i dati del grafico a strisce (posto di Milano su 107 province, indicatore per indicatore).

Uso (percorso assoluto della cartella docs, si puo' rilanciare):
  python -I -X utf8 strisce.py <docs_dir>

Legge solo docs/benessere/data/: milano_posizione_ultimo_anno.csv, cm14_ultimo_anno.csv, riepilogo.json.
Entrano nel grafico gli indicatori con direzione scritta da Istat (istat, istat_testo), con posto su 107 e senza avviso.
Gli altri sono elencati in "esclusi", con il motivo, cosi' la pagina puo' dire perche' i confrontabili sono meno del totale."""
import sys, os, csv, json, collections

DOCS = sys.argv[1]
B = os.path.join(DOCS, 'benessere', 'data')


def rd(f):
    return list(csv.DictReader(open(os.path.join(B, f), encoding='utf-8-sig')))


pos = rd('milano_posizione_ultimo_anno.csv')
cm = rd('cm14_ultimo_anno.csv')
riep = json.load(open(os.path.join(B, 'riepilogo.json'), encoding='utf-8'))
dec = {i['cod']: i['dec'] for dm in riep['domini'] for i in dm['indicatori']}

altre = collections.defaultdict(list)
for r in cm:
    if r['citta_metropolitana'] != 'Milano' and r['rango_107']:
        altre[r['codice']].append((r['citta_metropolitana'], int(float(r['rango_107']))))

ind, esclusi, domini = [], [], []
for r in pos:
    if r['dominio'] not in domini:
        domini.append(r['dominio'])
    if r['livello_polarita'] in ('istat', 'istat_testo') and r['rango_107'] and not r['avviso']:
        ind.append(dict(c=r['codice'], d=r['dominio'], n=r['indicatore'], u=r['unita'], pol=r['polarita'], a=int(float(r['anno_ultimo'])),
                        k=int(float(r['n_province'])), r=int(float(r['rango_107'])), r14=int(float(r['rango_14'])),
                        vm=float(r['valore_milano']), vi=float(r['valore_italia']), dec=dec.get(r['codice'], 1),
                        o=sorted(altre[r['codice']], key=lambda t: t[1])))
    else:
        if not r['rango_107']:
            g = 'senza'      # nessun posto in classifica tra le 107 province, o direzione assente/dubbia
        elif r['avviso']:
            g = 'confronto'  # valore dell'Italia non confrontabile con quello delle province
        else:
            g = 'derivata'   # direzione ricavata da noi, non scritta da Istat
        esclusi.append(dict(n=r['indicatore'], g=g))

ordine = {d: i for i, d in enumerate(domini)}
ind.sort(key=lambda i: (ordine[i['d']], i['r'] / i['k']))
out = dict(n_tot=len(pos), n=len(ind), domini=domini, ind=ind, esclusi=esclusi)
json.dump(out, open(os.path.join(B, 'strisce.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
top = sum(1 for i in ind if i['r'] <= i['k'] / 3)
bot = sum(1 for i in ind if i['r'] > 2 * i['k'] / 3)
print('ok', len(ind), 'su', len(pos), 'terzo migliore', top, 'terzo peggiore', bot, 'esclusi', collections.Counter(e['g'] for e in esclusi))
