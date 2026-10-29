"""Estrae da uno zip ECA&D online (via HTTP Range) solo i file delle stazioni indicate + i file di servizio.
uso: python -I ecad_extract.py URL OUTDIR STAID [STAID...]"""
import sys, os, zipfile, importlib.util
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('lz', os.path.join(here,'ecad_list_zip.py')); lz=importlib.util.module_from_spec(spec); spec.loader.exec_module(lz)
url,out=sys.argv[1],sys.argv[2]; staids=[int(x) for x in sys.argv[3:]]
os.makedirs(out,exist_ok=True)
rf=lz.RangeFile(url); z=zipfile.ZipFile(rf)
names=z.namelist()
want=[n for n in names if not n[:2] in ('TX','TN','TG') or any(n.endswith('STAID%06d.txt'%s) for s in staids)]
for n in want:
    open(os.path.join(out,n),'wb').write(z.read(n))
print(url.split('/')[-1], 'file nello zip:',len(names),'estratti:',len(want),'byte scaricati:',rf.n, 'di', rf.size)
