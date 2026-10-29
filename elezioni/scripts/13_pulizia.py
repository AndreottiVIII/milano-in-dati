"""Passo 1b: dataset pulito unificato (livello sezione).
uso: python -I 13_pulizia.py <cartella elezioni> <cartella lavoro con carica.pkl>
Scrive in <elezioni>/pulito/: elezioni.csv, risultati_sezione.csv, voti_sezione.csv, problemi_auto.json
(problemi.md viene composto da 14_problemi.py)
"""
import sys, os, re, pickle, json
import numpy as np
import pandas as pd

base, work = sys.argv[1], sys.argv[2]
outdir = os.path.join(base, 'pulito')
os.makedirs(outdir, exist_ok=True)
data = pickle.load(open(os.path.join(work, 'carica.pkl'), 'rb'))
problemi = []  # dict(codice, dove, cosa, righe)


def P(codice, dove, cosa, righe=None):
    problemi.append(dict(codice=codice, dove=dove, cosa=cosa, righe=righe))


# ---------------------------------------------------------------- classificazione
def classify(base_title, etype):
    t = base_title
    if etype == 'referendum' or 'Referendum' in t:
        return 'referendum', 'Referendum', True, ''
    if 'Comunali' in t:
        if 'ballottaggio' in t:
            return 'comunali_ballottaggio', 'Comunali - ballottaggio', True, ''
        if 'Sindaco' in t:
            return 'comunali_sindaco', 'Comunali - Sindaco', True, ''
        return 'comunali_consiglio', 'Comunali - Consiglio', True, ''
    if 'Municipali' in t:
        if 'Presidente' in t:
            return 'municipali_presidente', 'Municipali - Presidente', False, 'candidati presidente: 59 nomi nel 2016, nessuna famiglia'
        return 'municipali_consiglio', 'Municipali - Consiglio', True, ''
    if 'Circoscrizionali' in t and 'Regionali' not in t:
        if 'Coalizioni' in t:
            return 'circoscrizionali_coalizioni', 'Circoscrizionali - coalizioni', False, 'coalizioni locali, doppione delle liste'
        return 'circoscrizionali_liste', 'Circoscrizionali - liste', True, ''
    if 'Politiche' in t:
        cam = 'Camera' in t
        if 'Maggioritaria' in t:
            return ('camera_maggioritario' if cam else 'senato_maggioritario'), 'Politiche - ' + ('Camera' if cam else 'Senato') + ' maggioritario', False, 'quota maggioritaria: voti ai candidati/coalizioni'
        if 'Candidati nel Collegio' in t:
            return ('camera_candidati' if cam else 'senato_candidati'), 'Politiche - ' + ('Camera' if cam else 'Senato') + ' candidati uninominali', False, 'voti ai candidati uninominali'
        return ('camera' if cam else 'senato'), 'Politiche - ' + ('Camera' if cam else 'Senato'), True, ''
    if 'Europeo' in t:
        return 'europee', 'Europee', True, ''
    if 'Regionali' in t:
        if 'Liste Regionali' in t or 'Candidati Presidente' in t:
            return 'regionali_presidente', 'Regionali - candidati presidente', False, 'voti ai candidati presidente (listini regionali)'
        return 'regionali_consiglio', 'Regionali - Consiglio', True, ''
    if 'Provinciali' in t:
        if 'Consiglio' in t:
            return 'provinciali_consiglio', 'Provinciali - Consiglio', True, ''
        if 'Ballottaggio' in t:
            return 'provinciali_ballottaggio', 'Provinciali - ballottaggio presidente', False, 'candidati'
        return 'provinciali_presidente', 'Provinciali - Presidente', False, 'candidati'
    raise ValueError(base_title)


# date vere dei ballottaggi (il portale mette la data del primo turno). Fonte: calendario ufficiale (Ministero dell'Interno),
# confermata per il 2011 dal titolo di ds1111 ("Ballottaggio del 29-30/5/2011") e per il 2016 da ds1117 ("19/6/2016").
BALLOT = {('comunali_ballottaggio', 1993): '1993-06-20', ('comunali_ballottaggio', 1997): '1997-05-11',
          ('comunali_ballottaggio', 2011): '2011-05-29', ('comunali_ballottaggio', 2016): '2016-06-19',
          ('provinciali_ballottaggio', 2009): '2009-06-21'}


def parse_date_str(s):
    s = str(s).strip()
    m = re.fullmatch(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m:
        return '%04d-%02d-%02d' % (int(m[3]), int(m[2]), int(m[1]))
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        return s
    return None


def title_date(title):
    m = re.search(r'(\d{1,2})(?:-\d{1,2})?/(\d{1,2})/(\d{4})', title)
    return '%04d-%02d-%02d' % (int(m[3]), int(m[2]), int(m[1])) if m else None


def clean_ref_title(title):
    """titolo del quesito referendum: dopo 'su' fino a ' del '/':'"""
    t = title.split(':')[0] if title.count(':') > 1 else title
    t = re.sub(r'^Elezioni:\s*', '', title)
    t = re.sub(r':\s*Risultati.*$', '', t)
    return t


# ---------------------------------------------------------------- raggruppa dataset per elezione
by_base = {}
for ds, o in data.items():
    bt = re.split(r':\s*(?:Voti di lista|Risultati|Riepilog)', o['title'])[0].strip()
    by_base.setdefault(bt, {})['voti' if o['kind'].startswith('voti') else 'ris'] = ds

catalogo = []
ris_rows = []
voti_rows = []
for bt, pair in sorted(by_base.items(), key=lambda kv: min(kv[1].values())):
    dr, dv = pair.get('ris'), pair.get('voti')
    if dr is None:
        P('NO_RISULTATI', 'ds%s' % dv, 'dataset voti senza file risultati abbinato: %s' % bt)
        continue
    o = data[dr]
    gruppo, etich, nelsito, nota = classify(bt, o['etype'])
    sess_raw = o['df'].sessione.iloc[0]
    sdate = parse_date_str(sess_raw)
    tdate = title_date(o['title']) if gruppo == 'referendum' else None
    year_title = re.search(r'(19|20)\d\d', bt)
    note_data = ''
    if gruppo == 'referendum':
        date = tdate
        if sdate != date:
            P('DATA_REFERENDUM', 'ds%s' % dr, "campo Sessione = '%s' non coincide con la data nel titolo (%s): uso quella del titolo" % (sess_raw, date),
              len(o['df']))
            note_data = "Sessione nel file: '%s'" % sess_raw
    else:
        date = sdate
        key = (gruppo, int(year_title.group(0)) if year_title else None)
        if key in BALLOT:
            date = BALLOT[key]
            P('DATA_BALLOTTAGGIO', 'ds%s' % dr,
              "Sessione = %s (primo turno), ballottaggio corretto a %s (calendario ufficiale)" % (sess_raw, date), len(o['df']))
            note_data = 'ballottaggio, data del file = primo turno'
    anno = int(date[:4])
    # sistema territoriale
    tcol = o['tcol']
    tmax = o['df'].territorio.max()
    if tcol == 'Circoscrizione':
        sistema = 'circoscrizione'
    elif tcol == 'Zona':
        sistema = 'circoscrizione' if (tmax == tmax and tmax > 9) else 'zona'
        if sistema == 'circoscrizione' and tcol == 'Zona':
            P('ZONA_E_CIRCOSCRIZIONE', 'ds%s' % dr, "colonna 'Zona' con valori fino a %d: sono le 20 circoscrizioni" % tmax, None)
    elif tcol == 'Municipio':
        sistema = 'municipio'
    else:
        sistema = ''
    eid = '%s_%s' % (gruppo, date) if gruppo != 'referendum' else 'referendum_%s_ds%d' % (date, dr)
    cat = dict(elezione_id=eid, gruppo=gruppo, etichetta=etich, data=date, anno=anno, titolo=bt, ds_risultati=dr, ds_voti=dv if dv else '',
               sistema_territorio=sistema, nel_sito='si' if nelsito else 'no', nota_sito=nota, nota_data=note_data)
    catalogo.append(cat)

    # ---------------- risultati
    d = o['df'].copy()
    r = pd.DataFrame(dict(elezione_id=eid, sezione=d.sezione, territorio=d.territorio))
    for src, dst in [('Elettori', 'elettori'), ('Votanti', 'votanti'), ('Validi', 'validi'), ('Non validi', 'non_validi'), ('Si', 'si'), ('No', 'no')]:
        r[dst] = d[src] if src in d else np.nan
    r['flag'] = ''
    if (r.elettori.fillna(0).sum() == 0):
        r['elettori'] = np.nan
        P('ELETTORI_ZERO', 'ds%s' % dr, "campo Elettori = 0 in tutte le righe: lo metto vuoto (affluenza non calcolabile)", len(r))
    if (r.votanti.fillna(0).sum() == 0):
        if r.non_validi.fillna(0).sum() > 0 and r.validi.fillna(0).sum() > 0:
            r['votanti'] = r.validi + r.non_validi
            r['flag'] = 'votanti_derivati'
            P('VOTANTI_ZERO', 'ds%s' % dr, "campo Votanti = 0 in tutte le righe: ricalcolato come Validi + Non validi", len(r))
        else:
            r['votanti'] = np.nan
            P('VOTANTI_ZERO', 'ds%s' % dr, "campo Votanti vuoto/0 in tutte le righe e Non validi non disponibile: lasciato vuoto", len(r))
    # votanti > elettori
    n_gt = int(((r.votanti > r.elettori) & (r.elettori > 0)).sum())
    n_e0 = int(((r.elettori == 0) & (r.votanti > 0)).sum())
    if n_gt or n_e0:
        P('VOTANTI_SOPRA_ELETTORI', 'ds%s' % dr, "%d sezioni con votanti > elettori e %d con elettori = 0 ma votanti > 0 (tenute come sono; probabili sezioni speciali/ospedaliere)" % (n_gt, n_e0), n_gt + n_e0)
    spec = (r.sezione >= 9000)
    if spec.any():
        r.loc[spec, 'flag'] = (r.loc[spec, 'flag'] + ' sezione_speciale').str.strip()
        P('SEZIONI_9001_9011', 'ds%s' % dr, "%d sezioni numerate >= 9001 (seggi speciali 2025): tenute, flag sezione_speciale" % int(spec.sum()), int(spec.sum()))
    r['territorio_derivato'] = 0
    ris_rows.append(r)

    # ---------------- voti
    if gruppo == 'referendum':
        v1 = pd.DataFrame(dict(elezione_id=eid, sezione=r.sezione, territorio=r.territorio, lista='Sì', voti=r.si))
        v2 = pd.DataFrame(dict(elezione_id=eid, sezione=r.sezione, territorio=r.territorio, lista='No', voti=r.no))
        if r.si.isna().all():
            P('REFERENDUM_SENZA_SI_NO', 'ds%s' % dr, 'campi Si/No vuoti', len(r))
        voti_rows += [v1, v2]
        # Sì + No = validi?
        diff = int(((r.si + r.no) != r.validi).sum())
        if diff:
            P('SI_NO_NON_TORNANO', 'ds%s' % dr, '%d sezioni con Sì+No diverso da Validi' % diff, diff)
    elif dv:
        dd = data[dv]['df']
        v = pd.DataFrame(dict(elezione_id=eid, sezione=dd.sezione, territorio=dd.territorio, lista=dd.lista, voti=dd['Voti']))
        voti_rows.append(v)
    else:
        P('SENZA_VOTI', 'ds%s' % dr, 'nessun file voti di lista abbinato (solo risultati): %s' % bt)

cat = pd.DataFrame(catalogo)
ris = pd.concat(ris_rows, ignore_index=True)
voti = pd.concat(voti_rows, ignore_index=True)

# ---------------------------------------------------------------- territorio dei referendum 1981 (colonna vuota)
miss = ris.groupby('elezione_id').territorio.apply(lambda s: s.isna().all())
miss = miss[miss].index.tolist()
ref80 = ris[ris.elezione_id == 'comunali_consiglio_1980-06-08'].set_index('sezione').territorio
ref79 = ris[ris.elezione_id == 'camera_1979-06-03'].set_index('sezione').territorio
for eid in miss:
    m = ris.elezione_id == eid
    t = ris.loc[m, 'sezione'].map(ref80)
    t = t.fillna(ris.loc[m, 'sezione'].map(ref79))
    ris.loc[m, 'territorio'] = t.values
    ris.loc[m, 'territorio_derivato'] = 1
    n_na = int(t.isna().sum())
    P('TERRITORIO_MANCANTE', eid, "colonna Zona vuota nei referendum 1981: territorio ripreso dal numero di sezione nelle Comunali 1980 (poi Politiche 1979); %d sezioni su %d non ritrovate" % (n_na, len(t)), len(t))
    cat.loc[cat.elezione_id == eid, 'sistema_territorio'] = 'circoscrizione'
    vm = voti.elezione_id == eid
    voti.loc[vm, 'territorio'] = voti.loc[vm, 'sezione'].map(ref80).fillna(voti.loc[vm, 'sezione'].map(ref79)).values

# territorio dei voti = quello dei risultati (verifica)
key = ris.set_index(['elezione_id', 'sezione']).territorio
vk = pd.MultiIndex.from_frame(voti[['elezione_id', 'sezione']])
tr = key.reindex(vk).values
mism = (voti.territorio.values != tr) & ~np.isnan(tr.astype(float))
if mism.any():
    P('TERRITORIO_DIVERSO', 'voti vs risultati', '%d righe voti con territorio diverso dai risultati: uso quello dei risultati' % int(mism.sum()), int(mism.sum()))
voti['territorio'] = np.where(np.isnan(tr.astype(float)), voti.territorio.values, tr)
no_ris = int(np.isnan(tr.astype(float)).sum())
if no_ris:
    P('VOTI_SENZA_RISULTATI', 'voti', '%d righe voti di sezioni senza territorio nei risultati (le 2 sezioni dei referendum 1981 non ritrovate): restano senza territorio' % no_ris, no_ris)

# sezioni con voti ma non nei risultati e viceversa, per elezione
# controllo: somma voti di lista per sezione vs validi (solo elezioni di lista)
for eid, g in voti.groupby('elezione_id'):
    if eid.startswith('referendum'):
        continue
    s = g.groupby('sezione').voti.sum()
    rr = ris[ris.elezione_id == eid].set_index('sezione')
    j = rr[['validi']].join(s.rename('lista'), how='left').fillna({'lista': 0})
    over = int((j.lista > j.validi).sum())
    if over:
        P('LISTE_OLTRE_VALIDI', eid, '%d sezioni con somma voti di lista > Validi del file risultati (campo Validi non e la somma delle liste)' % over, over)
    # sezioni dei risultati senza nessun voto di lista
    nov = int((~rr.index.isin(s.index)).sum())
    if nov:
        P('SEZIONI_SENZA_VOTI_LISTA', eid, '%d sezioni nel file risultati senza righe nel file voti di lista (di solito perche non hanno voti a nessuna lista)' % nov, nov)

# voti nulli/NaN
nn = int(voti.voti.isna().sum())
if nn:
    P('VOTI_VUOTI', 'voti', '%d righe con voti vuoti: tolte' % nn, nn)
    voti = voti[voti.voti.notna()]

for c in ['sezione', 'territorio']:
    ris[c] = ris[c].astype('Int64')
    voti[c] = voti[c].astype('Int64')
for c in ['elettori', 'votanti', 'validi', 'non_validi', 'si', 'no']:
    ris[c] = ris[c].astype('Int64')
voti['voti'] = voti.voti.astype('Int64')

# n sezioni
cat['n_sezioni'] = cat.elezione_id.map(ris.groupby('elezione_id').sezione.nunique())
cat['elettori'] = cat.elezione_id.map(ris.groupby('elezione_id').elettori.sum(min_count=1))
cat['votanti'] = cat.elezione_id.map(ris.groupby('elezione_id').votanti.sum(min_count=1))
cat = cat.sort_values(['data', 'gruppo', 'ds_risultati']).reset_index(drop=True)

cat.to_csv(os.path.join(outdir, 'elezioni.csv'), index=False, encoding='utf-8-sig')
ris.drop(columns=[]).to_csv(os.path.join(outdir, 'risultati_sezione.csv'), index=False, encoding='utf-8-sig')
voti.to_csv(os.path.join(outdir, 'voti_sezione.csv'), index=False, encoding='utf-8-sig')
json.dump(problemi, open(os.path.join(work, 'problemi_auto.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print('elezioni', len(cat), 'ris', len(ris), 'voti', len(voti), 'problemi', len(problemi))
print(cat.groupby('gruppo').size())
