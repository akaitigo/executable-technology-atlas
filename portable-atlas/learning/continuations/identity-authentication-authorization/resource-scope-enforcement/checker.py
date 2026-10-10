import copy,hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def check_rows(raw,c,e):
    rows={r['id']:r for r in raw['rows']};assert len(rows)==len(raw['rows'])==30
    expected={r['id']:r for r in e['rows']};assert len(expected)==24
    tuples={(s['subject'],s['scope'],s['resource'],s['action']) for s in c['cases']}
    assert tuples==set(itertools.product(('a-reader','a-no-read','b-reader'),('alpha','beta'),('doc-alpha','doc-beta'),('read','write')))
    def result(r,request,want,mode):
        allow=want=='allow';refuse=want in ('unknown-resource','missing-resource-attribute','authenticated-subject-required','request-field-set','scope-contract')
        decision='allow' if allow else 'refuse' if refuse else 'deny'
        assert r['decision']==decision and r['reason']==want and r['read_count']==int(allow)
        content=None
        if allow:content=e['fixture_literals']['alpha.txt' if request['resource']=='doc-alpha' else 'beta.txt'].encode('ascii')
        assert r['content_ascii']==(content.decode() if content is not None else None) and r['content_hex']==(content.hex() if content is not None else None) and r['content_sha256']==(hashlib.sha256(content).hexdigest() if content is not None else None)
        events=[t['event'] for t in r['trace']]
        assert events==(['request','decision'] if refuse else ['request','trusted-resource','checks','decision']+(['read-start','read-complete'] if allow else []))
        assert r['trace'][0]=={'event':'request','mode':mode}
        dec=r['trace'][1 if refuse else 3];assert dec=={'event':'decision','decision':decision,'reason':want}
        if not refuse:
            scope='alpha' if request['resource']=='doc-alpha' else 'beta';owner='owner-'+scope
            assert r['trace'][1]=={'event':'trusted-resource','resource':request['resource'],'scope':scope,'owner':owner}
            assigned='beta' if request['subject']=='b-reader' else 'alpha'
            assert r['trace'][2]=={'event':'checks','resource_scope_matches':request['scope']==scope,'subject_scope_assigned':request['scope']==assigned,'read_permitted':request['action']=='read' and request['subject']!='a-no-read','resource_scope_enforced':mode=='normal'}
        if allow:
            file='alpha.txt' if request['resource']=='doc-alpha' else 'beta.txt'
            assert r['trace'][4]=={'event':'read-start','fixture_file':file} and r['trace'][5]=={'event':'read-complete','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest()}
    for s in c['cases']:
        r=rows[s['id']];request={k:v for k,v in s.items() if k!='id'}
        assert r['status']=='normal-comparison' and r['request']==request
        result(r['normal'],request,expected[s['id']]['normal'],'normal');result(r['faulty'],request,expected[s['id']]['faulty'],'scope-only')
    for s in c['refusals']:
        r=rows[s['id']];assert r['status']=='expected-refusal' and r['request']==s['request']
        result(r['normal'],s['request'],s['reason'],'normal');result(r['faulty'],s['request'],s['reason'],'scope-only')
    assert sum(r['normal']['read_count'] for r in raw['rows'])==2 and sum(r['faulty']['read_count'] for r in raw['rows'])==4
    return rows
def main():
    raw=json.loads((ROOT/'observation-data.js').read_text().removeprefix('window.SCOPE_OBSERVATION = ').strip().removesuffix(';'));d=ROOT/'observations'/raw['run_id']
    assert json.loads((d/'raw.json').read_text())==raw
    for n,h in raw['source_digests'].items():assert sha(ROOT/n)==h,n
    for n,v in json.loads((d/'artifact-index.json').read_text())['artifacts'].items():assert sha(d/n)==v['sha256'] and (d/n).stat().st_size==v['bytes']
    c=json.loads((ROOT/'contracts.json').read_text());e=json.loads((ROOT/'expected-table.json').read_text())
    for n in ('contracts.json','expected-table.json'):assert (ROOT/n).read_bytes()==(d/n).read_bytes()
    # Content oracle is a separate fixed literal, never read via producer serializer.
    assert e['fixture_literals']=={'alpha.txt':'ALPHA SYNTHETIC DOCUMENT\n','beta.txt':'BETA SYNTHETIC DOCUMENT\n'}
    for n,literal in e['fixture_literals'].items():assert (ROOT/'fixtures'/n).read_bytes()==(d/n).read_bytes()==literal.encode('ascii')
    cmd=json.loads((d/'command.json').read_text());assert cmd['exit']==0 and cmd['stderr']=='' and cmd['argv']==['python3','experiment.py','<owned-fixture-directory>'];assert json.loads(cmd['stdout'])['rows']==raw['rows']
    check_rows(raw,c,e);detected=[]
    for fault in ('scope-bypass-hidden','read-before-deny','wrong-content','refusal-as-success','decision-after-read'):
        bad=copy.deepcopy(raw)
        if fault=='scope-bypass-hidden':bad['rows'][2]['faulty']['decision']='deny'
        if fault=='read-before-deny':bad['rows'][2]['normal']['read_count']=1
        if fault=='wrong-content':bad['rows'][0]['normal']['content_ascii']='BETA SYNTHETIC DOCUMENT\n'
        if fault=='refusal-as-success':bad['rows'][24]['status']='normal-comparison'
        if fault=='decision-after-read':bad['rows'][0]['normal']['trace'][3:5]=reversed(bad['rows'][0]['normal']['trace'][3:5])
        try:check_rows(bad,c,e)
        except AssertionError:detected.append(fault)
        else:raise AssertionError('escaped negative control '+fault)
    sys.dont_write_bytecode=True
    import route
    for q,t in route.ROUTES.items():assert route.route(q)=={'supported':True,'target':t,'executed':False,'reason':None}
    for q in route.UNSUPPORTED:assert route.route(q)['supported'] is False and route.route(q)['executed'] is False
    print(json.dumps({'status':'passed','run_id':raw['run_id'],'normal_comparisons':24,'expected_refusals':6,'actual_reads':{'normal':2,'faulty':4},'independent_oracle':'handwritten full truth table + separate literal content bytes; no producer import','negative_controls_detected':detected,'skill_routes':{'normal':7,'unsupported':4,'scope':'structural only; model behavior unrun'}}))
if __name__=='__main__':main()
