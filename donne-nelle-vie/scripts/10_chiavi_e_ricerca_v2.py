"""Fase 2, passo 1. Costruisce le chiavi di ricerca (con e senza titoli) per le strade senza tag e
rifa' le ricerche Wikidata. TRAPPOLA: nel primo giro 737 ricerche su 3.047 erano vuote perche' l'API rispondeva
'cirrussearch-too-busy-error' (HTTP 200!) e lo script lo contava come 'nessun risultato'. Qui l'errore viene riconosciuto e ritentato.
Uso: python -I 10_chiavi_e_ricerca_v2.py strade_unite.csv old_search_dir new_dir"""
import sys, json, re, time, os, requests, pandas as pd

UA = {"User-Agent": "milano-in-dati/0.2 (davide.caniatti@gmail.com; street-name research, polite)"}
API = "https://www.wikidata.org/w/api.php"
TYPE = r"^(via privata|via|viale|piazzale|piazza|piazzetta|largo|corso|vicolo|galleria|passaggio|bastioni|cavalcavia|strada|parco|giardino|alzaia|foro|sottopasso|sito|vicoletto|ripa|rampa|sottopassaggio|stradone|strada vicinale|passerella|passeggiata|rotatoria|sopraelevata|ponte)\s+"
ART = r"^(?:(?:dell'|dall'|nell'|all'|d'|l')|(?:del|della|dello|dei|degli|delle|di|de|dal|dalla|dai|dagli|al|alla|alle|ai|agli|la|le|lo|il|i|gli)\s+)"
TITLES = ["santissima", "santissimo", "santa", "santo", "santi", "sante", "sant'", "san", "madre", "suor", "suora", "sorella", "don", "fra", "frate", "padre", "beata", "beato", "contessa", "conte", "regina", "re", "principessa", "principe",
          "duchessa", "duca", "marchesa", "marchese", "imperatrice", "imperatore", "papa", "cardinale", "vescovo", "monsignor", "monsignore", "arcivescovo", "abate", "badessa", "generale", "colonnello", "capitano", "tenente", "maresciallo", "ammiraglio",
          "dottor", "dottore", "professor", "professore", "prof", "ingegner", "ingegnere", "ing", "avvocato", "avv", "maestro", "cavaliere", "cav", "senatore", "onorevole", "sindaco", "commendator", "commendatore", "barone", "baronessa", "granduchessa", "madame", "lady", "sir", "mons", "martire", "venerabile", "servo", "serva", "dott", "rag", "geom", "magg", "maggiore", "sergente", "ministro", "mastro", "dama", "donna", "nobildonna", "signora", "signor"]
TITLES = sorted(set(TITLES), key=lambda t: -len(t))
TITLE_RE = re.compile(r"^(" + '|'.join(re.escape(x) for x in TITLES) + r")(?:\s+|(?<=')(?=\S))", re.I)


def fix_apos(s):
    s = s.replace('�', '').replace('’', "'")
    acc = {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù', 'A': 'À', 'E': 'È', 'I': 'Ì', 'O': 'Ò', 'U': 'Ù'}
    return re.sub(r"([AEIOUaeiou])'(?![A-Za-z])", lambda m: acc[m.group(1)], s)


def tc(s):
    if s.isupper() or s.islower():
        small = ('di', 'de', 'del', 'della', 'dei', 'da', 'e', 'd', 'dal', 'dalla', 'delle', 'degli', 'dello')
        s = ' '.join(w if w.lower() in small else w.capitalize() for w in s.lower().split())
        s = re.sub(r"\b([DdLl])'(\w)", lambda m: m.group(1).lower() + "'" + m.group(2).upper(), s)
        s = re.sub(r"\b(Sant|Dell|Dall|Nell|All)'(\w)", lambda m: m.group(1) + "'" + m.group(2).upper(), s)
    return s


def base_name(r):
    s = r.descrittivo if r.origine == 'comune' else re.sub(TYPE, '', r.descrittivo, flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"^\s*(via|viale|piazza|largo|vicolo)\s+(?=(san|santa|sant'|fra|don|madre|suor|regina)\b)", "", s, flags=re.I)
    return re.sub(r"\s+", " ", fix_apos(s)).strip()


def strip_art(s):
    return re.sub(ART, '', s, flags=re.I).strip() or s


def strip_titles(s):
    t = s
    for _ in range(3):
        m = TITLE_RE.match(t)
        if not m:
            break
        rest = t[m.end():].strip()
        if not rest:
            break
        t = rest
    return t


def keys_for(r):
    b = tc(base_name(r))
    ks = [b, tc(strip_art(base_name(r)))]
    ks.append(strip_titles(ks[1]))
    out = []
    for k in ks:
        k = k.strip()
        if k and k not in out:
            out.append(k)
    return out


TYPEW = {'via', 'viale', 'piazza', 'piazzale', 'piazzetta', 'largo', 'corso', 'vicolo', 'galleria', 'passaggio', 'bastioni', 'strada', 'privata', 'alzaia', 'foro', 'ripa', 'rampa', 'passerella', 'passeggiata', 'rotatoria', 'sopraelevata', 'ponte', 'cavalcavia', 'sottopasso', 'parco', 'giardino', 'giardini', 'vicinale', 'stradone', 'vicoletto'}
STOPW = {'di', 'del', 'della', 'dello', 'dei', 'degli', 'delle', 'de', 'd', 'dell', 'da', 'dal', 'dalla', 'e', 'la', 'le', 'lo', 'il', 'l', 'i', 'gli', 'al', 'alla', 'all'}


def core_tokens(s):
    import unicodedata
    s = re.sub(r"\(.*?\)", " ", s)
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    t = re.sub(r"[^a-z0-9 ]", " ", s.replace("'", " ")).split()
    ROM = {'i': 'primo', 'ii': 'secondo', 'iii': 'terzo', 'iv': 'quarto', 'v': 'quinto', 'vi': 'sesto', 'vii': 'settimo', 'viii': 'ottavo', 'ix': 'nono', 'x': 'decimo',
           'xi': 'undicesimo', 'xii': 'dodicesimo', 'xiii': 'tredicesimo', 'xiv': 'quattordicesimo', 'xv': 'quindicesimo', 'xxiii': 'ventitreesimo'}
    return {ROM.get(w, w) for w in t if w not in TYPEW and w not in STOPW}


def pick_names(r, names):
    """TRAPPOLA fase 2: il codice loc_ref raggruppa piu nomi OSM (es. 'Via Fezzan' e 'Viale Caterina da Forli' hanno lo stesso
    CODICE_VIA): le etimologie vanno prese solo dal nome OSM che corrisponde al nome del Comune."""
    if r.origine != 'comune' or len(names) <= 1:
        return names
    tgt = core_tokens(r.descrittivo)
    sc = []
    for n in names:
        t = core_tokens(n)
        if not t or not tgt:
            sc.append((0, n)); continue
        j = len(t & tgt) / len(t | tgt)
        small, big = (t, tgt) if len(t) <= len(tgt) else (tgt, t)
        if small <= big and len(small) >= 2 and len(big) - len(small) <= 1:
            j = max(j, 0.8)
        sc.append((j, n))
    best = max(x[0] for x in sc)
    if best < 0.6:
        return []
    return [n for j, n in sc if j >= 0.6 and j >= best - 0.15]


def effective_units(units_csv, agg_csv):
    """tabella delle strade 'core' con i nomi OSM scelti e le etimologie del solo nome giusto"""
    df = pd.read_csv(units_csv, dtype=str).fillna('')
    agg = pd.read_csv(agg_csv, dtype=str).fillna('').set_index('name')
    core_hw = ('residential', 'tertiary', 'secondary', 'primary', 'unclassified', 'living_street', 'pedestrian', 'place=square', 'trunk')
    df['core'] = df.apply(lambda r: r.origine == 'comune' or r.highway_osm.split(':')[0] in core_hw, axis=1)
    df = df[df.core].copy()
    df['uid'] = df.apply(lambda r: r.codice_via if r.origine == 'comune' else 'osm:' + r.descrittivo, axis=1)
    sel, qs, changed = [], [], []
    for r in df.itertuples():
        names = [n.strip() for n in r.nome_osm.split(' | ') if n.strip()]
        ch = pick_names(r, names)
        q = set()
        for n in ch:
            if n in agg.index:
                q |= {x for x in re.split(r"\s*;\s*", agg.loc[n, 'etymology_wikidata']) if x}
        sel.append(' | '.join(ch)); qs.append(';'.join(sorted(q, key=lambda x: int(x[1:]))))
        changed.append(int(set(x for x in r.qids_osm.split(';') if x) != q))
    df['nome_osm_scelto'] = sel
    df['qids_eff'] = qs
    df['tag_cambiato'] = changed
    # TRAPPOLA: una via del Comune senza nome OSM agganciato (tipo diverso: 'Galleria' vs 'Via') ricompare come riga 'solo_osm' => doppio conteggio.
    # Qui la riga solo_osm con le stesse parole significative viene fusa nella riga del Comune.
    vuote = {}
    for i, r in df[(df.origine == 'comune') & (df.nome_osm_scelto == '')].iterrows():
        vuote.setdefault(frozenset(core_tokens(r.descrittivo)), []).append(i)
    drop = []
    for i, r in df[df.origine == 'solo_osm'].iterrows():
        k = frozenset(core_tokens(r.descrittivo))
        if k and k in vuote:
            j = vuote[k][0]
            df.at[j, 'nome_osm_scelto'] = r.descrittivo
            if r.descrittivo in agg.index:
                df.at[j, 'qids_eff'] = ';'.join(sorted({x for x in re.split(r"\s*;\s*", agg.loc[r.descrittivo, 'etymology_wikidata']) if x}, key=lambda x: int(x[1:])))
            drop.append(i)
    df = df.drop(index=drop)
    print('righe solo_osm fuse con una via del Comune:', len(drop), flush=True)
    return df


def main(units_csv, old_dir, outdir, agg_csv):
    os.makedirs(outdir, exist_ok=True)
    df = effective_units(units_csv, agg_csv)
    print('strade con tag diverso dopo la scelta del nome OSM:', int(df.tag_cambiato.sum()), flush=True)
    todo = df[df.qids_eff == ''].copy()
    todo['unit_id'] = todo['uid']
    keymap = {r.unit_id: keys_for(r) for r in todo.itertuples()}
    json.dump(keymap, open(f"{outdir}/chiavi_per_strada.json", 'w', encoding='utf8'), ensure_ascii=False, indent=0)
    queries = sorted({k for ks in keymap.values() for k in ks})
    print(len(todo), 'strade senza tag;', len(queries), 'chiavi distinte', flush=True)
    sfile = f"{outdir}/search_results.json"
    search = json.load(open(sfile, encoding='utf8')) if os.path.exists(sfile) else {}
    if not search:  # riuso dei risultati VALIDI (non vuoti) del primo giro
        old = json.load(open(f"{old_dir}/search_results.json", encoding='utf8'))
        for k, v in old.items():
            if v:
                search[k.title() if k.isupper() else k] = v
        print('riusati dal primo giro:', len(search), flush=True)

    def get(params):
        for a in range(8):
            try:
                r = requests.get(API, params=params, headers=UA, timeout=60)
                if r.status_code == 200:
                    j = r.json()
                    if 'error' in j:
                        w = min(90, 6 * 2 ** a)
                        print('errore API', j['error'].get('code'), '-> attesa', w, flush=True)
                        time.sleep(w)
                        continue
                    return j
                print('status', r.status_code, flush=True)
            except Exception as e:
                print('err', e, flush=True)
            time.sleep(15 * (a + 1))
        return None

    n = 0
    for k in queries:
        if k in search:
            continue
        j = get(dict(action='wbsearchentities', search=k, language='it', uselang='it', limit=8, type='item', format='json'))
        if j is None:
            print('FALLITA', k, flush=True)
            continue
        search[k] = [dict(id=x['id'], label=x.get('label', ''), desc=x.get('description', ''), match=x.get('match', {}).get('text', '')) for x in j.get('search', [])]
        n += 1
        time.sleep(0.8)
        if n % 150 == 0:
            json.dump(search, open(sfile, 'w', encoding='utf8'), ensure_ascii=False)
            print('ricerche', n, 'ultima:', k, flush=True)
    json.dump(search, open(sfile, 'w', encoding='utf8'), ensure_ascii=False)
    print('ricerche nuove:', n, '| totali', len(search), '| vuote', sum(1 for v in search.values() if not v), flush=True)
    efile = f"{outdir}/entities.json"
    ents = json.load(open(efile, encoding='utf8')) if os.path.exists(efile) else json.load(open(f"{old_dir}/entities.json", encoding='utf8'))
    ids = sorted({x['id'] for v in search.values() for x in v}, key=lambda q: int(q[1:]))
    need = [q for q in ids if q not in ents]
    print(len(ids), 'candidati;', len(need), 'da scaricare', flush=True)

    def yr(claims, p):
        for c in claims.get(p, []):
            try:
                t = c['mainsnak']['datavalue']['value']['time']
                return int(t[:5].replace('+', '')) if t[0] == '+' else -int(t[1:5])
            except Exception:
                pass
        return ''

    def qs(claims, p):
        out = []
        for c in claims.get(p, []):
            try:
                out.append(c['mainsnak']['datavalue']['value']['id'])
            except Exception:
                pass
        return out

    for i in range(0, len(need), 50):
        j = get(dict(action='wbgetentities', ids='|'.join(need[i:i + 50]), props='claims|labels|descriptions|sitelinks', languages='it|en', format='json'))
        for q, e in (j or {}).get('entities', {}).items():
            cl = e.get('claims', {})
            ents[q] = dict(label_it=e.get('labels', {}).get('it', {}).get('value', ''), label_en=e.get('labels', {}).get('en', {}).get('value', ''),
                           desc=(e.get('descriptions', {}).get('it') or e.get('descriptions', {}).get('en') or {}).get('value', ''),
                           p31=qs(cl, 'P31'), sex=qs(cl, 'P21'), occ=qs(cl, 'P106'), cit=qs(cl, 'P27'), birth=yr(cl, 'P569'), death=yr(cl, 'P570'),
                           sitelinks=len(e.get('sitelinks', {})))
        time.sleep(0.7)
        if (i // 50) % 10 == 0:
            json.dump(ents, open(efile, 'w', encoding='utf8'), ensure_ascii=False)
            print('ents', i, len(need), flush=True)
    json.dump(ents, open(efile, 'w', encoding='utf8'), ensure_ascii=False)
    print('FINITO', flush=True)


if __name__ == '__main__':
    main(*sys.argv[1:5])
