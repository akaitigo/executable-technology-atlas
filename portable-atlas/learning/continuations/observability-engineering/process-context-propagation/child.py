"""Owned one-request child; custom JSON carrier, no OTel SDK."""
import sys,json,os,re,datetime
def event(name,seq):return dict(event=name,seq=seq,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
def valid_id(value,n):return isinstance(value,str) and re.fullmatch('[0-9a-f]{'+str(n)+'}',value) is not None and value!='0'*n
def process(req):
 if not isinstance(req,dict):return 'request must be object'
 if set(req)-{'units','context'}:return 'unexpected request key'
 if type(req.get('units')) is not int or not 1<=req['units']<=3:return 'units must be integer 1..3'
 if 'context' not in req:return None
 c=req['context']
 if not isinstance(c,dict):return 'context must be object'
 if set(c)-{'trace_id','parent_span_id'}:return 'unexpected context key'
 if 'trace_id' not in c:return 'context requires trace_id'
 if not valid_id(c['trace_id'],32):return 'invalid trace_id'
 if 'parent_span_id' in c and not valid_id(c['parent_span_id'],16):return 'invalid parent_span_id'
 return None
if __name__=='__main__':
 line=sys.stdin.readline();events=[event('childread',0)]
 try:req=json.loads(line);reason=process(req)
 except (ValueError,TypeError):req=None;reason='invalid JSON'
 out=dict(pid=os.getpid(),ppid=os.getppid(),received_stdin=line,request=req,events=events)
 if reason:
  out.update(status='refused',reason=reason,amount=None,span=None);events.append(event('childreject',1));exit_code=2
 else:
  c=req.get('context',{});out.update(status='succeeded',amount=100*req['units'],span=dict(trace_id=c.get('trace_id','d'*32),span_id='c'*16,parent_span_id=c.get('parent_span_id')));events.append(event('childcompute',1));exit_code=0
 events.append(event('childemit_ready',2));print(json.dumps(out),flush=True)
 print(json.dumps(dict(event='childemit_completed',seq=3,pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat())),flush=True);sys.exit(exit_code)
