"""Independent Python JSON/table oracle; no Swift/runner migration reuse."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def predict(case):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];d=json.loads(f['json']);table=json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case]
    version=d['version'];p=d['profile'];presence='missing' if 'displayName' not in p else 'null' if p['displayName'] is None else 'string' if type(p['displayName']) is str else 'number' if type(p['displayName']) is int else 'other'
    assert (version,presence,f['mode'])==(table['version'],table['presence'],table['mode'])
    assert p['name']=='Aki'
    if presence=='string':assert p['displayName']=='Mika'
    if presence=='number':assert p['displayName']==7
    # Select fixed independent version × existence × type × expected value row.
    return table
