"""RSA di Milano e hinterland + over 80: scrive i dati della pagina in docs/anziani/data/.
Uso: python -I -X utf8 anz_02_elabora.py <cartella progetto>
Entrate: anziani/raw/rsa.csv, anziani/raw/adi.csv, docs/eta/data/{eta_singola_nil_2025.json,nil.geojson},
         hinterland/raw/posas/POSAS_2026_it_Comuni.zip (ISTAT, 1/1/2026)."""
import sys, os, csv, io, json, zipfile, collections, shutil
R = sys.argv[1]
OUT = os.path.join(R, 'docs', 'anziani', 'data'); os.makedirs(OUT, exist_ok=True)
def wj(n, o):
    p = os.path.join(OUT, n); open(p, 'w', encoding='utf-8').write(json.dumps(o, ensure_ascii=False, separators=(',', ':')))
    assert os.path.getsize(p) < 2_000_000
MI = '015146'
rs = list(csv.DictReader(open(os.path.join(R, 'anziani/raw/rsa.csv'), encoding='utf-8')))
for x in rs:
    x['pa'] = int(x['TOT_POSTI_AUTORIZZATI'] or 0); x['pc'] = int(x['TOT_POSTI_ACCREDITATI'] or 0)
# --- over 80 per comune (ISTAT POSAS 1/1/2026)
z = zipfile.ZipFile(os.path.join(R, 'hinterland/raw/posas/POSAS_2026_it_Comuni.zip'))
rows = [r for r in csv.reader(io.TextIOWrapper(z.open('POSAS_2026_it_Comuni.csv'), encoding='utf-8-sig'), delimiter=';') if len(r) >= 6][1:]
o80 = collections.Counter(); nome = {}
for r in rows:
    if r[2] == '999': continue
    nome[r[0]] = r[1]
    if int(r[2]) >= 80: o80[r[0]] += int(r[5])
pa = collections.Counter(); nr = collections.Counter(); pub = collections.Counter()
for x in rs:
    c = x['COD_ISTAT_COMUNE_UBICAZIONE']; assert c in o80, c
    pa[c] += x['pa']; nr[c] += 1
    if x['PUBBLICA_PRIVATA'] == 'PUBBLICA': pub[c] += x['pa']
# --- comuni della Città metropolitana (codici 015xxx, Milano a parte)
com = [dict(cod=c, nome=nome[c], o80=o80[c], posti=pa[c], rsa=nr[c]) for c in o80 if c.startswith('015') and c != MI]
com.sort(key=lambda d: -d['o80'])
mil = dict(cod=MI, nome='Milano', o80=o80[MI], posti=pa[MI], rsa=nr[MI], pub=pub[MI])
wj('comuni.json', dict(milano=mil, comuni=com))
# --- province lombarde
PROV = {'012': 'Varese', '013': 'Como', '014': 'Sondrio', '015': 'Milano', '016': 'Bergamo', '017': 'Brescia', '018': 'Pavia',
        '019': 'Cremona', '020': 'Mantova', '097': 'Lecco', '098': 'Lodi', '108': 'Monza e Brianza'}
pv = []
for k, n in PROV.items():
    cs = [c for c in o80 if c.startswith(k)]
    pv.append(dict(cod=k, nome=n, o80=sum(o80[c] for c in cs), posti=sum(pa[c] for c in cs), rsa=sum(nr[c] for c in cs),
                   pub=sum(pub[c] for c in cs), comuni=len(cs), senza=sum(1 for c in cs if pa[c] == 0)))
wj('province.json', pv)
# --- RSA di Milano con quartiere (punto nel poligono)
gj = json.load(open(os.path.join(R, 'docs/eta/data/nil.geojson'), encoding='utf-8'))
def inring(x, y, ring):
    ins = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]; xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: ins = not ins
        j = i
    return ins
def inpoly(x, y, g):
    polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    for p in polys:
        if inring(x, y, p[0]) and not any(inring(x, y, h) for h in p[1:]): return True
    return False
def nil_of(lon, lat):
    for f in gj['features']:
        if inpoly(lon, lat, f['geometry']): return f['properties']['i']
    return None
lista = []
for x in rs:
    if x['COD_ISTAT_COMUNE_UBICAZIONE'] != MI: continue
    lat, lon = float(x['WGS84_Y']), float(x['WGS84_X'])
    lista.append(dict(n=' '.join(x['DENOM_STRUTTURA'].split()), g=' '.join(x['DENOM_GESTORE'].split()), lat=lat, lon=lon,
                      pa=x['pa'], pc=x['pc'], pub=x['PUBBLICA_PRIVATA'] == 'PUBBLICA', nil=nil_of(lon, lat), ind=' '.join(x['INDIRIZZO_UBICAZIONE'].split())))
assert all(r['nil'] for r in lista), [r['n'] for r in lista if not r['nil']]
lista.sort(key=lambda r: -r['pa'])
wj('rsa_milano.json', lista)
# --- over 80 per quartiere (anagrafe del Comune, 31/12/2025) + posti
et = json.load(open(os.path.join(R, 'docs/eta/data/eta_singola_nil_2025.json'), encoding='utf-8'))['nil']
nilp = collections.Counter(); niln = collections.Counter()
for r in lista: nilp[str(r['nil'])] += r['pa']; niln[str(r['nil'])] += 1
nl = []
for k, v in et.items():
    tot = sum(v['F']) + sum(v['M']); o = sum(v['F'][80:]) + sum(v['M'][80:])
    nl.append(dict(i=int(k), n=v['n'], pop=tot, o80=o, posti=nilp[k], rsa=niln[k]))
nl.sort(key=lambda d: d['i'])
wj('quartieri.json', nl)
shutil.copy(os.path.join(R, 'docs/eta/data/nil.geojson'), os.path.join(OUT, 'nil.geojson'))
# --- gestori di Milano
gs = collections.defaultdict(lambda: dict(pa=0, n=0, pub=False))
for r in lista:
    d = gs[r['g']]; d['pa'] += r['pa']; d['n'] += 1; d['pub'] = d['pub'] or r['pub']
gl = sorted(({'g': k, **v} for k, v in gs.items()), key=lambda d: -d['pa'])
wj('gestori.json', gl)
# --- ADI (solo conteggio dei servizi a Milano)
adi = list(csv.DictReader(open(os.path.join(R, 'anziani/raw/adi.csv'), encoding='utf-8'), delimiter=';'))
# --- riepilogo
meta = json.load(open(os.path.join(R, 'anziani/raw/rsa_meta.json'), encoding='utf-8'))
import datetime
agg = datetime.datetime.fromtimestamp(meta['rowsUpdatedAt']).strftime('%Y-%m-%d')
hin_o = sum(d['o80'] for d in com); hin_p = sum(d['posti'] for d in com)
wj('riepilogo.json', dict(
    rsa_aggiornato=agg, over80_data='1/1/2026', rsa_righe=len(rs),
    milano=mil, hinterland=dict(comuni=len(com), senza=sum(1 for d in com if d['posti'] == 0), o80=hin_o, posti=hin_p, rsa=sum(d['rsa'] for d in com)),
    nil_o80_tot=sum(d['o80'] for d in nl), nil_pop_tot=sum(d['pop'] for d in nl), adi_milano=len(adi),
    accreditati_milano=sum(r['pc'] for r in lista)))
def wc(n, head, rows_):
    with open(os.path.join(OUT, n), 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';'); w.writerow(head); w.writerows(rows_)
wc('rsa_milano.csv', ['struttura', 'gestore', 'indirizzo', 'quartiere_n', 'posti_autorizzati', 'posti_accreditati', 'pubblica'], [[r['n'], r['g'], r['ind'], r['nil'], r['pa'], r['pc'], 'si' if r['pub'] else 'no'] for r in lista])
wc('quartieri.csv', ['nil', 'quartiere', 'residenti_2025', 'over80_2025', 'posti_rsa', 'rsa'], [[d['i'], d['n'], d['pop'], d['o80'], d['posti'], d['rsa']] for d in nl])
wc('comuni.csv', ['codice_istat', 'comune', 'over80_2026', 'posti_rsa', 'rsa'], [[mil['cod'], 'Milano', mil['o80'], mil['posti'], mil['rsa']]] + [[d['cod'], d['nome'], d['o80'], d['posti'], d['rsa']] for d in com])
wc('province.csv', ['provincia', 'over80_2026', 'posti_rsa', 'rsa', 'rsa_pubbliche_posti'], [[p['nome'], p['o80'], p['posti'], p['rsa'], p['pub']] for p in pv])
print('ok')
