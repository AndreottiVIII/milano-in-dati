"""Legge i risultati di 06 e produce matching_candidati.csv (una riga per strada senza tag)."""
import sys, json, re, unicodedata, pandas as pd
units_csv, mdir, out_csv = sys.argv[1:4]
search = json.load(open(f"{mdir}/search_results.json", encoding='utf8'))
ents = json.load(open(f"{mdir}/entities.json", encoding='utf8'))

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s.replace("'", " ")).split()

TYPE = r"^(via privata|via|viale|piazzale|piazza|piazzetta|largo|corso|vicolo|galleria|passaggio|bastioni|cavalcavia|strada|parco|giardino|alzaia|foro|sottopasso|sito|vicoletto|ripa|rampa|sottopassaggio|stradone|strada vicinale)\s+"
ART = r"^(del|della|dello|dell'|dei|degli|delle|di|de|d')\s*"
SEX = {'Q6581072': 'donna', 'Q6581097': 'uomo'}
PLACE = {'Q747074', 'Q515', 'Q486972', 'Q8502', 'Q23442', 'Q4022', 'Q3957', 'Q532', 'Q6256', 'Q35657', 'Q82794', 'Q1549591', 'Q15284',
         'Q1620908', 'Q54050', 'Q23397', 'Q34763', 'Q123705', 'Q5084', 'Q3024240', 'Q7275', 'Q10864048', 'Q1048835', 'Q41176', 'Q16970',
         'Q1007870', 'Q2221906', 'Q56061', 'Q1763214', 'Q27666946', 'Q1637706', 'Q192287', 'Q22698', 'Q570116', 'Q39816', 'Q4421',
         'Q46831', 'Q355304', 'Q13221722', 'Q20019530', 'Q1115575', 'Q484170', 'Q161910', 'Q1229765', 'Q6465', 'Q1799794', 'Q2065736',
         'Q3957', 'Q1093829', 'Q1006733', 'Q15642541', 'Q83405'}
EVENT = {'Q178561', 'Q198', 'Q13418847', 'Q1656682', 'Q1190554', 'Q350604', 'Q645883', 'Q40231', 'Q8065', 'Q3839081', 'Q273120',
         'Q11514315', 'Q1478437', 'Q124734', 'Q625298', 'Q2627975', 'Q1138496'}
MONTHS = r"\b(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b"

df = pd.read_csv(units_csv, dtype=str).fillna('')
core_hw = ('residential', 'tertiary', 'secondary', 'primary', 'unclassified', 'living_street', 'pedestrian', 'place=square', 'trunk')
df['core'] = df.apply(lambda r: r.origine == 'comune' or r.highway_osm.split(':')[0] in core_hw, axis=1)
todo = df[(df.qids_osm == '') & df.core].copy()

def street_name(r):
    s = r.descrittivo if r.origine == 'comune' else re.sub(TYPE, '', r.descrittivo, flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s).strip()
    return re.sub(ART, '', s, flags=re.I).strip() or s

def italian(e):
    return bool({'Q38', 'Q172579', 'Q165154', 'Q2415901', 'Q4948', 'Q12548', 'Q15103'} & set(e['cit'])) or 'ital' in e['desc'].lower() or 'milan' in e['desc'].lower()

out = []
for _, r in todo.iterrows():
    k = street_name(r)
    nk = norm(k)
    res = search.get(k) or []
    cands = []
    for x in res:
        e = ents.get(x['id'])
        if not e:
            continue
        labs = [norm(e['label_it']), norm(e['label_en']), norm(x['match'])]
        exact = any(sorted(l) == sorted(nk) for l in labs if l)
        part = (not exact) and bool(e['p31']) and any(set(nk) <= set(l) and len(l) <= len(nk) + 3 for l in labs if l)
        cands.append(dict(id=x['id'], e=e, exact=exact, part=part, human='Q5' in e['p31']))
    exh = [c for c in cands if c['exact'] and c['human']]
    parth = sorted([c for c in cands if c['part'] and c['human'] and c['e']['sitelinks'] >= 8], key=lambda c: -c['e']['sitelinks'])
    nonh = [c for c in cands if c['exact'] and not c['human']]
    cat, conf, reason, chosen = 'sconosciuto', 'nessuno', 'nessun candidato umano trovato', []
    if re.search(r"\d", k) or re.search(MONTHS, k, re.I):
        cat, conf, reason = 'data_evento', 'nessuno', 'nome con numero o mese (probabile data o evento)'
        if exh:
            conf, reason, chosen, cat = 'incerto', 'nome con numero/mese ma esiste una persona con lo stesso nome', exh[:1], 'persona'
    elif len(exh) == 1:
        chosen = exh
        cat = 'persona'
        conf = 'sicuro'
        reason = 'un solo umano con etichetta o alias identico al nome'
        if not italian(exh[0]['e']) and not exh[0]['e']['cit']:
            conf, reason = 'incerto', 'un solo umano con nome identico, ma senza legame evidente con l Italia'
        if nonh:
            conf, reason = 'incerto', reason + '; esiste anche un\'entita non umana con lo stesso nome (luogo o altro)'
        if len(nk) == 1 and conf == 'sicuro':
            conf, reason = 'incerto', 'nome di una sola parola: possibile luogo o cognome omonimo'
    elif len(exh) > 1:
        s = sorted(exh, key=lambda c: -c['e']['sitelinks'])
        chosen = s[:3]
        cat = 'persona'
        if s[0]['e']['sitelinks'] >= 15 and s[0]['e']['sitelinks'] >= 4 * max(1, s[1]['e']['sitelinks']) and italian(s[0]['e']) and len(nk) > 1:
            conf, reason = 'sicuro', 'omonimi: prevale nettamente il piu famoso (numero di sitelink) e legato all Italia'
        else:
            conf, reason = 'incerto', f'{len(exh)} umani con lo stesso nome: scegliere a mano'
    elif parth:
        chosen = parth[:3]
        cat = 'persona'
        conf = 'incerto'
        reason = 'nessuna corrispondenza esatta: nome parziale (solo cognome o senza secondo nome)'
    elif nonh:
        c0 = nonh[0]
        if set(c0['e']['p31']) & EVENT:
            cat, reason = 'data_evento', 'corrisponde a un evento su Wikidata'
        elif set(c0['e']['p31']) & PLACE:
            cat, reason = 'luogo', 'corrisponde a un luogo su Wikidata'
        else:
            cat, reason = 'altro_non_persona', 'corrisponde a un\'entita non umana su Wikidata: ' + (c0['e']['desc'] or c0['e']['label_it'])[:60]
        chosen = nonh[:1]
        conf = 'nessuno'
    first = chosen[0] if chosen and chosen[0]['human'] else None
    out.append(dict(codice_via=r.codice_via,
                    nome_strada=(r.tipo + ' ' + r.descrittivo).strip() if r.origine == 'comune' else r.descrittivo,
                    nome_cercato=k, origine=r.origine, categoria=cat, confidenza=conf, motivo=reason,
                    candidati_qid=';'.join(c['id'] for c in chosen),
                    candidati_label=' | '.join(c['e']['label_it'] or c['e']['label_en'] for c in chosen),
                    candidati_descrizione=' | '.join(c['e']['desc'][:70] for c in chosen),
                    sesso_primo=(SEX.get(first['e']['sex'][0], 'altro') if first['e']['sex'] else 'non indicato') if first else '',
                    nascita_primo=first['e']['birth'] if first else '',
                    morte_primo=first['e']['death'] if first else ''))
res = pd.DataFrame(out)
res.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(len(res))
print(res.groupby(['categoria', 'confidenza']).size())
print(res[res.confidenza == 'sicuro'].sesso_primo.value_counts().to_dict(), res[res.confidenza == 'incerto'].sesso_primo.value_counts().to_dict())
