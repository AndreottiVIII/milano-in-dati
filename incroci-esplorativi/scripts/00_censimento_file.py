"""Censimento di tutti i CSV del progetto: colonne, righe, se hanno un id NIL o una colonna di tempo.
Non tocca nulla fuori da incroci-esplorativi/out."""
import csv, os, re, sys, json
ROOT=r"C:\Users\davide\Desktop\ClaudeTower\milano-in-dati"
OUT=os.path.join(ROOT,"incroci-esplorativi","out","censimento_file.csv")
rows=[]
csv.field_size_limit(10**8)
for top in os.listdir(ROOT):
    p=os.path.join(ROOT,top)
    if not os.path.isdir(p) or top.startswith('_') or top in('incroci-esplorativi','bozze-home'): continue
    for dp,dn,fn in os.walk(p):
        parts=set(dp.lower().replace('/',os.sep).split(os.sep))
        if parts & {'grezzi','raw','grezzo','cache','node_modules','scripts','foto','tile','tiles'}: continue
        for f in fn:
            if not f.lower().endswith('.csv'): continue
            fp=os.path.join(dp,f)
            sz=os.path.getsize(fp)
            if sz>60_000_000: 
                rows.append((os.path.relpath(fp,ROOT),sz,-1,'','','','TOO BIG')); continue
            try:
                with open(fp,encoding='utf-8-sig',newline='') as h:
                    head=h.readline()
                    sep=';' if head.count(';')>head.count(',') else ','
                    cols=next(csv.reader([head],delimiter=sep))
                    n=sum(1 for _ in h)
            except Exception as e:
                rows.append((os.path.relpath(fp,ROOT),sz,-1,'','','',str(e)[:80])); continue
            lc=[c.lower().strip() for c in cols]
            nil=[c for c in lc if re.fullmatch(r'(id_?nil|nil|nil_id|id_nil_?\d*|nil_nome|nome_nil|quartiere)',c)]
            tm=[c for c in lc if re.fullmatch(r'(anno|mese|data|giorno|year|month|date|anno_mese|periodo|ym|semestre|trimestre)',c)]
            rows.append((os.path.relpath(fp,ROOT),sz,n,'|'.join(nil),'|'.join(tm),'|'.join(cols)[:400],''))
with open(OUT,'w',encoding='utf-8',newline='') as h:
    w=csv.writer(h); w.writerow(['file','bytes','righe','col_nil','col_tempo','colonne','errore']); w.writerows(rows)
print(len(rows))
