"""Controlli di coerenza (fase 1).
 1) Milano: edizione 2025 vs edizione 2024 (stesso anno): quanti valori cambiano (revisioni ISTAT).
 2) Milano e CM: edizione 2025 vs Appendice del Report ISTAT sulle citta' metropolitane 2024 (file indipendente di ISTAT, stessa base dati ed. 2024).
Uso: python -I -X utf8 controlli.py <benessere assoluto>"""
import sys, json, re, pathlib, warnings
import pandas as pd
import openpyxl
warnings.filterwarnings('ignore')
base = pathlib.Path(sys.argv[1]); P = base / 'pulito'; R = base / 'raw'
L = pd.read_csv(P / 'bes_lungo.csv', low_memory=False)
L = L[(L.sesso == 'Totale')]

# 1) edizione 2024
f24 = R / 'ed2024' / 'x' / 'Indicatori_per_provincia_sesso_ed.2024_EC_18122024.xlsx'
d24 = pd.read_excel(f24, dtype=str, nrows=20000)
d24 = d24.dropna(subset=['CODICE'])
d24 = d24[d24.SESSO == 'Totale']
yrs = [c for c in d24.columns if re.fullmatch(r'V\d{4}', c)]
m = d24.melt(id_vars=['CODICE', 'TERRITORIO'], value_vars=yrs, var_name='anno', value_name='v')
m['anno'] = m['anno'].str[1:].astype(int)
m['v24'] = pd.to_numeric(m['v'].str.replace(',', '.'), errors='coerce')
m = m.dropna(subset=['v24'])
# i codici cambiano a volte tra edizioni (suffisso -N22/-N25): si confronta sul prefisso di 8 caratteri
m['cod8'] = m['CODICE'].str.split('-').str[0]
L8 = L.assign(cod8=L.codice.str.split('-').str[0])
x = L8[['cod8', 'territorio', 'anno', 'valore']].merge(m[['cod8', 'TERRITORIO', 'anno', 'v24']].rename(columns={'TERRITORIO': 'territorio'}),
                                                    on=['cod8', 'territorio', 'anno'], how='inner')
x['diff'] = (x.valore - x.v24).abs()
tot = len(x); uguali = int((x['diff'] < 1e-9).sum())
mi = x[x.territorio == 'Milano']
res = dict(confronto_ed2024_ed2025=dict(celle_confrontate=tot, uguali=uguali, quota_uguali=round(uguali / tot, 4),
                                        milano_celle=int(len(mi)), milano_uguali=int((mi['diff'] < 1e-9).sum())))
rev = mi[mi['diff'] >= 1e-9].groupby('cod8').agg(n=('anno', 'size'), anni=('anno', lambda s: sorted(s.tolist())[:8]), max_diff=('diff', 'max')).reset_index()
rev.to_csv(P / 'controllo_revisioni_milano_ed24_ed25.csv', index=False)

# 2) Appendice del Report CM 2024
f = R / 'report_cm2024' / 'Appendice_citta_metropolitane_VSP.xlsx'
wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
conf = []
for ws in wb.worksheets:
    rows = list(ws.iter_rows(values_only=True))
    hdr = None
    for i, r in enumerate(rows):
        if r and len(r) > 2 and isinstance(r[2], str) and re.fullmatch(r'\d\d-\d\d\s?', r[2]):
            hdr = i; break
    if hdr is None:
        continue
    cods = rows[hdr]; years = rows[hdr + 3]
    for r in rows[hdr + 4:]:
        if not r or r[1] not in ('Milano', 'Torino', 'Roma', 'Napoli'):
            continue
        for j in range(2, len(cods)):
            c = cods[j]
            if isinstance(c, str) and re.fullmatch(r'\d\d-\d\d\s?', c):
                for k in (0, 1):   # primo e secondo anno
                    y = years[j + k]; v = r[j + k]
                    ym = re.match(r'(\d{4})', str(y)) if y is not None else None
                    if ym and isinstance(v, (int, float)):
                        conf.append(dict(num=c.strip(), territorio=r[1], anno=int(ym.group(1)), v_appendice=float(v)))
ap = pd.DataFrame(conf)
ind = pd.read_csv(P / 'indicatori.csv', dtype=str)[['codice', 'num_indicatore']]
L2 = L.merge(ind, on='codice')
z = ap.merge(L2[['num_indicatore', 'territorio', 'anno', 'valore', 'codice']], left_on=['num', 'territorio', 'anno'],
             right_on=['num_indicatore', 'territorio', 'anno'], how='inner')
z['diff'] = (z.valore - z.v_appendice).abs()
z['rel'] = z['diff'] / z.v_appendice.abs().replace(0, 1)
res['confronto_appendice_report_cm2024'] = dict(celle_confrontate=int(len(z)), entro_arrotondamento_o_0_5pct=int(((z.rel < 0.005) | (z['diff'] <= 0.0501)).sum()),
                                                  esempi_diversi=z[(z.rel >= 0.005) & (z['diff'] > 0.0501)][['codice', 'territorio', 'anno', 'valore', 'v_appendice']].head(12).to_dict('records'))
json.dump(res, open(P / 'controlli_confronto.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
print(json.dumps(res, ensure_ascii=False, indent=1, default=str))
