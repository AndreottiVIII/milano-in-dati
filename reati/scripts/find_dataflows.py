"""Cerca nel catalogo dataflow ISTAT (XML SDMX) quelli su delitti/reati. Uso: find_dataflows.py <xml> <out.txt>"""
import re, sys
src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding="utf8").read()
lines = []
for m in re.finditer(r"<structure:Dataflow [^>]*>.*?</structure:Dataflow>", t, re.S):
    s = m.group(0)
    if re.search(r"(?i)delitt|reati|crimin|furti|sicurezza|denunc", s):
        head = re.match(r"<structure:Dataflow ([^>]*)>", s).group(1)
        idm = re.search(r'\bid="([^"]+)"', head).group(1)
        ver = re.search(r'\bversion="([^"]+)"', head)
        names = re.findall(r'<common:Name xml:lang="(\w+)">([^<]*)', s)
        ref = re.search(r"<Ref [^>]*/>", s)
        lines.append(f"{idm} v{ver.group(1) if ver else '?'} | {[n[1] for n in names if n[0]=='it']} | {ref.group(0) if ref else ''}")
open(out, "w", encoding="utf8").write("\n".join(lines))
print("\n".join(lines))
