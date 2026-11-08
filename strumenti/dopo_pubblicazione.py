"""Da lanciare dopo aver cambiato testi o dati di una o piu' pagine, prima di pubblicare.

Lancia in ordine:
  1. anteprime_link.py  (immagine e meta di condivisione)
  2. statico.py         (testo visibile anche senza JavaScript)
  3. seo.py             (description, canonical, JSON-LD, sitemap, manifest, 404)
seo.py viene dopo statico.py perche' la data "lastmod" della mappa del sito dipende dal testo della pagina,
blocco statico compreso. Il server locale (http://localhost:8796) deve essere acceso.

Uso: python -I -X utf8 strumenti/dopo_pubblicazione.py [pagina ...]   (senza nomi: tutte)
"""
import pathlib, subprocess, sys

QUI = pathlib.Path(__file__).resolve().parent


def main():
    nomi = [a for a in sys.argv[1:] if not a.startswith('--')]
    for prog in ('anteprime_link.py', 'statico.py', 'seo.py'):
        print('==', prog, flush=True)
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(QUI / prog)] + nomi)
        if r.returncode:
            print('%s e\' finito con errore (%d): mi fermo.' % (prog, r.returncode))
            return r.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
