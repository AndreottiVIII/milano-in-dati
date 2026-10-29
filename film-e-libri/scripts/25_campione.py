"""Estrae un campione casuale di match (alta+media) da controllare a mano. Uso: python -I 25_campione.py <strand> <seme> <n>"""
import sys, os, json, random
base, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
m = [x for x in json.load(open(os.path.join(base, "pulito", "_match_tutti.json"), encoding="utf8")) if x["conf"] != "bassa"]
random.Random(seed).shuffle(m)
for i, x in enumerate(m[:n]):
    f = x["frase"]; k = f.find(x["testo"])
    print(f"{i+1}. [{x['conf']}/{x['fonte']}/{x['tipo']}/{x['sezione']}] {x['luogo']} <- '{x['testo']}' | ...{f[max(0,k-110):k+len(x['testo'])+70]}...".encode("ascii", "replace").decode())
