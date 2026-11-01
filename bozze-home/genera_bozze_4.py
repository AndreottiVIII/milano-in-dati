# -*- coding: utf-8 -*-
"""Bozze 13-16 della home di "Milano in dati" (1080x1080, SVG ferme, nessuna navigazione).
Riusa mappa e funzioni di genera_bozze.py; legge solo docs/ (non lo modifica). Anteprime PNG con Playwright.
Uso: python -I genera_bozze_4.py
"""
import os, sys, math, random
QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from genera_bozze import NIL, NILINFO, COMUNE, Proj, path, esc, svg, T, salva, TEMP, centro_nil

BAH = "Bahnschrift, Arial Narrow, Segoe UI, Arial, sans-serif"
BAHC = "Bahnschrift SemiBold Condensed, Bahnschrift, Arial Narrow, Impact, sans-serif"
IMP = "Impact, Haettenschweiler, Arial Narrow, sans-serif"
BLACK = "Arial Black, Archivo Black, Impact, sans-serif"
MONO = "Consolas, Lucida Console, Courier New, monospace"
TOK = [a for a in TEMP if a['ok']]

STORIE = ['Temperature', 'Donne nelle vie', 'Beni culturali', 'Elezioni', 'Aria', 'Area C', 'Bici, auto, mezzi',
          'La Scala', 'Città dei 15 minuti', 'Violenza politica', 'Milano raccontata', 'Prezzi delle case',
          'Neve e nebbia', 'Cinema spariti', 'Derby', 'Nomi delle fermate', 'Bilancio del Comune',
          "Acqua del sindaco", 'Censimenti']
# solo numeri gia' usati nelle bozze 1-12 (letti da docs/); gli altri restano vuoti
NUM = {0: 'dal 1763', 3: 'dal 1946', 5: '−16%', 7: '4.635', 9: 'dal 1919', 12: 'dal 1950', 13: '171', 14: '246', 18: '19,6%'}

def media_mobile(v, k):
    return [sum(v[max(0, i - k // 2): i + k // 2 + 1]) / len(v[max(0, i - k // 2): i + k // 2 + 1]) for i in range(len(v))]

def poly(pts):
    return 'M' + 'L'.join('%.1f,%.1f' % p for p in pts)

# =================================================================== BOZZA 13  CANTIERE
def bozza13():
    GIALLO = '#FFC800'; NERO = '#0D0D0D'; BIANCO = '#FFFFFF'; ARANCIO = '#FF7A00'
    b = ['<defs><pattern id="haz" width="48" height="48" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="48" height="48" fill="%s"/><rect width="24" height="48" fill="%s"/></pattern></defs>' % (GIALLO, NERO)]
    b.append('<rect width="1080" height="1080" fill="%s"/>' % GIALLO)
    b.append('<rect width="1080" height="40" fill="url(#haz)"/>')
    b.append('<rect y="1040" width="1080" height="40" fill="url(#haz)"/>')
    b.append(T(26, 214, 'MILANO', 196, NERO, IMP, '400', extra='textLength="560" lengthAdjust="spacingAndGlyphs"'))
    b.append('<rect x="610" y="72" width="444" height="150" fill="%s"/>' % NERO)
    b.append(T(632, 196, 'IN DATI', 150, GIALLO, IMP, '400', extra='textLength="400" lengthAdjust="spacingAndGlyphs"'))
    b.append('<circle cx="1030" cy="92" r="14" fill="%s" stroke="%s" stroke-width="3"/>' % (ARANCIO, NERO))
    b.append(T(28, 262, 'LAVORI IN CORSO · 19 STORIE · 88 QUARTIERI · DATI DAL 1763 AL 2026', 25, NERO, BAH, '800', extra='letter-spacing="1"'))
    X0, Y0, W, H, G = 28, 282, 247, 128, 10
    for k in range(20):
        r, c = divmod(k, 4)
        x, y = X0 + c * (W + G), Y0 + r * (H + G)
        nero = (r + c) % 2 == 0 or k == 19
        fg = GIALLO if nero else NERO
        tx = BIANCO if nero else NERO
        b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="5"/>' % (x, y, W, H, NERO if nero else BIANCO, NERO))
        b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" stroke-width="2" opacity=".9"/>' % (x + 7, y + 7, W - 14, H - 14, fg if nero else NERO))
        if k < 19:
            b.append(T(x + 16, y + 56, '%02d' % (k + 1), 52, fg, IMP, '400'))
            if k in NUM:
                b.append(T(x + W - 16, y + 54, NUM[k], 28, ARANCIO if nero else NERO, BAHC, '800', 'end'))
            b.append(T(x + 16, y + 100, STORIE[k].upper(), 20, tx, BAHC, '800', extra='letter-spacing=".5"'))
        else:
            pm = Proj(box=(x + 12, y + 10, W - 24, H - 20))
            b.append('<path d="%s" fill="#222" stroke="%s" stroke-width="1.2"/>' % (path(COMUNE, pm), GIALLO))
            for i, gg in NIL.items():
                b.append('<path d="%s" fill="none" stroke="%s" stroke-width=".5" stroke-opacity=".7"/>' % (path(gg, pm), GIALLO))
            for i in (82, 33):
                b.append('<path d="%s" fill="%s"/>' % (path(NIL[i], pm), ARANCIO))
            b.append(T(x + W - 12, y + H - 12, '88 NIL', 18, GIALLO, BAHC, '800', 'end'))
    b.append(T(540, 1030, 'DEVIAZIONE OBBLIGATORIA: SI PASSA DAI NUMERI', 22, NERO, BAHC, '800', 'middle', 'letter-spacing="2"'))
    salva('bozza_13_cantiere.svg', svg('\n'.join(b), GIALLO, 'Milano in dati - bozza 13, cantiere'))

# =================================================================== BOZZA 14  MANIFESTO MODERNISTA
def bozza14():
    ROSSO = '#E30613'; COBALTO = '#0B2FD6'; NERO = '#0A0A0A'; GIALLO = '#FFD400'
    b = []
    b.append('<rect width="1080" height="1080" fill="#FFFFFF"/>')
    b.append('<rect width="150" height="1080" fill="%s"/>' % ROSSO)
    b.append('<text transform="translate(122 1050) rotate(-90)" font-family="%s" font-size="148" fill="#fff" letter-spacing="-6" textLength="1010" lengthAdjust="spacingAndGlyphs">milano in dati</text>' % BLACK)
    P = Proj(box=(196, 48, 560, 620))
    b.append('<path d="%s" fill="%s"/>' % (path(COMUNE, P), COBALTO))
    for i, gg in NIL.items():
        b.append('<path d="%s" fill="none" stroke="#fff" stroke-width=".9"/>' % path(gg, P))
    b.append('<path d="%s" fill="%s"/>' % (path(NIL[82], P), ROSSO))
    cx, cy = centro_nil(82, P)
    b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="4"/>' % (cx, cy, 790, 120, NERO))
    b.append(T(790, 112, '38%', 74, ROSSO, BLACK, '400', extra='letter-spacing="-3"'))
    b.append(T(792, 140, 'stranieri a Comasina', 20, NERO, BAH, '700'))
    b.append('<circle cx="905" cy="330" r="140" fill="%s"/>' % GIALLO)
    b.append(T(905, 380, '88', 150, NERO, BLACK, '400', 'middle', 'letter-spacing="-8"'))
    b.append(T(905, 415, 'QUARTIERI', 20, NERO, BAH, '800', 'middle', 'letter-spacing="4"'))
    b.append('<rect x="760" y="494" width="290" height="176" fill="%s"/>' % NERO)
    b.append(T(776, 580, '1763', 80, '#fff', BLACK, '400', extra='letter-spacing="-4"'))
    b.append(T(776, 630, '→ 2026', 46, ROSSO, BLACK, '400'))
    b.append(T(776, 656, 'le temperature a Brera', 16, '#fff', BAH, '700'))
    b.append(T(196, 718, '19 STORIE', 20, ROSSO, BAH, '800', extra='letter-spacing="4"'))
    cols = [(196, range(0, 7)), (480, range(7, 13)), (764, range(13, 19))]
    for x, rg in cols:
        for r, k in enumerate(rg):
            y = 760 + r * 46
            b.append('<rect x="%d" y="%d" width="276" height="2" fill="%s"/>' % (x, y - 31, NERO))
            b.append(T(x, y, '%d' % (k + 1), 28, ROSSO, BLACK, '400'))
            b.append(T(x + 42, y, STORIE[k].lower(), 19, NERO, BLACK, '400', extra='letter-spacing="-.4"'))
    salva('bozza_14_modernista.svg', svg('\n'.join(b), '#FFFFFF', 'Milano in dati - bozza 14, manifesto modernista'))

# =================================================================== BOZZA 15  TERMINALE
def bozza15():
    AMB = '#FFA11A'; AMB2 = '#7A4A00'; VERDE = '#27E07A'; ROSSO = '#FF4040'; BIA = '#EDEDED'; PAN = '#140C00'
    b = ['<rect width="1080" height="1080" fill="#000"/>']
    def pannello(x, y, w, h, tit):
        b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="1.5"/>' % (x, y, w, h, PAN, AMB2))
        b.append('<rect x="%d" y="%d" width="%d" height="22" fill="%s"/>' % (x, y, w, AMB2))
        b.append(T(x + 8, y + 16, tit, 14, '#FFD08A', MONO, '700', extra='letter-spacing="1"'))
    b.append('<rect width="1080" height="40" fill="%s"/>' % AMB)
    b.append(T(14, 28, 'MILANO IN DATI', 24, '#000', MONO, '700'))
    b.append(T(1066, 28, 'COMUNE DI MILANO  ·  19 STORIE  ·  88 NIL  ·  1763-2026', 16, '#000', MONO, '700', 'end'))
    b.append('<rect x="14" y="52" width="1052" height="30" fill="#000" stroke="%s" stroke-width="1.5"/>' % AMB)
    b.append(T(24, 73, 'STORIE <GO>', 18, AMB, MONO, '700'))
    b.append('<rect x="146" y="58" width="12" height="18" fill="%s"/>' % AMB)
    pannello(14, 94, 500, 640, 'ELENCO STORIE  ·  19')
    cod = ['TEMP', 'DONNE', 'BENI', 'ELEZ', 'ARIA', 'AREAC', 'MOBIL', 'SCALA', '15MIN', 'VIOL', 'FILM', 'CASE', 'NEVE', 'CINE', 'DERBY', 'FERM', 'BILAN', 'ACQUA', 'CENS']
    for k in range(19):
        y = 138 + k * 31
        if k % 2 == 0:
            b.append('<rect x="15" y="%d" width="498" height="31" fill="#1E1200"/>' % (y - 22))
        b.append(T(24, y, '%02d' % (k + 1), 17, AMB2, MONO, '700'))
        b.append(T(60, y, cod[k], 17, AMB, MONO, '700'))
        b.append(T(150, y, STORIE[k].upper(), 17, BIA, MONO, '400'))
        if k in NUM:
            b.append(T(470, y, NUM[k], 16, VERDE if not NUM[k].startswith('−') else ROSSO, MONO, '700', 'end'))
        b.append('<circle cx="498" cy="%d" r="4" fill="%s"/>' % (y - 5, VERDE))
    pannello(526, 94, 540, 300, 'TEMP  ·  BRERA  ·  MEDIA ANNUA  1763-2025')
    gx0, gx1, gy0, gy1 = 560, 1054, 132, 376
    v = [a['tmedia'] for a in TOK]; lo, hi = min(v) - .3, max(v) + .3
    for t in range(int(lo) + 1, int(hi) + 1):
        y = gy1 - (t - lo) / (hi - lo) * (gy1 - gy0)
        b.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1" stroke-dasharray="2 4"/>' % (gx0, y, gx1, y, AMB2))
        b.append(T(gx0 - 6, y + 5, '%d' % t, 13, AMB, MONO, '400', 'end'))
    pts = [(gx0 + (a['anno'] - 1763) / 262 * (gx1 - gx0), gy1 - (a['tmedia'] - lo) / (hi - lo) * (gy1 - gy0)) for a in TOK]
    mm = media_mobile(v, 11)
    pm = [(p[0], gy1 - (m - lo) / (hi - lo) * (gy1 - gy0)) for p, m in zip(pts, mm)]
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="1" opacity=".8"/>' % (poly(pts), '#9A8A6A'))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="2.6"/>' % (poly(pm), AMB))
    b.append(T(gx0, 392, '1763', 13, AMB, MONO, '700')); b.append(T(gx1, 392, '2025', 13, AMB, MONO, '700', 'end'))
    b.append(T(gx1 - 4, gy0 + 16, '▲ 2026 IL PIÙ CALDO (FINORA)', 14, VERDE, MONO, '700', 'end'))
    pannello(526, 406, 330, 328, 'NIL  ·  STRANIERI 2023')
    P = Proj(box=(534, 436, 314, 290))
    ramp = ['#2A1800', '#5A3500', '#8A5200', '#C27800', '#FFA11A', '#FFD27A']
    for i, gg in NIL.items():
        n = NILINFO[i]; s = n['v']['str'][4]
        f = '#111' if (s is None or not n['ok']) else ramp[min(5, int(s / 6))]
        b.append('<path d="%s" fill="%s" stroke="#000" stroke-width=".7"/>' % (path(gg, P), f))
    cx, cy = centro_nil(82, P)
    b.append('<circle cx="%.1f" cy="%.1f" r="9" fill="none" stroke="%s" stroke-width="2.5"/>' % (cx, cy, VERDE))
    pannello(868, 406, 198, 328, 'DERBY  ·  246')
    for k, (n, nome, col) in enumerate(((91, 'INTER', '#4F8BFF'), (71, 'PARI', '#AAA'), (84, 'MILAN', ROSSO))):
        x = 888 + k * 58; h = n / 91 * 230
        b.append('<rect x="%d" y="%.1f" width="44" height="%.1f" fill="%s"/>' % (x, 690 - h, h, col))
        b.append(T(x + 22, 690 - h - 6, str(n), 17, BIA, MONO, '700', 'middle'))
        b.append(T(x + 22, 712, nome, 11, AMB, MONO, '700', 'middle'))
    pannello(14, 746, 1052, 214, 'QUOTAZIONI')
    big = [('SCALA', '4.635', 'titoli dal 1778', VERDE), ('CINEMA', '171', 'sale sparite', ROSSO), ('DERBY', '+7', 'Inter avanti', '#4F8BFF'),
           ('AREA C', '−16%', 'ingressi dal 2019', ROSSO), ('STRANIERI', '19,6%', 'in città, 2023', VERDE), ('ROGOREDO', '+172%', 'abitanti dal 1991', VERDE)]
    for k, (a, n, c, col) in enumerate(big):
        x = 28 + (k % 3) * 348; y = 800 + (k // 3) * 80
        b.append(T(x, y - 6, a, 14, AMB, MONO, '700', extra='letter-spacing="1"'))
        b.append(T(x, y + 36, n, 44, col, MONO, '700'))
        b.append(T(x + 190, y + 36, c, 14, '#B8A888', MONO, '400'))
    b.append('<rect x="0" y="978" width="1080" height="102" fill="%s"/>' % AMB)
    b.append(T(14, 1018, 'TEMP 1763-2026 ▲   DERBY 246  91-71-84   SCALA 4.635 ▲', 26, '#000', MONO, '700'))
    b.append(T(14, 1058, 'CINEMA 171 ▼   AREA C −16% ▼   ROGOREDO +172% ▲   STRANIERI 19,6% ▲', 26, '#000', MONO, '700'))
    salva('bozza_15_terminale.svg', svg('\n'.join(b), '#000', 'Milano in dati - bozza 15, terminale'))

# =================================================================== BOZZA 16  RISOGRAFIA
def bozza16():
    ROSA = '#FF3E9E'; BLU = '#1D4FE0'
    mul = 'style="mix-blend-mode:multiply"'
    b = ['<defs>']
    for k, r in enumerate((0.8, 1.6, 2.4, 3.2, 4.0, 4.8)):
        b.append('<pattern id="d%d" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(15)"><circle cx="5" cy="5" r="%.1f" fill="%s"/></pattern>' % (k, r, ROSA))
    b.append('<pattern id="rig" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(-30)"><rect width="8" height="2.4" fill="%s"/></pattern>' % BLU)
    b.append('<filter id="grana" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="7"/>'
             '<feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 -2.6 1.45"/></filter></defs>')
    b.append('<rect width="1080" height="1080" fill="#FFFFFF"/>')
    b.append('<circle cx="860" cy="200" r="190" fill="%s" %s/>' % (ROSA, mul))
    b.append(T(30, 232, 'MILANO', 258, ROSA, IMP, '400', extra='textLength="760" lengthAdjust="spacingAndGlyphs" transform="translate(9 7)" ' + mul))
    b.append(T(30, 232, 'MILANO', 258, BLU, IMP, '400', extra='textLength="760" lengthAdjust="spacingAndGlyphs" ' + mul))
    b.append(T(30, 390, 'in dati', 150, BLU, IMP, '400', extra='textLength="380" lengthAdjust="spacingAndGlyphs" ' + mul))
    P = Proj(box=(400, 270, 650, 570))
    for i, gg in NIL.items():
        n = NILINFO[i]; s = n['v']['str'][4]
        f = 'url(#rig)' if (s is None or not n['ok']) else 'url(#d%d)' % min(5, int(s / 5.5))
        b.append('<path d="%s" fill="%s" stroke="%s" stroke-width="1" %s/>' % (path(gg, P), f, ROSA, mul))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="3.5" transform="translate(6 5)" %s/>' % (path(COMUNE, P), BLU, mul))
    cx, cy = centro_nil(82, P)
    b.append('<circle cx="%.1f" cy="%.1f" r="22" fill="none" stroke="%s" stroke-width="4" %s/>' % (cx, cy, BLU, mul))
    b.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="3" %s/>' % (cx - 14, cy - 8, 606, 300, BLU, mul))
    b.append(T(430, 306, '38%', 64, BLU, IMP, '400', extra=mul))
    b.append(T(432, 330, 'stranieri a Comasina', 18, BLU, BAH, '800', extra=mul))
    b.append(T(1050, 856, 'più punti, più stranieri (2023)', 15, BLU, BAH, '700', 'end', mul))
    for k in range(19):
        y = 452 + k * 30
        if k % 2 == 0:
            b.append('<rect x="24" y="%d" width="340" height="26" fill="%s" %s/>' % (y - 20, ROSA, mul))
        b.append(T(32, y, '%02d' % (k + 1), 20, BLU, IMP, '400', extra=mul))
        b.append(T(76, y, STORIE[k].upper(), 20, BLU, BAHC, '800', extra='letter-spacing=".5" ' + mul))
    n = len(TEMP); w = 640 / n
    vals = [a['tmedia'] for a in TOK]; lo, hi = min(vals), max(vals)
    for k, a in enumerate(TEMP):
        x = 410 + k * w
        if a['ok']:
            h = 14 + 110 * (a['tmedia'] - lo) / (hi - lo)
            b.append('<rect x="%.1f" y="%.1f" width="%.2f" height="%.1f" fill="%s" %s/>' % (x, 1030 - h, w + .2, h, BLU, mul))
        else:
            b.append('<rect x="%.1f" y="900" width="%.2f" height="130" fill="%s" %s/>' % (x - 2, w + 4, ROSA, mul))
    b.append(T(410, 884, 'Brera, 1763-2026: ogni barra è un anno', 18, BLU, BAH, '800', extra=mul))
    b.append(T(1050, 884, '2026, il più caldo (finora)', 18, ROSA, BAH, '800', 'end'))
    b.append(T(30, 1050, '19 storie · 88 quartieri · 2 colori', 20, BLU, BAH, '800', extra=mul))
    b.append('<rect width="1080" height="1080" filter="url(#grana)" opacity=".4"/>')
    salva('bozza_16_riso.svg', svg('\n'.join(b), '#FFFFFF', 'Milano in dati - bozza 16, risografia'))

def anteprime(nomi):
    from playwright.sync_api import sync_playwright
    os.makedirs(os.path.join(QUI, 'anteprime'), exist_ok=True)
    with sync_playwright() as p:
        try:
            br = p.chromium.launch()
        except Exception:
            br = p.chromium.launch(channel='msedge')
        pg = br.new_page(viewport={'width': 1080, 'height': 1080})
        for n in nomi:
            pg.goto('file:///' + os.path.join(QUI, n).replace('\\', '/'))
            pg.screenshot(path=os.path.join(QUI, 'anteprime', n.replace('.svg', '.png')))
            print('png', n)
        br.close()

if __name__ == '__main__':
    bozza13(); bozza14(); bozza15(); bozza16()
    anteprime(['bozza_13_cantiere.svg', 'bozza_14_modernista.svg', 'bozza_15_terminale.svg', 'bozza_16_riso.svg'])
