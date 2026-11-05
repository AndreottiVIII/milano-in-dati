"""Prova: i campioni INVALSI di alunni si agganciano al file delle classi (gestione, capoluogo, sistema locale)?"""
import csv, glob, os, sys, collections as C
import pandas as pd
B = sys.argv[1]
info = pd.read_csv(os.path.join(B, 'raw', 'invalsi_aperti', 'Info_territoriali_classi_anonima_agg_2025.csv'), dtype=str, sep=None, engine='python', encoding='latin-1')
print(open(os.path.join(B, 'raw', 'invalsi_aperti', 'Tracciato_Info_territoriali_classi_anonima.csv'), encoding='latin-1').read()[:900])
print(info.columns.tolist(), len(info))
print(info.groupby(['anno', 'grado']).size().tail(12).to_dict())
mi = info[(info.DEN_SLL_2011_2018.str.upper() == 'MILANO') & (info.capoluogo == '1')]
print('classi SLL Milano capoluogo', len(mi))
print(mi.groupby(['anno', 'grado', 'nome_gestione']).size().tail(24).to_string())
for d in sorted(glob.glob(os.path.join(B, 'raw', 'invalsi_campione', 'g*'))):
    fs = [f for f in glob.glob(os.path.join(d, '*')) if os.path.isfile(f)]
    print(os.path.basename(d), [os.path.basename(f) for f in fs][:4])
    for f in fs:
        if f.lower().endswith(('.csv', '.txt')):
            t = pd.read_csv(f, dtype=str, sep=None, engine='python', nrows=5, encoding='latin-1')
            print('  ', list(t.columns)[:16])
            cc = [c for c in t.columns if 'class' in c.lower()]
            print('   colonne classe', cc, t[cc].iloc[0].tolist() if cc else '')
            break
