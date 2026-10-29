"""Legge SOLO l'indice (e i file di servizio) di uno zip ECA&D online, senza scaricarlo tutto (HTTP Range).
uso: python -I ecad_list_zip.py URL OUTDIR  -> salva stations.txt, sources.txt, elements.txt ecc. e stampa il numero di file"""
import sys, io, zipfile, requests, os
class RangeFile(io.RawIOBase):
    def __init__(s, url):
        s.url=url; s.pos=0
        r=requests.head(url, allow_redirects=True); s.size=int(r.headers['Content-Length']); s.n=0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.pos
    def seek(s, off, whence=0):
        s.pos = off if whence==0 else (s.pos+off if whence==1 else s.size+off); return s.pos
    def read(s, n=-1):
        if n<0 or s.pos+n>s.size: n=s.size-s.pos
        if n<=0: return b''
        r=requests.get(s.url, headers={'Range':f'bytes={s.pos}-{s.pos+n-1}'}); r.raise_for_status()
        s.pos+=len(r.content); s.n+=len(r.content); return r.content
    def readinto(s, b):
        d=s.read(len(b)); b[:len(d)]=d; return len(d)
if __name__=='__main__':
    url, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    rf=RangeFile(url); z=zipfile.ZipFile(rf)
    names=z.namelist(); print(len(names),'file nello zip; byte scaricati per l indice:',rf.n)
    print([n for n in names if not n.startswith(('TX_','TN_','TG_'))][:20])
    for n in names:
        if not n.startswith(('TX_STAID','TN_STAID','TG_STAID')) :
            open(os.path.join(out,n),'wb').write(z.read(n))
