# -*- coding: utf-8 -*-
"""Bozze 5-8 della home di "Milano in dati" (1080x1080, SVG autonome).
Riusa mappa, proiezione e funzioni di genera_bozze.py; legge solo docs/ (non lo modifica).
Uso: python -I genera_bozze_2.py
"""
import os, sys, math, json, random, collections
QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera_bozze as G
from genera_bozze import NIL, NILINFO, COMUNE, Proj, path, esc, svg, T, SANS, GROT, IMPACT, salva, carica, TEMP, STAZ, LON0, LAT0
from shapely.geometry import shape

DERBY = carica('derby/data/partite.json')
SERIE_CIN = carica('cinema-spariti/data/serie.json')
SCALA = carica('scala/data/titoli.json')

# ------------------------------------------------------------- utilita'
def colore_t(v, lo, hi):
    t = max(0, min(1, (v - lo) / (hi - lo)))
    stops = [(0, (8, 48, 107)), (0.35, (66, 146, 198)), (0.55, (235, 235, 235)), (0.75, (255, 160, 40)), (0.9, (240, 70, 20)), (1, (180, 0, 30))]
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            u = (t - t0) / (t1 - t0)
            return '#%02x%02x%02x' % tuple(int(c0[k] + (c1[k] - c0[k]) * u) for k in range(3))
    return '#b4001e'

def catmull(pts, passi=40):
    """curva liscia che passa per i punti dati"""
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(passi):
            t = k / passi
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(pts[-1])
    return out

class Linea:
    """polilinea con parametro d'arco: at(f) -> punto e normale, f tra 0 e 1"""
    def __init__(self, pts):
        self.p = pts
        self.c = [0]
        for a, b in zip(pts, pts[1:]):
            self.c.append(self.c[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.L = self.c[-1]
    def at(self, f):
        s = max(0, min(1, f)) * self.L
        i = 1
        while i < len(self.c) - 1 and self.c[i] < s:
            i += 1
        a, b = self.p[i - 1], self.p[i]
        seg = (self.c[i] - self.c[i - 1]) or 1
        u = (s - self.c[i - 1]) / seg
        x = a[0] + (b[0] - a[0]) * u; y = a[1] + (b[1] - a[1]) * u
        tx, ty = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
        return (x, y), (-ty, tx), (tx, ty)
    def offset(self, d, n=200):
        out = []
        for k in range(n + 1):
            (x, y), (nx, ny), _ = self.at(k / n)
            out.append((x + nx * d, y + ny * d))
        return out

def poly_d(pts, chiuso=False):
    return 'M' + 'L'.join('%.1f,%.1f' % p for p in pts) + ('Z' if chiuso else '')

def ottagono(c, R, rot=22.5):
    return [(c[0] + R * math.cos(math.radians(rot + 45 * k)), c[1] + R * math.sin(math.radians(rot + 45 * k))) for k in range(8)]

def settore(c, r1, r2, g1, g2, fill, extra=''):
    def pol(r, a):
        a = math.radians(a); return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    p1, p2, p3, p4 = pol(r2, g1), pol(r2, g2), pol(r1, g2), pol(r1, g1)
    lg = 1 if g2 - g1 > 180 else 0
    return '<path d="M%.1f,%.1fA%.1f,%.1f 0 %d 1 %.1f,%.1fL%.1f,%.1fA%.1f,%.1f 0 %d 0 %.1f,%.1fZ" fill="%s" %s/>' % (
        p1[0], p1[1], r2, r2, lg, p2[0], p2[1], p3[0], p3[1], r1, r1, lg, p4[0], p4[1], fill, extra)

def anno_frazione(data):
    y, m, d = (int(x) for x in data.split('-'))
    return y + ((m - 1) * 30.5 + d) / 366

# =================================================================== BOZZA 5
def bozza5():
    """Lo skyline che e' un grafico: ogni torre e' alta quanti anni di dati ha la sua storia"""
    random.seed(1763)
    NOTTE = '#141433'; GIALLO = '#FFD34D'; G0 = 905; K = 2.15
    b = []
    b.append('<defs><linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#0A1033"/><stop offset=".32" stop-color="#26206B"/>'
             '<stop offset=".58" stop-color="#7A2D8C"/><stop offset=".78" stop-color="#E5476B"/>'
             '<stop offset=".92" stop-color="#FF8A3D"/><stop offset="1" stop-color="#FFC15E"/></linearGradient></defs>')
    b.append('<rect width="1080" height="%d" fill="url(#cielo)"/>' % G0)
    for _ in range(90):   # stelle
        x, y = random.uniform(0, 1080), random.uniform(0, 330)
        b.append('<circle cx="%.0f" cy="%.0f" r="%.1f" fill="#fff" opacity="%.2f"/>' % (x, y, random.uniform(.6, 1.6), random.uniform(.3, .9)))
    # luna = la mappa vera degli 88 quartieri
    P = Proj(box=(800, 52, 190, 170))
    b.append('<circle cx="895" cy="137" r="104" fill="#FFE27A" opacity=".18"/>')
    b.append('<circle cx="895" cy="137" r="94" fill="#FFE27A"/>')
    for i, g in NIL.items():
        b.append('<path d="%s" fill="#F7C948" stroke="#FFF3B8" stroke-width=".9"/>' % path(g, P))
    b.append(T(895, 256, 'la luna? 88 quartieri', 15, '#FFE9A8', GROT, '700', 'middle'))
    # griglia: anni di dati
    for a in (50, 100, 150, 200, 250):
        y = G0 - a * K
        b.append('<line x1="0" y1="%.1f" x2="1080" y2="%.1f" stroke="#fff" stroke-opacity=".28" stroke-dasharray="3 7"/>' % (y, y))
        b.append(T(1070, y - 6, '%d anni' % a, 14, '#fff', GROT, '700', 'end', 'opacity=".75"'))
    # titolo
    b.append(T(36, 96, 'Milano in dati', 84, '#fff', GROT, '900', extra='letter-spacing="-2"'))
    b.append(T(40, 138, 'Ogni torre è alta quanti anni di dati ha la sua storia', 23, '#FFD9A0', GROT, '700'))
    b.append(T(40, 166, 'dal primo dato a oggi: più è vecchia, più è alta', 18, '#fff', GROT, '400', extra='opacity=".8"'))

    # --- edifici: (nome storia, anno di partenza, sagoma, x, larghezza)
    def duomo(x, w, h):
        top = G0 - h; corpo = G0 - h * .40; frontone = G0 - h * .55
        d = 'M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (x, G0, x, corpo, x + w / 2, frontone, x + w, corpo, x + w, G0)
        guglie = []
        for k in range(9):    # pinnacoli sulla facciata
            gx = x + 6 + k * (w - 12) / 8
            gy = corpo - (frontone - corpo) * (1 - abs(k - 4) / 4) * -1 if False else corpo + (frontone - corpo) * (1 - abs(k - 4) / 4)
            gh = 34 + (12 if k % 2 == 0 else 0)
            guglie.append('M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z' % (gx - 4, gy + 4, gx - 3, gy - gh + 8, gx, gy - gh, gx + 3, gy - gh + 8) + 'L%.1f,%.1fZ' % (gx + 4, gy + 4))
        # tiburio e guglia maggiore
        cx = x + w / 2
        guglie.append('M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z' % (cx - 34, frontone + 10, cx - 22, G0 - h * .70, cx + 22, G0 - h * .70, cx + 34, frontone + 10))
        guglie.append('M%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Z' % (cx - 9, G0 - h * .70 + 2, cx - 4, top + 18, cx + 4, top + 18, cx + 9, G0 - h * .70 + 2))
        sag = d + ' ' + ' '.join(guglie)
        extra = ['<path d="M%.1f,%.1f l-5,-4 l5,-14 l5,14 Z" fill="#FFC400"/><circle cx="%.1f" cy="%.1f" r="4" fill="#FFC400"/>' % (cx, top + 18, cx, top + 1),
                 '<circle cx="%.1f" cy="%.1f" r="14" fill="#FFC400" opacity=".25"/>' % (cx, top + 6)]
        # portali e rosone
        for k in range(5):
            px = x + 22 + k * (w - 44) / 4
            extra.append('<path d="M%.1f,%d v-34 a8,8 0 0 1 16,0 v34 Z" fill="#5A2A4A"/>' % (px - 8, G0))
        for k in range(5):
            px = x + 22 + k * (w - 44) / 4
            extra.append('<rect x="%.1f" y="%.1f" width="7" height="30" rx="3.5" fill="#5A2A4A"/>' % (px - 3.5, corpo + 40))
        return sag, extra, '#F6C6CF'   # marmo di Candoglia al tramonto
    def velasca(x, w, h):
        top = G0 - h; fusto = w * .64; cx = x + w / 2
        a = G0 - h * .70
        d = ('M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (
            cx - fusto / 2, G0, cx - fusto / 2, a, x, a - 24, x, top + 14, cx - 14, top + 14, cx - 14, top, cx + 14, top, cx + 14, top + 14,
            x + w, top + 14, x + w, G0))
        d = d.replace('L%.1f,%d Z' % (x + w, G0), 'L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (x + w, a - 24, cx + fusto / 2, a, cx + fusto / 2, G0))
        ex = ['<path d="M%.1f,%.1f L%.1f,%.1f M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="5"/>' % (cx - fusto / 2 + 3, a - 40, x + 8, a - 70, cx + fusto / 2 - 3, a - 40, x + w - 8, a - 70, NOTTE)]
        return d, ex, NOTTE
    def pirellone(x, w, h):
        top = G0 - h
        d = 'M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (x + 4, G0, x, top + 10, x + w / 2, top, x + w, top + 10, x + w - 4, top + 10, x + w - 4, G0)
        d = 'M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (x + 3, G0, x, top, x + w, top, x + w - 3, G0)
        ex = ['<rect x="%.1f" y="%.1f" width="%.1f" height="7" fill="#E5476B" opacity=".9"/>' % (x + 2, top + 8, w - 4),
              '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="#2A2A5A" stroke-width="4"/>' % (x + w * .33, top + 16, x + w * .33, G0),
              '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%d" stroke="#2A2A5A" stroke-width="4"/>' % (x + w * .67, top + 16, x + w * .67, G0)]
        return d, ex, NOTTE
    def unicredit(x, w, h):
        top = G0 - h; cx = x + w / 2; s = G0 - h * .70
        d = ('M%.1f,%d L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f L%.1f,%.1f L%.1f,%.1f L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f L%.1f,%d Z' % (
            x, G0, x, s, x + 4, s - 40, cx - 4, s - 52, cx - 2, top, cx + 2, top, cx + 4, s - 52, x + w - 4, s - 40, x + w, s, x + w, G0))
        ex = ['<circle cx="%.1f" cy="%.1f" r="3" fill="#FF3B3B"/>' % (cx, top + 2)]
        return d, ex, NOTTE
    def allianz(x, w, h):
        top = G0 - h
        d = 'M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (x, G0, x, top, x + w, top, x + w, G0)
        ex = []
        for k in range(1, 7):
            yy = G0 - h * k / 7
            ex.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#3A3A7A" stroke-width="3"/>' % (x, yy, x + w, yy))
        ex.append('<rect x="%.1f" y="%.1f" width="%.1f" height="16" fill="none" stroke="#7FD6FF" stroke-width="2.5"/>' % (x + 6, top + 6, w - 12))
        return d, ex, NOTTE
    def generali(x, w, h):
        top = G0 - h
        d = 'M%.1f,%d C%.1f,%.1f %.1f,%.1f %.1f,%.1f L%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%d Z' % (
            x, G0, x - 4, G0 - h * .5, x + 12, G0 - h * .8, x + 14, top + 12, x + w - 10, top, x + w + 6, G0 - h * .6, x + w - 8, G0 - h * .3, x + w, G0)
        ex = ['<path d="M%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%.1f" stroke="#3A3A7A" stroke-width="3" fill="none"/>' % (x + 18, G0, x + 10, G0 - h * .5, x + 30, G0 - h * .8, x + 34, top + 12),
              '<rect x="%.1f" y="%.1f" width="%.1f" height="9" fill="#FF6B6B" transform="rotate(-6 %.1f %.1f)"/>' % (x + 14, top + 10, w - 24, x + w / 2, top + 14)]
        return d, ex, NOTTE
    def curvo(x, w, h):
        top = G0 - h
        d = 'M%.1f,%d L%.1f,%.1f Q%.1f,%.1f %.1f,%.1f L%.1f,%.1f Q%.1f,%.1f %.1f,%d Z' % (
            x, G0, x, top + 30, x + w * .3, top + 2, x + w * .7, top, x + w, top + 8, x + w - 22, G0 - h * .45, x + w, G0)
        ex = ['<path d="M%.1f,%.1f Q%.1f,%.1f %.1f,%.1f" stroke="#7FD6FF" stroke-width="3" fill="none"/>' % (x + 4, top + 34, x + w * .45, top + 2, x + w - 4, top + 14)]
        return d, ex, NOTTE
    def bosco(x, w, h):
        top = G0 - h; w1 = w * .45
        d = 'M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z M%.1f,%d L%.1f,%.1f L%.1f,%.1f L%.1f,%d Z' % (
            x, G0, x, top + 18, x + w1, top + 18, x + w1, G0, x + w - w1, G0, x + w - w1, top, x + w, top, x + w, G0)
        ex = []
        for tx0, t0 in ((x, top + 18), (x + w - w1, top)):
            yy = G0 - 8
            while yy > t0 + 4:
                for k in range(4):
                    ex.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (tx0 + 3 + k * (w1 - 6) / 3, yy, random.uniform(3, 4.6), random.choice(['#2BB24C', '#4CD964', '#1E8E3E'])))
                yy -= 11
        return d, ex, NOTTE

    EDIFICI = [
        # nome, anno, funzione, x, larghezza, nome edificio, fatto
        ('Censimenti', 1991, bosco, 26, 92, 'Bosco Verticale', 'stranieri 1,9% → 19,6%'),
        ('La Scala', 1778, velasca, 136, 104, 'Torre Velasca', '4.635 titoli'),
        ('Neve e nebbia', 1950, curvo, 258, 70, 'il Curvo', 'neve: da 10,5 a 2 giorni'),
        ('Temperature', 1763, duomo, 346, 226, 'Duomo', '2026 il più caldo (finora)'),
        ('Cinema spariti', 1896, pirellone, 596, 84, 'Pirellone', '171 sale chiuse'),
        ('Elezioni', 1946, generali, 704, 70, 'lo Storto', '167 elezioni'),
        ('Il derby', 1909, unicredit, 794, 76, 'Unicredit', 'Inter 91 · pari 71 · Milan 84'),
        ('Violenza politica', 1919, allianz, 892, 58, 'il Dritto', '84 fatti, 1919-2019'),
    ]
    sagome, finestre, extra, etichette = [], [], [], []
    for k, (nome, anno, fn, x, w, edif, fatto) in enumerate(EDIFICI):
        h = (2026 - anno) * K
        d, ex, col = fn(x, w, h)
        sagome.append('<path d="%s" fill="%s"/>' % (d, col))
        if col == NOTTE:
            finestre.append('<clipPath id="c%d"><path d="%s"/></clipPath>' % (k, d))
            f = ['<g clip-path="url(#c%d)">' % k]
            yy = G0 - 14
            while yy > G0 - h:
                xx = x + 4
                while xx < x + w - 4:
                    if random.random() < .33:
                        f.append('<rect x="%.0f" y="%.0f" width="4" height="6" fill="%s"/>' % (xx, yy, random.choice([GIALLO, GIALLO, '#FFF1B0', '#FFB347'])))
                    xx += 8
                yy -= 11
            f.append('</g>')
            extra.append('\n'.join(f))
        extra += ex
        # etichetta sopra la torre
        cx = x + w / 2; top = G0 - h
        sopra = top - (34 if fn is duomo else 14)
        al = 'stroke="#141433" stroke-width="4" stroke-linejoin="round" paint-order="stroke"'
        etichette.append(T(cx, sopra, str(anno), 30, GIALLO, GROT, '900', 'middle', al))
        righe_n = nome.upper().split(' ', 1) if len(nome) > 13 else [nome.upper()]
        for j, rn in enumerate(righe_n[::-1]):
            etichette.append(T(cx, sopra - 32 - 16 * j, rn, 13, '#fff', GROT, '800', 'middle', 'letter-spacing=".5" ' + al))
    b += ['<defs>' + ''.join(finestre) + '</defs>'] + sagome + extra + etichette
    # strada, binari e tram (Area C, dal 2012: 14 anni = alto come un tram)
    b.append('<rect x="0" y="%d" width="1080" height="%d" fill="#0B0B1E"/>' % (G0, 1080 - G0))
    b.append('<rect x="0" y="%d" width="1080" height="3" fill="#FF8A3D" opacity=".7"/>' % G0)
    tw, th = 118, 14 * K
    tx = 952
    b.append('<rect x="%d" y="%.1f" width="%d" height="%.1f" rx="5" fill="#F2A900"/>' % (tx, G0 - th - 2, tw, th))
    b.append('<rect x="%d" y="%.1f" width="%d" height="5" fill="#1A1A1A"/>' % (tx, G0 - 8, tw))
    for k in range(6):
        b.append('<rect x="%d" y="%.1f" width="13" height="10" rx="2" fill="#FFF1B0"/>' % (tx + 6 + k * 18, G0 - th + 3))
    b.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#ccc" stroke-width="1.5"/>' % (tx + 50, G0 - th - 2, tx + 64, G0 - th - 18))
    b.append(T(tx + tw / 2 - 4, G0 - th - 26, 'AREA C · 2012', 13, '#fff', GROT, '800', 'middle'))
    b.append('<line x1="0" y1="%d" x2="1080" y2="%d" stroke="#555" stroke-width="2"/>' % (G0 + 1, G0 + 1))
    # fatti sotto ogni torre
    for nome, anno, fn, x, w, edif, fatto in EDIFICI:
        cx = x + w / 2
        b.append(T(cx, G0 + 26, edif, 13, '#9FA8FF', GROT, '700', 'middle'))
    b.append(T(40, 990, '263 anni di temperature a Brera, 248 di stagioni alla Scala,', 22, '#fff', GROT, '700'))
    b.append(T(40, 1020, '117 di derby: la storia più vecchia è la torre più alta.', 22, '#fff', GROT, '700'))
    b.append(T(40, 1052, 'Altezza = 2026 meno l’anno del primo dato. Il tram, Area C, ha 14 anni.', 16, '#FFD9A0', GROT, '400'))
    b.append(T(1044, 1040, '17 storie', 44, GIALLO, GROT, '900', 'end'))
    salva('bozza_5_skyline.svg', svg('\n'.join(b), '#0A1033', 'Milano in dati - bozza 5, skyline'))

# =================================================================== BOZZA 6
def bozza6():
    """Tabellone delle partenze di Centrale"""
    NERO = '#0C0C0C'; CELLA = '#1E1E1E'; GIALLO = '#FFC400'; BIANCO = '#F4F4F4'; ARANCIO = '#FF5A1F'; BLU = '#0A3D8F'
    b = []
    def flap(x, y, s, n, col, cw=22, ch=34, fs=25, pitch=25):
        out = []
        s = s.ljust(n)[:n]
        for k, c in enumerate(s):
            cx = x + k * pitch
            out.append('<rect x="%.1f" y="%.1f" width="%d" height="%d" rx="3" fill="%s"/>' % (cx, y, cw, ch, CELLA))
            if c != ' ':
                out.append(T(cx + cw / 2, y + ch / 2 + fs * .36, c, fs, col, GROT, '700', 'middle'))
            out.append('<rect x="%.1f" y="%.1f" width="%d" height="1.6" fill="#000"/>' % (cx, y + ch / 2 - .8, cw))
        return '\n'.join(out)
    # intestazione: il nome del sito come lettere a palette grandi
    b.append('<rect width="1080" height="150" fill="#050505"/>')
    b.append(flap(36, 34, 'MILANO IN DATI', 14, GIALLO, cw=48, ch=76, fs=58, pitch=52))
    # orologio di stazione: 19:09, l'ora del primo derby (10 gennaio 1909)
    cx, cy, r = 990, 72, 56
    b.append('<circle cx="%d" cy="%d" r="%d" fill="#fff" stroke="#888" stroke-width="4"/>' % (cx, cy, r))
    for k in range(60):
        a = math.radians(k * 6); l = 9 if k % 5 == 0 else 3
        b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#111" stroke-width="%s"/>' % (
            cx + (r - 5) * math.sin(a), cy - (r - 5) * math.cos(a), cx + (r - 5 - l) * math.sin(a), cy - (r - 5 - l) * math.cos(a), '3' if k % 5 == 0 else '1.2'))
    for ang, ln, wd in ((360 * (19 % 12 + 9 / 60) / 12, 30, 6), (360 * 9 / 60, 44, 4)):
        a = math.radians(ang)
        b.append('<line x1="%d" y1="%d" x2="%.1f" y2="%.1f" stroke="#111" stroke-width="%d" stroke-linecap="round"/>' % (cx, cy, cx + ln * math.sin(a), cy - ln * math.cos(a), wd))
    b.append('<circle cx="%d" cy="%d" r="4" fill="#D7001E"/>' % (cx, cy))
    b.append(T(cx, 145, '19:09 · il primo derby', 11, '#bbb', GROT, '600', 'middle'))
    # sottotitolo
    b.append(T(40, 192, 'Partenze', 32, BIANCO, GROT, '800'))
    b.append(T(190, 192, 'Departures', 24, '#9A9A9A', GROT, '400', extra='font-style="italic"'))
    b.append(T(1044, 190, '17 storie in partenza dai dati aperti di Milano', 17, '#9A9A9A', GROT, '500', 'end'))
    # colonne
    PITCH = 25; GAP = 14
    cols = [('N.', 5), ('DESTINAZIONE · DESTINATION', 15), ('DAL', 4), ('NOTE', 12), ('BIN.', 2)]
    xs = []; x = 40
    for nome, n in cols:
        xs.append(x); x += n * PITCH + GAP
    for (nome, n), x in zip(cols, xs):
        b.append(T(x, 228, nome, 12, '#8A8A8A', GROT, '800', extra='letter-spacing="1"'))
    b.append('<line x1="40" y1="236" x2="1040" y2="236" stroke="#333" stroke-width="1.5"/>')
    RIGHE = [
        ('246', 'DERBY', '1909', 'I91 P71 M84', None),
        ('4635', 'LA SCALA', '1778', 'TITOLI', None),
        ('2026', 'TEMPERATURE', '1763', 'IL PIÙ CALDO', ARANCIO),
        ('171', 'CINEMA SPARITI', '1896', 'SOPPRESSI', ARANCIO),
        ('167', 'ELEZIONI', '1946', 'IN ORARIO', None),
        ('84', 'VIOLENZA POL.', '1919', 'FINO AL 2019', None),
        ('19,6%', 'CENSIMENTI', '1991', 'STRANIERI', None),
        ('6,6%', 'DONNE NELLE VIE', '', 'IN RITARDO', ARANCIO),
        ('1/33', 'NOMI FERMATE', '', 'UNA DONNA', None),
        ('-16%', 'AREA C', '2012', 'VS 2019', None),
        ('88%', 'BICI AUTO MEZZI', '', 'BICI PRIMA', None),
        ('435', 'MILANO NEI FILM', '', '+280 LIBRI', None),
        ('27459', 'BENI CULTURALI', '', 'SCHEDE', None),
    ]
    y0 = 246; RP = 42
    for k, (num, dest, dal, nota, ncol) in enumerate(RIGHE):
        y = y0 + k * RP
        if k % 2 == 1:
            b.append('<rect x="30" y="%d" width="1020" height="%d" fill="#151515"/>' % (y - 3, RP))
        b.append(flap(xs[0], y, num, 5, GIALLO))
        b.append(flap(xs[1], y, dest, 15, BIANCO))
        b.append(flap(xs[2], y, dal, 4, GIALLO))
        b.append(flap(xs[3], y, nota, 12, ncol or BIANCO))
        b.append(flap(xs[4], y, '%d' % (k + 1), 2, BIANCO))
    # striscia degli avvisi
    yt = y0 + len(RIGHE) * RP + 10
    b.append('<rect x="0" y="%d" width="1080" height="40" fill="%s"/>' % (yt, BLU))
    b.append('<rect x="0" y="%d" width="118" height="40" fill="#FFC400"/>' % yt)
    b.append(T(59, yt + 27, 'AVVISO', 18, '#0C0C0C', GROT, '900', 'middle', 'letter-spacing="1"'))
    b.append(T(132, yt + 27, 'Il 2026 è l’anno più caldo a Brera (finora, sullo stesso periodo) · nel 1960 c’erano 123 cinema', 17, '#fff', GROT, '600'))
    # pianta: la mappa vera con le fermate del metro, "voi siete qui" a Centrale
    yp = yt + 52; hp = 1080 - yp - 18
    b.append('<rect x="30" y="%d" width="500" height="%d" rx="6" fill="%s"/>' % (yp, hp, BLU))
    P = Proj(box=(44, yp + 12, 250, hp - 24))
    for i, g in NIL.items():
        b.append('<path d="%s" fill="#0F4BA8" stroke="#6E9BE0" stroke-width=".8"/>' % path(g, P))
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="2"/>' % path(COMUNE, P))
    for s in STAZ:
        x, y = P(s['lon'], s['lat'])
        b.append('<circle cx="%.1f" cy="%.1f" r="1.6" fill="#fff"/>' % (x, y))
    cx, cy = P(9.2046, 45.4859)   # Milano Centrale
    b.append('<circle cx="%.1f" cy="%.1f" r="9" fill="#FFC400" stroke="#0C0C0C" stroke-width="2.5"/>' % (cx, cy))
    b.append(T(310, yp + 40, 'PIANTA DELLA CITTÀ', 15, '#FFC400', GROT, '900', extra='letter-spacing="1"'))
    b.append(T(310, yp + 66, '88 quartieri', 22, '#fff', GROT, '800'))
    b.append(T(310, yp + 90, '125 fermate del metrò', 16, '#cfe0ff', GROT, '500'))
    b.append('<circle cx="318" cy="%d" r="8" fill="#FFC400" stroke="#0C0C0C" stroke-width="2"/>' % (yp + 124))
    b.append(T(334, yp + 130, 'Voi siete qui', 17, '#fff', GROT, '800'))
    b.append(T(334, yp + 150, 'Milano Centrale', 14, '#cfe0ff', GROT, '500'))
    # binari: il ventaglio di Centrale (24 binari) che si apre verso le storie
    xb, yb = 548, yp
    b.append('<rect x="%d" y="%d" width="502" height="%d" rx="6" fill="#141414"/>' % (xb, yb, hp))
    ox, oy = xb + 30, yb + hp / 2
    for k in range(24):
        ty = yb + 14 + k * (hp - 28) / 23
        b.append('<path d="M%.1f,%.1f C%.1f,%.1f %.1f,%.1f %.1f,%.1f" fill="none" stroke="%s" stroke-width="%s"/>' % (
            ox, oy, ox + 170, oy, ox + 220, ty, xb + 490, ty, GIALLO if k in (0, 23) else '#4A4A4A', '2.5' if k in (0, 23) else '1.5'))
    b.append('<rect x="%d" y="%.1f" width="250" height="78" fill="#141414"/>' % (xb + 200, oy - 39))
    b.append(T(xb + 325, oy - 8, 'TUTTE LE STORIE', 18, GIALLO, GROT, '900', 'middle', 'letter-spacing="1"'))
    b.append(T(xb + 325, oy + 20, 'partono da qui', 18, '#fff', GROT, '600', 'middle'))
    salva('bozza_6_tabellone.svg', svg('\n'.join(b), NERO, 'Milano in dati - bozza 6, tabellone'))

# =================================================================== BOZZA 7
def bozza7():
    """Il pavimento della Galleria: 88 tessere = 88 quartieri"""
    ROSSO = '#B5121B'; NERO = '#161616'; BIANCO = '#F5F5F5'; ORO = '#E0A800'; BLU = '#1F4E9C'; VERDE = '#1F6F4A'
    C = (540, 597); R = 470
    b = []
    # classi: abitanti 1991 -> 2023
    CLASSI = [(-1e9, '#1F5E4B', '−10% e meno'), (-10, '#7FB89A', '−10/0'), (0, BIANCO, '0/+10'), (10, '#F2B705', '+10/50'), (50, '#E2541F', '+50/150'), (150, '#8E0F22', 'oltre +150%')]
    def colore(i):
        n = NILINFO[i]; v = n['v']['var'][4]
        if v is None or not n['ok']:
            return 'url(#venato)'
        return [c for t, c, _ in CLASSI if v >= t][-1]
    b.append('<defs>'
             '<pattern id="pav" width="60" height="60" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<rect width="60" height="60" fill="%s"/><rect x="0" y="0" width="60" height="4" fill="%s"/><rect x="0" y="0" width="4" height="60" fill="%s"/>'
             '<rect x="22" y="22" width="16" height="16" fill="%s"/></pattern>'
             '<pattern id="venato" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
             '<rect width="8" height="8" fill="#A9AEB3"/><line x1="0" y1="0" x2="0" y2="8" stroke="#D8DCDF" stroke-width="2.5"/></pattern>'
             '<pattern id="tess" width="6" height="6" patternUnits="userSpaceOnUse">'
             '<path d="M6,0V6H0" fill="none" stroke="#000" stroke-opacity=".22" stroke-width="1"/></pattern>'
             '<clipPath id="cm"><circle cx="%d" cy="%d" r="292"/></clipPath>'
             '</defs>' % (NERO, BIANCO, BIANCO, ROSSO, C[0], C[1]))
    b.append('<rect width="1080" height="1080" fill="url(#pav)"/>')
    # ottagono a fasce di marmo
    for rr, col in ((R, NERO), (R - 8, ROSSO), (R - 18, BIANCO), (R - 62, NERO), (R - 68, '#2A2A2A')):
        b.append('<path d="%s" fill="%s"/>' % (poly_d(ottagono(C, rr), True), col))
    # denti nella fascia bianca
    fl = (R - 18) * math.cos(math.radians(22.5)); fl2 = (R - 62) * math.cos(math.radians(22.5))
    for k in range(8):
        a = math.radians(45 * k)
        for j in range(-7, 8):
            if j in range(-4, 5) and k % 2 == 0:
                continue        # spazio per le scritte sui lati dritti
            t = j * 22
            px, py = C[0] + (fl - 9) * math.cos(a) - t * math.sin(a), C[1] + (fl - 9) * math.sin(a) + t * math.cos(a)
            b.append('<rect x="%.1f" y="%.1f" width="10" height="10" fill="%s" transform="rotate(%d %.1f %.1f)"/>' % (px - 5, py - 5, ROSSO if j % 2 else NERO, 45 * k + 45, px, py))
    # scritte sui 4 lati dritti
    mid = (fl + fl2) / 2
    sc = [('88 QUARTIERI', 0, -mid, 0), ('88 TESSERE', 0, mid, 0), ('1991 → 2023', -mid, 0, -90), ('ABITANTI', mid, 0, 90)]
    for testo, dx, dy, rot in sc:
        x, y = C[0] + dx, C[1] + dy
        b.append('<g transform="translate(%.1f %.1f) rotate(%d)">%s</g>' % (x, y, rot, T(0, 9, testo, 25, NERO, GROT, '900', 'middle', 'letter-spacing="5"')))
    # anello di 88 tessere: i quartieri in fila, dal piu' svuotato al piu' cresciuto
    ordine = sorted(NIL, key=lambda i: (not NILINFO[i]['ok'] or NILINFO[i]['v']['var'][4] is None, NILINFO[i]['v']['var'][4] or 0))
    n = len(ordine); step = 360 / n
    for k, i in enumerate(ordine):
        g1 = -90 + k * step + .45; g2 = -90 + (k + 1) * step - .45
        b.append(settore(C, 306, 366, g1, g2, colore(i)))
    b.append('<circle cx="%d" cy="%d" r="300" fill="%s"/>' % (C[0], C[1], ORO))
    b.append('<circle cx="%d" cy="%d" r="294" fill="%s"/>' % (C[0], C[1], BIANCO))
    # la mappa al centro come un mosaico
    P = Proj(box=(C[0] - 262, C[1] - 262, 524, 524))
    g = ['<g clip-path="url(#cm)">']
    g.append('<rect x="%d" y="%d" width="600" height="600" fill="#D9DDE0"/>' % (C[0] - 300, C[1] - 300))
    g.append('<rect x="%d" y="%d" width="600" height="600" fill="url(#tess)"/>' % (C[0] - 300, C[1] - 300))
    for i, gg in NIL.items():
        g.append('<path d="%s" fill="%s" stroke="%s" stroke-width="2.2" stroke-linejoin="round"/>' % (path(gg, P), colore(i), NERO))
    g.append('<path d="%s" fill="url(#tess)" stroke="%s" stroke-width="3"/>' % (path(COMUNE, P), NERO))
    g.append('</g>')
    b += g
    # Rogoredo-Santa Giulia segnato
    rx, ry = G.centro_nil(33, P)
    b.append('<circle cx="%.1f" cy="%.1f" r="6" fill="#fff" stroke="%s" stroke-width="3"/>' % (rx, ry, NERO))
    b.append(T(rx + 10, ry + 34, '+172%', 22, NERO, GROT, '900', extra='stroke="#fff" stroke-width="5" paint-order="stroke"'))
    b.append(T(rx + 10, ry + 52, 'Rogoredo', 14, NERO, GROT, '700', extra='stroke="#fff" stroke-width="4" paint-order="stroke"'))
    # fascia del titolo, come una lapide
    b.append('<rect x="0" y="0" width="1080" height="112" fill="%s"/>' % BIANCO)
    b.append('<rect x="0" y="104" width="1080" height="8" fill="%s"/>' % ROSSO)
    b.append('<text x="36" y="78" font-family="%s" font-size="60" font-weight="900" fill="%s" letter-spacing="2">MILANO <tspan fill="%s">IN DATI</tspan></text>' % (GROT, NERO, ROSSO))
    b.append(T(1044, 36, 'Abitanti dal 1991 al 2023, quartiere per quartiere', 15, NERO, GROT, '700', 'end'))
    lx = 1044 - 6 * 66
    for k, (t, c, lab) in enumerate(CLASSI):
        b.append('<rect x="%d" y="48" width="62" height="20" fill="%s" stroke="%s" stroke-width="1"/>' % (lx + k * 66, c, NERO))
        b.append(T(lx + k * 66 + 31, 86, lab, 11, NERO, GROT, '600', 'middle'))
    b.append('<rect x="%d" y="48" width="20" height="20" fill="url(#venato)" stroke="%s"/>' % (lx - 30, NERO))
    b.append(T(lx - 20, 86, 'incerto', 11, NERO, GROT, '600', 'middle'))
    # quattro tondi agli angoli, come gli stemmi della Galleria
    def tondo(cx, cy, fondo, num, righe, ink=BIANCO, toro=False):
        out = ['<circle cx="%d" cy="%d" r="104" fill="%s"/>' % (cx, cy, ORO),
               '<circle cx="%d" cy="%d" r="96" fill="%s"/>' % (cx, cy, fondo),
               '<circle cx="%d" cy="%d" r="86" fill="none" stroke="%s" stroke-width="1.5" stroke-dasharray="4 4"/>' % (cx, cy, ORO)]
        if toro:   # il toro della Galleria, ridotto all'osso: corna e muso
            out.append('<path d="M%d,%d q-22,-4 -26,-24 q14,14 30,12 Z M%d,%d q22,-4 26,-24 q-14,14 -30,12 Z" fill="%s"/>' % (cx - 12, cy - 50, cx + 12, cy - 50, ORO))
            out.append('<path d="M%d,%d q12,-8 24,0 l-4,20 q-8,6 -16,0 Z" fill="%s"/>' % (cx - 12, cy - 52, ORO))
            ny = cy + 8
        else:
            ny = cy + 4
        out.append(T(cx, ny + 14, num, 50 if len(num) < 5 else 42, ink, GROT, '900', 'middle', 'letter-spacing="-1"'))
        for k, r in enumerate(righe):
            out.append(T(cx, ny + 36 + k * 16, r, 13, ink, GROT, '700', 'middle'))
        return '\n'.join(out)
    b.append(tondo(118, 236, ROSSO, '1763', ['temperature a Brera:', 'il 2026 è il più caldo', '(finora)']))
    b.append(tondo(962, 236, VERDE, '4.635', ['titoli alla Scala', 'dal 1778']))
    b.append(tondo(118, 962, BLU, '246', ['derby: Inter 91,', 'pari 71, Milan 84'], toro=True))
    b.append(tondo(962, 962, NERO, '171', ['cinema spariti', '(123 sale nel 1960)']))
    salva('bozza_7_galleria.svg', svg('\n'.join(b), NERO, 'Milano in dati - bozza 7, Galleria'))

# =================================================================== BOZZA 8
def bozza8():
    """I Navigli come linee del tempo"""
    PRATO = '#2E9E4A'; PRATO2 = '#1F7F3A'; ACQUA = '#1565C0'; ACQUA2 = '#5FB0FF'; ALZAIA = '#D6DEE3'
    INTER = '#0A4FD6'; MILAN = '#E10600'; NERO = '#111'
    random.seed(1179)
    b = []
    b.append('<rect width="1080" height="1080" fill="%s"/>' % PRATO)
    # alberi sulle rive (macchie scure)
    for _ in range(170):
        x, y = random.uniform(0, 1080), random.uniform(0, 1080)
        b.append('<circle cx="%.0f" cy="%.0f" r="%.0f" fill="%s" opacity=".55"/>' % (x, y, random.uniform(6, 16), PRATO2))
    # --- tracciati (schematici, non in scala)
    CR = (650, 420); RC = 150
    grande = Linea(catmull([(-40, 905), (90, 880), (190, 820), (270, 770), (348, 742)]))     # 1763 -> 2026, verso la Darsena
    pavese = Linea(catmull([(470, 1110), (500, 1000), (488, 900), (470, 830), (450, 772)]))  # 1896 -> 2026
    mart = Linea(catmull([(1120, 30), (1010, 80), (930, 150), (860, 200), (790, 250), (CR[0] + RC * .7, CR[1] - RC * .7)]))  # 1909 -> 2026
    viarenna = Linea(catmull([(470, 720), (520, 640), (CR[0] - RC * .72, CR[1] + RC * .69)]))
    def acqua(lin, w, col=ACQUA):
        d = poly_d(lin.p)
        return ('<path d="%s" fill="none" stroke="%s" stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/>' % (d, ALZAIA, w + 12) +
                '<path d="%s" fill="none" stroke="%s" stroke-width="%d" stroke-linecap="round" stroke-linejoin="round"/>' % (d, col, w))
    # rive chiare
    b.append(acqua(viarenna, 18))
    b.append(acqua(mart, 34))
    b.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="38"/>' % (CR[0], CR[1], RC, ALZAIA))
    b.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="26"/>' % (CR[0], CR[1], RC, ACQUA))
    # Naviglio Pavese: larghezza = sale (poi chiuse) aperte in quell'anno
    anni = SERIE_CIN['anni']; ch = SERIE_CIN['chiuse']
    i0 = anni.index(1896); A = anni[i0:]; V = ch[i0:]
    mx = max(V)
    sx, dx = [], []
    for k, (a, v) in enumerate(zip(A, V)):
        f = k / (len(A) - 1)
        (x, y), (nx, ny), _ = pavese.at(f)
        w = 6 + 86 * v / mx
        sx.append((x + nx * w / 2, y + ny * w / 2)); dx.append((x - nx * w / 2, y - ny * w / 2))
    poly = sx + dx[::-1]
    b.append('<path d="%s" fill="%s" stroke="%s" stroke-width="10" stroke-linejoin="round"/>' % (poly_d(poly, True), ACQUA, ALZAIA))
    b.append('<path d="%s" fill="%s"/>' % (poly_d(poly, True), ACQUA))
    kp = V.index(mx); (px, py), _, _ = pavese.at(kp / (len(A) - 1))
    # Naviglio Grande: l'acqua ha il colore della temperatura, un anno per tratto
    vals = [a['tmedia'] for a in TEMP if a['ok']]; lo, hi = min(vals), max(vals)
    n = len(TEMP)
    b.append(acqua(grande, 44))
    for k, a in enumerate(TEMP):
        f1, f2 = k / n, (k + 1) / n + .002
        (x1, y1), (nx1, ny1), _ = grande.at(f1); (x2, y2), (nx2, ny2), _ = grande.at(f2)
        w = 22
        q = [(x1 + nx1 * w, y1 + ny1 * w), (x2 + nx2 * w, y2 + ny2 * w), (x2 - nx2 * w, y2 - ny2 * w), (x1 - nx1 * w, y1 - ny1 * w)]
        col = colore_t(a['tmedia'], lo, hi) if a['ok'] else '#b4001e'
        b.append('<path d="%s" fill="%s"/>' % (poly_d(q, True), col))
    # Darsena
    b.append('<rect x="318" y="700" width="180" height="84" rx="38" fill="%s" stroke="%s" stroke-width="8" transform="rotate(-12 408 742)"/>' % (ACQUA, ALZAIA))
    b.append(T(408, 735, 'DARSENA', 18, '#fff', GROT, '900', 'middle', 'letter-spacing="2" transform="rotate(-12 408 742)"'))
    b.append(T(408, 757, 'qui è il 2026', 14, '#cfe6ff', GROT, '700', 'middle', 'transform="rotate(-12 408 742)"'))
    # Cerchia: La Scala, titoli per stagione (barre verso l'interno)
    cnt = collections.Counter(r[0] for r in SCALA if r[0] <= 2026)
    yrs = list(range(1778, 2027)); mxs = max(cnt.values())
    gap = 26; a0 = -90 + gap / 2; span = 360 - gap
    for k, y in enumerate(yrs):
        v = cnt.get(y, 0)
        if not v:
            continue
        g1 = a0 + span * k / len(yrs); g2 = g1 + span / len(yrs) * .8
        b.append(settore(CR, RC - 20 - 64 * v / mxs, RC - 20, g1, g2, '#FFD200'))
    b.append('<circle cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="4 3"/>' % (CR[0], CR[1], RC, ACQUA2))
    b.append('<circle cx="%d" cy="%d" r="6" fill="#fff" stroke="%s" stroke-width="3"/>' % (CR[0], CR[1], NERO))
    b.append(T(CR[0], CR[1] + 24, 'Duomo', 14, '#fff', GROT, '800', 'middle'))
    p1 = (CR[0] + (RC + 30) * math.cos(math.radians(a0)), CR[1] + (RC + 30) * math.sin(math.radians(a0)))
    b.append(T(CR[0], CR[1] - RC - 28, '2026 ← · → 1778', 14, '#fff', GROT, '800', 'middle', 'stroke="#111" stroke-width="4" stroke-linejoin="round" paint-order="stroke"'))
    # Martesana: derby. Barche ormeggiate: Inter su una riva, Milan sull'altra, pareggi in acqua
    bins = collections.defaultdict(collections.Counter)
    for x in DERBY:
        bins[(int(x['date'][:4]) - 1905) // 5][x['w']] += 1
    nb = (2026 - 1905) // 5 + 1
    def barca(x, y, ang, col):
        return '<path d="M-7,-2.6 L6,-2.6 L8.5,0 L6,2.6 L-7,2.6 Z" fill="%s" stroke="#fff" stroke-width=".8" transform="translate(%.1f %.1f) rotate(%.1f)"/>' % (col, x, y, ang)
    for j in range(nb):
        c = bins.get(j, {})
        f = 1 - (j + .5) / nb          # 1909 lontano (in alto a destra), 2026 alla Cerchia
        f = .04 + .9 * f
        (x, y), (nx, ny), (tx, ty) = mart.at(f)
        ang = math.degrees(math.atan2(ty, tx))
        for side, key, col in ((1, 'I', INTER), (-1, 'M', MILAN)):
            for q in range(c.get(key, 0)):
                d = 25 + q * 6.5
                b.append(barca(x + nx * d * side, y + ny * d * side, ang, col))
        for q in range(c.get('D', 0)):
            off = (q % 3 - 1) * 9; along = (q // 3 - .5) * 9
            b.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#fff"/>' % (x + nx * off + tx * along, y + ny * off + ty * along))
    # nomi lungo i Navigli
    al = 'stroke="%s" stroke-width="5" stroke-linejoin="round" paint-order="stroke"' % NERO
    defs = ['<defs>']
    defs.append('<path id="tg" d="%s"/>' % poly_d(Linea(catmull([(10, 846), (110, 820), (200, 768), (300, 714)])).p))
    defs.append('<path id="tp" d="%s"/>' % poly_d(Linea(catmull([(392, 1070), (404, 960), (414, 850)])).p))
    defs.append('<path id="tm" d="%s"/>' % poly_d(Linea(catmull([(800, 330), (880, 272), (960, 216), (1060, 150)])).p))
    defs.append('</defs>')
    b += defs
    b.append('<text font-family="%s" font-size="15" font-weight="900" fill="#fff" letter-spacing="1" %s><textPath href="#tg">NAVIGLIO GRANDE · temperature</textPath></text>' % (GROT, al))
    b.append('<text font-family="%s" font-size="17" font-weight="900" fill="#fff" letter-spacing="1" %s><textPath href="#tp">PAVESE · cinema spariti</textPath></text>' % (GROT, al))
    b.append('<text font-family="%s" font-size="17" font-weight="900" fill="#fff" letter-spacing="1" %s><textPath href="#tm">MARTESANA · derby dal 1909</textPath></text>' % (GROT, al))
    b.append(T(CR[0], CR[1] - 44, 'CERCHIA', 17, '#fff', GROT, '900', 'middle', 'letter-spacing="1" ' + al))
    b.append(T(CR[0], CR[1] - 24, 'La Scala', 15, '#FFD200', GROT, '800', 'middle', al))
    b.append(T(px, py - 4, '1960', 18, '#fff', GROT, '900', 'middle', al))
    b.append(T(px, py + 16, '119 sale', 15, '#fff', GROT, '800', 'middle', al))
    b.append(T(30, 945, '1763', 22, '#fff', GROT, '900', 'start', al))
    b.append(T(486, 1066, '1896', 20, '#fff', GROT, '900', 'end', al))
    b.append(T(1062, 108, '1909', 20, '#fff', GROT, '900', 'end', al))
    # titolo
    b.append(T(32, 92, 'Milano in dati', 80, '#fff', GROT, '900', extra='letter-spacing="-2" stroke="%s" stroke-width="8" stroke-linejoin="round" paint-order="stroke"' % NERO))
    b.append(T(36, 132, 'Ogni Naviglio è una linea del tempo.', 22, '#fff', GROT, '800', extra=al))
    b.append(T(36, 158, 'Tutti arrivano in Darsena: il 2026.', 22, '#FFD200', GROT, '800', extra=al))
    # legenda in basso a destra, su una chiatta
    lx, ly = 672, 690
    b.append('<rect x="%d" y="%d" width="384" height="356" rx="14" fill="%s" opacity=".92"/>' % (lx, ly, NERO))
    # cartello con la citta' vera: 88 quartieri e i Navigli al loro posto (tracciati indicativi)
    b.append('<rect x="36" y="196" width="400" height="430" rx="14" fill="#fff"/>')
    Pm = Proj(box=(52, 252, 368, 330))
    for i, g in NIL.items():
        b.append('<path d="%s" fill="#E6F2E8" stroke="#9CC7A6" stroke-width=".8"/>' % path(g, Pm))
    b.append('<path d="%s" fill="none" stroke="#111" stroke-width="1.6"/>' % path(COMUNE, Pm))
    veri = [
        [(9.1765, 45.4527), (9.1650, 45.4498), (9.1420, 45.4440), (9.1150, 45.4380), (9.0850, 45.4310), (9.0600, 45.4250)],
        [(9.1780, 45.4515), (9.1785, 45.4400), (9.1800, 45.4250), (9.1830, 45.4050), (9.1850, 45.3900)],
        [(9.2700, 45.5200), (9.2550, 45.5150), (9.2350, 45.5070), (9.2180, 45.4980), (9.2050, 45.4880), (9.1990, 45.4850)],
    ]
    for tr in veri:
        b.append('<path d="%s" fill="none" stroke="%s" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>' % (poly_d([Pm(*c) for c in tr]), ACQUA))
    cx0, cy0 = Pm(9.1905, 45.4655)
    b.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="%s" stroke-width="3.5"/>' % (cx0, cy0, 0.85 * Pm.s, ACQUA))
    dx0, dy0 = Pm(9.1772, 45.4521)
    b.append('<circle cx="%.1f" cy="%.1f" r="5" fill="%s" stroke="#fff" stroke-width="1.5"/>' % (dx0, dy0, ACQUA))
    b.append(T(56, 228, 'La Milano vera', 20, NERO, GROT, '900'))
    b.append(T(56, 248, '88 quartieri e i Navigli (tracciato indicativo)', 13, '#333', GROT, '500'))
    b.append(T(56, 610, 'Qui sopra, i Navigli disegnati come linee del tempo.', 13, '#333', GROT, '600'))
    righe = [
        ('<rect x="%d" y="%d" width="40" height="16" fill="url(#lgT)"/>', '263 anni', 'di temperature a Brera nel Grande: il 2026 è il più caldo (finora)'),
        ('<rect x="%d" y="%d" width="40" height="16" fill="%s"/>' % (0, 0, '#FFD200'), '4.635', 'titoli alla Scala lungo la Cerchia, uno spicchio per stagione'),
        (None, '246', 'derby sulla Martesana: barche blu Inter 91, rosse Milan 84, boe bianche pari 71'),
        ('<rect x="%d" y="%d" width="40" height="16" fill="%s"/>' % (0, 0, ACQUA), '171', 'cinema spariti: il Pavese è largo quanto le sale aperte, e si asciuga'),
    ]
    b.append('<defs><linearGradient id="lgT"><stop offset="0" stop-color="#08306b"/><stop offset=".5" stop-color="#ebebeb"/><stop offset="1" stop-color="#b4001e"/></linearGradient></defs>')
    for k, (sw, num, txt) in enumerate(righe):
        y = ly + 34 + k * 82
        if k == 0:
            b.append('<rect x="%d" y="%d" width="40" height="16" fill="url(#lgT)"/>' % (lx + 20, y - 14))
        elif k == 1:
            b.append('<rect x="%d" y="%d" width="40" height="16" fill="#FFD200"/>' % (lx + 20, y - 14))
        elif k == 2:
            b.append(barca(lx + 30, y - 6, 0, INTER)); b.append(barca(lx + 50, y - 6, 0, MILAN))
        else:
            b.append('<rect x="%d" y="%d" width="40" height="16" fill="%s"/>' % (lx + 20, y - 14, ACQUA))
        b.append(T(lx + 72, y + 2, num, 30, '#fff', GROT, '900'))
        parole = txt.split(' '); r1, r2 = [], []
        for p in parole:
            (r1 if len(' '.join(r1 + [p])) <= 42 and not r2 else r2).append(p)
        b.append(T(lx + 20, y + 26, ' '.join(r1), 14, '#DDE6EE', GROT, '500'))
        b.append(T(lx + 20, y + 44, ' '.join(r2), 14, '#DDE6EE', GROT, '500'))
    salva('bozza_8_navigli.svg', svg('\n'.join(b), PRATO, 'Milano in dati - bozza 8, Navigli'))

if __name__ == '__main__':
    bozza5(); bozza6(); bozza7(); bozza8()
