import sys, glob, json, pandas as pd
indir, qfile, out_csv = sys.argv[1:4]
SEX = {'Q6581072':'donna','Q6581097':'uomo','Q1052281':'donna trans','Q2449503':'uomo trans','Q1097630':'intersex','Q48270':'non binario'}
rows = {}
for f in sorted(glob.glob(indir + '/batch_*.json')):
    for b in json.load(open(f, encoding='utf8'))['results']['bindings']:
        g = lambda k: b.get(k, {}).get('value', '')
        q = g('item').rsplit('/', 1)[-1]
        sexq = [s.rsplit('/',1)[-1] for s in g('sexs').split('|') if s]
        p31q = [s.rsplit('/',1)[-1] for s in g('p31s').split('|') if s]
        rows[q] = dict(qid=q, label=g('itemLabel'), descrizione=g('itemDescription'), p31=';'.join(p31q), p31_en=g('p31Ls'),
            umano=int('Q5' in p31q or 'Q21070568' in p31q), esistenza_discussa=int('Q21070568' in p31q), sesso_qid=';'.join(sexq), sesso=';'.join(SEX.get(s, s) for s in sexq),
            professioni_it=g('occs'), anno_nascita=g('birth'), anno_morte=g('death'), cittadinanza_qid=';'.join(s.rsplit('/',1)[-1] for s in g('cits').split('|') if s))
df = pd.DataFrame(rows.values())
asked = [x.strip() for x in open(qfile) if x.strip()]
missing = [q for q in asked if q not in rows]
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(len(asked), 'QID chiesti;', len(df), 'risposte; mancanti', len(missing), missing[:20])
print('label uguale al QID (senza etichetta it/en)', int((df.label==df.qid).sum()), 'esistenza discussa', int(df.esistenza_discussa.sum()))
print('umani', int(df.umano.sum()), '| sesso noto tra umani', int(((df.umano==1)&(df.sesso!='')).sum()))
print(df[df.umano==1].sesso.value_counts().to_dict())
print(df.p31_en.str.split('|').explode().value_counts().head(25).to_dict())
