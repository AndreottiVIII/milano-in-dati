"""Scarica l'elenco dei dataflow ISTAT (1 richiesta). Uso: python -I -X utf8 istat_dataflow_list.py <out.xml>"""
import sys, urllib.request
req = urllib.request.Request("https://esploradati.istat.it/SDMXWS/rest/dataflow/IT1", headers={"User-Agent": "milano-in-dati research (davide.caniatti@gmail.com)", "Accept": "application/xml"})
b = urllib.request.urlopen(req, timeout=500).read()
open(sys.argv[1], "wb").write(b); print(len(b))
