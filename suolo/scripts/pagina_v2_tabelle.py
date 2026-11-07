"""Scrive due tabelle semplici per la pagina "Quanto suolo si consuma" (versione 2).
Uso: python -I -X utf8 pagina_v2_tabelle.py <docs_dir>
Legge docs/suolo/data/nil.geojson e riepilogo.json; scrive nella stessa cartella
  quartieri_2006_2025.csv   (consumato 2006 e 2025 in %, punti in piu', terreno nuovo e tornato libero 2012-2025, per quartiere)
  milano_ettari_per_anno.csv (ettari netti, nuovi e tornati liberi per periodo, con ettari all'anno)
Nomi nuovi: non sovrascrive i file della pagina precedente."""
import sys, os, json, csv
d = os.path.join(sys.argv[1], 'suolo', 'data')
g = json.load(open(os.path.join(d, 'nil.geojson'), encoding='utf-8'))
rows = []
for f in g['features']:
    p = f['properties']
    rows.append([p['i'], p['n'], p['ha'], p['p06'], p['p25'], round(p['p25'] - p['p06'], 1), p['n1225'], p['r1225']])
rows.sort(key=lambda r: -r[4])
with open(os.path.join(d, 'quartieri_2006_2025.csv'), 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['id_nil', 'quartiere', 'area_ha', 'consumato_2006_pct', 'consumato_2025_pct', 'punti_in_piu', 'nuovo_2012_2025_ha', 'tornato_libero_2012_2025_ha'])
    w.writerows(rows)
r = json.load(open(os.path.join(d, 'riepilogo.json'), encoding='utf-8'))
with open(os.path.join(d, 'milano_ettari_per_anno.csv'), 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';')
    w.writerow(['periodo', 'anni', 'netto_ha', 'nuovo_ha', 'tornato_libero_ha', 'netto_ha_all_anno'])
    for x in r['milano']['incrementi']:
        w.writerow([x['periodo'], x['anni'], x['netto_ha'], x['lordo_ha'], x['ripristino_ha'], round(x['netto_ha'] / x['anni'], 2)])
print('ok', len(rows))
