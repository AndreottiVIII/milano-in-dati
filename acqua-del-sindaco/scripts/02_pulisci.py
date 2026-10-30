"""Passo 2 - pulizia delle analisi dell'acqua -> pulito/analisi.csv + controlli.
Uso: python -I 02_pulisci.py <cartella_strand>
Legge solo da raw/, scrive solo in pulito/ (CSV UTF-8, separatore ';').
"""
import sys, os, re, glob, json, math
import pandas as pd

BASE = sys.argv[1]
RAW = os.path.join(BASE, 'raw')
OUT = os.path.join(BASE, 'pulito')
CTL = os.path.join(OUT, '_controlli')
os.makedirs(CTL, exist_ok=True)
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    LOG.append(s)
    print(s)


# ---------------------------------------------------------------- codifica
NBSP = ' '
# caratteri "attesi" in un testo italiano corretto di questi file
ATTESI = set('àèéìòùÀÈÉÌÒÙ°µ’–' + NBSP)


def leggi_testo(path):
    """Ritorna (testo, codifica_usata). UTF-8 se valido, altrimenti cp1252."""
    b = open(path, 'rb').read()
    if b.startswith(b'\xef\xbb\xbf'):
        b = b[3:]
    try:
        return b.decode('utf-8'), 'utf-8'
    except UnicodeDecodeError:
        return b.decode('cp1252'), 'cp1252 (file non UTF-8)'


# Riparazioni a livello di campo (stringa) per i doppi passaggi di codifica.
# 1) cp850 -> letto come cp1252 -> salvato in UTF-8 : 'æ' (mu), 'ø' (gradi), '…' (a accentata)
# 2) cp1252 -> letto come cp1250 -> salvato in UTF-8 : 'ŕ' al posto della a accentata
SPIA_CP850 = set('æø…')
SPIA_CP1250 = set('ŕ')


def ripara(s):
    """Ritorna (stringa riparata, descrizione della riparazione o '')."""
    if any(ch in SPIA_CP850 for ch in s):
        try:
            r = s.encode('cp1252').decode('cp850')
            return r, 'cp850-letto-come-cp1252'
        except UnicodeError:
            pass
    if any(ch in SPIA_CP1250 for ch in s):
        try:
            r = s.encode('cp1250').decode('cp1252')
            return r, 'cp1252-letto-come-cp1250'
        except UnicodeError:
            pass
    return s, ''


# ---------------------------------------------------------------- normalizzazione parametri
def chiave(s):
    s = s.lower().replace(NBSP, ' ').replace("'", '').strip()
    for a, b in (('à', 'a'), ('è', 'e'), ('é', 'e'), ('ì', 'i'), ('ò', 'o'), ('ù', 'u')):
        s = s.replace(a, b)
    return s


PARAMS = [  # (prefisso chiave, codice, nome, gruppo)
    ('ph', 'ph', 'pH', 'acidita'),
    ('residuo fisso', 'residuo_fisso_180', 'Residuo fisso a 180 °C', 'mineralizzazione'),
    ('durezza', 'durezza', 'Durezza', 'mineralizzazione'),
    ('conducibil', 'conducibilita', 'Conducibilità elettrica a 20 °C', 'mineralizzazione'),
    ('calcio', 'calcio', 'Calcio', 'minerali'),
    ('magnesio', 'magnesio', 'Magnesio', 'minerali'),
    ('sodio', 'sodio', 'Sodio', 'minerali'),
    ('potassio', 'potassio', 'Potassio', 'minerali'),
    ('bicarbonat', 'bicarbonati', 'Bicarbonati', 'minerali'),
    ('cloruri', 'cloruri', 'Cloruri', 'sali'),
    ('solfati', 'solfati', 'Solfati', 'sali'),
    ('fluoruri', 'fluoruri', 'Fluoruri', 'sali'),
    ('nitrati', 'nitrati', 'Nitrati', 'composti_azotati'),
    ('nitriti', 'nitriti', 'Nitriti', 'composti_azotati'),
    ('ammonio', 'ammonio', 'Ammonio', 'composti_azotati'),
    ('arsenico', 'arsenico', 'Arsenico', 'metalli_tracce'),
    ('manganese', 'manganese', 'Manganese', 'metalli_tracce'),
    ('cloro residuo', 'cloro_residuo', 'Cloro residuo', 'disinfezione'),
]
UNITA = {
    'ph': 'pH', 'residuo_fisso_180': 'mg/L', 'durezza': '°F', 'conducibilita': 'µS/cm',
    'calcio': 'mg/L', 'magnesio': 'mg/L', 'sodio': 'mg/L', 'potassio': 'mg/L', 'bicarbonati': 'mg/L',
    'cloruri': 'mg/L', 'solfati': 'mg/L', 'fluoruri': 'mg/L', 'nitrati': 'mg/L', 'nitriti': 'mg/L',
    'ammonio': 'mg/L', 'arsenico': 'µg/L', 'manganese': 'µg/L', 'cloro_residuo': 'mg/L',
}


def normalizza_param(nome):
    k = chiave(nome)
    for pre, cod, desc, gruppo in PARAMS:
        if k.startswith(pre):
            return cod, desc, gruppo
    raise ValueError('parametro sconosciuto: ' + ascii(nome))


def normalizza_unita(u, cod):
    k = chiave(u).replace(' ', '')
    attesa = UNITA[cod]
    # confronto "morbido": mg/l == mg/L, "unita ph" == pH, "µs/cm a 20" == µS/cm
    kk = k.replace('µ', 'u').replace('°', '')
    ee = chiave(attesa).replace('µ', 'u').replace('°', '').replace(' ', '')
    ok = (kk == ee) or kk.startswith(ee) or (cod == 'ph' and 'ph' in kk)
    return attesa, ok


# ---------------------------------------------------------------- valori e limiti
RE_VAL = re.compile(r'^([<>]?)\s*(\d+(?:[.,]\d+)?)$')


def num(s):
    return float(s.replace(',', '.'))


def parse_valore(raw):
    """Ritorna dict: valore, sotto_soglia, soglia, qualita, nota."""
    r = raw.strip().replace(NBSP, ' ')
    if r in ('', '-'):
        return dict(valore=None, sotto_soglia=0, soglia=None, qualita='non_misurato', nota='')
    m = RE_VAL.match(r)
    if not m:
        return dict(valore=None, sotto_soglia=0, soglia=None, qualita='anomalo',
                    nota='valore non interpretabile: ' + ascii(r))
    op, n = m.group(1), num(m.group(2))
    if op == '<':
        return dict(valore=None, sotto_soglia=1, soglia=n, qualita='sotto_soglia', nota='')
    if op == '>':
        return dict(valore=None, sotto_soglia=0, soglia=None, qualita='anomalo',
                    nota='operatore ">" isolato, probabile refuso di "<": ' + ascii(r))
    nota = 'valore 0 scritto cosi nel file: probabile "sotto soglia" non marcato, non e uno zero misurato' if n == 0 else ''
    return dict(valore=n, sotto_soglia=0, soglia=None, qualita='ok', nota=nota)


def parse_limite(raw):
    t = raw.strip().replace(NBSP, ' ')
    ast = '*' in t
    t = t.replace('*', '').strip()
    tl = t.lower()
    out = dict(limite_min=None, limite_max=None, limite_tipo='nessuno', limite_asterisco=int(ast))
    if tl in ('', 'non previsto'):
        return out
    nums = [num(x) for x in re.findall(r'\d+(?:[.,]\d+)?', t)]
    if re.search(r'\bda\b.*\ba\b', tl) or re.match(r'^\d+(?:[.,]\d+)?\s*-\s*\d+(?:[.,]\d+)?$', tl):
        out['limite_min'], out['limite_max'] = nums[0], nums[1]
        out['limite_tipo'] = 'consigliato' if ('consigliat' in tl or re.match(r'^\d+\s*-', tl)) else 'legge'
        return out
    if 'consigliat' in tl or ast:
        out['limite_max'] = nums[0]
        out['limite_tipo'] = 'consigliato'
        return out
    out['limite_max'] = nums[0]
    out['limite_tipo'] = 'legge'
    return out


def entro_limite(v, sotto, soglia, lmin, lmax):
    if lmin is None and lmax is None:
        return 'n.a.'
    if sotto:
        # il valore vero e' < soglia: e' sicuramente entro il massimo se soglia <= massimo
        if lmax is not None and soglia is not None and soglia <= lmax:
            return 'si'
        return 'n.d.'
    if v is None:
        return 'n.d.'
    if lmin is not None and v < lmin:
        return 'no'
    if lmax is not None and v > lmax:
        return 'no'
    return 'si'


# ---------------------------------------------------------------- lettura sorgenti
MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
        'settembre', 'ottobre', 'novembre', 'dicembre']
ZONE = {  # nome file mensili -> (codice, id)
    'nord-est': ('NE', 18), 'nord-ovest': ('NO', 6), 'sud-est': ('SE', 16), 'sud-ovest': ('SO', 15)}

righe = []
rip_log = []          # tutte le riparazioni di codifica
enc_log = []          # codifica per file
json_diff = []


def aggiungi(rec, ripar):
    rec['codifica_riparata'] = ';'.join(sorted(set(r for r in ripar if r)))
    righe.append(rec)


def csv_testo_in_df(path):
    txt, enc = leggi_testo(path)
    from io import StringIO
    df = pd.read_csv(StringIO(txt), sep=';', dtype=str, keep_default_na=False)
    return df, enc


# --- mensili per zona (2021-2026)
for path in sorted(glob.glob(os.path.join(RAW, 'ds*', '*.csv'))):
    nome = os.path.basename(path)
    ds = os.path.basename(os.path.dirname(path))
    if nome.startswith('civici_zone') or ds.startswith('ds1571') or ds.startswith('ds1827'):
        continue
    df, enc = csv_testo_in_df(path)
    enc_log.append((ds, nome, enc, len(df)))
    if 'parametroMisurato' in df.columns:           # mensile per zona
        for i, r in df.iterrows():
            ripar = []
            campi = {}
            for c in ('parametroMisurato', 'unitaMisura', 'limitiLegge', 'valoreRilevato', 'zonaNome', 'mese'):
                v, rp = ripara(r[c])
                campi[c] = v
                if rp:
                    ripar.append(rp)
                    rip_log.append((nome, i + 2, c, r[c], v, rp))
            cod, desc, gruppo = normalizza_param(campi['parametroMisurato'])
            unita, uok = normalizza_unita(campi['unitaMisura'], cod)
            if not uok:
                log('ATTENZIONE unita non attesa', nome, i + 2, ascii(campi['unitaMisura']), cod)
            zc, zid = ZONE[campi['zonaNome'].lower()]
            if str(zid) != r['zonaId']:
                log('ATTENZIONE zonaId diverso', nome, i + 2, campi['zonaNome'], r['zonaId'])
            mnum = MESI.index(campi['mese'].lower()) + 1
            anno = int(r['anno'])
            val = parse_valore(campi['valoreRilevato'])
            lim = parse_limite(campi['limitiLegge'])
            dc = r['dataCaricamento'][:10]
            lorem = 'lorem' in r['info'].lower()
            # data di caricamento prima della fine del mese a cui il dato si riferisce
            fine_mese = pd.Timestamp(year=anno, month=mnum, day=1) + pd.offsets.MonthEnd(0)
            anomalo_car = int(pd.Timestamp(dc) < fine_mese) if dc else 0
            aggiungi(dict(
                periodo_tipo='mese', periodo='%04d-%02d' % (anno, mnum), anno=anno, mese=mnum,
                trimestre=(mnum - 1) // 3 + 1, data_riferimento='%04d-%02d-01' % (anno, mnum),
                zona_codice=zc, zona_nome=campi['zonaNome'], zona_id=zid,
                parametro=cod, parametro_nome=desc, gruppo=gruppo, parametro_originale=r['parametroMisurato'],
                valore_testo=campi['valoreRilevato'], valore=val['valore'], unita=unita,
                sotto_soglia=val['sotto_soglia'], soglia=val['soglia'], qualita_dato=val['qualita'],
                nota_valore=val['nota'],
                limite_testo=campi['limitiLegge'].replace(NBSP, ' ').strip(),
                limite_min=lim['limite_min'], limite_max=lim['limite_max'], limite_tipo=lim['limite_tipo'],
                limite_asterisco=lim['limite_asterisco'],
                entro_limite=entro_limite(val['valore'], val['sotto_soglia'], val['soglia'], lim['limite_min'], lim['limite_max']),
                data_caricamento=dc, caricamento_prima_del_mese=anomalo_car, info_segnaposto=int(lorem),
                dataset=ds, file_origine=nome, riga_origine=i + 2), ripar)
    else:                                           # trimestrale, tutta la citta'
        m = re.search(r'(\d)-trimestre-(\d{4})', ds)
        q, anno = int(m.group(1)), int(m.group(2))
        for i, r in df.iterrows():
            ripar = []
            campi = {}
            for c in df.columns:
                v, rp = ripara(r[c])
                v = v.replace(NBSP, ' ')
                campi[c] = v
                if rp:
                    ripar.append(rp)
                    rip_log.append((nome, i + 2, c, r[c], v, rp))
            cp = campi[df.columns[0]]
            cod, desc, gruppo = normalizza_param(cp)
            unita, uok = normalizza_unita(campi[df.columns[3]], cod)
            if not uok:
                log('ATTENZIONE unita non attesa', nome, i + 2, ascii(campi[df.columns[3]]), cod)
            val = parse_valore(campi[df.columns[2]])
            lim = parse_limite(campi[df.columns[1]])
            aggiungi(dict(
                periodo_tipo='trimestre', periodo='%04d-Q%d' % (anno, q), anno=anno, mese=None, trimestre=q,
                data_riferimento='%04d-%02d-01' % (anno, 3 * q - 2),
                zona_codice='MI', zona_nome='Tutta Milano', zona_id=None,
                parametro=cod, parametro_nome=desc, gruppo=gruppo, parametro_originale=r[df.columns[0]],
                valore_testo=campi[df.columns[2]], valore=val['valore'], unita=unita,
                sotto_soglia=val['sotto_soglia'], soglia=val['soglia'], qualita_dato=val['qualita'],
                nota_valore=val['nota'],
                limite_testo=campi[df.columns[1]].strip(),
                limite_min=lim['limite_min'], limite_max=lim['limite_max'], limite_tipo=lim['limite_tipo'],
                limite_asterisco=lim['limite_asterisco'],
                entro_limite=entro_limite(val['valore'], val['sotto_soglia'], val['soglia'], lim['limite_min'], lim['limite_max']),
                data_caricamento='', caricamento_prima_del_mese=0, info_segnaposto=0,
                dataset=ds, file_origine=nome, riga_origine=i + 2), ripar)

a = pd.DataFrame(righe)
# il campo "entro" va letto separatamente per limiti di legge e valori solo consigliati
a['entro_valore_consigliato'] = a.entro_limite.where(a.limite_tipo == 'consigliato', 'n.a.')
a['entro_limite_legge'] = a.entro_limite.where(a.limite_tipo == 'legge', 'n.a.')
a = a.drop(columns=['entro_limite'])
log('righe totali', len(a))

# --- confronto JSON vs CSV (stessi dati? stessa codifica?)
for path in sorted(glob.glob(os.path.join(RAW, 'ds*', '*.json'))):
    nome = os.path.basename(path)
    ds = os.path.basename(os.path.dirname(path))
    if nome.startswith('_package') or ds.startswith('ds1571') or ds.startswith('ds1827'):
        continue
    j = json.load(open(path, encoding='utf-8'))
    cpath = path[:-5] + '.csv'
    df, _ = csv_testo_in_df(cpath)
    if len(j) != len(df):
        json_diff.append((nome, 'numero righe diverso', len(j), len(df)))
        continue
    jd = pd.DataFrame(j).astype(str)
    if 'parametroMisurato' in jd.columns:
        # le righe del JSON sono in ordine diverso: confronto per chiave (anno, mese, zona, parametro)
        kk = ['anno', 'mese', 'zonaId', 'parametroMisurato']
        campi = ['limitiLegge', 'valoreRilevato', 'unitaMisura', 'zonaNome']
        m = df.astype(str).merge(jd, on=kk, suffixes=('_csv', '_json'), how='outer', indicator=True)
        non_appaiate = int((m['_merge'] != 'both').sum())
        diff = sum(int((m[c + '_csv'] != m[c + '_json']).sum()) for c in campi if c + '_csv' in m.columns)
        json_diff.append((nome, 'righe non appaiate / celle diverse (limite, valore, unita, zona) CSV vs JSON', non_appaiate, diff))
    else:
        diff = int((jd.values != df.astype(str).values).sum())
        json_diff.append((nome, 'celle diverse CSV vs JSON', 0, diff))
for d in json_diff:
    log('JSON vs CSV', d)

# --- log codifica
log('--- codifica per file')
for e in enc_log:
    log(e)
log('--- riparazioni di codifica:', len(rip_log), 'campi')
rp = pd.DataFrame(rip_log, columns=['file', 'riga', 'campo', 'prima', 'dopo', 'riparazione'])
rp['prima'] = rp['prima'].map(ascii)
rp['dopo'] = rp['dopo'].map(ascii)
rp.groupby(['file', 'campo', 'prima', 'dopo', 'riparazione']).size().reset_index(name='n').to_csv(
    os.path.join(CTL, 'codifica_riparazioni.csv'), sep=';', index=False)
log(rp.groupby(['file', 'riparazione']).size().to_string())

# caratteri non ASCII residui dopo la riparazione nei campi testuali tenuti
res = {}
for c in ('limite_testo', 'valore_testo', 'zona_nome', 'parametro_nome'):
    for s in a[c]:
        for ch in s:
            if ord(ch) > 127:
                res[ch] = res.get(ch, 0) + 1
log('caratteri non ASCII rimasti nei campi tenuti:', {ascii(k): v for k, v in res.items()})
assert all(k in ATTESI for k in res), 'carattere inatteso dopo riparazione'

# --- controlli di struttura
chiave_unica = ['periodo', 'zona_codice', 'parametro']
dup = a[a.duplicated(chiave_unica, keep=False)]
log('duplicati sulla chiave (periodo, zona, parametro):', len(dup))
dup_full = a.duplicated([c for c in a.columns if c not in ('riga_origine',)], keep=False).sum()
log('righe identiche duplicate:', dup_full)

# Nomi parametro/unita/limiti per anno -> controllo cambi nome
nomi = a.groupby(['parametro', 'parametro_originale', 'file_origine']).size().reset_index(name='n')
nomi['parametro_originale'] = nomi.parametro_originale.map(ascii)
nomi.to_csv(os.path.join(CTL, 'parametri_nomi_originali_per_file.csv'), sep=';', index=False)
lim = a.groupby(['parametro', 'anno', 'limite_testo', 'limite_tipo']).size().reset_index(name='n')
lim.to_csv(os.path.join(CTL, 'limiti_per_parametro_anno.csv'), sep=';', index=False)
cam = lim.groupby('parametro').limite_testo.nunique()
log('parametri con piu di una dicitura di limite:', cam[cam > 1].to_dict())

# unita originali
un = a.copy()
# riprendo unita originale dai file mensili: non salvata; il confronto e' stato fatto in normalizza_unita

# Soglie di rilevabilita' per parametro/anno
s = a[a.sotto_soglia == 1].groupby(['parametro', 'anno', 'valore_testo']).size().reset_index(name='n')
s.to_csv(os.path.join(CTL, 'soglie_sotto_limite_per_parametro_anno.csv'), sep=';', index=False)

# Quota sotto soglia
a['misurato'] = (a.qualita_dato != 'non_misurato').astype(int)
tot = len(a)
mis = int(a.misurato.sum())
sot = int(a.sotto_soglia.sum())
log('righe: %d, misurate (valore presente o sotto soglia): %d, sotto soglia: %d (%.1f%% delle misurate)' % (tot, mis, sot, 100 * sot / mis))
mm = a[(a.periodo_tipo == 'mese')]
log('solo mensili: righe %d, misurate %d, sotto soglia %d (%.1f%%)' % (len(mm), mm.misurato.sum(), mm.sotto_soglia.sum(), 100 * mm.sotto_soglia.sum() / mm.misurato.sum()))
q = a.groupby('parametro').agg(righe=('misurato', 'size'), misurate=('misurato', 'sum'), sotto_soglia=('sotto_soglia', 'sum'))
q['quota_sotto_soglia_su_misurate'] = (q.sotto_soglia / q.misurate).round(3)
q.to_csv(os.path.join(CTL, 'sotto_soglia_per_parametro.csv'), sep=';')
log(q.to_string())
qa = a.groupby('anno').agg(righe=('misurato', 'size'), misurate=('misurato', 'sum'), sotto_soglia=('sotto_soglia', 'sum'))
qa['quota'] = (qa.sotto_soglia / qa.misurate).round(3)
log(qa.to_string())
log('qualita_dato:', a.qualita_dato.value_counts().to_dict())
log('anomali:', a[a.qualita_dato == 'anomalo'][['periodo', 'zona_nome', 'parametro', 'valore_testo', 'nota_valore']].to_string())

# Completezza periodo x zona
comp = a[a.periodo_tipo == 'mese'].groupby(['periodo', 'zona_codice']).agg(
    parametri=('parametro', 'nunique'), misurati=('misurato', 'sum')).reset_index()
comp.to_csv(os.path.join(CTL, 'completezza_periodo_zona.csv'), sep=';', index=False)
incompleti = comp[(comp.parametri != 18)]
log('periodo x zona con meno di 18 parametri in elenco:\n' + incompleti.to_string())
mesi_presenti = sorted(a[a.periodo_tipo == 'mese'].periodo.unique())
atteso = pd.period_range('2021-01', '2026-09', freq='M').strftime('%Y-%m').tolist()
log('mesi attesi ma assenti (2021-01..2026-09):', [m for m in atteso if m not in mesi_presenti])
zp = comp.groupby('periodo').zona_codice.nunique()
log('mesi con meno di 4 zone:', zp[zp < 4].to_dict())

# Numero di parametri misurati in ogni mese (per vedere il "calendario" dei parametri)
cal = a[(a.periodo_tipo == 'mese') & (a.misurato == 1)].groupby(['periodo', 'zona_codice']).size().unstack()
cal.to_csv(os.path.join(CTL, 'parametri_misurati_per_mese_zona.csv'), sep=';')

# Valori ripetuti identici al mese precedente (stessa zona, parametro)
mnum = a[(a.periodo_tipo == 'mese') & (a.qualita_dato == 'ok')].copy()
mnum = mnum.sort_values(['zona_codice', 'parametro', 'periodo'])
mnum['prec'] = mnum.groupby(['zona_codice', 'parametro']).valore.shift(1)
mnum['prec_periodo'] = mnum.groupby(['zona_codice', 'parametro']).periodo.shift(1)
cons = mnum[mnum.prec_periodo.notna()].copy()
cons['mese_prec_ok'] = cons.apply(lambda r: (pd.Period(r.periodo, 'M') - pd.Period(r.prec_periodo, 'M')).n == 1, axis=1)
cons = cons[cons.mese_prec_ok]
cons['uguale'] = (cons.valore == cons.prec).astype(int)
rip = cons.groupby('anno').uguale.agg(['sum', 'count'])
rip['quota'] = (rip['sum'] / rip['count']).round(3)
rip.to_csv(os.path.join(CTL, 'valori_uguali_al_mese_precedente_per_anno.csv'), sep=';')
log('quota valori identici al mese precedente (stessa zona, stesso parametro):\n' + rip.to_string())

# Confronto trimestrali 2021 vs media mensile (4 zone, 3 mesi)
tq = a[(a.periodo_tipo == 'trimestre') & (a.anno == 2021) & (a.valore.notna())][['trimestre', 'parametro', 'valore']].rename(columns={'valore': 'trimestrale_citta'})
mq = a[(a.periodo_tipo == 'mese') & (a.anno == 2021) & (a.valore.notna())].groupby(['trimestre', 'parametro']).valore.mean().reset_index().rename(columns={'valore': 'media_mensile_4zone'})
cf = tq.merge(mq, on=['trimestre', 'parametro'], how='outer')
cf['differenza'] = (cf.media_mensile_4zone - cf.trimestrale_citta).round(2)
cf['diff_percentuale'] = (100 * cf.differenza / cf.trimestrale_citta).round(1)
cf.to_csv(os.path.join(CTL, 'confronto_2021_trimestrale_vs_mensile.csv'), sep=';', index=False)
log('confronto 2021 trimestrale vs media mensile: |diff percentuale| mediana %.1f, max %.1f' % (cf.diff_percentuale.abs().median(), cf.diff_percentuale.abs().max()))
log(cf[cf.diff_percentuale.abs() > 15].to_string())

# Valori anomali (outlier robusti) per parametro, solo valori numerici
vv = a[(a.qualita_dato == 'ok')].copy()
med = vv.groupby('parametro').valore.transform('median')
mad = vv.groupby('parametro').valore.transform(lambda x: (x - x.median()).abs().median())
vv['z'] = (vv.valore - med) / (1.4826 * mad.replace(0, float('nan')))
out = vv[vv.z.abs() > 6][['periodo', 'zona_nome', 'parametro', 'valore_testo', 'z']].sort_values('z', key=abs, ascending=False)
out.to_csv(os.path.join(CTL, 'valori_estremi_z_robusto_oltre_6.csv'), sep=';', index=False)
log('valori estremi (|z robusto| > 6):', len(out))
log(out.head(25).to_string())

# valori oltre il limite
no = a[(a.entro_limite_legge == 'no') | (a.entro_valore_consigliato == 'no')]
log('valori fuori dal campo di limite (legge o consigliato):', len(no))
log(no.groupby(['parametro', 'limite_tipo']).size().to_string() if len(no) else 'nessuno')
no[['periodo', 'zona_nome', 'parametro', 'valore_testo', 'limite_testo', 'limite_tipo']].to_csv(
    os.path.join(CTL, 'valori_oltre_limite.csv'), sep=';', index=False)
nd = a[((a.entro_limite_legge == 'n.d.') | (a.entro_valore_consigliato == 'n.d.')) & (a.qualita_dato == 'sotto_soglia')]
log('sotto soglia con soglia > limite (non valutabile):', len(nd))

# caricamenti anomali
ca = a[(a.periodo_tipo == 'mese')].groupby(['periodo', 'zona_codice']).agg(
    car=('data_caricamento', lambda s: ','.join(sorted(set(s)))), prima=('caricamento_prima_del_mese', 'max')).reset_index()
ca = ca[ca.prima == 1]
ca.to_csv(os.path.join(CTL, 'caricamento_prima_della_fine_del_mese.csv'), sep=';', index=False)
log('mesi con data di caricamento precedente alla fine del mese:', ca.periodo.unique().tolist())
log('segnaposto "Lorem ispum" nel campo info: righe', int(a.info_segnaposto.sum()), a[a.info_segnaposto == 1].periodo.unique().tolist())

# --- glossario dai testi "info" (non segnaposto)
glo = {}
for path in sorted(glob.glob(os.path.join(RAW, 'ds*', '*.csv'))):
    nome = os.path.basename(path)
    if 'getdatiqualitaacqua' not in nome.lower():
        continue
    df, _ = csv_testo_in_df(path)
    for _, r in df.iterrows():
        if 'lorem' in r['info'].lower():
            continue
        cod, _, _ = normalizza_param(ripara(r['parametroMisurato'])[0])
        glo.setdefault(cod, set()).add(r['info'].strip())
gl = []
for cod, tt in glo.items():
    gl.append(dict(parametro=cod, n_testi_diversi=len(tt), testo_info=sorted(tt)[0]))
pd.DataFrame(gl).sort_values('parametro').to_csv(os.path.join(OUT, 'parametri_info.csv'), sep=';', index=False)
log('glossario parametri_info.csv: testi diversi per parametro', {g['parametro']: g['n_testi_diversi'] for g in gl})

# --- scrittura finale
ordine = ['periodo_tipo', 'periodo', 'anno', 'mese', 'trimestre', 'data_riferimento', 'zona_codice', 'zona_nome', 'zona_id',
          'parametro', 'parametro_nome', 'gruppo', 'valore', 'unita', 'sotto_soglia', 'soglia', 'qualita_dato',
          'valore_testo', 'nota_valore', 'limite_testo', 'limite_tipo', 'limite_min', 'limite_max', 'entro_limite_legge', 'entro_valore_consigliato',
          'data_caricamento', 'caricamento_prima_del_mese', 'info_segnaposto', 'codifica_riparata',
          'parametro_originale', 'dataset', 'file_origine', 'riga_origine']
a = a.drop(columns=['misurato'])
a = a[ordine].sort_values(['data_riferimento', 'periodo_tipo', 'zona_codice', 'parametro']).reset_index(drop=True)
a.to_csv(os.path.join(OUT, 'analisi.csv'), sep=';', index=False, encoding='utf-8', float_format='%.6g')
log('scritto pulito/analisi.csv', a.shape)

open(os.path.join(OUT, '_log_pulizia.txt'), 'w', encoding='utf-8').write('\n'.join(LOG))
