"""Elenca contenuto degli zip e prime righe. Uso: python -I 32_eligendo_ispeziona.py <raw_eligendo>"""
import sys, os, zipfile, glob
for z in sorted(glob.glob(os.path.join(sys.argv[1], '*', '*.zip'))):
    zf = zipfile.ZipFile(z)
    print('=====', os.path.relpath(z, sys.argv[1]))
    for i in zf.infolist():
        print('  ', i.filename, i.file_size)
    if any(k in z for k in ['camera-19760620','comunali-19750615','regionali-19750615','referendum-19780611','assemblea']):
        for i in zf.infolist():
            if i.filename.lower().endswith(('.csv','.txt')):
                raw = zf.read(i.filename)
                txt = raw.decode('utf-8', errors='replace').splitlines()
                print('  --- head', i.filename, len(txt), 'righe')
                for l in txt[:4]: print('    ', l[:400])
