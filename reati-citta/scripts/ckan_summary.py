import json,glob,sys,os
seen={}
for f in sorted(glob.glob(os.path.join(sys.argv[1],'ck_*.json'))):
    try: d=json.load(open(f,encoding='utf-8'))
    except Exception as e: print(f,'ERR',e); continue
    r=d['result']; print('##',os.path.basename(f),r['count'])
    for p in r['results']:
        if p['name'] in seen: continue
        seen[p['name']]=1
        print(' ',p['name'][:40],'|',p['title'][:80],'|',p.get('metadata_modified','')[:10])
