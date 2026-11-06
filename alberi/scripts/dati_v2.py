"""Dati nuovi per la pagina Alberi (v2): alberi per via/parco/giardino e per quartiere, divisi per genere.
Uso: python -I -X utf8 dati_v2.py <alberi> <milano-in-dati>
Legge alberi/pulito/alberi.csv (edizione 2025), scrive in docs/alberi/data/: vie_2025.json e quartieri_generi_2025.json."""
import csv, sys, os, re, json, collections
csv.field_size_limit(10**9)
A, P = sys.argv[1], sys.argv[2]
TOP = ['Acer','Platanus','Tilia','Prunus','Celtis','Quercus','Fraxinus','Ulmus']
IX = {g:i for i,g in enumerate(TOP)}
def norm(s):
    s = re.sub(r'\s+n\.\s*.*$', '', s.strip())
    s = re.sub(r'\s+', ' ', s).strip(' ,-')
    return s
vie = collections.defaultdict(lambda: {'n':0,'g':[0]*9,'gen':collections.Counter(),'sp':collections.Counter(),'nil':collections.Counter()})
nil = collections.defaultdict(lambda: [0]*9)
r = csv.DictReader(open(os.path.join(A,'pulito','alberi.csv'),encoding='utf8'), delimiter=';')
for x in r:
    if not x['edizione'].startswith('2025'): continue
    g = IX.get(x['genere'], 8)
    nm = norm(x['localita'])
    if not nm: continue
    v = vie[nm]; v['n'] += 1; v['g'][g] += 1
    v['gen'][x['genere']] += 1
    v['sp'][x['nome_comune'] or x['specie_binomio_normalizzata']] += 1
    if x['id_nil']: v['nil'][x['id_nil']] += 1
    if x['id_nil']: nil[x['id_nil']][g] += 1
gen_nomi = {}
for l in csv.DictReader(open(os.path.join(P,'docs','alberi','data','generi_2025.csv'),encoding='utf8'), delimiter=';'):
    gen_nomi[l['genere']] = l['nome']
G = []; GI = {}
def gid(g):
    if g not in GI: GI[g] = len(G); G.append([g, gen_nomi.get(g, g)])
    return GI[g]
S = []; SI = {}
def sid(s):
    if s not in SI: SI[s] = len(S); S.append(s)
    return SI[s]
out = []
for nm, v in sorted(vie.items(), key=lambda kv: -kv[1]['n']):
    t3 = [[gid(g), c] for g, c in v['gen'].most_common(3)]
    s3 = [[sid(s), c] for s, c in v['sp'].most_common(3)]
    nid = int(v['nil'].most_common(1)[0][0]) if v['nil'] else None
    out.append([nm, v['n'], nid, v['g'], t3, s3])
json.dump({'top':TOP,'generi':G,'specie':S,'vie':out}, open(os.path.join(P,'docs','alberi','data','vie_2025.json'),'w',encoding='utf8'), ensure_ascii=False, separators=(',',':'))
json.dump({'top':TOP,'nil':{k:v for k,v in nil.items()}}, open(os.path.join(P,'docs','alberi','data','quartieri_generi_2025.json'),'w',encoding='utf8'), ensure_ascii=False, separators=(',',':'))
print(len(out), 'luoghi;', sum(o[1] for o in out), 'alberi')
