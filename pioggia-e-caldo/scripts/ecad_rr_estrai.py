"""Estrae dallo zip ECA&D della precipitazione (RR) solo i file delle stazioni di Milano indicate
+ i file di servizio, leggendo lo zip online per intervalli di byte (HTTP Range). Niente account.
uso: python -I -X utf8 ecad_rr_estrai.py URL OUTDIR_ASSOLUTA STAID_o_SOUID [...]   (es. 173 11493 ; per i nonblend si cercano i SOUID in sources.txt)
Se il primo argomento dopo OUTDIR e' 'elenca', salva solo i file di servizio."""
import sys, io, os, zipfile, requests, re
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
        for t in range(5):
            try:
                r=requests.get(s.url, headers={'Range':f'bytes={s.pos}-{s.pos+n-1}'}, timeout=300); r.raise_for_status(); break
            except Exception as e:
                print('retry',e)
        s.pos+=len(r.content); s.n+=len(r.content); return r.content
    def readinto(s, b):
        d=s.read(len(b)); b[:len(d)]=d; return len(d)
url, out = sys.argv[1], sys.argv[2]; ids = sys.argv[3:]
os.makedirs(out, exist_ok=True)
rf=RangeFile(url); z=zipfile.ZipFile(rf); names=z.namelist()
service=[n for n in names if not n.startswith('RR_')]
for n in service: open(os.path.join(out,n),'wb').write(z.read(n))
print(len(names),'file;', 'servizio:', service)
want=[]
if ids and ids[0]!='elenca':
    for n in names:
        m=re.match(r'RR_(?:STAID|SOUID)0*(\d+)\.txt$', n)
        if m and m.group(1) in ids: want.append(n)
    for n in want: open(os.path.join(out,n),'wb').write(z.read(n))
print('estratti',want,'byte scaricati',rf.n,'di',rf.size)
