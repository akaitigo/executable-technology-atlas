import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(case,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];e=oracle.inspect(case);r=v['result']
    assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00') and v['owned_tmp_cleaned'] is True and v['host_xdg_read_or_changed'] is False
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    for k,a in e.items():assert r[k]==a,(case,k)
    assert r['resolution_started']==(case!='outside-id') and len(r['trace'])==len(e['visited'])
    for row,source in zip(r['trace'],e['visited']):
        text=f[source];assert row['source']==source and row['path']==source+'/applications/org.example.Mock.desktop' and row['exists']==(text is not None)
        if text is None:assert set(row)=={'source','path','exists'};continue
        assert row['raw']==text and row['sha256']==hashlib.sha256(text.encode()).hexdigest()
        if case not in ['invalid-bool','duplicate-key']:
            assert row['fields']==dict(Type='Application',Name='User Mock' if source=='user' else 'System Mock',Exec='atlas-mock',Hidden='true' if source=='user' and case in ['hidden-user','bad-skip-hidden'] else 'false')
            assert row['action']==('BAD_SKIP' if case=='bad-skip-hidden' and source=='user' else 'SUPPRESS' if case=='hidden-user' else 'SELECT')
    if r['count']:assert r['name']==('User Mock' if e['selected_source']=='user' else 'System Mock')
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    cases=set(json.loads((ROOT/'fixtures.json').read_text()))
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==cases
        for c,v in raw.items():validate(c,v)
    failure_path=ROOT/'observations/actual-read-failure.json'
    if failure_path.exists():
        failure=json.loads(failure_path.read_text());assert failure['owned_tmp_cleaned'] is True and failure['actual_file_read_failure'] is True and failure['controlled_invalid_bytes'] is True
        assert failure['result']==dict(status='EXECUTION_FAILURE',phase='owned actual file UTF-8 decode',error='UnicodeDecodeError',encoding='utf-8',start=0,end=1,input_hex='ff',partial=dict(source='user',read_bytes_completed=True))
    rejected=[]
    for label,c,k,value in [('system beats user','both','selected_source','system'),('Hidden falls through','hidden-user','count',1),('bad marked selected','bad-skip-hidden','status','SELECTED'),('missing fabricated','absent','selected_source','system'),('bool accepted','invalid-bool','status','SELECTED'),('outside traversed','outside-id','resolution_started',True)]:
        v=copy.deepcopy(raw[c]);v['result'][k]=value
        try:validate(c,v)
        except (AssertionError,KeyError):rejected.append(label);continue
        raise AssertionError('escaped '+label)
    return dict(selected=2,suppressed=1,not_found=1,bad_resurrection=1,expected_subset_refusals=3,recorded_runs=len(paths),mutants_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
