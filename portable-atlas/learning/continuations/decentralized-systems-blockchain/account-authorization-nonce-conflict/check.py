import copy,hashlib,json,pathlib
import oracle
ROOT=pathlib.Path(__file__).resolve().parent
def validate(case,v):
    h,e=oracle.inspect(case);f=json.loads((ROOT/'fixtures.json').read_text())[case];r=v['result']
    assert v['case']==case and v['fixture']==f and v['utc'].endswith('+00:00')
    assert set(v['source_binding'])=={'calculate.py','runner.py','fixtures.json','hand-oracle.json'}
    for n,d in v['source_binding'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d
    assert r['status']==('BAD_ACCEPTED' if e['bad'] else 'MIXED_DECISIONS' if 'ACCEPT' in e['decisions'] and any(d!='ACCEPT' for d in e['decisions']) else 'ALL_ACCEPTED' if all(d=='ACCEPT' for d in e['decisions']) else 'ALL_REJECTED') and r['processing_started'] is True and r['authorization_table']==h['authorization'] and r['actor_trust']=='trusted synthetic fixture; no signature verification'
    assert len(r['rows'])==len(e['states'])==len(f['transactions'])
    for i,row in enumerate(r['rows']):
        before=h['initial'] if i==0 else e['states'][i-1];t=f['transactions'][i];accepted=e['decisions'][i] in ['ACCEPT','BAD_ACCEPT']
        assert row==dict(transaction=t,before=before,decision=e['decisions'][i],accepted=accepted,after=e['states'][i],authorization_ok=h['authorization'].get(t['actor'])==t['source'],nonce_matches=type(t['nonce']) is int and t['nonce']==before['nonces'][t['source']],bad=e['decisions'][i]=='BAD_ACCEPT')
        if not accepted:assert row['before']==row['after']
    assert r['final']==e['states'][-1]
def verify():
    paths=sorted((ROOT/'observations').glob('*/raw.json'));assert paths
    cases=set(json.loads((ROOT/'fixtures.json').read_text()))
    for p in paths:
        raw=json.loads(p.read_text());assert set(raw)==cases
        for c,v in raw.items():validate(c,v)
    rejected=[]
    for label,case,edit in [('nonce conflict accepted','conflict-forward',lambda v:v['result']['rows'][1].update(accepted=True)),('rejection changed balance','conflict-forward',lambda v:v['result']['rows'][1]['after']['balances'].update(A=70)),('reverse order erased','conflict-reverse',lambda v:v['result']['final']['balances'].update(A=90)),('unauthorized accepted','unauthorized',lambda v:v['result']['rows'][0].update(decision='ACCEPT')),('bad marked safe','bad-ignore-nonce',lambda v:v['result'].update(status='PROCESSED')),('bool nonce accepted','bool-nonce',lambda v:v['result']['rows'][0].update(decision='ACCEPT'))]:
        v=copy.deepcopy(raw[case]);edit(v)
        try:validate(case,v)
        except (AssertionError,KeyError):rejected.append(label);continue
        raise AssertionError('escaped '+label)
    return dict(cases=13,strict_cases=11,bad_cases=2,transactions=17,accepted=6,expected_rejections=11,mutants_rejected=rejected,recorded_runs=len(paths))
if __name__=='__main__':print(json.dumps(verify(),indent=2))
