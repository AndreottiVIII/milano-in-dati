"""Legge il DSD SDMX ISTAT: dimensioni e codelist (it). Uso: parse_dsd.py <dsd.xml> <outdir>"""
import sys, re, json
import xml.etree.ElementTree as ET
src, outdir = sys.argv[1], sys.argv[2]
ns = {"s": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure",
      "c": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common"}
XML = "{http://www.w3.org/XML/1998/namespace}lang"
root = ET.parse(src).getroot()
cls = {}
for cl in root.iter("{%s}Codelist" % ns["s"]):
    d = {}
    for code in cl.findall("s:Code", ns):
        nm = {n.get(XML): n.text for n in code.findall("c:Name", ns)}
        d[code.get("id")] = nm.get("it") or nm.get("en")
    cls[cl.get("id")] = d
for dsd in root.iter("{%s}DataStructure" % ns["s"]):
    print("DSD", dsd.get("id"))
    for dim in dsd.iter():
        tag = dim.tag.split("}")[-1]
        if tag in ("Dimension", "TimeDimension", "Attribute", "Measure", "PrimaryMeasure"):
            ref = None
            for r in dim.iter("Ref"):
                if r.get("class") == "Codelist":
                    ref = r.get("id")
            print(" ", tag, dim.get("id"), dim.get("position"), ref, len(cls.get(ref, {})))
json.dump(cls, open(outdir + "/codelists.json", "w", encoding="utf8"), ensure_ascii=False)
# contenuti dei codelist piccoli
for k, v in cls.items():
    if len(v) <= 40:
        print("CL", k, v)
