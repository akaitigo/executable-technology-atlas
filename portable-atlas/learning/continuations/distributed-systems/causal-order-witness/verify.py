"""Atlas: compare saved output to the pre-implementation table, never run producer."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inspect(run):
    checks = []

    def check(ok, label):
        checks.append({'label': label, 'passed': bool(ok)})

    try:
        expected = json.loads((ROOT / 'expected.json').read_text())
        fixture = json.loads((ROOT / 'inputs/events.json').read_text())
        check(run['collection_complete'] and run['input_unchanged'] and not run['errors'], 'complete successful collection')
        check(run['target_count'] == run['exec_attempt_count'] == 1 and run['target_retry'] == 0, 'one observed launch; no retry')
        check(run['target_start_unknown'] == [], 'no unknown start')
        for name, digest in run['input_sha256'].items():
            check(sha((ROOT / name).read_bytes()) == digest, 'fixed input: ' + name)
        command, = run['commands']
        check(command['success'] and command['exit_code'] == 0 and command['owned_process_reaped'] and command['owned_group_after'] == 'absent', 'owned child ended and reaped')
        check(command['priority']['priority']['after'] >= 10 and command['priority']['priority']['verified_before_exec'], 'actual nice before exec')
        check(command['priority']['cpu_limit']['actual'] == [2, 3] and command['priority']['cpu_limit']['verified_before_exec'], 'actual CPU limit before exec')
        stdout = (ROOT / command['stdout']['path']).read_bytes()
        stderr = (ROOT / command['stderr']['path']).read_bytes()
        check(sha(stdout) == command['stdout']['sha256'] and len(stdout) == command['stdout']['bytes'], 'complete stdout binding')
        check(sha(stderr) == command['stderr']['sha256'] and len(stderr) == command['stderr']['bytes'], 'complete stderr binding')
        check([json.loads(line) for line in stdout.splitlines()] == run['records'], 'parsed records equal complete saved stdout')
        gate = run['resource_gate']
        check(0 <= gate['age_seconds'] <= 60 and gate['record']['allowed'] is True, 'fresh allowed resource observation')
        from resource_policy import evaluate
        from run import check_gate_binding, FIXED_INPUTS
        check(set(run['input_sha256']) == set(FIXED_INPUTS), 'complete fixed input set')
        check(evaluate(gate['record'])['allowed'], 'resource conditions recomputed')
        check_gate_binding(gate['record'])
        check(sha((ROOT / gate['path']).read_bytes()) == gate['sha256'], 'saved resource bytes')
        records = run['records']
        check(len(records) == 7 and records[0]['kind'] == 'started', 'complete record shape')
        check(records[1] == {'kind': 'fixture', 'sha256': sha((ROOT / 'inputs/events.json').read_bytes()), 'input': fixture}, 'fixture bytes and parsed input')
        check(records[-1] == {'kind': 'batch-complete', 'case_count': 4, 'pair_rows': 60, 'retry_count': 0}, 'completion marker')
        results = [x['result'] for x in records if x['kind'] == 'case-result']
        check([x['case_id'] for x in results] == list(expected['cases']), 'four case identities in fixed order')
        causal = sorted(expected['causal_pairs'])
        base = [{'from': a, 'to': b, 'kind': 'process', 'source': p}
                for p, order in fixture['process_order'].items() for a, b in zip(order, order[1:])]
        base += [{'from': m['send'], 'to': m['receive'], 'kind': 'message', 'source': m['id']} for m in fixture['messages']]
        for result, case in zip(results, fixture['cases']):
            cid = case['id']
            want = expected['cases'][cid]
            check(result['rule'] == case['rule'] and result['replay_id'] == case['replay'], cid + ': chosen rule and replay')
            check(result['clock_labels'] == expected['clock_labels'], cid + ': unchanged fixed labels')
            replay = fixture['replays'][case['replay']]
            check(result['replay'] == replay and result['replay_clock_labels'] == [expected['clock_labels'][x] for x in replay], cid + ': display order and clock labels')
            check(result['events'] == fixture['events'] and result['base_edges'] == base, cid + ': events and six edge sources')
            rule_edges = list(base)
            if case['rule'] == 'scalar-inverse':
                rule_edges = [{'from': a, 'to': b, 'kind': 'clock-inference', 'source': 'intentional-error'}
                              for a, ca in expected['clock_labels'].items() for b, cb in expected['clock_labels'].items() if ca < cb]
            elif case['rule'] == 'display-edges':
                rule_edges += [{'from': a, 'to': b, 'kind': 'display-inference', 'source': case['replay']} for a, b in zip(replay, replay[1:])]
            check(result['rule_edges'] == rule_edges, cid + ': inference provenance distinct from causal edges')
            for key in want:
                check(result[key] == want[key], cid + ': ' + key)
            check(result['causal_pairs'] == causal and result['clock_condition_violations'] == [], cid + ': eleven causal pairs and clock condition')
            predicted = sorted(causal + want['false_positive_pairs'])
            check(result['predicted_pairs'] == predicted, cid + ': exact predicted pair IDs and directions')
            rows = result['pair_rows']
            check([[r['left'], r['right'], r['causal_relation']] for r in rows] == expected['pair_relations'], cid + ': all fifteen hand classifications')
            for row in rows:
                a, b = row['left'], row['right']
                relation = 'before' if [a, b] in predicted else 'after' if [b, a] in predicted else 'concurrent'
                check(row['predicted_relation'] == relation and row['matches'] == (relation == row['causal_relation']), cid + ': predicted relation ' + a + b)
                for prefix, edges, rel in [('causal', base, row['causal_relation']), ('rule', rule_edges, relation)]:
                    path = row[prefix + '_path']
                    if rel == 'concurrent':
                        check(path == [] and row[prefix + '_path_edges'] == [], cid + ': no ' + prefix + ' path for ' + a + b)
                    else:
                        endpoints = [a, b] if rel == 'before' else [b, a]
                        check(2 <= len(path) <= 6 and len(path) == len(set(path)) and [path[0], path[-1]] == endpoints, cid + ': path direction ' + prefix + a + b)
                        proof = [{'from': x, 'to': y, 'sources': [{'kind': e['kind'], 'source': e['source']} for e in edges if e['from'] == x and e['to'] == y]} for x, y in zip(path, path[1:])]
                        check(all(x['sources'] for x in proof) and proof == row[prefix + '_path_edges'], cid + ': path sources ' + prefix + a + b)
        check(results[0]['pair_rows'] == results[1]['pair_rows'], 'legal replay change preserves all pair relations and witnesses')
    except Exception as error:
        check(False, type(error).__name__ + ': ' + str(error))
    return {'project': 'Atlas', 'passed': all(x['passed'] for x in checks), 'checks': checks, 'check_count': len(checks)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run', type=Path)
    ap.add_argument('--mutations', action='store_true')
    args = ap.parse_args()
    saved = json.loads(args.run.read_text())
    result = inspect(saved)
    if args.mutations:
        controls = []
        for name in ['pair-direction', 'clock', 'path-source', 'false-positive', 'replay', 'stdout-binding']:
            changed = copy.deepcopy(saved)
            r = changed['records'][2]['result']
            if name == 'pair-direction': r['pair_rows'][0]['causal_relation'] = 'after'
            elif name == 'clock': r['clock_labels']['b'] = 99
            elif name == 'path-source': r['pair_rows'][0]['causal_path_edges'][0]['sources'] = []
            elif name == 'false-positive': changed['records'][4]['result']['false_positive_pairs'] = []
            elif name == 'replay': changed['records'][3]['result']['replay_clock_labels'] = [1, 1, 2, 2, 3, 4]
            else: changed['commands'][0]['stdout']['sha256'] = '0' * 64
            examined = inspect(changed)
            failed = [c['label'] for c in examined['checks'] if not c['passed']]
            target = {'pair-direction': 'all fifteen hand classifications', 'clock': 'unchanged fixed labels',
                      'path-source': 'path sources causalab', 'false-positive': 'scalar-inverse: false_positive_pairs',
                      'replay': 'causal-r2: display order and clock labels', 'stdout-binding': 'complete stdout binding'}[name]
            controls.append({'name': name, 'rejected': not examined['passed'], 'required_failed_label': target,
                             'required_check_failed': any(target in label for label in failed), 'failed_labels': failed})
        result['mutations'] = controls
        result['passed'] &= all(x['rejected'] and x['required_check_failed'] for x in controls)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
