"""Read-only default; explicit --record only updates execution receipt."""
import argparse,copy,datetime,hashlib,itertools,json,platform,re
from fractions import Fraction
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-sre-incident-operations/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def verify(record=False):
    f=runner.fixture();assert f['target']=={'numerator':9,'denominator':10} and f['windows']==[[0,10],[10,20]] and f['watermark']==20
    raw=[runner.run(c) for c in f['cases']];audits=[oracle.audit(r) for r in raw]
    generated=[]
    for n1 in range(1,6):
        for g1 in range(n1+1):
            for n2 in range(1,6):
                for g2 in range(n2+1):
                    events=[{'id':str(i),'at':i,'arrived':i,'kind':'success' if i<g1 else 'server_error'} for i in range(n1)]+[{'id':'b'+str(i),'at':10+i,'arrived':10+i,'kind':'success' if i<g2 else 'server_error'} for i in range(n2)]
                    s=runner.calculate(events)['summary'];n=n1+n2;good=g1+g2;bad=n-good
                    assert oracle.f(s['sli'])==Fraction(good,n);assert oracle.f(s['naiveUnweightedSLI'])==(Fraction(g1,n1)+Fraction(g2,n2))/2
                    assert oracle.f(s['burnRate'])==Fraction(bad,n)*10;assert oracle.f(s['allowedErrors'])==Fraction(n,10);assert oracle.f(s['remainingErrors'])==Fraction(n,10)-bad
                    generated.append({'population':[n1,g1,n2,g2],'summary':s})
    extra=[];base={'id':'x','at':1,'arrived':1,'kind':'success'}
    inputs=[([base,base],'duplicate-or-invalid-id'),([dict(base,at=True)],'invalid-event-time'),([dict(base,arrived=0)],'invalid-event-time'),([dict(base,at=21,arrived=21)],'invalid-event-time'),([dict(base,kind='unknown')],'unknown-outcome'),([dict(base,extra=1)],'invalid-event-schema'),([dict(base,arrived=21)],'late-input'),([dict(base,id='')],'duplicate-or-invalid-id'),([base]*101,'invalid-events')]
    for events,reason in inputs:
        try:runner.calculate(events);raise AssertionError('accepted invalid')
        except ValueError as e:assert str(e)==reason;extra.append({'input':events,'reason':reason})
    mutants=[]
    for kind in ('naive-as-global','wrong-denominator','wrong-burn','clamp-negative','rounded-budget','window-binding','boundary-inclusive','bad-count'):
        index=2 if kind=='clamp-negative' else 4 if kind in ('rounded-budget','boundary-inclusive') else 3 if kind=='wrong-denominator' else 0
        r=copy.deepcopy(raw[index]);s=r['summary']
        if kind=='naive-as-global':s['sli']=s['naiveUnweightedSLI']
        elif kind=='wrong-denominator':s['denominator']=12
        elif kind=='wrong-burn':s['burnRate']=runner.ratio(0,1)
        elif kind=='clamp-negative':s['remainingErrors']=runner.ratio(0,1)
        elif kind=='rounded-budget':s['allowedErrors']=runner.ratio(1,1)
        elif kind=='window-binding':r['windows'][0]['eligibleIds']=[]
        elif kind=='boundary-inclusive':s['outsideIds']=[]
        elif kind=='bad-count':s['bad']+=1
        try:oracle.audit(r);raise RuntimeError('survived '+kind)
        except AssertionError:mutants.append(kind)
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(word in text for word in ('予想','原典','限界','未実施','measurement','policy','incident','postmortem'))
    src=json.loads((ROOT/'sources.json').read_text());assert len(src)==7 and all(s['url'].startswith('https://') and s['locator'] and s['binding'] for s in src)
    return {'raw':raw,'audits':audits,'generated':generated,'extraRejects':extra,'mutantsDetected':mutants}
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();result=verify(a.record);h=hashes();dest=ROOT/'observations/run.json'
    data={'schema':1,'executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine()},'command':'python3 -B checker.py --record','scope':'fixed synthetic toy SLO; not real operations or incident success','sourceArtifactDigests':h,'inputDigest':runner.digest(runner.fixture()),'rawDigest':runner.digest(result),'result':result}
    if a.record:
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    else:
        saved=json.loads(dest.read_text());assert saved['sourceArtifactDigests']==h;assert saved['inputDigest']==data['inputDigest'];assert saved['rawDigest']==data['rawDigest'];assert saved['result']==result
        q=json.loads((ROOT/'observations/qa.json').read_text());assert q['sourceArtifactDigests']==h;assert q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert [r['case'] for r in q['cases']]==list(runner.fixture()['cases']);assert q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
        for observed in q['cases']:assert observed['oracle']==oracle.audit(runner.run(observed['case']))
        assert q['windowChecks']==len(q['windowObservations'])>=2 and len(q['roadmapTopics'])==4 and q['rawExpanded'] and q['answerExpanded']
        for observed in q['windowObservations']:
            actual=runner.run(observed['case'])['windows'][observed['index']]
            assert observed['observed']=={k:actual[k] for k in observed['observed']}
        assert q['title']=='分母から読むerror budget | SRE incident operations'
    print(json.dumps({'status':'PASS','cases':9,'generatedPopulations':len(result['generated']),'rejects':13,'mutantsDetected':8,'sourceArtifacts':len(h),'readOnly':not a.record}))
if __name__=='__main__':main()
