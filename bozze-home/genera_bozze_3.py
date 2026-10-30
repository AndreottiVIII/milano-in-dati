# -*- coding: utf-8 -*-
"""Bozze 9-12 della home di "Milano in dati" (1080x1080, SVG autonome).
Riusa mappa, proiezione e funzioni di genera_bozze.py e genera_bozze_2.py; legge solo docs/ (non lo modifica).
Uso: python -I genera_bozze_3.py
"""
import os, sys, math, random, collections
QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
import genera_bozze as G
from genera_bozze import NIL, NILINFO, COMUNE, Proj, path, esc, svg, T, GROT, IMPACT, salva, TEMP, STAZ, centro_nil
from genera_bozze_2 import catmull, Linea, poly_d, settore, DERBY

SCRIPT = "Segoe Script, Brush Script MT, Comic Sans MS, cursive"

def media_mobile(v, k):
    out = []
    for i in range(len(v)):
        w = v[max(0, i - k // 2): i + k // 2 + 1]
        out.append(sum(w) / len(w))
    return out

TOK = [a for a in TEMP if a['ok']]          # anni completi (il 2026 e' in corso: fuori dalle curve)

# =================================================================== BOZZA 9
def bozza9():
    """Le insegne al neon: piazza di notte, ogni numero e' un'insegna"""
    random.seed(9)
    MURO = '#0B0712'; ROSA = '#FF2E88'; CIANO = '#2EF2FF'; GIALLO = '#FFE53B'; VERDE = '#39FF6A'
    ROSSO = '#FF2A2A'; VIOLA = '#B266FF'; ARANCIO = '#FF8A1F'; BLU = '#3D7BFF'
    b = []
    b.append('<defs>'
             '<filter id="neon" x="-30%%" y="-30%%" width="160%%" height="160%%">'
             '<feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="a"/>'
             '<feGaussianBlur in="SourceGraphic" stdDeviation="9" result="c"/>'
             '<feMerge><feMergeNode in="c"/><feMergeNode in="c"/><feMergeNode in="a"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
             '<filter id="alone" x="-50%%" y="-50%%" width="200%%" height="200%%"><feGaussianBlur stdDeviation="22"/></filter>'
             '<filter id="riflesso"><feGaussianBlur stdDeviation="5"/></filter>'
             '<pattern id="mattoni" width="64" height="28" patternUnits="userSpaceOnUse">'
             '<rect width="64" height="28" fill="%s"/>'
             '<path d="M0,13.5H64M0,27.5H64M32,0V13.5M0,14V28M64,14V28" stroke="#24192F" stroke-width="2.4"/></pattern>'
             '<linearGradient id="bagnato" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#160C22"/><stop offset="1" stop-color="#05030A"/></linearGradient>'
             '<linearGradient id="tubo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/><stop offset=".55" stop-color="%s"/><stop offset=".85" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
             '</defs>' % (MURO, BLU, CIANO, ARANCIO, ROSSO))
    b.append('<rect width="1080" height="1080" fill="url(#mattoni)"/>')
    # aloni colorati sul muro, dietro le insegne
    for x, y, r, c in ((250, 120, 150, ROSA), (800, 450, 260, VIOLA), (200, 470, 170, GIALLO), (540, 850, 230, ARANCIO), (200, 700, 140, VERDE)):
        b.append('<circle cx="%d" cy="%d" r="%d" fill="%s" opacity=".16" filter="url(#alone)"/>' % (x, y, r, c))

    def tubo_testo(x, y, s, size, col, anchor='start', font=GROT, weight='400', extra='', spento=None):
        """testo a tubo: alone colorato + anima chiara. spento = indici delle lettere senza corrente"""
        if spento:
            parti = []
            for k, ch in enumerate(s):
                op = '.18' if k in spento else '1'
                parti.append('<tspan opacity="%s">%s</tspan>' % (op, esc(ch)))
            body = ''.join(parti)
        else:
            body = esc(s)
        base = '<text x="%.1f" y="%.1f" font-family="%s" font-size="%s" font-weight="%s" text-anchor="%s" %s ' % (x, y, font, size, weight, anchor, extra)
        sw = max(1.6, size / 34)
        return ('<g filter="url(#neon)">' + base + 'fill="none" stroke="%s" stroke-width="%.1f" stroke-linejoin="round">%s</text></g>' % (col, sw * 1.6, body) +
                base + 'fill="none" stroke="#FFFFFF" stroke-opacity=".85" stroke-width="%.1f">%s</text>' % (sw * .55, body))

    def cornice(x, y, w, h, col, r=14):
        d = '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" stroke="%s" stroke-width="4"/>' % (x, y, w, h, r, col)
        out = ['<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="#000" opacity=".55"/>' % (x, y, w, h, r)]
        out.append('<g filter="url(#neon)">%s</g>' % d)
        out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.3"/>' % (x, y, w, h, r))
        # staffe e fili
        for fx in (x + 24, x + w - 24):
            out.append('<rect x="%d" y="%d" width="6" height="14" fill="#555"/>' % (fx - 3, y - 14))
        return '\n'.join(out)

    # ---- titolo: MILANO a tubo rosso, "in dati" in corsivo ciano
    b.append(tubo_testo(40, 140, 'MILANO', 128, ROSSO, weight='700', extra='letter-spacing="6"'))
    b.append(tubo_testo(600, 150, 'in dati', 96, CIANO, font=SCRIPT, extra='transform="rotate(-6 700 120)"'))
    b.append(tubo_testo(1040, 52, '17 STORIE · APERTO TUTTA LA NOTTE', 17, GIALLO, 'end', weight='700', extra='letter-spacing="2"'))

    # ---- mappa: 88 quartieri come contorni luminosi
    P = Proj(box=(560, 240, 480, 470))
    g = ['<g filter="url(#neon)">']
    for i, gg in NIL.items():
        g.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.4" stroke-linejoin="round"/>' % (path(gg, P), ROSA))
    g.append('<path d="%s" fill="none" stroke="%s" stroke-width="4" stroke-linejoin="round"/>' % (path(COMUNE, P), CIANO))
    g.append('</g>')
    b += g
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="1.2" stroke-opacity=".85"/>' % path(COMUNE, P))
    # Comasina accesa in giallo, Rogoredo in verde
    for i, col in ((82, GIALLO), (33, VERDE)):
        b.append('<g filter="url(#neon)"><path d="%s" fill="%s" fill-opacity=".45" stroke="%s" stroke-width="2.5"/></g>' % (path(NIL[i], P), col, col))
    cx, cy = centro_nil(82, P)
    b.append(tubo_testo(cx - 22, cy - 18, '38%', 40, GIALLO, 'end', weight='700'))
    b.append(T(cx - 22, cy + 2, 'stranieri a Comasina', 14, '#FFF6B0', GROT, '700', 'end'))
    cx, cy = centro_nil(33, P)
    b.append(tubo_testo(1046, cy + 92, '+172%', 34, VERDE, 'end', weight='700'))
    b.append(T(1046, cy + 112, 'abitanti a Rogoredo', 14, '#C8FFD6', GROT, '700', 'end'))
    b.append(tubo_testo(800, 740, '88 QUARTIERI', 30, ROSA, 'middle', weight='700', extra='letter-spacing="5"'))

    # ---- insegna derby
    b.append(cornice(40, 220, 470, 170, GIALLO))
    b.append(tubo_testo(70, 335, '246', 112, GIALLO, weight='700'))
    b.append(tubo_testo(300, 280, 'DERBY', 40, '#FFFFFF', weight='700', extra='letter-spacing="3"'))
    b.append(tubo_testo(300, 324, 'INTER 91', 28, BLU, weight='700'))
    b.append(tubo_testo(300, 358, 'MILAN 84', 28, ROSSO, weight='700'))
    b.append(T(486, 358, 'pari 71', 15, '#ddd', GROT, '700', 'end'))
    # ---- insegna Scala
    b.append(cornice(40, 430, 470, 120, VERDE))
    b.append(tubo_testo(64, 520, '4.635', 80, VERDE, weight='700'))
    b.append(tubo_testo(300, 482, 'TITOLI', 28, '#fff', weight='700', extra='letter-spacing="2"'))
    b.append(tubo_testo(300, 518, 'ALLA SCALA', 28, '#fff', weight='700', extra='letter-spacing="2"'))
    b.append(T(486, 540, 'dal 1778', 15, '#C8FFD6', GROT, '700', 'end'))
    # ---- insegna cinema: mezza spenta, come le sale sparite
    b.append(cornice(40, 590, 470, 150, VIOLA))
    b.append(tubo_testo(64, 676, 'CINEMA', 76, VIOLA, weight='700', extra='letter-spacing="8"', spento={1, 4}))
    b.append(tubo_testo(64, 720, '171 SALE SPARITE', 30, ROSA, weight='700', extra='letter-spacing="2"', spento={9}))
    b.append(T(486, 720, '(123 nel 1960)', 15, '#E8D2FF', GROT, '700', 'end'))
    # filo che penzola dall'insegna del cinema
    b.append('<path d="M500,740 C506,770 470,780 480,812" fill="none" stroke="#444" stroke-width="2.5"/>')

    # ---- freccia a lampadine: "entra" verso la mappa
    fx, fy = 528, 400
    freccia = [(fx, fy - 26), (fx + 40, fy - 26), (fx + 40, fy - 46), (fx + 82, fy), (fx + 40, fy + 46), (fx + 40, fy + 26), (fx, fy + 26)]
    lf = Linea(freccia + [freccia[0]])
    b.append('<path d="%s" fill="#3A0A1E" stroke="%s" stroke-width="3"/>' % (poly_d(freccia, True), ROSA))
    for k in range(34):
        (x, y), _, _ = lf.at(k / 34)
        on = k % 5 != 3
        b.append('<circle cx="%.1f" cy="%.1f" r="3.4" fill="%s"%s/>' % (x, y, GIALLO if on else '#5A4A10', ' filter="url(#neon)"' if on else ''))
    b.append(T(fx + 34, fy + 6, 'ENTRA', 13, '#fff', GROT, '900', 'middle', 'letter-spacing="1"'))

    # ---- piccole insegne a destra in basso
    def piccola(x, y, num, lab, col):
        return tubo_testo(x, y, num, 46, col, weight='700') + T(x, y + 24, lab, 15, '#fff', GROT, '700')
    # ---- l'insegna lunga: la temperatura a Brera come un unico tubo che sale
    xs0, xs1, yb, ht = 60, 1020, 968, 106
    v = media_mobile([a['tmedia'] for a in TOK], 9)
    anni = [a['anno'] for a in TOK]
    lo, hi = min(v), max(v)
    pts = [(xs0 + (an - 1763) / (2025 - 1763) * (xs1 - xs0), yb - (t - lo) / (hi - lo) * ht) for an, t in zip(anni, v)]
    b.append('<rect x="36" y="790" width="1008" height="196" rx="18" fill="#000" opacity=".55"/>')
    b.append('<g filter="url(#neon)"><path d="%s" fill="none" stroke="url(#tubo)" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/></g>' % poly_d(pts))
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="1.6" stroke-linejoin="round"/>' % poly_d(pts))
    b.append(tubo_testo(60, 830, '1763', 34, CIANO, weight='700'))
    b.append(tubo_testo(1020, 830, '2026', 34, ROSSO, 'end', weight='700'))
    b.append(T(178, 826, 'Temperatura a Brera, media su 9 anni', 17, '#fff', GROT, '700'))
    b.append(T(860, 826, 'il più caldo: il 2026 (finora)', 17, '#FFD0C0', GROT, '700', 'end'))
    # marciapiede bagnato con il riflesso dell'insegna
    b.append('<rect x="0" y="1000" width="1080" height="80" fill="url(#bagnato)"/>')
    rif = [(x, 2 * 1000 - y + 40) for x, y in pts]
    b.append('<path d="%s" fill="none" stroke="url(#tubo)" stroke-width="6" opacity=".35" filter="url(#riflesso)"/>' % poly_d(rif))
    b.append(T(1040, 1062, 'Milano in dati · piazza di notte', 14, '#8A7FA0', GROT, '600', 'end'))
    salva('bozza_9_insegne.svg', svg('\n'.join(b), MURO, 'Milano in dati - bozza 9, insegne al neon'))

# =================================================================== BOZZA 10
def bozza10():
    """La prima pagina rosa: un quotidiano sportivo inventato, testata "Milano in dati" """
    CARTA = '#F7BFD0'; CARTA2 = '#F2A6BE'; INK = '#111111'; ROSSO = '#D9003B'; BLU = '#1236B8'
    b = []
    b.append('<defs>')
    # mezzetinte: punti di stampa sempre piu' grandi
    for k, r in enumerate((0.5, 1.0, 1.5, 2.0, 2.6, 3.2)):
        b.append('<pattern id="mt%d" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                 '<circle cx="3.5" cy="3.5" r="%.1f" fill="%s"/></pattern>' % (k, r, INK))
    b.append('<pattern id="tratt" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             '<line x1="0" y1="0" x2="0" y2="5" stroke="#777" stroke-width="1.2"/></pattern>')
    b.append('<filter id="grana"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/>'
             '<feColorMatrix values="0 0 0 0 .5  0 0 0 0 .2  0 0 0 0 .3  0 0 0 .10 0"/></filter>')
    b.append('</defs>')
    b.append('<rect width="1080" height="1080" fill="%s"/>' % CARTA)
    b.append('<rect width="1080" height="1080" filter="url(#grana)"/>')
    # riga di servizio
    b.append(T(30, 30, 'VENERDÌ 30 OTTOBRE 2026 · ANNO I · NUMERO 17', 14, INK, GROT, '700', extra='letter-spacing="1"'))
    b.append(T(1050, 30, 'GRATIS · I DATI SONO APERTI', 14, INK, GROT, '700', 'end', 'letter-spacing="1"'))
    b.append('<rect x="30" y="40" width="1020" height="2" fill="%s"/>' % INK)
    # testata con orecchie
    b.append('<text x="540" y="150" font-family="%s" font-size="112" font-weight="900" font-style="italic" fill="%s" text-anchor="middle" letter-spacing="-4" textLength="640" lengthAdjust="spacingAndGlyphs">Milano in dati</text>' % (GROT, INK))
    b.append(T(540, 178, 'IL QUOTIDIANO DEI NUMERI DELLA CITTÀ · 17 STORIE · 88 QUARTIERI', 14, INK, GROT, '800', 'middle', 'letter-spacing="2"'))
    for x0, tit, num, sub in ((30, 'IL TEMPO', '1763', 'Brera misura da allora'), (906, 'IN EDICOLA', '4.635', 'titoli alla Scala')):
        b.append('<rect x="%d" y="56" width="144" height="110" fill="none" stroke="%s" stroke-width="2"/>' % (x0, INK))
        b.append(T(x0 + 72, 78, tit, 13, INK, GROT, '900', 'middle', 'letter-spacing="2"'))
        b.append(T(x0 + 72, 124, num, 42, ROSSO, IMPACT, '400', 'middle'))
        b.append(T(x0 + 72, 150, sub, 13, INK, GROT, '600', 'middle'))
    b.append('<rect x="30" y="190" width="1020" height="6" fill="%s"/><rect x="30" y="199" width="1020" height="1.5" fill="%s"/>' % (INK, INK))
    # occhiello e titolo grande
    b.append('<rect x="30" y="214" width="290" height="30" fill="%s"/>' % ROSSO)
    b.append(T(42, 236, 'STRACITTADINA 1909-2026', 18, '#fff', GROT, '900', extra='letter-spacing="1"'))
    b.append(T(334, 236, 'L’ultimo, l’8 marzo, al Milan: 1-0', 18, INK, GROT, '700', extra='font-style="italic"'))
    b.append('<text x="30" y="346" font-family="%s" font-size="112" fill="%s" textLength="560" lengthAdjust="spacingAndGlyphs">246 DERBY,</text>' % (IMPACT, INK))
    # tabellino a destra del titolo: Inter, pari, Milan
    for k, (num, lab, col) in enumerate((('91', 'INTER', BLU), ('71', 'PARI', INK), ('84', 'MILAN', ROSSO))):
        x = 616 + k * 146
        b.append('<rect x="%d" y="256" width="136" height="92" fill="%s"/>' % (x, col))
        b.append(T(x + 68, 320, num, 62, '#fff', IMPACT, '400', 'middle'))
        b.append(T(x + 68, 342, lab, 14, '#fff', GROT, '900', 'middle', 'letter-spacing="2"'))
    b.append('<text x="30" y="446" font-family="%s" font-size="112" fill="%s" textLength="1020" lengthAdjust="spacingAndGlyphs">L’INTER AVANTI DI <tspan fill="%s">7</tspan></text>' % (IMPACT, INK, ROSSO))
    b.append(T(30, 474, '91 vittorie nerazzurre, 84 rossonere, 71 pareggi. Il saldo partita per partita, dal 10 gennaio 1909.', 19, INK, GROT, '600'))
    b.append('<rect x="30" y="490" width="1020" height="1.5" fill="%s"/>' % INK)

    # "foto" 1: il saldo dei derby
    X0, Y0, W, H = 30, 506, 500, 250
    b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (X0, Y0, W, H, CARTA2))
    ds = sorted(DERBY, key=lambda d: d['date'])
    sbs = [0] + [d['sb'] for d in ds]
    mx = max(abs(s) for s in sbs)
    zy = Y0 + 30 + (H - 60) * mx / (2 * mx)
    xs = [X0 + 14 + (W - 28) * k / (len(sbs) - 1) for k in range(len(sbs))]
    ys = [zy - s / mx * (H - 60) / 2 for s in sbs]
    area = [(xs[0], zy)] + list(zip(xs, ys)) + [(xs[-1], zy)]
    b.append('<clipPath id="sopra"><rect x="%d" y="%d" width="%d" height="%.1f"/></clipPath>' % (X0, Y0, W, zy - Y0))
    b.append('<clipPath id="sotto"><rect x="%d" y="%.1f" width="%d" height="%.1f"/></clipPath>' % (X0, zy, W, Y0 + H - zy))
    b.append('<path d="%s" fill="%s" clip-path="url(#sopra)"/>' % (poly_d(area, True), BLU))
    b.append('<path d="%s" fill="%s" clip-path="url(#sotto)"/>' % (poly_d(area, True), ROSSO))
    b.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5"/>' % (X0 + 10, zy, X0 + W - 10, zy, INK))
    # anni sotto
    for an in (1909, 1950, 2000, 2026):
        k = next(i for i, d in enumerate(ds) if int(d['date'][:4]) >= an) if an < 2026 else len(ds) - 1
        b.append(T(xs[k + 1], Y0 + H - 8, str(an), 13, INK, GROT, '800', 'middle'))
    b.append(T(X0 + 14, Y0 + 24, 'INTER AVANTI', 14, BLU, GROT, '900'))
    b.append(T(X0 + 14, Y0 + H - 26, 'MILAN AVANTI', 14, ROSSO, GROT, '900'))
    b.append(T(xs[-1] - 3, zy - 10, '+7', 24, '#fff', IMPACT, '400', 'end'))
    b.append(T(X0, Y0 + H + 20, 'LA FOTO · Il saldo dei derby: sopra la riga comanda l’Inter, sotto il Milan.', 13, INK, GROT, '600', extra='font-style="italic"'))

    # "foto" 2: la mappa in mezzetinta, stranieri 2023
    MX, MY, MW, MH = 550, 506, 500, 300
    b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" fill-opacity=".35"/>' % (MX, MY, MW, MH))
    P = Proj(box=(MX + 6, MY + 8, 300, MH - 16))
    classi = [0, 10, 15, 20, 25, 30]
    for i, gg in NIL.items():
        n = NILINFO[i]; v = n['v']['str'][4]
        fill = 'url(#tratt)' if (v is None or not n['ok']) else 'url(#mt%d)' % max(k for k, t in enumerate(classi) if v >= t)
        b.append('<path d="%s" fill="%s" stroke="%s" stroke-width=".8"/>' % (path(gg, P), fill, INK))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"/>' % (path(COMUNE, P), INK))
    cx, cy = centro_nil(82, P)
    b.append('<circle cx="%.1f" cy="%.1f" r="12" fill="none" stroke="%s" stroke-width="3"/>' % (cx, cy, ROSSO))
    b.append('<path d="M%.1f,%.1f L%d,%d" stroke="%s" stroke-width="2"/>' % (cx + 12, cy - 4, MX + 330, MY + 40, ROSSO))
    b.append(T(MX + 316, MY + 50, 'COMASINA', 30, INK, IMPACT, '400'))
    b.append(T(MX + 316, MY + 108, '38%', 64, ROSSO, IMPACT, '400'))
    b.append(T(MX + 316, MY + 132, 'di stranieri', 16, INK, GROT, '700'))
    b.append(T(MX + 316, MY + 176, 'In città il 19,6%', 17, INK, GROT, '700'))
    b.append(T(MX + 316, MY + 196, '(1,9% nel 1991)', 15, INK, GROT, '500'))
    for k in range(6):
        b.append('<rect x="%d" y="%d" width="26" height="18" fill="url(#mt%d)" stroke="%s" stroke-width=".8"/>' % (MX + 316 + k * 29, MY + 222, k, INK))
    b.append(T(MX + 316, MY + 256, 'più punti, più stranieri', 13, INK, GROT, '600', extra='font-style="italic"'))
    b.append(T(MX, MY + MH + 20, 'LA FOTO · 88 quartieri in mezzatinta (2023).', 13, INK, GROT, '600', extra='font-style="italic"'))

    # secondo articolo: Brera
    b.append('<rect x="30" y="788" width="500" height="1.5" fill="%s"/>' % INK)
    b.append(T(30, 836, 'BRERA, CALDO DA RECORD', 44, INK, IMPACT, '400', extra='textLength="500" lengthAdjust="spacingAndGlyphs"'))
    b.append(T(30, 862, 'Il 2026 è il più caldo dal 1763 (finora, sullo stesso periodo)', 16, INK, GROT, '700'))
    vals = [a['tmedia'] for a in TOK]; lo, hi = min(vals), max(vals)
    n = len(TEMP); w = 500 / n
    for k, a in enumerate(TEMP):
        if a['ok']:
            t = (a['tmedia'] - lo) / (hi - lo)
            col = BLU if t < .45 else (INK if t < .7 else ROSSO)
            h = 12 + 50 * t
            b.append('<rect x="%.1f" y="%.1f" width="%.2f" height="%.1f" fill="%s"/>' % (30 + k * w, 940 - h, w + .2, h, col))
        else:
            b.append('<rect x="%.1f" y="876" width="%.2f" height="64" fill="%s"/>' % (30 + k * w, w + 2, ROSSO))
    b.append(T(30, 958, '1763', 13, INK, GROT, '800'))
    b.append(T(530, 958, '2026', 13, ROSSO, GROT, '800', 'end'))

    # brevi
    BX = 550; BY = 834
    b.append('<rect x="%d" y="%d" width="500" height="30" fill="%s"/>' % (BX, BY - 4, INK))
    b.append(T(BX + 12, BY + 18, 'IN BREVE', 18, '#fff', GROT, '900', extra='letter-spacing="3"'))
    brevi = [('171', 'CINEMA', 'sale sparite'), ('−16%', 'AREA C', 'ingressi dal 2019'), ('167', 'ELEZIONI', 'dal 1946'), ('84', 'VIOLENZA', 'fatti 1919-2019')]
    for k, (num, tit, sub) in enumerate(brevi):
        x = BX + k * 125
        if k:
            b.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (x, BY + 36, x, BY + 124, INK))
        b.append(T(x + 10, BY + 56, tit, 14, ROSSO, GROT, '900', extra='letter-spacing="1"'))
        b.append(T(x + 10, BY + 98, num, 40, INK, IMPACT, '400'))
        b.append(T(x + 10, BY + 120, sub, 13, INK, GROT, '600'))
    # piede: codice a barre inventato
    b.append('<rect x="30" y="976" width="1020" height="1.5" fill="%s"/>' % INK)
    random.seed(1909)
    x = 880
    while x < 1046:
        wv = random.choice([1, 1, 2, 3])
        b.append('<rect x="%d" y="990" width="%d" height="60" fill="%s"/>' % (x, wv, INK))
        x += wv + random.choice([1, 2, 2, 3])
    b.append(T(963, 1068, '1 763 2026 1909', 13, INK, GROT, '700', 'middle', 'letter-spacing="2"'))
    b.append(T(30, 1012, 'DENTRO', 18, ROSSO, GROT, '900', extra='letter-spacing="2"'))
    b.append(T(30, 1040, 'Temperature · Neve e nebbia · Aria · Acqua · Bici · Area C · Fermate · Vie · Censimenti', 15, INK, GROT, '600'))
    b.append(T(30, 1062, 'Scala · Cinema · Film e libri · Beni culturali · Elezioni · Violenza politica · Derby · 15 minuti', 15, INK, GROT, '600'))
    salva('bozza_10_prima_pagina.svg', svg('\n'.join(b), CARTA, 'Milano in dati - bozza 10, prima pagina rosa'))

# =================================================================== BOZZA 11
def bozza11():
    """Memphis: colori che litigano, ghirigori, terrazzo; i dati come oggetti"""
    random.seed(1981)
    ROSA = '#FF4FA3'; CIANO = '#00C2D1'; GIALLO = '#FFE100'; BLU = '#2B2BD9'; ARANCIO = '#FF6B1A'; NERO = '#111'; VERDE = '#3DDC84'
    b = []
    defs = ['<defs>']
    # ghirigori neri su bianco (pattern "batterio")
    sq = []
    for _ in range(9):
        x, y = random.uniform(0, 90), random.uniform(0, 90); a = random.uniform(0, 360)
        sq.append('<path d="M0,0 q6,-8 12,0 t12,0 t12,0" fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round" transform="translate(%.0f %.0f) rotate(%.0f)"/>' % (NERO, x, y, a))
    defs.append('<pattern id="ghiri" width="100" height="100" patternUnits="userSpaceOnUse"><rect width="100" height="100" fill="#fff"/>%s</pattern>' % ''.join(sq))
    # terrazzo: scaglie colorate su bianco
    tz = []
    for _ in range(70):
        x, y = random.uniform(0, 140), random.uniform(0, 140); r = random.uniform(1.5, 6)
        k = random.randint(3, 6)
        pts = [(x + r * random.uniform(.6, 1.2) * math.cos(2 * math.pi * j / k), y + r * random.uniform(.6, 1.2) * math.sin(2 * math.pi * j / k)) for j in range(k)]
        tz.append('<path d="%s" fill="%s"/>' % (poly_d(pts, True), random.choice([ROSA, CIANO, GIALLO, BLU, ARANCIO, NERO, VERDE, '#BDBDBD'])))
    defs.append('<pattern id="terrazzo" width="140" height="140" patternUnits="userSpaceOnUse"><rect width="140" height="140" fill="#F7F7F7"/>%s</pattern>' % ''.join(tz))
    defs.append('<pattern id="puntini" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="8" cy="8" r="3" fill="%s"/></pattern>' % NERO)
    defs.append('<pattern id="righe" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="14" height="7" fill="%s"/><rect y="7" width="14" height="7" fill="#fff"/></pattern>' % NERO)
    defs.append('<pattern id="griglia" width="22" height="22" patternUnits="userSpaceOnUse"><rect width="22" height="22" fill="%s"/><path d="M0,0H22M0,0V22" stroke="%s" stroke-width="2"/></pattern>' % (GIALLO, NERO))
    defs.append('</defs>')
    b += defs
    b.append('<rect width="1080" height="1080" fill="%s"/>' % CIANO)
    # blocchi di fondo che litigano
    b.append('<rect x="0" y="0" width="1080" height="250" fill="url(#ghiri)"/>')
    b.append('<path d="M0,250 L1080,250 L1080,330 L0,420 Z" fill="%s"/>' % ROSA)
    b.append('<rect x="0" y="880" width="1080" height="200" fill="url(#griglia)"/>')
    b.append('<circle cx="700" cy="610" r="330" fill="%s"/>' % GIALLO)
    b.append('<path d="M960,340 L1080,340 L1080,560 Z" fill="url(#puntini)"/>')
    b.append('<path d="M250,420 L350,392 L318,500 Z" fill="%s" stroke="%s" stroke-width="4"/>' % (BLU, NERO))

    # titolo: lettere grosse con ombra sfalsata
    def ombra(x, y, s, size, fill, sh, dx=7, extra=''):
        return (T(x + dx, y + dx, s, size, sh, GROT, '900', extra=extra) + T(x, y, s, size, fill, GROT, '900', extra=extra + ' stroke="%s" stroke-width="3" paint-order="stroke"' % NERO))
    b.append('<rect x="30" y="34" width="560" height="190" fill="%s" stroke="%s" stroke-width="5"/>' % (GIALLO, NERO))
    b.append('<rect x="44" y="48" width="560" height="190" fill="none" stroke="%s" stroke-width="5"/>' % NERO)
    b.append(ombra(52, 130, 'MILANO', 104, ROSA, NERO, extra='letter-spacing="-3"'))
    b.append(ombra(56, 206, 'in dati', 70, BLU, NERO, extra='font-style="italic"'))
    b.append('<circle cx="500" cy="168" r="44" fill="%s" stroke="%s" stroke-width="5"/>' % (ARANCIO, NERO))
    b.append(T(500, 166, '17', 38, NERO, GROT, '900', 'middle'))
    b.append(T(500, 188, 'storie', 14, NERO, GROT, '900', 'middle'))

    # il ghirigoro e' la temperatura di Brera (media su 11 anni)
    v = media_mobile([a['tmedia'] for a in TOK], 11)
    anni = [a['anno'] for a in TOK]; lo, hi = min(v), max(v)
    pts = [(640 + (an - 1763) / (2025 - 1763) * 410, 216 - (t - lo) / (hi - lo) * 150) for an, t in zip(anni, v)]
    pts = [p for k, p in enumerate(pts) if k % 3 == 0] + [pts[-1]]
    b.append('<rect x="622" y="34" width="430" height="212" fill="#fff" stroke="%s" stroke-width="5"/>' % NERO)
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" transform="translate(4 4)"/>' % (poly_d(catmull(pts, 6)), ROSA))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>' % (poly_d(catmull(pts, 6)), NERO))
    b.append(T(640, 64, 'Il ghirigoro? È il caldo a Brera', 17, NERO, GROT, '900'))
    b.append(T(640, 236, '1763', 14, NERO, GROT, '900'))
    b.append(T(1036, 236, '2026: il più caldo (finora)', 14, ROSA, GROT, '900', 'end', 'stroke="%s" stroke-width=".6"' % NERO))

    # la mappa e' una lastra di terrazzo, con lo spessore
    P = Proj(box=(530, 370, 420, 450))
    b.append('<path d="%s" fill="%s" transform="translate(16 18)"/>' % (path(COMUNE, P), NERO))
    b.append('<path d="%s" fill="url(#terrazzo)" stroke="%s" stroke-width="5" stroke-linejoin="round"/>' % (path(COMUNE, P), NERO))
    for i, gg in NIL.items():
        b.append('<path d="%s" fill="none" stroke="%s" stroke-width=".8" stroke-opacity=".5"/>' % (path(gg, P), NERO))
    accesi = [(82, ROSA, '38%', 'stranieri a Comasina', (470, 296)), (33, BLU, '+172%', 'abitanti a Rogoredo', (856, 744)),
              (64, ARANCIO, '50,6', 'anni, età media a Trenno', (392, 560)), (43, VERDE, '10/10', 'servizi a 15 minuti a Tibaldi', (404, 776))]
    for i, col, num, lab, _ in accesi:
        b.append('<path d="%s" fill="%s" stroke="%s" stroke-width="3"/>' % (path(NIL[i], P), col, NERO))
    for i, col, num, lab, (tx, ty) in accesi:
        cx, cy = centro_nil(i, P)
        w = max(len(num) * 26, len(lab) * 8.2) + 24
        b.append('<path d="M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="3"/>' % (cx, cy, tx + w / 2, ty, NERO))
        b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="70" fill="%s" stroke="%s" stroke-width="4" transform="translate(5 5)"/>' % (tx, ty - 10, w, NERO, NERO))
        b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="70" fill="#fff" stroke="%s" stroke-width="4"/>' % (tx, ty - 10, w, NERO))
        b.append(T(tx + 12, ty + 30, num, 36, col, GROT, '900', extra='stroke="%s" stroke-width="1.5" paint-order="stroke"' % NERO))
        b.append(T(tx + 12, ty + 52, lab, 14, NERO, GROT, '800'))
    b.append(T(1050, 868, '88 quartieri in terrazzo', 20, NERO, GROT, '900', 'end'))

    # totem del derby: altezza = vittorie (e pareggi)
    G0 = 860; S = 2.9
    def totem(x, n, col, motivo, nome):
        h = n * S; out = []
        y = G0
        out.append('<rect x="%d" y="%.1f" width="84" height="30" fill="%s" stroke="%s" stroke-width="4"/>' % (x - 42, y - 30, NERO, NERO))
        y -= 30
        pezzi = [('cil', 48), ('cubo', 40), ('palla', 34), ('cil', 52), ('cono', 30), ('cubo', 36), ('palla', 30)]
        k = 0
        while y > G0 - h + 20:
            tipo, hh = pezzi[k % len(pezzi)]; hh = min(hh, y - (G0 - h) - 18)
            if hh < 14:
                break
            f = col if k % 2 == 0 else motivo
            if tipo == 'cil':
                out.append('<rect x="%d" y="%.1f" width="52" height="%.1f" fill="%s" stroke="%s" stroke-width="4"/>' % (x - 26, y - hh, hh, f, NERO))
            elif tipo == 'cubo':
                out.append('<rect x="%d" y="%.1f" width="72" height="%.1f" fill="%s" stroke="%s" stroke-width="4"/>' % (x - 36, y - hh, hh, f, NERO))
            elif tipo == 'palla':
                out.append('<ellipse cx="%d" cy="%.1f" rx="30" ry="%.1f" fill="%s" stroke="%s" stroke-width="4"/>' % (x, y - hh / 2, hh / 2, f, NERO))
            else:
                out.append('<path d="M%d,%.1f L%d,%.1f L%d,%.1f Z" fill="%s" stroke="%s" stroke-width="4"/>' % (x - 34, y, x, y - hh, x + 34, y, f, NERO))
            y -= hh; k += 1
        out.append('<circle cx="%d" cy="%.1f" r="14" fill="%s" stroke="%s" stroke-width="4"/>' % (x, G0 - h + 4, GIALLO, NERO))
        out.append(T(x, G0 - h - 20, str(n), 34, NERO, GROT, '900', 'middle', 'stroke="#fff" stroke-width="5" paint-order="stroke"'))
        out.append(T(x, G0 - 9, nome, 14, '#fff', GROT, '900', 'middle'))
        return '\n'.join(out)
    b.append(totem(90, 91, BLU, 'url(#puntini)', 'INTER'))
    b.append(totem(200, 71, '#fff', 'url(#righe)', 'PARI'))
    b.append(totem(310, 84, '#E10600', 'url(#ghiri)', 'MILAN'))
    b.append('<rect x="30" y="%d" width="340" height="8" fill="%s"/>' % (G0, NERO))
    b.append('<rect x="30" y="440" width="230" height="100" fill="#fff" stroke="%s" stroke-width="4"/>' % NERO)
    b.append(T(44, 478, '246 derby', 30, NERO, GROT, '900'))
    b.append(T(44, 504, 'tre totem alti quanto', 15, NERO, GROT, '800'))
    b.append(T(44, 524, 'vittorie e pareggi', 15, NERO, GROT, '800'))

    # oggetti in basso: Scala a ventaglio, cinema a triangoli, Area C
    b.append('<rect x="20" y="904" width="1040" height="156" fill="#fff" stroke="%s" stroke-width="5"/>' % NERO)
    # ventaglio Scala
    cx, cy = 120, 1040
    for k in range(9):
        b.append(settore((cx, cy), 0, 96, 180 + k * 20, 200 + k * 20, [ROSA, GIALLO, BLU, ARANCIO, CIANO][k % 5], 'stroke="%s" stroke-width="3"' % NERO))
    b.append(T(232, 970, '4.635', 44, NERO, GROT, '900'))
    b.append(T(232, 996, 'titoli alla Scala', 16, NERO, GROT, '800'))
    b.append(T(232, 1016, 'dal 1778', 16, NERO, GROT, '800'))
    # cinema: 123 triangoli nel 1960, ne restano accesi 28 oggi
    x0, y0 = 420, 930
    for k in range(123):
        col_, row = k % 25, k // 25
        x, y = x0 + col_ * 13, y0 + row * 22
        f = ARANCIO if k < 28 else 'none'
        b.append('<path d="M%d,%d l6,-14 l6,14 Z" fill="%s" stroke="%s" stroke-width="1.6"/>' % (x, y + 14, f, NERO))
    b.append(T(420, 1052, '123 cinema nel 1960 · oggi 28 aperti', 15, NERO, GROT, '900'))
    # Area C
    b.append('<circle cx="860" cy="982" r="58" fill="%s" stroke="%s" stroke-width="5"/>' % (ROSA, NERO))
    b.append('<path d="M812,982 a48,48 0 0 1 96,0" fill="none" stroke="%s" stroke-width="5" stroke-dasharray="10 8"/>' % NERO)
    b.append(T(860, 996, '−16%', 32, NERO, GROT, '900', 'middle'))
    b.append(T(1044, 950, 'Area C', 20, NERO, GROT, '900', 'end'))
    b.append(T(1044, 974, 'ingressi', 15, NERO, GROT, '800', 'end'))
    b.append(T(1044, 994, 'dal 2019', 15, NERO, GROT, '800', 'end'))
    salva('bozza_11_memphis.svg', svg('\n'.join(b), CIANO, 'Milano in dati - bozza 11, Memphis'))

# =================================================================== BOZZA 12
def bozza12():
    """Il tram Ventotto attraversa la piazza: ogni finestrino e' una storia"""
    random.seed(1928)
    CIELO = '#1F3BD6'; CIELO2 = '#3C6CFF'; ARANCIO = '#FF8A00'; ARANCIO2 = '#D85F00'; NERO = '#121212'; VETRO = '#FFF1A8'
    b = []
    b.append('<defs><linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
             '<linearGradient id="rotaia" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#F2F2F2"/><stop offset="1" stop-color="#7A7A7A"/></linearGradient></defs>' % (CIELO, CIELO2))
    b.append('<rect width="1080" height="880" fill="url(#cielo)"/>')
    # titolo
    b.append(T(36, 96, 'Milano in dati', 82, '#fff', GROT, '900', extra='letter-spacing="-2"'))
    b.append(T(40, 140, 'Sali sul Ventotto: ogni finestrino è una storia.', 24, '#FFE27A', GROT, '800'))
    b.append(T(40, 170, 'Il tram ha 98 anni (1928). I dati della città partono dal 1763.', 18, '#fff', GROT, '500'))

    # cartello del percorso: la mappa vera, la "linea 17" passa per i quartieri delle storie
    PX, PY, PW, PH = 560, 196, 490, 330
    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="12" fill="#fff" stroke="%s" stroke-width="5"/>' % (PX, PY, PW, PH, NERO))
    b.append('<rect x="%d" y="%d" width="%d" height="44" rx="10" fill="%s"/>' % (PX, PY, PW, NERO))
    b.append('<rect x="%d" y="%d" width="56" height="34" rx="4" fill="%s"/>' % (PX + 8, PY + 5, ARANCIO))
    b.append(T(PX + 36, PY + 31, '17', 26, NERO, GROT, '900', 'middle'))
    b.append(T(PX + 76, PY + 30, 'PERCORSO · TUTTE LE STORIE', 18, '#fff', GROT, '900', extra='letter-spacing="1"'))
    P = Proj(box=(PX + 12, PY + 52, 270, PH - 62))
    for i, gg in NIL.items():
        b.append('<path d="%s" fill="#EDEDED" stroke="#BDBDBD" stroke-width=".8"/>' % path(gg, P))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8"/>' % (path(COMUNE, P), NERO))
    fermate = [(82, 'Comasina', '38%'), (64, 'Trenno', '50,6'), (57, 'San Siro', '246'), (2, 'Brera', '1763'), (1, 'Duomo', '4.635'), (43, 'Tibaldi', '10/10'), (33, 'Rogoredo', '+172%')]
    pts = [centro_nil(i, P) for i, _, _ in fermate]
    curva = catmull(pts, 14)
    b.append('<path d="%s" fill="none" stroke="#fff" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>' % poly_d(curva))
    b.append('<path d="%s" fill="none" stroke="%s" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>' % (poly_d(curva), ARANCIO))
    for k, ((x, y), (i, nome, num)) in enumerate(zip(pts, fermate)):
        b.append('<circle cx="%.1f" cy="%.1f" r="7" fill="#fff" stroke="%s" stroke-width="3"/>' % (x, y, NERO))
        b.append(T(x, y + 4, str(k + 1), 9, NERO, GROT, '900', 'middle'))
    # elenco fermate a destra della mappa
    for k, (i, nome, num) in enumerate(fermate):
        y = PY + 76 + k * 36
        b.append('<circle cx="%d" cy="%d" r="11" fill="%s" stroke="%s" stroke-width="2.5"/>' % (PX + 300, y - 5, ARANCIO, NERO))
        b.append(T(PX + 300, y, str(k + 1), 13, NERO, GROT, '900', 'middle'))
        b.append(T(PX + 318, y, nome, 16, NERO, GROT, '800'))
        b.append(T(PX + PW - 14, y, num, 16, ARANCIO2, GROT, '900', 'end'))

    # fili aerei e pali
    b.append('<line x1="0" y1="232" x2="540" y2="214" stroke="%s" stroke-width="2.5"/>' % NERO)
    b.append('<line x1="0" y1="242" x2="540" y2="226" stroke="%s" stroke-width="1.2"/>' % NERO)
    b.append('<rect x="18" y="200" width="12" height="680" fill="#0E1A66"/>')
    b.append('<path d="M24,226 L250,226" stroke="#0E1A66" stroke-width="4"/>')

    # palina della fermata (dietro il tram)
    b.append('<rect x="138" y="300" width="12" height="560" fill="#9AA3B5" stroke="%s" stroke-width="2"/>' % NERO)
    b.append('<rect x="52" y="262" width="184" height="236" rx="8" fill="#fff" stroke="%s" stroke-width="4"/>' % NERO)
    b.append('<rect x="52" y="262" width="184" height="40" rx="8" fill="%s" stroke="%s" stroke-width="4"/>' % (ARANCIO, NERO))
    b.append(T(144, 290, 'FERMATA', 22, NERO, GROT, '900', 'middle', 'letter-spacing="3"'))
    b.append(T(144, 340, 'Duomo', 30, NERO, GROT, '900', 'middle'))
    b.append('<rect x="118" y="352" width="52" height="30" rx="4" fill="%s"/>' % NERO)
    b.append(T(144, 375, '17', 22, '#FFC400', GROT, '900', 'middle'))
    b.append('<line x1="64" y1="396" x2="224" y2="396" stroke="%s" stroke-width="1.5"/>' % NERO)
    b.append(T(144, 418, 'IN ARRIVO', 14, ARANCIO2, GROT, '900', 'middle', 'letter-spacing="2"'))
    b.append(T(144, 444, 'il 2026, l’anno', 16, NERO, GROT, '800', 'middle'))
    b.append(T(144, 464, 'più caldo a Brera', 16, NERO, GROT, '800', 'middle'))
    b.append(T(144, 484, '(finora)', 14, NERO, GROT, '600', 'middle'))

    # ---- il tram, di fianco
    TX, TY, TW, TH = 40, 560, 1000, 250
    roof = TY - 26
    # pantografo / asta verso il filo
    b.append('<path d="M%d,%d L%d,%d" stroke="%s" stroke-width="5"/>' % (TX + 300, roof + 2, 250, 226, NERO))
    b.append('<circle cx="250" cy="226" r="6" fill="%s"/>' % NERO)
    b.append('<rect x="%d" y="%d" width="%d" height="32" rx="14" fill="#3A3A3A"/>' % (TX + 20, roof, TW - 40))
    # indicatore di linea e destinazione
    b.append('<rect x="%d" y="%d" width="340" height="44" rx="4" fill="%s" stroke="#555" stroke-width="3"/>' % (TX + TW - 400, roof - 30, NERO))
    b.append(T(TX + TW - 230, roof + 1, 'MILANO IN DATI', 26, '#FFC400', GROT, '900', 'middle', 'letter-spacing="3"'))
    b.append('<rect x="%d" y="%d" width="64" height="44" rx="4" fill="#fff" stroke="%s" stroke-width="3"/>' % (TX + TW - 480, roof - 30, NERO))
    b.append(T(TX + TW - 448, roof + 4, '17', 32, NERO, GROT, '900', 'middle'))
    # cassa
    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="22" fill="%s" stroke="%s" stroke-width="4"/>' % (TX, TY, TW, TH, ARANCIO, NERO))
    b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (TX + 2, TY + 168, TW - 4, TH - 190, ARANCIO2))
    b.append('<rect x="%d" y="%d" width="%d" height="6" fill="%s"/>' % (TX, TY + 164, TW, NERO))
    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="0" fill="%s"/>' % (TX + 2, TY + TH - 18, TW - 4, 12, NERO))
    # finestrini = storie
    FIN = [('1763', 'temperature'), ('4.635', 'titoli Scala'), ('246', 'derby'), ('171', 'cinema spariti'), (None, None),
           ('167', 'elezioni'), ('84', 'violenza pol.'), ('19,6%', 'stranieri'), ('−16%', 'Area C'), ('88%', 'bici prima')]
    fx = TX + 30; fw = 84; gap = 10
    for k, (num, lab) in enumerate(FIN):
        x = fx + k * (fw + gap)
        if num is None:     # porta centrale a libro
            b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="3"/>' % (x, TY + 18, fw, TH - 36, ARANCIO2, NERO))
            for j in range(2):
                b.append('<rect x="%d" y="%d" width="%d" height="96" rx="4" fill="%s" stroke="%s" stroke-width="2"/>' % (x + 8 + j * 36, TY + 30, 32, VETRO, NERO))
            b.append(T(x + fw / 2, TY + 158, 'SALITE', 13, '#fff', GROT, '900', 'middle'))
            continue
        b.append('<rect x="%d" y="%d" width="%d" height="110" rx="8" fill="%s" stroke="%s" stroke-width="3.5"/>' % (x, TY + 26, fw, VETRO, NERO))
        b.append('<rect x="%d" y="%d" width="%d" height="28" rx="6" fill="#FFF8D8" stroke="%s" stroke-width="2"/>' % (x + 6, TY + 32, fw - 12, NERO))
        fs = 30 if len(num) <= 4 else 24
        b.append(T(x + fw / 2, TY + 104, num, fs, NERO, GROT, '900', 'middle', 'letter-spacing="-1"'))
        b.append(T(x + fw / 2, TY + 158, lab, 13, NERO, GROT, '800', 'middle'))
    # numero di matricola sulla fiancata: l'anno del primo dato
    b.append(T(TX + TW - 60, TY + 210, '1763', 26, '#FFE27A', GROT, '900', 'end', 'letter-spacing="2"'))
    b.append(T(TX + 60, TY + 210, 'dati aperti dal 1763 al 2026', 15, '#FFE27A', GROT, '700'))
    # fanali e paraurti
    b.append('<circle cx="%d" cy="%d" r="10" fill="#FFF6B0" stroke="%s" stroke-width="3"/>' % (TX + TW - 14, TY + 192, NERO))
    b.append('<circle cx="%d" cy="%d" r="10" fill="#FF3B3B" stroke="%s" stroke-width="3"/>' % (TX + 14, TY + 192, NERO))
    # carrelli e ruote
    for cx in (TX + 200, TX + TW - 200):
        b.append('<rect x="%d" y="%d" width="200" height="26" rx="6" fill="#2A2A2A"/>' % (cx - 100, TY + TH - 10))
        for dx in (-60, 60):
            b.append('<circle cx="%d" cy="%d" r="24" fill="%s"/><circle cx="%d" cy="%d" r="9" fill="#777"/>' % (cx + dx, TY + TH + 16, NERO, cx + dx, TY + TH + 16))

    # ---- selciato a coda di pavone e binari
    b.append('<rect x="0" y="850" width="1080" height="230" fill="#3E3346"/>')
    pietre = ['#8A6A7A', '#A0707E', '#6E5868', '#B98A96', '#5C4A58', '#C0805E', '#9A5A62']
    for cxp in range(-60, 1200, 170):
        for r in range(14, 250, 16):
            n = max(3, int(math.pi * r / 15))
            for j in range(n):
                a1 = math.pi + math.pi * j / n; a2 = math.pi + math.pi * (j + .82) / n
                x1, y1 = cxp + r * math.cos(a1), 1080 + r * math.sin(a1)
                if y1 < 852:
                    continue
                b.append('<path d="M%.1f,%.1f A%d,%d 0 0 1 %.1f,%.1f" stroke="%s" stroke-width="13" fill="none"/>' % (
                    x1, y1, r, r, cxp + r * math.cos(a2), 1080 + r * math.sin(a2), random.choice(pietre)))
    for y, hh in ((850, 9), (904, 12)):
        b.append('<rect x="0" y="%d" width="1080" height="%d" fill="url(#rotaia)"/>' % (y, hh))
        b.append('<rect x="0" y="%d" width="1080" height="3" fill="#1E1E1E"/>' % (y + hh))
    b.append('<rect x="30" y="976" width="1020" height="82" rx="10" fill="%s" opacity=".9"/>' % NERO)
    b.append(T(54, 1010, 'Prossima fermata: la tua storia.', 22, '#FFC400', GROT, '900'))
    b.append(T(54, 1040, '17 storie, 88 quartieri, 125 fermate del metrò. Biglietto gratuito: i dati sono aperti.', 17, '#fff', GROT, '600'))
    salva('bozza_12_tram.svg', svg('\n'.join(b), CIELO, 'Milano in dati - bozza 12, il tram Ventotto'))

if __name__ == '__main__':
    bozza9(); bozza10(); bozza11(); bozza12()
