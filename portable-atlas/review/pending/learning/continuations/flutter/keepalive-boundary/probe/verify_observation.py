#!/usr/bin/env python3
"""将来の原票を別実装で読む。producerのpassed/期待行に依存しない。"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    run = json.loads((attempt / 'run.json').read_text())
    actual = json.loads((attempt / 'actual.json').read_text())
    checks = []

    def check(name, value):
        checks.append({'name': name, 'passed': bool(value)})

    check('actual hash', sha(attempt / 'actual.json') == run['actualSha256'])
    for name, digest in run['inputSha256'].items():
        check('input snapshot ' + name, sha(attempt / 'inputs' / name) == digest)
    check('finite case order', [c['id'] for c in actual['cases']] == ['requested', 'notRequested'])
    check('Flutter errors absent', actual['flutterErrors'] == [])
    check('sequential process names', [s['name'] for s in run['steps']] == ['compile', 'widgetProbe'])
    for step in run['steps']:
        check(step['name'] + ' bounded/nice/exit', step['exitCode'] == 0 and
              step['priority']['effectiveNice'] == 10 and 0 <= step['elapsedSeconds'] <= step['timeoutSeconds'])
    for case in actual['cases']:
        prefix = case['id'] + ': '
        requested = case['id'] == 'requested'
        stages = case['stages']
        check(prefix + 'phase order', [s['phase'] for s in stages] == ['initial', 'prepared', 'far', 'returned'])
        initial, prepared, far, returned = [{r['itemId']: r for r in s['rows']} for s in stages]
        live, ever = {}, set()
        for i, stage in enumerate(stages):
            label = prefix + stage['phase'] + ': '
            for event in stage['events']:
                state = event['stateId']
                if event['event'] == 'initState':
                    check(label + 'fresh ' + state, state not in ever)
                    ever.add(state)
                else:
                    check(label + 'live event ' + state, state in live)
                if event['event'] == 'dispose':
                    live.pop(state, None)
                else:
                    live[state] = event
            check(label + 'lifecycle replay', set(live) == {r['stateId'] for r in stage['rows']})
            check(label + 'offset', stage['offset'] == [0, 0, 640, 0][i])
            layout = [r['itemId'] for r in stage['rows'] if not r['keptAlive']]
            cached = [r['itemId'] for r in stage['rows'] if r['keptAlive']]
            check(label + 'layout items', layout == [['A', 'B'], ['A', 'B'], ['I', 'J'], ['A', 'B']][i])
            check(label + 'cached items', cached == ([[], [], ['A', 'B'], ['I', 'J']][i] if requested else []))
            for row in stage['rows']:
                suffix = row['itemId']
                event = live[row['stateId']]
                check(label + 'State record ' + suffix, all(row[k] == event[k] for k in ('itemId', 'mountedFor', 'count', 'wantKeepAlive')))
                check(label + 'request and mounted ' + suffix,
                      row['mounted'] is True and row['wantKeepAlive'] == requested and row['keepAlive'] == requested)
                check(label + 'storage flag ' + suffix, row['storage'] == ('cached' if row['keptAlive'] else 'layout'))
                check(label + 'render index ' + suffix, row['renderIndex'] == ord(row['itemId']) - ord('A'))
                check(label + 'Element Text ' + suffix, row['texts'] == [
                    '項目 {itemId} / State {stateId} / 回数 {count}'.format(**row)])
        for item, count in [('A', 1), ('B', 2)]:
            check(prefix + 'prepared retains ' + item, initial[item]['stateId'] == prepared[item]['stateId'] and prepared[item]['count'] == count)
            if requested:
                check(prefix + 'offscreen survives ' + item, far[item]['stateId'] == prepared[item]['stateId'] and far[item]['count'] == count and far[item]['keptAlive'])
                check(prefix + 'return retains ' + item, returned[item]['stateId'] == prepared[item]['stateId'] and returned[item]['count'] == count and not returned[item]['keptAlive'])
            else:
                check(prefix + 'offscreen removed ' + item, item not in far)
                earlier = {r['stateId'] for s in stages[:3] for r in s['rows']}
                check(prefix + 'return recreates ' + item, returned[item]['stateId'] not in earlier and returned[item]['count'] == 0)
        for item in ['I', 'J']:
            check(prefix + 'far fresh zero ' + item, far[item]['count'] == 0 and far[item]['stateId'] not in {r['stateId'] for r in prepared.values()})
            if requested:
                check(prefix + 'returned caches ' + item, returned[item]['stateId'] == far[item]['stateId'] and returned[item]['keptAlive'])
            else:
                check(prefix + 'returned removes ' + item, item not in returned)
        disposed = {e['stateId'] for e in case['cleanupEvents'] if e['event'] == 'dispose'}
        check(prefix + 'cleanup all remaining State', disposed == set(live))
    result = {'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'kind': 'independent_read_only_observation_check', 'independentHumanReviewer': False,
              'passed': all(c['passed'] for c in checks), 'checkCount': len(checks), 'checks': checks,
              'actualSha256': sha(attempt / 'actual.json'), 'checkerSha256': sha(Path(__file__)),
              'compilerTesterStarted': False, 'visualQaPerformed': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
