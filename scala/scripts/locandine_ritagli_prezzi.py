"""Ritaglia il fondo delle locandine d'opera fino al 2001 e lo ingrandisce, per leggere meglio la fascia dei prezzi.

Uso: python -I -X utf8 locandine_ritagli_prezzi.py --cartella <risultati> --archivio <locandine> --uscita <cartella temporanea>
Scrive ritagli e 4 elenchi per locandine_ocr.ps1. I ritagli non servono più dopo la lettura.
"""
import argparse, csv, os
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('--cartella', required=True)
ap.add_argument('--archivio', required=True)
ap.add_argument('--uscita', required=True)
a = ap.parse_args()
os.makedirs(a.uscita, exist_ok=True)
rec = [x for x in csv.DictReader(open(os.path.join(a.cartella, 'lavori_per_recita.csv'), encoding='utf-8-sig')) if x['tipo'] == 'Opera' and x['data'] < '20020101']
righe = []
for x in rec:
    for d in ('foto', 'Balletti', 'Concerti', 'Manifestazioni', 'Recital', 'Diversi'):
        p = os.path.join(a.archivio, d, x['file'])
        if os.path.exists(p):
            im = Image.open(p).convert('RGB')
            w, h = im.size
            im = im.crop((0, int(h * .62), w, h)).resize((w * 5, int(h * .38) * 5), Image.LANCZOS)
            q = os.path.join(a.uscita, x['file']).replace('/', '\\')
            im.save(q, quality=90)
            righe.append(q)
            break
for i in range(4):
    open(os.path.join(a.uscita, f'elenco{i}.txt'), 'w', encoding='utf-8').write('\n'.join(righe[i::4]) + '\n')
print(len(righe))
