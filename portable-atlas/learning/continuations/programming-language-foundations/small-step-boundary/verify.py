"""Atlas: inspect saved output using hand expectations; never run either evaluator."""
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
                              'fixture': fixture, 'prerequisite_sha256': sha((ROOT / 'inputs/prerequisite-interpreter.py').read_bytes())}, 'input and prerequisite bytes')
        check(records[-1] == {'kind': 'batch-complete', 'case_count': 5, 'retry': 0}, 'completion marker')
        results = [r for r in records if r['kind'] == 'case-result']
        check([r['case_id'] for r in results] == [c['id'] for c in want], 'five case identities')
        # Hand-counted instrumentation from the fixed old evaluator, not from step().
        counts = [(3, 1), (18, 7), (18, 7), (23, 8), (5, 2)]
        for r, case, expected, (events, enters) in zip(results, fixture['cases'], want, counts):
            cid = case['id']; s = r['small_step']; big = r['big_step']
            check(r['input'] == case, cid + ': identical input')
            check(s['status'] == expected['status'], cid + ': terminal classification')
            check(s['value'] == expected['value'] and s['function_value'] is None, cid + ': integer result versus no result')
            check(s['states'] == expected['states'], cid + ': exact hand AST states')
            check(s['final_term'] == expected['states'][-1], cid + ': final residual term')
            count = len(expected['rules'])
            check(s['budget'] == case['budget'] and s['applied_steps'] == count and s['remaining_budget'] == case['budget'] - count, cid + ': applied step budget')
            check(len(s['transitions']) == count and len(s['states']) == count + 1, cid + ': one transition per applied rule')
            check([t['rule_chain'] for t in s['transitions']] == expected['rules'], cid + ': rule chain')
            check([t['redex_path'] for t in s['transitions']] == expected['redex_paths'], cid + ': redex positions')
            for i, t in enumerate(s['transitions']):
                check(t['index'] == i + 1 and t['before'] == s['states'][i] and t['after'] == s['states'][i + 1], cid + ': transition state binding ' + str(i))
                check(t['redex_before'] == subtree(t['before'], t['redex_path']) and t['redex_after'] == subtree(t['after'], t['redex_path']), cid + ': redex before/after ' + str(i))
            check(s['unapplied_next_rule'] == expected['next_rule'], cid + ': unapplied next rule')
            check(s['unapplied_next_redex_path'] == ('$' if expected['next_rule'] else None), cid + ': unapplied next position')
            check(s['reason'] == ({'code': 'not-callable', 'path': '$'} if expected.get('reason') else None), cid + ': stuck reason distinct from budget')
            check(big['policy'] == 'lexical-definition-parent', cid + ': old evaluator lexical mode')
            check(big['status'] == expected['big_step']['status'] and big['value'] == expected['big_step']['value'], cid + ': old evaluator result')
            check((big['error']['code'] if big['error'] else None) == expected['big_step']['error'], cid + ': old evaluator error')
            check(len(big['trace']) == events and big['evaluations'] == enters, cid + ': hand-counted instrumentation')
            check(sum(e['action'] == 'enter' for e in big['trace']) == enters and [e['step'] for e in big['trace']] == list(range(1, events + 1)), cid + ': full observation event numbering')
            check(r['comparison'] == {'kind': 'same input, different observation units', 'applied_rule_steps': count,
                                       'big_step_node_enters': enters, 'big_step_trace_events': events,
                                       'event_count_is_not_rule_count': True}, cid + ': observation units separate')
            if cid == 'not-callable-stuck':
                check(not any(e['node_path'].startswith('$.arg') for e in big['trace']) and s['final_term']['arg'] == case['ast']['arg'], cid + ': argument not evaluated')
        check(results[1]['big_step'] == results[2]['big_step'], 'same arithmetic input gives same old observation; small budget differs')
    except Exception as error:
        check(False, type(error).__name__ + ': ' + str(error))
    return {'project': 'Atlas', 'passed': all(c['passed'] for c in checks), 'checks': checks, 'check_count': len(checks)}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('run', type=Path); parser.add_argument('--mutations', action='store_true'); args = parser.parse_args()
    saved = json.loads(args.run.read_text()); result = inspect(saved)
    if args.mutations:
        mutations = []
        for name in ['right-first', 'collapsed-step', 'value-as-budget', 'budget-as-stuck', 'apply-unexecuted-next', 'stdout-binding']:
            changed = copy.deepcopy(saved)
            cases = [r for r in changed['records'] if r['kind'] == 'case-result']
            if name == 'right-first':
                cases[1]['small_step']['states'][1] = {'kind': 'Add', 'left': {'kind': 'Add', 'left': {'kind': 'Int', 'value': 1}, 'right': {'kind': 'Int', 'value': 2}}, 'right': {'kind': 'Int', 'value': 7}}
                target = 'arithmetic-complete: exact hand AST states'
            elif name == 'collapsed-step':
                cases[1]['small_step']['applied_steps'] = 1; target = 'arithmetic-complete: applied step budget'
            elif name == 'value-as-budget':
                cases[0]['small_step']['status'] = 'budget_exhausted'; target = 'zero-value: terminal classification'
            elif name == 'budget-as-stuck':
                cases[2]['small_step']['status'] = 'stuck'; target = 'arithmetic-budget: terminal classification'
            elif name == 'apply-unexecuted-next':
                cases[2]['small_step']['final_term'] = {'kind': 'Int', 'value': 10}; target = 'arithmetic-budget: final residual term'
            else:
                changed['commands'][0]['stdout']['sha256'] = '0' * 64; target = 'complete stdout binding'
            tested = inspect(changed); failed = [c['label'] for c in tested['checks'] if not c['passed']]
            mutations.append({'name': name, 'rejected': not tested['passed'], 'required_failed_label': target,
                              'required_check_failed': target in failed, 'failed_labels': failed})
        result['mutations'] = mutations; result['passed'] &= all(m['rejected'] and m['required_check_failed'] for m in mutations)
    print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
