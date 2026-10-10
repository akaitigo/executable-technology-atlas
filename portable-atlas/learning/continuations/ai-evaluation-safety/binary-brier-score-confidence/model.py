import json,sys
from fractions import Fraction

def run(x):
 def refuse(reason):return {'observed':False,'reason':reason,'summary':None,'samples':[]},2
 if not isinstance(x,dict) or set(x)!={'mode','samples'} or x['mode'] not in ('probability','threshold-fault'):return refuse('schema/mode')
 ss=x['samples']
 if not isinstance(ss,list) or not 1<=len(ss)<=8:return refuse('sample count 1..8')
 seen=set()
 for s in ss:
  if not isinstance(s,dict) or set(s)!={'id','percent','label'}:return refuse('sample schema')
  if not isinstance(s['id'],str) or not s['id'] or len(s['id'])>40 or s['id'] in seen:return refuse('unique nonempty ID required')
  seen.add(s['id'])
  if type(s['percent']) is not int or not 0<=s['percent']<=100:return refuse('percent exact integer 0..100; bool/nonfinite forbidden')
  if type(s['label']) is not int or s['label'] not in (0,1):return refuse('label exact integer 0 or1; bool forbidden')
 rows=[];errors=[];correct=0
 for s in ss:
  p=Fraction(s['percent'],100);c=int(s['percent']>=50);score=Fraction(c) if x['mode']=='threshold-fault' else p;loss=(score-s['label'])**2;errors.append(loss);correct+=int(c==s['label']);rows.append({'id':s['id'],'percent':s['percent'],'label':s['label'],'probability':str(p),'class':c,'usedScore':str(score),'squaredError':str(loss)})
 return {'observed':True,'reason':None,'samples':rows,'summary':{'count':len(ss),'correct':correct,'accuracy':str(Fraction(correct,len(ss))),'reportedBrier':str(sum(errors)/len(ss)),'mode':x['mode'],'thresholdPercent':50}},0
if __name__=='__main__':
 if sys.argv[1:]:print('unsupported argument',file=sys.stderr);sys.exit(2)
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 o,code=run(x);print(json.dumps(o));sys.exit(code)
