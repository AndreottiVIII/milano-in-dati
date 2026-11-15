"""Assembla la bozza della pagina: intestazione e stile presi dalla pagina dei negozi, corpo da altezze/scripts/corpo.html."""
import os, re
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.dirname(R)
src = open(os.path.join(P, 'docs', 'negozi', 'index.html'), encoding='utf-8').read()
testa = src[:src.index('</style>')]
TIT = 'Quanto è alta Milano'
DESC = 'Quanto sono alti i palazzi di Milano quartiere per quartiere, quali sono le torri più alte e dove la città è cresciuta in altezza tra il 2012 e il 2020.'
testa = testa.replace('I negozi di Milano', TIT)
testa = re.sub(r'(<meta property="og:description" content=")[^"]*', r'\g<1>' + DESC, testa)
testa = re.sub(r'(<meta name="twitter:description" content=")[^"]*', r'\g<1>' + DESC, testa)
testa = re.sub(r'(<meta name="description" content=")[^"]*', r'\g<1>' + DESC, testa)
testa = re.sub(r'"description":"[^"]*"', '"description":"' + DESC + '"', testa)
testa = testa.replace('/negozi/', '/altezze/')
testa = testa.replace('"temporalCoverage":"2003/2025"', '"temporalCoverage":"2012/2020"').replace('"dateModified":"2026-11-10"', '"dateModified":"2026-11-15"')
testa = re.sub(r'<meta property="og:image[^>]*>', '', testa)
testa = re.sub(r'<meta name="twitter:image"[^>]*>', '', testa)
testa = testa.replace('summary_large_image', 'summary')
corpo = open(os.path.join(R, 'scripts', 'corpo.html'), encoding='utf-8').read()
out = testa + '</style><script src="../menu.js" defer></script></head><body><main>\n' + corpo
d = os.path.join(P, 'bozze-grafici', 'altezze-v2'); os.makedirs(d, exist_ok=True)
open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(out)
print(len(out), 'byte')
