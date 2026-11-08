"""Dati in più per la pagina rifatta (bozza v2): nomi corti dei progetti, i 14 progetti PINQuA divisi per tipo di opera,
flussi Legge solo i file già in docs/fondi-quartieri/data/ e scrive fondi_v2.json.
Uso: python -I -X utf8 dati_pagina_v2.py <percorso assoluto di milano-in-dati>"""
import json, sys, os
R = sys.argv[1]
D = os.path.join(R, 'docs', 'fondi-quartieri', 'data')
P = json.load(open(os.path.join(D, 'progetti.json'), encoding='utf-8'))
S = json.load(open(os.path.join(D, 'riepilogo.json'), encoding='utf-8'))

NOMI = {  # nomi corti per i progetti più grandi (titoli come nella fonte sono lunghi e in maiuscolo)
 'J42C21002820004': 'Via dei Giaggioli (Lorenteggio)', 'I49J21000550006': 'Gratosoglio: palazzi ALER',
 'H41H14000130009': 'Lorenteggio: palazzi ERP', 'B47H21007240004': 'Via San Romanello 34',
 'B44F18000180004': 'Bando periferie', 'B44E21012970001': 'Via Pianell 15',
 'B43J18000130004': 'Biblioteca Lorenteggio', 'B47H21004490004': 'San Siro: strade',
 'B44E21012980001': 'Via Newton 15 (caserma)', 'B47H21008570001': 'Niguarda: palazzi ERP',
 'B47H21008580001': 'San Siro: palazzi ERP', 'B41H17000140001': 'Spazi e servizi alle persone',
 'B47H21004480004': 'Niguarda: strade', 'B41H17000030004': 'Hub ospitalità temporanea',
 'I49F18000680001': 'Ponte Lambro: spazio di coesione', 'I42H19000260002': 'Bovisasca: palazzo ALER',
}
def prog(p):
    t = p['programma']
    for a, b in [("PNRR - PINQuA (qualita' dell'abitare)", 'PNRR · PINQuA'), ('PNRR - Housing First e stazioni di posta', 'PNRR · Housing First'),
                 ('POC LOMBARDIA', 'POC Lombardia'), ('PN FESR FSE+ METRO PLUS E CITTÀ MEDIE SUD', 'PN Metro Plus'),
                 ("PON FESR FSE CITTA' METROPOLITANE", 'PON Metro'), ('PSC CITTÀ METROPOLITANA DI MILANO', 'PSC Città metropolitana'),
                 ('POC METRO', 'POC Metro'), ('PR FSE+ LOMBARDIA', 'FSE+ Lombardia'), ("PON FESR FSE LEGALITA'", 'PON Legalità'),
                 ('POR FESR LOMBARDIA', 'POR FESR Lombardia'), ('PN FESR FSE+ SCUOLA E COMPETENZE', 'PN Scuola')]:
        if t == a: return b
    return t
def ente(p):
    return {'Citta metropolitana di Milano': 'Città metropolitana', 'Altro/non indicato': 'Scuole e altri'}.get(p['tipo_ente'], p['tipo_ente'])
def nome(p):
    if p['cup'] in NOMI: return NOMI[p['cup']]
    t = p['titolo'].strip()
    if t.lower().startswith('housing first'): return 'Housing First'
    t = t.capitalize()
    return t[:34] + ('…' if len(t) > 34 else '')
nuc = [p for p in P if p['nucleo'] == 1 and not p['fonte'].startswith('PNC')]
assert len(nuc) == S['totali']['nucleo_progetti'], len(nuc)
assert abs(sum(p['importo'] for p in nuc) - S['totali']['nucleo_finanziato']) < 10
out = {'progetti': [], 'pinqua': []}
for p in sorted(nuc, key=lambda p: -p['importo']):
    out['progetti'].append({'cup': p['cup'], 'n': nome(p), 'titolo': p['titolo'][:140], 'prog': prog(p), 'ente': ente(p), 'amb': p['ambito'],
        'amb_txt': p['ambito_txt'], 'q': p['quartiere'], 'imp': round(p['importo']), 'pag': round(p['pagato'] or 0), 'fine': p['fine_prevista_iso'],
        'fase': (p['fase'] or '').split(' (')[0].lower(), 'rit': p['ritardo_giorni'], 'stato': p['stato']})
# PINQuA: tipo di opera
TIPO = {'J42C21002820004': 'case', 'I49J21000550006': 'case', 'B44E21012970001': 'case', 'B47H21008570001': 'case', 'B47H21008580001': 'case',
        'J49J21000090004': 'm4', 'J49J21000080004': 'm4', 'J49J21000100004': 'm4', 'B44E07000120004': 'tram', 'B43J18000130004': 'bibl',
        'B44E21012980001': 'caserma', 'B47H21004490004': 'strade', 'B47H21004480004': 'strade', 'B47H20011270004': 'ciclab'}
NT = {'case': 'Edifici di case popolari', 'm4': 'Strade sopra la metropolitana M4', 'tram': 'Tram 90-91', 'bibl': 'Biblioteca', 'caserma': 'Caserma di via Newton',
      'strade': 'Strade e piazze nei quartieri', 'ciclab': 'Pista ciclabile'}
pin = [p for p in P if 'PINQuA' in p['programma']]
assert len(pin) == 14
for p in pin:
    out['pinqua'].append({'cup': p['cup'], 'tipo': TIPO[p['cup']], 'tipo_txt': NT[TIPO[p['cup']]], 'n': nome(p), 'imp': round(p['importo']), 'pag': round(p['pagato'] or 0)})
tot = sum(x['imp'] for x in out['pinqua'])
cas = sum(x['imp'] for x in out['pinqua'] if x['tipo'] == 'case')
assert abs(tot - S['avanzamento_pnrr']['PINQuA']['finanziato']) < 5, tot
assert abs(cas - S['pinqua_split']['case_popolari_e_abitare']) < 5, cas
json.dump(out, open(os.path.join(D, 'fondi_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(out['progetti']), tot, cas)
