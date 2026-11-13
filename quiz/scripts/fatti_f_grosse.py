"""Domande «grosse e succose» (modulo f_grosse): fatti da raccontare a cena, con confronti e record.

Temi rinforzati: cultura, politica, sicurezza, casa, servizi. Ogni numero viene da p.v(...) o p.calc(...).
"""
from mazzo import Prove, carica, piuomeno, numero, vf, ordine, anno_q


def ix(rel, **cond):
    """Posizione (nel file) della prima riga che soddisfa tutte le condizioni."""
    for i, r in enumerate(carica(rel)):
        if all(str(r.get(k)) == str(v) for k, v in cond.items()):
            return '[%d]' % i
    raise KeyError((rel, cond))


def domande():
    out = []
    out += cultura()
    out += politica()
    out += sicurezza()
    out += casa()
    out += servizi()
    return out


# ====================================================================== CULTURA
def cultura():
    out = []

    # --- Wikipedia: italiano o altre lingue
    L = 'luoghi-cercati/data/riepilogo.json'
    p = Prove()
    it = p.v(L, 'annuale', '2025', 'it')
    st = p.v(L, 'annuale', '2025', 'estero')
    it19 = p.v(L, 'annuale', '2019', 'it')
    st19 = p.v(L, 'annuale', '2019', 'estero')
    out.append(piuomeno(p, id='luoghi-estero-2025', pagina='luoghi-cercati', diff='facile',
        domanda='Nel 2025 le voci sui luoghi di Milano (Duomo, San Siro, Navigli…) su Wikipedia sono state lette di più in italiano o in tutte le altre lingue messe insieme?',
        a=('in italiano, 2025', it, 'letture'), b=('in tutte le altre lingue, 2025', st, 'letture'),
        spiega='Le altre lingue vincono: 6,5 milioni di letture contro 6,0 in italiano. Nel 2019 era l’opposto: 7,5 milioni in italiano e 5,8 nelle altre lingue.',
        anno='2025', fonte='Wikimedia, letture delle voci di Wikipedia sui luoghi di Milano', licenza='CC0 1.0'))

    p = Prove()
    rk = p.v(L, 'sorpresa', 'bosco_rango')
    bo = p.v(L, 'sorpresa', 'bosco_t')
    du = p.v(L, 'sorpresa', 'duomo_t')
    out.append(vf(p, id='bosco-verticale-top10', pagina='luoghi-cercati', diff='facile',
        affermazione='Il Bosco Verticale, i due grattacieli con gli alberi sui balconi, è tra i dieci luoghi di Milano più letti su Wikipedia.',
        vero=rk <= 10, confronto=[('Bosco Verticale', bo, 'letture'), ('Duomo di Milano', du, 'letture')],
        spiega='È il settimo luogo più letto, con 3,1 milioni di letture dal 2015. Il Duomo ne ha 15,8 milioni, cinque volte tanto.',
        anno='2015–2026', fonte='Wikimedia, letture delle voci di Wikipedia sui luoghi di Milano', licenza='CC0 1.0'))

    # --- Musei
    M = 'musei/data/riepilogo.json'
    p = Prove()
    c19 = p.v(M, 'sorprese', 'cenacolo_2019')
    c24 = p.v(M, 'sorprese', 'cenacolo_2024')
    c20 = p.v(M, 'sorprese', 'cenacolo_2020')
    pc = p.calc('round((p[1]/p[0]-1)*100, 1)')
    out.append(vf(p, id='cenacolo-2019-2024', pagina='musei', diff='facile',
        affermazione='Nel 2024 il Cenacolo Vinciano, con l’Ultima Cena di Leonardo, ha avuto più visitatori che nel 2019, l’anno prima della pandemia.',
        vero=c24 > c19, confronto=[('2019', c19, 'visitatori'), ('2024', c24, 'visitatori')],
        spiega='Nel 2019 erano 445.728 e nel 2024 sono 529.422: il 19% in più. Nel 2020 erano scesi a 132.223.',
        anno='2019–2024', fonte='Ministero della Cultura, visitatori dei musei statali', licenza='Uso con citazione, non aperta'))

    p = Prove()
    i10 = p.v(M, 'sorprese', 'cenacolo_introiti_2010')
    i24 = p.v(M, 'sorprese', 'cenacolo_introiti_2024')
    v10 = p.v(M, 'sorprese', 'cenacolo_vis_2010')
    v24 = p.v(M, 'sorprese', 'cenacolo_vis_2024')
    e10 = p.v(M, 'sorprese', 'cenacolo_euro_pagante_2010')
    e24 = p.v(M, 'sorprese', 'cenacolo_euro_pagante_2024')
    pv = p.calc('round((p[3]/p[2]-1)*100)')
    rt = p.calc('round(p[1]/p[0], 1)')
    out.append(numero(p, id='cenacolo-incassi', pagina='musei', diff='media',
        domanda='Quante volte più incassa oggi il Cenacolo Vinciano rispetto al 2010? Si contano gli incassi lordi dei biglietti.',
        v=rt, lo=1, hi=10, passo=0.1, unita='volte', dec=1,
        confronto=[('incassi 2010', i10, '€'), ('incassi 2024', i24, '€')],
        spiega='Da 1,7 a 6,3 milioni di euro: quasi quattro volte tanto, mentre i visitatori sono cresciuti solo del 57%. Ogni visitatore pagante lascia in media 14,32 euro, contro 6,39 nel 2010.',
        anno='2010–2024', fonte='Ministero della Cultura, visitatori e incassi dei musei statali', licenza='Uso con citazione, non aperta'))

    # --- Derby
    D = 'derby/data/derby.csv'
    righe = carica(D)
    p = Prove()
    w = [p.v(D, '[%d]' % i, 'winner') for i in range(len(righe))]
    ni = p.calc('+'.join("(p[%d]=='Inter')" % i for i in range(len(righe))))
    nm = p.calc('+'.join("(p[%d]=='Milan')" % i for i in range(len(righe))))
    npar = p.calc('+'.join("(p[%d]=='draw')" % i for i in range(len(righe))))
    assert (ni, nm, npar) == (91, 85, 71), (ni, nm, npar)
    ntot = p.calc('len(p)')
    out.append(piuomeno(p, id='derby-vittorie', pagina='derby', diff='facile',
        domanda='Nei derby di Milano dal 1909 a oggi, chi ha vinto di più: l’Inter o il Milan?',
        a=('vittorie dell’Inter', ni, 'derby'), b=('vittorie del Milan', nm, 'derby'),
        spiega='L’Inter è avanti 91 a 85, con 71 pareggi, su 247 derby. Due sono derby di guerra, riconosciuti a titolo onorario.',
        anno='1909–2026', fonte='Wikipedia, tutti i derby Inter-Milan dal 1909', licenza='CC BY-SA 4.0'))

    ix11 = [i for i, r in enumerate(righe) if r['home_goals'] + r['away_goals'] == 11]
    assert len(ix11) == 1
    k = ix11[0]
    p = Prove()
    hg = p.v(D, '[%d]' % k, 'home_goals')
    ag = p.v(D, '[%d]' % k, 'away_goals')
    gol = p.calc('p[0]+p[1]')
    kk = [i for i, r in enumerate(righe) if r['home_goals'] + r['away_goals'] == 6 and abs(r['home_goals'] - r['away_goals']) == 6][0]
    dsc = p.v(D, '[%d]' % kk, 'date')
    hs = p.v(D, '[%d]' % kk, 'home_goals')
    as_ = p.v(D, '[%d]' % kk, 'away_goals')
    assert max(abs(r['home_goals'] - r['away_goals']) for r in righe) == 6
    mx = max(r['home_goals'] + r['away_goals'] for r in righe)
    assert gol == mx
    out.append(numero(p, id='derby-gol-record', pagina='derby', diff='difficile',
        domanda='Nel derby con più gol della storia, giocato nel 1949, quanti gol sono stati segnati in tutto, tra Inter e Milan?',
        v=gol, lo=3, hi=20, passo=1, unita='gol',
        confronto=[('Inter', hg, 'gol'), ('Milan', ag, 'gol')],
        spiega='Inter 6, Milan 5: undici gol, il 6 novembre 1949. Il derby con il maggior scarto è invece lo 0-6 del 2001: Milan avanti di 6 gol.',
        anno='1949 e 2001', fonte='Wikipedia, tutti i derby Inter-Milan dal 1909', licenza='CC BY-SA 4.0'))

    # --- La Scala
    S = 'scala/data/sette_dicembre.json'
    se = carica(S)['serate']
    p = Prove()
    p.v(S, 'serate')
    a = [p.v(S, 'serate', '[%d]' % i, '2') for i in range(len(se))]
    # il lettore dei percorsi usa [i] per le liste; il primo p.v sopra serve per il numero di serate
    nv = p.calc('+'.join("(p[%d]=='Giuseppe Verdi')" % (i + 1) for i in range(len(se))))
    tot = p.calc('len(p[0])')
    assert nv == 36 and tot == 75, (nv, tot)
    out.append(numero(p, id='scala-verdi-7dic', pagina='scala', diff='media',
        domanda='Dal 1951, quante delle serate di apertura della Scala (il 7 dicembre) sono state con un’opera di Giuseppe Verdi?',
        v=nv, lo=0, hi=75, passo=1, unita='serate su 75',
        spiega='Verdi ha aperto la stagione 36 volte su 75: quasi una su due. Dietro di lui Wagner con 7 aperture, poi Puccini e Mozart con 5.',
        anno='1951–2025', fonte='Teatro alla Scala e Wikipedia, le serate di apertura dal 1951', licenza='CC BY-SA 4.0'))

    # --- Cinema
    C = 'cinema-spariti/data/serie.json'
    cs = carica(C)
    i60 = cs['anni'].index(1960)
    p = Prove()
    c1 = p.v(C, 'chiuse', '[%d]' % i60)
    c2 = p.v(C, 'aperte_note', '[%d]' % i60)
    ap = p.v(C, 'aperti_oggi_totale')
    s60 = p.calc('p[0]+p[1]')
    out.append(numero(p, id='cinema-1960', pagina='cinema-spariti', diff='media',
        domanda='Nel 1960 a Milano c’erano almeno quante sale cinematografiche attive? (Oggi i cinema aperti sono 28.)',
        v=s60, lo=0, hi=400, passo=5, unita='sale',
        confronto=[('cinema aperti oggi', ap, 'sale'), ('sale attive nel 1960 (almeno)', s60, 'sale')],
        spiega='Almeno 123 sale, il massimo di sempre: il conto è per difetto, perché mancano le sale parrocchiali e le arene. Oggi ne restano 28.',
        anno='1960', fonte='spazioCinema, Wikidata e Wikipedia; cinema aperti oggi: OpenStreetMap', licenza='CC BY-SA 4.0'))

    # --- Film girati o ambientati a Milano
    R = 'milano-raccontata/data/stats.json'
    p = Prove()
    f70 = p.v(R, 'per_decennio', 'film', '1970', 'tot')
    f10 = p.v(R, 'per_decennio', 'film', '2010', 'tot')
    ftot = p.v(R, 'film', 'tot')
    out.append(piuomeno(p, id='film-anni-70', pagina='milano-raccontata', diff='facile',
        domanda='Film ambientati o girati a Milano: ce ne sono di più degli anni Settanta o degli anni Dieci del Duemila (2010-2019)?',
        a=('anni Settanta', f70, 'film'), b=('anni Dieci del Duemila', f10, 'film'),
        spiega='Gli anni Settanta ne hanno 95, quasi il doppio dei 54 degli anni Dieci: è il decennio con più film su Milano, su 435 in tutto.',
        anno='1970 e 2010–2019', fonte='Wikipedia e Wikidata, film e libri ambientati a Milano', licenza='CC BY-SA 4.0'))

    # --- Pietre d'inciampo
    P = 'pietre-inciampo/data/riepilogo.json'
    p = Prove()
    po = p.v(P, 'categorie', 'politica')
    ra = p.v(P, 'categorie', 'razziale')
    im = p.v(P, 'categorie', 'IMI')
    out.append(piuomeno(p, id='pietre-politica-razziale', pagina='pietre-inciampo', diff='difficile',
        domanda='Le pietre d’inciampo di Milano ricordano persone deportate. Sono di più quelle per ragioni politiche o quelle per ragioni razziali?',
        a=('deportati per ragioni politiche', po, 'pietre'), b=('deportati per ragioni razziali', ra, 'pietre'),
        spiega='Quelle per ragioni politiche sono 134 e quelle per ragioni razziali 123. Altre 5 ricordano militari italiani internati nei campi tedeschi.',
        anno='2026', fonte='Comitato per le Pietre d’inciampo – Milano', licenza='Uso con citazione, non aperta'))

    # --- Beni culturali
    B = 'beni-culturali/data/numeri.json'
    p = Prove()
    s19 = p.v(B, 'per_secolo', '19')
    s18 = p.v(B, 'per_secolo', '18')
    s16 = p.v(B, 'per_secolo', '16')
    out.append(ordine(p, id='beni-secoli', pagina='beni-culturali', diff='media',
        domanda='Beni culturali schedati a Milano (quadri, statue, edifici, oggetti): metti in ordine i secoli, dal più ricco di beni al meno ricco.',
        elementi=[('Cinquecento', s16, 'schede'), ('Ottocento', s19, 'schede'), ('Settecento', s18, 'schede')], unita='schede',
        spiega='L’Ottocento ne ha 9.376: due volte e mezza il Settecento (3.786) e più di quattro volte il Cinquecento (2.268). Il Cinquecento è il più povero dei tre.',
        anno='2026', fonte='Catalogo generale dei beni culturali (ICCD), schede dei beni di Milano', licenza='CC BY-SA 4.0'))
    return out


# ====================================================================== POLITICA
def politica():
    out = []
    E = 'elezioni/data/index.json'
    FE = 'Comune di Milano, risultati delle elezioni comunali'

    # --- Sala contro Parisi
    p = Prove()
    bal = '[id=comunali_ballottaggio_2016-06-19]'
    sala = p.v(E, 'elezioni', bal, 'city', 'v', '0')
    pari = p.v(E, 'elezioni', bal, 'city', 'v', '1')
    nome_s = p.v(E, 'elezioni', bal, 'par', '0', '0')
    nome_p = p.v(E, 'elezioni', bal, 'par', '1', '0')
    assert 'Sala' in nome_s and 'Parisi' in nome_p
    dif = p.calc('p[0]-p[1]')
    out.append(numero(p, id='sala-parisi-voti', pagina='elezioni', diff='difficile',
        domanda='Nel ballottaggio del 2016 Beppe Sala ha battuto Stefano Parisi per pochissimo. Di quanti voti?',
        v=dif, lo=1000, hi=100000, passo=500, unita='voti',
        confronto=[('Parisi', pari, 'voti'), ('Sala', sala, 'voti')],
        spiega='Sala ha preso 264.387 voti e Parisi 247.149: 17.238 voti di scarto, in una città di oltre un milione di elettori.',
        anno='2016', fonte=FE, licenza='CC BY'))

    # --- 2021: più della metà non ha votato
    p = Prove()
    e21 = '[id=comunali_sindaco_2021-10-03]'
    el = p.v(E, 'elezioni', e21, 'city', 'e')
    vt = p.v(E, 'elezioni', e21, 'city', 'vt')
    aff = p.calc('round(p[1]/p[0]*100, 1)')
    nonv = p.calc('round(100-p[1]/p[0]*100, 1)')
    nvot = p.v(E, 'elezioni', e21, 'city', 'vt')
    out.append(vf(p, id='elez-2021-meta', pagina='elezioni', diff='facile',
        affermazione='Alle comunali del 2021, più della metà dei milanesi che avevano diritto di voto non è andata a votare per il sindaco.',
        vero=aff < 50, confronto=[('hanno votato', aff, 'su 100'), ('non hanno votato', nonv, 'su 100')], dec=1,
        spiega='Ha votato il 47,7% degli elettori: 491.134 su 1.029.232 aventi diritto. Più della metà è rimasta a casa.',
        anno='2021', fonte=FE, licenza='CC BY'))

    # --- Il calo dell'affluenza dal 1993
    p = Prove()
    e93 = '[id=comunali_sindaco_1993-06-06]'
    el93 = p.v(E, 'elezioni', e93, 'city', 'e')
    vt93 = p.v(E, 'elezioni', e93, 'city', 'vt')
    el21 = p.v(E, 'elezioni', e21, 'city', 'e')
    vt21 = p.v(E, 'elezioni', e21, 'city', 'vt')
    a93 = p.calc('round(p[1]/p[0]*100, 1)')
    a21 = p.calc('round(p[3]/p[2]*100, 1)')
    cal = p.calc('round(p[1]/p[0]*100-p[3]/p[2]*100, 1)')
    e16 = '[id=comunali_sindaco_2016-06-05]'
    el16 = p.v(E, 'elezioni', e16, 'city', 'e')
    vt16 = p.v(E, 'elezioni', e16, 'city', 'vt')
    a16 = p.calc('round(p[5]/p[4]*100, 1)')
    out.append(numero(p, id='affluenza-calo-1993', pagina='elezioni', diff='media',
        domanda='Alle comunali del 1993 ha votato il 78% dei milanesi, nel 2021 meno della metà. Di quanti punti percentuali è scesa l’affluenza?',
        v=cal, lo=0, hi=60, passo=1, unita='punti', dec=1,
        confronto=[('affluenza 2021', a21, '%'), ('affluenza 1993', a93, '%')],
        spiega='Dal 78,2% al 47,7%: circa 30 punti in meno. Nel 2016 aveva votato il 54,7%.',
        anno='1993, 2016 e 2021', fonte=FE, licenza='CC BY'))

    # --- Primo sindaco eletto direttamente
    p = Prove()
    y = p.v(E, 'elezioni', '[id=comunali_sindaco_1993-06-06]', 'anno')
    out.append(anno_q(p, id='sindaco-diretto-anno', pagina='elezioni', diff='media',
        domanda='In che anno i milanesi hanno scelto per la prima volta il sindaco con il voto diretto, invece di lasciarlo scegliere al consiglio comunale?',
        v=y, lo=1946, hi=2021,
        spiega='Nel 1993: vinse Marco Formentini, della Lega Nord, al ballottaggio contro Nando Dalla Chiesa. Prima il sindaco veniva scelto dai consiglieri.',
        anno='1993', fonte=FE, licenza='CC BY'))

    # --- Sindaci: età e durata
    SI = 'amministratori/data/sindaci_milano.csv'
    FA = 'Wikipedia e Wikidata, i sindaci di Milano dal 1946'
    p = Prove()
    to = p.v(SI, ix(SI, sindaco='Carlo Tognoli'), 'eta_inizio')
    ca = p.v(SI, ix(SI, sindaco='Gino Cassinis'), 'eta_inizio')
    assert to == min(r['eta_inizio'] for r in carica(SI)) and ca == max(r['eta_inizio'] for r in carica(SI))
    out.append(numero(p, id='sindaco-piu-giovane', pagina='amministratori', diff='difficile',
        domanda='Carlo Tognoli, socialista, è il sindaco più giovane di Milano dal 1946. Quanti anni aveva quando ha cominciato?',
        v=to, lo=20, hi=80, passo=1, unita='anni',
        confronto=[('Gino Cassinis, il più anziano', ca, 'anni'), ('Carlo Tognoli, il più giovane', to, 'anni')],
        spiega='Aveva 38 anni, e fece il sindaco per quasi undici anni. Il più anziano fu Gino Cassinis, scelto a 76 anni: morì in carica dopo tre anni.',
        anno='1946–2026', fonte=FA, licenza='CC BY-SA 4.0'))

    p = Prove()
    tutti = p.v(SI)
    nsind = p.calc('len(p[0])')
    dt = p.v(SI, ix(SI, sindaco='Carlo Tognoli'), 'durata_anni')
    da = p.v(SI, ix(SI, sindaco='Gabriele Albertini'), 'durata_anni')
    dm = p.v(SI, ix(SI, sindaco='Letizia Moratti'), 'durata_anni')
    out.append(ordine(p, id='sindaci-durata', pagina='amministratori', diff='media',
        domanda='Quanto sono rimasti in carica questi tre sindaci di Milano? Mettili in ordine, dal più lungo al più breve.',
        elementi=[('Letizia Moratti', dm, 'anni'), ('Carlo Tognoli', dt, 'anni'), ('Gabriele Albertini', da, 'anni')], unita='anni', dec=1,
        spiega='Tognoli è stato sindaco 10,6 anni, Albertini 9,0 e Moratti 5,0. Dal 1946 Milano ha avuto 13 sindaci, e una sola donna: Moratti.',
        anno='1946–2026', fonte=FA, licenza='CC BY-SA 4.0'))

    # --- Voto e reddito
    V = 'voto-reddito/data/vr2_coalizioni.json'
    FV = 'Comune di Milano, voti per sezione; Ministero dell’Economia e delle Finanze, redditi per CAP'
    p = Prove()
    ric = p.v(V, 'el', '[4]', 'cs', 'dec', '[9]')
    pov = p.v(V, 'el', '[4]', 'cs', 'dec', '[0]')
    assert carica(V)['el'][4]['id'].startswith('comunali_consiglio_2021')
    out.append(piuomeno(p, id='voto-ricchi-2021', pagina='voto-reddito', diff='media',
        domanda='Alle comunali del 2021 il centrosinistra ha preso più voti (in percentuale) tra gli elettori delle zone più ricche o tra quelli delle zone più povere di Milano?',
        a=('zone più ricche (un decimo degli elettori)', ric, '%'), b=('zone più povere (un decimo degli elettori)', pov, '%'), dec=1,
        spiega='Nelle zone più ricche il centrosinistra ha preso il 65,1% dei voti, nelle più povere il 51,4%. Reddito e voto vanno insieme, ma non vuol dire che uno causi l’altro.',
        anno='2021', fonte=FV, licenza='CC BY'))

    p = Prove()
    ric = p.v(V, 'el', '[7]', 'cs', 'dec', '[9]')
    pov = p.v(V, 'el', '[7]', 'cs', 'dec', '[0]')
    assert carica(V)['el'][7]['id'].startswith('europee_2024')
    out.append(vf(p, id='voto-ricchi-europee24', pagina='voto-reddito', diff='difficile',
        affermazione='Alle elezioni europee del 2024 il centrosinistra ha preso più voti nelle zone ricche di Milano che in quelle povere.',
        vero=ric > pov, confronto=[('zone più povere', pov, '%'), ('zone più ricche', ric, '%')], dec=1,
        spiega='Il contrario: 35,9% nelle zone più ricche e 42,1% nelle più povere. Tre anni prima, alle comunali, era andata al rovescio.',
        anno='2024', fonte=FV, licenza='CC BY'))

    p = Prove()
    ric = p.v(V, 'el', '[5]', 'af', 'dec', '[9]')
    pov = p.v(V, 'el', '[5]', 'af', 'dec', '[0]')
    assert carica(V)['el'][5]['id'].startswith('camera_2022')
    out.append(piuomeno(p, id='voto-affluenza-2022', pagina='voto-reddito', diff='facile',
        domanda='Alle elezioni politiche del 2022 è andata a votare una quota più alta di persone nelle zone più ricche o in quelle più povere di Milano?',
        a=('zone più ricche (un decimo degli elettori)', ric, '%'), b=('zone più povere (un decimo degli elettori)', pov, '%'), dec=1,
        spiega='Hanno votato 74 su 100 nelle zone più ricche e 62,7 su 100 nelle più povere: più di undici punti di distanza.',
        anno='2022', fonte=FV, licenza='CC BY'))
    return out


# ====================================================================== SICUREZZA
def sicurezza():
    out = []

    # --- Denunce per abitante: Milano non è prima
    G = 'reati/data/grandi_comuni.json'
    g24 = carica(G)['per_anno']['2024']
    iM = [i for i, x in enumerate(g24) if x['nome'] == 'Milano'][0]
    iF = [i for i, x in enumerate(g24) if x['nome'] == 'Firenze'][0]
    p = Prove()
    m = p.v(G, 'per_anno', '2024', '[%d]' % iM, 'tasso')
    f = p.v(G, 'per_anno', '2024', '[%d]' % iF, 'tasso')
    rg = p.v(G, 'per_anno', '2024', '[%d]' % iM, 'rango')
    out.append(vf(p, id='denunce-milano-prima', pagina='reati', diff='media',
        affermazione='Nel 2024, tra i dodici comuni italiani più grandi, Milano è la città con più denunce di reati in rapporto agli abitanti.',
        vero=rg == 1, confronto=[('Milano', m, 'ogni 100.000 abitanti'), ('Firenze', f, 'ogni 100.000 abitanti')], dec=0,
        spiega='Milano è seconda: 10.343 denunce ogni 100.000 abitanti contro le 11.422 di Firenze. Nel 2006 era prima. Le denunce non sono i reati: dove ci si fida di più, si denuncia di più.',
        anno='2006 e 2024', fonte='ISTAT e Ministero dell’Interno, reati denunciati nei grandi comuni', licenza='CC BY'))

    S = 'reati/data/serie_totale.json'
    p = Prove()
    a06 = p.v(S, 'tasso', 'milano_comune', '[0]')
    a24 = p.v(S, 'tasso', 'milano_comune', '[-1]')
    cal = p.calc('round((1-p[1]/p[0])*100, 1)')
    out.append(numero(p, id='denunce-calo-2006', pagina='reati', diff='media',
        domanda='Dal 2006 al 2024 le denunce di reati a Milano, in rapporto agli abitanti, sono diminuite. Di quanto, su 100?',
        v=cal, lo=0, hi=60, passo=1, unita='%', dec=1,
        confronto=[('2006', a06, 'ogni 100.000 abitanti'), ('2024', a24, 'ogni 100.000 abitanti')],
        spiega='Da 13.025 a 10.343 denunce ogni 100.000 abitanti: un quinto in meno. Il calo più forte è del 2020, l’anno dei lockdown.',
        anno='2006–2024', fonte='ISTAT e Ministero dell’Interno, reati denunciati', licenza='CC BY'))

    # --- Omicidi
    O = 'omicidi/data/comune_milano_2004_2024.csv'
    p = Prove()
    o04 = p.v(O, ix(O, anno=2004), 'omicidi')
    o24 = p.v(O, ix(O, anno=2024), 'omicidi')
    out.append(numero(p, id='omicidi-comune-2024', pagina='omicidi', diff='facile',
        domanda='Quanti omicidi sono stati denunciati nel 2024 nel Comune di Milano?',
        v=o24, lo=0, hi=60, passo=1, unita='omicidi',
        confronto=[('2004', o04, 'omicidi'), ('2024', o24, 'omicidi')],
        spiega='Sei in tutto l’anno, in una delle città più grandi d’Italia. Nel 2004 erano 22: oggi sono meno di un terzo.',
        anno='2004 e 2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY'))

    # --- Violenza politica: gli anni di piombo
    VP = 'violenza-politica/data/eventi.csv'
    ev = carica(VP)
    p = Prove()
    for i in range(len(ev)):
        p.v(VP, '[%d]' % i, 'anno')
    n = len(ev)
    nip = p.calc('+'.join('(1969<=p[%d]<=1982)' % i for i in range(n)))
    nres = p.calc('len(p)-(%s)' % '+'.join('(1969<=p[%d]<=1982)' % i for i in range(n)))
    assert (nip, nres) == (43, 41), (nip, nres)
    out.append(piuomeno(p, id='piombo-eventi', pagina='violenza-politica', diff='difficile',
        domanda='Stragi, attentati e omicidi politici a Milano dal 1919 al 2019, secondo Wikipedia: più negli anni di piombo (1969-1982) o in tutti gli altri anni del secolo messi insieme?',
        a=('anni di piombo, 1969-1982', nip, 'eventi'), b=('tutti gli altri anni, 1919-2019', nres, 'eventi'),
        spiega='Nei soli quattordici anni di piombo gli eventi sono 43, contro 41 in tutti gli altri anni. Non è un elenco completo: ci sono solo i fatti che hanno una voce su Wikipedia.',
        anno='1919–2019', fonte='Wikipedia e Wikidata, violenza politica a Milano', licenza='CC BY-SA 4.0'))
    return out


# ====================================================================== CASA
def casa():
    out = []

    # --- Il metro quadro più caro e il più economico
    Z = 'prezzi-case/data/zone_ultimo_semestre.csv'
    righe = [r for r in carica(Z) if isinstance(r.get('compr_centro'), (int, float))]
    mx = max(righe, key=lambda r: r['compr_centro'])
    mn = min(righe, key=lambda r: r['compr_centro'])
    assert mx['zona'] == 'C14' and mn['zona'] == 'E8'
    p = Prove()
    a = p.v(Z, ix(Z, zona='C14'), 'compr_centro')
    b = p.v(Z, ix(Z, zona='E8'), 'compr_centro')
    rt = p.calc('round(p[0]/p[1], 1)')
    ca60 = p.calc('round(p[0]*60)')
    ec60 = p.calc('round(p[1]*60)')
    out.append(numero(p, id='casa-zona-cara-economica', pagina='prezzi-case', diff='media',
        domanda='Comprare casa a Porta Nuova (la zona più cara) costa quante volte di più, al metro quadro, che a Quarto Oggiaro e Sacco (la zona più economica)?',
        v=rt, lo=1, hi=15, passo=0.1, unita='volte', dec=1,
        confronto=[('Quarto Oggiaro, Sacco', b, '€ al m²'), ('Porta Nuova', a, '€ al m²')],
        spiega='A Porta Nuova si pagano in media 13.100 euro al metro quadro, a Quarto Oggiaro e Sacco 2.350: 5,6 volte tanto. Una casa di sessanta metri quadri costa 786.000 euro da una parte e 141.000 dall’altra.',
        anno='1° sem. 2026', fonte='Agenzia delle Entrate, Osservatorio del mercato immobiliare (OMI)', licenza='CC BY'))

    p = Prove()
    an = p.v(Z, ix(Z, zona='B12'), 'anni_di_affitto')
    out.append(numero(p, id='casa-anni-affitto-centro', pagina='prezzi-case', diff='facile',
        domanda='Nel centro storico, intorno al Duomo e a Montenapoleone, quanti anni di affitto servono per pagare una casa che si compra? (Si parte dal prezzo medio di acquisto e dall’affitto medio.)',
        v=an, lo=5, hi=60, passo=0.5, unita='anni', dec=1,
        spiega='Servono 27,5 anni di affitto: un proprietario che affittasse la casa incasserebbe ogni anno meno del 4% del suo valore.',
        anno='1° sem. 2026', fonte='Agenzia delle Entrate, Osservatorio del mercato immobiliare (OMI)', licenza='CC BY'))

    # --- Case popolari
    CP = 'case-popolari/data/riepilogo.json'
    FP = 'Comune di Milano, ALER e Regione Lombardia, alloggi di edilizia residenziale pubblica; ISTAT, abitazioni'
    p = Prove()
    q = p.v(CP, 'stock', 'quota_pct', '2023')
    tot = p.v(CP, 'stock', 'tot')
    nc = p.v(CP, 'stock', 'comune')
    na = p.v(CP, 'stock', 'aler')
    nab = p.v(CP, 'stock', 'abitazioni', '2023')
    q11 = p.v(CP, 'stock', 'quota_pct', '2011')
    out.append(numero(p, id='popolari-quota', pagina='case-popolari', diff='facile',
        domanda='Su 100 case di Milano, quante sono alloggi popolari del Comune o dell’ALER?',
        v=q, lo=0, hi=30, passo=0.5, unita='su 100', dec=1,
        spiega='Sono 7,1 su 100: 59.054 alloggi (26.010 del Comune e 33.044 dell’ALER) su 827.648 abitazioni. Nel 2011 erano 9,2 su 100.',
        anno='2023–2026', fonte=FP, licenza='CC BY'))

    p = Prove()
    vp = p.v(CP, 'snapshot', 'vuoti_pct')
    cp = p.v(CP, 'snapshot', 'comune_pct')
    ap = p.v(CP, 'snapshot', 'aler_pct')
    nv = p.v(CP, 'snapshot', 'vuoti')
    nt = p.v(CP, 'snapshot', 'totale')
    out.append(numero(p, id='popolari-vuoti', pagina='case-popolari', diff='difficile',
        domanda='A marzo 2023, su 100 alloggi popolari di Comune e ALER a Milano, quanti erano vuoti, cioè senza nessuno dentro?',
        v=vp, lo=0, hi=50, passo=0.5, unita='su 100', dec=1,
        confronto=[('ALER', ap, 'su 100'), ('Comune', cp, 'su 100')],
        spiega='Erano vuoti 8.420 alloggi su 58.506: 14,4 su 100. Nelle case del Comune la quota è più alta (17,9 su 100) che in quelle dell’ALER (11,5).',
        anno='marzo 2023', fonte=FP, licenza='CC BY'))

    FV_ = 'case-vuote/data/fasce_distanza_anni.csv'
    p = Prove()
    c0 = p.v(FV_, ix(FV_, anno=2023, fascia_distanza_dal_Duomo_centroide_quartiere='0-2 km'), 'quota_non_occupate')
    c6 = p.v(FV_, ix(FV_, anno=2023, fascia_distanza_dal_Duomo_centroide_quartiere='oltre 6 km'), 'quota_non_occupate')
    cn = p.v(FV_, ix(FV_, anno=2023, fascia_distanza_dal_Duomo_centroide_quartiere='0-2 km'), 'non_occupate_da_residenti')
    ct = p.v(FV_, ix(FV_, anno=2023, fascia_distanza_dal_Duomo_centroide_quartiere='0-2 km'), 'abitazioni')
    c0r = p.calc('round(p[0], 1)')
    c6r = p.calc('round(p[1], 1)')
    out.append(vf(p, id='centro-case-senza-residenti', pagina='case-vuote', diff='facile',
        affermazione='Nel 2023, entro due chilometri dal Duomo, più di una casa su quattro non aveva nessun residente.',
        vero=c0 > 25, confronto=[('oltre 6 km dal Duomo', c6r, 'su 100'), ('entro 2 km dal Duomo', c0r, 'su 100')], dec=1,
        spiega='Sono 30.795 case su 113.859: 27 su 100. Oltre sei chilometri dal Duomo sono solo 6 su 100. «Senza residenti» non vuol dire per forza vuota: può essere una seconda casa, uno studio, una casa per turisti.',
        anno='2023', fonte='ISTAT, censimento permanente della popolazione e delle abitazioni', licenza='CC BY'))
    return out


# ====================================================================== SERVIZI
def servizi():
    out = []

    # --- Biblioteche: Geronimo Stilton
    T = 'biblioteche/data/top_autori_anno.csv'
    p = Prove()
    rk = []
    for y in range(2013, 2025):
        rk.append(p.v(T, ix(T, anno=y, fascia_utente='tutti', autore='Stilton, Geronimo'), 'rango'))
    n1 = p.calc('+'.join('(p[%d]==1)' % i for i in range(len(rk))))
    pr24 = p.v(T, ix(T, anno=2024, fascia_utente='tutti', rango=1), 'prestiti')
    pr24b = p.v(T, ix(T, anno=2024, fascia_utente='tutti', rango=2), 'prestiti')
    assert n1 == 10, n1
    out.append(numero(p, id='stilton-primo', pagina='biblioteche', diff='media',
        domanda='Negli ultimi dodici anni, dal 2013 al 2024, in quanti anni l’autore più prestato dalle biblioteche del Comune di Milano è stato Geronimo Stilton, il topo giornalista dei libri per ragazzi?',
        v=n1, lo=0, hi=12, passo=1, unita='anni su 12',
        spiega='In dieci anni su dodici. Negli altri due è stato secondo. Nel 2024 ha avuto 2.997 prestiti, davanti a Maurizio De Giovanni (1.957).',
        anno='2013–2024', fonte='Comune di Milano, prestiti delle biblioteche rionali', licenza='CC BY'))

    # --- Telefoni pubblici
    TP = 'telefoni-pubblici/data/pagina.json'
    p = Prove()
    n = p.v(TP, 'milano', 'telefoni')
    rm = p.v(TP, 'citta', '[0]', 'telefoni')
    quota = p.v(TP, 'milano', 'quota_su_italia')
    assert carica(TP)['citta'][0]['nome'] == 'Roma'
    out.append(numero(p, id='telefoni-pubblici-milano', pagina='telefoni-pubblici', diff='facile',
        domanda='Quanti telefoni pubblici, le vecchie cabine con la tessera, ci sono ancora a Milano?',
        v=n, lo=0, hi=2000, passo=10, unita='telefoni',
        confronto=[('Roma', rm, 'telefoni'), ('Milano', n, 'telefoni')],
        spiega='Sono ancora 627 nell’elenco di TIM: il 6,3% di quelli di tutta Italia. In rapporto agli abitanti Milano ne ha più di Roma, che ne ha 772 ma il doppio degli abitanti.',
        anno='2026', fonte='TIM, elenco dei telefoni pubblici', licenza='Uso con citazione, non aperta'))

    # --- Telefoni pubblici per abitante
    p = Prove()
    pm = p.v(TP, 'milano', 'per_10000')
    pr = p.v(TP, 'citta', '[0]', 'per_10000')
    assert carica(TP)['citta'][0]['nome'] == 'Roma'
    tm = p.v(TP, 'milano', 'telefoni')
    trm = p.v(TP, 'citta', '[0]', 'telefoni')
    out.append(piuomeno(p, id='telefoni-per-abitante', pagina='telefoni-pubblici', diff='facile',
        domanda='I telefoni pubblici rimasti in Italia: in rapporto agli abitanti, ce ne sono di più a Milano o a Roma?',
        a=('Milano', pm, 'telefoni ogni 10.000 abitanti'), b=('Roma', pr, 'telefoni ogni 10.000 abitanti'), dec=1,
        spiega='A Milano sono 4,6 ogni 10.000 abitanti, a Roma 2,8. In numero assoluto Roma ne ha di più (772 contro 627), ma ha il doppio degli abitanti.',
        anno='2026', fonte='TIM, elenco dei telefoni pubblici; ISTAT, popolazione', licenza='Uso con citazione, non aperta'))

    # --- Tempo pieno alle elementari
    TPI = 'poverta-educativa/data/tempo_pieno_primaria_citta_serie.csv'
    p = Prove()
    m = p.v(TPI, ix(TPI, anno=2024, citta='Milano', gestione='statale'), 'tempo_pieno_pct')
    ro = p.v(TPI, ix(TPI, anno=2024, citta='Roma', gestione='statale'), 'tempo_pieno_pct')
    na = p.v(TPI, ix(TPI, anno=2024, citta='Napoli', gestione='statale'), 'tempo_pieno_pct')
    it = p.v(TPI, ix(TPI, anno=2024, citta='Italia', gestione='statale'), 'tempo_pieno_pct')
    out.append(ordine(p, id='tempo-pieno-statali', pagina='poverta-educativa', diff='facile',
        domanda='Quanti bambini delle elementari statali fanno il tempo pieno (lezioni anche al pomeriggio, con la mensa)? Metti in ordine queste tre città, dalla più alta alla più bassa.',
        elementi=[('Napoli', na, 'su 100'), ('Milano', m, 'su 100'), ('Roma', ro, 'su 100')], unita='su 100', dec=1,
        spiega='A Milano fa il tempo pieno il 96,8% dei bambini, il valore più alto tra le grandi città; a Roma l’88,9% e a Napoli il 34,9%. In Italia le statali sono ferme al 44%.',
        anno='2024', fonte='Ministero dell’Istruzione e del Merito, alunni delle scuole primarie', licenza='IODL 2.0'))
    return out
