"""Read-only checker; explicit --record writes the finite execution receipt only."""
import argparse
import copy
import datetime
import hashlib
import itertools
import json
import platform
import re
import sys
from pathlib import Path
import runner
import oracle

ROOT = runner.ROOT

def hashes():
    names = ['fixture.json', 'runner.py', 'oracle.py', 'checker.py', 'server.py', 'index.html', 'app.js', 'README.md', 'sources.json', 'skills/atlas-software-engineering-foundations/SKILL.md']
    return {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in names}

def rejection(f, changes, receipt, reason):
    try:
        runner.select(f, changes, receipt)
    except ValueError as e:
        assert str(e) == reason, (str(e), reason)
        return reason
    raise AssertionError('accepted invalid input')

def verify(record=False):
    f = runner.fixture()
    fixed = []
    for bits in itertools.product([False, True], repeat=5):
        changed = [n for n, b in zip(f['graph'], bits) if b]
        a, tests, trace = runner.select(f, changed, runner.baseline(f))
        o, ps = oracle.impact(f['graph'], changed)
        assert a == o
        assert tests == sorted(r['test'] for r in f['requirements'].values() if r['module'] in o)
        fixed.append({'changed': changed, 'selected': a, 'tests': tests, 'oraclePaths': ps})
    # Every DAG with fixed order 4 nodes: 2^6 edge choices x 2^4 changed subsets.
    nodes = ['a', 'b', 'c', 'd']
    edges = [(nodes[i], nodes[j]) for i in range(4) for j in range(i)]
    generated = []
    for mask in range(64):
        g = {n: [] for n in nodes}
        for bit, (a, b) in enumerate(edges):
            if mask & (1 << bit):
                g[a].append(b)
        ff = {'graph': g, 'requirements': {n: {'module': n, 'test': 'T-'+n} for n in nodes}, 'before': {n: 'v1' for n in nodes}}
        for bits in itertools.product([False, True], repeat=4):
            ch = [n for n, bit in zip(nodes, bits) if bit]
            actual = runner.select(ff, ch, runner.baseline(ff))[0]
            expected = oracle.impact(g, ch)[0]
            assert actual == expected
            generated.append({'edgeMask': mask, 'changed': ch, 'actual': actual, 'oracle': expected})
    raw = [runner.run(case) for case in oracle.EXPECTED]
    for row in raw:
        case = row['case']
        assert row['values']['after'] == oracle.EXPECTED[case]
        assert all(r['pass'] for r in runner.execute(f, f['before'], [r['test'] for r in f['requirements'].values()]))
        assert {r['test'] for r in row['closure'] if not r['pass']} == {r['test'] for r in row['all'] if not r['pass']}
    config = raw[0]
    assert len(config['naive']) == 1 and config['naive'][0]['pass']
    assert config['missedByNaive'] == ['T-price', 'T-invoice', 'T-report']
    rejected = [runner.run(c) for c in ['cycle', 'unknown', 'stale']]
    assert [r['rejected'] for r in rejected] == ['cycle', 'unknown-or-duplicate-change', 'outdated-baseline']
    more = []
    for ch in [['absent'], ['config', 'config']]:
        more.append(rejection(f, ch, runner.baseline(f), 'unknown-or-duplicate-change'))
    for kind in ['self-cycle', 'unknown-dependency', 'duplicate-dependency', 'orphan-binding', 'duplicate-test', 'graph-stale', 'binding-stale', 'version-stale']:
        ff = copy.deepcopy(f)
        receipt = runner.baseline(f)
        reason = 'outdated-baseline'
        if kind == 'self-cycle':
            ff['graph']['audit'] = ['audit']; reason = 'cycle'
        if kind == 'unknown-dependency':
            ff['graph']['audit'] = ['absent']; reason = 'unknown-dependency-or-invalid-graph'
        if kind == 'duplicate-dependency':
            ff['graph']['price'] = ['config','config']; reason = 'unknown-dependency-or-invalid-graph'
        if kind == 'orphan-binding':
            del ff['requirements']['R-audit']; reason = 'invalid-binding'
        if kind == 'duplicate-test':
            ff['requirements']['R-audit']['test'] = 'T-config'; reason = 'invalid-binding'
        if kind == 'graph-stale': ff['graph']['audit'] = ['config']
        if kind == 'binding-stale': ff['requirements']['R-config']['description'] += ' revision2'
        if kind == 'version-stale': ff['before']['audit'] = 'v2'
        more.append({'case': kind, 'reason': rejection(ff, ['config'], receipt, reason)})
    # Reject two plausible faulty selectors via the independent oracle.
    changed = ['config']; expected = oracle.impact(f['graph'], changed)[0]
    assert sorted(changed) != expected  # changed-file only
    direct = sorted(set(changed) | {n for n, ds in f['graph'].items() if 'config' in ds})
    assert direct != expected  # only one level
    for doc in ['README.md', 'index.html']:
        text = (ROOT / doc).read_text()
        links = re.findall(r'\]\(([^)]+)\)', text) if doc.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"', text)
        for link in links:
            if not link.startswith(('http:', 'https:', '#')):
                if record and link in ['observations/run.json', 'observations/qa.json'] and not (ROOT / link).exists():
                    continue  # explicit first recording; read-only validation requires both
                assert (ROOT / link.split('#')[0]).is_file(), (doc, link)
        assert all(word in text for word in ['ライフサイクル', '設計', '測定', '専門倫理', '未実施', '原典'])
    sources = json.loads((ROOT / 'sources.json').read_text())
    assert len(sources) == 5 and all(x['locator'] and x['binding'] and x['url'].startswith('https://') for x in sources)
    return {'fixedSubsets': fixed, 'generatedDAGChecks': generated, 'raw': raw, 'rejected': rejected, 'additionalRejects': more, 'mutantsDetected': ['changed-file-only', 'one-level-only'], 'routeSmoke': {'supported': ['config','price','invoice','report','audit','nochange','cycle','unknown','stale'], 'unsupported': ['actual repository scan','ethical verdict','release authorization'], 'kind': 'author main-agent routing smoke, not independent forwardAgentEval'}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--record', action='store_true'); a = p.parse_args()
    result = verify(a.record)
    current = hashes()
    data = {'schema': 1, 'executedAtUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment': {'python': platform.python_version(), 'system': platform.system(), 'machine': platform.machine()}, 'command': 'python3 -B checker.py --record', 'scope': 'finite subject unit; whole subject incomplete', 'sourceArtifactDigests': current, 'inputDigest': runner.digest(runner.fixture()), 'rawDigest': runner.digest(result), 'result': result}
    receipt = ROOT / 'observations/run.json'
    if a.record:
        tmp = receipt.with_suffix('.tmp'); tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n'); tmp.replace(receipt)
    else:
        saved = json.loads(receipt.read_text())
        assert saved['sourceArtifactDigests'] == current, 'stale source/artifact receipt'
        assert saved['inputDigest'] == data['inputDigest']
        assert saved['rawDigest'] == data['rawDigest']
        assert saved['result'] == result, 'raw mismatch'
        qa = json.loads((ROOT / 'observations/qa.json').read_text())
        assert qa['sourceArtifactDigests'] == current, 'stale QA binding'
        assert len(qa['cases']) == 9 and qa['cleanup']['serverClosed'] and qa['cleanup']['tabClosed']
        assert qa['title'] == '変更影響と構成baseline | ソフトウェア工学基礎'
        assert qa['qaDigest'] == runner.digest({k:v for k,v in qa.items() if k != 'qaDigest'})
        for observed in qa['cases']:
            actual = runner.run(observed['case'])
            assert observed['baseline'] == actual['input']['receipt']
            if 'rejected' in actual:
                assert observed['summary'] == '拒否：'+actual['rejected']
            else:
                assert observed['values'] == actual['values']['after']
                assert observed['affected'] == actual['affected']
                assert observed['oracleMatches']
                failures = sum(not r['pass'] for r in actual['closure'])
                assert observed['counts'] == [len(actual['affected']),len(actual['closure']),failures,len(actual['missedByNaive'])]
        assert qa['rawExpanded'] and qa['answerExpanded'] and len(qa['roadmapTopics']) == 4
    print(json.dumps({'status':'PASS','fixedSubsets':32,'generatedDAGChecks':1024,'behaviorCases':6,'rejectionCases':13,'mutantsDetected':2,'readOnly':not a.record}, ensure_ascii=False))

if __name__ == '__main__': main()
