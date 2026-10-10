"""Read-only default, explicit --record captures new actual timing observations."""
import argparse,copy,datetime,hashlib,itertools,json,platform,re
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-observability-engineering/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def smoke():
    observations=[runner.run(c) for c in runner.cases()];audits=[oracle.audit(r) for r in observations]
    generated=[]
    for units,fail,propagate in itertools.product((1,2,3),(False,True),(False,True)):
        inst=runner.Instrumentation();req={'units':units,'fail':fail,'propagate':propagate};runner.validate(req);response=runner.request(req,inst,1)
        assert response['status']==(503 if fail else 200)
        if not fail:assert response['amount']==[100,200,300][units-1]
        assert len(inst.spans)==2 and len(inst.logs)==6
        root=next(x for x in inst.spans if x['name']=='request');child=next(x for x in inst.spans if x['name']=='price_lookup');assert root['start_ns']<=child['start_ns']<=child['end_ns']<=root['end_ns']
        assert (child['trace_id']==root['trace_id'] and child['parent_span_id']==root['span_id'])==propagate
        generated.append({'input':req,'response':response,'logs':inst.logs,'spans':inst.spans,'metrics':inst.counter.rows()})
    rejects=[]
    for req,reason in [({'units':True,'fail':False,'propagate':True},'invalid-units'),({'units':4,'fail':False,'propagate':True},'invalid-units'),({'units':'2','fail':False,'propagate':True},'invalid-units'),({'units':1,'fail':1,'propagate':True},'invalid-flag'),({'units':1,'fail':False,'propagate':0},'invalid-flag'),({'units':1,'fail':False,'propagate':True,'extra':'x'},'invalid-request-key')]:
        try:runner.validate(req);raise AssertionError('accepted')
        except ValueError as e:assert str(e)==reason;rejects.append({'input':req,'reason':str(e)})
    for labels,reason in [({'route':'quote','outcome':'success','id':'dummy'},'unexpected-label-key'),({'route':'quote/1','outcome':'success'},'unexpected-label-value'),({'route':'quote','outcome':'other'},'unexpected-label-value')]:
        c=runner.Counter()
        try:c.add(labels);raise AssertionError('accepted')
        except ValueError as e:assert str(e)==reason and c.rows()==[];rejects.append({'labels':labels,'reason':str(e)})
    mutant=[];base=observations[0]
    for kind in ('event-order','clock-regression','negative-duration','wrong-duration','missing-parent','log-trace','metric-count','duplicate-series'):
        r=copy.deepcopy(base)
        if kind=='event-order':r['logs'][1]['event']='lookup.end'
        elif kind=='clock-regression':r['logs'][2]['monotonic_ns']=r['logs'][0]['monotonic_ns']-1
        elif kind=='negative-duration':r['spans'][0]['end_ns']=r['spans'][0]['start_ns']-1
        elif kind=='wrong-duration':r['spans'][0]['duration_ns']+=1
        elif kind=='missing-parent':r['spans'][0]['parent_span_id']=None
        elif kind=='log-trace':r['logs'][1]['trace_id']='f'*32
        elif kind=='metric-count':r['metrics'][0]['value']+=1
        elif kind=='duplicate-series':r['metrics'].append(copy.deepcopy(r['metrics'][0]))
        try:oracle.audit(r);raise RuntimeError('mutant survived '+kind)
        except AssertionError as e:mutant.append({'mutation':kind,'rejectedBy':str(e)})
    return {'raw':observations,'audits':audits,'generated':generated,'additionalRejects':rejects,'mutantsDetected':mutant}
def docs(record=False):
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(word in text for word in ('予想','原典','限界','未実施','SLO','privacy','pipeline'))
    sources=json.loads((ROOT/'sources.json').read_text());assert len(sources)==9 and all(s['url'].startswith('https://') and s['locator'] and s['binding'] for s in sources)
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();fresh=smoke();docs(a.record);h=hashes();input_digest=runner.digest(runner.cases())
    target=ROOT/'observations/run.json'
    if a.record:
        result={'schema':1,'executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'system':platform.system(),'machine':platform.machine(),'clock':str(__import__('time').get_clock_info('perf_counter'))},'command':'python3 -B checker.py --record','sourceArtifactDigests':h,'inputDigest':input_digest,'rawDigest':runner.digest(fresh),'result':fresh,'limits':'one-process actual functions; no OTel SDK/distributed backend'}
        tmp=target.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.replace(target)
    else:
        saved=json.loads(target.read_text());assert saved['sourceArtifactDigests']==h and saved['inputDigest']==input_digest;assert saved['rawDigest']==runner.digest(saved['result']);assert [oracle.audit(r) for r in saved['result']['raw']]==saved['result']['audits'];assert saved['result']['audits']==fresh['audits'];assert [r['case'] for r in saved['result']['raw']]==list(runner.cases());assert all(r['input']==runner.cases()[r['case']] for r in saved['result']['raw'])
        q=json.loads((ROOT/'observations/qa.json').read_text());assert q['sourceArtifactDigests']==h;assert q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'});assert [r['case'] for r in q['cases']]==list(runner.cases());assert q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
        for row in q['cases']:
            o=oracle.audit(next(r for r in saved['result']['raw'] if r['case']==row['case']));assert row['oracle']==o
        assert q['eventChecks']==len(q['eventObservations'])>=3 and len(q['roadmapTopics'])==4
        assert q['title']=='成功したrequestと切れたtrace | Observability'
        assert q['rawExpanded'] and q['answerExpanded']
        for event in q['eventObservations']:
            assert type(event['monotonic_ns']) is int and event['timestampUTC'].endswith('+00:00')
            if event['event']=='lookup.error':assert event['severity']=='ERROR' and event['attributes']=={'error_type':'LookupError'}
            if event['case']=='missing-propagation':assert event['trace_id']=='000000000000000000000000000003e9'

    print(json.dumps({'status':'PASS','cases':9,'generatedInputs':12,'rejects':12,'mutantsDetected':8,'sourceArtifacts':len(h),'readOnly':not a.record}))
if __name__=='__main__':main()
