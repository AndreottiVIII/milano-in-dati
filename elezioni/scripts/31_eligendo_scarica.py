"""Scarica gli zip open data di Eligendo (pre-1979 + Camera/Senato 1979).
Uso: python -I 31_eligendo_scarica.py <cartella_raw_eligendo>"""
import sys, os, urllib.request, time
base = 'https://elezionistorico.interno.gov.it/daithome/documenti/opendata/'
files = ['assemblea_costituente/assemblea_costituente-19460602.zip','referendum/referendum-19460602.zip']
for d in ['19480418','19530607','19580525','19630428','19680519','19720507','19760620','19790603']:
    files += ['camera/camera-%s.zip' % d, 'senato/senato-%s.zip' % d]
files += ['referendum/referendum-19740512.zip','referendum/referendum-19780611.zip',
          'regionali/regionali-19700607.zip','regionali/regionali-19750615.zip',
          'comunali/comunali-19641122.zip','comunali/comunali-19700607.zip','comunali/comunali-19750615.zip']
out = sys.argv[1]
for f in files:
    dst = os.path.join(out, f.replace('/', os.sep))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print('gia', f); continue
    req = urllib.request.Request(base + f, headers={'User-Agent': 'Mozilla/5.0 (milano-in-dati)'})
    try:
        data = urllib.request.urlopen(req, timeout=120).read()
        open(dst, 'wb').write(data)
        print('ok', f, len(data))
    except Exception as e:
        print('ERR', f, e)
    time.sleep(1)
