"""Estrae la polarita' (+/-) degli indicatori dalla Tavola 1 della Nota metodologica ISTAT
(Misure del benessere dei territori, anno 2018): pagine 4-5 del PDF.
E' l'UNICA fonte ISTAT di polarita' per il BesT: i metadati delle edizioni 2020-2025 (Excel)
non hanno la colonna polarita'. Gli indicatori nati dopo il 2018 non sono quindi coperti.
Uso: python -I -X utf8 polarita_istat.py <pdf assoluto> <csv di uscita assoluto>"""
import sys, re, csv, pypdf

pdf, out = sys.argv[1], sys.argv[2]
r = pypdf.PdfReader(pdf)
righe = []
for pg in (3, 4):
    righe += (r.pages[pg].extract_text() or '').split('\n')

# frammenti di nome-dominio che il PDF mette nelle stesse righe degli indicatori
DOM = ['anni disponibili, per dominio', 'Bes, anni disponibili, per dominio', 'Salute', 'Istruzione e', 'formazione', 'Lavoro e', 'conciliazione', 'dei tempi di vita', 'Benessere',
       'economico', 'Relazio', 'ni', 'sociali', 'Politica e istituzioni', 'Sicurezza', 'Paesaggio',
       'e patrimonio', 'culturale', 'Ambiente', 'Innovazio', 'ne,', 'ricerca', 'e creatività',
       'Qualità dei servizi', 'Qualità  dei servizi']
tipo_re = r'(Bes|Proxy|Locale|Altro)'
buf = ''
voci = []
for ln in righe:
    ln = ln.strip()
    if not ln or ln.startswith(('MISURE DEL', 'ISTITUTO', 'Tavola', 'Dominio', 'Indicatore', 'Tipo', 'di', 'misura', 'Bes dei', 'Bes ')) and 'Bes ' in ln[:4] and False:
        continue
    if ln.startswith(('MISURE DEL', 'ISTITUTO NAZ', 'Tavola 1', 'Dominio', 'Tipo')):
        continue
    buf = (buf + ' ' + ln).strip()
    m = re.search(r'^(.*?)\s+([+\-])?\s*' + tipo_re + r'\s+(\d{4}(?:\s*[–\-;]\s*\d{4})?)\s*$', buf)
    if m:
        voci.append((m.group(1), m.group(2), m.group(3), m.group(4)))
        buf = ''

def pulisci(nome):
    nome = nome.strip()
    changed = True
    while changed:
        changed = False
        for d in sorted(DOM, key=len, reverse=True):
            if nome.startswith(d + ' '):
                nome = nome[len(d):].strip(); changed = True
    return re.sub(r'\s+', ' ', nome).strip(' -')

with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['indicatore_nota_2018', 'polarita_istat', 'tipo_misura', 'anni', 'fonte'])
    for nome, pol, tipo, anni in voci:
        w.writerow([pulisci(nome), pol or '', tipo, anni, 'Istat, Nota metodologica (Misure del benessere dei territori), Tavola 1, file raw/' + pdf.split('/')[-2] + '/' + pdf.split('/')[-1]])
print(len(voci), 'voci')
