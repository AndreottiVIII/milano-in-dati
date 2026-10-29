"""Fase 4: inserisce (o sostituisce) la sezione 'Dove la bici e' piu a rischio' in docs/bici-auto-mezzi/index.html, prima del <footer>.
Non tocca le altre sezioni.  Uso: python -I f4_inserisci.py <ABS strand> <ABS index.html>"""
import sys, re
S, H = sys.argv[1], sys.argv[2]
blk = open(S + '/scripts/f4_sezione_rischio.html', encoding='utf-8').read().replace('\r\n', '\n').replace('\n', '\r\n')
raw = open(H, 'rb').read().decode('utf-8')
if '<!-- RISCHIO:INIZIO' in raw:
    raw = re.sub(r'<!-- RISCHIO:INIZIO.*?<!-- RISCHIO:FINE -->\r?\n?', lambda m: blk, raw, flags=re.S)
else:
    i = raw.index('<footer>')
    raw = raw[:i] + blk + '\r\n' + raw[i:]
open(H, 'wb').write(raw.encode('utf-8'))
print('ok', len(raw))
