"""Atlas: saved synthetic guard inputs only; no host commands, process or model runs."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from resource_parse import parse_processes
from resource_policy import evaluate
from priority_launcher import priority_gate, cpu_gate
import run

ROOT = Path(__file__).resolve().parent


def main():
    reference = json.loads((ROOT / 'records/root-browser-reference.json').read_text())
    ps = [{**p, 'rss_kib': 10, 'cpu_percent_one_core': 0} for p in reference['identities']]
    for p in ps:
        p.pop('cpu', None)
    base = {'summary': {'read_success': True, 'idle_percent': 80, 'memory_free_percent': 50, 'available_memory_estimate_gib': 5},
            'cpu_count': 12, 'loadavg': [2, 2, 2],
            'process_observation': {'trusted': True, 'processes': ps, 'browsers': ps[1:], 'heavy': []},
            'coordination': {'root_slot': True, 'root_gui_idle': True, 'other_target_count': 0, 'authorization': 'SYNTHETIC ONLY'},
            'root_browser_reference': reference,
            'root_batch_decision': {'scope': 'distributed-causal-order-witness', 'allowed': True, 'identities': ps}}
    checks = []

    def check(name, condition, detail=None):
        checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

    variants = [('synthetic normal', base, True)]
    for name, modify in [
        ('slot absent', lambda r: r['coordination'].update(root_slot=False)),
        ('gui idle unknown', lambda r: r['coordination'].update(root_gui_idle=None)),
        ('other target exists', lambda r: r['coordination'].update(other_target_count=1)),
        ('decision absent', lambda r: r.update(root_batch_decision=None)),
        ('old decision scope', lambda r: r['root_batch_decision'].update(scope='formal-fairness-starvation')),
        ('load at boundary', lambda r: r.update(loadavg=[6, 2, 2])),
        ('idle below boundary', lambda r: r['summary'].update(idle_percent=59)),
        ('free below boundary', lambda r: r['summary'].update(memory_free_percent=39)),
        ('aggregate over 400', lambda r: r['summary'].update(idle_percent=66)),
        ('missing root', lambda r: r['process_observation']['processes'].pop(0)),
        ('changed start', lambda r: r['process_observation']['processes'][0].update(lstart='Thu Jan  1 00:00:00 1970')),
        ('ps unknown', lambda r: r['process_observation'].update(trusted=False, heavy=None, browsers=None)),
        ('heavy present', lambda r: r['process_observation'].update(heavy=[{'name': 'synthetic'}])),
        ('new browser', lambda r: r['process_observation']['browsers'].append({'pid': 999001, 'ppid': 1, 'lstart': 'Thu Jan  1 00:00:00 1970', 'command': '/Applications/Google Chrome.app/Google Chrome', 'cpu_percent_one_core': 0})),
        ('root browser busy', lambda r: r['process_observation']['browsers'][0].update(cpu_percent_one_core=1.01)),
        ('aggregate browser busy', lambda r: [p.update(cpu_percent_one_core=0.6) for p in r['process_observation']['browsers']]),
    ]:
        value = copy.deepcopy(base)
        modify(value)
        variants.append((name, value, False))
    for name, value, allowed in variants:
        result = evaluate(value)
        check(name, result['allowed'] is allowed, {'input': value, 'decision': result, 'expected': allowed})
    line = '123 1 0.0 10 Tue Oct  6 20:00:00 2026 /usr/bin/python3'
    for name, text, exit_code, own, expected in [
        ('ps good', line, 0, 123, True), ('ps empty', '', 0, 123, False),
        ('ps mixed bad', line + '\nbroken', 0, 123, False), ('ps own missing', line, 0, 999, False),
        ('ps refused', line, 1, 123, False)]:
        result = parse_processes(text, exit_code, own)
        check(name, result['trusted'] is expected, {'input': text, 'result': result})
    state = [0]
    check('priority success', priority_gate(lambda *a: state[0], lambda *a: state.__setitem__(0, a[-1]))['verified_before_exec'])
    check('priority remained low', not priority_gate(lambda *a: 0, lambda *a: None)['verified_before_exec'])
    def reject(*args):
        raise PermissionError('synthetic refusal')
    check('priority refused', not priority_gate(lambda *a: 0, reject)['verified_before_exec'])
    check('cpu limit confirmed', cpu_gate(2, lambda *a: None, lambda *a: (2, 3))['verified_before_exec'])
    check('cpu limit refused', not cpu_gate(2, reject, lambda *a: (2, 3))['verified_before_exec'])
    original_root = run.ROOT
    try:
        with tempfile.TemporaryDirectory(prefix='atlas-causal-guard-', dir=ROOT / 'records') as temp:
            p = Path(temp)
            (p / 'records').mkdir()
            for n in ['resources.py', 'resource_parse.py', 'resource_policy.py']:
                (p / n).write_text('synthetic ' + n)
            (p / 'records/root-browser-reference.json').write_text('{"synthetic": true}')
            (p / 'decision.json').write_text('{"scope": "synthetic"}')
            gate = {'policy_input_hashes': {n: run.digest(p / n) for n in ['resources.py', 'resource_parse.py', 'resource_policy.py']},
                    'root_browser_reference': {'synthetic': True}, 'root_browser_reference_sha256': run.digest(p / 'records/root-browser-reference.json'),
                    'root_batch_decision': {'scope': 'synthetic'}, 'root_batch_decision_file': {'path': str(p / 'decision.json'), 'sha256': run.digest(p / 'decision.json')}}
            run.ROOT = p
            run.check_gate_binding(gate)
            check('binding unchanged', True)
            for name, change in [('policy changed', lambda g: g['policy_input_hashes'].update({'resources.py': '0' * 64})),
                                 ('reference changed', lambda g: g.update(root_browser_reference={})),
                                 ('decision changed', lambda g: g.update(root_batch_decision={}))]:
                changed = copy.deepcopy(gate)
                change(changed)
                try:
                    run.check_gate_binding(changed)
                    check(name, False)
                except RuntimeError:
                    check(name, True)
    finally:
        run.ROOT = original_root
    result = {'project': 'Atlas', 'scope': 'synthetic guard checks only; no producer import/run, no host observation',
              'passed': all(x['passed'] for x in checks), 'check_count': len(checks), 'checks': checks,
              'input_hashes': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ['preflight.py', 'run.py', 'resource_parse.py', 'resource_policy.py', 'priority_launcher.py']},
              'target_launches': 0}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
