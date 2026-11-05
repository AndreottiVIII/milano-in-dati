"""Analisi INVALSI per istituto a Milano: primo ciclo e superiori, zone, tipi di scuola, statali e paritarie.
Uso: python -I -X utf8 invalsi_analisi_milano.py <cartella scuole>
Scrive pulito/invalsi_analisi_*.csv e stampa i riepiloghi. Nessun numero va in pagina senza controllo.
"""
import glob, os, sys
import numpy as np
import pandas as pd

B = sys.argv[1]
pd.set_option('display.width', 220, 'display.max_columns', 30, 'display.max_rows', 200, 'display.max_colwidth', 42)
P = os.path.join(B, 'pulito')
pc = pd.read_csv(os.path.join(P, 'invalsi_istituti.csv'), sep=';', encoding='utf-8-sig', dtype={'istituto': str})
sup = pd.read_csv(os.path.join(P, 'invalsi_superiori.csv'), sep=';', encoding='utf-8-sig', dtype={'istituto': str})
par_f = os.path.join(P, 'invalsi_paritarie.csv')
par = pd.read_csv(par_f, sep=';', encoding='utf-8-sig', dtype={'istituto': str}) if os.path.exists(par_f) else pd.DataFrame()
# anagrafe: nome, tipo, quartiere (dai plessi)
ms = pd.read_csv(os.path.join(P, 'miur_scuole_anno.csv'), sep=';', encoding='utf-8-sig', dtype=str)
ms = ms[ms.anno_scolastico == ms.anno_scolastico.max()]
g = pd.read_csv(sorted(glob.glob(os.path.join(B, 'raw', 'miur', 'SCUANAGRAFESTAT*.csv')))[-1], dtype=str, keep_default_na=False)
g = g[g.CODICECOMUNESCUOLA == 'F205']
nome = g.drop_duplicates('CODICEISTITUTORIFERIMENTO').set_index('CODICEISTITUTORIFERIMENTO').DENOMINAZIONEISTITUTORIFERIMENTO.to_dict()
pl = g[['CODICEISTITUTORIFERIMENTO', 'CODICESCUOLA']].merge(ms[['codice_mecc', 'nil', 'iscritti', 'cittadinanza_non_italiana']], left_on='CODICESCUOLA', right_on='codice_mecc', how='left')
for c in ('iscritti', 'cittadinanza_non_italiana'):
    pl[c] = pd.to_numeric(pl[c], errors='coerce')
def zona(x):
    x = x.dropna(subset=['nil', 'iscritti'])
    if x.empty:
        return None
    return x.groupby('nil').iscritti.sum().idxmax()
nil = pl.groupby('CODICEISTITUTORIFERIMENTO').apply(zona).to_dict()
quota = pl.groupby('CODICEISTITUTORIFERIMENTO')[['iscritti', 'cittadinanza_non_italiana']].sum()
quota['q'] = quota.cittadinanza_non_italiana / quota.iscritti * 100
# municipio del quartiere
geo = {}
try:
    import json
    gj = json.load(open(os.path.join(B, '..', 'docs', 'scuole', 'data', 'nil.geojson'), encoding='utf-8'))
    print('campi nil', list(gj['features'][0]['properties'].keys())[:12])
except Exception as e:
    print('nil', e)


def num(d):
    d = d.copy()
    for c in ('punteggio', 'lombardia', 'diff_escs', 'partecipazione'):
        d[c] = pd.to_numeric(d[c], errors='coerce')
    d['scarto'] = d.punteggio - d.lombardia
    return d


pc = num(pc)
pc['tipo'] = 'primo ciclo'
pc['nome'] = pc.istituto.map(nome)
pc['nil'] = pc.istituto.map(nil)
pc['q'] = pc.istituto.map(quota.q)
sup = num(sup)
sup['nome'] = sup.istituto.map(nome)
sup['nil'] = sup.istituto.map(nil)
sup['q'] = sup.istituto.map(quota.q)
def tipo(g_):
    g_ = g_.lower()
    if g_.startswith('licei scientifici, classici') or g_.startswith('licei scientifici -'):
        return 'licei scientifici, classici, linguistici'
    if g_.startswith('altri licei'):
        return 'altri licei'
    if 'tecnici' in g_:
        return 'tecnici'
    if 'professional' in g_:
        return 'professionali'
    return g_[:30]
sup['tipo'] = sup.grado.map(tipo)
sup['classe'] = np.where(sup.grado.str.contains('quinte'), 'quinta', 'seconda')

print('\n=== RACCOLTA ===')
print('primo ciclo', pc.istituto.nunique(), '| superiori', sup.istituto.nunique(), '| righe', len(pc), len(sup))
print(sup.groupby(['tipo', 'classe']).istituto.nunique().to_string())
print(sup.materia.value_counts().to_dict())

print('\n=== PRIMO CICLO, 5a primaria e 3a media, rispetto alla Lombardia ===')
for gr, mat in (('Scuola primaria - classi quinte', 'Italiano'), ('Scuola primaria - classi quinte', 'Matematica'), ('Scuola secondaria di primo grado - classi terze', 'Italiano'), ('Scuola secondaria di primo grado - classi terze', 'Matematica')):
    x = pc[(pc.grado == gr) & (pc.materia == mat)].dropna(subset=['scarto'])
    print(gr[:32], mat, 'n', len(x), 'media scarto %.1f' % x.scarto.mean(), 'quanti sopra la Lombardia', (x.scarto > 0).sum(), '| media diff contesto %.1f' % x.diff_escs.mean())
print('\n3a media, italiano: i primi e gli ultimi per scarto')
x = pc[(pc.grado == 'Scuola secondaria di primo grado - classi terze') & (pc.materia == 'Italiano')].dropna(subset=['scarto']).sort_values('scarto', ascending=False)
print(x[['nome', 'nil', 'punteggio', 'lombardia', 'scarto', 'diff_escs', 'q']].round(1).head(8).to_string(index=False))
print(x[['nome', 'nil', 'punteggio', 'lombardia', 'scarto', 'diff_escs', 'q']].round(1).tail(8).to_string(index=False))

print('\n=== ZONE (primo ciclo, 3a media e 5a primaria insieme, media degli scarti per quartiere con almeno 2 prove) ===')
z = pc[pc.grado.isin(['Scuola primaria - classi quinte', 'Scuola secondaria di primo grado - classi terze'])].dropna(subset=['scarto'])
# scala diversa tra primaria e media: si usa lo scarto standardizzato dentro ogni prova
z = z.assign(zs=z.groupby(['grado', 'materia']).scarto.transform(lambda s: (s - s.mean()) / s.std()), ze=z.groupby(['grado', 'materia']).diff_escs.transform(lambda s: (s - s.mean()) / s.std()))
zq = z.groupby('nil').agg(istituti=('istituto', 'nunique'), prove=('zs', 'size'), z_punteggio=('zs', 'mean'), z_contesto=('ze', 'mean')).sort_values('z_punteggio', ascending=False)
print(zq.round(2).to_string())
zq.round(3).to_csv(os.path.join(P, 'invalsi_analisi_zone.csv'), sep=';', encoding='utf-8-sig')

print('\n=== SUPERIORI per tipo, rispetto alla Lombardia dello stesso tipo ===')
for mat in ('Italiano', 'Matematica'):
    for cl in ('seconda', 'quinta'):
        x = sup[(sup.materia == mat) & (sup.classe == cl)].dropna(subset=['scarto'])
        print(mat, cl)
        print(x.groupby('tipo').agg(n=('istituto', 'nunique'), scarto=('scarto', 'mean'), contesto=('diff_escs', 'mean'), sopra=('scarto', lambda s: (s > 0).sum())).round(1).to_string())
print('\nLicei scientifici, classici, linguistici: quinta, italiano e matematica')
L = sup[(sup.classe == 'quinta') & sup.materia.isin(['Italiano', 'Matematica']) & sup.tipo.isin(['licei scientifici, classici, linguistici'])].dropna(subset=['scarto'])
ita = L[L.materia == 'Italiano'].sort_values('scarto', ascending=False)
print(ita[['nome', 'nil', 'punteggio', 'lombardia', 'scarto', 'diff_escs', 'q']].round(1).to_string(index=False))
sup.to_csv(os.path.join(P, 'invalsi_analisi_superiori.csv'), sep=';', index=False, encoding='utf-8-sig')

if len(par):
    par = num(par)
    print('\n=== PARITARIE: con punteggi', par.istituto.nunique(), '===')
    par['classe'] = np.where(par.grado.str.contains('quinte'), 'quinta', np.where(par.grado.str.contains('seconde'), 'seconda', 'terza'))
    print(par.groupby(['tipo', 'grado', 'materia']).agg(n=('istituto', 'nunique'), scarto=('scarto', 'mean'), contesto=('diff_escs', 'mean'), part=('partecipazione', 'mean')).round(1).to_string())
    st = pd.concat([pc.assign(grado_=pc.grado), sup.assign(grado_=sup.grado)])
    print('\nStatali, per confronto')
    print(st[st.materia.isin(['Italiano', 'Matematica'])].groupby(['grado_', 'materia']).agg(n=('istituto', 'nunique'), scarto=('scarto', 'mean'), contesto=('diff_escs', 'mean'), part=('partecipazione', 'mean')).round(1).to_string())
