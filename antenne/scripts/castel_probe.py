"""Sonda l'interfaccia pubblica (senza login) di CASTEL ARPA Lombardia: una sola ricerca per Milano.
Uso: python -I -X utf8 castel_probe.py <out_dir>   (salva HTML in out_dir)"""
import sys, re, os, requests
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
B = "https://castel.arpalombardia.it/castel/report/report_dati.aspx"
s = requests.Session(); s.headers["User-Agent"] = "milano-in-dati/antenne (ricerca open data)"
def hidden(h):
    return {k: re.search(r'id="%s" value="([^"]*)"' % k, h).group(1) for k in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"] if re.search(r'id="%s" value="([^"]*)"' % k, h)}
h = s.get(B, timeout=60).text
d = hidden(h)
d.update({"ScriptManager1_HiddenField": "", "listProvince": "015", "__EVENTTARGET": "listProvince", "__EVENTARGUMENT": "", "__ASYNCPOST": "true"})
r = s.post(B, data=d, timeout=60)
open(os.path.join(out, "castel_post1.txt"), "w", encoding="utf-8").write(r.text)
print(r.status_code, len(r.text)); print(r.text[:300])
m = re.findall(r'<option value="(\d+)">([^<]*)</option>', r.text)
print(len(m), [x for x in m if "ilano" in x[1]][:3])
