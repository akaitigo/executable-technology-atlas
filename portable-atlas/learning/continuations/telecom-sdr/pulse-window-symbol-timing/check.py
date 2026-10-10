import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(key,v):
    case,off=key.split('@');off=int(off);e=oracle.inspect(case,off);r=v['result']
    assert v['case']==case and v['offset']==off and v['utc'].endswith('+00:00')
    assert v['fixture']==json.loads((ROOT/'fixtures.json').read_text())[case]
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    for k,value in e.items():assert r[k]==value,(key,k,r[k],value)
    if not e['convolution_started']:assert r==e;return
    assert r['known_transmitted_bits']==[0,1,0]
    x=v['fixture']['impulses'];h=v['fixture']['pulse'];totals=[0]*len(r['samples'])
    assert len(r['products'])==len(x)*len(h)
    for step,(i,j) in zip(r['products'],((i,j) for i in range(len(x)) for j in range(len(h)))):
        totals[i+j]+=x[i]*h[j]
        assert step==dict(input_index=i,pulse_index=j,output_index=i+j,product=x[i]*h[j],running_sum=totals[i+j])
    assert totals==e['samples']
    for row,indices,mean,bit in zip(r['rows'],e['windows'],e['means'],e['decisions']):
        vals=[e['samples'][i] if i<len(e['samples']) else 0 for i in indices]
        n,d=(map(int,mean.split('/')) if '/' in mean else (int(mean),1))
        assert row==dict(indices=indices,values=vals,provenance=['convolution' if i<len(e['samples']) else 'declared_zero_padding' for i in indices],sum=sum(vals),mean=dict(numerator=n,denominator=d,exact=mean),decision=bit)
    assert len(r['rows'])==3
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    expected=set(json.loads((ROOT/'hand-oracle.json').read_text())['cases'])
    for path in paths:
        raw=json.loads(path.read_text());assert set(raw)==expected
        for key,v in raw.items():validate(key,v)
    rejected=[]
    def mutation(label,key,edit):
        v=copy.deepcopy(raw[key]);edit(v)
        try:validate(key,v)
        except (AssertionError,KeyError):rejected.append(label);return
        raise AssertionError('escaped '+label)
    mutation('wrong sample','short-pad@0',lambda v:v['result']['samples'].__setitem__(2,1))
    mutation('offset ignored','short-pad@1',lambda v:v['result']['windows'].__setitem__(0,[0,1]))
    mutation('padding called observed','short-pad@1',lambda v:v['result']['rows'][2]['provenance'].__setitem__(1,'convolution'))
    mutation('zero collapsed','long@0',lambda v:v['result']['decisions'].__setitem__(1,0))
    mutation('bad marked safe','bad-zero-bit@0',lambda v:v['result'].update(rule_failed=False))
    mutation('missing window executed','short-no-pad@1',lambda v:v['result'].update(convolution_started=True))
    return dict(strict_windowed=5,expected_window_refusals=1,bad_acceptances=1,fault_controls=1,recorded_runs=len(paths),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
