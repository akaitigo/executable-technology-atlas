"""Atlas: current decision identity classification on saved synthetic rows, no system read."""
import copy, hashlib, importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('resource_gate', ROOT / 'resource-gate.py')
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
policy = json.loads((ROOT / 'gate-policy.json').read_text())
rows = [{k: value[k] for k in ['pid', 'ppid', 'lstart', 'comm']} | {'cpu': 0.0} for value in policy['known_idle_identities']]
checks = []


def check(name, values, complete, expected):
    observed = gate.assess(values, policy, complete)
    assert observed['process_condition_passed'] is expected, name
    checks.append({'case': name, 'expected': expected, 'observed': observed})


check('all-current-identities', rows, True, True)
check('nonroot-trusted-absence', rows[1:], True, True)
check('required-root-absent', [r for r in rows if r['pid'] != policy['required_present_pids'][-1]], True, False)
check('incomplete', rows, False, False)
check('empty', [], True, False)
for name, change, expected in [
    ('cpu-at-limit', {'cpu': 1.0}, True), ('cpu-above-limit', {'cpu': 1.1}, False),
    ('pid-reused-noncandidate-name', {'comm': '/fixture/python'}, False),
    ('changed-parent', {'ppid': -1}, False), ('changed-start', {'lstart': 'changed'}, False)]:
    values = copy.deepcopy(rows); values[0].update(change); check(name, values, True, expected)
values = copy.deepcopy(rows); values[0]['cpu'] = values[1]['cpu'] = 1.0
check('group-at-limit', values, True, True)
values[2]['cpu'] = 0.1; check('group-above-limit', values, True, False)
check('new-runtime', rows + [{'pid': 1000009, 'ppid': 1, 'lstart': 'synthetic', 'comm': '/fixture/chromium', 'cpu': 0.0}], True, False)
report = {'title': 'Atlas current scoped decision pure-input checks', 'passed': True, 'checks': checks,
          'process_observations': 0, 'target_runs': 0, 'sources': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
          for n in ['resource-gate.py', 'gate-policy.json', 'check-scoped-policy.py']}}
(ROOT / 'observations/scoped-policy-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'cases': len(checks), 'target_runs': 0}))
