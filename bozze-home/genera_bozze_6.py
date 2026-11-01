# -*- coding: utf-8 -*-
"""Bozze 21-24 della home di "Milano in dati": la COPERTINA DI TUTTE LE RICERCHE.
Ogni storia e' presente con un numero vero e, dove costa poco, una piccola figura fatta con i suoi dati (docs/<filone>/data/).
Formato: 1600x1600 (22 storie non stanno bene in 1080). SVG ferme, colori piatti, un solo carattere (Helvetica/Arial, due pesi).
Legge solo docs/ (non lo modifica). Anteprime PNG con Playwright + foglio anteprime/bozze_21_24.png.
Uso: python -I genera_bozze_6.py
"""
import os, sys, csv, json, glob, collections
sys.stdout.reconfigure(encoding='utf-8')
QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from genera_bozze import NIL, COMUNE, Proj, path, esc, T, TEMP, centro_nil, carica, DOCS

W = H = 1600
SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
ROSSO = '#E30613'; NERO = '#111111'; GR = '#E6E6E6'; GR2 = '#8C8C8C'; BIANCO = '#FFFFFF'
LIN = {'M1': '#E3001B', 'M2': '#00A650', 'M3': '#FFD200', 'M4': '#0072BC', 'M5': '#9B5BA5'}
LIN_T = dict(LIN, M3='#E0A800')           # giallo piu' scuro per tratti sottili su bianco
GRUPPI = {'M1': 'Clima e ambiente', 'M2': 'Chi siamo', 'M3': 'Muoversi', 'M4': 'Cultura', 'M5': 'Passioni e conflitti'}

def it(n, dec=0):
    s = ('{:,.%df}' % dec).format(n)
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')

def csvr(p):
    with open(os.path.join(DOCS, p), encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def svg2(body, titolo):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">\n<title>%s</title>\n'
            '<rect width="%d" height="%d" fill="#FFFFFF"/>\n%s\n</svg>\n') % (W, H, W, H, esc(titolo), W, H, body)

def salva(nome, s):
    with open(os.path.join(QUI, nome), 'w', encoding='utf-8') as f:
        f.write(s)
    print(nome, round(len(s.encode('utf-8')) / 1024), 'KB')

# ====================================================================== DATI (un numero vero per storia)
def per_decennio(anni):
    c = collections.Counter((a // 10) * 10 for a in anni)
    return [c[d] for d in range(min(c), max(c) + 1, 10)]

def dati():
    S = []
    def add(id_, nome, g, num, lab, kind=None, data=None, da=None, pos=None, note=''):
        S.append(dict(id=id_, nome=nome, g=g, num=num, lab=lab, kind=kind, data=data, da=da, pos=pos, note=note))

    # temperature: temperature/data/finora.json righe[0] (tmedia: rank_alto, n); serie = annuale.json (TEMP, anni completi)
    fin = carica('temperature/data/finora.json')['righe'][0]
    tok = [a['tmedia'] for a in TEMP if a['ok']]
    add('temp', 'Temperature', 'M1', 'n. %d' % fin['rank_alto'], 'anno più caldo su %d, il 2026 (finora). Brera dal 1763' % fin['n'],
        'spark', tok, 1763, (9.188, 45.472))
    # aria: aria/data/annuale.json NO2, stazione 501 (viale Marche), anni fino al 2025
    no2 = [(a[0], a[1]) for a in carica('aria/data/annuale.json')['NO2']['stazioni']['501'] if a[0] <= 2025]
    add('aria', 'Aria', 'M1', it(no2[-1][1], 1), 'µg/m³ di NO₂ in viale Marche nel %d (nel %d: %s)' % (no2[-1][0], no2[0][0], it(no2[0][1], 1)),
        'spark', [v for _, v in no2], 1977, (9.19093, 45.49632))
    # neve e nebbia: neve-e-nebbia/data/decenni.json inverni.LINATE.n[].m (giorni di neve a inverno, media per decennio)
    nv = carica('neve-e-nebbia/data/decenni.json')['inverni']['LINATE']['n']
    add('neve', 'Neve e nebbia', 'M1', it(nv[0]['m'], 1) + ' → ' + it(nv[-1]['m'], 0), 'giorni di neve a Linate: anni Cinquanta → anni Venti',
        'bars', [x['m'] for x in nv], 1951, (9.2300, 45.4580))
    # acqua: acqua-del-sindaco/index.html ("nessun valore supera un limite di legge", gen 2021 - set 2026)
    add('acqua', 'Acqua del sindaco', 'M1', '0', 'valori sopra i limiti di legge, da gennaio 2021', 'dots4', None, 2021, (9.1990, 45.4720))

    # censimenti: censimenti/data/dati.json comune.str (quota stranieri 1991..2023)
    st = carica('censimenti/data/dati.json')['comune']['str']
    add('cens', 'Censimenti', 'M2', it(st[-1], 1) + '%', 'stranieri nel 2023 (nel 1991: %s%%)' % it(st[0], 1), 'bars', st, 1861, 'NIL82')
    # donne nelle vie: vie/data/percentuali.json percentuali[0].quota_donne_su_persone_ferma (santi compresi)
    pv = carica('vie/data/percentuali.json')['percentuali'][0]
    add('vie', 'Donne nelle vie', 'M2', it(pv['quota_donne_su_persone_ferma'] * 100, 1) + '%',
        'delle vie intitolate a persone: %d donne su %s' % (pv['donne_sicure'], it(pv['persone_sicure'])), 'pct', pv['quota_donne_su_persone_ferma'] * 100, None, (9.1798, 45.4852))
    # prezzi case: prezzi-case/data/serie_citta.csv, Abitazioni civili, prezzo mediano nominale e in euro 2025
    pr = [r for r in csvr('prezzi-case/data/serie_citta.csv') if r['tipologia'] == 'Abitazioni civili']
    add('case', 'Prezzi delle case', 'M2', it(float(pr[-1]['prezzo_mediano_nominale_eur_m2'])) + ' €', '€ al m², zona mediana, %s (nel 2006: %s)' % ('1° semestre 2026' if pr[-1]['semestre'].endswith('S1') else pr[-1]['semestre'], it(float(pr[0]['prezzo_mediano_nominale_eur_m2']))),
        'spark', [float(r['prezzo_mediano_euro2025_m2']) for r in pr], 2006, (9.1957, 45.4686))
    # bilancio: bilancio-comune/data/riepilogo.json spesa.totale.reale_pc (spesa corrente per abitante, euro 2025)
    bil = carica('bilancio-comune/data/riepilogo.json')['spesa']['totale']['reale_pc']
    add('bil', 'Bilancio del Comune', 'M2', it(bil[-1]) + ' €', 'di spesa corrente per abitante nel 2025 (euro 2025)', 'spark', bil, 2015, (9.1905, 45.4660))
    # appalti: appalti/index.html "A Milano città ... il 54,5% dei lotti ha un solo offerente, contro il 43,0% atteso"
    add('app', 'Appalti pubblici', 'M2', '54,5%', 'dei lotti ha un solo offerente a Milano città (atteso: 43,0%)', 'bars', [54.5, 43.0], 2019, (9.1830, 45.4640))

    # area c: area-c/data/tabelle.json anno[].lavorativi_media (ingressi medi in un giorno feriale)
    ac = [(x['anno'], x['lavorativi_media']) for x in carica('area-c/data/tabelle.json')['anno']]
    a19 = dict(ac)[2019]; a24 = dict(ac)[2024]
    add('areac', 'Area C', 'M3', '%s%%' % it((a24 / a19 - 1) * 100, 0).replace('-', '−'), 'ingressi in un giorno feriale, 2024 rispetto al 2019', 'spark', [v for _, v in ac], 2016, (9.1900, 45.4640))
    # bici: bici-auto-mezzi/data/quote.json quote[] alle 08:00, media di bici_pct pesata con coppie
    q = [x for x in carica('bici-auto-mezzi/data/quote.json')['quote'] if x['fascia_oraria'] == '08:00']
    bici = sum(x['coppie'] * x['bici_pct'] for x in q) / sum(x['coppie'] for x in q)
    add('bici', 'Bici, auto, mezzi', 'M3', it(bici, 0) + '%', 'dei viaggi in cui, alle 8, arriva prima la bici', 'pct', bici, 2026, (9.1799, 45.4533))
    # 15 minuti: citta-15-minuti/data/riepilogo.json citta.tutti (quota con tutti e 10 i servizi) e distribuzione
    c15 = carica('citta-15-minuti/data/riepilogo.json')['citta']
    add('15', 'Città dei 15 minuti', 'M3', it(c15['tutti'] * 100, 1) + '%', 'dei residenti ha tutti e 10 i servizi a 15 minuti a piedi',
        'bars', [c15['distribuzione'][str(i)] for i in range(11)], 2026, 'NIL43')
    # nomi fermate: nomi-fermate/data/riepilogo.json persone_reali, donne
    nf = carica('nomi-fermate/data/riepilogo.json')
    add('fermate', 'Nomi delle fermate', 'M3', '1 su %d' % nf['persone_reali'], 'nomi di persone del metrò è una donna (%d stazioni)' % nf['stazioni'], 'dots', (nf['persone_reali'], nf['donne']), None, (9.1900, 45.4642))

    # scala: scala/data/titoli.json, titoli diversi per anno senza concerti (tipo c)
    sc = carica('scala/data/titoli.json')
    uniq = {(r[0], r[3]) for r in sc if r[5] != 'c'}
    cy = collections.Counter(a for a, _ in uniq)
    add('scala', 'La Scala', 'M4', it(len(uniq)), 'titoli diversi in scena, dal 1778 (senza i concerti)', 'spark', [cy[a] for a in range(1778, 2026)], 1778, (9.1895, 45.4674))
    # beni culturali: beni-culturali/data/numeri.json schede_sede_milano, per_secolo
    bc = carica('beni-culturali/data/numeri.json')
    ps = bc['per_secolo']
    add('beni', 'Beni culturali', 'M4', it(bc['schede_sede_milano']), 'schede di beni a Milano nel Catalogo generale (per secolo)', 'bars', [ps[k] for k in sorted((k for k in ps if k.isdigit()), key=int)], 1100, (9.1794, 45.4705))
    # milano raccontata: milano-raccontata/data/stats.json film.tot, libro.tot, per_decennio.film
    mr = carica('milano-raccontata/data/stats.json')
    pd = mr['per_decennio']['film']
    add('film', 'Milano raccontata', 'M4', it(mr['film']['tot']), 'film e %d libri ambientati a Milano (film per decennio)' % mr['libro']['tot'], 'bars', [pd[k]['tot'] for k in sorted(pd)], 1930, (9.2043, 45.4863))
    # cinema: cinema-spariti/data/serie.json chiuse totali + istantanee (sale attive per decennio)
    cs = carica('cinema-spariti/data/serie.json')
    add('cinema', 'Cinema spariti', 'M4', '171', 'sale chiuse dal 1896 al 2023; 28 aperte oggi', 'bars', [c['chiuse'] + c['aperte_note'] for c in cs['istantanee']], 1896, (9.1905, 45.4652))

    # derby: derby/data/partite.json, w = I (Inter), M (Milan), D (pari)
    dp = carica('derby/data/partite.json')
    cw = collections.Counter(x['w'] for x in dp)
    add('derby', 'Derby', 'M5', str(len(dp)), 'Inter %d, pari %d, Milan %d, dal 1909' % (cw['I'], cw['D'], cw['M']), 'split', [cw['I'], cw['D'], cw['M']], 1909, (9.1240, 45.4781))
    # elezioni: elezioni/data/index.json elezioni[] (una per elezione), per decennio
    el = carica('elezioni/data/index.json')['elezioni']
    add('elez', 'Elezioni', 'M5', str(len(el)), 'elezioni nei dati, dal 1946 (per decennio)', 'bars', per_decennio([e['anno'] for e in el]), 1946, (9.1905, 45.4666))
    # violenza politica: violenza-politica/data/eventi.csv (una riga per fatto), per decennio
    vp = csvr('violenza-politica/data/eventi.csv')
    add('viol', 'Violenza politica', 'M5', str(len(vp)), 'fatti registrati a Milano dal 1900 (per decennio)', 'bars', per_decennio([int(r['anno']) for r in vp]), 1900, (9.1930, 45.4640))

    add('alberi', 'Alberi', 'M1', 'in arrivo', 'prossima storia', None, None, None, None)
    add('affitti', 'Affitti brevi', 'M2', 'in arrivo', 'prossima storia', None, None, None, None)
    return S

# ====================================================================== micro-figure
def micro(S, x, y, w, h):
    """piccola figura piatta fatta con i dati della storia, dentro il riquadro (x,y,w,h)"""
    k, d = S['kind'], S['data']
    col = LIN_T[S['g']]
    o = []
    if k == 'spark':
        lo, hi = min(d), max(d)
        pts = ['%.1f,%.1f' % (x + w * i / (len(d) - 1), y + h - (v - lo) / (hi - lo or 1) * h) for i, v in enumerate(d)]
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.4" stroke-linejoin="round"/>' % (' '.join(pts), col))
        px, py = pts[-1].split(',')
        o.append('<circle cx="%s" cy="%s" r="4.5" fill="%s"/>' % (px, py, ROSSO))
        o.append('<rect x="%d" y="%d" width="%d" height="1.5" fill="%s"/>' % (x, y + h + 4, w, NERO))
    elif k == 'bars':
        n = len(d); bw = w / n; hi = max(d)
        for i, v in enumerate(d):
            bh = max(2, v / hi * h)
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x + i * bw + bw * .12, y + h - bh, bw * .76, bh, col))
        o.append('<rect x="%d" y="%d" width="%d" height="1.5" fill="%s"/>' % (x, y + h + 3, w, NERO))
    elif k == 'split':
        tot = sum(d); cx = x
        for v, c in zip(d, ('#1B3FA8', '#BDBDBD', '#D40000')):
            ww = w * v / tot
            o.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (cx, y + h * .25, ww - 2, h * .5, c))
            cx += ww
    elif k == 'pct':
        o.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (x, y + h * .3, w, h * .4, GR))
        o.append('<rect x="%d" y="%d" width="%.1f" height="%d" fill="%s"/>' % (x, y + h * .3, w * d / 100, h * .4, col))
    elif k == 'dots':
        n, r = d; cols = 11; rad = min(w / cols, h / 3) / 2 - 1
        for i in range(n):
            cxx = x + (i % cols + .5) * (w / cols); cyy = y + (i // cols + .5) * (h / 3)
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (cxx, cyy, rad, ROSSO if i < r else GR))
    elif k == 'dots4':
        for i in range(4):
            o.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x + (i + .5) * w / 4, y + h / 2, min(h, w / 4) / 2 - 3, LIN['M2']))
    return ''.join(o)

def wrap(s, n):
    righe, cur = [], ''
    for p in s.split():
        if len(cur) + len(p) + 1 > n and cur:
            righe.append(cur); cur = p
        else:
            cur = (cur + ' ' + p).strip()
    if cur: righe.append(cur)
    return righe

def inarrivo_box(x, y, w, h, nome):
    return ('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="8 6"/>' % (x, y, w, h, GR2) +
            T(x + 20, y + 44, nome, 22, GR2, SANS, '700') + T(x + 20, y + 100, 'in arrivo', 40, GR2, SANS, '700', extra='letter-spacing="-1"'))

def mappa_flat(P, fill=GR, stroke=BIANCO, sw=1):
    return ''.join('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>' % (path(g, P), fill, stroke, sw) for g in NIL.values())

def fascia(titolo_y=118):
    b = ['<rect width="%d" height="170" fill="%s"/>' % (W, ROSSO)]
    b.append(T(60, 120, 'Milano in dati', 96, BIANCO, SANS, '700', extra='letter-spacing="-2"'))
    b.append(T(1540, 120, '22 storie · 88 quartieri', 34, BIANCO, SANS, '400', 'end'))
    return ''.join(b)

# ====================================================================== 21  tessere uguali
def bozza21(S):
    b = []
    M, G = 40, 12
    TS = (W - 2 * M - 4 * G) / 5
    cells = ['titolo'] + S + ['mappa', 'legenda']
    for i, c in enumerate(cells):
        r, cc = divmod(i, 5)
        x = M + cc * (TS + G); y = M + r * (TS + G)
        if c == 'titolo':
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s"/>' % (x, y, TS, TS, ROSSO))
            b.append(T(x + 24, y + 120, 'Milano', 64, BIANCO, SANS, '700', extra='letter-spacing="-2"'))
            b.append(T(x + 24, y + 186, 'in dati', 64, BIANCO, SANS, '700', extra='letter-spacing="-2"'))
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="3" fill="%s"/>' % (x + 24, y + 216, TS - 48, BIANCO))
            b.append(T(x + 24, y + 258, '22 storie sulla città', 22, BIANCO, SANS, '400'))
        elif c == 'mappa':
            P = Proj(box=(x + 20, y + 20, TS - 40, TS - 40))
            b.append(mappa_flat(P))
            b.append('<path d="%s" fill="%s"/>' % (path(NIL[82], P), ROSSO))
        elif c == 'legenda':
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="%s" stroke-width="2"/>' % (x, y, TS, TS, NERO))
            for j, g in enumerate(LIN):
                yy = y + 50 + j * 46
                b.append('<circle cx="%.1f" cy="%.1f" r="16" fill="%s"/>' % (x + 38, yy - 6, LIN[g]))
                b.append(T(x + 38, yy, g, 15, NERO if g == 'M3' else BIANCO, SANS, '700', 'middle'))
                b.append(T(x + 68, yy, GRUPPI[g], 20, NERO, SANS, '400'))
            b.append(T(x + 24, y + TS - 22, 'colore = tema della storia', 16, GR2, SANS, '400'))
        elif c['kind'] is None:
            b.append(inarrivo_box(x, y, TS, TS, c['nome']))
        else:
            col = LIN[c['g']]
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, TS, TS, BIANCO, NERO))
            b.append('<rect x="%.1f" y="%.1f" width="%.1f" height="14" fill="%s"/>' % (x, y, TS, col))
            b.append(T(x + 20, y + 54, c['nome'], 23, NERO, SANS, '700'))
            fs = 60 if len(c['num']) <= 6 else 44
            b.append(T(x + 18, y + 120, c['num'], fs, ROSSO if c['g'] != 'M3' else NERO, SANS, '700', extra='letter-spacing="-2"'))
            for j, ln in enumerate(wrap(c['lab'], 31)[:3]):
                b.append(T(x + 20, y + 152 + j * 20, ln, 16, NERO, SANS, '400'))
            b.append(micro(c, x + 20, y + TS - 78, TS - 40, 52))
            if c['da']:
                b.append(T(x + 20, y + TS - 10, ('dal %d' % c['da']) if c['da'] < 2026 else 'oggi', 14, GR2, SANS, '700'))
    salva('bozza_21_tessere.svg', svg2('\n'.join(b), 'Milano in dati - bozza 21, tessere'))

# ====================================================================== 22  mappa con le storie dove stanno
def bozza22(S):
    b = []
    b.append(T(40, 84, 'Milano in dati', 64, ROSSO, SANS, '700', extra='letter-spacing="-2"'))
    b.append(T(1560, 84, '22 storie · 88 quartieri', 26, NERO, SANS, '400', 'end'))
    b.append('<rect x="40" y="104" width="1520" height="3" fill="%s"/>' % NERO)
    P = Proj(box=(425, 190, 750, 1180))
    b.append(mappa_flat(P, GR, BIANCO, 1.2))
    pubb = [s for s in S if s['kind']]
    def punto(s):
        if s['pos'] is None:
            return None
        if isinstance(s['pos'], str):
            return centro_nil(int(s['pos'][3:]), P)
        return P(*s['pos'])
    for s in pubb:
        s['xy'] = punto(s)
    # sinistra/destra: metà per parte, ordinate dall'alto in basso (le righe non si incrociano)
    ordine = sorted(pubb, key=lambda s: s['xy'][0])
    sx, dx = ordine[:10], ordine[10:]
    sx.sort(key=lambda s: s['xy'][1]); dx.sort(key=lambda s: s['xy'][1])
    CW, CH, GAP = 380, 132, 12
    y0 = 128
    cards = []
    for lato, lista in (('s', sx), ('d', dx)):
        for i, s in enumerate(lista):
            x = 40 if lato == 's' else W - 40 - CW
            y = y0 + i * (CH + GAP)
            cards.append((s, x, y, lato))
    # prima le linee, poi i punti, poi le schede
    for s, x, y, lato in cards:
        ax = x + CW if lato == 's' else x
        b.append('<path d="M%.1f,%.1f L%.1f,%.1f" stroke="%s" stroke-width="2.4" fill="none"/>' % (ax, y + CH / 2, s['xy'][0], s['xy'][1], LIN_T[s['g']]))
    for s, x, y, lato in cards:
        b.append('<circle cx="%.1f" cy="%.1f" r="8" fill="%s" stroke="%s" stroke-width="3"/>' % (s['xy'][0], s['xy'][1], LIN[s['g']], BIANCO))
    for s, x, y, lato in cards:
        col = LIN[s['g']]
        b.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, CW, CH, BIANCO, NERO))
        b.append('<rect x="%d" y="%d" width="12" height="%d" fill="%s"/>' % (x, y, CH, col))
        b.append(T(x + 28, y + 30, s['nome'], 21, NERO, SANS, '700'))
        b.append(T(x + 26, y + 74, s['num'], 44 if len(s['num']) <= 7 else 34, ROSSO if s['g'] != 'M3' else NERO, SANS, '700', extra='letter-spacing="-1.5"'))
        for j, ln in enumerate(wrap(s['lab'], 31)[:3]):
            b.append(T(x + 28, y + 94 + j * 15, ln, 14, NERO, SANS, '400'))
        b.append(micro(s, x + CW - 150, y + 40, 132, 44))
    # in arrivo, in basso al centro
    ia = [s for s in S if not s['kind']]
    for j, s in enumerate(ia):
        x = 470 + j * 340; y = 1470
        b.append('<rect x="%d" y="%d" width="320" height="90" fill="none" stroke="%s" stroke-width="2" stroke-dasharray="8 6"/>' % (x, y, GR2))
        b.append(T(x + 20, y + 38, s['nome'], 22, GR2, SANS, '700'))
        b.append(T(x + 20, y + 72, 'in arrivo', 26, GR2, SANS, '700'))
    # legenda
    for j, g in enumerate(LIN):
        b.append('<circle cx="%d" cy="%d" r="9" fill="%s"/>' % (440 + j * 150 + 9, 150, LIN[g]))
        b.append(T(440 + j * 150 + 26, 156, GRUPPI[g], 13, NERO, SANS, '400'))
    b.append(T(1160, 200, 'Le linee uniscono ogni storia', 15, GR2, SANS, '400', 'end'))
    b.append(T(1160, 218, 'a un luogo indicativo della città', 15, GR2, SANS, '400', 'end'))
    salva('bozza_22_mappa.svg', svg2('\n'.join(b), 'Milano in dati - bozza 22, mappa con le storie'))

# ====================================================================== 23  linea del tempo
def bozza23(S):
    b = []
    b.append(fascia())
    X0, X1 = 370, 1000           # asse 1760 -> 2030
    A0, A1 = 1760, 2030
    fx = lambda a: X0 + (max(a, A0) - A0) / (A1 - A0) * (X1 - X0)
    y0 = 300
    RH = 56
    # assi
    for a in range(1800, 2031, 50):
        b.append('<rect x="%.1f" y="%d" width="1.5" height="%d" fill="%s"/>' % (fx(a), y0 - 24, RH * 22 + 30, GR))
        b.append(T(fx(a), y0 - 34, str(a), 18, GR2, SANS, '700', 'middle'))
    b.append(T(60, y0 - 34, 'storia', 18, GR2, SANS, '700'))
    b.append(T(1030, y0 - 34, 'il numero', 18, GR2, SANS, '700'))
    b.append(T(X0, 214, 'Ogni barra parte dal primo anno dei dati e arriva al 2026.', 24, NERO, SANS, '400'))
    ordine = sorted([s for s in S if s['kind']], key=lambda s: (s['da'] if s['da'] else 2026, s['nome']))
    ia = [s for s in S if not s['kind']]
    for i, s in enumerate(ordine + ia):
        y = y0 + i * RH
        if i % 2 == 0:
            b.append('<rect x="40" y="%d" width="1520" height="%d" fill="#F5F5F5"/>' % (y - 12, RH))
        col = LIN[s['g']] if s['kind'] else GR2
        b.append('<rect x="40" y="%d" width="10" height="%d" fill="%s"/>' % (y - 12, RH, col))
        b.append(T(66, y + 22, s['nome'], 24, NERO if s['kind'] else GR2, SANS, '700'))
        if not s['kind']:
            b.append(T(1030, y + 24, 'in arrivo', 24, GR2, SANS, '700'))
            continue
        da = s['da'] or 2026
        x1 = fx(da); x2 = fx(2026)
        if s['da'] is None:      # istantanea di oggi
            b.append('<circle cx="%.1f" cy="%d" r="9" fill="%s"/>' % (x2, y + 16, col))
            b.append(T(x2 - 20, y + 22, 'oggi', 16, GR2, SANS, '700', 'end'))
        else:
            b.append('<rect x="%.1f" y="%d" width="%.1f" height="18" fill="%s"/>' % (x1, y + 7, max(6, x2 - x1), LIN_T[s['g']]))
            if da < A0:
                b.append(T(x1 - 6, y + 22, '◀ dal %d' % da, 16, GR2, SANS, '700', 'end'))
            else:
                b.append(T(x1 - 8, y + 22, str(da), 16, GR2, SANS, '700', 'end'))
        b.append(T(1030, y + 30, s['num'], 34, ROSSO if s['g'] != 'M3' else NERO, SANS, '700', extra='letter-spacing="-1"'))
        for j, ln in enumerate(wrap(s['lab'], 50)[:2]):
            b.append(T(1215, y + 20 + j * 17, ln, 14, NERO, SANS, '400'))
    P = Proj(box=(60, 1560, 40, 40))
    b.append(T(60, 1578, 'Dal Settecento a oggi: le barre lunghe sono le serie storiche, le corte i dati recenti.', 18, GR2, SANS, '400'))
    salva('bozza_23_tempo.svg', svg2('\n'.join(b), 'Milano in dati - bozza 23, linea del tempo'))

# ====================================================================== 24  sommario
def bozza24(S):
    b = []
    b.append('<rect width="%d" height="190" fill="%s"/>' % (W, ROSSO))
    b.append(T(60, 130, 'Milano in dati', 110, BIANCO, SANS, '700', extra='letter-spacing="-3"'))
    P = Proj(box=(1330, 20, 230, 150))
    b.append(mappa_flat(P, BIANCO, ROSSO, .8))
    b.append(T(1290, 100, 'Sommario', 38, BIANCO, SANS, '400', 'end'))
    b.append('<rect x="0" y="190" width="%d" height="8" fill="%s"/>' % (W, NERO))
    ordine = []
    for g in LIN:
        ordine += [s for s in S if s['g'] == g]
    col1, col2 = ordine[:11], ordine[11:]
    RH = 118; y0 = 240; CWd = 740
    n = 0
    for ci, lista in enumerate((col1, col2)):
        x = 40 + ci * 780
        for i, s in enumerate(lista):
            y = y0 + i * RH
            n += 1
            b.append('<rect x="%d" y="%d" width="%d" height="2" fill="%s"/>' % (x, y, CWd, NERO))
            col = LIN[s['g']]
            b.append('<circle cx="%d" cy="%d" r="17" fill="%s"/>' % (x + 18, y + 38, col))
            b.append(T(x + 18, y + 44, s['g'], 14, NERO if s['g'] == 'M3' else BIANCO, SANS, '700', 'middle'))
            b.append(T(x + 52, y + 42, s['nome'], 26, NERO if s['kind'] else GR2, SANS, '700'))
            if not s['kind']:
                b.append(T(x + 52, y + 86, 'in arrivo', 20, GR2, SANS, '700'))
                continue
            for j, ln in enumerate(wrap(s['lab'], 34)[:2]):
                b.append(T(x + 52, y + 72 + j * 20, ln, 15, NERO, SANS, '400'))
            b.append(T(x + 505, y + 62, s['num'], 46 if len(s['num']) <= 6 else 38, ROSSO if s['g'] != 'M3' else NERO, SANS, '700', 'end', 'letter-spacing="-2"'))
            b.append(micro(s, x + 530, y + 24, 190, 60))
        b.append('<rect x="%d" y="%d" width="%d" height="2" fill="%s"/>' % (x, y0 + 11 * RH, CWd, NERO))
    b.append(T(40, 1590, 'Rosso, verde, giallo, blu e lilla sono i colori delle linee del metrò: ogni linea raggruppa le storie di un tema.', 18, GR2, SANS, '400'))
    salva('bozza_24_sommario.svg', svg2('\n'.join(b), 'Milano in dati - bozza 24, sommario'))

def anteprime(nomi):
    from playwright.sync_api import sync_playwright
    os.makedirs(os.path.join(QUI, 'anteprime'), exist_ok=True)
    with sync_playwright() as p:
        try:
            br = p.chromium.launch()
        except Exception:
            br = p.chromium.launch(channel='msedge')
        pg = br.new_page(viewport={'width': W, 'height': H})
        for n in nomi:
            pg.goto('file:///' + os.path.join(QUI, n).replace('\\', '/'))
            pg.screenshot(path=os.path.join(QUI, 'anteprime', n.replace('.svg', '.png')))
        br.close()

def foglio(nomi):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype('arialbd.ttf', 34)
    IM = 900; img = Image.new('RGB', (2 * IM + 60, 2 * (IM + 70) + 20), '#FFFFFF'); d = ImageDraw.Draw(img)
    etich = ['21  Tessere', '22  Mappa', '23  Linea del tempo', '24  Sommario']
    for k, n in enumerate(nomi):
        r, c = divmod(k, 2)
        x, y = 20 + c * (IM + 20), 20 + r * (IM + 70)
        im = Image.open(os.path.join(QUI, 'anteprime', n.replace('.svg', '.png'))).convert('RGB').resize((IM, IM), Image.LANCZOS)
        img.paste(im, (x, y)); d.rectangle([x - 1, y - 1, x + IM, y + IM], outline='#BBBBBB')
        d.text((x, y + IM + 10), etich[k], fill='#111111', font=f)
    img.save(os.path.join(QUI, 'anteprime', 'bozze_21_24.png'))

if __name__ == '__main__':
    S = dati()
    for s in S:
        print(s['id'], '|', s['num'], '|', s['lab'])
    bozza21(S); bozza22(S); bozza23(S); bozza24(S)
    nomi = ['bozza_21_tessere.svg', 'bozza_22_mappa.svg', 'bozza_23_tempo.svg', 'bozza_24_sommario.svg']
    anteprime(nomi); foglio(nomi)
