"""Trasloco del sito su un dominio proprio: cambia l'indirizzo in un colpo solo e rigenera tutto cio' che lo contiene.

Uso:  python -I -X utf8 strumenti/trasloco_dominio.py milanoindati.it            (vero: modifica sito.py e docs/)
      python -I -X utf8 strumenti/trasloco_dominio.py milanoindati.it --prova    (su una copia temporanea, non tocca nulla)
      python -I -X utf8 strumenti/trasloco_dominio.py milanoindati.it --con-statico   (rilancia anche statico.py)

Il dominio si scrive senza https:// e senza barre (anche con https:// va bene). Va lanciato SOLO dopo che il
dominio risponde (DNS) e dopo il "git pull" che porta il file docs/CNAME scritto da GitHub.
Il server locale (http://localhost:8796) deve essere acceso: anteprime_link.py legge le pagine da li'.

Ordine:
  1. strumenti/sito.py: BASE = 'https://<dominio>/'
  2. anteprime_link.py --senza-immagini  (og:url, og:image, twitter:image: le immagini non cambiano)
  3. seo.py  (canonical, JSON-LD, manifest, sitemap.xml, site.webmanifest, 404.html, robots.txt)
     seo.py va dopo anteprime_link.py (il blocco <!--seo--> viene dopo <!--condividi-->)
  4. le anteprime in docs/anteprima/ (non indicizzate, copiate da bozze-grafici/anteprima.py): sostituzione
     diretta del vecchio indirizzo con il nuovo, perche' seo.py e anteprime_link.py non le toccano
  5. (solo con --con-statico) statico.py: non contiene indirizzi, serve solo se sono cambiati i testi
  6. controllo finale: in docs/ non deve restare "andreottiviii.github.io" ne' "/milano-in-dati/"
     (i link a github.com/AndreottiVIII/milano-in-dati sono giusti e si ignorano); ogni pagina deve avere
     un solo canonical e un solo og:url, uguali a <dominio>/<pagina>/. Se c'e' un problema esce con errore.
Dopo: git commit e push, poi Enforce HTTPS su GitHub (vedi REVIEW_DOMINIO_2026-11-15.md).
"""
import pathlib, re, shutil, subprocess, sys, tempfile

QUI = pathlib.Path(__file__).resolve().parent
RADICE = QUI.parent
VECCHI = ('andreottiviii.github.io', '/milano-in-dati/')
ESTENSIONI = {'.html', '.js', '.json', '.xml', '.txt', '.webmanifest', '.css', '.svg', '.md', '.csv'}
MAX_LETTURA = 3_000_000


def cerca_vecchi(docs):
    """Righe di docs/ con un indirizzo vecchio (tranne i link al repo su github.com)."""
    trovati = []
    rx_path = re.compile(r'(?<!AndreottiVIII)(?<!andreottiviii)/milano-in-dati/')
    for f in sorted(docs.rglob('*')):
        if not f.is_file() or f.suffix.lower() not in ESTENSIONI or f.stat().st_size > MAX_LETTURA:
            continue
        s = f.read_text(encoding='utf-8', errors='ignore')
        if VECCHI[0] in s or rx_path.search(s):
            n = s.count(VECCHI[0]) + len(rx_path.findall(s))
            trovati.append('%s (%d volte)' % (f.relative_to(docs).as_posix(), n))
    return trovati


def controlla_teste(docs, base):
    problemi = []
    for f in sorted(docs.rglob('index.html')):
        rel = f.relative_to(docs).parent.as_posix()
        if rel.startswith('anteprima') or rel.startswith('_'):
            continue
        atteso = base + ('' if rel == '.' else rel + '/')
        testa = f.read_text(encoding='utf-8').split('</head>')[0]
        can = re.findall(r'<link\s+rel="canonical"\s+href="([^"]*)"', testa)
        ogu = re.findall(r'<meta\s+property="og:url"\s+content="([^"]*)"', testa)
        if can != [atteso]:
            problemi.append('%s: canonical %s, atteso %s' % (rel, can, atteso))
        if ogu != [atteso]:
            problemi.append('%s: og:url %s, atteso %s' % (rel, ogu, atteso))
    for nome, deve in (('sitemap.xml', 'Sitemap'), ('robots.txt', base + 'sitemap.xml')):
        f = docs / nome
        if not f.is_file():
            problemi.append('manca ' + nome)
        elif nome == 'robots.txt' and deve not in f.read_text(encoding='utf-8'):
            problemi.append('robots.txt senza la mappa del sito')
    return problemi


def lancia(radice, prog, *args):
    print('==', prog, *args, flush=True)
    r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(radice / 'strumenti' / prog), *args])
    if r.returncode:
        sys.exit('%s e\' finito con errore (%d): mi fermo.' % (prog, r.returncode))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    prova = '--prova' in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    dominio = re.sub(r'^https?://', '', args[0]).strip('/')
    if not re.fullmatch(r'[a-z0-9.-]+\.[a-z]{2,}', dominio) or 'andreottiviii' in dominio:
        sys.exit('dominio non valido: ' + args[0])
    base = 'https://%s/' % dominio

    if prova:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix='trasloco_prova_'))
        print('prova su una copia in', tmp)
        shutil.copytree(QUI, tmp / 'strumenti', ignore=shutil.ignore_patterns('__pycache__'))
        shutil.copytree(RADICE / 'docs', tmp / 'docs')
        (tmp / 'bozze-grafici').mkdir()
        mod = RADICE / 'bozze-grafici' / 'anteprime-link'
        if mod.is_dir():
            shutil.copytree(mod, tmp / 'bozze-grafici' / 'anteprime-link')
        radice = tmp
    else:
        radice = RADICE

    sito_py = radice / 'strumenti' / 'sito.py'
    s = sito_py.read_text(encoding='utf-8')
    n, k = re.subn(r"^BASE = '[^']*'", "BASE = '%s'" % base, s, count=1, flags=re.M)
    if not k:
        sys.exit('non trovo BASE in sito.py')
    sito_py.write_text(n, encoding='utf-8', newline='')
    print('BASE =', base)

    lancia(radice, 'anteprime_link.py', '--senza-immagini')
    lancia(radice, 'seo.py')
    vecchia_base = re.search(r"^BASE = '([^']*)'", s, re.M).group(1)
    for f in sorted((radice / 'docs' / 'anteprima').rglob('*.html')):
        t = f.read_text(encoding='utf-8')
        if vecchia_base in t:
            f.write_text(t.replace(vecchia_base, base), encoding='utf-8', newline='')
            print('anteprima aggiornata:', f.relative_to(radice / 'docs').as_posix())
    if '--con-statico' in sys.argv:
        lancia(radice, 'statico.py')

    vecchi = cerca_vecchi(radice / 'docs')
    problemi = controlla_teste(radice / 'docs', base)
    if vecchi:
        print('\nINDIRIZZI VECCHI RIMASTI in docs/:')
        for v in vecchi:
            print('  ', v)
    if problemi:
        print('\nPROBLEMI nelle teste:')
        for p in problemi[:30]:
            print('  ', p)
    if vecchi or problemi:
        sys.exit(1)
    print('\ntrasloco_dominio: tutto su %s, nessun indirizzo vecchio in docs/, un solo canonical e og:url per pagina.' % base)
    if prova:
        print('(prova: la copia e\' in %s, il sito vero non e\' stato toccato)' % radice)


if __name__ == '__main__':
    main()
