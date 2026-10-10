import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def inspect(case,offset):
    h=json.loads((ROOT/'hand-oracle.json').read_text());f=json.loads((ROOT/'fixtures.json').read_text())[case];e=h['cases'][case+'@'+str(offset)]
    if not e['convolution_started']:assert offset==1 and not f['padding'] and len(f['pulse'])==2;return e
    # Literal per-symbol shifted contribution vectors, authored before execution.
    matrix=h['long_contributions' if len(f['pulse'])==3 else 'short_contributions']
    assert [sum(column) for column in zip(*matrix)]==e['samples']
    for indices,mean in zip(e['windows'],e['means']):
        values=[e['samples'][i] if i<len(e['samples']) else 0 for i in indices]
        n,d=(map(int,mean.split('/')) if '/' in mean else (int(mean),1))
        assert sum(values)*d==2*n
    return e
