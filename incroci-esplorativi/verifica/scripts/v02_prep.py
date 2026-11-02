"""Prepara: (1) ds27 NIL x anno x età x sesso x italiani/stranieri; (2) SMR propri; (3) voti e affluenza per NIL ricalcolati dalle sezioni."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 200)
raw = p('popolazione', 'raw', 'comune_ds27', 'unzip', 'ds27_pop_sto_quartiere.csv')
h = pd.read_csv(raw, sep=None, engine='python', nrows=5, encoding='latin1'); print(h.to_string())
sep = ';' if ';' in open(raw, encoding='latin1').readline() else ','
cols = pd.read_csv(raw, sep=sep, nrows=0, encoding='latin1').columns.tolist(); print(cols)
fp = os.path.join(OUT, 'ds27_nil_eta_sesso_cit.csv')
if not os.path.exists(fp):
    d = pd.read_csv(raw, sep=sep, encoding='latin1')
    print(d.head(3).to_string())
    print(d.nunique())
    d.to_pickle(os.path.join(OUT, '_ds27.pkl'))
