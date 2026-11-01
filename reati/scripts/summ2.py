import sys, csv, collections
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
print(len(rows), "righe", list(rows[0].keys())[:9])
for k in ["REF_AREA", "DATA_TYPE", "Y_KNOWN_OFFENDER_IDEN", "REFERENCE_PERIOD_CRIME", "OBS_STATUS", "TIME_PERIOD"]:
    c = collections.Counter(r[k] for r in rows); print(k, len(c), c.most_common(8))
print(len({r["TYPE_CRIME"] for r in rows}))
