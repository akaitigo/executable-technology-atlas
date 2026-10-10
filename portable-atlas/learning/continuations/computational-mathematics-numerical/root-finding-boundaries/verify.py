"""Read saved JSON only. Never imports or executes the root-finding producer."""
import argparse
import copy
import hashlib
import json
from datetime import datetime
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REFUSALS = ['budget-bool','budget-float','budget-negative','budget-excess','width-zero','width-float',
            'residual-negative','step-noncanonical','unknown-polynomial','x0-float','x0-zero-denominator',
            'x0-changed','reversed-bracket','equal-bracket','unknown-id','missing-case','extra-key']


def exact(a, b):
    assert type(a) is type(b), ('type', type(a).__name__, type(b).__name__)
    if isinstance(a, dict):
        assert a.keys() == b.keys(), 'keys'
        for key in a:
            exact(a[key], b[key])
    elif isinstance(a, list):
        assert len(a) == len(b), 'length'
        for x, y in zip(a, b):
            exact(x, y)
    else:
        assert a == b, ('value', a, b)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polynomial(name, x):
    # Independent coefficient expansion, no producer import or iteration.
    coefficients = {'cubic': [2,-2,0,1], 'quadratic': [-2,0,1], 'square':[0,0,1]}[name]
    value = sum(F(c)*x**i for i,c in enumerate(coefficients))
    derivative = sum(F(i*c)*x**(i-1) for i,c in enumerate(coefficients) if i)
    return value, derivative


def check(data):
    assert set(data) == {'schema','run','scope','fixture','values','input_rejections'}
    assert data['schema'] == 'atlas-root-boundaries-run-v1'
    fixture = json.loads((ROOT/'fixtures.json').read_text())
    oracle = json.loads((ROOT/'hand-oracle.json').read_text())
    exact(data['fixture'], fixture)
    exact(data['values'], oracle)  # literal expectations locked before implementation
    exact(data['scope'], {'exact_rational': True, 'floating_point_solver': False, 'scipy_used': False,
                         'network_requests':0, 'browser_launches':0, 'server_launches':0,
                         'general_convergence_claim':False})
    exact(data['input_rejections'], [dict(id=n,rejected=True,reason='FIXED_INPUT_REQUIRED',updates=0) for n in REFUSALS])
    run = data['run']
    assert set(run) == {'run_id','observed_at_utc','pid','actual_nice','source_hashes'}
    assert type(run['pid']) is int and run['pid'] > 0
    assert type(run['actual_nice']) is int and run['actual_nice'] == 10
    timestamp = datetime.fromisoformat(run['observed_at_utc'])
    assert timestamp.utcoffset() is not None and timestamp.utcoffset().total_seconds() == 0
    assert run['run_id'] == 'root-boundaries-'+timestamp.strftime('%Y%m%dT%H%M%S%fZ')
    source_names = ['model.py','observe.py','fixtures.json','CONTRACT.md','contract-lock.json']
    exact(run['source_hashes'], {name:sha(ROOT/name) for name in source_names})
    lock = json.loads((ROOT/'contract-lock.json').read_text())
    for name, digest in lock['files'].items():
        assert sha(ROOT/name) == digest, 'contract bytes changed: '+name

    for case, inp in zip(data['values']['cases'], fixture['cases']):
        name = inp['polynomial']
        br = case['bisection']
        validation = br['validation']
        for key, fkey in [('a','fa'),('b','fb')]:
            assert polynomial(name,F(validation[key]))[0] == F(validation[fkey])
        for row in br['rows']:
            a,b,x = (F(row[key]) for key in ['a','b','estimate'])
            assert a <= x <= b and 2*x == a+b
            assert F(row['width']) == b-a and 2*F(row['radius']) == b-a
            assert polynomial(name,x)[0] == F(row['f'])
            assert F(row['residual']) == abs(F(row['f']))
            assert polynomial(name,a)[0] == F(row['fa']) and polynomial(name,b)[0] == F(row['fb'])
            assert F(row['fa'])*F(row['fb']) <= 0
            assert row['width_met'] == (b-a <= F('1/8'))
            if row['k']:
                prev = br['rows'][row['k']-1]
                assert row['probe'] == prev['estimate'] and row['probe_f'] == prev['f']
                assert F(prev['a']) <= a <= b <= F(prev['b'])
                assert F(prev['width']) == 2*F(row['width'])
        for row in case['newton']['rows']:
            x=F(row['x']); fx,df=polynomial(name,x)
            assert str(fx)==row['f'] and str(df)==row['df'] and abs(fx)==F(row['residual'])
            assert row['residual_met'] == (abs(fx)<=F('1/16'))
            if row['k']:
                prev=case['newton']['rows'][row['k']-1]
                delta=x-F(prev['x'])
                assert F(prev['df'])*delta + F(prev['f']) == 0  # tangent zero identity
                assert str(delta)==row['delta'] and str(abs(delta))==row['step']
                assert row['step_met'] == (abs(delta)<=F('1/16'))
            else:
                assert row['delta'] is None and row['step'] is None and row['step_met'] is None
    return {'cases':5,'method_results':10,'saved_boundaries':29,'saved_updates':20,'input_rejections':17}


def tamper_checks(data):
    edits = [
        ('wrong-return', ['values','cases',0,'bisection','estimate'], '-15/8'),
        ('wrong-radius', ['values','cases',0,'bisection','radius'], '1/8'),
        ('probe-vs-candidate', ['values','cases',0,'bisection','rows',4,'probe'], '-29/16'),
        ('changed-sign', ['values','cases',0,'bisection','rows',4,'fa'], '431/512'),
        ('cycle-as-success', ['values','cases',0,'newton','status'], 'LOCAL_TOLERANCES_MET'),
        ('cycle-early-stop', ['values','cases',0,'newton','updates'], 2),
        ('derivative-zero-update', ['values','cases',2,'newton','updates'], 1),
        ('null-to-zero', ['values','cases',2,'newton','step'], '0'),
        ('invalid-bracket-estimate', ['values','cases',3,'bisection','estimate'], '5/2'),
        ('residual-only-success', ['values','cases',3,'newton','rows',2,'status'], 'LOCAL_TOLERANCES_MET'),
        ('step-bool', ['values','cases',3,'newton','rows',2,'step_met'], 0),
        ('exact-vs-derivative', ['values','cases',4,'newton','status'], 'ZERO_DERIVATIVE'),
        ('scope-overclaim', ['scope','floating_point_solver'], True),
        ('nice-changed', ['run','actual_nice'], 0),
        ('refusal-updated', ['input_rejections',0,'updates'], 1),
        ('fixture-budget-float', ['fixture','max_updates'], 4.0)]
    result=[]
    for name,path,value in edits:
        bad=copy.deepcopy(data); target=bad
        for key in path[:-1]:target=target[key]
        target[path[-1]]=value
        try:check(bad)
        except (AssertionError,ValueError,KeyError,TypeError):result.append(dict(id=name,rejected=True))
        else:raise AssertionError('saved tamper accepted: '+name)
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--result',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args()
    data=json.loads(args.result.read_text())
    checked=check(data)
    report=dict(passed=True,result_path=str(args.result.resolve()),result_sha256=sha(args.result),
                verify_source_sha256=sha(Path(__file__)),run_id=data['run']['run_id'],
                checked=checked,tamper_checks=tamper_checks(data),producer_executions=0)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
