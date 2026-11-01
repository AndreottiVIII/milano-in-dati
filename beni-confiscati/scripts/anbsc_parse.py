"""Lettura dei CSV ANBSC OpenRE.G.I.O. "destinati". Il campo 'utilizzo' ha virgolette non scappate e a volte a-capo,
e qualche indirizzo ha virgolette dentro: il modulo csv standard sbaglia. Qui si divide il testo in record dove
inizia un identificativo (es. "I-MI-123456") e ogni record si divide sul separatore '","'."""
import re

REC_START = re.compile(r'(?m)^"([IA]-[A-Z]{2}-\d+)","')


def parse_destinati(path):
    t = open(path, encoding="utf8").read()
    header_end = t.index("\n") + 1
    header = t[:header_end].strip().split(",")
    starts = [m.start() for m in REC_START.finditer(t)]
    starts.append(len(t) + 1)
    out, bad = [], []
    for a, b in zip(starts, starts[1:]):
        rec = t[a:b].rstrip("\r\n").strip()
        if not (rec.startswith('"') and rec.endswith('"')):
            bad.append(rec[:150]); continue
        parts = rec[1:-1].split('","')
        if len(parts) != len(header):
            bad.append(rec[:150]); continue
        row = {k: re.sub(r"\s+", " ", v).strip() for k, v in zip(header, parts)}
        out.append(row)
    return header, out, bad


if __name__ == "__main__":
    import sys
    h, rows, bad = parse_destinati(sys.argv[1])
    print(len(rows), "righe;", len(bad), "scartate")
    for b in bad[:5]:
        print("  ", b)
