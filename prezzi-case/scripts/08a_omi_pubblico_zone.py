r"""Passo 1 della raccolta delle quotazioni OMI dal servizio PUBBLICO di consultazione (GEOPOI), senza login.
La pagina dei risultati (stampaomi.php) cerca per LINK_ZONA + semestre (il codice zona e' solo decorativo). Il legame codice zona -> LINK_ZONA
si chiede con zoneomi.php?richiesta=8&codcom=F205&semestre=<S>&zo=<codice> (la stessa chiamata della mappa quando si clicca una zona):
risponde solo se la zona esiste in quel semestre.
Qui si interroga, per il primo e l'ultimo semestre di ogni periodo di zonizzazione (P1..P7 di zone_periodi.csv), ogni codice zona dei perimetri,
poi per 2004/1, 2006/1, 2008/1, 2010/1 i codici del 2010/2, poi (fase 'enum') tutti i codici possibili a 2008/1 per cercare zone
esistite solo prima del 2010. Una richiesta alla volta, pausa 3 s, cache in raw\omi_pubblico_cache\r8\<S>_<codice>.json, riprendibile.
Uscita: raw\omi_pubblico_cache\zone_link_map.json  {semestre: {codice: [LINK_ZONA,...]}}
Uso: python -I 08a_omi_pubblico_zone.py <cartella prezzi-case>
"""
import os, sys, json, time, glob, urllib.request

base = sys.argv[1]
C = os.path.join(base, 'raw', 'omi_pubblico_cache')
os.makedirs(os.path.join(C, 'r8'), exist_ok=True)
URL = 'https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/zoneomi.php?richiesta=8&codcom=F205&semestre=%s&zo=%s'
UA = 'Mozilla/5.0 (research; milano-in-dati; polite; 1 req/3s)'
PAUSA = 3.0

geo = {}
for f in sorted(glob.glob(os.path.join(base, 'raw', 'geopoi', 'F205_*.json'))):
    geo[os.path.basename(f)[5:10]] = [ft['properties']['zona'] for ft in json.load(open(f, encoding='utf-8'))['dat']['features']]

plan = []
for s in ['20102', '20132', '20141', '20142', '20192', '20201', '20202', '20212', '20221', '20241', '20242', '20261']:
    plan += [(s, z) for z in geo[s]]
for s in ['20101', '20081', '20061', '20041']:
    plan += [(s, z) for z in geo['20102']]
enum = []
conosciuti = set(geo['20102'])
for L, rng in (('B', 45), ('C', 45), ('D', 60), ('E', 45), ('R', 9), ('A', 9)):
    for n in range(1, rng + 1):
        for z in ([f'{L}{n}', f'{L}{n:02d}'] if n < 10 else [f'{L}{n}']):
            if z not in conosciuti:
                enum.append(('20081', z))
print(len(plan), 'richieste di piano +', len(enum), 'di enumerazione', flush=True)


def chiedi(s, z):
    p = os.path.join(C, 'r8', f'{s}_{z}.json')
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return json.loads(open(p, encoding='utf-8').read())
    for tent in range(4):
        try:
            req = urllib.request.Request(URL % (s, z), headers={'User-Agent': UA})
            txt = urllib.request.urlopen(req, timeout=60).read().decode('utf-8')
            d = json.loads(txt)
            break
        except Exception as e:
            print('errore', s, z, e, flush=True)
            if getattr(e, 'code', None) in (403, 429):
                print('STOP: blocco'); sys.exit(2)
            time.sleep(15 * (tent + 1))
    else:
        sys.exit('troppi errori')
    open(p, 'w', encoding='utf-8').write(txt)
    time.sleep(PAUSA)
    return d


def salva(mappa):
    json.dump(mappa, open(os.path.join(C, 'zone_link_map.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True)


mappa = {}
for i, (s, z) in enumerate(plan + enum):
    d = chiedi(s, z)
    if d:
        mappa.setdefault(s if i < len(plan) else s + '_enum', {})[z] = sorted({r['LINK_ZONA'] for r in d})
    if i % 50 == 0:
        print(time.strftime('%H:%M:%S'), i, s, z, flush=True)
        salva(mappa)
    if i == len(plan) - 1:
        salva(mappa)
        print('PIANO FATTO', flush=True)
salva(mappa)
print('FATTO', {k: len(v) for k, v in mappa.items()})
