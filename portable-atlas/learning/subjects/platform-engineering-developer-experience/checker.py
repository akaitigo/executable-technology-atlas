import argparse,copy,datetime,hashlib,json,re,tempfile
from pathlib import Path
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','templates.json','contract.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-platform-engineering-developer-experience/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def docs(record):
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','data:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(x in text for x in ('予想','原典','限界','未実施','DX','policy','ownership','lifecycle'))
    src=runner.load('sources.json');assert len(src)==7 and all(x['url'].startswith('https://') and x['locator'] and x['binding'] for x in src)
def rejects():
    c={'name':'cedar','owner':'team-a','kind':'library','schemaVersion':2};result=[]
    for field,value,reason in [('name','/outside','path-escape'),('name','a/b','path-escape'),('name','a\\b','path-escape'),('name','','invalid-name'),('name','a'*21,'invalid-name'),('name','Cedar','invalid-name'),('name',True,'invalid-name'),('owner','other','invalid-owner'),('kind','other','invalid-kind'),('schemaVersion',True,'invalid-schema'),('schemaVersion',1,'invalid-schema')]:
        bad=dict(c);bad[field]=value
        try:runner.validate_config(bad);raise RuntimeError('accepted invalid')
        except ValueError as e:assert str(e)==reason;result.append({'config':bad,'reason':reason})
    for bad in (dict(c,extra=1),[],None):
        try:runner.validate_config(bad);raise RuntimeError('accepted invalid')
        except ValueError as e:assert str(e)=='config-keys';result.append({'config':bad,'reason':str(e)})
    for path in ('../outside','/outside','src/../../outside','a\\b',''):
        try:runner.safe_target(ROOT/'observations/work',path);raise RuntimeError('accepted path')
        except ValueError as e:assert str(e)=='path-escape';result.append({'path':path,'reason':str(e)})
    return result
def mutants(raw):
    found=[]
    for kind in ('wrong-content','wrong-hash','hidden-missing','hidden-schema','false-determinism','accepted-path','wrong-repeat','wrong-phase'):
        r=copy.deepcopy(raw[5 if kind=='hidden-missing' else 6 if kind=='hidden-schema' else 4 if kind=='accepted-path' else 0])
        if kind=='wrong-content':r['tree']['README.md']='wrong\n'
        elif kind=='wrong-hash':r['report']['actualFileHashes']['README.md']='0'*64
        elif kind=='hidden-missing':r['report']['missing']=[]
        elif kind=='hidden-schema':r['report']['metadataDrift']=[]
        elif kind=='false-determinism':r['deterministicRender']=False
        elif kind=='accepted-path':r['filesWritten']=1
        elif kind=='wrong-repeat':r['repeatTree']['src/main.py']='wrong\n'
        elif kind=='wrong-phase':r['trace'][0]['phase']='render-first'
        try:oracle.audit(r);raise RuntimeError('survived '+kind)
        except AssertionError:found.append(kind)
    return found
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();docs(a.record);dest=ROOT/'observations/run.json'
    if a.record:
        raw=[];work=ROOT/'observations/work';work.mkdir(exist_ok=True)
        for case in runner.load('fixture.json')['cases']:
            with tempfile.TemporaryDirectory(prefix='record-',dir=work) as folder:
                r=runner.cycle(case,folder);oracle.audit(r);raw.append(r)
        data={'schema':1,'command':'python3 -B checker.py --record','executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceArtifactDigests':hashes(),'inputDigest':runner.digest(runner.load('fixture.json')),'raw':raw,'rawDigest':runner.digest(raw),'rejects':rejects(),'mutantsDetected':mutants(raw)}
        # Saved artifacts are exactly the first/repeat trees, no generated project registration.
        for r in raw:
            for label,key in [('first','tree'),('repeat','repeatTree')]:
                target=ROOT/'observations/artifacts'/r['case']/label
                runner.write_tree(target,r[key])
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    s=runner.load('observations/run.json');raw=s['raw'];assert s['sourceArtifactDigests']==hashes() and s['inputDigest']==runner.digest(runner.load('fixture.json')) and s['rawDigest']==runner.digest(raw);assert s['rejects']==rejects() and s['mutantsDetected']==mutants(raw)
    assert [r['case'] for r in raw]==list(runner.load('fixture.json')['cases'])
    for r in raw:
        assert r['input']==runner.load('fixture.json')['cases'][r['case']] and r['inputDigest']==runner.digest(r['input']);oracle.audit(r)
        for label,key in [('first','tree'),('repeat','repeatTree')]:assert runner.read_tree(ROOT/'observations/artifacts'/r['case']/label)==r[key]
    if not a.record:
        q=runner.load('observations/qa.json');assert q['sourceArtifactDigests']==hashes() and q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert [x['case'] for x in q['cases']]==[r['case'] for r in raw]
        for observed,r in zip(q['cases'],raw):assert observed['oracle']==oracle.audit(r)
        assert q['rawExpanded'] and q['answerExpanded'] and len(q['roadmapTopics'])==4 and len(q['fileChecks'])>=3 and q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
        for o in q['fileChecks']:assert o['content']==next(r for r in raw if r['case']==o['case'])['tree'][o['file']]
    print(json.dumps({'status':'PASS','cases':len(raw),'rejects':len(s['rejects'])+2,'mutantsDetected':len(s['mutantsDetected']),'artifactFiles':sum(len(r['tree'])+len(r['repeatTree']) for r in raw),'sourceArtifacts':len(hashes()),'readOnly':not a.record}))
if __name__=='__main__':main()
