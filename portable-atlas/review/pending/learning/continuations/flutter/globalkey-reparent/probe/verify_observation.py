#!/usr/bin/env python3
"""Read raw observations; do not invoke Flutter or trust producer pass/expected/symbols."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads((args.attempt / 'actual.json').read_text())
    receipt = json.loads((args.attempt / 'run.json').read_text())
    checks = []

    def check(name, got, wanted):
        checks.append({'name': name, 'passed': got == wanted, 'actual': got, 'wanted': wanted})

    check('three cases', [c['id'] for c in raw['cases']], ['globalSameFrame', 'globalGap', 'valueSameFrame'])
    check('framework errors', raw['flutterErrors'], [])
    for name, digest in receipt['inputSha256'].items():
        check('executed input snapshot ' + name, hashlib.sha256((args.attempt / 'inputs' / name).read_bytes()).hexdigest(), digest)
    for case in raw['cases']:
        cid = case['id']
        stages = case['stages']
        check(cid + ' phases', [s['phase'] for s in stages], ['initial', 'prepared', 'transition', 'atRight'])
        initial = stages[0]['rows'][0]
        original = initial['stateId']
        parents = stages[0]['parents']
        check(cid + ' fixed parents', [p['slot'] for p in parents], ['left', 'right'])
        check(cid + ' distinct parent elements', len({p['elementId'] for p in parents}), 2)
        alive = {}
        created = set()
        deactivated = set()
        flattened = []
        for i, stage in enumerate(stages):
            prefix = cid + '/' + stage['phase']
            rows, events = stage['rows'], stage['events']
            flattened += events
            for event in events:
                name, sid = event['event'], event['stateId']
                if name == 'initState':
                    check(prefix + ' fresh constructor ' + sid, sid in created, False)
                    created.add(sid); alive[sid] = 0
                elif name == 'increment':
                    check(prefix + ' increment alive', sid in alive, True)
                    alive[sid] += 1
                elif name == 'deactivate':
                    check(prefix + ' deactivate alive', sid in alive, True); deactivated.add(sid)
                elif name == 'activate':
                    check(prefix + ' activate after deactivate', sid in deactivated, True); deactivated.remove(sid)
                elif name == 'dispose':
                    check(prefix + ' dispose after deactivate', sid in deactivated, True)
                    deactivated.remove(sid); del alive[sid]
                check(prefix + ' event count ' + name, event['count'], alive.get(sid, event['count']))
            check(prefix + ' lifecycle replay versus rows', {r['stateId']: r['count'] for r in rows}, alive)
            check(prefix + ' registry versus rows', stage['registryStateIds'], sorted(alive))
            check(prefix + ' parents stable', stage['parents'], parents)
            gap = cid == 'globalGap' and i == 2
            check(prefix + ' number of children', len(rows), 0 if gap else 1)
            expected_slot = None if gap else ('left' if i < 2 else 'right')
            check(prefix + ' location', stage['hostLocation'], expected_slot)
            if rows:
                r = rows[0]
                retained = i < 2 or cid == 'globalSameFrame'
                check(prefix + ' same State?', r['stateId'] == original, retained)
                check(prefix + ' same Element?', r['elementId'] == initial['elementId'], retained)
                check(prefix + ' fixed counter', r['count'], 0 if i == 0 or not retained else 1)
                check(prefix + ' parent slot', r['slot'], expected_slot)
                check(prefix + ' same direct parent?', r['parentElementId'] == initial['parentElementId'], i < 2)
                check(prefix + ' slot binding', r['slotElementId'], next(p['elementId'] for p in parents if p['slot'] == expected_slot))
                check(prefix + ' reused key object', r['sameKeyObject'], True)
                check(prefix + ' mounted', r['mounted'], True)
                check(prefix + ' actual Text', r['texts'], [f"\u9805\u76ee A / State {r['stateId']} / \u56de\u6570 {r['count']}"])
            check(prefix + ' GlobalKey currentState', stage['globalCurrentStateId'], rows[0]['stateId'] if rows and cid != 'valueSameFrame' else None)
            check(prefix + ' no inactive leftovers at frame completion', sorted(deactivated), [])
        check(cid + ' event slices reconstruct full log', flattened, case['allLifecycleEvents'][:len(flattened)])
        moved = stages[2]['events']
        check(cid + ' transition activate count', sum(e['event'] == 'activate' for e in moved), 1 if cid == 'globalSameFrame' else 0)
        check(cid + ' transition dispose count', sum(e['event'] == 'dispose' for e in moved), 0 if cid == 'globalSameFrame' else 1)
        final_row = stages[-1]['rows'][0]
        if cid == 'valueSameFrame':
            check(cid + ' new State then stable', final_row['stateId'], stages[2]['rows'][0]['stateId'])
            check(cid + ' new Element then stable', final_row['elementId'], stages[2]['rows'][0]['elementId'])
        cleanup = case['cleanupEvents']
        check(cid + ' cleanup dispose set', sorted(e['stateId'] for e in cleanup if e['event'] == 'dispose'), sorted(alive))
        all_events = case['allLifecycleEvents']
        check(cid + ' every created State disposed once', sorted(e['stateId'] for e in all_events if e['event'] == 'dispose'), sorted(created))
    failures = [c for c in checks if not c['passed']]
    result = {'kind': 'author_separate_python_raw_observation_check', 'differentReviewer': False,
              'compilerOrTesterInvoked': False, 'producerExpectedSymbolsPassedUsedAsOracle': False,
              'actualSha256': hashlib.sha256((args.attempt / 'actual.json').read_bytes()).hexdigest(),
              'checkCount': len(checks), 'passed': not failures, 'failures': failures, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
