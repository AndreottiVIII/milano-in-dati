import sys, csv, os, time, hashlib, json, zipfile, requests
inv, rawdir, logcsv = sys.argv[1:4]
R = list(csv.DictReader(open(inv, encoding='utf-8-sig')))
def want(r):
    f = r['format']
    if f == 'CSV': return True
    if f == 'SHP': return True
    if f == 'GeoJSON' and r['kind']=='collegi_geo': return True
    return False
sel = [r for r in R if want(r)]
print(len(sel), 'resources to download', flush=True)
out = []
sess = requests.Session()
sess.headers['User-Agent'] = 'milano-in-dati-research/1.0 (open data download)'
for i, r in enumerate(sel):
    d = os.path.join(rawdir, r['dataset'][:80])
    os.makedirs(d, exist_ok=True)
    fn = os.path.basename(r['url'].split('?')[0]) or r['resource_name']
    fn = r['resource_name'] if r['resource_name'] and '.' in r['resource_name'] else fn
    path = os.path.join(d, fn)
    status = 'ok'; err = ''
    if not os.path.exists(path):
        for attempt in range(3):
            try:
                resp = sess.get(r['url'], timeout=180)
                if resp.status_code == 200:
                    open(path, 'wb').write(resp.content); break
                err = 'HTTP %s' % resp.status_code
            except Exception as e:
                err = repr(e)
            time.sleep(3)
        else:
            status = 'FAIL'
        time.sleep(0.4)
    size = os.path.getsize(path) if os.path.exists(path) else 0
    sha = hashlib.sha256(open(path,'rb').read()).hexdigest() if size else ''
    members = ''
    if status=='ok' and zipfile.is_zipfile(path):
        sub = os.path.join(d, 'unzipped_' + os.path.splitext(fn)[0][:40])
        os.makedirs(sub, exist_ok=True)
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            for m in z.infolist():
                # safe extraction: only flat file names
                nm = os.path.basename(m.filename)
                if not nm: continue
                with z.open(m) as src, open(os.path.join(sub, nm), 'wb') as dst:
                    dst.write(src.read())
            members = ';'.join(names)
    out.append(dict(dataset=r['dataset'], resource_id=r['resource_id'], file=os.path.relpath(path, rawdir), size_bytes=size, sha256=sha, declared_size=r['size_bytes'], zip_members=members, status=status, error=err))
    if i % 25 == 0: print(i, r['dataset'][:50], status, size, flush=True)
with open(logcsv, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('done', sum(1 for o in out if o['status']!='ok'), 'failed', flush=True)
