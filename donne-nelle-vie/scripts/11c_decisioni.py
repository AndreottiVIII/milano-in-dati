"""Fase 2, passo 2c: applica le decisioni di Davide sui casi dubbi (decisioni_davide.csv) alle tabelle classificate.
Da eseguire dopo 11b_arricchisci e prima di 12_percentuali. Modifica i file in place.
Uso: python -I 11c_decisioni.py decisioni_davide.csv strade_classificate_v2.csv strade_classificate_arricchite_v2.csv
colonna persona (facoltativa): sostituisce la persona proposta da Wikidata
decisione: donna | uomo | luogo (non persona) | sconosciuto (persona non identificata)"""
import sys
import pandas as pd

dec_csv, *tabelle = sys.argv[1:]
D = pd.read_csv(dec_csv, sep=';', dtype=str, encoding='utf-8-sig').fillna('')
CAT = {'donna': 'donna', 'uomo': 'uomo', 'luogo': 'non_persona', 'sconosciuto': 'sconosciuto'}
for t in tabelle:
    d = pd.read_csv(t, dtype=str).fillna('')
    trovate = 0
    for r in D.itertuples():
        m = d.nome == r.nome
        if not m.any():
            print('non trovata:', r.nome)
            continue
        trovate += int(m.sum())
        d.loc[m, 'categoria'] = CAT[r.decisione]
        d.loc[m, 'confidenza'] = 'sicuro' if r.decisione in ('donna', 'uomo', 'luogo') else 'nessuno'
        d.loc[m, 'fonte'] = 'decisione Davide 2026-10-29'
        d.loc[m, 'motivo'] = r.nota
        d.loc[m, 'santa'] = r.santa
        if r.decisione != 'donna':
            d.loc[m, ['qid', 'persona', 'nascita', 'morte', 'descrizione', 'professioni']] = ''
        if getattr(r, 'persona', ''):
            d.loc[m, ['qid', 'nascita', 'morte', 'descrizione', 'professioni']] = ''
            d.loc[m, 'persona'] = r.persona
    d.to_csv(t, index=False, encoding='utf-8')
    print(t, 'righe aggiornate:', trovate)
