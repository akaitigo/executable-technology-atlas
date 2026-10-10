"""Atlas: record four finite logical-time cases; no sleep, network, worker or scheduler."""
import copy, datetime, hashlib, json, os, platform
from pathlib import Path
from model import execute

ROOT = Path(__file__).resolve().parent


def refusal_inputs(base):
    changes = [
        ('schema-bool', 'INTEGER_REQUIRED', lambda f: f.update(schema=True)),
        ('budget-float', 'INTEGER_REQUIRED', lambda f: f.update(retry_budget=2.0)),
        ('delay-bool', 'INTEGER_REQUIRED', lambda f: f.update(retry_delay=True)),
        ('missing-field', 'SCHEMA', lambda f: f.pop('retry_delay')),
        ('extra-field', 'SCHEMA', lambda f: f.update(real_worker=True)),
        ('reverse-edge', 'FIXED_INPUT', lambda f: f.update(edge=['D', 'B'])),
        ('negative-budget', 'FIXED_INPUT', lambda f: f.update(retry_budget=-1)),
        ('zero-delay', 'FIXED_INPUT', lambda f: f.update(retry_delay=0)),
        ('different-duration', 'FIXED_INPUT', lambda f: f.update(attempt_duration=2)),
        ('different-result', 'FIXED_INPUT', lambda f: f.update(b_success_value=100)),
        ('missing-case', 'CASE_SCHEMA', lambda f: f['cases'].pop()),
        ('unknown-error', 'FAILURE_LABEL', lambda f: f['cases'][0]['outcomes'].__setitem__(0, 'HTTP_503')),
        ('nonstring-error', 'FAILURE_LABEL', lambda f: f['cases'][0]['outcomes'].__setitem__(0, 503)),
        ('future-success-changed', 'FIXED_CASE', lambda f: f['cases'][1].update(outcomes=['PERMANENT', 'TRANSIENT'])),
        ('unknown-mode', 'FIXED_CASE', lambda f: f['cases'][0].update(downstream_mode='eager')),
        ('case-extra-field', 'CASE_SCHEMA', lambda f: f['cases'][0].update(timeout=10)),
    ]
    for name, reason, change in changes:
        value = copy.deepcopy(base); change(value)
        yield name, reason, value, 'retryable-resume'
    yield 'unknown-case', 'UNKNOWN_CASE', copy.deepcopy(base), 'live-airflow'


def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('actual nice 10 required before model execution')
    fixture = json.loads((ROOT / 'fixtures.json').read_text())
    cases = [execute(fixture, c['id']) for c in fixture['cases']]
    refusals = []
    for name, reason, value, case_id in refusal_inputs(fixture):
        try:
            execute(value, case_id)
        except ValueError as e:
            assert str(e) == reason, (name, str(e), reason)
            refusals.append({'id': name, 'status': 'INPUT_REFUSED', 'reason': str(e),
                             'b_calls': 0, 'd_calls': 0, 'boundaries': [], 'value': None})
        else:
            raise AssertionError('invalid input accepted: ' + name)
    result = {'title': 'Atlas retry readiness saved calculation', 'schema': 1, 'status': 'observed',
        'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runtime': {'python': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine()},
        'priority_observed': priority, 'fixture_sha256': hashlib.sha256((ROOT / 'fixtures.json').read_bytes()).hexdigest(),
        'cases': cases, 'input_refusals': refusals,
        'scope': {'model_only': True, 'logical_time': True, 'real_sleep_calls': 0, 'network_requests': 0,
                  'worker_runs': 0, 'airflow_runs': 0, 'browser_executed': False, 'server_started': False}}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
