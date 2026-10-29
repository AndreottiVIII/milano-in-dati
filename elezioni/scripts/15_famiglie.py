"""Passo 2: costruisce famiglie_partiti.csv (tabella modificabile) con regole semplici.
uso: python -I 15_famiglie.py <cartella elezioni>
La tabella e un file CSV: per correggere basta cambiare la colonna 'famiglia'. Lo script 16_aggrega.py legge solo il CSV.
Colonne: lista;famiglia;anno_da;anno_a;stato;da_rivedere;voti_totali;elezioni;nota
  stato = regola (trovata da una regola) | altri_di_default (nessuna regola: finisce in Altri)
"""
import sys, os, re, unicodedata
import pandas as pd

base = sys.argv[1]
voti = pd.read_csv(os.path.join(base, 'pulito', 'voti_sezione.csv'), encoding='utf-8-sig', dtype={'lista': str}, usecols=['elezione_id', 'lista', 'voti'])
cat = pd.read_csv(os.path.join(base, 'pulito', 'elezioni.csv'), encoding='utf-8-sig')
site = cat[(cat.nel_sito == 'si') & (cat.gruppo != 'referendum')]
voti = voti[voti.elezione_id.isin(site.elezione_id)]
tot = voti.groupby('lista').voti.sum()
n_el = voti.groupby('lista').elezione_id.nunique()
gruppi = voti.merge(site[['elezione_id', 'gruppo', 'anno']], on='elezione_id').groupby('lista').apply(
    lambda g: ', '.join(sorted(set('%s %d' % (a, b) for a, b in zip(g.gruppo, g.anno)))), include_groups=False)


def norm(s):
    s = s.lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.replace('+', ' piu ')
    s = re.sub(r"[^a-z0-9]+", ' ', s).strip()
    return s


# (pattern, famiglia, da_rivedere, nota). Prima regola che combacia vince.
R = [
    # --- eccezioni che finiscono in Altri (prima delle regole generali)
    (r'^lega (alp|pens|az|merid|padana|lombardo veneta|soc|comunista)', 'Altri', 0, 'liste "Lega" minori, non la Lega Nord'),
    (r'pens liga', 'Altri', 0, ''),
    (r'verdi moratti|verdi verdi|lista civ moratti|moratti m$|miracolo a milano|uniti con fo|io amo milano|milano al centro', 'Altri', 1, 'lista civica locale, schieramento non verificato'),
    (r'popolari italia domani|popolari per l italia|popolo della famiglia', 'Altri', 0, ''),
    (r'alleanza lombarda|all lombarda|auton all lomb|lombardia per le autonomie|energie per la lombardia|lista nord ?destra|lista un altra provincia|lista no box|lombardia autonoma|mpa|grande nord|fronte nord|unione padana', 'Altri', 1, 'autonomisti/civiche: schieramento non verificato'),
    (r'italexit|italia sovrana|^vita$|paragone|cappato|radicali con|bonino|pannella|part radicale|emma bonino|lista referendum|federalisti|antiproibizionisti|part op eur|part umanista|pension|pens |casal pens|automobilisti|caccia pesca|mov cacciatori|europa 2000|consumator|codacons', 'Altri', 0, 'radicali, pensionati e liste tematiche'),
    # --- Lega
    (r'^lega\b|liga veneta|lavoratori padani|pens sicura|formentini', 'Lega', 0, ''),
    # --- M5S
    (r'movimento 5 stelle|movimento cinque stelle|movimento beppe grillo|lista del grillo|calise|gianluca corrado', 'M5S', 0, ''),
    # --- Sinistra (a sinistra del PD e dei suoi predecessori)
    (r'la sinistra per sala|sinistra x milano|sinistra per pisapia|sinistra per la lombardia|sinistra ecologia|^sel$|sinistra e liberta|^la sinistra$|etico a sinistra|sin arcobaleno|sin critica|nuova sin|rifond|rif comunista|comunist|^part com|^pdup|dem proletaria|liberi e uguali|potere al popolo|unione popolare|alleanza verdi e sinistra|europa verde|rivoluzione civile|per una sinistra|milano in comune|lista sinistra provincia|verdi|lista verde|rizzo|altra europa|tsipras|pace terra dignita|sinistra critica|mariani|umberto gay|^gay u|^la rete$', 'Sinistra', 0, ''),
    # --- Destra
    (r'^msi|dem nazionale|^an$|alleanza nazionale|fiamma|la destra|destra f t|destra sociale|forza nuova|casapound|altern sociale|alternativa sociale|azione sociale|idea sociale|italia agli italiani|fratelli d italia|meloni|patto segni an|de corato|staiti', 'Destra', 0, ''),
    # --- Centro (prima del centrodestra solo dove serve)
    (r'letizia moratti presidente|azione italia viva|azione siamo europei|azione italia viva calenda|calenda|italia viva|scelta civica|con monti|scelta europea|piu europa|palmeri|stati uniti d europa|nuovo polo|casini unione|udc casini|mastella|^teso a$', 'Centro', 0, ''),
    # --- Centrodestra
    (r'forza italia|^pdl$|popolo del[a-z]* liberta|popolo liberta|tremonti|casa liberta|polo liberta|polo popolare|^ccd|^cdu|cdu ppe|nuovo centro destra|noi con l italia|noi moderati|per parisi|parisi|maroni|fontana|lombardia ideale|bernardo|lupi|lista l moratti|moratti l|moratti letizia|albertini|nuovo psi|io corro per milano|pdl', 'Centrodestra', 0, ''),
    # --- Centro
    (r'^dc$|democrazia cristiana|^pri$|^pri |^pli$|^psdi$|^udc|alleanza di centro|liberali centro|lista dini|rinnov italiano|^patto segni|patto con milano|patto per l italia|^ppi$|^popolari$|dem europea|con le donne|udeur|part liberale|bassetti|fare per fermare|futuro e liberta|centro popolare|repubbl eur|liberal', 'Centro', 0, ''),
    # --- Centrosinistra
    (r'^pds$|^ds$|^pd$|^pd |partito democratico|part democratico|i democratici|^democratici|ulivo|^l unione|margherita|^psi$|^sdi$|soc italiani|part socialista|socialisti|soc riformisti|patto democr|all democratica|alleanza democratica|popolari prodi|centro sinistra|italia dei valori|italia valori|di pietro|beppe sala|sala sindaco|volt sala|milano in salute|la milano radicale|impegno civico|^centro democratico|ferrante|milano civica per pisapia|milly moratti|lombardia civica|patto civico|gori presidente|lombardia progressista|majorino|penati|laburisti|riformisti lavoriamo|rosa nel pugno|girasole|civica popolare lorenzin|italia europa insieme|patto per milano|fiducia in milano|italia democr|\bsala\b|dalla chiesa|fumagalli|antoniazzi|borghini|pisapia', 'Centrosinistra', 0, 'filone PCI-PDS-DS-PD piu alleati storici (PSI, Margherita, IdV)'),
]
RI = [(re.compile(p), f, d, n) for p, f, d, n in R]
# liste incerte (segnate da_rivedere anche se una regola le prende)
UNCERTAIN = re.compile(r'^la rete$|fiducia in milano|patto segni an|io corro per milano|^psi$|udeur|dem europea|girasole|rosa nel pugno|soc riformisti|^pci$|italia europa insieme|civica popolare|centro popolare|futuro e liberta|tremonti|etico a sinistra|rinnov italiano|lista dini|^part socialista|di pietro|italia valori|italia dei valori|^laburisti|dc nuovo psi|nuovo psi|con le donne|bassetti|teso a$')

rows = []
for lista in sorted(tot.index):
    n = norm(lista)
    if n == 'pci':
        for (a, b, fam) in [(1, 1992, 'Centrosinistra'), (1993, 2100, 'Sinistra')]:
            rows.append(dict(lista=lista, famiglia=fam, anno_da=a, anno_a=b, stato='regola', da_rivedere='si',
                             voti_totali=int(tot[lista]), elezioni=gruppi[lista], nota='PCI storico (fino al 1992) nel filone PDS-PD; "PCI" 2021 e un partito nuovo, Sinistra'))
        continue
    fam, dr, nota, stato = 'Altri', 0, '', 'altri_di_default'
    for rx, f, d, nt in RI:
        if rx.search(n):
            fam, dr, nota, stato = f, d, nt, 'regola'
            break
    if UNCERTAIN.search(n):
        dr = 1
    if stato == 'altri_di_default' and tot[lista] > 5000:
        dr = 1
    rows.append(dict(lista=lista, famiglia=fam, anno_da='', anno_a='', stato=stato, da_rivedere='si' if dr else '',
                     voti_totali=int(tot[lista]), elezioni=gruppi[lista], nota=nota))
# referendum
rows.append(dict(lista='Sì', famiglia='Sì', anno_da='', anno_a='', stato='regola', da_rivedere='', voti_totali='', elezioni='referendum', nota=''))
rows.append(dict(lista='No', famiglia='No', anno_da='', anno_a='', stato='regola', da_rivedere='', voti_totali='', elezioni='referendum', nota=''))
df = pd.DataFrame(rows)
df.to_csv(os.path.join(base, 'famiglie_partiti.csv'), index=False, sep=';', encoding='utf-8-sig')
print(len(df), df.famiglia.value_counts().to_dict())
d0 = df[df.stato == 'altri_di_default'].sort_values('voti_totali', ascending=False)
print('altri di default:', len(d0), 'voti', int(d0.voti_totali.sum()), 'su', int(tot.sum()))
print(d0[['lista', 'voti_totali', 'elezioni']].head(60).to_string())
