"""Fase 1: tabelle pulite. Lanciare da bilancio-comune/:  python -I scripts/build.py"""
import sys; sys.path.insert(0,'scripts')
from common import *
import pandas as pd, numpy as np, unicodedata, re, os, glob
os.makedirs('pulito',exist_ok=True)

def clean(s): return s.replace('�','?') if isinstance(s,str) else s
EDIZ={'ds397':'2015-2019','ds396':'2016-2020','ds399':'2017-2021','ds400':'2018-2022','ds401':'2019-2023',
      'ds1936':'2020-2024','ds2352':'2021-2025','ds2738':'2022-2026','ds2956':'2023-2027','ds3013':'2024-2028'}
EINV={v:k for k,v in EDIZ.items()}
frames=[]
for ds in DS:
    d,v=load(ds)
    vc=[c for c in d.columns if c.startswith('v::')]
    last_r=None
    rows=[]
    for c in vc:
        name=c[3:].upper()
        m=re.search(r'(20\d\d)',name)
        anno=int(m.group(1)) if m else None
        if name.startswith('RENDICONTO'):
            fase,misura,last_r='consuntivo','rendiconto',anno
        elif 'CASSA' in name and name.startswith('ASSESTATO'):
            fase,misura='previsione','assestato_cassa'; anno=last_r+1
        elif 'CASSA' in name:
            fase,misura='previsione','stanziamento_cassa'
            if anno is None: anno=last_r+1
        else:
            fase,misura='previsione','stanziamento_competenza'
        rows.append((c,anno,fase,misura))
    for c,anno,fase,misura in rows:
        t=d[['ds','tipo','missione','desc_missione','programma','desc_programma','liv1','desc_liv1','liv2','desc_liv2','liv3','desc_liv3','liv4','desc_liv4','capitolo','desc_capitolo']].copy()
        t['edizione']=EDIZ[ds]; t['anno']=anno; t['fase']=fase; t['misura']=misura
        t['anni_dopo_ultimo_rendiconto']=0 if fase=='consuntivo' else anno-last_r
        t['importo']=d[c]
        frames.append(t)
L=pd.concat(frames,ignore_index=True)
L['tipo']=L.tipo.str.upper().map({'USCITE':'uscite','ENTRATE':'entrate'})
for c in ['missione','programma','liv1','liv2','liv3','liv4']:
    L[c]=pd.to_numeric(L[c],errors='coerce').fillna(-1).astype(int)
for c in [c for c in L.columns if c.startswith('desc_')]: L[c]=L[c].map(clean).str.replace(r'\s+',' ',regex=True).str.strip()
print(L.shape)

def canon(sub,key_cols,desc):
    x=sub[(sub[desc]!='')&(~sub[desc].str.contains(r'\?',regex=True))]
    return x.sort_values('edizione').groupby(key_cols)[desc].last()

def flag(df):
    """da_usare=1: riga consigliata per evitare doppi conteggi. Consuntivo: edizione piu' recente che contiene quell'anno.
    Previsione: solo stanziamento di competenza del primo anno dopo l'ultimo rendiconto (la previsione 'corrente' dell'edizione)."""
    df=df.copy()
    cons=df[df.fase=='consuntivo']
    last=cons.groupby('anno').edizione.max()
    df['da_usare']=0
    m1=(df.fase=='consuntivo')&(df.edizione==df.anno.map(last))
    m2=(df.fase=='previsione')&(df.anni_dopo_ultimo_rendiconto==1)&(df.misura.isin(['stanziamento_competenza','assestato','previsione_al_27/02/2014']))
    df.loc[m1|m2,'da_usare']=1
    return df
U=L[L.tipo=='uscite']
cm=canon(U,['missione'],'desc_missione'); cp=canon(U,['missione','programma'],'desc_programma')
g=U.groupby(['edizione','anno','fase','misura','anni_dopo_ultimo_rendiconto','liv1','missione','programma'],as_index=False).importo.sum()
tit={1:'Spese correnti',2:'Spese in conto capitale',3:'Spese per incremento attivita finanziarie',4:'Rimborso prestiti',5:'Chiusura anticipazioni tesoriere',7:'Uscite per conto terzi e partite di giro'}
g['titolo']=g.liv1; g['desc_titolo']=g.liv1.map(tit)
g['desc_missione']=[cm.get(m,'') for m in g.missione]
g['desc_programma']=[cp.get((m,p),'') for m,p in zip(g.missione,g.programma)]
g['fonte']=g.edizione.map(EINV)
g['unita']='euro'
g=g[['fonte','edizione','anno','fase','misura','anni_dopo_ultimo_rendiconto','titolo','desc_titolo','missione','desc_missione','programma','desc_programma','importo','unita']]

def norm(s):
    s=unicodedata.normalize('NFKD',str(s).replace('�','').replace('+','')).encode('ascii','ignore').decode().upper()
    return re.sub(r'[^A-Z0-9]','',s)
mcode={norm(v):k for k,v in cm.items()}
pcode={(m,norm(v)):p for (m,p),v in cp.items()}
def codes(mname,pname):
    m=mcode.get(norm(mname))
    if m is None:
        for k,v in mcode.items():
            if k.startswith(norm(mname)[:25]): m=v;break
    p=None
    if m is not None:
        p=pcode.get((m,norm(pname)))
        if p is None:
            for (mm,k),v in pcode.items():
                if mm==m and k.startswith(norm(pname)[:20]): p=v;break
    if m is not None and p is None:
        ALIAS={'FONDOSVALUTAZIONECREDITI':(20,2),'TRASPORTOPERVIEDACQUA':(10,3),'INTERVENTIPERISOGGETTIARISCHIODIESCLUSIONESOCIALE':(12,4),'INDUSTRIAEPMIEARTIGIANATO':(14,1)}
        mm,pp=ALIAS.get(norm(pname),(None,None))
        if mm==m: p=pp
    return m,p
rows=[]
b=pd.read_csv(glob.glob('raw/ckan_ds284/*.csv')[0],sep=';',encoding='cp1252',decimal=',')
b2=b.groupby(['Missione','Programma'],as_index=False).Impegni.sum()
for _,r in b2.iterrows():
    m,p=codes(r.Missione,r.Programma)
    rows.append(dict(fonte='ds284',edizione='PEG spese correnti consuntivo 2013',anno=2013,fase='consuntivo',misura='impegni',anni_dopo_ultimo_rendiconto=0,titolo=1,desc_titolo='Spese correnti',missione=m if m is not None else -1,desc_missione=r.Missione,programma=p if p is not None else -1,desc_programma=r.Programma,importo=r.Impegni,unita='euro'))
a=pd.read_csv(glob.glob('raw/ckan_ds227/*.csv')[0],sep=';',encoding='cp1252',dtype=str)
a.columns=['Missione','Programma','c2012','a2013','p2014']
a['Missione']=a.Missione.str.strip(); a['Programma']=a.Programma.str.strip()
a=a[a.Missione!='TOTALE']
for _,r in a.iterrows():
    if r.Programma=='TOTALE': continue
    m,p=codes(r.Missione,r.Programma)
    for col,anno,fase,mis,ad in [('c2012',2012,'consuntivo','consuntivo',0),('a2013',2013,'previsione','assestato',1),('p2014',2014,'previsione','previsione_al_27/02/2014',1)]:
        rows.append(dict(fonte='ds227',edizione='Spesa corrente per missioni 2012-2014',anno=anno,fase=fase,misura=mis,anni_dopo_ultimo_rendiconto=ad,titolo=1,desc_titolo='Spese correnti',missione=m if m is not None else -1,desc_missione=r.Missione,programma=p if p is not None else -1,desc_programma=r.Programma,importo=float(r[col].replace(',','.'))*1e6,unita='euro (originale in milioni)'))
O=pd.DataFrame(rows)
print('old rows w/o code:',(O.missione==-1).sum(),(O.programma==-1).sum())
print(O[(O.missione==-1)|(O.programma==-1)][['fonte','desc_missione','desc_programma']].drop_duplicates().to_string())
S=pd.concat([O,g],ignore_index=True)
S=S.sort_values(['anno','fase','fonte','titolo','missione','programma']).reset_index(drop=True)
S['importo']=S.importo.round(2)
S=flag(S)
S.to_csv('pulito/spesa_missioni.csv',index=False,sep=';',encoding='utf-8-sig')
print('spesa_missioni',S.shape)

E=L[L.tipo=='entrate']
ge=E.groupby(['edizione','anno','fase','misura','anni_dopo_ultimo_rendiconto','liv1','liv2','liv3','liv4'],as_index=False).importo.sum()
c1=canon(E,['liv1'],'desc_liv1'); c2=canon(E,['liv1','liv2'],'desc_liv2'); c3=canon(E,['liv1','liv2','liv3'],'desc_liv3'); c4=canon(E,['liv1','liv2','liv3','liv4'],'desc_liv4')
ge['desc_titolo']=[c1.get(a,'') for a in ge.liv1]
ge['desc_tipologia']=[c2.get((a,b),'') for a,b in zip(ge.liv1,ge.liv2)]
ge['desc_categoria']=[c3.get((a,b,c),'') for a,b,c in zip(ge.liv1,ge.liv2,ge.liv3)]
ge['desc_livello4']=[c4.get((a,b,c,d),'') for a,b,c,d in zip(ge.liv1,ge.liv2,ge.liv3,ge.liv4)]
ge['fonte']=ge.edizione.map(EINV)
ge=ge.rename(columns={'liv1':'titolo','liv2':'tipologia','liv3':'categoria','liv4':'livello4'})
ge['unita']='euro'
eo=[]
c=pd.read_csv(glob.glob('raw/ckan_ds285/*.csv')[0],sep=';',encoding='cp1252',decimal=',')
c2_=c.groupby(['IdTitolo','Titolo','Tipologia_di_Entrata','Voce_economica'],as_index=False).Accertamenti_Consuntivo.sum()
for _,r in c2_.iterrows():
    eo.append(dict(fonte='ds285',edizione='PEG entrate correnti consuntivo 2013',anno=2013,fase='consuntivo',misura='accertamenti',anni_dopo_ultimo_rendiconto=0,titolo=r.IdTitolo,tipologia=-1,categoria=-1,livello4=-1,desc_titolo=r.Titolo,desc_tipologia=r.Tipologia_di_Entrata,desc_categoria='',desc_livello4=r.Voce_economica,importo=r.Accertamenti_Consuntivo,unita='euro'))
ge=pd.concat([pd.DataFrame(eo),ge],ignore_index=True)
ge=ge[['fonte','edizione','anno','fase','misura','anni_dopo_ultimo_rendiconto','titolo','tipologia','categoria','livello4','desc_titolo','desc_tipologia','desc_categoria','desc_livello4','importo','unita']]
ge['importo']=ge.importo.round(2)
ge=flag(ge)
ge=ge.sort_values(['anno','fase','fonte','titolo','tipologia','categoria','livello4']).reset_index(drop=True)
ge.to_csv('pulito/entrate.csv',index=False,sep=';',encoding='utf-8-sig')
print('entrate',ge.shape)

cap=L[L.importo!=0].copy()
cap['edizione_ord']=cap.edizione
cap['fonte']=cap.edizione.map(EINV)
cap=cap[['fonte','edizione','tipo','anno','fase','misura','anni_dopo_ultimo_rendiconto','liv1','liv2','liv3','liv4','missione','programma','capitolo','desc_capitolo','importo']]
cap.to_csv('pulito/bilancio_capitoli.csv',index=False,sep=';',encoding='utf-8-sig')
print('capitoli',cap.shape)
L.to_pickle('raw/_L.pkl')
