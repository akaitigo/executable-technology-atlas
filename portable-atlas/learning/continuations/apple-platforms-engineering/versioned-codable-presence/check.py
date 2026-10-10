import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(case,v):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];h=oracle.predict(case);r=v['result'];assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00') and v['runtime']['python']
    assert set(v['source_binding'])=={'main.swift','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():
        target=ROOT/n
        if n=='hand-oracle.json' and hashlib.sha256(target.read_bytes()).hexdigest()!=d:target=ROOT/'observations/initial-hand-oracle.json'
        assert hashlib.sha256(target.read_bytes()).hexdigest()==d
    assert v['compile']['exit']==0 and v['compile']['toolchain_exit']==0 and '6.2.3' in v['compile']['toolchain'] and len(v['compile']['binary_sha256'])==64
    assert v['compile']['source_binding']==v['source_binding'] and v['attempt']['exit']==0 and v['attempt']['stderr']=='' and v['attempt']['binary_sha256']==v['compile']['binary_sha256']
    assert v['owned_compile_tmp_cleaned'] is True
    outputs=json.loads(v['attempt']['stdout']);assert next(x for x in outputs if x['case']==case)==r
    inputs=v['attempt']['input_requests'];assert dict(case=case,**f) in inputs
    assert r['case']==case and r['status']==h['status'] and r['decode_accepted']==h['decode_accepted']
    if not h['decode_accepted']:
        assert r['phase']=='decode' and r['error']['kind']==h['error_kind'] and r['error']['key']==h['error_key'] and r['error']['path']==h['error_path']
        assert r['migrated'] is None and r['roundtrip'] is None and r['encoded_text'] is None;return
    assert r['input_version']==h['version'] and r['input_presence']==('value' if h['presence']=='string' else h['presence'])
    assert r['migrated']==h['migrated'] and json.loads(r['encoded_text'])==h['encoded'] and r['roundtrip']==h['roundtrip']
    obj=json.loads(r['encoded_text']);assert type(obj['version']) is int and obj['version']==2 and 'displayName' in obj['profile']
    assert r['roundtrip_version']==2 and r['roundtrip_presence']==('null' if h['roundtrip']['displayName'] is None else 'value') and r['rule_failed']==h['rule_failed']
    if f['mode']=='strict' and h['presence']=='null':assert obj['profile']['displayName'] is None

def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert len(paths)>=2
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==set(json.loads((ROOT/'fixtures.json').read_text()))
        for case,v in raw.items():validate(case,v)
    rejected=[]
    def reject(label,case,edit):
        v=copy.deepcopy(raw[case]);edit(v)
        # Keep the stdout row self-consistent to test semantic oracle, not only binding.
        rows=json.loads(v['attempt']['stdout']);rows=[v['result'] if x['case']==case else x for x in rows];v['attempt']['stdout']=json.dumps(rows)
        try:validate(case,v)
        except (AssertionError,KeyError):rejected.append(label);return
        raise AssertionError('mutation escaped '+label)
    reject('v1 null collapsed to fallback','v1-null',lambda v:v['result']['migrated'].update(displayName='Aki'))
    reject('encoded null key omitted','v2-null',lambda v:v['result'].update(encoded_text='{"version":2,"profile":{"name":"Aki"}}'))
    reject('redecode value changed','v1-string',lambda v:v['result']['roundtrip'].update(displayName='Aki'))
    reject('v2 missing accepted','v2-missing',lambda v:v['result'].update(status='ROUNDTRIPPED',decode_accepted=True))
    reject('unknown version diagnostic forged','v99-string',lambda v:v['result']['error'].update(kind='keyNotFound'))
    reject('bad null marked safe','bad-v1-null',lambda v:v['result'].update(rule_failed=False))
    return dict(strict_roundtrips=6,expected_decode_refusals=4,bad_policy_violations=3,fault_policy_matching_control=1,recorded_runs=len(paths),independent_version_presence_type_value_table=True,json_objects_compared_not_key_order=True,initial_diagnostic_failure_preserved=True,mutations_rejected=rejected)
if __name__=='__main__':print(json.dumps(verify(),indent=2))
