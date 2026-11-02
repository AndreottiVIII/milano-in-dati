"""Estrae titoli e indirizzi dalle pagine ELENCO di Pietre della Memoria (solo conteggio di verifica, non entra nei dati pubblicati).
Uso: python -I -X utf8 03_pdm_titoli.py <raw/pdm assoluto> <uscita json assoluta>"""
import re,html,glob,collections,json,sys
items={}
for f in sorted(glob.glob(sys.argv[1]+'/elenco_*.html')):
    t=open(f,encoding='utf8').read()
    t=re.sub(r'<(script|style)[^>]*>.*?</\1>','',t,flags=re.S)
    for m in re.finditer(r'href="(https://www.pietredellamemoria.it/pietre/[^"]+)"[^>]*>\s*([^<]{8,250})<',t):
        items.setdefault(m.group(1),html.unescape(m.group(2)).strip())
json.dump(items,open(sys.argv[2],'w',encoding='utf8'),ensure_ascii=False,indent=0)
c=collections.Counter()
for u,t in items.items():
    tl=t.lower(); k='altro'
    for w in ['pietra d','pietre d','lapide','lastra','targa','monumento','cippo','stele','cripta','sacrario','busto','statua','epigrafe','scultura','fontana','casa']:
        if w in tl: k=w;break
    c[k]+=1
print(len(items),c)
