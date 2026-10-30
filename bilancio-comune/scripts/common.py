import pandas as pd, re, glob
# dataset id -> (file glob, encoding, number style, label)
DS = {
 'ds397': ('raw/ckan_ds397/*.csv','cp1252','it','PEG 2015-2019'),
 'ds396': ('raw/ckan_ds396/*.csv','utf-8','it','PEG 2016-2020'),
 'ds399': ('raw/ckan_ds399/*.csv','cp1252','it','PEG 2017-2021'),
 'ds400': ('raw/ckan_ds400/*.csv','cp1252','it','PEG 2018-2022'),
 'ds401': ('raw/ckan_ds401/*.csv','utf-8','en','PEG 2019-2023'),
 'ds1936':('raw/ckan_ds1936/*.csv','utf-8','plain','PEG 2020-2024'),
 'ds2352':('raw/ckan_ds2352/*.csv','utf-8','plain','PEG 2021-2025'),
 'ds2738':('raw/ckan_ds2738/*.csv','utf-8','plain','PEG 2022-2026'),
 'ds2956':('raw/ckan_ds2956/*.csv','utf-8','plain','PEG 2023-2027'),
 'ds3013':('raw/ckan_ds3013/*.csv','utf-8','plain','PEG 2024-2028'),
}
def num(s,style):
    s=str(s).strip()
    if s in ('','-'): return 0.0
    if style=='it': s=s.replace('.','').replace(',','.')
    elif style=='en': s=s.replace(',','')
    return float(s)
def load(ds):
    g,enc,style,label=DS[ds]
    f=glob.glob(g)[0]
    df=pd.read_csv(f,sep=';',encoding=enc,dtype=str,keep_default_na=False)
    df.columns=[c.strip() for c in df.columns]
    cols=list(df.columns)
    low=[c.lower() for c in cols]
    vcols=[c for c in cols if re.match(r'(rendiconto|stanziamento|assestato)',c.lower())]
    out=pd.DataFrame()
    out['tipo']=df[cols[0]].str.strip().str.upper()
    for k,c in zip(['missione','desc_missione','programma','desc_programma','liv1','desc_liv1','liv2','desc_liv2','liv3','desc_liv3','liv4','desc_liv4'],cols[1:13]):
        out[k]=df[c].str.strip()
    out['capitolo']=df[[c for c in cols if c.lower()=='capitolo'][0]].str.strip()
    out['desc_capitolo']=df[[c for c in cols if c.lower().startswith('desc') and 'capitolo' in c.lower() or c.lower() in ('desc peg',)][0]].str.strip()
    out['cdr']=df[cols[cols.index(vcols[0])-2]].str.strip() if False else ''
    for c in vcols:
        out['v::'+re.sub(r'\s+',' ',c)]=df[c].map(lambda x: num(x,style))
    out['ds']=ds
    return out, vcols
