import argparse,copy,datetime,hashlib,json,re
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','architectures.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-cloud-architecture/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def docs(record):
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','data:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(x in text for x in ('予想','原典','限界','未実施','Reliability','Performance','Security','Operations'))
    src=runner.load('sources.json');assert len(src)==8 and all(x['url'].startswith('https://') and x['locator'] and x['binding'] for x in src)
def rejects():
    results=[]
    for f,reason in [(None,'invalid-fault-list'),('zone-a','invalid-fault-list'),([True],'invalid-fault-list'),([1],'invalid-fault-list'),(['unknown'],'unknown-fault'),(['zone-a','zone-a'],'duplicate-fault')]:
        try:runner.evaluate('shared',f);raise RuntimeError('accepted invalid')
        except ValueError as e:assert str(e)==reason;results.append({'input':f,'reason':reason})
    try:runner.evaluate('real-cloud',[]);raise RuntimeError('accepted mode')
    except ValueError as e:assert str(e)=='unsupported-mode';results.append({'mode':'real-cloud','reason':str(e)})
    return results
def mutants(raw,matrix):
    found=[]
    for kind in ('ignore-dependency','ignore-zone','false-replication','wrong-cross-latency','wrong-router','wrong-route','false-availability','wrong-probability','wrong-matrix-fault'):
        r=copy.deepcopy(raw[1]);mat=copy.deepcopy(matrix)
        if kind=='ignore-dependency':r['results'][0]['serviceUp']=True
        elif kind=='ignore-zone':r=copy.deepcopy(raw[2]);r['results'][1]['nodeHealth']['app-a']=True
        elif kind=='false-replication':r['results'][2]['serviceUp']=False
        elif kind=='wrong-cross-latency':r=copy.deepcopy(raw[3]);r['results'][0]['latencySyntheticUnits']=7
        elif kind=='wrong-router':r=copy.deepcopy(raw[4]);r['results'][1]['serviceUp']=True
        elif kind=='wrong-route':r['results'][1]['selectedPath']=['router','app-a','dep-a']
        elif kind=='false-availability':mat['modeledAvailability']['shared']['numerator']+=1
        elif kind=='wrong-probability':mat['rows'][0]['probabilityUnderAssumptions']['numerator']+=1
        elif kind=='wrong-matrix-fault':mat['rows'][0]['faults']=['router']
        try:
            if kind in ('false-availability','wrong-probability','wrong-matrix-fault'):oracle.audit_matrix(mat)
            else:oracle.audit(r)
            raise RuntimeError('survived '+kind)
        except AssertionError:found.append(kind)
    return found
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();docs(a.record);fixture=runner.load('fixture.json');assert fixture['upProbability']=={'numerator':99,'denominator':100} and fixture['latencySynthetic']=={'router':1,'app':2,'dependency':4,'crossZone':5}
    if a.record:
        raw=[runner.run(c) for c in fixture['cases']];matrix=runner.matrix();[oracle.audit(r) for r in raw];mo=oracle.audit_matrix(matrix)
        out=ROOT/'observations/matrix.json';out.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
        s={'schema':1,'command':'python3 -B checker.py --record','executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceArtifactDigests':hashes(),'inputDigest':runner.digest(fixture),'raw':raw,'rawDigest':runner.digest(raw),'matrixDigest':runner.digest(matrix),'matrixFileHash':hashlib.sha256(out.read_bytes()).hexdigest(),'matrixOracle':mo,'rejects':rejects(),'mutantsDetected':mutants(raw,matrix)}
        out=ROOT/'observations/run.json';temp=out.with_suffix('.tmp');temp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');temp.replace(out)
    s=runner.load('observations/run.json');raw=s['raw'];matrix=runner.load('observations/matrix.json');assert s['sourceArtifactDigests']==hashes() and s['inputDigest']==runner.digest(fixture) and s['rawDigest']==runner.digest(raw) and s['matrixDigest']==runner.digest(matrix) and s['matrixFileHash']==hashlib.sha256((ROOT/'observations/matrix.json').read_bytes()).hexdigest();assert s['matrixOracle']==oracle.audit_matrix(matrix) and s['rejects']==rejects() and s['mutantsDetected']==mutants(raw,matrix)
    assert [r['case'] for r in raw]==list(fixture['cases'])
    for r in raw:
        assert r['input']==fixture['cases'][r['case']] and r['inputDigest']==runner.digest(r['input']);oracle.audit(r);assert r['executionObservedNs']>0;datetime.datetime.fromisoformat(r['executedAtUTC'])
    if not a.record:
        q=runner.load('observations/qa.json');assert q['sourceArtifactDigests']==hashes() and q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert [x['case'] for x in q['cases']]==[r['case'] for r in raw]
        for o,r in zip(q['cases'],raw):assert o['oracle']==oracle.audit(r)
        assert q['matrixOracle']==s['matrixOracle'] and q['matrixRowCount']==128
        for b in q['bindings']:
            results=next(r for r in raw if r['case']==b['case'])['results'] if b['mask']=='case' else next(row for row in matrix['rows'] if row['mask']==b['mask'])['results'];r=next(x for x in results if x['mode']==b['mode']);assert b['observed']=={k:r[k] for k in b['observed']}
        assert len(q['bindings'])>=4 and q['rawExpanded'] and q['answerExpanded'] and len(q['roadmapTopics'])==4 and q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
    print(json.dumps({'status':'PASS','cases':10,'failureStates':128,'modeChecks':384,'rejects':len(s['rejects'])+2,'mutantsDetected':len(s['mutantsDetected']),'sourceArtifacts':len(hashes()),'readOnly':not a.record}))
if __name__=='__main__':main()
