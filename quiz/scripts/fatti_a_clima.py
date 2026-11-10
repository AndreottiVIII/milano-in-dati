"""Domande: clima, ambiente, territorio e mobilità (modulo a_clima)."""
from mazzo import (Prove, piuomeno, numero, vf, ordine, anno_q, serie_da, carica, primo_sorpasso)


def ix(rel, **kw):
    """Indice (come testo tra parentesi quadre) della prima riga di un CSV che soddisfa le condizioni."""
    for i, r in enumerate(carica(rel)):
        if all(str(r.get(k)) == str(v) for k, v in kw.items()):
            return '[%d]' % i
    raise KeyError((rel, kw))


def ixl(lst, key, val):
    for i, r in enumerate(lst):
        if r.get(key) == val:
            return '[%d]' % i
    raise KeyError((key, val))


def domande():
    out = []
    add = out.append

    # ---------- TEMPERATURE ----------
    F = 'temperature/data/annuale.json'
    anni = carica(F)['anni']
    p = Prove()
    a61 = p.v(F, 'anni', ixl(anni, 'anno', 1861), 'gg_35')
    a24 = p.v(F, 'anni', ixl(anni, 'anno', 2024), 'gg_35')
    add(piuomeno(p, id='temp-35-1861', pagina='temperature', diff='difficile',
        domanda='Più giorni con almeno trentacinque gradi a Brera nel 1861 o nel 2024?',
        a=('giorni torridi, 1861', a61, 'giorni'), b=('giorni torridi, 2024', a24, 'giorni'),
        spiega='Nel 1861 i giorni così caldi furono di più del doppio. Attenzione: le misure di allora erano fatte con strumenti diversi e sono meno affidabili.',
        anno='1861 e 2024', fonte='serie di Milano Brera dal 1763 (Università di Milano, ARPA Lombardia)', licenza='CC BY-NC'))

    p = Prove()
    rec = p.v('temperature/data/records.json', 'giorni_estremi', 'tmax_alta', '[0]', 'valore')
    d1 = p.v('temperature/data/records.json', 'giorni_estremi', 'tmax_alta', '[0]', 'data')
    rec2 = p.v('temperature/data/records.json', 'giorni_estremi', 'tmax_alta', '[1]', 'valore')
    d2 = p.v('temperature/data/records.json', 'giorni_estremi', 'tmax_alta', '[1]', 'data')
    terzo = p.v('temperature/data/records.json', 'giorni_estremi', 'tmax_alta', '[2]', 'valore')
    m25 = p.v(F, 'anni', ixl(anni, 'anno', 2025), 'max_ass')
    assert rec == rec2 > terzo and d1 == '1902-07-09' and d2 == '2003-08-11'
    add(vf(p, id='temp-record-1902', pagina='temperature', diff='media',
        affermazione='Il giorno più caldo mai misurato a Brera è di un’estate recente: dopo il 2010.',
        vero=False, confronto=[('9 luglio 1902', rec, '°C'), ('11 agosto 2003', rec2, '°C'), ('il giorno più caldo del 2025', m25, '°C')], dec=1,
        spiega='Il record, 38,3 °C, è condiviso da due giorni: il 9 luglio 1902 e l’11 agosto 2003. Nel 2025 la giornata più calda si è fermata due gradi sotto.',
        anno='1902, 2003 e 2025', fonte='serie di Milano Brera dal 1763 (Università di Milano, ARPA Lombardia)', licenza='CC BY-NC'))

    # ---------- PIOGGIA ----------
    p = Prove()
    mm = p.v('pioggia/data/records.json', 'top', '[0]', 'mm')
    add(numero(p, id='pioggia-record-giorno', pagina='pioggia', diff='media',
        domanda='Quanti millimetri di pioggia sono caduti nel giorno più piovoso dal 1858, ad agosto del 1979?',
        v=mm, lo=40, hi=300, passo=5, unita='mm',
        spiega='Un millimetro è un litro d\'acqua su ogni metro quadrato. Quel giorno ne caddero 161 in un giorno solo, quasi un sesto di quanto piove in un anno intero.',
        anno='1858 e 1979', fonte='serie storica di Milano (Università di Milano) e pluviometri ARPA Lombardia', licenza='CC BY-NC'))

    p = Prove()
    q = p.v('pioggia/data/records.json', 'quota', 'media')
    pct = p.calc('round(p[0]*100)')
    ore1 = p.v('pioggia/data/records.json', 'ore', 'top')
    ore_a = p.v('pioggia/data/records.json', 'ore', 'anno')
    add(numero(p, id='pioggia-1pct-ore', pagina='pioggia', diff='difficile',
        domanda='Su ogni cento millimetri di pioggia di un anno, quanti cadono nell\'uno per cento delle ore, le più piovose?',
        v=pct, lo=10, hi=90, passo=1, unita='%',
        spiega='In media sono 54 su cento, in sole 88 ore su 8.760. Più che piovere poco ogni giorno, a Milano piove a scrosci.',
        anno='2003–2025', fonte='pluviometri ARPA Lombardia', licenza='CC0'))

    A = 'pioggia/data/annuale.json'
    an = carica(A)['anni']
    p = Prove()
    ys = list(range(2005, 2026))
    vals = [p.v(A, 'anni', ixl(an, 'a', y), 'tot') for y in ys]
    sec = p.v('pioggia/data/records.json', 'secco', 'a')
    add(anno_q(p, id='pioggia-anno-secco', pagina='pioggia', diff='media',
        domanda='In che anno è piovuto meno da quando si misura, dal 1858 (a Milano)?',
        v=sec, lo=1980, hi=2026,
        serie=serie_da(ys, [('mm di pioggia', vals)]),
        spiega='Nel 2022 caddero 398 mm, contro una media di quasi mille. Due anni dopo ne caddero 1.495.',
        anno='1858–2025', fonte='serie storica di Milano (Università di Milano) e pluviometri ARPA Lombardia', licenza='CC BY-NC'))

    # ---------- NEVE E NEBBIA ----------
    D = 'neve-e-nebbia/data/decenni.json'
    p = Prove()
    n20 = p.v(D, 'inverni', 'LINATE', 'n', '[7]', 'm')
    n70 = p.v(D, 'inverni', 'LINATE', 'n', '[2]', 'm')
    add(numero(p, id='neve-anni20', pagina='neve-e-nebbia', diff='facile',
        domanda='Quanti giorni di neve in un inverno, in media, a Linate dal 2020 in poi?',
        v=n20, lo=0, hi=12, passo=1, unita='giorni',
        spiega='Appena 2, contro i 10,5 degli anni Settanta. Gli inverni bianchi sono diventati rari.',
        anno='2020–2025', fonte='osservazioni dell\'aeroporto di Linate (NOAA)', licenza='Uso con citazione, non aperta',
        confronto=[('anni Settanta', n70, 'giorni'), ('dal 2020', n20, 'giorni')], dec=0))

    p = Prove()
    f50 = p.v(D, 'anni', 'LINATE', 'v', '[0]', 'm')
    f80 = p.v(D, 'anni', 'LINATE', 'v', '[3]', 'm')
    f20 = p.v(D, 'anni', 'LINATE', 'v', '[7]', 'm')
    add(ordine(p, id='nebbia-decenni', pagina='neve-e-nebbia', diff='facile',
        domanda='Giorni di nebbia all\'anno a Linate: metti in ordine, dal più alto al più basso.',
        elementi=[('dal 2020 in poi', f20, 'giorni'), ('anni Cinquanta', f50, 'giorni'), ('anni Ottanta', f80, 'giorni')],
        unita='giorni',
        spiega='Dagli anni Cinquanta a oggi la nebbia, cioè visibilità sotto un chilometro, si è più che dimezzata.',
        anno='1952–2024', fonte='osservazioni dell\'aeroporto di Linate (NOAA)', licenza='Uso con citazione, non aperta'))

    # ---------- ARIA ----------
    G = 'aria/data/annuale.json'
    p = Prove()
    g03 = p.v(G, 'PM10', 'stazioni', '528', '[2]', '4')
    g25 = p.v(G, 'PM10', 'stazioni', '528', '[24]', '4')
    add(numero(p, id='aria-pm10-2003', pagina='aria', diff='media',
        domanda='Quanti giorni nel 2003 il PM10 ha superato il limite giornaliero al Verziere? La legge ne ammette trentacinque.',
        v=g03, lo=30, hi=220, passo=5, unita='giorni',
        spiega='Il limite, cinquanta microgrammi, fu superato in 151 giorni. Nel 2025 i giorni sono stati 21.',
        anno='2003 e 2025', fonte='centralina del Verziere (ARPA Lombardia)', licenza='CC0',
        confronto=[('2003', g03, 'giorni'), ('2025', g25, 'giorni')]))

    p = Prove()
    ys = list(range(2008, 2026))
    vals = [p.v(G, 'PM10', 'stazioni', '528', '[%d]' % (y - 2001), '4') for y in ys]
    y21 = p.v(G, 'PM10', 'stazioni', '528', '[20]', '0')
    add(anno_q(p, id='aria-pm10-35', pagina='aria', diff='difficile',
        domanda='Al Verziere i giorni di PM10 fuori legge non devono superare trentacinque l\'anno. In che anno è successo per la prima volta?',
        v=y21, lo=2010, hi=2026,
        serie=serie_da(ys, [('giorni sopra 50', vals)]),
        spiega='Il limite fu rispettato per la prima volta nel 2021, con 30 giorni. Nel 2022 tornò a 44.',
        anno='2008–2025', fonte='centralina del Verziere (ARPA Lombardia)', licenza='CC0'))

    p = Prove()
    no2 = [p.v('aria/data/peggiori.json', 'NO2', '[%d]' % i, 'media') for i in (0, 2, 4)]
    lim = p.v(G, 'NO2', 'limite_ue')
    add(ordine(p, id='aria-no2-centraline', pagina='aria', diff='facile',
        domanda='Biossido di azoto, media 2021–2025: metti in ordine le centraline, dal valore più alto al più basso.',
        elementi=[('Senato', no2[1], 'µg/m³'), ('Pascal (Città Studi)', no2[2], 'µg/m³'), ('Marche', no2[0], 'µg/m³')],
        unita='µg/m³', dec=1,
        spiega='Viale Marche, con più traffico, è la peggiore. Il limite di legge è 40: soltanto lì è superato.',
        anno='2021–2025', fonte='centraline di Milano (ARPA Lombardia e Comune di Milano)', licenza='CC0'))

    # ---------- CALDO ----------
    C = 'caldo/data/riepilogo.json'
    rows = carica(C)['notti_per_anno']
    p = Prove()
    br = p.v(C, 'notti_per_anno', ixl(rows, 'a', 2025), 'Brera')
    ca = p.v(C, 'notti_per_anno', ixl(rows, 'a', 2025), 'Campagna (media)')
    add(piuomeno(p, id='caldo-notti-2025', pagina='caldo', diff='facile',
        domanda="Nell'estate 2025 più notti tropicali (minima da venti gradi in su) in centro a Milano o in campagna?",
        a=('centro di Milano (Brera)', br, 'notti'), b=('campagna intorno', ca, 'notti'),
        spiega="Brera ne ha avute 69, la campagna 33: la città di notte resta più calda. Succede in tutte le estati misurate.",
        anno='2025', fonte='termometri di ARPA Lombardia', licenza='CC0'))

    # ---------- ALBERI ----------
    R_ = 'alberi/data/riepilogo.json'
    p = Prove()
    a23 = p.v(R_, 'citta', 'alberi', '2023')
    a24 = p.v(R_, 'citta', 'alberi', '2024')
    a25 = p.v(R_, 'citta', 'alberi', '2025')
    sal = p.v(R_, 'cambi', 'saldo')
    salp = p.v(R_, 'cambi', 'saldo_pct')
    add(vf(p, id='alberi-calo', pagina='alberi', diff='media',
        affermazione="Tra marzo 2023 e marzo 2025 gli alberi dell'elenco del Comune di Milano sono diminuiti.",
        vero=a25 < a23, confronto=[('marzo 2023', a23, 'alberi'), ('marzo 2024', a24, 'alberi'), ('marzo 2025', a25, 'alberi')],
        spiega="Sono 3.910 in meno in due anni (-1,5%), anche se nell'ultimo anno l'elenco è risalito. Non è un conto degli alberi veri: conta l'elenco del Comune.",
        anno='2023–2025', fonte='Comune di Milano, censimento degli alberi', licenza='CC BY'))

    G_ = 'alberi/data/generi_2025.csv'
    p = Prove()
    ac = p.v(G_, '[0]', 'alberi')
    ti = p.v(G_, '[2]', 'alberi')
    qu = p.v(G_, '[5]', 'alberi')
    add(ordine(p, id='alberi-generi', pagina='alberi', diff='facile',
        domanda='Alberi del Comune di Milano per genere: metti in ordine, dal più numeroso al meno numeroso.',
        elementi=[('Quercia', qu, 'alberi'), ('Acero', ac, 'alberi'), ('Tiglio', ti, 'alberi')], unita='alberi',
        spiega="L'acero è il genere più numeroso; il platano è secondo e il tiglio terzo.",
        anno='2025', fonte='Comune di Milano, censimento degli alberi (31 marzo 2025)', licenza='CC BY'))

    # ---------- VERDE ----------
    V = 'verde/data/riepilogo.json'
    p = Prove()
    m2 = p.v(V, 'citta', 'B', 'citta_m2_ab')
    s9 = p.v(V, 'citta', 'B', 'sotto_9')
    n64 = p.v(V, 'citta', 'B', 'nil_classifica')
    add(numero(p, id='verde-m2', pagina='verde', diff='facile',
        domanda='Quanti metri quadrati di parchi e giardini ha in media ogni milanese (stima)?',
        v=m2, lo=2, hi=30, passo=0.5, unita='m²', dec=1,
        spiega='La soglia di legge è 9 metri quadrati a testa. In 44 quartieri su 64 non ci si arriva.',
        anno='2024', fonte='Comune di Milano, parchi e giardini; residenti: anagrafe del Comune', licenza='CC BY'))

    U = 'verde/data/uccelli.json'
    p = Prove()
    par = p.v(U, 'specie', '[6]', 'n')
    ger = p.v(U, 'specie', '[7]', 'n')
    add(piuomeno(p, id='verde-parrocchetto', pagina='verde', diff='difficile',
        domanda='Tra le segnalazioni di uccelli a Milano, più parrocchetti dal collare o più germani reali?',
        a=('parrocchetto dal collare', par, 'segnalazioni'), b=('germano reale', ger, 'segnalazioni'),
        spiega='Il pappagallo verde, arrivato da lontano, è la settima specie più segnalata. Sono segnalazioni di osservatori, non un censimento.',
        anno='2018–2025', fonte='segnalazioni di uccelli a Milano raccolte da osservatori (archivi aperti)', licenza='CC BY 4.0'))

    # ---------- RIFIUTI ----------
    MS = 'rifiuti/data/milano_serie.csv'
    p = Prove()
    i24 = p.v(MS, ix(MS, anno=2024), 'indiff_kg_per_abitante')
    i10 = p.v(MS, ix(MS, anno=2010), 'indiff_kg_per_abitante')
    add(numero(p, id='rifiuti-indiff', pagina='rifiuti', diff='media',
        domanda="Quanti chili di rifiuti indifferenziati (il sacco grigio) butta in un anno ogni milanese nel 2024?",
        v=i24, lo=50, hi=400, passo=5, unita='kg', dec=1,
        spiega='Nel 2010 erano 355,9: in quattordici anni il sacco grigio si è dimezzato, mentre cresceva la raccolta separata.',
        anno='2010 e 2024', fonte='ISPRA, rifiuti urbani comune per comune', licenza='CC BY 4.0',
        confronto=[('2010', i10, 'kg'), ('2024', i24, 'kg')]))

    GC = 'rifiuti/data/grandi_citta.csv'
    p = Prove()
    to = p.v(GC, ix(GC, citta='Torino', anno=2024), 'indifferenziato_kg_per_abitante')
    na = p.v(GC, ix(GC, citta='Napoli', anno=2024), 'indifferenziato_kg_per_abitante')
    mi = p.v(GC, ix(GC, citta='Milano', anno=2024), 'indifferenziato_kg_per_abitante')
    bo = p.v(GC, ix(GC, citta='Bologna', anno=2024), 'indifferenziato_kg_per_abitante')
    add(ordine(p, id='rifiuti-indiff-citta', pagina='rifiuti', diff='facile',
        domanda="Indifferenziato a testa nel 2024: metti in ordine le tre città, dalla più alta alla più bassa.",
        elementi=[('Milano', mi, 'kg'), ('Torino', to, 'kg'), ('Napoli', na, 'kg')], unita='kg', dec=1,
        spiega='Milano è la più bassa delle tre. Bologna fa ancora meglio, con 143,5 chili.',
        anno='2024', fonte='ISPRA, rifiuti urbani comune per comune', licenza='CC BY 4.0'))

    p = Prove()
    cmi = p.v(GC, ix(GC, citta='Milano', anno=2024), 'costo_euro_per_abitante')
    cbo = p.v(GC, ix(GC, citta='Bologna', anno=2024), 'costo_euro_per_abitante')
    cfi = p.v(GC, ix(GC, citta='Firenze', anno=2024), 'costo_euro_per_abitante')
    add(vf(p, id='rifiuti-costo', pagina='rifiuti', diff='media',
        affermazione='Nel 2024 il servizio rifiuti costa a Milano più che a Bologna e a Firenze, per abitante.',
        vero=cmi > cbo and cmi > cfi, confronto=[('Milano', cmi, '€'), ('Bologna', cbo, '€'), ('Firenze', cfi, '€')],
        spiega="Milano è la meno cara delle sette grandi città: 219 euro a testa, contro 269 di Bologna e 356 di Firenze.",
        anno='2024', fonte='ISPRA, costi di gestione dei rifiuti', licenza='CC BY 4.0', dec=0))

    # ---------- SUOLO ----------
    CC = 'suolo/data/confronto_citta_2025.csv'
    p = Prove()
    pm_ = p.v(CC, '[0]', 'consumato_2025_pct')
    ha = p.v(CC, '[0]', 'consumato_2025_ha')
    sup = p.v(CC, '[0]', 'superficie_ha')
    add(numero(p, id='suolo-pct', pagina='suolo', diff='media',
        domanda='Quanta parte del Comune di Milano è suolo consumato (costruito o asfaltato), nel 2025?',
        v=pm_, lo=10, hi=90, passo=1, unita='%', dec=1,
        spiega='Sono 10.679 ettari su 18.158. È più di Roma e Bologna, ma meno di Torino e Napoli.',
        anno='2025', fonte='ISPRA e rete SNPA, consumo di suolo', licenza='CC BY 4.0'))

    p = Prove()
    smi = p.v(CC, '[0]', 'consumato_2025_pct')
    sto = p.v(CC, '[2]', 'consumato_2025_pct')
    sna = p.v(CC, '[3]', 'consumato_2025_pct')
    add(piuomeno(p, id='suolo-torino', pagina='suolo', diff='difficile',
        domanda='Più suolo consumato (in percentuale del Comune), Milano o Torino, nel 2025?',
        a=('Milano', smi, '%'), b=('Torino', sto, '%'), dec=1,
        spiega='Torino sta peggio con 65,3%. Anche Napoli supera Milano (63,8%).',
        anno='2025', fonte='ISPRA e rete SNPA, consumo di suolo', licenza='CC BY 4.0'))

    # ---------- FOGNE ----------
    FR = 'fogne/data/riepilogo.json'
    p = Prove()
    l100 = p.v(FR, 'flusso2020', 'litri_ogni_100')
    add(numero(p, id='fogne-122', pagina='fogne', diff='difficile',
        domanda="Nel 2020 ai depuratori di Milano è arrivata più acqua di quella uscita dai rubinetti. Ogni cento litri dai rubinetti, quanti ai depuratori?",
        v=l100, lo=70, hi=160, passo=1, unita='litri',
        spiega='Ne arrivano 122. Le fogne di Milano sono miste: oltre alle acque di casa raccolgono la pioggia.',
        anno='2020', fonte='ISTAT (censimento delle acque) e depuratori di Milano', licenza='CC BY 4.0'))

    TF = 'fogne/data/tariffe_citta_2025.csv'
    p = Prove()
    tt = p.v(TF, ix(TF, citta='Torino'), 'totale_m3')
    tr_ = p.v(TF, ix(TF, citta='Roma'), 'totale_m3')
    tm = p.v(TF, ix(TF, citta='Milano'), 'totale_m3')
    add(ordine(p, id='fogne-tariffe', pagina='fogne', diff='media',
        domanda='Fognatura e depurazione, euro per ogni metro cubo nel 2025: metti in ordine, dal più caro al meno caro.',
        elementi=[('Milano', tm, '€'), ('Roma', tr_, '€'), ('Torino', tt, '€')], unita='€', dec=2,
        spiega='Milano costa circa la metà di Torino. Le tariffe le fissano i gestori locali, quindi cambiano molto da una città all\'altra.',
        anno='2025', fonte='tariffe dei gestori del servizio idrico delle città', licenza='Uso con citazione, non aperta'))

    # ---------- ACQUA DEL SINDACO ----------
    PF = 'acqua-del-sindaco/data/pfas.json'
    p = Prove()
    n_ = p.v(PF, 'n')
    mx = p.v(PF, 'max')
    li = p.v(PF, 'limite')
    mxn = p.calc('round(p[1]*1000)')
    lin = p.calc('round(p[2]*1000)')
    add(vf(p, id='acqua-pfas', pagina='acqua-del-sindaco', diff='media',
        affermazione='Nel 2025 nessuna delle 1.260 analisi di MM sui PFAS nell\'acqua ha superato il limite di legge.',
        vero=mx < li, confronto=[('valore più alto', mxn, 'ng/L'), ('limite di legge', lin, 'ng/L')],
        spiega='Il valore più alto è stato 87 nanogrammi per litro, contro un limite di 100. Il margine non è enorme: la maggior parte delle analisi è però molto più bassa.',
        anno='2025', fonte='MM Spa, analisi dei PFAS nell\'acqua distribuita', licenza='Uso con citazione, non aperta'))

    # ---------- POLLINI ----------
    AR = 'pollini/data/ambrosia_regione_lombardia.csv'
    p = Prove()
    a24p = p.v(AR, ix(AR, stazione='Milano', anno=2024), 'totale_stagionale_granuli_m3')
    a25p = p.v(AR, ix(AR, stazione='Milano', anno=2025), 'totale_stagionale_granuli_m3')
    add(piuomeno(p, id='pollini-ambrosia', pagina='pollini', diff='difficile',
        domanda="Pollini di ambrosia a Milano, in tutta la stagione: più nel 2024 o nel 2025?",
        a=('stagione 2024', a24p, 'granuli'), b=('stagione 2025', a25p, 'granuli'),
        spiega='Nel 2024 sono stati 428, nel 2025 solo 183. L\'ambrosia cambia molto da un anno all\'altro, e a Milano ce n\'è meno che nei comuni attorno.',
        anno='2024 e 2025', fonte='note di Regione Lombardia sull\'ambrosia', licenza='Nessuna licenza dichiarata'))

    # ---------- MILANO TREMA ----------
    TJ = 'milano-trema/data/terremoti.json'
    tr = carica(TJ)
    p = Prove()
    ntot = p.v(TJ, 'n')
    add(numero(p, id='trema-110', pagina='milano-trema', diff='media',
        domanda='Quante volte, in quasi mille anni, un terremoto con epicentro altrove si è sentito a Milano, secondo gli studiosi?',
        v=ntot, lo=20, hi=400, passo=5, unita='volte',
        spiega='Sono 110 terremoti sentiti, ma soltanto i più forti sono arrivati fino a noi nei documenti: nei secoli antichi molti saranno andati persi.',
        anno='1065–2016', fonte='INGV, database macrosismico italiano DBMI15', licenza='CC BY 4.0'))

    p = Prove()
    ntot = p.v(TJ, 'n')
    s4 = [p.v(TJ, 'secoli', '[%d]' % i, 'sentiti_4piu') for i in range(11)]
    dn = [p.v(TJ, 'secoli', '[%d]' % i, 'danni') for i in range(11)]
    n4 = p.calc('sum(p[1:12])')
    nd = p.calc('sum(p[12:23])')
    ult = p.v(TJ, 'eventi', '[4]', 'anno')
    add(vf(p, id='trema-danni', pagina='milano-trema', diff='media',
        affermazione='L\'ultimo terremoto che ha fatto danni a Milano risale all\'Ottocento.',
        vero=(1800 <= ult < 1900), confronto=[('sentiti a Milano', ntot, 'terremoti'), ('sentiti bene', n4, 'terremoti'), ('con danni', nd, 'terremoti')],
        spiega='I terremoti con danni a Milano sono stati solo 3 in mille anni, l\'ultimo nel 1348. Quelli sentiti bene sono 36.',
        anno='1065–2016', fonte='INGV, database macrosismico italiano DBMI15', licenza='CC BY 4.0'))

    # ---------- ANTENNE ----------
    AN = 'antenne/data/riepilogo.json'
    p = Prove()
    cm = p.v(AN, 'mobile_per_gestore', 'CommsCon')
    wt = p.v(AN, 'mobile_per_gestore', 'WindTre')
    il = p.v(AN, 'mobile_per_gestore', 'Iliad')
    tim = p.v(AN, 'mobile_per_gestore', 'TIM')
    vo = p.v(AN, 'mobile_per_gestore', 'Vodafone')
    mic = p.v(AN, 'commscon', 'micro')
    acc = p.v(AN, 'commscon', 'impianti_accesi')
    add(vf(p, id='antenne-commscon', pagina='antenne', diff='media',
        affermazione="Il terzo gestore di Milano per numero di impianti mobili accesi non è un operatore telefonico ma una società di infrastrutture.",
        vero=(cm > wt and cm > il and cm < vo and cm < tim),
        confronto=[('CommsCon', cm, 'impianti'), ('WindTre', wt, 'impianti'), ('Iliad', il, 'impianti')],
        spiega='È CommsCon, con 369 impianti, quasi tutti microcelle. Il catasto non dice per quale operatore lavorino.',
        anno='2025', fonte='catasto delle antenne di ARPA Lombardia, pubblicato dal Comune di Milano', licenza='CC BY'))

    p = Prove()
    mob = p.v(AN, 'citta', 'mobile')
    pkm = p.v(AN, 'citta', 'per_km2')
    add(numero(p, id='antenne-mobile', pagina='antenne', diff='media',
        domanda='Quanti impianti di telefonia mobile accesi ci sono a Milano nel catasto del Comune (giugno 2025)?',
        v=mob, lo=500, hi=5000, passo=50, unita='impianti',
        spiega='Sono 2.097 impianti, circa 11,5 per chilometro quadrato. Un impianto è l\'insieme degli apparecchi di un gestore in un punto, non una singola antenna.',
        anno='2025', fonte='catasto delle antenne di ARPA Lombardia, pubblicato dal Comune di Milano', licenza='CC BY'))
    # ---------- CONSUMI ----------
    PJ = 'consumi/data/pagina.json'
    p = Prove()
    pe = p.v(PJ, 'acqua', 'milano', '[-1]', 'perdite_pct')
    pt = p.v(PJ, 'acqua', 'citta', '[0]', 'perdite_2024')
    pg = p.v(PJ, 'acqua', 'citta', '[1]', 'perdite_2024')
    add(numero(p, id='consumi-perdite', pagina='consumi', diff='media',
        domanda='Nel 2024 su cento litri di acqua immessi nei tubi di Milano, quanti si perdono per strada?',
        v=pe, lo=1, hi=45, passo=0.5, unita='litri', dec=1,
        confronto=[('Milano', pe, 'litri'), ('Torino', pt, 'litri'), ('Genova', pg, 'litri')],
        spiega='Meno di tutte le quattordici città del confronto: a Torino se ne perdono 22,2, a Genova 28,4.',
        anno='2024', fonte='ISTAT, censimento delle acque per uso civile', licenza='CC BY 4.0'))

    p = Prove()
    k15 = p.v(PJ, 'annuale', 'serie', '[0]', 'kwh_ab')
    k24 = p.v(PJ, 'annuale', 'serie', '[-1]', 'kwh_ab')
    dk = p.calc('round((1-p[1]/p[0])*100)')
    add(vf(p, id='consumi-corrente', pagina='consumi', diff='facile',
        affermazione='Nel 2024 ogni milanese ha consumato più corrente elettrica che nel 2015.',
        vero=k24 > k15, confronto=[('2015', k15, 'kWh'), ('2024', k24, 'kWh')],
        spiega='In nove anni il consumo a testa è sceso dell\'8%: da 5.070 a 4.673 kilowattora.',
        anno='2015 e 2024', fonte='ISTAT, consumi di energia elettrica per abitante', licenza='CC BY 4.0'))

    # ---------- AREA C ----------
    TB = 'area-c/data/tabelle.json'
    p = Prove()
    rap = p.v(TB, 'agosto', '[7]', 'rapporto')
    pct_ago = p.calc('round(p[0]*100)')
    dom = p.v(TB, 'anno', '[7]', 'domenica')
    fer = p.v(TB, 'anno', '[7]', 'lavorativi_media')
    pct_dom = p.calc('round(p[1]/p[2]*100)')
    add(numero(p, id='areac-agosto', pagina='area-c', diff='facile',
        domanda='Ad agosto 2023, in un giorno feriale, quanti veicoli entrano in Area C ogni cento di un feriale normale?',
        v=pct_ago, lo=10, hi=100, passo=1, unita='%',
        spiega='Ad agosto la città si svuota: ne entrano 50 ogni cento. Una domenica, con Area C spenta, sono il 70%.',
        anno='2023', fonte='Comune di Milano e AMAT, passaggi ai varchi di Area C', licenza='CC BY'))

    p = Prove()
    dom = p.v(TB, 'anno', '[7]', 'domenica')
    ago = p.v(TB, 'agosto', '[7]', 'agosto')
    add(piuomeno(p, id='areac-domenica', pagina='area-c', diff='difficile',
        domanda='Nel 2023, più ingressi in Area C in una domenica media o in un giorno feriale di agosto?',
        a=('domenica media', dom, 'ingressi'), b=('feriale di agosto', ago, 'ingressi'),
        spiega='Una domenica entrano circa 98 mila veicoli, in un feriale di agosto 70 mila. Un «ingresso» è un passaggio ai varchi, non un veicolo diverso.',
        anno='2023', fonte='Comune di Milano e AMAT, passaggi ai varchi di Area C', licenza='CC BY'))

    # ---------- METRO ----------
    PL = 'metro/data/passeggeri_linea_anno.csv'
    RK = 'metro/data/rete_km_passeggeri.csv'
    p = Prove()
    t19 = p.v(PL, ix(PL, anno=2019), 'totale')
    t24 = p.v(PL, ix(PL, anno=2024), 'totale')
    k19 = p.v(RK, ix(RK, anno=2019), 'km')
    k24m = p.v(RK, ix(RK, anno=2024), 'km')
    add(vf(p, id='metro-passeggeri', pagina='metro', diff='facile',
        affermazione='Nel 2024 il metro di Milano ha più passeggeri che nel 2019, grazie alla rete più lunga.',
        vero=(t24 > t19), confronto=[('2019', t19, 'milioni'), ('2024', t24, 'milioni')], dec=1,
        spiega='La rete è passata da 96,8 a 111,3 chilometri, ma i passeggeri sono calati: ogni chilometro porta meno gente di prima.',
        anno='2019 e 2024', fonte='AMAT, Report della Mobilità 2024; chilometri: ATM', licenza='Tutti i diritti riservati — solo cifre citate'))

    p = Prove()
    ys = list(range(2016, 2026))
    kms = [p.v(RK, ix(RK, anno=y), 'km') for y in ys]
    y5 = p.v(RK, ix(RK, anno=2022), 'anno')
    k22 = p.v(RK, ix(RK, anno=2022), 'km')
    k24b = p.v(RK, ix(RK, anno=2024), 'km')
    add(anno_q(p, id='metro-cinque-linee', pagina='metro', diff='facile',
        domanda='In che anno la rete del metro di Milano è arrivata a cinque linee?',
        v=y5, lo=2016, hi=2025, serie=serie_da(ys, [('km di rete', kms)]),
        spiega='Con la M4 la rete ha superato i cento chilometri: 102 nel 2022 e 111,3 nel 2024.',
        anno='2016–2025', fonte='ATM, Carte della Mobilità', licenza='Uso con citazione, non aperta'))

    # ---------- BICI ----------
    BS = 'bici/data/bikemi_serie.csv'
    p = Prove()
    sb = p.v(BS, ix(BS, anno=2025), 'noleggi_giorno_sb')
    ff = p.v(BS, ix(BS, anno=2025), 'noleggi_giorno_ff')
    sb17 = p.v(BS, ix(BS, anno=2017), 'noleggi_giorno_sb')
    add(piuomeno(p, id='bici-ff-bikemi', pagina='bici', diff='media',
        domanda='Nel 2025, al giorno, più noleggi con BikeMi o con le bici senza stazioni?',
        a=('BikeMi (con stazioni)', sb, 'noleggi'), b=('bici senza stazioni', ff, 'noleggi'),
        spiega='Dal 2023 le bici senza stazioni fanno più noleggi di BikeMi, che nel 2017 ne faceva 11.740 al giorno.',
        anno='2017, 2023 e 2025', fonte='Comune di Milano, servizi di sharing', licenza='CC BY'))

    p = Prove()
    ys = list(range(2011, 2026))
    vals = [p.v(BS, ix(BS, anno=y), 'noleggi_giorno_sb') for y in ys]
    y17 = p.v(BS, ix(BS, anno=2017), 'anno')
    n17 = p.v(BS, ix(BS, anno=2017), 'noleggi_giorno_sb')
    n25 = p.v(BS, ix(BS, anno=2025), 'noleggi_giorno_sb')
    cal = p.calc('round((1-p[%d]/p[%d])*100)' % (len(ys) + 2, len(ys) + 1))
    add(anno_q(p, id='bici-record-bikemi', pagina='bici', diff='media',
        domanda='In che anno BikeMi ha avuto più noleggi al giorno, in media?',
        v=y17, lo=2011, hi=2025, serie=serie_da(ys, [('noleggi al giorno', vals)]),
        spiega='Nel 2017: 11.740 noleggi al giorno. Nel 2025 sono 8.321, il 29% in meno.',
        anno='2011–2025', fonte='Comune di Milano, servizi di sharing', licenza='CC BY'))

    CK = 'bici/data/ciclabili_km_per_anno.csv'
    p = Prove()
    ys = list(range(2010, 2026))
    vals = [p.v(CK, ix(CK, anno_fine_lavori=y), 'nuovi_km') for y in ys]
    y20 = p.v(CK, ix(CK, anno_fine_lavori=2020), 'anno_fine_lavori')
    km20 = p.v(CK, ix(CK, anno_fine_lavori=2020), 'nuovi_km')
    km25 = p.v(CK, ix(CK, anno_fine_lavori=2025), 'nuovi_km')
    add(anno_q(p, id='bici-record-piste', pagina='bici', diff='difficile',
        domanda='In che anno sono stati finiti più chilometri di piste e corsie ciclabili (tra quelle che esistono oggi)?',
        v=y20, lo=2010, hi=2025, serie=serie_da(ys, [('km finiti nell\'anno', vals)]),
        spiega='Nel 2020 ne sono stati finiti 32, un record. Nel 2025 appena 4.',
        anno='2010–2025', fonte='Comune di Milano, itinerari ciclabili', licenza='CC BY'))

    # ---------- AUTO ----------
    SM = 'auto/data/serie_milano_comune.csv'
    p = Prove()
    au07 = p.v(SM, ix(SM, anno=2007), 'autovetture')
    au25 = p.v(SM, ix(SM, anno=2025), 'autovetture')
    pm07 = p.v(SM, ix(SM, anno=2007), 'per1000_auto')
    pm25 = p.v(SM, ix(SM, anno=2025), 'per1000_auto')
    add(piuomeno(p, id='auto-2007-2025', pagina='auto', diff='media',
        domanda='Auto intestate ai residenti di Milano: di più nel 2007 o nel 2025?',
        a=('auto nel 2007', au07, 'auto'), b=('auto nel 2025', au25, 'auto'),
        spiega='Nel 2007 erano 726.896, nel 2025 706.764. Gli abitanti sono aumentati, così le auto ogni mille abitanti sono scese da 584 a 519.',
        anno='2007 e 2025', fonte='Comune di Milano e ACI, parco auto', licenza='CC BY'))

    EC = 'auto/data/euro_milano_comune_2007_2025.csv'
    righe = carica(EC)
    an_ = [r['anno'] for r in righe]
    iy = primo_sorpasso(an_, [r['euro6'] for r in righe], [r['euro4'] for r in righe])
    p = Prove()
    e4 = [p.v(EC, '[%d]' % i, 'euro4') for i in range(len(righe))]
    e6 = [p.v(EC, '[%d]' % i, 'euro6') for i in range(len(righe))]
    idx = an_.index(iy)
    yy = p.v(EC, '[%d]' % idx, 'anno')
    v6 = p.v(EC, '[%d]' % idx, 'euro6')
    v4 = p.v(EC, '[%d]' % idx, 'euro4')
    v425 = p.v(EC, '[%d]' % (len(righe) - 1), 'euro4')
    add(anno_q(p, id='auto-euro6', pagina='auto', diff='difficile',
        domanda='In che anno le auto Euro 6 sono diventate, per la prima volta, più numerose delle Euro 4 a Milano?',
        v=yy, lo=2012, hi=2025, serie=serie_da(an_, [('Euro 4', e4), ('Euro 6', e6)]),
        spiega='Nel 2019 le Euro 6 erano 198.684 e le Euro 4 165.063. Nel 2025 le Euro 4 sono scese a 104.563.',
        anno='2007–2025', fonte='Comune di Milano e ACI, parco auto per classe Euro', licenza='CC BY'))

    AC = 'auto/data/areac_composizione_pct.csv'
    p = Prove()
    d17 = p.v(AC, ix(AC, y=2017), 'alim_diesel')
    d24 = p.v(AC, ix(AC, y=2024), 'alim_diesel')
    add(vf(p, id='areac-diesel', pagina='auto', diff='facile',
        affermazione='Nel 2024 i diesel sono ancora più di un terzo degli ingressi in Area C.',
        vero=d24 > 100 / 3, confronto=[('2017', d17, '%'), ('2024', d24, '%')], dec=1,
        spiega='I diesel sono il 21% degli ingressi, contro il 38,9% del 2017. Crescono gli ibridi.',
        anno='2017 e 2024', fonte='Comune di Milano e AMAT, passaggi ai varchi di Area C', licenza='CC BY'))

    # ---------- AEROPORTI ----------
    AA = 'aeroporti/data/annuale_tre_aeroporti.csv'
    p = Prove()
    ma = p.v(AA, ix(AA, aeroporto='Malpensa', anno=2025), 'passeggeri')
    bg = p.v(AA, ix(AA, aeroporto='Bergamo', anno=2025), 'passeggeri')
    li25 = p.v(AA, ix(AA, aeroporto='Linate', anno=2025), 'passeggeri')
    add(ordine(p, id='aeroporti-2025', pagina='aeroporti', diff='facile',
        domanda='Passeggeri nel 2025: metti in ordine i tre aeroporti, dal più affollato al meno affollato.',
        elementi=[('Linate', li25, 'passeggeri'), ('Malpensa', ma, 'passeggeri'), ('Bergamo', bg, 'passeggeri')], unita='passeggeri',
        spiega='Malpensa ha 31,2 milioni di passeggeri, più di Bergamo e Linate messi insieme.',
        anno='2025', fonte='Eurostat, passeggeri per aeroporto', licenza='CC BY 4.0'))

    ys = list(range(2004, 2026))
    bgs = {y: carica(AA)[int(ix(AA, aeroporto='Bergamo', anno=y)[1:-1])]['passeggeri'] for y in ys}
    lis = {y: carica(AA)[int(ix(AA, aeroporto='Linate', anno=y)[1:-1])]['passeggeri'] for y in ys}
    ysor = primo_sorpasso(ys, [bgs[y] for y in ys], [lis[y] for y in ys])
    p = Prove()
    vb = [p.v(AA, ix(AA, aeroporto='Bergamo', anno=y), 'passeggeri') for y in ys]
    vl = [p.v(AA, ix(AA, aeroporto='Linate', anno=y), 'passeggeri') for y in ys]
    ysr = p.v(AA, ix(AA, aeroporto='Bergamo', anno=ysor), 'anno')
    sb_ = p.v(AA, ix(AA, aeroporto='Bergamo', anno=ysor), 'passeggeri')
    sl_ = p.v(AA, ix(AA, aeroporto='Linate', anno=ysor), 'passeggeri')
    add(anno_q(p, id='aeroporti-sorpasso', pagina='aeroporti', diff='difficile',
        domanda='In che anno Bergamo ha superato Linate per passeggeri, per la prima volta?',
        v=ysr, lo=2004, hi=2025, serie=serie_da(ys, [('Bergamo', vb), ('Linate', vl)]),
        spiega='Nel 2015 Bergamo ha avuto 10,4 milioni di passeggeri e Linate 9,6, e da allora è sempre rimasta davanti.',
        anno='2004–2025', fonte='Eurostat, passeggeri per aeroporto', licenza='CC BY 4.0'))

    # ---------- INCROCI ----------
    SA = 'incroci/data/serie_annuale.csv'
    p = Prove()
    inc24 = p.v(SA, ix(SA, anno=2024), 'incidenti')
    inc10 = p.v(SA, ix(SA, anno=2010), 'incidenti')
    ca_ = p.calc('round((1-p[0]/p[1])*100)')
    add(numero(p, id='incroci-2024', pagina='incroci', diff='media',
        domanda='Quanti incidenti stradali con feriti o morti ci sono stati a Milano nel 2024, secondo i dati ISTAT?',
        v=inc24, lo=2000, hi=20000, passo=100, unita='incidenti',
        confronto=[('2010', inc10, 'incidenti'), ('2024', inc24, 'incidenti')],
        spiega='Nel 2010 erano 12.085: in quattordici anni sono calati del 36%.',
        anno='2010 e 2024', fonte='ISTAT, incidenti stradali (microdati pubblicati da Regione Lombardia)', licenza='CC BY 4.0'))

    p = Prove()
    ms, ps_ = [], []
    for y in range(2010, 2025):
        ms.append(p.v(SA, ix(SA, anno=y), 'morti'))
    for y in range(2010, 2025):
        ps_.append(p.v(SA, ix(SA, anno=y), 'ped_morti'))
    mt = p.calc('sum(p[0:15])')
    pt_ = p.calc('sum(p[15:30])')
    altri = p.calc('sum(p[0:15])-sum(p[15:30])')
    quota = p.calc('round(sum(p[15:30])/sum(p[0:15])*100)')
    add(vf(p, id='incroci-pedoni', pagina='incroci', diff='difficile',
        affermazione='Dal 2010 al 2024 più di metà dei morti sulle strade di Milano era un pedone.',
        vero=(pt_ / mt > 1 / 2), confronto=[('pedoni', pt_, 'morti'), ('altri', altri, 'morti')],
        spiega='Sono 251 morti a piedi su 676, il 37%. Eppure i pedoni sono coinvolti in circa un incidente su sette.',
        anno='2010–2024', fonte='ISTAT, incidenti stradali (microdati pubblicati da Regione Lombardia)', licenza='CC BY 4.0'))

    # ---------- PENDOLARI ----------
    SP = 'pendolari/data/serie_totali.csv'
    p = Prove()
    l91 = p.v(SP, ix(SP, anno=1991, motivo='lavoro'), 'entra')
    s91 = p.v(SP, ix(SP, anno=1991, motivo='studio'), 'entra')
    l21 = p.v(SP, ix(SP, anno=2021, motivo='lavoro'), 'entra')
    s21 = p.v(SP, ix(SP, anno=2021, motivo='studio'), 'entra')
    t91 = p.calc('p[0]+p[1]')
    t21 = p.calc('p[2]+p[3]')
    add(numero(p, id='pendolari-2021', pagina='pendolari', diff='media',
        domanda='Nel 2021 (stima), quante persone entrano ogni giorno a Milano per lavoro o studio, abitando in un altro comune?',
        v=t21, lo=100000, hi=1000000, passo=10000, unita='persone',
        confronto=[('1991', t91, 'persone'), ('2021', t21, 'persone')],
        spiega='Circa 490 mila. Nel 1991 erano 470 mila: in trent\'anni il numero è cambiato poco, è cambiato chi viene (più lavoro, meno studio).',
        anno='1991 e 2021', fonte='ISTAT, matrici del pendolarismo', licenza='CC BY 4.0'))

    p = Prove()
    q91 = p.v(SP, ix(SP, anno=1991, motivo='lavoro'), 'quota_di_fuori')
    q21 = p.v(SP, ix(SP, anno=2021, motivo='lavoro'), 'quota_di_fuori')
    c91 = p.calc('round(p[0]*100,1)')
    c21 = p.calc('round(p[1]*100,1)')
    add(vf(p, id='pendolari-lavoro', pagina='pendolari', diff='media',
        affermazione='Nel 2021 più di metà dei posti di lavoro a Milano è occupata da persone che abitano in un altro comune.',
        vero=q21 > 0.5, confronto=[('1991', c91, '%'), ('2021', c21, '%')], dec=1,
        spiega='Sono il 51,5%, contro il 45,9% del 1991. Il 2021 è una stima fatta con un modello.',
        anno='1991 e 2021', fonte='ISTAT, matrici del pendolarismo', licenza='CC BY 4.0'))

    # ---------- PARCHEGGI ----------
    PR = 'parcheggi/data/riepilogo.json'
    p = Prove()
    campi = p.v(PR, 'sintesi', 'campi')
    akm = p.v(PR, 'sintesi', 'area_km2')
    qc = p.v(PR, 'sintesi', 'quota_citta_pct')
    add(numero(p, id='parcheggi-campi', pagina='parcheggi', diff='difficile',
        domanda='Lo spazio degli stalli per le auto in strada, a Milano, equivale a quanti campi da calcio? (è una stima)',
        v=campi, lo=50, hi=1500, passo=10, unita='campi',
        spiega='Circa 3,6 chilometri quadrati, il 2,0% della città. È una stima: il Comune non pubblica quanti stalli ci siano.',
        anno='2025', fonte='Comune di Milano, ambiti della sosta; auto: ACI', licenza='CC BY'))

    # ---------- ATTESA ALLA FERMATA ----------
    FJ = 'attesa-fermata/data/fermate.json'
    p = Prove()
    o8 = p.v(FJ, 'linee', '[2]', 'ore', '8')
    o22 = p.v(FJ, 'linee', '[2]', 'ore', '22')
    m8 = p.calc('round(60/p[0],1)')
    m22 = p.calc('round(60/p[1],1)')
    add(numero(p, id='attesa-m3', pagina='attesa-fermata', diff='facile',
        domanda='Alle 8 di un martedì, secondo gli orari programmati, ogni quanti minuti passa un treno della M3 in una direzione?',
        v=m8, lo=0, hi=15, passo=0.5, unita='min', dec=1,
        spiega='Uno ogni 3,3 minuti. Alle dieci di sera l\'attesa sale a 8,6 minuti. Sono orari scritti, non attese vere: ritardi e corse saltate non ci sono.',
        anno='2026', fonte='orari del trasporto pubblico (GTFS), Comune di Milano', licenza='CC BY'))

    # ---------- NOMI DELLE FERMATE ----------
    NF = 'nomi-fermate/data/riepilogo.json'
    p = Prove()
    don = p.v(NF, 'donne')
    uom = p.v(NF, 'uomini')
    per = p.v(NF, 'persone_reali')
    add(vf(p, id='nomi-una-donna', pagina='nomi-fermate', diff='facile',
        affermazione='Tra le persone reali a cui sono intitolate le stazioni del metro di Milano c\'è una sola donna.',
        vero=(don == 1), confronto=[('uomini', uom, 'persone'), ('donne', don, 'persone')],
        spiega='È Veronica Gambara, poetessa del Cinquecento. Le persone ricordate dalle stazioni sono 33 in tutto.',
        anno='2026', fonte='orari ATM (GTFS) del Comune di Milano; nomi: Wikidata', licenza='CC BY'))

    p = Prove()
    luo = p.v(NF, 'tab', 'luogo', 'tot')
    per = p.v(NF, 'persone_reali')
    add(piuomeno(p, id='nomi-luoghi-persone', pagina='nomi-fermate', diff='facile',
        domanda='Le stazioni del metro di Milano hanno più spesso il nome di un luogo o di una persona reale?',
        a=('nome di un luogo', luo, 'stazioni'), b=('nome di una persona reale', per, 'stazioni'),
        spiega='61 stazioni hanno il nome di un luogo, quasi la metà del totale. Le persone reali sono 33.',
        anno='2026', fonte='orari ATM (GTFS) del Comune di Milano; nomi: Wikidata', licenza='CC BY'))

    # ---------- BICI, AUTO O MEZZI ----------
    QJ = 'bici-auto-mezzi/data/quote.json'
    p = Prove()
    a21 = p.v(QJ, 'quote', '[23]', 'auto_pct')
    a08 = p.v(QJ, 'quote', '[7]', 'auto_pct')
    b08 = p.v(QJ, 'quote', '[7]', 'bici_pct')
    add(numero(p, id='bam-sera-auto', pagina='bici-auto-mezzi', diff='media',
        domanda='Secondo un modello di calcolo, alle nove di sera su cento viaggi tra due quartieri di Milano, in quanti arriva prima l\'auto?',
        v=a21, lo=5, hi=100, passo=1, unita='viaggi',
        confronto=[('alle otto', a08, 'viaggi'), ('alle nove di sera', a21, 'viaggi')],
        spiega='Alle nove di sera l\'auto vince in 57 viaggi su cento: la sera le strade sono libere. Alle otto ne vince solo 11, e la bici ne vince 88.',
        anno='2026', fonte='calcoli su orari ATM e Trenord e strade di OpenStreetMap', licenza='ODbL'))

    p = Prove()
    bm = p.v(QJ, 'tempi', '[7]', 'bici_min')
    am = p.v(QJ, 'tempi', '[7]', 'auto_porta_a_porta_min')
    add(piuomeno(p, id='bam-tempo-8', pagina='bici-auto-mezzi', diff='facile',
        domanda='Alle 8 di mattina, per un viaggio medio tra due quartieri, serve più tempo in bici o in auto (porta a porta)?',
        a=('in bici', bm, 'min'), b=('in auto, porta a porta', am, 'min'), dec=1,
        spiega='In bici 37,3 minuti, in auto 46,7: alle otto le strade sono piene. Sono tempi calcolati dal modello, non misurati.',
        anno='2026', fonte='calcoli su orari ATM e Trenord e strade di OpenStreetMap', licenza='ODbL'))
    # @@FINE@@
    return out
