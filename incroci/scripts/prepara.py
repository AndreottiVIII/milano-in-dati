"""Passo 1: prende gli incidenti di Milano 2010-2024 gia' puliti e geocodificati dal filone 7 (bici-auto-mezzi)
e scrive pulito/incidenti_geo.csv.gz con le sole colonne che servono (niente eta' dei conducenti).
Uso: python -I -X utf8 prepara.py <ABS cartella bici-auto-mezzi> <ABS cartella incroci>
Il file di partenza (out/f4_incidenti_geo.pkl) nasce da: microdati ISTAT / Regione Lombardia (CC BY 4.0) + registro civici del Comune (CC BY) + OpenStreetMap (ODbL)."""
import sys, pickle
import pandas as pd
F7, S = sys.argv[1], sys.argv[2]
df = pickle.load(open(F7 + '/out/f4_incidenti_geo.pkl', 'rb'))
has = lambda codes: df.va.isin(codes) | df.vb.isin(codes) | df.vc.isin(codes)
o = pd.DataFrame({'anno': df.anno, 'mese': df.mese})
o['livello'] = df.livello                      # civico | civico_approx | incrocio | incrocio_approx | strada | nessuna
o['lon'] = df.lon.round(6); o['lat'] = df.lat.round(6)
o['via1'] = df.via1.fillna(''); o['via2'] = df.via2.fillna('')
o['via1_k'] = df.via1_k.astype(str).where(df.via1_k.notna(), ''); o['via2_k'] = df.via2_k.astype(str).where(df.via2_k.notna(), '')
o['multi'] = df.multi.astype(int); o['fuzzy'] = df.fuzzy.astype(int)
o['interse'] = df.interse                      # 1 incrocio 2 rotatoria 3 intersez. segnalata 4 con semaforo/vigile 5 non segnalata 6 passaggio a livello | 7 rettilineo 8 curva 9 dosso 10 pendenza 11-12 galleria
o['natura'] = df.natura                        # 5 = investimento di pedone
o['tipo_strada'] = df.tipo_strada
o['feriti'] = df.feriti                        # feriti di tutto l'incidente
o['morti'] = df.morti24 + df.morti30           # morti24 = entro 24 ore, morti30 = dopo 24 ore ed entro 30 giorni: si sommano
o['ped_feriti'] = df.ped_feriti; o['ped_morti'] = df.ped_morti
o['bici'] = has([14, 23]).astype(int)
o['moto'] = has([15, 16, 17]).astype(int)      # ciclomotore, motociclo (solo o con passeggero)
o['monop'] = has([22]).astype(int)
o['auto'] = has([1, 2, 3, 4]).astype(int)
o['pesante'] = has([5, 6, 7, 8, 9, 10, 11, 12, 18]).astype(int)   # bus, tram, camion, mezzi speciali
o['ped'] = ((df.ped_feriti + df.ped_morti > 0) | (df.natura == 5)).astype(int)
o.to_csv(S + '/pulito/incidenti_geo.csv.gz', index=False, compression='gzip')
print(len(o), 'righe;', o.livello.value_counts().to_dict())
print('ped', int(o.ped.sum()), 'bici', int(o.bici.sum()), 'moto', int(o.moto.sum()), 'monop', int(o.monop.sum()), 'auto', int(o.auto.sum()))
