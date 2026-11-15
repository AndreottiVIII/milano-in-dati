"""Compone la bozza della pagina: modello + stile e funzioni dei grafici della pagina Senza dimora.
Uso: python -I -X utf8 anz_03_pagina.py <cartella progetto>"""
import sys, os, json
R = sys.argv[1]
src = open(os.path.join(R, 'docs/senza-dimora/index.html'), encoding='utf-8').read()
css = src[src.index('<style>'):src.index('</style>') + 8]
helpers = src[src.index('var CS=getComputedStyle'):src.index("fetch(DATA+'riepilogo.json'")]
helpers = helpers.replace('var D,RD=[];\n', '')
tpl = open(os.path.join(R, 'anziani/scripts/anz_pagina_modello.html'), encoding='utf-8').read()
ng = len(json.load(open(os.path.join(R, 'docs/anziani/data/gestori.json'), encoding='utf-8')))
out = tpl.replace('{{CSS}}', css).replace('{{HELPERS}}', helpers).replace('{{NGEST}}', str(ng))
os.makedirs(os.path.join(R, 'bozze-grafici/anziani-v2'), exist_ok=True)
open(os.path.join(R, 'bozze-grafici/anziani-v2/index.html'), 'w', encoding='utf-8').write(out)
print(len(out))
