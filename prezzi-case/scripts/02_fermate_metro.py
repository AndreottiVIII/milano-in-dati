"""Costruisce pulito/fermate_metro.csv: una riga per fermata di metropolitana (linea, nome, lat, lon, data di apertura, fonte).
Coordinate e nomi: GTFS AMAT (estratto fatto da 01_metro_da_gtfs.py). Date di apertura: tabelle 'Apertura' delle voci
it.wikipedia (M1-M5), controllate con en.wikipedia e con articoli di stampa (vedi NOTE.md).
Uso: python -I 02_fermate_metro.py <metro_stop_ordine.csv> <output fermate_metro.csv>
"""
import csv, sys, collections

SEGMENTI = {
 'M1': [
  ('1964-11-01', 'Sesto Marelli - Lotto', ['SESTO MARELLI','VILLA S.G.','PRECOTTO','GORLA','TURRO','ROVERETO','PASTEUR','LORETO M1','LIMA','P.TA VENEZIA','PALESTRO','SAN BABILA','DUOMO M1','CORDUSIO','CAIROLI','CADORNA FN M1','CONCILIAZIONE','PAGANO','BUONARROTI','AMENDOLA','LOTTO FIERAMILANOCITY']),
  ('1966-04-02', 'Pagano - Gambara', ['WAGNER','DE ANGELI','GAMBARA']),
  ('1975-04-18', 'Gambara - Inganni', ['BANDE NERE','PRIMATICCIO','INGANNI']),
  ('1975-11-08', 'Lotto - QT8', ['QT8']),
  ('1980-04-12', 'QT8 - San Leonardo', ['LAMPUGNANO','URUGUAY','BONOLA','S.LEONARDO']),
  ('1986-09-28', 'San Leonardo - Molino Dorino; Sesto Marelli - Sesto 1 Maggio FS', ['MOLINO DORINO','SESTO RONDO','SESTO 1 MAGGIO FS']),
  ('1992-03-21', 'Inganni - Bisceglie', ['BISCEGLIE']),
  ('2005-09-14', 'Molino Dorino - Rho Fieramilano (apertura provvisoria 30/03/2005, definitiva 14/09/2005)', ['RHO FIERAMILANO']),
  ('2005-12-19', 'fermata di Pero', ['PERO']),
 ],
 'M2': [
  ('1969-09-27', 'Caiazzo - Cascina Gobba', ['CAIAZZO','LORETO M2','PIOLA','LAMBRATE FS','UDINE','CIMIANO','CRESCENZAGO','CASCINA GOBBA']),
  ('1970-04-27', 'Caiazzo - Centrale FS', ['CENTRALE FS']),
  ('1971-07-12', 'Centrale FS - Garibaldi FS', ['GIOIA','GARIBALDI FS']),
  ('1972-12-04', 'Cascina Gobba - Gorgonzola', ['VIMODRONE','CASCINA BURRONA','CERNUSCO SUL NAVIGLIO','VILLA FIORITA','CASSINA DE PECCHI','BUSSERO','VILLA POMPEA','GORGONZOLA']),
  ('1978-03-03', 'Garibaldi FS - Cadorna', ['MOSCOVA','LANZA','CADORNA FN M2']),
  ('1981-06-07', 'Cascina Gobba - Cologno Nord', ['COLOGNO SUD','COLOGNO CENTRO','COLOGNO NORD']),
  ('1983-10-30', 'Cadorna - Porta Genova FS', ['S.AMBROGIO','S.AGOSTINO','P.TA GENOVA F.S.']),
  ('1985-04-13', 'Gorgonzola - Gessate; Porta Genova FS - Romolo', ['CASCINA ANTONIETTA','GESSATE','ROMOLO']),
  ('1994-11-01', 'Romolo - Famagosta', ['FAMAGOSTA']),
  ('2005-04-17', "Famagosta - Piazza Abbiategrasso (la voce it.wikipedia dice 17 aprile nel testo e 17 marzo nell'elenco: giorno da verificare)", ['ABBIATEGRASSO']),
  ('2011-02-20', 'Famagosta - Assago Milanofiori Forum', ['ASSAGO MILANOFIORI NORD','ASSAGO MILANOFIORI FORUM']),
 ],
 'M3': [
  ('1990-05-03', 'Centrale - Duomo', ['CENTRALE FS','REPUBBLICA','TURATI','MONTENAPOLEONE','DUOMO M3']),
  ('1990-12-16', 'Duomo - Porta Romana', ['MISSORI','CROCETTA','PORTA ROMANA']),
  ('1991-05-12', 'Centrale FS - Sondrio; Porta Romana - San Donato', ['SONDRIO','LODI T.I.B.B.','BRENTA','CORVETTO','PORTO DI MARE','ROGOREDO FS','SAN DONATO']),
  ('1995-12-16', 'Sondrio - Zara', ['ZARA']),
  ('2003-12-08', 'Zara - Maciachini', ['MACIACHINI']),
  ('2011-03-26', 'Maciachini - Comasina', ['DERGANO','AFFORI CENTRO','AFFORI FN','COMASINA']),
 ],
 'M4': [
  ('2022-11-26', 'Linate Aeroporto - Dateo', ['LINATE AEROPORTO','REPETTI','STAZIONE FORLANINI','ARGONNE','SUSA','DATEO']),
  ('2023-07-04', 'Dateo - San Babila', ['TRICOLORE','SAN BABILA']),
  ('2024-10-12', 'San Babila - San Cristoforo', ['SFORZA-POLICLINICO','SANTA SOFIA','VETRA','DE AMICIS','SAN AMBROGIO','CONI ZUGNA','CALIFORNIA','BOLIVAR','TOLSTOJ','FRATTINI','GELSOMINI','SEGNERI','SAN CRISTOFORO']),
 ],
 'M5': [
  ('2013-02-10', 'Bignami - Zara', ['BIGNAMI','PONALE','BICOCCA','CA GRANDA','ISTRIA','MARCHE','ZARA']),
  ('2014-03-01', 'Zara - Garibaldi FS', ['ISOLA','GARIBALDI FS']),
  ('2015-04-29', 'Garibaldi FS - San Siro Stadio (prime 5 stazioni)', ['DOMODOSSOLA','LOTTO M5','SEGESTA','SAN SIRO IPPODROMO','SAN SIRO STADIO']),
  ('2015-06-06', 'stazione Portello', ['PORTELLO']),
  ('2015-06-20', 'stazione Cenisio', ['CENISIO']),
  ('2015-09-26', 'stazione Gerusalemme', ['GERUSALEMME']),
  ('2015-10-11', 'stazione Monumentale', ['MONUMENTALE']),
  ('2015-11-14', 'stazione Tre Torri', ['TRE TORRI']),
 ],
}
FONTE = {
 'M1': 'it.wikipedia Linea M1 (Le date delle aperture)',
 'M2': 'it.wikipedia Linea M2 (Le date delle aperture)',
 'M3': 'it.wikipedia Linea M3 (Le date delle aperture)',
 'M4': 'it.wikipedia Linea M4 (tabella Apertura); en.wikipedia; Il Giorno/VareseNews/Sicurauto',
 'M5': 'it.wikipedia Linea M5 (Completamento) ed en.wikipedia Line 5 (tabella stazioni)',
}

inp, out = sys.argv[1], sys.argv[2]
coords = collections.defaultdict(list)
with open(inp, encoding='utf-8', newline='') as f:
    for r in csv.DictReader(f):
        coords[(r['linea'], r['nome'])].append((float(r['lat']), float(r['lon'])))
rows, usati = [], set()
for linea, segs in SEGMENTI.items():
    for data, tratta, nomi in segs:
        for n in nomi:
            c = coords.get((linea, n))
            if not c:
                print('ATTENZIONE: fermata non trovata nel GTFS:', linea, n)
                continue
            usati.add((linea, n))
            lat = sum(x[0] for x in c) / len(c)
            lon = sum(x[1] for x in c) / len(c)
            nome = n.title().replace('Fs', 'FS').replace('Fn', 'FN')
            rows.append([linea, nome, f'{lat:.6f}', f'{lon:.6f}', data, tratta, FONTE[linea]])
mancanti = [k for k in coords if k not in usati]
if mancanti:
    print('ATTENZIONE: fermate GTFS senza data:', mancanti)
with open(out, 'w', encoding='utf-8', newline='') as g:
    w = csv.writer(g)
    w.writerow(['linea', 'fermata', 'lat', 'lon', 'data_apertura', 'tratta', 'fonte'])
    w.writerows(sorted(rows, key=lambda r: (r[0], r[4], r[1])))
print('scritte', len(rows), 'fermate in', out)
