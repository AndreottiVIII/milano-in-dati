import sys,csv,glob,pandas as pd
root=sys.argv[1]; P=root+"/pulito"
rows=[]
f=glob.glob(root+"/raw/comune_ckan/ds303*/*.csv")[0]
d=pd.read_csv(f,sep=";",encoding="utf-8-sig")
for _,r in d.iterrows():
    rows.append([int(r.iloc[0]),"confini_dell_epoca",int(r.iloc[2]),r.iloc[1],"Comune di Milano ds303 (dati ISTAT), campi Anno di censimento/Popolazione/Superficie"])
vol={1861:267618,1871:290514,1881:354041,1901:538478,1911:701401,1921:818148,1931:960660,1936:1115768,1951:1274154,1961:1582421,1971:1732000,1981:1604773,1991:1369231}
for a,v in vol.items():
    rows.append([a,"confini_al_20_ott_1991",v,"","ISTAT 1994 'Popolazione residente dei comuni, censimenti dal 1861 al 1991', Tavola 3, riga 146 Milano (pdf pagina 293); letto da testo OCR e controllato a occhio sull'immagine"])
for y,fn,col in ((2001,"sezioni_2001.csv","P1"),(2011,"sezioni_2011.csv","P1"),(2021,"sezioni_2021.csv","P1"),(2023,"sezioni_2023.csv","P1")):
    s=pd.read_csv(P+"/"+fn,low_memory=False)[col].sum()
    rows.append([y,"confini_attuali",int(s),"",f"somma di {col} su tutte le sezioni di Milano in pulito/{fn} (ISTAT)"+(" - censimento permanente al 31.12.2023" if y==2023 else "")])
rows.sort(key=lambda r:(r[0],r[1]))
with open(P+"/popolazione_comune_1861_2021.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["anno","confini","popolazione_residente","superficie_km2","fonte"]); w.writerows(rows)
print(len(rows))
# serie annuale calcolata dal Comune
for pat,name in (("ds1494","popolazione_milano_annuale_1880_calcolata.csv"),):
    g=glob.glob(root+f"/raw/comune_ckan/{pat}*/*.csv")[0]
    x=pd.read_csv(g,sep=";",encoding="utf-8-sig"); x.columns=["anno","popolazione_calcolata"]; x.to_csv(P+"/"+name,index=False); print(name,len(x),x.anno.min(),x.anno.max())
