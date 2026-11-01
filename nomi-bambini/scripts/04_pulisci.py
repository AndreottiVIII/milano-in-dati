"""Pulisce i CSV scaricati in raw/lombardia e scrive le tabelle in pulito/.
Uso: python -I -X utf8 04_pulisci.py <cartella nomi-bambini>   (la cartella scripts/ deve essere accanto; si usa sys.path esplicito)"""
import sys, os, csv, collections
base = sys.argv[1]
sys.path.insert(0, os.path.join(base, 'scripts'))
from common import norm_nome
raw = os.path.join(base, 'raw', 'lombardia'); out = os.path.join(base, 'pulito')
os.makedirs(out, exist_ok=True)
SC = {'Italiani': 'italiana', 'Stranieri': 'straniera'}

# ---- Bergamo: nati per anno di nascita, sesso, cittadinanza (residenti oggi nati in quell'anno)
fonte = 'dati.lombardia.it 7nxs-kdhf (Comune di Bergamo, CC0), scaricato 2026-11-01'
agg = collections.OrderedDict(); n_in = 0; n_dup = 0
for x in csv.DictReader(open(os.path.join(raw, 'bergamo_nomi_neonati_7nxs-kdhf.csv'), encoding='utf8')):
    n_in += 1
    nome = x['NOME'].strip()
    k = (int(x['NASCITA_ANNO']), x['GENERE'], nome, SC[x['CITTADINANZA']])
    if k in agg: n_dup += 1
    agg[k] = agg.get(k, 0) + int(x['FREQUENZA'])
rows = []
tot_ns = collections.defaultdict(int)
for (a, s, nome, c), n in agg.items():
    rows.append((a, s, nome, norm_nome(nome), c, n))
# unione per nome normalizzato (stessa chiave anno, sesso, cittadinanza, nome_norm)
m = collections.OrderedDict()
for a, s, nome, nn, c, n in rows:
    m[(a, s, nn, c)] = m.get((a, s, nn, c), 0) + n
with open(os.path.join(out, 'nomi_nati_bergamo.csv'), 'w', encoding='utf8', newline='') as f:
    w = csv.writer(f); w.writerow(['anno', 'sesso', 'nome', 'cittadinanza', 'nati', 'fonte'])
    for (a, s, nn, c), n in sorted(m.items()):
        w.writerow([a, s, nn, c, n, 'bergamo_7nxs-kdhf'])
# tabella con i nomi originali, per controllo
with open(os.path.join(out, 'nomi_bergamo_varianti.csv'), 'w', encoding='utf8', newline='') as f:
    w = csv.writer(f); w.writerow(['nome_norm', 'varianti_originali'])
    v = collections.defaultdict(set)
    for a, s, nome, nn, c, n in rows: v[nn].add(nome)
    for nn, vs in sorted(v.items()):
        if len(vs) > 1: w.writerow([nn, ' | '.join(sorted(vs))])
print('Bergamo: righe in', n_in, 'chiavi doppie sommate', n_dup, 'righe dopo normalizzazione', len(m))

# ---- Rozzano: nomi dei nati sul territorio, 2007-2017
rz = []
for fn, s in (('rozzano_maschili_aqb5-z3e6.csv', 'M'), ('rozzano_femminili_ht8t-tug7.csv', 'F')):
    col = 'NOMI_MASCHILI' if s == 'M' else 'NOMI_FEMMINILI'
    for x in csv.DictReader(open(os.path.join(raw, fn), encoding='utf8')):
        rz.append((int(x['ANNO']), s, norm_nome(x[col]), int(x['FREQUENZA'])))
agg2 = collections.defaultdict(int)
for a, s, nn, n in rz: agg2[(a, s, nn)] += n
with open(os.path.join(out, 'nomi_nati_rozzano.csv'), 'w', encoding='utf8', newline='') as f:
    w = csv.writer(f); w.writerow(['anno', 'sesso', 'nome', 'nati', 'fonte'])
    for (a, s, nn), n in sorted(agg2.items()): w.writerow([a, s, nn, n, 'rozzano_aqb5-z3e6_ht8t-tug7'])
print('Rozzano righe', len(agg2))
