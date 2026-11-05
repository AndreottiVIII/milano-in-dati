import sys, urllib.request, time
url, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0", "Accept": "application/xml"})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=170)
    data = r.read()
    open(out, "wb").write(data)
    print(r.status, len(data), round(time.time()-t,1), r.headers.get("Content-Type"))
except Exception as e:
    print("ERR", e, round(time.time()-t,1))
