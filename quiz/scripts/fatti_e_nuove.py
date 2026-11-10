"""Domande del modulo e_nuove: dieci pagine nuove (università, ospedali, catasto, economia, lavoro,
Olimpiadi, case e energia, negozi, proverbi, il tuo anno).

Le pagine «olimpiadi»: le opere vengono da Simico, che non dichiara una licenza; in fonti.json la
pagina ha solo Eurostat (passeggeri degli aeroporti). Perciò qui ci sono solo domande sugli aeroporti.
"""
from mazzo import Prove, carica, piuomeno, numero, vf, ordine, quartiere, anno_q, serie_da


def ix(rel, **cond):
    """Posizione (nel file) della prima riga che soddisfa tutte le condizioni."""
    for i, r in enumerate(carica(rel)):
        if all(str(r.get(k)) == str(v) for k, v in cond.items()):
            return '[%d]' % i
    raise KeyError((rel, cond))


def domande():
    out = []
    out += universita()
    out += ospedali()
    out += catasto()
    out += economia()
    out += lavoro()
    out += olimpiadi()
    out += case_energia()
    out += negozi()
    out += proverbi()
    out += il_tuo_anno()
    return out


# ====================================================================== UNIVERSITÀ
def universita():
    out = []
    L = 'IODL 2.0'
    F = 'MUR, iscritti agli atenei (Anagrafe nazionale degli studenti)'
    cit = 'universita/data/citta_2024.csv'
    mi = 'universita/data/iscritti_milano_italia.csv'
    ate = 'universita/data/iscritti_per_ateneo.csv'
    riep = 'universita/data/riepilogo.json'

    p = Prove()
    roma = p.v(cit, ix(cit, citta='Roma'), 'iscritti_2024_25')
    mil = p.v(cit, ix(cit, citta='Milano'), 'iscritti_2024_25')
    man = p.calc('p[0]-p[1]')
    out.append(vf(p, id='uni-milano-roma', pagina='universita', diff='media',
        affermazione='Nell’anno accademico 2024/25 gli atenei di Milano hanno più iscritti di quelli di Roma.',
        vero=mil > roma, confronto=[('Roma', roma, 'iscritti'), ('Milano', mil, 'iscritti')],
        spiega='Roma ne ha 213.811 e Milano 211.428: ne mancano 2.383. Milano è seconda in Italia, ma cresce più in fretta. Non sono contate le università che fanno lezione soprattutto online.',
        anno='2024/25', fonte=F, licenza=L))

    p = Prove()
    b00 = p.v(cit, ix(cit, citta='Bologna'), 'iscritti_2000_01')
    b24 = p.v(cit, ix(cit, citta='Bologna'), 'iscritti_2024_25')
    out.append(vf(p, id='uni-bologna-calo', pagina='universita', diff='difficile',
        affermazione='Gli atenei di Bologna hanno meno iscritti oggi che nell’anno accademico 2000/01.',
        vero=b24 < b00, confronto=[('2000/01', b00, 'iscritti'), ('2024/25', b24, 'iscritti')],
        spiega='Erano 100.989 e sono 85.369. Anche Napoli, Bari e Palermo ne hanno meno di allora; Milano e Torino molti di più.',
        anno='2000–2024', fonte=F, licenza=L))

    p = Prove()
    m00 = p.v(mi, ix(mi, anno_accademico='2000/2001'), 'milano')
    m24 = p.v(mi, ix(mi, anno_accademico='2024/2025'), 'milano')
    i00 = p.v(mi, ix(mi, anno_accademico='2000/2001'), 'italia_senza_telematiche')
    i24 = p.v(mi, ix(mi, anno_accademico='2024/2025'), 'italia_senza_telematiche')
    cm = p.calc('round((p[1]/p[0]-1)*100, 1)')
    ci = p.calc('round((p[3]/p[2]-1)*100, 1)')
    out.append(numero(p, id='uni-crescita', pagina='universita', diff='facile',
        domanda='Di quanto sono cresciuti gli iscritti agli atenei di Milano tra l’anno accademico 2000/01 e il 2024/25?',
        v=cm, lo=-20, hi=80, passo=1, unita='%', dec=1,
        confronto=[('Italia (senza le università online)', ci, '%'), ('Milano', cm, '%')],
        spiega='Milano è cresciuta del 20,1%. Nel resto d’Italia, senza le università che fanno lezione online, gli iscritti sono aumentati solo dell’1,7%.',
        anno='2000–2024', fonte=F, licenza=L))

    p = Prove()
    prv = 'universita/data/provenienza_2024.csv'
    righe = carica(prv)
    tot_idx = []
    for i in range(len(righe)):
        p.v(prv, '[%d]' % i, 'iscritti_con_corso_a_milano')
        tot_idx.append(p.i())
    lomb = p.v(prv, ix(prv, regione_di_residenza='Lombardia'), 'iscritti_con_corso_a_milano')
    tot = p.calc('sum(p[0:%d])' % len(righe))
    fuori = p.calc('round((sum(p[0:%d])-p[%d])/sum(p[0:%d])*100, 1)' % (len(righe), len(righe), len(righe)))
    out.append(numero(p, id='uni-fuori-lombardia', pagina='universita', diff='media',
        domanda='Tra gli studenti che nel 2024/25 seguono un corso a Milano, quanti su 100 risiedono fuori dalla Lombardia (estero compreso)?',
        v=fuori, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        spiega='Quasi uno su tre: 31 su 100. La residenza è quella dell’anagrafe e non dice dove lo studente abita davvero durante gli studi.',
        anno='2024/25', fonte=F, licenza=L))

    p = Prove()
    bo = p.v(riep, 'atenei', '[id=bocconi]', 'intl_pct')
    bi = p.v(riep, 'atenei', '[id=bicocca]', 'intl_pct')
    out.append(vf(p, id='uni-bocconi-estero', pagina='universita', diff='difficile',
        affermazione='Alla Bocconi, nel 2024/25, più di un iscritto su quattro ha preso il diploma di scuola superiore all’estero.',
        vero=bo > 25, confronto=[('Bicocca', bi, '%'), ('Bocconi', bo, '%')], dec=1,
        spiega='Alla Bocconi sono 26,9 su 100. Alla Bicocca solo 2,7.',
        anno='2024/25', fonte=F, licenza=L))

    p = Prove()
    s00 = p.v(ate, ix(ate, anno_accademico='2000/2001', ateneo='San Raffaele'), 'totale')
    s24 = p.v(ate, ix(ate, anno_accademico='2024/2025', ateneo='San Raffaele'), 'totale')
    rt = p.calc('round(p[1]/p[0], 1)')
    out.append(numero(p, id='uni-sanraffaele', pagina='universita', diff='difficile',
        domanda='Quante volte più iscritti ha oggi l’università Vita-Salute San Raffaele rispetto all’anno accademico 2000/01?',
        v=rt, lo=1, hi=20, passo=0.1, unita='volte', dec=1,
        spiega='Gli iscritti sono passati da 696 a 5.829: oltre otto volte tanti. È la crescita più grande dei sette atenei di Milano.',
        anno='2000–2024', fonte=F, licenza=L))

    p = Prove()
    ar = 'universita/data/aree_di_studio_2024.csv'
    ed = p.v(ar, ix(ar, area='Educazione e Formazione'), 'donne_pct')
    ic = p.v(ar, ix(ar, area='Informatica e Tecnologie ICT'), 'donne_pct')
    out.append(numero(p, id='uni-donne-educazione', pagina='universita', diff='facile',
        domanda='Tra gli iscritti ai corsi di Educazione e Formazione dei sette atenei di Milano, nel 2024/25, quante su 100 sono donne?',
        v=ed, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('Informatica e tecnologie ICT', ic, 'su 100'), ('Educazione e formazione', ed, 'su 100')],
        spiega='Nove su dieci: 91,1. A Informatica e tecnologie ICT sono 18,3 su 100.',
        anno='2024/25', fonte=F, licenza=L))
    return out


# ====================================================================== OSPEDALI
def ospedali():
    out = []
    L = 'IODL 2.0'
    F = 'Ministero della Salute, posti letto delle strutture ospedaliere; Comune di Milano'
    sr = 'ospedali/data/letti_milano_per_anno.csv'
    cc = 'ospedali/data/confronto_citta_2023.csv'
    rp = 'ospedali/data/riepilogo.json'

    p = Prove()
    m = p.v(sr, ix(sr, anno=2023), 'm1000')
    it = p.v(sr, ix(sr, anno=2023), 'i1000')
    out.append(numero(p, id='osp-letti-1000', pagina='ospedali', diff='facile',
        domanda='Quanti posti letto ci sono negli ospedali e nelle case di cura di Milano ogni 1.000 abitanti, nel 2023?',
        v=m, lo=0, hi=15, passo=0.1, unita='ogni 1.000 abitanti', dec=1,
        confronto=[('Italia', it, 'ogni 1.000 abitanti'), ('Milano', m, 'ogni 1.000 abitanti')],
        spiega='Sono 6,6: quasi il doppio dell’Italia, che ne ha 3,6. Tra le dieci grandi città Milano è al quinto posto.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    bo = p.v(cc, ix(cc, nome='Bologna'), 'per1000')
    mi = p.v(cc, ix(cc, nome='Milano'), 'per1000')
    ro = p.v(cc, ix(cc, nome='Roma'), 'per1000')
    out.append(ordine(p, id='osp-ordine-citta', pagina='ospedali', diff='media',
        domanda='Posti letto ogni 1.000 abitanti nel 2023. Dalla città con più posti letto a quella con meno:',
        elementi=[('Roma', ro, 'ogni 1.000'), ('Bologna', bo, 'ogni 1.000'), ('Milano', mi, 'ogni 1.000')],
        unita='', dec=2,
        spiega='Bologna ne ha 9,42, Milano 6,62, Roma 5,06. Il confronto è per comune: i letti servono anche chi abita fuori città.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    m10 = p.v(sr, ix(sr, anno=2010), 'milano')
    m23 = p.v(sr, ix(sr, anno=2023), 'milano')
    i10 = p.v(sr, ix(sr, anno=2010), 'italia')
    i23 = p.v(sr, ix(sr, anno=2023), 'italia')
    cm = p.calc('round((p[1]/p[0]-1)*100, 1)')
    ci = p.calc('round((p[3]/p[2]-1)*100, 1)')
    out.append(vf(p, id='osp-calo-italia', pagina='ospedali', diff='media',
        affermazione='Dal 2010 al 2023 i posti letto negli ospedali sono diminuiti più a Milano che in tutta Italia.',
        vero=cm < ci, confronto=[('Milano', cm, '%'), ('Italia', ci, '%')], dec=1,
        spiega='A Milano sono calati del 7,5% (da 9.816 a 9.076 posti), in Italia del 12,9%. Il calo è stato più forte nel resto del Paese.',
        anno='2010–2023', fonte=F, licenza=L))

    p = Prove()
    n = p.v(rp, 'specialita', '[nome=NEUROCHIRURGIA]', 'rapporto')
    out.append(numero(p, id='osp-neurochirurgia', pagina='ospedali', diff='difficile',
        domanda='Per abitante, quante volte più posti letto di neurochirurgia ha Milano rispetto all’Italia, nel 2023?',
        v=n, lo=0, hi=10, passo=0.05, unita='volte', dec=2,
        spiega='Quasi quattro volte: 3,65. Molti reparti specializzati accolgono pazienti di tutta la Lombardia e d’Italia, non solo milanesi.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    med = p.v(rp, 'minuti', 'ps_g', 'mediana')
    out.append(numero(p, id='osp-minuti-ps', pagina='ospedali', diff='media',
        domanda='Per la metà dei milanesi il pronto soccorso generale più vicino è a meno di quanti minuti a piedi?',
        v=med, lo=0, hi=90, passo=1, unita='minuti', dec=0,
        spiega='Servono 28 minuti: più di mezz’ora per quasi uno su due. Sono stime fatte sulla rete dei marciapiedi, non misure sul posto.',
        anno='2023', fonte='Ministero della Salute e OpenStreetMap; stima del sito sulla rete pedonale', licenza='ODbL'))

    p = Prove()
    f = 'ospedali/data/ospedali_2023.csv'
    nig = p.v(f, ix(f, nome='Niguarda'), 'letti')
    pol = p.v(f, ix(f, nome='Policlinico (Ospedale Maggiore)'), 'letti')
    sra = p.v(f, ix(f, nome='San Raffaele'), 'letti')
    tot = p.v(cc, ix(cc, nome='Milano'), 'letti')
    q3 = p.calc('round((p[0]+p[1]+p[2])/p[3]*100, 1)')
    out.append(numero(p, id='osp-tre-strutture', pagina='ospedali', diff='difficile',
        domanda='Niguarda, Policlinico e San Raffaele insieme: quanti posti letto su 100 di tutta Milano hanno nel 2023?',
        v=q3, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        spiega='Più di un terzo: 36,4 su 100, con 1.184, 1.067 e 1.055 posti. Le altre strutture si dividono il resto.',
        anno='2023', fonte=F, licenza=L))
    return out


# ====================================================================== CATASTO
def catasto():
    out = []
    L = 'CC BY'
    F = 'Agenzia delle Entrate, Osservatorio del mercato immobiliare, statistiche catastali'
    fj = 'catasto/data/catasto.json'

    p = Prove()
    r = p.v(fj, 'citta', '[n=Roma]', 'u', 'A01')
    m = p.v(fj, 'citta', '[n=Milano]', 'u', 'A01')
    out.append(piuomeno(p, id='cat-signorili', pagina='catasto', diff='facile',
        domanda='Quale città ha più case di tipo signorile (la categoria più alta per il catasto): Roma o Milano? Dati del 2025.',
        a=('Roma', r, 'case'), b=('Milano', m, 'case'),
        spiega='Milano ne ha 3.458 e Roma 2.698, anche se Roma ha il doppio degli abitanti. È la città italiana con più case signorili.',
        anno='2025', fonte=F, licenza=L))

    p = Prove()
    u18 = p.v(fj, 'milano', 'A10', 'u', '[0]')
    u25 = p.v(fj, 'milano', 'A10', 'u', '[7]')
    ur = p.v(fj, 'citta', '[n=Roma]', 'u', 'A10')
    um = p.v(fj, 'citta', '[n=Milano]', 'u', 'A10')
    dd = p.calc('round((p[1]/p[0]-1)*100, 1)')
    out.append(vf(p, id='cat-uffici-calo', pagina='catasto', diff='media',
        affermazione='Dal 2018 al 2025 gli uffici accatastati a Milano sono diminuiti.',
        vero=u25 < u18, confronto=[('2018', u18, 'uffici'), ('2025', u25, 'uffici')],
        spiega='Erano 39.649 e sono 35.578, il 10,3% in meno. Milano ne ha comunque più di ogni altra città: Roma ne ha 26.993.',
        anno='2018–2025', fonte=F, licenza=L))

    p = Prove()
    g = 'grandi'
    mb = p.v(fj, g, '[n=Milano]', 'box100')
    nb = p.v(fj, g, '[n=Napoli]', 'box100')
    vb = p.v(fj, g, '[n=Verona]', 'box100')
    bx = p.v(fj, g, '[n=Milano]', 'box')
    out.append(numero(p, id='cat-box', pagina='catasto', diff='media',
        domanda='A Milano, ogni 100 abitanti, quanti box e posti auto coperti risultano in catasto nel 2025?',
        v=mb, lo=0, hi=80, passo=1, unita='ogni 100 abitanti', dec=1,
        confronto=[('Napoli', nb, 'ogni 100'), ('Milano', mb, 'ogni 100'), ('Verona', vb, 'ogni 100')],
        spiega='Sono 29,8: in tutto 405.626. Verona ne ha 47,4 e Napoli solo 8,7. I box non sono solo dei residenti.',
        anno='2025', fonte=F + '; residenti ISTAT', licenza=L))

    p = Prove()
    sm = p.v(fj, 'milano', 'A01', 'u', '[7]')
    sr_ = p.v(fj, 'resto', 'A01', 'u', '[7]')
    am = p.v(fj, 'meta', 'ab_milano')
    ap = p.v(fj, 'meta', 'ab_prov')
    qs = p.calc('round(p[0]/(p[0]+p[1])*100, 1)')
    qa = p.calc('round(p[2]/p[3]*100, 1)')
    out.append(vf(p, id='cat-signorili-provincia', pagina='catasto', diff='difficile',
        affermazione='Nel 2025 più di nove case signorili su dieci della provincia di Milano sono nella città di Milano, dove vive meno della metà degli abitanti della provincia.',
        vero=qs > 90 and qa < 50, confronto=[('abitanti della provincia che vivono in città', qa, '%'), ('case signorili della provincia che sono in città', qs, '%')], dec=1,
        spiega='Le case signorili in città sono il 91,4% di quelle della provincia, mentre ci vive il 41,9% degli abitanti.',
        anno='2025', fonte=F + '; residenti ISTAT', licenza=L))

    p = Prove()
    cp = 'catasto/data/capoluoghi_2025.csv'
    rm = p.v(cp, ix(cp, citta='Milano'), 'rendita_media_C01')
    rr = p.v(cp, ix(cp, citta='Roma'), 'rendita_media_C01')
    out.append(numero(p, id='cat-rendita-negozio', pagina='catasto', diff='difficile',
        domanda='Per il catasto, quanti euro l’anno vale in media un negozio a Milano? È la «rendita», il valore su cui si calcolano le tasse: non è il prezzo né l’affitto. Dati del 2025.',
        v=rm, lo=0, hi=10000, passo=50, unita='€ all’anno', dec=0,
        confronto=[('Roma', rr, '€ all’anno'), ('Milano', rm, '€ all’anno')],
        spiega='Circa 4.489 euro, la rendita media più alta tra tutte le città capoluogo. A Roma è 3.469.',
        anno='2025', fonte=F, licenza=L))

    p = Prove()
    c0 = p.v(fj, 'milano', 'A02', 'u', '[0]')
    c7 = p.v(fj, 'milano', 'A02', 'u', '[7]')
    b0 = p.v(fj, 'milano', 'C06', 'u', '[0]')
    b7 = p.v(fj, 'milano', 'C06', 'u', '[7]')
    a0 = p.v(fj, 'milano', 'A10', 'u', '[0]')
    a7 = p.v(fj, 'milano', 'A10', 'u', '[7]')
    vc = p.calc('round((p[1]/p[0]-1)*100, 1)')
    vb_ = p.calc('round((p[3]/p[2]-1)*100, 1)')
    va = p.calc('round((p[5]/p[4]-1)*100, 1)')
    out.append(ordine(p, id='cat-variazioni', pagina='catasto', diff='media',
        domanda='A Milano, dal 2018 al 2025, come sono cambiati questi immobili in catasto? Dalla crescita più grande al calo:',
        elementi=[('Uffici e studi privati', va, '%'), ('Box e posti auto coperti', vb_, '%'), ('Case di tipo civile', vc, '%')],
        unita='%', dec=1,
        spiega='Le case di tipo civile sono cresciute del 19,7%, i box del 6,6%; gli uffici sono calati del 10,3%.',
        anno='2018–2025', fonte=F, licenza=L))
    return out


# ====================================================================== ECONOMIA
def economia():
    out = []
    L = 'CC BY 4.0'
    F = 'Eurostat, conti economici regionali'
    rj = 'economia/data/riepilogo.json'

    p = Prove()
    mi = p.v(rj, 'pil_mi_2023')
    gr = p.v(rj, 'paesi_pil_2023', 'Grecia')
    bm = p.calc('round(p[0]/1000, 1)')
    bg = p.calc('round(p[1]/1000, 1)')
    out.append(vf(p, id='eco-grecia', pagina='economia', diff='facile',
        affermazione='Nel 2023 la Città metropolitana di Milano ha prodotto più ricchezza (PIL) dell’intera Grecia.',
        vero=mi > gr, confronto=[('Grecia', bg, 'miliardi di €'), ('Città metropolitana di Milano', bm, 'miliardi di €')], dec=1,
        spiega='Milano 230,5 miliardi di euro, Grecia 225,1. Milano è più grande di dodici paesi dell’Unione europea, tra cui l’Ungheria. Qui «Milano» è la vecchia provincia.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    q = p.v(rj, 'quota', 'quota', '[-1]')
    ab = p.v(rj, 'pesi', '2023', 'abitanti')
    q00 = p.v(rj, 'quota', 'quota', '[0]')
    out.append(numero(p, id='eco-quota-pil', pagina='economia', diff='facile',
        domanda='Su 100 euro di PIL prodotti in Italia nel 2023, quanti nascono nella Città metropolitana di Milano?',
        v=q, lo=0, hi=40, passo=0.1, unita='euro su 100', dec=1,
        confronto=[('quota degli abitanti italiani', ab, '%'), ('quota del PIL italiano', q, '%')],
        spiega='Quasi 11: 10,8. Ci vive il 5,5% degli italiani. Nel 2000 la quota del PIL era 8,8.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    bo = p.v(rj, 'pc', 'Bologna', '[-1]')
    ro = p.v(rj, 'pc', 'Roma', '[-1]')
    to = p.v(rj, 'pc', 'Torino', '[-1]')
    out.append(ordine(p, id='eco-ordine-pil-testa', pagina='economia', diff='media',
        domanda='PIL per abitante nel 2023. Dalla provincia più ricca a quella meno ricca:',
        elementi=[('Torino', to, '€'), ('Roma', ro, '€'), ('Bologna', bo, '€')], unita='€', dec=0,
        spiega='Bologna 50.100 euro, Roma 47.600, Torino 39.000. Bologna sta davanti a Roma.',
        anno='2023', fonte=F, licenza=L))

    p = Prove()
    r21 = p.v(rj, 'eu', 'rango_2021')
    r00 = p.v(rj, 'eu', 'rango_2000')
    su = p.v(rj, 'eu', 'su_2021')
    su0 = p.v(rj, 'eu', 'su_2000')
    out.append(numero(p, id='eco-europa-posto', pagina='economia', diff='difficile',
        domanda='Tra le 248 aree metropolitane europee, in che posizione è Milano per PIL a testa nel 2021 (a parità di potere d’acquisto)? Il primo posto è il più ricco.',
        v=r21, lo=1, hi=100, passo=1, unita='° posto', dec=0,
        confronto=[('2000', r00, '° posto'), ('2021', r21, '° posto')],
        spiega='Milano è al 14° posto. Nel 2000 era all’8°, ma allora le aree messe a confronto erano 238.',
        anno='2021', fonte=F, licenza=L))

    p = Prove()
    ep = 'economia/data/europa_pps.csv'
    mi21 = p.v(ep, ix(ep, citta='Milano'), 'indice_ue100_2021')
    bu21 = p.v(ep, ix(ep, citta='Bucarest'), 'indice_ue100_2021')
    mi00 = p.v(ep, ix(ep, citta='Milano'), 'indice_ue100_2000')
    bu00 = p.v(ep, ix(ep, citta='Bucarest'), 'indice_ue100_2000')
    out.append(vf(p, id='eco-bucarest', pagina='economia', diff='difficile',
        affermazione='Nel 2021 Bucarest aveva un PIL a testa più alto di Milano (area metropolitana, a parità di potere d’acquisto).',
        vero=bu21 > mi21, confronto=[('Milano', mi21, 'indice, media UE = 100'), ('Bucarest', bu21, 'indice, media UE = 100')],
        spiega='Bucarest era a 171 e Milano a 165, con la media europea uguale a 100. Nel 2000 Bucarest era a 58 e Milano a 185.',
        anno='2021', fonte=F, licenza=L))

    p = Prove()
    st = 'economia/data/settori_2023.csv'
    ij = p.v(st, ix(st, codice='J'), 'quota_milano_su_italia_pct')
    ik = p.v(st, ix(st, codice='K'), 'quota_milano_su_italia_pct')
    ia = p.v(st, ix(st, codice='O-Q'), 'quota_milano_su_italia_pct')
    out.append(numero(p, id='eco-informatica', pagina='economia', diff='difficile',
        domanda='Su 100 euro di valore prodotto in Italia nel 2023 dal settore informatica e comunicazione, quanti nascono nella Città metropolitana di Milano?',
        v=ij, lo=0, hi=80, passo=1, unita='euro su 100', dec=1,
        confronto=[('Pubblica amministrazione, scuola e sanità', ia, '%'), ('Banche e assicurazioni', ik, '%'), ('Informatica e comunicazione', ij, '%')],
        spiega='Più di un quarto: 26,7. Per banche e assicurazioni è il 20,2. Per pubblica amministrazione, scuola e sanità solo il 5,7.',
        anno='2023', fonte=F, licenza=L))
    return out


# ====================================================================== LAVORO
def lavoro():
    out = []
    rj = 'occupazione/data/riepilogo.json'
    FC = 'Regione Lombardia, comunicazioni obbligatorie sui contratti di lavoro'
    FT = 'Comune di Milano, indagine sulle forze di lavoro'

    anni = carica(rj)['contratti']['anni']
    p = Prove()
    td = p.v(rj, 'contratti', 'dati', 'Tempo determinato', '2024')
    k = p.i()
    corti = p.calc('p[%d][0]' % k)
    totale = p.calc('sum(p[%d])' % k)
    q = p.calc('round(p[%d][0]/sum(p[%d])*100, 1)' % (k, k))
    out.append(numero(p, id='lav-contratti-brevi', pagina='occupazione', diff='media',
        domanda='Tra i contratti di lavoro a termine iniziati nel 2024 nella provincia di Milano, quanti su 100 durano meno di un mese?',
        v=q, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        spiega='Quasi sei su dieci: 412.615 contratti su 712.891, cioè 57,9 su 100. Si contano i contratti, non le persone: chi ne firma tre in un anno compare tre volte.',
        anno='2024', fonte=FC, licenza='CC0 1.0'))

    p = Prove()
    vals = []
    for y in range(2013, 2025):
        p.v(rj, 'contratti', 'dati', 'Tempo determinato', str(y))
        kk = p.i()
        vals.append(p.calc('round(p[%d][0]/sum(p[%d])*100, 1)' % (kk, kk)))
    picco = anni[vals.index(max(vals))]
    assert picco == 2016, picco
    v = p.v(rj, 'contratti', 'anni', '[3]')
    assert v == 2016
    out.append(anno_q(p, id='lav-picco-brevi', pagina='occupazione', diff='difficile',
        domanda='In che anno la quota di contratti a termine che durano meno di un mese ha toccato il massimo, tra il 2013 e il 2024, nella provincia di Milano?',
        v=v, lo=2013, hi=2024,
        spiega='Nel 2016 furono quasi 64 su 100. Nel 2024 sono 58, come nel 2013: la quota non cresce, anche se i contratti brevi sono molti di più in numero.',
        anno='2013–2024', fonte=FC, licenza='CC0 1.0',
        serie=serie_da(list(range(2013, 2025)), [('Contratti a termine sotto il mese (su 100)', vals)])))

    p = Prove()
    tm = p.v(rj, 'tassi', 'Milano', 'occ', 't', '[-1]')
    ti = p.v(rj, 'tassi', 'Italia', 'occ', 't', '[-1]')
    tl = p.v(rj, 'tassi', 'Lombardia', 'occ', 't', '[-1]')
    out.append(numero(p, id='lav-tasso-occupazione', pagina='occupazione', diff='facile',
        domanda='Nel 2024, su 100 milanesi in età da lavoro (dai quindici ai sessantaquattro anni), quanti hanno un lavoro?',
        v=tm, lo=30, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('Italia', ti, 'su 100'), ('Lombardia', tl, 'su 100'), ('Milano', tm, 'su 100')],
        spiega='73,9 su 100. In Lombardia sono 69,4 e in Italia 62,2. Si contano i residenti a Milano, non chi ci lavora.',
        anno='2024', fonte=FT, licenza='CC BY'))

    p = Prove()
    m24 = p.v(rj, 'tassi', 'Milano', 'occ', 'm', '[-1]')
    f24 = p.v(rj, 'tassi', 'Milano', 'occ', 'f', '[-1]')
    m04 = p.v(rj, 'tassi', 'Milano', 'occ', 'm', '[0]')
    f04 = p.v(rj, 'tassi', 'Milano', 'occ', 'f', '[0]')
    d24 = p.calc('round(p[0]-p[1], 1)')
    d04 = p.calc('round(p[2]-p[3], 1)')
    out.append(numero(p, id='lav-divario', pagina='occupazione', diff='difficile',
        domanda='A Milano, nel 2024, di quanti punti il tasso di occupazione degli uomini supera quello delle donne (in età da lavoro)?',
        v=d24, lo=0, hi=30, passo=0.1, unita='punti', dec=1,
        confronto=[('2004', d04, 'punti'), ('2024', d24, 'punti')],
        spiega='Di 3,9 punti: 75,8 contro 71,9. Nel 2004 la distanza era di 14,7 punti.',
        anno='2004–2024', fonte=FT, licenza='CC BY'))

    p = Prove()
    m = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'tot')
    me = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'meno')
    mt = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'meta')
    it = p.v(rj, 'casa', 'citta', '[nome=Italia]', '2024T', 'tot')
    ie = p.v(rj, 'casa', 'citta', '[nome=Italia]', '2024T', 'meno')
    iu = p.v(rj, 'casa', 'citta', '[nome=Italia]', '2024T', 'meta')
    qm = p.calc('round((p[1]+p[2])/p[0]*100, 1)')
    qi = p.calc('round((p[4]+p[5])/p[3]*100, 1)')
    out.append(numero(p, id='lav-da-casa', pagina='occupazione', diff='media',
        domanda='A Milano, nel 2024, quanti occupati su 100 lavorano da casa almeno qualche volta?',
        v=qm, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('Italia', qi, 'su 100'), ('Milano', qm, 'su 100')],
        spiega='39 su 100, quasi tre volte la media italiana (14).',
        anno='2024', fonte='ISTAT, occupati che lavorano da casa', licenza='CC BY 4.0'))

    p = Prove()
    c = 'casa', 'citta'
    ro = p.v(rj, 'casa', 'citta', '[nome=Roma]', '2024T', 'tot')
    ro1 = p.v(rj, 'casa', 'citta', '[nome=Roma]', '2024T', 'meno')
    ro2 = p.v(rj, 'casa', 'citta', '[nome=Roma]', '2024T', 'meta')
    bo = p.v(rj, 'casa', 'citta', '[nome=Bologna]', '2024T', 'tot')
    bo1 = p.v(rj, 'casa', 'citta', '[nome=Bologna]', '2024T', 'meno')
    bo2 = p.v(rj, 'casa', 'citta', '[nome=Bologna]', '2024T', 'meta')
    to = p.v(rj, 'casa', 'citta', '[nome=Torino]', '2024T', 'tot')
    to1 = p.v(rj, 'casa', 'citta', '[nome=Torino]', '2024T', 'meno')
    to2 = p.v(rj, 'casa', 'citta', '[nome=Torino]', '2024T', 'meta')
    qr = p.calc('round((p[1]+p[2])/p[0]*100, 1)')
    qb = p.calc('round((p[4]+p[5])/p[3]*100, 1)')
    qt = p.calc('round((p[7]+p[8])/p[6]*100, 1)')
    mi_ = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'tot')
    mi1 = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'meno')
    mi2 = p.v(rj, 'casa', 'citta', '[nome=Milano]', '2024T', 'meta')
    qmi = p.calc('round((p[10]+p[11])/p[9]*100, 1)')
    out.append(ordine(p, id='lav-ordine-da-casa', pagina='occupazione', diff='media',
        domanda='Quanti occupati su 100 lavorano da casa almeno qualche volta, nel 2024? Dalla città con più lavoro da casa a quella con meno:',
        elementi=[('Torino', qt, 'su 100'), ('Roma', qr, 'su 100'), ('Bologna', qb, 'su 100')], unita='su 100', dec=1,
        spiega='Roma 31,1, Bologna 28,6, Torino 25,2. Milano è prima con 39,0.',
        anno='2024', fonte='ISTAT, occupati che lavorano da casa', licenza='CC BY 4.0'))

    p = Prove()
    dm = p.v(rj, 'tassi', 'Milano', 'occ', 'f', '[-1]')
    iu = p.v(rj, 'tassi', 'Italia', 'occ', 'm', '[-1]')
    itf = p.v(rj, 'tassi', 'Italia', 'occ', 'f', '[-1]')
    out.append(vf(p, id='lav-donne-mi-uomini-it', pagina='occupazione', diff='difficile',
        affermazione='Nel 2024 il tasso di occupazione delle donne di Milano, in età da lavoro, è più alto di quello degli uomini in tutta Italia.',
        vero=dm > iu, confronto=[('Uomini in Italia', iu, 'su 100'), ('Donne a Milano', dm, 'su 100')], dec=1,
        spiega='Le milanesi con un lavoro sono 71,9 su 100, gli italiani 71,1. Le donne in Italia sono a 53,3.',
        anno='2024', fonte=FT, licenza='CC BY'))
    return out


# ====================================================================== OLIMPIADI (solo aeroporti)
def olimpiadi():
    out = []
    L = 'CC BY 4.0'
    F = 'Eurostat, passeggeri per aeroporto (da gennaio a maggio)'
    f = 'olimpiadi/data/aeroporti_giochi.csv'

    def somma(p, aer, anno):
        idx = []
        p.v(f, ix(f, aeroporto=aer, anno=anno, mese=1), 'anno')
        for mese in range(1, 6):
            p.v(f, ix(f, aeroporto=aer, anno=anno, mese=mese), 'passeggeri')
            idx.append(p.i())
        return idx

    p = Prove()
    a = somma(p, 'Malpensa', 2025)
    b = somma(p, 'Malpensa', 2026)
    s25 = p.calc('round(sum(p[%d:%d])/1000000, 2)' % (a[0], a[-1] + 1))
    s26 = p.calc('round(sum(p[%d:%d])/1000000, 2)' % (b[0], b[-1] + 1))
    var = p.calc('round((sum(p[%d:%d])/sum(p[%d:%d])-1)*100, 1)' % (b[0], b[-1] + 1, a[0], a[-1] + 1))
    out.append(vf(p, id='oli-malpensa', pagina='olimpiadi', diff='difficile',
        affermazione='Da gennaio a maggio 2026, anno delle Olimpiadi invernali, Malpensa ha avuto più passeggeri che nello stesso periodo del 2025.',
        vero=s26 > s25, confronto=[('gennaio–maggio 2025', s25, 'milioni di passeggeri'), ('gennaio–maggio 2026', s26, 'milioni di passeggeri')], dec=2,
        spiega='Ne ha avuti 11,52 milioni contro 11,72, l’1,7% in meno. Sono cresciuti Linate e Bergamo.',
        anno='gennaio–maggio 2026', fonte=F, licenza=L))

    p = Prove()
    a = somma(p, 'Linate', 2025)
    b = somma(p, 'Linate', 2026)
    var_l = p.calc('round((sum(p[%d:%d])/sum(p[%d:%d])-1)*100, 1)' % (b[0], b[-1] + 1, a[0], a[-1] + 1))
    a2 = somma(p, 'Bergamo', 2025)
    b2 = somma(p, 'Bergamo', 2026)
    var_b = p.calc('round((sum(p[%d:%d])/sum(p[%d:%d])-1)*100, 1)' % (b2[0], b2[-1] + 1, a2[0], a2[-1] + 1))
    a3 = somma(p, 'Malpensa', 2025)
    b3 = somma(p, 'Malpensa', 2026)
    var_m = p.calc('round((sum(p[%d:%d])/sum(p[%d:%d])-1)*100, 1)' % (b3[0], b3[-1] + 1, a3[0], a3[-1] + 1))
    out.append(numero(p, id='oli-linate', pagina='olimpiadi', diff='media',
        domanda='Da gennaio a maggio 2026, di quanto sono cambiati i passeggeri di Linate rispetto agli stessi cinque mesi del 2025?',
        v=var_l, lo=-20, hi=40, passo=0.1, unita='%', dec=1,
        confronto=[('Malpensa', var_m, '%'), ('Bergamo', var_b, '%'), ('Linate', var_l, '%')],
        spiega='Linate è cresciuta dell’11,7%. Bergamo del 6,3% e Malpensa è calata dell’1,7%.',
        anno='gennaio–maggio 2026', fonte=F, licenza=L))

    p = Prove()
    a = somma(p, 'Bergamo', 2026)
    b = somma(p, 'Linate', 2026)
    sb = p.calc('round(sum(p[%d:%d])/1000000, 2)' % (a[0], a[-1] + 1))
    sl = p.calc('round(sum(p[%d:%d])/1000000, 2)' % (b[0], b[-1] + 1))
    out.append(piuomeno(p, id='oli-bergamo-linate', pagina='olimpiadi', diff='facile',
        domanda='Da gennaio a maggio 2026, quale aeroporto ha avuto più passeggeri: Linate o Bergamo-Orio al Serio?',
        a=('Linate', sl, 'milioni di passeggeri'), b=('Bergamo', sb, 'milioni di passeggeri'), dec=2,
        spiega='Bergamo ha avuto 6,99 milioni di passeggeri, Linate 4,82. Nonostante la crescita di Linate, Bergamo resta molto più grande.',
        anno='gennaio–maggio 2026', fonte=F, licenza=L))
    return out


# ====================================================================== CASE E ENERGIA
def case_energia():
    out = []
    rj = 'case-energia/data/riepilogo.json'
    FR = 'Regione Lombardia, attestati di prestazione energetica'
    FC = 'Comune di Milano'

    p = Prove()
    b6 = p.v(rj, 'epoca', 'bande', '[6]')
    v0 = p.v(rj, 'epoca', 'vecchio', 'co2_mediana', '[0]')
    v6 = p.v(rj, 'epoca', 'vecchio', 'co2_mediana', '[6]')
    out.append(numero(p, id='ene-co2-vecchie', pagina='case-energia', diff='difficile',
        domanda='Una casa tipica di Milano costruita prima del 1930 emette quanti chili di CO₂ per ogni metro quadro all’anno, secondo gli attestati energetici del 2009-2016?',
        v=v0, lo=0, hi=80, passo=0.5, unita='kg al m² all’anno', dec=1,
        confronto=[('costruite dopo il 2006', v6, 'kg'), ('costruite prima del 1930', v0, 'kg')],
        spiega='36,5 chili. Una casa costruita dopo il 2006 ne emette 8,7. Le emissioni sono calcolate dal tecnico, non misurate.',
        anno='2009–2016', fonte=FR, licenza='CC0 1.0'))

    p = Prove()
    n = p.v(rj, 'classi', 'n')
    fg = p.v(rj, 'classi', 'quota_fg')
    aa = p.v(rj, 'classi', 'quota_a')
    out.append(numero(p, id='ene-classe-fg', pagina='case-energia', diff='media',
        domanda='Tra i 235.106 attestati energetici delle case di Milano fatti fino al 2016, quanti su 100 sono in classe F o G, le due peggiori?',
        v=fg, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('classe A', aa, 'su 100'), ('classi F o G', fg, 'su 100')],
        spiega='Quasi sette su dieci: 67,6. Solo 1,6 su 100 sono in classe A. Gli attestati si fanno quando una casa si vende, si affitta o si ristruttura: non sono tutte le case.',
        anno='2009–2016', fonte=FR, licenza='CC0 1.0'))

    p = Prove()
    b2 = p.v(rj, 'epoca', 'bande', '[2]')
    b6 = p.v(rj, 'epoca', 'bande', '[6]')
    c0 = p.v(rj, 'epoca', 'vecchio', 'co2_mediana', '[0]')
    c2 = p.v(rj, 'epoca', 'vecchio', 'co2_mediana', '[2]')
    c6 = p.v(rj, 'epoca', 'vecchio', 'co2_mediana', '[6]')
    tutte = p.v(rj, 'epoca', 'vecchio', 'co2_mediana')
    out.append(vf(p, id='ene-vecchie-emettono-piu', pagina='case-energia', diff='difficile',
        affermazione='Le case costruite prima del 1930 sono quelle che emettono più CO₂ per metro quadro, tra tutte le epoche di costruzione.',
        vero=c0 == max(tutte), confronto=[('prima del 1930', c0, 'kg'), ('1946-1960', c2, 'kg'), ('dopo il 2006', c6, 'kg')], dec=1,
        spiega='No: le più vecchie emettono 36,5 chili, ma le case costruite tra il 1946 e il 1960 ne emettono 38,9. Dopo il 2006 il valore crolla a 8,7.',
        anno='2009–2016', fonte=FR, licenza='CC0 1.0'))

    p = Prove()
    y17 = p.v(rj, 'riscaldamento', 'serie', 'pdc', 'nuovo', '[0]', 'a')
    a17 = p.v(rj, 'riscaldamento', 'serie', 'pdc', 'nuovo', '[0]', 'v')
    a25 = p.v(rj, 'riscaldamento', 'serie', 'pdc', 'nuovo', '[8]', 'v')
    out.append(numero(p, id='ene-pompa-calore', pagina='case-energia', diff='media',
        domanda='Tra gli attestati energetici fatti a Milano nel 2025, quanti su 100 hanno una pompa di calore come impianto principale?',
        v=a25, lo=0, hi=60, passo=0.1, unita='su 100', dec=1,
        confronto=[('2017', a17, 'su 100'), ('2025', a25, 'su 100')],
        spiega='12,6 su 100. Nel 2017 erano 4,1. Resta la caldaia l’impianto più diffuso.',
        anno='2025', fonte=FR, licenza='CC0 1.0'))

    p = Prove()
    y16 = p.v(rj, 'colonnine', 'per_anno', '[0]', 'a')
    c16 = p.v(rj, 'colonnine', 'per_anno', '[0]', 'tot')
    c24 = p.v(rj, 'colonnine', 'per_anno', '[8]', 'tot')
    out.append(numero(p, id='ene-colonnine', pagina='case-energia', diff='media',
        domanda='Quante postazioni di ricarica per auto elettriche erano autorizzate a Milano alla fine del 2024?',
        v=c24, lo=0, hi=1500, passo=10, unita='postazioni', dec=0,
        confronto=[('fine 2016', c16, 'postazioni'), ('fine 2024', c24, 'postazioni')],
        spiega='483, contro 22 alla fine del 2016. Sono postazioni autorizzate dal Comune: non tutte sono già installate.',
        anno='2024', fonte=FC + ', colonnine di ricarica', licenza='CC BY'))

    p = Prove()
    r = p.v(rj, 'quartieri', '[n=Rogoredo - Santa Giulia]', 'fg')
    s = p.v(rj, 'quartieri', '[n=Sarpi]', 'fg')
    l = p.v(rj, 'quartieri', '[n=Lodi - Corvetto]', 'fg')
    out.append(quartiere(p, id='ene-quartiere-fg', pagina='case-energia', diff='media',
        domanda='Dal 2016, in quale di questi tre quartieri è più bassa la quota di attestati energetici in classe F o G, le due peggiori?',
        opzioni=[('Sarpi', s), ('Lodi - Corvetto', l), ('Rogoredo - Santa Giulia', r)], verso='min', unita='% in classe F o G', dec=1,
        spiega='A Rogoredo - Santa Giulia sono 15,6 su 100: è il valore più basso tra i quartieri con un numero sufficiente di attestati. A Sarpi sono 43,1 e a Lodi - Corvetto 49,0.',
        anno='2016–2026', fonte=FR, licenza='CC0 1.0'))

    return out


# ====================================================================== NEGOZI
def negozi():
    out = []
    L = 'CC BY'
    F = 'Comune di Milano, commercio al dettaglio'
    rj = 'negozi/data/riepilogo.json'
    qf = 'negozi/data/quartieri.csv'

    p = Prove()
    v03 = p.v(rj, 'serie', 'vicinato', '2003')
    v25 = p.v(rj, 'serie', 'vicinato', '2025')
    m03 = p.v(rj, 'serie', 'medie', '2003')
    m25 = p.v(rj, 'serie', 'medie', '2025')
    cv = p.calc('round((p[1]/p[0]-1)*100, 1)')
    cm = p.calc('round((p[3]/p[2]-1)*100, 1)')
    out.append(numero(p, id='neg-vicinato', pagina='negozi', diff='facile',
        domanda='I negozi di vicinato (i piccoli negozi) di Milano, dal 2003 al 2025: di quanto sono aumentati o diminuiti?',
        v=cv, lo=-60, hi=100, passo=1, unita='%', dec=1,
        confronto=[('medie strutture', cm, '%'), ('negozi di vicinato', cv, '%')],
        spiega='Sono aumentati del 39,7%: da 20.138 a 28.131. Non è vero che spariscono. Le medie strutture sono cresciute del 12,5%.',
        anno='2003–2025', fonte=F, licenza=L))

    p = Prove()
    g = p.v(qf, ix(qf, quartiere='Guastalla'), 'ogni1000')
    s = p.v(qf, ix(qf, quartiere='Sarpi'), 'ogni1000')
    sc = p.v(qf, ix(qf, quartiere='Stazione Centrale - Ponte Seveso'), 'ogni1000')
    out.append(quartiere(p, id='neg-quartiere-max', pagina='negozi', diff='media',
        domanda='Nel 2025, in quale di questi tre quartieri ci sono più negozi di vicinato in rapporto agli abitanti?',
        opzioni=[('Sarpi', s), ('Guastalla', g), ('Stazione Centrale - Ponte Seveso', sc)], verso='max', unita='negozi ogni 1.000 abitanti', dec=1,
        spiega='A Guastalla ce ne sono 46,5 ogni 1.000 abitanti, a Sarpi 39,5 e alla Stazione Centrale 37,9.',
        anno='2025', fonte=F, licenza=L))

    p = Prove()
    b = p.v(qf, ix(qf, quartiere='Barona'), 'ogni1000')
    a = p.v(qf, ix(qf, quartiere='Adriano'), 'ogni1000')
    s = p.v(qf, ix(qf, quartiere='Sarpi'), 'ogni1000')
    out.append(quartiere(p, id='neg-quartiere-min', pagina='negozi', diff='facile',
        domanda='Nel 2025, in quale di questi tre quartieri ci sono meno negozi di vicinato in rapporto agli abitanti?',
        opzioni=[('Sarpi', s), ('Barona', b), ('Adriano', a)], verso='min', unita='negozi ogni 1.000 abitanti', dec=1,
        spiega='Alla Barona ce ne sono solo 4,1 ogni 1.000 abitanti, ad Adriano 5,4. A Sarpi 39,5.',
        anno='2025', fonte=F, licenza=L))

    p = Prove()
    ap = 'negozi/data/aperture_chiusure_2018.csv'
    av = p.v(ap, ix(ap, attivita='Edicole'), 'avvii')
    ce = p.v(ap, ix(ap, attivita='Edicole'), 'cessazioni')
    assert all(r['saldo'] > 0 for r in carica(ap) if r['attivita'] != 'Edicole')
    out.append(vf(p, id='neg-edicole-2018', pagina='negozi', diff='difficile',
        affermazione='Nel 2018 le edicole sono state l’unico tipo di attività, tra quelle contate dal Comune, in cui hanno chiuso più esercizi di quanti ne sono stati aperti.',
        vero=ce > av, confronto=[('aperture', av, 'edicole'), ('chiusure', ce, 'edicole')],
        spiega='Le edicole che hanno aperto sono 7, quelle che hanno chiuso 15. Tutte le altre attività hanno aperto più di quanto hanno chiuso. Il 2018 è l’unico anno disponibile.',
        anno='2018', fonte=F, licenza=L))

    p = Prove()
    mg = 'negozi/data/mercati_giorni.csv'
    dom = p.v(mg, ix(mg, giorno='Domenica'), 'mercati')
    sab = p.v(mg, ix(mg, giorno='Sabato'), 'mercati')
    out.append(numero(p, id='neg-mercati-domenica', pagina='negozi', diff='media',
        domanda='Quanti mercati settimanali all’aperto si tengono di domenica a Milano?',
        v=dom, lo=0, hi=30, passo=1, unita='mercati', dec=0,
        confronto=[('sabato', sab, 'mercati'), ('domenica', dom, 'mercati')],
        spiega='Solo 2. Il sabato ce ne sono 20, il giorno con più mercati.',
        anno='2026', fonte='Comune di Milano, mercati settimanali scoperti', licenza=L))

    p = Prove()
    vi = 'negozi/data/vie_top15.csv'
    pa = p.v(vi, ix(vi, via='Via PADOVA'), 'negozi')
    mo = p.v(vi, ix(vi, via='Viale MONZA'), 'negozi')
    ba = p.v(vi, ix(vi, via='Corso BUENOS AIRES'), 'negozi')
    out.append(ordine(p, id='neg-ordine-vie', pagina='negozi', diff='media',
        domanda='Negozi di vicinato nel 2025. Dalla via con più negozi a quella con meno:',
        elementi=[('Via Padova', pa, 'negozi'), ('Corso Buenos Aires', ba, 'negozi'), ('Viale Monza', mo, 'negozi')], unita='negozi', dec=0,
        spiega='Viale Monza 275, Via Padova 262, Corso Buenos Aires 183. Le vie lunghe contano molto.',
        anno='2025', fonte=F, licenza=L))

    return out


# ====================================================================== PROVERBI
def proverbi():
    out = []
    pj = 'proverbi/data/proverbi.json'
    F = 'serie di Milano Brera dal 1763 (Università di Milano, ARPA Lombardia)'
    LNC = 'CC BY-NC'

    p = Prove()
    c = p.v(pj, 'martino', 'l11_tutti', 'c')
    n = p.v(pj, 'martino', 'l11_tutti', 'n')
    me = p.v(pj, 'martino', 'posto_11_nov', 'media_giorni')
    q = p.calc('round(p[0]/p[1]*100, 1)')
    out.append(numero(p, id='pro-san-martino', pagina='proverbi', diff='facile',
        domanda='In quanti anni su 100 il giorno di San Martino (l’undici novembre) è più caldo della settimana prima? Si conta su tutte le temperature di Milano dal 1763.',
        v=q, lo=0, hi=100, passo=1, unita='anni su 100', dec=0,
        confronto=[('media degli altri giorni, da metà ottobre a inizio dicembre', me, 'anni su 100'), ('giorno di San Martino', q, 'anni su 100')],
        spiega='In 31 anni su 100: meno della media degli altri giorni, che è 37. L’estate di San Martino non c’è.',
        anno='1763–2025', fonte=F, licenza=LNC))

    p = Prove()
    g = p.v(pj, 'merla', 'curva', 'giorni')
    v = p.v(pj, 'merla', 'curva', 'tutti')
    i_f = [g.index(x) for x in (110, 111, 112)]
    i_m = [g.index(x) for x in (129, 130, 131)]
    fr = p.calc('round((p[1][%d]+p[1][%d]+p[1][%d])/3, 1)' % tuple(i_f))
    me = p.calc('round((p[1][%d]+p[1][%d]+p[1][%d])/3, 1)' % tuple(i_m))
    out.append(vf(p, id='pro-merla', pagina='proverbi', diff='media',
        affermazione='I giorni della merla, gli ultimi tre di gennaio, sono in media i tre giorni più freddi dell’anno a Milano.',
        vero=me < fr, confronto=[('giorni della merla (ultimi tre di gennaio)', me, '°C'), ('dal decimo al dodicesimo giorno di gennaio', fr, '°C')], dec=1,
        spiega='No: i tre giorni più freddi sono il decimo, l’undicesimo e il dodicesimo di gennaio, con 1,4 °C. I giorni della merla sono a 2,6 °C.',
        anno='1763–2025', fonte=F, licenza=LNC))

    p = Prove()
    we = p.v(pj, 'weekend', 'tutti', 'we')
    fe = p.v(pj, 'weekend', 'tutti', 'feriali')
    out.append(numero(p, id='pro-weekend', pagina='proverbi', diff='difficile',
        domanda='A Milano, in quanti sabati e domeniche su 100 piove (almeno un millimetro)? Si conta dal 1858.',
        v=we, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('gli altri giorni', fe, 'su 100'), ('sabato e domenica', we, 'su 100')],
        spiega='In 23,4 su 100. Negli altri giorni della settimana è quasi lo stesso: 23,7. Il fine settimana non piove di più.',
        anno='1858–2025', fonte=F, licenza=LNC))

    p = Prove()
    pi = p.v(pj, 'ascensione', 'tutti', 'gg_piove')
    asc = p.v(pj, 'ascensione', 'tutti', 'gg_asciutto')
    fin = p.v(pj, 'ascensione', 'finestra')
    dif = p.calc('round(p[0]-p[1], 1)')
    out.append(numero(p, id='pro-ascensione', pagina='proverbi', diff='difficile',
        domanda='Il proverbio dice che se piove il giorno dell’Ascensione piove per quaranta giorni. In media, quanti dei quaranta giorni dopo un’Ascensione piovosa hanno davvero la pioggia a Milano?',
        v=pi, lo=0, hi=40, passo=0.1, unita='giorni', dec=1,
        confronto=[('dopo un’Ascensione asciutta', asc, 'giorni'), ('dopo un’Ascensione con pioggia', pi, 'giorni')],
        spiega='11,2 giorni su 40, appena 0,8 in più che dopo un’Ascensione asciutta (10,4).',
        anno='1858–2025', fonte=F, licenza=LNC))

    p = Prove()
    n = p.v(pj, 'natale_prima', 'tutti', 'n')
    d = p.v(pj, 'natale_prima', 'tutti', 'dopo_piu_freddo')
    q = p.calc('round(p[1]/p[0]*100, 1)')
    dopo = p.v(pj, 'natale_prima', 'tutti', 'dopo')
    prima = p.v(pj, 'natale_prima', 'tutti', 'prima')
    out.append(numero(p, id='pro-natale-freddo', pagina='proverbi', diff='media',
        domanda='Si confronta la temperatura media dei giorni dal primo al ventiquattro dicembre con quella dal ventisei dicembre al trentuno gennaio. In quanti inverni su 100 il secondo periodo è più freddo del primo?',
        v=q, lo=0, hi=100, passo=1, unita='inverni su 100', dec=0,
        spiega='In 78 inverni su 100: dopo Natale fa davvero più freddo, in media 1,9 °C contro 3,4 °C. Il proverbio «prima di Natale né freddo né fame, dopo Natale l’uno e l’altra» sul freddo regge.',
        anno='1763–2025', fonte=F, licenza=LNC))
    return out


# ====================================================================== IL TUO ANNO
def il_tuo_anno():
    out = []
    aj = 'il-tuo-anno/data/anno.json'
    L = 'CC BY 4.0'
    F = 'Comune di Milano, serie storiche dal 1880 e residenti per età e stato civile'

    p = Prove()
    a25 = p.v(aj, 'adulti', '2025')
    a12 = p.v(aj, 'adulti', '2012')
    pe25 = p.v(aj, 'adulti', '2025', 'persone')
    sp25 = p.v(aj, 'adulti', '2025', 'sposati')
    pe12 = p.v(aj, 'adulti', '2012', 'persone')
    sp12 = p.v(aj, 'adulti', '2012', 'sposati')
    q25 = p.calc('round(p[3]/p[2]*100, 1)')
    q12 = p.calc('round(p[5]/p[4]*100, 1)')
    out.append(numero(p, id='anno-sposati', pagina='il-tuo-anno', diff='media',
        domanda='Alla fine del 2025, quanti milanesi adulti su 100 sono sposati?',
        v=q25, lo=0, hi=100, passo=1, unita='su 100', dec=1,
        confronto=[('fine 2012', q12, 'su 100'), ('fine 2025', q25, 'su 100')],
        spiega='44,9 su 100. Alla fine del 2012 erano 51,9. Si contano solo i maggiorenni.',
        anno='2025', fonte=F, licenza=L))

    p = Prove()
    na = p.v(aj, 'natalita', '[110]')
    mo = p.v(aj, 'mortalita', '[110]')
    n90 = p.v(aj, 'nati', '[110]')
    out.append(vf(p, id='anno-1990-morti', pagina='il-tuo-anno', diff='facile',
        affermazione='Nel 1990 a Milano morivano più persone di quante ne nascevano.',
        vero=mo > na, confronto=[('nati', na, 'ogni 1.000 abitanti'), ('morti', mo, 'ogni 1.000 abitanti')], dec=1,
        spiega='Nel 1990 sono nati 7,1 bambini ogni mille abitanti e sono morte 11,2 persone: 10.230 nati in tutto.',
        anno='1990', fonte=F, licenza=L))

    p = Prove()
    anni = carica(aj)['anni']
    nati = p.v(aj, 'nati')
    mn = min(range(len(nati)), key=lambda i: nati[i])
    assert anni[mn] == 1918
    v = p.v(aj, 'anni', '[%d]' % mn)
    out.append(anno_q(p, id='anno-meno-nati', pagina='il-tuo-anno', diff='difficile',
        domanda='In che anno sono nati meno bambini a Milano da quando ci sono i dati (1880), nei confini del Comune di allora?',
        v=v, lo=1880, hi=2024,
        spiega='Nel 1918 ne nacquero solo 7.468: la guerra e la febbre spagnola. Il secondo anno più basso è il 1917, con 7.813.',
        anno='1880–2024', fonte=F, licenza=L,
        serie=serie_da(anni, [('Nati', nati)])))

    p = Prove()
    p90 = p.v(aj, 'pop', '[110]')
    p25 = p.v(aj, 'pop', '[-2]')
    out.append(piuomeno(p, id='anno-pop-1990', pagina='il-tuo-anno', diff='media',
        domanda='Milano ha più abitanti nel 2024 o ne aveva nel 1990?',
        a=('abitanti, 1990', p90, ''), b=('abitanti, 2024', p25, ''),
        spiega='Nel 1990 erano 1.432.184, nel 2024 sono 1.407.044: il 2% in meno.',
        anno='1990 e 2024', fonte=F, licenza=L))
    return out
