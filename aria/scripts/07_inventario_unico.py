import pandas as pd, sys
out=sys.argv[1]
a=pd.read_csv(f"{out}/inventario_arpa.csv",dtype={"idsensore":str,"idstazione":str})
c=pd.read_csv(f"{out}/inventario_comune.csv"); c=c[c.validi>0]
m_st={1:"549",2:"705",3:"539",4:"501",5:"547",6:"548",7:"528",8:"503",9:"502"}
m_in={"NO2":"Biossido di Azoto","SO2":"Biossido di Zolfo","O3":"Ozono","PM10":"PM10 (SM2005)","PM25":"Particelle sospese PM2.5","C6H6":"Benzene","CO_8h":"Monossido di Carbonio"}
c["idstazione"]=c.stazione_id.map(m_st); c["tipo"]=c.inquinante.map(m_in)
c=c.rename(columns={"prima":"comune_prima","ultima":"comune_ultima","validi":"comune_giorni_validi","max_buco_giorni":"comune_max_buco_giorni"})
a=a.rename(columns={"prima":"arpa_prima","ultima":"arpa_ultima","validi":"arpa_valori_validi","max_buco_giorni":"arpa_max_buco_giorni","passo_mediano":"arpa_passo"})
u=a[["idstazione","stazione","tipo","idsensore","unita","storico","datastart_reg","datastop_reg","arpa_prima","arpa_ultima","arpa_passo","arpa_valori_validi","arpa_max_buco_giorni"]].merge(
  c[["idstazione","tipo","stazione_id","comune_prima","comune_ultima","comune_giorni_validi","comune_max_buco_giorni"]],on=["idstazione","tipo"],how="outer")
u.sort_values(["idstazione","tipo","idsensore"]).to_csv(f"{out}/inventario_stazioni_inquinanti.csv",index=False,encoding="utf-8")
print(len(u)); print(u[u.idsensore.isna()|u.stazione_id.isna()][["idstazione","tipo","idsensore","stazione_id"]].head(40).to_string())
