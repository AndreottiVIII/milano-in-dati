# -*- coding: utf-8 -*-
"""Bozze 17-20 della home di "Milano in dati" (alla Noorda: rosso MM, bianco, griglia, un solo carattere).
1080x1080, SVG ferme senza navigazione, colori piatti. Riusa mappa e funzioni di genera_bozze.py; legge solo docs/.
In coda fa anche il foglio con tutte le bozze 1-20 (anteprime/tutte_le_bozze.png).
Uso: python -I genera_bozze_5.py
"""
import os, sys, glob
QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from genera_bozze import NIL, COMUNE, Proj, path, svg, T, salva, centro_nil

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
ROSSO = '#E30613'; NERO = '#111111'; GRIGIO = '#E4E4E4'; GRIGIO2 = '#9A9A9A'; BIANCO = '#FFFFFF'; FONDO = '#F4F4F4'
LINEE = {'M1': '#E3001B', 'M2': '#00A650', 'M3': '#FFD200', 'M4': '#0072BC', 'M5': '#9B5BA5'}

def mappa(P, fill, stroke, sw=.8, contorno=None, csw=1.6):
    out = []
    for i, gg in NIL.items():
        out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(gg, P), fill, stroke, sw))
    if contorno:
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(COMUNE, P), contorno, csw))
    return ''.join(out)

# =================================================================== BOZZA 17  fascia MM
def bozza17():
    b = ['<rect width="1080" height="1080" fill="#FFFFFF"/>']
    b.append('<rect width="1080" height="170" fill="%s"/>' % ROSSO)
    b.append(T(60, 118, 'Milano in dati', 92, BIANCO, SANS, '700', extra='letter-spacing="-2"'))
    b.append('<rect x="936" y="40" width="90" height="90" fill="%s"/>' % BIANCO)
    b.append(T(981, 112, 'M', 82, ROSSO, SANS, '700', 'middle'))
    b.append('<rect y="170" width="1080" height="8" fill="%s"/>' % NERO)
    b.append(T(60, 230, '19 storie · 88 quartieri · dal 1763 al 2026', 24, NERO, SANS, '400'))
    P = Proj(box=(60, 260, 600, 720))
    b.append(mappa(P, GRIGIO, BIANCO, 1.2))
    b.append('<path d="%s" fill="%s"/>' % (path(NIL[82], P), ROSSO))
    cx, cy = centro_nil(82, P)
    b.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>' % (cx, cy, BIANCO))
    nums = [('1763', 'anno dei primi dati di temperatura a Brera'), ('246', 'derby giocati a Milano'),
            ('4.635', 'titoli rappresentati alla Scala'), ('38%', 'stranieri a Comasina, il quartiere in rosso')]
    for k, (n, l) in enumerate(nums):
        y = 300 + k * 175
        b.append('<rect x="720" y="%d" width="300" height="3" fill="%s"/>' % (y - 56, NERO))
        b.append(T(718, y + 34, n, 86, ROSSO if k == 3 else NERO, SANS, '700', extra='letter-spacing="-3"'))
        b.append(T(720, y + 70, l, 17, NERO, SANS, '400'))
    b.append('<rect x="60" y="1010" width="960" height="2" fill="%s"/>' % NERO)
    b.append(T(60, 1044, 'Temperature · Aria · Area C · Scala · Cinema · Derby · Elezioni · Censimenti · e altre 11', 18, GRIGIO2, SANS, '400'))
    salva('bozza_17_mm.svg', svg('\n'.join(b), BIANCO, 'Milano in dati - bozza 17, fascia MM'))

# =================================================================== BOZZA 18  poster a griglia
def bozza18():
    b = ['<rect width="1080" height="1080" fill="%s"/>' % FONDO]
    # griglia: margine 60, 6 colonne da 140 con 12 di canale
    b.append('<rect x="60" y="60" width="960" height="3" fill="%s"/>' % NERO)
    b.append(T(60, 112, 'Milano', 54, NERO, SANS, '700', extra='letter-spacing="-1.5"'))
    b.append(T(60, 168, 'in dati', 54, ROSSO, SANS, '700', extra='letter-spacing="-1.5"'))
    P = Proj(box=(360, 90, 660, 880))
    b.append(mappa(P, BIANCO, NERO, .7, NERO, 2))
    b.append('<path d="%s" fill="%s"/>' % (path(NIL[82], P), ROSSO))
    cx, cy = centro_nil(82, P)
    b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="1.5" fill="%s"/>' % (cx, cy - 1, 300, NERO))
    b.append(T(cx + 300 - 4, cy - 10, '38%', 22, NERO, SANS, '700', 'end'))
    nums = [('1763', 'temperature a Brera'), ('246', 'derby'), ('4.635', 'titoli alla Scala'), ('88', 'quartieri')]
    for k, (n, l) in enumerate(nums):
        y = 330 + k * 160
        b.append('<rect x="60" y="%d" width="270" height="1.5" fill="%s"/>' % (y - 70, NERO))
        b.append(T(58, y + 20, n, 100 if len(n) < 5 else 88, NERO if k else ROSSO, SANS, '700', extra='letter-spacing="-4"'))
        b.append(T(60, y + 52, l, 19, NERO, SANS, '400'))
    b.append('<rect x="60" y="1008" width="960" height="1.5" fill="%s"/>' % NERO)
    b.append(T(60, 1042, '19 storie sulla città, dal 1763 al 2026', 18, NERO, SANS, '400'))
    b.append(T(1020, 1042, 'Comasina, 38% di stranieri nel 2023', 18, ROSSO, SANS, '700', 'end'))
    salva('bozza_18_griglia.svg', svg('\n'.join(b), FONDO, 'Milano in dati - bozza 18, poster a griglia'))

# =================================================================== BOZZA 19  le cinque linee
GRUPPI = [('M1', 'Clima e ambiente', ['Temperature', 'Aria', 'Neve e nebbia', 'Acqua del sindaco']),
          ('M2', 'Chi siamo', ['Censimenti', 'Donne nelle vie', 'Prezzi delle case', 'Bilancio del Comune']),
          ('M3', 'Muoversi', ['Area C', 'Bici, auto, mezzi', 'Città dei 15 minuti', 'Nomi delle fermate']),
          ('M4', 'Cultura', ['La Scala', 'Beni culturali', 'Milano raccontata', 'Cinema spariti']),
          ('M5', 'Passioni e conflitti', ['Derby', 'Elezioni', 'Violenza politica'])]

def bozza19():
    b = ['<rect width="1080" height="1080" fill="#FFFFFF"/>']
    b.append(T(50, 96, 'Milano in dati', 64, NERO, SANS, '700', extra='letter-spacing="-1.5"'))
    b.append(T(1030, 96, '19 storie su 5 linee', 24, NERO, SANS, '400', 'end'))
    b.append('<rect x="50" y="116" width="980" height="3" fill="%s"/>' % NERO)
    P = Proj(box=(150, 140, 780, 600))
    b.append(mappa(P, GRIGIO, BIANCO, 1.1))
    b.append('<path d="%s" fill="%s"/>' % (path(NIL[82], P), NERO))
    # sei puntini colorati sulla mappa, uno per linea, come fermate
    for (cod, _, _), i in zip(GRUPPI, (82, 2, 33, 64, 43)):
        x, y = centro_nil(i, P)
        b.append('<circle cx="%.1f" cy="%.1f" r="10" fill="%s" stroke="#fff" stroke-width="3"/>' % (x, y, LINEE[cod]))
    for k, (cod, nome, lista) in enumerate(GRUPPI):
        x = 50 + k * 198
        col = LINEE[cod]
        b.append('<rect x="%d" y="770" width="186" height="10" fill="%s"/>' % (x, col))
        b.append('<circle cx="%d" cy="838" r="26" fill="%s"/>' % (x + 26, col))
        b.append(T(x + 26, 847, cod, 24, NERO if cod == 'M3' else BIANCO, SANS, '700', 'middle'))
        b.append(T(x, 900, nome, 19, NERO, SANS, '700'))
        for j, s in enumerate(lista):
            b.append(T(x, 936 + j * 28, s, 17, NERO, SANS, '400'))
    salva('bozza_19_linee.svg', svg('\n'.join(b), BIANCO, 'Milano in dati - bozza 19, le cinque linee'))

# =================================================================== BOZZA 20  croce rossa
def bozza20():
    b = ['<rect width="1080" height="1080" fill="#FFFFFF"/>']
    b.append('<rect x="495" y="0" width="90" height="1080" fill="%s"/>' % ROSSO)
    b.append('<rect x="0" y="495" width="1080" height="90" fill="%s"/>' % ROSSO)
    P = Proj(box=(250, 250, 580, 580))
    b.append(mappa(P, BIANCO, ROSSO, 1, ROSSO, 3))
    quadranti = [(48, 'Milano', None), ]
    b.append(T(48, 110, 'Milano', 40, NERO, SANS, '700', extra='letter-spacing="-1"'))
    b.append(T(48, 152, 'in dati', 40, ROSSO, SANS, '700', extra='letter-spacing="-1"'))
    q = [(48, 420, '1763', 'temperature a Brera'), (1032, 420, '246', 'derby'), (48, 1000, '4.635', 'titoli alla Scala'), (1032, 1000, '88', 'quartieri')]
    for x, y, n, l in q:
        an = 'start' if x < 500 else 'end'
        b.append(T(x, y, n, 104, ROSSO, SANS, '700', an, 'letter-spacing="-5"'))
        b.append(T(x, y + 38, l, 22, NERO, SANS, '400', an))
    salva('bozza_20_croce.svg', svg('\n'.join(b), BIANCO, 'Milano in dati - bozza 20, croce rossa'))

NOMI = ['Mosaico', 'Metro', 'Cerchi', 'Manifesto', 'Skyline', 'Tabellone', 'Galleria', 'Navigli', 'Insegne', 'Prima pagina',
        'Memphis', 'Tram', 'Cantiere', 'Modernista', 'Terminale', 'Risografia', 'Fascia MM', 'Poster a griglia', 'Cinque linee', 'Croce rossa']

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

def foglio():
    from PIL import Image, ImageDraw, ImageFont
    W, CW, CH, IM, COLS = 2400, 480, 540, 440, 5
    righe = (len(NOMI) + COLS - 1) // COLS
    img = Image.new('RGB', (W, righe * CH + 20), '#FFFFFF')
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('arialbd.ttf', 28)
    except Exception:
        f = ImageFont.load_default()
    for k, nome in enumerate(NOMI):
        r, c = divmod(k, COLS)
        fs = glob.glob(os.path.join(QUI, 'anteprime', 'bozza_%d_*.png' % (k + 1)))
        x, y = c * CW + 20, r * CH + 20
        if fs:
            im = Image.open(fs[0]).convert('RGB').resize((IM, IM), Image.LANCZOS)
            img.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + IM, y + IM], outline='#BBBBBB')
        d.text((x, y + IM + 10), '%d  %s' % (k + 1, nome), fill='#111111', font=f)
    img.save(os.path.join(QUI, 'anteprime', 'tutte_le_bozze.png'))
    print('foglio', img.size)

if __name__ == '__main__':
    bozza17(); bozza18(); bozza19(); bozza20()
    anteprime(['bozza_17_mm.svg', 'bozza_18_griglia.svg', 'bozza_19_linee.svg', 'bozza_20_croce.svg'])
    foglio()
