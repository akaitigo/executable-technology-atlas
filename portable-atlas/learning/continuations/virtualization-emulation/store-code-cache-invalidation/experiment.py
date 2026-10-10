"""Tiny8 STORE extension. No external inputs, VM, JIT or native code."""
import json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
VALID={16,32,48,64,255}
def validate(x):
 if type(x) is not dict or set(x)!={'program','pc','a','budget'}:return False
 return type(x['program']) is list and 1<=len(x['program'])<=256 and all(type(b) is int and 0<=b<=255 for b in x['program']) and all(type(x[k]) is int and 0<=x[k]<=255 for k in ['pc','a']) and type(x['budget']) is int and 1<=x['budget']<=64

def decode(memory,start):
 instructions=[];addresses=[];pc=start
 # Bounded decode stops at a control/write boundary or illegal instruction.
 for _ in range(64):
  op=memory[pc];operand=None;addresses.append(pc)
  if op in VALID-{255}:operand=memory[(pc+1)&255];addresses.append((pc+1)&255)
  instructions.append({'pc':pc,'opcode':op,'operand':operand})
  if op not in VALID or op in {48,64,255}:break
  pc=(pc+2)&255
 return {'start':start,'addresses':list(dict.fromkeys(addresses)),'instructions':instructions}

def run(x,prewarm,mode):
 trace=[];events=[];stores=[];cache={};decoded=[]
 if not validate(x):return {'status':'input','pc':0,'a':0,'steps':0,'trace':[],'diagnostic':{'reason':'input_contract'},'memory':None,'cache_events':[],'store_events':[],'decoded_blocks':[]}
 memory=x['program']+[0]*(256-len(x['program']));pc=x['pc'];a=x['a'];block=None;offset=0
 def get(start,kind):
  if start in cache:events.append({'event':'hit','start':start});return cache[start]
  b=decode(memory,start);cache[start]=b;decoded.append(b);events.append({'event':kind,'start':start,'addresses':b['addresses']});return b
 if mode!='fetch':
  for start in prewarm:get(start,'prewarm')
 status='budget';diagnostic={'pc':pc,'limit':x['budget']}
 for _ in range(x['budget']):
  if mode=='fetch':
   op=memory[pc];operand=memory[(pc+1)&255] if op in VALID-{255} else None
  else:
   if block is None or offset>=len(block['instructions']) or block['instructions'][offset]['pc']!=pc:block=get(pc,'decode');offset=0
   ins=block['instructions'][offset];op=ins['opcode'];operand=ins['operand'];offset+=1
  if op not in VALID:status='illegal';diagnostic={'pc':pc,'opcode':op};break
  before_pc,before_a=pc,a;diff=[]
  if op==16:a=operand;pc=(pc+2)&255
  elif op==32:a=(a+operand)&255;pc=(pc+2)&255
  elif op==48:pc=operand if a==0 else (pc+2)&255;block=None
  elif op==64:
   diff=[[operand,memory[operand],a]];memory[operand]=a;pc=(pc+2)&255
   if mode!='fetch':
    overlaps=sorted(k for k,b in cache.items() if operand in b['addresses']);evicted=overlaps if mode=='invalidate' else []
    for k in evicted:del cache[k]
    stores.append({'write':operand,'overlaps':overlaps,'evicted':evicted,'kept':sorted(cache)})
    events.append({'event':'store','write':operand,'overlaps':overlaps,'evicted':evicted,'kept':sorted(cache)})
   block=None
  elif op==255:status='halt';diagnostic=None
  trace.append([before_pc,before_a,op,operand,pc,a,diff])
  if status=='halt':break
 else:diagnostic={'pc':pc,'limit':x['budget']}
 return dict(status=status,pc=pc,a=a,steps=len(trace),trace=trace,diagnostic=diagnostic,memory=memory,cache_events=events,store_events=stores,decoded_blocks=decoded)

def main():
 contracts=json.loads((ROOT/'contracts.json').read_text());rows=[]
 for c in contracts['cases']:rows.append({'id':c['id'],'label':c['label'],'input':c['input'],'prewarm':c['prewarm'],'variants':{m:run(c['input'],c['prewarm'],m) for m in contracts['modes']}})
 print(json.dumps({'schema':1,'engine':'author-defined Tiny8 STORE; Python interpreter and decoded blocks','rows':rows},ensure_ascii=False))
if __name__=='__main__':main()
