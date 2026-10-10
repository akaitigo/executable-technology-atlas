"""Read-only except explicitly requested --record. Independent finite oracle."""
import argparse,copy,datetime,hashlib,itertools,json,platform,re
import runner,oracle
ROOT=runner.ROOT
FILES=['runner.py','oracle.py','checker.py','server.py','manifest.json','desired/v1.json','desired/v2.json','desired/rollback-v3.json','README.md','index.html','app.js','sources.json','skills/atlas-gitops-continuous-delivery/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def verify(record=False):
    raw=[runner.run(c) for c in runner.CASES]
    for r in raw:
        actions,final=oracle.EXPECTED[r['case']]
        assert [x['action'] for x in r['trace']]==actions
        assert r['final']==final and r['finalHash']==oracle.statehash(final)
        for x in r['trace']:
            if x['action']=='refuse':assert x['liveBefore']==x['liveAfter']
            if 'afterHash' in x:assert x['afterHash']==oracle.statehash(x['liveAfter'])
    inputs=[runner.packet(n) for n in oracle.HASHES]
    for p in inputs:assert runner.sha(p['bytes'].encode())==p['sha256']==oracle.HASHES[p['name']]
    assert inputs[0]['sha256']==inputs[2]['sha256'] and inputs[0]['generation']!=inputs[2]['generation']
    generated=[]
    for name,mode,ignore,image,replicas,note in itertools.product(oracle.HASHES,('apply','observe'),((),('note',)),('demo:v1','demo:v2','demo:manual'),(0,2,5),('declared','operator')):
        live={'image':image,'replicas':replicas,'note':note};p=runner.packet(name)
        r=runner.reconcile(live,p,p,mode,ignore);expected=oracle.transition(live,name,mode,ignore)
        assert r['liveAfter']==expected and r['afterHash']==oracle.statehash(expected)
        again=runner.reconcile(r['liveAfter'],p,p,mode,ignore)
        assert again['liveAfter']==r['liveAfter']
        if mode=='apply':assert again['action']=='in-sync'
        generated.append({'revision':name,'mode':mode,'ignore':list(ignore),'before':live,'after':r['liveAfter'],'hash':r['afterHash']})
    rejects=[]
    p=runner.packet('v2');base=dict(oracle.V1)
    for kind in ('stale-generation','wrong-hash-token','tamper','bad-json','missing-field','bool-replicas','too-large','unknown-image','unknown-note','bad-mode','bad-ignore','duplicate-ignore'):
        pp=copy.deepcopy(p);live=dict(base);mode='apply';ig=[];reason=''
        if kind=='stale-generation':pp['generation']=1;reason='stale-revision'
        elif kind=='wrong-hash-token':pp['sha256']='0'*64;reason='stale-revision'
        elif kind=='tamper':pp['bytes']+=' ';reason='bytes-hash-mismatch'
        elif kind in ('bad-json','missing-field'):
            pp['bytes']='{' if kind=='bad-json' else '{"image":"demo:v2"}';pp['sha256']=runner.sha(pp['bytes'].encode());reason='json-or-schema'
        elif kind=='bool-replicas':live['replicas']=True;reason='invalid-state'
        elif kind=='too-large':live['replicas']=6;reason='invalid-state'
        elif kind=='unknown-image':live['image']='other';reason='invalid-state'
        elif kind=='unknown-note':live['note']='other';reason='invalid-state'
        elif kind=='bad-mode':mode='automatic';reason='invalid-mode'
        elif kind=='bad-ignore':ig=['image'];reason='invalid-ignore'
        elif kind=='duplicate-ignore':ig=['note','note'];reason='invalid-ignore'
        authoritative=pp if kind in ('bad-json','missing-field') else p
        r=runner.reconcile(live,pp,authoritative,mode,ig)
        assert r['action']=='refuse' and r['liveAfter']==live
        if reason!='json-or-schema':assert r['reason']==reason
        rejects.append({'case':kind,'raw':r})
    # Independent oracle detects plausible faulty algorithms.
    assert oracle.transition(oracle.MANUAL,'v2','apply',())!=oracle.MANUAL
    assert oracle.transition(oracle.MANUAL,'v2','observe',())!=oracle.V2
    assert oracle.transition({'image':'demo:v1','replicas':2,'note':'operator'},'v2','apply',('note',))!=oracle.V2
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(w in text for w in ('予想','原典','限界','未実施','所有','健康','復旧'))
    src=json.loads((ROOT/'sources.json').read_text());assert len(src)==6 and all(s['url'].startswith('https://') and s['locator'] and s['binding'] for s in src)
    return {'inputs':inputs,'raw':raw,'generatedTransitions':generated,'rejects':rejects,'mutantsDetected':['never-repair','apply-in-observe','ignore-not-respected']}
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();result=verify(a.record);h=hashes()
    data={'schema':1,'executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},'command':'python3 -B checker.py --record','scope':'local model, whole subject incomplete; no Git/Argo product/cluster execution','sourceArtifactDigests':h,'inputDigest':runner.digest(result['inputs']),'rawDigest':runner.digest(result),'result':result}
    dest=ROOT/'observations/run.json'
    if a.record:
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    else:
        saved=json.loads(dest.read_text());assert saved['sourceArtifactDigests']==h;assert saved['inputDigest']==data['inputDigest'];assert saved['rawDigest']==data['rawDigest'];assert saved['result']==result
        q=json.loads((ROOT/'observations/qa.json').read_text());assert q['sourceArtifactDigests']==h;assert q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert len(q['cases'])==10;assert q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
        for row in q['cases']:
            actual=runner.run(row['case']);assert row['final']==actual['final'];assert row['actions']==[x['action'] for x in actual['trace']]
        assert q['title']=='宣言へ戻すloop | GitOps継続的デリバリー';assert q['stepChecks']==len(q['stepObservations'])>=6 and len(q['roadmapTopics'])==4
        assert [row['case'] for row in q['cases']]==list(runner.CASES)
        for observed in q['stepObservations']:
            actual=runner.run(observed['case'])['trace'][observed['step']-1]
            assert observed['action']==actual['action']
            assert observed['before']==actual.get('liveBefore',actual['liveAfter'])
            assert observed['after']==actual['liveAfter']
    print(json.dumps({'status':'PASS','cases':10,'generatedTransitions':len(result['generatedTransitions']),'rejects':12,'mutantsDetected':3,'sourceArtifacts':len(h),'readOnly':not a.record}))
if __name__=='__main__':main()
