"""Domande del modulo c_cultura: scuole, sport, giustizia, sicurezza, cultura, memoria, elezioni, terzo settore."""
from mazzo import Prove, piuomeno, numero, vf, ordine, anno_q, serie_da


def domande():
    out = []

    # ------------------------------------------------------------------ PIU O MENO
    p = Prove()
    a = p.v('luoghi-cercati/data/riepilogo.json', 'top', 'all', '[n=stadio Giuseppe Meazza]', 'v')
    b = p.v('luoghi-cercati/data/riepilogo.json', 'top', 'all', '[n=Duomo di Milano]', 'v')
    ia = p.v('luoghi-cercati/data/riepilogo.json', 'top', 'all', '[n=stadio Giuseppe Meazza]', 'it')
    ib = p.v('luoghi-cercati/data/riepilogo.json', 'top', 'all', '[n=Duomo di Milano]', 'it')
    fa = p.calc('round(100-p[2],1)')
    fb = p.calc('round(100-p[3],1)')
    out.append(piuomeno(p, id='sansiro-duomo', pagina='luoghi-cercati', diff='media',
        domanda='Su Wikipedia, in tutte le lingue, da luglio 2015 a ottobre 2026: quale luogo di Milano è stato letto di più?',
        a=('Stadio di San Siro (Meazza)', a, 'letture'), b=('Duomo di Milano', b, 'letture'),
        spiega='San Siro batte il Duomo: l\'%s%% delle sue letture è in lingue diverse dall\'italiano, per il Duomo il %s%%.' % (str(round(fa)), str(round(fb))),
        anno='2015–2026', fonte='Wikimedia, letture delle voci di Wikipedia', licenza='CC0'))

    p = Prove()
    a = p.v('reati/data/tipi_comune.json', '[codice=SWINCYB]', 'den_2024')
    b = p.v('reati/data/tipi_comune.json', '[codice=BURGTHEF]', 'den_2024')
    a6 = p.v('reati/data/tipi_comune.json', '[codice=SWINCYB]', 'den_2006')
    b6 = p.v('reati/data/tipi_comune.json', '[codice=BURGTHEF]', 'den_2006')
    out.append(piuomeno(p, id='truffe-furti-casa', pagina='reati', diff='media',
        domanda='Nel 2024 a Milano sono state denunciate più truffe e frodi informatiche o più furti in abitazione?',
        a=('Truffe e frodi informatiche, 2024', a, 'denunce'), b=('Furti in abitazione, 2024', b, 'denunce'),
        spiega='Le truffe sono più di tre volte i furti in casa. Nel 2006 era il contrario: %s truffe contro %s furti in abitazione.' % (f'{a6:,}'.replace(',', '.'), f'{b6:,}'.replace(',', '.')),
        anno='2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('milano-raccontata/data/stats.json', 'film', 'tot')
    b = p.v('milano-raccontata/data/stats.json', 'libro', 'tot')
    fd = p.v('milano-raccontata/data/stats.json', 'film', 'dopo')
    ld = p.v('milano-raccontata/data/stats.json', 'libro', 'dopo')
    fq = p.calc('round(p[2]/p[0]*100)')
    lq = p.calc('round(p[3]/p[1]*100)')
    out.append(piuomeno(p, id='film-libri', pagina='milano-raccontata', diff='facile',
        domanda='Tra le opere ambientate o girate a Milano ce ne sono di più nei film o nei libri?',
        a=('Film', a, 'opere'), b=('Libri', b, 'opere'),
        spiega='Film più dei libri. Ma ben pochi dicono dove, a Milano: solo il %d%% dei film e il %d%% dei libri nomina un luogo preciso.' % (fq, lq),
        anno='2026', fonte='Wikidata e Wikipedia, opere ambientate a Milano', licenza='CC0'))

    p = Prove()
    a = p.v('musei/data/riepilogo.json', 'sorprese', 'brera_2024')
    b = p.v('musei/data/riepilogo.json', 'sorprese', 'cenacolo_2024')
    va = p.v('musei/data/riepilogo.json', 'sorprese', 'brera_var_2024')
    vb = p.v('musei/data/riepilogo.json', 'sorprese', 'cenacolo_var_2024')
    out.append(piuomeno(p, id='brera-cenacolo', pagina='musei', diff='difficile',
        domanda='Nel 2024 chi ha avuto più visitatori: la Pinacoteca di Brera o il Cenacolo Vinciano?',
        a=('Pinacoteca di Brera, 2024', a, 'visitatori'), b=('Cenacolo Vinciano, 2024', b, 'visitatori'),
        spiega='Brera sorpassa di poco il Cenacolo. Rispetto al 2019 Brera ha il %s%% di visitatori in più, il Cenacolo il %s%%.' % (str(round(va)), str(round(vb))),
        anno='2019–2024', fonte='Ministero della Cultura, visitatori dei musei statali', licenza='Uso con citazione, non aperta'))

    p = Prove()
    a = p.v('terzo-settore/data/citta.csv', '[citta=Milano]', 'per_10000')
    b = p.v('terzo-settore/data/citta.csv', '[citta=Firenze]', 'per_10000')
    alt = p.v('terzo-settore/data/citta.csv', '[citta=Milano]', 'altri_per_10000')
    out.append(piuomeno(p, id='terzo-firenze', pagina='terzo-settore', diff='facile',
        domanda='Enti del Terzo settore ogni diecimila abitanti: ne ha di più Milano o Firenze?',
        a=('Milano', a, 'ogni 10.000 ab.'), b=('Firenze', b, 'ogni 10.000 ab.'), dec=1,
        spiega='Firenze ne ha molti di più. Milano è nona tra le grandi città, ma prima per gli «altri enti» (%s ogni diecimila abitanti).' % str(alt).replace('.', ','),
        anno='2026', fonte='Ministero del Lavoro, Registro unico del Terzo settore; ISTAT, residenti', licenza='Uso con citazione, non aperta'))

    p = Prove()
    a = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=pasticceria_gelateria]', 'pct')
    b = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=bar_caffe]', 'pct')
    an = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=pasticceria_gelateria]', 'n')
    bn = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=bar_caffe]', 'n')
    ac = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=pasticceria_gelateria]', 'cessate')
    bc = p.v('botteghe/data/riepilogo.json', 'per_tipo', '[settore=bar_caffe]', 'cessate')
    out.append(piuomeno(p, id='botteghe-cessate', pagina='botteghe', diff='difficile',
        domanda='Tra le botteghe storiche di Milano, quali risultano più spesso «cessate»: pasticcerie e gelaterie o bar e caffè?',
        a=('Pasticcerie e gelaterie cessate', a, '%'), b=('Bar e caffè cessati', b, '%'), dec=1,
        spiega='Pasticcerie e gelaterie: %d su %d. Bar e caffè: solo %d su %d, quasi mai chiudono.' % (ac, an, bc, bn),
        anno='2026', fonte='Comune di Milano, Albo delle botteghe storiche; Regione Lombardia, negozi e locali storici', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('consiglio/data/riepilogo.json', 'sesso', '2021-2026', 'F', 'pct_presenze')
    b = p.v('consiglio/data/riepilogo.json', 'sesso', '2021-2026', 'M', 'pct_presenze')
    fo = p.v('consiglio/data/riepilogo.json', 'sesso', '2016-2021', 'F', 'pct_presenze')
    mo = p.v('consiglio/data/riepilogo.json', 'sesso', '2016-2021', 'M', 'pct_presenze')
    out.append(piuomeno(p, id='consiglio-donne-uomini', pagina='consiglio', diff='media',
        domanda='Nel mandato 2021–2026 chi è stato più presente alle sedute del consiglio comunale di Milano: le donne o gli uomini?',
        a=('Consigliere donne', a, '%'), b=('Consiglieri uomini', b, '%'), dec=1,
        spiega='Gli uomini, con 5 punti in più. Nel mandato 2016–2021 era il contrario: donne %s%%, uomini %s%%.' % (str(fo).replace('.', ','), str(mo).replace('.', ',')),
        anno='2021–2026', fonte='Comune di Milano, dati aperti sul consiglio comunale', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('telefoni-pubblici/data/pagina.json', 'citta', '[nome=Milano]', 'per_10000')
    b = p.v('telefoni-pubblici/data/pagina.json', 'citta', '[nome=Roma]', 'per_10000')
    fi = p.v('telefoni-pubblici/data/pagina.json', 'citta', '[nome=Firenze]', 'per_10000')
    tm = p.v('telefoni-pubblici/data/pagina.json', 'citta', '[nome=Milano]', 'telefoni')
    out.append(piuomeno(p, id='telefoni-roma', pagina='telefoni-pubblici', diff='facile',
        domanda='Telefoni pubblici ogni diecimila abitanti, nell\'elenco TIM: ne ha di più Milano o Roma?',
        a=('Milano', a, 'ogni 10.000 ab.'), b=('Roma', b, 'ogni 10.000 ab.'), dec=2,
        spiega='Milano: %s telefoni, secondo posto tra le grandi città dopo Firenze (%s ogni diecimila abitanti).' % (str(tm), str(fi).replace('.', ',')),
        anno='2026', fonte='TIM, elenco dei telefoni pubblici; ISTAT, residenti', licenza='Uso con citazione, non aperta'))

    p = Prove()
    a = p.v('ristoranti/data/riepilogo.json', 'cucine', 'mix', '[0]', '[1]')
    b = p.v('ristoranti/data/riepilogo.json', 'cucine', 'mix', '[1]', '[1]')
    n = p.v('ristoranti/data/riepilogo.json', 'cucine', 'n')
    pa = p.v('ristoranti/data/riepilogo.json', 'cucine', 'mix', '[0]', '[2]')
    pb = p.v('ristoranti/data/riepilogo.json', 'cucine', 'mix', '[1]', '[2]')
    out.append(piuomeno(p, id='pizza-italiana', pagina='ristoranti', diff='difficile',
        domanda='Tra i ristoranti e fast food di Milano con la cucina indicata, ce ne sono di più che fanno pizza o cucina italiana?',
        a=('Pizza', a, 'locali'), b=('Cucina italiana', b, 'locali'),
        spiega='Su %s locali con la cucina indicata, il %s%% fa pizza e il %s%% cucina italiana: sommati, meno di sei su dieci.' % (f'{n:,}'.replace(',', '.'), str(pa).replace('.', ','), str(pb).replace('.', ',')),
        anno='2026', fonte='OpenStreetMap, locali con cucina indicata', licenza='ODbL'))

    p = Prove()
    a = p.v('scala/data/direttori_decenni.json', 'direttori', '[n=Riccardo Muti]', 't')
    b = p.v('scala/data/direttori_decenni.json', 'direttori', '[n=Gianandrea Gavazzeni]', 't')
    c = p.v('scala/data/direttori_decenni.json', 'direttori', '[n=Nino Sanzogno]', 't')
    out.append(piuomeno(p, id='scala-muti', pagina='scala', diff='difficile',
        domanda='Alla Scala, dal 1943, chi ha diretto più recite: Riccardo Muti o Gianandrea Gavazzeni?',
        a=('Riccardo Muti', a, 'recite'), b=('Gianandrea Gavazzeni', b, 'recite'),
        spiega='Muti è il direttore più presente. Al terzo posto Nino Sanzogno, con %d recite.' % c,
        anno='1943–2026', fonte='Teatro alla Scala, locandine delle serate', licenza='Uso con citazione, non aperta'))

    # ------------------------------------------------------------------ NUMERO
    p = Prove()
    q = p.v('sport/data/riepilogo.json', 'R', 'gruppi', 'piscine', 'quota_residenti_entro15')
    t = p.v('sport/data/riepilogo.json', 'R', 'gruppi', 'tutti', 'quota_residenti_entro15')
    pc = p.v('sport/data/riepilogo.json', 'R', 'gruppi', 'piscine_comunali', 'quota_residenti_entro15')
    v = p.calc('round(p[0]*100,1)')
    vt = p.calc('round(p[1]*100,1)')
    vc = p.calc('round(p[2]*100,1)')
    out.append(numero(p, id='piscine-15min', pagina='sport', diff='facile',
        domanda='Quanti milanesi su cento arrivano a piedi, in quindici minuti, a una piscina aperta a tutti?',
        v=v, lo=20, hi=100, passo=1, unita='%', dec=1,
        confronto=[('Un impianto sportivo qualsiasi', vt, '%'), ('Una piscina aperta a tutti', v, '%'), ('Una piscina del Comune', vc, '%')],
        spiega='Quasi tutti hanno un impianto sportivo vicino, ma le piscine sono più rare. Contando solo quelle del Comune si scende al %s%%.' % str(round(vc)),
        anno='2025', fonte='Comune di Milano, Regione Lombardia e OpenStreetMap, impianti sportivi; residenti: anagrafe del Comune', licenza='CC BY 4.0'))

    p = Prove()
    q = p.v('citta-15-minuti/data/riepilogo.json', 'citta', 'tutti')
    bi = p.v('citta-15-minuti/data/riepilogo.json', 'tipi', '[t=biblioteche]', 'q')
    fa = p.v('citta-15-minuti/data/riepilogo.json', 'tipi', '[t=farmacie]', 'q')
    v = p.calc('round(p[0]*100,1)')
    vb = p.calc('round(p[1]*100,1)')
    vf_ = p.calc('round(p[2]*100,1)')
    out.append(numero(p, id='dieci-servizi', pagina='citta-15-minuti', diff='media',
        domanda='Quanti milanesi su cento raggiungono a piedi, in quindici minuti, tutti e dieci i servizi essenziali (farmacia, scuola, parco, biblioteca…)?',
        v=v, lo=5, hi=95, passo=1, unita='%', dec=1,
        confronto=[('Tutti e 10 i servizi', v, '%'), ('Una biblioteca', vb, '%'), ('Una farmacia', vf_, '%')],
        spiega='Il servizio che manca di più è la biblioteca. La farmacia invece è sotto casa per quasi tutti.',
        anno='2025', fonte='Comune di Milano e OpenStreetMap, servizi e rete pedonale; residenti: anagrafe del Comune', licenza='CC BY 4.0'))

    p = Prove()
    n = p.v('cani/data/riepilogo.json', 'comune', 'aree')
    parchi = p.v('cani/data/riepilogo.json', 'comune', 'id_area')
    mq = p.v('cani/data/riepilogo.json', 'comune', 'mq_mediana')
    out.append(numero(p, id='aree-cani', pagina='cani', diff='facile',
        domanda='Quante aree per i cani ci sono nell\'elenco del Comune di Milano?',
        v=n, lo=100, hi=800, passo=10, unita='aree',
        spiega='Sono distribuite in %d parchi e giardini. Metà delle aree è più piccola di %d m², poco più di tre campi da tennis.' % (parchi, mq),
        anno='2026', fonte='Comune di Milano, aree per i cani', licenza='CC BY 4.0'))

    p = Prove()
    mi = p.v('tribunale/data/riepilogo.json', 'n', 't_dur_co_mi_2025', 'v')
    it = p.v('tribunale/data/riepilogo.json', 'n', 't_dur_co_it_2025', 'v')
    m19 = p.v('tribunale/data/riepilogo.json', 'n', 't_dur_co_mi_2019', 'v')
    out.append(numero(p, id='causa-giorni', pagina='tribunale', diff='media',
        domanda='Nel 2025, quanti giorni dura in media una causa civile ordinaria al tribunale di Milano?',
        v=mi, lo=200, hi=1500, passo=10, unita='giorni',
        confronto=[('Milano', mi, 'giorni'), ('Italia', it, 'giorni')],
        spiega='Milano è più veloce della media italiana, ma nel 2019 bastavano %d giorni: le cause si sono allungate.' % m19,
        anno='2025', fonte='Ministero della Giustizia, durata dei procedimenti civili', licenza='Uso con citazione, non aperta'))

    p = Prove()
    sv = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=MILANO "F. DI CATALDO" SAN VITTORE]', 'presenti_ogni_100_posti')
    det = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=MILANO "F. DI CATALDO" SAN VITTORE]', 'detenuti_presenti')
    pos = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=MILANO "F. DI CATALDO" SAN VITTORE]', 'capienza_regolamentare')
    it = p.v('carceri/data/italia_lombardia_mensile.csv', '[data=2026-09-30]', 'presenti_ogni_100_posti')
    out.append(numero(p, id='san-vittore-100', pagina='carceri', diff='media',
        domanda='A fine settembre 2026, a San Vittore, quanti detenuti c\'erano ogni cento posti previsti?',
        v=sv, lo=80, hi=260, passo=1, unita='', dec=0,
        confronto=[('San Vittore', sv, ''), ('Italia', it, '')],
        spiega='Erano %s detenuti per %d posti. In tutta Italia, in media, %s ogni cento posti.' % (f'{det:,}'.replace(',', '.'), pos, str(it).replace('.', ',')),
        anno='2026', fonte='Ministero della Giustizia, detenuti presenti per istituto', licenza='Uso con citazione, non aperta'))

    p = Prove()
    mi = p.v('reati-citta/data/confronto_denunce_percezione_2024.csv', '[comune=Milano]', 'pct_buio_poco_o_per_niente_sicuro_2024')
    fi = p.v('reati-citta/data/confronto_denunce_percezione_2024.csv', '[comune=Firenze]', 'pct_buio_poco_o_per_niente_sicuro_2024')
    bo = p.v('reati-citta/data/confronto_denunce_percezione_2024.csv', '[comune=Bologna]', 'pct_buio_poco_o_per_niente_sicuro_2024')
    out.append(numero(p, id='buio-poco-sicuri', pagina='reati-citta', diff='media',
        domanda='Nel 2024, quanti milanesi su cento si sentono poco o per niente sicuri camminando al buio da soli nella loro zona?',
        v=mi, lo=5, hi=75, passo=1, unita='%', dec=1,
        confronto=[('Milano', mi, '%'), ('Firenze', fi, '%'), ('Bologna', bo, '%')],
        spiega='Tra i comuni più grandi Milano è prima per chi si sente poco sicuro al buio, anche se per denunce per abitante è seconda, dopo Firenze.',
        anno='2024', fonte='ISTAT, indagine «Aspetti della vita quotidiana»', licenza='CC BY 4.0'))

    p = Prove()
    mi = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Milano]', 'tot')
    na = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Napoli]', 'tot')
    ro = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Roma]', 'tot')
    imm = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Milano]', 'imm')
    az = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Milano]', 'az')
    out.append(numero(p, id='beni-confiscati-n', pagina='beni-confiscati', diff='media',
        domanda='Quanti beni confiscati alla criminalità organizzata ci sono nel comune di Milano (case, box, negozi, terreni, aziende)?',
        v=mi, lo=100, hi=1500, passo=5, unita='beni',
        confronto=[('Milano', mi, 'beni'), ('Napoli', na, 'beni'), ('Roma', ro, 'beni')],
        spiega='Sono %d immobili e %d aziende: è il comune del Nord con più beni confiscati.' % (imm, az),
        anno='2026', fonte='Agenzia nazionale per i beni confiscati e Comune di Milano', licenza='IODL 2.0'))

    p = Prove()
    n = p.v('terzo-settore/data/riepilogo.json', 'runts', 'milano')
    it = p.v('terzo-settore/data/riepilogo.json', 'runts', 'italia')
    qm = p.v('terzo-settore/data/riepilogo.json', 'runts', 'quota_milano_pct')
    out.append(numero(p, id='enti-terzo-settore', pagina='terzo-settore', diff='difficile',
        domanda='Quanti enti del Terzo settore (volontariato, promozione sociale, cooperative sociali, fondazioni) hanno sede a Milano?',
        v=n, lo=1000, hi=9000, passo=100, unita='enti',
        spiega='Sono il %s%% dei %s iscritti in tutta Italia al registro nazionale.' % (str(qm).replace('.', ','), f'{it:,}'.replace(',', '.')),
        anno='2026', fonte='Ministero del Lavoro, Registro unico del Terzo settore', licenza='Uso con citazione, non aperta'))

    p = Prove()
    tot = p.v('vie/data/percentuali.json', 'percentuali', '[scope=con santi]', 'quota_donne_su_tutte_le_strade_ferma')
    per = p.v('vie/data/percentuali.json', 'percentuali', '[scope=con santi]', 'quota_donne_su_persone_ferma')
    nd = p.v('vie/data/percentuali.json', 'percentuali', '[scope=con santi]', 'donne_sicure')
    ns = p.v('vie/data/percentuali.json', 'percentuali', '[scope=con santi]', 'strade_totali')
    v = p.calc('round(p[0]*100,1)')
    vp = p.calc('round(p[1]*100,1)')
    out.append(numero(p, id='vie-donne', pagina='vie', diff='facile',
        domanda='Su cento tra vie e piazze di Milano, quante portano il nome di una donna?',
        v=v, lo=0, hi=15, passo=0.1, unita='%', dec=1,
        confronto=[('Tutte le vie e piazze', v, '%'), ('Solo le vie intitolate a persone', vp, '%')],
        spiega='Sono %d su %s. Contando solo le vie intitolate a persone, le donne arrivano al %s%%.' % (nd, f'{ns:,}'.replace(',', '.'), str(vp).replace('.', ',')),
        anno='2026', fonte='OpenStreetMap, Wikidata e registro dei numeri civici del Comune di Milano', licenza='ODbL'))

    p = Prove()
    mi = p.v('poverta-educativa/data/dati.json', 'nidi_rank_2024', '[3]', '[1]')
    it = p.v('poverta-educativa/data/dati.json', 'nidi_rank_2024', '[9]', '[1]')
    fi = p.v('poverta-educativa/data/dati.json', 'nidi_rank_2024', '[0]', '[1]')
    out.append(numero(p, id='nidi-100', pagina='poverta-educativa', diff='difficile',
        domanda='Nel 2024, quanti posti negli asili nido ci sono a Milano ogni cento bambini tra 0 e 2 anni?',
        v=mi, lo=10, hi=90, passo=1, unita='posti', dec=1,
        confronto=[('Milano', mi, 'posti'), ('Italia', it, 'posti'), ('Firenze', fi, 'posti')],
        spiega='Milano è quarta tra le grandi città e ben sopra l\'Italia. Metà dei posti, però, è di nidi privati.',
        anno='2024', fonte='ISTAT, servizi socio-educativi per la prima infanzia', licenza='CC BY 4.0'))

    p = Prove()
    mmg = p.v('medici-farmacie/data/riepilogo.json', 'residenti_14piu_per_mmg')
    mmg2 = p.v('medici-farmacie/data/riepilogo.json', 'bambini_0_13_per_pls')
    out.append(numero(p, id='residenti-per-medico', pagina='medici-farmacie', diff='difficile',
        domanda='A Milano, in media, quanti residenti dai quattordici anni in su ci sono per ogni medico di famiglia?',
        v=mmg, lo=800, hi=3500, passo=25, unita='residenti',
        spiega='Per i bambini va meglio: ogni pediatra di libera scelta ha in media %s bambini fino a tredici anni.' % format(round(mmg2), ',').replace(',', '.'),
        anno='2025', fonte='Comune di Milano, elenco dei medici di famiglia; residenti: anagrafe del Comune', licenza='CC BY-NC (solo uso non commerciale)'))

    # ------------------------------------------------------------------ VERO / FALSO
    p = Prove()
    t13 = p.v('biblioteche/data/riepilogo.json', 'totali', '2013')
    t19 = p.v('biblioteche/data/riepilogo.json', 'totali', '2019')
    t25 = p.v('biblioteche/data/riepilogo.json', 'totali', '2025')
    out.append(vf(p, id='prestiti-2019', pagina='biblioteche', diff='facile',
        affermazione='Nel 2025 le biblioteche del Comune di Milano hanno fatto meno prestiti che nel 2019, prima della pandemia.',
        vero=t25 < t19, confronto=[('2013', t13, 'prestiti'), ('2019', t19, 'prestiti'), ('2025', t25, 'prestiti')],
        spiega='Quasi un milione di prestiti, ma ancora meno del 2019. Il calo viene soprattutto dai DVD e dai CD, non dai libri.',
        anno='2025', fonte='Comune di Milano, prestiti delle biblioteche', licenza='CC BY 4.0'))

    p = Prove()
    n12 = p.v('scuole/data/riepilogo.json', 'residenti_0_anni', '2012')
    n25 = p.v('scuole/data/riepilogo.json', 'residenti_0_anni', '2025')
    pct = p.calc('round((p[1]/p[0]-1)*100)')
    out.append(vf(p, id='bimbi-zero-anni', pagina='scuole', diff='facile',
        affermazione='Dal 2012 al 2025 i bambini di 0 anni che abitano a Milano sono diminuiti di oltre un quarto.',
        vero=n25 < n12 * 0.75, confronto=[('2012', n12, 'bambini'), ('2025', n25, 'bambini')],
        spiega='Da %s a %s: %d%%. È da qui che parte il calo degli alunni nelle scuole.' % (f'{n12:,}'.replace(',', '.'), f'{n25:,}'.replace(',', '.'), pct),
        anno='2012–2025', fonte='Comune di Milano, residenti per età', licenza='CC BY 4.0'))

    p = Prove()
    t = p.v('sport/data/riepilogo.json', 'R', 'gruppi', 'tutti', 'quota_residenti_entro15')
    pi = p.v('sport/data/riepilogo.json', 'R', 'gruppi', 'piscine', 'quota_residenti_entro15')
    vt = p.calc('round(p[0]*100,1)')
    vp = p.calc('round(p[1]*100,1)')
    out.append(vf(p, id='impianti-vicini', pagina='sport', diff='facile',
        affermazione='Più del 99% dei milanesi arriva a piedi, in quindici minuti, a un impianto sportivo, ma meno di due su tre a una piscina aperta a tutti.',
        vero=(t > 0.99 and pi < 2 / 3), confronto=[('Un impianto qualsiasi', vt, '%'), ('Una piscina aperta a tutti', vp, '%')],
        spiega='Palestre e campi sono ovunque; le piscine sono più rare e in più di un quartiere su tre servono più di quindici minuti a piedi.', dec=1,
        anno='2025', fonte='Comune di Milano, Regione Lombardia e OpenStreetMap, impianti sportivi', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('omicidi/data/area_milanese_italia_1983_2024.csv', '[anno=2024]', 'tasso')
    b = p.v('omicidi/data/area_milanese_italia_1983_2024.csv', '[anno=2024]', 'italia_tasso')
    a90 = p.v('omicidi/data/area_milanese_italia_1983_2024.csv', '[anno=1990]', 'tasso')
    out.append(vf(p, id='omicidi-sopra-italia', pagina='omicidi', diff='facile',
        affermazione='Nel 2024 il tasso di omicidi dell\'area milanese (Milano, Monza e Brianza, Lodi) è stato più alto di quello dell\'Italia.',
        vero=a > b, confronto=[('Area milanese', a, 'ogni 100.000 ab.'), ('Italia', b, 'ogni 100.000 ab.')], dec=2,
        spiega='L\'area milanese è sotto la media italiana, come quasi sempre dal 1983. Nel 1990 il suo tasso era %s ogni centomila.' % str(a90).replace('.', ','),
        anno='2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY 4.0'))

    p = Prove()
    m19 = p.v('tribunale/data/riepilogo.json', 'n', 't_dur_co_mi_2019', 'v')
    m25 = p.v('tribunale/data/riepilogo.json', 'n', 't_dur_co_mi_2025', 'v')
    out.append(vf(p, id='cause-piu-lunghe', pagina='tribunale', diff='media',
        affermazione='Dal 2019 al 2025 le cause civili ordinarie al tribunale di Milano sono diventate più lunghe.',
        vero=m25 > m19, confronto=[('2019', m19, 'giorni'), ('2025', m25, 'giorni')],
        spiega='Da %d a %d giorni in media. Nello stesso periodo la durata è scesa in tutta Italia, ma Milano resta sotto la media nazionale.' % (m19, m25),
        anno='2019–2025', fonte='Ministero della Giustizia, durata dei procedimenti civili', licenza='Uso con citazione, non aperta'))

    p = Prove()
    c17 = p.v('violenza-donne/data/1522_annuale_italia_lombardia.csv', '[anno=2017]', 'chiamate_valide_utenti_italia')
    c24 = p.v('violenza-donne/data/1522_annuale_italia_lombardia.csv', '[anno=2024]', 'chiamate_valide_utenti_italia')
    out.append(vf(p, id='chiamate-1522', pagina='violenza-donne', diff='facile',
        affermazione='Le chiamate valide al numero antiviolenza nazionale in Italia nel 2024 sono state più di tre volte quelle del 2017.',
        vero=c24 > 3 * c17, confronto=[('2017', c17, 'chiamate'), ('2024', c24, 'chiamate')],
        spiega='Da qualche anno le chiamate si contano con una nuova piattaforma, quindi il confronto non è del tutto esatto: ma la crescita è molto forte.',
        anno='2017–2024', fonte='ISTAT, chiamate al 1522', licenza='CC BY 4.0'))

    p = Prove()
    d = p.v('statue/data/pagina.json', 'genere', '[nome=Tutte le opere]', 'donne')
    pe = p.v('statue/data/pagina.json', 'genere', '[nome=Tutte le opere]', 'persone')
    qu = p.v('statue/data/pagina.json', 'genere', '[nome=Tutte le opere]', 'quota')
    qv = p.v('statue/data/pagina.json', 'genere', '[nome=Vie intitolate a persone]', 'quota')
    out.append(vf(p, id='statue-donne', pagina='statue', diff='facile',
        affermazione='Tra le persone raffigurate nelle statue e nei monumenti di Milano, le donne sono più del 10%.',
        vero=qu > 10, confronto=[('Statue e monumenti', qu, '%'), ('Vie intitolate a persone', qv, '%')], dec=1,
        spiega='Solo %d su %d, il %s%%.' % (d, pe, str(qu).replace('.', ',')),
        anno='2026', fonte='Wikidata, OpenStreetMap, catalogo ICCD e Comune di Milano: statue e monumenti', licenza='CC0'))

    p = Prove()
    tot = p.v('beni-confiscati/data/riepilogo.json', 'aziende', 'uscite')
    liq = p.v('beni-confiscati/data/riepilogo.json', 'aziende', 'liquidate')
    ven = p.v('beni-confiscati/data/riepilogo.json', 'aziende', 'vendute')
    out.append(vf(p, id='aziende-liquidate', pagina='beni-confiscati', diff='media',
        affermazione='A Milano, delle aziende confiscate alla criminalità organizzata e uscite dalla confisca, più di nove su dieci sono state liquidate.',
        vero=liq / tot > 0.9, confronto=[('Aziende uscite dalla confisca', tot, ''), ('Liquidate', liq, ''), ('Vendute', ven, '')],
        spiega='Su %d aziende uscite, %d sono state liquidate e %d vendute: quasi nessuna prosegue l\'attività.' % (tot, liq, ven),
        anno='2026', fonte='Agenzia nazionale per i beni confiscati', licenza='IODL 2.0'))

    p = Prove()
    a = p.v('botteghe/data/riepilogo.json', 'piu_antiche_aperte', '[n=Antica trattoria Bagutto]', 'a')
    cento = p.v('botteghe/data/riepilogo.json', 'cento_anni')
    tot = p.v('botteghe/data/riepilogo.json', 'tot')
    out.append(vf(p, id='bottega-antica', pagina='botteghe', diff='media',
        affermazione='La bottega storica più antica di Milano, l\'Antica trattoria Bagutto, è stata fondata nel Duecento.',
        vero=1200 < a < 1300, confronto=[('Botteghe con più di un secolo', cento, 'botteghe'), ('Botteghe storiche in tutto', tot, 'botteghe')],
        spiega='Bagutto nasce nel %d. Su %d botteghe storiche, %d hanno più di un secolo.' % (a, tot, cento),
        anno='2026', fonte='Comune di Milano e Regione Lombardia, elenchi delle botteghe storiche', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('consiglio/data/riepilogo.json', 'mandati', '2016-2021', 'pct_presenze')
    b = p.v('consiglio/data/riepilogo.json', 'mandati', '2021-2026', 'pct_presenze')
    vo = p.v('consiglio/data/riepilogo.json', 'mandati', '2021-2026', 'pct_votazioni')
    out.append(vf(p, id='consiglio-presenze', pagina='consiglio', diff='media',
        affermazione='Nel mandato 2021–2026 i consiglieri comunali di Milano sono stati più presenti alle sedute che nel mandato 2016–2021.',
        vero=b > a, confronto=[('2016–2021', a, '%'), ('2021–2026', b, '%')], dec=1,
        spiega='Le presenze sono scese da %s%% a %s%%. E in media i consiglieri partecipano solo al %s%% delle votazioni.' % (str(a).replace('.', ','), str(b).replace('.', ','), str(vo).replace('.', ',')),
        anno='2016–2026', fonte='Comune di Milano, dati aperti sul consiglio comunale', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('amministratori/data/riepilogo.json', 'cifre', 'consiglio_donne_milano', '2016')
    b = p.v('amministratori/data/riepilogo.json', 'cifre', 'consiglio_donne_milano', '2025')
    it = p.v('amministratori/data/riepilogo.json', 'cifre', 'consiglio_donne_italia', '2025')
    out.append(vf(p, id='consiglio-donne', pagina='amministratori', diff='difficile',
        affermazione='A fine 2025 le donne sono una quota più grande del consiglio comunale di Milano che a fine 2016.',
        vero=b > a, confronto=[('Milano 2016', a, '%'), ('Milano 2025', b, '%'), ('Italia 2025', it, '%')], dec=1,
        spiega='Nel 2016 erano il %s%%, nel 2025 il %s%%: in dieci anni la quota è scesa. In Italia nel 2025 la quota è quasi uguale: %s%%.' % (str(a).replace('.', ','), str(b).replace('.', ','), str(it).replace('.', ',')),
        anno='2016–2025', fonte='Ministero dell\'Interno, anagrafe degli amministratori locali', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('targhe/data/pagina.json', 'posatori', 'elenco', '[0]', '[1]')
    b = p.v('targhe/data/pagina.json', 'posatori', 'elenco', '[1]', '[1]')
    c = p.v('targhe/data/pagina.json', 'posatori', 'elenco', '[2]', '[1]')
    out.append(vf(p, id='targhe-anpi', pagina='targhe', diff='media',
        affermazione='Tra le lapidi e le targhe di Milano con l\'ente indicato, quello che ne ha messe di più è l\'ANPI, l\'associazione dei partigiani.',
        vero=a > b, confronto=[('ANPI', a, 'targhe'), ('Forze armate e dell\'ordine', b, 'targhe'), ('Comune e Municipi', c, 'targhe')],
        spiega='L\'ANPI mette soprattutto le targhe della Resistenza; le forze armate quelle di guerra. Seguono il Comune e i Municipi.',
        anno='2026', fonte='Pietre della Memoria (ANMIG), OpenStreetMap e Wikidata: lapidi e targhe', licenza='Autorizzazione dichiarata (ANMIG)'))

    # ------------------------------------------------------------------ ORDINE
    p = Prove()
    a = p.v('cani/data/riepilogo.json', 'nil', 'piu', '[n=Lorenteggio]', 'p')
    b = p.v('cani/data/riepilogo.json', 'nil', 'meno', '[n=Affori]', 'p')
    c = p.v('cani/data/riepilogo.json', 'nil', 'meno', '[n=Duomo]', 'p')
    out.append(ordine(p, id='cani-quartieri', pagina='cani', diff='media',
        domanda='Metti in ordine, dal più alto al più basso: aree per i cani ogni centomila abitanti, nel 2024.',
        elementi=[('Duomo', c, ''), ('Lorenteggio', a, ''), ('Affori', b, '')], unita='ogni 100.000 ab.', dec=1,
        spiega='A Lorenteggio ci sono più aree per abitante che in ogni altro quartiere in classifica. In centro, al Duomo, ce n\'è una sola.',
        anno='2024', fonte='Comune di Milano, aree per i cani e residenti', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('citta-15-minuti/data/riepilogo.json', 'tipi', '[t=vicinato]', 'q')
    b = p.v('citta-15-minuti/data/riepilogo.json', 'tipi', '[t=parchi]', 'q')
    c = p.v('citta-15-minuti/data/riepilogo.json', 'tipi', '[t=biblioteche]', 'q')
    va, vb, vc = p.calc('round(p[0]*100,1)'), p.calc('round(p[1]*100,1)'), p.calc('round(p[2]*100,1)')
    out.append(ordine(p, id='servizi-15', pagina='citta-15-minuti', diff='facile',
        domanda='Metti in ordine, dal più alto al più basso: quanti milanesi raggiungono a piedi in quindici minuti questi servizi.',
        elementi=[('Una biblioteca', vc, '%'), ('Un negozio alimentare di vicinato', va, '%'), ('Un parco grande (oltre cinquemila metri quadrati)', vb, '%')], unita='%', dec=1,
        spiega='Il negozio sotto casa c\'è per quasi tutti. La biblioteca è il servizio che manca di più.',
        anno='2025', fonte='Comune di Milano e OpenStreetMap, servizi e rete pedonale', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('reati/data/tipi_comune.json', '[codice=DAMAGE]', 'den_2024')
    b = p.v('reati/data/tipi_comune.json', '[codice=SWINCYB]', 'den_2024')
    c = p.v('reati/data/tipi_comune.json', '[codice=ROBBER]', 'den_2024')
    b6 = p.v('reati/data/tipi_comune.json', '[codice=SWINCYB]', 'den_2006')
    out.append(ordine(p, id='reati-tipi', pagina='reati', diff='facile',
        domanda='Metti in ordine, dal più alto al più basso: denunce a Milano nel 2024.',
        elementi=[('Rapine', c, 'denunce'), ('Danneggiamenti', a, 'denunce'), ('Truffe e frodi informatiche', b, 'denunce')], unita='denunce',
        spiega='I danneggiamenti sono molto più delle rapine. Le truffe e le frodi informatiche sono molto cresciute: nel 2006 erano %s.' % f'{b6:,}'.replace(',', '.'),
        anno='2006–2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('omicidi/data/grandi_comuni_2021_2024.csv', '[comune=Napoli]', 'tasso')
    b = p.v('omicidi/data/grandi_comuni_2021_2024.csv', '[comune=Bari]', 'tasso')
    c = p.v('omicidi/data/grandi_comuni_2021_2024.csv', '[comune=Milano]', 'tasso')
    out.append(ordine(p, id='omicidi-grandi-comuni', pagina='omicidi', diff='difficile',
        domanda='Metti in ordine, dal più alto al più basso: tasso di omicidi ogni centomila abitanti nel 2021–2024.',
        elementi=[('Milano', c, ''), ('Napoli', a, ''), ('Bari', b, '')], unita='ogni 100.000 ab.', dec=2,
        spiega='Napoli è prima tra i grandi comuni. Milano è sesta: più in basso di quanto molti penserebbero.',
        anno='2021–2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('tribunale/data/durata_per_tribunale_2025.csv', '[tribunale=Bari]', 'durata_cause_ordinarie_giorni_2025')
    b = p.v('tribunale/data/durata_per_tribunale_2025.csv', '[tribunale=Roma]', 'durata_cause_ordinarie_giorni_2025')
    c = p.v('tribunale/data/durata_per_tribunale_2025.csv', '[tribunale=Milano]', 'durata_cause_ordinarie_giorni_2025')
    out.append(ordine(p, id='tribunali-durata', pagina='tribunale', diff='media',
        domanda='Metti in ordine, dal più lento al più veloce: durata media delle cause civili ordinarie nel 2025.',
        elementi=[('Milano', c, 'giorni'), ('Bari', a, 'giorni'), ('Roma', b, 'giorni')], unita='giorni',
        spiega='Delle tre, Milano è la più rapida. A Bari una causa dura quasi il doppio.',
        anno='2025', fonte='Ministero della Giustizia, durata dei procedimenti civili', licenza='Uso con citazione, non aperta'))

    p = Prove()
    a = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=MILANO "F. DI CATALDO" SAN VITTORE]', 'presenti_ogni_100_posti')
    b = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=OPERA "I C.R."]', 'presenti_ogni_100_posti')
    c = p.v('carceri/data/classifica_istituti_ultimo_mese.csv', '[istituto=BOLLATE "II C.R."]', 'presenti_ogni_100_posti')
    out.append(ordine(p, id='carceri-pieni', pagina='carceri', diff='media',
        domanda='Metti in ordine, dal più pieno al meno pieno: detenuti ogni cento posti nelle carceri di Milano, settembre 2026.',
        elementi=[('Bollate', c, ''), ('San Vittore', a, ''), ('Opera', b, '')], unita='ogni 100 posti', dec=1,
        spiega='Tutte e tre hanno più detenuti che posti. San Vittore è la più affollata, Bollate la meno.',
        anno='2026', fonte='Ministero della Giustizia, detenuti presenti per istituto', licenza='Uso con citazione, non aperta'))

    p = Prove()
    a = p.v('scuole/data/riepilogo.json', 'serie', 'primaria', 'iscritti', '[15]')
    b = p.v('scuole/data/riepilogo.json', 'serie', 'sec1', 'iscritti', '[15]')
    c = p.v('scuole/data/riepilogo.json', 'serie', 'infanzia', 'iscritti', '[15]')
    out.append(ordine(p, id='scuole-iscritti', pagina='scuole', diff='facile',
        domanda='Metti in ordine, dal più alto al più basso: alunni nelle scuole di Milano, anno scolastico 2024/25.',
        elementi=[('Scuola dell\'infanzia', c, 'alunni'), ('Scuola media', b, 'alunni'), ('Scuola primaria', a, 'alunni')], unita='alunni',
        spiega='La primaria è il grado più numeroso. All\'infanzia gli iscritti sono in calo da anni, perché nascono meno bambini.',
        anno='2024', fonte='Comune di Milano e Ministero dell\'Istruzione, alunni delle scuole', licenza='CC BY 4.0'))

    p = Prove()
    a = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Palermo]', 'tot')
    b = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Roma]', 'tot')
    c = p.v('beni-confiscati/data/confronto_citta.csv', '[comune=Milano]', 'tot')
    out.append(ordine(p, id='beni-grandi-citta', pagina='beni-confiscati', diff='media',
        domanda='Metti in ordine, dal più alto al più basso: beni confiscati alla criminalità organizzata nel comune.',
        elementi=[('Milano', c, 'beni'), ('Palermo', a, 'beni'), ('Roma', b, 'beni')], unita='beni',
        spiega='Palermo è in testa con grande distacco. Milano però è il primo comune del Nord.',
        anno='2026', fonte='Agenzia nazionale per i beni confiscati', licenza='IODL 2.0'))

    p = Prove()
    a = p.v('musei/data/riepilogo.json', 'lombardia_top10_2024', '[0]', 'visitatori')
    b = p.v('musei/data/riepilogo.json', 'lombardia_top10_2024', '[1]', 'visitatori')
    c = p.v('musei/data/riepilogo.json', 'lombardia_top10_2024', '[4]', 'visitatori')
    out.append(ordine(p, id='musei-lombardia', pagina='musei', diff='facile',
        domanda='Metti in ordine, dal più visitato al meno visitato nel 2024: tre musei di Milano.',
        elementi=[('Raccolte artistiche del Castello', c, 'visitatori'), ('Museo del Duomo', a, 'visitatori'), ('La Triennale', b, 'visitatori')], unita='visitatori',
        spiega='Il Museo del Duomo è il più visitato di tutta la Lombardia. La Triennale è seconda.',
        anno='2024', fonte='Regione Lombardia, visitatori dei musei riconosciuti', licenza='Tutti i diritti riservati — solo cifre citate'))

    # ------------------------------------------------------------------ ANNO
    p = Prove()
    anni = list(range(1983, 2021))
    vals = [p.v('omicidi/data/area_milanese_italia_1983_2024.csv', '[anno=%d]' % y, 'omicidi') for y in anni]
    picco = p.v('omicidi/data/area_milanese_italia_1983_2024.csv', '[omicidi=96]', 'anno')
    out.append(anno_q(p, id='omicidi-picco', pagina='omicidi', diff='media',
        domanda='In che anno ci furono più omicidi nell\'area milanese (Milano, Monza e Brianza, Lodi), dal 1983?',
        v=picco, lo=1983, hi=2005,
        serie=serie_da(anni, [('Omicidi nell\'area milanese', vals)]),
        spiega='Fu il 1990, con 96 omicidi. Da allora sono calati dell\'82% in tasso, quanto in tutta Italia.',
        anno='1983–2024', fonte='ISTAT, delitti denunciati dalle forze di polizia', licenza='CC BY 4.0'))

    p = Prove()
    anni = p.v('reati/data/denunce_comune.json', 'anni')
    den = p.v('reati/data/denunce_comune.json', 'denunce')
    picco = p.v('reati/data/denunce_comune.json', 'picco', 'anno')
    pn = p.v('reati/data/denunce_comune.json', 'picco', 'n')
    out.append(anno_q(p, id='reati-picco', pagina='reati', diff='media',
        domanda='In che anno le denunce di reati nel comune di Milano sono state più numerose, dal 2004 al 2024?',
        v=picco, lo=2002, hi=2024,
        serie=serie_da(anni, [('Denunce nel comune di Milano', den)]),
        spiega='Il massimo è del 2007, con 174.040 denunce. Il minimo è del 2020, l\'anno del lockdown.',
        anno='2004–2024', fonte='Comune di Milano e ISTAT, delitti denunciati', licenza='CC BY 4.0'))

    p = Prove()
    ys = [1985, 1990, 1993, 1997, 2001, 2006, 2011, 2016, 2021]
    aff = []
    for y in ys:
        v = p.v('elezioni/data/comunali_blocchi.json', 'elezioni', '[anno=%d]' % y, 'votanti')
        e = p.v('elezioni/data/comunali_blocchi.json', 'elezioni', '[anno=%d]' % y, 'elettori')
        n = len(p.letture)
        aff.append(p.calc('round(p[%d]/p[%d]*100,1)' % (n - 2, n - 1)))
    an = p.v('elezioni/data/comunali_blocchi.json', 'elezioni', '[anno=2016]', 'anno')
    out.append(anno_q(p, id='affluenza-sotto-60', pagina='elezioni', diff='media',
        domanda='Alle elezioni comunali di Milano, in che anno l\'affluenza è scesa per la prima volta sotto il sessanta per cento?',
        v=an, lo=1990, hi=2021,
        serie=serie_da(ys, [('Affluenza alle Comunali (%)', aff)]),
        spiega='Nel 2016 votò il 54,7%. Nel 2021 solo il 47,7%: meno di un elettore su due. Nel 1985 aveva votato l\'88,6%.',
        anno='1985–2021', fonte='Comune di Milano, risultati delle elezioni comunali', licenza='CC BY 4.0'))

    p = Prove()
    ys = list(range(2017, 2026))
    tot = []
    for y in ys:
        base = len(p.letture)
        for k in ('razziale', 'politica', 'IMI', 'altro'):
            p.v('pietre-inciampo/data/riepilogo.json', 'anni', '[anno=%d]' % y, k)
        tot.append(p.calc('p[%d]+p[%d]+p[%d]+p[%d]' % (base, base + 1, base + 2, base + 3)))
    cib = p.v('pietre-inciampo/data/riepilogo.json', 'cibeno_2024')
    an = p.v('pietre-inciampo/data/riepilogo.json', 'anni', '[anno=2024]', 'anno')
    out.append(anno_q(p, id='pietre-record', pagina='pietre-inciampo', diff='difficile',
        domanda='In che anno furono posate più pietre d\'inciampo a Milano? (dal 2017 al 2025)',
        v=an, lo=2016, hi=2027,
        serie=serie_da(ys, [('Pietre posate', tot)]),
        spiega='Il 2024, con %d pietre: %d furono posate in due soli giorni di novembre per i fucilati di Cibeno. Dal 2018, negli altri anni, ne furono posate da 23 a 31.' % (tot[ys.index(2024)], cib),
        anno='2017–2025', fonte='Comitato Pietre d\'inciampo Milano; Wikipedia', licenza='Uso con citazione, non aperta'))

    p = Prove()
    anni = p.v('scuole/data/riepilogo.json', 'anni')
    isc = p.v('scuole/data/riepilogo.json', 'serie', 'infanzia', 'iscritti')
    an = p.v('scuole/data/riepilogo.json', 'anni', '[2]')
    calo = p.calc('round((p[1][15]/p[1][2]-1)*100)')
    out.append(anno_q(p, id='infanzia-picco', pagina='scuole', diff='media',
        domanda='In che anno scolastico (indichiamo l\'anno d\'inizio) ci furono più bambini iscritti alle scuole dell\'infanzia di Milano?',
        v=an, lo=2008, hi=2025,
        serie=serie_da(anni, [('Iscritti all\'infanzia', isc)]),
        spiega='Fu il 2011, con 33.007 bambini. Oggi sono 26.522, il %d%% in meno, perché nascono meno bambini.' % abs(calo),
        anno='2009–2024', fonte='Comune di Milano, iscritti alle scuole dell\'infanzia', licenza='CC BY 4.0'))

    p = Prove()
    ys = list(range(2013, 2025))
    ch = [p.v('violenza-donne/data/1522_annuale_italia_lombardia.csv', '[anno=%d]' % y, 'chiamate_valide_utenti_italia') for y in ys]
    an = p.v('violenza-donne/data/1522_annuale_italia_lombardia.csv', '[anno=2017]', 'anno')
    out.append(anno_q(p, id='1522-minimo', pagina='violenza-donne', diff='difficile',
        domanda='In che anno, tra il 2013 e il 2024, le chiamate valide al numero antiviolenza nazionale sono state meno numerose in Italia?',
        v=an, lo=2013, hi=2024,
        serie=serie_da(ys, [('Chiamate valide al 1522', ch)]),
        spiega='Il 2017, con 17.616 chiamate (nel 2013 erano 32.367). Poi la crescita, anche per il nuovo modo di contarle.',
        anno='2013–2024', fonte='ISTAT, chiamate al 1522', licenza='CC BY 4.0'))

    return out
