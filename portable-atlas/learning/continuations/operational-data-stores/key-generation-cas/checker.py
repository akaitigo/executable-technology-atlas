import copy,hashlib,json,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check_rows(raw,c,e):
    rows={r['id']:r for r in raw['rows']};assert len(rows)==len(raw['rows'])==11
    for s in c['cases']:
        r=rows[s['id']];assert r['status']=='accepted-experiment' and r['mode']==s['mode'] and r['lifetime']==s['lifetime']
        expected=e['cases'][s['id']];steps=r['steps'];assert len(steps)==len(expected)
        for i,(step,want) in enumerate(zip(steps,expected)):
            assert step['rowcount']==want['rowcount'] and step['state']==want['state']
            assert step['before']==(None if i==0 else expected[i-1]['state'])
        assert r['old_request_rowcount']==expected[-2]['rowcount'] and r['fresh_request_rowcount']==1 and r['final']==expected[-1]['state']
        labels=['create-g1','fresh-v1','old-v1','fresh-v2'] if s['lifetime']=='same' else ['create-g1','delete-g1','recreate-g2','old-g1-v1','fresh-g2']
        assert [t['label'] for t in steps]==labels
        assert steps[0]['sql']=='INSERT INTO kv VALUES(?,?,?,?)' and steps[0]['params']==['k','g1',1,0]
        updates=[t for t in steps if t['sql'].startswith('UPDATE')]
        sql='UPDATE kv SET value=?, version=version+1 WHERE key=? AND version=?' if s['mode']=='version' else 'UPDATE kv SET value=?, version=version+1 WHERE key=? AND generation=? AND version=?'
        assert all(t['sql']==sql for t in updates)
        # Manual request tuples anchored independently of producer schedule.
        if s['lifetime']=='same':requests=[(5,'g1',1),(1,'g1',1),(6,'g1',2)]
        else:
            assert steps[1]['sql']=='DELETE FROM kv WHERE key=?' and steps[1]['params']==['k']
            assert steps[2]['sql']=='INSERT INTO kv VALUES(?,?,?,?)' and steps[2]['params']==['k','g2',1,100]
            requests=[(1,'g1',1),(101,'g2',2 if s['mode']=='version' else 1)]
        for step,(value,generation,version) in zip(updates,requests):assert step['params']==([value,'k',version] if s['mode']=='version' else [value,'k',generation,version])
        assert len(updates)==len(requests) and len([t for t in r['sql_trace'] if t.startswith('UPDATE')])==len(requests)
    for s in c['refusals']:
        r=rows[s['id']];assert r['status']=='expected-refusal' and r['reason']==s['reason'] and r['request']==s['request'] and r['update_sql_issued'] is False
        assert r['before']==r['final']==e['refusal_state'] and not any(t.startswith('UPDATE') for t in r['sql_trace'])
    r=rows['sql-error'];assert r['status']=='expected-sql-error' and r['rowcount'] is None and r['error']['type']=='OperationalError' and r['error']['message'] and r['attempted_sql']=='UPDATE kv SET' and r['before']==r['final']==e['sql_error_state']
def main():
    raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.CAS_OBSERVATION = ').strip().removesuffix(';'));d=ROOT/'observations'/raw['run_id']
    assert json.loads((d/'raw.json').read_text())==raw
    for n,h in raw['source_digests'].items():assert sha(ROOT/n)==h,n
    for n,v in json.loads((d/'artifact-index.json').read_text())['artifacts'].items():assert sha(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes']
    c=json.loads((ROOT/'contracts.json').read_text());e=json.loads((ROOT/'expected-states.json').read_text())
    for n in ('contracts.json','expected-states.json'):assert (ROOT/n).read_bytes()==(d/n).read_bytes()
    cmd=json.loads((d/'command.json').read_text());assert cmd['exit']==0 and cmd['stderr']=='' and cmd['argv']==['python3','experiment.py','<owned-temporary-directory>']
    produced=json.loads(cmd['stdout']);assert produced['rows']==raw['rows'] and produced['sqlite_version']==raw['sqlite_version']
    check_rows(raw,c,e)
    for r in raw['rows']:
        file=d/r['database_file'];assert file.name==r['id']+'.sqlite'
        db=sqlite3.connect(file.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)
        try:result=db.execute('SELECT key,generation,version,value FROM kv ORDER BY key').fetchall()
        finally:db.close()
        want=r['final'];assert result==[(want['key'],want['generation'],want['version'],want['value'])]
    controls=[]
    for fault in ('old-generation-accepted','generation-lost','version-reuse-hidden','input-refusal-as-success','sql-error-as-zero'):
        bad=copy.deepcopy(raw)
        if fault=='old-generation-accepted':bad['rows'][3]['steps'][-2]['rowcount']=1
        if fault=='generation-lost':bad['rows'][3]['final']['generation']='g1'
        if fault=='version-reuse-hidden':bad['rows'][2]['steps'][2]['state']['version']=2
        if fault=='input-refusal-as-success':bad['rows'][4]['status']='accepted-experiment'
        if fault=='sql-error-as-zero':bad['rows'][-1]['rowcount']=0
        try:check_rows(bad,c,e)
        except AssertionError:controls.append(fault)
        else:raise AssertionError('undetected '+fault)
    sys.dont_write_bytecode=True
    import route
    for q,t in route.ROUTES.items():assert route.route(q)=={'supported':True,'target':t,'executed':False,'reason':None}
    for q in route.UNSUPPORTED:assert route.route(q)['supported'] is False and route.route(q)['executed'] is False
    print(json.dumps({'status':'passed','run_id':raw['run_id'],'normal_experiments':4,'expected_refusals':6,'expected_sql_errors':1,'readonly_database_snapshots':11,'independent_oracle':'handwritten state/rowcount table + independent request tuples, no producer import','negative_controls_detected':controls,'skill_routes':{'normal':7,'unsupported':4,'scope':'structural only; model behavior unrun'}}))
if __name__=='__main__':main()
