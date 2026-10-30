"""Legge tutti i semestri delle quotazioni OMI scaricate da Davide e tiene solo il Comune di Milano (codice catastale F205).
Entrata: cartella con i file originali (anche dentro sottocartelle o dentro .zip), nomi tipo
         QI_<numero>_1_<AAAAS>_VALORI.csv e QI_<numero>_1_<AAAAS>_ZONE.csv (S = 1 o 2).
Due formati sono riconosciuti:
  A) dal 2016: separatore ";", riga di titolo ("Quotazioni Immobiliari : Valori di Mercato - Semestre 2018/2 ..."), poi intestazione
     Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona;LinkZona;Cod_Tip;
     Descr_Tipologia;Stato;Stato_prev;Compr_min;Compr_max;Sup_NL_compr;Loc_min;Loc_max;Sup_NL_loc;
  B) prima del 2016 ("tracciato ante 2016": campi separati da "|", nomi tipo PROV, CODISTAT, COMUNE, DESC_COMUNE, FASCIA, ZONA,
     COD_TIP_PREV, TIPOLOGIA, STATO, VALMIN, VALMAX, SUP_NL_MER, LOCMIN, LOCMAX, SUP_NL_LOCAZ). QUESTO FORMATO NON E' STATO
     VISTO SU FILE VERI (solo descritto nel tracciato dell'Agenzia): il lettore e' tollerante sui nomi ma si ferma con un errore
     chiaro se non capisce un file. Non indovina mai il semestre: lo prende dal titolo o dal nome del file.
Uscite in <pulito>/: omi_milano_valori.csv, omi_milano_zone.csv, omi_controlli.txt
Uso: python -I 06_leggi_omi.py <cartella_quotazioni> <cartella_pulito>
"""
import sys, os, io, re, csv, zipfile, collections
import pandas as pd

ALIAS = {
    'prov': ['prov', 'provincia'],
    'comune_cat': ['comune_cat', 'comune', 'comunecat', 'codcom', 'cod_catastale'],
    'comune_amm': ['comune_amm', 'cod_naz', 'codnaz'],
    'comune_istat': ['comune_istat', 'codistat'],
    'comune_desc': ['comune_descrizione', 'desc_comune', 'descrizione_comune'],
    'fascia': ['fascia'],
    'zona': ['zona'],
    'zona_descr': ['zona_descr', 'descrizione_zona', 'descr_zona'],
    'link_zona': ['linkzona', 'link_zona'],
    'cod_tip': ['cod_tip', 'tipologia_cod', 'cod_tipologia'],
    'tipologia': ['descr_tipologia', 'tipologia_descr', 'descrizione_tipologia'],
    'stato': ['stato', 'stato_conservativo'],
    'stato_prev': ['stato_prev', 'stato_prevalente'],
    'compr_min': ['compr_min', 'valmin'],
    'compr_max': ['compr_max', 'valmax'],
    'sup_compr': ['sup_nl_compr', 'sup_nl_mer'],
    'loc_min': ['loc_min', 'locmin'],
    'loc_max': ['loc_max', 'locmax'],
    'sup_loc': ['sup_nl_loc', 'sup_nl_locaz'],
    'cod_tip_prev': ['cod_tip_prev', 'cod_tip_prev'],
    'descr_tip_prev': ['descr_tip_prev'],
    'microzona': ['microzona'],
}
# Nel formato B 'TIPOLOGIA' e' un codice numerico, nel formato A e' 'Cod_Tip' + 'Descr_Tipologia'. Gestito sotto.


def norm(s):
    return re.sub(r'[^a-z0-9_]', '', s.strip().lower().replace(' ', '_'))


def decodifica(b):
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return b.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError('codifica sconosciuta')


def iter_file(root):
    """Restituisce (nome_logico, bytes) per ogni .csv/.txt, anche dentro gli .zip."""
    for dp, dn, fn in os.walk(root):
        for f in sorted(fn):
            p = os.path.join(dp, f)
            if f.lower().endswith('.zip'):
                with zipfile.ZipFile(p) as z:
                    for i in z.infolist():
                        if i.filename.lower().endswith(('.csv', '.txt')):
                            yield f'{f}::{i.filename}', z.read(i)
            elif f.lower().endswith(('.csv', '.txt')):
                with open(p, 'rb') as fh:
                    yield f, fh.read()


def trova_semestre(nome, titolo):
    m = re.search(r'Semestre\s+(\d{4})\s*/\s*([12])', titolo or '', re.I)
    if m:
        return int(m.group(1)), int(m.group(2)), 'titolo'
    m = re.search(r'(?<!\d)(20\d{2})([12])(?!\d)', nome)
    if m:
        return int(m.group(1)), int(m.group(2)), 'nome file'
    m = re.search(r'(20\d{2})[_\-\s]+([12])(?!\d)', nome)
    if m:
        return int(m.group(1)), int(m.group(2)), 'nome file'
    return None


def leggi(nome, b, log):
    testo, enc = decodifica(b)
    righe = testo.splitlines()
    # intestazione = prima riga con almeno 8 separatori e la parola "zona"
    idx = None
    for i, r in enumerate(righe[:15]):
        if max(r.count(';'), r.count('|')) >= 8 and 'zona' in r.lower():
            idx = i
            break
    if idx is None:
        raise SystemExit(f'{nome}: intestazione non trovata nelle prime 15 righe: file non riconosciuto')
    titolo = ' '.join(righe[:idx])
    sep = ';' if righe[idx].count(';') >= righe[idx].count('|') else '|'
    sem = trova_semestre(nome, titolo)
    if sem is None:
        raise SystemExit(f'{nome}: semestre non ricavabile dal titolo ne dal nome del file. Non indovino: rinomina il file con il semestre (es. ..._20182_VALORI.csv).')
    hdr = [norm(h) for h in next(csv.reader([righe[idx]], delimiter=sep))]
    formato = 'A' if 'linkzona' in hdr or 'compr_min' in hdr else 'B'
    col = {}
    for std, als in ALIAS.items():
        for a in als:
            if a in hdr:
                col[std] = hdr.index(a)
                break
    # tipo di tabella
    if 'compr_min' in col:
        tipo = 'VALORI'
    elif 'cod_tip_prev' in col or 'descr_tip_prev' in col:
        tipo = 'ZONE'
    else:
        tipo = 'ZONE'
    if 'VALORI' in nome.upper():
        tipo = 'VALORI'
    elif 'ZONE' in nome.upper() and 'compr_min' not in col:
        tipo = 'ZONE'
    # formato B: TIPOLOGIA e' un codice numerico
    if formato == 'B' and tipo == 'VALORI' and 'tipologia' not in col:
        if 'tipologia' in hdr:
            pass
    out = []
    for r in csv.reader(righe[idx + 1:], delimiter=sep):
        if not r or all(not x.strip() for x in r):
            continue
        d = {k: (r[i].strip() if i < len(r) else '') for k, i in col.items()}
        if formato == 'B' and 'tipologia' in hdr and 'tipologia' not in col:
            d['cod_tip'] = r[hdr.index('tipologia')].strip()
        out.append(d)
    log.append(f'{nome}: formato {formato}, {tipo}, semestre {sem[0]}/{sem[1]} (da {sem[2]}), codifica {enc}, separatore "{sep}", {len(out)} righe')
    return tipo, sem, out


def num(x):
    x = (x or '').strip()
    if x == '':
        return float('nan')
    return float(x.replace('.', '').replace(',', '.')) if (',' in x and '.' in x) else float(x.replace(',', '.'))


def e_milano(d):
    if d.get('comune_cat', '').upper() == 'F205' or d.get('comune_amm', '').upper() == 'F205':
        return True
    return d.get('prov', '').upper() == 'MI' and d.get('comune_desc', '').strip().upper() == 'MILANO'


def main():
    qdir, pulito = sys.argv[1], sys.argv[2]
    os.makedirs(pulito, exist_ok=True)
    log = []
    val, zon = [], []
    visti = collections.Counter()
    for nome, b in iter_file(qdir):
        tipo, (anno, s, _), righe = leggi(nome, b, log)
        sem = f'{anno}-S{s}'
        visti[(sem, tipo)] += 1
        for d in righe:
            if not e_milano(d):
                continue
            d = dict(d)
            d['semestre'], d['anno'], d['sem'], d['file_origine'] = sem, anno, s, nome
            (val if tipo == 'VALORI' else zon).append(d)
    if not val:
        raise SystemExit('nessuna riga di Milano (F205) nei file VALORI: controllare cartella e codici')
    dv = pd.DataFrame(val)
    for c in ('compr_min', 'compr_max', 'loc_min', 'loc_max'):
        dv[c] = dv[c].map(num)
    for c in ('zona_descr',):
        pass
    cols_v = ['semestre', 'anno', 'sem', 'fascia', 'zona', 'link_zona', 'cod_tip', 'tipologia', 'stato', 'stato_prev', 'compr_min',
              'compr_max', 'sup_compr', 'loc_min', 'loc_max', 'sup_loc', 'file_origine']
    for c in cols_v:
        if c not in dv:
            dv[c] = ''
    dv = dv[cols_v].sort_values(['anno', 'sem', 'zona', 'cod_tip', 'stato'])
    dv.to_csv(os.path.join(pulito, 'omi_milano_valori.csv'), index=False)
    if zon:
        dz = pd.DataFrame(zon)
        if 'zona_descr' in dz:
            dz['zona_descr'] = dz['zona_descr'].str.strip("'").str.strip()
        cols_z = ['semestre', 'anno', 'sem', 'fascia', 'zona', 'zona_descr', 'link_zona', 'cod_tip_prev', 'descr_tip_prev', 'stato_prev', 'microzona', 'file_origine']
        for c in cols_z:
            if c not in dz:
                dz[c] = ''
        dz[cols_z].sort_values(['anno', 'sem', 'zona']).to_csv(os.path.join(pulito, 'omi_milano_zone.csv'), index=False)
    else:
        dz = pd.DataFrame(columns=['semestre', 'zona'])

    # ---- controlli (scritti in chiaro, nessuna correzione silenziosa)
    L = ['CONTROLLI SUI FILE OMI LETTI', '']
    L += log
    L.append('')
    sems = sorted(set(dv.semestre))
    attesi = [f'{a}-S{s}' for a in range(int(sems[0][:4]), int(sems[-1][:4]) + 1) for s in (1, 2)
              if f'{a}-S{s}' >= sems[0] and f'{a}-S{s}' <= sems[-1]]
    L.append(f'Semestri con valori: {len(sems)} (da {sems[0]} a {sems[-1]}). Buchi: {sorted(set(attesi) - set(sems)) or "nessuno"}')
    L.append(f'Semestri senza il file ZONE: {sorted(set(sems) - set(dz.semestre)) or "nessuno"}')
    L.append('Righe di Milano per semestre: ' + ', '.join(f'{k}={v}' for k, v in dv.groupby('semestre').size().items()))
    dup = dv.duplicated(['semestre', 'zona', 'cod_tip', 'stato'], keep=False)
    L.append(f'Righe doppie (stesso semestre/zona/tipologia/stato): {int(dup.sum())}')
    inv = dv[(dv.compr_min > dv.compr_max) | (dv.loc_min > dv.loc_max)]
    L.append(f'Righe con minimo > massimo: {len(inv)}')
    z0 = dv[(dv.compr_min <= 0) | (dv.compr_max <= 0)]
    L.append(f'Righe con prezzo di vendita 0 o vuoto: {len(z0)}; con affitto 0 o vuoto: {int(((dv.loc_min.fillna(0) <= 0) | (dv.loc_max.fillna(0) <= 0)).sum())}')
    cz = dv.groupby('semestre').zona.nunique()
    L.append('Numero di zone con valori per semestre: ' + ', '.join(f'{k}={v}' for k, v in cz.items()))
    if len(dz):
        for s in sems:
            a, b = set(dv[dv.semestre == s].zona), set(dz[dz.semestre == s].zona)
            if b and (a - b):
                L.append(f'  {s}: zone nei VALORI ma non nel file ZONE: {sorted(a - b)}')
    L.append('Insiemi di codici zona che cambiano da un semestre al successivo:')
    prev = None
    for s in sems:
        cur = set(dv[dv.semestre == s].zona)
        if prev is not None and cur != prev[1]:
            L.append(f'  {prev[0]} -> {s}: spariti {sorted(prev[1] - cur)[:12]}{"..." if len(prev[1] - cur) > 12 else ""}; nuovi {sorted(cur - prev[1])[:12]}{"..." if len(cur - prev[1]) > 12 else ""}')
        prev = (s, cur)
    open(os.path.join(pulito, 'omi_controlli.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('\n'.join(L[:3]))
    print('scritti omi_milano_valori.csv (%d righe), omi_milano_zone.csv (%d righe), omi_controlli.txt' % (len(dv), len(dz)))


if __name__ == '__main__':
    main()
