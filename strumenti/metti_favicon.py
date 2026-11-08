"""Mette i link della favicon in tutte le pagine HTML di docs/ (e nelle bozze v2), se mancano."""
import os, re, sys
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def tag(pre):
    return ('<link rel="icon" href="%sfavicon.svg" type="image/svg+xml"><link rel="icon" href="%sfavicon.ico" sizes="48x48">'
            '<link rel="apple-touch-icon" href="%sapple-touch-icon.png">') % (pre, pre, pre)
def metti(path, pre):
    s = open(path, encoding='utf8').read()
    if 'favicon.svg' in s: return 0
    m = re.search(r'<meta charset[^>]*>', s, re.I) or re.search(r'<head[^>]*>', s, re.I)
    if not m: return 0
    s = s[:m.end()] + tag(pre) + s[m.end():]
    open(path, 'w', encoding='utf8', newline='').write(s); return 1
n = 0
D = os.path.join(R, 'docs')
for root, dirs, files in os.walk(D):
    rel = os.path.relpath(root, D)
    if rel.split(os.sep)[0] == 'anteprima': continue
    depth = 0 if rel == '.' else len(rel.split(os.sep))
    for f in files:
        if f.endswith('.html'): n += metti(os.path.join(root, f), '../' * depth)
BZ = os.path.join(R, 'bozze-grafici')
for d in os.listdir(BZ):
    p = os.path.join(BZ, d, 'index.html')
    if d.endswith('-v2') and os.path.isfile(p): n += metti(p, '../')
print('pagine aggiornate:', n)
