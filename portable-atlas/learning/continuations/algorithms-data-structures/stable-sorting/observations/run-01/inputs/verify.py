"""Atlas: read saved values against literal expectations; never import the producer."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent

def inspect(raw, fixture, expected, refusals):
    checks = 0
    def eq(actual, wanted, label):
        nonlocal checks
        checks += 1
        if actual != wanted:
            raise AssertionError(label + ': ' + repr(actual) + ' != ' + repr(wanted))
    eq([c['id'] for c in raw['cases']], [c['id'] for c in fixture['cases']], 'case set/order')
    by_id = {x['caseId']: x for x in expected['rows']}
    search_by_id = {x['caseId']: x for x in expected['searchRows']}
    for row, case in zip(raw['cases'], fixture['cases']):
        original = case['records']
        eq(row['input'], original, 'input')
        eq(row['inputAfter'], original, 'input after')
        eq(row['inputUnchanged'], True, 'input unchanged')
        eq(set(row['outcomes']), {'insertion', 'merge_left', 'merge_right'}, 'method set')
        item_by_id = {x['id']: x for x in original}
        for method, out in row['outcomes'].items():
            hand = by_id[row['id']]['methods'][method]
            target = [item_by_id[x] for x in hand['ids']]
            eq(out['method'], method, 'method')
            eq(out['output'], target, 'literal output')
            eq(Counter((x['key'], x['id']) for x in out['output']), Counter((x['key'], x['id']) for x in original), 'record preservation')
            eq([x['key'] for x in out['output']], sorted(x['key'] for x in original), 'key order')
            stable = all([x['id'] for x in out['output'] if x['key'] == k] == [x['id'] for x in original if x['key'] == k] for k in {x['key'] for x in original})
            eq(out['properties'], {'sortedness': True, 'permutation': True, 'stability': stable}, 'independent properties')
            for name in ('comparisons', 'placements'):
                eq(out[name], hand[name], name)
            eq(stable, hand['stability'], 'literal stability')
            eq(sum(e['kind'] == 'compare' for e in out['events']), out['comparisons'], 'comparison events')
            eq(sum(e['kind'] == 'place' for e in out['events']), out['placements'], 'placement events')
            for event in out['events']:
                if event['kind'] == 'compare':
                    a, b = event['left']['key'], event['right']['key']
                    value = {'>': a > b, '<': a < b, '<=': a <= b}[event['operator']]
                    eq(event['result'], value, 'comparison truth')
                elif event['kind'] in ('hold', 'place'):
                    eq(event['record'], item_by_id[event['record']['id']], 'event record')
            eq(out['frames'][0]['records'], original, 'initial frame')
            eq(out['frames'][0]['comparisons'], 0, 'initial count')
            eq(out['frames'][0]['placements'], 0, 'initial writes')
            eq(out['frames'][-1]['records'], target, 'final frame')
            eq(out['frames'][-1]['comparisons'], hand['comparisons'], 'final count')
            eq(out['frames'][-1]['placements'], hand['placements'], 'final writes')
            for i, frame in enumerate(out['frames'][1:], 1):
                start, end = frame['scope']
                segment = original[start:end]
                if method == 'insertion':
                    wanted = sorted(original[:i+1], key=lambda x: x['key']) + original[i+1:]
                else:
                    indexed = list(enumerate(segment))
                    wanted = [r for _, r in sorted(indexed, key=lambda pair: (pair[1]['key'], pair[0] if method == 'merge_left' else -pair[0]))]
                eq(frame['records'], wanted, 'completed frame')
            s = search_by_id[row['id']]
            eq([q['query'] for q in out['search']], fixture['queries'], 'query set/order')
            for i, q in enumerate(out['search']):
                eq(q['linear']['found'], s['found'][i], 'linear found')
                eq(q['binary']['found'], s['found'][i], 'binary found')
                eq(q['binary']['index'], sum(r['key'] < q['query'] for r in original), 'lower bound position')
                eq(q['linear']['comparisons'], s['linearComparisons'][i], 'linear comparisons')
                eq(q['binary']['comparisons'], s['binaryComparisons'][i], 'binary comparisons')
                eq(q['linearPrefix'], s['linearPrefix'][i], 'linear prefix')
                eq(q['binaryPrefix'], s['binaryPrefix'][i], 'binary prefix')
                eq(q['preparedPrefix'], hand['comparisons'] + s['binaryPrefix'][i], 'preparation included once')
                for name in ('linear', 'binary'):
                    eq(len(q[name]['events']), q[name]['comparisons'], 'search event count')
                    for event in q[name]['events']:
                        eq(event['result'], event['key'] < q['query'] if event['operator'] == '<' else event['key'] == q['query'], 'search comparison truth')
    eq([r['id'] for r in raw['refusals']], [r['id'] for r in refusals['cases']], 'refusal set')
    for result, case in zip(raw['refusals'], refusals['cases']):
        eq(result['method'], case['method'], 'refusal method')
        eq(result['input'], case['records'], 'refusal input')
        eq(result['inputAfter'], case['records'], 'refusal unchanged')
        eq(result['reason'], case['expected'], 'refusal reason')
        eq(result['result'], None, 'no refusal output')
    return checks

def main():
    raw = json.loads((BASE/'observations/run-01/results.json').read_text())
    fixture = json.loads((BASE/'fixture.json').read_text())
    expected = json.loads((BASE/'expected.json').read_text())
    refusals = json.loads((BASE/'rejection-cases.json').read_text())
    checks = inspect(raw, fixture, expected, refusals)
    bindings = {}
    for name, digest in raw['inputs'].items():
        actual = hashlib.sha256((BASE/name).read_bytes()).hexdigest()
        snapshot = hashlib.sha256((BASE/'observations/run-01/inputs'/name).read_bytes()).hexdigest()
        if actual != digest or snapshot != digest:
            raise AssertionError('source mismatch: ' + name)
        bindings[name] = digest
    mutations = []
    for name in ['missing-case', 'changed-order', 'missing-record', 'count-change', 'missing-query', 'false-refusal-value']:
        bad = deepcopy(raw)
        if name == 'missing-case': bad['cases'].pop()
        elif name == 'changed-order': bad['cases'][4]['outcomes']['merge_right']['output'].reverse()
        elif name == 'missing-record': bad['cases'][2]['outcomes']['insertion']['output'].pop()
        elif name == 'count-change': bad['cases'][3]['outcomes']['insertion']['comparisons'] += 1
        elif name == 'missing-query': bad['cases'][4]['outcomes']['merge_left']['search'].pop()
        else: bad['refusals'][0]['result'] = []
        try: inspect(bad, fixture, expected, refusals)
        except (AssertionError, KeyError, IndexError): mutations.append(name)
        else: raise AssertionError('mutation not rejected: ' + name)
    report = {'Atlas': '保存した整列計算の照合', 'checkedAt': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'checks': checks, 'inputsMatched': bindings, 'memoryMutationsRejected': mutations,
              'producerImported': False, 'producerExecuted': False, 'guiChecked': False}
    if '--record' in sys.argv:
        destination = BASE/'verification/saved-result-check.json'
        with destination.open('x') as f: f.write(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
