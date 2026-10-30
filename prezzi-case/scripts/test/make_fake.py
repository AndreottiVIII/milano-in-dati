"""Crea un campione FINTO (numeri inventati, solo per provare le procedure) in <cartella_uscita>:
  quotazioni/  3 semestri nel formato A (QI_..._VALORI.csv / _ZONE.csv), 1 semestre nel formato B (barra verticale), con righe di un
               altro comune (Alessandria) che devono essere scartate, e un file dentro uno .zip
  geojson/     perimetri finti F205_AAAAS.json: griglia di quadrati; nel terzo semestre la zona C1 si divide in C1 e C2
Uso: python -I make_fake.py <cartella_uscita>
"""
import os, sys, json, zipfile

out = sys.argv[1]
q = os.path.join(out, 'quotazioni')
g = os.path.join(out, 'geojson')
os.makedirs(q, exist_ok=True)
os.makedirs(g, exist_ok=True)

HV = 'Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona;LinkZona;Cod_Tip;Descr_Tipologia;Stato;Stato_prev;Compr_min;Compr_max;Sup_NL_compr;Loc_min;Loc_max;Sup_NL_loc;'
HZ = 'Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona_Descr;Zona;LinkZona;Cod_tip_prev;Descr_tip_prev;Stato_prev;Microzona;'


def zone_per(sem):
    z = [('B', 'B1', 'MI0001', 8000), ('C', 'C1', 'MI0002', 5000), ('D', 'D1', 'MI0003', 3000)]
    if sem >= '20171':
        z = [('B', 'B1', 'MI0001', 8000), ('C', 'C1', 'MI0002', 5000), ('C', 'C2', 'MI0009', 5200), ('D', 'D1', 'MI0003', 3000)]
    return z


def righe_valori(sem, base_mult):
    r = []
    for fascia, zona, link, base in zone_per(sem):
        b = round(base * base_mult)
        r.append(f'NORD-OVEST;LOMBARDIA;MI;3015146;C1AA; ;F205;MILANO;{fascia};{zona};{link};20;Abitazioni civili;NORMALE;P;{b};{b + 1000};L;{b / 300:.1f}'.replace('.', ',') + f';{(b + 1000) / 300:.1f}'.replace('.', ',') + ';L;')
        r.append(f'NORD-OVEST;LOMBARDIA;MI;3015146;C1AA; ;F205;MILANO;{fascia};{zona};{link};20;Abitazioni civili;OTTIMO;;{b + 500};{b + 1800};L;0;0;L;')
        r.append(f'NORD-OVEST;LOMBARDIA;MI;3015146;C1AA; ;F205;MILANO;{fascia};{zona};{link};13;Box;NORMALE;P;{b // 3};{b // 3 + 300};L;4,0;6,0;L;')
    r.append('NORD-OVEST;PIEMONTE;AL;1006003;A2AA; ;A182;ALESSANDRIA;B;B1;AL00000001;20;Abitazioni civili;NORMALE;P;810;1000;L;4;5,1;L;')
    return r


def righe_zone(sem):
    r = []
    for fascia, zona, link, base in zone_per(sem):
        r.append(f"NORD-OVEST;LOMBARDIA;MI;3015146;C1AA; ;F205;MILANO;{fascia};'ZONA FINTA {zona}';{zona};{link};20;Abitazioni civili;N;0;")
    r.append("NORD-OVEST;PIEMONTE;AL;1006003;A2AA; ;A182;ALESSANDRIA;B;'CENTRO URBANO';B1;AL00000001;20;Abitazioni civili;N;0;")
    return r


mult = {'20161': 1.0, '20162': 1.02, '20171': 1.05}
for sem, m in mult.items():
    a, s = sem[:4], sem[4]
    num = {'20161': 900001, '20162': 900002, '20171': 900003}[sem]
    with open(os.path.join(q, f'QI_{num}_1_{sem}_VALORI.csv'), 'w', encoding='utf-8', newline='') as f:
        f.write(f'Quotazioni Immobiliari : Valori di Mercato - Semestre {a}/{s} - elaborazione del 01-GEN-27\n' + HV + '\n' + '\n'.join(righe_valori(sem, m)) + '\n')
    # il file ZONE del secondo semestre lo metto dentro uno zip, in cp1252, per provare anche questo
    zt = f'Quotazioni Immobiliari : Informazioni di Zona OMI - Semestre {a}/{s} - elaborazione del 01-GEN-27\n' + HZ + '\n' + '\n'.join(righe_zone(sem)) + '\n'
    if sem == '20162':
        with zipfile.ZipFile(os.path.join(q, f'QI_{num}_1_{sem}.zip'), 'w') as z:
            z.writestr(f'QI_{num}_1_{sem}_ZONE.csv', zt.encode('cp1252'))
    else:
        with open(os.path.join(q, f'QI_{num}_1_{sem}_ZONE.csv'), 'w', encoding='utf-8', newline='') as f:
            f.write(zt)

# formato B (prima del 2016), inventato seguendo il tracciato: separatore |
hb = 'AREA_TERR|PROV|CODISTAT|COD_NAZ|COMUNE|DESC_COMUNE|FASCIA|ZONA|DESCRIZIONE_ZONA|MICROZONA|COD_TIP_PREV|STATO_PREVALENTE|TIPOLOGIA|STATO|VALMIN|VALMAX|SUP_NL_MER|LOCMIN|LOCMAX|SUP_NL_LOCAZ'
rb = [f'NORD-OVEST|MI|15146|F205|F205|MILANO|{f}|{z}|FINTA|0|20|N|20|NORMALE|{b // 2}|{b // 2 + 800}|L|{b / 600:.1f}|{b / 600 + 1:.1f}|L' for f, z, l, b in zone_per('20161')]
with open(os.path.join(q, 'QI_900000_1_20101_VALORI.csv'), 'w', encoding='cp1252', newline='') as f:
    f.write('Quotazioni Immobiliari - Valori di Mercato - Semestre 2010/1\n' + hb + '\n' + '\n'.join(rb) + '\n')


# ---- perimetri finti: griglia 1 km x 1 km a nord di Milano (lon/lat), ogni zona un quadrato; una zona con 2 pezzi staccati (anelli)
def quad(x0, y0, w=0.01, h=0.01):
    return [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]]


def feat(zona, anelli):
    return {'type': 'Feature', 'id': zona, 'geometry': {'type': 'Polygon', 'coordinates': anelli}, 'properties': {'zona': zona, 'codCom': 'F205'}}


X0, Y0 = 9.15, 45.45
base = {'B1': [quad(X0, Y0)], 'C1': [quad(X0 + 0.01, Y0)], 'D1': [quad(X0 + 0.02, Y0), quad(X0 + 0.04, Y0)]}   # D1 = due pezzi staccati
base_new = {'B1': [quad(X0, Y0)], 'C1': [quad(X0 + 0.01, Y0, 0.005)], 'C2': [quad(X0 + 0.015, Y0, 0.005)], 'D1': [quad(X0 + 0.02, Y0), quad(X0 + 0.04, Y0)]}
for sem, zs in (('20161', base), ('20162', base), ('20171', base_new)):
    fc = {'cod': 0, 'msg': '', 'dat': {'type': 'FeatureCollection', 'features': [feat(z, a) for z, a in zs.items()]}}
    json.dump(fc, open(os.path.join(g, f'F205_{sem}.json'), 'w'))
print('campione finto scritto in', out)
