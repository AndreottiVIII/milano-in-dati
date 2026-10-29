import sys, json, time, requests
out = sys.argv[1]
B = "https://dati.comune.milano.it/api/3/action/"
qs = [("package_search", {"q":"elezioni","rows":1000}),
      ("package_search", {"q":"referendum","rows":1000}),
      ("package_search", {"q":"voti","rows":1000}),
      ("package_search", {"q":"sezioni","rows":1000}),
      ("package_search", {"q":"elettorale","rows":1000}),
      ("package_search", {"q":"sezione elettorale","rows":1000}),
      ("package_search", {"q":"politiche","rows":1000}),
      ("package_search", {"q":"europee","rows":1000}),
      ("package_search", {"q":"regionali","rows":1000}),
      ("package_search", {"q":"affluenza","rows":1000}),
      ("package_search", {"q":"comunali","rows":1000}),
      ("package_search", {"q":"municipali","rows":1000}),
      ("package_search", {"q":"seggi","rows":1000}),
      ("package_search", {"q":"plessi","rows":1000}),
      ("group_list", {"all_fields":"true"}),
      ("tag_list", {"query":"elezion"}),
      ("tag_list", {"query":"vot"}),
      ("organization_list", {"all_fields":"true"}),
      ]
allp = {}
log = []
for act, p in qs:
    r = requests.get(B+act, params=p, timeout=90)
    try:
        j = r.json()
    except Exception:
        print("FAIL", act, p, r.status_code, flush=True); log.append((act,p,"FAIL "+str(r.status_code))); continue
    res = j["result"]
    if act=="package_search":
        log.append((act,p,res["count"]))
        for x in res["results"]:
            allp[x["name"]] = x
    else:
        log.append((act,p,res))
    print(act,p,(res["count"] if act=="package_search" else (len(res) if hasattr(res,'__len__') else res)),flush=True)
    time.sleep(1)
json.dump({"log":log,"packages":allp}, open(out,"w",encoding="utf-8"), ensure_ascii=False)
print(len(allp))
