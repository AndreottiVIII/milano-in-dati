"""Rifa tutta la Fase 3: taratura, calcolo di tutte le coppie, dati della pagina, NOTE.md.
Uso (una riga): python -I C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/bici-auto-mezzi/scripts/f3_rifai.py C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/bici-auto-mezzi
Legge tragitti_prova.csv e (se c'e) tragitti_prova_2.csv. Dura circa 15-20 minuti."""
import sys, os, subprocess, glob
S = sys.argv[1]; H = os.path.dirname(os.path.abspath(__file__)); PY = [sys.executable, '-I']
def run(*a): 
    print('>>', ' '.join(a), flush=True); subprocess.run(PY + [H + '/' + a[0]] + list(a[1:]), check=True)
run('f3_calibra.py', S)
run('f3_tutte.py', S, 'nomi')
for f in glob.glob(S + '/out/f3_celle_[0-9].npz'): os.remove(f)
ps = [subprocess.Popen(PY + [H + '/f3_tutte.py', S, 'celle', str(k), '6']) for k in range(6)]
for p in ps:
    assert p.wait() == 0
for f in glob.glob(S + '/out/f3_sens_[0-9].npz'): os.remove(f)
ps = [subprocess.Popen(PY + [H + '/f3_sens.py', S, str(k), '6']) for k in range(6)]
for p in ps:
    assert p.wait() == 0
run('f3_esporta.py', S, '3')
run('f3_note.py', S)
print('RIFATTO')
