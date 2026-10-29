"""Fase 4 (incidenti), passo 1: legge i microdati Lombardia/ISTAT di Milano 2010-2024 in una tabella unica e normalizza i campi.
Uso: python -I f4_carica.py <ABS strand> -> out/f4_incidenti_raw.pkl"""
import sys, glob, json, pickle
import pandas as pd
S = sys.argv[1]
rows = []
for f in sorted(glob.glob(S + '/raw/incidenti/lombardia_microdati/*.json')):
    rows += json.load(open(f, encoding='utf-8'))
df = pd.DataFrame(rows)
def num(c, default=0):
    return pd.to_numeric(df[c], errors='coerce').fillna(default).astype(int) if c in df else default
out = pd.DataFrame({'anno': num('anno'), 'mese': num('mese'),
                    'va': num('tipo_veicolo_a', -1), 'vb': num('tipo_veicolo_b', -1), 'vc': num('tipo_veicolo_c', -1),
                    'eta_a': num('eta_conducente_a', -1), 'eta_b': num('eta_conducente_b', -1),
                    'natura': num('natura_incidente', -1), 'interse': num('intersezione_nonintersezione', -1),
                    'tipo_strada': num('tipo_strada', -1), 'loc': num('localizzazione_incidente', -1),
                    'ped_morti': num('n_pedoni_morti'), 'ped_feriti': num('n_pedoni_feriti'),
                    'morti24': num('tot_morti_a_24ore_incidente'), 'morti30': num('tot_morti_a_30gg_incidente'),
                    'feriti': num('totale_feriti'),
                    'nome_strada': df.nome_strada.fillna('').astype(str).str.strip()})
print(len(out), out.anno.value_counts().sort_index().to_dict())
pickle.dump(out, open(S + '/out/f4_incidenti_raw.pkl', 'wb'), protocol=4)
