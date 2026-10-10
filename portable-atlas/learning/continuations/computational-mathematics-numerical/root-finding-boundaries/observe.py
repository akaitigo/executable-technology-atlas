"""Root-managed single batch. Exactly one JSON on stdout; no subprocesses."""
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from model import calculate, InvalidInput

ROOT = Path(__file__).resolve().parent
SOURCE_FILES = ['model.py', 'observe.py', 'fixtures.json', 'CONTRACT.md', 'contract-lock.json']
SCOPE = {'exact_rational': True, 'floating_point_solver': False, 'scipy_used': False,
         'network_requests': 0, 'browser_launches': 0, 'server_launches': 0,
         'general_convergence_claim': False}


def bad_inputs(fixture):
    mutations = [
        ('budget-bool', ['max_updates'], True), ('budget-float', ['max_updates'], 4.0),
        ('budget-negative', ['max_updates'], -1), ('budget-excess', ['max_updates'], 100),
        ('width-zero', ['width_tolerance'], '0'), ('width-float', ['width_tolerance'], 0.125),
        ('residual-negative', ['residual_tolerance'], '-1'), ('step-noncanonical', ['step_tolerance'], '2/32'),
        ('unknown-polynomial', ['cases',0,'polynomial'], 'eval'), ('x0-float', ['cases',0,'x0'], 0.0),
        ('x0-zero-denominator', ['cases',0,'x0'], '1/0'), ('x0-changed', ['cases',0,'x0'], '1'),
        ('reversed-bracket', ['cases',0,'bracket'], ['0','-2']), ('equal-bracket', ['cases',0,'bracket'], ['0','0']),
        ('unknown-id', ['cases',0,'id'], 'other'), ('missing-case', ['cases'], fixture['cases'][:-1]),
        ('extra-key', ['unrecognized'], True)]
    for name, path, value in mutations:
        request = copy.deepcopy(fixture)
        obj = request
        for key in path[:-1]:
            obj = obj[key]
        obj[path[-1]] = value
        yield name, request


def main():
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    if nice != 10:
        raise RuntimeError('actual nice must be 10 before target calculation')
    fixture = json.loads((ROOT/'fixtures.json').read_text())
    values = calculate(fixture)
    refusals = []
    for name, request in bad_inputs(fixture):
        try:
            calculate(request)
        except InvalidInput as exc:
            refusals.append(dict(id=name, rejected=True, reason=str(exc), updates=exc.updates))
        else:
            raise AssertionError('invalid input accepted: '+name)
    now = datetime.now(timezone.utc)
    data = dict(schema='atlas-root-boundaries-run-v1',
                run=dict(run_id='root-boundaries-'+now.strftime('%Y%m%dT%H%M%S%fZ'),
                         observed_at_utc=now.isoformat(), pid=os.getpid(), actual_nice=nice,
                         source_hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCE_FILES}),
                scope=SCOPE, fixture=fixture, values=values, input_rejections=refusals)
    sys.stdout.write(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)+'\n')


if __name__ == '__main__':
    main()
