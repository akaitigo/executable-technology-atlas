"""Atlas: collect one finite read/add calculation; no external tools or services."""
import copy, datetime, hashlib, json, os, platform, sys
from pathlib import Path
from model import execute

ROOT = Path(__file__).resolve().parent

def refusals(base):
    changes = [
        ('unknown-tool', lambda x: x['input']['plan']['nodes'][1].update(tool='send')),
        ('unknown-reference', lambda x: x['input']['plan']['nodes'][1]['args']['a'].update(ref='old')),
        ('extra-input', lambda x: x['input'].update(extra=True)),
        ('time-bool', lambda x: x['input'].update(now=True)),
        ('time-negative', lambda x: x['input'].update(now=-1)),
        ('time-over', lambda x: x['input'].update(now=21)),
        ('time-float', lambda x: x['input'].update(now=9.0)),
        ('invalid-actor', lambda x: x['input'].update(actor='unknown')),
        ('invalid-policy', lambda x: x.update(policy='allow-all')),
        ('approval-arg-bool', lambda x: x['input']['approval']['args'].update(a=True)),
        ('approval-extra', lambda x: x['input']['approval'].update(signed=True)),
        ('invalid-hash', lambda x: x['input']['approval'].update(plan_sha256='x'*64)),
    ]
    result = []
    for name, mutate in changes:
        case = copy.deepcopy(base); mutate(case)
        try:
            execute(case)
        except ValueError as error:
            result.append({'id': name, 'status': 'input-refused', 'read_calls': 0, 'add_calls': 0, 'error': str(error)})
        else:
            raise AssertionError('invalid fixture was accepted: '+name)
    return result

def main():
    priority = os.getpriority(os.PRIO_PROCESS, 0)
    if priority != 10:
        raise RuntimeError('Atlas: actual nice 10 required before calculation')
    fixtures = json.loads((ROOT/'fixtures.json').read_text())
    result = {
        'title': 'Atlas exact call authorization saved calculation', 'schema': 1, 'status': 'observed',
        'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runtime': {'python': platform.python_version(), 'platform': platform.platform(), 'machine': platform.machine()},
        'priority_observed': priority,
        'fixture_sha256': hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),
        'cases': [execute(case) for case in fixtures['cases']],
        'input_refusals': refusals(fixtures['cases'][0]),
        'scope': {'external_tools': 0, 'llm_calls': 0, 'network_calls': 0, 'real_approval': False,
                  'browser_executed': False, 'server_started': False, 'persistent_effects': 0},
    }
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))

if __name__ == '__main__':
    main()
