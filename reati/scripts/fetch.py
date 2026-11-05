import sys, urllib.request, time
url, out = sys.argv[1], sys.argv[2]
acc = sys.argv[3] if len(sys.argv)>3 else "*/*"
timeout = int(sys.argv[4]) if len(sys.argv)>4 else 90
req = urllib.request.Request(url, headers={"Accept":acc,"User-Agent":"milano-in-dati/1.0"})
t=time.time()
try:
    r = urllib.request.urlopen(req, timeout=timeout)
    d = r.read()
    open(out,"wb").write(d)
    print("OK", len(d), r.status, r.headers.get("Content-Type"), round(time.time()-t,1),"s")
except Exception as e:
    print("ERR", repr(e), round(time.time()-t,1),"s")
