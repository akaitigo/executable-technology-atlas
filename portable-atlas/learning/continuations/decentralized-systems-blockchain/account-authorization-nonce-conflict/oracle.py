import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(case):
    # Independent pre-authored decisions/states; no producer rule or transition import.
    h=json.loads((ROOT/'hand-oracle.json').read_text());e=h['cases'][case]
    for s in e['states']:assert s['balances']['A']+s['balances']['B']==150
    return h,e
