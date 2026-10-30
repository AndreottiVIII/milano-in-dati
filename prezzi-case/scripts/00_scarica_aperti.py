"""Scarica (o riprende) i dati aperti del filone prezzi-case in <cartella prezzi-case>\\raw\\. Salta i file gia' presenti.
Nessun accesso con SPID o registrazione. Pause di 2-5 secondi. Uso: python -I 00_scarica_aperti.py <cartella prezzi-case>
Cosa scarica: perimetri zone OMI Milano (servizio di mappa pubblico), NTN (zip e xls), FOI ISTAT (SDMX), copie ondata 2016-2018 (solo prova).
Le quotazioni OMI NON si scaricano qui (servono SPID, vedi COSA_SCARICARE.md).
"""
import os, sys, re, time, urllib.request, urllib.parse, json

base = sys.argv[1]
UA = 'Mozilla/5.0 (research; milano-in-dati; polite)'


def get(url, dest, headers=None, timeout=300, pausa=3):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print('gia presente', os.path.relpath(dest, base))
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
    for tentativo in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=timeout).read()
            if not data:
                raise IOError('risposta vuota')
            open(dest, 'wb').write(data)
            print('scaricato', os.path.relpath(dest, base), len(data))
            break
        except Exception as e:
            print('errore', e, 'tentativo', tentativo + 1)
            time.sleep(10 * (tentativo + 1))
    time.sleep(pausa)


# 1) perimetri zone Milano: semestri dal 2010/2 al 2026/1
G = 'https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/zoneomi.php?richiesta=6&codcom=F205&semestre='
for anno in range(2010, 2027):
    for s in (1, 2):
        sem = f'{anno}{s}'
        if sem < '20102' or sem > '20261':
            continue
        get(G + sem, os.path.join(base, 'raw', 'geopoi', f'F205_{sem}.json'), pausa=2)

# 2) NTN
A = 'https://www.agenziaentrate.gov.it/portale/documents/20143/'
for nome, url in {
    'RESIDENZIALE_2025_2026_PROVV.zip': A + '10320492/RESIDENZIALE_2025_2026_PROVV.zip/b939ffd9-0fb4-0c28-cc61-4f285d6fab31?t=1789032622546',
    'RESIDENZIALE_DEFINITIVO_2011_2024.zip': A + '9812824/RESIDENZIALE_DEFINITIVO_2011_2024.zip/8cb254ca-e71c-da1b-2d7a-56d859dce93d?t=1772716377382',
    'NON_RESIDENZIALE_2025_2026_PROVV.zip': A + '10320492/NON_RESIDENZIALE_2025_2026_PROVV.zip/67d5bd64-b1be-a4cc-d260-b5c9ed49cb73?t=1789032624586',
    'NON_RESIDENZIALE_DEFINITIVO_2011_2024.zip': A + '10320492/NON_RESIDENZIALE_DEFINITIVO_2011_2024.zip/bf0b4a74-41cd-f2e9-c998-11c09b79a911?t=1789032588533',
}.items():
    get(url, os.path.join(base, 'raw', 'omi_ntn', nome))
# serie vecchia: gli indirizzi stanno nella pagina dell'archivio (raw/pagine_ae/archivio_res.html, salvata a mano il 30/10/2026)
pag = os.path.join(base, 'raw', 'pagine_ae', 'archivio_res.html')
if os.path.exists(pag):
    t = open(pag, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'(?is)<a [^>]*href="([^"]+)"[^>]*>\s*(Residenziale 20[0-9\- ]+)\s*</a>', t):
        h = m.group(1)
        h = 'https://www.agenziaentrate.gov.it' + h if h.startswith('/') else h
        get(h, os.path.join(base, 'raw', 'omi_ntn_archivio', m.group(2).strip().replace(' ', '_') + '.xls'))

# 3) ISTAT FOI (SDMX CSV)
I = 'https://esploradati.istat.it/SDMXWS/rest/data/IT1,%s,1.0/%s'
H = {'Accept': 'application/vnd.sdmx.data+csv;version=1.0.0'}
get(I % ('169_748_DF_DCSP_FOI1B2025_1', 'M.IT.....?startPeriod=2003-12'), os.path.join(base, 'raw', 'istat', '169_748_DF_DCSP_FOI1B2025_1.m.csv'), H, 600)
get(I % ('169_750_DF_DCSP_FOI2B2025_1', 'all/'), os.path.join(base, 'raw', 'istat', '169_750_DF_DCSP_FOI2B2025_1.csv'), H, 600)

# 4) copie di terzi delle quotazioni 2016/1-2018/2 (solo per provare i programmi)
R = 'https://raw.githubusercontent.com/ondata/quotazioni-immobiliari-agenzia-entrate/master/rawData/'
for f in ('2016-1', '2016-2', '2017-1', '2017-2', '2018-1', '2018-2'):
    get(R + f + '.zip', os.path.join(base, 'raw', 'ondata_mirror_rawdata', f + '.zip'))
print('fine')
