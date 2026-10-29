"""Legge il wikitext di it.wikipedia 'Stagioni liriche del Teatro alla Scala' e scrive pulito/_wp_stagioni.csv
(una riga per titolo/stagione) + pulito/_wp_aperture.csv (tabella 'Apertura della stagione lirica').
Uso: python -I -X utf8 scripts/parse_wikipedia_stagioni.py raw/wikipedia/Stagioni_liriche_wikitext.txt pulito"""
import re, sys, csv, os
src, outd = sys.argv[1], sys.argv[2]
L = open(src, encoding='utf-8').read().split('\n')
MESI = {m: i + 1 for i, m in enumerate("gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre".split())}
Q3 = "'''"
Q2 = "''"


def clean(s):
    s = re.sub(r'<ref[^>]*?/>', '', s)
    s = re.sub(r'<ref[^>]*>.*?</ref>', '', s, flags=re.S)
    s = re.sub(r'<ref[^>]*>.*$', '', s)
    s = re.sub(r'<!--.*?-->', '', s)
    s = re.sub(r'\{\{[^{}]*\}\}', '', s)
    s = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', s)
    s = s.replace(Q3, '').replace(Q2, '')
    return re.sub(r'\s+', ' ', s).strip()


def split_top(s, seps=','):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            d += 1
        if ch == ')':
            d = max(0, d - 1)
        if ch in seps and d == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    out.append(cur)
    return [x.strip(' .;') for x in out if x.strip(' .;')]


def parse_date(txt, year):
    m = re.search(r'(\d{1,2})(?:º|°)?\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)', txt)
    if m and year:
        return '%04d-%02d-%02d' % (year, MESI[m.group(2)], int(m.group(1)))
    return ''


def refs(raw):
    rm = re.findall(r'\{\{Cita\|([^|}]+)\|([^}]*)\}\}', raw)
    return '; '.join('%s %s' % (a, b) for a, b in rm)


rows = []
year = None
stag = ''
hdr = ''
cur = None


def flush():
    global cur
    if cur:
        rows.append(cur)
        cur = None


def newentry(raw, lineno):
    global cur
    flush()
    ref = refs(raw)
    mm = re.search(r'name="?R(\d+)"?', raw)
    if not ref and mm:
        ref = 'Romani p. ' + mm.group(1)
    t = clean(raw)
    tit, comp, rest = '', '', ''
    m = re.match(r"^(.*?)\s+di\s+(.+)$", t)
    if m:
        tit, rest = m.group(1), m.group(2)
        comp = re.split(r'\.|,| \(|\s+Prima rappresentazione|\s+Direttore|\s+Regia| e (?=[A-Z])', rest)[0].strip()
    else:
        tit = t.split('.')[0]
    tit = tit.strip(' .')
    cur = {'anno': year, 'stagione': stag, 'sezione': hdr, 'titolo': tit, 'compositore': comp, 'direttore': '', 'regista': '',
           'interpreti': '', 'scene': '', 'data': '', 'prima': '', 'ref': ref, 'riga_fonte': 'wikitext riga %d' % lineno}
    for key, fld in (('Direttore', 'direttore'), ('Regia', 'regista')):
        mm = re.search(key + r':\s*(.+?)(?=\s+(?:Direttore|Regia|Prima rappresentazione)\b|$)', t)
        if mm:
            cur[fld] = mm.group(1).strip(' .')
    mm = re.search(r'Prima rappresentazione[^:]*:\s*([^;(]+)', t)
    if mm:
        cur['data'] = parse_date(mm.group(1), year)


for i, ln in enumerate(L, 1):
    if ln.startswith('=== Apertura della stagione lirica'):
        flush()
        break
    my = re.match(r"^\s*'''(\d{4})'''", ln)
    if my:
        flush()
        year = int(my.group(1))
        stag = ''
        continue
    m = re.match(r'^={3,}\s*(.*?)\s*={3,}$', ln)
    if m:
        flush()
        hdr = m.group(1)
        continue
    if re.match(r'^\*\s*\S', ln) and year:
        raw = ln[1:].strip()
        if year < 2020 and Q2 not in raw:
            flush()
            continue
        if year >= 2020 and not re.search(r' di | Prima rappresentazione', raw):
            flush()
            continue
        newentry(raw, i)
        continue
    if ln.startswith(':') and cur:
        c = clean(ln[1:])
        m = re.match(r'^(Fra gli interpreti|Interpreti principali|Interpreti|Cantanti)\s*:?\s*(.*)$', c)
        if m:
            items = split_top(m.group(2), ',')
            cur['interpreti'] = ';'.join(([cur['interpreti']] if cur['interpreti'] else []) + items)
            continue
        m = re.match(r'^(Direttore e regista|Direttore di scena|Direttori|Direttore|Dirige il compositore|Dirige|Diretta da)\s*:?\s*(.*)$', c)
        if m:
            if m.group(1) == 'Direttore di scena':
                continue
            v = m.group(2).strip(' .') or ('il compositore' if 'compositore' in m.group(1) else '')
            if m.group(1) == 'Direttore e regista':
                cur['regista'] = v
            cur['direttore'] = v or cur['direttore']
            continue
        m = re.match(r'^(Regia e costumi|Regia|Ragia|Regista)\s*(?:di|:)?\s*(.*)$', c)
        if m:
            cur['regista'] = m.group(2).strip(' .')
            continue
        m = re.match(r'^(Scene e costumi|Scenografie e costumi|Scenografie|Scenografia|Scene)\s*(?:di|dei|:)?\s*(.*)$', c)
        if m:
            cur['scene'] = m.group(2).strip(' .')
            continue
        if c.startswith('Prima rappresentazione'):
            cur['prima'] = c.split(':')[0]
            cur['data'] = parse_date(c, year)
            r2 = refs(ln)
            if r2 and not cur['ref']:
                cur['ref'] = r2
            continue
        r2 = refs(ln)
        if r2 and not cur['ref']:
            cur['ref'] = r2
        continue
    if ln.strip() and year and not ln.startswith(('*', ':', '{', '|', '!', '[[File', '<', '=', Q3)):
        t = clean(ln)
        if len(t) < 90 and re.search(r'[Ss]tagione|[Cc]arnevale|[Qq]uaresima|[Pp]rimavera|[Aa]utunno|[Ee]state|[Aa]vvento', t):
            flush()
            stag = t.rstrip(':')
        continue
flush()
os.makedirs(outd, exist_ok=True)
cols = ['anno', 'stagione', 'data', 'titolo', 'compositore', 'direttore', 'regista', 'interpreti', 'scene', 'prima', 'ref', 'sezione', 'riga_fonte']
with open(os.path.join(outd, '_wp_stagioni.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, cols, extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(len(rows), 'voci')
txt = '\n'.join(L)
m = re.search(r'=== Apertura della stagione lirica ===(.*?)\n==', txt, re.S)
ap = []
if m:
    for blk in m.group(1).split('|-')[1:]:
        cells = [c.strip() for c in re.split(r'\n\||\|\|', blk) if c.strip()]
        cells = [clean(re.sub(r'^\|', '', c)) for c in cells]
        if len(cells) >= 4:
            for st in re.findall(r'(\d{4})/(\d{2,4})', cells[3]):
                ap.append([cells[0], cells[1], st[0] + '/' + st[1]])
with open(os.path.join(outd, '_wp_aperture.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f)
    w.writerow(['compositore', 'titolo', 'stagione'])
    w.writerows(ap)
print(len(ap), 'aperture')
