"""Atlas: inspect saved output using hand expectations; never run the type checker or either evaluation branch."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def subtree(term, path):
    current = term
    for key in path.split('.')[1:]:
        current = current[key]
    return current


def inspect(run):
    checks = []
    def check(ok, label):
        checks.append({'passed': bool(ok), 'label': label})
    try:
        want = json.loads((ROOT / 'expected.json').read_text())['cases']
        fixture = json.loads((ROOT / 'inputs/cases.json').read_text())
        check(run['collection_complete'] and run['input_unchanged'] and not run['errors'], 'complete successful collection')
        check(run['target_count'] == run['exec_attempt_count'] == 1 and run['target_retry'] == 0, 'one launch; automatic retry zero')
        check(run['target_start_unknown'] == [], 'no unknown start')
        from run import FIXED_INPUTS, check_gate_binding
        from resource_policy import evaluate
        check(set(run['input_sha256']) == set(FIXED_INPUTS), 'complete fixed input set')
        for name, digest in run['input_sha256'].items():
            check(sha((ROOT / name).read_bytes()) == digest, 'fixed input: ' + name)
        command, = run['commands']
        check(command['success'] and command['exit_code'] == 0 and command['owned_process_reaped'] and command['owned_group_after'] == 'absent', 'owned child ended and reaped')
        check(command['priority']['priority']['after'] >= 10 and command['priority']['priority']['verified_before_exec'], 'actual nice before exec')
        check(command['priority']['cpu_limit']['actual'] == [2, 3] and command['priority']['cpu_limit']['verified_before_exec'], 'actual CPU limit before exec')
        stdout = (ROOT / command['stdout']['path']).read_bytes()
        stderr = (ROOT / command['stderr']['path']).read_bytes()
        for name, data in [('stdout', stdout), ('stderr', stderr)]:
            check(sha(data) == command[name]['sha256'] and len(data) == command[name]['bytes'], 'complete ' + name + ' binding')
        check([json.loads(line) for line in stdout.splitlines()] == run['records'], 'parsed records equal complete stdout')
        gate = run['resource_gate']
        check(0 <= gate['age_seconds'] <= 60 and gate['record']['allowed'] is True, 'fresh allowed resource observation')
        check(evaluate(gate['record'])['allowed'], 'resource conditions recomputed')
        check_gate_binding(gate['record'])
        check(sha((ROOT / gate['path']).read_bytes()) == gate['sha256'], 'saved resource bytes')
        records = run['records']
        check(len(records) == 8 and records[0]['kind'] == 'producer-started', 'complete record shape')
        check(records[1] == {'kind': 'input', 'sha256': sha((ROOT / 'inputs/cases.json').read_bytes()),
                              'fixture': fixture, 'prerequisite_sha256': sha((ROOT / 'inputs/prerequisite-small-step.py').read_bytes())}, 'input and prerequisite bytes')
        check(records[-1] == {'kind': 'batch-complete', 'case_count': 5, 'retry': 0}, 'completion marker')
        results = [r for r in records if r['kind'] == 'case-result']
        check([r['case_id'] for r in results] == [c['id'] for c in want], 'five case identities')
        totals = {'accepted': 0, 'type_rejected': 0, 'strict_evaluator_calls': 0, 'diagnostic_evaluator_calls': 0}
        def nodes(tree):
            return [tree] + [n for child in tree['premises'] for n in nodes(child)]
        for r, case, expected in zip(results, fixture['cases'], want):
            cid = case['id']; typing = r['typing']; diag = r['diagnostic']; strict = r['strict']; d = diag['result']; hand = expected['diagnostic']
            check(r['input'] == case, cid + ': identical input')
            check(typing == expected['typing'], cid + ': complete hand typing tree')
            actual_nodes, hand_nodes = nodes(typing), nodes(expected['typing'])
            check(len(actual_nodes) == len(hand_nodes), cid + ': judgment node count')
            for actual, target in zip(actual_nodes, hand_nodes):
                tag = cid + ': ' + target['path']
                check(actual['path'] == target['path'] and actual['rule'] == target['rule'], tag + ': AST position and rule')
                check(actual['context'] == target['context'], tag + ': incoming Gamma')
                check(actual['type'] == target['type'] and actual['status'] == target['status'], tag + ': synthesized type or rejection')
                check(actual['rejection'] == target['rejection'] and actual['unvisited'] == target['unvisited'], tag + ': preserved refusal and unvisited')
                check([n['path'] for n in actual['premises']] == [n['path'] for n in target['premises']], tag + ': direct premises')
            check(r['erased_term'] == expected['erased_term'], cid + ': exact annotation erasure')
            check(strict['evaluator_calls'] == expected['strict_evaluator_calls'] and strict['status'] == expected['strict_status'], cid + ': strict dispatch count and status')
            check(diag['evaluator_calls'] == 1 and diag['purpose'] == 'separate annotation-erased comparison; not strict dispatch', cid + ': separate diagnostic call')
            if expected['strict_evaluator_calls'] == 0:
                check(strict['result'] is None, cid + ': strict rejection has no evaluation result')
            else:
                check(strict['result'] == d, cid + ': two independent deterministic branch results agree')
            check(d['status'] == hand['status'], cid + ': diagnostic classification')
            check(d['value'] == hand['value'] and d['function_value'] == hand['function_value'], cid + ': diagnostic integer versus function value')
            check(d['reason'] == hand['reason'], cid + ': diagnostic stuck reason')
            check(d['states'] == hand['states'] and d['final_term'] == hand['states'][-1], cid + ': full diagnostic hand AST states')
            count = len(hand['rules'])
            check(d['applied_steps'] == count and len(d['transitions']) == count and d['budget'] == case['diagnostic_budget'] and d['remaining_budget'] == case['diagnostic_budget'] - count, cid + ': diagnostic step budget')
            check([t['rule_chain'] for t in d['transitions']] == hand['rules'], cid + ': diagnostic rules')
            check([t['redex_path'] for t in d['transitions']] == ['$'] * count, cid + ': diagnostic root redex positions')
            for i, t in enumerate(d['transitions']):
                check(t['index'] == i + 1 and t['before'] == d['states'][i] and t['after'] == d['states'][i + 1], cid + ': transition states ' + str(i))
                check(t['redex_before'] == t['before'] and t['redex_after'] == t['after'], cid + ': root redex ' + str(i))
            check(d['unapplied_next_rule'] is None and d['unapplied_next_redex_path'] is None, cid + ': no extra unapplied rule')
            totals['accepted' if expected['typing']['status'] == 'accepted' else 'type_rejected'] += 1
            totals['strict_evaluator_calls'] += strict['evaluator_calls']; totals['diagnostic_evaluator_calls'] += diag['evaluator_calls']
        check(totals == json.loads((ROOT / 'expected.json').read_text())['totals'], 'two strict and five diagnostic evaluations are separate')
    except Exception as error:
        check(False, type(error).__name__ + ': ' + str(error))
    return {'project': 'Atlas', 'passed': all(c['passed'] for c in checks), 'checks': checks, 'check_count': len(checks)}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('run', type=Path); parser.add_argument('--mutations', action='store_true'); args = parser.parse_args()
    saved = json.loads(args.run.read_text()); result = inspect(saved)
    if args.mutations:
        mutations = []
        for name in ['wrong-gamma', 'wrong-function-type', 'strict-bypass', 'diagnostic-merged', 'erasure-changed', 'latent-value-as-stuck', 'stdout-binding']:
            changed = copy.deepcopy(saved)
            cases = [r for r in changed['records'] if r['kind'] == 'case-result']
            if name == 'wrong-gamma':
                cases[4]['typing']['premises'][0]['context']['x'] = {'arrow': ['Int', 'Int']}; target = 'latent-invalid-function: $.body: incoming Gamma'
            elif name == 'wrong-function-type':
                cases[0]['typing']['type'] = 'Int'; target = 'function-value: $: synthesized type or rejection'
            elif name == 'strict-bypass':
                cases[2]['strict']['evaluator_calls'] = 1; target = 'integer-call: strict dispatch count and status'
            elif name == 'diagnostic-merged':
                cases[2]['diagnostic']['evaluator_calls'] = 0; target = 'integer-call: separate diagnostic call'
            elif name == 'erasure-changed':
                cases[2]['erased_term']['arg'] = {'kind': 'Int', 'value': 3}; target = 'integer-call: exact annotation erasure'
            elif name == 'latent-value-as-stuck':
                cases[4]['diagnostic']['result']['status'] = 'stuck'; target = 'latent-invalid-function: diagnostic classification'
            else:
                changed['commands'][0]['stdout']['sha256'] = '0' * 64; target = 'complete stdout binding'
            tested = inspect(changed); failed = [c['label'] for c in tested['checks'] if not c['passed']]
            mutations.append({'name': name, 'rejected': not tested['passed'], 'required_failed_label': target,
                              'required_check_failed': target in failed, 'failed_labels': failed})
        result['mutations'] = mutations; result['passed'] &= all(m['rejected'] and m['required_check_failed'] for m in mutations)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
