import sys, urllib.request, time
url, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ricerca open data; davide.caniatti@gmail.com)", "Accept": "application/xml"})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=170)
    data = r.read()
    open(out, "wb").write(data)
    print(r.status, len(data), round(time.time()-t,1), r.headers.get("Content-Type"))
except Exception as e:
    print("ERR", e, round(time.time()-t,1))
