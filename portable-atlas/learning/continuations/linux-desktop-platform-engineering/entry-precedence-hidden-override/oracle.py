import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(case):
    # No resolver or parser import; candidate order/source/count authored as literal.
    return json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case]
