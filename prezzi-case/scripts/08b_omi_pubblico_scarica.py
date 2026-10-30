r"""Passo 2: scarica dal servizio PUBBLICO di consultazione OMI (GEOPOI, www1.agenziaentrate.gov.it/servizi/geopoi_omi/stampaomi.php,
la pagina "Banca dati delle quotazioni immobiliari - Risultato" che si apre cliccando una zona sulla mappa) le quotazioni di Milano (F205).
Nessun login. Una richiesta alla volta, pausa PAUSA secondi, ogni risposta salvata cosi' com'e' in
  raw\omi_pubblico_cache\stampa\<AAAAS>_<LINK_ZONA>_<T>.html   (T = R residenziale, C commerciale, T terziaria, P produttiva)
Riprendibile: salta cio' che c'e' gia'. Si ferma se compare un blocco (403/429/captcha) o troppi errori di fila.
Ordine: prima tutte le R, poi le C, poi T e P solo per le zone/semestri dove R o C hanno dato righe.
Uso: python -I 08b_omi_pubblico_scarica.py <cartella prezzi-case> [pausa_s]
"""
import os, sys, json, time, glob, re, csv, urllib.request

base = sys.argv[1]
PAUSA = float(sys.argv[2]) if len(sys.argv) > 2 else 2.5
C = os.path.join(base, 'raw', 'omi_pubblico_cache')
S = os.path.join(C, 'stampa')
os.makedirs(S, exist_ok=True)
UA = 'Mozilla/5.0 (research; milano-in-dati; polite; 1 req/%ss)' % PAUSA
BASE = 'https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/stampaomi.php?'

mp = json.load(open(os.path.join(C, 'zone_link_map.json'), encoding='utf-8'))  # semestre -> codice -> [LINK_ZONA]
geo = {}
for f in sorted(glob.glob(os.path.join(base, 'raw', 'geopoi', 'F205_*.json'))):
    geo[os.path.basename(f)[5:10]] = [ft['properties']['zona'] for ft in json.load(open(f, encoding='utf-8'))['dat']['features']]
sems = [f'{a}{s}' for a in range(2004, 2027) for s in (1, 2) if '20041' <= f'{a}{s}' <= '20261']
# periodi di zonizzazione (zone_periodi.csv): per un semestre si usa la mappa codice->link dell'ultimo semestre interrogato <= semestre, dentro lo stesso periodo
per = []
for r in csv.DictReader(open(os.path.join(base, 'pulito', 'zone_periodi.csv'), encoding='utf-8')):
    per.append((r['periodo'], r['primo_semestre'].replace('-S', ''), r['ultimo_semestre'].replace('-S', '')))
def periodo(s):
    for p, a, b in per:
        if a <= s <= b:
            return p, a
    return 'PRE', '20041'
qs = sorted(k for k in mp if not k.endswith('_enum'))
extra = sorted(mp.get('20081_enum', {}))   # codici esistiti nel 2008/1 e non nel 2010/2
def mappa_sem(s):
    p, a = periodo(s)
    cand = [q for q in qs if a <= q <= s]
    m = dict(mp[cand[-1]]) if cand else {}
    if s < '20102':
        m.update(mp.get('20081_enum', {}))
    return m
jobs = []  # (sem, zona, link)
nolink = []
for s in sems:
    codici = geo[s] if s in geo else sorted(set(geo['20102']) | set(extra))
    m = mappa_sem(s)
    for z in codici:
        if z not in m:
            nolink.append((s, z)); continue
        for l in m[z]:
            jobs.append((s, z, l))
json.dump({'jobs': jobs, 'senza_link': nolink}, open(os.path.join(C, 'jobs.json'), 'w'), indent=0)
print(len(jobs), 'coppie semestre-zona;', len(nolink), 'senza link (vedi jobs.json)', flush=True)


def path(s, link, t):
    return os.path.join(S, f'{s}_{link}_{t}.html')


def righe(p):
    t = open(p, encoding='utf-8', errors='replace').read()
    return len(re.findall(r"<tr><td id='sin'>", t))


def scarica(s, z, link, t):
    p = path(s, link, t)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return False
    url = BASE + '/'.join(['F205', link, s, t, z, '9.19', '45.46'])
    for tent in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            r = urllib.request.urlopen(req, timeout=60)
            b = r.read()
            txt = b.decode('utf-8', errors='replace')
            if 'captcha' in txt.lower() or 'access denied' in txt.lower() or 'robot' in txt.lower()[:3000]:
                print('STOP: possibile blocco/captcha su', url, flush=True)
                open(p + '.BLOCCO', 'wb').write(b)
                sys.exit(3)
            if 'Risultato interrogazione' not in txt:
                raise ValueError('risposta inattesa (%d byte)' % len(b))
            open(p + '.tmp', 'wb').write(b)
            os.replace(p + '.tmp', p)
            time.sleep(PAUSA)
            return True
        except SystemExit:
            raise
        except Exception as e:
            code = getattr(e, 'code', None)
            print('errore', s, z, t, e, 'tentativo', tent + 1, flush=True)
            if code in (403, 429):
                print('STOP: blocco', code, flush=True)
                sys.exit(3)
            time.sleep(20 * (tent + 1))
    print('STOP: troppi errori', flush=True)
    sys.exit(4)


n = 0
t0 = time.time()
for passo in ('R', 'C', 'TP'):
    for (s, z, link) in jobs:
        if passo in ('R', 'C'):
            tipi = [passo]
        else:
            rr = [path(s, link, 'R'), path(s, link, 'C')]
            if not any(os.path.exists(x) and righe(x) > 0 for x in rr):
                continue
            tipi = ['T', 'P']
        for t in tipi:
            if scarica(s, z, link, t):
                n += 1
                if n % 50 == 0:
                    print(f'{time.strftime("%H:%M:%S")} passo {passo} scaricate {n} (ultima {s} {z} {t}), {(time.time()-t0)/n:.1f} s/richiesta', flush=True)
    print('FINITO passo', passo, flush=True)
print('FATTO TUTTO, richieste nuove:', n)
