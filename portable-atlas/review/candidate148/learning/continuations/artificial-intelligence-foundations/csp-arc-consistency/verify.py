"""Atlas: inspect saved records only; never import the propagation model."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(run):
    checks = []
    def check(label, ok):
        checks.append({'label': label, 'passed': bool(ok)})
    expect = json.loads((ROOT / 'expected.json').read_text())
    fixture = json.loads((ROOT / 'inputs/cases.json').read_text())
    check('complete', run.get('collection_complete') and run.get('target_count') == 1 and not run.get('errors'))
    check('fixed-inputs', run.get('input_unchanged') and all(sha(ROOT / n) == h for n, h in run['input_sha256'].items()))
    command = run['commands'][0]
    check('priority-cleanup', command['success'] and command['priority']['priority']['verified_before_exec'] and command['priority']['cpu_limit']['verified_before_exec'] and command['owned_process_reaped'] and command['owned_group_after'] == 'absent' and command['exit_code'] == 0)
    stream = ROOT / command['stdout']['path']
    check('stdout-binding', sha(stream) == command['stdout']['sha256'] and [json.loads(x) for x in stream.read_text().splitlines()] == run['records'])
    gate = run['resource_gate']; observation = gate['record']
    check('resource-binding', sha(ROOT / gate['path']) == gate['sha256'] and json.loads((ROOT / gate['path']).read_text()) == observation and 0 <= gate['age_seconds'] <= 60 and observation['allowed'])
    check('policy-binding', observation['policy_input_hashes'] == {n: sha(ROOT / n) for n in ['resources.py', 'resource_parse.py', 'resource_policy.py']})
    check('reference-binding', observation['root_browser_reference_sha256'] == sha(ROOT / 'records/root-browser-reference.json') and observation['root_browser_reference'] == json.loads((ROOT / 'records/root-browser-reference.json').read_text()))
    decision = observation['root_batch_decision_file']; dp = Path(decision['path'])
    check('decision-binding', sha(dp) == decision['sha256'] and json.loads(dp.read_text()) == observation['root_batch_decision'])
    check('fixture-binding', run['records'][1]['fixture'] == fixture and run['records'][1]['sha256'] == sha(ROOT / 'inputs/cases.json'))
    cases = [r for r in run['records'] if r['kind'] == 'case']
    check('case-order', [c['id'] for c in cases] == [c['id'] for c in expect['cases']])
    for c, e, p in zip(cases, expect['cases'], fixture['cases']):
        tag = c['id']
        def ck(label, ok): check(tag + ':' + label, ok)
        for mode in ['FC', 'AC3']:
            r = c[mode]
            for key in e[mode]:
                ck(mode + ':' + key, r[key] == e[mode][key])
            domains = copy.deepcopy(p['domains'])
            arcs = sorted([list(a) for edge in p['edges'] for a in (edge, edge[::-1])])
            queue = copy.deepcopy(arcs) if mode == 'AC3' else []
            metrics = {k: 0 for k in r['metrics']}
            if mode == 'AC3': metrics['initial_arcs'] = len(arcs)
            transitions = reasons = operations = True
            active = None
            tests = []
            for seq, t in enumerate(r['events']):
                action, d = t['action'], t['detail']
                if action == 'POP':
                    operations &= bool(queue) and queue[0] == d['arc']
                    if queue: queue.pop(0)
                    active = d['arc']; tests = []
                    metrics['revise_calls'] += 1
                elif action == 'SUPPORT_TEST':
                    i, j = d['arc']; x, y = d['tail_value'], d['head_value']
                    operations &= active == d['arc'] and x in domains[i] and y in domains[j] and d['passes'] == (x != y)
                    # A passing comparison ends this tail value's scan.
                    operations &= not any(v['tail_value'] == x and v['passes'] for v in tests)
                    tests.append(d); metrics['support_tests'] += 1
                elif action == 'CHECK':
                    a, n = d['assigned'], d['neighbor']
                    operations &= a in p['fixed_assignment'] and p['fixed_assignment'][a] == d['value'] and n not in p['fixed_assignment'] and sorted([a, n]) in p['edges'] and d['candidate'] in domains[n] and d['passes'] == (d['value'] != d['candidate'])
                    metrics['constraint_tests'] += 1
                elif action == 'REMOVE':
                    v, x = d['variable'], d['value']
                    if mode == 'AC3':
                        j = d['head']
                        reasons &= active == [v, j] and d['head_domain'] == domains[j] and not any(x != y for y in domains[j])
                        reasons &= [q['head_value'] for q in tests if q['tail_value'] == x] == domains[j]
                    else:
                        a = d['assigned']
                        reasons &= a in p['fixed_assignment'] and p['fixed_assignment'][a] == d['assigned_value'] == x and sorted([a, v]) in p['edges']
                    reasons &= x in domains[v]
                    if x in domains[v]: domains[v].remove(x)
                    metrics['removed_values'] += 1
                elif action in ['ENQUEUE', 'ALREADY_QUEUED']:
                    a = d['arc']
                    operations &= active is not None and a[1] == active[0] and a[0] != active[1] and a in arcs
                    if action == 'ENQUEUE':
                        operations &= a not in queue
                        queue.append(a[:]); metrics['queue_added'] += 1
                    else:
                        operations &= a in queue
                        metrics['queue_skipped'] += 1
                elif action == 'EMPTY':
                    operations &= domains[d['variable']] == [] and seq == len(r['events']) - 1
                    metrics['empty_domain_stops'] += 1
                elif action == 'END':
                    operations &= seq == len(r['events']) - 1 and (mode == 'FC' or not queue)
                elif action not in ['INITIAL', 'REVISION_END']:
                    operations = False
                transitions &= t['seq'] == seq and t['domains'] == domains and t['metrics'] == metrics
                if mode == 'AC3': transitions &= t['queue'] == queue and t['iteration'] == metrics['revise_calls']
            ck(mode + ':event-transitions', transitions)
            ck(mode + ':removal-reasons', reasons)
            ck(mode + ':event-operations', operations)
            ck(mode + ':event-final', domains == r['domains'] and metrics == r['metrics'] and (mode == 'FC' or queue == r['remaining_queue']))
            ck(mode + ':initial-copy', r['events'][0]['action'] == 'INITIAL' and r['events'][0]['domains'] == p['domains'])
            if mode == 'AC3':
                summaries = True
                for number, summary in enumerate(r['iterations'], 1):
                    group = [t for t in r['events'] if t['iteration'] == number and t['action'] != 'END']
                    revisions = [t for t in group if t['action'] == 'REVISION_END']
                    removed = [[t['detail']['variable'], t['detail']['value']] for t in group if t['action'] == 'REMOVE']
                    summaries &= bool(group) and group[0]['action'] == 'POP' and group[0]['detail']['arc'] == summary['arc']
                    summaries &= len(revisions) == 1 and revisions[0]['detail'] == {'arc': summary['arc'], 'changed': bool(removed)}
                    summaries &= removed == summary['removed'] and sum(t['action'] == 'SUPPORT_TEST' for t in group) == summary['support_tests']
                    summaries &= [t['detail']['arc'] for t in group if t['action'] == 'ENQUEUE'] == summary['enqueued']
                    summaries &= [t['detail']['arc'] for t in group if t['action'] == 'ALREADY_QUEUED'] == summary['already_queued']
                    summaries &= bool(group) and group[-1]['domains'] == summary['domains_after'] and group[-1]['queue'] == summary['queue_after_iteration']
                ck('AC3:iteration-event-binding', summaries)
        # A fixed exhaustive assignment table, separate from the propagation trace.
        valid = []
        for bits in expect['all_assignments']:
            assignment = dict(zip('ABCD', map(int, bits)))
            if all(assignment[v] in p['domains'][v] for v in 'ABCD') and all(assignment[a] != assignment[b] for a, b in p['edges']):
                valid.append(bits)
        ck('hand-assignment-oracle', valid == e['valid_assignments'])
        consistent = all(any(x != y for y in c['AC3']['domains'][j]) for i, j in arcs for x in c['AC3']['domains'][i])
        if c['AC3']['status'] == 'arc-consistent': ck('final-local-supports', consistent)
        if tag == 'triangle-free': ck('nonempty-not-SAT', consistent and all(c['AC3']['domains'].values()) and valid == [])
        if tag == 'triangle-anchored': ck('early-stop-unprocessed-BC', c['AC3']['remaining_queue'] == [['B', 'C']] and c['AC3']['events'][-1]['action'] == 'EMPTY')
    return checks


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('run', type=Path); args = ap.parse_args()
    run = json.loads(args.run.read_text()); checks = inspect(run); mutations = []
    def changed(name, edit, required):
        value = copy.deepcopy(run); edit(value)
        failed = [c['label'] for c in inspect(value) if not c['passed']]
        mutations.append(dict(name=name, failed_labels=failed, required_label=required, passed=required in failed))
    def case(r, name): return next(c for c in r['records'] if c.get('id') == name)
    changed('FC final domain', lambda r: case(r, 'chain-anchored')['FC']['domains'].update(C=[0]), 'chain-anchored:FC:domains')
    changed('AC3 support count', lambda r: case(r, 'chain-anchored')['AC3']['metrics'].update(support_tests=99), 'chain-anchored:AC3:metrics')
    changed('lost pending arc', lambda r: case(r, 'triangle-anchored')['AC3']['remaining_queue'].clear(), 'triangle-anchored:AC3:remaining_queue')
    changed('SAT confused with AC', lambda r: case(r, 'triangle-free')['AC3'].update(status='SAT'), 'triangle-free:AC3:status')
    changed('forged removal reason', lambda r: next(t for t in case(r, 'chain-anchored')['AC3']['events'] if t['action'] == 'REMOVE')['detail'].update(head_domain=[]), 'chain-anchored:AC3:removal-reasons')
    changed('stdout binding', lambda r: r['commands'][0]['stdout'].update(sha256='0' * 64), 'stdout-binding')
    result = dict(project='Atlas', passed=all(c['passed'] for c in checks + mutations), checks=checks, check_count=len(checks), mutations=mutations, target_runs=0, scope='saved bytes and semantic mutation checks; model not imported', run_sha256=sha(args.run), verifier_sha256=sha(Path(__file__)))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
