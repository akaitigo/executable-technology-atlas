#!/usr/bin/env python3
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,itertools,json
from pathlib import Path
import model,oracle
ROOT=Path(__file__).resolve().parent
CAN=lambda o:json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
SHA=lambda o:hashlib.sha256(CAN(o).encode()).hexdigest()
def check_case(args):
    data=model.experiment(*args)
    for name,mode in [('protected','protected'),('bad','bad')]:
        actual=data[name];want=oracle.expected(*args,mode)
        for k in ('initCount','handlerCalls','statusCounts'):assert actual[k]==want[k],(args,name,k)
        assert actual['traceSha256']==SHA(actual['trace'])
        previous={};group={'warm':6,'cold-each':1,'recycle-pairs':2}[args[0]]
        for i,(row,expected) in enumerate(zip(actual['trace'],want['rows'])):
            for k in ('environment','coldInit'):assert row[k]==expected[k]
            for k,ek in [('status','status'),('handlerCalled','called'),('result','result')]:assert row['reply'][k]==expected[ek],(args,name,i,k)
            assert row['after']['scratch']==expected['scratch']
            prior_scratch=[] if expected['coldInit'] else want['rows'][i-1]['scratch']
            assert row['before']['scratch']==prior_scratch
            before={} if expected['coldInit'] and args[1]=='process-local' else previous
            assert row['before']['store']==before
            store={}
            for j in range(i+1):
                if args[1]=='process-local' and j//group!=i//group:continue
                r=want['rows'][j];e=data['events'][j]
                if r['status']=='executed':store[e['tenant']+':'+e['id']]={'fingerprint':SHA(e['items']),'result':r['result']}
            assert row['after']['store']==store,(args,name,i,'store')
            previous=store
    return data
def measurements():
    axes=[['warm','cold-each','recycle-pairs'],['process-local','run-shared'],['duplicates','unique'],['normal','empty','max','oversize','conflict'],['none','handler-error']]
    cases=[]
    for args in itertools.product(*axes):
        d=check_case(args);cases.append({'args':list(args),'protected':d['protected']['traceSha256'],'bad':d['bad']['traceSha256'],'inputSha256':SHA(d['events']),'actual':d,'expected':{mode:oracle.expected(*args,mode) for mode in ('protected','bad')}})
    hands=[(['warm','process-local','duplicates','normal','none'],1,4,[2,3,7,2,5,5],[2,5,12,2,17,17]),(['cold-each','process-local','duplicates','normal','none'],6,6,[2,3,7,2,5,5],[2,3,7,2,5,5]),(['cold-each','run-shared','duplicates','normal','none'],6,4,[2,3,7,2,5,5],[2,3,7,2,5,5]),(['warm','process-local','duplicates','normal','handler-error'],1,5,[2,3,7,2,None,5],[2,5,12,2,None,22])]
    for args,init,calls,good,bad in hands:
        d=check_case(args);assert d['protected']['initCount']==init and d['protected']['handlerCalls']==calls
        for name,vals in [('protected',good),('bad',bad)]:assert [r['reply']['result']['sum'] if r['reply']['result'] else None for r in d[name]['trace']]==vals
    invalid=[None,[],{}, {'tenant':'c','id':'e1','items':[]},{'tenant':'a','id':'unknown','items':[]},*[{'tenant':'a','id':'e1','items':x} for x in (None,'x',[True],[1.0],[-1],[10],[1,2,3,4])],{'tenant':'a','id':'e1','items':[],'extra':1},{'tenant':'a','items':[]}]
    for e in invalid:
        env=model.Environment(1,model.MemoryStore(),'protected');assert env.invoke(e)['status']=='input-rejected';assert env.handler_calls==0 and env.store.entries=={}
    for items in ([],[0,9,9]):
        env=model.Environment(1,model.MemoryStore(),'protected');r=env.invoke({'tenant':'a','id':'e1','items':items});assert r['result']['sum']==sum(items)
    env=model.Environment(1,model.MemoryStore(),'protected');e={'tenant':'a','id':'e1','items':[2]};env.invoke(e);r=env.invoke(e);r['result']['items'].append(9);assert env.invoke(e)['result']['items']==[2]
    defaults=['warm','process-local','duplicates','normal','none']
    for i in range(5):
        a=defaults[:];a[i]='unsupported'
        try:model.experiment(*a)
        except ValueError:pass
        else:raise AssertionError('accepted unsupported')
    d=model.experiment();assert d['bad']['trace'][2]['reply']['result']!=d['protected']['trace'][2]['reply']['result']
    fault=model.simulate(*defaults,'fault-global-key');assert fault['trace'][2]['reply']['status']=='conflict' and d['protected']['trace'][2]['reply']['status']=='executed'
    lost=model.experiment('cold-each','process-local');shared=model.experiment('cold-each','run-shared');assert lost['protected']['handlerCalls']==6 and shared['protected']['handlerCalls']==4
    return {'gridCount':len(cases),'cases':cases,'handCount':len(hands),'inputRejectCount':len(invalid),'optionRejectCount':5,'faultCount':3,'sources':model.SOURCES}
def bindings():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='bindings.json'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true');a=parser.parse_args();m=measurements()
    if a.record:
        (ROOT/'evidence/run.json').write_text(json.dumps({'measurements':m,'recordedAt':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'runtime':{'python':sys.version.split()[0],'platform':sys.platform}},ensure_ascii=False,indent=2)+'\n')
        (ROOT/'evidence/bindings.json').write_text(json.dumps(bindings(),indent=2)+'\n')
    else:
        assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==m
        assert json.loads((ROOT/'evidence/bindings.json').read_text())==bindings()
        qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['serverStopped'] and qa['tabClosed'] and len(qa['cases'])==10

        for observed in qa['cases']:
            args=observed['args']
            if args[0]=='live-cloud':
                assert observed['status']=='入力拒否: unsupported reuse' and observed['protectedTrace'] is None and observed['badTrace'] is None and observed['rows']==0
            else:
                actual=model.experiment(*args)
                assert observed['status']=='比較完了' and observed['rows']==6
                assert observed['protectedTrace']==actual['protected']['traceSha256'] and observed['badTrace']==actual['bad']['traceSha256']
        assert json.loads((ROOT/'evidence/routing-smoke.json').read_text())['forwardAgentEval']=='not-run'
    print(json.dumps({k:v for k,v in m.items() if k!='cases'},ensure_ascii=False))
if __name__=='__main__':main()
