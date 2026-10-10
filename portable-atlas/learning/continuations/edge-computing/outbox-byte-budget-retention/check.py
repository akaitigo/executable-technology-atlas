import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(c,v):
    f=v['fixture'];a=v['result'];default=json.loads((ROOT/'fixtures.json').read_text())[c]
    assert v['case']==c and v['utc'].endswith('+00:00') and v['owned_tmp_cleaned'] is True
    assert all(f[k]==x for k,x in default.items() if k!='payload')
    assert set(v['source_binding'])=={'calculate.py','runner.py','readback.py','fixtures.json','hand-oracle.json','oracle.py'}
    for n,h in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h
    e=oracle.independent(f)
    if f==default:assert e==oracle.inspect(c)
    for k,x in e.items():assert a[k]==x,(c,k,a[k],x)
    assert a['producer_connection_closed'] is True
    assert v['sql_readback']==dict(rows=e['rows'],used_bytes=e['used_bytes'],readonly=True,reopened_after_producer_close=True)
    assert len(v['db_sha256_before_cleanup'])==64
    if a['status'] in ['REJECTED','INPUT_REJECTED']:assert a['write_changes']==0 and a['rows']==[dict(id='old',payload_hex='c3a9',bytes=2)]
def verify():
    files=sorted((ROOT/'observations').glob('*/raw.json'));assert files
    for p in files:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for c,v in raw.items():validate(c,v)
    dynamic=json.loads((ROOT/'observations/payload-qa.json').read_text());assert len(dynamic)==6
    for v in dynamic:validate(v['case'],v)
    rejected=[]
    for label,c,k,x in [('character bytes','bad-char-count','used_bytes',4),('oversize erased old','oversize-keeps-old','rows',[]),('reject wrote','reject-new','write_changes',1),('exact rejected','exact-capacity','accepted',False),('policy accepted','unknown-policy','status','APPENDED'),('wrong retained hex','overwrite-oldest','rows',[dict(id='new',payload_hex='c3a9',bytes=2)])]:
        v=copy.deepcopy(raw[c]);v['result'][k]=x
        try:validate(c,v)
        except AssertionError:rejected.append(label);continue
        raise AssertionError('escaped '+label)
    return dict(appended=1,evicted=1,bad_accepted=1,capacity_rejected=2,expected_input_refusals=5,recorded_runs=len(files),dynamic_payload_runs=len(dynamic),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
