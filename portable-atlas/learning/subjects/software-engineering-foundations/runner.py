"""Finite declared dependency model, Python stdlib only. No repository scanning."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def fixture():
    return json.loads((ROOT / 'fixture.json').read_text())

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def baseline(f):
    return digest({k: f[k] for k in ('graph', 'requirements', 'before')})

def validate(f, changed, receipt):
    g = f['graph']
    if not isinstance(changed, list) or len(set(changed)) != len(changed) or any(n not in g for n in changed):
        raise ValueError('unknown-or-duplicate-change')
    if not g or len(g) > 8 or any(not isinstance(ds, list) or len(set(ds)) != len(ds) or any(d not in g for d in ds) for ds in g.values()):
        raise ValueError('unknown-dependency-or-invalid-graph')
    active, done = set(), set()
    def visit(n):
        if n in active:
            raise ValueError('cycle')
        if n in done:
            return
        active.add(n)
        for d in g[n]:
            visit(d)
        active.remove(n)
        done.add(n)
    for n in g:
        visit(n)
    rs = f['requirements']
    if set(r['module'] for r in rs.values()) != set(g) or len({r['test'] for r in rs.values()}) != len(rs):
        raise ValueError('invalid-binding')
    if receipt != baseline(f):
        raise ValueError('outdated-baseline')

def select(f, changed, receipt):
    validate(f, changed, receipt)
    affected, queue, trace = set(changed), list(changed), []
    while queue:
        dependency = queue.pop(0)
        for consumer, ds in f['graph'].items():
            if dependency in ds and consumer not in affected:
                affected.add(consumer)
                queue.append(consumer)
                trace.append({'dependency': dependency, 'consumer': consumer})
    tests = sorted(r['test'] for r in f['requirements'].values() if r['module'] in affected)
    return sorted(affected), tests, trace

def behavior(versions):
    tax = 10 if versions['config'] == 'tax10' else 20
    price = 100 if versions['price'] == 'ignore-tax' else 100 * (100 + tax) // 100
    invoice = price * (2 if versions['invoice'] == 'double' else 1)
    report = 0 if versions['report'] == 'zero' else invoice
    return {'config': tax, 'price': price, 'invoice': invoice, 'report': report, 'audit': versions['audit']}

def execute(f, versions, tests):
    values = behavior(versions)
    expected = {'price': 110, 'invoice': 110, 'report': 110, 'audit': 'ok'}
    rows = []
    for rid, r in f['requirements'].items():
        if r['test'] in tests:
            n = r['module']
            passed = isinstance(values[n], int) and 0 <= values[n] <= 100 if n == 'config' else values[n] == expected[n]
            rows.append({'requirement': rid, 'test': r['test'], 'module': n, 'actual': values[n], 'expected': 'integer 0..100' if n == 'config' else expected[n], 'pass': passed})
    return rows

def run(case='config'):
    from copy import deepcopy
    f = fixture()
    receipt = baseline(f)
    changed = [] if case == 'nochange' else [case]
    if case == 'cycle':
        f['graph']['config'] = ['report']
        changed = ['config']
        receipt = baseline(f)
    elif case == 'unknown':
        changed = ['missing']
    elif case == 'stale':
        changed = ['config']
        f['requirements']['R-price']['description'] += ' (revision2)'
    try:
        affected, tests, trace = select(f, changed, receipt)
    except ValueError as e:
        return {'case': case, 'input': {'graph': f['graph'], 'changed': changed, 'receipt': receipt, 'currentBaseline': baseline(f)}, 'rejected': str(e)}
    after = deepcopy(f['before'])
    for n in changed:
        after[n] = f['changes'][n]
    naive = sorted(r['test'] for r in f['requirements'].values() if r['module'] in changed)
    alltests = sorted(r['test'] for r in f['requirements'].values())
    allrows = execute(f, after, alltests)
    naiverows = execute(f, after, naive)
    closurerows = execute(f, after, tests)
    return {'case': case, 'input': {'graph': f['graph'], 'requirements': f['requirements'], 'changed': changed, 'receipt': receipt}, 'versions': {'before': f['before'], 'after': after}, 'values': {'before': behavior(f['before']), 'after': behavior(after)}, 'affected': affected, 'trace': trace, 'naive': naiverows, 'closure': closurerows, 'all': allrows, 'missedByNaive': [r['test'] for r in allrows if not r['pass'] and r['test'] not in naive]}

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--case', default='config', choices=['config', 'price', 'invoice', 'report', 'audit', 'nochange', 'cycle', 'unknown', 'stale'])
    a = p.parse_args()
    print(json.dumps(run(a.case), ensure_ascii=False, indent=2))
