import sys,re,html,requests
area=sys.argv[1]; out=sys.argv[2]
r=requests.get("https://dati.istruzione.it/opendata/opendata/catalogo/elements1/",params={"area":area},timeout=90,headers={"User-Agent":"milano-in-dati/1.0"})
r.encoding="utf-8"; open(out,"w",encoding="utf-8").write(r.text)
t=re.sub(r"<script.*?</script>|<style.*?</style>","",r.text,flags=re.S)
blocks=re.split(r'(?=<div[^>]*class="[^"]*(?:parte-superiore|dettagli)[^"]*")',t)
ids=re.findall(r'datasetId=(\w+)',t)
print(r.status_code,len(r.text),len(set(ids)))
tx=html.unescape(re.sub(r"<[^>]+>","\n",t)); tx=re.sub(r"\n\s*\n+","\n",tx)
lines=[l.strip() for l in tx.split("\n")]
# print title lines (lines before "Nel flusso")
for i,l in enumerate(lines):
    if l.startswith("Nel flusso") or l.startswith("Download:"): 
        print("-",lines[i-1][:160]); 
print(sorted(set(ids)))
print(sorted(set(re.findall(r'href="([^"/]*\.(?:csv|zip|json))"',t)))[:15])
