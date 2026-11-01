"""Estrae gli zip di raw/ed*/ in raw/ed*/x/ (con controllo zip-slip) e scrive l'elenco dei file.
Uso: python -I -X utf8 estrai.py <raw assoluto>"""
import sys, zipfile, pathlib
raw = pathlib.Path(sys.argv[1])
for z in sorted(raw.glob('ed*/*.zip')):
    out = z.parent / 'x'
    out.mkdir(exist_ok=True)
    with zipfile.ZipFile(z) as zf:
        for i in zf.infolist():
            # i nomi in zip possono essere cp437/utf8; si controlla che restino dentro out
            dest = (out / i.filename).resolve()
            if not str(dest).startswith(str(out.resolve())):
                print('SALTATO (percorso sospetto)', i.filename); continue
            zf.extract(i, out)
        print(z.parent.name, z.name, len(zf.infolist()), 'file')
