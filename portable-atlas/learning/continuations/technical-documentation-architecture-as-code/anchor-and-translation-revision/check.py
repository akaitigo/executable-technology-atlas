import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(case,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];e=oracle.inspect(case);r=v['result']
    assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00') and v['owned_tmp_cleaned'] is True
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    for k,a in e.items():assert r[k]==a,(case,k,r[k],a)
    assert len(r['reads'])==4
    expected=[(n,f['pages'][n]) for n in ['api.html','ja.html','guide.html']]+[('manifest.json',json.dumps(f['manifest'],ensure_ascii=False,sort_keys=True))]
    for row,(name,text) in zip(r['reads'],expected):assert row==dict(path=name,raw=text,sha256=hashlib.sha256(text.encode()).hexdigest())
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for c,v in raw.items():validate(c,v)
    rejected=[]
    for label,c,k,value in [('missing anchor passed','broken-fragment','passed',True),('duplicate anchor unique','duplicate-id','anchor_matches',1),('stale marked fresh','stale-translation','translation_fresh',True),('file-only marked safe','bad-broken','status','PASSED'),('external URL accepted','external-url','status','PASSED'),('cleanup skipped','normal',None,None)]:
        v=copy.deepcopy(raw[c])
        if k is None:v['owned_tmp_cleaned']=False
        else:v['result'][k]=value
        try:validate(c,v)
        except (AssertionError,KeyError):rejected.append(label);continue
        raise AssertionError('escaped '+label)
    return dict(normal_passed=1,strict_semantic_failures=3,file_only_bad_passes=3,expected_subset_refusals=3,recorded_runs=len(paths),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
