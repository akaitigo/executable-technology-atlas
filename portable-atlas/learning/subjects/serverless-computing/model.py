"""実local handler、合成environment再利用モデル。cloudへ接続しない。"""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCES={'reuse':'https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html','lifecycle':'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html','retry':'https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html'}
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def validate_event(e):
    if type(e)is not dict or set(e)!={'tenant','id','items'}:raise ValueError('event schema')
    if e['tenant'] not in ('a','b'):raise ValueError('unsupported tenant')
    if e['id'] not in ('e1','e2','e3'):raise ValueError('unsupported event id')
    if type(e['items'])is not list or len(e['items'])>3:raise ValueError('payload list length 0..3')
    if any(type(x)is not int or not 0<=x<=9 for x in e['items']):raise ValueError('payload integers 0..9')
def fixture(duplicates,payload):
    es=json.loads((ROOT/'events.json').read_text())
    if duplicates=='unique':es[3]['id']='e3';es[5]['id']='e3'
    if payload=='empty':
        for e in es:e['items']=[]
    elif payload=='max':
        for e in es:e['items']=[0,9,9]
    elif payload=='oversize':es[1]['items']=[1,2,3,4]
    elif payload=='conflict':es[3]['items']=[9]
    return es
class MemoryStore:
    def __init__(self):self.entries={}
    def snapshot(self):return {k:copy.deepcopy(v) for k,v in self.entries.items()}
class Environment:
    def __init__(self,number,store,mode):
        self.number=number;self.store=store;self.mode=mode;self.scratch=[];self.client={'label':'synthetic reusable client'};self.handler_calls=0
    def handler(self,event,fail=False):
        self.handler_calls+=1
        scratch=[] if self.mode=='protected' else self.scratch
        scratch.extend(event['items'])
        if fail:raise RuntimeError('synthetic handler failure before store commit')
        return {'tenant':event['tenant'],'items':list(scratch),'sum':sum(scratch),'count':len(scratch)}
    def invoke(self,event,fail=False):
        try:validate_event(event)
        except ValueError as e:return {'status':'input-rejected','error':str(e),'handlerCalled':False,'result':None}
        key=(event['id'] if self.mode=='fault-global-key' else event['tenant']+':'+event['id']);fingerprint=digest(event['items'])
        prior=self.store.entries.get(key)
        if prior:
            if prior['fingerprint']!=fingerprint:return {'status':'conflict','error':'same key different payload','handlerCalled':False,'result':None}
            return {'status':'duplicate','error':None,'handlerCalled':False,'result':copy.deepcopy(prior['result'])}
        try:result=self.handler(event,fail)
        except RuntimeError as e:return {'status':'handler-error','error':str(e),'handlerCalled':True,'result':None}
        self.store.entries[key]={'fingerprint':fingerprint,'result':copy.deepcopy(result)}
        return {'status':'executed','error':None,'handlerCalled':True,'result':result}
def simulate(reuse,lifetime,duplicates,payload,error,mode):
    es=fixture(duplicates,payload);shared=MemoryStore();env=None;trace=[];initCount=0;calls=0
    for index,event in enumerate(es):
        cold=env is None or reuse=='cold-each' or (reuse=='recycle-pairs' and index%2==0)
        if cold:initCount+=1;env=Environment(initCount,shared if lifetime=='run-shared' else MemoryStore(),mode)
        before={'scratch':list(env.scratch),'store':env.store.snapshot()};reply=env.invoke(event,error=='handler-error' and index==4);calls+=reply['handlerCalled']
        trace.append({'index':index,'event':event,'environment':env.number,'coldInit':cold,'before':before,'reply':reply,'after':{'scratch':list(env.scratch),'store':env.store.snapshot()}})
    return {'mode':mode,'initCount':initCount,'handlerCalls':calls,'statusCounts':{status:sum(t['reply']['status']==status for t in trace) for status in ('executed','duplicate','input-rejected','conflict','handler-error')},'trace':trace,'traceSha256':digest(trace)}
def experiment(reuse='warm',lifetime='process-local',duplicates='duplicates',payload='normal',error='none'):
    for label,v,allowed in [('reuse',reuse,('warm','cold-each','recycle-pairs')),('lifetime',lifetime,('process-local','run-shared')),('duplicates',duplicates,('duplicates','unique')),('payload',payload,('normal','empty','max','oversize','conflict')),('error',error,('none','handler-error'))]:
        if v not in allowed:raise ValueError('unsupported '+label)
    return {'input':dict(zip(('reuse','lifetime','duplicates','payload','error'),(reuse,lifetime,duplicates,payload,error))),'events':fixture(duplicates,payload),'protected':simulate(reuse,lifetime,duplicates,payload,error,'protected'),'bad':simulate(reuse,lifetime,duplicates,payload,error,'warm-state-leak')}
