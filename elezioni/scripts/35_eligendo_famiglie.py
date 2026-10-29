"""Propone la famiglia per le liste pre-1979 non presenti in famiglie_partiti.csv. NON modifica quella tabella.
Uso: python -I 35_eligendo_famiglie.py <elezioni_dir> <uscita.csv>"""
import sys, os, csv, collections
d, out = sys.argv[1], sys.argv[2]
S, CS, C, CD, D, A = 'Sinistra', 'Centrosinistra', 'Centro', 'Centrodestra', 'Destra', 'Altri'
# lista: (famiglia, da_rivedere, nota)
P = {
 'PSIUP': (S, '', 'PSIUP -> Sinistra (regola)'), 'PSI UP': (S, '', 'PSIUP (scritto PSI UP) -> Sinistra (regola)'),
 'DEM.PROL': (S, '', 'Democrazia Proletaria (stessa lista di "Dem. Proletaria"; 1976 e cartello di sinistra extraparlamentare) -> Sinistra (regola)'),
 'DEM. PROL.': (S, '', 'Democrazia Proletaria (come DEM.PROL) -> Sinistra (regola)'),
 'MSI-DN': (D, '', 'MSI-DN -> Destra (regola; il Comune scrive MSI)'), 'MSI DN': (D, '', 'MSI-DN -> Destra (regola)'),
 'P.MONARCHICO POP.': (D, '', 'monarchici -> Destra (regola)'), 'P.NAZ.MON.ALL.D.LAV.': (D, '', 'monarchici -> Destra (regola)'),
 'P.NAZ.MONARCHICO': (D, '', 'PNM -> Destra (regola)'), 'PART MON NAZ': (D, '', 'PNM -> Destra (regola)'), 'PART.MON.NAZ.': (D, '', 'PNM -> Destra (regola)'),
 'PDIUM': (D, '', 'PDIUM -> Destra (regola)'),
 'DN-CD': (D, '', 'Democrazia Nazionale: come "Dem. Nazionale" gia in Destra'),
 'P.RAD': (A, '', 'Partito Radicale: come "Part. Radicale" gia in Altri'),
 'POE': (A, '', 'Partito Operaio Europeo: come "Part. Op. Eur." gia in Altri'),
 'NUOVA SIN.UNITA': (S, '', 'come "Nuova Sin. Unita" gia in Sinistra'),
 'PARTITO POPOLARE ITALIANO': (C, '', 'come "PPI" (1979) gia in Centro'),
 'PSU': (CS, 'si', 'PSI-PSDI unificati 1968-69: base PSI -> Centrosinistra; ma PSDI sarebbe Centro'),
 'SOCIALDEM': (C, '', 'socialdemocratici (PSDI) -> Centro (regola)'),
 'UNITA\' SOCIALISTA': (C, 'si', '1948, PSLI-PSU di Saragat (poi PSDI) -> Centro'),
 'UNITA\' SOC.-PRI': (C, 'si', '1948 Senato, socialisti saragattiani + PRI -> Centro'),
 'PRI-P.RAD.': (C, 'si', '1958, PRI con radicali di Pannunzio -> Centro (PRI)'),
 'FR.DEMOCR.POPOLARE': (S, 'si', '1948, PCI+PSI insieme: Sinistra (PCI), ma contiene anche il PSI (Centrosinistra)'),
 'SOCIALCOMUNISTI': (S, 'si', '1948 Senato, Fronte PCI+PSI: come FR.DEMOCR.POPOLARE'),
 'PCI-PSIUP': (S, '', 'Senato 1968/1972: lista comune PCI+PSIUP -> Sinistra'),
 'PC.INTERNAZIONALISTA': (S, '', 'comunisti internazionalisti (bordighisti) -> Sinistra'),
 'PC(MARX-LEN)IT': (S, '', 'marxisti-leninisti (extraparlamentare) -> Sinistra'),
 'MANIFESTO': (S, '', 'Il Manifesto 1972 -> Sinistra'),
 'MOV.POL.LAV.': (S, 'si', 'Movimento Politico dei Lavoratori (Labor, cattolici di sinistra), 1972; potrebbe essere Altri'),
 'UN.SOCIAL.INDIP.': (S, 'si', 'Unione Socialisti Indipendenti 1953 (ex PCI); potrebbe essere Altri'),
 'UNITA\'POPOLARE': (CS, 'si', '1953, Parri/Calamandrei contro la legge truffa; potrebbe essere Sinistra'),
 'FR.UOMO QUALUNQUE': (D, 'si', 'Uomo Qualunque 1946: Destra o Altri (scelta da confermare)'),
 'BLOCCO NAZ.LIBERTA\'': (D, 'si', '1946, lista conservatrice-monarchica con ex Uomo Qualunque; potrebbe essere Centro'),
 'BLOCCO NAZIONALE': (C, 'si', '1948, PLI (Einaudi) + Uomo Qualunque: Centro per il PLI, ma anche Destra'),
 'UN.DEMOC.NAZIONALE': (C, 'si', '1946, Unione Democratica Nazionale (liberali Croce/Nitti/Orlando, base PLI) -> Centro'),
 'ALL.DEMOC.NAZIONALE': (C, 'si', '1953, Alleanza Democratica Nazionale (liberali dissidenti, Corbino); incerto'),
 'CDR': (C, 'si', '1946, Concentrazione Democratica Repubblicana (Parri, ex Partito d\'Azione, vicina al PRI) -> Centro'),
 'COMUNITA\'': (A, 'si', '1958, Movimento Comunita di Adriano Olivetti (liberal-socialista); potrebbe essere Centrosinistra'),
 'NUOVA REPUBBLICA': (A, 'si', '1968, Pacciardi (ex PRI, presidenzialista di destra); potrebbe essere Destra'),
 'M.COMB.IT-FR.RIN.NAZ': (A, 'si', '1963, combattentistico; potrebbe essere Destra'),
 'P.NAZIONALE LAVORO': (A, 'si', '1958, piccola lista; area incerta'),
}
ALTRI_MINORI = ['BLOCCO POP.UNIONISTA', 'CONC.EUROPEA DEMOC.', 'CONC.NAZ.COMBAT.UNIT', 'CONC.UNITA\'RURALE', 'FR.DEGLI ITALIANI', 'IND.',
                'MOV.NAZ.DEM.SOC.', 'MOV.POL.CATT.IT.', 'MOVIM.AUT.REG.-M.A.R.P.', 'P.CONTADINI D\'ITALIA', 'P.NETTISTA ITALIANO', 'PAPI',
                'PS D\'AZ.', 'RAG.VOL."T"', 'SCHIERAMENTO NAZ.', 'UN.AUTONOMISTI D\'IT.', 'UN.FORZE DEM.', 'UN.MOV.FEDERALISTI', 'UN.NAZ.DEM.IMP.PUB.']
for l in ALTRI_MINORI: P[l] = (A, '', 'lista minore o locale, nessuna regola -> Altri')
fam = {r['lista'].strip().lower() for r in csv.DictReader(open(os.path.join(d, 'famiglie_partiti.csv'), encoding='utf-8-sig'), delimiter=';')}
voti = collections.Counter(); el = collections.defaultdict(set)
for r in csv.DictReader(open(os.path.join(d, 'pulito', 'milano_pre1979.csv'), encoding='utf-8-sig')):
    if r['tipo'] == 'referendum': continue
    voti[r['lista']] += int(r['voti']); el[r['lista']].add((r['tipo'], r['data'][:4]))
missing = []
with open(out, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['lista', 'famiglia', 'anno_da', 'anno_a', 'stato', 'da_rivedere', 'voti_totali', 'elezioni', 'nota'])
    for l in sorted(voti):
        if l.lower() in fam: continue
        if l not in P: missing.append(l); continue
        fa, rv, nota = P[l]
        stato = 'altri_di_default' if l in ALTRI_MINORI else 'regola'
        ev = ', '.join('%s %s' % (t if t != 'regionali' else 'regionali_consiglio', y) if t != 'comunali' else 'comunali_consiglio %s' % y for t, y in sorted(el[l], key=lambda x: (x[1], x[0])))
        w.writerow([l, fa, '', '', stato, rv, voti[l], ev, nota])
print('liste non mappate:', missing)
print(sum(1 for _ in open(out, encoding='utf-8-sig')) - 1, 'righe')
