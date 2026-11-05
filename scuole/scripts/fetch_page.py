import sys, requests, re, html
u, out = sys.argv[1], sys.argv[2]
r = requests.get(u, timeout=60, headers={"User-Agent":"milano-in-dati/1.0"})
r.encoding = "utf-8"
open(out,"w",encoding="utf-8").write(r.text)
print(r.status_code, len(r.text))
t = re.sub(r"<script.*?</script>|<style.*?</style>","",r.text,flags=re.S)
for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', t, flags=re.S):
    print(m.group(1), "|", html.unescape(re.sub(r"<[^>]+>","",m.group(2))).strip()[:100])
