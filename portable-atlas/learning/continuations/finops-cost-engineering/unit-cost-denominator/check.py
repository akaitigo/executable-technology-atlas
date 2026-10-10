import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def pair(x):
    if x is None:return None
    n,d=x['numerator'],x['denominator'];assert type(n) is int and type(d) is int and d>0
    expected=oracle.reduced(n,d);assert expected==[n,d] and x['exact']==(str(n) if d==1 else str(n)+'/'+str(d));return [n,d]
def validate(case,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];h=json.loads((ROOT/'hand-oracle.json').read_text())['cases'][case];r=v['result']
    assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00') and v['runtime']['python']
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    assert r['status']==h['status']
    if r['status']=='INPUT_REJECTED':assert r==dict(status=h['status'],reason=h['reason'],calculation_started=False,periods={},comparison=None);return
    assert r['calculation_started'] is True;o=oracle.inspect(f)
    for k in ['totals','attempts','success','used_denominator','unit_cost','total_ratio','total_change','unit_ratio','unit_change']:assert o[k]==h[k]
    if case=='bad-all-attempts':assert o['strict_unit_cost']==h['strict_unit_cost'] and o['strict_unit_ratio']==h['strict_unit_ratio']
    assert set(r['periods'])=={'baseline','candidate'}
    for i,name in enumerate(['baseline','candidate']):
        p=r['periods'][name];assert p['source_costs']==f[name]['costs'] and p['currency']=='XCU' and p['cost_scope']==f['scope']
        assert [p['total_cents'],p['attempts'],p['success'],p['denominator_used']]==[o['totals'][i],o['attempts'][i],o['success'][i],o['used_denominator'][i]]
        assert p['failed_attempts']==o['attempts'][i]-o['success'][i] and p['declared_unit']=='cent_per_successful_request'
        assert p['denominator_basis']==('attempts' if case=='bad-all-attempts' else 'success') and pair(p['unit_cost'])==o['unit_cost'][i]
        assert p['unit_reason']==('ZERO_DENOMINATOR' if o['used_denominator'][i]==0 else None)
        if p['unit_cost'] is not None:assert p['unit_cost']['numerator']*p['denominator_used']==p['total_cents']*p['unit_cost']['denominator']
    c=r['comparison']
    for k in ['total_ratio','total_change','unit_ratio','unit_change']:assert pair(c[k])==o[k]
    assert c['total_ratio_reason']==('ZERO_BASELINE_TOTAL' if o['totals'][0]==0 else None)
    assert c['unit_ratio_reason']==('UNDEFINED_UNIT' if None in o['unit_cost'] else 'ZERO_BASELINE_UNIT' if o['unit_ratio'] is None else None)
    bad=case=='bad-all-attempts';assert r['bad_judgment']==dict(enabled=bad,claims_unit_improved=bad,rule_failed=bad)
    return o

def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for case,v in raw.items():validate(case,v)
    rejected=[]
    def reject(label,case,edit):
        v=copy.deepcopy(raw[case]);edit(v)
        try:validate(case,v)
        except (AssertionError,KeyError):rejected.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('total cost altered','lower-total-higher-unit',lambda v:v['result']['periods']['candidate'].update(total_cents=40))
    reject('attempt denominator declared successful','lower-total-higher-unit',lambda v:v['result']['periods']['candidate'].update(denominator_used=100))
    reject('unit cost ratio wrong','lower-total-higher-unit',lambda v:v['result']['comparison'].update(unit_ratio={'numerator':3,'denominator':5,'exact':'3/5'}))
    reject('zero success assigned zero unit cost','zero-success',lambda v:v['result']['periods']['candidate'].update(unit_cost={'numerator':0,'denominator':1,'exact':'0'}))
    reject('bad denominator marked safe','bad-all-attempts',lambda v:v['result']['bad_judgment'].update(rule_failed=False))
    reject('invalid input marked started','bool-success',lambda v:v['result'].update(calculation_started=True))
    return dict(strict_cases=6,compared=3,undefined_unit=2,undefined_comparison=1,bad_denominator=1,expected_input_refusals=10,recorded_runs=len(paths),oracle='integer pairs, cross-products + fixed hand Fraction expectations',mutations_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
