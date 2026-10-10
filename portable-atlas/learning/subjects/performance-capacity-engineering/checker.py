import argparse,copy,datetime,hashlib,itertools,json,re
from fractions import Fraction
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-performance-capacity-engineering/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def docs(record):
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','data:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(x in text for x in ('予想','原典','限界','未実施','Workload','Measurement','Capacity','Overload'))
    src=runner.load('sources.json');assert len(src)==6 and all(x['url'].startswith('https://') and x['locator'] and x['binding'] for x in src)
def generated():
    evidence=[]
    for arrivals in itertools.combinations_with_replacement(range(5),3):
        for service in (1,2,3):
            # Independent tick scheduler, not max(previousFinish,arrival) recurrence.
            pending=[];active=None;timeline={}
            for tick in range(30):
                if active is not None and timeline[active][1]==tick:active=None
                pending.extend(i for i,a in enumerate(arrivals) if a==tick)
                if active is None and pending:active=pending.pop(0);timeline[active]=(tick,tick+service)
            for a,b in ((0,6),(2,6)):
                inp={'arrivals':list(arrivals),'service':service,'window':[a,b]};r=runner.calculate(inp);assert [(j['start'],j['finish']) for j in r['jobs']]==[timeline[i] for i in range(3)]
                system=sum(arrivals[i]<=t<timeline[i][1] for t in range(a,b) for i in range(3));queue=sum(arrivals[i]<=t<timeline[i][0] for t in range(a,b) for i in range(3));busy=sum(timeline[i][0]<=t<timeline[i][1] for t in range(a,b) for i in range(3))
                assert (r['systemArea'],r['queueArea'],r['busyArea'])==(system,queue,busy) and oracle.f(r['L'])==Fraction(system,b-a)
                assert sum(x['systemIntersection'] for x in r['intersections'])==system and sum(x['queueIntersection'] for x in r['intersections'])==queue
                if r['cohortIds']:assert oracle.f(r['finiteExposureProduct'])==Fraction(system,b-a)
                evidence.append({'input':inp,'jobs':r['jobs'],'areas':[system,queue,busy]})
    return evidence
def rejects():
    base={'arrivals':[0,1],'service':2,'window':[0,6]};bad=[(dict(base,service=True),'invalid-service'),(dict(base,service=11),'invalid-service'),(dict(base,arrivals=[1,0]),'invalid-arrivals'),(dict(base,arrivals=[-1]),'invalid-arrivals'),(dict(base,arrivals=[0.5]),'invalid-arrivals'),(dict(base,arrivals=[True]),'invalid-arrivals'),(dict(base,arrivals=[0]*21),'invalid-arrivals'),(dict(base,window=[0,201]),'invalid-window'),(dict(base,window=[True,6]),'invalid-window'),(dict(base,extra=1),'invalid-schema'),(None,'invalid-schema')];out=[]
    for inp,reason in bad:
        try:runner.calculate(inp);raise RuntimeError('accepted invalid')
        except ValueError as e:assert str(e)==reason;out.append({'input':inp,'reason':reason})
    return out
def mutants(raw):
    found=[]
    for kind in ('omit-unfinished','queue-as-system','wrong-wait','wrong-boundary','omit-carry-in','mixed-cohort','fake-identity','wrong-segment','wrong-busy'):
        r=copy.deepcopy(raw[4 if kind=='omit-carry-in' else 5 if kind=='wrong-boundary' else 3]);v=r['result']
        if kind=='omit-unfinished':v['unfinishedAtEndIds']=[]
        elif kind=='queue-as-system':v['L']=v['Lq']
        elif kind=='wrong-wait':v['jobs'][1]['wait']=0
        elif kind=='wrong-boundary':v['arrivalIds'].append('j2')
        elif kind=='omit-carry-in':v['carryInIds']=[]
        elif kind=='mixed-cohort':v['cohortExposureMean']=v['completedMeanResponse']
        elif kind=='fake-identity':v['completedProductMatchesL']=True
        elif kind=='wrong-segment':v['segments'][0]['systemArea']+=1
        elif kind=='wrong-busy':v['busyArea']-=1
        try:oracle.audit(r);raise RuntimeError('survived '+kind)
        except AssertionError:found.append(kind)
    return found
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();docs(a.record);fixture=runner.load('fixture.json')
    if a.record:
        raw=[runner.run(c) for c in fixture['cases']];[oracle.audit(r) for r in raw];g=generated();s={'schema':1,'command':'python3 -B checker.py --record','executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceArtifactDigests':hashes(),'inputDigest':runner.digest(fixture),'raw':raw,'rawDigest':runner.digest(raw),'generated':g,'generatedDigest':runner.digest(g),'rejects':rejects(),'mutantsDetected':mutants(raw)};p=ROOT/'observations/run.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');temp.replace(p)
    s=runner.load('observations/run.json');raw=s['raw'];assert s['sourceArtifactDigests']==hashes() and s['inputDigest']==runner.digest(fixture) and s['rawDigest']==runner.digest(raw);assert s['generated']==generated() and s['generatedDigest']==runner.digest(s['generated']) and s['rejects']==rejects() and s['mutantsDetected']==mutants(raw)
    assert [r['case'] for r in raw]==list(fixture['cases'])
    for r in raw:assert r['input']==fixture['cases'][r['case']] and r['inputDigest']==runner.digest(r['input']);oracle.audit(r);assert r['executionObservedNs']>0;datetime.datetime.fromisoformat(r['executedAtUTC'])
    if not a.record:
        q=runner.load('observations/qa.json');assert q['sourceArtifactDigests']==hashes() and q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert [o['case'] for o in q['cases']]==[r['case'] for r in raw]
        for o,r in zip(q['cases'],raw):assert o['oracle']==oracle.audit(r)
        for o in q['jobBindings']:
            r=next(x for x in raw if x['case']==o['case'])['result'];assert o['observed']=={'job':next(j for j in r['jobs'] if j['id']==o['jobId']),'intersection':next(j for j in r['intersections'] if j['id']==o['jobId'])}
        assert len(q['jobBindings'])>=4 and q['rawExpanded'] and q['answerExpanded'] and len(q['roadmapTopics'])==4 and q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
    print(json.dumps({'status':'PASS','cases':9,'generatedWorkloads':len(s['generated']),'rejects':len(s['rejects'])+2,'mutantsDetected':len(s['mutantsDetected']),'sourceArtifacts':len(hashes()),'readOnly':not a.record}))
if __name__=='__main__':main()
