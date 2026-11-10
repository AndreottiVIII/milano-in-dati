"""Domande del modulo b_persone: popolazione, nascite, morti, casa, soldi, lavoro."""
from mazzo import (Prove, carica, piuomeno, numero, vf, ordine, anno_q, serie_da, primo_sorpasso)

CC = 'CC BY 4.0'
CITAZ = 'uso con citazione, non aperta'


def ix(rel, **cond):
    """Posizione (nel file) della prima riga che soddisfa tutte le condizioni."""
    for i, r in enumerate(carica(rel)):
        if all(str(r.get(k)) == str(v) for k, v in cond.items()):
            return '[%d]' % i
    raise KeyError((rel, cond))


def domande():
    out = []

    # ------------------------------------------------------------------ CENSIMENTI
    f = 'censimenti/data/dati.json'
    p = Prove()
    anni = [1951, 1961, 1971, 1981, 1991, 2001, 2011, 2021, 2023]
    vals = []
    for y in anni:
        k = 'r' if y <= 1991 else 'a'
        vals.append(p.v(f, 'storia', '[y=%d]' % y, k))
    top = anni[vals.index(max(vals))]
    assert top == 1971
    top = p.v(f, 'storia', '[y=1971]', 'y')
    out.append(anno_q(p, id='censi-picco', pagina='censimenti', diff='media',
        domanda='In che anno Milano ha avuto più abitanti nella sua storia (secondo i censimenti)?',
        v=top, lo=1951, hi=2011,
        spiega='Nel 1971 i residenti erano 1,73 milioni. Poi la città ne ha persi quasi mezzo milione e nel 2023 è tornata a 1,37 milioni.',
        anno='1951–2023', fonte='ISTAT e Comune di Milano, censimenti della popolazione', licenza=CC,
        serie=serie_da(anni, [('Residenti', vals)])))

    p = Prove()
    p23 = p.v(f, 'comune', 'pop', '[4]')
    p91 = p.v(f, 'comune', 'pop', '[0]')
    out.append(vf(p, id='censi-1991-2023', pagina='censimenti', diff='difficile',
        affermazione='Nel 2023 Milano ha più residenti di quanti ne aveva nel 1991.',
        vero=p23 > p91, confronto=[('1991', p91, 'residenti'), ('2023', p23, 'residenti')],
        spiega='Sono quasi uguali: 1.371.499 contro 1.369.231. Ma le famiglie sono molte di più, perché tante persone vivono sole.',
        anno='1991–2023', fonte='ISTAT e Comune di Milano, censimenti della popolazione', licenza=CC))

    p = Prove()
    s23 = p.v(f, 'comune', 'fam1_n', '[4]')
    t23 = p.v(f, 'comune', 'fam_n', '[4]')
    s91 = p.v(f, 'comune', 'fam1_n', '[0]')
    t91 = p.v(f, 'comune', 'fam_n', '[0]')
    q23 = p.calc('round(p[0]/p[1]*100, 1)')
    q91 = p.calc('round(p[2]/p[3]*100, 1)')
    out.append(numero(p, id='censi-sole', pagina='censimenti', diff='facile',
        domanda='Nel 2023, che quota delle famiglie di Milano è composta da una sola persona?',
        v=q23, lo=20, hi=80, passo=1, unita='%', dec=1,
        confronto=[('1991', q91, '%'), ('2023', q23, '%')],
        spiega='Più della metà: 55,6%. Nel 1991 era il 32,0%. Le famiglie di una persona sola sono più che raddoppiate.',
        anno='1991–2023', fonte='ISTAT, censimenti della popolazione; Comune di Milano', licenza=CC))

    # ------------------------------------------------------------------ ETÀ
    f = 'eta/data/citta_eta_centenari.csv'
    p = Prove()
    a65 = p.v(f, '[anno=2025]', 'quota_65_pct')
    a14 = p.v(f, '[anno=2025]', 'quota_0_14_pct')
    a80 = p.v(f, '[anno=2025]', 'quota_80_pct')
    out.append(ordine(p, id='eta-quote-2025', pagina='eta', diff='facile',
        domanda='Quota di residenti di Milano nel 2025. Dalla più alta alla più bassa:',
        elementi=[('Over 80', a80, '%'), ('Bambini fino a 14 anni', a14, '%'), ('Over 65 (compresi gli over 80)', a65, '%')],
        unita='%', dec=1,
        spiega='Gli anziani (sopra i sessantacinque anni) sono più di uno su cinque, i bambini uno su nove. Gli over 80, da soli, sono uno su dodici.',
        anno='2025', fonte='Comune di Milano, residenti per età (31 dicembre)', licenza=CC))

    p = Prove()
    d99 = p.v(f, '[anno=1999]', 'centenari_donne')
    u99 = p.v(f, '[anno=1999]', 'centenari_uomini')
    d25 = p.v(f, '[anno=2025]', 'centenari_donne')
    u25 = p.v(f, '[anno=2025]', 'centenari_uomini')
    c99 = p.calc('p[0]+p[1]')
    c25 = p.calc('p[2]+p[3]')
    rt = p.calc('round((p[2]+p[3])/(p[0]+p[1]), 1)')
    out.append(vf(p, id='eta-centenari', pagina='eta', diff='facile',
        affermazione='A Milano i centenari sono oggi più di quattro volte quelli del 1999.',
        vero=c25 > 4 * c99, confronto=[('1999', c99, 'centenari'), ('2025', c25, 'centenari')],
        spiega='Erano 249 nel 1999 e sono 835 nel 2025: 3,4 volte tanti. Più di otto su dieci sono donne: 717 contro 118 uomini.',
        anno='1999–2025', fonte='Comune di Milano, residenti per età (31 dicembre)', licenza=CC))

    # ------------------------------------------------------------------ COMUNITÀ
    f = 'comunita/data/riepilogo.json'
    p = Prove()
    n03 = p.v(f, 'naturalizzazioni', '2003')
    n24 = p.v(f, 'naturalizzazioni', '2024')
    n23 = p.v(f, 'naturalizzazioni', '2023')
    n16 = p.v(f, 'naturalizzazioni', '2016')
    altri = [carica(f)['naturalizzazioni'][str(y)] for y in range(2003, 2024)]
    out.append(vf(p, id='comu-cittadinanze', pagina='comunita', diff='media',
        affermazione='Nel 2024 hanno ottenuto la cittadinanza italiana più stranieri residenti a Milano che in ogni altro anno dal 2003.',
        vero=n24 > max(altri), confronto=[('2016', n16, 'cittadinanze'), ('2023', n23, 'cittadinanze'), ('2024', n24, 'cittadinanze')],
        spiega='Il record è del 2024, con 9.021 nuovi italiani. Nel 2003 erano 730. Negli ultimi anni gli egiziani sono il gruppo più numeroso.',
        anno='2003–2024', fonte='Comune di Milano, acquisizioni di cittadinanza italiana', licenza=CC))

    p = Prove()
    eg = p.v(f, 'naturalizzazioni_per_cittadinanza_2021_2024', 'Egitto')
    fi = p.v(f, 'naturalizzazioni_per_cittadinanza_2021_2024', 'Filippine')
    pe = p.v(f, 'naturalizzazioni_per_cittadinanza_2021_2024', 'Perù')
    out.append(ordine(p, id='comu-ordine-cittadinanze', pagina='comunita', diff='facile',
        domanda='Dal 2021 al 2024, chi ha preso più cittadinanze italiane a Milano? Dal più al meno:',
        elementi=[('Perù', pe, 'cittadinanze'), ('Egitto', eg, 'cittadinanze'), ('Filippine', fi, 'cittadinanze')],
        unita='', spiega='Gli egiziani sono quasi il doppio dei filippini.',
        anno='2021–2024', fonte='Comune di Milano, acquisizioni di cittadinanza italiana', licenza=CC))

    p = Prove()
    nat = p.v(f, 'naturalizzazioni', '2024')
    nati = p.v('nascite/data/serie_1880_2024.csv', '[anno=2024]', 'nati')
    out.append(piuomeno(p, id='comu-cittadini-o-nati', pagina='comunita', diff='difficile',
        domanda='Nel 2024 a Milano sono nati più bambini o più stranieri residenti sono diventati italiani?',
        a=('bambini nati nel 2024', nati, ''), b=('nuovi cittadini italiani nel 2024', nat, ''),
        spiega='Quasi pari: 9.147 nati contro 9.021 nuove cittadinanze. Basta poco per sorpassare le nascite.',
        anno='2024', fonte='Comune di Milano, nati e acquisizioni di cittadinanza', licenza=CC))

    # ------------------------------------------------------------------ NASCITE
    f = 'nascite/data/serie_1880_2024.csv'
    p = Prove()
    anni = list(range(1950, 1990))
    nn = [p.v(f, '[anno=%d]' % y, 'nati') for y in anni]
    rec = anni[nn.index(max(nn))]
    assert rec == 1964 and max(nn) == max(r['nati'] for r in carica(f))
    rec = p.v(f, '[anno=1964]', 'anno')
    ab64 = p.v(f, '[anno=1964]', 'abitanti')
    out.append(anno_q(p, id='nati-record', pagina='nascite', diff='media',
        domanda='In che anno sono nati più bambini a Milano, da quando ci sono i dati (1880)?',
        v=rec, lo=1950, hi=1985,
        spiega='Nel 1964 i nati furono 27.427, tre volte quelli di oggi. Era il picco del boom: la città contava 1,67 milioni di abitanti.',
        anno='1880–2024', fonte='Comune di Milano, nati e morti dal 1880', licenza=CC,
        serie=serie_da(anni, [('Nati', nn)])))

    p = Prove()
    nati = p.v(f, '[anno=2024]', 'nati')
    morti = p.v(f, '[anno=2024]', 'morti_ds71')
    assert all(r['nati'] < r['morti_ds71'] for r in carica(f) if r['anno'] >= 1976)
    out.append(piuomeno(p, id='nati-o-morti-2024', pagina='nascite', diff='facile',
        domanda='A Milano, nel 2024, sono nati più bambini o sono morte più persone?',
        a=('nati nel 2024', nati, ''), b=('morti nel 2024', morti, ''),
        spiega='Sono 13.782 morti contro 9.147 nati. Da decenni i morti superano i nati: il vuoto lo colma chi arriva da fuori.',
        anno='2024', fonte='Comune di Milano, nati e morti dal 1880', licenza=CC))

    p = Prove()
    q21 = p.v('nascite/data/tfr_citta_2021_2024.csv', '[anno=2021]', 'quota_madre_35_piu_pct')
    q24 = p.v('nascite/data/tfr_citta_2021_2024.csv', '[anno=2024]', 'quota_madre_35_piu_pct')
    out.append(numero(p, id='nati-madri-35', pagina='nascite', diff='media',
        domanda='Nel 2024, che quota dei bambini nati a Milano ha una mamma con almeno trentacinque anni?',
        v=q24, lo=20, hi=70, passo=1, unita='%', dec=1,
        confronto=[('2021', q21, '%'), ('2024', q24, '%')],
        spiega='Quasi uno su due: 49,4%. Nel 2021 erano il 47,4%. Le madri di Milano diventano tali sempre più tardi.',
        anno='2021–2024', fonte='Comune di Milano, nati per età della madre', licenza=CC))

    # ------------------------------------------------------------------ MORTI
    f = 'morti/data/estati_confronto.csv'
    p = Prove()
    anni = list(range(2014, 2026))
    gg = [p.v(f, '[anno=%d]' % y, 'giorni_tx_ge33') for y in anni]
    assert gg.count(max(gg)) == 1
    rec = anni[gg.index(max(gg))]
    assert rec == 2015
    rec = p.v(f, '[anno=2015]', 'anno')
    pc22 = p.v(f, '[anno=2022]', 'pct_B')
    pc24 = p.v(f, '[anno=2024]', 'pct_B')
    out.append(anno_q(p, id='morti-estate-caldo', pagina='morti', diff='difficile',
        domanda='Dal 2014 al 2025, in che estate a Milano (Brera) ci sono stati più giorni con almeno 33 °C?',
        v=rec, lo=2012, hi=2026,
        spiega='Il 2015, con 35 giorni; il 2024 ne ha avuti 34 e il 2022 33. Effetti diversi: nel 2022 i morti furono il 15,2% sopra il normale, nel 2024 il 4,1% sotto.',
        anno='2014–2025', fonte='ISTAT, decessi giornalieri; temperature di Brera', licenza=CC,
        serie=serie_da(anni, [('Giorni con almeno 33 °C', gg)])))

    f = 'morti/data/annuale.csv'
    p = Prove()
    righe = {y: p.v(f, ix(f, scope='Milano', anno=y), 'morti') for y in range(2014, 2026)}
    m25 = righe[2025]
    m20 = p.v(f, ix(f, scope='Milano', anno=2020), 'morti')
    for y in (2014, 2019, 2024, 2025):
        p.v(f, ix(f, scope='Milano', anno=y), 'anno')
    p.v(f, ix(f, scope='Milano', anno=2020), 'anno')
    altri = [v for y, v in righe.items() if y != 2025]
    out.append(vf(p, id='morti-2025-minimo', pagina='morti', diff='media',
        affermazione='Nel 2025 sono morti meno milanesi residenti che in ogni altro anno dal 2014.',
        vero=m25 < min(altri),
        confronto=[('2014', righe[2014], 'morti'), ('2019', righe[2019], 'morti'), ('2024', righe[2024], 'morti'), ('2025', m25, 'morti')],
        spiega='Sono 13.639 morti nel 2025. Nell’anno del Covid erano arrivati a 18.487.',
        anno='2014–2025', fonte='ISTAT, decessi giornalieri per comune di residenza', licenza=CC))

    # ------------------------------------------------------------------ MATRIMONI
    f = 'matrimoni/data/riepilogo.json'
    p = Prove()
    anni = list(range(1985, 2025))
    civ = [p.v(f, 'rito', '[a=%d]' % y, 'civ') for y in anni]
    rel = [p.v(f, 'rito', '[a=%d]' % y, 'rel') for y in anni]
    tutti_a = [x['a'] for x in carica(f)['rito']]
    s = primo_sorpasso(tutti_a, [x['civ'] for x in carica(f)['rito']], [x['rel'] for x in carica(f)['rito']])
    assert s == 2002 and anni.index(s) >= 0
    s = p.v(f, 'rito', '[a=2002]', 'a')
    c63 = p.v(f, 'rito', '[a=1963]', 'civ')
    l63 = p.v(f, 'rito', '[a=1963]', 'rel')
    q63 = p.calc('round(p[-1]/p[-2])')
    out.append(anno_q(p, id='matri-sorpasso-civile', pagina='matrimoni', diff='media',
        domanda='In che anno a Milano si sono celebrati per la prima volta più matrimoni civili che religiosi?',
        v=s, lo=1985, hi=2012,
        spiega='Nel 2002: 2.502 civili contro 2.313 religiosi. Nel 1963 quelli in chiesa erano 25 volte quelli civili.',
        anno='1948–2024', fonte='Comune di Milano, matrimoni per rito dal 1948', licenza=CC,
        serie=serie_da(anni, [('Civili', civ), ('Religiosi', rel)])))

    p = Prove()
    r24 = p.v(f, 'rito', '[a=2024]', 'rel')
    r63 = p.v(f, 'rito', '[a=1963]', 'rel')
    rat = p.calc('round(p[1]/p[0])')
    out.append(numero(p, id='matri-chiesa-2024', pagina='matrimoni', diff='difficile',
        domanda='Nel 2024, quanti matrimoni in chiesa (rito religioso) sono stati celebrati a Milano?',
        v=r24, lo=50, hi=2000, passo=10, unita='', dec=0,
        confronto=[('1963', r63, 'matrimoni'), ('2024', r24, 'matrimoni')],
        spiega='Appena 474. Nel 1963 erano 11.929: più di 25 volte tanti. Oggi più di otto matrimoni su dieci sono civili.',
        anno='1963–2024', fonte='Comune di Milano, matrimoni per rito dal 1948', licenza=CC))

    # ------------------------------------------------------------------ SPERANZA DI VITA
    f = 'speranza-vita/data/riepilogo.json'
    p = Prove()
    ef = p.v(f, 'citta', '2022-2024', 'F')
    em = p.v(f, 'citta', '2022-2024', 'M')
    out.append(
        numero(p, id='vita-donne', pagina='speranza-vita', diff='facile',
        domanda='A Milano, nel triennio 2022-2024, quanti anni può sperare di vivere una bambina appena nata?',
        v=ef, lo=78, hi=92, passo=0.5, unita='anni', dec=1,
        confronto=[('maschi', em, 'anni'), ('femmine', ef, 'anni')],
        spiega='Le femmine arrivano a 86,5 anni e i maschi a 82,5: una stima fatta sui decessi dei quartieri.',
        anno='2022–2024', fonte='Comune di Milano, decessi; ISTAT, residenti per età', licenza=CC))

    # ------------------------------------------------------------------ ARRIVI E PARTENZE
    f = 'arrivi-partenze/data/saldi_anno.csv'
    p = Prove()
    ii = p.v(f, '[a=2024]', 'isc_i')
    ci = p.v(f, '[a=2024]', 'canc_i')
    ie = p.v(f, '[a=2024]', 'isc_e')
    ce = p.v(f, '[a=2024]', 'canc_e')
    sal = p.calc('p[1]-p[0]')
    out.append(piuomeno(p, id='arrivi-resto-italia', pagina='arrivi-partenze', diff='media',
        domanda='Nel 2024 più persone si sono trasferite a Milano da altri comuni italiani o ne sono partite?',
        a=('arrivate da altri comuni italiani', ii, ''), b=('partite verso altri comuni italiani', ci, ''),
        spiega='Milano perde 10.222 residenti nello scambio con il resto d’Italia. Li compensa chi arriva dall’estero: 19.263 contro 6.479 partiti.',
        anno='2024', fonte='Comune di Milano e ISTAT, iscrizioni e cancellazioni anagrafiche', licenza=CC))

    # ------------------------------------------------------------------ HINTERLAND
    f = 'hinterland/data/gruppi_serie.csv'
    p = Prove()
    anni = list(range(2001, 2027))
    mi = [p.v(f, ix(f, gruppo='MILANO', anno_1_gennaio=y), 'stranieri') for y in anni]
    hi_ = [p.v(f, ix(f, gruppo='HINT', anno_1_gennaio=y), 'stranieri') for y in anni]
    s = primo_sorpasso(anni, hi_, mi)
    assert s == 2008 and all(h > m for y, h, m in zip(anni, hi_, mi) if y >= 2008)
    s = p.v(f, ix(f, gruppo='MILANO', anno_1_gennaio=2008), 'anno_1_gennaio')
    nh = p.v('hinterland/data/riepilogo.json', 'n_hint')
    qm_ = p.v('hinterland/data/riepilogo.json', 'sorprese', 'str_q_mi')
    qh_ = p.v('hinterland/data/riepilogo.json', 'sorprese', 'str_q_hint')
    out.append(anno_q(p, id='hint-sorpasso-stranieri', pagina='hinterland', diff='difficile',
        domanda='Da che anno i 187 comuni intorno a Milano hanno, tutti insieme, più stranieri residenti della città?',
        v=s, lo=2003, hi=2020,
        spiega='Dal 1° gennaio 2008. Oggi sono 316.894 contro 267.986 di Milano, ma in città gli stranieri sono il 19,7% dei residenti: nei comuni intorno l’11,4%.',
        anno='2001–2026', fonte='ISTAT, popolazione residente straniera al 1° gennaio', licenza=CC,
        serie=serie_da(anni, [('Comuni intorno a Milano', hi_), ('Milano', mi)])))

    f = 'hinterland/data/comuni.csv'
    p = Prove()
    nh = p.v('hinterland/data/riepilogo.json', 'n_hint')
    ba = p.v(f, '[comune=Basiglio]', 'reddito_medio_2024_euro')
    cu = p.v(f, '[comune=Cusago]', 'reddito_medio_2024_euro')
    mm = p.v(f, '[comune=Milano]', 'reddito_medio_2024_euro')
    out.append(vf(p, id='hint-reddito', pagina='hinterland', diff='media',
        affermazione='Tra Milano e i 187 comuni intorno, Milano è quello con il reddito medio dichiarato più alto (2024).',
        vero=mm > max(ba, cu),
        confronto=[('Basiglio', ba, '€'), ('Cusago', cu, '€'), ('Milano', mm, '€')],
        spiega='Milano è terza. Basiglio guida con 52.885 € per contribuente, poi Cusago con 43.328 €; Milano ne ha 40.316.',
        anno='2024', fonte='MEF, redditi IRPEF per comune; Comune di Milano', licenza=CC))

    p = Prove()
    bz = p.v(f, '[comune=Baranzate]', 'stranieri_2026_pc')
    pt = p.v(f, '[comune=Pioltello]', 'stranieri_2026_pc')
    ml = p.v(f, '[comune=Milano]', 'stranieri_2026_pc')
    out.append(ordine(p, id='hint-ordine-stranieri', pagina='hinterland', diff='media',
        domanda='Quota di stranieri tra i residenti (ISTAT, 1° gennaio 2026). Dalla più alta alla più bassa:',
        elementi=[('Milano', ml, '%'), ('Baranzate', bz, '%'), ('Pioltello', pt, '%')],
        unita='%', dec=1,
        spiega='A Baranzate più di un residente su tre è straniero. Solo cinque comuni intorno a Milano ne hanno una quota più alta della città.',
        anno='2026', fonte='ISTAT, popolazione residente straniera al 1° gennaio', licenza=CC))

    # ------------------------------------------------------------------ DIVISA
    f = 'divisa/data/cittadinanza_serie.csv'
    p = Prove()
    s25 = p.v(f, '[anno=2025]', 'quota_stranieri')
    s99 = p.v(f, '[anno=1999]', 'quota_stranieri')
    v25 = p.calc('round(p[0]*100, 1)')
    v99 = p.calc('round(p[1]*100, 1)')
    out.append(numero(p, id='divisa-stranieri', pagina='divisa', diff='facile',
        domanda='Nel 2025, che quota dei residenti di Milano ha una cittadinanza straniera?',
        v=v25, lo=5, hi=35, passo=0.5, unita='%', dec=1,
        confronto=[('1999', v99, '%'), ('2025', v25, '%')],
        spiega='Uno su cinque: 21,1%. Nel 1999 erano il 7,9%. Gli stranieri sono quasi triplicati in meno di trent’anni.',
        anno='1999–2025', fonte='Comune di Milano, residenti per cittadinanza (31 dicembre)', licenza=CC))

    # ------------------------------------------------------------------ BENESSERE
    f = 'benessere/data/riepilogo.json'
    p = Prove()
    ncm = p.v(f, 'meta', 'n_cm')
    fi = p.v(f, 'graduatoria', '[cm=Firenze]', 'perc')
    bo = p.v(f, 'graduatoria', '[cm=Bologna]', 'perc')
    mi_ = p.v(f, 'graduatoria', '[cm=Milano]', 'perc')
    out.append(vf(p, id='bene-prima', pagina='benessere', diff='media',
        affermazione='Tra le 14 città metropolitane italiane, Milano è prima per posizione media nelle misure di benessere.',
        vero=mi_ > max(fi, bo),
        confronto=[('Firenze', fi, ''), ('Bologna', bo, ''), ('Milano', mi_, '')],
        spiega='Milano è terza, dietro Firenze e Bologna. Vince in molte misure, ma non in tutte: la posizione media conta anche quelle in cui è indietro.',
        anno='2024', fonte='ISTAT, Bes dei territori', licenza=CC, dec=1))

    p = Prove()
    rm = p.v(f, 'graduatoria', '[cm=Roma]', 'perc')
    pa = p.v(f, 'graduatoria', '[cm=Palermo]', 'perc')
    mi_ = p.v(f, 'graduatoria', '[cm=Milano]', 'perc')
    out.append(ordine(p, id='bene-ordine', pagina='benessere', diff='facile',
        domanda='Benessere ISTAT, punteggio medio tra le 14 città metropolitane (più alto = meglio). Dal più alto al più basso:',
        elementi=[('Palermo', pa, ''), ('Milano', mi_, ''), ('Roma', rm, '')],
        unita='', dec=1,
        spiega='Milano 67,2, Roma 55,5 e Palermo 39,0 su cento: più è alto, più la città sta in alto nelle classifiche delle misure.',
        anno='2024', fonte='ISTAT, Bes dei territori', licenza=CC))

    # ------------------------------------------------------------------ PREZZI CASE
    f = 'prezzi-case/data/serie_citta.csv'
    p = Prove()
    e06 = p.v(f, '[0]', 'prezzo_mediano_euro2025_m2')
    e25 = p.v(f, '[39]', 'prezzo_mediano_euro2025_m2')
    n06 = p.v(f, '[0]', 'prezzo_mediano_nominale_eur_m2')
    n25 = p.v(f, '[39]', 'prezzo_mediano_nominale_eur_m2')
    assert carica(f)[0]['semestre'] == '2006-S1' and carica(f)[39]['semestre'] == '2025-S2'
    assert carica(f)[0]['tipologia'] == carica(f)[39]['tipologia'] == 'Abitazioni civili'
    pc = p.calc('round((p[1]/p[0]-1)*100)')
    pcn = p.calc('round((p[3]/p[2]-1)*100)')
    out.append(numero(p, id='case-prezzo-reale', pagina='prezzi-case', diff='difficile',
        domanda='Dal 2006 al 2025 di quanto è salito il prezzo mediano delle case a Milano, tolta l’inflazione?',
        v=pc, lo=0, hi=80, passo=1, unita='%', dec=0,
        confronto=[('2006, euro di oggi', e06, '€ al m²'), ('2025, euro di oggi', e25, '€ al m²')],
        spiega='Solo 19%: da 3.363 a 3.994 € al m² in euro di oggi (quotazioni OMI, zona mediana). Nei prezzi di allora, invece, da 2.400 a 4.000 €: più 67%.',
        anno='2006–2025', fonte='Agenzia delle Entrate, quotazioni OMI; ISTAT, indice dei prezzi', licenza=CC))

    # ------------------------------------------------------------------ AFFITTI BREVI
    f = 'affitti-brevi/data/notti_alberghi_extra.csv'
    p = Prove()
    q24 = p.v(f, '[anno=2024]', 'quota_extra')
    q19 = p.v(f, '[anno=2019]', 'quota_extra')
    c24 = p.calc('round(p[0]*100)')
    c19 = p.calc('round(p[1]*100)')
    out.append(numero(p, id='brevi-notti-fuori', pagina='affitti-brevi', diff='difficile',
        domanda='Nel 2024, che quota delle notti dei turisti a Milano è stata fuori dagli alberghi?',
        v=c24, lo=10, hi=70, passo=1, unita='%', dec=0,
        confronto=[('2019', c19, '%'), ('2024', c24, '%')],
        spiega='Il 42%: nel 2019 erano il 22%. Le notti in albergo sono un po’ calate, quelle fuori dagli alberghi sono più che raddoppiate.',
        anno='2019–2024', fonte='Comune di Milano e Regione Lombardia, presenze turistiche', licenza=CC))

    # ------------------------------------------------------------------ CASE VUOTE
    f = 'case-vuote/data/confronto_territori.csv'
    p = Prove()
    qm = p.v(f, '[territorio=Comune di Milano]', 'quota_2021')
    ql = p.v(f, '[territorio=Lombardia]', 'quota_2021')
    out.append(piuomeno(p, id='vuote-milano-lombardia', pagina='case-vuote', diff='media',
        domanda='Nel 2021 la quota di abitazioni senza residenti dentro è più alta a Milano o in tutta la Lombardia?',
        a=('Comune di Milano, 2021', qm, '%'), b=('Lombardia, 2021', ql, '%'), dec=1,
        spiega='In Lombardia 21,2%, a Milano 13,5%. Milano resta sotto, ma da sola ha più che raddoppiato la sua quota in dieci anni.',
        anno='2021', fonte='ISTAT, censimento della popolazione e delle abitazioni', licenza=CC))

    p = Prove()
    q11 = p.v(f, '[territorio=Comune di Milano]', 'quota_2011')
    q21 = p.v(f, '[territorio=Comune di Milano]', 'quota_2021')
    out.append(vf(p, id='vuote-raddoppiate', pagina='case-vuote', diff='facile',
        affermazione='Dal 2011 al 2021 a Milano la quota di abitazioni senza residenti dentro è più che raddoppiata.',
        vero=q21 > 2 * q11, confronto=[('2011', q11, '%'), ('2021', q21, '%')], dec=1,
        spiega='Dal 6,0% al 13,5%: sono più che raddoppiate. Dentro ci sono case sfitte, seconde case e affitti brevi.',
        anno='2011–2021', fonte='ISTAT, censimento della popolazione e delle abitazioni', licenza=CC))

    # ------------------------------------------------------------------ CASE POPOLARI
    f = 'case-popolari/data/aler_vuoti_serie_2018_2025.csv'
    p = Prove()
    v21 = p.v(f, '[anno=2021]', 'vuoti_totali_armonizzati')
    v25 = p.v(f, '[anno=2025]', 'vuoti_totali_armonizzati')
    pc25 = p.v(f, '[anno=2025]', 'vuoti_%_del_totale')
    out.append(vf(p, id='aler-vuoti-calo', pagina='case-popolari', diff='difficile',
        affermazione='Tra il 2021 e il 2025 gli alloggi vuoti dell’ALER Milano (tutto il suo territorio) sono diminuiti.',
        vero=v25 < v21, confronto=[('2021', v21, 'alloggi'), ('2025', v25, 'alloggi')],
        spiega='Da 8.350 a 7.735, contando i vuoti sempre nello stesso modo. Ma sono ancora il 14,6% degli alloggi a canone sociale.',
        anno='2021–2025', fonte='ALER Milano, prospetti sul patrimonio', licenza=CITAZ))

    # ------------------------------------------------------------------ COSTRUZIONI
    f = 'costruzioni/data/serie_annuale.csv'
    p = Prove()
    a22 = p.v(f, '[anno=2022]', 'abitazioni')
    a24 = p.v(f, '[anno=2024]', 'abitazioni')
    mx = max(r['abitazioni'] for r in carica(f))
    assert mx == a22
    dim = p.calc('round((1-p[1]/p[0])*100)')
    out.append(vf(p, id='costr-crollo', pagina='costruzioni', diff='media',
        affermazione='Nel 2024 le abitazioni nei nuovi edifici di Milano sono meno di un quinto di quelle del 2022.',
        vero=a24 < a22 / 5, confronto=[('2022', a22, 'abitazioni'), ('2024', a24, 'abitazioni')],
        spiega='Da 3.917 a 1.059: il 73% in meno, ma restano più di un quinto. Il 2022 è stato l’anno record dal 2014.',
        anno='2014–2024', fonte='Comune di Milano, titoli edilizi per nuove costruzioni', licenza=CC))

    # ------------------------------------------------------------------ PALAZZI
    f = 'palazzi/data/epoche_citta_municipi.csv'
    p = Prove()
    e1 = p.v(f, '[territorio=Milano (abitazioni occupate)]', '1946-1960')
    e2 = p.v(f, '[territorio=Milano (abitazioni occupate)]', '1961-1970')
    tt = p.v(f, '[territorio=Milano (abitazioni occupate)]', 'totale')
    q = p.calc('round((p[0]+p[1])/p[2]*100, 1)')
    out.append(numero(p, id='palazzi-boom', pagina='palazzi', diff='difficile',
        domanda='Che quota delle abitazioni occupate di Milano sta in palazzi costruiti tra il 1946 e il 1970?',
        v=q, lo=20, hi=80, passo=1, unita='%', dec=1,
        spiega='Più della metà: 53,6%. Sono le case della ricostruzione e del boom economico.',
        anno='2011', fonte='ISTAT, censimento della popolazione e delle abitazioni 2011', licenza=CC))

    # ------------------------------------------------------------------ SFRATTI
    f = 'sfratti/data/serie_unita.csv'
    p = Prove()
    na = p.v(f, ix(f, unita='Comune di Napoli', anno=2024), 'emessi_per_1000_fam')
    ro = p.v(f, ix(f, unita='Comune di Roma', anno=2024), 'emessi_per_1000_fam')
    mi_ = p.v(f, ix(f, unita='Comune di Milano', anno=2024), 'emessi_per_1000_fam')
    out.append(ordine(p, id='sfratti-ordine', pagina='sfratti', diff='media',
        domanda='Sfratti emessi nel 2024 ogni mille famiglie. Dal più alto al più basso:',
        elementi=[('Roma', ro, 'ogni mille'), ('Milano', mi_, 'ogni mille'), ('Napoli', na, 'ogni mille')],
        unita='ogni mille famiglie', dec=1,
        spiega='Napoli ha 5,2 sfratti ogni mille famiglie, Roma 2,8, Milano 1,4. Il numero delle famiglie è una stima per gli anni senza censimento.',
        anno='2024', fonte='Ministero dell’Interno, provvedimenti di sfratto; ISTAT, famiglie', licenza=CITAZ))

    p = Prove()
    s14 = p.v(f, ix(f, unita='Milano (provincia con Monza e Brianza)', anno=2014), 'emessi_per_1000_fam')
    s24 = p.v(f, ix(f, unita='Milano (provincia con Monza e Brianza)', anno=2024), 'emessi_per_1000_fam')
    dimi = p.calc('round((1-p[1]/p[0])*100)')
    out.append(vf(p, id='sfratti-dimezzati', pagina='sfratti', diff='facile',
        affermazione='Dal 2014 al 2024 gli sfratti emessi ogni mille famiglie, nella provincia di Milano con Monza e Brianza, sono diminuiti di più di tre quarti.',
        vero=s24 < s14 / 4, confronto=[('2014', s14, 'ogni mille'), ('2024', s24, 'ogni mille')], dec=2,
        spiega='Da 3,57 a 1,23 ogni mille famiglie: il 65% in meno, quasi due terzi ma non tre quarti.',
        anno='2014–2024', fonte='Ministero dell’Interno, provvedimenti di sfratto; ISTAT, famiglie', licenza=CITAZ))

    # ------------------------------------------------------------------ PERMETTERSI
    f = 'permettersi/data/riepilogo.json'
    p = Prove()
    nq = p.v(f, 'locale', 'n_nil')
    mq = p.v('permettersi/data/dati.json', 'mq', '[1]')
    sg = p.v('permettersi/data/dati.json', 'soglia')
    ra = p.v(f, 'affitto_civici_crescita_2015_2024_pct')
    rr_ = p.v(f, 'reddito_mediano_crescita_2015_2024_pct')
    c24 = p.v(f, 'locale', '60', '2024')
    c15 = p.v(f, 'locale', '60', '2015')
    out.append(numero(p, id='perm-quartieri', pagina='permettersi', diff='difficile',
        domanda='Su 69 quartieri di Milano, in quanti nel 2024 il reddito tipico di chi ci abita basta per un affitto di 60 m²?',
        v=c24, lo=0, hi=60, passo=1, unita='quartieri', dec=0,
        confronto=[('2015', c15, 'quartieri'), ('2024', c24, 'quartieri')],
        spiega='Solo 12 su 69. Nel 2015 erano 50. Dal 2015 al 2024 gli affitti sono saliti del 41,9%, i redditi mediani del 23,6%.',
        anno='2015–2024', fonte='Agenzia delle Entrate (OMI), MEF e Comune di Milano', licenza=CC))

    # ------------------------------------------------------------------ REDDITI
    f = 'redditi/data/riepilogo.json'
    p = Prove()
    r06 = p.v(f, 'serie', 'Milano', 'media_euro2025', '[6]')
    r24 = p.v(f, 'serie', 'Milano', 'media_euro2025', '[24]')
    assert carica(f)['anni'][6] == 2006 and carica(f)['anni'][24] == 2024
    var = p.calc('round((p[1]/p[0]-1)*100, 1)')
    out.append(vf(p, id='red-fermi', pagina='redditi', diff='difficile',
        affermazione='Dal 2006 al 2024, tolta l’inflazione, il reddito medio dichiarato dei milanesi è salito di oltre il 10%.',
        vero=var > 10, confronto=[('2006', r06, '€'), ('2024', r24, '€')],
        spiega='È salito dello 0,7%: da 40.595 a 40.889 € in euro di oggi. Nei prezzi di allora sarebbe molto di più, ma l’inflazione se lo mangia.',
        anno='2006–2024', fonte='MEF, dichiarazioni dei redditi per comune; ISTAT, indice dei prezzi', licenza=CC))

    p = Prove()
    rm = p.v(f, 'serie', 'Milano', 'media_nominale', '[24]')
    rr = p.v(f, 'serie', 'Roma', 'media_nominale', '[24]')
    rn = p.v(f, 'serie', 'Napoli', 'media_nominale', '[24]')
    out.append(ordine(p, id='red-ordine', pagina='redditi', diff='facile',
        domanda='Reddito medio dichiarato per contribuente nel 2024. Dal più alto al più basso:',
        elementi=[('Napoli', rn, '€'), ('Milano', rm, '€'), ('Roma', rr, '€')],
        unita='€', dec=0,
        spiega='Milano 40.316 €, Roma 31.423 €, Napoli 24.388 €. Sono medie: dentro Milano il divario tra zone è enorme.',
        anno='2024', fonte='MEF, dichiarazioni dei redditi per comune', licenza=CC))

    # ------------------------------------------------------------------ COSTO DELLA VITA
    f = 'costo-vita/data/affitto_vs_reddito.csv'
    p = Prove()
    mq = p.v('permettersi/data/dati.json', 'mq', '[1]')
    q06 = p.v(f, '[anno=2006]', 'quota_affitto_su_reddito_pct')
    q21 = p.v(f, '[anno=2021]', 'quota_affitto_su_reddito_pct')
    q24 = p.v(f, '[anno=2024]', 'quota_affitto_su_reddito_pct')
    out.append(numero(p, id='vita-affitto-quota', pagina='costo-vita', diff='media',
        domanda='Nel 2024, che parte del reddito mensile mediano serve a Milano per un mese d’affitto di 60 m²?',
        v=q24, lo=15, hi=55, passo=0.5, unita='%', dec=1,
        confronto=[('2006', q06, '%'), ('2021', q21, '%'), ('2024', q24, '%')],
        spiega='Più di un terzo: 34,5%. Nel 2021 era il 27,8%: in tre anni gli affitti sono cresciuti molto più dei redditi.',
        anno='2006–2024', fonte='Agenzia delle Entrate (OMI), affitti; MEF, redditi', licenza=CC))

    # ------------------------------------------------------------------ BILANCIO DEL COMUNE
    f = 'bilancio-comune/data/riepilogo.json'
    p = Prove()
    s15 = p.v(f, 'spesa', 'totale', 'reale_pc', '[0]')
    s24 = p.v(f, 'spesa', 'totale', 'reale_pc', '[9]')
    out.append(vf(p, id='bil-spesa-abitante', pagina='bilancio-comune', diff='difficile',
        affermazione='Per ogni abitante, il Comune di Milano spende nel 2024 meno di quanto spendeva nel 2015 (in euro del 2025).',
        vero=s24 < s15, confronto=[('2015', s15, '€'), ('2024', s24, '€')],
        spiega='Spesa corrente per abitante: da 2.520 € a 2.284 €, in euro del 2025.',
        anno='2015–2024, euro 2025', fonte='Comune di Milano, rendiconti di bilancio; ISTAT, indice dei prezzi', licenza=CC))

    p = Prove()
    amb = p.v(f, 'spesa', 'missioni', '[cod=9]', 'reale_pc', '[9]')
    tra = p.v(f, 'spesa', 'missioni', '[cod=10]', 'reale_pc', '[9]')
    soc = p.v(f, 'spesa', 'missioni', '[cod=12]', 'reale_pc', '[9]')
    out.append(ordine(p, id='bil-ordine-missioni', pagina='bilancio-comune', diff='media',
        domanda='Spesa corrente per abitante del Comune nel 2024 (euro 2025). Dalla più alta alla più bassa:',
        elementi=[('Ambiente e rifiuti', amb, '€'), ('Trasporti e strade', tra, '€'), ('Servizi sociali e nidi', soc, '€')],
        unita='€', dec=0,
        spiega='Trasporti e strade pesano più di tutto: 853 € a testa. Servizi sociali e nidi 311 €, ambiente e rifiuti 262 €.',
        anno='2024, euro 2025', fonte='Comune di Milano, rendiconti di bilancio', licenza=CC))

    f = 'bilancio-comune/data/voci_concrete.csv'
    p = Prove()
    mu = p.v(f, ix(f, anno=2025, voce='Multe del codice della strada (anno corrente)'), 'importo_euro')
    di = p.v(f, ix(f, anno=2025, voce='Dividendi'), 'importo_euro')
    mu_m = p.calc('round(p[0]/1000000)')
    di_m = p.calc('round(p[1]/1000000)')
    out.append(piuomeno(p, id='bil-multe-dividendi', pagina='bilancio-comune', diff='facile',
        domanda='Nel 2025 il Comune di Milano incassa di più dalle multe stradali o dai dividendi delle sue società?',
        a=('multe stradali dell’anno', mu_m, 'milioni €'), b=('dividendi delle società', di_m, 'milioni €'),
        spiega='Le multe dell’anno valgono 261 milioni, i dividendi di A2A, SEA e altre società 203.',
        anno='2025', fonte='Comune di Milano, entrate del bilancio', licenza=CC))

    # ------------------------------------------------------------------ TASSE
    f = 'tasse/data/irpef_citta_2024.csv'
    p = Prove()
    im = p.v(f, '[citta=Milano]', 'irpef_netta_euro')
    ir = p.v(f, '[citta=Roma]', 'irpef_netta_euro')
    pm = p.v(f, '[citta=Milano]', 'irpef_per_abitante')
    pr = p.v(f, '[citta=Roma]', 'irpef_per_abitante')
    im_m = p.calc('round(p[0]/1000000)')
    ir_m = p.calc('round(p[1]/1000000)')
    out.append(piuomeno(p, id='tasse-irpef-roma', pagina='tasse', diff='media',
        domanda='Nel 2024 l’IRPEF pagata in totale dai contribuenti di Milano è più alta o più bassa di quella di Roma?',
        a=('IRPEF di Milano, 2024', im_m, 'milioni €'), b=('IRPEF di Roma, 2024', ir_m, 'milioni €'),
        spiega='Roma ha il doppio degli abitanti e quindi più IRPEF in totale. Per abitante vince Milano: 7.735 € contro 4.981 €.',
        anno='2024', fonte='MEF, dichiarazioni dei redditi per comune', licenza=CC))

    p = Prove()
    pa = p.v('tasse/data/riepilogo.json', 'sintesi', 'per_abitante_2025')
    qe = p.v('tasse/data/riepilogo.json', 'sintesi', 'quota_entrate_correnti_2025')
    out.append(numero(p, id='tasse-quattro', pagina='tasse', diff='media',
        domanda='Nel 2025 le quattro tasse del Comune (casa, rifiuti, addizionale, soggiorno) valgono quanto per abitante?',
        v=pa, lo=300, hi=2500, passo=10, unita='€', dec=0,
        spiega='1.058 € a testa, il 37% delle entrate correnti del Comune. Le paga anche chi non abita a Milano: turisti e proprietari.',
        anno='2025', fonte='Comune di Milano, entrate tributarie', licenza=CC))

    # ------------------------------------------------------------------ TURISTI
    f = 'turisti/data/serie_totale.csv'
    p = Prove()
    anni = list(range(2005, 2020))
    pr = [p.v(f, '[anno=%d]' % y, 'presenze_totale') for y in anni]
    primo = next(y for y, v in zip(anni, pr) if v > 10_000_000)
    assert primo == 2014 and pr[anni.index(2013)] < 10_000_000
    primo = p.v(f, '[anno=2014]', 'anno')
    out.append(anno_q(p, id='tur-10-milioni', pagina='turisti', diff='difficile',
        domanda='In che anno le notti dei turisti a Milano hanno superato per la prima volta i 10 milioni?',
        v=primo, lo=2007, hi=2019,
        spiega='Nel 2014, con 10,2 milioni di notti. Nel 2019, prima del Covid, erano 12,9 milioni.',
        anno='2005–2019', fonte='Comune di Milano e Regione Lombardia, presenze turistiche', licenza=CC,
        serie=serie_da(anni, [('Notti dei turisti', pr)])))

    f = 'turisti/data/paesi_anno.csv'
    p = Prove()
    us = p.v(f, ix(f, anno=2024, paese="Stati Uniti d'America"), 'presenze')
    fr = p.v(f, ix(f, anno=2024, paese='Francia'), 'presenze')
    cn = p.v(f, ix(f, anno=2024, paese='Cina'), 'presenze')
    out.append(ordine(p, id='tur-paesi', pagina='turisti', diff='media',
        domanda='Notti passate a Milano nel 2024 dai turisti stranieri. Dal Paese con più notti a quello con meno:',
        elementi=[('Francia', fr, 'notti'), ('Cina', cn, 'notti'), ('Stati Uniti', us, 'notti')],
        unita='notti', dec=0,
        spiega='Gli americani guidano con 1,3 milioni di notti, poi i francesi con 863 mila. I cinesi sono 452 mila.',
        anno='2024', fonte='Comune di Milano e Regione Lombardia, presenze per Paese di provenienza', licenza=CC))

    # ------------------------------------------------------------------ IMPRESE
    f = 'imprese/data/milano_annuale.csv'
    p = Prove()
    isc = p.v(f, '[anno=2025]', 'iscrizioni')
    ces = p.v(f, '[anno=2025]', 'cessazioni_lorde')
    off = p.v(f, '[anno=2025]', 'cancellazioni_ufficio')
    vere = p.v(f, '[anno=2025]', 'cessazioni_non_ufficio')
    out.append(vf(p, id='imp-chiusure', pagina='imprese', diff='difficile',
        affermazione='Nel 2025, nella provincia di Milano (senza Monza e Brianza), le imprese cessate sono più di quelle nate.',
        vero=ces > isc, confronto=[('nate', isc, 'imprese'), ('cessate', ces, 'imprese')],
        spiega='Sono 26.262 nate contro 24.606 cessate. E delle cessate 7.523 sono cancellazioni d’ufficio: le chiusure vere sono 17.083.',
        anno='2025', fonte='Unioncamere e InfoCamere, Registro delle imprese', licenza=CITAZ))

    # ------------------------------------------------------------------ LAVORO
    f = 'lavoro/data/comune_lavoro.csv'
    p = Prove()
    o91 = p.v(f, '[anno=1991]', 'occ')
    o11 = p.v(f, '[anno=2011]', 'occ')
    o23 = p.v(f, '[anno=2023]', 'occ')
    out.append(vf(p, id='lav-occupati-1991', pagina='lavoro', diff='difficile',
        affermazione='Nel 2011 gli occupati residenti a Milano erano meno di quelli del 1991.',
        vero=o11 < o91, confronto=[('1991', o91, 'occupati'), ('2011', o11, 'occupati'), ('2023', o23, 'occupati')],
        spiega='Erano 550.946 contro 553.978, quasi uguali. Poi risalgono: 642.475 nel 2023.',
        anno='1991–2023', fonte='ISTAT, censimenti della popolazione e delle abitazioni', licenza=CC))

    # ------------------------------------------------------------------ CHILOMETRI DAL DUOMO
    f = 'chilometri-duomo/data/chilometri.json'
    p = Prove()
    r0 = p.v(f, 'fasce', '[0]', 'v', 'reddito')
    r8 = p.v(f, 'fasce', '[4]', 'v', 'reddito')
    rc = p.v(f, 'indicatori', '[5]', 'citta')
    assert carica(f)['fasce'][4]['da'] == 8 and carica(f)['indicatori'][5]['id'] == 'reddito'
    out.append(numero(p, id='km-reddito-duomo', pagina='chilometri-duomo', diff='media',
        domanda='Reddito medio per contribuente nei primi 2 km dal Duomo, in euro del 2025: quanto?',
        v=r0, lo=20000, hi=90000, passo=500, unita='€', dec=0,
        confronto=[('oltre 8 km dal Duomo', r8, '€'), ('tutta Milano', rc, '€'), ('primi 2 km', r0, '€')],
        spiega='67.922 € nei primi 2 km, contro 27.201 € oltre gli 8 km: due volte e mezzo tanto. La media di tutta Milano è 40.889 €.',
        anno='2024, euro 2025', fonte='MEF, redditi per CAP; Comune di Milano', licenza=CC))

    # ------------------------------------------------------------------ piuomeno aggiunti
    f = 'matrimoni/data/unioni_civili_riepilogo.csv'
    p = Prove()
    uo = p.v(f, '[anno=2024]', 'uomini')
    do = p.v(f, '[anno=2024]', 'donne')
    qu = p.v(f, '[anno=2024]', 'quota_uomini_pct')
    out.append(piuomeno(p, id='matri-unioni-civili', pagina='matrimoni', diff='media',
        domanda='Nelle unioni civili celebrate a Milano nel 2024, ci sono state più coppie di uomini o di donne?',
        a=('coppie di uomini', uo, ''), b=('coppie di donne', do, ''),
        spiega='Le coppie di uomini sono 128, quelle di donne 51: il 71,5% del totale.',
        anno='2024', fonte='Comune di Milano, unioni civili', licenza=CC))

    f = 'lavoro/data/comune_lavoro.csv'
    p = Prove()
    om = p.v(f, '[anno=2023]', 'occ_m')
    of_ = p.v(f, '[anno=2023]', 'occ_f')
    om91 = p.v(f, '[anno=1991]', 'occ_m')
    of91 = p.v(f, '[anno=1991]', 'occ_f')
    out.append(piuomeno(p, id='lav-uomini-donne', pagina='lavoro', diff='facile',
        domanda='Nel 2023 a Milano ci sono più occupati uomini o più occupate donne?',
        a=('occupati uomini', om, ''), b=('occupate donne', of_, ''),
        spiega='Gli uomini sono 346.847, le donne 295.628. Il divario si è ridotto molto: nel 1991 erano 330.899 contro 223.079.',
        anno='1991–2023', fonte='ISTAT, censimenti della popolazione e delle abitazioni', licenza=CC))

    f = 'turisti/data/serie_totale.csv'
    p = Prove()
    ps = p.v(f, '[anno=2024]', 'presenze_stranieri')
    pi = p.v(f, '[anno=2024]', 'presenze_italiani')
    pt = p.v(f, '[anno=2024]', 'presenze_totale')
    ms = p.calc('round(p[0]/1000000, 1)')
    mi_ = p.calc('round(p[1]/1000000, 1)')
    sh = p.calc('round(p[0]/p[2]*100)')
    out.append(piuomeno(p, id='tur-stranieri-italiani', pagina='turisti', diff='facile',
        domanda='Nel 2024 a Milano, i turisti stranieri hanno passato più notti di quelli italiani?',
        a=('turisti stranieri', ms, 'milioni di notti'), b=('turisti italiani', mi_, 'milioni di notti'), dec=1,
        spiega='Ben 12,4 milioni di notti contro 4,1. Tre notti su quattro, il 75%, sono di stranieri.',
        anno='2024', fonte='Comune di Milano e Regione Lombardia, presenze turistiche', licenza=CC))

    f = 'costo-vita/data/milano_vs_italia.csv'
    p = Prove()
    rm = p.v(f, '[8]', 'milano_pct')
    ri = p.v(f, '[8]', 'italia_pct')
    gm = p.v(f, '[4]', 'milano_pct')
    gi = p.v(f, '[4]', 'italia_pct')
    assert carica(f)[8]['confronto'] == 'Ristoranti e alberghi' and carica(f)[4]['confronto'] == 'indice generale' and carica(f)[4]['periodo_da'] == 2020
    out.append(piuomeno(p, id='vita-ristoranti', pagina='costo-vita', diff='media',
        domanda='Dal 2020 al 2025 i prezzi di ristoranti e alberghi sono saliti di più a Milano o in tutta Italia?',
        a=('Milano', rm, '%'), b=('Italia', ri, '%'), dec=1,
        spiega='A Milano +30,5%, in Italia +24,2%. Nel complesso, invece, i prezzi sono saliti quasi uguale: 19,2% a Milano e 19,4% in Italia.',
        anno='2020–2025', fonte='ISTAT, indici dei prezzi al consumo', licenza=CC))

    f = 'costo-vita/data/biglietto_atm.csv'
    p = Prove()
    b02 = p.v(f, ix(f, data_inizio='2002-01', titolo='biglietto ordinario'), 'prezzo_eur')
    b26 = p.v(f, ix(f, data_inizio='2026-11-01', titolo='biglietto ordinario'), 'prezzo_eur')
    out.append(vf(p, id='vita-biglietto-atm', pagina='costo-vita', diff='facile',
        affermazione='Il biglietto ordinario dei mezzi pubblici di Milano costa oggi più del doppio di quello del 2002.',
        vero=b26 > 2 * b02, confronto=[('2002', b02, '€'), ('oggi', b26, '€')], dec=2,
        spiega='Costava 1,00 € nel 2002 e costa 2,20 € oggi: più del doppio.',
        anno='2002–2026', fonte='ATM, tariffe del biglietto ordinario', licenza='Tutti i diritti riservati — solo cifre citate'))

    f = 'case-popolari/data/patrimonio_sap_milano_serie.csv'
    p = Prove()
    cm = p.v(f, '[8]', 'unita_proprieta_Comune_di_Milano')
    al = p.v(f, '[8]', 'unita_proprieta_ALER_Milano')
    tot = p.v(f, '[8]', 'totale_Milano_citta')
    assert carica(f)[8]['rapporto'].startswith('Rapporto 2025')
    out.append(piuomeno(p, id='aler-o-comune', pagina='case-popolari', diff='media',
        domanda='Tra le case popolari di Milano, ne ha di più il Comune o l’ALER?',
        a=('case del Comune di Milano', cm, ''), b=('case dell’ALER in città', al, ''),
        spiega='L’ALER ne ha 33.044, il Comune 26.010: in tutto 59.054 case popolari in città.',
        anno='2026', fonte='Regione Lombardia, rapporto sul patrimonio dei servizi abitativi pubblici', licenza=CITAZ))

    f = 'affitti-brevi/data/notti_alberghi_extra.csv'
    p = Prove()
    al_ = p.v(f, '[anno=2024]', 'presenze_alberghi')
    ex = p.v(f, '[anno=2024]', 'presenze_extra_alberghiere')
    ex19 = p.v(f, '[anno=2019]', 'presenze_extra_alberghiere')
    al_m = p.calc('round(p[0]/1000000, 1)')
    ex_m = p.calc('round(p[1]/1000000, 1)')
    ex19m = p.calc('round(p[2]/1000000, 1)')
    out.append(piuomeno(p, id='brevi-alberghi-extra', pagina='affitti-brevi', diff='media',
        domanda='Nel 2024 i turisti hanno passato a Milano più notti negli alberghi o fuori dagli alberghi?',
        a=('notti in albergo', al_m, 'milioni'), b=('notti fuori dagli alberghi', ex_m, 'milioni'), dec=1,
        spiega='Gli alberghi vincono ancora, 9,5 milioni contro 7,0, ma nel 2019 le notti fuori dagli alberghi erano solo 2,9 milioni.',
        anno='2019–2024', fonte='Comune di Milano e Regione Lombardia, presenze turistiche', licenza=CC))

    return out
