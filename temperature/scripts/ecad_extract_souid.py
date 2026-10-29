"""Estrae da uno zip ECA&D non-blended (via HTTP Range) i file per SOUID. uso: python -I ecad_extract_souid.py URL OUTDIR PREFISSO SOUID..."""
import sys, os, zipfile, importlib.util
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location('lz', os.path.join(here,'ecad_list_zip.py')); lz=importlib.util.module_from_spec(spec); spec.loader.exec_module(lz)
url,out,pre=sys.argv[1:4]; ids=sys.argv[4:]
rf=lz.RangeFile(url); z=zipfile.ZipFile(rf); names=z.namelist()
for i in ids:
    n=f'{pre}_SOUID{i}.txt'
    if n in names: open(os.path.join(out,n),'wb').write(z.read(n)); print('ok',n)
    else: print('MANCA',n)
print('byte scaricati',rf.n)
