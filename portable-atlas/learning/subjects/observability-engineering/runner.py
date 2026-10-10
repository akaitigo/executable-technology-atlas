"""Actual local request/lookup instrumentation, no OpenTelemetry SDK or remote backend."""
import datetime,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def cases():return json.loads((ROOT/'fixture.json').read_text())
class Counter:
    def __init__(self):self.values={}
    def add(self,labels):
        if set(labels)!= {'route','outcome'}:raise ValueError('unexpected-label-key')
        if labels['route']!='quote' or labels['outcome'] not in ('success','error'):raise ValueError('unexpected-label-value')
        key=(labels['route'],labels['outcome']);self.values[key]=self.values.get(key,0)+1
    def rows(self):return [{'name':'requests_total','labels':{'route':r,'outcome':o},'value':v} for (r,o),v in sorted(self.values.items())]
class Instrumentation:
    def __init__(self):self.logs=[];self.spans=[];self.counter=Counter()
    def log(self,event,ctx,severity='INFO',**attrs):
        self.logs.append({'sequence':len(self.logs)+1,'monotonic_ns':time.perf_counter_ns(),'timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'event':event,'trace_id':ctx['trace_id'],'span_id':ctx['span_id'],'severity':severity,'attributes':attrs})
    def finish(self,name,ctx,start,status):
        end=time.perf_counter_ns();self.spans.append({'name':name,**ctx,'start_ns':start,'end_ns':end,'duration_ns':end-start,'status':status})
def validate(req):
    if not isinstance(req,dict) or set(req)-{'units','fail','propagate','route','metric_extra'}:raise ValueError('invalid-request-key')
    if type(req.get('units')) is not int or not 1<=req['units']<=3:raise ValueError('invalid-units')
    if type(req.get('fail')) is not bool or type(req.get('propagate')) is not bool:raise ValueError('invalid-flag')
    if req.get('route','quote')!='quote':raise ValueError('unexpected-label-value')
    extra=req.get('metric_extra',{})
    if not isinstance(extra,dict) or extra:raise ValueError('unexpected-label-key')
def context(n,kind,parent=None):
    return {'trace_id':f'{n:032x}' if kind!='orphan' else f'{1000+n:032x}','span_id':f'{n*10+(1 if kind=="root" else 2):016x}','parent_span_id':parent}
def price_lookup(req,inst,ctx):
    start=time.perf_counter_ns();inst.log('lookup.begin',ctx)
    try:
        if req['fail']:raise LookupError('fixed local price unavailable')
        amount=req['units']*100;inst.log('lookup.result',ctx,amount=amount);status='OK';return amount
    except LookupError:
        inst.log('lookup.error',ctx,'ERROR',error_type='LookupError');status='ERROR';raise
    finally:
        inst.log('lookup.end',ctx);inst.finish('price_lookup',ctx,start,status)
def request(req,inst,n):
    ctx=context(n,'root');start=time.perf_counter_ns();inst.log('request.begin',ctx,route='quote')
    child=context(n,'child',ctx['span_id']) if req['propagate'] else context(n,'orphan')
    try:
        amount=price_lookup(req,inst,child);response={'status':200,'amount':amount};outcome='success';status='OK'
    except LookupError:
        response={'status':503,'error':'price_unavailable'};outcome='error';status='ERROR'
    inst.log('request.response',ctx,'ERROR' if outcome=='error' else 'INFO',status=response['status'])
    inst.counter.add({'route':'quote','outcome':outcome})
    inst.log('request.end',ctx);inst.finish('request',ctx,start,status)
    return response
def run(case='success'):
    fixture=cases()
    if case not in fixture:raise ValueError('unsupported-case')
    inputs=fixture[case];inst=Instrumentation();responses=[];rejected=[]
    for n,req in enumerate(inputs,1):
        try:validate(req)
        except ValueError as e:rejected.append({'requestIndex':n,'reason':str(e)});continue
        responses.append({'requestIndex':n,**request(req,inst,n)})
    return {'case':case,'input':inputs,'responses':responses,'rejected':rejected,'logs':inst.logs,'spans':inst.spans,'metrics':inst.counter.rows(),'clock':'actual perf_counter_ns, one process; UTC log timestamps for display only','model':'actual local Python functions, not distributed backend or OTel conformance','executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--case',choices=list(cases()),default='success');a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))
