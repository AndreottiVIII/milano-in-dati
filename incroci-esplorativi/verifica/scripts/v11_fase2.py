"""Fase 2: prove mirate sulle righe sospette di 01_tabella_nil.py, robusta.py, 07_approfondimenti_nil.py.
Rifà i singoli passaggi con le stesse righe, senza scrivere fuori da verifica/ e senza leggere incroci-esplorativi/out."""
import sys, os, json, re, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 230); pd.set_option('display.max_columns', 40); pd.set_option('display.max_rows', 200); pd.set_option('display.max_colwidth', 60)
L = open(os.path.join(OUT, 'fase2.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
def rd(rel, **kw):
    pth = p(*rel.split('/'))
    head = open(pth, encoding='utf-8-sig', errors='replace').readline()
    sep = ';' if head.count(';') > head.count(',') else ','
    d = pd.read_csv(pth, sep=sep, encoding='utf-8-sig', low_memory=False, **kw)
    d.columns = [c.strip().lstrip('﻿') for c in d.columns]
    if sep == ';':
        for c in d.columns:
            if pd.api.types.is_string_dtype(d[c]) or d[c].dtype == object:
                s = d[c].fillna('').astype(str).str.strip()
                if s.str.fullmatch(r'-?\d+,\d+|-?\d+|nan|<NA>|').mean() > 0.9 and s.str.contains(',').any():
                    d[c] = pd.to_numeric(s.str.replace(',', '.'), errors='coerce')
    return d
def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)
g = json.load(open(p('docs', 'quartiere', 'data', 'nil.geojson'), encoding='utf8'))
REF = {f['properties']['i']: f['properties']['n'] for f in g['features']}
say('riferimento NIL', len(REF), list(REF.items())[:3], 'chiavi props', list(g['features'][0]['properties'].keys())[:8])
# --- 1. allineamento codici: id contro nome in ogni file usato
say('\n--- 1. Codici NIL contro nomi')
FILES = [('popolazione/pulito/eta_nil_anno_indicatori.csv', 'id_nil', 'nil'), ('popolazione/pulito/nil_anagrafica.csv', 'id_nil', None), ('censimenti/pulito/indicatori_NIL.csv', 'nil', 'nil_nome'), ('docs/lavoro/data/nil_lavoro.csv', 'nil', 'nil_nome'), ('quartieri-che-cambiano/out/indicatori_nil.csv', 'id_nil', 'nil'), ('speranza-vita/pulito/nil_smr_e0.csv', 'id_nil', 'nil'), ('elezioni/pulito/nil_info.csv', 'nil', 'nome'), ('docs/medici-farmacie/data/nil.csv', 'id_nil', None), ('docs/palazzi/data/nil.csv', 'id_nil', None), ('docs/costruzioni/data/nil.csv', 'id_nil', None), ('docs/case-popolari/data/nil.csv', 'id_nil', 'nil'), ('affitti-brevi/pulito/nil_riepilogo.csv', 'nil', 'nil_nome'), ('affitti-brevi/pulito/crescita_nil.csv', 'nil_id', 'nil_nome'), ('docs/citta-15-minuti/data/nil_punteggi.csv', 'ID_NIL', 'NIL_nome'), ('docs/ristoranti/data/nil.csv', 'id_nil', 'nil'), ('docs/ristoranti/data/pratiche_2019_2026_nil.csv', 'id_nil', None), ('docs/ristoranti/data/nil_cucine.csv', 'id_nil', None), ('docs/sport/data/nil_sport.csv', 'ID_NIL', None), ('docs/terzo-settore/data/nil.csv', 'id_nil', None), ('biblioteche/pulito/nil_biblioteche.csv', 'ID_NIL', None), ('docs/alberi/data/nil.csv', 'id_nil', None), ('docs/verde/data/nil_verde.csv', 'id_nil', 'nome'), ('docs/cani/data/aree_cani_per_nil.csv', 'id_nil', None), ('docs/suolo/data/nil_suolo.csv', 'id_nil', None), ('docs/rigenerazione/data/nil.csv', 'id_nil', None), ('docs/parcheggi/data/nil.csv', 'id_nil', 'nil'), ('docs/antenne/data/nil.csv', 'id_nil', None), ('docs/statue/data/per_nil.csv', 'id_nil', None), ('docs/targhe/data/per_nil.csv', 'id_nil', None), ('docs/pietre-inciampo/data/nil.csv', 'id', None), ('botteghe/pulito/per_nil.csv', 'nil_id', None), ('docs/scuole/data/nil_scuole.csv', 'id_nil', None), ('scuole/pulito/nil_stranieri_2024.csv', 'id_nil', None), ('docs/poverta-educativa/data/milano_nil_poverta_educativa.csv', 'id_nil', 'nil'), ('docs/nascite/data/nil_2022_2024.csv', 'id_nil', 'nil'), ('docs/case-vuote/data/nil.csv', 'id_nil', 'quartiere'), ('popolazione/pulito/flussi_nil_riepilogo.csv', 'id_nil', None), ('divisa/out/reddito_nil_milano.csv', 'id_nil', None), ('luoghi-cercati/pulito/totali_luogo.csv', 'id_nil', 'nil')]
ALIAS = {}
for f, ic, nc in FILES:
    try:
        d = rd(f)
    except Exception as ex:
        say('NON LETTO', f, ex); continue
    if ic not in d.columns:
        say('COLONNA ID ASSENTE', f, list(d.columns)[:10]); continue
    if nc is not None and nc not in d.columns:
        nc = None
    if nc is None:
        cand =[c for c in d.columns if c.lower() in ('nil', 'nome', 'quartiere', 'nil_nome', 'nome_nil', 'nil_nome', 'denominazione')]
        nc = cand[0] if cand else None
    ids = pd.to_numeric(d[ic], errors='coerce')
    ok = ids.dropna().astype(int).unique()
    nuovi = sorted(set(ok) - set(REF))
    if nc:
        t = pd.DataFrame({'i': ids, 'n': d[nc]}).dropna().drop_duplicates()
        t['ref'] = t.i.astype(int).map(REF)
        def simile(a, b):
            a, b = norm(a), norm(b)
            if not a or not b:
                return False
            return a == b or a[:8] == b[:8] or a in b or b in a
        t['ok'] = [simile(a, b) for a, b in zip(t.n, t.ref)]
        bad = t[~t.ok]
        say(f"{f:62s} id {len(ok):3d} fuori {nuovi[:3]} nomi discordi {len(bad)}", bad.head(4)[['i', 'n', 'ref']].values.tolist() if len(bad) else '')
    else:
        say(f'{f:62s} id {len(ok):3d} fuori {nuovi[:3]} (nessun nome nel file)')
# --- 2. flussi: quali periodi
say('\n--- 2. Periodi di flussi_nil_riepilogo (riga 170-176 di 01)')
fl = rd('popolazione/pulito/flussi_nil_riepilogo.csv')
per = sorted(fl.periodo.astype(str).unique()); say(' periodi', per, ' p_old', per[0], ' p_new', per[-1], 'colonne', [c for c in fl.columns if 'saldo' in c][:8])
# --- 3. beni confiscati, riga 298-300
say('\n--- 3. Beni confiscati geojson')
bc = json.load(open(p('docs', 'beni-confiscati', 'data', 'nil.geojson'), encoding='utf8'))
say(' proprietà', list(bc['features'][0]['properties'].items())[:12])
bcs = pd.Series({f['properties'].get('i', f['properties'].get('id')): f['properties'].get('cu') for f in bc['features']})
say(' chiavi tipo', type(list(bcs.index)[0]), 'valori non nulli', bcs.notna().sum(), 'somma', pd.to_numeric(bcs, errors='coerce').sum())
num = pd.to_numeric(bcs, errors='coerce'); num.index = pd.to_numeric(num.index, errors='coerce')
co = pd.read_csv(p('beni-confiscati', 'pulito', 'comune_ds147_milano.csv'), low_memory=False); mine = co.groupby('id_nil').size(); mine.index = mine.index.astype(int)
x = pd.DataFrame({'cu': num, 'mio': mine}).fillna(0); say(' confronto cu vs conteggio ds147: uguali', int((x.cu == x.mio).sum()), 'su', len(x), 'scarto max', (x.cu - x.mio).abs().max())
# nomi in unita_comune (07 riga 218-222)
uc = rd('docs/beni-confiscati/data/unita_comune.csv'); say(' unita_comune', uc.shape, list(uc.columns)[:8])
AN = {i: REF[i] for i in REF}
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv')); r24 = e[e.anno == 2024].set_index('id_nil').residenti
A_ids = [i for i in REF if r24.get(i, 0) >= 3000]
nome2id = {AN[i].lower(): i for i in A_ids}
uc['id'] = uc.quartiere.astype(str).str.lower().map(nome2id)
nm = uc[uc.id.isna()]
say(' unità senza NIL di analisi', len(nm), 'su', len(uc), 'quartieri:', nm.quartiere.value_counts().head(25).to_dict())
tutti = {AN[i].lower(): i for i in AN}
say(' di cui nomi che non esistono nemmeno tra gli 88', nm[~nm.quartiere.astype(str).str.lower().isin(tutti)].quartiere.value_counts().to_dict())
# confronto indirizzi per NIL con la lettura per norm
uc['id2'] = uc.quartiere.map(lambda s: {norm(AN[i]): i for i in AN}.get(norm(s)))
chk = pd.DataFrame({'esatto': uc.groupby('id').indirizzo.nunique(), 'norm': uc[uc.id2.isin(A_ids)].groupby('id2').indirizzo.nunique()}).fillna(0)
say(' NIL con conteggio perso per scrittura diversa:', chk[chk.esatto != chk.norm].to_dict('index'))
# --- 4. NIL di analisi senza voti: le somme diventano 0 (07 righe 41, 123, 177-178; 01 riga 426)
say('\n--- 4. NIL di analisi con meno di 1.000 elettori')
for eid in ELEZ_POL:
    d = json.load(open(p('docs', 'elezioni', 'data', 'nil', eid + '.json'), encoding='utf8'))['p']
    bad = [(i, REF[i], d.get(str(i), {}).get('e')) for i in A_ids if d.get(str(i), {}).get('e', 0) < 1000]
    say(' ', eid, bad)
# --- 5. Iv e Rv di docs/scuole
say('\n--- 5. Colonne scuole')
sc = rd('docs/scuole/data/nil_scuole.csv'); say(sc.head(3).to_string()[:900])
sv = pd.read_csv(p('scuole', 'pulito', 'nil_iscritti_variazione_2015_2024.csv'), sep=';').dropna(subset=['id_nil']); sv['id_nil'] = sv.id_nil.astype(int); gg = sv.groupby('id_nil')[['iscritti_2015', 'iscritti_2024']].sum(); gg['v'] = (gg.iscritti_2024 / gg.iscritti_2015 - 1) * 100
xx = sc.set_index('id_nil').join(gg); say(' Iv contro mio', round(xx[['Iv', 'v']].corr(method='spearman').iloc[0, 1], 4), ' scarto mediano', round((xx.Iv - xx.v).abs().median(), 2))
# --- 6. Colonne numeriche lette come testo
say('\n--- 6. Colonne usate: quanti valori numerici dopo la lettura')
USI = [('docs/case-popolari/data/nil.csv', 'id_nil', ['canone_ALER_2016_per_abitazione_euro']), ('docs/verde/data/nil_verde.csv', 'id_nil', ['m2_ab_A', 'm2_ab_B', 'pct_area_A', 'min_parco_mediana', 'calore_esposizione', 'indice_verde_spotted', 'gioco_n', 'orti_m2']), ('docs/parcheggi/data/nil.csv', 'id_nil', ['STIMA_m2_stalli_per_abitante', 'ciclabili_km', 'aree_pedonali_m2']), ('docs/palazzi/data/nil.csv', 'id_nil', ['quota_prima_del_1946_pct', 'quota_1946_1970_pct', 'quota_dopo_il_1980_pct', 'interni_per_edificio']), ('docs/costruzioni/data/nil.csv', 'id_nil', ['nuove_abitazioni_ogni_1000_abitanti_2024', 'volume_nuovi_fabbricati_m3']), ('docs/medici-farmacie/data/nil.csv', 'id_nil', ['medici_famiglia_ogni_1000_residenti_14_e_piu', 'farmacie_ogni_10000_residenti', 'minuti_a_piedi_farmacia_mediana', 'minuti_a_piedi_ambulatorio_medico_mediana', 'titolari_65_anni_e_piu_solo_se_almeno_10_medici', 'di_cui_titolari']), ('docs/terzo-settore/data/nil.csv', 'id_nil', ['associazioni_registro_comune_per_10000', 'cooperative_sociali_albo_comune_per_10000', 'persone_giuridiche_regione_per_10000']), ('docs/sport/data/nil_sport.csv', 'ID_NIL', ['per10k_tutti', 'per10k_comunali']), ('docs/antenne/data/nil.csv', 'id_nil', ['mobile_per_km2', 'mobile_per_1000_ab']), ('docs/statue/data/per_nil.csv', 'id_nil', ['opere_per_kmq', 'murali']), ('docs/targhe/data/per_nil.csv', 'id_nil', ['targhe', 'targhe_resistenza']), ('docs/pietre-inciampo/data/nil.csv', 'id', ['per10mila', 'politica']), ('docs/suolo/data/nil_suolo.csv', 'id_nil', ['pct_2025', 'nuovo_ha_per_100ha_nil']), ('docs/rigenerazione/data/nil.csv', 'id_nil', ['ambiti_pct']), ('docs/alberi/data/nil.csv', 'id_nil', ['alberi_per_1000_abitanti_2025', 'alberi_per_km2_2025', 'variazione_pct_2023_2025']), ('docs/nascite/data/nil_2022_2024.csv', 'id_nil', ['nati_per_1000_donne_15_49_2022_2024', 'nati_per_1000_donne_15_49_2003_2005']), ('docs/poverta-educativa/data/milano_nil_poverta_educativa.csv', 'id_nil', ['tp_pct_statali', 'quota_paritaria_pct', 'sedi_nido_per_1000_0_2']), ('docs/ristoranti/data/nil.csv', 'id_nil', ['in_piano_per_1000ab', 'in_piano_per_km2', 'pratiche_artigianato_alim']), ('docs/lavoro/data/nil_lavoro.csv', 'nil', ['tasso_occ', 'gap_occ_mf'])]
for f, ic, cc in USI:
    d = rd(f)
    if f.endswith('nil_lavoro.csv'):
        d = d[d.anno == 2023]
    for c_ in cc:
        if c_ not in d.columns:
            say(' COLONNA ASSENTE', f, c_); continue
        s = pd.to_numeric(d.set_index(ic)[c_], errors='coerce'); s.index = pd.to_numeric(s.index, errors='coerce')
        v = s.reindex(A_ids)
        flag = '  <--- pochi' if v.notna().sum() < 50 else ''
        if flag or v.nunique() < 5:
            say(f' {f} {c_}: valori {v.notna().sum()} distinti {v.nunique()}{flag}')
say(' (righe mostrate solo se sospette)')
# --- 7. Fattori di scala e unità: esempio docs/ristoranti e parcheggi
ri = rd('docs/ristoranti/data/nil.csv').set_index('id_nil'); say(' locali_x1000 esempio', ri.in_piano_per_1000ab.reindex(A_ids).describe().round(2).to_dict())
# --- 8. Famiglia media: fillna fra esatto e approssimato (01 riga 102)
ce = rd('censimenti/pulito/indicatori_NIL.csv'); c23 = ce[ce.anno == 2023].set_index('nil')
say('\n--- 8. famiglie 2023: esatto non nullo', c23.famiglie_comp_medio_esatto.notna().sum(), 'approssimato non nullo', c23.famiglie_comp_medio_approx.notna().sum(), 'stessa cosa?', round(c23[['famiglie_comp_medio_esatto', 'famiglie_comp_medio_approx']].corr().iloc[0, 1], 3) if c23.famiglie_comp_medio_esatto.notna().sum() > 2 else '-', 'residenti/fam', round(stats.spearmanr(c23['pop'] / c23.fam, c23.famiglie_comp_medio_approx, nan_policy='omit').statistic, 3))
# --- 9. rho_loo_min/max (robusta 134-135): quante volte nasconde un cambio di segno, simulato sulle mie coppie
say('\n--- 9. robusta.py righe 134-135')
N = pd.read_csv(os.path.join(OUT, 'nil_tabella_finale.csv'))
def loo(x, y):
    rs = []
    for m in sorted(N.municipio.unique()):
        d = N[N.municipio != m]
        rs.append(parz(d[x].values, d[y].values, d[CTRL].values))
    return np.array(rs)
for x, y in [('fam_2021', 'q_sx|comunali_consiglio_2016'), ('gap_2011', 'aff_netta'), ('bc_negozi_x1000', 'in_piano_per_km2'), ('air100', 'k_2014_2019')]:
    d = N.dropna(subset=[x, y]); r0 = parz(d[x].values, d[y].values, d[CTRL].values)
    rs = loo(x, y) if d.shape[0] == len(N) else np.array([np.nan])
    if np.isnan(rs).all():
        continue
    say(f' {x} {y}: r {r0:+.3f} vero min/max {rs.min():+.3f}/{rs.max():+.3f}; come scritto min {np.min(np.abs(rs)) * np.sign(r0):+.3f} max {np.max(np.abs(rs)) * np.sign(r0):+.3f}')
# --- 10. msr (robusta 79): colonne perse
xy = N[['cx', 'cy']].values; Dm = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1)); W = ((Dm < 2.2) & (Dm > 0)).astype(float)
n_ = len(N); H = np.eye(n_) - 1 / n_; lam, U = np.linalg.eigh(H @ W @ H)
U2 = U[:, np.abs(U.T @ np.ones(n_)) < 1e-6]; say('--- 10. msr: colonne tenute', U2.shape[1], 'su', n_, '(attese', n_ - 1, ')')
rng = np.random.default_rng(1); z = rng.normal(size=n_); z -= z.mean(); say('  quota di un residuo ricostruita', round(float(np.sum((U2.T @ z) ** 2) / (z @ z)), 6))
# --- 11. Sfoca: reddito sfocato contro reddito (controllo di validità del metodo)
cap = rd('quartieri-che-cambiano/out/collegamento_cap_nil.csv'); say('--- 11. righe collegamento', cap.shape, 'quote per NIL sommano a', cap.groupby('ID_NIL').quota_nil.sum().round(3).describe()[['min', 'max']].to_dict(), 'ID_NIL mancanti', int(cap.ID_NIL.isna().sum()))
# --- 12. Effetto famiglia sul confronto lista per lista: Centro assente (07 riga 115) già nel rapporto di fase 1
# --- 13. Differenza qmat: distanza al quadrato
say('--- 13. Con distanza + distanza² (come robusta.py) i miei risultati principali')
N['d2'] = (N.dist_duomo.rank() - N.dist_duomo.rank().mean()) ** 2
for x, y in [('aff_cam22', 'smrTT|2022-2024'), ('aff_netta', 'smrTT|2012-2019'), ('laur_oggi', 'q_dx|camera_2022'), ('air100', 'g_x1000')]:
    d = N.dropna(subset=[x, y]); say(f' {x} {y}: base {parz(d[x].values, d[y].values, d[CTRL].values):+.3f}; con d² {parz(d[x].values, d[y].values, d[CTRL + ["d2"]].values):+.3f}')
# --- 14. Totali luogo: comprende i non luoghi? (01 riga 304-307)
tl = rd('luoghi-cercati/pulito/totali_luogo.csv'); say('--- 14. totali_luogo', tl.shape, list(tl.columns)[:12])
if 'tipo' in tl.columns:
    say('  per tipo', tl.groupby('tipo').views_totali.sum().to_dict())
lm = rd('luoghi-cercati/pulito/luoghi.csv')[['qid', 'tipo', 'categoria']]; t2 = tl.merge(lm, on='qid', how='left', suffixes=('', '_l'))
say('  fuori dai luoghi veri, per tipo (views):', t2.groupby(t2.tipo_l if 'tipo_l' in t2 else t2.tipo).views_totali.sum().to_dict())
L.close()
