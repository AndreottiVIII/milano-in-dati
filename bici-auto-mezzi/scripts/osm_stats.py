import sys, gzip, collections
import xml.etree.ElementTree as ET
hw = collections.Counter(); sig = 0; cyc = collections.Counter(); ow = collections.Counter(); ms = 0; ped_area = 0
nodes = 0; lats = []; lons = []; tagged = collections.Counter(); rel = collections.Counter()
for ev, el in ET.iterparse(gzip.open(sys.argv[1]), events=('end',)):
    if el.tag == 'node':
        nodes += 1
        if nodes % 50 == 0:
            lats.append(float(el.get('lat'))); lons.append(float(el.get('lon')))
        for t in el.findall('tag'):
            if t.get('k') == 'highway': tagged['highway=' + t.get('v')] += 1
            if t.get('k') == 'crossing' : tagged['crossing'] += 1
    elif el.tag == 'way':
        tg = {t.get('k'): t.get('v') for t in el.findall('tag')}
        hw[tg.get('highway')] += 1
        if any(k.startswith('cycleway') for k in tg) or tg.get('highway') == 'cycleway' or tg.get('bicycle') == 'designated': cyc['ciclabile (cycleway*, highway=cycleway o bicycle=designated)'] += 1
        for k in tg:
            if k.startswith('cycleway'): cyc[k + '=' + tg[k]] += 1
        if 'oneway' in tg: ow['oneway=' + tg['oneway']] += 1
        if 'oneway:bicycle' in tg: ow['oneway:bicycle=' + tg['oneway:bicycle']] += 1
        if 'maxspeed' in tg: ms += 1
        if tg.get('highway') == 'pedestrian' : ped_area += 1
        el.clear()
    elif el.tag == 'relation':
        rel[next((t.get('v') for t in el.findall('tag') if t.get('k') in ('type',)), None)] += 1
        el.clear()
print('nodi', nodes, 'lat', min(lats), max(lats), 'lon', min(lons), max(lons))
print('highway ways', sum(hw.values())); print(hw.most_common(25))
print('maxspeed ways', ms); print('oneway', ow.most_common(12)); print('ciclabili', cyc.most_common(14))
print('nodi con tag', tagged.most_common(15)); print('relazioni', rel)
