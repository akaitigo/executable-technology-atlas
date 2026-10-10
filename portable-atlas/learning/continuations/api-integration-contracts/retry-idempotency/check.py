import argparse, copy, hashlib, json, pathlib, sqlite3
from runner import ROOT, CASES, run, snapshot

def validate(case, actual, expected):
    assert actual['first_client']=={'exception':'RemoteDisconnected','outcome':'unknown'}
    assert actual['after_first']['orders']==[[1,'demo-seat',1]]
    assert actual['after_retry']['orders']==expected['orders']
    assert actual['retry_response']=={key:expected[key] for key in ('status','body','replay')}
    ledger=actual['after_retry']['ledger']; assert len(ledger)==expected['ledger_count']
    if ledger:
        # Separate constant, authored before execution; does not call producer canonical().
        digest=hashlib.sha256(b'{"quantity":1,"sku":"demo-seat"}').hexdigest()
        assert ledger==[['demo-request-1',digest,201,'{"order_id":1,"quantity":1,"sku":"demo-seat"}',1]]
        assert actual['after_first']['ledger']==ledger
    assert actual['after_retry']['integrity']=='ok'
    events=actual['trace']; kinds=[e['kind'] for e in events]
    assert kinds.count('client_send')==2 and kinds.count('explicit_retry')==1
    assert kinds.index('business_commit')<kinds.index('close_before_response')<kinds.index('client_uncertain')<kinds.index('explicit_retry')
    commits=[i for i,e in enumerate(events) if e['kind']=='sql' and e['statement']=='COMMIT']
    assert len(commits)==(2 if case=='no-key' else 1)
    if ledger:
        first_commit=commits[0]; sql=[e['statement'] for e in events[:first_commit] if e['kind']=='sql']
        assert any(s=='BEGIN IMMEDIATE' for s in sql)
        assert any(s.startswith('INSERT INTO orders') for s in sql) and any(s.startswith('INSERT INTO ledger') for s in sql)
    assert all(actual['cleanup'][k] for k in ('server_closed','thread_joined','temporary_database_removed'))

def record():
    folder=ROOT/'observations'; artifacts=folder/'artifacts'; artifacts.mkdir(exist_ok=True)
    values={case:run(case,artifacts/(case+'.sqlite')) for case in CASES}
    (folder/'runs.json').write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n')

def verify():
    expected=json.loads((ROOT/'oracle.json').read_text()); values=json.loads((ROOT/'observations'/'runs.json').read_text())
    rejected=0
    for case in CASES:
        actual=values[case]; validate(case,actual,expected[case])
        db=snapshot(ROOT/'observations'/'artifacts'/(case+'.sqlite'))
        assert json.loads(json.dumps(db))==actual['after_retry']
        for field in ('orders','integrity'):
            mutant=copy.deepcopy(actual); mutant['after_retry'][field]=[] if field=='orders' else 'corrupt'
            try: validate(case,mutant,expected[case])
            except AssertionError: rejected+=1
            else: raise AssertionError('oracle accepted mutant')
    print(json.dumps({'cases':len(CASES),'mutants_rejected':rejected,'sqlite_artifacts':3,'scope':'finite continuation only'}))
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--record',action='store_true'); args=parser.parse_args()
    if args.record: record()
    verify()
