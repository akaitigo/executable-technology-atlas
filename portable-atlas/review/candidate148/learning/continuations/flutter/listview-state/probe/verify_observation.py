#!/usr/bin/env python3
"""実行しない独立照合。producerのpassed/expectedを使わず原票の関係を検査する。"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, required=True)
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    run = json.loads((attempt / 'run.json').read_text())
    actual = json.loads((attempt / 'actual.json').read_text())
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})

    check('actual digest', digest(attempt / 'actual.json') == run['actualSha256'])
    for name, sha in run['inputSha256'].items():
        check('input snapshot ' + name, digest(attempt / 'inputs' / name) == sha)
    check('no Flutter errors', actual['flutterErrors'] == [])
    check('finite cases', [c['id'] for c in actual['cases']] == ['withLookup', 'withoutLookup'])
    check('finite process sequence', [s['name'] for s in run['steps']] == ['compile', 'widgetProbe'])
    for step in run['steps']:
        check(step['name'] + ' exit and nice', step['exitCode'] == 0 and step['priority']['effectiveNice'] == 10)
        check(step['name'] + ' bounded time', 0 <= step['elapsedSeconds'] <= step['timeoutSeconds'])

    for case in actual['cases']:
        prefix = case['id'] + ': '
        stages = case['stages']
        check(prefix + 'phase sequence', [s['phase'] for s in stages] ==
              ['initial', 'prepared', 'reordered', 'far', 'returned'])
        rows = [{r['itemId']: r for r in s['rows']} for s in stages]
        initial, prepared, reordered, far, returned = rows
        live, ever = {}, set()
        for i, stage in enumerate(stages):
            for event in stage['events']:
                state = event['stateId']
                if event['event'] == 'initState':
                    check(prefix + stage['phase'] + ' fresh ' + state, state not in ever)
                    ever.add(state)
                elif event['event'] in ('increment', 'didUpdateWidget', 'deactivate', 'dispose'):
                    check(prefix + stage['phase'] + ' live event ' + state, state in live)
                if event['event'] == 'dispose':
                    live.pop(state, None)
                else:
                    live[state] = event
            observed_ids = {r['stateId'] for r in stage['rows']}
            check(prefix + stage['phase'] + ' lifecycle replay', set(live) == observed_ids)
            check(prefix + stage['phase'] + ' rendered row geometry',
                  [r['renderBox'] for r in stage['rows']] ==
                  [{'top': 0.0, 'width': 320.0, 'height': 80.0},
                   {'top': 80.0, 'width': 320.0, 'height': 80.0}])
            check(prefix + stage['phase'] + ' item order',
                  [r['itemId'] for r in stage['rows']] ==
                  [['A', 'B'], ['A', 'B'], ['B', 'A'], ['I', 'J'], ['B', 'A']][i])
            check(prefix + stage['phase'] + ' offset', stage['offset'] == [0, 0, 0, 640, 0][i])
            for row in stage['rows']:
                event = live[row['stateId']]
                check(prefix + stage['phase'] + ' state log ' + row['itemId'],
                      all(row[key] == event[key] for key in ('itemId', 'mountedFor', 'count')))
                text = '項目 {itemId} / State {stateId} / 生成時 {mountedFor} / 回数 {count}'.format(**row)
                check(prefix + stage['phase'] + ' Element Text ' + row['itemId'], row['texts'] == [text])
        for item, count in [('A', 1), ('B', 2)]:
            check(prefix + 'prepared identity ' + item,
                  initial[item]['stateId'] == prepared[item]['stateId'] and prepared[item]['count'] == count)
            check(prefix + 'initial zero ' + item, initial[item]['count'] == 0)
            if case['id'] == 'withLookup':
                check(prefix + 'reorder preserves ' + item,
                      reordered[item]['stateId'] == prepared[item]['stateId'] and reordered[item]['count'] == count)
            else:
                check(prefix + 'reorder recreates ' + item,
                      reordered[item]['stateId'] not in {r['stateId'] for r in prepared.values()}
                      and reordered[item]['count'] == 0)
            previous_ids = {r['stateId'] for s in stages[:4] for r in s['rows']}
            check(prefix + 'return fresh zero ' + item,
                  returned[item]['stateId'] not in previous_ids and returned[item]['count'] == 0)
        check(prefix + 'far fresh zero', all(r['count'] == 0 and r['stateId'] not in
              {r['stateId'] for s in stages[:3] for r in s['rows']} for r in far.values()))
        for phase_index, wanted in [(0, {0, 1}), (3, {8, 9}), (4, {0, 1})]:
            check(prefix + stages[phase_index]['phase'] + ' builder indices',
                  {c['index'] for c in stages[phase_index]['builderCalls']} == wanted)
        disposed = {e['stateId'] for e in case['cleanupEvents'] if e['event'] == 'dispose'}
        check(prefix + 'cleanup', disposed == set(live))
    report = {'checkedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'kind': 'independent_read_only_observation_check',
              'method': '別Python実装。producerのpassed/expected/差分配列に依存せずState関係とイベント原票を再照合。',
              'independentHumanReviewer': False,
              'passed': all(c['passed'] for c in checks), 'checkCount': len(checks),
              'checks': checks, 'actualSha256': digest(attempt / 'actual.json'),
              'checkerSha256': digest(Path(__file__)),
              'compilerTesterStarted': False, 'visualQaPerformed': False}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
