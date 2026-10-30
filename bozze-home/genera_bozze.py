# -*- coding: utf-8 -*-
"""Genera 4 bozze quadrate (1080x1080, SVG autonome) per la home di "Milano in dati".
Legge solo i dati gia' pubblicati in docs/ (non li modifica).
Uso: python -I genera_bozze.py
"""
import json, math, os
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union

QUI = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(QUI, '..', 'docs')

def carica(p):
    with open(os.path.join(DOCS, p), encoding='utf-8') as f:
        return json.load(f)

# ---------------------------------------------------------------- dati
GEO = carica('censimenti/data/nil.geojson')
CENS = carica('censimenti/data/dati.json')
NILINFO = {n['i']: n for n in CENS['nil']}
AREAC = carica('area-c/data/confine.json')
TEMP = carica('temperature/data/annuale.json')['anni']
STAZ = carica('nomi-fermate/data/stazioni.json')
CIN = carica('cinema-spariti/data/serie.json')['istantanee']

NIL = {}
for f in GEO['features']:
    g = shape(f['geometry']).simplify(0.00012, preserve_topology=True)
    NIL[f['properties']['i']] = g
COMUNE = unary_union(list(NIL.values())).buffer(0.00005).simplify(0.0001)

LAT0, LON0 = 45.4642, 9.1900          # Duomo
K = math.cos(math.radians(LAT0))

def km(lon, lat):
    return ((lon - LON0) * K * 111.32, -(lat - LAT0) * 111.32)

class Proj:
    """proiezione equirettangolare (cos lat) adattata a un riquadro, oppure centrata con scala fissa"""
    def __init__(self, box=None, centro=None, scala=None):
        if box:
            x0, y0, w, h = box
            bx = [km(*c) for c in COMUNE.exterior.coords] if COMUNE.geom_type == 'Polygon' else \
                 [km(*c) for p in COMUNE.geoms for c in p.exterior.coords]
            mnx = min(p[0] for p in bx); mxx = max(p[0] for p in bx)
            mny = min(p[1] for p in bx); mxy = max(p[1] for p in bx)
            s = min(w / (mxx - mnx), h / (mxy - mny))
            self.s = s
            self.ox = x0 + (w - (mxx - mnx) * s) / 2 - mnx * s
            self.oy = y0 + (h - (mxy - mny) * s) / 2 - mny * s
        else:
            self.s = scala
            self.ox, self.oy = centro
    def __call__(self, lon, lat):
        x, y = km(lon, lat)
        return (self.ox + x * self.s, self.oy + y * self.s)

def anelli(g):
    if g.geom_type == 'Polygon':
        return [g.exterior] + list(g.interiors)
    out = []
    for p in g.geoms:
        out += [p.exterior] + list(p.interiors)
    return out

def path(g, P):
    d = []
    for r in anelli(g):
        pts = [P(*c) for c in r.coords]
        d.append('M' + 'L'.join('%.1f,%.1f' % p for p in pts) + 'Z')
    return ''.join(d)

def centro_nil(i, P):
    c = NIL[i].representative_point()
    return P(c.x, c.y)

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def svg(body, bg, titolo):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">\n'
            '<title>%s</title>\n<rect width="1080" height="1080" fill="%s"/>\n%s\n</svg>\n') % (esc(titolo), bg, body)

def T(x, y, s, size, fill, font, weight='400', anchor='start', extra=''):
    return '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" fill="%s" text-anchor="%s" %s>%s</text>' % (
        x, y, font, size, weight, fill, anchor, extra, esc(s))

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
GROT = "Segoe UI, Helvetica Neue, Arial, sans-serif"
IMPACT = "Impact, Haettenschweiler, Arial Narrow, Arial Black, sans-serif"

def salva(nome, contenuto):
    p = os.path.join(QUI, nome)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(contenuto)
    print(nome, round(len(contenuto.encode('utf-8')) / 1024), 'KB')

# =================================================================== BOZZA 1
def bozza1():
    ROSSO = '#D7001E'; NERO = '#141414'
    P = Proj(box=(150, 175, 860, 760))
    dx, dy = P(LON0, LAT0)
    b = []
    # croce di Sant'Ambrogio: due bracci rossi che attraversano il quadrato e si incrociano sul Duomo
    b.append('<rect x="0" y="%.1f" width="1080" height="26" fill="%s"/>' % (dy - 13, ROSSO))
    b.append('<rect x="%.1f" y="0" width="26" height="1080" fill="%s"/>' % (dx - 13, ROSSO))
    # sagoma bianca della citta' sopra la croce
    b.append('<path d="%s" fill="#fff" stroke="#fff" stroke-width="18" stroke-linejoin="round"/>' % path(COMUNE, P))
    # mosaico: stranieri 2023
    classi = [(0, '#FDE3E3'), (10, '#F9B7B9'), (15, '#F07F84'), (20, '#E3394A'), (25, '#C0001E'), (30, '#7A0014')]
    b.append('<defs><pattern id="tr" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<rect width="7" height="7" fill="#eee"/><line x1="0" y1="0" x2="0" y2="7" stroke="#bbb" stroke-width="3"/></pattern></defs>')
    for i, g in NIL.items():
        n = NILINFO[i]; v = n['v']['str'][4]
        if v is None or not n['ok']:
            fill = 'url(#tr)'
        else:
            fill = [c for t, c in classi if v >= t][-1]
        b.append('<path d="%s" fill="%s" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/>' % (path(g, P), fill))
    # anello di Area C (Bastioni) come filo nero
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.5" stroke-dasharray="6 4"/>' % (path(shape(AREAC['geometry']).simplify(0.0001), P), NERO))
    # titolo
    b.append(T(40, 98, 'Milano', 96, NERO, SANS, '900', extra='letter-spacing="-3"'))
    b.append(T(40, 152, 'in dati', 54, ROSSO, SANS, '900', extra='letter-spacing="-1"'))
    b.append(T(1040, 60, '88 quartieri, 17 storie', 22, NERO, SANS, '700', 'end'))
    b.append(T(1040, 86, 'raccontate con i dati aperti', 18, '#444', SANS, '400', 'end'))
    # etichette che galleggiano
    linee, scatole = [], []
    def tag(i, tx, ty, num, testo, colore=NERO, anchor='start'):
        cx, cy = centro_nil(i, P)
        w = max(len(num) * 26, max(len(r) for r in testo) * 9.2) + 24
        h = 50 + 21 * len(testo)
        x = tx if anchor == 'start' else tx - w
        y = ty - 22
        ax = min(max(cx, x), x + w); ay = min(max(cy, y), y + h)   # attacco sul bordo piu' vicino
        linee.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="2"/>' % (cx, cy, ax, ay, NERO))
        linee.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#fff" stroke="%s" stroke-width="2.5"/>' % (cx, cy, NERO))
        out = ['<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#fff" stroke="%s" stroke-width="2.5"/>' % (x, y, w, h, NERO)]
        out.append(T(x + 12, ty + 22, num, 42, colore, SANS, '900', extra='letter-spacing="-1"'))
        for k, r in enumerate(testo):
            out.append(T(x + 12, ty + 46 + 21 * k, r, 16, NERO, SANS, '500'))
        scatole.append('\n'.join(out))
    tag(82, 640, 190, '38%', ['stranieri a Comasina', '(0,5% nel 1991)'], ROSSO)
    tag(2, 770, 330, '1763', ['a Brera si misura la', 'temperatura dal 1763:', 'il 2026 è il più caldo (finora)'])
    tag(57, 40, 545, '246', ['derby a San Siro e dintorni:', 'Inter 91, pari 71, Milan 84'])
    tag(1, 800, 520, '4.635', ['titoli alla Scala', 'dal 1778'])
    tag(64, 40, 290, '50,6', ['anni, età media a Trenno', '(36,6 nel 1991)'])
    tag(33, 860, 780, '+172%', ['abitanti a Rogoredo-', 'Santa Giulia dal 1991'])
    tag(43, 130, 830, '10/10', ['a Tibaldi tutti i servizi', 'a 15 minuti a piedi'])
    b += linee + scatole
    # legenda
    lx, ly = 40, 990
    b.append(T(lx, ly - 24, 'Residenti stranieri nel 2023, quartiere per quartiere', 17, NERO, SANS, '700'))
    for k, (t, c) in enumerate(classi):
        b.append('<rect x="%d" y="%d" width="56" height="18" fill="%s"/>' % (lx + k * 58, ly - 12, c))
        b.append(T(lx + k * 58, ly + 26, ('%d%%' % t) if k else '0', 14, NERO, SANS))
    b.append('<rect x="%d" y="%d" width="56" height="18" fill="url(#tr)"/>' % (lx + 6 * 58 + 12, ly - 12))
    b.append(T(lx + 6 * 58 + 12, ly + 26, 'dato poco solido', 14, NERO, SANS))
    # numero grande in basso a destra
    b.append(T(1040, 1000, '19,6%', 88, ROSSO, SANS, '900', 'end', 'letter-spacing="-3"'))
    b.append(T(1040, 1040, 'stranieri nel 2023 (1,9% nel 1991)', 18, NERO, SANS, '700', 'end', 'stroke="#fff" stroke-width="6" paint-order="stroke"'))
    salva('bozza_1_mosaico.svg', svg('\n'.join(b), '#FFFFFF', 'Milano in dati - bozza 1, mosaico'))

# =================================================================== BOZZA 2
LINEE = {'M1': '#E3001B', 'M2': '#00A650', 'M3': '#FFD200', 'M4': '#0072BC', 'M5': '#9B5BA5'}

def bozza2():
    P = Proj(box=(20, 170, 1040, 900))
    b = []
    # Milano sullo sfondo: sagoma, Area C, fermate vere (puntini)
    b.append('<path d="%s" fill="#F1F1F1" stroke="#DADADA" stroke-width="2"/>' % path(COMUNE, P))
    for i, g in NIL.items():
        b.append('<path d="%s" fill="none" stroke="#E2E2E2" stroke-width="1"/>' % path(g, P))
    for s in STAZ:
        x, y = P(s['lon'], s['lat'])
        b.append('<circle cx="%.1f" cy="%.1f" r="2.6" fill="%s" opacity=".45"/>' % (x, y, LINEE[s['l'][0]]))
    # fascia rossa in alto come le insegne del metro
    b.append('<rect width="1080" height="140" fill="#E3001B"/>')
    b.append('<rect y="140" width="1080" height="8" fill="#141414"/>')
    b.append(T(40, 95, 'Milano in dati', 74, '#fff', SANS, '700', extra='letter-spacing="-1"'))
    b.append(T(1040, 70, '17 fermate', 26, '#fff', SANS, '700', 'end'))
    b.append(T(1040, 102, '5 linee · 1 città', 22, '#fff', SANS, '400', 'end'))

    H = (540, 600)
    # linee: lista di punti (polilinee) e fermate (punto, nome, numero, lato etichetta)
    L = {
        'M1': [(70, 600), (1010, 600)],
        'M3': [(540, 245), (540, 860), (640, 960)],
        'M2': [(880, 260), (270, 870)],
        'M4': [(300, 360), (860, 920)],
        'M5': [(80, 245), (540, 245)],
    }
    FERMATE = [
        # (x, y, linee, nome, numero, dx, dy, anchor)
        (110, 600, 'M1', 'Temperature', 'dal 1763 · 2026 il più caldo (finora)', -20, 48, 'start'),
        (330, 600, 'M1', 'Neve e nebbia', 'neve: da 10,5 a 2 giorni', -10, -48, 'start'),
        (745, 600, 'M1', 'Aria', 'NO₂: 41,9 µg/m³ in viale Marche', 8, -48, 'start'),
        (960, 600, 'M1', 'Acqua del sindaco', 'nei limiti in ogni zona', 50, 48, 'end'),
        (540, 370, 'M3', 'Bici, auto o mezzi', '88%: alle 8 vince la bici', 26, 6, 'start'),
        (540, 800, 'M3', 'Area C', '−16% ingressi dal 2019', 26, 6, 'start'),
        (640, 960, 'M3', 'La città dei 15 minuti', 'biblioteca vicina per il 46,5%', 26, 6, 'start'),
        (700, 440, 'M2', 'Censimenti', 'stranieri: 1,9% → 19,6%', 22, 8, 'start'),
        (850, 290, 'M2', 'Elezioni', '167 elezioni dal 1946', 22, 8, 'start'),
        (330, 810, 'M2', 'Donne nelle vie', '6,6% delle vie', -36, 8, 'end'),
        (400, 460, 'M4', 'La Scala', '4.635 titoli dal 1778', -22, 8, 'end'),
        (300, 360, 'M4', 'Beni culturali', '27.459 schede', -24, 8, 'end'),
        (700, 760, 'M4', 'Milano raccontata', '435 film, 280 libri', 30, -6, 'start'),
        (840, 900, 'M4', 'Cinema spariti', '171 sale chiuse', 30, -6, 'start'),
        (540, 245, 'M3', 'Nomi delle fermate', '1 donna su 33 nomi', 26, -36, 'start'),
        (330, 245, 'M5', 'Violenza politica', '84 fatti dal 1919', 0, -48, 'middle'),
        (110, 245, 'M5', 'Il derby', '246 · Inter 91, pari 71, Milan 84', -30, 48, 'start'),
    ]
    order = ['M5', 'M4', 'M2', 'M1', 'M3']
    for l in order:
        pts = L[l]
        d = 'M' + 'L'.join('%d,%d' % p for p in pts)
        b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="24" stroke-linecap="round" stroke-linejoin="round"/>' % d)
        b.append('<path d="%s" fill="none" stroke="%s" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>' % (d, LINEE[l]))
    # interscambi: hub e Nomi delle fermate (M3/M5)
    for (x, y) in [(540, 245)]:
        b.append('<rect x="%d" y="%d" width="40" height="22" rx="11" fill="#fff" stroke="#141414" stroke-width="4" transform="rotate(0)"/>' % (x - 20, y - 11))
    for x, y, l, nome, num, ox, oy, an in FERMATE:
        if (x, y) != (540, 245):
            b.append('<circle cx="%d" cy="%d" r="11" fill="#fff" stroke="#141414" stroke-width="4"/>' % (x, y))
        alone = 'stroke="#fff" stroke-width="6" stroke-linejoin="round" paint-order="stroke"'
        b.append(T(x + ox, y + oy, nome, 21, '#141414', SANS, '700', an, alone))
        b.append(T(x + ox, y + oy + 22, num, 16, '#333', SANS, '400', an, alone))
    # stazione centrale: Duomo (tutte le linee)
    hx, hy = H
    b.append('<circle cx="%d" cy="%d" r="38" fill="#fff" stroke="#141414" stroke-width="6"/>' % H)
    b.append(T(hx, hy - 4, 'DUOMO', 15, '#141414', SANS, '800', 'middle', 'letter-spacing="1"'))
    b.append(T(hx, hy + 14, 'home', 13, '#555', SANS, '400', 'middle'))
    # legenda linee
    leg = [('M1', 'clima e ambiente'), ('M2', 'chi siamo'), ('M3', 'muoversi'), ('M4', 'cultura'), ('M5', 'passioni e conflitti')]
    for k, (l, t) in enumerate(leg):
        x = 40 + k * 205; y = 1046
        b.append('<rect x="%d" y="%d" width="44" height="26" rx="4" fill="%s"/>' % (x, y - 19, LINEE[l]))
        b.append(T(x + 22, y, l, 17, '#141414' if l == 'M3' else '#fff', SANS, '800', 'middle'))
        b.append(T(x + 52, y, t, 16, '#141414', SANS, '500'))
    salva('bozza_2_metro.svg', svg('\n'.join(b), '#FFFFFF', 'Milano in dati - bozza 2, metro'))

# =================================================================== BOZZA 3
def bozza3():
    BLU = '#071E36'; BLU2 = '#0E3358'; ARANCIO = '#FF7A00'; GIALLO = '#FFC20E'; ACQUA = '#3FB7E6'
    C = (560, 560)
    R_T1, R_T2 = 448, 512           # anello delle temperature
    R_S1, R_S2 = 286, 430           # anello delle 16 storie
    b = []
    b.append('<defs><clipPath id="cc"><circle cx="%d" cy="%d" r="%d"/></clipPath></defs>' % (C[0], C[1], R_S1 - 10))
    # --- anello del tempo: una fetta per anno 1763-2026
    anni = [a for a in TEMP]
    vals = [a['tmedia'] for a in anni if a['ok']]
    lo, hi = min(vals), max(vals)
    def colore_t(v):
        t = (v - lo) / (hi - lo)
        stops = [(0, (8, 48, 107)), (0.35, (66, 146, 198)), (0.55, (235, 235, 235)), (0.75, (255, 160, 40)), (0.9, (240, 70, 20)), (1, (180, 0, 30))]
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                return '#%02x%02x%02x' % tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3))
        return '#b4001e'
    n = len(anni); gap = 22  # gradi lasciati aperti in alto per l'etichetta
    a0 = -90 + gap / 2; span = 360 - gap
    def polar(r, ang):
        a = math.radians(ang)
        return (C[0] + r * math.cos(a), C[1] + r * math.sin(a))
    def fetta(r1, r2, g1, g2, fill, extra=''):
        p1 = polar(r2, g1); p2 = polar(r2, g2); p3 = polar(r1, g2); p4 = polar(r1, g1)
        large = 1 if g2 - g1 > 180 else 0
        return '<path d="M%.1f,%.1fA%d,%d 0 %d 1 %.1f,%.1fL%.1f,%.1fA%d,%d 0 %d 0 %.1f,%.1fZ" fill="%s" %s/>' % (
            p1[0], p1[1], r2, r2, large, p2[0], p2[1], p3[0], p3[1], r1, r1, large, p4[0], p4[1], fill, extra)
    for k, a in enumerate(anni):
        g1 = a0 + span * k / n; g2 = a0 + span * (k + 1) / n + 0.05
        v = a['tmedia']
        fill = colore_t(v) if a['ok'] else '#b4001e'   # 2026: il piu' caldo finora (stesso periodo)
        b.append(fetta(R_T1, R_T2, g1, g2, fill))
    # etichette dell'anello del tempo
    p = polar(R_T2 + 2, a0); b.append(T(p[0] + 8, p[1] - 6, '1763', 20, '#fff', GROT, '700'))
    p = polar(R_T2 + 2, a0 + span); b.append(T(p[0] - 8, p[1] - 6, '2026', 20, '#fff', GROT, '700', 'end'))
    # --- mappa al centro, ritagliata nel cerchio
    P = Proj(centro=C, scala=46)
    b.append('<circle cx="%d" cy="%d" r="%d" fill="%s"/>' % (C[0], C[1], R_S1 - 10, BLU2))
    g = ['<g clip-path="url(#cc)">']
    for i, gg in NIL.items():
        g.append('<path d="%s" fill="#13426E" stroke="%s" stroke-width="1.2"/>' % (path(gg, P), BLU))
    # circonvallazione esterna (tracciato indicativo: ellisse) - filobus 90/91
    g.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="none" stroke="%s" stroke-width="5" stroke-dasharray="14 7"/>' % (
        P(9.183, 45.465)[0], P(9.183, 45.465)[1], 3.0 * 46, 2.45 * 46, GIALLO))
    # Bastioni = confine di Area C (geometria vera)
    g.append('<path d="%s" fill="none" stroke="%s" stroke-width="6" stroke-linejoin="round"/>' % (path(shape(AREAC['geometry']).simplify(0.0002), P), ARANCIO))
    # Cerchia dei Navigli (tracciato indicativo)
    g.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="6"/>' % (P(9.1905, 45.4655)[0], P(9.1905, 45.4655)[1], 0.82 * 46, ACQUA))
    g.append('</g>')
    b += g
    b.append('<circle cx="%d" cy="%d" r="7" fill="#fff"/>' % C)
    b.append(T(C[0], C[1] + 24, 'Duomo', 15, '#fff', GROT, '700', 'middle'))
    # etichette anelli della citta'
    al = 'stroke="%s" stroke-width="5" stroke-linejoin="round" paint-order="stroke"' % BLU2
    b.append(T(C[0], C[1] - 46, 'Cerchia dei Navigli', 13, ACQUA, GROT, '700', 'middle', al))
    b.append(T(C[0], C[1] - 100, 'Bastioni · Area C', 14, ARANCIO, GROT, '700', 'middle', al))
    b.append(T(C[0], C[1] - 143, 'Circonvallazione', 14, GIALLO, GROT, '700', 'middle', al))
    # --- anello delle storie: 16 settori
    ST = [
        ('Derby', '246', 'derby', ('split', [91, 71, 84])),
        ('Cinema spariti', '171', 'sale chiuse', ('bars', [c['chiuse'] + c['aperte_note'] for c in CIN])),
        ('La Scala', '4.635', 'titoli dal 1778', ('dots', 25)),   # un punto per decennio
        ('Milano raccontata', '435', 'film', ('dots', 22)),       # un punto ogni 20 film
        ('Beni culturali', '27.459', 'schede', ('dots', 27)),     # un punto ogni 1.000
        ('Donne nelle vie', '6,6%', 'vie a donne', ('pct', 6.6)),
        ('Nomi fermate', '1/33', 'una donna', ('pct', 100 / 33)),
        ('Censimenti', '19,6%', 'stranieri', ('pct2', [1.9, 19.6])),
        ('Elezioni', '167', 'dal 1946', ('dots', 17)),            # un punto ogni 10
        ('Violenza politica', '84', 'fatti', ('dots', 21)),        # un punto ogni 4
        ('Area C', '−16%', 'ingressi', ('bars', [163.2, 137.0])),
        ('Bici, auto, mezzi', '88%', 'bici prima', ('pct', 88)),
        ('15 minuti', '46,5%', 'biblioteca', ('pct', 46.5)),
        ('Aria', '41,9', 'NO₂ µg/m³ v. Marche', ('lim', [41.9, 40, 50])),
        ('Acqua', '4 su 4', 'zone in regola', ('pct', 100)),
        ('Neve', '2', 'giorni l’anno', ('bars', [10.5, 8.0, 10.5, 9.0, 5.8, 7.1, 8.3, 2.0])),
    ]
    m = len(ST); step = 360 / m
    for k, (nome, num, sub, (tipo, dati)) in enumerate(ST):
        g1 = -90 + k * step + 0.8; g2 = -90 + (k + 1) * step - 0.8; gm = (g1 + g2) / 2
        fill = BLU2 if k % 2 == 0 else '#0B2B4C'
        b.append(fetta(R_S1, R_S2, g1, g2, fill))
        # mini grafico lungo il bordo esterno del settore
        r1, r2 = R_S2 - 26, R_S2 - 6          # fascia del mini grafico, lungo il bordo esterno
        A = lambda f: g1 + 3 + (g2 - g1 - 6) * f
        if tipo == 'pct':
            b.append(fetta(r1 + 6, r2 - 6, A(0), A(1), '#1d4a75'))
            b.append(fetta(r1 + 6, r2 - 6, A(0), A(min(dati, 100) / 100), ARANCIO))
        elif tipo in ('pct2', 'lim'):
            if tipo == 'pct2':
                fv, ft = dati[1] / 40, dati[0] / 40
            else:
                fv, ft = dati[0] / dati[2], dati[1] / dati[2]
            b.append(fetta(r1 + 6, r2 - 6, A(0), A(1), '#1d4a75'))
            b.append(fetta(r1 + 6, r2 - 6, A(0), A(fv), ARANCIO))
            b.append(fetta(r1 + 1, r2 - 1, A(ft) - 0.5, A(ft) + 0.5, '#fff'))
        elif tipo == 'split':
            tot = sum(dati); cur = 0; cols = ['#2E6FD8', '#9fb3c8', '#E3001B']
            for v, c in zip(dati, cols):
                b.append(fetta(r1 + 3, r2 - 3, A(cur / tot), A((cur + v) / tot) - 0.4, c)); cur += v
        elif tipo == 'bars':
            mx = max(dati); q = len(dati)
            for j, v in enumerate(dati):
                b.append(fetta(r1, r1 + (r2 - r1) * v / mx, A(j / q), A((j + 1) / q) - 0.4, GIALLO))
        elif tipo == 'dots':
            for j in range(dati):
                p = polar(r2 - 2 - 8 * (j // 10), A((j % 10 + .5) / 10))
                b.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="%s"/>' % (p[0], p[1], ARANCIO))
        # testo (orizzontale): nome, numero, didascalia, centrati nel settore
        p = polar(R_S1 + 58, gm)
        b.append(T(p[0], p[1] - 22, nome.upper(), 9.5, GIALLO, GROT, '700', 'middle', 'letter-spacing="0.6"'))
        b.append(T(p[0], p[1] + 6, num, 25, '#fff', GROT, '800', 'middle'))
        b.append(T(p[0], p[1] + 22, sub, 11.5, '#cfe3f5', GROT, '500', 'middle'))
    # --- angoli
    b.append(T(28, 66, 'Milano', 54, '#fff', GROT, '900', extra='letter-spacing="-1.5"'))
    b.append(T(28, 112, 'in dati', 40, ARANCIO, GROT, '900'))
    b.append(T(1052, 44, 'un cerchio di storie', 18, '#fff', GROT, '700', 'end'))
    b.append(T(1052, 68, 'intorno ai cerchi della città', 15, '#cfe3f5', GROT, '400', 'end'))
    b.append(T(28, 1000, 'L’anello esterno è il tempo:', 15, '#fff', GROT, '700'))
    b.append(T(28, 1020, 'una fetta per anno a Brera,', 15, '#cfe3f5', GROT, '400'))
    b.append(T(28, 1040, 'dal 1763 al 2026', 15, '#cfe3f5', GROT, '400'))
    b.append(T(1052, 1010, '2026', 50, '#FF4D2E', GROT, '900', 'end'))
    b.append(T(1052, 1040, 'l’anno più caldo (finora)', 15, '#fff', GROT, '700', 'end'))
    salva('bozza_3_cerchi.svg', svg('\n'.join(b), BLU, 'Milano in dati - bozza 3, cerchi'))

# =================================================================== BOZZA 4
def bozza4():
    ROSSO = '#E1001A'; NERO = '#111111'; BIANCO = '#FFFFFF'
    b = []
    # linee-forza alla Boccioni: raggi da un punto fuori quadro
    O = (-160, 1260)
    import random
    random.seed(1910)
    ang = -80
    while ang < -2:
        w = random.uniform(1.2, 4.5)
        a1, a2 = math.radians(ang), math.radians(ang + w)
        L = 2200
        p1 = (O[0] + L * math.cos(a1), O[1] + L * math.sin(a1))
        p2 = (O[0] + L * math.cos(a2), O[1] + L * math.sin(a2))
        col = random.choice(['#B80016', '#C9001A', '#F0213A', '#B80016'])
        b.append('<path d="M%d,%dL%.0f,%.0fL%.0f,%.0fZ" fill="%s"/>' % (O[0], O[1], p1[0], p1[1], p2[0], p2[1], col))
        ang += w + random.uniform(1.5, 6)
    # grande banda nera diagonale
    b.append('<path d="M-50,690 L1130,330 L1130,520 L-50,880 Z" fill="%s"/>' % NERO)
    # mappa nel tondo (in alto a destra)
    P = Proj(box=(760, 40, 290, 270))
    b.append('<circle cx="905" cy="175" r="158" fill="%s"/>' % BIANCO)
    for i, g in NIL.items():
        b.append('<path d="%s" fill="%s" stroke="%s" stroke-width="0.8"/>' % (path(g, P), NERO, BIANCO))
    dx, dy = P(LON0, LAT0)
    b.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s" stroke="#fff" stroke-width="2"/>' % (dx, dy, ROSSO))
    b.append(T(905, 352, '88 QUARTIERI', 20, BIANCO, IMPACT, '400', 'middle', 'letter-spacing="3"'))
    # titolo enorme, inclinato
    b.append('<g transform="rotate(-17 540 540)">')
    b.append(T(10, 488, 'MILANO', 270, BIANCO, IMPACT, '400', extra='letter-spacing="-4"'))
    b.append(T(1045, 662, 'IN DATI', 140, BIANCO, IMPACT, '400', 'end', 'letter-spacing="3"'))
    # dentro la banda nera, a sinistra
    b.append(T(30, 640, '19,6%', 104, ROSSO, IMPACT, '400', extra='letter-spacing="-2"'))
    b.append(T(36, 672, 'RESIDENTI STRANIERI (1,9% NEL 1991)', 17, BIANCO, GROT, '800'))
    b.append('</g>')
    # numeri giganti sparsi (parole in liberta')
    def num(x, y, n, size, col, rot, didas, dcol=None, dsize=22):
        out = ['<g transform="translate(%d %d) rotate(%d)">' % (x, y, rot)]
        out.append(T(0, 0, n, size, col, IMPACT, '400', extra='letter-spacing="-2"'))
        for k, r in enumerate(didas):
            out.append(T(6, 30 + k * (dsize + 4), r, dsize, dcol or col, GROT, '800'))
        out.append('</g>')
        return '\n'.join(out)
    b.append(num(40, 160, '1763', 150, NERO, 0, ['TEMPERATURE A BRERA DAL 1763:', 'IL 2026 È IL PIÙ CALDO (FINORA)'], NERO, 20))
    b.append(num(370, 140, '6,6%', 110, BIANCO, 0, ['VIE CON NOME DI DONNA'], BIANCO, 17))
    b.append(num(560, 875, '88%', 160, BIANCO, -17, ['ALLE 8 IN BICI SI ARRIVA PRIMA'], BIANCO, 21))
    b.append(num(40, 995, '246', 140, BIANCO, 0, ['DERBY · INTER 91 · PARI 71 · MILAN 84'], BIANCO, 19))
    b.append(num(420, 1005, '1/33', 100, NERO, 0, ['UNA DONNA TRA I NOMI', 'DELLE FERMATE DEL METRO'], NERO, 16))
    b.append(num(760, 1005, '171', 110, BIANCO, 0, ['CINEMA SPARITI', '(123 SALE NEL 1960)'], BIANCO, 16))
    # in verticale sul bordo destro
    b.append('<g transform="translate(1048 1050) rotate(-90)">' + T(0, 0, '4.635', 76, NERO, IMPACT, '400') +
             T(0, 24, 'TITOLI ALLA SCALA DAL 1778', 15, NERO, GROT, '800') + '</g>')
    salva('bozza_4_manifesto.svg', svg('\n'.join(b), ROSSO, 'Milano in dati - bozza 4, manifesto'))

if __name__ == '__main__':
    bozza1(); bozza2(); bozza3(); bozza4()
