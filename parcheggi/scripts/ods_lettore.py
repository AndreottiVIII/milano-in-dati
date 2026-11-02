"""Lettore minimo di file .ods (zip + content.xml), senza librerie esterne oltre alla libreria standard.
Uso come modulo: from ods_lettore import fogli ; fogli(path) -> {nome_foglio: lista di righe (liste di stringhe)}"""
import zipfile
import xml.etree.ElementTree as ET
NS = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0", "x": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
      "o": "urn:oasis:names:tc:opendocument:xmlns:office:1.0"}
T = "{%s}" % NS["t"]; X = "{%s}" % NS["x"]; O = "{%s}" % NS["o"]
def fogli(path, solo=None, max_righe=None):
    out = {}
    with zipfile.ZipFile(path) as z:
        with z.open("content.xml") as f:
            for ev, el in ET.iterparse(f, events=("end",)):
                if el.tag == T + "table":
                    nome = el.get(T + "name")
                    if solo and nome not in solo:
                        el.clear(); continue
                    righe = []
                    for r in el.iter(T + "table-row"):
                        rep = int(r.get(T + "number-rows-repeated", "1"))
                        cells = []
                        for c in r:
                            if c.tag not in (T + "table-cell", T + "covered-table-cell"):
                                continue
                            n = int(c.get(T + "number-columns-repeated", "1"))
                            v = c.get(O + "value")
                            if v is None:
                                v = "".join("".join(p.itertext()) for p in c.findall(X + "p"))
                            cells.extend([v] * min(n, 50))
                        while cells and cells[-1] == "":
                            cells.pop()
                        if cells:
                            righe.extend([cells] * min(rep, 5))
                        if max_righe and len(righe) >= max_righe:
                            break
                    out[nome] = righe
                    el.clear()
    return out
