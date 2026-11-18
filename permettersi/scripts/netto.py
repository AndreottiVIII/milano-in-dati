"""Dal lordo al netto: stipendio annuo NETTO di un dipendente a tempo indeterminato, residente a Milano,
senza familiari a carico, per ogni anno 2011-2024. Serve alla pagina "Chi puo' permettersi dove" (interruttore Lordo / Netto).

Uso:  python -I -X utf8 netto.py <C:\\...\\milano-in-dati>          scrive docs/permettersi/data/netto.json e stampa i controlli
      python -I -X utf8 netto.py <C:\\...\\milano-in-dati> --solo-controlli     solo i controlli, senza scrivere

Cosa e' (e cosa NON e'): una stima per UN caso tipo (dipendente, tempo indeterminato, 13 mensilita', nessun carico familiare,
nessun altro reddito, nessuna spesa detraibile). Non vale per pensionati, autonomi, partite IVA, contratti a termine corti,
chi ha figli o coniuge a carico. Le regole fiscali sono quelle di ogni anno d'imposta (competenza dell'anno: le addizionali
si pagano in parte l'anno dopo, qui sono contate nell'anno a cui si riferiscono).

NETTO = LORDO - contributi INPS del lavoratore - IRPEF netta - addizionale regionale (Lombardia) - addizionale comunale (Milano)
        + bonus 80 euro / trattamento integrativo (ove spetta).
Il lordo e' la retribuzione annua lorda (RAL) in euro di quell'anno. Il reddito complessivo (base IRPEF e addizionali) e'
lordo meno i contributi INPS effettivamente trattenuti (sono deducibili).

=========================  FONTI E REGOLE, UNA PER UNA  =========================

1. CONTRIBUTI INPS A CARICO DEL LAVORATORE
   - 9,19% della retribuzione imponibile (aliquota IVS+altre del lavoratore, azienda industriale/terziario con piu' di 15 dipendenti).
     INPS, circolare n. 11 del 2024 (par. sull'esonero: "quota di contribuzione IVS a carico del lavoratore pari al 9,19%").
     https://www.fiscoetasse.com/files/17659/circolare-inps-11-2024.pdf
   - Aliquota aggiuntiva dell'1% sulla parte di retribuzione sopra la "prima fascia di retribuzione pensionabile"
     (art. 3-ter, D.L. 384/1992, conv. L. 438/1992). Limite annuo, dalle circolari INPS di ogni anno:
       2011 43.042 (tabella INPS riportata da CNOS-FAP, circ. 36/2012: https://www.cnos-fap.it/sites/default/files/newsletter/2012/April/03_b_Allegato%201%20Circ_36_14032012.pdf)
       2012 44.204 (circ. INPS 21 del 9/2/2012)         2013 45.530 (circ. INPS 22 del 8/2/2013)
       2014 46.031 (circ. INPS 20 del 6/2/2014)         2015, 2016, 2017 46.123 (circ. INPS 11/2015, 14/2016, 19/2017)
       2018 46.630 (circ. INPS 13 del 26/1/2018)        2019 47.143 (circ. INPS 6 del 25/1/2019)
       2020 e 2021 47.379 (circ. INPS 9/2020 e 10/2021)  2022 48.279 (messaggio INPS 3418 del 19/9/2022)
       2023 52.190 (circ. INPS 11 del 1/2/2023)         2024 55.008 (circ. INPS 21 del 25/1/2024)
     Indirizzi: https://servizi2.inps.it/CircolariZIP/Circolare numero 22 del 08-02-2013.pdf (e analoghi per le altre circolari).
     IPOTESI: nessun massimale contributivo (vale per chi e' nel sistema retributivo/misto; per i "contributivi puri" i contributi
     si fermano oltre ~100-120 mila euro, sopra la parte di griglia che serve alla pagina).
   - TAGLI DEL CUNEO CONTRIBUTIVO (esonero su quota IVS del lavoratore; la soglia e' sulla retribuzione mensile con 13 mensilita'):
       2022  -0,8 punti per tutto l'anno (legge 234/2021, art. 1 c. 121) e +1,2 punti dal 1/7 al 31/12 compresa la 13a (D.L. 115/2022
             art. 20): quindi 0,8% su tutta la RAL + 1,2% su 7/13 della RAL (6 mensilita' + 13a). Soglia 2.692 euro/mese (= 34.996 l'anno).
             INPS circ. 43/2022 e messaggio 3499/2022: https://consulenzaagricola.it/files/file/prassi/inps-3499-del-26-09-2022.pdf
       2023  gen-dic: -2 punti (soglia 2.692/mese) o -3 punti (soglia 1.923/mese), anche sulla 13a (legge 197/2022 art. 1 c. 281);
             luglio-dicembre: altri +4 punti ("senza effetti sul rateo di tredicesima": D.L. 48/2023 art. 39), cioe' 6 e 7 punti
             sulle 6 mensilita' di luglio-dicembre, escluso il 13a. INPS circ. 7 del 24/1/2023: https://consulenzaagricola.it/files/file/prassi/inps_7_2023.pdf
             e messaggi INPS 1932 del 24/5/2023 e 2924 del 10/8/2023 (le soglie restano 2.692 e 1.923 al mese).
       2024  -6 punti (soglia 2.692/mese) o -7 punti (soglia 1.923/mese) sulle 12 mensilita' ordinarie, NON sulla 13a (legge 213/2023
             art. 1 c. 15). INPS circ. 11 del 2024: https://www.fiscoetasse.com/files/17659/circolare-inps-11-2024.pdf
       Soglie annue equivalenti: 2.692 x 13 = 34.996 euro e 1.923 x 13 = 24.999 euro. Superata la soglia il taglio sparisce di colpo
       (salto: sopra 25.000 e sopra 35.000 euro lordi il netto scende un poco; nella griglia da 100 euro il salto e' spalmato; c'e' anche un piccolo salto in su a ~26.000 lordi per i +65 euro di detrazione dal 2022).

2. IRPEF - SCAGLIONI (reddito complessivo = lordo - contributi)
   - fino al 2021: 23% fino a 15.000; 27% 15.000-28.000; 38% 28.000-55.000; 41% 55.000-75.000; 43% oltre (art. 11 TUIR).
     Esempio AdE: circolare 4/E del 18/2/2022, par. 1.5 (imposta lorda 2021: 7.720 su 30.000 e 15.320 su 50.000).
   - 2022-2023 (legge 234/2021, art. 1 c. 2): 23% fino a 15.000; 25% 15.000-28.000; 35% 28.000-50.000; 43% oltre.
   - 2024 (D.Lgs. 216/2023, art. 1 c. 1): 23% fino a 28.000; 35% 28.000-50.000; 43% oltre. AdE circolare 2/E del 6/2/2024
     (imposta: 6.440 euro a 28.000; 14.140 a 50.000). https://www.informazionefiscale.it/IMG/pdf/circolare_n_2_del_06_02_2024.pdf
   Il "contributo di solidarieta'" del 3% oltre 300.000 euro (2011-2013) e' fuori griglia.

3. DETRAZIONE PER LAVORO DIPENDENTE (art. 13 TUIR; dipendente tutto l'anno)
   - 2011-2013 (testo L. 296/2006): 1.840 fino a 8.000; 1.338 + 502 x (15.000-R)/7.000 tra 8.000 e 15.000; 1.338 x (55.000-R)/40.000
     tra 15.000 e 55.000; piu' gli incrementi del comma 2 per R tra 23.000 e 28.000 (10 euro fino a 24.000; 20 fino a 25.000; 30 fino a
     26.000; 40 fino a 27.700; 25 fino a 28.000). Comma 2 abrogato dal 2014 (L. 147/2013, art. 1 c. 127).
     Testo: https://brocardi.it/testo-unico-imposte-redditi/titolo-i/capo-i/art13.html (note storiche) e Normattiva.
   - 2014-2021 (L. 147/2013): 1.880 fino a 8.000; 978 + 902 x (28.000-R)/20.000 fino a 28.000; 978 x (55.000-R)/27.000 fino a 55.000.
     Testo coordinato nel D.L. 3/2020 (Gazzetta Ufficiale n. 90 del 4/4/2020, pagg. 68-69).
   - 2022-2023 (L. 234/2021): 1.880 fino a 15.000; 1.910 + 1.190 x (28.000-R)/13.000 fino a 28.000; 1.910 x (50.000-R)/22.000 fino a
     50.000; + 65 euro se R tra 25.000 e 35.000 (comma 1.1). AdE circolare 4/E del 18/2/2022:
     https://www.fiscoetasse.com/files/13946/circolare-n4-18febbraio2022-novitairpef.pdf
   - 2024 (D.Lgs. 216/2023, solo per il 2024): 1.955 (invece di 1.880) fino a 15.000. AdE circolare 2/E del 6/2/2024, par. 1.2.
   - Il minimo di 690 euro (1.380 a termine) riguarda solo i rapporti di lavoro di parte dell'anno: non serve per un anno intero.

4. "ULTERIORE DETRAZIONE" 28.000-40.000 (D.L. 3/2020 art. 2, poi stabilizzata dalla legge 178/2020 art. 1 c. 8)
   - luglio-dicembre 2020: 480 + 120 x (35.000-R)/7.000 tra 28.000 e 35.000; 480 x (40.000-R)/5.000 tra 35.000 e 40.000
     (Gazzetta Ufficiale n. 90 del 4/4/2020; tabella nel dossier Camera D20003: https://documenti.camera.it/Leg18/Dossier/Pdf/D20003.Pdf)
   - 2021 (intero anno): 960 + 240 x (35.000-R)/7.000 e 960 x (40.000-R)/5.000. AdE circolare 4/E 2022 (esempio: 1.131 euro a R=30.000).
   - Abrogata dal 2022 (assorbita dalla nuova curva della detrazione).

5. BONUS 80 EURO e TRATTAMENTO INTEGRATIVO ("bonus 100 euro")
   - Bonus 80 euro (D.L. 66/2014, poi art. 13 c. 1-bis TUIR): 2014: 640 euro (80 x 8 mesi, da maggio); 2015-2019: 960 euro l'anno.
     Pieno fino a 24.000 di reddito complessivo, poi scende in modo lineare fino a zero a 26.000. Dal 2018 le soglie sono 24.600 e 26.600
     (legge 205/2017, art. 1 c. 132). Serve la "capienza": imposta lorda maggiore della detrazione da lavoro dipendente (cioe' R sopra
     circa 8.174 euro). Primo semestre 2020: 480 euro (960 x 6/12) con le stesse soglie 2018-19.
     Testo di legge nel D.L. 3/2020 coordinato (Gazzetta Ufficiale n. 90 del 4/4/2020) e dossier Camera D20003.
   - Dal 1/7/2020 trattamento integrativo (D.L. 3/2020 art. 1): 600 euro per il 2020 (secondo semestre), 1.200 euro dal 2021, se R fino
     a 28.000 e c'e' capienza.
   - Dal 2022 (legge 234/2021): 1.200 euro se R fino a 15.000 e imposta lorda maggiore della detrazione; tra 15.000 e 28.000 solo se le
     detrazioni (familiari, lavoro, alcuni oneri) superano l'imposta lorda: per il nostro caso tipo (nessun carico) non spetta mai.
     AdE circolare 4/E 2022. Per il 2024 la capienza si misura con la detrazione ridotta di 75 euro (AdE circolare 2/E 2024, par. 1.3).

6. ADDIZIONALE REGIONALE IRPEF - LOMBARDIA (sul reddito complessivo, per scaglioni; nessuna esenzione per il dipendente tipo)
   - 2022-2024: 1,23% fino a 15.000; 1,58% fino a 28.000; 1,72% fino a 50.000; 1,73% oltre
     (l.r. Lombardia 5/2022; https://www.regione.lombardia.it/bollo-auto-e-tributi-regionali/red-addizionale-regionale-irpef).
     Per il 2024 la Regione poteva cambiare entro il 15/4/2024; se non l'ha fatto valgono gli scaglioni 2023 (AdE circolare 2/E 2024).
     IPOTESI: per il 2024 uso le stesse aliquote del 2023 (la pagina della Regione indica queste aliquote come in vigore "dal 2022").
   - 2015-2021: 1,23% fino a 15.000; 1,58% fino a 28.000; 1,72% fino a 55.000; 1,73% fino a 75.000; 1,74% oltre
     (Directio, addizionali regionali 2014 e 2015: https://www.directio.it/News/Details/2394 ; CGIA/Blitz 7/5/2015: "Lombardia da tre a cinque aliquote").
   - 2014: 1,23% fino a 15.000; 1,53% fino a 28.000; 1,73% oltre (stessa fonte Directio).
   - 2012-2013: IPOTESI = stesse aliquote del 2014 (non ho trovato una fonte ufficiale per questi due anni; la Regione le aveva aumentate nel 2012).
   - 2011: 1,2% fino a 15.493,71; 1,3% fino a 30.987,41; 1,4% oltre (regime in vigore dal 2007, tabella AdE dell'addizionale regionale 2006:
     https://www.agenziaentrate.gov.it/portale/-/8-quadro-rv-45-addizionale-regionale-e-comunale-all-39-irpef). IPOTESI: invariato fino al 2011.

7. ADDIZIONALE COMUNALE IRPEF - MILANO (sul reddito complessivo; esenzione = sotto la soglia non si paga niente, sopra si paga su tutto)
   Fonte: Ministero dell'Economia e delle Finanze, Dipartimento delle Finanze, aliquote applicabili per Milano (F205):
   https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/risultato.htm?anno=9999&cc=F205
   - 2011: 0,2%, esenti fino a 33.500 (delibera 41 del 1/8/2011).
   - 2012: per scaglioni 0,2% fino a 15.000; 0,3% fino a 28.000; 0,4% fino a 55.000; 0,6% fino a 75.000; 0,8% oltre; esenti fino a 33.500
     (delibera 20 del 20/6/2012, testo trasmesso dal Comune e pubblicato l'8/2/2013; il sito del Ministero riporta per lo stesso anno
     anche una versione "inserita d'ufficio" con aliquote piu' basse 0,1-0,7%: scelgo quella del Comune; per R sotto 33.500 non cambia nulla).
   - 2013-2019: 0,8% con esenzione fino a 21.000 (delibera 36 del 21/10/2013).
   - 2020-2024: 0,8% con esenzione fino a 23.000 (delibera 46 del 28/9/2020).

8. NON CONSIDERATO: tasse "una tantum" (bonus 200 euro del 2022, DL 50/2022), tfr, previdenza complementare, sindacato, welfare aziendale,
   premi di risultato, straordinari, 14a, contratti con piu' di 13 mensilita', detrazioni per spese (sanitarie, mutuo...), il "contributo di
   solidarieta'" sopra 300.000 euro. Il contributo di assistenza per CIGS e simili (0,30%) e' dentro il 9,19%.

CONTROLLI: in fondo al file, con le cifre pubblicate da AdE, INPS e dal dossier della Camera (funzione controlli()).
"""
import sys, os, json

ANNI = list(range(2011, 2025))
PASSO = 100     # euro di lordo tra una riga e l'altra della tabella esportata (la pagina interpola)
SOGLIA_1 = {2011: 43042, 2012: 44204, 2013: 45530, 2014: 46031, 2015: 46123, 2016: 46123, 2017: 46123,
            2018: 46630, 2019: 47143, 2020: 47379, 2021: 47379, 2022: 48279, 2023: 52190, 2024: 55008}
SOGLIA_CUNEO_ALTA = 2692 * 13    # 34.996: sotto, taglio piu' piccolo (0,8 / 2 / 6 punti)
SOGLIA_CUNEO_BASSA = 1923 * 13   # 24.999: sotto, taglio piu' grande (3 / 7 punti)


def a_scaglioni(x, sc):
    """sc = [(limite_superiore, aliquota), ...], l'ultimo con limite None."""
    tot, prev = 0.0, 0.0
    for lim, al in sc:
        if lim is None or x <= lim:
            return tot + max(0.0, x - prev) * al
        tot += (lim - prev) * al
        prev = lim
    return tot


def inps(L, y):
    """Contributi INPS del lavoratore trattenuti (dopo gli eventuali tagli). Ritorna (contributi, taglio)."""
    pieno = 0.0919 * L + 0.01 * max(0.0, L - SOGLIA_1[y])
    taglio = 0.0
    if y == 2022 and L <= SOGLIA_CUNEO_ALTA:
        taglio = 0.008 * L + 0.012 * L * 7 / 13
    elif y == 2023 and L <= SOGLIA_CUNEO_ALTA:
        base = 0.03 if L <= SOGLIA_CUNEO_BASSA else 0.02
        taglio = base * L + 0.04 * L * 6 / 13
    elif y == 2024 and L <= SOGLIA_CUNEO_ALTA:
        taglio = (0.07 if L <= SOGLIA_CUNEO_BASSA else 0.06) * L * 12 / 13
    return pieno - taglio, taglio


def irpef_lorda(R, y):
    if y <= 2021:
        sc = [(15000, .23), (28000, .27), (55000, .38), (75000, .41), (None, .43)]
    elif y <= 2023:
        sc = [(15000, .23), (28000, .25), (50000, .35), (None, .43)]
    else:
        sc = [(28000, .23), (50000, .35), (None, .43)]
    return a_scaglioni(R, sc)


def detrazione13(R, y):
    if y <= 2013:
        if R <= 8000:
            d = 1840.0
        elif R <= 15000:
            d = 1338 + 502 * (15000 - R) / 7000
        elif R <= 55000:
            d = 1338 * (55000 - R) / 40000
            for lim, inc in ((24000, 10), (25000, 20), (26000, 30), (27700, 40), (28000, 25)):
                if 23000 < R <= lim:
                    d += inc
                    break
        else:
            d = 0.0
        return d
    if y <= 2021:
        if R <= 8000:
            return 1880.0
        if R <= 28000:
            return 978 + 902 * (28000 - R) / 20000
        if R <= 55000:
            return 978 * (55000 - R) / 27000
        return 0.0
    alta = 1955.0 if y == 2024 else 1880.0
    if R <= 15000:
        d = alta
    elif R <= 28000:
        d = 1910 + 1190 * (28000 - R) / 13000
    elif R <= 50000:
        d = 1910 * (50000 - R) / 22000
    else:
        d = 0.0
    if 25000 < R <= 35000:
        d += 65
    return d


def ulteriore_detrazione(R, y):
    if y not in (2020, 2021):
        return 0.0
    a, b = (480.0, 120.0) if y == 2020 else (960.0, 240.0)
    if 28000 < R <= 35000:
        return a + b * (35000 - R) / 7000
    if 35000 < R <= 40000:
        return a * (40000 - R) / 5000
    return 0.0


def bonus(R, lorda, det, y):
    """Bonus 80 euro (2014-primo semestre 2020) o trattamento integrativo (da luglio 2020)."""
    cap = lorda > det     # capienza
    b = 0.0
    if 2014 <= y <= 2020:
        pieno = {2014: 640.0, 2020: 480.0}.get(y, 960.0)
        lo, hi = (24000, 26000) if y <= 2017 else (24600, 26600)
        if cap:
            b += pieno * max(0.0, min(1.0, (hi - R) / (hi - lo)))
    if y == 2020 and R <= 28000 and cap:
        b += 600.0
    if y == 2021 and R <= 28000 and cap:
        b += 1200.0
    if y >= 2022:
        det_ti = det - 75 if y == 2024 else det
        if R <= 15000:
            if lorda > det_ti:
                b += 1200.0
        elif R <= 28000:
            b += min(1200.0, max(0.0, det - lorda))     # senza altre detrazioni (carichi, oneri) e' sempre 0
    return b


def add_regionale(R, y):
    if y == 2011:
        sc = [(15493.71, .012), (30987.41, .013), (None, .014)]
    elif y <= 2014:
        sc = [(15000, .0123), (28000, .0153), (None, .0173)]
    elif y <= 2021:
        sc = [(15000, .0123), (28000, .0158), (55000, .0172), (75000, .0173), (None, .0174)]
    else:
        sc = [(15000, .0123), (28000, .0158), (50000, .0172), (None, .0173)]
    return a_scaglioni(R, sc)


def add_comunale(R, y):
    if y == 2011:
        return 0.002 * R if R > 33500 else 0.0
    if y == 2012:
        return a_scaglioni(R, [(15000, .002), (28000, .003), (55000, .004), (75000, .006), (None, .008)]) if R > 33500 else 0.0
    soglia = 21000 if y <= 2019 else 23000
    return 0.008 * R if R > soglia else 0.0


def conto(L, y):
    """Tutte le voci per un lordo annuo L (euro dell'anno y)."""
    contr, taglio = inps(L, y)
    R = L - contr
    lorda = irpef_lorda(R, y)
    det = detrazione13(R, y)
    ult = ulteriore_detrazione(R, y)
    netta = max(0.0, lorda - det - ult)
    reg = add_regionale(R, y)
    com = add_comunale(R, y)
    bon = bonus(R, lorda, det, y)
    netto = L - contr - netta - reg - com + bon
    return dict(lordo=L, contributi=contr, taglio_cuneo=taglio, reddito_complessivo=R, irpef_lorda=lorda, detrazione=det,
                ulteriore_detrazione=ult, irpef_netta=netta, add_regionale=reg, add_comunale=com, bonus=bon, netto=netto)


def netto(L, y):
    return conto(L, y)['netto']


def controlli():
    """Confronto con le cifre pubblicate. Ritorna lista di (descrizione, nostro, pubblicato, fonte)."""
    out = []

    def irpef_netta_R(R, y):   # IRPEF netta partendo dal reddito complessivo (come negli esempi AdE)
        lorda = irpef_lorda(R, y)
        return max(0.0, lorda - detrazione13(R, y) - ulteriore_detrazione(R, y))
    f = 'Agenzia delle Entrate, circolare 4/E del 18/2/2022, par. 1.5'
    out.append(('IRPEF netta 2021, reddito 30.000', irpef_netta_R(30000, 2021), 5683, f))
    out.append(('IRPEF netta 2021, reddito 50.000', irpef_netta_R(50000, 2021), 15139, f))
    out.append(('IRPEF netta 2022, reddito 30.000', irpef_netta_R(30000, 2022), 5599, f))
    out.append(('IRPEF netta 2022, reddito 50.000', irpef_netta_R(50000, 2022), 14400, f))
    f2 = 'Agenzia delle Entrate, circolare 2/E del 6/2/2024, tabella degli scaglioni'
    out.append(('IRPEF lorda 2024, reddito 28.000', irpef_lorda(28000, 2024), 6440, f2))
    out.append(('IRPEF lorda 2024, reddito 50.000', irpef_lorda(50000, 2024), 14140, f2))
    f3 = 'Camera dei deputati, dossier D20003 (D.L. 3/2020), tabella dell\'ulteriore detrazione, 2020 secondo semestre'
    out.append(('Ulteriore detrazione 2020, reddito 30.000', ulteriore_detrazione(30000, 2020), 565.7, f3))
    out.append(('Ulteriore detrazione 2020, reddito 36.000', ulteriore_detrazione(36000, 2020), 384, f3))
    f4 = 'INPS, circolare 11/2024, esempio di quota IVS del lavoratore'
    mensile = 2000.0                       # 2.000 euro al mese, 13 mensilita': L = 26.000
    c, tg = inps(mensile * 13, 2024)
    quota_mese = (0.0919 * mensile * 12 - tg) / (mensile * 12)    # sulle 12 mensilita' ordinarie
    out.append(('Quota IVS 2024 sulla paga mensile fino a 2.692 euro (%)', quota_mese * 100, 3.19, f4))
    mensile = 1900.0
    c, tg = inps(mensile * 13, 2024)
    quota_mese = (0.0919 * mensile * 12 - tg) / (mensile * 12)
    out.append(('Quota IVS 2024 sulla paga mensile fino a 1.923 euro (%)', quota_mese * 100, 2.19, f4))
    return out


def griglia():
    lordi = list(range(0, 150001, PASSO))
    return lordi, {str(y): [int(round(netto(L, y))) for L in lordi] for y in ANNI}


if __name__ == '__main__':
    base = sys.argv[1]
    print('CONTROLLI (nostro / pubblicato / scarto)')
    for d, a, b, f in controlli():
        print('  %-62s %10.2f %10.2f %8.2f   %s' % (d, a, b, a - b, f))
    if '--solo-controlli' in sys.argv:
        sys.exit(0)
    lordi, g = griglia()
    out = {
        'nota': ('Netto annuo stimato di un dipendente a tempo indeterminato, residente a Milano, senza carichi di famiglia, per lordo annuo '
                 '(euro dell\'anno). Griglia ogni 100 euro da 0 a 150.000, si interpola. Regole e fonti: permettersi/scripts/netto.py.'),
        'lordo_da': 0, 'passo': PASSO, 'anni': ANNI, 'netto': g,
    }
    p = os.path.join(base, 'docs', 'permettersi', 'data', 'netto.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('scritto', p, os.path.getsize(p), 'byte')
    for y in (2015, 2024):
        c = conto(25926, y)
        print(y, {k: round(v, 1) for k, v in c.items()})
