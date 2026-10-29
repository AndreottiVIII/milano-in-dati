"""Fase 2, passo 2: classificazione migliorata di TUTTE le 4.280 strade (tag OSM + ricerca Wikidata con titoli + nomi di battesimo + gruppi + santi).
Uso: python -I 11_classifica_v2.py strade_unite.csv etimologie_wikidata.csv osm_strade_aggregate.csv v2dir out_dir
Produce in out_dir: strade_classificate_v2.csv (tutte), matching_candidati_v2.csv (solo senza tag), da_verificare_donne.csv"""
import sys, json, re, unicodedata, os, importlib.util
import pandas as pd

units_csv, etim_csv, agg_csv, v2dir, outdir = sys.argv[1:6]
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('m10', os.path.join(here, '10_chiavi_e_ricerca_v2.py'))
m10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m10)

SEXQ = {'Q6581072': 'donna', 'Q6581097': 'uomo'}
search = json.load(open(f"{v2dir}/search_results.json", encoding='utf8'))
ents = json.load(open(f"{v2dir}/entities.json", encoding='utf8'))
keymap = json.load(open(f"{v2dir}/chiavi_per_strada.json", encoding='utf8'))
etim = pd.read_csv(etim_csv, dtype=str).fillna('').set_index('qid')


def fold(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s.replace("'", " ")).split()


FEM_NAMES = set("""adele adelaide adelina adriana agata agnese alba alberta alessandra alice alida alina allegra amalia amelia anastasia andreina angela angelica angiolina anita anna annamaria annetta annunziata antonia antonietta arianna armida
assunta augusta aurelia aurora barbara beatrice benedetta bernardina berta bianca bice bona bruna camilla candida carla carlotta carolina caterina cecilia celeste chiara cinzia clara clarissa claudia clelia clementina clotilde concetta
consolata costanza cristina cunegonda dafne daria debora delia diana dina dolores domitilla donata dora dorotea edith elena eleonora elisa elisabetta elsa emilia emma enrica erminia ernesta estella ester eufemia eugenia eva evelina fabiola
fanny fausta federica felicita fernanda filomena fiorella flavia flora fortunata francesca franca gabriella gaetana gemma generosa giacinta gianna ginevra gina giorgia giovanna giulia giuliana giuseppina giustina gioconda gisella grazia graziella
greta guendalina ida ilaria ilda immacolata ines irene iris irma isabella isotta italia ivana jolanda iolanda laura lavinia lea leonora letizia lia liliana lidia lina livia lorella lorenza lucia luciana lucrezia ludovica luigia luisa lydia manuela
marcella margherita maria mariangela marianna marina marisa marta martina matilde mafalda maddalena melania mercedes michela mimma mirella miriam monica nadia natalia nella nicoletta nilde noemi nora norma olga olimpia ornella ortensia ottavia
paola paolina pasqua patrizia perla petronilla pia piera pierina placidia polissena primavera priscilla rachele raffaella regina renata rita roberta romilda romana rosa rosalia rosanna rosaria rosetta rosina rossana sabina samantha sandra santina
sara sofia silvia simona speranza stefania stella tecla teodolinda teresa tina tiziana ursula valentina valeria vanna vera veronica vincenza vittoria viola violetta virginia vita wanda zaira zita gae frida ipazia artemisia sibilla marie anne jane
george hannah hanna emily charlotte florence ingrid agatha mary sophie helen ada milly mina oriana alda alfonsina amedea antonella arabella argia ausilia bettina brigida cleonice coletta cosima edvige eloisa ersilia fedora fiammetta florinda
gualtiera ippolita isabel lisa lola lodovica lucilla malvina mara melchiorra nerina nives novella odette ofelia oliva palmira pamela penelope pierangela plautilla quirina rebecca rina rufina savina serafina severina silvana sidonia tatiana tilde
ubalda vanda venera vilma vitalba zelinda zenobia zoe orsola radegonda marcellina germana adelasia gilda giuditta cleopatra elvira ermelinda esterina eurosia fosca giacomina giannina ginia lodovica loredana lucilla margherita marisa nanda ninetta olimpia
piera rosita santa selma tullia ulrica valdina vittorina zanobia teodora tarsilla crocifissa addolorata assunta arcangela brunilde cesira cornelia dalila elettra emiliana erminia eugenia genoveffa gesuina giustina ilia isolina leopolda lisetta
mariuccia mirella ottavia pierina pompea rachele ruth sabrina sidonia stefana tersilla venusta veneranda viviana wilma yvonne""".split())
MALE_NAMES = set("""adolfo adriano agostino alberto aldo alessandro alessio alfonso alfredo amedeo amerigo andrea angelo anselmo antonio arnaldo arrigo arturo attilio augusto aurelio baldassarre bartolomeo battista benedetto benito bernardo bruno camillo carlo cesare
claudio clemente corrado cosimo costantino damiano daniele dante dario davide domenico donato edoardo egidio elia emanuele emilio enrico enzo ermanno ernesto ettore eugenio fabio fabrizio federico felice ferdinando fernando filippo flavio francesco franco
fulvio gabriele gaetano galileo gaspare gerolamo giacinto giacomo gian gianni giorgio giosue giovanni giulio giuseppe giusto goffredo guglielmo guido gustavo ignazio innocenzo ippolito italo jacopo lamberto leonardo leone leopoldo lodovico lorenzo luca luciano
lucio ludovico luigi manlio marco mario martino massimo matteo mattia maurizio michele napoleone nazario nicola niccolo nicolo orazio oreste oscar osvaldo ottavio ottone pablo paolo pasquale pellegrino piero pietro pio placido quintino raffaele raimondo
renato riccardo roberto rocco rodolfo romeo romolo ruggero salvatore samuele sandro santo saverio sebastiano serafino sergio severino silvio simone stefano tancredi tito tommaso ubaldo ugo umberto valentino vincenzo virgilio vittorio walter zeno ambrogio
anacleto aristide arialdo carlo gerardo gregorio onorato orlando ottorino ruggiero teodoro teofilo vito achille alvise ardito attilio bonaventura bonifacio candido carmelo celestino cipriano cirillo cristoforo curzio dionigi eligio erasmo eusebio fedele
filiberto florenzio fortunato gelasio glicerio gottardo graziano ilario isidoro lazzaro libero lino luigi macario marcellino mauro metodio nabore nereo onofrio pancrazio patrizio pompeo protaso prospero remigio rinaldo rosario sallustio sisto taddeo
tiziano tullio urbano valerio venanzio vigilio vitale zaccaria""".split())
FEM_TITLES = {'santa', 'suor', 'suora', 'sorella', 'madre', 'beata', 'contessa', 'regina', 'principessa', 'duchessa', 'marchesa', 'imperatrice', 'badessa', 'baronessa', 'granduchessa', 'madame', 'lady', 'donna', 'dama', 'nobildonna', 'signora'}
MALE_TITLES = {'san', 'santo', 'don', 'fra', 'frate', 'padre', 'beato', 'conte', 're', 'principe', 'duca', 'marchese', 'imperatore', 'papa', 'cardinale', 'vescovo', 'monsignor', 'monsignore', 'arcivescovo', 'abate', 'generale', 'colonnello',
               'capitano', 'tenente', 'maresciallo', 'ammiraglio', 'dottor', 'dottore', 'professor', 'professore', 'prof', 'ingegner', 'ingegnere', 'ing', 'avvocato', 'avv', 'maestro', 'cavaliere', 'cav', 'senatore', 'barone', 'sir', 'mons', 'magg', 'maggiore',
               'sergente', 'ministro', 'mastro', 'commendator', 'commendatore', 'sindaco', 'onorevole', 'dott', 'rag', 'geom', 'signor', 'servo', 'venerabile'}
SAINT_TITLES = {'san', 'santa', 'santo', 'sant', 'santi', 'sante'}
RELIGIOUS_DESC = re.compile(r"sant[ao]\b|santi|martire|beat[ao]|venerabil|vescov|monac|abate|abbadess|religios|eremit|papa|apostol|evangelist|profeta|mistic|fondatrice|fondatore|cristian|taumaturg|patrono|patrona|confessore|padre della chiesa", re.I)
GROUP_BROTHERS = re.compile(r"^(fratelli|f\.lli|f\.lli|fratello)\s+", re.I)
GROUP_SISTERS = re.compile(r"^(sorelle)\s+", re.I)
GROUP_COUPLE = re.compile(r"^(coniugi|famiglia|famiglie|sposi|fratelli e sorelle|fratelli e sorelle)\s+", re.I)
COLLECTIVE = re.compile(r"^(caduti|martiri|volontari|alpini|bersaglieri|eroi|partigiani|deportati|combattenti|lavoratori|vittime|cinque giornate|mille|legionari|carabinieri|giusti|fondatori|pionieri|marinai|internati|donatori|donne|ragazzi|bambini|soldati|aviatori|reduci|tre|due|quattro|cinque|sette|dieci|dodici|ventiquattro|quartieri|società|societ.|associazione|giardini|giardino|parco|campi|campo|cascina|ponti|ponte|monte|monti|colle|valle|val|lago|isola|isole|fiume|porta|ripa|foro|borgo|cimitero|circonvallazione|area|zona|rotatoria)\b", re.I)
PLACE = {'Q747074', 'Q515', 'Q486972', 'Q8502', 'Q23442', 'Q4022', 'Q3957', 'Q532', 'Q6256', 'Q35657', 'Q82794', 'Q1549591', 'Q15284', 'Q1620908', 'Q54050', 'Q23397', 'Q34763', 'Q123705', 'Q5084', 'Q3024240', 'Q7275', 'Q10864048', 'Q1048835', 'Q41176', 'Q16970', 'Q1007870', 'Q2221906', 'Q56061', 'Q1763214', 'Q27666946', 'Q1637706', 'Q192287', 'Q22698', 'Q570116', 'Q39816', 'Q4421', 'Q46831', 'Q355304', 'Q13221722', 'Q20019530', 'Q1115575', 'Q484170', 'Q161910', 'Q1229765', 'Q6465', 'Q1799794', 'Q2065736', 'Q1093829', 'Q1006733', 'Q15642541', 'Q83405'}
EVENT = {'Q178561', 'Q198', 'Q13418847', 'Q1656682', 'Q1190554', 'Q350604', 'Q645883', 'Q40231', 'Q8065', 'Q3839081', 'Q273120', 'Q11514315', 'Q1478437', 'Q124734', 'Q625298', 'Q2627975', 'Q1138496'}
MONTHS = r"\b(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\b"


MALE_NAMES |= set("lodovico ercole elio siro annibale giancarlo giosia geremia lionello bernardino demetrio lanfranco tommaso alessio amilcare ferruccio gianni gian bortolo battista abramo achille ambrogio aristide eugenio edmondo ennio erminio ezio fausto fiorenzo gabriello gino giordano giuliano ildebrando ivo livio lucilio maffeo marcello mariano melchiorre mino nello nino olindo onorio oddone ottaviano pacifico pietrino prospero quirino remo renzo rolando rosolino sabino saturnino settimio silverio tarcisio teobaldo tommaso torquato vasco vezio vinicio virginio vitaliano wladimiro zefferino".split())
_wd = {}
for _e in list(ents.values()):
    if 'Q5' in _e['p31'] and _e['sex'] and _e['sex'][0] in SEXQ:
        _t = fold(_e['label_it'] or _e['label_en'])
        if _t:
            _wd.setdefault(_t[0], [0, 0])[0 if SEXQ[_e['sex'][0]] == 'donna' else 1] += 1
WD_SEX = {t: ('donna' if f >= 3 and m == 0 else 'uomo') for t, (f, m) in _wd.items() if (f >= 3 and m == 0) or (m >= 3 and f == 0)}


def given_sex(tok):
    """sesso del nome di battesimo: elenchi scritti a mano, poi nomi ricorrenti su Wikidata (mai la desinenza)"""
    if tok in FEM_NAMES:
        return 'donna'
    if tok in MALE_NAMES:
        return 'uomo'
    return WD_SEX.get(tok, '')


def strip_t(tokens):
    t = list(tokens)
    while len(t) > 1 and t[0] in (FEM_TITLES | MALE_TITLES | SAINT_TITLES):
        t = t[1:]
    return t


def italian(e):
    return bool({'Q38', 'Q172579', 'Q165154', 'Q2415901', 'Q4948', 'Q12548', 'Q15103'} & set(e['cit'])) or 'ital' in e['desc'].lower() or 'milan' in e['desc'].lower()


def sexof(e):
    return SEXQ.get(e['sex'][0], 'altro') if e['sex'] else 'non indicato'


def classify_untagged(r, ks):
    """restituisce un dizionario con categoria/confidenza/ecc. per una strada senza tag"""
    k0 = ks[0]
    nk_full = fold(ks[1] if len(ks) > 1 else k0)
    nk0 = fold(k0)
    first = nk0[0] if nk0 else ''
    res = dict(categoria='sconosciuto', confidenza='nessuno', fonte='', motivo='nessun candidato', santa=0, santo=0, gruppo=0, ambigua=0,
               cands=[], qid='', persona='', nascita='', morte='', desc='', occ='')
    title = first if (first in FEM_TITLES | MALE_TITLES | SAINT_TITLES) else ''
    # sant' (Sant'Agnese): fold gives 'sant'
    exp = ''  # sesso atteso dal titolo
    if title in FEM_TITLES or title == 'santa':
        exp = 'donna'
    elif title in MALE_TITLES or title in ('san', 'santo'):
        exp = 'uomo'
    elif title == 'sant' and len(nk0) > 1:
        g = given_sex(nk0[1])
        exp = g or ''
    is_saint = title in SAINT_TITLES
    # gruppi e collettivi
    if GROUP_SISTERS.match(k0):
        res.update(categoria='donna', confidenza='sicuro', fonte='gruppo', motivo='"Sorelle ...": gruppo di donne', gruppo=1)
        return res
    if GROUP_BROTHERS.match(k0) or re.search(r"\bfratelli\b", k0, re.I):
        res.update(categoria='misto', confidenza='sicuro', fonte='gruppo', motivo='"Fratelli ...": gruppo (di soli uomini o misto, non contato come donne)', gruppo=1)
        return res
    if GROUP_COUPLE.match(k0):
        res.update(categoria='misto', confidenza='sicuro', fonte='gruppo', motivo='coniugi/famiglia: misto', gruppo=1)
        return res
    if re.search(r"\d", k0) or re.search(MONTHS, k0, re.I):
        res.update(categoria='non_persona', confidenza='nessuno', fonte='nome', motivo='numero o mese nel nome: data/evento')
        return res
    # coppie "Nome e Nome Cognome"
    m = re.match(r"^([A-Za-zÀ-ÿ']+) e ([A-Za-zÀ-ÿ']+) (.+)$", k0)
    if m:
        s1, s2 = given_sex(fold(m.group(1))[0]), given_sex(fold(m.group(2))[0])
        if s1 and s2:
            cat = 'misto' if s1 != s2 else ('donna' if s1 == 'donna' else 'uomo')
            res.update(categoria=cat, confidenza='sicuro' if cat == 'misto' else 'incerto', fonte='gruppo' if cat == 'misto' else 'nome',
                       motivo=f'coppia "Nome e Nome Cognome" ({s1}/{s2}) dedotta dai nomi di battesimo', gruppo=1)
            return res
    if COLLECTIVE.match(k0) and not is_saint:
        res.update(categoria='non_persona', confidenza='nessuno', fonte='nome', motivo='parola chiave non personale (collettivo, luogo)')
        return res
    if first in ('santissima', 'santissimo', 'madonna', 'sacro', 'sacra'):
        res.update(categoria='non_persona', confidenza='nessuno', fonte='nome', motivo='concetto religioso')
        return res
    # candidati Wikidata
    cands = []
    seen = set()
    for k in ks:
        for x in search.get(k, []) or []:
            if x['id'] in seen:
                continue
            e = ents.get(x['id'])
            if not e:
                continue
            seen.add(x['id'])
            labs = [fold(e['label_it']), fold(e['label_en']), fold(x['match'])]
            labs = [l for l in labs if l]
            keyset = [sorted(nk0), sorted(nk_full)]
            e1 = any(sorted(l) in keyset for l in labs)
            stripk = sorted(strip_t(nk_full))
            e2 = (not e1) and any(sorted(strip_t(l)) == stripk for l in labs) and len(stripk) >= 1
            nkset = set(strip_t(nk_full))
            part = (not e1 and not e2) and bool(e['p31']) and any(nkset <= set(l) and len(l) <= len(nkset) + 3 for l in labs) and len(nkset) >= 2
            cands.append(dict(id=x['id'], e=e, e1=e1, e2=e2, part=part, human='Q5' in e['p31'], sex=sexof(e)))
    # filtro sul sesso atteso dal titolo
    def okx(c):
        return (not exp) or c['sex'] in (exp, 'non indicato') or not c['human']
    hum = [c for c in cands if c['human'] and okx(c)]
    E1 = [c for c in hum if c['e1']]
    E2 = [c for c in hum if c['e2']]
    if is_saint:  # per i santi il candidato deve avere una descrizione religiosa
        E2 = [c for c in E2 if RELIGIOUS_DESC.search(c['e']['desc'])]
        E1 = [c for c in E1 if RELIGIOUS_DESC.search(c['e']['desc'])]
    E = E1 or E2
    if exp and any(c['sex'] == exp for c in E):
        E = [c for c in E if c['sex'] == exp]
    P = sorted([c for c in hum if c['part'] and c['e']['sitelinks'] >= 8 and (not is_saint or RELIGIOUS_DESC.search(c['e']['desc']))], key=lambda c: -c['e']['sitelinks'])
    nonh = [c for c in cands if not c['human'] and (c['e1'] or c['e2'])]
    nwords = len(strip_t(nk_full))
    res['cands'] = (E or P)[:4]
    if is_saint:
        res['santa' if exp == 'donna' else 'santo'] = 1
    chosen = []
    single_place = (nwords == 1 and not title and not is_saint and nonh and given_sex(strip_t(nk_full)[0]) != 'donna' and not any(c['e']['sitelinks'] >= 25 for c in E))
    if single_place:
        E, P = [], []
    if len(E) == 1 and (nwords >= 2 or title or given_sex(nk_full[0]) == 'donna'):
        chosen = E
        c = E[0]
        conf, why = 'sicuro', 'un solo umano con etichetta/alias identico al nome' + (' (titolo tolto)' if c['e2'] else '')
        if not italian(c['e']) and not c['e']['cit'] and nwords < 3 and not is_saint:
            conf, why = 'incerto', 'un solo umano con nome identico, ma senza legame evidente con l Italia'
        if nonh and nwords == 1 and not title:
            conf, why = 'incerto', why + "; esiste anche un'entita non umana con lo stesso nome (luogo o altro)"
        res.update(categoria='persona', confidenza=conf, fonte='wikidata', motivo=why)
    elif len(E) > 1:
        s = sorted(E, key=lambda c: -c['e']['sitelinks'])
        chosen = s[:3]
        sexes = {c['sex'] for c in E}
        if nwords >= 2 and s[0]['e']['sitelinks'] >= 15 and s[0]['e']['sitelinks'] >= 4 * max(1, s[1]['e']['sitelinks']) and italian(s[0]['e']):
            res.update(categoria='persona', confidenza='sicuro', fonte='wikidata', motivo='omonimi: prevale nettamente il piu famoso e legato all Italia')
        elif exp and len(sexes) == 1 and (is_saint or title in FEM_TITLES | MALE_TITLES):
            res.update(categoria='persona', confidenza='sicuro', fonte='wikidata+titolo', ambigua=1,
                       motivo=f'{len(E)} persone omonime, tutte {exp}: il sesso e certo (titolo), la persona precisa no')
        else:
            res.update(categoria='persona', confidenza='incerto', fonte='wikidata', motivo=f'{len(E)} umani con lo stesso nome: scegliere a mano')
    elif P:
        chosen = P[:3]
        res.update(categoria='persona', confidenza='incerto', fonte='wikidata', motivo='nessuna corrispondenza esatta: nome parziale o titolo (candidati in ordine di notorieta)')
    elif nonh and not is_saint:
        c0 = nonh[0]
        if set(c0['e']['p31']) & EVENT:
            res.update(categoria='non_persona', fonte='wikidata', motivo='corrisponde a un evento su Wikidata')
        elif set(c0['e']['p31']) & PLACE:
            res.update(categoria='non_persona', fonte='wikidata', motivo='corrisponde a un luogo su Wikidata')
        else:
            res.update(categoria='non_persona', fonte='wikidata', motivo="corrisponde a un'entita non umana su Wikidata: " + (c0['e']['desc'] or c0['e']['label_it'])[:60])
        chosen = []
    if chosen:
        c = chosen[0]
        e = c['e']
        res.update(qid=';'.join(x['id'] for x in chosen), persona=' | '.join(x['e']['label_it'] or x['e']['label_en'] for x in chosen),
                   nascita=e['birth'], morte=e['death'], desc=' | '.join(x['e']['desc'][:80] for x in chosen))
        res['sesso_c'] = c['sex']
        res['occ_q'] = ';'.join(e['occ'])
        res['cands'] = chosen
        if res['categoria'] == 'persona':
            sx = c['sex']
            if exp and sx in ('non indicato', 'altro'):
                sx = exp
            elif sx in ('non indicato', 'altro'):
                g = given_sex(strip_t(nk_full)[0]) if strip_t(nk_full) else ''
                if g:
                    sx = g
                    res['confidenza'] = 'incerto'
                    res['motivo'] += '; Wikidata non indica il sesso: dedotto dal nome di battesimo'
            res['categoria'] = {'donna': 'donna', 'uomo': 'uomo'}.get(sx, 'sconosciuto')
            if is_saint and not res['santa'] and not res['santo']:
                res['santa' if sx == 'donna' else 'santo'] = 1
        return res
    if res['categoria'] == 'non_persona':
        return res
    # nessun candidato Wikidata: titoli e nomi di battesimo
    if is_saint:
        sx = exp or (given_sex(nk0[1]) if len(nk0) > 1 else '')
        if sx:
            note = 'santo/a dedotto dal titolo, nessuna persona trovata su Wikidata: potrebbe essere la chiesa'
            if re.match(r"^(santa maria|sant'?\s*maria)", k0, re.I) or fold(k0)[:2] == ['santa', 'maria']:
                note = 'Santa Maria + qualificativo: quasi certamente una chiesa o un luogo di culto'
            res.update(categoria=sx, confidenza='incerto', fonte='titolo', motivo=note)
            res['santa' if sx == 'donna' else 'santo'] = 1
            return res
    if title in FEM_TITLES and len(strip_t(nk_full)) >= 1:
        res.update(categoria='donna', confidenza='incerto', fonte='titolo', motivo=f'titolo femminile ({title}) senza corrispondenza su Wikidata')
        return res
    if title in MALE_TITLES and len(strip_t(nk_full)) >= 1:
        res.update(categoria='uomo', confidenza='incerto', fonte='titolo', motivo=f'titolo maschile ({title}) senza corrispondenza su Wikidata')
        return res
    toks = strip_t(nk_full)
    if len(toks) >= 2:
        g = given_sex(toks[0])
        if g:
            res.update(categoria=g, confidenza='incerto', fonte='nome', motivo=f'nome di battesimo "{toks[0]}" ({g}) + cognome, senza corrispondenza su Wikidata')
            return res
    elif len(toks) == 1 and given_sex(toks[0]) == 'donna' and not nonh:
        res.update(categoria='donna', confidenza='incerto', fonte='nome', motivo='una sola parola, che e un nome femminile: persona o altro?')
        return res
    return res


# ---------------- tag OSM ----------------
units = m10.effective_units(units_csv, agg_csv)
units['nome'] = units.apply(lambda r: (r.tipo + ' ' + r.descrittivo).strip() if r.origine == 'comune' else r.descrittivo, axis=1)


def classify_tag(qids):
    qs = [q for q in qids.split(';') if q]
    hum = [q for q in qs if q in etim.index and etim.loc[q, 'umano'] == '1']
    if not hum:
        return None
    sexes = set()
    for q in hum:
        s = etim.loc[q, 'sesso']
        sexes.add(s if s in ('donna', 'uomo') else 'altro')
    cat = list(sexes)[0] if len(sexes) == 1 and list(sexes)[0] in ('donna', 'uomo') else 'misto'
    q0 = hum[0]
    row = etim.loc[q0]
    return dict(categoria=cat, confidenza='sicuro', fonte='tag_osm', hum=hum, motivo='tag name:etymology:wikidata OSM' + (f' ({len(hum)} persone)' if len(hum) > 1 else ''),
                qid=';'.join(hum), persona=' | '.join(etim.loc[q, 'label'] for q in hum), nascita=row.anno_nascita, morte=row.anno_morte,
                desc=row.descrizione[:80], occ=row.professioni_it.replace('|', ', '), gruppo=int(len(hum) > 1), santa=0, santo=0, ambigua=0, cands=[])


out = []
for r in units.itertuples():
    d = None
    saintname = bool(re.match(r"^(san|santa|santo|sant'|santi|sante)\b", r.descrittivo.strip(), re.I)) and not re.match(r"^sant(ander|a lucia)", r.descrittivo, re.I)
    if r.qids_eff:
        d = classify_tag(r.qids_eff)
        if d is None:
            # tag verso non-persona: se e un nome di santo, rivalutarlo con il titolo; altrimenti non persona
            if saintname:
                d = None
            else:
                d = dict(categoria='non_persona', confidenza='sicuro', fonte='tag_osm', motivo='tag OSM verso luogo/oggetto (non persona)', qid=r.qids_eff, persona='', nascita='', morte='', desc='', occ='', gruppo=0, santa=0, santo=0, ambigua=0, cands=[])
        else:
            if d['categoria'] in ('donna', 'uomo') and saintname:
                d['santa' if d['categoria'] == 'donna' else 'santo'] = 1
            # coerenza: almeno una parola del nome della via deve comparire nel nome della persona
            st = m10.core_tokens(r.descrittivo) | {w for w in fold(r.descrittivo) if w not in m10.STOPW and w not in m10.TYPEW}
            pt = set()
            for q in d['hum']:
                pt |= set(fold(etim.loc[q, 'label'])) | set(fold(etim.loc[q, 'descrizione']))
            import difflib
            if not any(a == b or (len(a) >= 4 and len(b) >= 4 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.8) for a in st for b in pt):
                d['confidenza'] = 'incerto'
                d['motivo'] = 'tag OSM verso una persona il cui nome non compare nel nome della via: da controllare'
    if d is None:
        d = classify_untagged(r, keymap.get(r.uid) or [r.descrittivo])
        d['fonte_tag'] = 'senza_tag'
    d.update(uid=r.uid, codice_via=r.codice_via, nome=r.nome, origine=r.origine, tipo=r.tipo, data_intitolazione=r.data_intitolazione, nome_osm=r.nome_osm_scelto, haTag=int(bool(r.qids_eff)))
    out.append(d)

rows = []
for d in out:
    cl = d.get('cands') or []
    cand_txt = ' || '.join(f"{c['id']}|{c['e']['label_it'] or c['e']['label_en']}|{c['sex']}|{c['e']['birth']}-{c['e']['death']}|{c['e']['desc'][:70]}" for c in cl)
    rows.append(dict(uid=d['uid'], codice_via=d['codice_via'], nome=d['nome'], origine=d['origine'], tipo=d['tipo'], nome_osm=d['nome_osm'], ha_tag=d['haTag'],
                     categoria=d['categoria'], confidenza=d['confidenza'], fonte=d['fonte'], motivo=d['motivo'], santa=d['santa'], santo=d['santo'], gruppo=d['gruppo'], persona_ambigua=d['ambigua'],
                     qid=d.get('qid', ''), persona=d.get('persona', ''), nascita=d.get('nascita', ''), morte=d.get('morte', ''), descrizione=d.get('desc', ''), professioni=d.get('occ', ''),
                     occupazioni_qid=d.get('occ_q', ''), data_intitolazione=d['data_intitolazione'], candidati=cand_txt))
df = pd.DataFrame(rows)
os.makedirs(outdir, exist_ok=True)
df.to_csv(f"{outdir}/strade_classificate_v2.csv", index=False, encoding='utf-8-sig')
mc = df[df.ha_tag == 0].copy()
mc.to_csv(f"{outdir}/matching_candidati_v2.csv", index=False, encoding='utf-8-sig')
dv = df[(df.confidenza == 'incerto') & (df.categoria == 'donna')].copy()
dv['wikidata'] = dv.qid.apply(lambda s: ' '.join('https://www.wikidata.org/wiki/' + q for q in s.split(';') if q))
dv['tua_decisione (donna / non donna / altro)'] = ''
dv[['nome', 'codice_via', 'motivo', 'santa', 'persona', 'qid', 'nascita', 'morte', 'descrizione', 'candidati', 'wikidata', 'data_intitolazione', 'tua_decisione (donna / non donna / altro)']].to_csv(f"{outdir}/da_verificare_donne.csv", index=False, encoding='utf-8-sig')
print(len(df), 'strade')
print(df.groupby(['categoria', 'confidenza']).size())
print('da verificare (incerto, donna):', len(dv))
