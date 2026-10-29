import re
def strip(s):
    s = re.sub(r"<ref[^>]*/>", "", s); s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", s); s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'''?", "", s); s = re.sub(r"<br\s*/?>", "; ", s); s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" ;")
def infobox(text):
    i = text.find("{{Incidente")
    if i < 0: i = text.find("{{incidente")
    if i < 0: return {}
    depth = 0; j = i
    while j < len(text):
        if text.startswith("{{", j): depth += 1; j += 2
        elif text.startswith("}}", j):
            depth -= 1; j += 2
            if depth == 0: break
        else: j += 1
    body = text[i+2:j-2]
    # split top-level on newline + |
    fields = {}; cur = None; buf = []
    for line in body.split("\n")[1:]:
        m = re.match(r"\s*\|\s*([^=|]+?)\s*=(.*)", line)
        if m:
            if cur: fields[cur] = "\n".join(buf)
            cur = m.group(1).strip().lower(); buf = [m.group(2)]
        else: buf.append(line)
    if cur: fields[cur] = "\n".join(buf)
    return {k: strip(v) for k, v in fields.items()}
