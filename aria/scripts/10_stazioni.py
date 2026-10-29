# Fase 2, passo 3: storia delle stazioni e dei sensori.
# uso: python -I scripts/10_stazioni.py raw out pulito
import pandas as pd, numpy as np, os, sys
from math import radians, sin, cos, asin, sqrt
raw,outd,pul=sys.argv[1:4]
reg=pd.read_csv(os.path.join(raw,"arpa","ib47-atvt_stazioni_tutte.csv"),dtype=str)
reg=reg[reg.comune.str.upper()=="MILANO"].copy()
inv=pd.read_csv(os.path.join(outd,"inventario_arpa.csv"),dtype=str).set_index("idsensore")
com=pd.read_csv(os.path.join(raw,"comune","qaria_stazione.csv"),sep=";")
D=pd.read_csv(os.path.join(pul,"aria_giornaliera.csv"),dtype={"id_stazione":str},parse_dates=["data"])
R=pd.read_csv(os.path.join(pul,"riepilogo_annuale.csv"),dtype={"id_stazione":str})

def dist(a,b,c,d):
    a,b,c,d=map(radians,(a,b,c,d)); h=sin((c-a)/2)**2+cos(a)*cos(c)*sin((d-b)/2)**2
    return 2*6371000*asin(sqrt(h))

NOMI={"501":("Marche","viale Marche"),"502":("Juvara","via Juvara"),"503":("Zavattari","piazzale Zavattari"),
      "528":("Verziere","Verziere"),"539":("Liguria","viale Liguria"),"547":("Parco Lambro","Parco Lambro"),
      "548":("Senato","via Senato"),"549":("Abbiategrasso","piazzale Abbiategrasso"),"705":("Pascal","via Pascal (Citta' Studi)")}
COM={"549":1,"705":2,"539":3,"501":4,"547":5,"548":6,"528":7,"503":8,"502":9}
NOTE={
"501":"Aperta per NO2 e CO dal 1980/1989; il PM10 parte solo nel 2018, il PM2.5 nel 2021 (i dati partono dal 30/09/2021, il registro dice 2022). Benzene dal 2012. Per il benzene ARPA non ha dati 2018-2025: usato il Comune (flag da_comune). PM10 e PM2.5 ARPA senza 2025: il Comune ha pochi giorni.",
"502":"CHIUSA l'11/06/2007 e SOSTITUITA da Pascal (705), a circa 925 m di distanza. Non e' la stessa stazione: la serie Juvara e la serie Pascal non vanno unite. Juvara: SO2 e ozono arrivano a meta' luglio 2007, NO2 e polveri all'11/06. Nel 2007 le due stazioni misurano PM10 insieme per 48 giorni (21/04-10/06/2007): media 33,1 (Juvara) contro 34,7 (Pascal), correlazione 0,82.",
"503":"CHIUSA nel 2017 (Comune: 31/08/2017 per NO2; O3/CO fino a fine 2017; registro ARPA: 30/07/2018). I dati ARPA finiscono con il 2016; per il 2017 solo i giorni del Comune (flag da_comune) e solo come massimo orario NO2.",
"528":"Aperta dal 1988. Il CO e' spento dal 04/07/2011, il SO2 dal 2004. Aperta oggi (NO2, O3, PM10). Il Comune la chiama Verziere.",
"539":"Aperta dal 1991. Il CO e' spento dal 03/10/2023 (nel file pulito il CO arriva al 2023). Polveri totali sospese 1995-2013 (non nel file pulito). Non ha PM10/PM2.5.",
"547":"CHIUSA nel 2017 (Comune: 31/08/2017; registro ARPA: 30/07/2018; ozono: 01/01/2018). I dati ARPA finiscono con il 2016. Misurava solo NO2 e ozono.",
"548":"Aperta dal 1995 (NO2, CO), benzene dal 1999, PM10 dal 10/08/2007, PM2.5 dal 04/09/2012. Nel nome Comune c'e' un asterisco non spiegato (via Senato *). Ha anche metalli e benzo(a)pirene (fuori dal file pulito).",
"549":"CHIUSA nel 2017 (Comune: 31/08/2017; registro ARPA: 30/07/2018). I dati ARPA finiscono con il 2016. Misurava solo NO2 (nel file pulito).",
"705":"APERTA nel 2007 al posto di Juvara: NO2/O3/SO2 dal 16/06/2007, PM10 dal 21/04/2007, PM2.5 dal 29/03/2007 (registro ARPA). Le coordinate del Comune e di ARPA differiscono di 531 m: nella mappa si usano quelle di ARPA. Nel nome Comune c'e' un asterisco non spiegato. 2012: NO2 con soli 45% di giorni validi.",
}
SOST={"502":"sostituita_da_705_Pascal_2007","705":"sostituisce_502_Juvara_2007"}
rows=[]
for sid,g in reg.groupby("idstazione"):
    g0=g.iloc[0]; lat,lng=float(g0.lat),float(g0.lng)
    cm=com[com.id_amat==COM[sid]].iloc[0]
    d=dist(lat,lng,float(cm.LAT_Y_4326),float(cm.LONG_X_4326))
    firsts=[inv.loc[s,"prima"][:10] for s in g.idsensore if s in inv.index]
    lasts=[inv.loc[s,"ultima"][:10] for s in g.idsensore if s in inv.index]
    stops=g.datastop.dropna().str[:10]
    chiusa = sid in ("502","503","547","549")
    pul_sid=D[D.id_stazione==sid]
    inq=[]
    for (pc,stat),h in pul_sid.groupby(["inquinante","statistica"]):
        if stat=="max_orario": continue
        rr=R[(R.id_stazione==sid)&(R.inquinante==pc)&(R.statistica==stat)&(R.anno_ok_75==1)]
        inq.append(f"{pc} {h.data.min().year}-{h.data.max().year}")
    rows.append(dict(id_stazione_arpa=sid,id_comune=COM[sid],nome=NOMI[sid][0],posizione=NOMI[sid][1],nome_registro_arpa=g0.nomestazione.replace("�","a'"),
        lat_arpa=lat,lng_arpa=lng,lat_comune=round(float(cm.LAT_Y_4326),6),lng_comune=round(float(cm.LONG_X_4326),6),distanza_coordinate_m=round(d),
        quota_m=g0.quota,primo_dato_arpa=min(firsts),ultimo_dato_arpa=max(lasts) if chiusa else "in corso",
        fine_registro_arpa=(stops.max() if (g.datastop.notna().all() or chiusa) else ""),fine_comune=str(cm.fine_operativita) if str(cm.fine_operativita)[:4]!="2099" else "",
        stato_2026="chiusa" if chiusa else "aperta",sostituzione=SOST.get(sid,""),inquinanti_nel_file_pulito="; ".join(inq),
        cambio_stazione=int(sid in SOST),note=NOTE[sid]))
S=pd.DataFrame(rows).sort_values("id_stazione_arpa")
S.to_csv(os.path.join(pul,"stazioni_storia.csv"),index=False,encoding="utf-8")
print(S[["id_stazione_arpa","nome","distanza_coordinate_m","primo_dato_arpa","ultimo_dato_arpa","fine_registro_arpa","fine_comune","stato_2026"]].to_string())

# sensori
NEL={"Biossido di Azoto","PM10 (SM2005)","Particelle sospese PM2.5","Ozono","Monossido di Carbonio","Benzene"}
SNOTE={"29001":"BlackCarbon: strumento sostituito da 20455 (2020)","20455":"BlackCarbon: succede a 29001","20005":"BlackCarbon: sostituito da 20465 (2020)","20465":"BlackCarbon: succede a 20005",
       "20004":"BlackCarbon: sostituito da 20581 (2023)","20581":"BlackCarbon: succede a 20004","20020":"Ammoniaca: sostituito da 20484 (2020)","20484":"Ammoniaca: succede a 20020",
       "6637":"Polveri totali sospese (PTS): finiscono il 12/02/1998, non sono la stessa cosa del PM10 che inizia il giorno dopo (6905)","6905":"PM10 dal 13/02/1998, dopo le PTS (6637)",
       "5823":"CO spento il 03/10/2023","5838":"CO spento il 04/07/2011","17127":"Nessun dato ARPA 2018-2025 (buco dataset g2hp-ar79)","17126":"Nessun dato ARPA 2018-2025 (buco dataset g2hp-ar79)"}
sr=[]
for _,r in reg.sort_values(["idstazione","nometiposensore","datastart"]).iterrows():
    i=inv.loc[r.idsensore] if r.idsensore in inv.index else None
    sr.append(dict(id_stazione_arpa=r.idstazione,nome=NOMI[r.idstazione][0],idsensore=r.idsensore,tipo=r.nometiposensore,unita=r.unitamisura.replace("�","u") if isinstance(r.unitamisura,str) else "",
        inizio_registro=r.datastart[:10],fine_registro=r.datastop[:10] if isinstance(r.datastop,str) else "",
        primo_dato_valido=i.prima[:10] if i is not None else "",ultimo_dato_valido=i.ultima[:10] if i is not None else "",
        nel_file_pulito="si" if r.nometiposensore in NEL else "no",note=SNOTE.get(r.idsensore,"")))
pd.DataFrame(sr).to_csv(os.path.join(pul,"stazioni_sensori.csv"),index=False,encoding="utf-8")
print("sensori",len(sr))
