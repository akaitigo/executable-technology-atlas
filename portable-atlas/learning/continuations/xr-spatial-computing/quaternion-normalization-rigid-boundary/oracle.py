import json,pathlib
from fractions import Fraction as F
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(key):
    # Independent literal quarter-turn/identity/nonrigid matrices, not quaternion formula.
    e=json.loads((ROOT/'hand-oracle.json').read_text())['cases'][key]
    if not e['matrix_started']:return e
    m=[[F(a) for a in row] for row in e['matrix_rows']];inv=[[F(a) for a in row] for row in e['inverse_rows']]
    for i in range(4):
        for j in range(4):assert sum(m[i][k]*inv[k][j] for k in range(4))==int(i==j)
    x=int(key.split('@')[1]);assert e['world']==[str(m[i][0]*x+m[i][3]) for i in range(4)]
    return e
