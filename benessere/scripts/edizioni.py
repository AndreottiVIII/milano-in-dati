"""Catalogo degli indicatori in ciascuna edizione 2020-2025 (file Indicatori_per_provincia_sesso*.xlsx) e
confronto Milano ultimo anno per edizione. Serve a vedere quali indicatori sono usciti/entrati e come cambiano i valori.
(Le edizioni 2018 e 2019 hanno tavole in altro formato - un file per dominio e per regione - e non sono lette qui.)
Uso: python -I -X utf8 edizioni.py <benessere assoluto>
Scrive: pulito/indicatori_per_edizione.csv, pulito/milano_per_edizione.csv"""
import sys, re, pathlib, glob, warnings
import pandas as pd
warnings.filterwarnings('ignore')
base = pathlib.Path(sys.argv[1]); R = base / 'raw'; P = base / 'pulito'
files = {2020: R / 'ed2020/x/Bes/Indicatori_per_provincia_sesso.xlsx',
         2021: R / 'ed2021/x/Bes_dei_territori_edizione_092021/Indicatori_per_provincia_sesso_ed.2021.xlsx',
         2022: R / 'ed2022/x/Indicatori_per_provincia_sesso_ed.2022.xlsx',
         2023: R / 'ed2023/x/Indicatori_per_provincia_sesso_ed.2023.xlsx.xlsx',
         2024: R / 'ed2024/x/Indicatori_per_provincia_sesso_ed.2024_EC_18122024.xlsx',
         2025: R / 'ed2025/x/Indicatori_per_provincia_sesso_ed.2025.xlsx'}


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', str(s).lower().replace('’', "'")).strip()


cat, mil = [], []
for ed, f in files.items():
    d = pd.read_excel(f, dtype=str, nrows=20000)
    d.columns = [c.strip() for c in d.columns]
    # l'edizione 2022 non ha CODICE e ha le colonne SESSO/TERRITORIO spostate: si legge per nome colonna dove possibile
    if 'CODICE' not in d.columns:
        d['CODICE'] = ''
    d = d.dropna(subset=['INDICATORE'])
    yc = [c for c in d.columns if re.fullmatch(r'V_?\d{4}', c)]
    for (cod, nome, dom), g in d.groupby(['CODICE', 'INDICATORE', 'DOMINIO']):
        cat.append(dict(edizione=ed, codice=cod, indicatore=nome, dominio=dom, nome_norm=norm(nome)))
    # Milano, sesso totale, ultimo anno con valore
    sx = 'SESSO' if 'SESSO' in d.columns else None
    mi = d[(d.TERRITORIO == 'Milano') & (d[sx] == 'Totale')] if sx and (d[sx] == 'Totale').any() else d[d.TERRITORIO == 'Milano']
    for _, r in mi.iterrows():
        for c in reversed(yc):
            v = pd.to_numeric(str(r[c]).replace(',', '.'), errors='coerce')
            if pd.notna(v):
                mil.append(dict(edizione=ed, codice=r['CODICE'], indicatore=r['INDICATORE'], nome_norm=norm(r['INDICATORE']),
                                anno_ultimo=int(c[-4:]), valore_milano=v)); break
cat = pd.DataFrame(cat)
w = cat.pivot_table(index='nome_norm', columns='edizione', values='codice', aggfunc='first').notna().astype(int)
nomi = cat.sort_values('edizione').groupby('nome_norm').agg(indicatore=('indicatore', 'last'), dominio=('dominio', 'last'))
out = nomi.join(w)
out['n_edizioni'] = w.sum(axis=1)
out = out.reset_index(drop=True)
out.to_csv(P / 'indicatori_per_edizione.csv', index=False, encoding='utf-8')
m = pd.DataFrame(mil)
mw = m.pivot_table(index='nome_norm', columns='edizione', values='valore_milano', aggfunc='first')
aw = m.pivot_table(index='nome_norm', columns='edizione', values='anno_ultimo', aggfunc='first').add_prefix('anno_')
mm = nomi.join(mw).join(aw).reset_index(drop=True)
mm.to_csv(P / 'milano_per_edizione.csv', index=False, encoding='utf-8')
print(cat.groupby('edizione').size().to_dict())
print('indicatori (nomi normalizzati) apparsi in almeno una edizione:', len(out))
print('presenti in 2025:', int(out[2025].sum()), '; solo nelle edizioni precedenti:', int(((out[2025] == 0)).sum()))
