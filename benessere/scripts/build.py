"""Fase 1 - Bes dei territori: costruisce la tabella pulita (formato lungo) dall'edizione 2025.
Uso: python -I -X utf8 build.py <benessere assoluto>
Legge:  raw/ed2025/x/Indicatori_per_provincia_sesso_ed.2025.xlsx, Metadati_IT_ed.2025.xlsx
        pulito/polarita_istat_nota2019.csv (da polarita_istat.py), pulito/polarita_istat_aggiunte.csv,
        scripts/alias_polarita.csv
Scrive: pulito/bes_lungo.csv, pulito/indicatori.csv, pulito/controlli_build.json"""
import sys, json, re, pathlib
import pandas as pd

base = pathlib.Path(sys.argv[1])
raw = base / 'raw' / 'ed2025' / 'x'
f_ind = raw / 'Indicatori_per_provincia_sesso_ed.2025.xlsx'
f_met = raw / 'Metadati_IT_ed.2025.xlsx'

CM14 = ['Torino', 'Genova', 'Milano', 'Venezia', 'Bologna', 'Firenze', 'Roma', 'Napoli', 'Bari',
        'Reggio di Calabria', 'Palermo', 'Messina', 'Catania', 'Cagliari']
RIPART = ['Nord', 'Nord-ovest', 'Nord-est', 'Centro', 'Mezzogiorno', 'Sud', 'Isole']
STORICHE = ['Olbia-Tempio', 'Ogliastra', 'Medio Campidano', 'Carbonia-Iglesias']

# ---------------- indicatori (dati) ----------------
df = pd.read_excel(f_ind, dtype=str)
df = df.dropna(subset=['CODICE', 'TERRITORIO'])
yrs = [c for c in df.columns if re.fullmatch(r'V\d{4}', c)]
for c in ['DOMINIO', 'INDICATORE', 'UNITA_MISURA', 'FONTE', 'NOTA']:
    df[c] = df[c].str.replace('\xa0', ' ').str.strip()
geo = df[['TERRITORIO', 'W_GEO']].drop_duplicates()


def tipo_terr(r):
    t, g = r['TERRITORIO'], r['W_GEO']
    if t == 'Italia':
        return 'italia'
    if t in RIPART:
        return 'ripartizione'
    if t in STORICHE:
        return 'provincia_storica'
    if g.endswith('-000'):
        return 'regione'
    return 'provincia'


geo['tipo_territorio'] = geo.apply(tipo_terr, axis=1)
geo['citta_metropolitana'] = geo['TERRITORIO'].isin(CM14)

# ---------------- formato lungo ----------------
m = df.melt(id_vars=['DOMINIO', 'CODICE', 'INDICATORE', 'SESSO', 'TERRITORIO', 'UNITA_MISURA', 'FONTE', 'NOTA'],
            value_vars=yrs, var_name='anno', value_name='grezzo')
m['anno'] = m['anno'].str[1:].astype(int)
g = m['grezzo'].str.replace('\xa0', ' ').str.strip()
g = g.str.replace(r'\s*\(a\)$', '', regex=True)
valore = pd.to_numeric(g.str.replace(',', '.'), errors='coerce')
flag = pd.Series('', index=m.index)
flag[g == '-'] = 'assente_zero_casi'      # ISTAT: linea = fenomeno inesistente o casi non verificati
flag[g == '..'] = 'quasi_zero'            # ISTAT: sotto la meta' dell'ultima cifra
flag[g == '....'] = 'non_disponibile'     # ISTAT: dato non conosciuto
flag[g.isna()] = 'vuoto'
valore[g.isin(['-', '..'])] = 0.0
m['valore'] = valore
m['flag_valore'] = flag
m['valore_grezzo'] = m['grezzo']
m = m.drop(columns='grezzo')
m = m.merge(geo[['TERRITORIO', 'W_GEO', 'tipo_territorio', 'citta_metropolitana']], on='TERRITORIO', how='left')
# si tengono le celle con un valore o con un segno ISTAT (assente/quasi zero); si scartano i 'non disponibile'/vuoti
tieni = m['valore'].notna()
n_scartate = int((~tieni).sum())
m = m[tieni].copy()

# ---------------- metadati ----------------
mt = pd.read_excel(f_met, dtype=str, header=0)
mt = mt.iloc[:, :8]
mt.columns = ['dominio', 'tipo_indicatore', 'num_indicatore', 'codice', 'indicatore_meta', 'definizione', 'unita_meta', 'fonte_ente']
mt['dominio'] = mt['dominio'].ffill()
mt = mt[mt['codice'].str.match(r'^\d\d[A-Z]{3}\d{3}', na=False)].copy()
for c in mt.columns:
    mt[c] = mt[c].astype(str).str.replace('\xa0', ' ').str.replace('\n', ' ').str.strip()

# ---------------- polarita' ----------------
nota = pd.read_csv(base / 'pulito' / 'polarita_istat_nota2019.csv', dtype=str).fillna('')
agg = pd.read_csv(base / 'pulito' / 'polarita_istat_aggiunte.csv', dtype=str).fillna('')
nota_all = pd.concat([nota, agg], ignore_index=True)
alias = pd.read_csv(base / 'scripts' / 'alias_polarita.csv', dtype=str).fillna('')


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower().replace('’', "'")).strip()


nota_all['k'] = nota_all['indicatore_nota_2018'].map(norm)
rows = []
for _, a in alias.iterrows():
    if a['livello'] == 'istat_testo':
        # polarita' ricavata dal testo ISTAT (Report CM 2024) quando dice in modo non ambiguo quale direzione e' favorevole
        rows.append(dict(codice=a['codice'], polarita=a['polarita_esplicita'], livello_polarita='istat_testo',
                         nome_in_nota_istat='', motivo_polarita=a['motivo'], fonte_polarita=a['fonte_testo']))
        continue
    k = norm(a['nome_in_nota_istat'])
    hit = nota_all[nota_all['k'] == k]
    if hit.empty:
        raise SystemExit('NON TROVATO in nota ISTAT: ' + a['nome_in_nota_istat'])
    h = hit.iloc[0]
    p = h['polarita_istat']
    if a['livello'] == 'derivata' and a['codice'] in ('02IST010P', '02IST011P'):
        p = '-' if p == '+' else '+'   # complemento: "non adeguata" invece di "adeguata"
    rows.append(dict(codice=a['codice'], polarita=p, livello_polarita=a['livello'],
                     nome_in_nota_istat=h['indicatore_nota_2018'], motivo_polarita=a['motivo'],
                     fonte_polarita=h['fonte']))
pol = pd.DataFrame(rows)
pol.loc[pol.livello_polarita == 'dubbia', 'polarita'] = ''   # + su un tasso di sofferenza: non usata

chiavi = df[['CODICE', 'DOMINIO', 'INDICATORE', 'UNITA_MISURA', 'FONTE']].drop_duplicates('CODICE').rename(
    columns={'CODICE': 'codice', 'DOMINIO': 'dominio_dati', 'INDICATORE': 'indicatore', 'UNITA_MISURA': 'unita', 'FONTE': 'fonte_dato'})
sol_dati = sorted(set(chiavi['codice']) - set(mt['codice']))
sol_meta = sorted(set(mt['codice']) - set(chiavi['codice']))
ind = chiavi.merge(mt, on='codice', how='left').merge(pol, on='codice', how='left')
ind['livello_polarita'] = ind['livello_polarita'].fillna('assente')
ind['polarita'] = ind['polarita'].fillna('')
ind = ind.sort_values('num_indicatore')
ind.to_csv(base / 'pulito' / 'indicatori.csv', index=False, encoding='utf-8')

m = m.merge(ind[['codice', 'polarita', 'livello_polarita', 'tipo_indicatore', 'dominio']].rename(
    columns={'codice': 'CODICE', 'dominio': 'dominio_meta'}), on='CODICE', how='left')
out = m.rename(columns={'DOMINIO': 'dominio', 'CODICE': 'codice', 'INDICATORE': 'indicatore', 'SESSO': 'sesso',
                        'TERRITORIO': 'territorio', 'UNITA_MISURA': 'unita', 'FONTE': 'fonte_dato',
                        'NOTA': 'nota_edizione', 'W_GEO': 'codice_territorio'})
out['edizione'] = 2025
cols = ['dominio', 'codice', 'indicatore', 'unita', 'polarita', 'livello_polarita', 'tipo_indicatore', 'sesso',
        'territorio', 'codice_territorio', 'tipo_territorio', 'citta_metropolitana', 'anno', 'valore', 'flag_valore',
        'valore_grezzo', 'nota_edizione', 'fonte_dato', 'edizione']
out = out[cols].sort_values(['codice', 'sesso', 'codice_territorio', 'anno'])
out.to_csv(base / 'pulito' / 'bes_lungo.csv', index=False, encoding='utf-8')

ctrl = dict(
    righe_lungo=int(len(out)), celle_scartate_non_disponibili_o_vuote=n_scartate,
    indicatori=int(ind['codice'].nunique()), domini=sorted(ind['dominio'].dropna().unique().tolist()),
    domini_nei_dati=sorted(ind['dominio_dati'].dropna().unique().tolist()),
    codici_nei_dati_non_nei_metadati=sol_dati, codici_nei_metadati_non_nei_dati=sol_meta,
    territori_per_tipo={k: int(v) for k, v in geo.groupby('tipo_territorio').size().items()},
    cm_trovate=sorted(geo[geo.citta_metropolitana].TERRITORIO.tolist()),
    livelli_polarita={k: int(v) for k, v in ind['livello_polarita'].value_counts().items()},
    sesso={k: int(v) for k, v in out['sesso'].value_counts().items()},
    flag={k: int(v) for k, v in out['flag_valore'].value_counts().items()})
json.dump(ctrl, open(base / 'pulito' / 'controlli_build.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(ctrl, ensure_ascii=False, indent=1))
