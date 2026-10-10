"""Read-only verifier; no imports of solver/reference/runner."""
import copy,hashlib,json,math,pathlib
from fractions import Fraction as F
ROOT=pathlib.Path(__file__).resolve().parent
def norm(v):return max(abs(x) for x in v)
def vector(v):return list(map(F,v))
def matvec(a,x):return [sum(p*q for p,q in zip(row,x)) for row in a]
def check_scalar(value,want):assert F(value['exact'])==want and value['float']==float(want)
def validate(case,v):
    fixtures=json.loads((ROOT/'fixtures.json').read_text());hand=json.loads((ROOT/'oracle.json').read_text());f=fixtures[case];h=hand[case];r=v['result'];ref=v['references'];assert v['case']==case and v['fixture']==f and r['status']==h['status']
    for n,digest in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==digest
    assert set(v['source_binding'])=={'solver.py','reference.py','runner.py','fixtures.json','oracle.json'}
    assert v['utc'].endswith('+00:00') and v['runtime']['python']
    if h['status']=='INPUT_REJECTED':assert r==h and ref is None;return
    assert r['solver_started'] is True;e=F(f['epsilon']);delta=F(f['delta']);d=ref['decimal'];c=ref['computed'];q=ref['float_inputs']
    expected=[1-delta/e,1+delta/e];assert vector(d['x_perturbed'])==expected==vector(h['decimal_solution']);assert d['change']==h['decimal_change'] and d['change_inf']==h['decimal_change_inf']
    ad=[[F(1),F(1)],[F(1),1+e]];bd=[F(2),2+e];bp=[bd[0],bd[1]+delta]
    assert [vector(row) for row in d['A']]==ad and vector(d['b_original'])==bd and vector(d['b_perturbed'])==bp and d['x_baseline']==['1','1']
    assert d['residual_perturbed']==h['decimal_residual_perturbed'] and d['residual_original']==h['decimal_residual_original']
    assert matvec(ad,expected)==bp and [a-b for a,b in zip(matvec(ad,expected),bd)]==[F(0),delta]
    assert F(d['input_change_inf'])==delta and F(d['input_relative_change_inf'])==delta/norm(bd)
    assert F(d['solution_relative_change_inf'])==delta/e and F(d['directional_relative_amplification'])==(2+e)/e
    # Matrix norm definition: independently use explicit inverse rows and row sums.
    inverse=[[(1+e)/e,-1/e],[-1/e,1/e]];kappa=max(sum(map(abs,row)) for row in ad)*max(sum(map(abs,row)) for row in inverse)
    assert F(d['condition_inf'])==kappa==F(h['condition_inf'])
    af=[[F.from_float(x) for x in row] for row in r['A']];bf=list(map(F.from_float,r['b_original']));bpf=list(map(F.from_float,r['b_perturbed']));xf=vector(q['x_perturbed']);xf0=vector(q['x_baseline']);actual=list(map(F.from_float,r['x_float_perturbed']));baseline=list(map(F.from_float,r['x_float_baseline']))
    assert [vector(row) for row in q['A']]==af and vector(q['b_original'])==bf and vector(q['b_perturbed'])==bpf
    assert af[0]==[F(1),F(1)] and af[1][0]==1 and af[1][1]!=1
    assert af[1][1]==F.from_float(1.0+float(f['epsilon'])) and bf==[F(2),F.from_float(r['A'][1][1]+1.0)]
    assert bpf==[bf[0],F.from_float(float(bf[1])+float(f['delta']))]
    # Nonsingularity plus exact equations uniquely certify both float-input oracles.
    assert matvec(af,xf)==bpf and matvec(af,xf0)==bf and vector(q['change'])==[xf[i]-xf0[i] for i in range(2)]
    check_scalar(c['forward_error_decimal_inf'],norm([actual[i]-expected[i] for i in range(2)]));check_scalar(c['forward_error_float_inputs_inf'],norm([actual[i]-xf[i] for i in range(2)]));check_scalar(c['oracle_conversion_shift_inf'],norm([expected[i]-xf[i] for i in range(2)]));check_scalar(c['distance_from_original_inf'],norm([x-1 for x in actual]))
    assert c['forward_error_float_inputs_inf']['float']<1e-12 and c['forward_error_decimal_inf']['float']<1e-10
    for label,a,b in [('decimal_perturbed',ad,bp),('decimal_original',ad,bd),('float_perturbed',af,bpf),('float_original',af,bf)]:assert vector(c['exact_residual_'+label])==[a-b for a,b in zip(matvec(a,actual),b)]
    m=r['float_metrics'];expected_metrics=dict(input_change_inf=float(norm([bpf[i]-bf[i] for i in range(2)])),solution_change_inf=float(norm([actual[i]-baseline[i] for i in range(2)])),distance_from_original_inf=float(norm([x-1 for x in actual])))
    expected_metrics['input_relative_change_inf']=expected_metrics['input_change_inf']/float(norm(bf));expected_metrics['solution_relative_change_inf']=expected_metrics['solution_change_inf']/float(norm(baseline))
    for k,want in expected_metrics.items():assert math.isclose(m[k],want,rel_tol=1e-14,abs_tol=1e-20),(case,k)
    for label,b in [('perturbed',bpf),('original',bf)]:
        exact=[a-b for a,b in zip(matvec(af,actual),b)];observed=m['residual_'+label];assert all(abs(F.from_float(x)-y)<F('0.000000000000004') for x,y in zip(observed,exact));assert m['residual_'+label+'_inf']==norm(observed)
    assert m['residual_perturbed_inf']<=1e-12 and m['distance_from_original_inf']>1e-6
    bad=r['bad_judgment'];assert bad['enabled']==(f['judgment']=='residual-only') and bad['bad_rule_failed']==h['bad_rule_failed'] and bad['actually_original_near'] is False
    assert bad['claims_original_near']==(True if bad['enabled'] else None)
    assert [e['event'] for e in r['trace']['perturbed']]==['eliminate','back_substitute'] and r['trace']['perturbed'][-1]['x']==r['x_float_perturbed']
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths;fixtures=json.loads((ROOT/'fixtures.json').read_text())
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(fixtures)
        for n,v in raw.items():validate(n,v)
    mutations=[]
    def reject(label,case,edit):
        v=copy.deepcopy(raw[case]);edit(v)
        try:validate(case,v)
        except (AssertionError,KeyError):mutations.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('wrong decimal solution','epsilon-0.0001',lambda v:v['references']['decimal']['x_perturbed'].__setitem__(0,'1'))
    reject('decimal oracle substituted for float oracle','epsilon-0.0001',lambda v:v['references']['float_inputs'].update(x_perturbed=['99/100','101/100']))
    reject('original residual hidden','epsilon-0.1',lambda v:v['result']['float_metrics'].update(residual_original=[0.0,0.0],residual_original_inf=0.0))
    reject('bad judgment declared correct','bad-residual-only',lambda v:v['result']['bad_judgment'].update(bad_rule_failed=False))
    reject('solver started for rejected singular case','singular-refusal',lambda v:v['result'].update(solver_started=True))
    return dict(normal_cases=2,bad_judgment_comparisons=1,expected_domain_refusals=1,recorded_runs=len(paths),dual_exact_oracles=True,mutations_rejected=mutations)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
