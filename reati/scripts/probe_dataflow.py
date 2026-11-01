import sys, urllib.request
out = sys.argv[1]
req = urllib.request.Request("https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1", headers={"Accept":"application/vnd.sdmx.structure+xml;version=2.1","User-Agent":"Mozilla/5.0 (milano-in-dati research)"})
d = urllib.request.urlopen(req, timeout=120).read()
open(out,"wb").write(d)
print(len(d))
