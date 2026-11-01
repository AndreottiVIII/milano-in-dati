"""Riepilogo copertura per sensore (T: estati complete; P: anni completi) + conteggi di qualita'.
uso: python -I -X utf8 riepilogo_copertura.py <pioggia-e-caldo assoluta>   -> pulito/riepilogo_copertura_sensori.csv"""
import sys, os
import pandas as pd
base = sys.argv[1]
pu = os.path.join(base, 'pulito')
sel = pd.read_csv(os.path.join(pu, 'sensori_selezionati.csv'), dtype=str)
q = pd.read_csv(os.path.join(pu, 'qualita_sensori.csv'), dtype={'idsensore': str})
E = pd.read_csv(os.path.join(pu, 'caldo_estate_sensore.csv'), dtype={'idsensore': str})
A = pd.read_csv(os.path.join(pu, 'pioggia_anno_sensore.csv'), dtype={'idsensore': str})
rows = []
for _, s in sel.iterrows():
    r = dict(idsensore=s.idsensore, tipologia=s.tipologia, nomestazione=s.nomestazione, dist_duomo_km=s.dist_duomo_km, quota=s.quota,
             datastart_registro=s.datastart[:10], datastop_registro=(s.datastop if isinstance(s.datastop, str) else '')[:10], storico=s.storico)
    qq = q[q.idsensore == s.idsensore]
    if len(qq):
        qq = qq.iloc[0]
        r.update(righe=qq.righe, validi=qq.validi, meno999=qq.meno999, stato_non_VA=qq.stato_non_VA, fuori_soglia=qq.fuori_soglia, duplicati=qq.duplicati,
                 primo_dato=str(qq.primo)[:10], ultimo_dato=str(qq.ultimo)[:10])
    if s.tipologia == 'Temperatura':
        e = E[(E.idsensore == s.idsensore) & E.estate_completa]
        r.update(estati_complete=len(e), prima_estate=int(e.anno.min()) if len(e) else None, ultima_estate=int(e.anno.max()) if len(e) else None,
                 anni_mancanti_tra_prima_e_ultima=(int(e.anno.max() - e.anno.min() + 1 - len(e)) if len(e) else None))
    else:
        a = A[(A.idsensore == s.idsensore) & A.anno_completo]
        r.update(anni_completi=len(a), primo_anno=int(a.anno.min()) if len(a) else None, ultimo_anno=int(a.anno.max()) if len(a) else None,
                 anni_mancanti_tra_primo_e_ultimo=(int(a.anno.max() - a.anno.min() + 1 - len(a)) if len(a) else None))
    rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(pu, 'riepilogo_copertura_sensori.csv'), index=False)
print('FATTO')
