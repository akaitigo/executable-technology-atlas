import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(case):
    # Literal anchor multiset, href, revision and decisions authored before parser runs.
    return json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case]
